import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, GRU, Dense
import xgboost as xgb
import datetime

# Common Data Fetching & Analysis
def get_stock_data(ticker, period='5y'):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        if df.empty:
            return None
        return df
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def get_market_summary():
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'BTC-USD', 'ETH-USD', '^GSPC']
    summary = []
    try:
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                info = stock.fast_info
                price = info.last_price
                prev_close = info.previous_close
                change = price - prev_close
                change_pct = (change / prev_close) * 100
                summary.append({
                    'ticker': ticker,
                    'price': price,
                    'change': change,
                    'change_pct': change_pct
                })
            except:
                continue
    except Exception as e:
        print(f"Error fetching market summary: {e}")
    return summary

def get_recommendation(df):
    close = df['Close']
    rsi_series = calculate_rsi(close)
    current_rsi = rsi_series.iloc[-1]
    sma_50 = close.rolling(window=50).mean().iloc[-1]
    current_price = close.iloc[-1]
    
    signals = []
    score = 0
    
    if current_rsi < 30:
        signals.append("RSI is Oversold (Buy Signal)")
        score += 1
    elif current_rsi > 70:
        signals.append("RSI is Overbought (Sell Signal)")
        score -= 1
    else:
        signals.append(f"RSI is Neutral ({current_rsi:.2f})")
        
    if current_price > sma_50:
        signals.append("Price is above 50-day SMA (Uptrend)")
        score += 1
    else:
        signals.append("Price is below 50-day SMA (Downtrend)")
        score -= 1
        
    if score >= 2:
        recommendation = "STRONG BUY"
        color = "green"
    elif score == 1:
        recommendation = "BUY"
        color = "lightgreen"
    elif score == 0:
        recommendation = "HOLD"
        color = "gray"
    elif score == -1:
        recommendation = "SELL"
        color = "orange"
    else:
        recommendation = "STRONG SELL"
        color = "red"
        
    return {
        'recommendation': recommendation,
        'color': color,
        'rsi': float(current_rsi),
        'current_price': float(current_price),
        'sma_50': float(sma_50) if not np.isnan(sma_50) else None,
        'signals': signals
    }

# --- Data Preparation ---
def prepare_sequence_data(data, look_back=60):
    """Prepares data for LSTM/GRU (3D array)"""
    dataset = data['Close'].values.reshape(-1, 1)
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(dataset)
    
    X, y = [], []
    for i in range(look_back, len(scaled_data)):
        X.append(scaled_data[i-look_back:i, 0])
        y.append(scaled_data[i, 0])
        
    X, y = np.array(X), np.array(y)
    X = np.reshape(X, (X.shape[0], X.shape[1], 1))
    return X, y, scaler, scaled_data

def prepare_flat_data(data, look_back=60):
    """Prepares data for ML models (2D array)"""
    dataset = data['Close'].values
    X, y = [], []
    for i in range(look_back, len(dataset)):
        X.append(dataset[i-look_back:i])
        y.append(dataset[i])
    X, y = np.array(X), np.array(y)
    return X, y

# --- Deep Learning Models ---
def run_dl_model(df, look_back, forecast_days, model_type='lstm'):
    X, y, scaler, scaled_data = prepare_sequence_data(df, look_back)
    training_size = int(len(X) * 0.8)
    X_train, X_test = X[:training_size], X[training_size:]
    y_train, y_test = y[:training_size], y[training_size:]
    
    model = Sequential()
    if model_type == 'lstm':
        model.add(LSTM(units=50, return_sequences=True, input_shape=(X_train.shape[1], 1)))
        model.add(LSTM(units=50, return_sequences=False))
    elif model_type == 'gru':
        model.add(GRU(units=50, return_sequences=True, input_shape=(X_train.shape[1], 1)))
        model.add(GRU(units=50, return_sequences=False))
        
    model.add(Dense(units=25))
    model.add(Dense(units=1))
    model.compile(optimizer='adam', loss='mean_squared_error')
    
    model.fit(X_train, y_train, batch_size=32, epochs=5, verbose=0)
    
    predictions = model.predict(X_test, verbose=0)
    predictions = scaler.inverse_transform(predictions)
    y_test_scaled = scaler.inverse_transform(y_test.reshape(-1, 1))
    
    mse = mean_squared_error(y_test_scaled, predictions)
    rmse = np.sqrt(mse)
    
    # Future
    last_sequence = scaled_data[-look_back:]
    curr_sequence = last_sequence.reshape(1, look_back, 1)
    future_predictions = []
    
    for _ in range(forecast_days):
        next_pred = model.predict(curr_sequence, verbose=0)
        future_predictions.append(next_pred[0, 0])
        next_val = next_pred.reshape(1, 1, 1)
        curr_sequence = np.append(curr_sequence[:, 1:, :], next_val, axis=1)
        
    future_predictions = scaler.inverse_transform(np.array(future_predictions).reshape(-1, 1))
    
    return predictions, future_predictions, rmse, look_back + training_size

# --- Machine Learning Models ---
def run_ml_model(df, look_back, forecast_days, model_type='linear'):
    X, y = prepare_flat_data(df, look_back)
    training_size = int(len(X) * 0.8)
    X_train, X_test = X[:training_size], X[training_size:]
    y_train, y_test = y[:training_size], y[training_size:]
    
    if model_type == 'linear':
        model = LinearRegression()
    elif model_type == 'random_forest':
        model = RandomForestRegressor(n_estimators=100, random_state=42)
    elif model_type == 'xgboost':
        model = xgb.XGBRegressor(objective='reg:squarederror', n_estimators=100, seed=42)
        
    model.fit(X_train, y_train)
    
    predictions = model.predict(X_test)
    mse = mean_squared_error(y_test, predictions)
    rmse = np.sqrt(mse)
    
    # Future
    curr_sequence = df['Close'].values[-look_back:]
    future_predictions = []
    
    for _ in range(forecast_days):
        # Reshape for prediction (1 sample, look_back features)
        next_pred = model.predict(curr_sequence.reshape(1, -1))
        val = next_pred[0]
        future_predictions.append(val)
        # Update sequence: remove first, add new prediction
        curr_sequence = np.append(curr_sequence[1:], val)
        
    return predictions.reshape(-1, 1), np.array(future_predictions).reshape(-1, 1), rmse, look_back + training_size

# Main Dispatcher
def train_and_predict(ticker, look_back=60, forecast_days=5, model_type='lstm'):
    df = get_stock_data(ticker)
    if df is None:
        return {'error': 'Could not fetch data.'}
    
    dates = df.index.strftime('%Y-%m-%d').tolist()
    close_prices = df['Close'].values.tolist()
    
    if model_type in ['lstm', 'gru']:
        predictions, future_predictions, rmse, test_start_idx = run_dl_model(df, look_back, forecast_days, model_type)
    else:
        predictions, future_predictions, rmse, test_start_idx = run_ml_model(df, look_back, forecast_days, model_type)
        
    test_dates = dates[test_start_idx:]
    
    last_date = datetime.datetime.strptime(dates[-1], '%Y-%m-%d')
    future_dates = []
    current_date = last_date
    for _ in range(forecast_days):
        current_date += datetime.timedelta(days=1)
        future_dates.append(current_date.strftime('%Y-%m-%d'))
        
    analysis = get_recommendation(df)
    
    return {
        'ticker': ticker.upper(),
        'model': model_type,
        'dates': dates,
        'actual_prices': close_prices,
        'test_dates': test_dates,
        'test_predictions': predictions.flatten().tolist(),
        'future_dates': future_dates,
        'future_predictions': future_predictions.flatten().tolist(),
        'metrics': {'rmse': float(rmse)},
        'summary': {
            'look_back': look_back,
            'forecast_days': forecast_days,
            'last_date': dates[-1],
            'last_predicted_date': future_dates[-1],
            'last_predicted_price': float(future_predictions[-1][0])
        },
        'analysis': analysis
    }
