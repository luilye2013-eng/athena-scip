/**
 * Athena SCIP - Analytics Page Logic
 */

const supabaseClient = supabase.createClient(CONFIG.SUPABASE_URL, CONFIG.SUPABASE_KEY);
const API_URL = CONFIG.API_URL;

let dailyChart = null, typeChart = null, countryChart = null;

async function checkAuth() {
    const { data: { session } } = await supabaseClient.auth.getSession();
    if (!session) window.location.href = 'secure-login.html';
    else {
        const userInfo = document.getElementById('userInfo');
        if (userInfo) userInfo.innerHTML = `👤 ${session.user.email}`;
    }
}

async function loadAnalytics() {
    try {
        // Fetch all events
        const response = await fetch(`${API_URL}/events?limit=1000`);
        const result = await response.json();
        const data = result.success ? result.data : null;
        const events = data?.events || [];

        // Stats
        document.getElementById('totalEvents').innerText = events.length;
        document.getElementById('warEvents').innerText = events.filter(e => e.event_type === 'war').length;
        document.getElementById('disasterEvents').innerText = events.filter(e => e.event_type === 'natural_disaster').length;
        const countries = new Set(events.map(e => e.location_country).filter(c => c && !['Unknown', 'null'].includes(c)));
        document.getElementById('affectedCountries').innerText = countries.size;

        // Daily trends
        const dailyData = {};
        events.forEach(e => {
            const date = e.created_at ? new Date(e.created_at).toISOString().split('T')[0] : null;
            if (date) {
                dailyData[date] = (dailyData[date] || 0) + 1;
            }
        });
        const sortedDates = Object.keys(dailyData).sort();
        const dailyCounts = sortedDates.map(d => dailyData[d]);

        if (dailyChart) dailyChart.destroy();
        const ctx1 = document.getElementById('dailyTrendChart');
        if (ctx1) {
            dailyChart = new Chart(ctx1, {
                type: 'line',
                data: {
                    labels: sortedDates.map(d => d.slice(5)),
                    datasets: [{
                        label: 'Events per Day',
                        data: dailyCounts,
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        fill: true,
                        tension: 0.3
                    }]
                },
                options: { 
                    responsive: true, 
                    maintainAspectRatio: true, 
                    plugins: { 
                        legend: { position: 'top' } 
                    },
                    scales: { y: { beginAtZero: true } }
                }
            });
        }

        // Type distribution
        const typeCounts = {};
        events.forEach(e => {
            const type = e.event_type || 'other';
            typeCounts[type] = (typeCounts[type] || 0) + 1;
        });
        const typeLabels = Object.keys(typeCounts);
        const typeData = typeLabels.map(t => typeCounts[t]);
        const typeColors = ['#dc2626', '#f97316', '#eab308', '#22c55e', '#3b82f6', '#8b5cf6', '#ec4899', '#14b8a6'];

        if (typeChart) typeChart.destroy();
        const ctx2 = document.getElementById('typeDistributionChart');
        if (ctx2) {
            typeChart = new Chart(ctx2, {
                type: 'bar',
                data: {
                    labels: typeLabels.map(t => t.replace('_', ' ')),
                    datasets: [{
                        label: 'Event Count',
                        data: typeData,
                        backgroundColor: typeColors.slice(0, typeLabels.length)
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: { 
                        legend: { display: false } 
                    },
                    scales: { 
                        y: { beginAtZero: true } 
                    }
                }
            });
        }

        // Country chart - different colors for each bar
        const countryData = {};
        events.forEach(e => {
            const country = e.location_country;
            if (country && !['Unknown', 'null', 'N/A'].includes(country)) {
                countryData[country] = (countryData[country] || 0) + 1;
            }
        });
        const sortedCountries = Object.entries(countryData).sort((a, b) => b[1] - a[1]).slice(0, 12);
        const countryLabels = sortedCountries.map(c => c[0]);
        const countryCounts = sortedCountries.map(c => c[1]);
        const countryColors = CONFIG.COLORS.chart;

        if (countryChart) countryChart.destroy();
        const ctx3 = document.getElementById('countryChart');
        if (ctx3) {
            countryChart = new Chart(ctx3, {
                type: 'bar',
                data: {
                    labels: countryLabels,
                    datasets: [{
                        label: 'Event Count',
                        data: countryCounts,
                        backgroundColor: countryColors.slice(0, countryLabels.length),
                        borderColor: 'rgba(255,255,255,0.3)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: { 
                        legend: { display: false } 
                    },
                    scales: {
                        y: { beginAtZero: true },
                        x: { ticks: { font: { size: 10 } } }
                    }
                }
            });
        }

        document.getElementById('lastUpdated').innerHTML = `Last updated: ${new Date().toLocaleString()}`;

    } catch (error) {
        console.error('Analytics error:', error);
    }
}

// Initialize
checkAuth().then(loadAnalytics);