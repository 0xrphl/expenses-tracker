"""Calendar widget showing income and expense events"""
import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from psycopg2.extras import RealDictCursor
import plotly.graph_objects as go

def show_calendar_widget(cur, user_id):
    """Display calendar widget with income and expense events"""
    st.markdown("---")
    st.markdown("### 📅 Financial Calendar")
    
    # Get current month or selected month
    if 'calendar_month' not in st.session_state:
        st.session_state.calendar_month = date.today()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("◀ Previous", key="cal_prev"):
            if st.session_state.calendar_month.month == 1:
                st.session_state.calendar_month = st.session_state.calendar_month.replace(year=st.session_state.calendar_month.year - 1, month=12)
            else:
                st.session_state.calendar_month = st.session_state.calendar_month.replace(month=st.session_state.calendar_month.month - 1)
            st.rerun()
    with col2:
        st.markdown(f"### {st.session_state.calendar_month.strftime('%B %Y')}")
    with col3:
        if st.button("Next ▶", key="cal_next"):
            if st.session_state.calendar_month.month == 12:
                st.session_state.calendar_month = st.session_state.calendar_month.replace(year=st.session_state.calendar_month.year + 1, month=1)
            else:
                st.session_state.calendar_month = st.session_state.calendar_month.replace(month=st.session_state.calendar_month.month + 1)
            st.rerun()
    
    # Get events for the month
    month_start = st.session_state.calendar_month.replace(day=1)
    if month_start.month == 12:
        month_end = month_start.replace(year=month_start.year + 1, month=1) - timedelta(days=1)
    else:
        month_end = month_start.replace(month=month_start.month + 1) - timedelta(days=1)
    
    # Get income events
    cur.execute("""
        SELECT date, name, amount_usd, payment_source
        FROM income
        WHERE date >= %s AND date <= %s
        ORDER BY date
    """, (month_start, month_end))
    income_events = cur.fetchall()
    
    # Get expense events
    cur.execute("""
        SELECT e.date, e.amount, e.description, ec.name as category, e.payment_source
        FROM expenses e
        LEFT JOIN expense_categories ec ON e.category_id = ec.id
        WHERE e.user_id = %s AND e.date >= %s AND e.date <= %s
        ORDER BY e.date
    """, (user_id, month_start, month_end))
    expense_events = cur.fetchall()
    
    # Get fixed expenses due dates (30th of month)
    try:
        fixed_due_date = month_start.replace(day=30)
    except ValueError:
        # For months with less than 30 days, use last day
        if month_start.month == 2:
            fixed_due_date = month_start.replace(day=28)
        else:
            fixed_due_date = month_start.replace(day=28)
    
    # Get payment dates (20th Jessica, 25th Rafael)
    jessica_pay_date = month_start.replace(day=20)
    rafael_pay_date = month_start.replace(day=25)
    
    # Create calendar view
    today = date.today()
    # weekday() returns 0=Monday, 6=Sunday
    first_day = month_start.weekday()
    
    # Calendar grid with modern styling
    st.markdown("#### 📅 Calendar View")
    
    # Day names header
    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    cols = st.columns(7)
    for i, day in enumerate(day_names):
        with cols[i]:
            st.markdown(f"<div style='text-align: center; font-weight: bold; color: #6366f1;'>{day}</div>", unsafe_allow_html=True)
    
    # Calendar days
    current_date = month_start
    week_rows = []
    current_week = []
    
    # Add empty cells for days before month starts
    for _ in range(first_day):
        current_week.append(None)
    
    while current_date <= month_end:
        current_week.append(current_date)
        if len(current_week) == 7:
            week_rows.append(current_week)
            current_week = []
        current_date += timedelta(days=1)
    
    # Add remaining days
    while len(current_week) < 7:
        current_week.append(None)
    if current_week:
        week_rows.append(current_week)
    
    # Display calendar
    for week in week_rows:
        cols = st.columns(7)
        for i, day_date in enumerate(week):
            with cols[i]:
                if day_date:
                    is_today = day_date == today
                    is_past = day_date < today
                    
                    # Get events for this day
                    day_income = [e for e in income_events if e['date'] == day_date]
                    day_expenses = [e for e in expense_events if e['date'] == day_date]
                    
                    # Special dates
                    is_jessica_pay = day_date == jessica_pay_date
                    is_rafael_pay = day_date == rafael_pay_date
                    is_fixed_due = day_date == fixed_due_date
                    
                    # Style based on date with modern design
                    bg_color = "#6366f1" if is_today else "#1a1a1a"
                    border_color = "#10b981" if is_today else "#333333"
                    text_color = "#ffffff" if is_today else "#e0e0e0"
                    opacity = "1.0" if not is_past else "0.5"
                    
                    st.markdown(f"""
                        <div style='
                            background-color: {bg_color};
                            border: 2px solid {border_color};
                            padding: 8px;
                            border-radius: 8px;
                            text-align: center;
                            min-height: 60px;
                            opacity: {opacity};
                        '>
                            <strong style='color: {text_color}; font-size: 16px;'>{day_date.day}</strong>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Show events
                    event_text = []
                    if is_jessica_pay:
                        event_text.append("💰 Jessica Pay")
                    if is_rafael_pay:
                        event_text.append("💰 Rafael Pay")
                    if is_fixed_due:
                        event_text.append("📅 Fixed Due")
                    if day_income:
                        total_income = sum(e['amount_usd'] for e in day_income)
                        event_text.append(f"💵 +${total_income:,.0f}")
                    if day_expenses:
                        total_exp = sum(e['amount'] for e in day_expenses)
                        event_text.append(f"💸 -${total_exp:,.0f}")
                    
                    if event_text:
                        # Display events with colored icons
                        event_html = []
                        for event in event_text:
                            if "💰" in event or "💵" in event:
                                event_html.append(f"<span style='color: #10b981; font-size: 9px;'>{event}</span>")
                            elif "💸" in event or "📅" in event:
                                event_html.append(f"<span style='color: #ef4444; font-size: 9px;'>{event}</span>")
                            else:
                                event_html.append(f"<span style='font-size: 9px;'>{event}</span>")
                        st.markdown(f"<div style='margin-top: 5px; line-height: 1.2;'> {' | '.join(event_html)}</div>", unsafe_allow_html=True)
                else:
                    st.write("")
    
    # Event list below calendar
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 💵 Income Events")
        if income_events:
            for event in income_events:
                is_past = event['date'] <= today
                icon = "✅" if is_past else "📅"
                st.markdown(f"{icon} **{event['date'].strftime('%d %b')}**: {event['name']} - ${event['amount_usd']:,.2f}")
                if event.get('payment_source'):
                    st.caption(f"   Source: {event['payment_source']}")
        else:
            st.info("No income events this month")
    
    with col2:
        st.markdown("#### 💸 Expense Events")
        if expense_events:
            for event in expense_events:
                is_past = event['date'] <= today
                icon = "✅" if is_past else "📅"
                is_fixed = event['description'] and 'Fixed Expense:' in event['description']
                fixed_icon = "🏠" if is_fixed else "💰"
                st.markdown(f"{icon} {fixed_icon} **{event['date'].strftime('%d %b')}**: ${event['amount']:,.2f} - {event['description'][:50]}")
                if event.get('payment_source'):
                    st.caption(f"   Paid from: {event['payment_source']}")
        else:
            st.info("No expense events this month")
        
        # Show upcoming fixed expenses due
        if fixed_due_date >= today:
            st.markdown(f"#### 📅 Upcoming")
            if fixed_due_date == today:
                st.warning(f"⚠️ Fixed expenses due TODAY ({fixed_due_date.strftime('%d %b')})")
            else:
                st.info(f"Fixed expenses due: {fixed_due_date.strftime('%d %b')}")

