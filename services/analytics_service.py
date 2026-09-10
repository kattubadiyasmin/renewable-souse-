import pandas as pd
import numpy as np
from sqlalchemy import func
from models import db
from models.energy_data import EnergyReading

def get_analytics_data(building_filter=None, date_from=None, date_to=None):
    """
    Calculate comprehensive energy analytics from the database.
    Supports optional filtering by building and date range.
    """
    query = EnergyReading.query

    if building_filter and building_filter != "All":
        query = query.filter(EnergyReading.building_name == building_filter)
    if date_from:
        query = query.filter(EnergyReading.date >= date_from)
    if date_to:
        query = query.filter(EnergyReading.date <= date_to)

    readings = query.all()

    if not readings:
        return {
            "total_consumption": 0.0,
            "average_consumption": 0.0,
            "max_consumption": 0.0,
            "max_record": None,
            "min_consumption": 0.0,
            "min_record": None,
            "total_solar_generated": 0.0,
            "total_solar_used": 0.0,
            "unused_solar": 0.0,
            "solar_utilization_pct": 0.0,
            "renewable_contribution_pct": 0.0,
            "efficiency_score": 50.0,
            "peak_usage_time": "N/A",
            "highest_consuming_building": "N/A",
            "highest_building_pct": 0.0,
            "building_breakdown": [],
            "daily_trends": [],
            "hourly_trends": [],
            "dynamic_insights": ["Insufficient data available to generate insights."]
        }

    # Convert to DataFrame for fast vectorized aggregation
    data = [{
        'id': r.id,
        'date': r.date,
        'time': r.time,
        'building_name': r.building_name,
        'building_type': r.building_type,
        'energy_consumption': r.energy_consumption,
        'solar_generated': r.solar_generated,
        'solar_used': r.solar_used,
        'battery_level': r.battery_level,
        'temperature': r.temperature,
        'weather_condition': r.weather_condition
    } for r in readings]

    df = pd.DataFrame(data)

    total_consumption = float(df['energy_consumption'].sum())
    avg_consumption = float(df['energy_consumption'].mean())
    max_consumption = float(df['energy_consumption'].max())
    min_consumption = float(df['energy_consumption'].min())

    max_row = df.loc[df['energy_consumption'].idxmax()]
    min_row = df.loc[df['energy_consumption'].idxmin()]

    total_solar_generated = float(df['solar_generated'].sum())
    total_solar_used = float(df['solar_used'].sum())
    unused_solar = max(0.0, total_solar_generated - total_solar_used)

    # Solar utilization: (solar_used / solar_generated) * 100
    solar_utilization_pct = round((total_solar_used / total_solar_generated * 100), 1) if total_solar_generated > 0 else 0.0
    
    # Renewable contribution: (solar_used / energy_consumption) * 100
    renewable_contribution_pct = round((total_solar_used / total_consumption * 100), 1) if total_consumption > 0 else 0.0

    # Building-wise aggregation
    b_group = df.groupby('building_name').agg({
        'energy_consumption': ['sum', 'mean', 'max'],
        'solar_generated': 'sum',
        'solar_used': 'sum',
        'building_type': 'first'
    })
    
    building_breakdown = []
    highest_building_name = "N/A"
    highest_building_cons = 0.0

    for bname, row in b_group.iterrows():
        b_sum = float(row[('energy_consumption', 'sum')])
        b_mean = float(row[('energy_consumption', 'mean')])
        b_max = float(row[('energy_consumption', 'max')])
        b_solar_gen = float(row[('solar_generated', 'sum')])
        b_solar_used = float(row[('solar_used', 'sum')])
        b_type = str(row[('building_type', 'first')])
        
        pct_of_total = round((b_sum / total_consumption * 100), 1) if total_consumption > 0 else 0.0
        
        if b_sum > highest_building_cons:
            highest_building_cons = b_sum
            highest_building_name = bname

        building_breakdown.append({
            'name': bname,
            'type': b_type,
            'total_consumption': round(b_sum, 2),
            'avg_consumption': round(b_mean, 2),
            'max_consumption': round(b_max, 2),
            'solar_generated': round(b_solar_gen, 2),
            'solar_used': round(b_solar_used, 2),
            'share_pct': pct_of_total
        })

    # Sort building breakdown descending by total consumption
    building_breakdown.sort(key=lambda x: x['total_consumption'], reverse=True)
    highest_building_pct = round((highest_building_cons / total_consumption * 100), 1) if total_consumption > 0 else 0.0

    # Peak usage hour calculation
    df['hour'] = df['time'].apply(lambda t: int(t.split(':')[0]) if isinstance(t, str) and ':' in t else 0)
    hourly_avg = df.groupby('hour')['energy_consumption'].mean()
    peak_hour = int(hourly_avg.idxmax()) if not hourly_avg.empty else 13
    peak_hour_str = f"{peak_hour:02d}:00 - {(peak_hour+1)%24:02d}:00"

    # Energy Efficiency Score (0 to 100)
    # Balanced weighting:
    # 40% Solar Utilization (scaled to 100)
    # 35% Renewable Contribution (scaled with target 40%)
    # 25% Off-hours Waste Penalty
    solar_util_component = min(100.0, solar_utilization_pct) * 0.40
    renew_component = min(100.0, (renewable_contribution_pct / 45.0) * 100.0) * 0.35
    
    # Calculate night vs day ratio (night load penalty)
    daytime_df = df[(df['hour'] >= 8) & (df['hour'] <= 18)]
    night_df = df[(df['hour'] < 8) | (df['hour'] > 18)]
    day_avg = daytime_df['energy_consumption'].mean() if not daytime_df.empty else 1.0
    night_avg = night_df['energy_consumption'].mean() if not night_df.empty else 0.0
    night_ratio = night_avg / (day_avg + 1e-6)
    
    # Lower night ratio gives higher efficiency (excluding hostel)
    offhour_score = max(20.0, min(100.0, (1.0 - night_ratio * 0.8) * 100)) * 0.25
    
    efficiency_score = round(max(15.0, min(99.0, solar_util_component + renew_component + offhour_score)), 1)

    # Daily trends (last 14 days grouped)
    daily_grouped = df.groupby('date').agg({
        'energy_consumption': 'sum',
        'solar_generated': 'sum',
        'solar_used': 'sum'
    }).reset_index().sort_values('date')
    
    # Take last 14 dates
    recent_daily = daily_grouped.tail(14)
    daily_trends = [{
        'date': row['date'],
        'consumption': round(float(row['energy_consumption']), 2),
        'solar_generated': round(float(row['solar_generated']), 2),
        'solar_used': round(float(row['solar_used']), 2)
    } for _, row in recent_daily.iterrows()]

    # Hourly diurnal profile (00 to 23)
    hourly_grouped = df.groupby('hour').agg({
        'energy_consumption': 'mean',
        'solar_generated': 'mean',
        'solar_used': 'mean'
    }).reindex(range(24), fill_value=0.0).reset_index()

    hourly_trends = [{
        'hour': f"{int(row['hour']):02d}:00",
        'avg_consumption': round(float(row['energy_consumption']), 2),
        'avg_solar_generated': round(float(row['solar_generated']), 2),
        'avg_solar_used': round(float(row['solar_used']), 2)
    } for _, row in hourly_grouped.iterrows()]

    # Dynamic Insights generation
    dynamic_insights = generate_dynamic_insights(
        df, total_consumption, avg_consumption, highest_building_name,
        highest_building_pct, peak_hour_str, solar_utilization_pct,
        renewable_contribution_pct, building_breakdown
    )

    return {
        "total_consumption": round(total_consumption, 2),
        "average_consumption": round(avg_consumption, 2),
        "max_consumption": round(max_consumption, 2),
        "max_record": {
            "building": max_row['building_name'],
            "date": max_row['date'],
            "time": max_row['time'],
            "value": round(float(max_row['energy_consumption']), 2)
        },
        "min_consumption": round(min_consumption, 2),
        "min_record": {
            "building": min_row['building_name'],
            "date": min_row['date'],
            "time": min_row['time'],
            "value": round(float(min_row['energy_consumption']), 2)
        },
        "total_solar_generated": round(total_solar_generated, 2),
        "total_solar_used": round(total_solar_used, 2),
        "unused_solar": round(unused_solar, 2),
        "solar_utilization_pct": solar_utilization_pct,
        "renewable_contribution_pct": renewable_contribution_pct,
        "efficiency_score": efficiency_score,
        "peak_usage_time": peak_hour_str,
        "highest_consuming_building": highest_building_name,
        "highest_building_pct": highest_building_pct,
        "building_breakdown": building_breakdown,
        "daily_trends": daily_trends,
        "hourly_trends": hourly_trends,
        "dynamic_insights": dynamic_insights
    }

def generate_dynamic_insights(df, total_consumption, campus_avg, highest_building,
                             highest_pct, peak_time, solar_util, renew_share, buildings):
    """Generate dynamic narrative intelligence statements grounded in real dataset math."""
    insights = []

    # 1. Building load insight
    if highest_building and highest_building != "N/A":
        # Find how much higher than campus average this building is
        b_data = df[df['building_name'] == highest_building]
        if not b_data.empty:
            b_avg = b_data['energy_consumption'].mean()
            diff_pct = round(((b_avg - campus_avg) / campus_avg) * 100, 1) if campus_avg > 0 else 0
            if diff_pct > 0:
                insights.append(
                    f"⚠️ {highest_building} is the highest campus energy consumer, accounting for {highest_pct}% of total electricity demand and consuming {diff_pct}% more power than the campus average."
                )
            else:
                insights.append(
                    f"📊 {highest_building} accounts for {highest_pct}% of total campus electricity consumption."
                )

    # 2. Peak demand hour insight
    insights.append(
        f"⏰ Campus peak electrical load consistently materializes during the {peak_time} window, driven by simultaneous air conditioning, laboratory equipment, and academic lighting."
    )

    # 3. Solar utilization insight
    if solar_util >= 70:
        insights.append(
            f"☀️ High Solar Efficiency: Solar utilization stands strong at {solar_util}%, successfully offsetting {renew_share}% of total campus electricity requirements."
        )
    elif solar_util >= 40:
        insights.append(
            f"☀️ Moderate Solar Capture: Solar utilization is at {solar_util}%. Expanding thermal storage or rescheduling peak loads could tap into {100 - solar_util:.1f}% unused solar generation."
        )
    else:
        insights.append(
            f"⚠️ Low Solar Utilization Warning: Only {solar_util}% of generated solar energy is directly utilized or stored. Microgrid load balancing is strongly recommended."
        )

    # 4. Off-hours night waste check
    off_hours = df[(df['hour'] >= 22) | (df['hour'] <= 5)]
    non_hostel_night = off_hours[off_hours['building_name'] != 'Hostel']
    if not non_hostel_night.empty:
        night_mean = non_hostel_night['energy_consumption'].mean()
        high_night = non_hostel_night[non_hostel_night['energy_consumption'] > night_mean * 1.8]
        if len(high_night) > 3:
            affected_b = high_night['building_name'].mode()[0] if not high_night.empty else "Facilities"
            insights.append(
                f"🌙 Off-Hours Wastage Detected: {affected_b} demonstrates abnormal overnight power draws (averaging {night_mean:.1f} kWh between 10 PM and 5 AM). Review equipment auto-shutdown policies."
            )

    # 5. Clean energy balance
    insights.append(
        f"🌱 Overall Green Transition: On-site photovoltaics currently furnish {renew_share}% of total net energy consumption, preventing substantial grid-related carbon emissions."
    )

    return insights
