from datetime import datetime
from models import db

class EnergyReading(db.Model):
    """Energy reading database model for campus buildings."""
    __tablename__ = 'energy_readings'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.String(10), nullable=False, index=True) # YYYY-MM-DD
    time = db.Column(db.String(8), nullable=False)              # HH:MM or HH:MM:SS
    building_name = db.Column(db.String(100), nullable=False, index=True)
    building_type = db.Column(db.String(50), nullable=False)
    energy_consumption = db.Column(db.Float, nullable=False, default=0.0) # kWh
    solar_generated = db.Column(db.Float, nullable=False, default=0.0)    # kWh
    solar_used = db.Column(db.Float, nullable=False, default=0.0)         # kWh
    battery_level = db.Column(db.Float, nullable=False, default=0.0)      # %
    temperature = db.Column(db.Float, nullable=False, default=25.0)       # °C
    weather_condition = db.Column(db.String(50), nullable=False, default="Sunny")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        """Convert reading instance to JSON serializable dictionary."""
        return {
            'id': self.id,
            'date': self.date,
            'time': self.time,
            'building_name': self.building_name,
            'building_type': self.building_type,
            'energy_consumption': round(float(self.energy_consumption), 2),
            'solar_generated': round(float(self.solar_generated), 2),
            'solar_used': round(float(self.solar_used), 2),
            'battery_level': round(float(self.battery_level), 1),
            'temperature': round(float(self.temperature), 1),
            'weather_condition': self.weather_condition,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

    def __repr__(self):
        return f"<EnergyReading id={self.id} building='{self.building_name}' date='{self.date}' time='{self.time}'>"
