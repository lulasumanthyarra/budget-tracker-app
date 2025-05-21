import streamlit as st
import pandas as pd
import datetime
import gspread
from google.oauth2.service_account import Credentials
from streamlit.components.v1 import html
import json

# -------------------------
# Google Sheet Connection
# -------------------------
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GOOGLE_CREDS"])
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)
sheet = client.open("Budget_Tracker").sheet1

# -------------------------
# App Setup
# -------------------------
st.set_page_config(layout="wide", page_title="💸 Budget Tracker", page_icon="💸")

# -------------------------
# Categories
# -------------------------
income_categories = ["💼 Bonus", "💰 Daily Earnings", "💰 Freelance", "💵 Other Income", "🏦 Salary", "💎 Savings"]
expense_categories = ["🔧 Car Repairs/Maintenance", "☕️ Entertainment", "🍽️ Food", "⛽ Gas", "🛍️ Shopping", "📺 Subscriptions", "🚗 Travel", "💡 Utilities", "📦 Other Expense"]

st.markdown("""
<style>
html, body, [class*="css"]  {
    font-family: 'Segoe UI', sans-serif;
}
.main-title {
    font-size: 42px;
    color: #2e7d32;
    text-align: center;
    margin-top: 20px;
}
.subtitle {
    text-align: center;
    font-size: 16px;
    color: #888;
    margin-bottom: 30px;
}
</style>
<h1 class='main-title'>💸 Personal Budget Tracker</h1>
<p class='subtitle'>Track smart. Save better. Live richer.</p>
""", unsafe_allow_html=True)

try:
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date']).dt.normalize()
    else:
        st.error("❌ 'Date' column not found in Google Sheet.")
        st.stop()

    df['Category_clean'] = df['Category'].str.extract(r'([\w\s]+)$')[0].str.lower().str.strip()

    total_income_all = df[df['Type'] == 'Income']['Amount'].sum()
    total_expense_all = df[df['Type'] == 'Expense']['Amount'].sum()
    savings_total = total_income_all - total_expense_all

    df['Month'] = df['Date'].dt.to_period('M')
    today = pd.to_datetime(datetime.date.today())
    current_period = today.to_period('M')
    current_month_df = df[df['Month'] == current_period]

    total_income = current_month_df[current_month_df['Type'] == 'Income']['Amount'].sum()
    total_expense = current_month_df[current_month_df['Type'] == 'Expense']['Amount'].sum()
    net_balance = total_income - total_expense

    html(f'''
        <div style="text-align:center;">
            <div id='savings-box' style='display:inline-block;padding:20px;border-radius:20px;background:linear-gradient(to right, #fff3cd, #fff9e6);border:2px solid gold;box-shadow:0 4px 10px rgba(0,0,0,0.15);backdrop-filter:blur(8px);'>
                <h4 style='color:#ff6f00;margin-bottom:8px;font-size:20px;'>💎 TOTAL SAVINGS</h4>
                <h2 id='savings-value' style='color:#c62828;font-size:30px;'>₹0</h2>
            </div>
        </div>
        <script>
            let start = 0;
            let end = {savings_total};
            let duration = 1000;
            let frameRate = 20;
            let steps = duration / frameRate;
            let step = (end - start) / steps;
            let count = start;
            let interval = setInterval(function() {{
                count += step;
                if (count >= end) {{
                    count = end;
                    clearInterval(interval);
                }}
                document.getElementById("savings-value").innerText = '₹' + count.toLocaleString(undefined, {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }});
            }}, frameRate);
        </script>
    ''', height=200)

    html(f'''
        <div style='display:flex;justify-content:center;margin-top:20px;'>
            <div style='padding:20px;border-radius:20px;background:rgba(208,240,192,0.7);margin:10px;text-align:center;color:#1b5e20;'>
                <h5>💰 Monthly Income</h5><h4 id="income-val">$0.00</h4>
            </div>
            <div style='padding:20px;border-radius:20px;background:rgba(255,205,210,0.7);margin:10px;text-align:center;color:#b71c1c;'>
                <h5>💸 Monthly Expense</h5><h4 id="expense-val">$0.00</h4>
            </div>
            <div style='padding:20px;border-radius:20px;background:rgba(187,222,251,0.7);margin:10px;text-align:center;color:#0d47a1;'>
                <h5>💼 Net Balance</h5><h4 id="net-val">$0.00</h4>
            </div>
        </div>
        <script>
            function animateValue(id, end) {{
                let start = 0;
                let duration = 1000;
                let frameRate = 20;
                let steps = duration / frameRate;
                let step = (end - start) / steps;
                let count = start;
                let el = document.getElementById(id);
                let interval = setInterval(function() {{
                    count += step;
                    if (count >= end) {{
                        count = end;
                        clearInterval(interval);
                    }}
                    el.innerText = '$' + count.toLocaleString(undefined, {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }});
                }}, frameRate);
            }}
            animateValue("income-val", {total_income});
            animateValue("expense-val", {total_expense});
            animateValue("net-val", {net_balance});
        </script>
    ''', height=200)

    # MAIN APP UI
    col1, col2 = st.columns([1, 2])
    with col1:
        st.header("➕ Add Transaction")
        trans_date = st.date_input("Date", today)
        trans_type = st.radio("Type", ["Income", "Expense"])
        category_options = income_categories if trans_type == "Income" else expense_categories
        category = st.radio("Category", category_options)
        description = st.text_input("Description")
        amount = st.number_input("Amount", min_value=0.0, format="%.2f")
        if st.button("Add Transaction"):
            try:
                sheet.append_row([str(trans_date), trans_type, category, description, amount])
                st.success("✅ Added!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

        st.subheader("🗑 Manage Today's Transactions")
        today_data = df[df['Date'] == today]
        if not today_data.empty:
            selected_index = st.selectbox("Select a transaction to delete", options=today_data.index.tolist(),
                                          format_func=lambda x: f"{today_data.loc[x, 'Category']} | ${today_data.loc[x, 'Amount']} | {today_data.loc[x, 'Description']}")
            if st.button("❌ Delete Selected Transaction"):
                sheet.delete_rows(selected_index + 2)
                st.success("✅ Transaction deleted!")
                st.rerun()

            confirm_reset = st.radio("Are you sure you want to reset all transactions for today?", ("No", "Yes"))
            if confirm_reset == "Yes" and st.button("🚫 Reset All Today's Transactions"):
                for row in sorted(today_data.index, reverse=True):
                    sheet.delete_rows(row + 2)
                st.success("✅ All today's transactions deleted.")
                st.rerun()
        else:
            st.info("ℹ️ No transactions found for today.")

    with col2:
        st.header("📊 Reports")
        report_type = st.radio("Report Type", ["Daily", "Monthly"])
        if report_type == "Daily":
            selected_date = st.date_input("Select Date", today)
            filtered = df[df['Date'] == pd.to_datetime(selected_date)]
        else:
            selected_month = st.selectbox("Select Month", sorted(df['Month'].astype(str).unique()), index=len(df['Month'].unique()) - 1)
            selected_period = pd.Period(selected_month)
            filtered = df[df['Month'] == selected_period]

        if not filtered.empty:
            inc = filtered[filtered['Type'] == 'Income']['Amount'].sum()
            exp = filtered[filtered['Type'] == 'Expense']['Amount'].sum()
            net = inc - exp
            c1, c2, c3 = st.columns(3)
            c1.metric("💰 Income", f"${inc:.2f}")
            c2.metric("💸 Expense", f"${exp:.2f}")
            c3.metric("💼 Net", f"${net:.2f}")

            if report_type == "Daily":
                st.dataframe(filtered[['Date', 'Type', 'Category', 'Amount', 'Description']])
        else:
            st.info("No transactions for this period.")

except Exception as e:
    st.error(f"❌ Failed to load data from Google Sheet: {e}")
