<<<<<<< HEAD
# 🌾 Agricultural Crop Yield Data System (Big Data Analytics Project)

A complete, production-ready **Big Data Analytics (BDA) MongoDB application** for storing, analyzing, and predicting farm-level crop yield patterns and optimal growing conditions using FAO FAOSTAT statistics and synthetic IoT sensor logs.

---

## 🚀 Key Features & Highlights

- **MongoDB Schema with Embedded Sensor Logs**: Stores farm documents in MongoDB (`agricultural_db.farms`) containing an embedded sub-document array `sensor_logs` (`soil_moisture_pct`, `ambient_temp_c`, `ph_reading`, `solar_radiation_wm2`, `npk_index`).
- **20,500 Farm Records Dataset**: Synthetic dataset based on real-world FAOSTAT crop yield distributions across 7 major crop species and 8 global agricultural regions.
- **5 MQL Aggregation Queries**:
  1. Average Yield by Crop Type (`$group` & `$sort`)
  2. Top 5 Regions by Total Agricultural Output (`$group` & `$limit`)
  3. Yield vs. Rainfall Correlation & Impact Brackets (`$bucket`)
  4. Optimal Sensor & Soil Growing Conditions per Crop (`$unwind` `$sensor_logs` & `$group`)
  5. Year-over-Year Yield Growth Patterns (`$group` multi-key)
- **Interactive Visual Dashboard**: Modern glassmorphic web dashboard built with Flask, HTML5, CSS3, and Chart.js featuring:
  - **Yield Comparison Bar Chart** (Crop Type vs. Average Yield in tons/ha)
  - **Rainfall Impact Scatter Plot** (Annual rainfall vs. crop output)
  - **🚨 Real-Time Anomaly Alert Center** (Soil acidity stress, drought, heatwaves)
  - **⚖️ Side-by-Side Crop Matrix Comparator** (Compare 3 crops across 6 indicators)
  - **🔮 Crop Yield Predictor Tool** (Agronomic condition optimizer)
  - **📊 CSV & JSON Dataset Exporter**
- **Executive PDF Project Report**: Auto-generated publication-grade PDF report (`BDA_Agricultural_Crop_Yield_Project_Report.pdf`) featuring high-resolution visual charts, data tables, and strategic crop recommendations.

---

## 📁 Repository Structure

```
BDAproject/
├── app.py                      # Flask REST API & Web Dashboard Server
├── data_generator.py           # 20,500 Farm Record & IoT Sensor Log Generator
├── mongo_analytics.py          # PyMongo MongoDB Aggregation Pipeline Engine (5 MQL queries)
├── generate_pdf_report.py      # Executive PDF Report Generator (ReportLab & Matplotlib)
├── data/
│   └── farm_records_20k.json   # Generated 20,500 Farm Records Dataset
├── reports/
│   └── BDA_Agricultural_Crop_Yield_Project_Report.pdf  # Downloadable PDF Report
├── static/
│   ├── css/styles.css          # Glassmorphic Dark-Mode CSS System
│   └── js/main.js              # Chart.js Visualizations & Dashboard Client Logic
├── templates/
│   └── index.html              # Main Web Dashboard Interface
└── README.md                   # Project Documentation
```

---

## 🛠️ Setup & Running Instructions

### 1. Install Python Dependencies
```bash
pip install pymongo pandas numpy matplotlib seaborn reportlab fpdf2 flask
```

### 2. Generate Dataset & Seed MongoDB
```bash
python data_generator.py
```
*(Generates 20,500 records into MongoDB collection `farms` in database `agricultural_db`, with automatic fallback to `data/farm_records_20k.json` if MongoDB daemon is inactive).*

### 3. Run MongoDB Aggregation Queries Test
```bash
python mongo_analytics.py
```

### 4. Generate Executive PDF Project Report
```bash
python generate_pdf_report.py
```

### 5. Launch Interactive Web Dashboard
```bash
python app.py
```
Open **`http://127.0.0.1:5000`** in your browser to view the dynamic dashboard!

---

## 📊 Summary of MongoDB Aggregation Pipelines

```javascript
// Query 1: Average Yield by Crop Type
db.farms.aggregate([
  { $group: { _id: "$crop_type", avg_yield: { $avg: "$yield_tons" }, min_yield: { $min: "$yield_tons" }, max_yield: { $max: "$yield_tons" } } },
  { $sort: { avg_yield: -1 } }
])

// Query 2: Top 5 Regions by Total Output
db.farms.aggregate([
  { $group: { _id: "$location", total_output_tons: { $sum: "$yield_tons" }, avg_farm_yield: { $avg: "$yield_tons" } } },
  { $sort: { total_output_tons: -1 } },
  { $limit: 5 }
])

// Query 3: Yield vs Rainfall Correlation & Bucketing
db.farms.aggregate([
  { $bucket: { groupBy: "$rainfall", boundaries: [0, 500, 800, 1200, 1600, 3000], output: { avg_yield: { $avg: "$yield_tons" }, farm_count: { $sum: 1 } } } }
])

// Query 4: Optimal Sensor & Soil Conditions
db.farms.aggregate([
  { $unwind: "$sensor_logs" },
  { $group: { _id: "$crop_type", optimal_soil_pH: { $avg: "$soil_pH" }, optimal_moisture_pct: { $avg: "$sensor_logs.soil_moisture_pct" }, avg_temp_c: { $avg: "$sensor_logs.ambient_temp_c" } } }
])

// Query 5: Year-over-Year Yield Growth Patterns
db.farms.aggregate([
  { $group: { _id: { crop_type: "$crop_type", year: "$year" }, avg_yield: { $avg: "$yield_tons" } } },
  { $sort: { "_id.crop_type": 1, "_id.year": 1 } }
])
```
=======
# BDA_Agriculture_cropyeild_data
Proect
>>>>>>> 99edb800f6e0bd43013bc20717086778d01e1f33
