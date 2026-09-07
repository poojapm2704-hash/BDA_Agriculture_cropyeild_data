// Global State & Chart Handles
let yieldBarChart = null;
let rainfallScatterChart = null;
let regionDonutChart = null;
let soilRadarChart = null;
let allQueriesData = [];

document.addEventListener('DOMContentLoaded', () => {
  fetchOverviewStats();
  fetchQueriesAndBuildCharts();
  loadFarmSamples();
  fetchAnomalies();
  fetchComparison();
});

// Tab Switcher
function switchTab(tabId) {
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));

  event.currentTarget.classList.add('active');
  document.getElementById(tabId).classList.add('active');
}

// Fetch Summary Stats
async function fetchOverviewStats() {
  try {
    const res = await fetch('/api/stats');
    const data = await res.json();

    document.getElementById('statRecords').textContent = data.total_records.toLocaleString();
    document.getElementById('statCrops').textContent = data.total_crops;
    document.getElementById('statRegions').textContent = data.total_regions;
    document.getElementById('statAvgYield').innerHTML = `${data.avg_yield_tons} <small style="font-size: 1rem;">tons/ha</small>`;

    const badge = document.getElementById('mongoStatusBadge');
    if (data.mongo_connected) {
      badge.textContent = "MongoDB Connected";
      badge.className = "badge badge-green";
    } else {
      badge.textContent = "JSON Fallback Mode";
      badge.className = "badge badge-blue";
    }
  } catch (err) {
    console.error("Failed to fetch stats:", err);
  }
}

// Fetch 5 Queries & Build Visual Charts
async function fetchQueriesAndBuildCharts() {
  try {
    const res = await fetch('/api/queries');
    const result = await res.json();
    allQueriesData = result.queries;

    loadQuery(1);

    const q1 = allQueriesData.find(q => q.query_id === 1);
    if (q1) renderYieldBarChart(q1.data);

    renderRainfallScatterPlot();

    const q2 = allQueriesData.find(q => q.query_id === 2);
    if (q2) renderRegionDonutChart(q2.data);

    const q4 = allQueriesData.find(q => q.query_id === 4);
    if (q4) renderSoilRadarChart(q4.data);

  } catch (err) {
    console.error("Failed to fetch queries:", err);
  }
}

// --------------------------------------------------------
// CHART 1: Crop Yield Bar Chart (Requirement #4)
// --------------------------------------------------------
function renderYieldBarChart(data) {
  const ctx = document.getElementById('yieldBarChart').getContext('2d');
  
  const labels = data.map(d => d.crop_type);
  const yields = data.map(d => d.avg_yield);

  if (yieldBarChart) yieldBarChart.destroy();

  yieldBarChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Average Yield (tons/hectare)',
        data: yields,
        backgroundColor: [
          '#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899', '#06B6D4', '#84CC16'
        ],
        borderRadius: 8,
        borderWidth: 1,
        borderColor: 'rgba(255,255,255,0.2)'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => `Yield: ${ctx.parsed.y} tons/ha`
          }
        }
      },
      scales: {
        x: { ticks: { color: '#94A3B8' }, grid: { display: false } },
        y: { ticks: { color: '#94A3B8' }, grid: { color: 'rgba(255,255,255,0.05)' } }
      }
    }
  });
}

// --------------------------------------------------------
// CHART 2: Rainfall vs Yield Scatter Plot (Requirement #5)
// --------------------------------------------------------
async function renderRainfallScatterPlot() {
  const ctx = document.getElementById('rainfallScatterChart').getContext('2d');

  try {
    const res = await fetch('/api/farms?limit=250');
    const farmRes = await res.json();
    const farms = farmRes.data;

    const scatterPoints = farms.map(f => ({
      x: f.rainfall,
      y: f.yield_tons,
      crop: f.crop_type
    }));

    if (rainfallScatterChart) rainfallScatterChart.destroy();

    rainfallScatterChart = new Chart(ctx, {
      type: 'scatter',
      data: {
        datasets: [{
          label: 'Farm Rainfall vs Yield',
          data: scatterPoints,
          backgroundColor: 'rgba(59, 130, 246, 0.6)',
          borderColor: '#3B82F6',
          pointRadius: 5,
          pointHoverRadius: 8
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          tooltip: {
            callbacks: {
              label: (ctx) => `${ctx.raw.crop}: ${ctx.raw.x} mm rain -> ${ctx.raw.y} tons/ha`
            }
          }
        },
        scales: {
          x: {
            title: { display: true, text: 'Annual Rainfall (mm)', color: '#94A3B8' },
            ticks: { color: '#94A3B8' },
            grid: { color: 'rgba(255,255,255,0.05)' }
          },
          y: {
            title: { display: true, text: 'Annual Yield (tons/ha)', color: '#94A3B8' },
            ticks: { color: '#94A3B8' },
            grid: { color: 'rgba(255,255,255,0.05)' }
          }
        }
      }
    });
  } catch (err) {
    console.error("Scatter plot error:", err);
  }
}

// CHART 3: Region Output Donut
function renderRegionDonutChart(data) {
  const ctx = document.getElementById('regionDonutChart').getContext('2d');
  if (regionDonutChart) regionDonutChart.destroy();

  regionDonutChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: data.map(d => d.region),
      datasets: [{
        data: data.map(d => d.total_output_tons),
        backgroundColor: ['#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899'],
        borderWidth: 2,
        borderColor: '#0B0F19'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'right', labels: { color: '#94A3B8' } }
      }
    }
  });
}

// CHART 4: Soil Radar Chart
function renderSoilRadarChart(data) {
  const ctx = document.getElementById('soilRadarChart').getContext('2d');
  if (soilRadarChart) soilRadarChart.destroy();

  soilRadarChart = new Chart(ctx, {
    type: 'radar',
    data: {
      labels: data.map(d => d.crop_type),
      datasets: [
        {
          label: 'Optimal Soil pH (x10)',
          data: data.map(d => d.optimal_soil_pH * 10),
          borderColor: '#10B981',
          backgroundColor: 'rgba(16, 185, 129, 0.2)'
        },
        {
          label: 'Soil Moisture %',
          data: data.map(d => d.optimal_moisture_pct),
          borderColor: '#3B82F6',
          backgroundColor: 'rgba(59, 130, 246, 0.2)'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        r: {
          angleLines: { color: 'rgba(255,255,255,0.1)' },
          grid: { color: 'rgba(255,255,255,0.1)' },
          pointLabels: { color: '#94A3B8' },
          ticks: { backdropColor: 'transparent', color: '#94A3B8' }
        }
      },
      plugins: {
        legend: { labels: { color: '#94A3B8' } }
      }
    }
  });
}

// Load MongoDB Query in Workbench Tab
function loadQuery(qId) {
  document.querySelectorAll('.q-btn').forEach(btn => btn.classList.remove('active'));
  if (event && event.target) event.target.classList.add('active');

  const q = allQueriesData.find(item => item.query_id === qId);
  if (!q) return;

  document.getElementById('queryDesc').textContent = q.description;
  document.getElementById('queryMqlCode').textContent = JSON.stringify(q.mql, null, 2);

  const header = document.getElementById('queryTableHeader');
  const body = document.getElementById('queryTableBody');

  if (!q.data || q.data.length === 0) return;

  const cols = Object.keys(q.data[0]);
  header.innerHTML = `<tr>${cols.map(c => `<th>${c.replace(/_/g, ' ')}</th>`).join('')}</tr>`;

  body.innerHTML = q.data.slice(0, 10).map(row => `
    <tr>${cols.map(c => `<td>${row[c]}</td>`).join('')}</tr>
  `).join('');
}

// EXTRA FEATURE 1: Anomaly Alert Center Handler
async function fetchAnomalies() {
  try {
    const res = await fetch('/api/anomalies');
    const data = await res.json();

    document.getElementById('anomalyBadgeCount').textContent = `${data.anomaly_count} Anomalies Active`;
    
    const tbody = document.getElementById('anomalyTableBody');
    tbody.innerHTML = data.anomalies.map(a => `
      <tr>
        <td><strong>${a.farm_id}</strong></td>
        <td>${a.location}</td>
        <td><span class="badge badge-blue">${a.crop_type}</span></td>
        <td>${a.soil_pH}</td>
        <td>${a.moisture_pct}%</td>
        <td>${a.temp_c}°C</td>
        <td>${a.alerts.map(al => `<span class="badge badge-green" style="background: rgba(239,68,68,0.2); color:#FCA5A5; border-color: rgba(239,68,68,0.4); margin-right:4px;">${al}</span>`).join('')}</td>
      </tr>
    `).join('');
  } catch (err) {
    console.error("Anomaly fetch error:", err);
  }
}

// EXTRA FEATURE 2: Comparative Crop Matrix Handler
async function fetchComparison() {
  const c1 = document.getElementById('compCrop1').value;
  const c2 = document.getElementById('compCrop2').value;
  const c3 = document.getElementById('compCrop3').value;

  try {
    const res = await fetch(`/api/compare?crop1=${c1}&crop2=${c2}&crop3=${c3}`);
    const data = await res.json();
    const comp = data.comparison;

    document.getElementById('compHead1').textContent = comp[0].crop_type;
    document.getElementById('compHead2').textContent = comp[1].crop_type;
    document.getElementById('compHead3').textContent = comp[2].crop_type;

    const metrics = [
      { label: "Average Yield (tons/ha)", key: "avg_yield" },
      { label: "Max Peak Yield (tons/ha)", key: "max_yield" },
      { label: "Optimal Soil pH", key: "optimal_soil_pH" },
      { label: "Optimal Soil Moisture (%)", key: "optimal_moisture_pct" },
      { label: "Ambient Growing Temp (°C)", key: "avg_temp_c" },
      { label: "Target Fertilizer (kg/ha)", key: "avg_fertilizer_kg" }
    ];

    const tbody = document.getElementById('compareTableBody');
    tbody.innerHTML = metrics.map(m => `
      <tr>
        <td><strong>${m.label}</strong></td>
        <td>${comp[0][m.key]}</td>
        <td>${comp[1][m.key]}</td>
        <td>${comp[2][m.key]}</td>
      </tr>
    `).join('');

  } catch (err) {
    console.error("Comparison fetch error:", err);
  }
}

// Predictor Calculator Form Submit
async function calculateYield(e) {
  e.preventDefault();
  const payload = {
    crop_type: document.getElementById('predCrop').value,
    soil_pH: parseFloat(document.getElementById('predPh').value),
    rainfall: parseFloat(document.getElementById('predRain').value),
    fertilizer_kg: parseFloat(document.getElementById('predFert').value),
    soil_moisture_pct: parseFloat(document.getElementById('predMoist').value)
  };

  try {
    const res = await fetch('/api/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    document.getElementById('predictResultBanner').style.display = 'flex';
    document.getElementById('resYield').textContent = `${data.predicted_yield_tons} tons/ha`;
    document.getElementById('resScore').textContent = `${data.growth_score} / 100`;

    document.getElementById('resTargets').innerHTML = `
      <strong>Optimal Agronomic Guidance:</strong><br/>
      • ${data.recommendations.soil_pH}<br/>
      • ${data.recommendations.rainfall}<br/>
      • ${data.recommendations.fertilizer}
    `;
  } catch (err) {
    console.error("Prediction error:", err);
  }
}

// Populate Farm Inspector
async function loadFarmSamples() {
  try {
    const res = await fetch('/api/farms?limit=12');
    const result = await res.json();

    const tbody = document.getElementById('farmInspectorBody');
    tbody.innerHTML = result.data.map(f => {
      const sCount = f.sensor_logs ? f.sensor_logs.length : 0;
      return `
        <tr>
          <td><strong>${f.farm_id}</strong></td>
          <td>${f.location}</td>
          <td><span class="badge badge-green">${f.crop_type}</span></td>
          <td>${f.soil_pH}</td>
          <td>${f.rainfall} mm</td>
          <td>${f.fertilizer_kg} kg</td>
          <td><strong>${f.yield_tons} tons/ha</strong></td>
          <td>${f.year}</td>
          <td><span class="badge badge-blue">${sCount} IoT Logs</span></td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    console.error("Inspector load error:", err);
  }
}
