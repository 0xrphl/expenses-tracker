"""Charts and analytics functions"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from psycopg2.extras import RealDictCursor
from datetime import date

def show_charts(cur, user_id):
    """Display charts and analytics"""
    st.markdown("---")
    st.markdown("### Charts & Analytics")
    
    # Row 1: Income and Expenses Overview
    col1, col2 = st.columns(2)
    
    with col1:
        # Monthly income chart
        try:
            cur.execute("""
                SELECT 
                    DATE_TRUNC('month', date) as month,
                    name,
                    SUM(amount_usd) as total
                FROM income
                GROUP BY DATE_TRUNC('month', date), name
                ORDER BY month DESC
                LIMIT 12
            """)
            income_chart_data = cur.fetchall()
            
            if income_chart_data:
                df_income = pd.DataFrame(income_chart_data)
                df_income['month'] = pd.to_datetime(df_income['month']).dt.strftime('%Y-%m')
                fig_income = px.bar(
                    df_income, 
                    x='month', 
                    y='total', 
                    color='name',
                    title='Monthly Income by Source',
                    labels={'total': 'Amount (USD)', 'month': 'Month', 'name': 'Income Source'}
                )
                fig_income.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_income, use_container_width=True)
            else:
                st.info("No income data for chart")
        except Exception as e:
            st.error(f"Error loading income chart: {e}")
    
    with col2:
        # Expenses by category chart
        try:
            cur.execute("""
                SELECT 
                    ec.name as category,
                    SUM(e.amount) as total
                FROM expenses e
                LEFT JOIN expense_categories ec ON e.category_id = ec.id
                WHERE e.user_id = %s
                GROUP BY ec.name
                ORDER BY total DESC
            """, (user_id,))
            expense_chart_data = cur.fetchall()
            
            if expense_chart_data:
                df_expenses = pd.DataFrame(expense_chart_data)
                fig_expenses = px.pie(
                    df_expenses,
                    values='total',
                    names='category',
                    title='Expenses by Category'
                )
                fig_expenses.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_expenses, use_container_width=True)
            else:
                st.info("No expenses data for chart")
        except Exception as e:
            st.error(f"Error loading expense chart: {e}")
    
    # Row 2: Income vs Expenses Trend
    st.markdown("#### Income vs Expenses Trend")
    try:
        # Get monthly income
        cur.execute("""
            SELECT 
                DATE_TRUNC('month', date) as month,
                SUM(amount_usd) as total_income
            FROM income
            GROUP BY DATE_TRUNC('month', date)
            ORDER BY month DESC
            LIMIT 12
        """)
        monthly_income = {row['month'].strftime('%Y-%m'): row['total_income'] for row in cur.fetchall()}
        
        # Get monthly expenses
        cur.execute("""
            SELECT 
                DATE_TRUNC('month', date) as month,
                SUM(amount) as total_expenses
            FROM expenses
            WHERE user_id = %s
            GROUP BY DATE_TRUNC('month', date)
            ORDER BY month DESC
            LIMIT 12
        """, (user_id,))
        monthly_expenses = {row['month'].strftime('%Y-%m'): row['total_expenses'] for row in cur.fetchall()}
        
        # Combine data
        all_months = sorted(set(list(monthly_income.keys()) + list(monthly_expenses.keys())), reverse=True)[:12]
        
        if all_months:
            df_trend = pd.DataFrame({
                'Month': all_months,
                'Income': [monthly_income.get(m, 0) for m in all_months],
                'Expenses': [monthly_expenses.get(m, 0) for m in all_months]
            })
            
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(
                x=df_trend['Month'],
                y=df_trend['Income'],
                name='Income',
                line=dict(color='#10b981', width=3),
                mode='lines+markers'
            ))
            fig_trend.add_trace(go.Scatter(
                x=df_trend['Month'],
                y=df_trend['Expenses'],
                name='Expenses',
                line=dict(color='#ef4444', width=3),
                mode='lines+markers'
            ))
            fig_trend.update_layout(
                title='Income vs Expenses Trend',
                xaxis_title='Month',
                yaxis_title='Amount (USD)',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                hovermode='x unified'
            )
            st.plotly_chart(fig_trend, use_container_width=True)
    except Exception as e:
        st.error(f"Error loading trend chart: {e}")
    
    # Row 3: Fixed Expenses Status and Credit Tracking
    col1, col2 = st.columns(2)
    
    with col1:
        # Fixed Expenses Status
        try:
            current_month = date.today().strftime('%Y-%m')
            cur.execute("""
                SELECT 
                    name,
                    amount,
                    is_paid
                FROM fixed_expenses
                WHERE user_id = %s AND month_year = %s
                ORDER BY name
            """, (user_id, current_month))
            fixed_data = cur.fetchall()
            
            if fixed_data:
                df_fixed = pd.DataFrame(fixed_data)
                paid_count = len(df_fixed[df_fixed['is_paid'] == True])
                total_count = len(df_fixed)
                
                fig_fixed = go.Figure(data=[
                    go.Bar(
                        x=['Paid', 'Pending'],
                        y=[paid_count, total_count - paid_count],
                        marker_color=['#10b981', '#f59e0b'],
                        text=[paid_count, total_count - paid_count],
                        textposition='auto'
                    )
                ])
                fig_fixed.update_layout(
                    title=f'Fixed Expenses Status ({current_month})',
                    xaxis_title='Status',
                    yaxis_title='Count',
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_fixed, use_container_width=True)
        except Exception as e:
            st.error(f"Error loading fixed expenses chart: {e}")
    
    with col2:
        # Credit Amounts Tracking
        try:
            cur.execute("""
                SELECT 
                    name,
                    amount,
                    month_year,
                    is_paid
                FROM fixed_expenses
                WHERE user_id = %s 
                AND (name LIKE '%%Credit%%' OR name LIKE '%%Mortgage%%')
                ORDER BY month_year DESC, name
                LIMIT 12
            """, (user_id,))
            credit_data = cur.fetchall()
            
            if credit_data:
                df_credit = pd.DataFrame(credit_data)
                # Group by name and sum amounts
                credit_summary = df_credit.groupby('name')['amount'].sum().reset_index()
                
                fig_credit = px.bar(
                    credit_summary,
                    x='name',
                    y='amount',
                    title='Credit & Mortgage Amounts',
                    labels={'amount': 'Total Amount (USD)', 'name': 'Credit Type'},
                    color='amount',
                    color_continuous_scale='Reds'
                )
                fig_credit.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    showlegend=False
                )
                st.plotly_chart(fig_credit, use_container_width=True)
            else:
                st.info("No credit data available")
        except Exception as e:
            st.error(f"Error loading credit chart: {e}")
    
    # Row 4: Assets Chart and Expenses Breakdown
    col1, col2 = st.columns(2)
    
    with col1:
        # Assets Chart
        try:
            st.markdown("#### 💎 Assets Overview")
            cur.execute("""
                SELECT 
                    type,
                    SUM(value) as total
                FROM assets
                WHERE user_id = %s
                GROUP BY type
                ORDER BY total DESC
            """, (user_id,))
            assets_data = cur.fetchall()
            
            if assets_data:
                df_assets = pd.DataFrame(assets_data)
                fig_assets = px.bar(
                    df_assets,
                    x='type',
                    y='total',
                    title='Assets by Type',
                    labels={'total': 'Value (USD)', 'type': 'Asset Type'},
                    color='total',
                    color_continuous_scale='Greens'
                )
                fig_assets.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_assets, use_container_width=True)
            else:
                st.info("No assets data for chart")
        except Exception as e:
            st.error(f"Error loading assets chart: {e}")
    
    with col2:
        # Expenses Breakdown
        try:
            st.markdown("#### Expenses Breakdown: Regular vs Fixed")
            cur.execute("""
                SELECT 
                    CASE 
                        WHEN description LIKE 'Fixed Expense:%%' THEN 'Fixed Expenses'
                        ELSE 'Regular Expenses'
                    END as expense_type,
                    SUM(amount) as total
                FROM expenses
                WHERE user_id = %s
                GROUP BY expense_type
            """, (user_id,))
            expense_breakdown = cur.fetchall()
            
            if expense_breakdown:
                df_breakdown = pd.DataFrame(expense_breakdown)
                fig_breakdown = px.pie(
                    df_breakdown,
                    values='total',
                    names='expense_type',
                    title='Regular vs Fixed Expenses',
                    color_discrete_map={
                        'Fixed Expenses': '#6366f1',
                        'Regular Expenses': '#10b981'
                    }
                )
                fig_breakdown.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_breakdown, use_container_width=True)
            else:
                st.info("No expenses data for chart")
        except Exception as e:
            st.error(f"Error loading expense breakdown: {e}")

