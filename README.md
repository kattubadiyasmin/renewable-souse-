# ⚡ WattWise - AI-Powered Smart Renewable Energy Management System

> **Tagline:** "Smart Energy. Sustainable Future."  
> **Mission:** "Reduce Energy Waste, Maximize Renewable Energy."  
> **Primary Challenge:** *"How can campuses intelligently reduce energy wastage and maximize renewable energy utilization?"*

---

## 📌 1. Project Overview & Problem Statement

College campuses, research parks, and municipal complexes consume massive quantities of electricity across dispersed facilities (academic blocks, computing laboratories, libraries, administrative centers, and dormitories). Despite investments in rooftop solar photovoltaics (PV) and battery storage, organizations routinely struggle with:
1. **Opaque Facility Footprints:** Lack of visibility into which buildings draw excessive power.
2. **Severe Off-Hours Wastage:** HVAC systems, high-performance computing labs, and lighting left running overnight or during weekends.
3. **Solar Energy Curtailment:** Midday solar generation surplus going unabsorbed or dumped due to misaligned load scheduling.
4. **Demand Peak Penalties:** Synchronous appliance startups causing expensive peak demand charges on utility bills.

**WattWise** solves these issues by uniting IoT telemetry ingestion, hybrid machine learning anomaly detection, predictive demand forecasting, and an algorithmic recommendation engine into a single unified web platform.

---

## 🌟 2. Core Features & Capabilities

- 📊 **Energy Command Center:** Live dashboard calculating total energy demand, solar generation, direct absorption, renewable percentage, efficiency scores, and active wastage alerts.
- 📈 **Interactive Visual Telemetry:** Built with Chart.js:
  - 14-day energy consumption trends
  - 14-day solar generation profiles
  - 24-hour diurnal load vs solar curve
  - Building-by-building breakdown & energy distribution donut
- 🔍 **Hybrid Wastage Detection Engine:**
  - **Rule-Based Engine:** Detects non-working hour (8 PM – 6 AM) spikes, building z-score outliers, low solar utilization (< 30%), and battery reserve drops (< 20%).
  - **Machine Learning (Isolation Forest):** Unsupervised multivariate pattern detection across consumption, generation, battery, and ambient temperature.
- 🔮 **Predictive Demand Forecasting:**
  - **Random Forest Regressor:** Dynamically trained on SQLite historical readings, encoding hour-of-day, day-of-week, weekend flags, temperature curves, and building baselines.
  - Predicts 24-hour hourly curves and identifies peak usage windows.
  - Graceful fallback to empirical diurnal averages if database size is small.
- ☀️ **Solar Utilization Deep Dive:**
  - Quantifies direct solar consumption vs unused curtailment.
  - Evaluates weather impact (Sunny vs Cloudy vs Rainy yields).
  - Dynamic narrative insights describing peak irradiance windows.
- 💡 **Smart Recommendation Engine:**
  - Generates data-driven policy recommendations (load shifting, night shutdowns, emergency battery shedding, peak shaving).
  - Includes estimated kWh savings and concrete action steps.
- 📡 **Real-Time Simulation & Live Monitor:**
  - Generates realistic physics-based sensor readings based on system time and weather.
  - Supports anomaly injection testing and automated 3-second live streaming.
  - Direct single-click database logging.
- 📝 **Telemetry Data Management:**
  - Add manual readings with constraint validation (non-negative, battery 0-100%, solar used $\le$ solar generated).
  - CSV dataset batch upload with automated Pandas parsing, schema validation, error skipping, and downloadable sample CSV.

---

## 🛠️ 3. Technology Stack

- **Backend:** Python 3.12+, Flask 3.1, Flask-CORS, Flask-SQLAlchemy, Werkzeug, Jinja2
- **Database:** SQLite (ORM-managed via SQLAlchemy; zero configuration required; easily migrated to MySQL via `DATABASE_URL`)
- **Data Analytics & ML:** Pandas, NumPy, Scikit-learn (`IsolationForest`, `RandomForestRegressor`), SciPy
- **Frontend:** HTML5, CSS3 (Modern Clean-Energy Dark/Glassmorphism theme), Vanilla JavaScript
- **Visualization:** Chart.js 4 (responsive canvas rendering with glowing gradients)
- **Icons & Fonts:** Font Awesome 6, Google Fonts (Inter)

---

## 📂 4. Project Architecture

```
renewable energy/
│
├── app.py                      # Application entrypoint and database auto-seeder
├── config.py                   # Centralized configuration (SQLite/MySQL URLs, paths)
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git exclusion rules
├── README.md                   # Complete architectural and setup guide
│
├── models/
│   ├── __init__.py             # SQLAlchemy instance initialization
│   └── energy_data.py          # EnergyReading ORM model and serialization
│
├── routes/
│   ├── __init__.py             # Blueprint package
│   ├── main_routes.py          # HTML page routes (overview, dashboard, live, etc.)
│   └── api_routes.py           # REST API endpoints (/api/dashboard, /api/prediction, etc.)
│
├── services/
│   ├── __init__.py             # Services package
│   ├── analytics_service.py    # Statistical aggregation & dynamic narrative insights
│   ├── anomaly_service.py      # Hybrid Rule-Based & Isolation Forest anomaly engine
│   ├── prediction_service.py   # Scikit-learn RandomForestRegressor demand forecasting
│   ├── solar_service.py        # Solar yield, curtailment, and weather efficiency
│   └── recommendation_service.py # Algorithmic rule-based action plan generator
│
├── utils/
│   ├── __init__.py             # Utilities package
│   ├── validators.py           # Form and CSV schema validation rules
│   └── data_generator.py       # 35-day realistic campus data simulation engine
│
├── templates/
│   ├── base.html               # Master layout (sidebar, topbar, toasts, clock)
│   ├── overview.html           # Landing page with problem, solution, workflow
│   ├── dashboard.html          # Main energy dashboard with 5 Chart.js charts
│   ├── live_monitor.html       # Real-time campus simulation & live stream
│   ├── analytics.html          # Deep statistical analytics & building benchmarks
│   ├── alerts.html             # Wastage detection & anomaly incident log
│   ├── prediction.html         # ML demand forecasting with 24h prediction curve
│   ├── solar.html              # Solar photovoltaic utilization & curtailment
│   ├── recommendations.html    # Smart operational recommendation cards
│   ├── add_data.html           # Manual telemetry recording form
│   └── upload.html             # CSV upload, validation, and batch ingestion
│
├── static/
│   ├── css/
│   │   └── style.css           # Clean-tech CSS design system
│   ├── js/
│   │   ├── main.js             # Global clock, mobile navigation, toast system
│   │   ├── charts.js           # Reusable Chart.js theme and builders
│   │   ├── dashboard.js        # Dashboard data fetching and chart binding
│   │   ├── live_monitor.js     # Live simulation stream and database commit
│   │   ├── analytics.js        # Filtered analytics and comparison table
│   │   ├── alerts.js           # Anomaly log filtering and severity management
│   │   ├── prediction.js       # ML forecast triggering and 24h curve rendering
│   │   └── solar.js            # Solar generation and weather correlation charts
│   └── uploads/                # Directory for uploaded CSV files
│
└── data/
    └── sample_energy_data.csv  # 35-day generated sample dataset ready for download
```

---

## 🚀 5. Installation & Local Execution

### Prerequisites
- Python 3.10+ (Recommended: Python 3.12)
- Git

### Step-by-Step Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/kattubadiyasmin/renewable-souse-.git
   cd "renewable energy"
   ```

2. **Create and activate a virtual environment:**
   - **Windows (PowerShell):**
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - **Linux / macOS:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch the application:**
   ```bash
   python app.py
   ```

5. **Open in browser:**
   Navigate to [http://127.0.0.1:5000](http://127.0.0.1:5000).

> **Note:** Upon the very first launch, WattWise will automatically create the SQLite database (`wattwise.db`) and seed **35 days of realistic diurnal campus data** across 5 facilities. No manual database setup is required.

---

## 🤖 6. How the AI/ML & Analytics Work

### 1. Hybrid Wastage Detection
- **Approach 1: Deterministic Rule Engine**
  - Flags non-residential facilities drawing more than $2.2\times$ their baseline between 8:00 PM and 6:00 AM.
  - Computes building-specific z-scores ($Z = \frac{x - \mu}{\sigma}$); flags deviations above $2.4\sigma$.
  - Flags solar curtailment when generation exceeds $25\text{ kWh}$ but utilization is $< 30\%$.
  - Monitors battery state of charge (SoC) for drops below $20\%$.
- **Approach 2: Isolation Forest Machine Learning**
  - Unsupervised multivariate outlier detection using `sklearn.ensemble.IsolationForest`.
  - Analyzes multidimensional interactions between `[energy_consumption, solar_generated, solar_used, battery_level, temperature]`.
  - Graceful fallback ensures 100% uptime even on sparse datasets.

### 2. Energy Demand Forecasting
- Model: `sklearn.ensemble.RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42)`.
- Dynamic Training: Fits live against the SQLite database table upon forecast request.
- Feature Space:
  - `hour`: Diurnal load cycling ($0 - 23$)
  - `day_of_week` & `is_weekend`: Academic vs weekend schedules
  - `temperature`: Diurnal thermal load proxy
  - `historical_building_mean`: Building size normalization
  - One-hot facility indicators (`bld_Main Block`, `bld_Computer Lab`, etc.)
- Provides $R^2$ fit scores, Mean Absolute Error (MAE), and identifies the expected peak consumption window.

---

## 📋 7. CSV Dataset Schema

When uploading custom CSV files, ensure the following columns are present:

| Column Header | Format / Type | Description |
| :--- | :--- | :--- |
| `date` | `YYYY-MM-DD` | Date of reading (e.g. `2026-09-10`) |
| `time` | `HH:MM:SS` | 24-hour time of reading (e.g. `14:00:00`) |
| `building_name` | String | e.g. `Main Block`, `Computer Lab`, `Library` |
| `building_type` | String | e.g. `Academic`, `Laboratory`, `Residential` |
| `energy_consumption` | Float ($\ge 0$) | Electricity consumed in kilowatt-hours (kWh) |
| `solar_generated` | Float ($\ge 0$) | Photovoltaic generation in kWh |
| `solar_used` | Float ($\le \text{generated}$) | Solar power directly consumed or stored in kWh |
| `battery_level` | Float ($0 - 100$) | Storage battery state of charge percentage |
| `temperature` | Float | Ambient temperature in degrees Celsius (°C) |
| `weather_condition` | String | `Sunny`, `Partly Cloudy`, `Cloudy`, `Rainy` |

---

## 🔮 8. Future Roadmap

- [ ] Support for multi-campus tenant isolation and custom tariffs.
- [ ] Integration with hardware smart meters via MQTT / Modbus.
- [ ] Automated relay switching for HVAC and inverter charge control.
- [ ] Migration support to MySQL / PostgreSQL clusters for enterprise deployments.

---

## 📄 9. License

Developed for hackathon demonstration and sustainable energy research. Distributed under the MIT License.
