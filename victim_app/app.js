/**
 * RESQ-NET Victim Emergency SOS App Client Engine
 * Auto-detects Backend IP so it works from any device on the network.
 */

// If opened via 127.0.0.1/localhost (same machine), use localhost.
// If opened via the server's real IP (phone, tablet, other PC), use that IP.
// Auto-detects Backend API URL: supports local dev (http://...:8000) and production cloud HTTPS (https://domain.com)
const API_BASE = (() => {
    const origin = window.location.origin;
    const host = window.location.hostname;
    if (origin.startsWith("file://") || host === "127.0.0.1" || host === "localhost") {
        return "http://127.0.0.1:8000";
    }
    return origin;
})();

let userToken = localStorage.getItem("resq_victim_token") || "";
let currentLatitude = 13.0827; // Default Chennai GPS
let currentLongitude = 80.2707;
let activeIncidentId = null;
let pollTimer = null;

// DOM Elements
const btnTriggerSos = document.getElementById("btnTriggerSos");
const floorSelect = document.getElementById("floorSelect");
const zoneSelect = document.getElementById("zoneSelect");
const urgencySelect = document.getElementById("urgencySelect");
const messageInput = document.getElementById("messageInput");
const gpsText = document.getElementById("gpsText");

const sosCard = document.getElementById("sosCard");
const trackerCard = document.getElementById("trackerCard");
const trackerIncidentId = document.getElementById("trackerIncidentId");
const trackerStatusText = document.getElementById("trackerStatusText");
const trackerDetailText = document.getElementById("trackerDetailText");
const btnCancelSos = document.getElementById("btnCancelSos");

document.addEventListener("DOMContentLoaded", async () => {
    await autoAuthenticateVictim();
    acquirePhoneGPS();
    setupEventListeners();
});

// Auto Login as Victim User
async function autoAuthenticateVictim(forceRefresh = false) {
    if (userToken && !forceRefresh) return userToken;

    try {
        const res = await fetch(`${API_BASE}/api/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username: "victim1", password: "user123" })
        });
        const data = await res.json();
        if (res.ok) {
            userToken = data.access_token;
            localStorage.setItem("resq_victim_token", userToken);
            return userToken;
        } else {
            console.warn("Victim login attempt response:", data.detail);
        }
    } catch (err) {
        console.error("Auto login error:", err);
    }
    return null;
}

// Fetch Browser / Phone GPS
function acquirePhoneGPS() {
    if ("geolocation" in navigator) {
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                currentLatitude = pos.coords.latitude;
                currentLongitude = pos.coords.longitude;
                gpsText.innerHTML = `<i class="fa-solid fa-location-crosshairs"></i> GPS Acquired: ${currentLatitude.toFixed(4)}, ${currentLongitude.toFixed(4)}`;
            },
            (err) => {
                gpsText.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> GPS Default (Building Fixed Grid)`;
            }
        );
    } else {
        gpsText.innerText = "GPS Not Supported";
    }
}

// Setup Event Listeners
function setupEventListeners() {
    btnTriggerSos.addEventListener("click", sendEmergencySos);
    btnCancelSos.addEventListener("click", resetSosView);
}

// Send SOS Request to Backend
async function sendEmergencySos() {
    if (!userToken) {
        await autoAuthenticateVictim(true);
    }

    const payload = {
        latitude: currentLatitude,
        longitude: currentLongitude,
        floor: floorSelect.value,
        zone: zoneSelect.value,
        urgency: urgencySelect.value,
        message: messageInput.value || "Emergency SOS Distress"
    };

    try {
        btnTriggerSos.disabled = true;
        btnTriggerSos.style.opacity = "0.6";

        let res = await fetch(`${API_BASE}/api/sos`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${userToken}`
            },
            body: JSON.stringify(payload)
        });

        // If stale or expired token returned 401, clear local token, re-authenticate, and retry once
        if (res.status === 401) {
            localStorage.removeItem("resq_victim_token");
            userToken = "";
            await autoAuthenticateVictim(true);

            const headers = { "Content-Type": "application/json" };
            if (userToken) {
                headers["Authorization"] = `Bearer ${userToken}`;
            }

            res = await fetch(`${API_BASE}/api/sos`, {
                method: "POST",
                headers: headers,
                body: JSON.stringify(payload)
            });
        }

        const data = await res.json();
        if (res.ok) {
            activeIncidentId = data.id;
            showTrackerCard(data);
            startStatusPolling();
        } else {
            alert("Failed to send SOS: " + (data.detail || "Server error"));
            btnTriggerSos.disabled = false;
            btnTriggerSos.style.opacity = "1";
        }
    } catch (err) {
        alert("Network error while sending SOS signal.");
        btnTriggerSos.disabled = false;
        btnTriggerSos.style.opacity = "1";
    }
}

// Show Active Tracker UI
function showTrackerCard(incidentData) {
    sosCard.style.display = "none";
    trackerCard.style.display = "block";
    trackerIncidentId.innerText = incidentData.id;
    updateTrackerStepUI(incidentData.status);
}

// Poll Incident Status from Backend
function startStatusPolling() {
    if (pollTimer) clearInterval(pollTimer);
    pollTimer = setInterval(async () => {
        if (!activeIncidentId) return;

        try {
            const res = await fetch(`${API_BASE}/api/incidents/${activeIncidentId}`);
            if (res.ok) {
                const inc = await res.json();
                updateTrackerStepUI(inc.status);
            }
        } catch (err) {
            console.error("Polling error:", err);
        }
    }, 1000);
}

// Update Step Tracker Progress
function updateTrackerStepUI(status) {
    const stepSos = document.getElementById("step-sos");
    const stepAdmin = document.getElementById("step-admin");
    const stepDispatched = document.getElementById("step-dispatched");
    const stepArrived = document.getElementById("step-arrived");

    const line1 = document.getElementById("line-1");
    const line2 = document.getElementById("line-2");
    const line3 = document.getElementById("line-3");

    if (status === "SOS_RECEIVED") {
        stepSos.className = "step-item active";
        stepAdmin.className = "step-item";
        stepDispatched.className = "step-item";
        stepArrived.className = "step-item";
        trackerStatusText.innerText = "SOS Received at Rescue Operations";
        trackerDetailText.innerText = "Distress signal logged. Priority engine evaluated rescue rank.";
    } else if (status === "ADMIN_NOTIFIED" || status === "ROBOT_DISPATCHED") {
        stepSos.className = "step-item completed";
        stepAdmin.className = "step-item active";
        stepDispatched.className = "step-item";
        stepArrived.className = "step-item";
        line1.className = "step-line active";
        trackerStatusText.innerText = "Rescue Operator Dispatched Robot";
        trackerDetailText.innerText = "Robot R1 has been assigned to your building floor and zone.";
    } else if (status === "ROBOT_EN_ROUTE") {
        stepSos.className = "step-item completed";
        stepAdmin.className = "step-item completed";
        stepDispatched.className = "step-item active";
        stepArrived.className = "step-item";
        line1.className = "step-line active";
        line2.className = "step-line active";
        trackerStatusText.innerText = "ResQ-OmniBot En-Route to Your Zone!";
        trackerDetailText.innerText = "Robot is executing sequential motor movement steps to reach your floor.";
    } else if (status === "ROBOT_ARRIVED") {
        stepSos.className = "step-item completed";
        stepAdmin.className = "step-item completed";
        stepDispatched.className = "step-item completed";
        stepArrived.className = "step-item completed";
        line1.className = "step-line active";
        line2.className = "step-line active";
        line3.className = "step-line active";
        trackerStatusText.innerText = "🚨 ROBOT HAS ARRIVED AT YOUR ZONE!";
        trackerDetailText.innerText = "ResQ-OmniBot is outside your room. Remain calm.";
    }
}

// Reset view to send new SOS
function resetSosView() {
    if (pollTimer) clearInterval(pollTimer);
    activeIncidentId = null;
    trackerCard.style.display = "none";
    sosCard.style.display = "block";
    btnTriggerSos.disabled = false;
    btnTriggerSos.style.opacity = "1";
}
