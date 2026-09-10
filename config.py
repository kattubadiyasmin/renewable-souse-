import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Application Configuration for WattWise."""
    BASE_DIR = BASE_DIR
    SECRET_KEY = os.environ.get('SECRET_KEY', 'wattwise-smart-energy-secret-2026')
    
    # SQLite default database path (ready to migrate to MySQL by setting DATABASE_URL)
    # Example for MySQL: mysql+pymysql://username:password@localhost/wattwise
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f"sqlite:///{os.path.join(BASE_DIR, 'wattwise.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File Uploads
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    DATA_FOLDER = os.path.join(BASE_DIR, 'data')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size
    ALLOWED_EXTENSIONS = {'csv'}
    
    # Campus Configuration Defaults
    CAMPUS_NAME = "Apex University Smart Campus"
    NORMAL_WORK_HOUR_START = 8   # 8:00 AM
    NORMAL_WORK_HOUR_END = 18    # 6:00 PM
    MIN_BATTERY_THRESHOLD = 20.0 # 20%
    LOW_SOLAR_UTIL_THRESHOLD = 30.0 # 30%
