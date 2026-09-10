import pandas as pd
from models.energy_data import EnergyReading
from services.analytics_service import get_analytics_data
from services.anomaly_service import detect_anomalies

def generate_smart_recommendations():
    """
    Generate dynamic rule-based intelligent recommendations based on real campus energy data,
    solar utilization metrics, and detected anomalies.
    """
    readings = EnergyReading.query.all()
    if not readings:
        return {
            "total_recommendations": 0,
            "high_priority_count": 0,
            "recommendations": [],
            "message": "No energy data available to generate recommendations."
        }

    records = [{
        'building_name': r.building_name,
        'energy_consumption': float(r.energy_consumption),
        'solar_generated': float(r.solar_generated),
        'solar_used': float(r.solar_used),
        'battery_level': float(r.battery_level),
        'time': r.time
    } for r in readings]

    df = pd.DataFrame(records)
    df['hour'] = df['time'].apply(lambda t: int(t.split(':')[0]) if isinstance(t, str) and ':' in t else 12)

    total_gen = float(df['solar_generated'].sum())
    total_used = float(df['solar_used'].sum())
    total_cons = float(df['energy_consumption'].sum())
    
    solar_utilization = round((total_used / total_gen * 100), 1) if total_gen > 0 else 0.0
    unused_solar_kwh = max(0.0, total_gen - total_used)
    
    # Off hours check (8 PM to 5 AM)
    night_df = df[(df['hour'] >= 20) | (df['hour'] <= 5)]
    non_hostel_night = night_df[night_df['building_name'] != 'Hostel']
    night_cons_avg = float(non_hostel_night['energy_consumption'].mean()) if not non_hostel_night.empty else 0.0

    # Low battery incidents
    low_battery_count = int((df['battery_level'] < 20.0).sum())
    min_battery = float(df['battery_level'].min()) if not df.empty else 50.0

    # Building breakdown
    bld_sums = df.groupby('building_name')['energy_consumption'].sum()
    top_building = bld_sums.idxmax() if not bld_sums.empty else "Main Block"
    top_bld_share = round((bld_sums.max() / total_cons * 100), 1) if total_cons > 0 else 0.0

    # Get anomalies for cross-validation
    anomaly_result = detect_anomalies(limit=10)
    high_alerts_count = anomaly_result['summary']['high']

    recommendations = []

    # =========================================================================
    # RULE 1: Solar Utilization & Load Shifting
    # =========================================================================
    if solar_utilization < 75.0 and unused_solar_kwh > 50:
        recommendations.append({
            "id": "REC-SOLAR-01",
            "title": "Shift Flexible Campus Loads to Peak Solar Window",
            "category": "Load Shifting",
            "priority": "HIGH" if solar_utilization < 50 else "MEDIUM",
            "icon": "fa-sun",
            "trigger_reason": f"Current solar utilization is {solar_utilization}%, resulting in {unused_solar_kwh:,.1f} kWh of unutilized clean solar energy during midday hours.",
            "action_plan": [
                "Reschedule heavy equipment operations (central water pumping, EV charging docks, laboratory autoclave cycles) to between 11:00 AM and 2:30 PM.",
                "Program thermal pre-cooling in academic blocks to store cold thermal energy using midday solar surplus.",
                "Review inverter export throttle limits and evaluate battery storage expansion."
            ],
            "estimated_impact": f"Can capture up to {round(unused_solar_kwh * 0.45, 1):,.1f} kWh of curtailed clean energy and reduce peak grid tariff costs by 15-25%."
        })
    else:
        recommendations.append({
            "id": "REC-SOLAR-02",
            "title": "Maintain High Solar Direct-Consumption Alignment",
            "category": "Clean Energy",
            "priority": "INFO",
            "icon": "fa-solar-panel",
            "trigger_reason": f"Strong solar utilization achieved at {solar_utilization}%. Most solar power is directly absorbed by daytime campus loads.",
            "action_plan": [
                "Conduct routine bi-weekly photovoltaic panel cleaning to prevent dust soiling losses.",
                "Check rooftop inverter phase balance across academic buildings."
            ],
            "estimated_impact": "Maintains 95%+ photovoltaic operational efficiency."
        })

    # =========================================================================
    # RULE 2: Off-Hours Energy Wastage Mitigation
    # =========================================================================
    if night_cons_avg > 15.0 or high_alerts_count > 0:
        recommendations.append({
            "id": "REC-WASTE-01",
            "title": "Implement Automated Equipment Shutdown Outside Working Hours",
            "category": "Wastage Mitigation",
            "priority": "HIGH",
            "icon": "fa-moon",
            "trigger_reason": f"Non-residential buildings draw an average of {night_cons_avg:.1f} kWh per reading between 8:00 PM and 5:00 AM, indicating equipment left running idle.",
            "action_plan": [
                "Install automated smart timer switches and occupancy sensors on lighting and HVAC circuits in Academic and Administration blocks.",
                "Enforce network-wide PC sleep policies in Computer Labs at 7:00 PM.",
                "Conduct nightly security rounds to ensure split-system air conditioning units are powered off."
            ],
            "estimated_impact": f"Reduces phantom overnight energy consumption by up to {min(40, round(night_cons_avg * 1.8, 1))}%, saving thousands of kWh monthly."
        })

    # =========================================================================
    # RULE 3: Battery Reserve & Resilience Management
    # =========================================================================
    if low_battery_count > 0 or min_battery < 20.0:
        recommendations.append({
            "id": "REC-BATT-01",
            "title": "Enforce Critical Load Shedding Under Low Battery States",
            "category": "Storage Optimization",
            "priority": "HIGH",
            "icon": "fa-battery-quarter",
            "trigger_reason": f"Battery storage dipped below safety reserve threshold (minimum recorded: {min_battery:.1f}%), risking inverter blackout during grid interruptions.",
            "action_plan": [
                "Program automated load shedding: isolate non-critical loads (hallway display monitors, aesthetic lighting) when battery level drops below 25%.",
                "Keep essential circuits (campus server rooms, emergency lighting, perimeter security) on a dedicated protected sub-bus.",
                "Review battery state-of-charge charge controller algorithms during cloudy weather."
            ],
            "estimated_impact": "Extends critical campus backup runtime by 35-50% during grid outages and prolongs battery pack life cycle."
        })
    else:
        recommendations.append({
            "id": "REC-BATT-02",
            "title": "Healthy Battery Storage Buffering",
            "category": "Storage Optimization",
            "priority": "INFO",
            "icon": "fa-battery-full",
            "trigger_reason": f"Storage batteries are operating within safe operating margins (minimum reserve observed: {min_battery:.1f}%).",
            "action_plan": [
                "Maintain depth of discharge (DoD) above 20% to maximize lithium/lead cycle life.",
                "Ensure battery enclosure ambient temperature remains below 28°C."
            ],
            "estimated_impact": "Preserves battery lifespan up to 8+ years."
        })

    # =========================================================================
    # RULE 4: Heavy Consumer Building Peak Shaving
    # =========================================================================
    if top_bld_share > 25.0:
        recommendations.append({
            "id": "REC-PEAK-01",
            "title": f"Targeted Peak Shaving for {top_building}",
            "category": "Peak Shaving",
            "priority": "MEDIUM",
            "icon": "fa-building",
            "trigger_reason": f"{top_building} is the single largest consumer on campus, accounting for {top_bld_share}% of total electricity demand.",
            "action_plan": [
                f"Audit HVAC chiller sets and laboratory computer stations specifically in {top_building}.",
                "Stagger lecture hall air conditioning starts by 15-minute intervals between 8:30 AM and 9:30 AM to eliminate simultaneous startup demand spikes.",
                "Upgrade existing fluorescent fixtures to high-efficacy LED fittings with daylight harvesting sensors."
            ],
            "estimated_impact": f"Can shave building peak demand by 12-18% and smooth campus grid load factor."
        })

    # =========================================================================
    # RULE 5: Microgrid Inter-Building Power Sharing
    # =========================================================================
    recommendations.append({
        "id": "REC-GRID-01",
        "title": "Enable Inter-Building Microgrid Power Routing",
        "category": "Campus Microgrid",
        "priority": "MEDIUM",
        "icon": "fa-network-wired",
        "trigger_reason": "Academic blocks generate excess rooftop solar at midday while Hostel consumption surges in evening hours.",
        "action_plan": [
            "Couple rooftop solar from Academic Block and Library to charge central microgrid battery banks.",
            "Discharge stored clean power to the Hostel during its evening residential peak (6:00 PM - 10:00 PM).",
            "Implement automated directional energy meters between campus distribution feeders."
        ],
        "estimated_impact": "Boosts net campus renewable self-sufficiency from 38% to over 55% without purchasing additional panels."
    })

    high_pri_count = sum(1 for r in recommendations if r['priority'] == "HIGH")

    return {
        "total_recommendations": len(recommendations),
        "high_priority_count": high_pri_count,
        "recommendations": recommendations,
        "campus_summary": {
            "solar_utilization": solar_utilization,
            "unused_solar_kwh": unused_solar_kwh,
            "top_building": top_building,
            "top_bld_share": top_bld_share,
            "min_battery": min_battery
        }
    }
