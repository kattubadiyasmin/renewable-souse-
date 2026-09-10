from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
from models.energy_data import EnergyReading
from utils.validators import ALLOWED_BUILDINGS, BUILDING_TYPE_MAP, ALLOWED_WEATHER

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def overview():
    """WattWise Overview and Landing Page."""
    return render_template('overview.html', active_page='overview')

@main_bp.route('/dashboard')
def dashboard():
    """Energy Dashboard with real-time KPI metrics and Chart.js graphs."""
    return render_template('dashboard.html', active_page='dashboard')

@main_bp.route('/analytics')
def analytics():
    """Energy Analytics Page with historical distributions and dynamic insights."""
    buildings = ALLOWED_BUILDINGS
    return render_template('analytics.html', active_page='analytics', buildings=buildings)

@main_bp.route('/alerts')
def alerts():
    """Wastage Detection & Anomaly Alerts (Rule-Based + Isolation Forest ML)."""
    return render_template('alerts.html', active_page='alerts')

@main_bp.route('/prediction')
def prediction():
    """Energy Demand Prediction (Random Forest Regressor ML)."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    buildings = ALLOWED_BUILDINGS
    return render_template('prediction.html', active_page='prediction', today_str=today_str, buildings=buildings)

@main_bp.route('/solar')
def solar():
    """Solar Energy Analysis & Photovoltaic Utilization Tracking."""
    return render_template('solar.html', active_page='solar')

@main_bp.route('/recommendations')
def recommendations():
    """Dynamic Rule-Based Smart Energy Recommendations."""
    return render_template('recommendations.html', active_page='recommendations')

@main_bp.route('/live')
def live_monitor():
    """Real-Time Energy Monitoring Simulation."""
    buildings = ALLOWED_BUILDINGS
    return render_template('live_monitor.html', active_page='live', buildings=buildings)

@main_bp.route('/add-data')
def add_data():
    """Manual Energy Reading Data Entry Page."""
    now = datetime.now()
    today_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")
    
    # Fetch 10 most recent readings for preview
    recent_readings = EnergyReading.query.order_by(
        EnergyReading.date.desc(),
        EnergyReading.time.desc(),
        EnergyReading.id.desc()
    ).limit(10).all()
    
    return render_template(
        'add_data.html',
        active_page='add-data',
        buildings=ALLOWED_BUILDINGS,
        building_map=BUILDING_TYPE_MAP,
        weather_list=ALLOWED_WEATHER,
        default_date=today_date,
        default_time=current_time,
        recent_readings=recent_readings
    )

@main_bp.route('/upload')
def upload():
    """CSV Dataset Upload and Batch Processing Page."""
    total_count = EnergyReading.query.count()
    return render_template('upload.html', active_page='upload', total_count=total_count)
