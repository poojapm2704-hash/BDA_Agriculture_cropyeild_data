"""
Agricultural Crop Yield Data System - Web Application Server
Flask REST API & Web Dashboard backend connecting to MongoDB Analytics Engine.
Includes Anomaly Alert System, Crop Comparative Matrix, Data Exporters, and PDF Report service.
"""

import os
import json
import csv
import io
from flask import Flask, render_template, jsonify, request, send_file, Response
from mongo_analytics import MongoAnalyticsEngine
from generate_pdf_report import create_project_report_pdf, PDF_OUTPUT_PATH

app = Flask(__name__, static_folder='static', template_folder='templates')
engine = MongoAnalyticsEngine()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Returns dataset summary metrics."""
    if engine.use_mongo:
        total_records = engine.collection.count_documents({})
        crops = engine.collection.distinct("crop_type")
        regions = engine.collection.distinct("location")
        pipeline = [{"$group": {"_id": None, "avg": {"$avg": "$yield_tons"}}}]
        avg_res = list(engine.collection.aggregate(pipeline))
        avg_yield = round(avg_res[0]["avg"], 2) if avg_res else 0.0
    else:
        total_records = len(engine.df_cache)
        crops = engine.df_cache["crop_type"].unique().tolist()
        regions = engine.df_cache["location"].unique().tolist()
        avg_yield = round(float(engine.df_cache["yield_tons"].mean()), 2)
        
    return jsonify({
        "status": "success",
        "mongo_connected": engine.use_mongo,
        "total_records": total_records,
        "total_crops": len(crops),
        "crops": crops,
        "total_regions": len(regions),
        "regions": regions,
        "avg_yield_tons": avg_yield
    })

@app.route('/api/queries', methods=['GET'])
def get_queries():
    """Returns results for all 5 MongoDB analytical queries."""
    queries = engine.execute_all_queries()
    return jsonify({
        "status": "success",
        "queries": queries
    })

@app.route('/api/query/<int:query_id>', methods=['GET'])
def get_query_by_id(query_id):
    """Returns specific query result by ID (1 to 5)."""
    handlers = {
        1: engine.query_1_avg_yield_by_crop,
        2: engine.query_2_top_5_regions,
        3: engine.query_3_yield_vs_rainfall,
        4: engine.query_4_optimal_sensor_soil_conditions,
        5: engine.query_5_yoy_yield_patterns
    }
    if query_id in handlers:
        return jsonify({"status": "success", "result": handlers[query_id]()})
    return jsonify({"status": "error", "message": "Invalid query ID"}), 400

# EXTRA FEATURE 1: Anomaly Alert Detection Endpoint
@app.route('/api/anomalies', methods=['GET'])
def get_anomalies():
    """Detects farms with critical soil pH, extreme temperature, or drought moisture levels."""
    anomalies = []
    
    if engine.use_mongo:
        pipeline = [
            {"$unwind": "$sensor_logs"},
            {
                "$match": {
                    "$or": [
                        {"soil_pH": {"$lt": 5.2}},
                        {"soil_pH": {"$gt": 8.0}},
                        {"sensor_logs.soil_moisture_pct": {"$lt": 25.0}},
                        {"sensor_logs.ambient_temp_c": {"$gt": 38.0}}
                    ]
                }
            },
            {"$limit": 20}
        ]
        results = list(engine.collection.aggregate(pipeline))
        for r in results:
            sens = r.get("sensor_logs", {})
            issues = []
            if r.get("soil_pH", 7.0) < 5.2: issues.append("Severe Acidic Soil (pH < 5.2)")
            elif r.get("soil_pH", 7.0) > 8.0: issues.append("Alkaline Soil Stress (pH > 8.0)")
            if sens.get("soil_moisture_pct", 50) < 25.0: issues.append("Severe Soil Drought (<25% moisture)")
            if sens.get("ambient_temp_c", 25) > 38.0: issues.append("Heatwave Warning (>38°C)")
            
            anomalies.append({
                "farm_id": r.get("farm_id"),
                "crop_type": r.get("crop_type"),
                "location": r.get("location"),
                "soil_pH": r.get("soil_pH"),
                "moisture_pct": sens.get("soil_moisture_pct"),
                "temp_c": sens.get("ambient_temp_c"),
                "alerts": issues
            })
    else:
        for item in engine.data_cache:
            soil_ph = item.get("soil_pH", 7.0)
            logs = item.get("sensor_logs", [])
            for sens in logs:
                moist = sens.get("soil_moisture_pct", 50)
                temp = sens.get("ambient_temp_c", 25)
                issues = []
                if soil_ph < 5.2: issues.append("Severe Acidic Soil (pH < 5.2)")
                elif soil_ph > 8.0: issues.append("Alkaline Soil Stress (pH > 8.0)")
                if moist < 25.0: issues.append("Severe Soil Drought (<25% moisture)")
                if temp > 38.0: issues.append("Heatwave Warning (>38°C)")
                
                if issues:
                    anomalies.append({
                        "farm_id": item.get("farm_id"),
                        "crop_type": item.get("crop_type"),
                        "location": item.get("location"),
                        "soil_pH": soil_ph,
                        "moisture_pct": moist,
                        "temp_c": temp,
                        "alerts": issues
                    })
                    break
            if len(anomalies) >= 20:
                break
                
    return jsonify({
        "status": "success",
        "anomaly_count": len(anomalies),
        "anomalies": anomalies
    })

# EXTRA FEATURE 2: Comparative Crop Matrix
@app.route('/api/compare', methods=['GET'])
def compare_crops():
    """Returns side-by-side metrics comparing selected crops."""
    crop1 = request.args.get('crop1', 'Wheat')
    crop2 = request.args.get('crop2', 'Rice')
    crop3 = request.args.get('crop3', 'Maize')
    
    crops_to_compare = [crop1, crop2, crop3]
    q1 = engine.query_1_avg_yield_by_crop()['data']
    q4 = engine.query_4_optimal_sensor_soil_conditions()['data']
    
    comparison = []
    for c in crops_to_compare:
        q1_item = next((item for item in q1 if item["crop_type"] == c), {})
        q4_item = next((item for item in q4 if item["crop_type"] == c), {})
        
        comparison.append({
            "crop_type": c,
            "avg_yield": q1_item.get("avg_yield", 0.0),
            "max_yield": q1_item.get("max_yield", 0.0),
            "optimal_soil_pH": q4_item.get("optimal_soil_pH", 0.0),
            "optimal_moisture_pct": q4_item.get("optimal_moisture_pct", 0.0),
            "avg_temp_c": q4_item.get("avg_temp_c", 0.0),
            "avg_fertilizer_kg": q4_item.get("avg_fertilizer_kg", 0.0)
        })
        
    return jsonify({
        "status": "success",
        "comparison": comparison
    })

# EXTRA FEATURE 3: CSV Data Exporter
@app.route('/api/export-csv', methods=['GET'])
def export_csv():
    """Exports farm dataset as CSV file."""
    if engine.use_mongo:
        records = list(engine.collection.find({}, {"_id": 0, "sensor_logs": 0}).limit(2000))
    else:
        records = engine.df_cache.drop(columns=["sensor_logs"], errors="ignore").head(2000).to_dict(orient="records")
        
    output = io.StringIO()
    if records:
        writer = csv.DictWriter(output, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
        
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=farm_yield_dataset_export.csv"}
    )

@app.route('/api/predict', methods=['POST'])
def predict_yield():
    """Calculates predicted crop yield based on soil pH, rainfall, fertilizer, and sensor logs."""
    data = request.json or {}
    crop = data.get("crop_type", "Wheat")
    soil_pH = float(data.get("soil_pH", 6.5))
    rainfall = float(data.get("rainfall", 700.0))
    fertilizer = float(data.get("fertilizer_kg", 150.0))
    moisture = float(data.get("soil_moisture_pct", 50.0))
    
    from data_generator import CROP_PROFILES
    profile = CROP_PROFILES.get(crop, CROP_PROFILES["Wheat"])
    
    ph_dev = abs(soil_pH - profile['ideal_ph']) / profile['ideal_ph']
    rain_dev = abs(rainfall - profile['ideal_rain']) / profile['ideal_rain']
    fert_factor = min(1.35, fertilizer / profile['ideal_fert'])
    moist_factor = 1.0 - abs(moisture - 50.0) / 100.0
    
    yield_multiplier = max(0.3, (1.0 - (0.35 * ph_dev) - (0.3 * rain_dev)) * fert_factor * moist_factor)
    predicted_yield = round(profile['base_yield'] * yield_multiplier, 2)
    
    score = int(min(100, max(20, (yield_multiplier / 1.2) * 100)))
    
    return jsonify({
        "status": "success",
        "crop_type": crop,
        "predicted_yield_tons": predicted_yield,
        "ideal_yield_baseline": profile['base_yield'],
        "growth_score": score,
        "recommendations": {
            "soil_pH": f"Target: {profile['ideal_ph']} (Current: {soil_pH})",
            "rainfall": f"Target: {profile['ideal_rain']}mm (Current: {rainfall}mm)",
            "fertilizer": f"Target: {profile['ideal_fert']}kg/ha (Current: {fertilizer}kg/ha)"
        }
    })

@app.route('/api/farms', methods=['GET'])
def get_farm_samples():
    """Returns sample farm records with embedded sensor arrays."""
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 15))
    crop = request.args.get('crop', None)
    
    if engine.use_mongo:
        query_filter = {"crop_type": crop} if crop else {}
        cursor = engine.collection.find(query_filter, {"_id": 0}).skip((page - 1) * limit).limit(limit)
        items = list(cursor)
        total = engine.collection.count_documents(query_filter)
    else:
        df = engine.df_cache
        if crop:
            df = df[df["crop_type"] == crop]
        total = len(df)
        sub_df = df.iloc[(page - 1) * limit : page * limit]
        items = sub_df.to_dict(orient="records")
        
    return jsonify({
        "status": "success",
        "page": page,
        "limit": limit,
        "total_records": total,
        "data": items
    })

@app.route('/api/download-report', methods=['GET'])
def download_report():
    """Serves the generated executive PDF project report (graphs & tables only)."""
    create_project_report_pdf()
    return send_file(
        PDF_OUTPUT_PATH,
        as_attachment=True,
        download_name="BDA_Agricultural_Crop_Yield_Executive_Report.pdf",
        mimetype="application/pdf"
    )

if __name__ == '__main__':
    print(" Starting Agricultural Crop Yield Data System Web Server...")
    app.run(host='127.0.0.1', port=5000, debug=False)
