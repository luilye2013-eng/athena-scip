/**
 * Athena SCIP - Recommendations Page Logic
 */

// Use window objects - NO DECLARATIONS
const API_URL = window.CONFIG.API_URL;
const supabaseClient = window.supabaseClient;

const COST_REFERENCE = {
    'Wheat': { basePrice: 245, unit: 'per ton', shippingCost: 0.15 },
    'Natural Gas': { basePrice: 3.28, unit: 'per MMBtu', shippingCost: 0.20 },
    'Oil': { basePrice: 77.50, unit: 'per barrel', shippingCost: 0.18 },
    'Steel': { basePrice: 847.50, unit: 'per ton', shippingCost: 0.12 },
    'Semiconductors': { basePrice: 1248, unit: 'per wafer', shippingCost: 0.25 },
    'Lithium': { basePrice: 14750, unit: 'per ton', shippingCost: 0.30 },
    'Nickel': { basePrice: 18450, unit: 'per ton', shippingCost: 0.22 },
    'Iron Ore': { basePrice: 117.20, unit: 'per ton', shippingCost: 0.10 }
};

const SUPPLIER_ALTERNATIVES = {
    'Russia': [
        { country: 'United States', leadTime: 30, costIncrease: 25 },
        { country: 'Qatar', leadTime: 25, costIncrease: 20 },
        { country: 'Norway', leadTime: 28, costIncrease: 22 }
    ],
    'Ukraine': [
        { country: 'Poland', leadTime: 18, costIncrease: 12 },
        { country: 'Romania', leadTime: 20, costIncrease: 15 },
        { country: 'Germany', leadTime: 22, costIncrease: 18 }
    ],
    'Iran': [
        { country: 'Saudi Arabia', leadTime: 15, costIncrease: 10 },
        { country: 'UAE', leadTime: 12, costIncrease: 8 },
        { country: 'Iraq', leadTime: 18, costIncrease: 14 }
    ],
    'Israel': [
        { country: 'Egypt', leadTime: 20, costIncrease: 15 },
        { country: 'Greece', leadTime: 25, costIncrease: 20 },
        { country: 'Cyprus', leadTime: 22, costIncrease: 17 }
    ],
    'China': [
        { country: 'Vietnam', leadTime: 14, costIncrease: 10 },
        { country: 'India', leadTime: 16, costIncrease: 12 },
        { country: 'Taiwan', leadTime: 10, costIncrease: 8 }
    ]
};

async function checkAuth() {
    const { data: { session } } = await supabaseClient.auth.getSession();
    if (!session) window.location.href = 'secure-login.html';
    else {
        const userInfo = document.getElementById('userInfo');
        if (userInfo) userInfo.innerHTML = `👤 ${session.user.email}`;
    }
}

function generateRecommendationCard(r) {
    const urgencyClass = r.urgency === 'immediate' ? 'severity-5' : r.urgency === 'short_term' ? 'severity-4' : 'severity-2';
    const actions = r.actions || ['Monitor situation', 'Review inventory'];
    const commodities = r.affected_commodities || ['General'];
    
    let costHTML = '';
    for (let comm of commodities.slice(0, 3)) {
        const costData = COST_REFERENCE[comm];
        if (costData) {
            const costImpact = (costData.basePrice * 0.15).toFixed(2);
            costHTML += `<li>${comm}: ~$${costImpact} ${costData.unit} additional cost</li>`;
        }
    }
    
    const country = r.location_country || 'Russia';
    const alternatives = SUPPLIER_ALTERNATIVES[country] || SUPPLIER_ALTERNATIVES['Russia'];
    let supplierHTML = '';
    if (alternatives && alternatives.length) {
        supplierHTML = `<div style="margin-top: 8px; font-size: 12px; background: #f1f5f9; padding: 8px; border-radius: 6px;">
            <strong>🔄 Supplier Options:</strong><br>`;
        for (let alt of alternatives.slice(0, 3)) {
            supplierHTML += `${alt.country} (Lead time: ${alt.leadTime}d, Cost: +${alt.costIncrease}%)<br>`;
        }
        supplierHTML += `</div>`;
    }

    return `
        <div class="card" style="border-left: 4px solid ${r.urgency === 'immediate' ? '#dc2626' : r.urgency === 'short_term' ? '#f97316' : '#eab308'}; margin-bottom: 15px;">
            <div style="display: flex; justify-content: space-between; align-items: start; flex-wrap: wrap;">
                <h3 style="color: ${r.urgency === 'immediate' ? '#dc2626' : r.urgency === 'short_term' ? '#f97316' : '#2c4a6e'}; margin-bottom: 8px; font-size: 14px;">
                    ${r.urgency === 'immediate' ? '🚨 IMMEDIATE' : r.urgency === 'short_term' ? '⚡ SHORT TERM' : '📋 LONG TERM'}
                </h3>
                <span class="severity-badge ${urgencyClass}">Severity: ${r.severity || 2}</span>
            </div>
            <p style="font-weight: 500; margin-bottom: 8px; font-size: 14px;">${r.event_title || 'Recommendation'}</p>
            <p style="font-size: 13px; color: #4b5563; margin-bottom: 8px;">
                <strong>Affected:</strong> ${commodities.join(', ')}
            </p>
            <div style="font-size: 13px;">
                <strong>Actions:</strong>
                <ul style="margin-top: 4px; padding-left: 20px;">
                    ${actions.map(a => `<li>${a}</li>`).join('')}
                </ul>
            </div>
            ${costHTML ? `<div style="margin-top: 8px; font-size: 12px; background: #fef3c7; padding: 8px; border-radius: 6px;">
                <strong>💰 Cost Impact:</strong>
                <ul style="margin-top: 4px; padding-left: 20px; margin-bottom: 0;">${costHTML}</ul>
            </div>` : ''}
            ${supplierHTML}
        </div>
    `;
}

async function loadRecommendations() {
    const container = document.getElementById('recommendationsContainer');
    if (!container) return;
    
    try {
        const response = await fetch(`${API_URL}/recommendations/improved?limit=10`);
        const result = await response.json();
        const data = result.success ? result.data : null;
        const recommendations = data?.recommendations || [];

        if (!recommendations.length) {
            container.innerHTML = '<div class="card"><p>No recommendations available</p></div>';
            return;
        }

        const mid = Math.ceil(recommendations.length / 2);
        const leftCol = recommendations.slice(0, mid);
        const rightCol = recommendations.slice(mid);

        let leftHTML = '';
        let rightHTML = '';

        for (let r of leftCol) {
            leftHTML += generateRecommendationCard(r);
        }
        for (let r of rightCol) {
            rightHTML += generateRecommendationCard(r);
        }

        container.innerHTML = `
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                <div>${leftHTML}</div>
                <div>${rightHTML}</div>
            </div>
        `;
        document.getElementById('lastUpdated').innerHTML = `Last updated: ${new Date().toLocaleString()}`;

    } catch (error) {
        console.error('Recommendations error:', error);
        container.innerHTML = '<div class="card"><p>Error loading recommendations</p></div>';
    }
}

async function runScenario(type) {
    const resultDiv = document.getElementById('scenarioResult');
    const titleDiv = document.getElementById('scenarioTitle');
    const contentDiv = document.getElementById('scenarioContent');
    
    if (!resultDiv) return;
    
    resultDiv.style.display = 'block';
    titleDiv.textContent = `⏳ Analyzing ${type.replace('_', ' ')} scenario...`;
    contentDiv.innerHTML = 'Loading...';
    
    try {
        const eventsResponse = await fetch(`${API_URL}/events?event_type=${type}&limit=20`);
        const eventsData = await eventsResponse.json();
        const events = eventsData.success ? eventsData.data.events : [];
        
        if (events.length === 0) {
            titleDiv.textContent = '⚠️ No data available for this scenario';
            contentDiv.innerHTML = 'There are no recent events of this type to simulate.';
            return;
        }
        
        let affectedCommodities = ['Wheat', 'Natural Gas', 'Oil', 'Steel'];
        if (type === 'natural_disaster' || type === 'weather') {
            affectedCommodities = ['Semiconductors', 'Lithium', 'Nickel', 'Iron Ore'];
        } else if (type === 'sanctions') {
            affectedCommodities = ['Oil', 'Natural Gas', 'Steel', 'Wheat'];
        } else if (type === 'strike' || type === 'shipping') {
            affectedCommodities = ['Steel', 'Semiconductors', 'Nickel', 'Iron Ore'];
        }
        
        let costImpactHTML = '';
        for (let comm of affectedCommodities.slice(0, 4)) {
            const costData = COST_REFERENCE[comm];
            if (costData) {
                const impact = (costData.basePrice * (0.10 + Math.random() * 0.20)).toFixed(2);
                costImpactHTML += `<li>${comm}: ~$${impact} ${costData.unit} (${(Math.random() * 20 + 5).toFixed(0)}% increase)</li>`;
            }
        }
        
        let supplierHTML = '';
        const supplierCountries = ['Brazil', 'Australia', 'Qatar', 'United States', 'Norway', 'Saudi Arabia', 'UAE', 'India'];
        for (let i = 0; i < Math.min(3, affectedCommodities.length); i++) {
            const alt = supplierCountries[i % supplierCountries.length];
            const leadTime = Math.floor(Math.random() * 20) + 10;
            const costIncrease = Math.floor(Math.random() * 20) + 5;
            supplierHTML += `<li>${affectedCommodities[i]}: ${alt} (Lead time: ${leadTime}d, Cost: +${costIncrease}%)</li>`;
        }
        
        let shippingImpact = '';
        if (type === 'shipping' || type === 'strike' || type === 'war') {
            const routes = ['Strait of Hormuz', 'Red Sea', 'Panama Canal', 'Suez Canal', 'South China Sea'];
            const selectedRoute = routes[Math.floor(Math.random() * routes.length)];
            const delay = Math.floor(Math.random() * 20) + 5;
            shippingImpact = `
                <div style="margin-top: 8px; font-size: 12px; background: #fef3c7; padding: 8px; border-radius: 6px;">
                    <strong>🚢 Shipping Impact:</strong><br>
                    Route: ${selectedRoute}<br>
                    Estimated Delay: ${delay} days<br>
                    Additional Cost: ~$${(delay * 1000).toFixed(0)} per container
                </div>
            `;
        }
        
        let html = `
            <div style="margin-bottom: 12px;">
                <strong>📋 Impact Analysis</strong>
                <ul style="margin-top: 6px; padding-left: 20px; font-size: 13px;">
                    <li>Based on ${events.length} recent ${type.replace('_', ' ')} events</li>
                    <li>Affected commodities: ${affectedCommodities.join(', ')}</li>
                    <li>Average severity: ${(events.reduce((sum, e) => sum + e.severity, 0) / events.length).toFixed(1)}/5</li>
                </ul>
            </div>
            <div style="margin-bottom: 12px;">
                <strong>💰 Cost Impact Analysis</strong>
                <ul style="margin-top: 6px; padding-left: 20px; font-size: 13px;">
                    ${costImpactHTML}
                </ul>
            </div>
            <div style="margin-bottom: 12px;">
                <strong>💡 Recommended Actions</strong>
                <ul style="margin-top: 6px; padding-left: 20px; font-size: 13px;">
                    <li>Activate business continuity plans for affected regions</li>
                    <li>Increase inventory buffer by 30-60 days</li>
                    <li>Identify alternative suppliers in stable regions</li>
                    <li>Reroute shipments away from conflict zones</li>
                </ul>
            </div>
            <div style="margin-bottom: 12px;">
                <strong>🔄 Supplier Alternatives</strong>
                <ul style="margin-top: 6px; padding-left: 20px; font-size: 13px;">
                    ${supplierHTML}
                </ul>
            </div>
            ${shippingImpact}
        `;
        
        titleDiv.textContent = `📊 Scenario Analysis: ${type.replace('_', ' ')} (${events.length} events analyzed)`;
        contentDiv.innerHTML = html;
        
    } catch (error) {
        console.error('Scenario error:', error);
        contentDiv.innerHTML = '❌ Error loading scenario data. Please try again.';
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function() {
            supabaseClient.auth.signOut().then(() => {
                window.location.href = 'secure-login.html';
            });
        });
    }
    checkAuth().then(loadRecommendations);
});