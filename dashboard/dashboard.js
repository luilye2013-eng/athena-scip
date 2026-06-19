/**
 * Athena SCIP - Main Dashboard Logic
 */

// Use window objects - NO DECLARATIONS
const API_URL = window.CONFIG.API_URL;
const supabaseClient = window.supabaseClient;

let priceChart = null, riskChart = null, pieChart = null;
let allPrices = [];
let priceDisplayLimit = 12;

async function checkAuth() {
    const { data: { session } } = await supabaseClient.auth.getSession();
    if (!session) window.location.href = 'secure-login.html';
    else {
        const userInfo = document.getElementById('userInfo');
        if (userInfo) userInfo.innerHTML = `👤 ${session.user.email}`;
    }
}

async function logout() {
    await supabaseClient.auth.signOut();
    window.location.href = 'secure-login.html';
}

async function safeFetch(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) return null;
        const result = await response.json();
        return result.success ? result.data : null;
    } catch (error) {
        console.error('Fetch error:', error);
        return null;
    }
}

function updateTimestamp() {
    const el = document.getElementById('lastUpdated');
    if (el) el.innerHTML = `Last updated: ${new Date().toLocaleString()}`;
}

async function loadWeather() {
    const container = document.getElementById('weatherContainer');
    if (!container) return;
    
    try {
        const data = await safeFetch(`${API_URL}/weather/alerts`);
        const alerts = data?.alerts || [];
        if (!alerts.length) {
            container.innerHTML = '<p>No active alerts</p>';
            return;
        }
        let html = '';
        for (let a of alerts.slice(0, 8)) {
            const alertType = a.alert_type ? a.alert_type.charAt(0).toUpperCase() + a.alert_type.slice(1) : 'Unknown';
            const severityText = a.severity === 5 ? 'Critical' : a.severity === 4 ? 'Severe' : a.severity === 3 ? 'Moderate' : 'Minor';
            const location = a.location_city ? `${a.location_city}, ${a.location_country || 'Global'}` : (a.location_country || 'Global');
            const description = a.description || 'No details available';
            const alertId = `alert-${Math.random().toString(36).substring(2, 8)}`;

            html += `<div class="weather-item">
                <div class="weather-header" onclick="document.getElementById('${alertId}').style.display = document.getElementById('${alertId}').style.display === 'none' ? 'block' : 'none'">
                    <div>
                        <span class="severity-badge severity-${a.severity}">${severityText}</span>
                        <strong>${alertType}</strong>
                    </div>
                    <div style="font-size: 11px; color: #6b7280;">📍 ${location}</div>
                </div>
                <div id="${alertId}" class="weather-desc">${description}</div>
            </div>`;
        }
        container.innerHTML = html;
    } catch (e) {
        container.innerHTML = '<p>Weather data unavailable</p>';
    }
}

async function loadShipping() {
    const container = document.getElementById('shippingContainer');
    if (!container) return;
    
    try {
        const data = await safeFetch(`${API_URL}/shipping/disruptions`);
        const disruptions = data?.disruptions || [];
        const countEl = document.getElementById('shippingCount');
        if (countEl) countEl.innerText = disruptions.length;
        
        if (!disruptions.length) {
            container.innerHTML = '<p>No disruptions</p>';
            return;
        }
        let html = '';
        for (let d of disruptions.slice(0, 8)) {
            const severityText = d.severity === 5 ? 'Critical' : d.severity === 4 ? 'Severe' : d.severity === 3 ? 'Moderate' : 'Minor';
            const delay = d.estimated_delay_days || 'N/A';
            const route = d.route_name || 'Unknown';
            const type = d.disruption_type || 'Unknown';
            const desc = d.description || 'No details available';

            html += `<div class="shipping-item">
                <div class="shipping-header">
                    <strong>${route}</strong>
                    <span class="severity-badge severity-${d.severity}">${severityText}</span>
                    <span>⏱️ ${delay}d</span>
                </div>
                <div style="font-size: 10px; color: #6b7280;">📌 ${type}</div>
                <div class="shipping-desc">${desc.substring(0, 100)}${desc.length > 100 ? '...' : ''}</div>
            </div>`;
        }
        container.innerHTML = html;
    } catch (e) {
        container.innerHTML = '<p>Shipping data unavailable</p>';
    }
}

async function loadPrices() {
    const container = document.getElementById('pricesContainer');
    if (!container) return;
    
    try {
        const data = await safeFetch(`${API_URL}/prices/live-comprehensive`);
        allPrices = data?.prices || [];
        
        // If no prices from API, use fallback data with more commodities
        if (allPrices.length === 0) {
            allPrices = [
                { commodity_name: 'Steel', price_usd: 847.50, unit: 'per ton', change_24h: -0.8 },
                { commodity_name: 'Semiconductors', price_usd: 1248.00, unit: 'per wafer', change_24h: -0.2 },
                { commodity_name: 'Lithium', price_usd: 14750.00, unit: 'per ton', change_24h: 1.5 },
                { commodity_name: 'Nickel', price_usd: 18450.00, unit: 'per ton', change_24h: -0.5 },
                { commodity_name: 'Iron Ore', price_usd: 117.20, unit: 'per ton', change_24h: -0.5 },
                { commodity_name: 'Crude Oil', price_usd: 77.50, unit: 'per barrel', change_24h: -0.3 },
                { commodity_name: 'Natural Gas', price_usd: 3.28, unit: 'per MMBtu', change_24h: 0.5 },
                { commodity_name: 'Gold', price_usd: 2020.00, unit: 'per ounce', change_24h: 0.8 },
                { commodity_name: 'Copper', price_usd: 4.70, unit: 'per pound', change_24h: -0.2 },
                { commodity_name: 'Wheat', price_usd: 249.00, unit: 'per bushel', change_24h: 0.3 },
                { commodity_name: 'Corn', price_usd: 198.00, unit: 'per bushel', change_24h: -0.1 },
                { commodity_name: 'Soybeans', price_usd: 425.00, unit: 'per bushel', change_24h: 0.2 }
            ];
        }
        
        // Make sure we have enough commodities
        if (allPrices.length < 12) {
            console.warn('⚠️ Only ' + allPrices.length + ' commodities available. Adding fallback data.');
            const fallback = [
                { commodity_name: 'Crude Oil', price_usd: 77.50, unit: 'per barrel', change_24h: -0.3 },
                { commodity_name: 'Natural Gas', price_usd: 3.28, unit: 'per MMBtu', change_24h: 0.5 },
                { commodity_name: 'Gold', price_usd: 2020.00, unit: 'per ounce', change_24h: 0.8 },
                { commodity_name: 'Copper', price_usd: 4.70, unit: 'per pound', change_24h: -0.2 },
                { commodity_name: 'Wheat', price_usd: 249.00, unit: 'per bushel', change_24h: 0.3 },
                { commodity_name: 'Corn', price_usd: 198.00, unit: 'per bushel', change_24h: -0.1 },
                { commodity_name: 'Soybeans', price_usd: 425.00, unit: 'per bushel', change_24h: 0.2 }
            ];
            // Merge, avoiding duplicates
            const existingNames = allPrices.map(p => p.commodity_name);
            for (let f of fallback) {
                if (!existingNames.includes(f.commodity_name)) {
                    allPrices.push(f);
                }
            }
        }
        
        displayPrices();
    } catch (e) {
        console.error('Price load error:', e);
        container.innerHTML = '<p>Price data unavailable</p>';
    }
}

function displayPrices() {
    const container = document.getElementById('pricesContainer');
    if (!container) return;
    
    const prices = allPrices.slice(0, priceDisplayLimit);
    const showMoreBtn = document.getElementById('showMorePrices');
    
    if (allPrices.length > priceDisplayLimit) {
        if (showMoreBtn) {
            showMoreBtn.style.display = 'inline-block';
            showMoreBtn.textContent = `Show More (${allPrices.length - priceDisplayLimit} remaining)`;
        }
    } else {
        if (showMoreBtn) showMoreBtn.style.display = 'none';
    }
    
    if (!prices.length) {
        container.innerHTML = '<p>No price data</p>';
        return;
    }
    
    let html = '';
    for (let p of prices) {
        const change = p.change_24h || 0;
        const changeSymbol = change > 0 ? '▲' : (change < 0 ? '▼' : '●');
        const color = change > 0 ? '#10b981' : (change < 0 ? '#dc2626' : '#6b7280');
        html += `<div class="price-item">
            <strong>${p.commodity_name}</strong>
            <span>$${p.price_usd}</span>
            <span style="color: ${color};">${changeSymbol} ${Math.abs(change).toFixed(1)}%</span>
            <span style="font-size: 9px; color: #6b7280;">${p.unit || ''}</span>
        </div>`;
    }
    container.innerHTML = html;
}

function loadMorePrices() {
    priceDisplayLimit += 12;
    displayPrices();
}

async function loadStats() {
    try {
        const summary = await safeFetch(`${API_URL}/events/summary`);
        const totalEl = document.getElementById('totalEvents');
        if (totalEl) totalEl.innerText = summary?.total_events || 0;
        
        const data = await safeFetch(`${API_URL}/events?limit=500`);
        const events = data?.events || [];
        const warEl = document.getElementById('warEvents');
        if (warEl) warEl.innerText = events.filter(e => e.event_type === 'war').length;
        
        const disasterEl = document.getElementById('disasterEvents');
        if (disasterEl) disasterEl.innerText = events.filter(e => e.event_type === 'natural_disaster').length;
        
        const recSummary = await safeFetch(`${API_URL}/recommendations/summary`);
        const recEl = document.getElementById('recCount');
        if (recEl) recEl.innerText = recSummary?.total_recommendations || 0;
    } catch (e) {
        console.error('Stats error:', e);
    }
}

async function loadCountryRisk() {
    const container = document.getElementById('countryRiskContainer');
    if (!container) return;
    
    try {
        console.log('🔍 Fetching country risk data...');
        const data = await safeFetch(`${API_URL}/country-risk/enhanced`);
        console.log('📡 Country risk response:', data);
        
        const countries = data?.countries || [];
        if (!countries.length) {
            console.warn('⚠️ No country risk data available');
            container.innerHTML = '<p>Risk data unavailable</p>';
            return;
        }
        
        let gridHtml = '<div class="risk-grid">';
        const riskLabels = [];
        const riskScores = [];
        
        for (let c of countries.slice(0, 12)) {
            let colorClass = c.risk_level === 'Critical' ? 'risk-critical' : (c.risk_level === 'High' ? 'risk-high' : '');
            gridHtml += `<div class="risk-item"><strong>${c.country}</strong><br><span class="${colorClass}">${c.risk_level}</span><br><span style="font-size:10px;">Score: ${c.risk_score}</span></div>`;
            riskLabels.push(c.country);
            riskScores.push(c.risk_score);
        }
        gridHtml += '</div>';
        container.innerHTML = gridHtml;

        // Pie chart - with proper destroy check
        const ctx = document.getElementById('riskPieChart');
        if (ctx) {
            // Check if chart exists before destroying
            if (window.riskPieChart && typeof window.riskPieChart.destroy === 'function') {
                window.riskPieChart.destroy();
            } else if (window.riskPieChart) {
                // If it exists but destroy is not a function, just clear it
                delete window.riskPieChart;
            }
            
            try {
                window.riskPieChart = new Chart(ctx, {
                    type: 'pie',
                    data: { 
                        labels: riskLabels, 
                        datasets: [{ 
                            data: riskScores, 
                            backgroundColor: window.CONFIG.COLORS.chart 
                        }] 
                    },
                    options: { 
                        responsive: true, 
                        maintainAspectRatio: true, 
                        plugins: { 
                            legend: { 
                                position: 'bottom', 
                                labels: { font: { size: 10 } } 
                            } 
                        } 
                    }
                });
                console.log('✅ Risk pie chart created');
            } catch (chartError) {
                console.error('Chart error:', chartError);
            }
        }
    } catch (e) {
        console.error('❌ Country risk error:', e);
        container.innerHTML = '<p>Risk data unavailable</p>';
    }
}

cd C:\Users\hp\athena-scip\dashboard
notepad dashboard.js
async function exportData(type) {
    const statusDiv = document.getElementById('exportStatus');
    if (!statusDiv) return;
    
    statusDiv.textContent = '⏳ Exporting...';
    
    try {
        let endpoint, filename;
        switch(type) {
            case 'events':
                endpoint = `${API_URL}/events/export/csv`;
                filename = 'events';
                break;
            case 'recommendations':
                endpoint = `${API_URL}/recommendations`;
                filename = 'recommendations';
                break;
            case 'prices':
                endpoint = `${API_URL}/prices/live-comprehensive`;
                filename = 'prices';
                break;
            case 'risk':
                endpoint = `${API_URL}/country-risk/enhanced`;
                filename = 'country-risk';
                break;
            default:
                throw new Error('Unknown export type');
        }
        
        const response = await fetch(endpoint);
        if (!response.ok) throw new Error('Failed to fetch data');
        
        if (type === 'events') {
            const blob = await response.blob();
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = `${filename}_${new Date().toISOString().split('T')[0]}.csv`;
            link.click();
            URL.revokeObjectURL(link.href);
        } else {
            const data = await response.json();
            const jsonData = data.success ? data.data : data;
            if (window.DataExporter) {
                window.DataExporter.toJSON(jsonData, filename);
            } else {
                const jsonContent = JSON.stringify(jsonData, null, 2);
                const blob = new Blob([jsonContent], { type: 'application/json;charset=utf-8' });
                const link = document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.download = `${filename}_${new Date().toISOString().split('T')[0]}.json`;
                link.click();
                URL.revokeObjectURL(link.href);
            }
        }
        
        statusDiv.textContent = '✅ Export successful!';
    } catch (error) {
        console.error('Export error:', error);
        statusDiv.textContent = '❌ Export failed: ' + error.message;
    }
}

async function exportAllData() {
    const statusDiv = document.getElementById('exportStatus');
    if (!statusDiv) return;
    
    statusDiv.textContent = '⏳ Exporting all data...';
    
    try {
        const [events, recommendations, prices, risk] = await Promise.all([
            fetch(`${API_URL}/events?limit=1000`).then(r => r.json()),
            fetch(`${API_URL}/recommendations?limit=200`).then(r => r.json()),
            fetch(`${API_URL}/prices/live-comprehensive`).then(r => r.json()),
            fetch(`${API_URL}/country-risk/enhanced`).then(r => r.json())
        ]);
        
        const allData = {
            events: events.success ? events.data : events,
            recommendations: recommendations.success ? recommendations.data : recommendations,
            prices: prices.success ? prices.data : prices,
            risk: risk.success ? risk.data : risk,
            exported_at: new Date().toISOString()
        };
        
        if (window.DataExporter) {
            window.DataExporter.toJSON(allData, 'athena-scip-all-data');
        } else {
            const jsonContent = JSON.stringify(allData, null, 2);
            const blob = new Blob([jsonContent], { type: 'application/json;charset=utf-8' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = `athena-scip-all-data_${new Date().toISOString().split('T')[0]}.json`;
            link.click();
            URL.revokeObjectURL(link.href);
        }
        statusDiv.textContent = '✅ All data exported successfully!';
    } catch (error) {
        console.error('Export all error:', error);
        statusDiv.textContent = '❌ Export all failed: ' + error.message;
    }
}

async function loadAll() {
    await loadStats();
    await loadWeather();
    await loadShipping();
    await loadPrices();
    await loadCountryRisk();
    
    const trendPeriod = document.getElementById('trendPeriod');
    const days = trendPeriod ? parseInt(trendPeriod.value) : 14;
    await loadTrends(days);
    
    updateTimestamp();
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) logoutBtn.addEventListener('click', logout);
    
    const showMoreBtn = document.getElementById('showMorePrices');
    if (showMoreBtn) showMoreBtn.addEventListener('click', loadMorePrices);
    
    const trendPeriod = document.getElementById('trendPeriod');
    if (trendPeriod) {
        trendPeriod.addEventListener('change', function() {
            loadTrends(parseInt(this.value));
        });
    }
    
    checkAuth().then(() => {
        loadAll();
        setInterval(loadAll, 60000);
    });
});