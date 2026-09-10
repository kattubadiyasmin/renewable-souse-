import os
from flask import Flask, render_template, jsonify
from flask_cors import CORS
from config import Config
from models import db
from routes.main_routes import main_bp
from routes.api_routes import api_bp
from utils.data_generator import init_sample_data

def create_app(config_class=Config):
    """Factory function to build and configure the WattWise Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Enable Cross-Origin Resource Sharing
    CORS(app)

    # Initialize SQLAlchemy ORM
    db.init_app(app)

    # Ensure upload & data directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['DATA_FOLDER'], exist_ok=True)

    # Register application blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    # Global Error Handlers for graceful UX
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('base.html', error_message="404 - The requested resource was not found on WattWise."), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('base.html', error_message="500 - An internal server error occurred. Please verify telemetry inputs."), 500

    # Auto-initialize database tables and realistic sample data on first launch
    with app.app_context():
        db.create_all()
        init_sample_data(app)

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"================================================================")
    print(f"  WATTWISE - AI-Powered Smart Renewable Energy Management System")
    print(f"  Tagline: 'Smart Energy. Sustainable Future.'")
    print(f"  Starting local server at: http://127.0.0.1:{port}")
    print(f"================================================================")
    app.run(host='0.0.0.0', port=port, debug=True)
