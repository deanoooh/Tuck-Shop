import os
import csv
import smtplib
from datetime import datetime
from email.message import EmailMessage

import streamlit as st
import pandas as pd

# ----------------------------------------------------
# TUCK SHOP PRICE LIST
# This app reads "tuck_shop_items.csv" and displays it.
# To change prices/stock/sales, just edit that CSV file
# in GitHub - you never need to touch this code again.
# ----------------------------------------------------

st.set_page_config(page_title="Tuck Shop", page_icon="🛒", layout="centered")

st.title("🛒 Tuck Shop Price List")
st.caption("Prices and sale items — pay via the honesty box as usual!")


def save_suggestion_to_csv(name: str, suggestion: str):
    suggestions_file = os.path.join(os.path.dirname(__file__) or ".", "suggestions.csv")
    file_exists = os.path.exists(suggestions_file)

    with open(suggestions_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Timestamp", "Name", "Suggestion"])
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            name.strip() if name.strip() else "Anonymous",
            suggestion.strip(),
        ])


def send_suggestion_email(name: str, suggestion: str):
    recipient = os.environ.get("SUGGESTION_EMAIL")
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "465"))
    smtp_user = os.environ.get("SMTP_USERNAME") or os.environ.get("SMTP_EMAIL")
    smtp_password = os.environ.get("SMTP_PASSWORD")

    if not recipient or not smtp_user or not smtp_password:
        raise ValueError(
            "Missing email configuration. Set SUGGESTION_EMAIL, SMTP_USERNAME/SMTP_EMAIL, and SMTP_PASSWORD."
        )

    message = EmailMessage()
    message["Subject"] = "New Tuck Shop Suggestion"
    message["From"] = smtp_user
    message["To"] = recipient
    message.set_content(
        f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        f"Name: {name}\n\n"
        f"Suggestion:\n{suggestion}"
    )

    with smtplib.SMTP_SSL(smtp_server, smtp_port) as smtp:
        smtp.login(smtp_user, smtp_password)
        smtp.send_message(message)


# Load the data
try:
    df = pd.read_csv("tuck_shop_items.csv")
except FileNotFoundError:
    st.error("Couldn't find tuck_shop_items.csv. Make sure it's in the same folder as app.py.")
    st.stop()

# Clean up column names just in case of stray spaces
df.columns = [c.strip() for c in df.columns]

# Make sure prices are numbers. The CSV's spreadsheet formulas are not evaluated
# by pandas, so calculate the saving here for display in the app.
df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
df["Supermarket RRP"] = pd.to_numeric(df["Supermarket RRP"], errors="coerce")
df["Saving"] = (df["Supermarket RRP"] - df["Price"]).round(2)

# --- Search box ---
search = st.text_input("🔍 Search for an item")

# --- Category filter ---
categories = ["All"] + sorted(df["Category"].dropna().unique().tolist())
selected_category = st.selectbox("Filter by category", categories)

# Apply filters
filtered = df.copy()
if search:
    filtered = filtered[filtered["Item"].str.contains(search, case=False, na=False)]
if selected_category != "All":
    filtered = filtered[filtered["Category"] == selected_category]

# --- Sale items section (shown first, if any exist) ---
sale_items = filtered[filtered["On Sale"].astype(str).str.strip().str.lower() == "yes"]
if not sale_items.empty:
    st.subheader("🔥 On Sale This Week")
    for _, row in sale_items.iterrows():
        note = f" — {row['Sale Note']}" if pd.notna(row["Sale Note"]) and str(row["Sale Note"]).strip() else ""
        supermarket_value = ""
        if pd.notna(row["Supermarket RRP"]):
            supermarket_value = f" — supermarket £{row['Supermarket RRP']:.2f}"
            if pd.notna(row["Saving"]):
                supermarket_value += f" (save £{row['Saving']:.2f})"
        st.markdown(
            f"**{row['Item']}** — **£{row['Price']:.2f}**{supermarket_value}{note}"
        )
    st.divider()

# --- Full list, grouped by category ---
st.subheader("Full Price List")

if filtered.empty:
    st.info("No items match your search.")
else:
    for category in sorted(filtered["Category"].dropna().unique()):
        st.markdown(f"### {category}")
        cat_items = filtered[filtered["Category"] == category]

        # Combine the supermarket RRP and saving into one compact value column.
        display_df = cat_items[["Item", "Price", "Supermarket RRP", "Saving"]].copy()
        display_df["Supermarket Value"] = display_df.apply(
            lambda row: (
                f"£{row['Supermarket RRP']:.2f} (save £{row['Saving']:.2f})"
                if pd.notna(row["Supermarket RRP"]) and pd.notna(row["Saving"])
                else f"£{row['Supermarket RRP']:.2f}"
                if pd.notna(row["Supermarket RRP"])
                else ""
            ),
            axis=1,
        )
        display_df = display_df[["Item", "Price", "Supermarket Value"]].rename(
            columns={"Price": "Tuck Shop Price"}
        ).set_index("Item")

        # Keep the tuck-shop price bold and the combined supermarket value muted.
        styled_df = (
            display_df.style
            .format({
                "Tuck Shop Price": lambda p: f"£{p:.2f}" if pd.notna(p) else "",
            })
            .apply(
                lambda s: s.map(lambda v: "font-weight: bold;" if pd.notna(v) else ""),
                subset=["Tuck Shop Price"],
            )
            .apply(
                lambda s: s.map(lambda v: "color: #6c757d;" if pd.notna(v) and v else ""),
                subset=["Supermarket Value"],
            )
        )
        st.dataframe(styled_df, use_container_width=True)

st.divider()
st.caption("Prices last updated by editing tuck_shop_items.csv in GitHub.")

# --- Feedback section ---
st.subheader("💬 Got a suggestion?")
st.caption("Let us know what items you'd like to see in the Tuck Shop!")

with st.form("feedback_form", clear_on_submit=True):
    name = st.text_input("Your name (optional)")
    suggestion = st.text_area(
        "What would you like us to stock?",
        placeholder="e.g. Almond butter, Oat milk, Energy bars...",
        height=100,
    )
    submitted = st.form_submit_button("Submit Suggestion", use_container_width=True)

    if submitted:
        if suggestion.strip():
            clean_name = name.strip() if name.strip() else "Anonymous"
            clean_suggestion = suggestion.strip()

            # Always keep a local backup in the repository/app folder.
            save_suggestion_to_csv(clean_name, clean_suggestion)

            # Try to send an email if SMTP is configured.
            email_ok = False
            try:
                send_suggestion_email(clean_name, clean_suggestion)
                email_ok = True
            except Exception as exc:
                st.warning(
                    "✅ Suggestion saved locally, but email alert failed. "
                    f"Check your SMTP settings: {exc}"
                )

            if email_ok:
                st.success(
                    "✅ Thanks for your suggestion! It has been saved locally and emailed to the configured inbox."
                )
        else:
            st.warning("Please enter a suggestion before submitting.")
