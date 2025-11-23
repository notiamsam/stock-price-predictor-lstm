from flask import Flask, render_template, request, jsonify
from models.stock_model import train_and_predict, get_market_summary
import os
import requests

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search')
def search_ticker():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    try:
        # Yahoo Finance Autocomplete API
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        data = response.json()
        
        results = []
        if 'quotes' in data:
            for quote in data['quotes']:
                if 'symbol' in quote:
                    results.append({
                        'symbol': quote['symbol'],
                        'name': quote.get('shortname', quote.get('longname', 'N/A')),
                        'exchange': quote.get('exchange', 'N/A')
                    })
        return jsonify(results)
    except Exception as e:
        print(f"Search error: {e}")
        return jsonify([])

@app.route('/market-summary')
def market_summary():
    try:
        summary = get_market_summary()
        return jsonify(summary)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    ticker = data.get('ticker')
    look_back = int(data.get('look_back', 60))
    forecast_days = int(data.get('forecast_days', 5))
    
    if not ticker:
        return jsonify({'error': 'Ticker symbol is required'}), 400
        
    try:
        result = train_and_predict(ticker, look_back, forecast_days)
        if 'error' in result:
             return jsonify(result), 400
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
