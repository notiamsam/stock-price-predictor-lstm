import os
import openai
import google.generativeai as genai
from dotenv import load_dotenv
from chat.news_service import get_stock_news, format_news_for_llm

load_dotenv()

def get_chat_response(provider, message, context=None, api_key=None, model=None):
    """
    Generates a response from the selected LLM provider.
    Context contains stock data to inject into the system prompt.
    api_key: User-provided API key (takes precedence over env vars)
    model: Specific model name to use (e.g., 'gpt-5.1', 'gemini-2.5-pro')
    """
    
    # Check if user is asking for news/real-time info
    news_keywords = ['news', 'latest', 'headline', 'happening', 'update', 'recent', 'why', 'moving', 'event']
    include_news = any(keyword in message.lower() for keyword in news_keywords)
    
    # Construct System Prompt
    system_prompt = "You are a helpful financial assistant and stock market analyst."
    
    if context:
        ticker = context.get('ticker')
        system_prompt += f"\n\nCurrent Stock Context for {ticker}:"
        system_prompt += f"\n- Current Price: ${context.get('current_price')}"
        system_prompt += f"\n- Recommendation: {context.get('recommendation')}"
        system_prompt += f"\n- RSI: {context.get('rsi')}"
        system_prompt += f"\n- SMA(50): {context.get('sma_50')}"
        system_prompt += f"\n- Key Signals: {', '.join(context.get('signals', []))}"
        
        # Fetch and inject news if requested or relevant
        if include_news:
            try:
                news_items = get_stock_news(ticker)
                news_context = format_news_for_llm(news_items)
                system_prompt += f"\n\n{news_context}"
                system_prompt += "\n\nNote: Use the provided news headlines to explain recent price movements or market sentiment if relevant."
            except Exception as e:
                print(f"News fetch failed: {e}")

        system_prompt += "\nUse this data to answer the user's questions accurately. Do not give financial advice, but explain the technical indicators."

    # Valid model names for validation
    openai_models = ['gpt-5.1', 'gpt-5-mini', 'gpt-4o', 'gpt-3.5-turbo']
    gemini_models = ['gemini-3-pro-preview', 'gemini-2.5-pro', 'gemini-2.5-flash', 'gemini-2.5-flash-lite', 'gemini-pro']

    try:
        if provider == 'openai':
            # Use provided API key or fall back to environment variable
            if not api_key:
                api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                return "Error: OpenAI API key not configured. Please add your API key in settings."
            
            # Determine which model to use (default to gpt-3.5-turbo if not specified or invalid)
            selected_model = model if model and model in openai_models else 'gpt-3.5-turbo'
            
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=selected_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ]
            )
            return response.choices[0].message.content

        elif provider == 'gemini':
            # Use provided API key or fall back to environment variable
            if not api_key:
                api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                return "Error: Gemini API key not configured. Please add your API key in settings."
            
            genai.configure(api_key=api_key)
            
            # Determine which model to use (default to gemini-2.5-flash if not specified or invalid)
            selected_model = model if model and model in gemini_models else 'gemini-2.5-flash'
            
            # Use GenerativeModel with the selected model
            gen_model = genai.GenerativeModel(selected_model)
            
            # Gemini doesn't have a strict 'system' role in the same way, but we can prepend it
            full_prompt = f"{system_prompt}\n\nUser: {message}"
            response = gen_model.generate_content(full_prompt)
            return response.text

        else:
            return "Error: Invalid provider selected."

    except openai.AuthenticationError:
        return "Error: Invalid OpenAI API key. Please check your settings."
    except Exception as e:
        error_msg = str(e)
        if "API key" in error_msg or "authentication" in error_msg.lower():
            return f"Error: Authentication failed. Please check your {provider.upper()} API key in settings."
        if "model" in error_msg.lower() and ("not found" in error_msg.lower() or "invalid" in error_msg.lower()):
            return f"Error: The selected model may not be available or you may not have access to it. Please try a different model."
        return f"Error communicating with AI: {error_msg}"
