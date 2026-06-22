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
        var allPrices = data?.prices || [];
        var dataSource = data?.data_source || 'Unknown';
        var message = data?.message || '';

        if (allPrices.length === 0) {
            container.innerHTML = `
                <div style="text-align: center; padding: 20px; color: #6b7280;">
                    <p>⚠️ No price data available</p>
                    <p style="font-size: 11px; margin-top: 8px;">Please check back later.</p>
                </div>
            `;
            return;
        }

        // Store for display
        window.allPrices = allPrices;
        displayPrices();

    } catch (e) {
        console.error('Price load error:', e);
        container.innerHTML = '<p>Price data unavailable</p>';
    }
}

function displayPrices() {
    var container = document.getElementById('pricesContainer');
    if (!container) return;

    // Check if we have prices
    if (!window.allPrices || window.allPrices.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 20px; color: #6b7280;">
                <p>📊 No commodity prices available</p>
                <p style="font-size: 11px; margin-top: 8px;">Live prices are currently unavailable. Please check back later.</p>
            </div>
        `;
        return;
    }

    var prices = window.allPrices.slice(0, priceDisplayLimit);
    var showMoreBtn = document.getElementById('showMorePrices');

    if (window.allPrices.length > priceDisplayLimit) {
        if (showMoreBtn) {
            showMoreBtn.style.display = 'inline-block';
            showMoreBtn.textContent = 'Show More (' + (window.allPrices.length - priceDisplayLimit) + ' remaining)';
        }
    } else {
        if (showMoreBtn) showMoreBtn.style.display = 'none';
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

    // Determine data source
    var dataSource = 'Unknown';
    var isLive = false;
    if (window.allPrices.length > 0 && window.allPrices[0].source) {
        dataSource = window.allPrices[0].source;
        isLive = dataSource.includes('Live') || dataSource.includes('Yahoo');
    }
    
    var sourceIcon = isLive ? '✅' : '📊';
    var sourceNote = isLive ? ' (Live data)' : ' (Reference data - may not reflect current market)';
    
    html += `
        <div style="font-size: 10px; color: #6b7280; text-align: right; margin-top: 8px; padding-top: 8px; border-top: 1px solid #e5e7eb;">
            ${sourceIcon} Source: <strong>${dataSource}</strong>${sourceNote}
        </div>
    `;

    container.innerHTML = html;
}
function loadMorePrices() {
    priceDisplayLimit += 12;
    displayPrices();
}

function refreshPrices() {
    console.log('🔄 Refreshing prices...');
    loadPrices();
    loadTrends(parseInt(document.getElementById('trendPeriod').value));
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

        // Update the risk grid
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

        // Pie chart - with proper destroy check to prevent flickering
        var ctx = document.getElementById('riskPieChart');
        if (ctx) {
            // Properly destroy existing chart
            if (window.riskPieChart) {
                try {
                    window.riskPieChart.destroy();
                } catch (e) {
                    console.warn('Chart destroy warning:', e);
                }
                window.riskPieChart = null;
            }

            // Create new chart
            try {
                window.riskPieChart = new Chart(ctx, {
                    type: 'pie',
                    data: {
                        labels: riskLabels,
                        datasets: [{
                            data: riskScores,
                            backgroundColor: ['#dc2626', '#f97316', '#eab308', '#22c55e', '#3b82f6', '#8b5cf6', '#ec4899', '#14b8a6', '#f59e0b', '#6366f1', '#06b6d4', '#84cc16']
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: true,
                        plugins: {
                            legend: {
                                position: 'bottom',
                                labels: { 
                                    font: { size: 9 },
                                    boxWidth: 10,
                                    padding: 8
                                }
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

        var ctx1 = document.getElementById('priceTrendChart');
        if (!ctx1) return;

        // Handle no data
        if (Object.keys(priceTrends).length === 0) {
            if (window.priceChart) window.priceChart.destroy();
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
                labels: {
                    font: { size: 9 },
                    boxWidth: 12,
                    padding: 8
                }
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                ticks: {
                    font: { size: 8 },
                    maxTicksLimit: 6,
                    callback: function(value) {
                        if (value >= 1000) {
                            return '$' + (value / 1000).toFixed(0) + 'k';
                        }
                        return '$' + value.toFixed(0);
                    }
                },
                title: {
                    display: true,
                    text: 'Price (USD)',
                    font: { size: 9 }
                }
            },
            x: {
                ticks: {
                    font: { size: 7 },
                    maxRotation: 45,
                    minRotation: 0,
                    autoSkip: true,
                    maxTicksLimit: 10
                }
            }
        },
        // Prevent chart from expanding
        layout: {
            padding: {
                left: 5,
                right: 5,
                top: 5,
                bottom: 5
            }
        }
    }
});
            
            var overlay = ctx1.parentElement.querySelector('.no-data-overlay');
            if (!overlay) {
                overlay = document.createElement('div');
                overlay.className = 'no-data-overlay';
                overlay.style.cssText = 'position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; color: #6b7280; font-size: 14px; pointer-events: none;';
                overlay.innerHTML = '📊 No price trends data available<br><span style="font-size: 11px;">Data is being collected. Please check back tomorrow.</span>';
                ctx1.parentElement.style.position = 'relative';
                ctx1.parentElement.appendChild(overlay);
            }
            
            await loadRiskTrends(days);
            return;
        }

        var existingOverlay = ctx1.parentElement.querySelector('.no-data-overlay');
        if (existingOverlay) existingOverlay.remove();

        // Get all commodities and limit to 5 most relevant
        var allCommodities = Object.keys(priceTrends);
        
        // Calculate price range for each commodity and sort by max price
        var commodityRanges = [];
        for (var c = 0; c < allCommodities.length; c++) {
            var commodity = allCommodities[c];
            var prices = priceTrends[commodity] || [];
            var maxPrice = 0;
            for (var p = 0; p < prices.length; p++) {
                if (prices[p].price > maxPrice) maxPrice = prices[p].price;
            }
            commodityRanges.push({ name: commodity, maxPrice: maxPrice });
        }
        // Sort by max price descending, then take top 5
        commodityRanges.sort(function(a, b) { return b.maxPrice - a.maxPrice; });
        var commodities = [];
        for (var c = 0; c < Math.min(5, commodityRanges.length); c++) {
            commodities.push(commodityRanges[c].name);
        }

        var colors = window.CONFIG.COLORS.chart;
        var allDates = {};
        var datasets = [];
        var currentYear = new Date().getFullYear();

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

        if (window.priceChart) window.priceChart.destroy();
        var formattedDates = [];
        for (var d = 0; d < sortedDates.length; d++) {
            var dateObj = new Date(sortedDates[d]);
            var dateYear = dateObj.getFullYear();
            var formatOptions = dateYear === currentYear
                ? { month: 'short', day: 'numeric' }
                : { month: 'short', day: 'numeric', year: 'numeric' };
            formattedDates.push(dateObj.toLocaleDateString('en-US', formatOptions));
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
                        labels: {
                            font: { size: 9 },
                            boxWidth: 12,
                            padding: 8
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            font: { size: 8 },
                            maxTicksLimit: 6,
                            callback: function(value) {
                                if (value >= 1000) {
                                    return '$' + (value / 1000).toFixed(0) + 'k';
                                }
                                return '$' + value.toFixed(0);
                            }
                        },
                        title: {
                            display: true,
                            text: 'Price (USD)',
                            font: { size: 9 }
                        }
                    },
                    x: {
                        ticks: {
                            font: { size: 7 },
                            maxRotation: 45,
                            minRotation: 0,
                            autoSkip: true,
                            maxTicksLimit: 10
                        }
                    }
                }
            }
        });
        console.log('✅ Price chart updated with top 5 commodities');

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

        var ctx2 = document.getElementById('riskTrendChart');
        if (!ctx2) return;

        // Handle no data
        if (Object.keys(riskTrends).length === 0) {
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
                    scales: {
                        y: {
                            min: 0,
                            max: 100,
                            ticks: { stepSize: 10 }
                        }
                    }
                }
            });
            return;
        }

        var countries = Object.keys(riskTrends);
        var riskColors = ['#dc2626', '#f97316', '#eab308', '#2c4a6e', '#8b5cf6', '#ec4899'];
        var allRiskDates = {};
        var riskDatasets = [];
        var currentYear = new Date().getFullYear();

        for (var i = 0; i < countries.length; i++) {
            var country = countries[i];
            var risks = riskTrends[country] || [];
            if (risks.length > 0) {
                for (var r = 0; r < risks.length; r++) {
                    allRiskDates[risks[r].date] = true;
                }
                var riskValues = [];
                for (var r2 = 0; r2 < risks.length; r2++) {
                    var riskVal = Math.min(100, Math.max(0, risks[r2].risk || 0));
                    riskValues.push(riskVal);
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

        if (window.riskChart) window.riskChart.destroy();
        var formattedRiskDates = [];
        for (var d = 0; d < sortedRiskDates.length; d++) {
            var dateObj = new Date(sortedRiskDates[d]);
            var dateYear = dateObj.getFullYear();
            var formatOptions = dateYear === currentYear
                ? { month: 'short', day: 'numeric' }
                : { month: 'short', day: 'numeric', year: 'numeric' };
            formattedRiskDates.push(dateObj.toLocaleDateString('en-US', formatOptions));
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
                        labels: {
                            font: { size: 10 },
                            boxWidth: 12,
                            padding: 10
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + context.parsed.y + '%';
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        min: 0,
                        max: 100,
                        ticks: {
                            stepSize: 10,
                            font: { size: 9 },
                            callback: function(value) {
                                return value + '%';
                            }
                        },
                        title: {
                            display: true,
                            text: 'Risk Score',
                            font: { size: 10 }
                        }
                    },
                    x: {
                        ticks: {
                            font: { size: 8 },
                            maxRotation: 45,
                            minRotation: 0,
                            autoSkip: true,
                            maxTicksLimit: 12,
                            sampleSize: 10
                        },
                        grid: {
                            display: false
                        }
                    }
                },
                layout: {
                    padding: {
                        left: 5,
                        right: 5,
                        top: 5,
                        bottom: 5
                    }
                }
            }
        });
        console.log('✅ Risk chart updated with real data (0-100 scale)');

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