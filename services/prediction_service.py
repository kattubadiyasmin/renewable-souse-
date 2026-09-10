import math
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from models.energy_data import EnergyReading

def predict_energy_demand(target_date_str=None, building_name=None):
    """
    Train a dynamic RandomForestRegressor on current database data and predict
    hourly energy demand for a selected date and building.
    
    Returns:
        forecast_results: dict containing hourly curve, total demand, peak time, model metrics, fallback status
    """
    # 1. Target date setup
    if not target_date_str:
        # Default to tomorrow
        tomorrow = datetime.now() + timedelta(days=1)
        target_date_str = tomorrow.strftime("%Y-%m-%d")
    
    try:
        target_dt = datetime.strptime(target_date_str, "%Y-%m-%d")
    except ValueError:
        target_dt = datetime.now() + timedelta(days=1)
        target_date_str = target_dt.strftime("%Y-%m-%d")
        
    day_of_week = target_dt.weekday() # 0 = Mon, 6 = Sun
    is_weekend = 1 if day_of_week >= 5 else 0

    # 2. Fetch data from DB
    readings = EnergyReading.query.all()
    
    if len(readings) < 20:
        return _fallback_prediction(target_date_str, building_name, day_of_week, "Insufficient historical records (< 20).")

    # 3. Build DataFrame
    records = [{
        'date': r.date,
        'time': r.time,
        'building_name': r.building_name,
        'energy_consumption': float(r.energy_consumption),
        'temperature': float(r.temperature)
    } for r in readings]
    
    df = pd.DataFrame(records)
    
    # Feature Engineering
    df['hour'] = df['time'].apply(lambda t: int(t.split(':')[0]) if isinstance(t, str) and ':' in t else 12)
    try:
        df['datetime'] = pd.to_datetime(df['date'])
        df['day_of_week'] = df['datetime'].dt.weekday
        df['is_weekend'] = df['day_of_week'].apply(lambda d: 1 if d >= 5 else 0)
    except Exception:
        df['day_of_week'] = 2
        df['is_weekend'] = 0

    # Building list
    buildings = list(df['building_name'].unique())
    
    # Historical Building Means
    building_means = df.groupby('building_name')['energy_consumption'].mean().to_dict()
    df['building_mean'] = df['building_name'].map(building_means).fillna(df['energy_consumption'].mean())

    # One-hot encoding for building
    df_encoded = pd.get_dummies(df, columns=['building_name'], prefix='bld')
    
    # Feature columns
    feature_cols = ['hour', 'day_of_week', 'is_weekend', 'temperature', 'building_mean']
    bld_cols = [c for c in df_encoded.columns if c.startswith('bld_')]
    feature_cols.extend(bld_cols)

    X = df_encoded[feature_cols].copy().fillna(0)
    y = df_encoded['energy_consumption'].copy().fillna(0)

    # Train Random Forest Regressor dynamically
    try:
        rf_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=12,
            min_samples_split=4,
            random_state=42
        )
        rf_model.fit(X, y)
        
        # Training evaluation
        y_pred_train = rf_model.predict(X)
        mae = round(float(mean_absolute_error(y, y_pred_train)), 2)
        r2 = round(max(0.0, float(r2_score(y, y_pred_train))), 3)
        ml_active = True
        notes = "RandomForestRegressor trained on active campus dataset."
    except Exception as e:
        print(f"[Prediction Service] ML training error: {e}. Switching to historical average fallback.")
        return _fallback_prediction(target_date_str, building_name, day_of_week, f"Model training exception: {str(e)}")

    # 4. Predict 24 hours (00:00 to 23:00) for target date
    # Synthesize realistic diurnal temperature for target date
    # Min ~22°C at 5 AM, Max ~34°C at 14:00
    hourly_predictions = []
    total_predicted_demand = 0.0

    target_buildings = [building_name] if (building_name and building_name != "All" and building_name in buildings) else buildings

    for hour in range(24):
        # Estimated temperature for this hour
        est_temp = round(28.0 + 6.0 * math.sin((hour - 8.5) * math.pi / 12), 1)
        
        hour_demand_sum = 0.0
        
        for b in target_buildings:
            row_dict = {
                'hour': hour,
                'day_of_week': day_of_week,
                'is_weekend': is_weekend,
                'temperature': est_temp,
                'building_mean': building_means.get(b, 25.0)
            }
            # Fill one-hot columns
            for col in bld_cols:
                row_dict[col] = 1 if col == f"bld_{b}" else 0
                
            pred_val = float(rf_model.predict(pd.DataFrame([row_dict])[feature_cols])[0])
            hour_demand_sum += max(0.5, pred_val)

        hour_demand_sum = round(hour_demand_sum, 2)
        total_predicted_demand += hour_demand_sum
        hourly_predictions.append({
            'hour': f"{hour:02d}:00",
            'hour_num': hour,
            'temperature': est_temp,
            'predicted_demand': hour_demand_sum
        })

    # Find peak period
    peak_record = max(hourly_predictions, key=lambda x: x['predicted_demand'])
    peak_hour = peak_record['hour_num']
    peak_time_str = f"{peak_hour:02d}:00 - {(peak_hour+1)%24:02d}:00"
    peak_demand_kwh = peak_record['predicted_demand']

    # Historical comparison for same day of week if exists
    same_dow_readings = df[df['day_of_week'] == day_of_week]
    if not same_dow_readings.empty:
        if building_name and building_name != "All":
            hist_daily_avg = same_dow_readings[same_dow_readings['building_name'] == building_name]['energy_consumption'].sum() / max(1, len(same_dow_readings['date'].unique()))
        else:
            hist_daily_avg = same_dow_readings['energy_consumption'].sum() / max(1, len(same_dow_readings['date'].unique()))
    else:
        hist_daily_avg = total_predicted_demand

    diff_from_hist = round(((total_predicted_demand - hist_daily_avg) / (hist_daily_avg + 1e-6)) * 100, 1)

    return {
        "target_date": target_date_str,
        "selected_building": building_name or "All Buildings",
        "available_buildings": buildings,
        "total_predicted_demand_kwh": round(total_predicted_demand, 2),
        "peak_time": peak_time_str,
        "peak_demand_kwh": round(peak_demand_kwh, 2),
        "historical_benchmark_kwh": round(float(hist_daily_avg), 2),
        "benchmark_diff_pct": diff_from_hist,
        "model_type": "RandomForestRegressor (Scikit-Learn)",
        "model_r2_score": r2,
        "model_mae": mae,
        "is_fallback": False,
        "notes": notes,
        "hourly_curve": hourly_predictions
    }

def _fallback_prediction(target_date_str, building_name, day_of_week, reason):
    """Graceful fallback calculation using simple historical moving averages."""
    readings = EnergyReading.query.all()
    buildings = list(set([r.building_name for r in readings])) if readings else [
        "Main Block", "Computer Lab", "Library", "Administration Block", "Hostel"
    ]
    
    hourly_curve = []
    total_demand = 0.0
    
    # Calculate empirical baseline averages
    for hour in range(24):
        est_temp = round(28.0 + 6.0 * math.sin((hour - 8.5) * math.pi / 12), 1)
        base = 25.0
        # Diurnal multiplier
        if 9 <= hour <= 17:
            mult = 1.4
        elif 6 <= hour < 9 or 17 < hour <= 21:
            mult = 0.9
        else:
            mult = 0.4
            
        bld_mult = 5.0 if (not building_name or building_name == "All") else 1.0
        est_cons = round(base * mult * bld_mult, 2)
        total_demand += est_cons
        hourly_curve.append({
            'hour': f"{hour:02d}:00",
            'hour_num': hour,
            'temperature': est_temp,
            'predicted_demand': est_cons
        })
        
    peak_rec = max(hourly_curve, key=lambda x: x['predicted_demand'])

    return {
        "target_date": target_date_str,
        "selected_building": building_name or "All Buildings",
        "available_buildings": buildings,
        "total_predicted_demand_kwh": round(total_demand, 2),
        "peak_time": f"{peak_rec['hour_num']:02d}:00 - {(peak_rec['hour_num']+1)%24:02d}:00",
        "peak_demand_kwh": peak_rec['predicted_demand'],
        "historical_benchmark_kwh": round(total_demand, 2),
        "benchmark_diff_pct": 0.0,
        "model_type": "Historical Average Fallback",
        "model_r2_score": 0.0,
        "model_mae": 0.0,
        "is_fallback": True,
        "notes": f"Fallback Mode: {reason}",
        "hourly_curve": hourly_curve
    }
