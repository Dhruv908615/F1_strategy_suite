import fastf1
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import r2_score
import numpy as np
import streamlit as st
import os


if not os.path.exists('cache_dir'):
    os.makedirs('cache_dir')
fastf1.Cache.enable_cache('cache_dir')

def load_f1_data(year, race_name, session_type='R'):
    """Load F1 session data for a specific race."""
    try:
        session = fastf1.get_session(year, race_name, session_type)
        session.load()
        return session
    except Exception as e:
        print(f"Error loading data for {race_name}: {e}")
        return None

def load_weather_data(session):
    """Load and process weather data from the session."""
    try:
        weather = session.weather_data
        
        weather_agg = weather.groupby('Time').agg({'AirTemp': 'mean', 'Humidity': 'mean', 'TrackTemp': 'mean'}).reset_index()
        return weather_agg
    except:
        return pd.DataFrame()

def calculate_degradation(laps_df, weather_df=None):
    """Calculate tire degradation, optionally incorporating weather."""
    
    laps_df = laps_df.dropna(subset=['LapTime', 'Compound'])
    
    
    if not weather_df.empty:
        laps_df = pd.merge_asof(laps_df.sort_values('Time'), weather_df.sort_values('Time'), on='Time', direction='backward')
        laps_df.fillna(method='ffill', inplace=True)
    
    
    degradation_data = []
    for driver in laps_df['Driver'].unique():
        driver_laps = laps_df[laps_df['Driver'] == driver].copy()
        driver_laps = driver_laps.sort_values('LapNumber')
        
        
        driver_laps['TimeDelta'] = driver_laps['LapTime'].diff().fillna(pd.Timedelta(0))
        driver_laps['CumulativeDegradation'] = driver_laps['TimeDelta'].cumsum()
        
        driver_laps['CumulativeDegradation'] = driver_laps['CumulativeDegradation'].dt.total_seconds()
        
        degradation_data.append(driver_laps[['LapNumber', 'Driver', 'Compound', 'CumulativeDegradation', 'LapTime'] +(['AirTemp', 'Humidity', 'TrackTemp'] if 'AirTemp' in driver_laps.columns else [])])
    
    return pd.concat(degradation_data, ignore_index=True)

def predict_degradation_arima(degradation_df, future_laps=5):
    """Predict degradation using ARIMA time-series model."""
    predictions = {}
    for driver in degradation_df['Driver'].unique():
        data = degradation_df[degradation_df['Driver'] == driver]
        if len(data) < 10:
            continue
        series = data.set_index('LapNumber')['CumulativeDegradation']
        
        
        try:
            model = ARIMA(series, order=(2, 1, 2))
            model_fit = model.fit()
            
            
            forecast = model_fit.forecast(steps=future_laps)
            future_laps_nums = np.arange(data['LapNumber'].max() + 1, data['LapNumber'].max() + future_laps + 1)
            predictions[driver] = (future_laps_nums, forecast.values)
            
            
            fitted = model_fit.fittedvalues
            r2 = r2_score(series[1:], fitted)
            print(f"{driver} ARIMA R-squared: {r2:.2f}")
        except:
            print(f"ARIMA failed for {driver}; falling back to linear.")
            
            from sklearn.linear_model import LinearRegression
            X = data[['LapNumber']].values
            y = data['CumulativeDegradation'].values
            model = LinearRegression()
            model.fit(X, y)
            future_X = np.arange(data['LapNumber'].max() + 1, data['LapNumber'].max() + future_laps + 1).reshape(-1, 1)
            pred_y = model.predict(future_X)
            predictions[driver] = (future_X.flatten(), pred_y)
    
    return predictions

def analyze_multiple_races(year, races_list):
    """Analyze degradation across multiple races."""
    all_degradations = []
    for race in races_list:
        session = load_f1_data(year, race)
        if session:
            weather = load_weather_data(session)
            laps = session.laps
            degradation = calculate_degradation(laps, weather)
            degradation['Race'] = race
            all_degradations.append(degradation)
    return pd.concat(all_degradations, ignore_index=True) if all_degradations else pd.DataFrame()


st.title("F1 Tyre Degradation Analyzer (Enhanced)")
year = st.selectbox("Select Year", [2022, 2023])
races = st.multiselect("Select Races", ["Monaco", "Silverstone", "Spa", "Monza", "Bahrain", "Austin", "Abu Dhabi"], default=["Monaco"])  
selected_race = st.selectbox("Select Race for Detailed Analysis", races if races else ["Monaco"])
driver = st.selectbox("Select Driver (optional)", ["All"] + ["VER", "HAM", "LEC", "PER"])
include_weather = st.checkbox("Include Weather Correlations")

if st.button("Analyze"):
    multi_data = analyze_multiple_races(year, races)
    if not multi_data.empty:
        st.subheader("Multi-Race Degradation Comparison")
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.lineplot(data=multi_data, x='LapNumber', y='CumulativeDegradation', hue='Race', ax=ax)
        st.pyplot(fig)
    
    session = load_f1_data(year, selected_race)
    if session:
        weather = load_weather_data(session) if include_weather else pd.DataFrame()
        laps = session.laps
        degradation = calculate_degradation(laps, weather)
        
        
        csv_filename = f"{selected_race.lower()}_degradation_data.csv"
        degradation.to_csv(csv_filename, index=False)
        st.download_button("Download Degradation Data as CSV", data=degradation.to_csv(index=False), file_name=csv_filename, mime='text/csv')
        
        st.subheader(f"Degradation Plot for {selected_race}")
        fig, ax = plt.subplots()
        if driver != "All":
            data = degradation[degradation['Driver'] == driver]
            sns.lineplot(data=data, x='LapNumber', y='CumulativeDegradation', hue='Compound', ax=ax)
            if include_weather and not weather.empty:
                ax2 = ax.twinx()
                sns.lineplot(data=data, x='LapNumber', y='AirTemp', ax=ax2, color='red')
                ax2.set_ylabel('Air Temp (°C)')
        else:
            sns.lineplot(data=degradation, x='LapNumber', y='CumulativeDegradation', hue='Driver', ax=ax)
        st.pyplot(fig)
        
        st.subheader("ARIMA Predictions for Next 5 Laps")
        preds = predict_degradation_arima(degradation)
        for drv, (laps_pred, deg_pred) in preds.items():
            st.write(f"**{drv}**: Predicted degradation up to lap {laps_pred[-1]}")
            st.line_chart(pd.DataFrame({'Lap': laps_pred, 'Degradation': deg_pred}))
            
