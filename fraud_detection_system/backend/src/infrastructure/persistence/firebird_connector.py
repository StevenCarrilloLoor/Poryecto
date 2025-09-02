# backend/src/infrastructure/persistence/firebird_connector.py

import logging
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import fdb
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.src.config.settings import Settings

logger = logging.getLogger(__name__)


class FirebirdConnector:
    """
    Connector for Firebird database with connection pooling and retry logic.
    Read-only access to the CONTAC.fdb database.
    """
    
    def __init__(self):
        self.settings = Settings()
        self.connection_params = {
            'dsn': f"{self.settings.FIREBIRD_HOST}:{self.settings.FIREBIRD_DATABASE}",
            'user': self.settings.FIREBIRD_USERNAME,
            'password': self.settings.FIREBIRD_PASSWORD,
            'charset': self.settings.FIREBIRD_CHARSET
        }
        self._connection = None
        
    @contextmanager
    def get_connection(self):
        """Context manager for Firebird connections."""
        conn = None
        try:
            conn = fdb.connect(**self.connection_params)
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Firebird connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def execute_query(self, query: str, params: Tuple = None) -> List[Dict[str, Any]]:
        """Execute a query and return results as list of dictionaries."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            
            # Get column names
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            # Fetch all results
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
                
            cursor.close()
            return results
    
    def get_transactions(
        self,
        date_from: datetime = None,
        date_to: datetime = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get transactions from DCTO table."""
        query = """
            SELECT FIRST ? 
                SEC_DCTO, TIP_DCTO, NUM_DCTO, FEC_DCTO, COD_CLIE,
                TNI_DCTO, TSI_DCTO, IVA_DCTO, DSC_DCTO,
                COD_VEND, COD_PAGO, COD_BODE, PLA_DCTO,
                COD_XUSUA, FEC_XDCTO, NIP_XDCTO
            FROM DCTO
            WHERE 1=1
        """
        params = [limit]
        
        if date_from:
            query += " AND FEC_DCTO >= ?"
            params.append(date_from)
        if date_to:
            query += " AND FEC_DCTO <= ?"
            params.append(date_to)
            
        query += " ORDER BY FEC_DCTO DESC"
        
        return self.execute_query(query, tuple(params))
    
    def get_fuel_dispatches(
        self,
        date_from: datetime = None,
        date_to: datetime = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get fuel dispatches from DESP table."""
        query = """
            SELECT FIRST ?
                NUM_DESP, COD_MANG, FEC_DESP, VTO_DESP, CAN_DESP,
                VUN_DESP, COD_PROD, NOM_PROD, SUR_DESP, COD_CLIE,
                PLA_PUNT, COD_CHOF
            FROM DESP
            WHERE 1=1
        """
        params = [limit]
        
        if date_from:
            query += " AND FIN_DESP >= ?"
            params.append(date_from)
        if date_to:
            query += " AND FIN_DESP <= ?"
            params.append(date_to)
            
        query += " ORDER BY FIN_DESP DESC"
        
        return self.execute_query(query, tuple(params))
    
    def get_tank_movements(
        self,
        date_from: datetime = None,
        date_to: datetime = None
    ) -> List[Dict[str, Any]]:
        """Get tank movements from TANQ_MOV table."""
        query = """
            SELECT 
                NUM_TQMV, COD_TANQ, FEC_TQMV,
                SCO_TQMV, SAG_TQMV, TEM_TQMV,
                SCO_GAL_TQMV, SAG_GAL_TQMV
            FROM TANQ_MOV
            WHERE 1=1
        """
        params = []
        
        if date_from:
            query += " AND FEC_TQMV >= ?"
            params.append(date_from)
        if date_to:
            query += " AND FEC_TQMV <= ?"
            params.append(date_to)
            
        query += " ORDER BY FEC_TQMV DESC"
        
        return self.execute_query(query, tuple(params))
    
    def get_client_info(self, client_code: str) -> Optional[Dict[str, Any]]:
        """Get client information."""
        query = """
            SELECT 
                COD_CLIE, NOM_CLIE, RUC_CLIE, DCA_CLIE,
                TE1_CLIE, CRE_CLIE, CUP_CLIE, DEF_CUP_CLIE,
                VAL_CUP_CLIE, CON_CUP_CLIE
            FROM CLIE
            WHERE COD_CLIE = ?
        """
        
        results = self.execute_query(query, (client_code,))
        return results[0] if results else None
    
    def get_vehicle_info(self, plate: str) -> Optional[Dict[str, Any]]:
        """Get vehicle/plate information."""
        query = """
            SELECT 
                CODI_PLA, RUC_PLA, DET_PLA, CRE_PLA,
                CUP_PLA, DEF_CUP_PLA, VAL_CUP_PLA
            FROM PLACA
            WHERE CODI_PLA = ?
        """
        
        results = self.execute_query(query, (plate,))
        return results[0] if results else None
    
    def get_liquidations(
        self,
        date_from: datetime = None,
        date_to: datetime = None
    ) -> List[Dict[str, Any]]:
        """Get liquidations from LIQU table."""
        query = """
            SELECT 
                NUM_LIQU, COD_CLIE, FEC_LIQU,
                TDE_LIQU, TCR_LIQU, EDE_LIQU, ECR_LIQU,
                GAS_LIQU, FAL_LIQU, SOB_LIQU,
                TAR_LIQU, CON_LIQU, CRE_LIQU, DIF_LIQU
            FROM LIQU
            WHERE 1=1
        """
        params = []
        
        if date_from:
            query += " AND FEC_LIQU >= ?"
            params.append(date_from)
        if date_to:
            query += " AND FEC_LIQU <= ?"
            params.append(date_to)
            
        query += " ORDER BY FEC_LIQU DESC"
        
        return self.execute_query(query, tuple(params))
    
    def get_rfid_movements(
        self,
        date_from: datetime = None,
        date_to: datetime = None
    ) -> List[Dict[str, Any]]:
        """Get RFID movements from RFID_COMB table."""
        query = """
            SELECT 
                SEC_RFID, NUM_RFID, COD_RFID, EST_RFID,
                SAL_RFID, CUP_RFID, CCU_RFID, CAN_PRO_RFID,
                KLM_RFID, COD_ITEM, FEC_RFID, SEC_DCTO
            FROM RFID_COMB
            WHERE 1=1
        """
        params = []
        
        if date_from:
            query += " AND FEC_RFID >= ?"
            params.append(date_from)
        if date_to:
            query += " AND FEC_RFID <= ?"
            params.append(date_to)
            
        query += " ORDER BY FEC_RFID DESC"
        
        return self.execute_query(query, tuple(params))
    
    def get_audit_logs(
        self,
        table_name: str = None,
        date_from: datetime = None,
        date_to: datetime = None
    ) -> List[Dict[str, Any]]:
        """Get audit logs from LOG table."""
        query = """
            SELECT 
                NUM_LOG, USU_LOG, TAB_LOG, DIR_LOG,
                FEC_LOG, ACC_LOG
            FROM LOG
            WHERE 1=1
        """
        params = []
        
        if table_name:
            query += " AND TAB_LOG = ?"
            params.append(table_name)
        if date_from:
            query += " AND FEC_LOG >= ?"
            params.append(date_from)
        if date_to:
            query += " AND FEC_LOG <= ?"
            params.append(date_to)
            
        query += " ORDER BY FEC_LOG DESC"
        
        return self.execute_query(query, tuple(params))
    
    def check_invoice_sequence(
        self,
        doc_type: str,
        date_from: datetime,
        date_to: datetime
    ) -> List[Dict[str, Any]]:
        """Check for missing invoice sequences."""
        query = """
            SELECT 
                TIP_DCTO, NUM_DCTO, FEC_DCTO
            FROM DCTO
            WHERE TIP_DCTO = ?
                AND FEC_DCTO BETWEEN ? AND ?
            ORDER BY CAST(NUM_DCTO AS INTEGER)
        """
        
        return self.execute_query(query, (doc_type, date_from, date_to))
    
    def get_night_transactions(
        self,
        start_hour: int = 22,
        end_hour: int = 6
    ) -> List[Dict[str, Any]]:
        """Get transactions made during night hours."""
        query = """
            SELECT 
                SEC_DCTO, TIP_DCTO, NUM_DCTO, FEC_DCTO,
                COD_CLIE, TNI_DCTO, TSI_DCTO, IVA_DCTO,
                COD_XUSUA, FEC_XDCTO
            FROM DCTO
            WHERE EXTRACT(HOUR FROM FEC_DCTO) >= ? 
                OR EXTRACT(HOUR FROM FEC_DCTO) < ?
            ORDER BY FEC_DCTO DESC
        """
        
        return self.execute_query(query, (start_hour, end_hour))
    
    def get_round_amount_transactions(
        self,
        threshold: float = 100.0
    ) -> List[Dict[str, Any]]:
        """Get transactions with suspiciously round amounts."""
        query = """
            SELECT 
                SEC_DCTO, TIP_DCTO, NUM_DCTO, FEC_DCTO,
                COD_CLIE, TNI_DCTO, TSI_DCTO, IVA_DCTO,
                (TNI_DCTO + TSI_DCTO + IVA_DCTO) AS TOTAL
            FROM DCTO
            WHERE MOD(TNI_DCTO + TSI_DCTO + IVA_DCTO, ?) = 0
                AND (TNI_DCTO + TSI_DCTO + IVA_DCTO) > ?
            ORDER BY FEC_DCTO DESC
        """
        
        return self.execute_query(query, (threshold, threshold))
    
    def get_table_structure(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table structure information."""
        query = """
            SELECT 
                rf.RDB$FIELD_NAME as COLUMN_NAME,
                CASE f.RDB$FIELD_TYPE
                    WHEN 261 THEN 'BLOB'
                    WHEN 14 THEN 'CHAR'
                    WHEN 40 THEN 'CSTRING' 
                    WHEN 27 THEN 'DOUBLE'
                    WHEN 10 THEN 'FLOAT'
                    WHEN 16 THEN 'BIGINT'
                    WHEN 8 THEN 'INTEGER' 
                    WHEN 7 THEN 'SMALLINT'
                    WHEN 12 THEN 'DATE'
                    WHEN 13 THEN 'TIME'
                    WHEN 35 THEN 'TIMESTAMP'
                    WHEN 37 THEN 'VARCHAR'
                    ELSE 'OTHER'
                END as DATA_TYPE,
                f.RDB$FIELD_LENGTH as FIELD_LENGTH
            FROM RDB$RELATION_FIELDS rf
            JOIN RDB$FIELDS f ON rf.RDB$FIELD_SOURCE = f.RDB$FIELD_NAME
            WHERE TRIM(rf.RDB$RELATION_NAME) = ?
            ORDER BY rf.RDB$FIELD_POSITION
        """
        
        return self.execute_query(query, (table_name.upper(),))
    
    def test_connection(self) -> bool:
        """Test if the Firebird connection is working."""
        try:
            query = "SELECT CURRENT_TIMESTAMP FROM RDB$DATABASE"
            result = self.execute_query(query)
            logger.info(f"Firebird connection successful: {result[0]}")
            return True
        except Exception as e:
            logger.error(f"Firebird connection failed: {e}")
            return False


# Singleton instance
_firebird_connector: Optional[FirebirdConnector] = None


def get_firebird_connector() -> FirebirdConnector:
    """Get or create the Firebird connector singleton."""
    global _firebird_connector
    if _firebird_connector is None:
        _firebird_connector = FirebirdConnector()
    return _firebird_connector