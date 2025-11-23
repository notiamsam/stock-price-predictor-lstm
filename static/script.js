let stockChart = null;

// Load Market Watch on startup
document.addEventListener('DOMContentLoaded', () => {
    fetchMarketSummary();
    setupAutocomplete();
    updateModelOptions(); // Initialize model options based on default provider
    // Refresh market data every 60 seconds
    setInterval(fetchMarketSummary, 60000);
});

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function setupAutocomplete() {
    const input = document.getElementById('ticker');
    const dropdown = document.getElementById('ticker-dropdown');

    const fetchTickers = async (value) => {
        if (!value) {
            dropdown.classList.add('hidden');
            return;
        }

        try {
            const response = await fetch(`/search?q=${encodeURIComponent(value)}`);
            const results = await response.json();

            if (results.length === 0) {
                dropdown.classList.add('hidden');
                return;
            }

            dropdown.innerHTML = '';
            results.forEach(t => {
                const div = document.createElement('div');
                div.className = 'dropdown-item';
                div.innerHTML = `
                    <span class="item-symbol">${t.symbol}</span>
                    <span class="item-name">${t.name} <span style="font-size: 0.7em; color: var(--text-secondary);">(${t.exchange})</span></span>
                `;
                div.onclick = () => {
                    input.value = t.symbol;
                    dropdown.classList.add('hidden');
                };
                dropdown.appendChild(div);
            });

            dropdown.classList.remove('hidden');
        } catch (error) {
            console.error('Search error:', error);
        }
    };

    const debouncedFetch = debounce((e) => {
        fetchTickers(e.target.value);
    }, 300);

    input.addEventListener('input', debouncedFetch);

    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!input.contains(e.target) && !dropdown.contains(e.target)) {
            dropdown.classList.add('hidden');
        }
    });
}

async function fetchMarketSummary() {
    const listContainer = document.getElementById('market-list');
    try {
        const response = await fetch('/market-summary');
        const data = await response.json();

        listContainer.innerHTML = '';

        data.forEach(item => {
            const div = document.createElement('div');
            div.className = 'market-item';
            const changeClass = item.change >= 0 ? 'text-green' : 'text-red';
            const sign = item.change >= 0 ? '+' : '';

            div.innerHTML = `
                <div class="market-item-header">
                    <span class="ticker-symbol">${item.ticker}</span>
                    <span class="ticker-price">$${item.price.toFixed(2)}</span>
                </div>
                <div class="ticker-change ${changeClass}">
                    ${sign}${item.change.toFixed(2)} (${sign}${item.change_pct.toFixed(2)}%)
                </div>
            `;
            // Click to populate input
            div.style.cursor = 'pointer';
            div.onclick = () => {
                document.getElementById('ticker').value = item.ticker;
            };

            listContainer.appendChild(div);
        });
    } catch (error) {
        console.error('Error fetching market summary:', error);
        listContainer.innerHTML = '<div style="text-align: center; color: var(--text-secondary);">Failed to load data.</div>';
    }
}

async function predictPrice() {
    const ticker = document.getElementById('ticker').value.trim();
    const lookBack = document.getElementById('look_back').value;
    const forecastDays = document.getElementById('forecast_days').value;
    const modelType = document.getElementById('model_type').value;
    const errorMsg = document.getElementById('error-msg');
    const loading = document.getElementById('loading');
    const resultsSection = document.getElementById('results');
    const predictBtn = document.getElementById('predict-btn');

    // Reset UI
    errorMsg.classList.add('hidden');
    errorMsg.textContent = '';
    resultsSection.classList.add('hidden');

    // Validation
    if (!ticker) {
        showError('Please enter a stock ticker.');
        return;
    }

    // Show loading
    loading.classList.remove('hidden');
    predictBtn.disabled = true;

    try {
        const response = await fetch('/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                ticker: ticker,
                look_back: parseInt(lookBack),
                forecast_days: parseInt(forecastDays),
                model_type: modelType
            }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'An error occurred while fetching predictions.');
        }

        displayResults(data);

        // Store context for chat
        window.currentStockContext = {
            ticker: data.ticker,
            current_price: data.analysis.current_price,
            recommendation: data.analysis.recommendation,
            rsi: data.analysis.rsi,
            sma_50: data.analysis.sma_50,
            signals: data.analysis.signals
        };

        // Add system message about new stock
        addMessage('system', `Loaded data for ${data.ticker}. You can now ask questions about it.`);

    } catch (error) {
        showError(error.message);
    } finally {
        loading.classList.add('hidden');
        predictBtn.disabled = false;
    }
}

function showError(message) {
    const errorMsg = document.getElementById('error-msg');
    if (errorMsg) {
        errorMsg.textContent = message;
        errorMsg.classList.remove('hidden');
    } else {
        alert(message);
    }
}

function displayResults(data) {
    const resultsSection = document.getElementById('results');
    resultsSection.classList.remove('hidden');

    // Update Analysis Cards
    const badge = document.getElementById('recommendation-badge');
    badge.textContent = data.analysis.recommendation;
    badge.style.backgroundColor = data.analysis.color;
    badge.style.boxShadow = `0 0 15px ${data.analysis.color}40`;

    const signalList = document.getElementById('signal-list');
    signalList.innerHTML = data.analysis.signals.map(s => `<div>• ${s}</div>`).join('');

    document.getElementById('rsi-value').textContent = data.analysis.rsi.toFixed(2);
    document.getElementById('sma-value').textContent = data.analysis.sma_50 ? '$' + data.analysis.sma_50.toFixed(2) : 'N/A';
    document.getElementById('rmse-value').textContent = data.metrics.rmse.toFixed(4);

    // Chart
    renderChart(data);
}

// Chat Functions
function updateModelOptions() {
    const provider = document.getElementById('chat-provider').value;
    const modelSelect = document.getElementById('chat-model');
    
    // Clear existing options
    modelSelect.innerHTML = '';
    
    if (provider === 'openai') {
        modelSelect.innerHTML = `
            <option value="gpt-5.1">GPT-5.1 (Latest)</option>
            <option value="gpt-5-mini">GPT-5 Mini (Cost-optimized)</option>
            <option value="gpt-4o">GPT-4o (Multimodal)</option>
            <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
        `;
    } else if (provider === 'gemini') {
        modelSelect.innerHTML = `
            <option value="gemini-3-pro-preview">Gemini 3 Pro (Latest)</option>
            <option value="gemini-2.5-pro">Gemini 2.5 Pro</option>
            <option value="gemini-2.5-flash" selected>Gemini 2.5 Flash (Recommended)</option>
            <option value="gemini-2.5-flash-lite">Gemini 2.5 Flash-Lite (Fastest)</option>
        `;
    }
}

async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    const provider = document.getElementById('chat-provider').value;
    const model = document.getElementById('chat-model').value;

    if (!message) return;

    // Add user message
    addMessage('user', message);
    input.value = '';
    
    // Disable input while processing
    input.disabled = true;

    // Check if context exists
    if (!window.currentStockContext) {
        addMessage('system', 'Please analyze a stock first so I have context to answer your questions.');
        input.disabled = false;
        return;
    }

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                provider: provider,
                model: model,
                message: message,
                context: window.currentStockContext
            })
        });

        const data = await response.json();
        if (data.error) {
            addMessage('system', 'Error: ' + data.error);
            if (data.error.includes('API key') || data.error.includes('configure')) {
                addMessage('system', 'Please configure your API key in Settings (⚙️ icon in header).');
            }
        } else {
            addMessage('assistant', data.response);
        }
    } catch (error) {
        addMessage('system', 'Error communicating with server: ' + error.message);
    } finally {
        input.disabled = false;
        input.focus();
    }
}

function addMessage(role, text) {
    const history = document.getElementById('chat-history');
    const div = document.createElement('div');
    div.className = `message ${role}`;

    // Convert newlines to breaks for assistant
    if (role === 'assistant') {
        div.innerHTML = text.replace(/\n/g, '<br>');
    } else {
        div.textContent = text;
    }

    history.appendChild(div);
    history.scrollTop = history.scrollHeight;
}

function handleChatKey(event) {
    if (event.key === 'Enter') {
        sendChatMessage();
    }
}

function renderChart(data) {
    const ctx = document.getElementById('stockChart').getContext('2d');

    if (stockChart) {
        stockChart.destroy();
    }

    // Chart.js Dark Theme Config
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.borderColor = '#334155';

    const displayLimit = 100; // Show last 100 days
    const historicalDates = data.dates.slice(-displayLimit);
    const historicalPrices = data.actual_prices.slice(-displayLimit);

    const allLabels = [...historicalDates, ...data.future_dates];
    const actualSeries = [...historicalPrices, ...new Array(data.future_dates.length).fill(null)];
    const futureSeries = [...new Array(historicalDates.length).fill(null), ...data.future_predictions];

    // Connect lines
    futureSeries[historicalDates.length - 1] = historicalPrices[historicalPrices.length - 1];

    stockChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: allLabels,
            datasets: [
                {
                    label: 'Historical',
                    data: actualSeries,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 2,
                    pointRadius: 0,
                    tension: 0.1,
                    fill: true
                },
                {
                    label: 'Forecast',
                    data: futureSeries,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    borderWidth: 2,
                    pointRadius: 0,
                    borderDash: [5, 5],
                    tension: 0.1,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    labels: {
                        font: { family: 'Inter' }
                    }
                },
                tooltip: {
                    backgroundColor: '#1e293b',
                    titleColor: '#f8fafc',
                    bodyColor: '#cbd5e1',
                    borderColor: '#334155',
                    borderWidth: 1,
                    padding: 10,
                    displayColors: true,
                    callbacks: {
                        label: function (context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(context.parsed.y);
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { maxTicksLimit: 8 }
                },
                y: {
                    grid: { color: '#334155' },
                    ticks: {
                        callback: function (value) {
                            return '$' + value;
                        }
                    }
                }
            }
        }
    });
}

// Settings Functions
function openSettings() {
    const modal = document.getElementById('settings-modal');
    modal.classList.remove('hidden');
    loadSettings();
}

function closeSettings() {
    const modal = document.getElementById('settings-modal');
    modal.classList.add('hidden');
    document.getElementById('settings-status').textContent = '';
}

async function loadSettings() {
    try {
        const response = await fetch('/settings');
        const data = await response.json();
        
        // Load existing keys (we don't get the full keys, just status)
        // Note: In a real app, you might want to store keys encrypted
        // For now, we'll leave fields empty for security
        
        // Show status if keys are configured
        const statusDiv = document.getElementById('settings-status');
        if (data.openai_configured && data.gemini_configured) {
            statusDiv.textContent = '✓ Both API keys are configured';
            statusDiv.className = 'status-message success';
        } else if (data.openai_configured || data.gemini_configured) {
            statusDiv.textContent = '⚠ Some API keys are not configured';
            statusDiv.className = 'status-message warning';
        } else {
            statusDiv.textContent = '⚠ Please configure at least one API key to use the chat feature';
            statusDiv.className = 'status-message warning';
        }
    } catch (error) {
        console.error('Error loading settings:', error);
    }
}

async function saveSettings() {
    const openaiKey = document.getElementById('openai-key').value.trim();
    const geminiKey = document.getElementById('gemini-key').value.trim();
    const statusDiv = document.getElementById('settings-status');
    
    if (!openaiKey && !geminiKey) {
        statusDiv.textContent = 'Please enter at least one API key';
        statusDiv.className = 'status-message error';
        return;
    }
    
    try {
        const response = await fetch('/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                openai_api_key: openaiKey,
                gemini_api_key: geminiKey
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            statusDiv.textContent = '✓ Settings saved successfully!';
            statusDiv.className = 'status-message success';
            
            // Clear the input fields after saving
            document.getElementById('openai-key').value = '';
            document.getElementById('gemini-key').value = '';
            
            // Close modal after a short delay
            setTimeout(() => {
                closeSettings();
            }, 1500);
        } else {
            statusDiv.textContent = 'Error: ' + (data.error || 'Failed to save settings');
            statusDiv.className = 'status-message error';
        }
    } catch (error) {
        statusDiv.textContent = 'Error: ' + error.message;
        statusDiv.className = 'status-message error';
    }
}

// Close modal when clicking outside
document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('settings-modal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeSettings();
            }
        });
    }
});
