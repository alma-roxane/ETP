import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
from database import (
    init_db, add_transaction, get_transactions, get_summary,
    delete_transaction, export_to_csv
)
from chatbot import get_chatbot_response
import os

# ----------------------------------
# 🔧 PAGE CONFIGURATION
# ----------------------------------
st.set_page_config(
    page_title="Personal Finance Chatbot",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
init_db()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "transactions" not in st.session_state:
    st.session_state.transactions = get_transactions()

# ----------------------------------
# 🧭 SIDEBAR NAVIGATION
# ----------------------------------
st.sidebar.title("💼 Personal Finance Assistant")
page = st.sidebar.radio(
    "Select a page:",
    ["💬 Chat", "📊 Analytics Dashboard", "⚙️ Settings"],
    label_visibility="collapsed"
)

# Sidebar quick settings
with st.sidebar.expander("⚙️ Quick Settings"):
    currency = st.selectbox("Currency", ["USD", "EUR", "GBP", "INR"], key="currency")
    theme = st.selectbox("Theme", ["Light", "Dark"], key="theme")

# Currency symbol mapping (FIX #1: Dynamic currency symbols)
CURRENCY_SYMBOLS = {
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "INR": "₹"
}
curr_symbol = CURRENCY_SYMBOLS.get(currency, "$")

# Theme colors
# NOTE: Streamlit handles the main app theme (Light/Dark) itself. 
# We use these colors to style the charts for responsiveness.

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


if (theme == "Light"):
   # st.success("Light mode")
    local_css("C:/Users/Alma/Downloads/ETP/ETP/assests/style.css")
else:
    #st.success("Dark mode")
    local_css("C:/Users/Alma/Downloads/ETP/ETP/assests/dark.css")
# ----------------------------------
# 💬 CHAT PAGE
# ----------------------------------
if page == "💬 Chat":
    st.title("💬 Personal Finance Chatbot")

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input (FIX #2: Proper indentation - stays inside the if block)
    if prompt := st.chat_input("Ask me about your finances..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate chatbot response (passing currency symbol)
        response = get_chatbot_response(
            prompt, 
            st.session_state.transactions,
            curr_symbol  # Pass currency symbol to chatbot
        )

        # Display assistant reply
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

# ----------------------------------
# 📊 ANALYTICS DASHBOARD
# ----------------------------------
elif page == "📊 Analytics Dashboard":
    st.title("📊 Financial Analytics Dashboard")

    # Fetch data
    transactions = get_transactions()
    summary = get_summary()
    st.session_state.transactions = transactions

    if transactions:
        df = pd.DataFrame(transactions)
        df['date'] = pd.to_datetime(df['date'])

        # ---- Summary metrics ----
        st.markdown("### 💡 Summary Overview")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Income", f"{curr_symbol} {summary['total_income']:.2f}")
        with col2:
            st.metric("Total Expenses", f"{curr_symbol} {summary['total_expenses']:.2f}")
        with col3:
            # FIX #3: Color-coded balance
            balance_delta = summary['balance']
            st.metric(
                "Balance", 
                f"{curr_symbol} {summary['balance']:.2f}",
                delta=None,
                delta_color="normal" if balance_delta >= 0 else "inverse"
            )
        with col4:
            st.metric("Transactions", len(df))

        st.divider()

        # ---- Filters ----
        st.markdown("### 🔍 Filter Transactions")
        col1, col2 = st.columns(2)
        with col1:
            year_filter = st.selectbox(
                "Filter by Year",
                ["All"] + sorted(df['date'].dt.year.astype(str).unique().tolist(), reverse=True)
            )
        with col2:
            month_filter = st.selectbox(
                "Filter by Month",
                ["All"] + sorted([m.strftime("%B %Y") for m in df['date'].dt.to_period("M").unique()], reverse=True)
            )

        filtered_df = df.copy()
        if year_filter != "All":
            filtered_df = filtered_df[filtered_df['date'].dt.year.astype(str) == year_filter]
        if month_filter != "All":
            filtered_df = filtered_df[filtered_df['date'].dt.strftime("%B %Y") == month_filter]

        # ---- Charts ----
        st.markdown("### 📈 Spending Visualizations")
        col1, col2 = st.columns(2)

        with col1:
            expense_df = filtered_df[filtered_df['type'] == 'expense']
            if not expense_df.empty:
                category_spending = expense_df.groupby('category')['amount'].sum().sort_values(ascending=False)
                fig = px.pie(
                    values=category_spending.values,
                    names=category_spending.index,
                    title="Expense Breakdown by Category",
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                # Apply theme colors to the pie chart
                fig.update_layout(
                    paper_bgcolor=bg_color,
                    plot_bgcolor=bg_color,
                    font=dict(color=text_color)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No expenses in the selected period")

        with col2:
            # FIX #4: Better trend visualization
            if len(filtered_df) > 0:
                trend_df = filtered_df.groupby(['date', 'type'])['amount'].sum().unstack(fill_value=0)
                fig = px.line(
                    trend_df,
                    title="Income vs Expenses Over Time",
                    labels={"value": f"Amount ({curr_symbol})", "date": "Date"}
                )
                fig.update_layout(legend_title_text='Type')
                # Apply theme colors to the line chart
                fig.update_layout(
                    paper_bgcolor=bg_color,
                    plot_bgcolor=bg_color,
                    font=dict(color=text_color),
                    # Adjust axes lines for better contrast in dark mode
                    xaxis=dict(showgrid=False),
                    yaxis=dict(gridcolor='#444444' if theme == "Dark" else '#CCCCCC') 
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data for the selected period")

        st.divider()

        # ---- Transactions Table ----
        st.subheader("🧾 Transaction History")
        # FIX #5: Format amount with currency symbol in table
        display_df = filtered_df[['date', 'type', 'category', 'amount', 'description']].copy()
        display_df['amount'] = display_df['amount'].apply(lambda x: f"{curr_symbol} {x:.2f}")
        display_df = display_df.sort_values('date', ascending=False)
        st.dataframe(display_df, use_container_width=True)

        # ---- Export CSV ----
        if st.button("⬇️ Export to CSV"):
            try:
                csv_file = export_to_csv()
                with open(csv_file, 'r') as f:
                    st.download_button(
                        label="📥 Download CSV",
                        data=f.read(),
                        file_name=f"transactions_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                # Clean up temp file
                if os.path.exists(csv_file):
                    os.remove(csv_file)
            except Exception as e:
                st.error(f"Error exporting CSV: {str(e)}")

    else:
        st.info("📝 No transactions found. Add some income or expenses in the Settings page to get started!")

# ----------------------------------
# ⚙️ SETTINGS PAGE
# ----------------------------------
elif page == "⚙️ Settings":
    st.title("⚙️ Manage Transactions")

    col1, col2 = st.columns(2)

    # === Add Income ===
    with col1:
        st.subheader("💵 Add Income")
        with st.form("income_form"):
            amount = st.number_input("Amount", min_value=0.01, step=0.01, format="%.2f")
            category = st.selectbox("Category", ["Salary", "Freelance", "Investment", "Other"])
            date = st.date_input("Date", max_value=datetime.now().date())
            desc = st.text_input("Description (optional)")

            if st.form_submit_button("➕ Add Income"):
                # FIX #6: Validation for zero amounts
                if amount > 0:
                    try:
                        add_transaction("income", category, amount, date.isoformat(), desc)
                        st.success("✅ Income added successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding income: {str(e)}")
                else:
                    st.error("❌ Amount must be greater than 0")

    # === Add Expense ===
    with col2:
        st.subheader("💸 Add Expense")
        with st.form("expense_form"):
            amount = st.number_input("Amount", min_value=0.01, step=0.01, format="%.2f", key="expense_amount")
            category = st.selectbox(
                "Category",
                ["Food", "Transport", "Entertainment", "Utilities", "Healthcare", "Shopping", "Other"],
                key="expense_category"
            )
            date = st.date_input("Date", max_value=datetime.now().date(), key="expense_date")
            desc = st.text_input("Description (optional)", key="expense_desc")

            if st.form_submit_button("➕ Add Expense"):
                # FIX #7: Validation for zero amounts
                if amount > 0:
                    try:
                        add_transaction("expense", category, amount, date.isoformat(), desc)
                        st.success("✅ Expense added successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding expense: {str(e)}")
                else:
                    st.error("❌ Amount must be greater than 0")

    st.divider()
    st.subheader("🗑️ Delete Transactions")

    transactions = get_transactions()
    if transactions:
        df = pd.DataFrame(transactions)
        df['date'] = pd.to_datetime(df['date'])

        # FIX #8: Better transaction display for deletion
        transaction_options = [
            f"{t['id']} - {t['date']} - {t['type'].upper()} - {t['category']} - {curr_symbol}{t['amount']:.2f}"
            for t in transactions
        ]

        if len(transaction_options) > 0:
            transaction_to_delete = st.selectbox(
                "Select transaction to delete", 
                transaction_options,
                help="Choose a transaction to permanently delete"
            )
            
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("🗑️ Delete", type="primary"):
                    try:
                        transaction_id = int(transaction_to_delete.split(" - ")[0])
                        delete_transaction(transaction_id)
                        st.success("✅ Transaction deleted successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting transaction: {str(e)}")
            with col2:
                st.caption("⚠️ This action cannot be undone")
    else:
        st.info("📝 No transactions found to delete. Add some transactions first!")