import os
from dotenv import load_dotenv

load_dotenv()

# Database
DB_SERVER = os.getenv('DB_SERVER', 'STEVEN-ALIENWAR\\SQLTRABAJO')
DB_DATABASE = os.getenv('DB_DATABASE', 'FraudDetectionDB')
DB_TRUSTED_CONNECTION = os.getenv('DB_TRUSTED_CONNECTION', 'yes')

# API
API_HOST = os.getenv('API_HOST', '0.0.0.0')
API_PORT = int(os.getenv('API_PORT', 8000))

# Security
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')