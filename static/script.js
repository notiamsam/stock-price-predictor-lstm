let stockChart = null;

// Load Market Watch on startup
document.addEventListener('DOMContentLoaded', () => {
    fetchMarketSummary();
    setupAutocomplete();
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
    const errorMsg = document.getElementById('error-msg');
    const loading = document.getElementById('loading');
    const resultsSection = document.getElementById('results-section');
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
                forecast_days: parseInt(forecastDays)
            }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'An error occurred while fetching predictions.');
        }

        renderResults(data);

    } catch (error) {
        showError(error.message);
    } finally {
        loading.classList.add('hidden');
        predictBtn.disabled = false;
    }
}

function showError(message) {
    const errorMsg = document.getElementById('error-msg');
    errorMsg.textContent = message;
    errorMsg.classList.remove('hidden');
}

function renderResults(data) {
    const resultsSection = document.getElementById('results-section');
    resultsSection.classList.remove('hidden');

    // Metrics
    document.getElementById('rmse-val').textContent = data.metrics.rmse.toFixed(2);
    document.getElementById('current-price').textContent = '$' + data.analysis.current_price.toFixed(2);
    document.getElementById('future-price').textContent = '$' + data.summary.last_predicted_price.toFixed(2);

    // Analysis / Recommendation
    const recBadge = document.getElementById('rec-badge');
    const recText = document.getElementById('rec-text');

    recText.textContent = data.analysis.recommendation;
    recBadge.style.borderColor = data.analysis.color;
    recBadge.style.boxShadow = `0 0 15px ${data.analysis.color}40`; // Add glow
    recText.style.color = data.analysis.color;

    document.getElementById('rsi-val').textContent = data.analysis.rsi.toFixed(2);
    document.getElementById('sma-val').textContent = data.analysis.sma_50 ? '$' + data.analysis.sma_50.toFixed(2) : 'N/A';

    // Signals List
    const signalList = document.getElementById('signal-list');
    signalList.innerHTML = '';
    data.analysis.signals.forEach(signal => {
        const li = document.createElement('li');
        li.textContent = signal;
        signalList.appendChild(li);
    });

    // Chart
    renderChart(data);
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
