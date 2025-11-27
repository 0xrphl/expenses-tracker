"""Assets and liabilities management"""
import streamlit as st
from datetime import date
from psycopg2.extras import RealDictCursor

def show_assets_modal(cur, conn):
    """Assets and liabilities management page content"""
    
    tab1, tab2, tab3 = st.tabs(["Assets", "Add Asset", "Liabilities/Credits"])
    
    with tab1:
        st.markdown("#### Your Assets")
        try:
            cur.execute("""
                SELECT * FROM assets
                WHERE user_id = %s
                ORDER BY date DESC, created_at DESC
            """, (st.session_state.user_id,))
            assets = cur.fetchall()
            
            if assets:
                # Summary
                total_assets = sum(asset['value'] for asset in assets)
                st.metric("Total Assets Value", f"${total_assets:,.2f}")
                
                st.markdown("---")
                
                # Assets list with edit/delete
                for asset in assets:
                    with st.container():
                        col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 1, 1])
                        with col1:
                            st.write(f"**{asset['name']}**")
                        with col2:
                            st.write(f"${asset['value']:,.2f}")
                        with col3:
                            st.write(asset['type'] or 'N/A')
                        with col4:
                            if st.button("✏️ Edit", key=f"edit_asset_{asset['id']}"):
                                st.session_state[f"editing_asset_{asset['id']}"] = True
                                st.rerun()
                        with col5:
                            if st.button("🗑️ Delete", key=f"delete_asset_{asset['id']}"):
                                try:
                                    cur.execute("DELETE FROM assets WHERE id = %s", (asset['id'],))
                                    conn.commit()
                                    st.success(f"Asset {asset['name']} deleted!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
                                    conn.rollback()
                        
                        # Edit form if editing
                        if st.session_state.get(f"editing_asset_{asset['id']}"):
                            with st.form(f"edit_asset_form_{asset['id']}", clear_on_submit=False):
                                edit_name = st.text_input("Name", value=asset['name'], key=f"edit_name_{asset['id']}")
                                edit_type = st.text_input("Type", value=asset['type'] or '', key=f"edit_type_{asset['id']}")
                                edit_value = st.number_input("Value (USD)", min_value=0.01, step=0.01, format="%.2f", value=float(asset['value']), key=f"edit_value_{asset['id']}")
                                edit_desc = st.text_area("Description", value=asset['description'] or '', key=f"edit_desc_{asset['id']}")
                                edit_date = st.date_input("Date", value=asset['date'], key=f"edit_date_{asset['id']}")
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.form_submit_button("💾 Save", use_container_width=True):
                                        try:
                                            cur.execute("""
                                                UPDATE assets
                                                SET name = %s, type = %s, value = %s, description = %s, date = %s
                                                WHERE id = %s
                                            """, (edit_name, edit_type, edit_value, edit_desc, edit_date, asset['id']))
                                            conn.commit()
                                            st.session_state[f"editing_asset_{asset['id']}"] = False
                                            st.success("Asset updated!")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Error: {e}")
                                            conn.rollback()
                                with col2:
                                    if st.form_submit_button("❌ Cancel", use_container_width=True):
                                        st.session_state[f"editing_asset_{asset['id']}"] = False
                                        st.rerun()
                        
                        st.divider()
            else:
                st.info("No assets yet. Add your first asset in the 'Add Asset' tab.")
        except Exception as e:
            st.error(f"Error loading assets: {e}")
    
    with tab2:
        st.markdown("#### Add New Asset")
        with st.form("add_asset_form_new", clear_on_submit=False):
            name = st.text_input("Asset Name", key="new_asset_name")
            asset_type = st.text_input("Type", placeholder="e.g., savings, investment, property, vehicle", key="new_asset_type")
            value = st.number_input("Value (USD)", min_value=0.01, step=0.01, format="%.2f", key="new_asset_value")
            description = st.text_area("Description", key="new_asset_desc")
            asset_date = st.date_input("Date", value=date.today(), key="new_asset_date")
            
            if st.form_submit_button("➕ Add Asset", use_container_width=True):
                try:
                    cur.execute("""
                        INSERT INTO assets (user_id, name, type, value, currency, description, date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (st.session_state.user_id, name, asset_type, value, 'USD', description, asset_date))
                    conn.commit()
                    st.success("Asset added successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding asset: {e}")
                    conn.rollback()
    
    with tab3:
        st.markdown("#### Liabilities & Credits")
        st.info("💡 Edit credit amounts and mortgage here. These are tracked as Fixed Expenses.")
        
        # Show credit/liability summary with edit capability
        try:
            cur.execute("""
                SELECT 
                    id,
                    name,
                    amount,
                    month_year,
                    is_paid,
                    category_id
                FROM fixed_expenses
                WHERE user_id = %s 
                AND (name LIKE '%%Credit%%' OR name LIKE '%%Mortgage%%' OR name LIKE '%%Second Credit%%')
                ORDER BY name, month_year DESC
            """, (st.session_state.user_id,))
            liabilities = cur.fetchall()
            
            if liabilities:
                # Group by name to show latest amount
                liability_groups = {}
                for liab in liabilities:
                    name = liab['name']
                    if name not in liability_groups:
                        liability_groups[name] = liab
                    elif liab['month_year'] > liability_groups[name]['month_year']:
                        liability_groups[name] = liab
                
                st.markdown("**Current Liabilities:**")
                total_liabilities = sum(liab['amount'] for liab in liability_groups.values() if not liab['is_paid'])
                st.metric("Total Outstanding", f"${total_liabilities:,.2f}")
                
                st.markdown("---")
                
                # Show editable credits (grouped by name, showing latest month)
                for name, liab in liability_groups.items():
                    with st.container():
                        col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                        with col1:
                            st.write(f"**{liab['name']}**")
                        with col2:
                            st.write(f"${liab['amount']:,.2f} | {liab['month_year']}")
                        with col3:
                            status = "✅ Paid" if liab['is_paid'] else "⏳ Outstanding"
                            st.write(status)
                        with col4:
                            if st.button("✏️ Edit", key=f"edit_credit_{liab['id']}"):
                                st.session_state[f"editing_credit_{liab['id']}"] = True
                                st.rerun()
                        
                        # Edit form if editing
                        if st.session_state.get(f"editing_credit_{liab['id']}"):
                            with st.form(f"edit_credit_form_{liab['id']}", clear_on_submit=False):
                                edit_name = st.text_input("Name", value=liab['name'], key=f"edit_credit_name_{liab['id']}")
                                edit_amount = st.number_input("Amount (USD)", min_value=0.01, step=0.01, format="%.2f", value=float(liab['amount']), key=f"edit_credit_amount_{liab['id']}")
                                edit_month = st.text_input("Month/Year (YYYY-MM)", value=liab['month_year'], key=f"edit_credit_month_{liab['id']}")
                                edit_paid = st.checkbox("Is Paid", value=liab['is_paid'], key=f"edit_credit_paid_{liab['id']}")
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.form_submit_button("💾 Save", use_container_width=True):
                                        try:
                                            # Update all instances of this credit with the same name for this month
                                            cur.execute("""
                                                UPDATE fixed_expenses
                                                SET name = %s, amount = %s, month_year = %s, is_paid = %s
                                                WHERE id = %s
                                            """, (edit_name, edit_amount, edit_month, edit_paid, liab['id']))
                                            conn.commit()
                                            st.session_state[f"editing_credit_{liab['id']}"] = False
                                            st.success("Credit updated!")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Error: {e}")
                                            conn.rollback()
                                with col2:
                                    if st.form_submit_button("❌ Cancel", use_container_width=True):
                                        st.session_state[f"editing_credit_{liab['id']}"] = False
                                        st.rerun()
                        
                        st.divider()
                
                # Show all months for each credit
                st.markdown("#### All Credit Entries by Month")
                for liab in sorted(liabilities, key=lambda x: (x['name'], x['month_year']), reverse=True):
                    status = "✅ Paid" if liab['is_paid'] else "⏳ Outstanding"
                    status_color = "#10b981" if liab['is_paid'] else "#ef4444"
                    st.markdown(f"""
                        <div style='background-color: #1a1a1a; padding: 1rem; border-radius: 8px; border-left: 4px solid {status_color}; margin-bottom: 0.5rem;'>
                            <strong>{liab['name']}</strong> - ${liab['amount']:,.2f} | {liab['month_year']} | <span style='color: {status_color};'>{status}</span>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No liabilities found. Liabilities are managed as Fixed Expenses.")
        except Exception as e:
            st.error(f"Error loading liabilities: {e}")
            import traceback
            st.code(traceback.format_exc())

