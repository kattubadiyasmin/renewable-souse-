import re
from datetime import datetime

ALLOWED_BUILDINGS = [
    "Main Block",
    "Computer Lab",
    "Library",
    "Administration Block",
    "Hostel"
]

BUILDING_TYPE_MAP = {
    "Main Block": "Academic",
    "Computer Lab": "Laboratory",
    "Library": "Library",
    "Administration Block": "Administrative",
    "Hostel": "Residential"
}

ALLOWED_WEATHER = ["Sunny", "Partly Cloudy", "Cloudy", "Rainy"]

def validate_energy_data(data):
    """
    Validate an energy reading dictionary from manual form entry or API.
    Returns:
        (is_valid: bool, cleaned_data: dict or None, errors: list of str)
    """
    errors = []
    cleaned = {}

    # 1. Date validation
    date_val = data.get('date', '').strip() if isinstance(data.get('date'), str) else ''
    if not date_val:
        errors.append("Date is required.")
    else:
        try:
            datetime.strptime(date_val, "%Y-%m-%d")
            cleaned['date'] = date_val
        except ValueError:
            errors.append("Invalid date format. Expected YYYY-MM-DD.")

    # 2. Time validation
    time_val = data.get('time', '').strip() if isinstance(data.get('time'), str) else ''
    if not time_val:
        errors.append("Time is required.")
    else:
        # Match HH:MM or HH:MM:SS
        if not re.match(r'^(?:[01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?$', time_val):
            errors.append("Invalid time format. Expected HH:MM or HH:MM:SS (24-hour).")
        else:
            # Normalize to HH:MM:00 if HH:MM
            parts = time_val.split(':')
            if len(parts) == 2:
                cleaned['time'] = f"{parts[0].zfill(2)}:{parts[1].zfill(2)}:00"
            else:
                cleaned['time'] = f"{parts[0].zfill(2)}:{parts[1].zfill(2)}:{parts[2].zfill(2)}"

    # 3. Building Name & Type
    building_name = str(data.get('building_name', '')).strip()
    if not building_name:
        errors.append("Building Name is required.")
    else:
        cleaned['building_name'] = building_name

    building_type = str(data.get('building_type', '')).strip()
    if not building_type:
        cleaned['building_type'] = BUILDING_TYPE_MAP.get(building_name, "General")
    else:
        cleaned['building_type'] = building_type

    # 4. Energy Consumption
    try:
        raw_cons = data.get('energy_consumption')
        if raw_cons is None or str(raw_cons).strip() == '':
            errors.append("Energy consumption is required.")
        else:
            cons = float(raw_cons)
            if cons < 0:
                errors.append("Energy consumption cannot be negative.")
            else:
                cleaned['energy_consumption'] = round(cons, 2)
    except (ValueError, TypeError):
        errors.append("Energy consumption must be a valid numeric value.")

    # 5. Solar Generated
    try:
        raw_solar_gen = data.get('solar_generated')
        if raw_solar_gen is None or str(raw_solar_gen).strip() == '':
            cleaned['solar_generated'] = 0.0
        else:
            solar_gen = float(raw_solar_gen)
            if solar_gen < 0:
                errors.append("Solar generated cannot be negative.")
            else:
                cleaned['solar_generated'] = round(solar_gen, 2)
    except (ValueError, TypeError):
        errors.append("Solar generated must be a valid numeric value.")

    # 6. Solar Used
    try:
        raw_solar_used = data.get('solar_used')
        if raw_solar_used is None or str(raw_solar_used).strip() == '':
            cleaned['solar_used'] = 0.0
        else:
            solar_used = float(raw_solar_used)
            if solar_used < 0:
                errors.append("Solar used cannot be negative.")
            else:
                cleaned['solar_used'] = round(solar_used, 2)
    except (ValueError, TypeError):
        errors.append("Solar used must be a valid numeric value.")

    # Cross-check: solar used cannot exceed solar generated
    if 'solar_generated' in cleaned and 'solar_used' in cleaned:
        if cleaned['solar_used'] > cleaned['solar_generated'] + 0.01:
            errors.append(f"Solar used ({cleaned['solar_used']} kWh) cannot be greater than solar generated ({cleaned['solar_generated']} kWh).")

    # 7. Battery Level
    try:
        raw_battery = data.get('battery_level')
        if raw_battery is None or str(raw_battery).strip() == '':
            cleaned['battery_level'] = 50.0
        else:
            battery = float(raw_battery)
            if battery < 0 or battery > 100:
                errors.append("Battery level must be between 0 and 100%.")
            else:
                cleaned['battery_level'] = round(battery, 1)
    except (ValueError, TypeError):
        errors.append("Battery level must be a numeric value between 0 and 100.")

    # 8. Temperature
    try:
        raw_temp = data.get('temperature')
        if raw_temp is None or str(raw_temp).strip() == '':
            cleaned['temperature'] = 25.0
        else:
            temp = float(raw_temp)
            if temp < -30 or temp > 70:
                errors.append("Temperature must be within a realistic range (-30°C to 70°C).")
            else:
                cleaned['temperature'] = round(temp, 1)
    except (ValueError, TypeError):
        errors.append("Temperature must be a valid numeric value.")

    # 9. Weather Condition
    weather = str(data.get('weather_condition', 'Sunny')).strip()
    if not weather:
        cleaned['weather_condition'] = "Sunny"
    else:
        cleaned['weather_condition'] = weather

    is_valid = len(errors) == 0
    return is_valid, cleaned if is_valid else None, errors
