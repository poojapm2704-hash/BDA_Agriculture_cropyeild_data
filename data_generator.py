"""
Agricultural Crop Yield Data System - Dataset Generator
Generates 20,000+ realistic farm documents based on FAO FAOSTAT benchmarks
with embedded synthetic sensor logs array for MongoDB ingestion.
"""

import os
import json
import random
import datetime
from pymongo import MongoClient

# Target output directory
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)
JSON_PATH = os.path.join(DATA_DIR, 'farm_records_20k.json')

# FAO FAOSTAT Baseline Crop Characteristics
CROP_PROFILES = {
    'Wheat': {'base_yield': 4.2, 'std_yield': 1.1, 'ideal_ph': 6.5, 'ph_range': (5.5, 7.8), 'ideal_rain': 650, 'rain_range': (350, 1100), 'ideal_fert': 160, 'temp_range': (12, 28)},
    'Rice': {'base_yield': 5.8, 'std_yield': 1.4, 'ideal_ph': 6.2, 'ph_range': (5.0, 7.5), 'ideal_rain': 1400, 'rain_range': (800, 2200), 'ideal_fert': 180, 'temp_range': (20, 35)},
    'Maize': {'base_yield': 6.5, 'std_yield': 1.6, 'ideal_ph': 6.8, 'ph_range': (5.8, 8.0), 'ideal_rain': 800, 'rain_range': (450, 1400), 'ideal_fert': 210, 'temp_range': (18, 32)},
    'Soybeans': {'base_yield': 3.1, 'std_yield': 0.7, 'ideal_ph': 6.5, 'ph_range': (6.0, 7.5), 'ideal_rain': 700, 'rain_range': (400, 1200), 'ideal_fert': 90, 'temp_range': (15, 30)},
    'Barley': {'base_yield': 3.9, 'std_yield': 0.9, 'ideal_ph': 7.0, 'ph_range': (6.0, 8.2), 'ideal_rain': 500, 'rain_range': (300, 900), 'ideal_fert': 120, 'temp_range': (10, 25)},
    'Potato': {'base_yield': 22.5, 'std_yield': 4.5, 'ideal_ph': 5.8, 'ph_range': (4.8, 6.8), 'ideal_rain': 600, 'rain_range': (350, 1000), 'ideal_fert': 230, 'temp_range': (12, 24)},
    'Sugarcane': {'base_yield': 72.0, 'std_yield': 12.0, 'ideal_ph': 6.5, 'ph_range': (5.5, 7.8), 'ideal_rain': 1600, 'rain_range': (1000, 2500), 'ideal_fert': 280, 'temp_range': (22, 38)}
}

REGIONS = [
    'North America', 'South Asia', 'Sub-Saharan Africa', 'East Asia',
    'Latin America', 'Western Europe', 'Eastern Europe', 'Southeast Asia'
]

YEARS = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]

def generate_sensor_logs(count=3, base_ph=6.5, base_temp=22.0):
    """Generates synthetic embedded sensor reading sub-documents."""
    logs = []
    base_time = datetime.datetime(2025, 4, 1, 8, 0, 0)
    for i in range(count):
        log_time = base_time + datetime.timedelta(days=i * 30 + random.randint(1, 10))
        logs.append({
            "log_id": f"SENS-{random.randint(100000, 999999)}",
            "timestamp": log_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "soil_moisture_pct": round(max(10.0, min(90.0, random.gauss(48.0, 12.0))), 2),
            "ambient_temp_c": round(max(5.0, min(45.0, random.gauss(base_temp, 4.0))), 2),
            "ph_reading": round(max(4.0, min(9.0, random.gauss(base_ph, 0.2))), 2),
            "solar_radiation_wm2": round(max(100.0, min(1000.0, random.gauss(650.0, 150.0))), 1),
            "npk_index": round(random.uniform(0.4, 0.95), 2)
        })
    return logs

def generate_farm_records(num_records=20500):
    """Generates 20,000+ realistic farm documents with embedded sensor arrays."""
    print(f"Generating {num_records:,} farm documents based on FAO statistics & sensor arrays...")
    records = []
    
    for i in range(1, num_records + 1):
        farm_id = f"FARM-{i:06d}"
        crop = random.choice(list(CROP_PROFILES.keys()))
        profile = CROP_PROFILES[crop]
        region = random.choice(REGIONS)
        year = random.choice(YEARS)
        
        # Soil pH, Rainfall, Fertilizer
        soil_pH = round(random.uniform(profile['ph_range'][0], profile['ph_range'][1]), 2)
        rainfall = round(random.uniform(profile['rain_range'][0], profile['rain_range'][1]), 1)
        fertilizer_kg = round(max(20.0, random.gauss(profile['ideal_fert'], 45.0)), 1)
        
        # Calculate realistic yield influenced by conditions
        ph_dev = abs(soil_pH - profile['ideal_ph']) / profile['ideal_ph']
        rain_dev = abs(rainfall - profile['ideal_rain']) / profile['ideal_rain']
        fert_factor = min(1.3, fertilizer_kg / profile['ideal_fert'])
        
        yield_multiplier = max(0.4, (1.0 - (0.4 * ph_dev) - (0.3 * rain_dev)) * fert_factor)
        yield_tons = round(max(0.5, random.gauss(profile['base_yield'] * yield_multiplier, profile['std_yield'] * 0.4)), 2)
        
        avg_temp = (profile['temp_range'][0] + profile['temp_range'][1]) / 2.0
        sensor_logs = generate_sensor_logs(count=random.randint(2, 4), base_ph=soil_pH, base_temp=avg_temp)
        
        doc = {
            "farm_id": farm_id,
            "location": region,
            "crop_type": crop,
            "soil_pH": soil_pH,
            "rainfall": rainfall,
            "fertilizer_kg": fertilizer_kg,
            "yield_tons": yield_tons,
            "year": year,
            "sensor_logs": sensor_logs
        }
        records.append(doc)
        
        if i % 5000 == 0:
            print(f" Generated {i:,} records...")
            
    return records

def save_and_seed_mongodb(records):
    """Saves records to JSON file and seeds MongoDB database if available."""
    # 1. Save JSON
    print(f"Saving JSON dataset to {JSON_PATH}...")
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2)
    print(f"Saved {len(records):,} records to JSON file.")
    
    # 2. Try MongoDB seeding
    print("Attempting connection to local MongoDB instance (mongodb://localhost:27017)...")
    try:
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
        client.admin.command('ping')
        db = client['agricultural_db']
        collection = db['farms']
        
        # Clear existing and insert bulk
        collection.drop()
        collection.insert_many(records)
        
        # Create index on farm_id, location, crop_type
        collection.create_index([("farm_id", 1)], unique=True)
        collection.create_index([("crop_type", 1)])
        collection.create_index([("location", 1)])
        collection.create_index([("year", 1)])
        
        print(f" Successfully inserted {len(records):,} documents into MongoDB collection 'farms' in database 'agricultural_db'.")
        return True
    except Exception as e:
        print(f" MongoDB local server connection skipped ({e}). System will fall back to JSON dataset seamlessly.")
        return False

if __name__ == '__main__':
    data = generate_farm_records(20500)
    save_and_seed_mongodb(data)
