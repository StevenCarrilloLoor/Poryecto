# scripts/init_database.py

"""
Database Initialization Script
Crea la base de datos, tablas y datos iniciales
"""

import sys
import os
from pathlib import Path

# Add backend/src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))

import logging
from datetime import datetime

from sqlalchemy import text
from passlib.context import CryptContext

from infrastructure.persistence.db_context import get_db_context, init_database
from infrastructure.persistence.models import (
    User, DetectorConfig, DetectorType, FraudSeverity
)
from config.settings import Settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_admin_user():
    """Create default admin user."""
    logger.info("Creating admin user...")
    
    db_context = get_db_context()
    
    with db_context.get_session() as session:
        # Check if admin exists
        admin = session.query(User).filter(User.username == "admin").first()
        
        if not admin:
            admin = User(
                username="admin",
                email="admin@frauddetection.com",
                full_name="System Administrator",
                hashed_password=pwd_context.hash("Admin123!"),
                is_active=True,
                is_superuser=True
            )
            session.add(admin)
            session.commit()
            logger.info("Admin user created successfully")
        else:
            logger.info("Admin user already exists")


def create_default_detector_configs():
    """Create default detector configurations."""
    logger.info("Creating default detector configurations...")
    
    db_context = get_db_context()
    
    default_configs = [
        # Invoice Anomaly Detector
        {
            "detector_type": DetectorType.INVOICE_ANOMALY,
            "parameter_name": "round_amount_threshold",
            "parameter_value": "100",
            "data_type": "DECIMAL",
            "description": "Umbral para montos redondos sospechosos",
            "min_value": "10",
            "max_value": "10000",
            "default_value": "100"
        },
        {
            "detector_type": DetectorType.INVOICE_ANOMALY,
            "parameter_name": "business_start_hour",
            "parameter_value": "7",
            "data_type": "INTEGER",
            "description": "Hora de inicio del horario laboral",
            "min_value": "0",
            "max_value": "23",
            "default_value": "7"
        },
        {
            "detector_type": DetectorType.INVOICE_ANOMALY,
            "parameter_name": "business_end_hour",
            "parameter_value": "19",
            "data_type": "INTEGER",
            "description": "Hora de fin del horario laboral",
            "min_value": "0",
            "max_value": "23",
            "default_value": "19"
        },
        {
            "detector_type": DetectorType.INVOICE_ANOMALY,
            "parameter_name": "max_discount_percent",
            "parameter_value": "30",
            "data_type": "DECIMAL",
            "description": "Porcentaje máximo de descuento permitido",
            "min_value": "0",
            "max_value": "100",
            "default_value": "30"
        },
        
        # Fuel Theft Detector
        {
            "detector_type": DetectorType.FUEL_THEFT,
            "parameter_name": "capacity_tolerance_percent",
            "parameter_value": "5",
            "data_type": "DECIMAL",
            "description": "Tolerancia para capacidad del tanque (%)",
            "min_value": "0",
            "max_value": "20",
            "default_value": "5"
        },
        {
            "detector_type": DetectorType.FUEL_THEFT,
            "parameter_name": "refuel_check_days",
            "parameter_value": "7",
            "data_type": "INTEGER",
            "description": "Días para verificar frecuencia de repostaje",
            "min_value": "1",
            "max_value": "30",
            "default_value": "7"
        },
        
        # Data Manipulation Detector
        {
            "detector_type": DetectorType.DATA_MANIPULATION,
            "parameter_name": "massive_change_threshold",
            "parameter_value": "50",
            "data_type": "INTEGER",
            "description": "Número de cambios para considerar masivo",
            "min_value": "10",
            "max_value": "1000",
            "default_value": "50"
        },
        {
            "detector_type": DetectorType.DATA_MANIPULATION,
            "parameter_name": "massive_change_window_hours",
            "parameter_value": "2",
            "data_type": "INTEGER",
            "description": "Ventana de tiempo para cambios masivos (horas)",
            "min_value": "1",
            "max_value": "24",
            "default_value": "2"
        },
    ]
    
    with db_context.get_session() as session:
        for config_data in default_configs:
            # Check if config exists
            existing = session.query(DetectorConfig).filter(
                DetectorConfig.detector_type == config_data["detector_type"],
                DetectorConfig.parameter_name == config_data["parameter_name"]
            ).first()
            
            if not existing:
                config = DetectorConfig(**config_data)
                session.add(config)
                logger.info(f"Created config: {config_data['detector_type'].value} - {config_data['parameter_name']}")
            else:
                logger.info(f"Config already exists: {config_data['detector_type'].value} - {config_data['parameter_name']}")
        
        session.commit()
    
    logger.info("Default detector configurations created")


def test_connections():
    """Test database connections."""
    logger.info("Testing database connections...")
    
    # Test SQL Server
    try:
        db_context = get_db_context()
        result = db_context.execute_query("SELECT @@VERSION")
        logger.info(f"SQL Server connection successful")
        logger.info(f"SQL Server version: {result[0][0][:50]}...")
    except Exception as e:
        logger.error(f"SQL Server connection failed: {e}")
        return False
    
    # Test Firebird
    try:
        from infrastructure.persistence.firebird_connector import get_firebird_connector
        fb_connector = get_firebird_connector()
        if fb_connector.test_connection():
            logger.info("Firebird connection successful")
        else:
            logger.error("Firebird connection failed")
            return False
    except Exception as e:
        logger.error(f"Firebird connection error: {e}")
        return False
    
    return True


def main():
    """Main initialization function."""
    logger.info("="*60)
    logger.info("FRAUD DETECTION SYSTEM - DATABASE INITIALIZATION")
    logger.info("="*60)
    
    # Load settings
    settings = Settings()
    logger.info(f"Environment: {settings.ENV}")
    logger.info(f"SQL Server: {settings.SQLSERVER_HOST}")
    
    # Test connections
    if not test_connections():
        logger.error("Connection tests failed. Please check your configuration.")
        sys.exit(1)
    
    # Initialize database
    logger.info("Initializing database schema...")
    try:
        init_database()
        logger.info("Database schema created successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)
    
    # Create initial data
    create_admin_user()
    create_default_detector_configs()
    
    logger.info("="*60)
    logger.info("DATABASE INITIALIZATION COMPLETED SUCCESSFULLY")
    logger.info("="*60)
    logger.info("")
    logger.info("You can now start the application with:")
    logger.info("  Backend:  cd backend && uvicorn src.main:app --reload")
    logger.info("  Frontend: cd frontend && npm start")
    logger.info("")
    logger.info("Default admin credentials:")
    logger.info("  Username: admin")
    logger.info("  Password: Admin123!")
    logger.info("")


if __name__ == "__main__":
    main()