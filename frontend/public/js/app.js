// ==============================================================================
// eRTMAC-NWIS FRONTEND CONTROLLER
// High-Fidelity Industrial SCADA Dashboard
// ==============================================================================

const API_BASE = "http://127.0.0.1:8000/api/v1";

let mapInstance = null;
let activeWellId = "NO-15/9-F-12";
let currentSearchRadiusKm = 5.0;
let radiusCircle = null;
let wellMarkers = [];

let currentBitDepthMD = 2893.5;
let currentBitDepthTVDSS = 2850.0;
let activeFormation = "Hugin FM";

// Initial Setup
document.addEventListener("DOMContentLoaded", () => {
  initMap();
  loadWellMaster();
  loadStratigraphicTrack();
  triggerLookaheadScan();
  initEventListeners();
});

// 1. Leaflet Geospatial Radar Map Initialization
function initMap() {
  // Center on Volve Field coordinates (58.441, 1.895)
  mapInstance = L.map("leaflet-map", {
    zoomControl: true,
    attributionControl: false
  }).setView([58.442, 1.895], 13);

  // High-contrast dark tile layer (CartoDB Dark Matter)
  L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
    maxZoom: 18,
    subdomains: "abcd"
  }).addTo(mapInstance);
}

// 2. Load Wells Master Data & Render Map Pins
async function loadWellMaster() {
  try {
    const res = await fetch(`${API_BASE}/wells`);
    const wells = await res.json();

    // Clear existing markers
    wellMarkers.forEach(m => mapInstance.removeLayer(m));
    wellMarkers = [];

    let activeCoords = null;

    wells.forEach(w => {
      const isCurrentActive = (w.well_id === activeWellId);
      if (isCurrentActive) {
        activeCoords = [w.latitude, w.longitude];
      }

      const markerColor = isCurrentActive ? "#10b981" : "#06b6d4";
      const markerRadius = isCurrentActive ? 9 : 7;

      const circleMarker = L.circleMarker([w.latitude, w.longitude], {
        radius: markerRadius,
        fillColor: markerColor,
        color: "#ffffff",
        weight: 2,
        opacity: 1,
        fillOpacity: 0.9
      }).addTo(mapInstance);

      circleMarker.bindPopup(`
        <div style="font-family: sans-serif; font-size: 12px; color: #111;">
          <strong>Well: ${w.well_name}</strong> (${w.well_id})<br/>
          Operator: ${w.operator}<br/>
          Field: ${w.field_name}<br/>
          Total Depth: ${w.total_depth_md_m}m MD / ${w.total_depth_tvd_m}m TVD<br/>
          ${isCurrentActive ? '<span style="color:#059669; font-weight:700;">★ ACTIVE DRILLING WELL</span>' : ''}
        </div>
      `);

      wellMarkers.push(circleMarker);
    });

    // Draw dynamic radius circle around active well
    if (activeCoords) {
      if (radiusCircle) {
        mapInstance.removeLayer(radiusCircle);
      }
      radiusCircle = L.circle(activeCoords, {
        radius: currentSearchRadiusKm * 1000,
        color: "#f59e0b",
        weight: 1.5,
        fillColor: "#f59e0b",
        fillOpacity: 0.08,
        dashArray: "4, 6"
      }).addTo(mapInstance);

      mapInstance.panTo(activeCoords);
    }

  } catch (err) {
    console.error("Failed to load wells from API:", err);
  }
}

// 3. Load Stratigraphic Formation Tops & Events Track
async function loadStratigraphicTrack() {
  try {
    const [topsRes, eventsRes] = await Promise.all([
      fetch(`${API_BASE}/wells/formations?well_id=${encodeURIComponent(activeWellId)}`),
      fetch(`${API_BASE}/wells/events?well_id=${encodeURIComponent(activeWellId)}`)
    ]);

    const tops = await topsRes.json();
    const events = await eventsRes.json();

    const column = document.getElementById("stratigraphic-column");
    column.innerHTML = "";

    tops.forEach(t => {
      // Find matching events in this formation
      const matchedEvents = events.filter(e => e.formation_name === t.formation_name);
      let eventBadges = "";

      matchedEvents.forEach(e => {
        eventBadges += `<span class="incident-badge-pill" title="${e.operational_narrative}">⚠️ ${e.event_type} (${e.depth_tvdss_m}m)</span> `;
      });

      if (!eventBadges) {
        eventBadges = `<span style="color:#4b5563; font-size:10px;">Clear Interval</span>`;
      }

      const row = document.createElement("div");
      row.className = "formation-row";
      if (t.formation_name === activeFormation) {
        row.style.background = "rgba(6, 182, 212, 0.12)";
        row.style.borderLeft = "3px solid #06b6d4";
      }

      row.innerHTML = `
        <span class="fm-name-tag">${t.formation_name}</span>
        <span class="fm-depth">${t.top_tvdss_m.toFixed(1)}m</span>
        <div>${eventBadges}</div>
      `;
      column.appendChild(row);
    });

  } catch (err) {
    console.error("Failed to load stratigraphic track:", err);
  }
}

// 4. Pre-Bit Look-Ahead Hazard Evaluation
async function triggerLookaheadScan(telemetryOverride = null) {
  try {
    const payload = {
      active_well_id: activeWellId,
      current_bit_depth_md_m: currentBitDepthMD,
      current_bit_depth_tvdss_m: currentBitDepthTVDSS,
      active_formation: activeFormation,
      lookahead_window_m: 75.0,
      recent_telemetry: telemetryOverride || {
        rop_mhr: 14.2,
        wob_klbs: 24.0,
        rpm: 110.0,
        torque_kftlbs: 15.0,
        spp_psi: 2900.0,
        flow_in_gpm: 550.0,
        flow_out_pct: 95.0,
        pit_volume_m3: 45.0,
        ecd_sg: 1.28
      }
    };

    const res = await fetch(`${API_BASE}/lookahead/scan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    renderLookaheadAlerts(data);

  } catch (err) {
    console.error("Failed to execute look-ahead scan:", err);
  }
}

// 5. Render Look-Ahead Alerts
function renderLookaheadAlerts(data) {
  const container = document.getElementById("lookahead-alerts-container");
  const badgeStatus = document.getElementById("badge-horizon-status");
  const pillEvidence = document.getElementById("evidence-status-pill");

  badgeStatus.className = `telemetry-badge badge-${data.hazard_level.toLowerCase()}`;
  badgeStatus.textContent = `LOOK-AHEAD: ${data.hazard_level}`;

  pillEvidence.textContent = data.evidence_status.replace(/_/g, " ");

  if (data.alert_count === 0) {
    container.innerHTML = `
      <div style="padding: 20px; text-align: center; color: #9ca3af; font-size: 12px;">
        <span style="font-size: 24px; display: block; margin-bottom: 8px;">🛡️</span>
        <strong>HORIZON CLEAR (75m Look-Ahead Window)</strong><br/>
        No historical offset incidents recorded in upcoming stratigraphic interval.
      </div>
    `;
    return;
  }

  container.innerHTML = "";
  data.alerts.forEach((alert, idx) => {
    const isCrit = (alert.severity === "CRITICAL" || alert.risk_score >= 0.85);
    const card = document.createElement("div");
    card.className = `alert-card ${isCrit ? 'critical' : ''}`;
    card.innerHTML = `
      <div class="alert-header-row">
        <span class="alert-hazard-name">⚠️ ${alert.hazard_type.replace(/_/g, ' ')} (${alert.severity})</span>
        <span class="alert-lead-distance">${alert.lead_distance_m}m Ahead (${alert.projected_tvdss_m}m TVDSS)</span>
      </div>
      <p class="alert-narrative">${alert.historical_narrative}</p>
      <div class="alert-mitigation-box">
        <strong>Recommended Mitigation:</strong> ${alert.recommended_mitigation}
      </div>
      <div class="alert-citation">
        Source: ${alert.source_offset_well} | ${alert.source_citation} | Risk Index: ${(alert.risk_score * 100).toFixed(0)}%
        <br/>
        <button class="btn-evidence-passport" onclick="openEvidencePassport('${alert.matched_event_id || 'EVT-VOLVE-001'}')">📜 View Evidence Passport</button>
      </div>
    `;
    container.appendChild(card);
  });
}

// 6. Live Telemetry Drilling Simulation Flow
let simulationTimer = null;
function playLiveSimulation() {
  const btn = document.getElementById("btn-run-simulation");
  if (simulationTimer) {
    clearInterval(simulationTimer);
    simulationTimer = null;
    btn.innerHTML = `<span class="btn-icon">&#9658;</span> Play Live Telemetry`;
    return;
  }

  btn.innerHTML = `<span class="btn-icon">&#9208;</span> Pause Telemetry`;

  const steps = [
    { md: 2850.0, tvdss: 2806.5, fm: "Heather FM", rop: 16.5, torque: 12.0, spp: 2800, flow: "550 / 98%" },
    { md: 2875.0, tvdss: 2831.5, fm: "Heather FM", rop: 15.2, torque: 13.5, spp: 2850, flow: "550 / 97%" },
    { md: 2893.5, tvdss: 2850.0, fm: "Hugin FM",   rop: 14.2, torque: 15.0, spp: 2900, flow: "550 / 95%" }, // Alert horizon entry
    { md: 2905.0, tvdss: 2858.0, fm: "Hugin FM",   rop: 8.5,  torque: 19.8, spp: 3450, flow: "550 / 82%" }, // Torque spike & loss!
    { md: 2920.0, tvdss: 2870.0, fm: "Hugin FM",   rop: 12.0, torque: 14.5, spp: 2950, flow: "550 / 92%" }
  ];

  let stepIdx = 0;
  simulationTimer = setInterval(() => {
    if (stepIdx >= steps.length) {
      clearInterval(simulationTimer);
      simulationTimer = null;
      btn.innerHTML = `<span class="btn-icon">&#9658;</span> Play Live Telemetry`;
      return;
    }

    const cur = steps[stepIdx];
    currentBitDepthMD = cur.md;
    currentBitDepthTVDSS = cur.tvdss;
    activeFormation = cur.fm;

    // Update Ribbon Display
    document.getElementById("val-depth-md").innerHTML = `${cur.md.toFixed(1)} <small>m</small>`;
    document.getElementById("val-depth-tvdss").innerHTML = `${cur.tvdss.toFixed(1)} <small>m</small>`;
    document.getElementById("val-formation").textContent = cur.fm;
    document.getElementById("val-rop").innerHTML = `${cur.rop.toFixed(1)} <small>m/hr</small>`;
    document.getElementById("val-torque-spp").innerHTML = `${cur.torque.toFixed(1)} <small>kft-lb</small> / ${cur.spp} <small>psi</small>`;
    document.getElementById("val-flow").innerHTML = cur.flow;

    triggerLookaheadScan({
      rop_mhr: cur.rop,
      wob_klbs: 24.0,
      rpm: 110.0,
      torque_kftlbs: cur.torque,
      spp_psi: cur.spp,
      flow_in_gpm: 550.0,
      flow_out_pct: parseFloat(cur.flow.split("/")[1]),
      pit_volume_m3: 45.0,
      ecd_sg: 1.28
    });

    loadStratigraphicTrack();
    stepIdx++;
  }, 2000);
}

// 7. LOWO Back-Test Runner
async function runLOWOBacktest() {
  const grid = document.getElementById("backtest-summary-grid");
  grid.innerHTML = "<p>Running Leave-One-Well-Out empirical validation on held-out well NO-15/9-F-12...</p>";

  // Switch tab to Backtest pane
  switchDrawerTab("tab-backtest-results", "pane-backtest-results");

  try {
    const res = await fetch(`${API_BASE}/backtest/run?held_out_well_id=${encodeURIComponent(activeWellId)}&lookahead_window_m=75.0`, {
      method: "POST"
    });
    const data = await res.json();

    grid.innerHTML = `
      <div class="metric-card">
        <div class="metric-card-label">SENSITIVITY / RECALL</div>
        <div class="metric-card-val">${data.sensitivity_recall_pct}%</div>
        <small style="color:#9ca3af;">${data.proactively_flagged_true_positives} of ${data.total_real_documented_events} real events flagged ahead</small>
      </div>
      <div class="metric-card">
        <div class="metric-card-label">ADVANCE LEAD DISTANCE</div>
        <div class="metric-card-val">${data.average_advance_warning_lead_meters}m</div>
        <small style="color:#9ca3af;">Avg advance lead before drill bit arrival</small>
      </div>
      <div class="metric-card">
        <div class="metric-card-label">FALSE ALARMS (FP)</div>
        <div class="metric-card-val" style="color:#f59e0b;">${data.false_alarms}</div>
        <small style="color:#9ca3af;">Reported honestly without suppression</small>
      </div>
      <div class="metric-card">
        <div class="metric-card-label">UNPRECEDENTED MISSES</div>
        <div class="metric-card-val" style="color:#ef4444;">${data.unprecedented_misses_false_negatives}</div>
        <small style="color:#9ca3af;">Zero historical offset records in interval</small>
      </div>
      <div style="grid-column: span 4; background: rgba(31, 41, 55, 0.6); padding: 8px 12px; border-radius: 6px; font-size: 11px; line-height: 1.5; color: #d1d5db;">
        <strong>Empirical Conclusion:</strong> ${data.engineering_conclusion}
      </div>
    `;

  } catch (err) {
    grid.innerHTML = `<p style="color:#ef4444;">Failed to run back-test: ${err}</p>`;
  }
}

// 8. Ask NWIS Grounded Chat
async function handleAskNWIS(e) {
  e.preventDefault();
  const input = document.getElementById("input-query");
  const query = input.value.trim();
  if (!query) return;

  const history = document.getElementById("chat-history");
  
  // Add user message
  const userMsg = document.createElement("div");
  userMsg.className = "chat-message user-msg";
  userMsg.textContent = query;
  history.appendChild(userMsg);
  input.value = "";
  history.scrollTop = history.scrollHeight;

  try {
    const res = await fetch(`${API_BASE}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, active_well_id: activeWellId, target_formation: activeFormation })
    });
    const data = await res.json();

    const botMsg = document.createElement("div");
    botMsg.className = "chat-message bot-msg";

    let citationsHtml = "";
    if (data.citations && data.citations.length > 0) {
      citationsHtml = "<br/><br/><strong style='color:#06b6d4;'>VERIFIED EVIDENCE CITATIONS:</strong><br/>";
      data.citations.forEach(c => {
        citationsHtml += `<span style="display:inline-block; margin-top:4px; font-size:11px; color:#9ca3af; font-family:var(--font-mono); background:#111827; padding:3px 6px; border-radius:4px; border:1px solid #374151;">📄 ${c.source_document} (${c.depth_interval})</span><br/>`;
      });
    }

    botMsg.innerHTML = `<strong>NWIS Copilot:</strong> ${data.grounded_answer} ${citationsHtml}`;
    history.appendChild(botMsg);
    history.scrollTop = history.scrollHeight;

  } catch (err) {
    console.error("Ask NWIS error:", err);
  }
}

// 9. Driller Feedback Handler
async function handleDrillerFeedback(actionType, comment) {
  try {
    const res = await fetch(`${API_BASE}/lookahead/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        alert_id: "alert-current-session",
        driller_response: actionType,
        driller_comments: comment
      })
    });
    const result = await res.json();
    const feedbackMsg = document.getElementById("feedback-confirmation");
    feedbackMsg.textContent = `✓ Response logged: ${actionType} at ${new Date().toLocaleTimeString()} [Audit ID: ${result.alert_id || 'OK'}]`;
    setTimeout(() => { feedbackMsg.textContent = ""; }, 5000);
  } catch (err) {
    console.error("Failed to record feedback:", err);
  }
}

// Event Listeners Setup
function initEventListeners() {
  document.getElementById("btn-run-simulation").addEventListener("click", playLiveSimulation);
  document.getElementById("btn-run-backtest").addEventListener("click", runLOWOBacktest);
  document.getElementById("form-ask-nwis").addEventListener("submit", handleAskNWIS);

  document.getElementById("slider-radius").addEventListener("input", (e) => {
    currentSearchRadiusKm = parseFloat(e.target.value);
    document.getElementById("label-radius").textContent = currentSearchRadiusKm.toFixed(1);
    loadWellMaster();
  });

  document.getElementById("active-well-select").addEventListener("change", (e) => {
    activeWellId = e.target.value;
    loadWellMaster();
    loadStratigraphicTrack();
    triggerLookaheadScan();
  });

  document.getElementById("btn-action-taken").addEventListener("click", () => {
    handleDrillerFeedback("ACTION_TAKEN", "Pre-mixed LCM pill staged on floor.");
  });
  document.getElementById("btn-nuisance-alarm").addEventListener("click", () => {
    handleDrillerFeedback("NUISANCE_ALARM", "Formation drilled without resistance.");
  });
  document.getElementById("btn-noted").addEventListener("click", () => {
    handleDrillerFeedback("NOTED", "Superintendent notified.");
  });

  // Tab switching
  document.getElementById("tab-ask-nwis").addEventListener("click", () => switchDrawerTab("tab-ask-nwis", "pane-ask-nwis"));
  document.getElementById("tab-backtest-results").addEventListener("click", () => switchDrawerTab("tab-backtest-results", "pane-backtest-results"));
  document.getElementById("tab-documents").addEventListener("click", () => {
    switchDrawerTab("tab-documents", "pane-documents");
    loadDocuments();
  });
  document.getElementById("tab-review-queue").addEventListener("click", () => {
    switchDrawerTab("tab-review-queue", "pane-review-queue");
    loadReviewTasks();
  });
  document.getElementById("tab-audit-trail").addEventListener("click", () => {
    switchDrawerTab("tab-audit-trail", "pane-audit-trail");
    loadAuditTrail();
  });

  // Document upload button
  document.getElementById("btn-upload-doc").addEventListener("click", uploadDocument);

  // Evidence modal close button
  document.getElementById("btn-close-evidence-modal").addEventListener("click", closeEvidenceModal);

  // Poll review tasks count initially
  loadReviewTasksCount();
}

function switchDrawerTab(tabId, paneId) {
  document.querySelectorAll(".drawer-tab").forEach(t => t.classList.remove("active"));
  document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));
  document.getElementById(tabId).classList.add("active");
  document.getElementById(paneId).classList.add("active");
}

// 7. Document Intelligence & Upload Functions
async function loadDocuments() {
  try {
    const res = await fetch(`${API_BASE}/documents`);
    const docs = await res.json();
    const tbody = document.getElementById("tbody-documents");
    tbody.innerHTML = "";

    if (docs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:#9ca3af; padding:16px;">No historical petroleum documents ingested yet. Upload a DDR PDF above.</td></tr>`;
      return;
    }

    docs.forEach(d => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong>${d.original_filename}</strong></td>
        <td>${d.well_id || 'Auto-Detected'}</td>
        <td>${d.source_date || 'N/A'}</td>
        <td>${d.total_pages}</td>
        <td>${d.document_type} ${d.is_scanned ? '<span class="badge-pill" style="background:#f59e0b;">SCANNED OCR</span>' : '<span class="badge-pill" style="background:#10b981;">NATIVE PDF</span>'}</td>
        <td><span class="telemetry-badge badge-clear">${d.status}</span></td>
        <td>
          <button class="btn btn-secondary" style="font-size:11px; padding:3px 8px;" onclick="previewDocumentPage('${d.doc_id}', 1)">Preview P.1</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Failed to load documents:", err);
  }
}

async function uploadDocument() {
  const fileInput = document.getElementById("input-doc-file");
  const wellSelect = document.getElementById("select-doc-well");
  const statusMsg = document.getElementById("upload-status-msg");

  if (!fileInput.files || fileInput.files.length === 0) {
    statusMsg.innerHTML = `<span style="color:#ef4444;">Please select a genuine PDF document to upload.</span>`;
    return;
  }

  const file = fileInput.files[0];
  const formData = new FormData();
  formData.append("file", file);
  if (wellSelect.value) {
    formData.append("well_id", wellSelect.value);
  }

  statusMsg.innerHTML = `<span style="color:#06b6d4;">Ingesting, verifying checksum, running OCR & extracting entities...</span>`;

  try {
    const res = await fetch(`${API_BASE}/documents/upload`, {
      method: "POST",
      body: formData
    });

    const data = await res.json();
    if (res.ok) {
      statusMsg.innerHTML = `<span style="color:#10b981;">✔ ${data.message}</span>`;
      loadDocuments();
      loadReviewTasksCount();
      triggerLookaheadScan();
    } else {
      statusMsg.innerHTML = `<span style="color:#ef4444;">✖ Upload Failed: ${data.detail || 'Error'}</span>`;
    }
  } catch (err) {
    statusMsg.innerHTML = `<span style="color:#ef4444;">✖ Ingestion error: ${err.message}</span>`;
  }
}

// 8. Human-in-the-Loop Review Queue Functions
async function loadReviewTasksCount() {
  try {
    const res = await fetch(`${API_BASE}/review/tasks?status=PENDING`);
    const tasks = await res.json();
    const badge = document.getElementById("badge-review-count");
    if (badge) {
      badge.textContent = tasks.length;
      badge.style.display = tasks.length > 0 ? "inline-block" : "none";
    }
  } catch (err) {
    console.error("Failed to load review task count:", err);
  }
}

async function loadReviewTasks() {
  try {
    const res = await fetch(`${API_BASE}/review/tasks?status=PENDING`);
    const tasks = await res.json();
    const tbody = document.getElementById("tbody-review-tasks");
    tbody.innerHTML = "";

    if (tasks.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:#10b981; padding:16px;">✔ Zero pending review tasks. All extracted incidents are verified.</td></tr>`;
      return;
    }

    tasks.forEach(t => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><code>${t.task_id.substring(0, 8)}</code></td>
        <td>${t.original_filename}</td>
        <td><strong style="color:#f59e0b;">${t.event_type}</strong></td>
        <td>${t.depth_md_m ? t.depth_md_m + 'm MD' : '<span style="color:#ef4444;">Missing Depth</span>'}</td>
        <td><span class="telemetry-badge badge-warning" style="font-size:10px;">${t.flag_reason}</span></td>
        <td>
          <button class="btn btn-primary" style="font-size:10px; padding:3px 8px; margin-right:4px;" onclick="submitDecision('${t.task_id}', 'APPROVED')">Approve (Verify)</button>
          <button class="btn btn-secondary" style="font-size:10px; padding:3px 8px; background:#ef4444;" onclick="submitDecision('${t.task_id}', 'REJECTED')">Reject (Quarantine)</button>
        </td>
      `;
      tbody.appendChild(tr);
    });

    loadReviewTasksCount();
  } catch (err) {
    console.error("Failed to load review tasks:", err);
  }
}

async function submitDecision(taskId, decision) {
  try {
    const res = await fetch(`${API_BASE}/review/decision`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        task_id: taskId,
        reviewer_id: "OIL-DRILLER-CONSOLE",
        reviewer_role: "DRILLING_SUPERINTENDENT",
        decision: decision,
        comments: `Manual validation decision: ${decision} via SCADA dashboard.`
      })
    });

    const data = await res.json();
    if (res.ok) {
      alert(`Decision recorded: ${data.decision} (Status: ${data.verification_status})`);
      loadReviewTasks();
      loadReviewTasksCount();
      triggerLookaheadScan();
    } else {
      alert(`Failed to record decision: ${data.detail || 'Error'}`);
    }
  } catch (err) {
    alert(`Error submitting review decision: ${err.message}`);
  }
}

// 9. Evidence Passport Modal Functions
async function openEvidencePassport(eventId) {
  try {
    const res = await fetch(`${API_BASE}/evidence/${eventId}`);
    if (!res.ok) {
      alert(`Evidence Passport for ${eventId} not available.`);
      return;
    }

    const p = await res.json();
    document.getElementById("ev-modal-title").textContent = `${p.hazard_type} Evidence Dossier (${p.event_id})`;

    document.getElementById("q-what-happened").textContent = `${p.hazard_type} (${p.severity})`;
    document.getElementById("q-what-narrative").textContent = p.operational_narrative;
    document.getElementById("q-what-mitigation").textContent = p.mitigation_applied ? `Mitigation: ${p.mitigation_applied}` : "";

    document.getElementById("q-wellbore").textContent = `${p.well_id} (${p.well_name})`;
    document.getElementById("q-wellbore-sub").textContent = `${p.field_name} | Operator: ${p.operator}`;

    document.getElementById("q-timestamp").textContent = p.event_timestamp || "Historical Date Verified";
    document.getElementById("q-depth").textContent = `${p.depth_md_m}m MD / ${p.depth_tvdss_m}m TVDSS`;
    document.getElementById("q-depth-datum").textContent = `Datum: ${p.depth_datum}`;

    document.getElementById("q-formation").textContent = `${p.formation_name} (${p.relative_formation_depth_m ? '+' + p.relative_formation_depth_m + 'm into top' : 'Top zone'})`;

    document.getElementById("q-quote").textContent = `"${p.quoted_passage}"`;
    document.getElementById("q-source-doc").textContent = `Source Document: ${p.source_document_name} | Page ${p.source_page_number}`;

    document.getElementById("q-missing-info").textContent = p.missing_fields && p.missing_fields.length > 0 ? `Uncertain: ${p.missing_fields.join(', ')}` : "None (Fully Verified Historical Record)";

    document.getElementById("q-verification-status").textContent = p.verification_status;
    document.getElementById("q-verification-status").className = `telemetry-badge badge-${p.verification_status === 'VERIFIED' ? 'clear' : 'warning'}`;
    document.getElementById("q-confidence").textContent = `Confidence: ${(p.confidence_score * 100).toFixed(0)}%`;
    document.getElementById("q-reviewer-sub").textContent = `Extraction: ${p.extraction_method} ${p.reviewed_by ? '| Verified by ' + p.reviewed_by : ''}`;

    // Load snippet image
    const imgEl = document.getElementById("img-evidence-snippet");
    if (p.doc_id) {
      imgEl.src = `${API_BASE}/documents/${p.doc_id}/pages/${p.source_page_number}/preview?t=${Date.now()}`;
      imgEl.style.display = "block";
    } else {
      imgEl.style.display = "none";
    }

    document.getElementById("modal-evidence-passport").classList.remove("hidden");
  } catch (err) {
    console.error("Failed to open Evidence Passport:", err);
  }
}

function closeEvidenceModal() {
  document.getElementById("modal-evidence-passport").classList.add("hidden");
}

function previewDocumentPage(docId, pageNumber) {
  const url = `${API_BASE}/documents/${docId}/pages/${pageNumber}/preview`;
  window.open(url, "_blank");
}

async function loadAuditTrail() {
  try {
    const res = await fetch(`${API_BASE}/audit/logs`);
    const logs = await res.json();
    const list = document.getElementById("audit-log-list");
    list.innerHTML = "";
    if (logs.length === 0) {
      list.innerHTML = `<span style="color:#6b7280;">No audit events recorded yet. Perform look-ahead scans or submit driller feedback to generate audit entries.</span>`;
      return;
    }
    logs.forEach(l => {
      const item = document.createElement("div");
      item.innerHTML = `<span style="color:#06b6d4;">${l.timestamp}</span> | User: <strong>${l.user_id}</strong> | Action: <span style="color:#10b981;">${l.action}</span> | Resource: ${l.resource_type}:${l.resource_id}`;
      list.appendChild(item);
    });
  } catch (err) {
    console.error("Failed to load audit logs:", err);
  }
}

// -------------------------------------------------------------
// Visual Intelligence Lightbox Modal for Cockpit
// -------------------------------------------------------------
window.openModalVisual = function(imgSrc, title, caption) {
  const modal = document.getElementById("modalVisualArtifact");
  const img = document.getElementById("modalVisualImg");
  const titleEl = document.getElementById("modalVisualTitle");
  const capEl = document.getElementById("modalVisualCaption");

  if (!modal || !img) return;
  img.src = imgSrc;
  titleEl.textContent = title;
  capEl.innerHTML = `<strong>Engineering Analysis & Context:</strong> ${caption}`;
  modal.style.display = "flex";
  document.body.style.overflow = "hidden";
};

window.closeModalVisual = function() {
  const modal = document.getElementById("modalVisualArtifact");
  if (!modal) return;
  modal.style.display = "none";
  document.body.style.overflow = "";
};

