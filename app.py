import streamlit as st
import pandas as pd

# Set page config
st.set_page_config(page_title="Tuck Shop Price List", layout="wide")

# Title
st.title("🛍️ Tuck Shop Price List")

# Load the CSV file
df = pd.read_csv('tuck_shop_items.csv')

# Display the dataframe as a locked, read-only table
st.dataframe(df, use_container_width=True, disabled=True)

# Optional: Add some stats
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Items", len(df))

with col2:
    st.metric("Categories", df['Category'].nunique())

with col3:
    st.metric("Average Price", f"£{df['Price'].mean():.2f}")
