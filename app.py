import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Advanced Buy vs Rent", layout="wide")
st.title("🏠 Advanced Buy vs. Rent Simulator")

st.sidebar.title("Configuration Parameters")

with st.sidebar.expander("1. Property & Loan Details", expanded=True):
    home_price = st.number_input("Home Price ($)", value=500000, step=10000)
    down_payment_pct = st.slider("Down Payment (%)", 0.0, 100.0, 20.0) / 100
    mortgage_rate = st.slider("Mortgage Rate (%)", 1.0, 10.0, 6.5) / 100
    loan_years = st.slider("Loan Term (Years)", 10, 30, 30)
    closing_costs_pct = st.slider("Closing Costs (% of loan)", 0.0, 5.0, 3.0) / 100
    selling_costs_pct = st.slider("Selling Costs / Realtor Fees (%)", 0.0, 10.0, 6.0) / 100

with st.sidebar.expander("2. Renting Details", expanded=True):
    monthly_rent = st.number_input("Initial Monthly Rent ($)", value=2500, step=100)
    rent_inflation = st.slider("Annual Rent Inflation (%)", 0.0, 10.0, 3.0) / 100
    renters_insurance = st.number_input("Renter's Ins. ($/mo)", value=20)

with st.sidebar.expander("3. Market Returns & Inflation", expanded=True):
    home_appreciation = st.slider("Home Appreciation (%)", 0.0, 10.0, 4.0) / 100
    stock_return = st.slider("Stock Market Return (%)", 0.0, 15.0, 8.0) / 100

with st.sidebar.expander("4. Taxes & Maintenance", expanded=True):
    property_tax_rate = st.slider("Property Tax Rate (%)", 0.0, 3.0, 1.2) / 100
    maintenance_rate = st.slider("Annual Maintenance (%)", 0.0, 3.0, 1.0) / 100
    home_insurance_rate = st.slider("Home Insurance (%)", 0.0, 2.0, 0.5) / 100
    marginal_tax_rate = st.slider("Marginal Tax Rate (%)", 10, 50, 24) / 100
    capital_gains_tax = st.slider("Long-Term Capital Gains Tax (%)", 0, 30, 15) / 100
    standard_deduction = st.number_input("Standard Deduction ($)", value=14600)

years_to_simulate = st.slider("Years to Simulate", 1, 50, 30)

# Core Math
down_payment = home_price * down_payment_pct
loan_amount = home_price - down_payment
monthly_mortgage_rate = mortgage_rate / 12
n_payments = loan_years * 12
monthly_pi = loan_amount * (monthly_mortgage_rate * (1 + monthly_mortgage_rate)**n_payments) / ((1 + monthly_mortgage_rate)**n_payments - 1) if monthly_mortgage_rate > 0 else loan_amount / n_payments

buy_net_worth = []
rent_net_worth = []
current_home_value = home_price
current_loan_balance = loan_amount
current_rent = monthly_rent
renter_portfolio = down_payment + (loan_amount * closing_costs_pct)
renter_cost_basis = renter_portfolio

for year in range(1, years_to_simulate + 1):
    annual_property_tax = current_home_value * property_tax_rate
    annual_insurance = current_home_value * home_insurance_rate
    annual_maintenance = current_home_value * maintenance_rate
    annual_mortgage_interest = 0
    
    for month in range(12):
        if current_loan_balance > 0:
            interest_payment = current_loan_balance * monthly_mortgage_rate
            principal_payment = monthly_pi - interest_payment
            current_loan_balance -= principal_payment
            annual_mortgage_interest += interest_payment
        else:
            interest_payment = 0; principal_payment = 0
            
        monthly_buy_cost = principal_payment + interest_payment + (annual_property_tax/12) + (annual_insurance/12) + (annual_maintenance/12)
        cash_flow_diff = monthly_buy_cost - (current_rent + renters_insurance)
        
        renter_portfolio *= (1 + stock_return/12)
        renter_portfolio += cash_flow_diff
        renter_cost_basis += max(0, cash_flow_diff)
        
    deductible_tax = min(annual_property_tax, 10000)
    if (annual_mortgage_interest + deductible_tax) > standard_deduction:
        renter_portfolio -= ((annual_mortgage_interest + deductible_tax) - standard_deduction) * marginal_tax_rate
    
    current_home_value *= (1 + home_appreciation)
    current_rent *= (1 + rent_inflation)
    
    buy_net_worth.append(max(0, (current_home_value - current_loan_balance) - (current_home_value * selling_costs_pct)))
    rent_net_worth.append(max(0, renter_portfolio - (max(0, renter_portfolio - renter_cost_basis) * capital_gains_tax)))
# --- INITIAL MONTHLY BREAKDOWN ---
st.subheader("Year 1: Monthly Cash Flow Breakdown")

# Calculate Year 1 monthly extras for the buyer
initial_taxes_ins_maint = (home_price * property_tax_rate / 12) + (home_price * home_insurance_rate / 12) + (home_price * maintenance_rate / 12)
initial_total_buy = monthly_pi + initial_taxes_ins_maint
initial_total_rent = monthly_rent + renters_insurance
initial_investment = max(0, initial_total_buy - initial_total_rent)

colA, colB, colC, colD = st.columns(4)
with colA: 
    st.metric("Mortgage (P&I)", f"${int(monthly_pi):,}")
with colB: 
    st.metric("Taxes/Ins/Maint", f"${int(initial_taxes_ins_maint):,}")
with colC: 
    st.metric("Total Buy Cost", f"${int(initial_total_buy):,}")
with colD: 
    st.metric("Renter's Investment", f"${int(initial_investment):,}")

st.divider()
# Display
st.subheader(f"Results after {years_to_simulate} Years")
col1, col2, col3 = st.columns(3)
with col1: st.metric("Net Worth (If Bought)", f"${int(buy_net_worth[-1]):,}")
with col2: st.metric("Net Worth (If Rented)", f"${int(rent_net_worth[-1]):,}")
with col3:
    diff = buy_net_worth[-1] - rent_net_worth[-1]
    st.metric(f"Winner: {'Buying' if diff > 0 else 'Renting'}", f"+${abs(int(diff)):,}")

st.line_chart(pd.DataFrame({"Buying": buy_net_worth, "Renting": rent_net_worth}, index=range(1, years_to_simulate + 1)))