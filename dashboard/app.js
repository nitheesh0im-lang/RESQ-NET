/**
 * RESQ-NET Admin Rescue Control Center Client Engine
 * Auto-detects Backend IP so it works from any device on the network.
 */

// If opened via 127.0.0.1/localhost (same machine), use localhost.
// If opened via the server's real IP (phone, tablet, other PC), use that IP.
// Auto-detects Backend API URL with live cloud fallback (https://omni-boy.onrender.com)
let API_BASE = (() => {
    const origin = window.location.origin;
    const host = window.location.hostname;
    if (origin.startsWith("file://")) {
        return "https://omni-boy.onrender.com";
    }
    if (host === "127.0.0.1" || host === "localhost") {
        return "http://127.0.0.1:8000";
    }
    return origin;
})();

let adminToken = localStorage.getItem("resq_admin_token") || "";
let displayedMapFloor = "Floor 1";
let selectedIncidentId = null;
let selectedIncidentFloor = null;
let selectedIncidentZone = null;
let activeMissionId = null;
let currentRouteSteps = [];
let latestRobotState = null;
let isSimulating = false;

// DOM Elements
const incidentsListEl = document.getElementById("incidentsList");
const incidentCountEl = document.getElementById("incidentCount");
const activeIncidentLabelEl = document.getElementById("activeIncidentLabel");
const editorFloorSelect = document.getElementById("editorFloorSelect");
const editorZoneSelect = document.getElementById("editorZoneSelect");
const routeStepsListEl = document.getElementById("routeStepsList");
const logEntriesEl = document.getElementById("logEntries");

// Boolean Direction Cards
const boolCards = {
    NORTH: document.getElementById("bool-north"),
    SOUTH: document.getElementById("bool-south"),
    NORTHWEST: document.getElementById("bool-northwest"),
    SOUTHEAST: document.getElementById("bool-southeast"),
    CW: document.getElementById("bool-cw"),
    CCW: document.getElementById("bool-ccw")
};

// Initialize Application
document.addEventListener("DOMContentLoaded", () => {
    initAuthUI();
    setupEventListeners();
    initInteractiveBooleanCards();
    loadZoneRoute(editorFloorSelect.value, editorZoneSelect.value);

    // Start 1-second background polling
    setInterval(pollBackendState, 1000);
});

// Setup UI Event Listeners
function setupEventListeners() {
    // Floor Tabs (viewing different floor maps without breaking selected incident)
    document.querySelectorAll(".tab-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
            document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            displayedMapFloor = btn.getAttribute("data-floor");
            renderMapMarkers();
            if (latestRobotState) {
                updateRobotPositionUI(latestRobotState.estimated_floor, latestRobotState.estimated_zone);
            }
        });
    });

    // Route Editor Dropdowns
    editorFloorSelect.addEventListener("change", () => {
        loadZoneRoute(editorFloorSelect.value, editorZoneSelect.value);
    });

    editorZoneSelect.addEventListener("change", () => {
        loadZoneRoute(editorFloorSelect.value, editorZoneSelect.value);
    });

    // Buttons
    document.getElementById("btnAddStep").addEventListener("click", addStepRow);
    document.getElementById("btnSaveRoute").addEventListener("click", saveZoneRoute);
    document.getElementById("btnEmergencyStop").addEventListener("click", triggerEmergencyStop);
    document.getElementById("btnDispatchRobot").addEventListener("click", dispatchRealRobot);
    document.getElementById("btnSimulateRoute").addEventListener("click", runSoftwareSimulation);
    document.getElementById("btnPauseMission").addEventListener("click", pauseMission);
    document.getElementById("btnResumeMission").addEventListener("click", resumeMission);

    // Delete / Clear Incidents
    const btnClearAll = document.getElementById("btnClearAllIncidents");
    if (btnClearAll) {
        btnClearAll.addEventListener("click", clearAllIncidents);
    }

    // Auth Modal & Login/Logout Toggle
    document.getElementById("btnLoginModal").addEventListener("click", () => {
        if (adminToken) {
            // Logout
            adminToken = "";
            localStorage.removeItem("resq_admin_token");
            initAuthUI();
            logEvent("Auth", "Admin logged out");
        } else {
            // Open Login Modal
            const errEl = document.getElementById("loginError");
            if (errEl) errEl.style.display = "none";
            document.getElementById("loginModal").style.display = "flex";
        }
    });

    document.getElementById("btnCloseModal").addEventListener("click", () => {
        document.getElementById("loginModal").style.display = "none";
    });

    document.getElementById("loginForm").addEventListener("submit", handleLogin);
}

// Update Auth Badge UI
function updateAuthBadgeUI(isLoggedIn) {
    const badge = document.getElementById("userRoleBadge");
    const btn = document.getElementById("btnLoginModal");
    if (!badge || !btn) return;

    if (isLoggedIn && adminToken) {
        badge.innerHTML = `<i class="fa-solid fa-circle-check" style="color:#52C41A;"></i> Logged in as Admin`;
        btn.innerHTML = `<i class="fa-solid fa-power-off"></i> Logout`;
        btn.style.background = "#EF4444";
        btn.title = "Click to Logout of Admin session";
    } else {
        badge.innerHTML = `<i class="fa-solid fa-user-xmark"></i> Guest / Logged Out`;
        btn.innerHTML = `<i class="fa-solid fa-lock"></i> Click to Login`;
        btn.style.background = "var(--soft-green)";
    }
}

// Auto Login as Admin or Refresh Token
async function ensureAdminToken(forceRefresh = false) {
    if (adminToken && !forceRefresh) return adminToken;

    try {
        const res = await fetch(`${API_BASE}/api/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username: "admin1", password: "admin123" })
        });
        const data = await res.json();
        if (res.ok) {
            adminToken = data.access_token;
            localStorage.setItem("resq_admin_token", adminToken);
            updateAuthBadgeUI(true);
            return adminToken;
        }
    } catch (e) {
        console.warn("Auto admin auth check.");
    }
    return null;
}

// Universal fetch wrapper with auto 401 token refresh & retry
async function fetchWithAdminAuth(url, options = {}) {
    await ensureAdminToken();

    options.headers = options.headers || {};
    if (adminToken) {
        options.headers["Authorization"] = `Bearer ${adminToken}`;
    }

    let res = await fetch(url, options);

    // If token was expired or invalid (401), clear local token, re-authenticate as admin, and retry
    if (res.status === 401) {
        localStorage.removeItem("resq_admin_token");
        adminToken = "";
        await ensureAdminToken(true);

        if (adminToken) {
            options.headers["Authorization"] = `Bearer ${adminToken}`;
        }
        res = await fetch(url, options);
    }

    return res;
}

// Check stored token or auto-login with default credentials
async function initAuthUI() {
    if (!adminToken) {
        await ensureAdminToken(true);
    } else {
        updateAuthBadgeUI(true);
    }
}

// Login Handler
async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById("loginUsername").value;
    const password = document.getElementById("loginPassword").value;
    const errEl = document.getElementById("loginError");

    try {
        const res = await fetch(`${API_BASE}/api/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });
        const data = await res.json();
        if (res.ok) {
            adminToken = data.access_token;
            localStorage.setItem("resq_admin_token", adminToken);
            document.getElementById("loginModal").style.display = "none";
            updateAuthBadgeUI(true);
            logEvent("Auth", `Successfully logged in as Admin (${data.name || username})`);
        } else {
            if (errEl) {
                errEl.innerText = `❌ ${data.detail || "Invalid credentials"}`;
                errEl.style.display = "block";
            } else {
                alert(data.detail || "Login failed");
            }
        }
    } catch (err) {
        if (errEl) {
            errEl.innerText = "❌ Unable to connect to backend server";
            errEl.style.display = "block";
        } else {
            alert("Unable to connect to server");
        }
    }
}

// Delete single SOS incident
async function deleteIncident(id) {
    if (!confirm(`Delete test SOS incident ${id}?`)) return;
    try {
        const res = await fetchWithAdminAuth(`${API_BASE}/api/incidents/${id}`, {
            method: "DELETE"
        });
        if (res.ok) {
            if (selectedIncidentId === id) {
                selectedIncidentId = null;
                selectedIncidentFloor = null;
                selectedIncidentZone = null;
                activeIncidentLabelEl.innerText = "No Active Incident Selected";
                renderMapMarkers();
            }
            logEvent("SOS Delete", `Deleted Incident ${id}`);
            pollBackendState();
        }
    } catch (e) {
        alert("Failed to delete incident");
    }
}

// Clear all test SOS incidents
async function clearAllIncidents() {
    if (!confirm("Are you sure you want to delete ALL test SOS incidents?")) return;
    try {
        const res = await fetchWithAdminAuth(`${API_BASE}/api/incidents`, {
            method: "DELETE"
        });
        if (res.ok) {
            selectedIncidentId = null;
            selectedIncidentFloor = null;
            selectedIncidentZone = null;
            activeIncidentLabelEl.innerText = "No Active Incident Selected";
            renderMapMarkers();
            logEvent("SOS Clear All", "Cleared all test incidents");
            pollBackendState();
        }
    } catch (e) {
        alert("Failed to clear incidents");
    }
}

// Background Polling Loop
async function pollBackendState() {
    try {
        // 1. Poll IoT State (6-Boolean status & position)
        const iotRes = await fetch(`${API_BASE}/api/iot/state`);
        if (iotRes.ok) {
            const iotState = await iotRes.json();
            latestRobotState = iotState;
            updateBooleanUI(iotState);
            updateRobotPositionUI(iotState.estimated_floor, iotState.estimated_zone);
        }

        // 2. Poll Incidents
        const incRes = await fetch(`${API_BASE}/api/incidents`);
        if (incRes.ok) {
            const incidents = await incRes.json();
            renderIncidentsList(incidents);
        }

        document.getElementById("serverStatusBadge").className = "status-badge online";
        document.getElementById("serverStatusBadge").innerHTML = `<span class="pulse-dot green"></span> SYSTEM ONLINE`;

    } catch (err) {
        document.getElementById("serverStatusBadge").className = "status-badge offline";
        document.getElementById("serverStatusBadge").innerHTML = `<span class="pulse-dot red"></span> SERVER OFFLINE`;
    }
}

// Render Incidents List
function renderIncidentsList(incidents) {
    incidentCountEl.innerText = incidents.length;
    if (incidents.length === 0) {
        selectedIncidentId = null;
        selectedIncidentFloor = null;
        selectedIncidentZone = null;
        activeIncidentLabelEl.innerText = "No Active Incident Selected";
        renderMapMarkers();
        incidentsListEl.innerHTML = `
            <div class="empty-state">
                <i class="fa-solid fa-shield-heart"></i>
                <p>No active emergency SOS requests.</p>
            </div>`;
        return;
    }

    let html = "";
    incidents.forEach(inc => {
        const isSelected = (inc.id === selectedIncidentId) ? "selected" : "";
        html += `
            <div class="incident-item ${isSelected}" onclick="selectIncident('${inc.id}', '${inc.floor}', '${inc.zone}')">
                <div class="incident-top">
                    <span class="incident-id">${inc.id}</span>
                    <div style="display:flex; gap:6px; align-items:center;">
                        <span class="urgency-badge urgency-${inc.urgency}">${inc.urgency}</span>
                        <button class="btn-delete-inc" onclick="event.stopPropagation(); deleteIncident('${inc.id}')" title="Delete SOS Incident"><i class="fa-solid fa-trash"></i></button>
                    </div>
                </div>
                <div class="incident-loc"><i class="fa-solid fa-location-dot"></i> ${inc.floor} -> ${inc.zone}</div>
                <div class="incident-reason">Score: <strong>${inc.priority_score.toFixed(1)}</strong> | ${inc.priority_reason || 'SOS Distress'}</div>
            </div>`;
    });
    incidentsListEl.innerHTML = html;

    // Auto select first active incident if none selected yet
    if (!selectedIncidentId && incidents.length > 0) {
        selectIncident(incidents[0].id, incidents[0].floor, incidents[0].zone);
    }
}

// Select Incident
function selectIncident(id, floor, zone) {
    selectedIncidentId = id;
    selectedIncidentFloor = floor;
    selectedIncidentZone = zone;
    displayedMapFloor = floor;

    // Switch Building Map floor tab to victim's floor
    document.querySelectorAll(".tab-btn").forEach(btn => {
        btn.classList.toggle("active", btn.getAttribute("data-floor") === floor);
    });

    // Auto sync Admin Route Editor dropdowns to victim's floor & zone
    editorFloorSelect.value = floor;
    editorZoneSelect.value = zone;
    loadZoneRoute(floor, zone);

    activeIncidentLabelEl.innerText = `Selected: ${id} (${floor} -> ${zone})`;
    renderMapMarkers();
    if (latestRobotState) {
        updateRobotPositionUI(latestRobotState.estimated_floor, latestRobotState.estimated_zone);
    }
    logEvent("SOS Select", `Selected Incident ${id} at ${floor} -> ${zone}`);
}

// Render Building Map Markers
function renderMapMarkers() {
    ["Zone 1", "Zone 2", "Zone 3"].forEach((z, idx) => {
        const zNum = idx + 1;
        const targetMarker = document.getElementById(`zone-${zNum}-target`);
        const zoneCard = document.getElementById(`zone-${zNum}`);
        const tag = document.getElementById(`zone-${zNum}-tag`);

        // Check if victim is on the currently displayed map floor & zone
        const isVictimHere = (selectedIncidentId !== null && displayedMapFloor === selectedIncidentFloor && selectedIncidentZone === z);

        if (isVictimHere) {
            targetMarker.style.display = "block";
            zoneCard.classList.add("has-victim");
            tag.innerText = "VICTIM LOCATED";
            tag.style.background = "#EF4444";
            tag.style.color = "#FFF";
        } else {
            targetMarker.style.display = "none";
            zoneCard.classList.remove("has-victim");
            tag.innerText = "SAFE";
            tag.style.background = "var(--bg-card)";
            tag.style.color = "var(--text-muted)";
        }
    });
}

// Update Robot Estimated Position on Map
function updateRobotPositionUI(rFloor, rZone) {
    document.getElementById("robotPositionVal").innerText = `${rFloor} -> ${rZone}`;

    ["Zone 1", "Zone 2", "Zone 3"].forEach((z, idx) => {
        const zNum = idx + 1;
        const robotMarker = document.getElementById(`zone-${zNum}-robot`);
        const zoneCard = document.getElementById(`zone-${zNum}`);

        if (displayedMapFloor === rFloor && z === rZone) {
            robotMarker.style.display = "block";
            zoneCard.classList.add("has-robot");
        } else {
            robotMarker.style.display = "none";
            zoneCard.classList.remove("has-robot");
        }
    });
}

// Update 6-Boolean Motor Cards UI
function updateBooleanUI(state) {
    const directions = ["NORTH", "SOUTH", "NORTHWEST", "SOUTHEAST", "CW", "CCW"];
    directions.forEach(dir => {
        const key = dir.toLowerCase();
        const card = boolCards[dir];
        if (card) {
            const isActive = state[key];
            card.classList.toggle("active", isActive);
            const stateSpan = card.querySelector(".bool-state");
            if (stateSpan) {
                stateSpan.innerText = isActive ? "ON" : "OFF";
            }
        }
    });

    document.getElementById("robotStatusPill").innerText = state.active_direction !== "STOP" ? `MOVING (${state.active_direction})` : "IDLE";
}

// Make 6-Boolean Direction Cards Interactive (Click to manually test motors)
function initInteractiveBooleanCards() {
    const directions = ["NORTH", "SOUTH", "NORTHWEST", "SOUTHEAST", "CW", "CCW"];
    directions.forEach(dir => {
        const card = boolCards[dir];
        if (card) {
            card.style.cursor = "pointer";
            card.title = `Click to test ${dir} motor command`;
            card.addEventListener("click", async () => {
                const isActive = card.classList.contains("active");
                const targetDir = isActive ? "STOP" : dir;
                try {
                    const res = await fetch(`${API_BASE}/api/iot/set/${targetDir}`, { method: "POST" });
                    if (res.ok) {
                        const data = await res.json();
                        updateBooleanUI(data.iot_state);
                        logEvent("Manual Control", `Set motor state to ${targetDir}`);
                    }
                } catch (e) {
                    console.error("Manual direction toggle error:", e);
                }
            });
        }
    });
}

// Route Editor: Load steps
async function loadZoneRoute(floor, zone) {
    try {
        const res = await fetch(`${API_BASE}/api/routes/${encodeURIComponent(floor)}/${encodeURIComponent(zone)}`);
        if (res.ok) {
            const route = await res.json();
            currentRouteSteps = route.steps || [];
            renderRouteEditorSteps();
        }
    } catch (err) {
        console.error("Error loading route:", err);
    }
}

// Render Route Editor rows
function renderRouteEditorSteps() {
    if (currentRouteSteps.length === 0) {
        routeStepsListEl.innerHTML = `<div class="step-row"><span>1</span><span>STOP</span><span>0</span><span>-</span></div>`;
        return;
    }

    let html = "";
    currentRouteSteps.forEach((s, idx) => {
        html += `
            <div class="step-row">
                <span>Step ${idx + 1}</span>
                <span>
                    <select class="form-select step-dir" data-idx="${idx}">
                        <option value="NORTH" ${s.direction === "NORTH" ? "selected" : ""}>NORTH</option>
                        <option value="SOUTH" ${s.direction === "SOUTH" ? "selected" : ""}>SOUTH</option>
                        <option value="NORTHWEST" ${s.direction === "NORTHWEST" ? "selected" : ""}>NORTHWEST</option>
                        <option value="SOUTHEAST" ${s.direction === "SOUTHEAST" ? "selected" : ""}>SOUTHEAST</option>
                        <option value="CW" ${s.direction === "CW" ? "selected" : ""}>CW (Rotate Clockwise)</option>
                        <option value="CCW" ${s.direction === "CCW" ? "selected" : ""}>CCW (Rotate Counter-CW)</option>
                        <option value="STOP" ${s.direction === "STOP" ? "selected" : ""}>STOP</option>
                    </select>
                </span>
                <span>
                    <input type="number" class="form-control step-dur" data-idx="${idx}" value="${s.duration_sec}" min="0" step="1">
                </span>
                <span>
                    <button class="btn-sm" style="background:#EF4444;" onclick="removeStepRow(${idx})"><i class="fa-solid fa-trash"></i></button>
                </span>
            </div>`;
    });
    routeStepsListEl.innerHTML = html;

    // Attach listeners
    document.querySelectorAll(".step-dir").forEach(el => {
        el.addEventListener("change", (e) => {
            const idx = parseInt(e.target.getAttribute("data-idx"));
            currentRouteSteps[idx].direction = e.target.value;
        });
    });
    document.querySelectorAll(".step-dur").forEach(el => {
        el.addEventListener("change", (e) => {
            const idx = parseInt(e.target.getAttribute("data-idx"));
            currentRouteSteps[idx].duration_sec = parseFloat(e.target.value);
        });
    });
}

function addStepRow() {
    currentRouteSteps.push({ sequence: currentRouteSteps.length + 1, direction: "NORTH", duration_sec: 10 });
    renderRouteEditorSteps();
}

function removeStepRow(idx) {
    currentRouteSteps.splice(idx, 1);
    renderRouteEditorSteps();
}

// Save Route
async function saveZoneRoute() {
    if (!adminToken) {
        alert("Please login as Admin first!");
        document.getElementById("loginModal").style.display = "flex";
        return;
    }

    const floor = editorFloorSelect.value;
    const zone = editorZoneSelect.value;
    const payload = {
        floor: floor,
        zone: zone,
        name: `${floor} ${zone} Custom Route`,
        steps: currentRouteSteps
    };

    try {
        const res = await fetchWithAdminAuth(`${API_BASE}/api/routes/${encodeURIComponent(floor)}/${encodeURIComponent(zone)}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        if (res.ok) {
            alert(`Route for ${floor} -> ${zone} saved successfully!`);
            logEvent("Route Editor", `Saved updated route for ${floor} -> ${zone}`);
        } else {
            alert("Failed to save route. Check admin rights.");
        }
    } catch (err) {
        alert("Error saving route");
    }
}

// Unity 3D & Digital Software Simulator (Does NOT move physical ESP-12E robot)
async function runSoftwareSimulation() {
    if (!selectedIncidentId) {
        alert("Please click and select an active SOS Incident from the left panel first!");
        return;
    }

    const simBar = document.getElementById("simPreviewBar");
    const progressFill = document.getElementById("simProgressFill");
    const stepText = document.getElementById("simStepText");

    if (currentRouteSteps.length > 0) {
        simBar.style.display = "block";
        let stepIdx = 0;

        async function stepSim() {
            if (stepIdx >= currentRouteSteps.length) {
                stepText.innerText = "Unity 3D Simulation Completed!";
                progressFill.style.width = "100%";
                logEvent("Simulation", "🎮 Unity 3D & Digital Simulation finished.");
                // Reset simulation state to STOP
                fetch(`${API_BASE}/api/simulation/set/STOP`, { method: "POST" }).catch(() => {});
                setTimeout(() => { simBar.style.display = "none"; }, 3000);
                return;
            }

            const step = currentRouteSteps[stepIdx];
            stepText.innerText = `Simulating Step ${stepIdx + 1}/${currentRouteSteps.length}: ${step.direction} (${step.duration_sec}s)`;
            progressFill.style.width = `${((stepIdx + 1) / currentRouteSteps.length) * 100}%`;

            // Send simulation 6-Boolean state update for Unity 3D simulator
            try {
                await fetch(`${API_BASE}/api/simulation/set/${step.direction}`, { method: "POST" });
            } catch (e) {
                console.warn("Simulation endpoint broadcast note.");
            }

            stepIdx++;
            setTimeout(stepSim, step.duration_sec * 1000);
        }

        stepSim();
    } else {
        alert("No route steps loaded to simulate. Please save or select a route first.");
    }
}

// Dispatch Real Robot
async function dispatchRealRobot() {
    if (!selectedIncidentId) {
        alert("Please select an SOS incident from the left panel first!");
        return;
    }

    try {
        const res = await fetchWithAdminAuth(`${API_BASE}/api/missions`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ incident_id: selectedIncidentId, robot_id: "R1" })
        });
        const data = await res.json();
        if (res.ok) {
            activeMissionId = data.id;
            alert(`✅ Mission ${data.id} dispatched to Robot R1!`);
            logEvent("Dispatch", `Dispatched Mission ${data.id} for incident ${selectedIncidentId}`);
        } else {
            // Give admin a helpful message — most common failure is a missing route
            const errMsg = data.detail || "Dispatch failed";
            const hint = errMsg.includes("route") || errMsg.includes("500") || errMsg.includes("missing")
                ? `\n\n⚠️ Hint: Make sure you have SAVED a route for the incident's Floor/Zone (${selectedFloor} → ${selectedZone}) in the Route Editor before dispatching.`
                : "";
            alert(`❌ ${errMsg}${hint}`);
            logEvent("Dispatch ERROR", `${errMsg} — Check route exists for ${selectedFloor} → ${selectedZone}`);
        }
    } catch (err) {
        alert("Unable to connect to backend");
    }
}

// Pause Mission
async function pauseMission() {
    try {
        const url = activeMissionId ? `${API_BASE}/api/missions/${activeMissionId}/pause` : `${API_BASE}/api/missions/pause`;
        const res = await fetchWithAdminAuth(url, { method: "POST" });
        if (res.ok) {
            logEvent("Mission Control", "⏸️ Mission PAUSED — All motor movement halted.");
            pollBackendState();
        } else {
            alert("No active mission running to pause.");
        }
    } catch (e) {
        console.error("Pause error:", e);
    }
}

// Resume Mission
async function resumeMission() {
    try {
        const url = activeMissionId ? `${API_BASE}/api/missions/${activeMissionId}/resume` : `${API_BASE}/api/missions/resume`;
        const res = await fetchWithAdminAuth(url, { method: "POST" });
        if (res.ok) {
            const data = await res.json();
            if (data.mission_id) activeMissionId = data.mission_id;
            logEvent("Mission Control", "▶️ Mission RESUMED — Continuing motor route.");
            pollBackendState();
        } else {
            alert("No paused mission found to resume.");
        }
    } catch (e) {
        console.error("Resume error:", e);
    }
}

// Universal Emergency STOP
async function triggerEmergencyStop() {
    try {
        const res = await fetchWithAdminAuth(`${API_BASE}/api/robots/R1/stop`, { method: "POST" });
        if (res.ok) {
            activeMissionId = null;
            logEvent("EMERGENCY", "🚨 UNIVERSAL EMERGENCY STOP EXECUTED! All 6 motor booleans locked OFF permanently.");
            pollBackendState();
        }
    } catch (err) {
        alert("Emergency stop signal failed");
    }
}

// Logging Utility
function logEvent(tag, msg) {
    const time = new Date().toLocaleTimeString();
    const line = document.createElement("div");
    line.className = "log-line";
    line.innerHTML = `[${time}] <strong>[${tag}]</strong> ${msg}`;
    logEntriesEl.prepend(line);
}
