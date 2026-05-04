const $ = (id) => document.getElementById(id);
let SCHOOLS = [];
let FACETS = {};
let LAST_RESULTS = null;
let BREAKDOWN_CHART = null;

// Categorical palette tuned to the teal/slate UI.
const CHART_COLORS = [
  "#0f766e", "#1e40af", "#b45309", "#7e22ce", "#be123c",
  "#0369a1", "#15803d", "#a16207", "#9d174d", "#4338ca",
  "#0e7490", "#65a30d", "#c2410c", "#6d28d9", "#0891b2",
  "#a3e635", "#f59e0b", "#ec4899", "#8b5cf6", "#06b6d4",
  "#84cc16", "#fb923c", "#f43f5e", "#a855f7", "#14b8a6",
];

function colorAt(i) { return CHART_COLORS[i % CHART_COLORS.length]; }

async function loadInit() {
  const [schools, facets] = await Promise.all([
    fetch("/api/schools").then(r => r.json()),
    fetch("/api/facets").then(r => r.json()),
  ]);
  SCHOOLS = schools.schools;
  FACETS = facets;

  const picker = $("school-picker");
  picker.innerHTML = SCHOOLS.map(s => `
    <label>
      <input type="checkbox" value="${s.id}" ${s.id.endsWith("_2026") || s.id === "columbia_2024" ? "checked" : ""}>
      <span>
        <span class="school-name">${s.school_name}</span>
        <span class="school-meta">Class of ${s.year} · ${s.class_size} placements</span>
      </span>
    </label>
  `).join("");

  const bdSelect = $("bd-school");
  bdSelect.innerHTML = SCHOOLS.map(s =>
    `<option value="${s.id}">${s.school_name} (${s.year})</option>`
  ).join("");

  const spec = $("specialty");
  spec.innerHTML = `<option value="">— any —</option>` +
    FACETS.specialties.map(s => `<option value="${s}">${s}</option>`).join("");

  // Default question: matches in the Chicago metro
  $("geo-type").value = "metro";
  populateGeoValues();
  if (FACETS.metros.includes("Chicago")) $("geo-value").value = "Chicago";
}

function populateGeoValues() {
  const t = $("geo-type").value;
  const v = $("geo-value");
  if (!t) {
    v.innerHTML = `<option value="">—</option>`;
    return;
  }
  const opts = FACETS[t === "metro" ? "metros" : t === "region" ? "regions" : "states"];
  v.innerHTML = opts.map(o => `<option value="${o}">${o}</option>`).join("");
}

function getSelectedSchools() {
  return [...document.querySelectorAll("#school-picker input:checked")].map(i => i.value);
}

async function runCompare() {
  const ids = getSelectedSchools();
  if (!ids.length) { alert("Pick at least one school."); return; }

  const params = new URLSearchParams({ schools: ids.join(",") });
  const t = $("geo-type").value;
  const v = $("geo-value").value;
  if (t && v) params.set(t, v);
  const spec = $("specialty").value;
  if (spec) params.set("specialty", spec);

  const data = await fetch(`/api/compare?${params}`).then(r => r.json());
  renderCompare(data);
}

function renderCompare(data) {
  $("results-panel").hidden = false;
  const filters = data.filters;
  const summary = $("filter-summary");
  if (Object.keys(filters).length) {
    summary.innerHTML = `<div class="filter-chips">${
      Object.entries(filters).map(([k, v]) => `<span class="chip">${k}: ${v}</span>`).join("")
    }</div>`;
  } else {
    summary.innerHTML = `<p class="muted">No filters applied — showing full class totals.</p>`;
  }

  const maxPct = Math.max(...data.results.map(r => r.matched_pct), 1);
  const tableHtml = `
    <table>
      <thead><tr><th>School</th><th>Matched</th><th>Class size</th><th>Share</th></tr></thead>
      <tbody>
        ${data.results.map(r => `
          <tr>
            <td>
              <span class="school-cell">${r.school_name}</span>
              <span class="year-pill">${r.year}</span>
            </td>
            <td>${r.matched_count}</td>
            <td>${r.class_size}</td>
            <td>
              <div class="pct-cell">
                <div class="pct-bar"><div class="pct-bar-fill" style="width: ${(r.matched_pct / maxPct) * 100}%"></div></div>
                <span class="pct-value">${r.matched_pct}%</span>
              </div>
            </td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
  $("comparison-table").innerHTML = tableHtml;

  LAST_RESULTS = data.results;
  renderMatchDetail();
}

function renderMatchDetail() {
  if (!LAST_RESULTS) return;
  const groupBy = $("detail-group-by").value;

  const html = LAST_RESULTS.map(r => {
    const groups = {};
    for (const m of r.matches) {
      const key = m[groupBy] || "(unknown)";
      (groups[key] ||= []).push(m);
    }
    const sortedKeys = Object.keys(groups).sort((a, b) =>
      groups[b].length - groups[a].length || a.localeCompare(b)
    );

    const groupsHtml = sortedKeys.length
      ? sortedKeys.map(k => `
          <div class="group-block">
            <div class="group-label">${k} <span class="group-count">· ${groups[k].length}</span></div>
            <ul>
              ${groups[k].map(m => `<li>${formatMatch(m, groupBy)}</li>`).join("")}
            </ul>
          </div>
        `).join("")
      : `<div class="empty">No matches.</div>`;

    return `
      <div class="school-detail">
        <h4>${r.school_name} <span class="year-pill">${r.year}</span> <span class="match-count">${r.matched_count}</span></h4>
        ${groupsHtml}
      </div>
    `;
  }).join("");

  $("match-detail").innerHTML = html;
}

function formatMatch(m, groupBy) {
  // Avoid repeating the field used for grouping.
  switch (groupBy) {
    case "specialty_category":
      return `${m.institution} — ${m.city}, ${m.state}`;
    case "institution":
      return `${m.specialty} — ${m.city}, ${m.state}`;
    case "metro":
      return `${m.specialty} — ${m.institution} (${m.city}, ${m.state})`;
    case "state":
      return `${m.specialty} — ${m.institution} (${m.city})`;
    default:
      return `${m.specialty} — ${m.institution} (${m.city}, ${m.state})`;
  }
}

async function runBreakdown() {
  const sid = $("bd-school").value;
  const by = $("bd-by").value;
  const data = await fetch(`/api/breakdown?school=${sid}&by=${by}`).then(r => r.json());
  const max = Math.max(...data.rows.map(r => r.pct), 1);
  renderBreakdownChart(data);
  $("breakdown-result").innerHTML = `
    <p class="muted">${data.school_name} <span class="year-pill">${data.year}</span> · ${data.class_size} placements, grouped by ${data.group_by.replace("_", " ")}</p>
    <table>
      <thead><tr><th>${data.group_by.replace("_", " ")}</th><th>Count</th><th>Share</th></tr></thead>
      <tbody>
        ${data.rows.map(r => `
          <tr>
            <td>${r.value}</td>
            <td>${r.count}</td>
            <td>
              <div class="pct-cell">
                <div class="pct-bar"><div class="pct-bar-fill" style="width: ${(r.pct / max) * 100}%"></div></div>
                <span class="pct-value">${r.pct}%</span>
              </div>
            </td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}

function renderBreakdownChart(data) {
  const wrap = $("breakdown-chart-wrap");
  wrap.hidden = false;

  // Cap visible slices so the pie stays readable; bucket the long tail as "Other".
  const TOP_N = 12;
  const rows = [...data.rows];
  let labels, values, raw;
  if (rows.length > TOP_N) {
    const top = rows.slice(0, TOP_N);
    const tail = rows.slice(TOP_N);
    const otherCount = tail.reduce((sum, r) => sum + r.count, 0);
    const otherPct = +(tail.reduce((sum, r) => sum + r.pct, 0)).toFixed(1);
    labels = [...top.map(r => r.value), `Other (${tail.length})`];
    values = [...top.map(r => r.count), otherCount];
    raw = [...top, { value: `Other (${tail.length})`, count: otherCount, pct: otherPct, _tail: tail }];
  } else {
    labels = rows.map(r => r.value);
    values = rows.map(r => r.count);
    raw = rows;
  }

  const colors = labels.map((_, i) => colorAt(i));

  if (BREAKDOWN_CHART) BREAKDOWN_CHART.destroy();

  const ctx = $("breakdown-chart").getContext("2d");
  BREAKDOWN_CHART = new Chart(ctx, {
    type: "pie",
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: colors,
        borderColor: "#fff",
        borderWidth: 2,
        hoverOffset: 8,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      animation: { duration: 350 },
      plugins: {
        legend: {
          position: "bottom",
          labels: { boxWidth: 10, boxHeight: 10, font: { size: 11 }, padding: 8 },
        },
        title: {
          display: true,
          text: `${data.school_name} (${data.year}) — by ${data.group_by.replace("_", " ")}`,
          font: { size: 13, weight: "600" },
          color: "#0f172a",
          padding: { bottom: 12 },
        },
        tooltip: {
          padding: 10,
          titleFont: { size: 13, weight: "600" },
          bodyFont: { size: 12 },
          callbacks: {
            title: (items) => items[0].label,
            label: (item) => {
              const r = raw[item.dataIndex];
              const lines = [`${r.count} placements (${r.pct}%)`];
              if (r._tail) {
                lines.push("");
                lines.push("Includes:");
                r._tail.slice(0, 6).forEach(t => lines.push(`  ${t.value}: ${t.count}`));
                if (r._tail.length > 6) lines.push(`  …and ${r._tail.length - 6} more`);
              }
              return lines;
            },
          },
        },
      },
    },
  });
}

document.addEventListener("DOMContentLoaded", () => {
  loadInit();
  $("geo-type").addEventListener("change", populateGeoValues);
  $("run-compare").addEventListener("click", runCompare);
  $("run-breakdown").addEventListener("click", runBreakdown);
  $("detail-group-by").addEventListener("change", renderMatchDetail);
});
