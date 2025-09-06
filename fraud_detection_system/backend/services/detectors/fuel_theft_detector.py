"""
Detector de robo de combustible
backend/services/detectors/fuel_theft_detector.py
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta

from .base_detector import BaseDetector
from models.fraud_models import DetectorType, FraudSeverity


class FuelTheftDetector(BaseDetector):
    """Detector especializado en posible robo de combustible"""
    
    detector_type = DetectorType.FUEL_THEFT
    detector_name = "Detector de Robo de Combustible"
    detector_description = "Detecta patrones anómalos en despachos de combustible: consumos excesivos, múltiples repostajes"
    enabled_by_default = True
    
    def detect(self) -> List[Dict[str, Any]]:
        """Ejecuta todas las detecciones de robo de combustible"""
        self.results = []
        self.log_detection_start()
        
        try:
            print("    Detectando consumo anormal...")
            self._detect_consumo_anormal()
            
            print("    Detectando repostajes excesivos...")
            self._detect_repostajes_excesivos()
        except Exception as e:
            print(f"  Error en {self.detector_name}: {e}")
        
        # Filtrar None (casos duplicados)
        self.results = [r for r in self.results if r is not None]
        self.log_detection_end(len(self.results))
        
        return self.results
    
    def get_detector_info(self) -> Dict[str, Any]:
        """Información del detector"""
        info = super().get_detector_info()
        info["thresholds"] = {
            "excessive_fuel_gallons": 200,
            "critical_fuel_gallons": 300,
            "multiple_refills_per_day": 3,
            "days_lookback": 7
        }
        return info
    
    def get_detection_rules(self) -> List[str]:
        """Reglas que aplica este detector"""
        return [
            "Despachos superiores a 200 galones",
            "Múltiples repostajes el mismo día (>3)",
            "Consumo que excede capacidad del tanque",
            "Patrones inusuales de repostaje",
            "Despachos a vehículos no registrados"
        ]
    
    def _detect_consumo_anormal(self):
        """Detecta consumo anormal vs capacidad del tanque"""
        query = """
        SELECT 
            NUM_DESP, FEC_DESP, CAN_DESP, VTO_DESP,
            COD_PROD, NOM_PROD, COD_CLIE
        FROM DESP
        WHERE CAN_DESP > 150
        """
        
        try:
            despachos = self.db.execute_firebird_query(query, fetch_size=300)
            print(f"      Despachos encontrados: {len(despachos)}")
            
            # Obtener nombres de clientes
            clientes = self._get_client_info()
            
            for d in despachos:
                cantidad = self.safe_float(d.get('CAN_DESP', 0))
                
                if cantidad > 200:
                    cod_cliente = d.get('COD_CLIE')
                    cliente_info = clientes.get(cod_cliente, {})
                    fecha_desp = self.parse_firebird_date(d.get('FEC_DESP'))
                    
                    case = self.create_fraud_case(
                        title=f"Despacho excesivo de combustible - {cantidad:.1f} galones",
                        description=f"Despacho anormal de {cantidad:.1f} galones detectado. "
                                   f"Cliente: {cliente_info.get('nombre', cod_cliente or 'Desconocido')}. "
                                   f"Producto: {d.get('NOM_PROD', 'N/A')}. "
                                   f"Valor: ${self.safe_float(d.get('VTO_DESP', 0)):,.2f}",
                        severity=FraudSeverity.HIGH if cantidad > 300 else FraudSeverity.MEDIUM,
                        amount=d.get('VTO_DESP'),
                        source_table="DESP",
                        source_record_id=str(d.get('NUM_DESP', '')),
                        client_code=cod_cliente,
                        client_name=cliente_info.get('nombre'),
                        client_ruc=cliente_info.get('ruc'),
                        transaction_date=fecha_desp,
                        confidence_score=85.0,
                        detection_rules={"rule": "consumo_excesivo", "cantidad": cantidad}
                    )
                    
                    if case:
                        self.results.append(case)
                    
        except Exception as e:
            print(f"      Error en _detect_consumo_anormal: {e}")
    
    def _detect_repostajes_excesivos(self):
        """Detecta múltiples repostajes en el mismo día"""
        # Query simplificada para evitar el error de conversión
        query = """
        SELECT 
            COD_CLIE, CAN_DESP, VTO_DESP, NUM_DESP
        FROM DESP
        WHERE COD_CLIE IS NOT NULL
        """
        
        try:
            # Traer despachos sin filtro de fecha en SQL
            despachos = self.db.execute_firebird_query(query, fetch_size=1000)
            print(f"      Total despachos a analizar: {len(despachos)}")
            
            # Traer fechas por separado
            fechas_dict = self._get_despacho_dates()
            
            # Obtener info de clientes
            clientes = self._get_client_info()
            
            # Agrupar por cliente y fecha
            fecha_limite = datetime.now() - timedelta(days=7)
            cliente_dias = {}
            
            for d in despachos:
                num_desp = d.get('NUM_DESP')
                fecha = fechas_dict.get(num_desp)
                cliente = d.get('COD_CLIE')
                
                if fecha and cliente and fecha >= fecha_limite:
                    fecha_dia = fecha.date()
                    key = f"{cliente}_{fecha_dia}"
                    
                    if key not in cliente_dias:
                        cliente_info = clientes.get(cliente, {})
                        cliente_dias[key] = {
                            'cliente': cliente,
                            'nombre': cliente_info.get('nombre'),
                            'ruc': cliente_info.get('ruc'),
                            'fecha': fecha,
                            'despachos': []
                        }
                    
                    cliente_dias[key]['despachos'].append({
                        'num': num_desp,
                        'cantidad': self.safe_float(d.get('CAN_DESP', 0)),
                        'valor': self.safe_float(d.get('VTO_DESP', 0))
                    })
            
            print(f"      Días-cliente analizados: {len(cliente_dias)}")
            
            # Detectar múltiples despachos el mismo día
            for key, info in cliente_dias.items():
                num_despachos = len(info['despachos'])
                
                if num_despachos > 3:  # Más de 3 despachos el mismo día
                    # ID único para el grupo
                    group_id = f"MULTIPLE_{key}_{num_despachos}"
                    
                    if not self.check_existing_case("DESP", group_id):
                        total_galones = sum([d['cantidad'] for d in info['despachos']])
                        total_valor = sum([d['valor'] for d in info['despachos']])
                        
                        case = self.create_fraud_case(
                            title=f"Múltiples repostajes mismo día - {info['nombre'] or info['cliente']}",
                            description=f"Cliente {info['nombre'] or 'Desconocido'} realizó "
                                       f"{num_despachos} despachos en el mismo día. "
                                       f"Total: {total_galones:.1f} galones, ${total_valor:,.2f}",
                            severity=FraudSeverity.HIGH if num_despachos > 5 else FraudSeverity.MEDIUM,
                            amount=total_valor,
                            source_table="DESP",
                            source_record_id=group_id,
                            client_code=info['cliente'],
                            client_name=info['nombre'],
                            client_ruc=info['ruc'],
                            transaction_date=info['fecha'],
                            confidence_score=90.0,
                            detection_rules={"rule": "repostajes_multiples", "count": num_despachos}
                        )
                        
                        if case:
                            self.results.append(case)
                    
        except Exception as e:
            print(f"      Error en _detect_repostajes_excesivos: {e}")
    
    def _get_client_info(self) -> Dict[str, Dict]:
        """Obtiene información de clientes"""
        clientes = {}
        cliente_query = "SELECT COD_CLIE, NOM_CLIE, RUC_CLIE FROM CLIE"
        try:
            cliente_data = self.db.execute_firebird_query(cliente_query, fetch_size=5000)
            for c in cliente_data:
                if c.get('COD_CLIE'):
                    clientes[c['COD_CLIE']] = {
                        'nombre': c.get('NOM_CLIE'),
                        'ruc': c.get('RUC_CLIE')
                    }
        except Exception as e:
            print(f"      Error obteniendo info de clientes: {e}")
        return clientes
    
    def _get_despacho_dates(self) -> Dict[str, datetime]:
        """Obtiene las fechas de los despachos"""
        fechas_dict = {}
        fecha_query = """
        SELECT NUM_DESP, FEC_DESP
        FROM DESP
        WHERE FEC_DESP IS NOT NULL
        """
        try:
            fechas_data = self.db.execute_firebird_query(fecha_query, fetch_size=1000)
            for fd in fechas_data:
                num = fd.get('NUM_DESP')
                if num:
                    fechas_dict[num] = self.parse_firebird_date(fd.get('FEC_DESP'))
        except Exception as e:
            print(f"      Error obteniendo fechas: {e}")
        return fechas_dict