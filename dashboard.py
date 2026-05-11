import streamlit as st
import pandas as pd
from predictor import LotteryForecastEngine
from auto_fetcher import fetch_lotteryusa_results, STATE_SLUGS

st.set_page_config(page_title="Lottery Forecast Engine Ultra", layout="wide")

st.title("Lottery Forecast Engine Ultra")
st.caption("Stronger ensemble predictor with automatic backtest tuning.")

st.warning(
    "Ultra mode pushes the model harder by testing multiple strategies against past draws and selecting the best-performing ensemble. Scores are rankings, not guaranteed win percentages."
)

mode = st.radio("Data Mode", ["Auto Results Mode", "CSV Upload Backup"], horizontal=True)

col1, col2, col3 = st.columns(3)
with col1:
    state_list = sorted(STATE_SLUGS.keys())
    state = st.selectbox("State", state_list, index=state_list.index("SC"))
with col2:
    game = st.selectbox("Game", ["pick3", "pick4"])
with col3:
    draw = st.selectbox("Draw", ["both", "midday", "evening"])

top_n = st.slider("How many straight picks to display?", 10, 100, 25, 5)

df = None

if mode == "Auto Results Mode":
    if st.button("Fetch Results, Tune Model & Predict", type="primary"):
        with st.spinner("Fetching results, tuning models, backtesting, and ranking predictions..."):
            try:
                df = fetch_lotteryusa_results(state, game=game, draw=draw, limit=150)
                if df is None or len(df) < 20:
                    st.error("Auto fetch did not return enough previous results. Try CSV Upload Backup.")
                    df = None
            except Exception as e:
                st.error(f"Auto fetch failed: {e}")
                df = None
else:
    uploaded = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded:
        df = pd.read_csv(uploaded)

if df is not None:
    st.subheader("Previous Results Used")
    st.dataframe(df, use_container_width=True)

    try:
        engine = LotteryForecastEngine(df, game=game, state=state, draw=draw)
        predictions, tuned = engine.ensemble_predict(top_n=top_n)
        best_name, best_weights, best_backtest, best_objective = tuned[0]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Results Loaded", len(engine.numbers))
        c2.metric("Best Model", best_name)
        c3.metric("Top 25 Straight", f"{best_backtest.get('top25_straight', 0)}%")
        c4.metric("Top 25 Boxed", f"{best_backtest.get('top25_boxed', 0)}%")

        st.subheader("Ultra Ensemble Straight Picks")
        pred_df = pd.DataFrame(predictions, columns=["Number", "Raw Ensemble Score", "Strength 0-100", "Tier"])
        st.dataframe(pred_df, use_container_width=True)

        st.subheader("Ultra Boxed Picks")
        boxed = engine.boxed_from_ranked(predictions, top_n=15)
        st.dataframe(pd.DataFrame(boxed, columns=["Box", "Combined Raw Score"]), use_container_width=True)

        st.subheader("Model Backtest Comparison")
        rows = []
        for name, weights, bt, objective in tuned:
            row = {"Model": name, "Objective": round(objective, 2)}
            row.update(bt)
            rows.append(row)
        st.dataframe(pd.DataFrame(rows), use_container_width=True)

        st.subheader("70–80% Target Check")
        max_boxed = max(x[2].get("top50_boxed", 0) for x in tuned)
        max_straight = max(x[2].get("top50_straight", 0) for x in tuned)
        st.write(f"Best tested Top 50 boxed coverage: **{max_boxed}%**")
        st.write(f"Best tested Top 50 straight coverage: **{max_straight}%**")
        st.write("If the model ever reaches 70–80% in backtesting, this section will show it clearly instead of guessing.")

    except Exception as e:
        st.error(f"Prediction failed: {e}")
else:
    st.info("Use Auto Results Mode, or upload a CSV with columns: date, state, game, draw, number.")