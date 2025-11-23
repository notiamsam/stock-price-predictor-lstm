# 🚀 ProPredict: Next-Gen AI Stock Analysis Platform

![ProPredict Dashboard](static/screenshot.png)

**ProPredict** is a cutting-edge financial intelligence platform that fuses advanced Deep Learning algorithms with state-of-the-art Large Language Models to provide unparalleled market insights.

Unlike traditional tools, ProPredict doesn't just show you charts—it **understands** the market. By combining quantitative analysis (LSTM/GRU/XGBoost) with qualitative intelligence (GPT-5.1/Gemini 3 Pro), it offers a holistic view of any asset's future potential.

---

## ✨ Key Features

### 🧠 Advanced Neural Forecasting
Harness the power of multiple deep learning architectures to predict future price movements with high precision.
- **LSTM & GRU Networks:** Deep neural networks capable of learning long-term dependencies in time-series data.
- **Ensemble ML Models:** Integrated Random Forest and XGBoost engines for robust, data-driven validation.
- **Dynamic Forecasting:** Customize look-back periods and forecast horizons to suit your trading strategy.

### 💬 Intelligent Market Assistant
Engage with our sophisticated AI analyst, powered by the world's most advanced language engines.
- **Supported Engines:** **GPT-5.1**, **GPT-5 Mini**, **GPT-4o**, **Gemini 3 Pro**, and **Gemini 2.5 Flash**.
- **Context-Aware:** The AI isn't just a chatbot—it's fed real-time technical indicators (RSI, SMA, Trends) and price data to give you highly specific analysis.
- **Real-Time Web Intelligence:** The system autonomously surfs the live internet to fetch breaking news and headlines, interpreting how global events impact your specific stock.

### 📊 Professional-Grade Visualization
- **Interactive Financial Charts:** powered by Chart.js with dark-mode aesthetics.
- **Technical Indicators:** Real-time calculation of RSI, Moving Averages, and volatility metrics.
- **Live Market Watch:** Real-time side-panel updates for major indices and tech giants.

### ⚡ Real-Time News Integration
Never miss a beat. The system performs **semantic live searches** across the web to bring you the latest financial news, earnings reports, and market rumors, instantly summarized by the AI engine.

---

## 🛠️ Technical Stack

- **Core Engine:** Python 3.9+, Flask
- **Deep Learning:** TensorFlow, Keras
- **Machine Learning:** Scikit-learn, XGBoost
- **AI Integration:** OpenAI SDK, Google Generative AI, DuckDuckGo Search (for live web access)
- **Data Pipeline:** yfinance (Real-time market data)
- **Frontend:** HTML5, CSS3 (Glassmorphism Design), JavaScript (ES6+)

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/notiamsam/stock-price-predictor-lstm.git
   cd stock-price-predictor-lstm
   ```

2. **Set Up Virtual Environment (Recommended)**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Mac/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API Access**
   - Launch the app and click the **Settings (⚙️)** icon in the header.
   - Enter your keys for the AI engines (OpenAI / Gemini) to unlock the chat capabilities.
   - *Note: Prediction features work without API keys; keys are only needed for the Chat Assistant.*

### Running the Application

1. **Start the Server**
   ```bash
   python app.py
   ```

2. **Access the Dashboard**
   Open your browser and navigate to:
   [http://localhost:5000](http://localhost:5000)

---

## 🔮 Usage Guide

1. **Analyze a Stock:** Enter a ticker (e.g., `NVDA`, `BTC-USD`) in the search bar.
2. **Select Model:** Choose between Deep Learning (LSTM/GRU) or faster ML models (Linear/RF).
3. **View Predictions:** Watch the neural network train in real-time and render the forecast chart.
4. **Ask the AI:** Use the chat interface to ask questions like:
   - *"Why is the stock down today?"* (Triggers live news search)
   - *"Is the RSI indicating an oversold condition?"*
   - *"Summarize the latest earnings report."*

---

## 📸 Screenshots

### Dashboard & Prediction
![Dashboard](static/screenshot.png)

### AI Chat with Real-Time News
*(Add your chat screenshot here)*

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
