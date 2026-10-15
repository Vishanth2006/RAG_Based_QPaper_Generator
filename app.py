"""Streamlit entry point with an explicit five-stage sidebar."""

import streamlit as st

st.set_page_config(
    page_title="RAG Question Paper Generator",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
)

pages = [
    st.Page("pages/1_Upload.py", title="Upload Documents & Syllabus", icon="📂"),
    st.Page("pages/2_Ingestion_Pipeline.py", title="RAG Ingestion Pipeline", icon="🔬"),
    st.Page("pages/3_Paper_Structure.py", title="Question Paper Structure", icon="📝"),
    st.Page("pages/4_Retrieval_Pipeline.py", title="Retrieval Pipeline", icon="🔍"),
    st.Page("pages/5_Generation.py", title="Generation & Review", icon="✨"),
]

st.navigation(pages).run()
