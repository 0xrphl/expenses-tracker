"""Modal components for expenses, income, assets, and exchange rates"""
import streamlit as st
from datetime import date
from psycopg2.extras import RealDictCursor

def show_add_expense_modal(cur, conn):
    """Add expense modal"""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### Add Expense")
    with col2:
        if st.button("❌ Close", key="close_expense"):
            if st.session_state.get('show_add_expense'):
                st.session_state.show_add_expense = False
                st.rerun()
    
    # Get categories
    cur.execute("SELECT id, name FROM expense_categories ORDER BY name")
    categories = cur.fetchall()
    category_dict = {cat['name']: cat['id'] for cat in categories}
    
    tab1, tab2 = st.tabs(["Regular Expense", "Extra Expense"])
    
    with tab1:
        with st.form("add_expense_form", clear_on_submit=False):
            amount = st.number_input("Amount (USD)", min_value=0.01, step=0.01, format="%.2f", key="expense_amount")
            category_name = st.selectbox("Category", options=list(category_dict.keys()), key="expense_category")
            description = st.text_input("Description", key="expense_desc")
            expense_date = st.date_input("Date", value=date.today(), key="expense_date")
            
            # Wallet selection
            wallet_source = st.selectbox(
                "Payment Source",
                ["Rafael", "Jessica"],
                key="expense_wallet",
                help="Select which wallet paid this expense"
            )
            
            submitted = st.form_submit_button("Add Expense", use_container_width=True)
            if submitted:
                try:
                    cur.execute("""
                        INSERT INTO expenses (user_id, amount, currency, category_id, description, date, payment_source)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (st.session_state.user_id, amount, 'USD', category_dict[category_name], description, expense_date, wallet_source))
                    conn.commit()
                    st.success("Expense added successfully!")
                    st.session_state.show_add_expense = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding expense: {e}")
                    conn.rollback()
    
    with tab2:
        with st.form("add_extra_expense_form", clear_on_submit=False):
            st.markdown("Add extra/additional expense")
            extra_amount = st.number_input("Amount (USD)", min_value=0.01, step=0.01, format="%.2f", key="extra_expense_amount")
            extra_category = st.selectbox("Category", options=list(category_dict.keys()), key="extra_expense_category")
            extra_description = st.text_input("Description", key="extra_expense_desc")
            extra_date = st.date_input("Date", value=date.today(), key="extra_expense_date")
            
            # Wallet selection for extra expense
            extra_wallet_source = st.selectbox(
                "Payment Source",
                ["Rafael", "Jessica"],
                key="extra_expense_wallet",
                help="Select which wallet paid this expense"
            )
            
            submitted = st.form_submit_button("Add Extra Expense", use_container_width=True)
            if submitted:
                try:
                    cur.execute("""
                        INSERT INTO expenses (user_id, amount, currency, category_id, description, date, payment_source)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (st.session_state.user_id, extra_amount, 'USD', category_dict[extra_category], extra_description, extra_date, extra_wallet_source))
                    conn.commit()
                    st.success("Extra expense added successfully!")
                    st.session_state.show_add_expense = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding expense: {e}")
                    conn.rollback()
        
        # Quick add for fixed expenses due on 30th
        st.markdown("---")
        today = date.today()
        if today.day == 30:
            if st.button("Mark All Fixed Expenses as Due", use_container_width=True, key="mark_due_30th"):
                try:
                    current_month = today.strftime('%Y-%m')
                    cur.execute("""
                        UPDATE fixed_expenses 
                        SET is_paid = FALSE 
                        WHERE user_id = %s AND month_year = %s
                    """, (st.session_state.user_id, current_month))
                    conn.commit()
                    st.success("All fixed expenses marked as due for this month!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
                    conn.rollback()
        else:
            st.info(f"Fixed expenses are due on the 30th. Today is the {today.day}th.")

def show_add_income_modal(cur, conn, current_rate):
    """Add income modal"""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### Add Income")
    with col2:
        if st.button("❌ Close", key="close_income"):
            if st.session_state.get('show_add_income'):
                st.session_state.show_add_income = False
                st.rerun()
    
    # Tabs for different income types
    tab1, tab2, tab3 = st.tabs(["Standard Income", "Extra Income", "Quick Add"])
    
    with tab1:
        with st.form("add_income_form", clear_on_submit=False):
            income_type = st.selectbox("Income Source", ["Income 1 (Rafael)", "Income 2"], key="income_type_std")
            
            if income_type == "Income 1 (Rafael)":
                multiplier = 2300
            else:
                multiplier = 3000
            
            st.info(f"Multiplier: {multiplier} | Base COP: {4400 * multiplier:,.2f}")
            
            income_date = st.date_input("Date", value=date.today(), key="income_date_std")
            threshold = st.number_input("Threshold", value=4400.0, step=0.01, key="threshold_std")
            
            submitted = st.form_submit_button("Add Income", use_container_width=True)
            if submitted:
                try:
                    # Calculate income
                    amount_cop = 4400 * multiplier
                    
                    if current_rate < threshold:
                        calculated_rate = threshold
                        amount_usd = amount_cop / threshold
                    else:
                        calculated_rate = current_rate
                        amount_usd = amount_cop / current_rate
                    
                    # Determine payment source based on income type
                    payment_source = "Rafael" if income_type == "Income 1 (Rafael)" else "Jessica"
                    
                    cur.execute("""
                        INSERT INTO income (user_id, name, amount_cop, exchange_rate, amount_usd, date, payment_source)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (st.session_state.user_id, income_type, amount_cop, calculated_rate, amount_usd, income_date, payment_source))
                    conn.commit()
                    st.success(f"Income added! Amount: ${amount_usd:,.2f} USD (Rate: {calculated_rate:,.2f})")
                    st.session_state.show_add_income = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding income: {e}")
                    conn.rollback()
    
    with tab2:
        with st.form("add_extra_income_form", clear_on_submit=False):
            st.markdown("Add extra/additional income")
            extra_name = st.text_input("Income Name", placeholder="e.g., Bonus, Freelance, etc.", key="extra_name")
            extra_amount_usd = st.number_input("Amount (USD)", min_value=0.01, step=0.01, format="%.2f", key="extra_amount")
            extra_date = st.date_input("Date", value=date.today(), key="extra_date")
            
            # Payment source for extra income
            extra_income_wallet = st.selectbox(
                "Income Source",
                ["Rafael", "Jessica"],
                key="extra_income_wallet",
                help="Select which wallet this income belongs to"
            )
            
            submitted = st.form_submit_button("Add Extra Income", use_container_width=True)
            if submitted:
                try:
                    cur.execute("""
                        INSERT INTO income (user_id, name, amount_cop, exchange_rate, amount_usd, date, payment_source)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (st.session_state.user_id, extra_name, 0, current_rate, extra_amount_usd, extra_date, extra_income_wallet))
                    conn.commit()
                    st.success(f"Extra income added! Amount: ${extra_amount_usd:,.2f} USD")
                    st.session_state.show_add_income = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding income: {e}")
                    conn.rollback()
    
    with tab3:
        st.markdown("Quick add based on payment dates")
        today = date.today()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Add Rafael Payment (25th)", use_container_width=True, key="quick_rafael"):
                try:
                    amount_cop = 4400 * 2300
                    if current_rate < 4400:
                        calculated_rate = 4400
                        amount_usd = amount_cop / 4400
                    else:
                        calculated_rate = current_rate
                        amount_usd = amount_cop / current_rate
                    cur.execute("""
                        INSERT INTO income (user_id, name, amount_cop, exchange_rate, amount_usd, date, payment_source)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (st.session_state.user_id, 'Income 1 (Rafael)', amount_cop, calculated_rate, amount_usd, today, 'Rafael'))
                    conn.commit()
                    st.success(f"Rafael payment added! ${amount_usd:,.2f} USD")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
                    conn.rollback()
            if today.day != 25:
                st.caption(f"⚠️ Rafael payment is due on the 25th. Today is the {today.day}th.")
        with col2:
            if st.button("Add Jessica Payment (20th)", use_container_width=True, key="quick_jessica"):
                try:
                    amount_cop = 4400 * 3000
                    if current_rate < 4400:
                        calculated_rate = 4400
                        amount_usd = amount_cop / 4400
                    else:
                        calculated_rate = current_rate
                        amount_usd = amount_cop / current_rate
                    cur.execute("""
                        INSERT INTO income (user_id, name, amount_cop, exchange_rate, amount_usd, date, payment_source)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (st.session_state.user_id, 'Income 2', amount_cop, calculated_rate, amount_usd, today, 'Jessica'))
                    conn.commit()
                    st.success(f"Jessica payment added! ${amount_usd:,.2f} USD")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
                    conn.rollback()
            if today.day != 20:
                st.caption(f"⚠️ Jessica payment is due on the 20th. Today is the {today.day}th.")

def show_add_asset_modal(cur, conn):
    """Add asset modal"""
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### Add Asset")
    with col2:
        if st.button("❌ Close", key="close_asset"):
            if st.session_state.get('show_add_asset'):
                st.session_state.show_add_asset = False
                st.rerun()
    
    with st.form("add_asset_form", clear_on_submit=False):
        name = st.text_input("Asset Name", key="asset_name")
        asset_type = st.text_input("Type", placeholder="e.g., savings, investment", key="asset_type")
        value = st.number_input("Value (USD)", min_value=0.01, step=0.01, format="%.2f", key="asset_value")
        description = st.text_area("Description", key="asset_desc")
        asset_date = st.date_input("Date", value=date.today(), key="asset_date")
        
        submitted = st.form_submit_button("Add Asset", use_container_width=True)
        if submitted:
            try:
                cur.execute("""
                    INSERT INTO assets (user_id, name, type, value, currency, description, date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (st.session_state.user_id, name, asset_type, value, 'USD', description, asset_date))
                conn.commit()
                st.success("Asset added successfully!")
                st.session_state.show_add_asset = False
                st.rerun()
            except Exception as e:
                st.error(f"Error adding asset: {e}")
                conn.rollback()

def show_exchange_rates_modal(cur, conn):
    """Exchange rates management modal"""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### Manage Exchange Rates")
    with col2:
        if st.button("❌ Close", key="close_rates"):
            if st.session_state.get('show_exchange_rates'):
                st.session_state.show_exchange_rates = False
                st.rerun()
    
    # Add new rate
    with st.form("add_rate_form", clear_on_submit=False):
        st.markdown("#### Add New Rate")
        rate = st.number_input("USD/COP Rate", min_value=0.01, step=0.01, format="%.2f", value=4200.0, key="new_rate")
        rate_date = st.date_input("Date", value=date.today(), key="rate_date")
        notes = st.text_input("Notes", key="rate_notes")
        
        submitted = st.form_submit_button("Add Rate", use_container_width=True)
        if submitted:
            try:
                # Deactivate all previous rates
                cur.execute("UPDATE exchange_rates SET is_active = FALSE WHERE is_active = TRUE")
                
                # Insert new rate
                cur.execute("""
                    INSERT INTO exchange_rates (rate, date, is_active, notes)
                    VALUES (%s, %s, TRUE, %s)
                """, (rate, rate_date, notes))
                conn.commit()
                st.success("Exchange rate added and activated!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
                conn.rollback()
    
    # List all rates
    st.markdown("#### All Exchange Rates")
    try:
        cur.execute("""
            SELECT * FROM exchange_rates 
            ORDER BY date DESC, created_at DESC
        """)
        rates = cur.fetchall()
        
        if rates:
            for rate in rates:
                col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])
                with col1:
                    st.write(f"**{rate['rate']:,.2f}**")
                with col2:
                    st.write(rate['date'].strftime('%Y-%m-%d'))
                with col3:
                    st.write("✅ Active" if rate['is_active'] else "❌ Inactive")
                with col4:
                    st.write(rate['notes'] or '-')
                with col5:
                    if not rate['is_active']:
                        if st.button("Activate", key=f"activate_{rate['id']}"):
                            try:
                                cur.execute("UPDATE exchange_rates SET is_active = FALSE")
                                cur.execute("UPDATE exchange_rates SET is_active = TRUE WHERE id = %s", (rate['id'],))
                                conn.commit()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                                conn.rollback()
                st.divider()
        else:
            st.info("No exchange rates found")
    except Exception as e:
        st.error(f"Error loading exchange rates: {e}")

