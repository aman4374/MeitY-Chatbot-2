import streamlit as st
import sys
import platform

st.set_page_config(page_title="Azure Test App", layout="wide")
st.title("✅ Success! Your Azure App Service is Working.")
st.write("This is a minimal Streamlit application.")
st.info(f"Python Version: {sys.version}")
st.info(f"Platform: {platform.platform()}")
st.balloons()