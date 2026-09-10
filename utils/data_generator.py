import os
import math
import random
from datetime import datetime, timedelta
import pandas as pd
from models import db
from models.energy_data import EnergyReading

BUILDINGS = [
    {"name": "Main Block", "type": "Academic", "base_energy": 28.0, "solar_capacity": 60.0},
    {"name": "Computer Lab", "type": "Laboratory", "base_energy": 35.0, "solar_capacity": 45.0},
    {"name": "Library", "type": "Library", "base_energy": 22.0, "solar_capacity": 40.0},
    {"name": "Administration Block", "type": "Administrative", "base_energy": 20.0, "solar_capacity": 35.0},
    {"name": "Hostel", "type": "Residential", "base_energy": 30.0, "solar_capacity": 30.0},
]

WEATHER_TYPES = ["Sunny", "Partly Cloudy", "Cloudy", "Rainy"]
WEATHER_WEIGHTS = [0.55, 0.25, 0.12, 0.08]

def get_solar_multiplier(hour, weather):
    """
    Realistic bell-curve solar generation based on hour of day (6 AM to 7 PM).
    Night hours (before 6 AM, after 7 PM) return 0.
    """
    if hour < 6 or hour >= 19:
        return 0.0
    
    # Peak is at 12.5 (12:30 PM)
    # Using Gaussian curve
    midday = 12.5
    spread = 2.8
    base_curve = math.exp(-0.5 * ((hour - midday) / spread) ** 2)
    
    # Weather degradation
    weather_factor = {
        "Sunny": 1.0,
        "Partly Cloudy": 0.75,
        "Cloudy": 0.40,
        "Rainy": 0.15
    }.get(weather, 0.8)
    
    return base_curve * weather_factor

def get_energy_multiplier(hour, building_name, is_weekend):
    """
    Realistic diurnal consumption pattern based on building type and time.
    """
    if building_name == "Hostel":
        # Residential pattern: high in morning (6-9 AM), low during day (students in class), high evening/night (6 PM-11 PM)
        if 0 <= hour < 6:
            mult = 0.45 + 0.05 * math.sin(hour)
        elif 6 <= hour < 9:
            mult = 1.25 + 0.15 * math.sin(hour)
        elif 9 <= hour < 17:
            mult = 0.55 + 0.10 * (1.3 if is_weekend else 0.8)
        elif 17 <= hour < 23:
            mult = 1.45 + 0.20 * math.sin(hour)
        else:
            mult = 0.85
    else:
        # Academic / Administrative / Lab / Library
        if is_weekend:
            # Low activity on weekends
            if 9 <= hour <= 17:
                mult = 0.35 + 0.05 * math.sin(hour)
            else:
                mult = 0.18
        else:
            # Weekday schedule
            if 0 <= hour < 7:
                # Night baseline (lights, standby, servers)
                mult = 0.20 + 0.05 * math.cos(hour)
            elif 7 <= hour < 9:
                # Morning ramp-up
                mult = 0.65 + 0.15 * (hour - 7)
            elif 9 <= hour < 13:
                # Late morning peak
                mult = 1.30 + 0.15 * math.sin(hour)
            elif 13 <= hour < 17:
                # Afternoon high peak (AC + labs + classes)
                mult = 1.40 + 0.10 * math.cos(hour)
            elif 17 <= hour < 20:
                # Evening drop-off
                mult = 0.70 - 0.15 * (hour - 17)
            else:
                # Late night minimal
                mult = 0.25

    return max(0.12, mult)

def get_temperature(hour, weather):
    """Generate realistic diurnal temperature profile (°C)."""
    # Minimum at 5 AM (~22°C), maximum at 2:30 PM (~34°C)
    daily_base = 28.0
    temp_variation = 6.0 * math.sin((hour - 8.5) * math.pi / 12)
    weather_offset = {
        "Sunny": 2.5,
        "Partly Cloudy": 0.5,
        "Cloudy": -2.0,
        "Rainy": -4.5
    }.get(weather, 0.0)
    
    return round(daily_base + temp_variation + weather_offset + random.uniform(-0.8, 0.8), 1)

def generate_sample_data(days=35):
    """
    Generate at least 30+ days of realistic campus energy data across 5 buildings.
    Generates data up to the current date with realistic time-based patterns and anomalies.
    Returns list of dicts.
    """
    records = []
    # Seed for realistic consistency
    random.seed(42)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    current_date = start_date
    
    # State tracking for battery simulation
    building_battery = {b["name"]: 65.0 for b in BUILDINGS}
    
    anomaly_count = 0

    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        day_of_week = current_date.weekday() # 0 = Monday, 6 = Sunday
        is_weekend = (day_of_week >= 5)
        
        # Weather for the day with smooth transitions
        daily_weather = random.choices(WEATHER_TYPES, weights=WEATHER_WEIGHTS)[0]
        
        # Sample every 2 hours: 00:00, 02:00, 04:00, ..., 22:00
        for hour in range(0, 24, 2):
            time_str = f"{hour:02d}:00:00"
            temp = get_temperature(hour, daily_weather)
            
            # Weather might slightly vary in afternoon/evening
            current_weather = daily_weather
            if daily_weather == "Rainy" and hour < 8:
                current_weather = "Cloudy"

            solar_mult = get_solar_multiplier(hour, current_weather)

            for b in BUILDINGS:
                b_name = b["name"]
                b_type = b["type"]
                base_e = b["base_energy"]
                solar_cap = b["solar_capacity"]
                
                # Base consumption calculation
                e_mult = get_energy_multiplier(hour, b_name, is_weekend)
                consumption = round(base_e * e_mult * random.uniform(0.92, 1.08), 2)
                
                # Solar generation calculation
                # Cap varies slightly by building orientation & roof efficiency
                solar_gen = round(solar_cap * solar_mult * random.uniform(0.90, 1.05), 2) if solar_mult > 0 else 0.0
                
                # Calculate realistic solar used:
                # Can only use what is generated and what the building or shared microgrid absorbs
                if solar_gen > 0:
                    # Building directly uses solar up to its consumption or microgrid battery buffer
                    max_usable = min(solar_gen, consumption * random.uniform(0.75, 0.95))
                    solar_used = round(max_usable, 2)
                else:
                    solar_used = 0.0
                
                # Battery charge / discharge simulation
                curr_batt = building_battery[b_name]
                if solar_gen > solar_used:
                    # Excess solar charges battery
                    surplus = solar_gen - solar_used
                    charge = surplus * 0.45
                    curr_batt = min(98.0, curr_batt + charge)
                else:
                    # Deficit discharges battery
                    deficit = max(0.0, consumption - solar_used)
                    discharge = deficit * 0.22
                    curr_batt = max(12.0, curr_batt - discharge)
                
                # Settle battery with small noise
                building_battery[b_name] = round(curr_batt, 1)

                # ===================================================
                # SEED REALISTIC DETECTABLE ANOMALIES
                # ===================================================
                
                # Anomaly 1: Computer Lab midnight AC/Rig energy spike (Outside working hours)
                # Specific nights (e.g. Day 7, 14, 21, 28 at 02:00 or 04:00)
                if b_name == "Computer Lab" and hour in [2, 4] and random.random() < 0.18:
                    consumption = round(base_e * 2.8 * random.uniform(1.1, 1.3), 2) # e.g. ~48-55 kWh instead of 7 kWh
                    anomaly_count += 1
                
                # Anomaly 2: Administration Block weekend / late night lights and equipment left on
                if b_name == "Administration Block" and is_weekend and hour in [20, 22] and random.random() < 0.15:
                    consumption = round(base_e * 2.1 * random.uniform(1.1, 1.25), 2)
                    anomaly_count += 1

                # Anomaly 3: Low Solar Utilization anomaly (High solar generation 50-70 kWh, but solar used is only ~6 kWh)
                if solar_gen > 40.0 and hour in [12, 14] and random.random() < 0.08:
                    solar_used = round(solar_gen * random.uniform(0.12, 0.22), 2) # Low utilization!
                    anomaly_count += 1

                # Anomaly 4: Battery critical drop (< 20%) after extended cloudy/rainy spell
                if current_weather in ["Cloudy", "Rainy"] and random.random() < 0.07:
                    curr_batt = round(random.uniform(13.0, 19.5), 1)
                    building_battery[b_name] = curr_batt
                    anomaly_count += 1

                # Safety: ensure solar_used <= solar_generated
                solar_used = min(solar_used, solar_gen)

                records.append({
                    "date": date_str,
                    "time": time_str,
                    "building_name": b_name,
                    "building_type": b_type,
                    "energy_consumption": consumption,
                    "solar_generated": solar_gen,
                    "solar_used": solar_used,
                    "battery_level": round(curr_batt, 1),
                    "temperature": temp,
                    "weather_condition": current_weather
                })

        current_date += timedelta(days=1)
        
    return records

def init_sample_data(app, force=False):
    """
    Initialize sample energy data in database and sample CSV file.
    Runs on startup if table is empty or force=True.
    """
    data_dir = os.path.join(app.config['BASE_DIR'], 'data')
    os.makedirs(data_dir, exist_ok=True)
    csv_file_path = os.path.join(data_dir, 'sample_energy_data.csv')

    with app.app_context():
        # Check current count
        count = EnergyReading.query.count()
        if count < 50 or force:
            print(f"[WattWise] Database currently has {count} records. Generating 35 days of realistic data...")
            records = generate_sample_data(days=35)
            
            # 1. Save to SQLite database
            db_objects = [
                EnergyReading(
                    date=r['date'],
                    time=r['time'],
                    building_name=r['building_name'],
                    building_type=r['building_type'],
                    energy_consumption=r['energy_consumption'],
                    solar_generated=r['solar_generated'],
                    solar_used=r['solar_used'],
                    battery_level=r['battery_level'],
                    temperature=r['temperature'],
                    weather_condition=r['weather_condition']
                ) for r in records
            ]
            
            db.session.bulk_save_objects(db_objects)
            db.session.commit()
            print(f"[WattWise] Successfully seeded {len(db_objects)} energy records into SQLite database.")
            
            # 2. Save to data/sample_energy_data.csv for downloads and tests
            df = pd.DataFrame(records)
            df.to_csv(csv_file_path, index=False)
            print(f"[WattWise] Created sample CSV at {csv_file_path}")
        else:
            # Ensure the CSV file exists if DB was already populated
            if not os.path.exists(csv_file_path):
                records = generate_sample_data(days=10)
                df = pd.DataFrame(records)
                df.to_csv(csv_file_path, index=False)
                print(f"[WattWise] Ensured sample CSV at {csv_file_path}")
            print(f"[WattWise] Database already contains {count} records. Seeding skipped.")
