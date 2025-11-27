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
                # Summary - separate assets and liabilities
                total_assets = sum(asset['value'] for asset in assets if asset['value'] >= 0)
                total_liabilities = sum(abs(asset['value']) for asset in assets if asset['value'] < 0)
                net_worth = total_assets - total_liabilities
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Assets", f"${total_assets:,.2f}")
                with col2:
                    st.metric("Total Liabilities", f"${total_liabilities:,.2f}")
                with col3:
                    st.metric("Net Worth", f"${net_worth:,.2f}")
                
                st.markdown("---")
                
                # Assets list with edit/delete
                for asset in assets:
                    with st.container():
                        col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 1, 1])
                        with col1:
                            st.write(f"**{asset['name']}**")
                        with col2:
                            if asset['value'] < 0:
                                st.write(f"-${abs(asset['value']):,.2f}", help="Liability/Credit")
                            else:
                                st.write(f"${asset['value']:,.2f}")
                        with col3:
                            asset_type_display = asset['type'] or 'N/A'
                            if asset['value'] < 0:
                                asset_type_display = "Liability/Credit"
                            st.write(asset_type_display)
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
        st.markdown("#### Add New Asset or Liability")
        with st.form("add_asset_form_new", clear_on_submit=False):
            name = st.text_input("Name", key="new_asset_name", placeholder="Asset name or Credit/Liability name")
            asset_type = st.selectbox(
                "Type", 
                ["Asset", "Liability/Credit"],
                key="new_asset_type_select",
                help="Select Asset for positive value, Liability/Credit for negative value"
            )
            value = st.number_input(
                "Value (USD)", 
                min_value=-999999999.99,  # Allow negative values for liabilities
                step=0.01, 
                format="%.2f", 
                key="new_asset_value",
                help="Enter positive for assets, negative for liabilities/credits"
            )
            description = st.text_area("Description", key="new_asset_desc")
            asset_date = st.date_input("Date", value=date.today(), key="new_asset_date")
            
            if st.form_submit_button("➕ Add", use_container_width=True):
                try:
                    # If liability selected, ensure value is negative
                    if asset_type == "Liability/Credit" and value > 0:
                        value = -value
                    
                    asset_type_value = asset_type if asset_type == "Liability/Credit" else asset_type
                    cur.execute("""
                        INSERT INTO assets (user_id, name, type, value, currency, description, date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (st.session_state.user_id, name, asset_type_value, value, 'USD', description, asset_date))
                    conn.commit()
                    if value < 0:
                        st.success(f"Liability/Credit added successfully! (${abs(value):,.2f})")
                    else:
                        st.success("Asset added successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding asset/liability: {e}")
                    conn.rollback()
    
    with tab3:
        st.markdown("#### Liabilities & Credits")
        st.info("💡 Add credits and liabilities as negative assets in the 'Add Asset' tab. Monthly payments are tracked in 'Fixed Expenses'.")
        
        # Show credits/liabilities from assets table (negative values)
        try:
            cur.execute("""
                SELECT 
                    id,
                    name,
                    value,
                    type,
                    description,
                    date
                FROM assets
                WHERE user_id = %s 
                AND value < 0
                ORDER BY name, date DESC
            """, (st.session_state.user_id,))
            liabilities = cur.fetchall()
            
            # Also show monthly credit payments from fixed expenses
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
                AND (name LIKE '%%Mortgage%%' OR name LIKE '%%Second Credit%%')
                ORDER BY name, month_year DESC
            """, (st.session_state.user_id,))
            monthly_credits = cur.fetchall()
            
            if liabilities or monthly_credits:
                # Show total outstanding from assets (negative values)
                total_outstanding = sum(abs(liab['value']) for liab in liabilities)
                if total_outstanding > 0:
                    st.markdown("**Outstanding Credits/Liabilities (from Assets):**")
                    st.metric("Total Outstanding Balance", f"${total_outstanding:,.2f}")
                    
                    st.markdown("---")
                    st.markdown("#### Credit/Liability Balances")
                    for liab in liabilities:
                        with st.container():
                            col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                            with col1:
                                st.write(f"**{liab['name']}**")
                            with col2:
                                st.write(f"${abs(liab['value']):,.2f}")
                            with col3:
                                if st.button("✏️ Edit", key=f"edit_liab_{liab['id']}"):
                                    st.session_state[f"editing_liab_{liab['id']}"] = True
                                    st.rerun()
                            with col4:
                                if st.button("🗑️ Delete", key=f"delete_liab_{liab['id']}"):
                                    try:
                                        cur.execute("DELETE FROM assets WHERE id = %s", (liab['id'],))
                                        conn.commit()
                                        st.success(f"Liability {liab['name']} deleted!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {e}")
                                        conn.rollback()
                            
                            # Edit form if editing
                            if st.session_state.get(f"editing_liab_{liab['id']}"):
                                with st.form(f"edit_liab_form_{liab['id']}", clear_on_submit=False):
                                    edit_name = st.text_input("Name", value=liab['name'], key=f"edit_liab_name_{liab['id']}")
                                    edit_value = st.number_input("Outstanding Balance (USD)", min_value=0.01, step=0.01, format="%.2f", value=abs(float(liab['value'])), key=f"edit_liab_value_{liab['id']}")
                                    edit_desc = st.text_area("Description", value=liab['description'] or '', key=f"edit_liab_desc_{liab['id']}")
                                    edit_date = st.date_input("Date", value=liab['date'], key=f"edit_liab_date_{liab['id']}")
                                    
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        if st.form_submit_button("💾 Save", use_container_width=True):
                                            try:
                                                # Save as negative value (liability)
                                                cur.execute("""
                                                    UPDATE assets
                                                    SET name = %s, value = %s, description = %s, date = %s
                                                    WHERE id = %s
                                                """, (edit_name, -edit_value, edit_desc, edit_date, liab['id']))
                                                conn.commit()
                                                st.session_state[f"editing_liab_{liab['id']}"] = False
                                                st.success("Liability updated!")
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Error: {e}")
                                                conn.rollback()
                                    with col2:
                                        if st.form_submit_button("❌ Cancel", use_container_width=True):
                                            st.session_state[f"editing_liab_{liab['id']}"] = False
                                            st.rerun()
                            
                            st.divider()
                
                # Show monthly credit payments
                if monthly_credits:
                    st.markdown("---")
                    st.markdown("#### Monthly Credit Payments (from Fixed Expenses)")
                    for liab in monthly_credits:
                        status = "✅ Paid" if liab['is_paid'] else "⏳ Outstanding"
                        status_color = "#10b981" if liab['is_paid'] else "#ef4444"
                        st.markdown(f"""
                            <div style='background-color: #1a1a1a; padding: 1rem; border-radius: 8px; border-left: 4px solid {status_color}; margin-bottom: 0.5rem;'>
                                <strong>{liab['name']}</strong> - ${liab['amount']:,.2f} | {liab['month_year']} | <span style='color: {status_color};'>{status}</span>
                            </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No liabilities found. Add credits/liabilities in the 'Add Asset' tab as negative values.")
        except Exception as e:
            st.error(f"Error loading liabilities: {e}")
            import traceback
            st.code(traceback.format_exc())

