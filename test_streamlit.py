import streamlit as st

st.title("Test Streamlit")
st.write("Si ves esto, Streamlit funciona")

tab1, tab2 = st.tabs(["Tab 1", "Tab 2"])

with tab1:
    st.write("Tab 1 content")

with tab2:
    st.write("Tab 2 content")