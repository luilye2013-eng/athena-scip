/**
 * Athena SCIP - Events Page Logic
 */

// Use window objects - NO DECLARATIONS
const API_URL = window.CONFIG.API_URL;
const supabaseClient = window.supabaseClient;

async function checkAuth() {
    const { data: { session } } = await supabaseClient.auth.getSession();
    if (!session) window.location.href = 'secure-login.html';
    else {
        const userInfo = document.getElementById('userInfo');
        if (userInfo) userInfo.innerHTML = `👤 ${session.user.email}`;
    }
}

async function loadEvents() {
    try {
        const response = await fetch(`${API_URL}/events?limit=1000`);
        const result = await response.json();
        const data = result.success ? result.data : null;
        const events = data?.events || [];

        document.getElementById('totalEvents').innerText = events.length;
        document.getElementById('warCount').innerText = events.filter(e => e.event_type === 'war').length;
        document.getElementById('disasterCount').innerText = events.filter(e => e.event_type === 'natural_disaster').length;
        document.getElementById('otherCount').innerText = events.filter(e => !['war', 'natural_disaster'].includes(e.event_type)).length;

        if (!events.length) {
            document.getElementById('eventsContainer').innerHTML = '<p>No events found</p>';
            return;
        }

        let html = `<table style="width:100%; border-collapse: collapse; font-size: 13px;">
            <thead>
                <tr style="background: #f1f5f9; text-align: left;">
                    <th style="padding: 10px; border-bottom: 2px solid #e2e8f0;">Title</th>
                    <th style="padding: 10px; border-bottom: 2px solid #e2e8f0;">Type</th>
                    <th style="padding: 10px; border-bottom: 2px solid #e2e8f0;">Severity</th>
                    <th style="padding: 10px; border-bottom: 2px solid #e2e8f0;">Location</th>
                    <th style="padding: 10px; border-bottom: 2px solid #e2e8f0;">Source</th>
                    <th style="padding: 10px; border-bottom: 2px solid #e2e8f0;">Date</th>
                </tr>
            </thead>
            <tbody>`;

        for (let e of events) {
            const severityClass = e.severity >= 4 ? 'severity-5' : e.severity >= 3 ? 'severity-4' : e.severity >= 2 ? 'severity-3' : 'severity-2';
            const severityText = e.severity >= 4 ? 'Critical' : e.severity >= 3 ? 'High' : e.severity >= 2 ? 'Medium' : 'Low';
            const location = e.location_country || e.location_city || 'Unknown';
            const date = e.created_at ? new Date(e.created_at).toLocaleDateString() : 'N/A';
            
            html += `<tr style="border-bottom: 1px solid #e5e7eb;">
                <td style="padding: 10px;">${e.title || 'Untitled'}</td>
                <td style="padding: 10px;">${e.event_type || 'other'}</td>
                <td style="padding: 10px;"><span class="severity-badge ${severityClass}">${severityText}</span></td>
                <td style="padding: 10px;">${location}</td>
                <td style="padding: 10px; font-size: 11px;">${e.source || 'N/A'}</td>
                <td style="padding: 10px; font-size: 11px;">${date}</td>
            </tr>`;
        }

        html += `</tbody></table>`;
        document.getElementById('eventsContainer').innerHTML = html;
        const lastUpdated = document.getElementById('lastUpdated');
if (lastUpdated) {
    lastUpdated.innerHTML = `Last updated: ${new Date().toLocaleString()}`;
}

    } catch (error) {
    console.error('Events error:', error);
    document.getElementById('eventsContainer').innerHTML = '<p>Error loading events</p>';
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
    checkAuth().then(loadEvents);
});