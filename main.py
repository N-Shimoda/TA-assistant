import streamlit as st

pg = st.navigation(
    [
        st.Page("pages/Home.py", title="Home", icon="🏠"),
        st.Page("pages/Grading.py", title="Grading", icon="✏️"),
        st.Page("pages/Allocation.py", title="Allocation", icon="📊"),
        st.Page("pages/Config.py", title="Config", icon="⚙️"),
    ]
)
pg.run()
