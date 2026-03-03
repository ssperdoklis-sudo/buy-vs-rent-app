import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Αγορά vs. Ενοίκιο (Greece)", layout="wide")
st.title("🇬🇷 Advanced Buy vs. Rent Simulator (Greece)")

st.sidebar.title("Configuration Parameters")

# --- 1. PROPERTY & LOAN ---
with st.sidebar.expander("1. Property & Loan Details", expanded=True):
    home_price = st.number_input("Home Price (€)", value=250000, step=10000)
    down_payment_pct = st.slider("Down Payment (%)", 0.0, 100.0, 20.0) / 100
    mortgage_rate = st.slider("Mortgage Rate (%)", 1.0, 10.0, 4.0) / 100
    loan_years = st.slider("Loan Term (Years)", 10, 40, 30)
    # In Greece, transfer tax, notary, registry, and agent fees apply to the total home price
    closing_costs_pct = st.slider("Buying Closing Costs (%)", 0.0, 15.0, 6.5) / 100
    selling_costs_pct = st.slider("Selling Agent Fees (%)", 0.0, 10.0, 2.5) / 100

# --- 2. RENTING DETAILS ---
with st.sidebar.expander("2. Renting Details", expanded=True):
    monthly_rent = st.number_input("Initial Monthly Rent (€)", value=900, step=50)
    rent_inflation = st.slider("Annual Rent Inflation (%)", 0.0, 10.0, 3.0) / 100
    renters_insurance = st.number_input("Renter's Ins. (€/mo)", value=10)

# --- 3. MARKET RETURNS ---
with st.sidebar.expander("3. Market Returns", expanded=True):
    home_appreciation = st.slider("Home Appreciation (%)", 0.0, 10.0, 3.0) / 100
    stock_return = st.slider("Stock Market Return (%)", 0.0, 15.0, 7.0) / 100

# --- 4. TAXES & UPKEEP ---
with st.sidebar.expander("4. Taxes & Maintenance", expanded=True):
    property_tax_rate = st.slider("Annual ENFIA / Prop. Tax (%)", 0.0, 2.0, 0.2) / 100
    maintenance_rate = st.slider("Annual Maintenance (%)", 0.0, 3.0, 0.5) / 100
    home_insurance_rate = st.slider("Home Insurance (%)", 0.0, 2.0, 0.2) / 100
    # UCITS ETFs are 0% tax in Greece, but we leave the slider just in case
    capital_gains_tax = st.slider("Stock Capital Gains Tax (%)", 0, 30, 0) / 100

years_to_simulate = st.slider("Years to Simulate", 1, 50, 30)

# --- CORE MATH PREP ---
down_payment = home_price * down_payment_pct
loan_amount = home_price - down_payment
closing_costs = home_price * closing_costs_pct
initial_cash_outlay_buy = down_payment + closing_costs

monthly_mortgage_rate = mortgage_rate / 12
n_payments = loan_years * 12

# Amortization Formula
if monthly_mortgage_rate > 0:
    monthly_pi = loan_amount * (monthly_mortgage_rate * (1 + monthly_mortgage_rate)**n_payments) / ((1 + monthly_mortgage_rate)**n_payments - 1)
else:
    monthly_pi = loan_amount / n_payments

# Simulation Tracking Lists
buy_net_worth = []
rent_net_worth = []
yearly_data = []

current_home_value = home_price
current_loan_balance = loan_amount
current_rent = monthly_rent

# The renter takes the exact same initial cash the buyer needed and invests it
renter_portfolio = initial_cash_outlay_buy
renter_cost_basis = initial_cash_outlay_buy

# Calculate Initial Monthly Breakdown for Display
initial_taxes_ins_maint = (home_price * property_tax_rate / 12) + (home_price * home_insurance_rate / 12) + (home_price * maintenance_rate / 12)
initial_total_buy = monthly_pi + initial_taxes_ins_maint
initial_total_rent = monthly_rent + renters_insurance
initial_investment = initial_total_buy - initial_total_rent

# --- SIMULATION LOOP ---
for year in range(1, years_to_simulate + 1):
    annual_property_tax = current_home_value * property_tax_rate
    annual_insurance = current_home_value * home_insurance_rate
    annual_maintenance = current_home_value * maintenance_rate
    
    annual_principal_paid = 0
    annual_interest_paid = 0
    annual_renter_investment = 0
    
    for month in range(12):
        if current_loan_balance > 0:
            interest_payment = current_loan_balance * monthly_mortgage_rate
            principal_payment = monthly_pi - interest_payment
            
            if principal_payment > current_loan_balance:
                principal_payment = current_loan_balance
                interest_payment = 0
                
            current_loan_balance -= principal_payment
            annual_interest_paid += interest_payment
            annual_principal_paid += principal_payment
        else:
            interest_payment = 0
            principal_payment = 0
            
        monthly_buy_cost = principal_payment + interest_payment + (annual_property_tax/12) + (annual_insurance/12) + (annual_maintenance/12)
        monthly_rent_cost = current_rent + renters_insurance
        
        # Investment diff
        cash_flow_diff = monthly_buy_cost - monthly_rent_cost
        
        renter_portfolio *= (1 + stock_return/12)
        renter_portfolio += cash_flow_diff
        
        # Track cost basis for potential taxes
        if cash_flow_diff > 0:
            renter_cost_basis += cash_flow_diff
            annual_renter_investment += cash_flow_diff
        else:
            annual_renter_investment += cash_flow_diff # Negative means pulling from investments
            
    # Yearly Appreciations
    current_home_value *= (1 + home_appreciation)
    current_rent *= (1 + rent_inflation)
    
    # Buyer NW
    buyer_equity = current_home_value - current_loan_balance
    buyer_nw_if_sold = buyer_equity - (current_home_value * selling_costs_pct)
    final_buy_nw = max(0, buyer_nw_if_sold)
    buy_net_worth.append(final_buy_nw)
    
    # Renter NW
    capital_gains = max(0, renter_portfolio - renter_cost_basis)
    renter_nw_after_tax = renter_portfolio - (capital_gains * capital_gains_tax)
    final_rent_nw = max(0, renter_nw_after_tax)
    rent_net_worth.append(final_rent_nw)
    
    # Save for table
    yearly_data.append({
        "Year": year,
        "Home Value (€)": round(current_home_value),
        "Loan Balance (€)": round(current_loan_balance),
        "Buyer Net Worth (€)": round(final_buy_nw),
        "Monthly Rent (€)": round(current_rent),
        "Renter Portfolio (€)": round(renter_portfolio),
        "Renter Net Worth (€)": round(final_rent_nw)
    })

# --- UI DISPLAY ---
st.subheader("Year 1: Monthly Cash Flow Breakdown")

colA, colB, colC, colD = st.columns(4)
with colA: 
    st.metric("Mortgage (P&I)", f"€{int(monthly_pi):,}")
with colB: 
    st.metric("Taxes/Ins/Maint", f"€{int(initial_taxes_ins_maint):,}")
with colC: 
    st.metric("Total Buy Cost", f"€{int(initial_total_buy):,}")
with colD: 
    # If the renter has extra cash, show it. If buying is cheaper, show 0.
    st.metric("Renter's Investment", f"€{int(max(0, initial_investment)):,}")

st.divider()

st.subheader(f"Final Results after {years_to_simulate} Years")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Net Worth (If Bought)", value=f"€{int(buy_net_worth[-1]):,}")
with col2:
    st.metric(label="Net Worth (If Rented)", value=f"€{int(rent_net_worth[-1]):,}")
with col3:
    difference = buy_net_worth[-1] - rent_net_worth[-1]
    winner = "Buying" if difference > 0 else "Renting"
    st.metric(label=f"Winner: {winner}", value=f"+€{abs(int(difference)):,}")

# --- CHART ---
chart_data = pd.DataFrame({
    "Year": range(1, years_to_simulate + 1),
    "Buying Net Worth": buy_net_worth,
    "Renting Net Worth": rent_net_worth
}).set_index("Year")

st.line_chart(chart_data)

# --- DATA TABLE ---
with st.expander("📊 View Detailed Yearly Data (Click to expand)"):
    
    df_yearly = pd.DataFrame(yearly_data).set_index("Year")
    st.dataframe(df_yearly, use_container_width=True)
    
    st.markdown("""
    **Formula Used for Mortgage:**
    The monthly principal and interest is calculated using the standard amortization formula:
    $$M = P \\frac{r(1+r)^n}{(1+r)^n - 1}$$
    """)