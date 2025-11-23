import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from sklearn.metrics import mean_squared_error
import datetime

def get_stock_data(ticker, period='2y'):
    """
    Fetches historical stock data from yfinance.
    """
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        if df.empty:
            return None
        return df
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def prepare_data(data, look_back=60):
    """
    Prepares data for LSTM model.
    Scales data and creates sequences.
    """
    # Use only Close price
    dataset = data['Close'].values.reshape(-1, 1)
    
    # Scale data
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(dataset)
    
    X, y = [], []
    for i in range(look_back, len(scaled_data)):
        X.append(scaled_data[i-look_back:i, 0])
        y.append(scaled_data[i, 0])
        
    X, y = np.array(X), np.array(y)
    X = np.reshape(X, (X.shape[0], X.shape[1], 1))
    
    return X, y, scaler, scaled_data

def create_lstm_model(input_shape):
    """
    Builds the LSTM model architecture.
    """
    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True, input_shape=input_shape))
    model.add(LSTM(units=50, return_sequences=False))
    model.add(Dense(units=25))
    model.add(Dense(units=1))
    
    model.compile(optimizer='adam', loss='mean_squared_error')
    return model

def train_and_predict(ticker, look_back=60, forecast_days=5):
    """
    Main function to run the pipeline:
    1. Fetch data
    2. Preprocess
    3. Train model
    4. Predict test set
    5. Predict future
    """
    # 1. Fetch Data
    # Fetch enough data to have a reasonable training set. 
    # 2y is usually enough for a demo, but we can adjust.
    df = get_stock_data(ticker, period='5y') 
    if df is None:
        return {'error': 'Could not fetch data for ticker or ticker invalid.'}
    
    # Keep dates for plotting
    dates = df.index.strftime('%Y-%m-%d').tolist()
    close_prices = df['Close'].values.tolist()
    
    # 2. Preprocess
    X, y, scaler, scaled_data = prepare_data(df, look_back)
    
    # Split into train and test
    training_size = int(len(X) * 0.8)
    X_train, X_test = X[:training_size], X[training_size:]
    y_train, y_test = y[:training_size], y[training_size:]
    
    # 3. Train Model
    model = create_lstm_model((X_train.shape[1], 1))
    model.fit(X_train, y_train, batch_size=32, epochs=5, verbose=0) # Low epochs for demo speed
    
    # 4. Predict Test Set
    predictions = model.predict(X_test)
    predictions = scaler.inverse_transform(predictions)
    y_test_scaled = scaler.inverse_transform(y_test.reshape(-1, 1))
    
    # Calculate Metrics
    mse = mean_squared_error(y_test_scaled, predictions)
    rmse = np.sqrt(mse)
    
    # Align predictions with dates
    # The first 'look_back' points are used for the first prediction, so predictions start at index 'look_back'
    # But we split X into train and test.
    # X starts at index 'look_back' of the original data.
    # X_test starts at 'training_size' index of X.
    # So X_test corresponds to original data indices: look_back + training_size to end.
    
    test_start_index = look_back + training_size
    test_dates = dates[test_start_index:]
    
    # 5. Predict Future
    # Start with the last 'look_back' days of data
    last_sequence = scaled_data[-look_back:]
    curr_sequence = last_sequence.reshape(1, look_back, 1)
    
    future_predictions = []
    
    for _ in range(forecast_days):
        next_pred = model.predict(curr_sequence, verbose=0)
        future_predictions.append(next_pred[0, 0])
        
        # Update sequence: remove first, add new prediction
        # Reshape next_pred to (1, 1, 1) to match dimensions if needed, or just append
        next_val = next_pred.reshape(1, 1, 1)
        curr_sequence = np.append(curr_sequence[:, 1:, :], next_val, axis=1)
        
    future_predictions = scaler.inverse_transform(np.array(future_predictions).reshape(-1, 1))
    
    # Generate future dates
    last_date = datetime.datetime.strptime(dates[-1], '%Y-%m-%d')
    future_dates = []
    current_date = last_date
    for _ in range(forecast_days):
        current_date += datetime.timedelta(days=1)
        future_dates.append(current_date.strftime('%Y-%m-%d'))
    
    # Technical Analysis
    analysis = get_recommendation(df)

    return {
        'ticker': ticker.upper(),
        'dates': dates, # All historical dates
        'actual_prices': close_prices, # All historical prices
        'test_dates': test_dates,
        'test_predictions': predictions.flatten().tolist(),
        'future_dates': future_dates,
        'future_predictions': future_predictions.flatten().tolist(),
        'metrics': {
            'mse': float(mse),
            'rmse': float(rmse)
        },
        'summary': {
            'look_back': look_back,
            'forecast_days': forecast_days,
            'last_date': dates[-1],
            'last_predicted_date': future_dates[-1],
            'last_predicted_price': float(future_predictions[-1][0])
        },
        'analysis': analysis
    }

def get_market_summary():
    """
    Fetches data for a list of popular stocks.
    """
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'BTC-USD', 'ETH-USD', '^GSPC']
    summary = []
    
    try:
        # Fetch data in bulk for efficiency (though yfinance bulk might be tricky with different types, loop is safer for small list)
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                # Get fast info if available, else history
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

def calculate_rsi(data, window=14):
    """Calculate RSI indicator"""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def get_recommendation(df):
    """
    Analyzes the stock data to generate a recommendation.
    """
    # Calculate Indicators
    close = df['Close']
    
    # RSI
    rsi_series = calculate_rsi(close)
    current_rsi = rsi_series.iloc[-1]
    
    # SMA 50
    sma_50 = close.rolling(window=50).mean().iloc[-1]
    current_price = close.iloc[-1]
    
    # Logic
    signals = []
    score = 0 # -2 to +2
    
    # RSI Logic
    if current_rsi < 30:
        signals.append("RSI is Oversold (Buy Signal)")
        score += 1
    elif current_rsi > 70:
        signals.append("RSI is Overbought (Sell Signal)")
        score -= 1
    else:
        signals.append(f"RSI is Neutral ({current_rsi:.2f})")
        
    # Trend Logic
    if current_price > sma_50:
        signals.append("Price is above 50-day SMA (Uptrend)")
        score += 1
    else:
        signals.append("Price is below 50-day SMA (Downtrend)")
        score -= 1
        
    # Final Recommendation
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
