import pandas as pd
import numpy as np
from models.energy_data import EnergyReading

def get_solar_analysis():
    """
    Perform deep solar energy analysis from SQLite database records.
    Returns metrics, hourly generation curves, utilization breakdown, and dynamic insights.
    """
    readings = EnergyReading.query.all()
    if not readings:
        return {
            "total_solar_generated": 0.0,
            "total_solar_used": 0.0,
            "unused_solar": 0.0,
            "solar_utilization_pct": 0.0,
            "renewable_fraction_pct": 0.0,
            "peak_solar_window": "N/A",
            "peak_hourly_yield_kwh": 0.0,
            "avg_daily_solar_kwh": 0.0,
            "hourly_solar_profile": [],
            "daily_solar_trend": [],
            "weather_efficiency": [],
            "insights": ["No solar generation records found in the database."]
        }

    records = [{
        'date': r.date,
        'time': r.time,
        'building_name': r.building_name,
        'energy_consumption': float(r.energy_consumption),
        'solar_generated': float(r.solar_generated),
        'solar_used': float(r.solar_used),
        'battery_level': float(r.battery_level),
        'weather_condition': r.weather_condition
    } for r in readings]

    df = pd.DataFrame(records)
    
    total_solar_generated = float(df['solar_generated'].sum())
    total_solar_used = float(df['solar_used'].sum())
    total_energy_consumption = float(df['energy_consumption'].sum())
    unused_solar = max(0.0, total_solar_generated - total_solar_used)

    # Safe division for utilization
    solar_utilization_pct = round((total_solar_used / total_solar_generated * 100), 1) if total_solar_generated > 0 else 0.0
    renewable_fraction_pct = round((total_solar_used / total_energy_consumption * 100), 1) if total_energy_consumption > 0 else 0.0

    # Hourly generation curve (extract hour)
    df['hour'] = df['time'].apply(lambda t: int(t.split(':')[0]) if isinstance(t, str) and ':' in t else 12)
    
    # Campus total hourly sum averaged across unique dates
    num_days = max(1, len(df['date'].unique()))
    
    # Hourly solar generation and usage
    hourly_agg = df.groupby('hour').agg({
        'solar_generated': lambda x: x.sum() / num_days,
        'solar_used': lambda x: x.sum() / num_days,
        'energy_consumption': lambda x: x.sum() / num_days
    }).reindex(range(24), fill_value=0.0).reset_index()

    hourly_solar_profile = [{
        'hour': f"{int(row['hour']):02d}:00",
        'solar_generated': round(float(row['solar_generated']), 2),
        'solar_used': round(float(row['solar_used']), 2),
        'unused': round(max(0.0, float(row['solar_generated']) - float(row['solar_used'])), 2),
        'consumption': round(float(row['energy_consumption']), 2)
    } for _, row in hourly_agg.iterrows()]

    # Find peak solar window
    solar_hours = hourly_agg[hourly_agg['solar_generated'] > 0]
    if not solar_hours.empty:
        peak_hr = int(solar_hours.loc[solar_hours['solar_generated'].idxmax(), 'hour'])
        peak_window_str = f"{(peak_hr-1):02d}:00 - {(peak_hr+2):02d}:00"
        peak_yield = round(float(solar_hours['solar_generated'].max()), 2)
    else:
        peak_window_str = "11:00 - 14:00"
        peak_yield = 0.0

    avg_daily_solar = round(total_solar_generated / num_days, 2)

    # Daily solar trend (last 14 days)
    daily_agg = df.groupby('date').agg({
        'solar_generated': 'sum',
        'solar_used': 'sum',
        'energy_consumption': 'sum'
    }).reset_index().sort_values('date')

    recent_daily = daily_agg.tail(14)
    daily_solar_trend = [{
        'date': row['date'],
        'solar_generated': round(float(row['solar_generated']), 2),
        'solar_used': round(float(row['solar_used']), 2),
        'unused_solar': round(max(0.0, float(row['solar_generated']) - float(row['solar_used'])), 2),
        'utilization_pct': round((float(row['solar_used']) / float(row['solar_generated']) * 100), 1) if float(row['solar_generated']) > 0 else 0.0
    } for _, row in recent_daily.iterrows()]

    # Weather efficiency breakdown
    weather_agg = df.groupby('weather_condition').agg({
        'solar_generated': 'mean',
        'battery_level': 'mean'
    }).reset_index()

    weather_efficiency = [{
        'weather': row['weather_condition'],
        'avg_solar_reading': round(float(row['solar_generated']), 2),
        'avg_battery': round(float(row['battery_level']), 1)
    } for _, row in weather_agg.iterrows()]

    # Dynamic Insights
    insights = []
    insights.append(
        f"☀️ Peak Solar Yield: Campus solar photovoltaic arrays produce their highest output between {peak_window_str}, peaking at an average of {peak_yield} kWh per hour."
    )

    if solar_utilization_pct >= 80:
        insights.append(
            f"⚡ Exceptional Solar Absorption: {solar_utilization_pct}% of generated solar power is directly channeled into campus loads and battery banks."
        )
    elif solar_utilization_pct >= 60:
        insights.append(
            f"📈 Optimization Opportunity: Solar utilization is {solar_utilization_pct}%. An estimated {unused_solar:,.1f} kWh has gone unutilized, which could recharge campus electric vehicles or run water treatment pumps."
        )
    else:
        insights.append(
            f"⚠️ Significant Solar Curtailment: {100 - solar_utilization_pct:.1f}% ({unused_solar:,.1f} kWh) of generated solar is currently lost or curtailed due to storage limits during midday."
        )

    # Weather contrast insight
    sunny_rows = df[df['weather_condition'] == 'Sunny']['solar_generated']
    rainy_rows = df[df['weather_condition'] == 'Rainy']['solar_generated']
    if not sunny_rows.empty and not rainy_rows.empty:
        s_mean = sunny_rows.mean()
        r_mean = rainy_rows.mean()
        drop_pct = round(((s_mean - r_mean) / (s_mean + 1e-6)) * 100, 1)
        insights.append(
            f"🌧️ Weather Impact: Solar output drops by {drop_pct}% during rainy conditions compared to clear sunny skies, requiring proactive battery reserve scheduling."
        )

    return {
        "total_solar_generated": round(total_solar_generated, 2),
        "total_solar_used": round(total_solar_used, 2),
        "unused_solar": round(unused_solar, 2),
        "solar_utilization_pct": solar_utilization_pct,
        "renewable_fraction_pct": renewable_fraction_pct,
        "peak_solar_window": peak_window_str,
        "peak_hourly_yield_kwh": peak_yield,
        "avg_daily_solar_kwh": avg_daily_solar,
        "hourly_solar_profile": hourly_solar_profile,
        "daily_solar_trend": daily_solar_trend,
        "weather_efficiency": weather_efficiency,
        "insights": insights
    }
