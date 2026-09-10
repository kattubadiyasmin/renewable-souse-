import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from models import db
from models.energy_data import EnergyReading

def detect_anomalies(limit=100):
    """
    Perform hybrid anomaly and energy wastage detection:
    1. Rule-Based Engine (Working hours, historical baselines, solar utilization, battery levels)
    2. Machine Learning Engine (Scikit-Learn IsolationForest)
    
    Returns a unified, prioritized list of alert objects.
    """
    # Fetch all readings ordered by date & time desc
    readings = EnergyReading.query.order_by(EnergyReading.date.desc(), EnergyReading.time.desc()).all()
    
    if not readings:
        return {
            "summary": {"total_alerts": 0, "high": 0, "medium": 0, "low": 0},
            "alerts": [],
            "ml_active": False,
            "message": "No energy data available for anomaly scanning."
        }

    # Prepare DataFrame
    records = [r.to_dict() for r in readings]
    df = pd.DataFrame(records)
    
    # Extract hour as integer
    df['hour'] = df['time'].apply(lambda t: int(t.split(':')[0]) if isinstance(t, str) and ':' in t else 0)

    # Compute building-level historical baseline stats
    building_stats = df.groupby('building_name')['energy_consumption'].agg(['mean', 'std']).reset_index()
    building_stats['std'] = building_stats['std'].fillna(1.0).apply(lambda s: max(s, 1.0)) # avoid std=0
    b_stat_map = {row['building_name']: (row['mean'], row['std']) for _, row in building_stats.iterrows()}

    # Night-time normal baselines for non-hostel
    night_mask = (df['hour'] < 8) | (df['hour'] >= 18)
    night_df = df[night_mask]
    night_building_means = night_df.groupby('building_name')['energy_consumption'].mean().to_dict()

    alerts_dict = {} # Keyed by reading id or (building, date, time) to prevent duplicates

    def add_alert(r_id, building, date, time, issue, severity, reason, recommendation, method):
        key = f"{building}_{date}_{time}"
        existing = alerts_dict.get(key)
        # Priority ranking: HIGH > MEDIUM > LOW
        sev_rank = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
        
        if existing:
            # Upgrade severity if new detection has higher severity
            if sev_rank.get(severity, 1) > sev_rank.get(existing['severity'], 1):
                existing['severity'] = severity
                existing['issue'] = issue
                existing['reason'] = reason
                existing['recommendation'] = recommendation
            if method not in existing['detection_method']:
                existing['detection_method'] = f"{existing['detection_method']} + {method}"
        else:
            alerts_dict[key] = {
                "id": r_id,
                "building": building,
                "date": date,
                "time": time,
                "issue": issue,
                "severity": severity,
                "reason": reason,
                "recommendation": recommendation,
                "detection_method": method
            }

    # =========================================================================
    # 1. RULE-BASED ENGINE
    # =========================================================================
    for _, row in df.iterrows():
        b_name = row['building_name']
        b_type = row['building_type']
        hour = row['hour']
        cons = row['energy_consumption']
        solar_gen = row['solar_generated']
        solar_used = row['solar_used']
        battery = row['battery_level']
        r_id = row['id']
        date_val = row['date']
        time_val = row['time']

        b_mean, b_std = b_stat_map.get(b_name, (cons, 1.0))
        z_score = (cons - b_mean) / b_std

        # Rule 1: High energy consumption outside normal working hours (8 AM - 6 PM)
        # (Hostel is residential so normal night usage is expected, but non-hostels shouldn't spike)
        is_off_hours = (hour < 8 or hour >= 18)
        if is_off_hours and b_name != "Hostel":
            night_baseline = night_building_means.get(b_name, b_mean * 0.3)
            if cons > night_baseline * 2.2 and cons > 25.0:
                severity = "HIGH" if (hour >= 23 or hour <= 4) or cons > night_baseline * 3.0 else "MEDIUM"
                add_alert(
                    r_id, b_name, date_val, time_val,
                    issue="High Off-Hours Energy Consumption",
                    severity=severity,
                    reason=f"Off-hours draw reached {cons:.1f} kWh at {time_val} (Normal off-hours average: {night_baseline:.1f} kWh).",
                    recommendation="Verify that air conditioning, computer rigs, and interior lighting were not left running unattended.",
                    method="Rule Engine"
                )

        # Rule 2: Unusually high building consumption (extreme statistical outlier)
        if z_score >= 2.4:
            severity = "HIGH" if z_score >= 3.0 else "MEDIUM"
            add_alert(
                r_id, b_name, date_val, time_val,
                issue="Severe Energy Consumption Spike",
                severity=severity,
                reason=f"Consumption of {cons:.1f} kWh is {z_score:.1f} standard deviations above the building normal average ({b_mean:.1f} kWh).",
                recommendation="Investigate mechanical equipment anomalies, concurrent machinery startup, or electrical fault.",
                method="Rule Engine"
            )
        elif z_score >= 1.8:
            add_alert(
                r_id, b_name, date_val, time_val,
                issue="Elevated Building Power Demand",
                severity="LOW",
                reason=f"Power demand reached {cons:.1f} kWh, exceeding typical building average ({b_mean:.1f} kWh).",
                recommendation="Monitor load trajectory and stagger non-critical appliance cycles.",
                method="Rule Engine"
            )

        # Rule 3: Low Solar Utilization
        # Solar generated is high (> 25 kWh) but solar used is very low (< 30% of gen)
        if solar_gen > 25.0 and solar_gen > 0:
            utilization = (solar_used / solar_gen) * 100.0
            if utilization < 30.0:
                add_alert(
                    r_id, b_name, date_val, time_val,
                    issue="Low Solar Energy Utilization",
                    severity="MEDIUM",
                    reason=f"High solar generation ({solar_gen:.1f} kWh) produced, but only {solar_used:.1f} kWh ({utilization:.1f}%) was utilized.",
                    recommendation="Reroute surplus solar energy to battery banks, campus water pumping, or adjacent building microgrids.",
                    method="Rule Engine"
                )

        # Rule 4: Low Battery Level
        if battery < 20.0:
            severity = "HIGH" if battery < 15.0 else "MEDIUM"
            add_alert(
                r_id, b_name, date_val, time_val,
                issue="Critical Low Battery Reserve",
                severity=severity,
                reason=f"Storage battery dropped to {battery:.1f}% (below 20.0% safety reserve threshold).",
                recommendation="Shed non-essential secondary loads immediately to preserve emergency operations.",
                method="Rule Engine"
            )

    # =========================================================================
    # 2. MACHINE LEARNING ENGINE: ISOLATION FOREST
    # =========================================================================
    ml_active = False
    if len(df) >= 30:
        try:
            features = ['energy_consumption', 'solar_generated', 'solar_used', 'battery_level', 'temperature']
            X = df[features].copy().fillna(0)

            # Contamination rate = 0.04 (approx top 4% multivariate anomalies)
            iso = IsolationForest(
                contamination=0.04,
                random_state=42,
                n_estimators=100
            )
            df['ml_anomaly'] = iso.fit_predict(X) # -1 is anomaly, 1 is normal
            df['ml_score'] = iso.decision_function(X) # lower score = more anomalous

            ml_anomalies = df[df['ml_anomaly'] == -1]
            ml_active = True

            for _, row in ml_anomalies.iterrows():
                b_name = row['building_name']
                cons = row['energy_consumption']
                sol_gen = row['solar_generated']
                sol_used = row['solar_used']
                batt = row['battery_level']
                temp = row['temperature']
                r_id = row['id']
                date_val = row['date']
                time_val = row['time']
                score = row['ml_score']

                # Categorize anomaly severity by ML outlier score
                severity = "HIGH" if score < -0.12 else ("MEDIUM" if score < -0.06 else "LOW")

                add_alert(
                    r_id, b_name, date_val, time_val,
                    issue="Multivariate Anomaly Detected by ML",
                    severity=severity,
                    reason=f"Isolation Forest identified abnormal multi-factor correlation (Cons: {cons:.1f} kWh, Solar: {sol_gen:.1f} kWh, Batt: {batt:.1f}%, Temp: {temp:.1f}°C, Anomaly score: {score:.3f}).",
                    recommendation="Review cross-subsystem telemetry for concurrent equipment anomalies or sensor calibration drift.",
                    method="IsolationForest ML"
                )
        except Exception as e:
            print(f"[WattWise Anomaly Engine] Isolation Forest warning: {e}. Falling back cleanly to Rule Engine.")
            ml_active = False

    # Convert alert dictionary to list and sort by severity (HIGH > MEDIUM > LOW) then date/time desc
    severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    alerts_list = list(alerts_dict.values())
    alerts_list.sort(key=lambda a: (severity_order.get(a['severity'], 3), a['date'], a['time']), reverse=False)

    # Calculate summary counts
    high_count = sum(1 for a in alerts_list if a['severity'] == "HIGH")
    med_count = sum(1 for a in alerts_list if a['severity'] == "MEDIUM")
    low_count = sum(1 for a in alerts_list if a['severity'] == "LOW")

    return {
        "summary": {
            "total_alerts": len(alerts_list),
            "high": high_count,
            "medium": med_count,
            "low": low_count
        },
        "alerts": alerts_list[:limit],
        "ml_active": ml_active,
        "total_records_scanned": len(df)
    }
