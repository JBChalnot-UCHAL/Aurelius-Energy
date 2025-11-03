import streamlit as st
import math
import sys

# --- 0. LOGGING FUNCTION ---
def log_debug(message):
    """Prints a log to the terminal running Streamlit."""
    print(f"DEBUG: {message}", file=sys.stderr)

log_debug("--- Starting Simulator Script v25 (UI & Lifecycle Fix) ---")

# --- 1. SIMULATION CONSTANTS (based on documents) ---
MATERIAL_COST_PER_UNIT = 18.0
LABOR_COST_PER_WORKER = 18000.0
UNITS_PER_WORKER = 2000.0
LABOR_COST_PER_UNIT = LABOR_COST_PER_WORKER / UNITS_PER_WORKER # 9.0
UNIT_COST_FOR_COGS = MATERIAL_COST_PER_UNIT # 18.0
UNIT_COST_FOR_INVENTORY = MATERIAL_COST_PER_UNIT + LABOR_COST_PER_UNIT # 27.0
UNITS_PER_LINE = 10000.0
COST_PER_NEW_LINE = 50000.0
DEPRECIATION_PER_LINE = 10000.0
BASE_ADMIN_SALARIES = 300000.0
RENT_FACTORY = 300000.0
PROPERTY_TAX = 40000.0
AUDITING_FEES = 0.0 # Assumption
EXISTING_DEBT = 200000.0
INTEREST_RATE_DEBT = 0.08
INTEREST_RATE_OVERDRAFT = 0.10
DEBT_REPAYMENT_YEAR = 2 # Year X8
TAX_RATE = 0.40
CASH_PAYMENT_RATE_SALES = 0.85
CASH_PAYMENT_RATE_PURCHASES = 0.90

# --- 2. INITIAL STATE (END OF YEAR X6) ---
INITIAL_BALANCE_SHEET = {
    'year': 'X6',
    'cash': 70000.0,
    'accounts_receivable': 350000.0,
    'inventory_finished_units': 5000.0,
    'inventory_finished_value': 135000.0,
    'inventory_materials_units': 10000.0,
    'inventory_materials_value': 180000.0,
    'gross_fixed_assets': 450000.0,
    'accumulated_depreciation': 240000.0,
    'accounts_payable': 235000.0,
    'income_tax_payable': 60000.0,
    'bank_overdraft': 0.0,
    'long_term_debt': 200000.0,
    'capital_stock': 250000.0,
    'retained_earnings': 110000.0,
    'net_income_previous_year': 90000.0,
}
# Auditor-Confirmed Correct Initial Ages
INITIAL_LINE_AGES = {
    'age_0': 0, # New
    'age_1': 1, # Operated 1 year
    'age_2': 3, # Operated 2 years
    'age_3': 3, # Operated 3 years
    'age_4': 2, # Operated 4 years
}
INITIAL_WORKERS = 50

# --- 3. SIMULATION ENGINE (RUNS ONE YEAR AT A TIME) ---

def run_one_year(year_label, year_index, prev_bs, prev_lines, prev_workers, decisions):
    """
    Simulates a single year and returns all calculated data and the new "previous state".
    """
    log_debug(f"--- Calculating Year {year_label} (Index {year_index}) ---")
    
    cf_data, is_data, bs_data, bs_internal, inventory_flow_data, lines_flow_data = {}, {}, {}, {}, {}, {}
    
    # --- A. STRATEGIC DECISIONS ---
    target_production_volume = decisions['prod_volume']
    
    # --- B. PRODUCTION PLANNING (CAPACITY) ---
    total_existing_lines = sum(prev_lines.values())
    existing_line_capacity = total_existing_lines * UNITS_PER_LINE
    log_debug(f"[{year_label}] Lines (start): {total_existing_lines} - Capacity: {existing_line_capacity}")
    
    new_lines_needed = 0
    if target_production_volume > existing_line_capacity:
        new_lines_needed = math.ceil((target_production_volume - existing_line_capacity) / UNITS_PER_LINE)
        log_debug(f"[{year_label}] NEW LINES PURCHASED: {new_lines_needed}")
    
    investment_cash_out = new_lines_needed * COST_PER_NEW_LINE
    total_lines_for_year = total_existing_lines + new_lines_needed
    total_line_capacity = total_lines_for_year * UNITS_PER_LINE
    
    current_workers = prev_workers
    existing_worker_capacity = current_workers * UNITS_PER_WORKER
    new_workers_needed = 0
    if target_production_volume > existing_worker_capacity:
        new_workers_needed = math.ceil((target_production_volume - existing_worker_capacity) / UNITS_PER_WORKER)
        log_debug(f"[{year_label}] NEW EMPLOYEES HIRED: {new_workers_needed}")
        current_workers += new_workers_needed
    
    total_worker_capacity = current_workers * UNITS_PER_WORKER
    
    production_capacity = min(total_line_capacity, total_worker_capacity)
    production_volume = min(target_production_volume, production_capacity)
    log_debug(f"[{year_label}] Production: Target={target_production_volume}, Capacity={production_capacity}, Actual Production={production_volume}")
    
    # --- C. INCOME STATEMENT (AUDIT FIX E1) ---
    
    # C1. Sales & Revenue
    opening_inv_units = prev_bs['inventory_finished_units']
    total_available_for_sale = opening_inv_units + production_volume
    actual_sales_volume = total_available_for_sale * decisions['percent_sold']
    log_debug(f"[{year_label}] Sales: Available={total_available_for_sale}, %Sold={decisions['percent_sold']*100}%, Actual Sold={actual_sales_volume}")
    revenue = actual_sales_volume * decisions['price']
    
    # C2. Finished Inventory Change (E-B)
    opening_inv_fin_val = prev_bs['inventory_finished_value']
    ending_inv_units = opening_inv_units + production_volume - actual_sales_volume
    ending_inv_fin_val = ending_inv_units * UNIT_COST_FOR_INVENTORY # Valued at 27 CU
    change_in_finished_inv = ending_inv_fin_val - opening_inv_fin_val # (E-B)
    
    # C3. Operating Revenue (Per Template)
    operating_revenue = revenue + change_in_finished_inv
    
    # C4. Material Expense (Per Template)
    materials_needed = production_volume
    materials_from_stock = prev_bs['inventory_materials_units']
    materials_to_purchase = max(0, materials_needed - materials_from_stock)
    cost_materials_to_purchase = materials_to_purchase * MATERIAL_COST_PER_UNIT
    
    opening_inv_mat_val = prev_bs['inventory_materials_value']
    ending_mat_units = materials_from_stock - materials_needed + materials_to_purchase
    ending_inv_mat_val = ending_mat_units * MATERIAL_COST_PER_UNIT
    change_in_raw_inv = opening_inv_mat_val - ending_inv_mat_val # (B-E)
    
    material_expense = cost_materials_to_purchase + change_in_raw_inv
    
    # C5. Other Operating Expenses
    personnel_expenses = current_workers * LABOR_COST_PER_WORKER + BASE_ADMIN_SALARIES
    external_expenses_base = RENT_FACTORY + PROPERTY_TAX + AUDITING_FEES
    depreciation_expense = total_lines_for_year * DEPRECIATION_PER_LINE
    
    # C6. Marketing Expense (Base = All other OpEx)
    base_for_marketing = material_expense + personnel_expenses + external_expenses_base + depreciation_expense
    marketing_expense = (base_for_marketing / (1 - decisions['marketing_pct'])) * decisions['marketing_pct'] if decisions['marketing_pct'] < 1 else base_for_marketing
    
    # C7. Total Operating Expense & EBIT
    operating_expense = material_expense + personnel_expenses + external_expenses_base + marketing_expense + depreciation_expense
    ebit = operating_revenue - operating_expense
    
    # C8. Financial Charges (AUDIT FIX E2)
    interest_fixed_debt = prev_bs['long_term_debt'] * INTEREST_RATE_DEBT
    interest_overdraft = 0.0
    
    # --- D. CASH FLOW STATEMENT (CF) ---
    
    # D1. Tentative Cash Flow (to find Overdraft)
    cash_from_sales_AR = prev_bs['accounts_receivable']
    cash_from_sales_current = revenue * CASH_PAYMENT_RATE_SALES
    
    cash_out_purchases_AP = prev_bs['accounts_payable']
    cash_out_purchases_current = cost_materials_to_purchase * CASH_PAYMENT_RATE_PURCHASES
    
    cash_out_personnel = personnel_expenses
    cash_out_external = external_expenses_base + marketing_expense # Full cash out
    cash_out_interest_fixed = interest_fixed_debt # Pay fixed interest
    cash_out_income_tax = prev_bs['income_tax_payable']
    
    tentative_total_cash_out = (cash_out_purchases_AP + cash_out_purchases_current + 
                                cash_out_personnel + cash_out_external + 
                                cash_out_interest_fixed + cash_out_income_tax)
    
    tentative_cfo = (cash_from_sales_AR + cash_from_sales_current) - tentative_total_cash_out
    
    cfi = -investment_cash_out
    
    # D2. Dividends
    dividends_paid = min(decisions['dividends_amount'], prev_bs['net_income_previous_year'])
    
    debt_repayment = 0
    if year_index == DEBT_REPAYMENT_YEAR:
        debt_repayment = min(prev_bs['long_term_debt'], EXISTING_DEBT)
        log_debug(f"[{year_label}] DEBT REPAYMENT: {debt_repayment}")
        
    cff = -dividends_paid - debt_repayment
    
    # D3. Overdraft Interest Calculation (AUDIT FIX E2)
    opening_net_cash = prev_bs['cash'] - prev_bs['bank_overdraft']
    tentative_cash_flow = tentative_cfo + cfi + cff
    tentative_ending_net_cash = opening_net_cash + tentative_cash_flow
    
    if tentative_ending_net_cash < 0:
        tentative_overdraft = -tentative_ending_net_cash
        interest_overdraft = (tentative_overdraft * INTEREST_RATE_OVERDRAFT) / (1.0 - INTEREST_RATE_OVERDRAFT)
        log_debug(f"[{year_label}] Overdraft interest loop: {interest_overdraft}")
    
    # --- E. FINAL IS, CF, and BS ---
    
    # E1. Final Income Statement
    financial_charges = interest_fixed_debt + interest_overdraft
    ebt = ebit - financial_charges # ebit was calculated before any interest
    
    # E2. Income Tax (AUDIT FIX E3)
    income_tax = max(0, math.floor(ebt * TAX_RATE / 1000) * 1000)
    net_income = ebt - income_tax
    
    # E3. Final Cash Flow
    cash_out_interest = financial_charges # This is the full cash out for interest
    total_cash_out_operating = (cash_out_purchases_AP + cash_out_purchases_current + 
                                cash_out_personnel + cash_out_external + 
                                cash_out_interest + cash_out_income_tax)
    
    cfo = (cash_from_sales_AR + cash_from_sales_current) - total_cash_out_operating
    net_cash_flow = cfo + cfi + cff
    ending_net_cash = opening_net_cash + net_cash_flow
    
    # Populate IS_DATA (for display)
    is_data['Revenue - Sales'] = revenue
    is_data['Revenue - Inventory Change (E-B)'] = change_in_finished_inv
    is_data['Operating Revenue'] = operating_revenue
    is_data['Expenses - Material Expense'] = material_expense
    is_data['Expenses - External (Rent, Tax...)'] = external_expenses_base
    is_data['Expenses - Marketing'] = marketing_expense
    is_data['Expenses - Personnel'] = personnel_expenses
    is_data['Expenses - Depreciation'] = depreciation_expense
    is_data['Operating Expense'] = operating_expense
    is_data['EBIT'] = ebit
    is_data['Expenses - Financial Charges'] = financial_charges
    is_data['Earnings Before Tax (EBT)'] = ebt
    is_data['Taxes'] = income_tax
    is_data['Net Income'] = net_income
    
    # Populate CF_DATA (for display)
    cf_data['Opening Balance (net)'] = opening_net_cash
    cf_data['Operating Cash Flow (CFO)'] = cfo
    cf_data['... Cash In (Y-1)'] = cash_from_sales_AR
    cf_data['... Cash In (Y)'] = cash_from_sales_current
    cf_data['... Cash Out (Operating)'] = -total_cash_out_operating 
    cf_data['Cash Out - Personnel'] = -cash_out_personnel
    cf_data['Cash Out - External & Mktg'] = -(external_expenses_base + marketing_expense)
    cf_data['Cash Out - Interest'] = -cash_out_interest
    cf_data['Cash Out - Taxes (from Y-1)'] = -cash_out_income_tax
    cf_data['Cash Out - Purchases (Current 90%)'] = -cash_out_purchases_current
    cf_data['Cash Out - Payables (from Y-1)'] = -cash_out_purchases_AP
    cf_data['Investing Cash Flow (CFI)'] = cfi
    cf_data['Financing Cash Flow (CFF)'] = cff
    cf_data['Net Change in Cash'] = net_cash_flow
    cf_data['Ending Balance (net)'] = ending_net_cash
    
    # E4. Final Balance Sheet
    if ending_net_cash >= 0:
        bs_internal['cash'] = ending_net_cash
        bs_internal['bank_overdraft'] = 0.0
    else:
        bs_internal['cash'] = 0.0
        bs_internal['bank_overdraft'] = -ending_net_cash
        
    bs_internal['accounts_receivable'] = revenue * (1.0 - CASH_PAYMENT_RATE_SALES)
    bs_internal['inventory_materials_units'] = ending_mat_units
    bs_internal['inventory_materials_value'] = ending_inv_mat_val
    bs_internal['inventory_finished_units'] = ending_inv_units
    bs_internal['inventory_finished_value'] = ending_inv_fin_val
    
    bs_internal['gross_fixed_assets'] = prev_bs['gross_fixed_assets'] + investment_cash_out
    bs_internal['accumulated_depreciation'] = prev_bs['accumulated_depreciation'] + depreciation_expense
    net_fixed_assets = bs_internal['gross_fixed_assets'] - bs_internal['accumulated_depreciation']
    
    bs_internal['accounts_payable'] = cost_materials_to_purchase * (1.0 - CASH_PAYMENT_RATE_PURCHASES)
    bs_internal['income_tax_payable'] = income_tax
    bs_internal['long_term_debt'] = prev_bs['long_term_debt'] - debt_repayment
    
    bs_internal['capital_stock'] = prev_bs['capital_stock']
    retained_from_previous = prev_bs['net_income_previous_year'] - dividends_paid
    bs_internal['retained_earnings'] = prev_bs['retained_earnings'] + retained_from_previous
    bs_internal['net_income_previous_year'] = net_income
    
    # Populate BS_DATA (for display)
    bs_data['Fixed Assets - Equipment (Net)'] = net_fixed_assets
    bs_data['Current Assets - Material Inv.'] = bs_internal['inventory_materials_value']
    bs_data['Current Assets - Finished Inv.'] = bs_internal['inventory_finished_value']
    bs_data['Current Assets - Receivables (AR)'] = bs_internal['accounts_receivable']
    bs_data['Current Assets - Cash'] = bs_internal['cash']
    total_current_assets = bs_internal['inventory_materials_value'] + bs_internal['inventory_finished_value'] + bs_internal['accounts_receivable'] + bs_internal['cash']
    total_assets = net_fixed_assets + total_current_assets
    bs_data['TOTAL ASSETS'] = total_assets
    
    bs_data['Equity - Capital Stock'] = bs_internal['capital_stock']
    bs_data['Equity - Retained Earnings'] = bs_internal['retained_earnings']
    bs_data['Equity - Net Income (Y)'] = bs_internal['net_income_previous_year']
    total_equity = bs_internal['capital_stock'] + bs_internal['retained_earnings'] + bs_internal['net_income_previous_year']
    bs_data['Total Equity'] = total_equity
    
    bs_data['Liabilities - Long-Term Debt'] = bs_internal['long_term_debt']
    bs_data['Liabilities - Bank Overdraft (ST)'] = bs_internal['bank_overdraft']
    bs_data['Liabilities - Payables (AP)'] = bs_internal['accounts_payable']
    bs_data['Liabilities - Taxes Payable'] = bs_internal['income_tax_payable']
    total_current_liabilities = bs_internal['bank_overdraft'] + bs_internal['accounts_payable'] + bs_internal['income_tax_payable']
    total_liabilities = bs_internal['long_term_debt'] + total_current_liabilities
    bs_data['Total Liabilities'] = total_liabilities
    bs_data['TOTAL LIABILITIES + EQUITY'] = total_equity + total_liabilities
    
    # Metrics
    bs_data['METRIC_ROE'] = net_income / total_equity if total_equity != 0 else 0
    bs_data['METRIC_Current_Ratio'] = total_current_assets / total_current_liabilities if total_current_liabilities > 0 else 0

    # --- F. AGING & ITERATION (AUDIT FIX E4) ---
    next_lines = {}
    lines_scrapped = prev_lines['age_4'] # These are the 4-year-old lines to be scrapped
    next_lines['age_4'] = prev_lines['age_3']
    next_lines['age_3'] = prev_lines['age_2']
    next_lines['age_2'] = prev_lines['age_1']
    next_lines['age_1'] = prev_lines['age_0'] 
    next_lines['age_0'] = new_lines_needed
    
    if lines_scrapped > 0:
        log_debug(f"[{year_label}] {lines_scrapped} lines (4-yr-old) were scrapped at END of year.")

    # Data for this year's display
    lines_flow_data['park_composition_start'] = prev_lines # Show state at start of year
    lines_flow_data['opening_lines'] = total_existing_lines
    lines_flow_data['opening_capacity'] = existing_line_capacity
    lines_flow_data['purchased_this_year'] = new_lines_needed
    lines_flow_data['capacity_purchased'] = new_lines_needed * UNITS_PER_LINE
    lines_flow_data['capacity_during_year'] = total_line_capacity
    lines_flow_data['scrapped_this_year'] = lines_scrapped
    lines_flow_data['capacity_scrapped'] = lines_scrapped * UNITS_PER_LINE
    lines_flow_data['ending_lines'] = total_existing_lines + new_lines_needed - lines_scrapped
    lines_flow_data['capacity_next_year'] = lines_flow_data['ending_lines'] * UNITS_PER_LINE
    lines_flow_data['park_composition_end'] = next_lines # EOY state for expander
    
    # Inventory Flow Data
    inventory_flow_data['fg_opening'] = opening_inv_units
    inventory_flow_data['fg_produced'] = production_volume
    inventory_flow_data['fg_sold'] = actual_sales_volume
    inventory_flow_data['fg_ending'] = ending_inv_units
    inventory_flow_data['mat_opening'] = materials_from_stock
    inventory_flow_data['mat_purchased'] = materials_to_purchase
    inventory_flow_data['mat_used'] = materials_needed
    inventory_flow_data['mat_ending'] = ending_mat_units
    
    next_workers = current_workers
    
    log_debug(f"[{year_label}] END Year Loop.")
    
    return cf_data, is_data, bs_data, bs_internal, lines_flow_data, inventory_flow_data, next_lines, next_workers


# --- 4. USER INTERFACE (Streamlit) ---

st.set_page_config(layout="wide")
st.title("Financial Simulator (Excel Layout) - v25 (UI Fix)")
st.write("Model based on the ACC (EMBA) case. This version incorporates fixes from the auditor's report.")

# --- Sidebar for Inputs ---
st.sidebar.header("Decision Parameters")
st.sidebar.markdown("Use the expanders to set decisions year by year. The simulation updates automatically.")

prod_volume_options = list(range(100000, 400001, 10000))
all_decisions = {}
prior_ni = INITIAL_BALANCE_SHEET['net_income_previous_year'] # Start with 90k

with st.sidebar.expander("Year X7 (Mandatory)", expanded=True):
    dec_X7 = {}
    dec_X7['price'] = st.number_input("1.1 Unit Selling Price (CU)", 
        min_value=36.0, max_value=48.0, value=42.0, step=1, key='price_X7')
    dec_X7['prod_volume'] = st.select_slider("1.2 Target Production Volume (units)",
        options=prod_volume_options, value=100000, key='prod_X7',
        help="The simulator will automatically buy/hire to meet this target.")
    dec_X7['percent_sold_display'] = st.slider("% of Available Stock Sold",
        min_value=80.0, max_value=100.0, value=100.0, step=1.0, format="%.0f%%", key='sold_X7',
        help="Simulates demand. 100% = you sell all available stock (opening + produced).")
    dec_X7['percent_sold'] = dec_X7['percent_sold_display'] / 100.0
    dec_X7['marketing_pct'] = st.slider("4.1 Marketing Budget (% of Total Costs)",
        min_value=1.0, max_value=15.0, value=10.0, step=0.1, key='mktg_X7',
        help="Calculated as % of Total Costs (Material Exp + Personnel + External + Depr).") / 100.0
    dec_X7['dividends_amount'] = st.number_input("5.1 Dividends Paid (Year X7 only)",
        min_value=0.0, max_value=90000.0, value=12500.0, step=1000.0, key='div_X7',
        help="Paid from the 90k CU profit from Y6. Capped at 90,000.")
    all_decisions['X7'] = dec_X7

# --- Per-Year Inputs (v21) ---
def create_year_sidebar(year_label, prev_year_label, default_decisions):
    with st.sidebar.expander(f"Year {year_label} (default = {prev_year_label})"):
        dec = {}
        dec['price'] = st.number_input("1.1 Unit Selling Price (CU)", 
            min_value=30.0, max_value=100.0, value=default_decisions['price'], step=0.5, key=f'price_{year_label}')
        dec['prod_volume'] = st.select_slider("1.2 Target Production Volume (units)",
            options=prod_volume_options, value=default_decisions['prod_volume'], key=f'prod_{year_label}')
        dec['percent_sold_display'] = st.slider("% of Available Stock Sold",
            min_value=80.0, max_value=100.0, value=default_decisions['percent_sold_display'], step=1.0, format="%.0f%%", key=f'sold_{year_label}')
        dec['percent_sold'] = dec['percent_sold_display'] / 100.0
        dec['marketing_pct'] = st.slider("4.1 Marketing Budget (% of Total Costs)",
            min_value=1.0, max_value=15.0, value=default_decisions['marketing_pct']*100.0, step=0.1, key=f'mktg_{year_label}',
            help="Calculated as % of Total Costs (Material Exp + Personnel + External + Depr).") / 100.0
        dec['dividends_amount'] = st.number_input(f"Dividends Paid (Year {year_label})",
            min_value=0.0, value=0.0, step=1000.0, key=f'div_amt_{year_label}',
            help="Amount to pay from *prior year's* Net Income. Will be automatically capped at the available amount.")
        return dec

all_decisions['X8'] = create_year_sidebar('X8', 'X7', dec_X7)
all_decisions['X9'] = create_year_sidebar('X9', 'X8', all_decisions['X8'])
all_decisions['X10'] = create_year_sidebar('X10', 'X9', all_decisions['X9'])
all_decisions['X11'] = create_year_sidebar('X11', 'X10', all_decisions['X10'])

st.sidebar.divider()
st.sidebar.info("App created by Gemini (v25 - UI & Lifecycle Fix). The simulation runs automatically.")

# --- Main Display ---
# App is now DYNAMIC. No button, just run the simulation every time.

log_debug("--- STARTING DYNAMIC SIMULATION RUN ---")
results_cf, results_is, results_bs, results_lines, results_inventory = {}, {}, {}, {}, {}

prev_bs = INITIAL_BALANCE_SHEET.copy()
prev_lines = INITIAL_LINE_AGES.copy()
prev_workers = INITIAL_WORKERS

for year_index in range(1, 6):
    year_label = f"X{6+year_index}"
    decisions = all_decisions[year_label]
    
    cf_data, is_data, bs_data, bs_internal, lines_data, inv_data, \
    next_lines, next_workers = run_one_year(
        year_label, year_index, prev_bs, prev_lines, prev_workers, decisions
    )
    
    results_cf[year_label] = cf_data
    results_is[year_label] = is_data
    results_bs[year_label] = bs_data
    results_lines[year_label] = lines_data
    results_inventory[year_label] = inv_data
    
    prev_bs = bs_internal.copy()
    prev_lines = next_lines.copy()
    prev_workers = next_workers

log_debug("--- SIMULATION COMPLETE, POPULATING TABS ---")

# --- NEW: Year Selector as Tabs ---
tab_names = ['X6', 'X7', 'X8', 'X9', 'X10', 'X11']
tabs = st.tabs([f" **{name}** " for name in tab_names])

# Helper function for clean display
def show_item(label, value, is_total=False, is_sub=False, is_unit=False, is_negative=False, indent_level=1):
    if value is None:
        value_str = "n/a"
    else:
        if is_unit:
            value_str = f"{value:,.0f}"
        else:
            value_kcu = value / 1000.0
            value_str = f"{value_kcu:,.1f}"
            if is_negative and value_kcu != 0: # Show (value) for negatives
                value_str = f"({abs(value_kcu):,.1f})" 
        
    label_style = "font-weight: bold;" if is_total else ""
    indent_px = 20 * indent_level if is_sub else 0
    indent = f"padding-left: {indent_px}px;"
    
    st.write(f"""
    <div style='display: flex; justify-content: space-between; border-bottom: 1px solid #eee; padding: 4px 0; {indent}'>
        <span style='color: #444; {label_style}'>{label}</span> 
        <b style='{label_style}'>{value_str}</b>
    </div>
    """, unsafe_allow_html=True)

# Function to display the data for a given year
def display_year_data(selected_year, cf_display, is_display, bs_data, lines_flow_data, inv_display, is_static=False):
    """Renders all the data for a specific year tab."""
    
    st.header(f"Financial Statement Projection - Year {selected_year}")
    if is_static:
        st.info("Displaying Initial State at the end of Year X6 (Start of Simulation).")
    else:
        st.info(f"Displaying simulated results for year **{selected_year}**. All figures in thousands of CU (kCU).")

    # --- Key Metrics Dashboard ---
    st.divider()
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.metric(label="Net Income (kCU)", value=f"{is_display['Net Income']/1000:,.1f}" if is_display['Net Income'] is not None else "n/a")
    with m_col2:
        st.metric(label="Ending Cash (net) (kCU)", value=f"{cf_display['Ending Balance (net)']/1000:,.1f}" if cf_display['Ending Balance (net)'] is not None else "n/a")
    with m_col3:
        st.metric(label="Return on Equity (ROE)", value=f"{bs_data['METRIC_ROE']:.1%}" if bs_data.get('METRIC_ROE') is not None else "n/a")
    with m_col4:
        st.metric(label="Current Ratio (Liquidity)", value=f"{bs_data['METRIC_Current_Ratio']:.2f}" if bs_data.get('METRIC_Current_Ratio') is not None else "n/a")
    st.divider()
    
    # --- 3-Column Display (Excel-style) ---
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Cash Flow Budget (kCU)")
        show_item("Opening Balance (net)", cf_display['Opening Balance (net)'])
        show_item("Operating Cash Flow (CFO)", cf_display['Operating Cash Flow (CFO)'], is_total=True)
        show_item("... Cash In (Y-1)", cf_display['... Cash In (Y-1)'], is_sub=True, indent_level=1)
        show_item("... Cash In (Y)", cf_display['... Cash In (Y)'], is_sub=True, indent_level=1)
        
        show_item("... Cash Out (Operating)", cf_display['... Cash Out (Operating)'], is_sub=True, is_negative=True, indent_level=1)
        show_item("... ... Personnel", cf_display.get('Cash Out - Personnel'), is_sub=True, is_negative=True, indent_level=2)
        show_item("... ... External & Mktg", cf_display.get('Cash Out - External & Mktg'), is_sub=True, is_negative=True, indent_level=2)
        show_item("... ... Interest", cf_display.get('Cash Out - Interest'), is_sub=True, is_negative=True, indent_level=2)
        show_item("... ... Taxes (from Y-1)", cf_display.get('Cash Out - Taxes (from Y-1)'), is_sub=True, is_negative=True, indent_level=2)
        
        st.markdown("<div style='padding-left: 40px; color: #444; font-size: 14px;'><b>... ... Cash Out for Purchases:</b></div>", unsafe_allow_html=True)
        show_item("... ... ... Purchases (90%)", cf_display.get('Cash Out - Purchases (Current 90%)'), is_sub=True, is_negative=True, indent_level=3)
        show_item("... ... ... Payables (from Y-1)", cf_display.get('Cash Out - Payables (from Y-1)'), is_sub=True, is_negative=True, indent_level=3)

        show_item("Investing Cash Flow (CFI)", cf_display['Investing Cash Flow (CFI)'], is_total=True)
        show_item("Financing Cash Flow (CFF)", cf_display['Financing Cash Flow (CFF)'], is_total=True)
        st.divider()
        show_item("Net Change in Cash", cf_display['Net Change in Cash'])
        show_item("Ending Balance (net)", cf_display['Ending Balance (net)'], is_total=True)
        if cf_display['Ending Balance (net)'] is not None and cf_display['Ending Balance (net)'] < 0:
            st.warning(f"Bank Overdraft: {cf_display['Ending Balance (net)']/1000:,.1f} kCU")

    with col2:
        st.subheader("Income Statement (kCU)")
        st.markdown("**Revenue**")
        show_item("Sales", is_display['Revenue - Sales'])
        show_item("Inventory Change (E-B)", is_display['Revenue - Inventory Change (E-B)'])
        show_item("Total Operating Revenue", is_display.get('Operating Revenue'), is_total=True)
        st.markdown("**Operating Expenses**")
        show_item("Material Expense", is_display['Expenses - Material Expense'])
        show_item("External (Rent, Tax...)", is_display['Expenses - External (Rent, Tax...)']) 
        show_item("Marketing", is_display['Expenses - Marketing'])
        show_item("Personnel", is_display['Expenses - Personnel'])
        show_item("Depreciation", is_display['Expenses - Depreciation'])
        show_item("Total Operating Expense", is_display.get('Operating Expense'), is_total=True)
        st.divider()
        show_item("EBIT", is_display.get('EBIT'), is_total=True)
        show_item("Financial Charges", is_display['Expenses - Financial Charges'], is_negative=True)
        st.divider()
        show_item("Earnings Before Tax (EBT)", is_display['Earnings Before Tax (EBT)']) 
        show_item("Taxes", is_display['Taxes'], is_negative=True)
        st.divider()
        show_item("Net Income", is_display['Net Income'], is_total=True)

    with col3:
        st.subheader("Balance Sheet (kCU)")
        st.markdown("**Assets**")
        show_item("Equipment (Net)", bs_data['Fixed Assets - Equipment (Net)'])
        show_item("Material Inventory", bs_data['Current Assets - Material Inv.'])
        show_item("Finished Inventory", bs_data['Current Assets - Finished Inv.'])
        show_item("Receivables (AR)", bs_data['Current Assets - Receivables (AR)'])
        show_item("Cash", bs_data['Current Assets - Cash'])
        st.divider()
        show_item("TOTAL ASSETS", bs_data['TOTAL ASSETS'], is_total=True)
        
        st.markdown("**Liabilities & Equity**")
        show_item("Capital Stock", bs_data['Equity - Capital Stock'])
        show_item("Retained Earnings", bs_data['Equity - Retained Earnings'])
        show_item("Net Income (Y)", bs_data['Equity - Net Income (Y)'])
        show_item("Total Equity", bs_data['Total Equity'], is_total=True)
        st.divider()
        show_item("Long-Term Debt", bs_data['Liabilities - Long-Term Debt'])
        show_item("Bank Overdraft (ST)", bs_data['Liabilities - Bank Overdraft (ST)'])
        show_item("Payables (AP)", bs_data['Liabilities - Payables (AP)'])
        show_item("Taxes Payable", bs_data['Liabilities - Taxes Payable'])
        show_item("Total Liabilities", bs_data['Total Liabilities'], is_total=True)
        st.divider()
        show_item("TOTAL LIABILITIES + EQUITY", bs_data['TOTAL LIABILITIES + EQUITY'], is_total=True)
        
        if bs_data['TOTAL ASSETS'] is not None and not math.isclose(bs_data['TOTAL ASSETS'], bs_data['TOTAL LIABILITIES + EQUITY'], rel_tol=1e-3):
            st.error(f"Balance Sheet Unbalanced! A={bs_data['TOTAL ASSETS']/1000:,.1f}k, L+E={bs_data['TOTAL LIABILITIES + EQUITY']/1000:,.1f}k")

    # --- Machine Tracking Section (v23) ---
    st.divider()
    st.subheader(f"Capacity & Asset Lifecycle (Lines) - {selected_year}")

    metric_col1, metric_col2, metric_col3 = st.columns(3)
    next_year_label = f"X{int(selected_year.replace('X',''))+1}"
    
    if is_static:
        # X6 Special Display
        scrapped_in_X7 = lines_flow_data['capacity_scrapped']
        st.metric(label=f"Opening Capacity (Start of {selected_year})", value=f"{lines_flow_data['opening_capacity']:,.0f} units")
        st.metric(label=f"Projected Capacity (Start of X7)", value=f"{lines_flow_data['capacity_next_year']:,.0f} units",
                  delta=f"{-scrapped_in_X7:,.0f} units (To be scrapped in X7)", delta_color="inverse")
        
        with st.expander("View Detailed Machine Park (Start of X6)"):
            park = lines_flow_data['park_composition_start']
            st.write(f"**Lines at 1 Year Old:** `{park.get('age_1', 0)}`")
            st.write(f"**Lines at 2 Years Old:** `{park.get('age_2', 0)}`")
            st.write(f"**Lines at 3 Years Old:** `{park.get('age_3', 0)}`")
            st.write(f"**Lines at 4 Years Old (To be scrapped in X7):** `{park.get('age_4', 0)}`")

    else:
        # X7-X11 Display
        with metric_col1:
            st.metric(label=f"Opening Capacity (Start of {selected_year})", value=f"{lines_flow_data['opening_capacity']:,.0f} units")
        with metric_col2:
            st.metric(label=f"Total Capacity (During {selected_year})", 
                      value=f"{lines_flow_data['capacity_during_year']:,.0f} units",
                      delta=f"{lines_flow_data['capacity_purchased']:,.0f} (Purchased)")
        with metric_col3:
            st.metric(label=f"Opening Capacity (Start of {next_year_label})", 
                      value=f"{lines_flow_data['capacity_next_year']:,.0f} units",
                      delta=f"{-lines_flow_data['capacity_scrapped']:,.0f} (Scrapped EOY)", 
                      delta_color="inverse")

        with st.expander(f"View Detailed Machine Park (End of {selected_year})"):
            park = lines_flow_data['park_composition_end'] # *** FIX: Show EOY state ***
            st.write(f"**Lines at 0 Years Old (New):** `{park.get('age_0', 0)}`")
            st.write(f"**Lines at 1 Year Old:** `{park.get('age_1', 0)}`")
            st.write(f"**Lines at 2 Years Old:** `{park.get('age_2', 0)}`")
            st.write(f"**Lines at 3 Years Old:** `{park.get('age_3', 0)}`")
            st.write(f"**Lines at 4 Years Old (To be scrapped next year):** `{park.get('age_4', 0)}`")


    # --- Inventory Tracking Section ---
    st.divider()
    st.subheader(f"Inventory Flow (Units) - Year {selected_year}")
    
    inv_col1, inv_col2 = st.columns(2)
    
    with inv_col1:
        st.markdown("##### Finished Goods (Units)")
        show_item("Opening Stock", inv_display.get('fg_opening'), is_unit=True)
        show_item("+ Units Produced", inv_display.get('fg_produced'), is_unit=True, is_sub=True, indent_level=1)
        show_item("- Units Sold", inv_display.get('fg_sold'), is_unit=True, is_sub=True, is_negative=True, indent_level=1)
        show_item("Ending Stock", inv_display.get('fg_ending'), is_total=True, is_unit=True)

    with inv_col2:
        st.markdown("##### Raw Materials (Units)")
        show_item("Opening Stock", inv_display.get('mat_opening'), is_unit=True)
        show_item("+ Units Purchased", inv_display.get('mat_purchased'), is_unit=True, is_sub=True, indent_level=1)
        show_item("- Units Used", inv_display.get('mat_used'), is_unit=True, is_sub=True, is_negative=True, indent_level=1)
        show_item("Ending Stock", inv_display.get('mat_ending'), is_total=True, is_unit=True)

# --- Tab for Year X6 (Static) ---
with tabs[0]:
    # (Code to build static X6 data)
    cf_display_X6 = {
        'Opening Balance (net)': None, 'Operating Cash Flow (CFO)': None,
        '... Cash In (Y-1)': None, '... Cash In (Y)': None, 
        '... Cash Out (Operating)': None, 
        'Cash Out - Personnel': None, 'Cash Out - External & Mktg': None,
        'Cash Out - Interest': None, 'Cash Out - Taxes (from Y-1)': None,
        'Cash Out - Purchases (Current 90%)': None, 'Cash Out - Payables (from Y-1)': None,
        'Investing Cash Flow (CFI)': None, 'Financing Cash Flow (CFF)': None,
        'Net Change in Cash': None,
        'Ending Balance (net)': INITIAL_BALANCE_SHEET['cash'] - INITIAL_BALANCE_SHEET['bank_overdraft']
    }
    is_display_X6 = {
        'Revenue - Sales': None, 'Revenue - Inventory Change (E-B)': None,
        'Operating Revenue': None,
        'Expenses - Material Expense': None,
        'Expenses - External (Rent, Tax...)': None, 'Expenses - Marketing': None, 
        'Expenses - Personnel': None, 'Expenses - Depreciation': None,
        'Operating Expense': None, 'EBIT': None,
        'Expenses - Financial Charges': None, 'Earnings Before Tax (EBT)': None,
        'Taxes': None, 'Net Income': INITIAL_BALANCE_SHEET['net_income_previous_year']
    }
    bs_data_X6 = {
        'Fixed Assets - Equipment (Net)': INITIAL_BALANCE_SHEET['gross_fixed_assets'] - INITIAL_BALANCE_SHEET['accumulated_depreciation'],
        'Current Assets - Material Inv.': INITIAL_BALANCE_SHEET['inventory_materials_value'],
        'Current Assets - Finished Inv.': INITIAL_BALANCE_SHEET['inventory_finished_value'],
        'Current Assets - Receivables (AR)': INITIAL_BALANCE_SHEET['accounts_receivable'],
        'Current Assets - Cash': INITIAL_BALANCE_SHEET['cash'],
        'Equity - Capital Stock': INITIAL_BALANCE_SHEET['capital_stock'],
        'Equity - Retained Earnings': INITIAL_BALANCE_SHEET['retained_earnings'],
        'Equity - Net Income (Y)': INITIAL_BALANCE_SHEET['net_income_previous_year'],
        'Liabilities - Long-Term Debt': INITIAL_BALANCE_SHEET['long_term_debt'],
        'Liabilities - Bank Overdraft (ST)': INITIAL_BALANCE_SHEET['bank_overdraft'],
        'Liabilities - Payables (AP)': INITIAL_BALANCE_SHEET['accounts_payable'],
        'Liabilities - Taxes Payable': INITIAL_BALANCE_SHEET['income_tax_payable'],
    }
    current_assets = bs_data_X6['Current Assets - Material Inv.'] + bs_data_X6['Current Assets - Finished Inv.'] + bs_data_X6['Current Assets - Receivables (AR)'] + bs_data_X6['Current Assets - Cash']
    bs_data_X6['TOTAL ASSETS'] = bs_data_X6['Fixed Assets - Equipment (Net)'] + current_assets
    bs_data_X6['Total Equity'] = bs_data_X6['Equity - Capital Stock'] + bs_data_X6['Equity - Retained Earnings'] + bs_data_X6['Equity - Net Income (Y)']
    current_liabilities = bs_data_X6['Liabilities - Bank Overdraft (ST)'] + bs_data_X6['Liabilities - Payables (AP)'] + bs_data_X6['Liabilities - Taxes Payable']
    bs_data_X6['Total Liabilities'] = bs_data_X6['Liabilities - Long-Term Debt'] + current_liabilities
    bs_data_X6['TOTAL LIABILITIES + EQUITY'] = bs_data_X6['Total Equity'] + bs_data_X6['Total Liabilities']
    bs_data_X6['METRIC_ROE'] = 0
    bs_data_X6['METRIC_Current_Ratio'] = current_assets / current_liabilities if current_liabilities > 0 else 0
    
    lines_display_X6_actual = {
        'age_0': 0, 'age_1': INITIAL_LINE_AGES['age_1'], 'age_2': INITIAL_LINE_AGES['age_2'], 
        'age_3': INITIAL_LINE_AGES['age_3'], 'age_4': INITIAL_LINE_AGES['age_4']
    }
    lines_flow_data_X6 = {
        'park_composition_start': lines_display_X6_actual,
        'opening_capacity': sum(INITIAL_LINE_AGES.values()) * UNITS_PER_LINE,
        'capacity_purchased': 0,
        'capacity_during_year': sum(INITIAL_LINE_AGES.values()) * UNITS_PER_LINE,
        'scrapped_this_year': 0, # Nothing is scrapped in X6
        'capacity_scrapped': 0,
        'capacity_next_year': (sum(INITIAL_LINE_AGES.values()) - INITIAL_LINE_AGES['age_4']) * UNITS_PER_LINE,
    }

    inv_display_X6 = {
        'fg_opening': None, 'fg_produced': None, 'fg_sold': None,
        'fg_ending': INITIAL_BALANCE_SHEET['inventory_finished_units'],
        'mat_opening': None, 'mat_purchased': None, 'mat_used': None,
        'mat_ending': INITIAL_BALANCE_SHEET['inventory_materials_units']
    }
    
    display_year_data('X6', cf_display_X6, is_display_X6, bs_data_X6, lines_flow_data_X6, inv_display_X6, is_static=True)

# --- Loop for Dynamic Tabs (X7-X11) ---
for i, year_label in enumerate(tab_names[1:]): # Start from X7
    with tabs[i+1]:
        display_year_data(
            year_label,
            results_cf[year_label],
            results_is[year_label],
            results_bs[year_label],
            results_lines[year_label],
            results_inventory[year_label],
            is_static=False
        )

st.sidebar.info("App created by Gemini (v25 - UI & Lifecycle Fix).")
