"""Dashboard main view"""
import streamlit as st
from psycopg2.extras import RealDictCursor
from datetime import date
from modules.database import get_db_connection
from modules.charts import show_charts
from modules.modals import show_add_expense_modal, show_add_income_modal, show_exchange_rates_modal
from modules.fixed_expenses import show_fixed_expenses_modal
from modules.forecasts import show_forecasts
from modules.calendar import show_calendar_widget
from modules.assets import show_assets_modal

def dashboard():
    """Main dashboard"""
    st.title(f"💰 Expenses Tracker - Welcome, {st.session_state.username}")
    
    # Logout button
    if st.button("Logout", type="secondary"):
        st.session_state.authenticated = False
        st.session_state.user_id = None
        st.session_state.username = None
        st.rerun()
    
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get current exchange rate
        cur.execute("""
            SELECT rate FROM exchange_rates 
            WHERE is_active = TRUE 
            ORDER BY date DESC LIMIT 1
        """)
        exchange_rate_data = cur.fetchone()
        current_rate = exchange_rate_data['rate'] if exchange_rate_data else 4200
        
        # Display exchange rate
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"### Current USD/COP Exchange Rate: **{current_rate:,.2f}**")
        with col2:
            if st.button("Manage Rates", key="btn_manage_rates"):
                if not st.session_state.get('show_exchange_rates'):
                    st.session_state.show_exchange_rates = True
                    st.rerun()
        
        # Statistics
        st.markdown("---")
        st.markdown("### Statistics")
        
        # Get totals - show both incomes for all users (general dashboard)
        cur.execute("""
            SELECT COALESCE(SUM(amount_usd), 0) as total_income
            FROM income
        """)
        total_income = cur.fetchone()['total_income'] or 0
        
        # Get individual income totals by wallet
        cur.execute("""
            SELECT 
                payment_source,
                COALESCE(SUM(amount_usd), 0) as total
            FROM income
            WHERE payment_source IN ('Rafael', 'Jessica')
            GROUP BY payment_source
        """)
        income_by_wallet = {row['payment_source']: row['total'] for row in cur.fetchall()}
        
        # Get income by name for display
        cur.execute("""
            SELECT name, COALESCE(SUM(amount_usd), 0) as total
            FROM income
            GROUP BY name
        """)
        income_breakdown = {row['name']: row['total'] for row in cur.fetchall()}
        
        # Expenses by wallet
        cur.execute("""
            SELECT 
                payment_source,
                COALESCE(SUM(amount), 0) as total
            FROM expenses 
            WHERE user_id = %s AND payment_source IN ('Rafael', 'Jessica')
            GROUP BY payment_source
        """, (st.session_state.user_id,))
        expenses_by_wallet = {row['payment_source']: row['total'] for row in cur.fetchall()}
        
        # Total expenses
        cur.execute("""
            SELECT COALESCE(SUM(amount), 0) as total_expenses
            FROM expenses WHERE user_id = %s
        """, (st.session_state.user_id,))
        total_expenses = cur.fetchone()['total_expenses'] or 0
        
        cur.execute("""
            SELECT COALESCE(SUM(value), 0) as total_assets
            FROM assets WHERE user_id = %s
        """, (st.session_state.user_id,))
        total_assets = cur.fetchone()['total_assets'] or 0
        
        # Calculate wallet balances
        rafael_income = income_by_wallet.get('Rafael', 0)
        jessica_income = income_by_wallet.get('Jessica', 0)
        rafael_expenses = expenses_by_wallet.get('Rafael', 0)
        jessica_expenses = expenses_by_wallet.get('Jessica', 0)
        rafael_balance = rafael_income - rafael_expenses
        jessica_balance = jessica_income - jessica_expenses
        total_balance = rafael_balance + jessica_balance
        
        # Display income breakdown
        income1_total = income_breakdown.get('Income 1 (Rafael)', 0)
        income2_total = income_breakdown.get('Income 2', 0)
        
        st.markdown("#### 💰 Wallet Balances")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Rafael Balance", f"${rafael_balance:,.2f}", 
                     delta=f"Income: ${rafael_income:,.2f} | Expenses: ${rafael_expenses:,.2f}")
        with col2:
            st.metric("Jessica Balance", f"${jessica_balance:,.2f}", 
                     delta=f"Income: ${jessica_income:,.2f} | Expenses: ${jessica_expenses:,.2f}")
        with col3:
            delta_color = "normal" if total_balance >= 0 else "inverse"
            st.metric("Total Balance", f"${total_balance:,.2f}", delta=None)
        
        st.markdown("---")
        st.markdown("#### 📊 Overall Statistics")
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Income", f"${total_income:,.2f}", delta=None)
        with col2:
            st.metric("Income 1 (Rafael)", f"${income1_total:,.2f}", delta=None)
        with col3:
            st.metric("Income 2 (Jessica)", f"${income2_total:,.2f}", delta=None)
        with col4:
            st.metric("Total Expenses", f"${total_expenses:,.2f}", delta=None)
        with col5:
            delta_color = "normal" if total_balance >= 0 else "inverse"
            st.metric("Net Balance", f"${total_balance:,.2f}", delta=None)
        
        # Payment dates info
        today = date.today()
        st.info(f"📅 Payment Schedule: Jessica (20th) | Rafael (25th) | Fixed Expenses (30th) | Today: {today.day}")
        
        # Show forecasts
        show_forecasts(cur, st.session_state.user_id, current_rate)
        
        # Show calendar widget
        show_calendar_widget(cur, st.session_state.user_id)
        
        # Action buttons
        st.markdown("---")
        st.markdown("### Quick Actions")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("➕ Add Expense", use_container_width=True, key="btn_add_expense"):
                if not st.session_state.get('show_add_expense'):
                    st.session_state.show_add_expense = True
                    st.rerun()
        with col2:
            if st.button("💰 Add Income", use_container_width=True, key="btn_add_income"):
                if not st.session_state.get('show_add_income'):
                    st.session_state.show_add_income = True
                    st.rerun()
        with col3:
            if st.button("💎 Assets & Liabilities", use_container_width=True, key="btn_add_asset"):
                if not st.session_state.get('show_add_asset'):
                    st.session_state.show_add_asset = True
                    st.rerun()
        with col4:
            if st.button("🏠 Fixed Expenses", use_container_width=True, key="btn_fixed_expenses"):
                if not st.session_state.get('show_fixed_expenses'):
                    st.session_state.show_fixed_expenses = True
                    st.rerun()
        
        # Handle modals - show them before closing connection
        if st.session_state.get('show_add_expense'):
            show_add_expense_modal(cur, conn)
        if st.session_state.get('show_add_income'):
            show_add_income_modal(cur, conn, current_rate)
        if st.session_state.get('show_add_asset'):
            show_assets_modal(cur, conn)
        if st.session_state.get('show_fixed_expenses'):
            show_fixed_expenses_modal(cur, conn)
        if st.session_state.get('show_exchange_rates'):
            show_exchange_rates_modal(cur, conn)
        
        # Charts and Recent transactions (only show if no modals are open)
        if not any([
            st.session_state.get('show_add_expense'),
            st.session_state.get('show_add_income'),
            st.session_state.get('show_add_asset'),
            st.session_state.get('show_fixed_expenses'),
            st.session_state.get('show_exchange_rates')
        ]):
            # Show charts
            show_charts(cur, st.session_state.user_id)
            
            # Recent transactions
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Recent Expenses")
                
                # Filter options
                filter_type = st.radio(
                    "Filter:",
                    ["All", "Regular", "Fixed Expenses"],
                    horizontal=True,
                    key="expense_filter"
                )
                
                if filter_type == "All":
                    query = """
                        SELECT e.*, ec.name as category_name
                        FROM expenses e
                        LEFT JOIN expense_categories ec ON e.category_id = ec.id
                        WHERE e.user_id = %s
                        ORDER BY e.date DESC, e.created_at DESC
                        LIMIT 20
                    """
                elif filter_type == "Fixed Expenses":
                    query = """
                        SELECT e.*, ec.name as category_name
                        FROM expenses e
                        LEFT JOIN expense_categories ec ON e.category_id = ec.id
                        WHERE e.user_id = %s
                        AND e.description LIKE 'Fixed Expense:%%'
                        ORDER BY e.date DESC, e.created_at DESC
                        LIMIT 20
                    """
                else:
                    query = """
                        SELECT e.*, ec.name as category_name
                        FROM expenses e
                        LEFT JOIN expense_categories ec ON e.category_id = ec.id
                        WHERE e.user_id = %s
                        AND e.description NOT LIKE 'Fixed Expense:%%'
                        ORDER BY e.date DESC, e.created_at DESC
                        LIMIT 20
                    """
                
                cur.execute(query, (st.session_state.user_id,))
                expenses = cur.fetchall()
                
                if expenses:
                    expense_data = []
                    for exp in expenses:
                        is_fixed = exp['description'] and 'Fixed Expense:' in exp['description']
                        expense_data.append({
                            'Date': exp['date'].strftime('%Y-%m-%d'),
                            'Amount': f"${exp['amount']:,.2f}",
                            'Category': exp['category_name'] or 'N/A',
                            'Type': '🏠 Fixed' if is_fixed else '💰 Regular',
                            'Description': exp['description'] or '-'
                        })
                    st.dataframe(expense_data, use_container_width=True, hide_index=True)
                else:
                    st.info("No expenses yet")
            
            with col2:
                st.markdown("### Recent Income (All Users)")
                cur.execute("""
                    SELECT * FROM income
                    ORDER BY date DESC, created_at DESC
                    LIMIT 10
                """)
                income_records = cur.fetchall()
                
                if income_records:
                    income_data = []
                    for inc in income_records:
                        income_data.append({
                            'Date': inc['date'].strftime('%Y-%m-%d'),
                            'Name': inc['name'],
                            'COP': f"${inc['amount_cop']:,.2f}",
                            'USD': f"${inc['amount_usd']:,.2f}",
                            'Rate': f"{inc['exchange_rate']:,.2f}"
                        })
                    st.dataframe(income_data, use_container_width=True, hide_index=True)
                else:
                    st.info("No income records yet")
        
        # Close connection only after all operations
        cur.close()
        conn.close()
        
    except Exception as e:
        st.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.close()

