/**
 * NWIS GEOCORE — FRONTEND CONTROLLER
 * Connects GeoCore views with backend APIs:
 * - Minimum Curvature Trajectories
 * - Geological Fingerprints
 * - Formation Correlation
 * - Explainable Similarity & "Why This Well, Not That Well"
 * - Subsurface Corridor & Evidence Passport Modals
 * - Specialist Human Review & Cryptographic Audit
 */

let activeWellId = 'NO-15/9-F-12';
let targetFormation = 'Hugin FM';
let geocoreMap = null;
let radiusCircle = null;
let wellMarkers = [];

document.addEventListener('DOMContentLoaded', () => {
  initGeoCore();
});

async function initGeoCore() {
  await loadOverviewData();
  await loadFingerprintData();
  await loadCorrelationData();
  await loadComparisonData();
  await loadCorridorData();
  await loadAuditHistory();
  initMap();
}

// -------------------------------------------------------------
// View Switcher
// -------------------------------------------------------------
function switchView(viewName) {
  document.querySelectorAll('.geocore-tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.geocore-view').forEach(view => view.classList.remove('active'));

  const activeBtn = Array.from(document.querySelectorAll('.geocore-tab-btn')).find(b => 
    b.getAttribute('onclick').includes(viewName)
  );
  if (activeBtn) activeBtn.classList.add('active');

  const targetView = document.getElementById(`view-${viewName}`);
  if (targetView) targetView.classList.add('active');

  if (viewName === 'map' && geocoreMap) {
    setTimeout(() => { geocoreMap.invalidateSize(); }, 200);
  }
}

// -------------------------------------------------------------
// Well & Formation Change Handlers
// -------------------------------------------------------------
async function onWellChange() {
  const sel = document.getElementById('well-selector');
  activeWellId = sel.value;
  document.getElementById('overview-well-name').textContent = activeWellId;
  await runSimilarityScan();
}

async function onTargetFormationChange() {
  const sel = document.getElementById('target-formation-select');
  targetFormation = sel.value;
  await runSimilarityScan();
}

async function runSimilarityScan() {
  await loadOverviewData();
  await loadFingerprintData();
  await loadCorrelationData();
  await loadComparisonData();
  await loadCorridorData();
  if (geocoreMap) updateMapMarkers();
}

// -------------------------------------------------------------
// View A: Overview Data
// -------------------------------------------------------------
async function loadOverviewData() {
  try {
    const res = await fetch('/api/v1/geocore/similarity', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        primary_well_id: activeWellId,
        target_formation_name: targetFormation,
        max_search_radius_km: 10.0
      })
    });
    const data = await res.json();
    if (data.status === 'SUCCESS') {
      renderAnaloguesList(data.ranking.ranked_analogues);
    }

    // Load active well formations
    const wellRes = await fetch(`/api/v1/geocore/wellbores/${activeWellId}`);
    const wellData = await wellRes.json();
    renderFormationsTable(wellData.formations);
    document.getElementById('overview-kb-elevation').textContent = `${wellData.kb_elevation_m} m (Verified RKB)`;
    document.getElementById('overview-survey-count').textContent = `${wellData.survey_stations_count} Definitive Stations`;
    document.getElementById('overview-active-formation').textContent = `${targetFormation}`;
  } catch (err) {
    console.error('Error loading overview:', err);
  }
}

function renderAnaloguesList(analogues) {
  const container = document.getElementById('overview-analogues-list');
  container.innerHTML = '';
  document.getElementById('overview-offset-count').textContent = `${analogues.length} Evaluated`;

  analogues.forEach((a, idx) => {
    const card = document.createElement('div');
    card.className = 'well-item';
    card.style.background = 'rgba(255,255,255,0.02)';
    card.style.border = '1px solid var(--border-subtle)';
    card.style.borderRadius = '8px';
    card.style.padding = '12px 16px';
    card.style.cursor = 'pointer';

    const matchBadge = a.target_formation_matched 
      ? `<span class="tag tag-green">✓ ${targetFormation} Matched</span>`
      : `<span class="tag tag-red">✕ Target Missing</span>`;

    card.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
        <span style="font-weight:700; color:var(--text-main); font-size:0.95rem;">
          #${idx + 1} ${a.offset_well_name}
        </span>
        <span style="font-family:var(--font-mono); font-size:0.85rem; font-weight:800; color:var(--copper-bright);">
          Score: ${(a.composite_similarity_score * 100).toFixed(1)}%
        </span>
      </div>
      <div style="display:flex; gap:8px; align-items:center; margin-bottom:8px;">
        ${matchBadge}
        <span class="tag tag-amber">${a.distance_km} km away</span>
        <span class="tag tag-cyan">${a.events_in_target_formation} Relevant Incidents</span>
      </div>
      <div style="font-size:0.8rem; color:var(--text-muted); line-height:1.4;">
        ${a.engineering_rationale}
      </div>
    `;
    container.appendChild(card);
  });
}

function renderFormationsTable(formations) {
  const container = document.getElementById('overview-formations-table');
  let html = `
    <table class="audit-table">
      <thead>
        <tr>
          <th>Formation</th>
          <th>Lithology</th>
          <th>Top (TVDSS)</th>
          <th>Base (TVDSS)</th>
          <th>Confidence</th>
        </tr>
      </thead>
      <tbody>
  `;
  formations.forEach(f => {
    const isTarget = f.formation_name.toLowerCase() === targetFormation.toLowerCase();
    const highlight = isTarget ? 'style="background:rgba(205,133,63,0.15); font-weight:700;"' : '';
    html += `
      <tr ${highlight}>
        <td style="color:${isTarget ? 'var(--copper-bright)' : 'var(--text-main)'};">${f.formation_name}</td>
        <td>${f.lithology}</td>
        <td style="font-family:var(--font-mono);">${f.top_tvdss_m} m</td>
        <td style="font-family:var(--font-mono);">${f.base_tvdss_m ? f.base_tvdss_m + ' m' : 'Unproven'}</td>
        <td><span class="tag tag-green">${f.confidence}</span></td>
      </tr>
    `;
  });
  html += `</tbody></table>`;
  container.innerHTML = html;
}

// -------------------------------------------------------------
// View B: Interactive Radar Map
// -------------------------------------------------------------
function initMap() {
  if (geocoreMap) return;
  geocoreMap = L.map('geocore-map', {
    zoomControl: true,
    attributionControl: false
  }).setView([58.44123, 1.89531], 13);

  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    maxZoom: 18,
    subdomains: 'abcd'
  }).addTo(geocoreMap);

  radiusCircle = L.circle([58.44123, 1.89531], {
    radius: 5000,
    color: '#CD853F',
    fillColor: '#CD853F',
    fillOpacity: 0.08,
    weight: 1.5,
    dashArray: '4, 4'
  }).addTo(geocoreMap);

  updateMapMarkers();
}

async function updateMapMarkers() {
  if (!geocoreMap) return;
  wellMarkers.forEach(m => geocoreMap.removeLayer(m));
  wellMarkers = [];

  try {
    const res = await fetch('/api/v1/geocore/wellbores');
    const data = await res.json();
    const listWrap = document.getElementById('map-well-list');
    listWrap.innerHTML = '';

    data.wellbores.forEach(w => {
      const isActive = w.well_id === activeWellId;
      const pinColor = isActive ? '#E8A83D' : '#3DB868';
      const pinSize = isActive ? 18 : 14;

      const icon = L.divIcon({
        className: 'custom-pin',
        html: `<div style="background:${pinColor}; width:${pinSize}px; height:${pinSize}px; border-radius:50%; border:2px solid #FFFFFF; box-shadow:0 0 10px ${pinColor};"></div>`,
        iconSize: [pinSize, pinSize],
        iconAnchor: [pinSize / 2, pinSize / 2]
      });

      const marker = L.marker([w.latitude, w.longitude], { icon })
        .addTo(geocoreMap)
        .bindPopup(`
          <strong>${w.well_name} (${w.well_id})</strong><br>
          Operator: ${w.operator}<br>
          KB Elevation: ${w.kb_elevation_m}m<br>
          Historical Events: ${w.historical_events_count}<br>
          Status: ${isActive ? 'ACTIVE RIG DRILLING' : 'HISTORICAL OFFSET'}
        `);

      wellMarkers.push(marker);

      const item = document.createElement('div');
      item.className = 'well-item';
      item.innerHTML = `
        <div style="display:flex; justify-content:space-between; font-weight:700;">
          <span style="color:${isActive ? 'var(--gold-accent)' : 'var(--text-main)'};">${w.well_name}</span>
          <span style="font-size:0.75rem; color:var(--text-muted);">${w.well_type}</span>
        </div>
        <div style="font-size:0.75rem; color:var(--text-muted); font-family:var(--font-mono);">
          TD: ${w.total_depth_md_m}m MD | Events: ${w.historical_events_count}
        </div>
      `;
      item.onclick = () => {
        geocoreMap.setView([w.latitude, w.longitude], 14);
        marker.openPopup();
      };
      listWrap.appendChild(item);
    });
  } catch (err) {
    console.error('Error updating map markers:', err);
  }
}

function updateRadius(val) {
  document.getElementById('radius-val').textContent = `${parseFloat(val).toFixed(1)} km`;
  if (radiusCircle) {
    radiusCircle.setRadius(parseFloat(val) * 1000);
  }
}

// -------------------------------------------------------------
// View C: Formation Correlation Track
// -------------------------------------------------------------
async function loadCorrelationData() {
  const offsetId = document.getElementById('correlation-offset-select').value;
  try {
    const res = await fetch('/api/v1/geocore/correlations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        primary_well_id: activeWellId,
        offset_well_id: offsetId,
        formation_name: targetFormation,
        primary_depth_tvdss_m: 2855.0
      })
    });
    const data = await res.json();
    const corr = data.correlation;

    const box = document.getElementById('correlation-result-box');
    if (corr.is_abstaining) {
      box.innerHTML = `
        <div style="color:var(--red-hazard); font-weight:700;">⚠ CORRELATION ABSTAINED: ${corr.correlation_status}</div>
        <div style="font-size:0.85rem; color:var(--text-muted); margin-top:6px;">${corr.abstention_reason}</div>
      `;
      document.getElementById('correlation-events-table').innerHTML = '<div style="color:var(--text-muted); font-size:0.85rem;">No historical events available for uncorrelated formation.</div>';
      return;
    }

    box.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <span style="font-weight:700; color:var(--text-main); font-size:1.05rem;">
          Geological Alignment: ${corr.formation_name} (${corr.primary_horizon.lithology})
        </span>
        <span class="tag tag-green">✓ STATUS: CORRELATED</span>
      </div>
      <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:12px; font-family:var(--font-mono); font-size:0.8rem; margin-top:10px;">
        <div><strong>Active Top:</strong> ${corr.primary_horizon.top_tvdss_m}m TVDSS</div>
        <div><strong>Offset Top:</strong> ${corr.offset_horizon.top_tvdss_m}m TVDSS</div>
        <div><strong>Structural Shift:</strong> ${corr.structural_shift_tvdss_m} m</div>
        <div><strong>Uncertainty:</strong> ±${corr.correlation_uncertainty_m} m</div>
      </div>
    `;

    renderCorrelatedEvents(corr.historical_events_in_interval);
  } catch (err) {
    console.error('Error loading correlation:', err);
  }
}

function runFormationCorrelation() {
  loadCorrelationData();
}

function renderCorrelatedEvents(events) {
  const container = document.getElementById('correlation-events-table');
  if (!events || events.length === 0) {
    container.innerHTML = '<div style="color:var(--text-muted); font-size:0.85rem;">No historical incidents recorded in this geological formation interval.</div>';
    return;
  }

  let html = `
    <table class="audit-table">
      <thead>
        <tr>
          <th>Event ID</th>
          <th>Hazard Type</th>
          <th>Severity</th>
          <th>Offset Depth</th>
          <th>Projected Active TVDSS</th>
          <th>Action / Evidence</th>
        </tr>
      </thead>
      <tbody>
  `;
  events.forEach(e => {
    const sevColor = e.severity === 'SEVERE' || e.severity === 'CRITICAL' ? 'tag-red' : 'tag-amber';
    html += `
      <tr>
        <td style="font-family:var(--font-mono); font-weight:700; color:var(--copper-bright);">${e.event_id}</td>
        <td><strong>${e.event_type}</strong></td>
        <td><span class="tag ${sevColor}">${e.severity}</span></td>
        <td style="font-family:var(--font-mono);">${e.offset_depth_md_m}m MD (${e.offset_depth_tvdss_m}m TVDSS)</td>
        <td style="font-family:var(--font-mono); color:var(--amber-accent); font-weight:700;">${e.projected_active_tvdss_m}m TVDSS</td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick='openEvidenceModal(${JSON.stringify(e).replace(/'/g, "&apos;")})'>
            🔍 Evidence Passport
          </button>
        </td>
      </tr>
    `;
  });
  html += `</tbody></table>`;
  container.innerHTML = html;
}

// -------------------------------------------------------------
// View D: Geological Fingerprint
// -------------------------------------------------------------
async function loadFingerprintData() {
  try {
    const res = await fetch(`/api/v1/geocore/wellbores/${activeWellId}/fingerprint?formation=${encodeURIComponent(targetFormation)}`);
    const data = await res.json();
    const fp = data.fingerprint;
    const audit = fp.categorized_audit;

    document.getElementById('fp-completeness-badge').textContent = `COMPLETENESS: ${audit.completeness_score_pct}%`;

    // Verified Grid
    const vGrid = document.getElementById('fp-verified-grid');
    vGrid.innerHTML = audit.verified_features.map(f => `
      <div class="fp-badge-item verified">
        <div style="font-size:0.75rem; font-weight:800; color:var(--green-safe); text-transform:uppercase;">${f.feature}</div>
        <div style="font-size:0.95rem; font-weight:700; margin:4px 0;">${f.value}</div>
        <div style="font-size:0.72rem; color:var(--text-muted);">Source: ${f.source}</div>
      </div>
    `).join('');

    // Derived Grid
    const dGrid = document.getElementById('fp-derived-grid');
    dGrid.innerHTML = audit.derived_features.map(f => `
      <div class="fp-badge-item derived">
        <div style="font-size:0.75rem; font-weight:800; color:var(--copper-primary); text-transform:uppercase;">${f.feature}</div>
        <div style="font-size:0.95rem; font-weight:700; margin:4px 0;">${f.value}</div>
        <div style="font-size:0.72rem; color:var(--text-muted);">Method: ${f.method}</div>
      </div>
    `).join('');

    // Missing Grid
    const mGrid = document.getElementById('fp-missing-grid');
    mGrid.innerHTML = audit.missing_features.map(f => `
      <div class="fp-badge-item missing">
        <div style="font-size:0.75rem; font-weight:800; color:var(--red-hazard); text-transform:uppercase;">UNRECORDED PARAMETER</div>
        <div style="font-size:0.9rem; font-weight:600; margin:4px 0; color:var(--text-main);">${f}</div>
        <div style="font-size:0.72rem; color:var(--text-muted);">Explicitly penalized in similarity scoring</div>
      </div>
    `).join('');

    // Uncertain Grid
    const uGrid = document.getElementById('fp-uncertain-grid');
    uGrid.innerHTML = audit.uncertain_interpretations.length > 0 ? audit.uncertain_interpretations.map(f => `
      <div class="fp-badge-item uncertain">
        <div style="font-size:0.75rem; font-weight:800; color:var(--gold-accent); text-transform:uppercase;">${f.feature}</div>
        <div style="font-size:0.9rem; font-weight:600; margin:4px 0;">${f.value}</div>
        <div style="font-size:0.72rem; color:var(--text-muted);">${f.reason}</div>
      </div>
    `).join('') : '<div style="color:var(--text-muted); font-size:0.85rem; padding:10px;">Zero uncertain interpretations flagged for active well.</div>';

  } catch (err) {
    console.error('Error loading fingerprint:', err);
  }
}

// -------------------------------------------------------------
// View E: "Why This Well, Not That Well?"
// -------------------------------------------------------------
async function loadComparisonData() {
  const wellA = document.getElementById('comp-well-a').value;
  const wellB = document.getElementById('comp-well-b').value;
  if (wellA === wellB) return;

  try {
    const res = await fetch('/api/v1/geocore/compare', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        primary_well_id: activeWellId,
        well_a_id: wellA,
        well_b_id: wellB,
        target_formation_name: targetFormation
      })
    });
    const data = await res.json();
    const comp = data.comparison;

    document.getElementById('comparison-verdict-banner').innerHTML = `
      <strong style="color:var(--copper-bright);">ENGINEERING DETERMINATION:</strong><br>
      ${comp.comparison_verdict}
      <div style="margin-top:10px; font-size:0.8rem; color:var(--text-muted);">
        <strong>Baseline Contrast:</strong> ${comp.baseline_distance_comparison.explanation}
      </div>
    `;

    const cols = document.getElementById('comparison-columns');
    const aWinner = comp.score_differential >= 0;

    cols.innerHTML = `
      <div class="comp-col ${aWinner ? 'winner' : ''}">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <h4 style="font-size:1.1rem; color:var(--copper-bright);">${comp.well_a.offset_well_name}</h4>
          ${aWinner ? '<span class="tag tag-amber">★ RECOMMENDED ANALOGUE</span>' : ''}
        </div>
        <div style="margin:12px 0; font-size:0.85rem;">
          <div><strong>GeoCore Score:</strong> ${(comp.well_a.composite_similarity_score * 100).toFixed(1)}% (Rank #${comp.well_a.rank_order})</div>
          <div><strong>Geographic Distance:</strong> ${comp.well_a.distance_km} km (Distance Rank #${comp.baseline_distance_comparison.well_a_distance_rank})</div>
          <div><strong>Target Formation Match:</strong> ${comp.well_a.target_formation_matched ? '✓ YES' : '✕ NO'}</div>
          <div><strong>Verified Incidents in Target:</strong> ${comp.well_a.events_in_target_formation}</div>
        </div>
        <p style="font-size:0.8rem; color:var(--text-muted); line-height:1.5;">${comp.well_a.engineering_rationale}</p>
      </div>

      <div class="comp-col ${!aWinner ? 'winner' : ''}">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <h4 style="font-size:1.1rem; color:var(--text-muted);">${comp.well_b.offset_well_name}</h4>
          ${!aWinner ? '<span class="tag tag-amber">★ RECOMMENDED ANALOGUE</span>' : ''}
        </div>
        <div style="margin:12px 0; font-size:0.85rem;">
          <div><strong>GeoCore Score:</strong> ${(comp.well_b.composite_similarity_score * 100).toFixed(1)}% (Rank #${comp.well_b.rank_order})</div>
          <div><strong>Geographic Distance:</strong> ${comp.well_b.distance_km} km (Distance Rank #${comp.baseline_distance_comparison.well_b_distance_rank})</div>
          <div><strong>Target Formation Match:</strong> ${comp.well_b.target_formation_matched ? '✓ YES' : '✕ NO'}</div>
          <div><strong>Verified Incidents in Target:</strong> ${comp.well_b.events_in_target_formation}</div>
        </div>
        <p style="font-size:0.8rem; color:var(--text-muted); line-height:1.5;">${comp.well_b.engineering_rationale}</p>
      </div>
    `;
  } catch (err) {
    console.error('Error running comparison:', err);
  }
}

function runComparison() {
  loadComparisonData();
}

// -------------------------------------------------------------
// View F: Subsurface Corridor
// -------------------------------------------------------------
async function loadCorridorData() {
  try {
    const res = await fetch('/api/v1/geocore/corridor', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        primary_well_id: activeWellId,
        max_corridor_radius_m: 6000.0
      })
    });
    const data = await res.json();
    const corr = data.corridor;

    const wrap = document.getElementById('corridor-table-wrap');
    let html = `
      <table class="audit-table">
        <thead>
          <tr>
            <th>Offset Wellbore</th>
            <th>Surface Distance</th>
            <th>3D Subsurface Min Separation</th>
            <th>Survey Stations</th>
            <th>Historical Incidents</th>
          </tr>
        </thead>
        <tbody>
    `;
    corr.corridor_offsets.forEach(o => {
      html += `
        <tr>
          <td style="font-weight:700; color:var(--copper-bright);">${o.well_name}</td>
          <td style="font-family:var(--font-mono);">${(o.surface_distance_m / 1000).toFixed(2)} km</td>
          <td style="font-family:var(--font-mono); font-weight:700; color:var(--amber-accent);">${(o.min_subsurface_distance_m / 1000).toFixed(2)} km</td>
          <td>${o.survey_station_count} stations</td>
          <td><span class="tag tag-cyan">${o.historical_events_count} Incidents</span></td>
        </tr>
      `;
    });
    html += `</tbody></table>`;
    wrap.innerHTML = html;
  } catch (err) {
    console.error('Error loading corridor:', err);
  }
}

// -------------------------------------------------------------
// View G: Specialist Review & Cryptographic Audit
// -------------------------------------------------------------
async function submitSpecialistReview(event) {
  event.preventDefault();
  const corrId = document.getElementById('review-corr-id').value;
  const name = document.getElementById('review-name').value;
  const role = document.getElementById('review-role').value;
  const decision = document.getElementById('review-decision').value;
  const notes = document.getElementById('review-notes').value;

  try {
    const res = await fetch('/api/v1/geocore/correlations/review', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        correlation_id: corrId,
        reviewer_name: name,
        reviewer_role: role,
        decision: decision,
        review_notes: notes
      })
    });
    const data = await res.json();
    if (data.status === 'SUCCESS') {
      alert(`✓ Review successfully committed to immutable audit log! HMAC: ${data.review.integrity_hmac.substring(0, 16)}...`);
      await loadAuditHistory();
    }
  } catch (err) {
    alert('Error submitting review: ' + err);
  }
}

async function loadAuditHistory() {
  try {
    const res = await fetch('/api/v1/geocore/audit?limit=20');
    const data = await res.json();
    const container = document.getElementById('review-audit-history');

    if (data.audit_trail.length === 0) {
      container.innerHTML = '<div style="color:var(--text-muted); font-size:0.85rem;">No specialist reviews recorded yet.</div>';
      return;
    }

    container.innerHTML = data.audit_trail.map(r => `
      <div style="background:rgba(255,255,255,0.02); border:1px solid var(--border-subtle); border-radius:8px; padding:14px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
          <span style="font-weight:700; color:var(--text-main); font-size:0.9rem;">${r.correlation_id}</span>
          <span class="tag ${r.decision === 'APPROVED' ? 'tag-green' : 'tag-red'}">${r.decision}</span>
        </div>
        <div style="font-size:0.8rem; color:var(--copper-light); margin-bottom:4px;">
          Reviewer: ${r.reviewer_name} (${r.reviewer_role})
        </div>
        <div style="font-size:0.8rem; color:var(--text-muted); line-height:1.4;">
          ${r.notes || 'No remarks provided.'}
        </div>
        <div style="font-family:var(--font-mono); font-size:0.7rem; color:var(--text-dim); margin-top:6px;">
          Timestamp: ${r.timestamp}
        </div>
      </div>
    `).join('');
  } catch (err) {
    console.error('Error loading audit:', err);
  }
}

// -------------------------------------------------------------
// Evidence Passport Modal
// -------------------------------------------------------------
function openEvidenceModal(evt) {
  document.getElementById('modal-event-type').textContent = evt.event_type;
  document.getElementById('modal-event-title').textContent = `${evt.event_type} (${evt.severity}) at ${evt.offset_depth_md_m}m MD`;
  document.getElementById('modal-narrative').textContent = evt.narrative;
  document.getElementById('modal-mitigation').innerHTML = `<strong>Applied Mitigation Protocol:</strong><br>${evt.mitigation}`;
  document.getElementById('modal-well').textContent = evt.well_id || 'NO-15/9-F-14';
  document.getElementById('modal-citation').textContent = evt.source_citation;
  document.getElementById('modal-doc-id').textContent = evt.doc_id || 'DOC-VOLVE-DDR-20080914-F14';

  document.getElementById('evidence-modal').classList.add('active');
}

function closeEvidenceModal() {
  document.getElementById('evidence-modal').classList.remove('active');
}
