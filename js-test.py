import streamlit as st
from streamlit_js_eval import streamlit_js_eval

res = streamlit_js_eval(js_expressions="window.innerHeight", key="js_height")

if res is not None:
    st.write(f"ブラウザの高さ: {res}px")
