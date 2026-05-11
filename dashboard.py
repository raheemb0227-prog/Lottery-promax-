import streamlit as st
import pandas as pd
from predictor import LotteryForecastEngine

st.set_page_config(
    page_title="Lottery Forecast Engine Ultra",
    layout="wide"
)

st.title("Lottery Forecast Engine Ultra")

st.write("Upload a CSV file with a column named 'number'.")

uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

draws = []

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    if "number" not in df.columns:
        st.error("CSV must contain a column named 'number'")
        st.stop()

    draws = df["number"].astype(str).str.zfill(3).tolist()

else:
    draws = [
        "123",
        "456",
        "789",
        "555",
        "321",
        "111",
        "222",
        "333",
        "444",
        "777"
    ]

engine = LotteryForecastEngine(draws)

predictions = engine.generate_predictions(limit=25)

prediction_df = pd.DataFrame(predictions)

st.subheader("Top Predictions")

st.dataframe(prediction_df)
