import streamlit as st
from datetime import datetime

st.title("Portfolio Test")

tab1, tab2 = st.tabs(["Add Card", "View Portfolio"])

with tab1:
    st.subheader("Add Card")
    
    with st.form("test_form"):
        player = st.text_input("Player", "LeBron James")
        price = st.number_input("Price", value=100.0)
        submit = st.form_submit_button("Add")
        
        if submit:
            st.success(f"Added {player} at ${price}")

with tab2:
    st.subheader("Your Portfolio")
    st.write("Portfolio items will appear here")