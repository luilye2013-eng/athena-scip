/**
 * Athena SCIP - Main Dashboard Logic
 */

// Use the global CONFIG and supabaseClient
const CONFIG = window.CONFIG;
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
        const data = await safeFetch(`${CONFIG.API_URL}/weather/alerts`);
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
        const data = await safeFetch(`${CONFIG.API_URL}/shipping/disruptions`);
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
        const data = await safeFetch(`${CONFIG.API_URL}/prices/live-comprehensive`);
        allPrices = data?.prices || [];
        displayPrices();
    } catch (e) {
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
        const summary = await safeFetch(`${CONFIG.API_URL}/events/summary`);
        const totalEl = document.getElementById('totalEvents');
        if (totalEl) totalEl.innerText = summary?.total_events || 0;
        
        const data = await safeFetch(`${CONFIG.API_URL}/events?limit=500`);
        const events = data?.events || [];
        const warEl = document.getElementById('warEvents');
        if (warEl) warEl.innerText = events.filter(e => e.event_type === 'war').length;
        
        const disasterEl = document.getElementById('disasterEvents');
        if (disasterEl) disasterEl.innerText = events.filter(e => e.event_type === 'natural_disaster').length;
        
        const recSummary = await safeFetch(`${CONFIG.API_URL}/recommendations/summary`);
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
        const data = await safeFetch(`${CONFIG.API_URL}/country-risk/enhanced`);
        const countries = data?.countries || [];
        if (!countries.length) {
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

        const ctx = document.getElementById('riskPieChart');
        if (ctx) {
            if (window.riskPieChart) window.riskPieChart.destroy();
            window.riskPieChart = new Chart(ctx, {
                type: 'pie',
                data: { 
                    labels: riskLabels, 
                    datasets: [{ 
                        data: riskScores, 
                        backgroundColor: CONFIG.COLORS.chart 
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
        }
    } catch (e) {
        container.innerHTML = '<p>Risk data unavailable</p>';
    }
}

async function loadTrends(days = 14) {
    try {
        const priceData = await safeFetch(`${CONFIG.API_URL}/trends/prices?days=${days}`);
        let priceTrends = priceData?.trends || {};

        if (Object.keys(priceTrends).length === 0) {
            priceTrends = {
                'Steel': [862, 858, 855, 850, 848, 847, 845].map((p, i) => ({ date: `Day ${i + 1}`, price: p })),
                'Wheat': [238, 240, 242, 245, 247, 248, 249].map((p, i) => ({ date: `Day ${i + 1}`, price: p })),
                'Crude Oil': [79.5, 79.0, 78.5, 78.0, 77.8, 77.5, 77.2].map((p, i) => ({ date: `Day ${i + 1}`, price: p })),
                'Natural Gas': [3.35, 3.33, 3.30, 3.28, 3.27, 3.28, 3.28].map((p, i) => ({ date: `Day ${i + 1}`, price: p })),
                'Copper': [4.85, 4.82, 4.80, 4.78, 4.75, 4.72, 4.70].map((p, i) => ({ date: `Day ${i + 1}`, price: p })),
                'Gold': [1950, 1960, 1975, 1985, 1990, 2005, 2020].map((p, i) => ({ date: `Day ${i + 1}`, price: p }))
            };
        }

        const commodities = ['Steel', 'Wheat', 'Crude Oil', 'Natural Gas', 'Copper', 'Gold'];
        const colors = CONFIG.COLORS.chart;
        const dates = [];
        const datasets = [];

        for (let i = 0; i < commodities.length; i++) {
            const commodity = commodities[i];
            if (priceTrends[commodity] && priceTrends[commodity].length > 0) {
                const prices = priceTrends[commodity];
                if (dates.length === 0) prices.forEach(p => dates.push(p.date));
                datasets.push({ 
                    label: commodity, 
                    data: prices.map(p => p.price), 
                    borderColor: colors[i % colors.length], 
                    fill: false, 
                    tension: 0.3 
                });
            }
        }

        const ctx1 = document.getElementById('priceTrendChart');
        if (ctx1) {
            if (window.priceChart) window.priceChart.destroy();
            window.priceChart = new Chart(ctx1, {
                type: 'line',
                data: { 
                    labels: dates, 
                    datasets: datasets.length ? datasets : [{ label: 'No data', data: [0], borderColor: '#ccc' }] 
                },
                options: { 
                    responsive: true, 
                    maintainAspectRatio: true, 
                    plugins: { 
                        legend: { 
                            position: 'top', 
                            labels: { font: { size: 10 } } 
                        } 
                    } 
                }
            });
        }

        const riskData = await safeFetch(`${CONFIG.API_URL}/trends/risk?days=${days}`);
        let riskTrends = riskData?.trends || {};

        if (Object.keys(riskTrends).length === 0) {
            riskTrends = {
                'Iran': [75, 80, 85, 90, 94, 98, 100].map((r, i) => ({ date: `Day ${i + 1}`, risk: r })),
                'Russia': [85, 88, 90, 92, 94, 96, 100].map((r, i) => ({ date: `Day ${i + 1}`, risk: r })),
                'Ukraine': [82, 86, 89, 92, 94, 96, 100].map((r, i) => ({ date: `Day ${i + 1}`, risk: r })),
                'Israel': [70, 75, 80, 85, 90, 95, 100].map((r, i) => ({ date: `Day ${i + 1}`, risk: r }))
            };
        }

        const countries = ['Iran', 'Russia', 'Ukraine', 'Israel'];
        const riskColors = ['#dc2626', '#f97316', '#eab308', '#2c4a6e'];
        const riskDates = [];
        const riskDatasets = [];

        for (let i = 0; i < countries.length; i++) {
            const country = countries[i];
            if (riskTrends[country] && riskTrends[country].length > 0) {
                const risks = riskTrends[country];
                if (riskDates.length === 0) risks.forEach(r => riskDates.push(r.date));
                riskDatasets.push({ 
                    label: country, 
                    data: risks.map(r => r.risk), 
                    borderColor: riskColors[i % riskColors.length], 
                    fill: false, 
                    tension: 0.3 
                });
            }
        }

        const ctx2 = document.getElementById('riskTrendChart');
        if (ctx2) {
            if (window.riskChart) window.riskChart.destroy();
            window.riskChart = new Chart(ctx2, {
                type: 'line',
                data: { 
                    labels: riskDates, 
                    datasets: riskDatasets.length ? riskDatasets : [{ label: 'No data', data: [0], borderColor: '#ccc' }] 
                },
                options: { 
                    responsive: true, 
                    maintainAspectRatio: true, 
                    plugins: { 
                        legend: { 
                            position: 'top', 
                            labels: { font: { size: 10 } } 
                        } 
                    }, 
                    scales: { y: { min: 0, max: 100 } } 
                }
            });
        }

    } catch (e) {
        console.error('Trend error:', e);
    }
}

async function exportData(type) {
    const statusDiv = document.getElementById('exportStatus');
    if (!statusDiv) return;
    
    statusDiv.textContent = '⏳ Exporting...';
    
    try {
        let endpoint, filename;
        switch(type) {
            case 'events':
                endpoint = `${CONFIG.API_URL}/events/export/csv`;
                filename = 'events';
                break;
            case 'recommendations':
                endpoint = `${CONFIG.API_URL}/recommendations`;
                filename = 'recommendations';
                break;
            case 'prices':
                endpoint = `${CONFIG.API_URL}/prices/live-comprehensive`;
                filename = 'prices';
                break;
            case 'risk':
                endpoint = `${CONFIG.API_URL}/country-risk/enhanced`;
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
            fetch(`${CONFIG.API_URL}/events?limit=1000`).then(r => r.json()),
            fetch(`${CONFIG.API_URL}/recommendations?limit=200`).then(r => r.json()),
            fetch(`${CONFIG.API_URL}/prices/live-comprehensive`).then(r => r.json()),
            fetch(`${CONFIG.API_URL}/country-risk/enhanced`).then(r => r.json())
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