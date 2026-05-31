# 🏎️ F1 Tyre Degradation Analyzer

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red.svg)
![FastF1](https://img.shields.io/badge/Data-FastF1-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Status](https://img.shields.io/badge/Status-Active-success.svg)

---

## 🚀 Overview
An advanced **Formula 1 analytics dashboard** that analyzes and predicts **tyre degradation** using real race data.

Built with data science and time-series modeling, this project helps visualize how tyre performance evolves and forecasts future degradation trends — just like real F1 strategy teams.



## ✨ Features

- 📥 Fetch real race data using **FastF1 API**
- 📊 Interactive dashboard with **Streamlit**
- 📉 Calculate **cumulative tyre degradation**
- 🌦️ Weather correlation (Track temp, Air temp, Humidity)
- 🔮 Predict future degradation using **ARIMA**
- 🔁 Fallback to **Linear Regression**
- 🏁 Multi-race comparison
- 📂 Export data as CSV

---

## 🧠 Tech Stack

| Category        | Tools Used |
|----------------|----------|
| Language       | Python |
| Data Handling  | Pandas, NumPy |
| Visualization  | Matplotlib, Seaborn |
| ML Models      | ARIMA (Statsmodels), Linear Regression |
| Data Source    | FastF1 |
| Frontend       | Streamlit |

---

## 📊 How It Works

```mermaid
graph TD
A[Load Race Data] --> B[Process Lap Times]
B --> C[Calculate Degradation]
C --> D[Merge Weather Data]
D --> E[Train ARIMA Model]
E --> F[Predict Future Laps]
F --> G[Visualize in Dashboard]
