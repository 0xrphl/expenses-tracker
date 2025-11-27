"""Page views for different sections"""
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

def show_dashboard_page():
    """Dashboard overview page"""
    st.title("📊 Dashboard")
    
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
        
        # Show charts
        show_charts(cur, st.session_state.user_id)
        
        # Handle exchange rates modal
        if st.session_state.get('show_exchange_rates'):
            show_exchange_rates_modal(cur, conn)
        
        cur.close()
        conn.close()
    except Exception as e:
        st.error(f"Error: {e}")
        import traceback
        st.code(traceback.format_exc())

def show_expenses_page():
    """Expenses table and management page"""
    st.title("💸 Expenses")
    
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Action buttons
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("➕ Add Expense", use_container_width=True, key="btn_add_expense_page"):
                if not st.session_state.get('show_add_expense'):
                    st.session_state.show_add_expense = True
                    st.rerun()
        
        # Handle add expense modal
        if st.session_state.get('show_add_expense'):
            st.markdown("---")
            show_add_expense_modal(cur, conn)
        
        # Expenses table
        st.markdown("---")
        st.markdown("### Expenses Table")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            cur.execute("SELECT id, name FROM expense_categories ORDER BY name")
            categories = cur.fetchall()
            category_options = ["All"] + [cat['name'] for cat in categories]
            selected_category = st.selectbox("Filter by Category", category_options, key="expense_filter_category")
        
        with col2:
            wallet_options = ["All", "Rafael", "Jessica"]
            selected_wallet = st.selectbox("Filter by Wallet", wallet_options, key="expense_filter_wallet")
        
        with col3:
            date_range = st.selectbox("Date Range", ["All Time", "This Month", "This Year"], key="expense_filter_date")
        
        # Build query
        query = """
            SELECT 
                e.*,
                ec.name as category_name,
                e.date as expense_date
            FROM expenses e
            LEFT JOIN expense_categories ec ON e.category_id = ec.id
            WHERE e.user_id = %s
        """
        params = [st.session_state.user_id]
        
        if selected_category != "All":
            query += " AND ec.name = %s"
            params.append(selected_category)
        
        if selected_wallet != "All":
            query += " AND e.payment_source = %s"
            params.append(selected_wallet)
        
        if date_range == "This Month":
            query += " AND DATE_TRUNC('month', e.date) = DATE_TRUNC('month', CURRENT_DATE)"
        elif date_range == "This Year":
            query += " AND DATE_TRUNC('year', e.date) = DATE_TRUNC('year', CURRENT_DATE)"
        
        query += " ORDER BY e.date DESC, e.created_at DESC"
        
        cur.execute(query, params)
        expenses = cur.fetchall()
        
        if expenses:
            # Summary
            total_amount = sum(exp['amount'] for exp in expenses)
            st.metric("Total Expenses", f"${total_amount:,.2f}", delta=f"{len(expenses)} transactions")
            
            # Display table
            import pandas as pd
            df = pd.DataFrame([{
                'Date': exp['expense_date'].strftime('%Y-%m-%d'),
                'Amount': f"${exp['amount']:,.2f}",
                'Category': exp['category_name'] or 'N/A',
                'Description': exp['description'] or '',
                'Wallet': exp['payment_source'] or 'N/A'
            } for exp in expenses])
            
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No expenses found. Add your first expense using the 'Add Expense' button.")
        
        cur.close()
        conn.close()
    except Exception as e:
        st.error(f"Error: {e}")
        import traceback
        st.code(traceback.format_exc())

def show_fixed_expenses_page():
    """Fixed expenses management page"""
    st.title("🏠 Fixed Expenses")
    
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        show_fixed_expenses_modal(cur, conn)
        cur.close()
        conn.close()
    except Exception as e:
        st.error(f"Error: {e}")
        import traceback
        st.code(traceback.format_exc())

def show_assets_page():
    """Assets and credits management page"""
    st.title("💎 Assets & Credits")
    
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        show_assets_modal(cur, conn)
        cur.close()
        conn.close()
    except Exception as e:
        st.error(f"Error: {e}")
        import traceback
        st.code(traceback.format_exc())

