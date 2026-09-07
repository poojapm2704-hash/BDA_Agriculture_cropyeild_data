"""
Agricultural Crop Yield Data System - MongoDB Analytics Engine
Contains raw MongoDB Aggregation Pipelines (MQL) and execution wrappers.
Supports PyMongo live MongoDB queries with seamless JSON fallback.
"""

import os
import json
import numpy as np
import pandas as pd
from pymongo import MongoClient

DATA_PATH = os.path.join(os.path.dirname(__file__), 'data', 'farm_records_20k.json')

class MongoAnalyticsEngine:
    def __init__(self, mongo_uri="mongodb://localhost:27017/", db_name="agricultural_db", collection_name="farms"):
        self.use_mongo = False
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.collection_name = collection_name
        self.collection = None
        self.data_cache = None
        
        # Try MongoDB connection
        try:
            self.client = MongoClient(mongo_uri, serverSelectionTimeoutMS=1500)
            self.client.admin.command('ping')
            db = self.client[db_name]
            self.collection = db[collection_name]
            if self.collection.count_documents({}) > 0:
                self.use_mongo = True
                print(" Analytics Engine initialized with live MongoDB connection.")
        except Exception as e:
            print(f" MongoDB unavailable ({e}). Using JSON file fallback.")
            self.use_mongo = False
            
        if not self.use_mongo:
            with open(DATA_PATH, 'r', encoding='utf-8') as f:
                self.data_cache = json.load(f)
            self.df_cache = pd.DataFrame(self.data_cache)
            print(f" Loaded {len(self.data_cache):,} records into memory fallback.")

    # ----------------------------------------------------
    # QUERY 1: Average Yield by Crop Type
    # ----------------------------------------------------
    def query_1_avg_yield_by_crop(self):
        mql_pipeline = [
            {
                "$group": {
                    "_id": "$crop_type",
                    "avg_yield": {"$avg": "$yield_tons"},
                    "min_yield": {"$min": "$yield_tons"},
                    "max_yield": {"$max": "$yield_tons"},
                    "total_farms": {"$sum": 1}
                }
            },
            {"$sort": {"avg_yield": -1}}
        ]
        
        if self.use_mongo:
            results = list(self.collection.aggregate(mql_pipeline))
            formatted = [{
                "crop_type": r["_id"],
                "avg_yield": round(r["avg_yield"], 2),
                "min_yield": round(r["min_yield"], 2),
                "max_yield": round(r["max_yield"], 2),
                "total_farms": r["total_farms"]
            } for r in results]
        else:
            grouped = self.df_cache.groupby("crop_type")["yield_tons"].agg(
                avg_yield="mean", min_yield="min", max_yield="max", total_farms="count"
            ).reset_index().sort_values(by="avg_yield", ascending=False)
            formatted = grouped.round(2).to_dict(orient="records")
            
        return {
            "query_id": 1,
            "title": "Average Yield by Crop Type",
            "mql": mql_pipeline,
            "description": "Groups farm records by crop type to determine mean, minimum, and maximum yield (tons/hectare).",
            "data": formatted
        }

    # ----------------------------------------------------
    # QUERY 2: Top 5 Regions by Total Agricultural Output
    # ----------------------------------------------------
    def query_2_top_5_regions(self):
        mql_pipeline = [
            {
                "$group": {
                    "_id": "$location",
                    "total_output_tons": {"$sum": "$yield_tons"},
                    "avg_farm_yield": {"$avg": "$yield_tons"},
                    "total_farms": {"$sum": 1}
                }
            },
            {"$sort": {"total_output_tons": -1}},
            {"$limit": 5}
        ]
        
        if self.use_mongo:
            results = list(self.collection.aggregate(mql_pipeline))
            formatted = [{
                "region": r["_id"],
                "total_output_tons": round(r["total_output_tons"], 1),
                "avg_farm_yield": round(r["avg_farm_yield"], 2),
                "total_farms": r["total_farms"]
            } for r in results]
        else:
            grouped = self.df_cache.groupby("location").agg(
                total_output_tons=("yield_tons", "sum"),
                avg_farm_yield=("yield_tons", "mean"),
                total_farms=("yield_tons", "count")
            ).reset_index().sort_values(by="total_output_tons", ascending=False).head(5)
            grouped.rename(columns={"location": "region"}, inplace=True)
            formatted = grouped.round(2).to_dict(orient="records")

        return {
            "query_id": 2,
            "title": "Top 5 Regions by Agricultural Output",
            "mql": mql_pipeline,
            "description": "Aggregates total produced crop output across global agricultural regions to identify top 5 producers.",
            "data": formatted
        }

    # ----------------------------------------------------
    # QUERY 3: Rainfall vs Yield Correlation & Rainfall Bins
    # ----------------------------------------------------
    def query_3_yield_vs_rainfall(self):
        mql_pipeline = [
            {
                "$bucket": {
                    "groupBy": "$rainfall",
                    "boundaries": [0, 500, 800, 1200, 1600, 3000],
                    "default": "Other",
                    "output": {
                        "avg_yield": {"$avg": "$yield_tons"},
                        "farm_count": {"$sum": 1},
                        "avg_fertilizer": {"$avg": "$fertilizer_kg"}
                    }
                }
            }
        ]
        
        if self.use_mongo:
            results = list(self.collection.aggregate(mql_pipeline))
            formatted = []
            labels = {0: "Low (<500mm)", 500: "Moderate (500-800mm)", 800: "Optimal (800-1200mm)", 1200: "High (1200-1600mm)", 1600: "Very High (>1600mm)"}
            for r in results:
                b_val = r["_id"]
                formatted.append({
                    "rainfall_range": labels.get(b_val, str(b_val)),
                    "avg_yield": round(r["avg_yield"], 2),
                    "farm_count": r["farm_count"],
                    "avg_fertilizer": round(r["avg_fertilizer"], 1)
                })
        else:
            bins = [0, 500, 800, 1200, 1600, 3000]
            labels = ["Low (<500mm)", "Moderate (500-800mm)", "Optimal (800-1200mm)", "High (1200-1600mm)", "Very High (>1600mm)"]
            df_copy = self.df_cache.copy()
            df_copy['rainfall_range'] = pd.cut(df_copy['rainfall'], bins=bins, labels=labels, right=False)
            grouped = df_copy.groupby('rainfall_range', observed=False).agg(
                avg_yield=('yield_tons', 'mean'),
                farm_count=('yield_tons', 'count'),
                avg_fertilizer=('fertilizer_kg', 'mean')
            ).reset_index()
            formatted = grouped.round(2).to_dict(orient="records")

        # Calculate Pearson Correlation
        if self.use_mongo:
            all_data = list(self.collection.find({}, {"rainfall": 1, "yield_tons": 1}))
            r_val = float(np.corrcoef([d["rainfall"] for d in all_data], [d["yield_tons"] for d in all_data])[0, 1])
        else:
            r_val = float(np.corrcoef(self.df_cache["rainfall"], self.df_cache["yield_tons"])[0, 1])

        return {
            "query_id": 3,
            "title": "Yield vs Rainfall Correlation",
            "mql": mql_pipeline,
            "correlation_coefficient": round(r_val, 4),
            "description": "Uses MongoDB $bucket to segment annual rainfall levels into 5 brackets and evaluate crop output impact.",
            "data": formatted
        }

    # ----------------------------------------------------
    # QUERY 4: Optimal Soil & Sensor Readings per Crop
    # ----------------------------------------------------
    def query_4_optimal_sensor_soil_conditions(self):
        mql_pipeline = [
            {"$unwind": "$sensor_logs"},
            {
                "$group": {
                    "_id": "$crop_type",
                    "optimal_soil_pH": {"$avg": "$soil_pH"},
                    "optimal_moisture_pct": {"$avg": "$sensor_logs.soil_moisture_pct"},
                    "avg_temp_c": {"$avg": "$sensor_logs.ambient_temp_c"},
                    "avg_fertilizer_kg": {"$avg": "$fertilizer_kg"},
                    "avg_high_yield": {"$avg": "$yield_tons"}
                }
            },
            {"$sort": {"avg_high_yield": -1}}
        ]
        
        if self.use_mongo:
            results = list(self.collection.aggregate(mql_pipeline))
            formatted = [{
                "crop_type": r["_id"],
                "optimal_soil_pH": round(r["optimal_soil_pH"], 2),
                "optimal_moisture_pct": round(r["optimal_moisture_pct"], 1),
                "avg_temp_c": round(r["avg_temp_c"], 1),
                "avg_fertilizer_kg": round(r["avg_fertilizer_kg"], 1),
                "avg_yield": round(r["avg_high_yield"], 2)
            } for r in results]
        else:
            # Flatten sensor logs
            records = []
            for item in self.data_cache:
                for s in item.get('sensor_logs', []):
                    records.append({
                        'crop_type': item['crop_type'],
                        'soil_pH': item['soil_pH'],
                        'fertilizer_kg': item['fertilizer_kg'],
                        'yield_tons': item['yield_tons'],
                        'soil_moisture_pct': s['soil_moisture_pct'],
                        'ambient_temp_c': s['ambient_temp_c']
                    })
            df_sens = pd.DataFrame(records)
            grouped = df_sens.groupby('crop_type').agg(
                optimal_soil_pH=('soil_pH', 'mean'),
                optimal_moisture_pct=('soil_moisture_pct', 'mean'),
                avg_temp_c=('ambient_temp_c', 'mean'),
                avg_fertilizer_kg=('fertilizer_kg', 'mean'),
                avg_yield=('yield_tons', 'mean')
            ).reset_index().sort_values(by='avg_yield', ascending=False)
            formatted = grouped.round(2).to_dict(orient="records")

        return {
            "query_id": 4,
            "title": "Optimal Soil & Sensor Growing Conditions",
            "mql": mql_pipeline,
            "description": "Unwinds embedded sensor_logs sub-documents to correlate IoT moisture & temperature logs with optimal crop yields.",
            "data": formatted
        }

    # ----------------------------------------------------
    # QUERY 5: YoY Crop Yield Trends & Growth Pattern
    # ----------------------------------------------------
    def query_5_yoy_yield_patterns(self):
        mql_pipeline = [
            {
                "$group": {
                    "_id": {"crop_type": "$crop_type", "year": "$year"},
                    "avg_yield": {"$avg": "$yield_tons"},
                    "total_farms": {"$sum": 1}
                }
            },
            {"$sort": {"_id.crop_type": 1, "_id.year": 1}}
        ]
        
        if self.use_mongo:
            results = list(self.collection.aggregate(mql_pipeline))
            formatted = [{
                "crop_type": r["_id"]["crop_type"],
                "year": r["_id"]["year"],
                "avg_yield": round(r["avg_yield"], 2),
                "total_farms": r["total_farms"]
            } for r in results]
        else:
            grouped = self.df_cache.groupby(["crop_type", "year"])["yield_tons"].agg(
                avg_yield="mean", total_farms="count"
            ).reset_index().sort_values(by=["crop_type", "year"])
            formatted = grouped.round(2).to_dict(orient="records")

        return {
            "query_id": 5,
            "title": "Year-over-Year Yield Trends (2018 - 2025)",
            "mql": mql_pipeline,
            "description": "Tracks multi-year annual yield trajectories across crop species to detect climate-driven growth patterns.",
            "data": formatted
        }

    def execute_all_queries(self):
        return [
            self.query_1_avg_yield_by_crop(),
            self.query_2_top_5_regions(),
            self.query_3_yield_vs_rainfall(),
            self.query_4_optimal_sensor_soil_conditions(),
            self.query_5_yoy_yield_patterns()
        ]

if __name__ == '__main__':
    engine = MongoAnalyticsEngine()
    q_all = engine.execute_all_queries()
    print("\n--- MONGO ANALYTICS TEST RESULTS ---")
    for q in q_all:
        print(f"Query {q['query_id']}: {q['title']} -> {len(q['data'])} records returned.")
