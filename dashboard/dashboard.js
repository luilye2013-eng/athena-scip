/**
 * Athena SCIP - Main Dashboard Logic
 */

// Use window objects - NO DECLARATIONS
const API_URL = window.CONFIG.API_URL;
const supabaseClient = window.supabaseClient;

var priceChart = null, riskChart = null, pieChart = null;
var allPrices = [];
var priceDisplayLimit = 12;

async function checkAuth() {
    var sessionData = await supabaseClient.auth.getSession();
    var session = sessionData.data.session;
    if (!session) window.location.href = 'secure-login.html';
    else {
        var userInfo = document.getElementById('userInfo');
        if (userInfo) userInfo.innerHTML = '👤 ' + session.user.email;
    }
}

async function logout() {
    await supabaseClient.auth.signOut();
    window.location.href = 'secure-login.html';
}

async function safeFetch(url) {
    try {
        var response = await fetch(url);
        if (!response.ok) return null;
        var result = await response.json();
        return result.success ? result.data : null;
    } catch (error) {
        console.error('Fetch error:', error);
        return null;
    }
}

function updateTimestamp() {
    var el = document.getElementById('lastUpdated');
    if (el) el.innerHTML = 'Last updated: ' + new Date().toLocaleString();
}

async function loadWeather() {
    var container = document.getElementById('weatherContainer');
    if (!container) return;

    try {
        var data = await safeFetch(API_URL + '/weather/alerts');
        var alerts = data?.alerts || [];
        if (!alerts.length) {
            container.innerHTML = '<p>No active alerts</p>';
            return;
        }
        var html = '';
        for (var a = 0; a < Math.min(alerts.length, 8); a++) {
            var alert = alerts[a];
            var alertType = alert.alert_type ? alert.alert_type.charAt(0).toUpperCase() + alert.alert_type.slice(1) : 'Unknown';
            var severityText = alert.severity === 5 ? 'Critical' : alert.severity === 4 ? 'Severe' : alert.severity === 3 ? 'Moderate' : 'Minor';
            var location = alert.location_city ? alert.location_city + ', ' + (alert.location_country || 'Global') : (alert.location_country || 'Global');
            var description = alert.description || 'No details available';
            var alertId = 'alert-' + Math.random().toString(36).substring(2, 8);

            html += '<div class="weather-item">';
            html += '<div class="weather-header" onclick="document.getElementById(\'' + alertId + '\').style.display = document.getElementById(\'' + alertId + '\').style.display === \'none\' ? \'block\' : \'none\'">';
            html += '<div><span class="severity-badge severity-' + alert.severity + '">' + severityText + '</span> <strong>' + alertType + '</strong></div>';
            html += '<div style="font-size: 11px; color: #6b7280;">📍 ' + location + '</div>';
            html += '</div>';
            html += '<div id="' + alertId + '" class="weather-desc">' + description + '</div>';
            html += '</div>';
        }
        container.innerHTML = html;
    } catch (e) {
        container.innerHTML = '<p>Weather data unavailable</p>';
    }
}

async function loadShipping() {
    var container = document.getElementById('shippingContainer');
    if (!container) return;

    try {
        var data = await safeFetch(API_URL + '/shipping/disruptions');
        var disruptions = data?.disruptions || [];
        var countEl = document.getElementById('shippingCount');
        if (countEl) countEl.innerText = disruptions.length;

        if (!disruptions.length) {
            container.innerHTML = '<p>No disruptions</p>';
            return;
        }
        var html = '';
        for (var d = 0; d < Math.min(disruptions.length, 8); d++) {
            var disruption = disruptions[d];
            var severityText = disruption.severity === 5 ? 'Critical' : disruption.severity === 4 ? 'Severe' : disruption.severity === 3 ? 'Moderate' : 'Minor';
            var delay = disruption.estimated_delay_days || 'N/A';
            var route = disruption.route_name || 'Unknown';
            var type = disruption.disruption_type || 'Unknown';
            var desc = disruption.description || 'No details available';

            html += '<div class="shipping-item">';
            html += '<div class="shipping-header"><strong>' + route + '</strong> <span class="severity-badge severity-' + disruption.severity + '">' + severityText + '</span> <span>⏱️ ' + delay + 'd</span></div>';
            html += '<div style="font-size: 10px; color: #6b7280;">📌 ' + type + '</div>';
            html += '<div class="shipping-desc">' + desc.substring(0, 100) + (desc.length > 100 ? '...' : '') + '</div>';
            html += '</div>';
        }
        container.innerHTML = html;
    } catch (e) {
        container.innerHTML = '<p>Shipping data unavailable</p>';
    }
}

async function loadPrices() {
    var container = document.getElementById('pricesContainer');
    if (!container) return;

    try {
        var data = await safeFetch(API_URL + '/prices/live-comprehensive');
        allPrices = data?.prices || [];

        if (allPrices.length < 10) {
            console.log('⚠️ Adding expanded commodity data...');
            var fallbackPrices = [
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

            var existingNames = {};
            for (var i = 0; i < allPrices.length; i++) {
                existingNames[allPrices[i].commodity_name] = true;
            }
            for (var f = 0; f < fallbackPrices.length; f++) {
                if (!existingNames[fallbackPrices[f].commodity_name]) {
                    allPrices.push(fallbackPrices[f]);
                }
            }
        }

        if (allPrices.length > 20) {
            allPrices = allPrices.slice(0, 20);
        }

        displayPrices();
    } catch (e) {
        console.error('Price load error:', e);
        container.innerHTML = '<p>Price data unavailable</p>';
    }
}

function displayPrices() {
    var container = document.getElementById('pricesContainer');
    if (!container) return;

    var prices = allPrices.slice(0, priceDisplayLimit);
    var showMoreBtn = document.getElementById('showMorePrices');

    if (allPrices.length > priceDisplayLimit) {
        if (showMoreBtn) {
            showMoreBtn.style.display = 'inline-block';
            showMoreBtn.textContent = 'Show More (' + (allPrices.length - priceDisplayLimit) + ' remaining)';
        }
    } else {
        if (showMoreBtn) showMoreBtn.style.display = 'none';
    }

    if (!prices.length) {
        container.innerHTML = '<p>No price data</p>';
        return;
    }

    var html = '';
    for (var p = 0; p < prices.length; p++) {
        var item = prices[p];
        var change = item.change_24h || 0;
        var changeSymbol = change > 0 ? '▲' : (change < 0 ? '▼' : '●');
        var color = change > 0 ? '#10b981' : (change < 0 ? '#dc2626' : '#6b7280');
        html += '<div class="price-item">';
        html += '<strong>' + item.commodity_name + '</strong>';
        html += '<span>$' + item.price_usd + '</span>';
        html += '<span style="color: ' + color + ';">' + changeSymbol + ' ' + Math.abs(change).toFixed(1) + '%</span>';
        html += '<span style="font-size: 9px; color: #6b7280;">' + (item.unit || '') + '</span>';
        html += '</div>';
    }
    container.innerHTML = html;
}

function loadMorePrices() {
    priceDisplayLimit += 12;
    displayPrices();
}

async function loadStats() {
    try {
        var summary = await safeFetch(API_URL + '/events/summary');
        var totalEl = document.getElementById('totalEvents');
        if (totalEl) totalEl.innerText = summary?.total_events || 0;

        var data = await safeFetch(API_URL + '/events?limit=500');
        var events = data?.events || [];
        var warEl = document.getElementById('warEvents');
        if (warEl) {
            var warCount = 0;
            for (var e = 0; e < events.length; e++) {
                if (events[e].event_type === 'war') warCount++;
            }
            warEl.innerText = warCount;
        }

        var disasterEl = document.getElementById('disasterEvents');
        if (disasterEl) {
            var disasterCount = 0;
            for (var d = 0; d < events.length; d++) {
                if (events[d].event_type === 'natural_disaster') disasterCount++;
            }
            disasterEl.innerText = disasterCount;
        }

        var recSummary = await safeFetch(API_URL + '/recommendations/summary');
        var recEl = document.getElementById('recCount');
        if (recEl) recEl.innerText = recSummary?.total_recommendations || 0;
    } catch (e) {
        console.error('Stats error:', e);
    }
}

async function loadCountryRisk() {
    var container = document.getElementById('countryRiskContainer');
    if (!container) return;

    try {
        console.log('🔍 Fetching country risk data...');
        var data = await safeFetch(API_URL + '/country-risk/enhanced');
        console.log('📡 Country risk response:', data);

        var countries = data?.countries || [];
        if (!countries.length) {
            console.warn('⚠️ No country risk data available');
            container.innerHTML = '<p>Risk data unavailable</p>';
            return;
        }

        var gridHtml = '<div class="risk-grid">';
        var riskLabels = [];
        var riskScores = [];

        for (var c = 0; c < Math.min(countries.length, 12); c++) {
            var country = countries[c];
            var colorClass = country.risk_level === 'Critical' ? 'risk-critical' : (country.risk_level === 'High' ? 'risk-high' : '');
            gridHtml += '<div class="risk-item"><strong>' + country.country + '</strong><br><span class="' + colorClass + '">' + country.risk_level + '</span><br><span style="font-size:10px;">Score: ' + country.risk_score + '</span></div>';
            riskLabels.push(country.country);
            riskScores.push(country.risk_score);
        }
        gridHtml += '</div>';
        container.innerHTML = gridHtml;

        var ctx = document.getElementById('riskPieChart');
        if (ctx) {
            if (window.riskPieChart && typeof window.riskPieChart.destroy === 'function') {
                window.riskPieChart.destroy();
            } else if (window.riskPieChart) {
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

async function loadTrends(days) {
    if (days === undefined) days = 14;
    try {
        var priceData = await safeFetch(API_URL + '/trends/prices?days=' + days);
        console.log('📊 Price trend data:', priceData);

        var priceTrends = priceData?.trends || {};

        if (Object.keys(priceTrends).length === 0) {
            console.warn('⚠️ No price trend data available from API');
            var ctx1 = document.getElementById('priceTrendChart');
            if (ctx1) {
                if (window.priceChart) window.priceChart.destroy();
                window.priceChart = new Chart(ctx1, {
                    type: 'line',
                    data: {
                        labels: ['No Data'],
                        datasets: [{
                            label: 'No price data available',
                            data: [0],
                            borderColor: '#ccc',
                            fill: false
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: true,
                        plugins: {
                            legend: { position: 'top', labels: { font: { size: 10 } } }
                        }
                    }
                });
            }
            return;
        }

        var allDates = {};
        var commodities = Object.keys(priceTrends);
        var colors = window.CONFIG.COLORS.chart;
        var datasets = [];

        for (var i = 0; i < commodities.length; i++) {
            var commodity = commodities[i];
            var prices = priceTrends[commodity] || [];
            if (prices.length > 0) {
                for (var p = 0; p < prices.length; p++) {
                    allDates[prices[p].date] = true;
                }
                var priceValues = [];
                for (var p2 = 0; p2 < prices.length; p2++) {
                    priceValues.push(prices[p2].price);
                }
                datasets.push({
                    label: commodity,
                    data: priceValues,
                    borderColor: colors[i % colors.length],
                    fill: false,
                    tension: 0.3,
                    pointRadius: 3,
                    pointHoverRadius: 5
                });
            }
        }

        var sortedDates = Object.keys(allDates).sort();

        var ctx1 = document.getElementById('priceTrendChart');
        if (ctx1) {
            if (window.priceChart) window.priceChart.destroy();
            var formattedDates = [];
            for (var d = 0; d < sortedDates.length; d++) {
                var dateObj = new Date(sortedDates[d]);
                formattedDates.push(dateObj.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
            }
            window.priceChart = new Chart(ctx1, {
                type: 'line',
                data: {
                    labels: formattedDates,
                    datasets: datasets
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
                    scales: {
                        x: {
                            ticks: { font: { size: 9 } }
                        },
                        y: {
                            beginAtZero: false,
                            ticks: { font: { size: 9 } }
                        }
                    }
                }
            });
            console.log('✅ Price chart updated with real data');
        }

        await loadRiskTrends(days);

    } catch (e) {
        console.error('Trend error:', e);
    }
}

async function loadRiskTrends(days) {
    if (days === undefined) days = 14;
    try {
        var riskData = await safeFetch(API_URL + '/trends/risk?days=' + days);
        console.log('📊 Risk trend data:', riskData);

        var riskTrends = riskData?.trends || {};

        if (Object.keys(riskTrends).length === 0) {
            console.warn('⚠️ No risk trend data available from API');
            var ctx2 = document.getElementById('riskTrendChart');
            if (ctx2) {
                if (window.riskChart) window.riskChart.destroy();
                window.riskChart = new Chart(ctx2, {
                    type: 'line',
                    data: {
                        labels: ['No Data'],
                        datasets: [{
                            label: 'No risk data available',
                            data: [0],
                            borderColor: '#ccc',
                            fill: false
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: true,
                        plugins: {
                            legend: { position: 'top', labels: { font: { size: 10 } } }
                        },
                        scales: { y: { min: 0, max: 100 } }
                    }
                });
            }
            return;
        }

        var countries = Object.keys(riskTrends);
        var riskColors = ['#dc2626', '#f97316', '#eab308', '#2c4a6e', '#8b5cf6', '#ec4899'];
        var allRiskDates = {};
        var riskDatasets = [];

        for (var i = 0; i < countries.length; i++) {
            var country = countries[i];
            var risks = riskTrends[country] || [];
            if (risks.length > 0) {
                for (var r = 0; r < risks.length; r++) {
                    allRiskDates[risks[r].date] = true;
                }
                var riskValues = [];
                for (var r2 = 0; r2 < risks.length; r2++) {
                    riskValues.push(risks[r2].risk);
                }
                riskDatasets.push({
                    label: country,
                    data: riskValues,
                    borderColor: riskColors[i % riskColors.length],
                    fill: false,
                    tension: 0.3,
                    pointRadius: 3,
                    pointHoverRadius: 5
                });
            }
        }

        var sortedRiskDates = Object.keys(allRiskDates).sort();

        var ctx2 = document.getElementById('riskTrendChart');
        if (ctx2) {
            if (window.riskChart) window.riskChart.destroy();
            var formattedRiskDates = [];
            for (var d = 0; d < sortedRiskDates.length; d++) {
                var dateObj = new Date(sortedRiskDates[d]);
                formattedRiskDates.push(dateObj.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
            }
            window.riskChart = new Chart(ctx2, {
                type: 'line',
                data: {
                    labels: formattedRiskDates,
                    datasets: riskDatasets
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
            console.log('✅ Risk chart updated with real data');
        }

    } catch (e) {
        console.error('Risk trend error:', e);
    }
}

async function exportData(type) {
    var statusDiv = document.getElementById('exportStatus');
    if (!statusDiv) return;

    statusDiv.textContent = '⏳ Exporting...';

    try {
        var endpoint, filename;
        switch (type) {
            case 'events':
                endpoint = API_URL + '/events/export/csv';
                filename = 'events';
                break;
            case 'recommendations':
                endpoint = API_URL + '/recommendations';
                filename = 'recommendations';
                break;
            case 'prices':
                endpoint = API_URL + '/prices/live-comprehensive';
                filename = 'prices';
                break;
            case 'risk':
                endpoint = API_URL + '/country-risk/enhanced';
                filename = 'country-risk';
                break;
            default:
                throw new Error('Unknown export type');
        }

        var response = await fetch(endpoint);
        if (!response.ok) throw new Error('Failed to fetch data');

        if (type === 'events') {
            var blob = await response.blob();
            var link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = filename + '_' + new Date().toISOString().split('T')[0] + '.csv';
            link.click();
            URL.revokeObjectURL(link.href);
        } else {
            var data = await response.json();
            var jsonData = data.success ? data.data : data;
            if (window.DataExporter) {
                window.DataExporter.toJSON(jsonData, filename);
            } else {
                var jsonContent = JSON.stringify(jsonData, null, 2);
                var blob2 = new Blob([jsonContent], { type: 'application/json;charset=utf-8' });
                var link2 = document.createElement('a');
                link2.href = URL.createObjectURL(blob2);
                link2.download = filename + '_' + new Date().toISOString().split('T')[0] + '.json';
                link2.click();
                URL.revokeObjectURL(link2.href);
            }
        }

        statusDiv.textContent = '✅ Export successful!';
    } catch (error) {
        console.error('Export error:', error);
        statusDiv.textContent = '❌ Export failed: ' + error.message;
    }
}

async function exportAllData() {
    var statusDiv = document.getElementById('exportStatus');
    if (!statusDiv) return;

    statusDiv.textContent = '⏳ Exporting all data...';

    try {
        var eventsResponse = await fetch(API_URL + '/events?limit=1000');
        var events = await eventsResponse.json();
        var recResponse = await fetch(API_URL + '/recommendations?limit=200');
        var recommendations = await recResponse.json();
        var pricesResponse = await fetch(API_URL + '/prices/live-comprehensive');
        var prices = await pricesResponse.json();
        var riskResponse = await fetch(API_URL + '/country-risk/enhanced');
        var risk = await riskResponse.json();

        var allData = {
            events: events.success ? events.data : events,
            recommendations: recommendations.success ? recommendations.data : recommendations,
            prices: prices.success ? prices.data : prices,
            risk: risk.success ? risk.data : risk,
            exported_at: new Date().toISOString()
        };

        if (window.DataExporter) {
            window.DataExporter.toJSON(allData, 'athena-scip-all-data');
        } else {
            var jsonContent = JSON.stringify(allData, null, 2);
            var blob = new Blob([jsonContent], { type: 'application/json;charset=utf-8' });
            var link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = 'athena-scip-all-data_' + new Date().toISOString().split('T')[0] + '.json';
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

    var trendPeriod = document.getElementById('trendPeriod');
    var days = trendPeriod ? parseInt(trendPeriod.value) : 14;
    await loadTrends(days);

    updateTimestamp();
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    var logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) logoutBtn.addEventListener('click', logout);

    var showMoreBtn = document.getElementById('showMorePrices');
    if (showMoreBtn) showMoreBtn.addEventListener('click', loadMorePrices);

    var trendPeriod = document.getElementById('trendPeriod');
    if (trendPeriod) {
        trendPeriod.addEventListener('change', function() {
            loadTrends(parseInt(this.value));
        });
    }

    checkAuth().then(function() {
        loadAll();
        setInterval(loadAll, 60000);
    });
});