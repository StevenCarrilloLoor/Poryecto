# backend/src/infrastructure/persistence/db_context.py

import logging
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Type, TypeVar

from sqlalchemy import create_engine, event, pool
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker, scoped_session
from sqlalchemy.orm.query import Query

from backend.src.infrastructure.persistence.models import Base
from backend.src.config.settings import Settings

T = TypeVar('T')
logger = logging.getLogger(__name__)


class FraudDetectionDbContext:
    """
    Database context implementing Unit of Work and Repository patterns.
    Manages all database operations for the fraud detection system.
    """
    
    def __init__(self, connection_string: str = None):
        """Initialize the database context with SQL Server connection."""
        self.settings = Settings()
        self.connection_string = connection_string or self._build_connection_string()
        
        # Create engine with connection pooling
        self.engine = create_engine(
            self.connection_string,
            pool_size=self.settings.CONNECTION_POOL_SIZE,
            max_overflow=self.settings.CONNECTION_POOL_OVERFLOW,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600,   # Recycle connections after 1 hour
            echo=self.settings.DEBUG,
            future=True
        )
        
        # Create session factory
        self.SessionLocal = scoped_session(
            sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine,
                expire_on_commit=False
            )
        )
        
        # Set up event listeners
        self._setup_listeners()
        
    def _build_connection_string(self) -> str:
        """Build SQL Server connection string from settings."""
        return (
            f"mssql+pyodbc://{self.settings.SQLSERVER_USERNAME}:"
            f"{self.settings.SQLSERVER_PASSWORD}@"
            f"{self.settings.SQLSERVER_HOST}/"
            f"{self.settings.SQLSERVER_DATABASE}"
            f"?driver={self.settings.SQLSERVER_DRIVER}"
            f"&TrustServerCertificate=yes"
        )
    
    def _setup_listeners(self):
        """Set up SQLAlchemy event listeners for monitoring."""
        @event.listens_for(Engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            connection_record.info['pid'] = dbapi_conn.execute(
                "SELECT @@SPID"
            ).scalar()
            
        @event.listens_for(Engine, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            logger.debug(f"Connection {connection_record.info.get('pid')} checked out")
    
    def create_database(self):
        """Create database and all tables if they don't exist."""
        try:
            # First, create database if it doesn't exist
            temp_engine = create_engine(
                self.connection_string.rsplit('/', 1)[0] + '/master',
                isolation_level="AUTOCOMMIT"
            )
            
            with temp_engine.connect() as conn:
                result = conn.execute(
                    f"SELECT database_id FROM sys.databases WHERE name = '{self.settings.SQLSERVER_DATABASE}'"
                )
                
                if not result.fetchone():
                    conn.execute(f"CREATE DATABASE [{self.settings.SQLSERVER_DATABASE}]")
                    logger.info(f"Database {self.settings.SQLSERVER_DATABASE} created successfully")
                    
            temp_engine.dispose()
            
            # Create all tables
            Base.metadata.create_all(bind=self.engine)
            logger.info("All tables created successfully")
            
        except SQLAlchemyError as e:
            logger.error(f"Error creating database: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Session:
        """
        Context manager for database sessions.
        Ensures proper cleanup and error handling.
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            session.close()
    
    def add(self, entity: T) -> T:
        """Add a new entity to the database."""
        with self.get_session() as session:
            session.add(entity)
            session.flush()
            session.refresh(entity)
            return entity
    
    def add_many(self, entities: List[T]) -> List[T]:
        """Add multiple entities to the database."""
        with self.get_session() as session:
            session.add_all(entities)
            session.flush()
            for entity in entities:
                session.refresh(entity)
            return entities
    
    def get_by_id(self, model: Type[T], entity_id: Any) -> Optional[T]:
        """Get an entity by its primary key."""
        with self.get_session() as session:
            return session.query(model).get(entity_id)
    
    def get_all(self, model: Type[T], limit: int = None, offset: int = None) -> List[T]:
        """Get all entities of a given type with optional pagination."""
        with self.get_session() as session:
            query = session.query(model)
            
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
                
            return query.all()
    
    def update(self, entity: T) -> T:
        """Update an existing entity."""
        with self.get_session() as session:
            session.merge(entity)
            session.flush()
            session.refresh(entity)
            return entity
    
    def delete(self, entity: T) -> bool:
        """Delete an entity from the database."""
        with self.get_session() as session:
            session.delete(entity)
            return True
    
    def delete_by_id(self, model: Type[T], entity_id: Any) -> bool:
        """Delete an entity by its primary key."""
        with self.get_session() as session:
            entity = session.query(model).get(entity_id)
            if entity:
                session.delete(entity)
                return True
            return False
    
    def execute_query(self, query: str, params: Dict[str, Any] = None) -> List[Any]:
        """Execute a raw SQL query."""
        with self.get_session() as session:
            result = session.execute(query, params or {})
            return result.fetchall()
    
    def get_fraud_cases(
        self,
        status: str = None,
        severity: str = None,
        client_code: str = None,
        date_from: str = None,
        date_to: str = None,
        limit: int = 100
    ) -> List[Any]:
        """Get fraud cases with filtering options."""
        from backend.src.infrastructure.persistence.models import FraudCase
        
        with self.get_session() as session:
            query = session.query(FraudCase)
            
            if status:
                query = query.filter(FraudCase.status == status)
            if severity:
                query = query.filter(FraudCase.severity == severity)
            if client_code:
                query = query.filter(FraudCase.client_code == client_code)
            if date_from:
                query = query.filter(FraudCase.detection_date >= date_from)
            if date_to:
                query = query.filter(FraudCase.detection_date <= date_to)
                
            return query.order_by(FraudCase.detection_date.desc()).limit(limit).all()
    
    def get_pending_cases(self) -> List[Any]:
        """Get all pending fraud cases."""
        from backend.src.infrastructure.persistence.models import FraudCase, FraudStatus
        
        with self.get_session() as session:
            return session.query(FraudCase).filter(
                FraudCase.status == FraudStatus.PENDING
            ).all()
    
    def get_metrics_summary(self, date_from: str = None, date_to: str = None) -> Dict[str, Any]:
        """Get fraud metrics summary."""
        from sqlalchemy import func
        from backend.src.infrastructure.persistence.models import FraudCase, FraudStatus
        
        with self.get_session() as session:
            query = session.query(
                func.count(FraudCase.id).label('total_cases'),
                func.sum(FraudCase.amount_involved).label('total_amount'),
                func.avg(FraudCase.confidence_score).label('avg_confidence')
            )
            
            if date_from:
                query = query.filter(FraudCase.detection_date >= date_from)
            if date_to:
                query = query.filter(FraudCase.detection_date <= date_to)
                
            result = query.first()
            
            # Get status distribution
            status_dist = session.query(
                FraudCase.status,
                func.count(FraudCase.id).label('count')
            ).group_by(FraudCase.status).all()
            
            # Get severity distribution
            severity_dist = session.query(
                FraudCase.severity,
                func.count(FraudCase.id).label('count')
            ).group_by(FraudCase.severity).all()
            
            return {
                'total_cases': result.total_cases or 0,
                'total_amount': float(result.total_amount or 0),
                'avg_confidence': float(result.avg_confidence or 0),
                'status_distribution': {str(s.status): s.count for s in status_dist},
                'severity_distribution': {str(s.severity): s.count for s in severity_dist}
            }
    
    def cleanup(self):
        """Clean up database connections."""
        self.SessionLocal.remove()
        self.engine.dispose()
        logger.info("Database connections cleaned up")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup()


# Singleton instance
_db_context: Optional[FraudDetectionDbContext] = None


def get_db_context() -> FraudDetectionDbContext:
    """Get or create the database context singleton."""
    global _db_context
    if _db_context is None:
        _db_context = FraudDetectionDbContext()
    return _db_context


def init_database():
    """Initialize the database with all required tables."""
    db_context = get_db_context()
    db_context.create_database()
    logger.info("Database initialization completed")