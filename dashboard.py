import streamlit as st
import pandas as pd
from predictor import LotteryForecastEngine

from auto_fetcher import fetch_lotteryusa_results, STATE_SLUGS

st.set_page_config(

    page_title="Lottery Forecast Engine Ultra",

    layout="wide"

)

st.title("Lottery Forecast Engine Ultra")

st.caption("Prediction tool using frequency, hot digits, pairs, mirrors, and recent draw weighting.")

state = st.selectbox("Choose State", list(STATE_SLUGS.keys()))

st.write("Upload recent Pick 3 results as a CSV with a column named `number`.")

uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

draws = []

if uploaded_file:

    df = pd.read_csv(uploaded_file)

    if "number" not in df.columns:

        st.error("CSV must contain a column named `number`.")

        st.stop()

    draws = df["number"].astype(str).str.zfill(3).tolist()

else:

    st.info("No CSV uploaded. Using demo data so the app can run.")

    draws = [

        "123", "456", "789", "555", "321", "111", "890", "234", "567", "678",

        "222", "333", "444", "345", "901", "210", "120", "777", "888", "999"

    ]

engine = LotteryForecastEngine(draws)

st.subheader("Top Pick 3 Predictions")

predictions = engine.generate_predictions(limit=25)

prediction_df = pd.DataFrame(predictions)

st.dataframe(prediction_df, use_container_width=True)

summary = engine.summary_tables()

col1, col2, col3 = st.columns(3)

with col1:

    st.subheader("Hot Digits")

    st.dataframe(pd.DataFrame(summary["hot_digits"], columns=["Digit", "Hits"]))

with col2:

    st.subheader("Hot Numbers")

    st.dataframe(pd.DataFrame(summary["hot_numbers"], columns=["Number", "Hits"]))

with col3:

    st.subheader("Hot Pairs")

    st.dataframe(pd.DataFrame(summary["hot_pairs"], columns=["Pair", "Hits"]))

st.subheader("How Scores Work")

st.write("""

Higher scores mean the number is showing stronger historical activity based on:

- repeated number hits

- hot digit strength

- strong front/back pairs

- mirror number activity

- recent draw activity

- double/triple number boost

""")

st.warning("This tool improves analysis, but lottery drawings are still not guaranteed.")
