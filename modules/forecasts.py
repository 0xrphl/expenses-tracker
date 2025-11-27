"""Forecast calculations for income and expenses"""
import streamlit as st
from datetime import date, datetime, timedelta
from psycopg2.extras import RealDictCursor

def show_forecasts(cur, user_id, current_rate):
    """Display income and expense forecasts"""
    st.markdown("---")
    st.markdown("### 📊 Financial Forecasts")
    
    today = date.today()
    current_month = today.strftime('%Y-%m')
    
    # Income Forecast
    st.markdown("#### 💵 Income Forecast")
    
    # Calculate expected income for current month
    # Rafael payment (25th) - Income 1
    rafael_expected = 0
    if today.day < 25 or (today.day >= 25 and today.month == datetime.now().month):
        amount_cop = 4400 * 2300
        if current_rate < 4400:
            rafael_expected = amount_cop / 4400
        else:
            rafael_expected = amount_cop / current_rate
    
    # Jessica payment (20th) - Income 2
    jessica_expected = 0
    if today.day < 20 or (today.day >= 20 and today.month == datetime.now().month):
        amount_cop = 4400 * 3000
        if current_rate < 4400:
            jessica_expected = amount_cop / 4400
        else:
            jessica_expected = amount_cop / current_rate
    
    # Get actual income for current month
    cur.execute("""
        SELECT 
            name,
            SUM(amount_usd) as total
        FROM income
        WHERE DATE_TRUNC('month', date) = DATE_TRUNC('month', CURRENT_DATE)
        GROUP BY name
    """)
    actual_income = {row['name']: row['total'] for row in cur.fetchall()}
    
    income1_actual = actual_income.get('Income 1 (Rafael)', 0)
    income2_actual = actual_income.get('Income 2', 0)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Income 1 (Rafael)",
            f"${income1_actual:,.2f}",
            delta=f"Expected: ${rafael_expected:,.2f}" if rafael_expected > 0 else None,
            delta_color="normal" if income1_actual >= rafael_expected else "inverse"
        )
        if today.day < 25:
            st.caption(f"Due: 25th (in {25 - today.day} days)")
        elif today.day == 25:
            st.caption("Due: TODAY")
        else:
            st.caption("Paid this month")
    
    with col2:
        st.metric(
            "Income 2 (Jessica)",
            f"${income2_actual:,.2f}",
            delta=f"Expected: ${jessica_expected:,.2f}" if jessica_expected > 0 else None,
            delta_color="normal" if income2_actual >= jessica_expected else "inverse"
        )
        if today.day < 20:
            st.caption(f"Due: 20th (in {20 - today.day} days)")
        elif today.day == 20:
            st.caption("Due: TODAY")
        else:
            st.caption("Paid this month")
    
    with col3:
        total_expected = rafael_expected + jessica_expected
        total_actual = income1_actual + income2_actual
        st.metric(
            "Total Expected",
            f"${total_expected:,.2f}",
            delta=f"Actual: ${total_actual:,.2f}",
            delta_color="normal" if total_actual >= total_expected else "inverse"
        )
    
    # Fixed Expenses Forecast
    st.markdown("#### 🏠 Fixed Expenses Forecast")
    
    # Get fixed expenses for current month
    cur.execute("""
        SELECT 
            name,
            amount,
            is_paid
        FROM fixed_expenses
        WHERE user_id = %s AND month_year = %s
        ORDER BY name
    """, (user_id, current_month))
    fixed_expenses = cur.fetchall()
    
    if fixed_expenses:
        total_fixed = sum(exp['amount'] for exp in fixed_expenses)
        total_paid = sum(exp['amount'] for exp in fixed_expenses if exp['is_paid'])
        total_pending = total_fixed - total_paid
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Fixed", f"${total_fixed:,.2f}")
        with col2:
            st.metric("Paid", f"${total_paid:,.2f}", delta=f"{len([e for e in fixed_expenses if e['is_paid']])}/{len(fixed_expenses)}")
        with col3:
            st.metric("Pending", f"${total_pending:,.2f}", delta=f"{len([e for e in fixed_expenses if not e['is_paid']])} remaining")
        
        # Show pending expenses
        pending = [e for e in fixed_expenses if not e['is_paid']]
        if pending:
            st.markdown("**Pending Fixed Expenses:**")
            for exp in pending:
                st.write(f"  • {exp['name']}: ${exp['amount']:,.2f}")
        
        # Due date info
        due_day = 30
        if today.day < due_day:
            days_until_due = due_day - today.day
            st.info(f"📅 Fixed expenses due on {due_day}th (in {days_until_due} days)")
        elif today.day == due_day:
            st.warning(f"⚠️ Fixed expenses due TODAY!")
        else:
            st.success("✅ All fixed expenses due date passed")
    else:
        st.info("No fixed expenses for this month")

