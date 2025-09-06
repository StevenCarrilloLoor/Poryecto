"""
API FastAPI principal ACTUALIZADA con Factory Pattern
backend/api/main.py
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import asyncio
import json

from fastapi import FastAPI, HTTPException, Depends, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from enum import Enum

from database.db_context import db_context
# Importar el factory en lugar de detectores individuales
from services.detectors import detector_factory
from models.fraud_models import FraudStatus, FraudSeverity, DetectorType

# Inicializar FastAPI
app = FastAPI(
    title="Sistema de Detección de Fraude",
    description="API para detección y gestión de fraudes empresariales",
    version="2.0.0",  # Actualizada la versión
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos Pydantic
class FraudCaseResponse(BaseModel):
    id: int
    case_number: str
    detector_type: str
    severity: str
    status: str
    title: str
    description: Optional[str]
    amount: Optional[float]
    client_code: Optional[str]
    client_name: Optional[str]
    detection_date: datetime
    confidence_score: Optional[float]
    
    class Config:
        from_attributes = True

class UpdateStatusRequest(BaseModel):
    status: FraudStatus
    notes: Optional[str] = None
    user: str = Field(..., min_length=1)

class DetectorRunRequest(BaseModel):
    detector_types: Optional[List[str]] = None  # Ahora acepta strings
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

class DashboardStats(BaseModel):
    total_cases: int
    pending_cases: int
    confirmed_cases: int
    rejected_cases: int
    total_amount: float
    cases_by_severity: Dict[str, int]
    recent_cases: List[FraudCaseResponse]
    detection_rate_today: int
    detection_rate_week: int

# Nuevo modelo para información de detectores
class DetectorInfo(BaseModel):
    key: str
    name: str
    description: str
    enabled: bool
    rules: List[str]
    thresholds: Optional[Dict[str, Any]] = None

# WebSocket manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

# Endpoints

@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "Fraud Detection System",
        "version": "2.0.0",
        "timestamp": datetime.utcnow(),
        "detectors_available": len(detector_factory.get_available_detectors())
    }

# NUEVO ENDPOINT: Obtener información de detectores disponibles
@app.get("/api/detectors", response_model=List[DetectorInfo], tags=["Detectors"])
async def get_available_detectors():
    """Obtiene información de todos los detectores disponibles"""
    detector_info = detector_factory.get_detector_info()
    
    return [
        DetectorInfo(
            key=info["key"],
            name=info["name"],
            description=info["description"],
            enabled=info["enabled"],
            rules=info["info"]["rules"],
            thresholds=info["info"].get("thresholds")
        )
        for info in detector_info
    ]

# NUEVO ENDPOINT: Recargar detectores (útil para desarrollo)
@app.post("/api/detectors/reload", tags=["Detectors"])
async def reload_detectors():
    """Recarga todos los detectores (útil cuando se agregan nuevos)"""
    try:
        detector_factory.reload_detectors()
        return {
            "success": True,
            "message": "Detectores recargados correctamente",
            "detectors_loaded": len(detector_factory.get_available_detectors())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/fraud-cases", response_model=List[FraudCaseResponse], tags=["Fraud Cases"])
async def get_fraud_cases(
    status: Optional[FraudStatus] = None,
    detector_type: Optional[str] = None,  # Ahora acepta string
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: int = Query(default=100, le=500)
):
    """Obtiene lista de casos de fraude con filtros opcionales"""
    try:
        cases = db_context.get_fraud_cases(
            status=status.value if status else None,
            detector_type=detector_type,  # Ya es string
            date_from=date_from,
            date_to=date_to,
            limit=limit
        )
        
        response_cases = []
        for case_dict in cases:
            try:
                response_data = {
                    'id': case_dict.get('id'),
                    'case_number': case_dict.get('case_number', ''),
                    'detector_type': case_dict.get('detector_type', 'UNKNOWN'),
                    'severity': case_dict.get('severity', 'MEDIO'),
                    'status': case_dict.get('status', 'PENDIENTE'),
                    'title': case_dict.get('title', 'Sin título'),
                    'description': case_dict.get('description'),
                    'amount': case_dict.get('amount'),
                    'client_code': case_dict.get('client_code'),
                    'client_name': case_dict.get('client_name'),
                    'detection_date': case_dict.get('detection_date', datetime.utcnow()),
                    'confidence_score': case_dict.get('confidence_score')
                }
                response_cases.append(FraudCaseResponse(**response_data))
            except Exception as e:
                print(f"Error procesando caso: {e}")
                continue
        
        return response_cases
    
    except Exception as e:
        print(f"Error en get_fraud_cases: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/fraud-cases/{case_id}", response_model=FraudCaseResponse, tags=["Fraud Cases"])
async def get_fraud_case(case_id: int):
    """Obtiene un caso de fraude específico"""
    cases = db_context.get_fraud_cases(limit=1)
    
    for case_dict in cases:
        if case_dict.get('id') == case_id:
            response_data = {
                'id': case_dict.get('id'),
                'case_number': case_dict.get('case_number', ''),
                'detector_type': case_dict.get('detector_type', 'UNKNOWN'),
                'severity': case_dict.get('severity', 'MEDIO'),
                'status': case_dict.get('status', 'PENDIENTE'),
                'title': case_dict.get('title', 'Sin título'),
                'description': case_dict.get('description'),
                'amount': case_dict.get('amount'),
                'client_code': case_dict.get('client_code'),
                'client_name': case_dict.get('client_name'),
                'detection_date': case_dict.get('detection_date', datetime.utcnow()),
                'confidence_score': case_dict.get('confidence_score')
            }
            return FraudCaseResponse(**response_data)
    
    raise HTTPException(status_code=404, detail="Caso no encontrado")

@app.patch("/api/fraud-cases/{case_id}/status", tags=["Fraud Cases"])
async def update_fraud_case_status(case_id: int, request: UpdateStatusRequest):
    """Actualiza el estado de un caso de fraude"""
    success = db_context.update_fraud_case_status(
        case_id=case_id,
        new_status=request.status.value,
        user=request.user,
        notes=request.notes
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Caso no encontrado")
    
    await manager.broadcast(json.dumps({
        "event": "status_updated",
        "case_id": case_id,
        "new_status": request.status.value,
        "user": request.user
    }))
    
    return {"success": True, "message": "Estado actualizado correctamente"}

@app.post("/api/run-detection", tags=["Detection"])
async def run_detection(request: DetectorRunRequest = None):
    """Ejecuta los detectores de fraude manualmente - USANDO FACTORY"""
    try:
        if request is None:
            request = DetectorRunRequest()
        
        print("\n=== Iniciando detección manual ===")
        print(f"Detectores disponibles: {detector_factory.get_available_detectors()}")
        
        # Determinar qué detectores ejecutar
        if request.detector_types:
            print(f"Ejecutando detectores específicos: {request.detector_types}")
            detection_results = detector_factory.run_specific_detectors(request.detector_types)
        else:
            print("Ejecutando todos los detectores...")
            detection_results = detector_factory.run_all_detectors()
        
        # Procesar resultados y guardar en base de datos
        all_results = []
        for detector_type, fraud_cases in detection_results.items():
            print(f"\nProcesando resultados de {detector_type}: {len(fraud_cases)} casos")
            
            for fraud_data in fraud_cases:
                if fraud_data:  # Ignorar None (duplicados)
                    try:
                        case = db_context.create_fraud_case(fraud_data)
                        if case:
                            all_results.append({
                                "detector": detector_type,
                                "case_id": case.id,
                                "case_number": case.case_number,
                                "title": case.title[:50] if case.title else "Sin título"
                            })
                            
                            # Notificar via WebSocket
                            case_dict = {
                                'id': case.id,
                                'case_number': case.case_number,
                                'detector_type': detector_type,
                                'title': case.title or 'Sin título'
                            }
                            
                            await manager.broadcast(json.dumps({
                                "event": "new_case",
                                "case": case_dict
                            }))
                            
                    except Exception as e:
                        print(f"    Error guardando caso: {e}")
        
        print(f"\n=== Detección completada. Total casos nuevos: {len(all_results)} ===")
        
        return {
            "success": True,
            "cases_detected": len(all_results),
            "results": all_results,
            "detectors_run": list(detection_results.keys())
        }
    
    except Exception as e:
        print(f"Error en run_detection: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "cases_detected": 0,
            "results": [],
            "error": str(e)
        }

@app.get("/api/dashboard/stats", response_model=DashboardStats, tags=["Dashboard"])
async def get_dashboard_stats():
    """Obtiene estadísticas para el dashboard"""
    try:
        print("\nObteniendo estadísticas del dashboard...")
        
        stats = db_context.get_fraud_statistics()
        print(f"  Estadísticas base: {stats}")
        
        cases_by_severity = {
            "CRITICO": 0,
            "ALTO": 0,
            "MEDIO": 0,
            "BAJO": 0
        }
        
        if "by_severity" in stats and stats["by_severity"]:
            for key, value in stats["by_severity"].items():
                if key in cases_by_severity:
                    cases_by_severity[key] = value
        
        recent_cases_dicts = db_context.get_fraud_cases(limit=10)
        
        recent_cases = []
        for case_dict in recent_cases_dicts:
            try:
                response_data = {
                    'id': case_dict.get('id'),
                    'case_number': case_dict.get('case_number', ''),
                    'detector_type': case_dict.get('detector_type', 'UNKNOWN'),
                    'severity': case_dict.get('severity', 'MEDIO'),
                    'status': case_dict.get('status', 'PENDIENTE'),
                    'title': case_dict.get('title', 'Sin título'),
                    'description': case_dict.get('description'),
                    'amount': case_dict.get('amount'),
                    'client_code': case_dict.get('client_code'),
                    'client_name': case_dict.get('client_name'),
                    'detection_date': case_dict.get('detection_date', datetime.utcnow()),
                    'confidence_score': case_dict.get('confidence_score')
                }
                recent_cases.append(FraudCaseResponse(**response_data))
            except Exception as e:
                print(f"  Error procesando caso reciente: {e}")
                continue
        
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)
        
        today_stats = db_context.get_fraud_statistics(date_from=today_start)
        week_stats = db_context.get_fraud_statistics(date_from=week_start)
        
        response = DashboardStats(
            total_cases=stats.get("total_cases", 0),
            pending_cases=stats.get("pending", 0),
            confirmed_cases=stats.get("confirmed", 0),
            rejected_cases=stats.get("rejected", 0),
            total_amount=float(stats.get("total_amount", 0)),
            cases_by_severity=cases_by_severity,
            recent_cases=recent_cases,
            detection_rate_today=today_stats.get("total_cases", 0),
            detection_rate_week=week_stats.get("total_cases", 0)
        )
        
        return response
    
    except Exception as e:
        print(f"Error en get_dashboard_stats: {e}")
        import traceback
        traceback.print_exc()
        
        return DashboardStats(
            total_cases=0,
            pending_cases=0,
            confirmed_cases=0,
            rejected_cases=0,
            total_amount=0.0,
            cases_by_severity={"CRITICO": 0, "ALTO": 0, "MEDIO": 0, "BAJO": 0},
            recent_cases=[],
            detection_rate_today=0,
            detection_rate_week=0
        )

@app.get("/api/detector-configs", tags=["Configuration"])
async def get_detector_configs():
    """Obtiene configuraciones de detectores desde la base de datos"""
    try:
        configs = db_context.get_detector_configs()
        
        return [
            {
                "id": config.id,
                "detector_type": config.detector_type.value if hasattr(config.detector_type, 'value') else config.detector_type,
                "enabled": config.enabled,
                "name": config.name,
                "description": config.description,
                "last_run": config.last_run,
                "config": json.loads(config.config_json) if config.config_json else {}
            }
            for config in configs
        ]
    except Exception as e:
        print(f"Error en get_detector_configs: {e}")
        return []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket para notificaciones en tiempo real"""
    await manager.connect(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            
            if data == "ping":
                await websocket.send_text("pong")
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Background task para detección automática con Factory
async def automatic_detection():
    """Ejecuta detección automática cada 5 minutos usando Factory"""
    while True:
        await asyncio.sleep(300)  # 5 minutos
        
        try:
            print("\n=== Ejecutando detección automática ===")
            
            # Usar factory para obtener todos los detectores habilitados
            detection_results = detector_factory.run_all_detectors()
            
            for detector_type, fraud_cases in detection_results.items():
                for fraud_data in fraud_cases:
                    if fraud_data:  # Ignorar None
                        try:
                            case = db_context.create_fraud_case(fraud_data)
                            
                            if case:
                                case_dict = {
                                    'id': case.id,
                                    'case_number': case.case_number,
                                    'detector_type': detector_type,
                                    'title': getattr(case, 'title', 'Sin título')
                                }
                                
                                await manager.broadcast(json.dumps({
                                    "event": "auto_detection",
                                    "case": case_dict
                                }))
                                
                        except Exception as e:
                            print(f"Error en detección automática: {e}")
                            
        except Exception as e:
            print(f"Error en ciclo de detección: {e}")

@app.on_event("startup")
async def startup_event():
    """Inicializa tareas en background al iniciar"""
    # Mostrar detectores disponibles al inicio
    print("\n=== Sistema de Detección de Fraude ===")
    print(f"Detectores disponibles: {detector_factory.get_available_detectors()}")
    print("=====================================\n")
    
    # Iniciar detección automática
    asyncio.create_task(automatic_detection())
    print("✓ Sistema de detección de fraude iniciado")

@app.on_event("shutdown")
async def shutdown_event():
    """Limpieza al cerrar la aplicación"""
    db_context.close()
    print("✓ Sistema de detección de fraude detenido")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )