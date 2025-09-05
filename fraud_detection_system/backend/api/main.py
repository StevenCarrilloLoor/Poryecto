"""
API FastAPI principal CORREGIDA - backend/api/main.py
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
from services.detectors import FacturasAnomalias, RoboDeCombustible, ManipulacionDatos
from models.fraud_models import FraudStatus, FraudSeverity, DetectorType

# Inicializar FastAPI
app = FastAPI(
    title="Sistema de Detección de Fraude",
    description="API para detección y gestión de fraudes empresariales",
    version="1.0.0",
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
    detector_types: Optional[List[DetectorType]] = None
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
        "timestamp": datetime.utcnow()
    }

@app.get("/api/fraud-cases", response_model=List[FraudCaseResponse], tags=["Fraud Cases"])
async def get_fraud_cases(
    status: Optional[FraudStatus] = None,
    detector_type: Optional[DetectorType] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: int = Query(default=100, le=500)
):
    """Obtiene lista de casos de fraude con filtros opcionales"""
    try:
        # get_fraud_cases ahora retorna diccionarios
        cases = db_context.get_fraud_cases(
            status=status.value if status else None,
            detector_type=detector_type.value if detector_type else None,
            date_from=date_from,
            date_to=date_to,
            limit=limit
        )
        
        # Convertir diccionarios a FraudCaseResponse
        response_cases = []
        for case_dict in cases:
            try:
                # Asegurar que todos los campos requeridos estén presentes
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
    
    # Notificar via WebSocket
    await manager.broadcast(json.dumps({
        "event": "status_updated",
        "case_id": case_id,
        "new_status": request.status.value,
        "user": request.user
    }))
    
    return {"success": True, "message": "Estado actualizado correctamente"}

@app.post("/api/run-detection", tags=["Detection"])
async def run_detection(request: DetectorRunRequest):
    """Ejecuta los detectores de fraude manualmente"""
    try:
        results = []
        detectors = []
        
        # Configurar detectores
        if not request.detector_types or DetectorType.INVOICE_ANOMALY in request.detector_types:
            detectors.append(FacturasAnomalias())
        if not request.detector_types or DetectorType.FUEL_THEFT in request.detector_types:
            detectors.append(RoboDeCombustible())
        if not request.detector_types or DetectorType.DATA_MANIPULATION in request.detector_types:
            detectors.append(ManipulacionDatos())
        
        # Ejecutar detectores
        for detector in detectors:
            detector_results = detector.detect()
            
            for fraud_data in detector_results:
                try:
                    case = db_context.create_fraud_case(fraud_data)
                    results.append({
                        "detector": detector.__class__.__name__,
                        "case_id": case.id,
                        "case_number": case.case_number,
                        "title": case.title
                    })
                    
                    # Preparar datos para WebSocket
                    case_dict = {
                        'id': case.id,
                        'case_number': case.case_number,
                        'detector_type': case.detector_type if isinstance(case.detector_type, str) else case.detector_type,
                        'severity': case.severity if isinstance(case.severity, str) else case.severity,
                        'status': case.status if isinstance(case.status, str) else 'PENDIENTE',
                        'title': case.title or 'Sin título',
                        'description': case.description or '',
                        'amount': case.amount,
                        'client_code': case.client_code or '',
                        'client_name': case.client_name or '',
                        'detection_date': case.detection_date.isoformat() if case.detection_date else datetime.utcnow().isoformat(),
                        'confidence_score': case.confidence_score
                    }
                    
                    await manager.broadcast(json.dumps({
                        "event": "new_case",
                        "case": case_dict
                    }))
                    
                except Exception as e:
                    print(f"Error guardando caso: {e}")
        
        return {
            "success": True,
            "cases_detected": len(results),
            "results": results
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/stats", response_model=DashboardStats, tags=["Dashboard"])
async def get_dashboard_stats():
    """Obtiene estadísticas para el dashboard"""
    try:
        # Obtener estadísticas generales
        stats = db_context.get_fraud_statistics()
        
        # Obtener casos recientes (devuelve diccionarios)
        recent_cases_dicts = db_context.get_fraud_cases(limit=10)
        
        # Convertir a FraudCaseResponse
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
            except:
                continue
        
        # Calcular tasas de detección
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)
        
        today_stats = db_context.get_fraud_statistics(date_from=today_start)
        week_stats = db_context.get_fraud_statistics(date_from=week_start)
        
        return DashboardStats(
            total_cases=stats["total_cases"],
            pending_cases=stats["pending"],
            confirmed_cases=stats["confirmed"],
            rejected_cases=stats["rejected"],
            total_amount=float(stats["total_amount"]),
            cases_by_severity=stats["by_severity"],
            recent_cases=recent_cases,
            detection_rate_today=today_stats["total_cases"],
            detection_rate_week=week_stats["total_cases"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/detector-configs", tags=["Configuration"])
async def get_detector_configs():
    """Obtiene configuraciones de detectores"""
    configs = db_context.get_detector_configs()
    
    return [
        {
            "id": config.id,
            "detector_type": config.detector_type.value if config.detector_type else None,
            "enabled": config.enabled,
            "name": config.name,
            "description": config.description,
            "last_run": config.last_run,
            "config": json.loads(config.config_json) if config.config_json else {}
        }
        for config in configs
    ]

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

# Background task para detección automática
async def automatic_detection():
    """Ejecuta detección automática cada 5 minutos"""
    while True:
        await asyncio.sleep(300)  # 5 minutos
        
        try:
            detectors = [
                FacturasAnomalias(),
                RoboDeCombustible(),
                ManipulacionDatos()
            ]
            
            for detector in detectors:
                try:
                    results = detector.detect()
                    
                    for fraud_data in results:
                        try:
                            case = db_context.create_fraud_case(fraud_data)
                            
                            # Preparar datos para WebSocket
                            case_dict = {
                                'id': case.id,
                                'case_number': case.case_number,
                                'detector_type': getattr(case, 'detector_type', 'UNKNOWN'),
                                'severity': getattr(case, 'severity', 'MEDIO'),
                                'status': getattr(case, 'status', 'PENDIENTE'),
                                'title': getattr(case, 'title', 'Sin título'),
                                'description': getattr(case, 'description', ''),
                                'amount': getattr(case, 'amount', None),
                                'client_code': getattr(case, 'client_code', ''),
                                'client_name': getattr(case, 'client_name', ''),
                                'detection_date': datetime.utcnow().isoformat(),
                                'confidence_score': getattr(case, 'confidence_score', None)
                            }
                            
                            await manager.broadcast(json.dumps({
                                "event": "auto_detection",
                                "case": case_dict
                            }))
                            
                        except Exception as e:
                            print(f"Error en detección automática: {e}")
                            
                except Exception as e:
                    print(f"Error ejecutando detector {detector.__class__.__name__}: {e}")
        
        except Exception as e:
            print(f"Error en ciclo de detección: {e}")

@app.on_event("startup")
async def startup_event():
    """Inicializa tareas en background al iniciar"""
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