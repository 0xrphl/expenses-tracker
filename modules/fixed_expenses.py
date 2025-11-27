"""Fixed expenses management"""
import streamlit as st
from datetime import datetime, date, timedelta
from psycopg2.extras import RealDictCursor

def show_fixed_expenses_modal(cur, conn):
    """Fixed expenses page content"""
    
    # Month selector - default to December 2025
    current_month = datetime.now().strftime('%Y-%m')
    # Initialize month selector in session state
    if 'selected_month_fixed' not in st.session_state:
        st.session_state.selected_month_fixed = "2025-12"  # Default to December 2025
    
    # Display current month being viewed
    selected_month_display = st.session_state.selected_month_fixed
    try:
        month_date = datetime.strptime(selected_month_display, '%Y-%m')
        month_name = month_date.strftime('%B %Y')
        st.markdown(f"### 📅 Showing Fixed Expenses for **{month_name}**")
    except:
        st.markdown(f"### 📅 Showing Fixed Expenses for **{selected_month_display}**")
    
    st.markdown("---")
    
    # Quick month selector buttons - use on_change to avoid rerun lag
    st.markdown("**Select Month:**")
    col1, col2, col3, col4 = st.columns(4)
    
    def update_month(month):
        st.session_state.selected_month_fixed = month
    
    with col1:
        st.button("December 2025", key="btn_dec_2025", use_container_width=True, 
                 on_click=update_month, args=("2025-12",))
    with col2:
        st.button("January 2026", key="btn_jan_2026", use_container_width=True,
                 on_click=update_month, args=("2026-01",))
    with col3:
        st.button("Current Month", key="btn_current", use_container_width=True,
                 on_click=update_month, args=(current_month,))
    with col4:
        prev_month = (datetime.now().replace(day=1) - timedelta(days=1)).strftime('%Y-%m')
        st.button("Previous Month", key="btn_prev", use_container_width=True,
                 on_click=update_month, args=(prev_month,))
    
    selected_month = st.text_input("Or enter Month/Year (YYYY-MM)", value=st.session_state.selected_month_fixed, key="month_selector_input")
    if selected_month != st.session_state.selected_month_fixed:
        st.session_state.selected_month_fixed = selected_month
        st.rerun()
    
    with st.form("init_fixed_form", clear_on_submit=True):
        if st.form_submit_button("Initialize Default Fixed Expenses", use_container_width=True):
            try:
                # Get category IDs
                cur.execute("SELECT id, name FROM expense_categories")
                categories = {cat['name']: cat['id'] for cat in cur.fetchall()}
                
                # Get 'Other' category ID as fallback
                other_category_id = categories.get('Other')
                if not other_category_id:
                    # If 'Other' doesn't exist, get any category or None
                    other_category_id = list(categories.values())[0] if categories else None
                
                default_expenses = [
                    ('Residence Admin', 100, categories.get('Utility Bills', other_category_id)),
                    ('Gas Utility Bill', 15, categories.get('Utility Bills', other_category_id)),
                    ('Internet', 25, categories.get('Utility Bills', other_category_id)),
                    ('Mobile Internet', 20, categories.get('Utility Bills', other_category_id)),
                    ('Water', 26, categories.get('Utility Bills', other_category_id)),
                    ('Mortgage', 490, other_category_id),
                    ('Second Credit Line', 300, other_category_id),
                    ('Uber', 100, categories.get('Uber', other_category_id))
                ]
                
                inserted_count = 0
                for name, amount, cat_id in default_expenses:
                    if cat_id is None:
                        st.warning(f"Skipping {name}: No category found. Please ensure categories are set up.")
                        continue
                    try:
                        cur.execute("""
                            INSERT INTO fixed_expenses (user_id, name, amount, currency, category_id, month_year, is_paid)
                            VALUES (%s, %s, %s, %s, %s, %s, FALSE)
                            ON CONFLICT (user_id, name, month_year) DO NOTHING
                        """, (st.session_state.user_id, name, amount, 'USD', cat_id, st.session_state.selected_month_fixed))
                        inserted_count += 1
                    except Exception as e:
                        st.warning(f"Could not insert {name}: {e}")
                
                conn.commit()
                st.success(f"Fixed expenses initialized! ({inserted_count} expenses added)")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
                import traceback
                st.code(traceback.format_exc())
                conn.rollback()
    
    # Display fixed expenses with payment date info
    today = date.today()
    st.markdown(f"**Payment Due Date: 30th of each month** | Today: {today.day}")
    
    try:
        cur.execute("""
            SELECT fe.*, ec.name as category_name
            FROM fixed_expenses fe
            LEFT JOIN expense_categories ec ON fe.category_id = ec.id
            WHERE fe.user_id = %s 
            AND fe.month_year = %s
            AND fe.name NOT IN ('Credit 1', 'Credit 2')
            ORDER BY fe.name
        """, (st.session_state.user_id, st.session_state.selected_month_fixed))
        fixed_expenses = cur.fetchall()
        
        # Track current month to detect month changes
        current_month_key = f"current_month_fixed_{st.session_state.selected_month_fixed}"
        if current_month_key not in st.session_state:
            st.session_state[current_month_key] = True
            # Clear checkbox states when month changes
            for key in list(st.session_state.keys()):
                if key.startswith("paid_cb_") or (key.startswith("amt_") and key not in [f"amt_{exp['id']}" for exp in fixed_expenses]):
                    # Only clear if it's not for current expenses
                    pass
        
        if fixed_expenses:
            # Calculate totals
            total_fixed = sum(exp['amount'] for exp in fixed_expenses)
            total_paid = sum(exp['amount'] for exp in fixed_expenses if exp['is_paid'])
            total_pending = total_fixed - total_paid
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Fixed Expenses", f"${total_fixed:,.2f}")
            with col2:
                st.metric("Paid", f"${total_paid:,.2f}", delta=f"{len([e for e in fixed_expenses if e['is_paid']])} items")
            with col3:
                st.metric("Pending", f"${total_pending:,.2f}", delta=f"{len([e for e in fixed_expenses if not e['is_paid']])} items")
            
            st.markdown("---")
            
            # Display expenses with checkbox list and payment forms
            st.markdown("#### Fixed Liabilities - Check when paid")
            
            # Create a form for all expenses
            with st.form("fixed_expenses_payment_form", clear_on_submit=False):
                # Header row
                col_h1, col_h2, col_h3, col_h4, col_h5, col_h6 = st.columns([1, 2, 2, 2, 2, 2])
                with col_h1:
                    st.write("**Paid**")
                with col_h2:
                    st.write("**Expense**")
                with col_h3:
                    st.write("**Amount (USD)**")
                with col_h4:
                    st.write("**Wallet**")
                with col_h5:
                    st.write("**Date**")
                with col_h6:
                    st.write("**Status**")
                
                st.divider()
                
                # Store original expense data for comparison
                original_expenses = {exp['id']: exp for exp in fixed_expenses}
                
                for expense in fixed_expenses:
                    col1, col2, col3, col4, col5, col6 = st.columns([1, 2, 2, 2, 2, 2])
                    
                    with col1:
                        # Checkbox - use database value, but don't set in session state if already exists
                        checkbox_key = f"paid_cb_{expense['id']}"
                        # Only set session state if it doesn't exist or if database value changed
                        if checkbox_key not in st.session_state:
                            st.session_state[checkbox_key] = expense['is_paid']
                        elif st.session_state[checkbox_key] != expense['is_paid']:
                            # Database value changed, update session state
                            st.session_state[checkbox_key] = expense['is_paid']
                        
                        # Checkbox - use session state value (which is synced with DB)
                        is_paid = st.checkbox(
                            "Paid",
                            value=st.session_state[checkbox_key],
                            key=checkbox_key,
                            label_visibility="collapsed"
                        )
                    
                    with col2:
                        st.write(f"**{expense['name']}**")
                    
                    with col3:
                        # Editable amount - use database value
                        paid_amount = st.number_input(
                            "Amount (USD)",
                            min_value=0.01,
                            step=0.01,
                            format="%.2f",
                            value=float(expense['amount']),
                            key=f"amt_{expense['id']}",
                            label_visibility="collapsed"
                        )
                    
                    with col4:
                        # Wallet selection - default to Rafael
                        wallet_source = st.selectbox(
                            "Payment Source",
                            ["Rafael", "Jessica"],
                            key=f"wal_{expense['id']}",
                            label_visibility="collapsed"
                        )
                    
                    with col5:
                        # Payment date - default to today
                        payment_date = st.date_input(
                            "Payment Date",
                            value=date.today(),
                            key=f"date_{expense['id']}",
                            label_visibility="collapsed"
                        )
                    
                    with col6:
                        # Show status from database (not from checkbox state)
                        status = "✅ Paid" if expense['is_paid'] else "⏳ Pending"
                        st.write(status)
                    
                    st.divider()
                
                submitted = st.form_submit_button("💾 Save All Payments", use_container_width=True, type="primary")
                if submitted:
                    try:
                        expenses_added = []
                        expenses_removed = []
                        status_updates = []
                        
                        for expense in fixed_expenses:
                            exp_id = expense['id']
                            
                            # Get form values directly from session state (form widgets update session state)
                            checkbox_key = f"paid_cb_{exp_id}"
                            amount_key = f"amt_{exp_id}"
                            wallet_key = f"wal_{exp_id}"
                            date_key = f"date_{exp_id}"
                            
                            # Get current values from session state - these are updated by the form widgets
                            is_paid = st.session_state.get(checkbox_key, expense['is_paid'])
                            paid_amount = st.session_state.get(amount_key, float(expense['amount']))
                            wallet_source = st.session_state.get(wallet_key, "Rafael")
                            payment_date = st.session_state.get(date_key, date.today())
                            
                            # Get original status from database
                            was_paid = original_expenses[exp_id]['is_paid']
                            
                            # Always update the database with current checkbox state
                            cur.execute("""
                                UPDATE fixed_expenses 
                                SET is_paid = %s 
                                WHERE id = %s
                            """, (is_paid, exp_id))
                            
                            # Track status changes
                            if is_paid != was_paid:
                                status_updates.append(expense['name'])
                            
                            # If marked as paid and wasn't paid before, add to expenses
                            if is_paid and not was_paid:
                                # Check if already added to expenses for this month
                                cur.execute("""
                                    SELECT COUNT(*) as count
                                    FROM expenses
                                    WHERE user_id = %s 
                                    AND description = %s
                                """, (
                                    st.session_state.user_id,
                                    f"Fixed Expense: {expense['name']} ({st.session_state.selected_month_fixed})"
                                ))
                                
                                existing = cur.fetchone()['count']
                                if existing == 0:
                                    # Add to expenses with wallet source
                                    cur.execute("""
                                        INSERT INTO expenses (user_id, amount, currency, category_id, description, date, payment_source)
                                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                                    """, (
                                        st.session_state.user_id,
                                        paid_amount,
                                        'USD',
                                        expense['category_id'],
                                        f"Fixed Expense: {expense['name']} ({st.session_state.selected_month_fixed})",
                                        payment_date,
                                        wallet_source
                                    ))
                                    expenses_added.append(expense['name'])
                            
                            # If unmarked as paid and was paid before, remove from expenses
                            elif not is_paid and was_paid:
                                cur.execute("""
                                    DELETE FROM expenses
                                    WHERE user_id = %s 
                                    AND description = %s
                                    LIMIT 1
                                """, (
                                    st.session_state.user_id,
                                    f"Fixed Expense: {expense['name']} ({st.session_state.selected_month_fixed})"
                                ))
                                expenses_removed.append(expense['name'])
                        
                        conn.commit()
                        
                        # Show success message
                        msg_parts = []
                        if status_updates:
                            msg_parts.append(f"Updated: {', '.join(status_updates)}")
                        if expenses_added:
                            msg_parts.append(f"Added to expenses: {', '.join(expenses_added)}")
                        if expenses_removed:
                            msg_parts.append(f"Removed from expenses: {', '.join(expenses_removed)}")
                        
                        if msg_parts:
                            st.success(f"✅ Saved! {' | '.join(msg_parts)}")
                        else:
                            st.success("✅ All payments saved!")
                        
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error saving payments: {e}")
                        import traceback
                        st.code(traceback.format_exc())
                        conn.rollback()
        else:
            st.info("No fixed expenses for this month. Click 'Initialize Default Fixed Expenses' to add them.")
    except Exception as e:
        st.error(f"Error loading fixed expenses: {e}")

