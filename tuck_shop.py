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

# Load the data
try:
    df = pd.read_csv("tuck_shop_items.csv")
except FileNotFoundError:
    st.error("Couldn't find tuck_shop_items.csv. Make sure it's in the same folder as app.py.")
    st.stop()

# Clean up column names just in case of stray spaces
df.columns = [c.strip() for c in df.columns]

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
        st.markdown(f"**{row['Item']}** — £{row['Price']:.2f}{note}")
    st.divider()

# --- Full list, grouped by category ---
st.subheader("Full Price List")

if filtered.empty:
    st.info("No items match your search.")
else:
    for category in sorted(filtered["Category"].dropna().unique()):
        st.markdown(f"### {category}")
        cat_items = filtered[filtered["Category"] == category]
        # Simple table: Item + Price
        display_df = cat_items[["Item", "Price"]].copy()
        display_df["Price"] = display_df["Price"].apply(lambda p: f"£{p:.2f}")
        st.table(display_df.set_index("Item"))

st.divider()
st.caption("Prices last updated by editing tuck_shop_items.csv in GitHub.")
