# Sistema de Detección de Fraude Empresarial

Sistema profesional de detección de fraude con arquitectura empresarial, diseñado para monitorear y detectar patrones fraudulentos en tiempo real.

## 🚀 Características Principales

### Detectores de Fraude
- **Anomalías de Facturas**: Detecta montos redondos sospechosos, secuencias faltantes, transacciones fuera de horario
- **Robo de Combustible**: Identifica consumo excesivo, patrones de carga sospechosos, violaciones de capacidad
- **Manipulación de Datos**: Detecta cambios masivos, eliminaciones sospechosas, modificaciones no autorizadas
- **Abuso de Cupos**: Monitorea uso excesivo de límites y cupos
- **Fraude en Liquidaciones**: Analiza discrepancias en cierres de caja y liquidaciones

### Arquitectura Técnica
- **Clean Architecture** con Domain-Driven Design
- **Patrón Repository** para acceso a datos
- **Strategy Pattern** para detectores modulares
- **Event Sourcing** para auditoría completa
- **WebSockets** para alertas en tiempo real
- **Circuit Breaker** para resiliencia

## 📋 Requisitos Previos

- Windows 11
- Python 3.10+
- Node.js 18+
- SQL Server 2019+ (instalado en `STEVEN-ALIENWAR\SQLTRABAJO`)
- Firebird 3.0+
- Redis (opcional, para caché)
- Git

## 🛠️ Instalación

### 1. Clonar el Repositorio
```bash
git clone https://github.com/your-org/fraud-detection-system.git
cd fraud-detection-system
```

### 2. Configurar Variables de Entorno
```bash
cp .env.template .env
# Editar .env con tus credenciales
```

### 3. Instalar Backend

```bash
cd backend

# Crear entorno virtual
python -m venv venv
venv\Scripts\activate  # En Windows

# Instalar dependencias
pip install -r requirements.txt

# Inicializar base de datos
python ../scripts/init_database.py

# Ejecutar migraciones
alembic upgrade head
```

### 4. Instalar Frontend

```bash
cd frontend

# Instalar dependencias
npm install

# O con yarn
yarn install
```

## 🚀 Ejecución

### Modo Desarrollo

#### Backend
```bash
cd backend
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd frontend
npm start
```

#### Celery Worker (para tareas asíncronas)
```bash
cd backend
celery -A src.infrastructure.tasks.celery_app worker --loglevel=info
```

#### Celery Beat (para tareas programadas)
```bash
cd backend
celery -A src.infrastructure.tasks.celery_app beat --loglevel=info
```

### Modo Docker (Recomendado)

```bash
docker-compose up -d
```

Esto levantará:
- Backend API (puerto 8000)
- Frontend React (puerto 3000)
- Redis
- Celery Worker y Beat
- Flower (monitoreo Celery, puerto 5555)
- Prometheus (opcional, puerto 9090)
- Grafana (opcional, puerto 3001)

## 📊 Uso del Sistema

### Acceso Web
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/api/docs
- Flower (Celery): http://localhost:5555
- Grafana: http://localhost:3001 (admin/admin)

### Credenciales por Defecto
- **Usuario**: admin
- **Contraseña**: Admin123!

### Flujo de Trabajo

1. **Login**: Autenticarse en el sistema
2. **Dashboard**: Ver métricas y alertas en tiempo real
3. **Casos de Fraude**: Revisar casos detectados
4. **Confirmar/Rechazar**: Tomar decisiones sobre casos
5. **Reportes**: Generar informes ejecutivos

## 🔧 Configuración de VS Code

El proyecto incluye configuración completa para VS Code:

### Debugging
- **F5**: Iniciar FastAPI con debugging
- **Ctrl+Shift+D**: Panel de debugging
- Configuraciones disponibles:
  - Python: FastAPI
  - Python: Celery Worker
  - React: Chrome
  - Full Stack (Backend + Frontend)

### Extensiones Recomendadas
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "ms-vscode.vscode-typescript-tslint-plugin",
    "ms-mssql.mssql",
    "mtxr.sqltools"
  ]
}
```

## 📁 Estructura del Proyecto

```
fraud_detection_system/
├── backend/
│   ├── src/
│   │   ├── domain/           # Lógica de negocio
│   │   ├── application/      # Casos de uso
│   │   ├── infrastructure/   # Implementaciones
│   │   └── api/              # Endpoints REST
│   ├── tests/
│   └── alembic/              # Migraciones
├── frontend/
│   ├── src/
│   │   ├── components/       # Componentes React
│   │   ├── pages/           # Páginas principales
│   │   ├── services/        # Servicios API
│   │   └── context/         # Context providers
│   └── public/
├── scripts/                  # Scripts de utilidad
├── monitoring/              # Configuración Prometheus/Grafana
└── docs/                    # Documentación adicional
```

## 🔍 Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v --cov=src --cov-report=html
```

### Frontend Tests
```bash
cd frontend
npm test
npm run test:coverage
```

## 📈 Monitoreo y Métricas

### Prometheus Metrics
- Endpoint: http://localhost:8000/metrics
- Métricas disponibles:
  - Casos detectados por tipo
  - Tiempo de respuesta de detección
  - Tasa de falsos positivos
  - Uso de recursos

### Logs
Los logs se almacenan en:
- Backend: `backend/logs/fraud_detection.log`
- Celery: `backend/logs/celery.log`

## 🚨 Configuración de Alertas

Las alertas se pueden configurar en:
- Email: Configurar SMTP en `.env`
- WebSocket: Alertas en tiempo real en el dashboard
- Webhook: Integración con sistemas externos

## 🔒 Seguridad

- Autenticación JWT con refresh tokens
- Rate limiting configurable
- Validación de entrada con Pydantic
- Auditoría completa de acciones
- Encriptación de contraseñas con bcrypt
- CORS configurado
- SQL injection prevention con SQLAlchemy

## 🐛 Troubleshooting

### Error de Conexión SQL Server
```bash
# Verificar que SQL Server esté corriendo
sqlcmd -S STEVEN-ALIENWAR\SQLTRABAJO -Q "SELECT @@VERSION"
```

### Error de Conexión Firebird
```bash
# Verificar servicio Firebird
sc query FirebirdServerDefaultInstance
```

### Puerto en Uso
```bash
# Windows - Encontrar proceso usando puerto
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

## 📝 Licencia

Propietario - Todos los derechos reservados

## 👥 Equipo

- Arquitecto de Software
- Desarrolladores Backend
- Desarrolladores Frontend
- Analistas de Fraude

## 📞 Soporte

Para soporte técnico, contactar:
- Email: support@frauddetection.com
- Documentación: http://docs.frauddetection.com

---

**Versión**: 1.0.0  
**Última Actualización**: Enero 2025