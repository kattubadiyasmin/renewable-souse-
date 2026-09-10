import os
import io
import math
import random
from datetime import datetime
import pandas as pd
from flask import Blueprint, jsonify, request, send_file, current_app
from werkzeug.utils import secure_filename
from models import db
from models.energy_data import EnergyReading
from utils.validators import validate_energy_data, ALLOWED_BUILDINGS, BUILDING_TYPE_MAP, ALLOWED_WEATHER
from utils.data_generator import get_solar_multiplier, get_energy_multiplier, get_temperature, init_sample_data
from services.analytics_service import get_analytics_data
from services.anomaly_service import detect_anomalies
from services.prediction_service import predict_energy_demand
from services.solar_service import get_solar_analysis
from services.recommendation_service import generate_smart_recommendations

api_bp = Blueprint('api', __name__)

@api_bp.route('/dashboard', methods=['GET'])
def api_dashboard():
    """Returns top-level dashboard metrics and charts data."""
    try:
        analytics = get_analytics_data()
        alerts_data = detect_anomalies(limit=5)
        
        return jsonify({
            "status": "success",
            "kpis": {
                "total_consumption": analytics["total_consumption"],
                "total_solar_generated": analytics["total_solar_generated"],
                "total_solar_used": analytics["total_solar_used"],
                "renewable_contribution_pct": analytics["renewable_contribution_pct"],
                "efficiency_score": analytics["efficiency_score"],
                "active_wastage_alerts": alerts_data["summary"]["total_alerts"],
                "high_severity_alerts": alerts_data["summary"]["high"]
            },
            "charts": {
                "daily_trends": analytics["daily_trends"],
                "hourly_trends": analytics["hourly_trends"],
                "building_breakdown": analytics["building_breakdown"]
            },
            "recent_alerts": alerts_data["alerts"][:5],
            "insights": analytics["dynamic_insights"][:3]
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@api_bp.route('/analytics', methods=['GET'])
def api_analytics():
    """Returns detailed energy analytics with optional filters."""
    try:
        building = request.args.get('building', None)
        date_from = request.args.get('date_from', None)
        date_to = request.args.get('date_to', None)
        
        analytics = get_analytics_data(building_filter=building, date_from=date_from, date_to=date_to)
        return jsonify({"status": "success", "data": analytics})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@api_bp.route('/alerts', methods=['GET'])
def api_alerts():
    """Returns detected anomalies and energy wastage alerts."""
    try:
        limit = int(request.args.get('limit', 100))
        result = detect_anomalies(limit=limit)
        return jsonify({"status": "success", "data": result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@api_bp.route('/prediction', methods=['GET'])
def api_prediction():
    """Returns machine learning demand forecasts."""
    try:
        target_date = request.args.get('date', None)
        building = request.args.get('building', None)
        
        forecast = predict_energy_demand(target_date_str=target_date, building_name=building)
        return jsonify({"status": "success", "data": forecast})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@api_bp.route('/solar', methods=['GET'])
def api_solar():
    """Returns solar analysis metrics and hourly solar curves."""
    try:
        solar_data = get_solar_analysis()
        return jsonify({"status": "success", "data": solar_data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@api_bp.route('/recommendations', methods=['GET'])
def api_recommendations():
    """Returns dynamic rule-based smart recommendations."""
    try:
        recs = generate_smart_recommendations()
        return jsonify({"status": "success", "data": recs})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@api_bp.route('/energy', methods=['POST'])
def api_add_energy():
    """Add a single energy reading into the database."""
    try:
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()

        is_valid, cleaned, errors = validate_energy_data(data)
        if not is_valid:
            return jsonify({
                "status": "fail",
                "message": "Validation failed.",
                "errors": errors
            }), 400

        # Save to database
        reading = EnergyReading(
            date=cleaned['date'],
            time=cleaned['time'],
            building_name=cleaned['building_name'],
            building_type=cleaned['building_type'],
            energy_consumption=cleaned['energy_consumption'],
            solar_generated=cleaned['solar_generated'],
            solar_used=cleaned['solar_used'],
            battery_level=cleaned['battery_level'],
            temperature=cleaned['temperature'],
            weather_condition=cleaned['weather_condition']
        )
        db.session.add(reading)
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Energy reading saved successfully.",
            "data": reading.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@api_bp.route('/upload', methods=['POST'])
def api_upload_csv():
    """Process uploaded CSV dataset using pandas, validate, and batch insert."""
    if 'file' not in request.files:
        return jsonify({"status": "fail", "message": "No file uploaded in the request."}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "fail", "message": "No file selected."}), 400

    if not file.filename.lower().endswith('.csv'):
        return jsonify({"status": "fail", "message": "Invalid file format. Only CSV files (.csv) are accepted."}), 400

    try:
        # Read into memory using Pandas
        stream = io.StringIO(file.stream.read().decode("utf-8-sig", errors="replace"), newline=None)
        df = pd.read_csv(stream)

        # Expected columns check
        required_cols = [
            'date', 'time', 'building_name', 'building_type',
            'energy_consumption', 'solar_generated', 'solar_used',
            'battery_level', 'temperature', 'weather_condition'
        ]
        
        # Normalize column names
        df.columns = [str(c).strip().lower().replace(' ', '_') for c in df.columns]
        missing_cols = [c for c in required_cols if c not in df.columns]
        
        if missing_cols:
            return jsonify({
                "status": "fail",
                "message": f"CSV is missing required columns: {', '.join(missing_cols)}",
                "expected_columns": required_cols
            }), 400

        total_rows = len(df)
        if total_rows == 0:
            return jsonify({"status": "fail", "message": "The uploaded CSV file is empty."}), 400

        valid_objects = []
        skipped_errors = []

        for idx, row in df.iterrows():
            row_dict = row.to_dict()
            is_valid, cleaned, errors = validate_energy_data(row_dict)
            if is_valid:
                valid_objects.append(EnergyReading(
                    date=cleaned['date'],
                    time=cleaned['time'],
                    building_name=cleaned['building_name'],
                    building_type=cleaned['building_type'],
                    energy_consumption=cleaned['energy_consumption'],
                    solar_generated=cleaned['solar_generated'],
                    solar_used=cleaned['solar_used'],
                    battery_level=cleaned['battery_level'],
                    temperature=cleaned['temperature'],
                    weather_condition=cleaned['weather_condition']
                ))
            else:
                skipped_errors.append({
                    "row_number": idx + 2, # +2 for 1-based index and header
                    "errors": errors
                })

        # Save valid records in bulk
        if valid_objects:
            db.session.bulk_save_objects(valid_objects)
            db.session.commit()

        return jsonify({
            "status": "success",
            "message": f"Import completed. Successfully imported {len(valid_objects)} records.",
            "total_rows_in_file": total_rows,
            "imported_count": len(valid_objects),
            "skipped_count": len(skipped_errors),
            "skipped_details": skipped_errors[:10] # show top 10 errors if any
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Error parsing CSV dataset: {str(e)}"}), 500

@api_bp.route('/live', methods=['GET'])
def api_live_reading():
    """
    Generate physics-based realistic live campus readings based on the current hour.
    Supports optional query parameters:
      - building: building name
      - force_anomaly: 'true' or 'false'
    """
    now = datetime.now()
    hour = now.hour
    
    building = request.args.get('building', random.choice(ALLOWED_BUILDINGS))
    if building not in ALLOWED_BUILDINGS:
        building = "Main Block"
        
    force_anomaly = request.args.get('force_anomaly', 'false').lower() == 'true'

    # Weather determination
    weather = request.args.get('weather', random.choice(ALLOWED_WEATHER))
    is_weekend = (now.weekday() >= 5)

    # Physics-based generation
    solar_mult = get_solar_multiplier(hour, weather)
    e_mult = get_energy_multiplier(hour, building, is_weekend)
    temp = get_temperature(hour, weather)

    base_configs = {
        "Main Block": {"base": 28.0, "solar_cap": 60.0, "type": "Academic"},
        "Computer Lab": {"base": 35.0, "solar_cap": 45.0, "type": "Laboratory"},
        "Library": {"base": 22.0, "solar_cap": 40.0, "type": "Library"},
        "Administration Block": {"base": 20.0, "solar_cap": 35.0, "type": "Administrative"},
        "Hostel": {"base": 30.0, "solar_cap": 30.0, "type": "Residential"},
    }
    cfg = base_configs.get(building, {"base": 25.0, "solar_cap": 40.0, "type": "Academic"})

    consumption = round(cfg["base"] * e_mult * random.uniform(0.95, 1.05), 2)
    solar_gen = round(cfg["solar_cap"] * solar_mult * random.uniform(0.95, 1.05), 2) if solar_mult > 0 else 0.0
    
    if solar_gen > 0:
        solar_used = round(min(solar_gen, consumption * random.uniform(0.75, 0.95)), 2)
    else:
        solar_used = 0.0

    battery_level = round(random.uniform(55.0, 92.0), 1)

    is_anomaly = False
    anomaly_msg = ""
    
    # Anomaly injection if forced or random 10% chance
    if force_anomaly or (random.random() < 0.10 and (hour < 8 or hour > 18)):
        is_anomaly = True
        if hour < 8 or hour > 18:
            consumption = round(cfg["base"] * 2.8, 2)
            anomaly_msg = f"Abnormal High Off-Hours Consumption ({consumption} kWh) in {building} outside regular schedule!"
        elif solar_gen > 25:
            solar_used = round(solar_gen * 0.15, 2) # low utilization
            anomaly_msg = f"Low Solar Absorption: {solar_gen} kWh generated but only {solar_used} kWh utilized!"
        else:
            battery_level = 16.4
            anomaly_msg = f"Battery Reserve Warning: Dropped to {battery_level}% (Critical Load Threshold)!"

    # Ensure constraints
    solar_used = min(solar_used, solar_gen)

    live_data = {
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "building_name": building,
        "building_type": cfg["type"],
        "energy_consumption": consumption,
        "solar_generated": solar_gen,
        "solar_used": solar_used,
        "battery_level": battery_level,
        "temperature": temp,
        "weather_condition": weather,
        "is_anomaly": is_anomaly,
        "anomaly_message": anomaly_msg,
        "system_status": "ONLINE - LIVE SIMULATION ACTIVE"
    }

    return jsonify({"status": "success", "data": live_data})

@api_bp.route('/live/save', methods=['POST'])
def api_live_save():
    """Save the current live reading into the SQLite database."""
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        is_valid, cleaned, errors = validate_energy_data(data)
        
        if not is_valid:
            return jsonify({"status": "fail", "errors": errors}), 400
            
        reading = EnergyReading(
            date=cleaned['date'],
            time=cleaned['time'],
            building_name=cleaned['building_name'],
            building_type=cleaned['building_type'],
            energy_consumption=cleaned['energy_consumption'],
            solar_generated=cleaned['solar_generated'],
            solar_used=cleaned['solar_used'],
            battery_level=cleaned['battery_level'],
            temperature=cleaned['temperature'],
            weather_condition=cleaned['weather_condition']
        )
        db.session.add(reading)
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Live reading successfully committed to SQLite database.",
            "data": reading.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@api_bp.route('/sample-csv', methods=['GET'])
def api_sample_csv():
    """Download the sample CSV file for users and testing."""
    csv_path = os.path.join(current_app.config['BASE_DIR'], 'data', 'sample_energy_data.csv')
    if not os.path.exists(csv_path):
        # Generate on the fly
        init_sample_data(current_app, force=True)
        
    return send_file(
        csv_path,
        mimetype='text/csv',
        as_attachment=True,
        download_name='wattwise_sample_energy_data.csv'
    )

@api_bp.route('/reset-data', methods=['POST'])
def api_reset_sample_data():
    """Reset database and re-seed 35 days of fresh realistic data for judges."""
    try:
        EnergyReading.query.delete()
        db.session.commit()
        init_sample_data(current_app, force=True)
        return jsonify({
            "status": "success",
            "message": "Database successfully reset and re-seeded with 35 days of realistic data."
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
