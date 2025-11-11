import pandas as pd
import streamlit as st

st.set_page_config(page_title="CSV Explorer", page_icon="🧮", layout="wide")
st.title("CSV Explorer")

uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"]) 

if uploaded_file is not None:
    try:
        dataframe = pd.read_csv(uploaded_file)
        st.success(f"Loaded {len(dataframe)} rows")
        st.dataframe(dataframe, use_container_width=True)
        st.download_button(
            "Download filtered CSV",
            data=dataframe.to_csv(index=False).encode("utf-8"),
            file_name="filtered.csv",
            mime="text/csv",
        )
    except Exception as exc:  # pragma: no cover
        st.error(f"Unable to parse CSV: {exc}")
else:
    st.info("Upload a CSV to begin exploring your data.")
