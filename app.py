from flask import Flask, render_template, request, jsonify
from models.prediction_engine import train_and_predict, get_market_summary
from chat.llm_service import get_chat_response
import os
import requests
import json

app = Flask(__name__)
SETTINGS_FILE = 'api_settings.json'

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
    model_type = data.get('model_type', 'lstm')
    
    if not ticker:
        return jsonify({'error': 'Ticker symbol is required'}), 400
        
    try:
        result = train_and_predict(ticker, look_back, forecast_days, model_type)
        if 'error' in result:
             return jsonify(result), 400
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    provider = data.get('provider')
    model = data.get('model')  # Get the selected model
    message = data.get('message')
    context = data.get('context') # Stock data passed from frontend
    
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    
    # Load API keys from settings
    api_keys = load_api_keys()
    api_key = None
    if provider == 'openai':
        api_key = api_keys.get('openai_api_key', '')
    elif provider == 'gemini':
        api_key = api_keys.get('gemini_api_key', '')
    
    if not api_key:
        return jsonify({'error': f'Please configure your {provider.upper()} API key in settings first.'}), 400
        
    response = get_chat_response(provider, message, context, api_key, model)
    return jsonify({'response': response})

@app.route('/settings', methods=['GET'])
def get_settings():
    """Get current API key settings"""
    api_keys = load_api_keys()
    # Don't send full keys, just indicate if they're set
    return jsonify({
        'openai_configured': bool(api_keys.get('openai_api_key')),
        'gemini_configured': bool(api_keys.get('gemini_api_key'))
    })

@app.route('/settings', methods=['POST'])
def save_settings():
    """Save API key settings"""
    data = request.get_json()
    openai_key = data.get('openai_api_key', '').strip()
    gemini_key = data.get('gemini_api_key', '').strip()
    
    # Load existing settings
    api_keys = load_api_keys()
    
    # Update only non-empty keys
    if openai_key:
        api_keys['openai_api_key'] = openai_key
    if gemini_key:
        api_keys['gemini_api_key'] = gemini_key
    
    # Save to file
    save_api_keys(api_keys)
    
    return jsonify({
        'success': True,
        'message': 'Settings saved successfully'
    })

def load_api_keys():
    """Load API keys from JSON file"""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_api_keys(api_keys):
    """Save API keys to JSON file"""
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(api_keys, f)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
