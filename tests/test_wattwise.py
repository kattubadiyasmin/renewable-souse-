import os
import sys
import io
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app
from config import Config
from models import db
from models.energy_data import EnergyReading
from utils.validators import validate_energy_data
from services.analytics_service import get_analytics_data
from services.anomaly_service import detect_anomalies
from services.prediction_service import predict_energy_demand
from services.solar_service import get_solar_analysis
from services.recommendation_service import generate_smart_recommendations

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

def test_validators():
    # Valid record
    valid_data = {
        'date': '2026-09-10',
        'time': '14:30',
        'building_name': 'Main Block',
        'building_type': 'Academic',
        'energy_consumption': 42.5,
        'solar_generated': 50.0,
        'solar_used': 35.0,
        'battery_level': 80.0,
        'temperature': 28.5,
        'weather_condition': 'Sunny'
    }
    is_valid, cleaned, errors = validate_energy_data(valid_data)
    assert is_valid is True
    assert len(errors) == 0
    assert cleaned['energy_consumption'] == 42.5

    # Negative energy
    invalid_data = valid_data.copy()
    invalid_data['energy_consumption'] = -10.0
    is_valid, _, errors = validate_energy_data(invalid_data)
    assert is_valid is False
    assert any("negative" in e.lower() for e in errors)

    # Solar used > solar generated
    invalid_data = valid_data.copy()
    invalid_data['solar_used'] = 60.0
    invalid_data['solar_generated'] = 40.0
    is_valid, _, errors = validate_energy_data(invalid_data)
    assert is_valid is False
    assert any("cannot be greater than solar generated" in e.lower() for e in errors)

    # Battery out of bounds
    invalid_data = valid_data.copy()
    invalid_data['battery_level'] = 110.0
    is_valid, _, errors = validate_energy_data(invalid_data)
    assert is_valid is False
    assert any("between 0 and 100" in e.lower() for e in errors)

def test_endpoints_and_services():
    test_app = create_app(TestConfig)
    client = test_app.test_client()

    with test_app.app_context():
        # Seed test readings
        for h in [2, 10, 14, 20]:
            r = EnergyReading(
                date='2026-09-10',
                time=f"{h:02d}:00:00",
                building_name='Main Block',
                building_type='Academic',
                energy_consumption=30.0 + h,
                solar_generated=50.0 if 10 <= h <= 14 else 0.0,
                solar_used=25.0 if 10 <= h <= 14 else 0.0,
                battery_level=75.0,
                temperature=28.0,
                weather_condition='Sunny'
            )
            db.session.add(r)
        db.session.commit()

        # Test Analytics Service
        analytics = get_analytics_data()
        assert analytics['total_consumption'] > 0
        assert analytics['efficiency_score'] >= 0

        # Test Anomaly Detection
        anomalies = detect_anomalies()
        assert 'summary' in anomalies

        # Test Prediction Service
        pred = predict_energy_demand(target_date_str='2026-09-11', building_name='Main Block')
        assert pred['total_predicted_demand_kwh'] > 0
        assert len(pred['hourly_curve']) == 24

        # Test Solar Service
        solar = get_solar_analysis()
        assert solar['total_solar_generated'] > 0

        # Test Recommendations
        recs = generate_smart_recommendations()
        assert recs['total_recommendations'] > 0

    # Test HTTP Routes
    res = client.get('/')
    assert res.status_code == 200
    assert b"WATTWISE" in res.data

    res = client.get('/dashboard')
    assert res.status_code == 200

    res = client.get('/live')
    assert res.status_code == 200

    res = client.get('/analytics')
    assert res.status_code == 200

    res = client.get('/alerts')
    assert res.status_code == 200

    res = client.get('/prediction')
    assert res.status_code == 200

    res = client.get('/solar')
    assert res.status_code == 200

    res = client.get('/recommendations')
    assert res.status_code == 200

    res = client.get('/add-data')
    assert res.status_code == 200

    res = client.get('/upload')
    assert res.status_code == 200

    # Test API Endpoints
    res = client.get('/api/dashboard')
    assert res.status_code == 200
    assert res.json['status'] == 'success'

    res = client.get('/api/live?building=Main+Block')
    assert res.status_code == 200
    assert 'energy_consumption' in res.json['data']

    # Test CSV upload endpoint with in-memory CSV
    csv_content = """date,time,building_name,building_type,energy_consumption,solar_generated,solar_used,battery_level,temperature,weather_condition
2026-09-10,12:00:00,Hostel,Residential,34.5,12.0,10.0,68.0,29.0,Sunny
2026-09-10,14:00:00,Computer Lab,Laboratory,45.0,20.0,18.0,65.0,30.0,Sunny
"""
    data = {'file': (io.BytesIO(csv_content.encode('utf-8')), 'test.csv')}
    res = client.post('/api/upload', data=data, content_type='multipart/form-data')
    assert res.status_code == 200
    assert res.json['status'] == 'success'
    assert res.json['imported_count'] == 2

    print("ALL TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    test_validators()
    test_endpoints_and_services()
