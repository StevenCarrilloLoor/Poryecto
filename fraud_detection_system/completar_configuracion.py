#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para Completar Configuraciones Faltantes
===============================================

Este script crea y configura todos los archivos faltantes del proyecto:
- alembic.ini (configuración de migraciones)
- .gitignore (reglas de exclusión de git)
- frontend/.env (variables de entorno del frontend)
- frontend/.eslintrc.json (configuración de ESLint)
- frontend/.prettierrc (configuración de Prettier)
- frontend/tsconfig.node.json (configuración TypeScript para Vite)
- README.md (documentación del proyecto)

Uso:
    python completar_configuracion.py

Requisitos:
    - Ejecutar desde la raíz del proyecto
"""

import os
import sys
from pathlib import Path
import platform

# Colores para consola
class Colors:
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'

def print_header(text: str):
    """Imprime un encabezado."""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{text.center(70)}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'='*70}{Colors.RESET}\n")

def print_success(text: str):
    """Imprime mensaje de éxito."""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")

def print_warning(text: str):
    """Imprime mensaje de advertencia."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")

def print_error(text: str):
    """Imprime mensaje de error."""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")

# ============================================================================
# CONTENIDOS DE ARCHIVOS
# ============================================================================

ALEMBIC_INI_CONTENT = """# Alembic Configuration File

[alembic]
# Path to migration scripts
script_location = backend/migrations

# Template file for generating migration files
# file_template = %%(rev)s_%%(slug)s

# Timezone for timestamps (optional)
# timezone = UTC

# Max length of characters to apply to the "slug" field
# truncate_slug_length = 40

# Set to 'true' to run the environment during the 'revision' command
# revision_environment = false

# Set to 'true' to allow .pyc and .pyo files without a source .py file
# sourceless = false

# Version location specification
# version_locations = %(here)s/bar:%(here)s/bat:backend/migrations/versions

# Version path separator
version_path_separator = os  # Use os.pathsep. Default configuration used for new projects.

# Output encoding used when revision files are written
# output_encoding = utf-8

# SQLAlchemy URL (overridden by env.py from .env file)
sqlalchemy.url = driver://user:pass@localhost/dbname

[post_write_hooks]
# Post-write hook for code formatting with black
hooks = black
black.type = console_scripts
black.entrypoint = black
black.options = -l 88 REVISION_SCRIPT_FILENAME

# Logging configuration
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""

GITIGNORE_CONTENT = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
venv32/
env/
ENV/
.venv
pip-log.txt
pip-delete-this-directory.txt
.pytest_cache/
.coverage
htmlcov/
.tox/
.mypy_cache/
.dmypy.json
dmypy.json
*.log

# Node
node_modules/
dist/
build/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.npm
.eslintcache
*.tsbuildinfo

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Environment
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Database
*.db
*.sqlite
*.sqlite3
instance/
backend/migrations/versions/

# Temporary files
*.tmp
*.bak
*.backup
temp/
tmp/

# OS
Thumbs.db
Desktop.ini

# Build tools
*.exe
rustup-init.exe

# Personal config
set_venv32_default.py
Comandos.txt
"""

FRONTEND_ENV_CONTENT = """# Frontend Environment Variables
# Vite requires variables to start with VITE_ prefix

# Backend API URL
VITE_API_URL=http://localhost:8000

# WebSocket URL
VITE_WS_URL=ws://localhost:8000/ws

# Environment
VITE_APP_ENV=development
"""

ESLINTRC_CONTENT = """{
  "root": true,
  "env": {
    "browser": true,
    "es2020": true
  },
  "extends": [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:react-hooks/recommended"
  ],
  "ignorePatterns": ["dist", ".eslintrc.cjs"],
  "parser": "@typescript-eslint/parser",
  "plugins": ["react-refresh"],
  "rules": {
    "react-refresh/only-export-components": [
      "warn",
      { "allowConstantExport": true }
    ],
    "@typescript-eslint/no-explicit-any": "warn",
    "@typescript-eslint/no-unused-vars": [
      "warn",
      { "argsIgnorePattern": "^_" }
    ]
  }
}
"""

PRETTIERRC_CONTENT = """{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false,
  "arrowParens": "avoid",
  "endOfLine": "lf"
}
"""

TSCONFIG_NODE_CONTENT = """{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
"""

README_CONTENT = """# Sistema de Detección de Fraude

Sistema empresarial automatizado para la detección, monitoreo y gestión de casos de fraude en transacciones comerciales.

## 🎯 Características Principales

- **Detección Automática**: Múltiples algoritmos de detección ejecutándose cada 5 minutos
- **Dashboard en Tiempo Real**: Visualización de estadísticas y casos con WebSockets
- **Arquitectura Dual de Bases de Datos**: SQL Server para casos nuevos + Firebird para datos legacy
- **Detectores Extensibles**: Sistema de plugins para agregar nuevos algoritmos fácilmente
- **Gestión Completa de Casos**: Actualización de estados, notas, confirmaciones y auditoría
- **Interfaz Moderna**: React + Material-UI con componentes responsivos

## 🛠️ Tecnologías

### Backend
- **FastAPI** - Framework web asíncrono
- **SQLAlchemy** - ORM para manejo de base de datos
- **Alembic** - Migraciones de base de datos
- **WebSockets** - Comunicación en tiempo real
- **Pydantic** - Validación de datos

### Frontend
- **React 18** - Biblioteca de UI
- **TypeScript** - Tipado estático
- **Material-UI (MUI)** - Componentes de interfaz
- **Vite** - Build tool ultrarrápido
- **TanStack Query** - Gestión de estado del servidor
- **Socket.io** - Cliente WebSocket
- **Recharts** - Gráficos y visualizaciones

### Bases de Datos
- **SQL Server** - Almacenamiento principal de casos de fraude
- **Firebird** - Conexión a sistema ERP legacy

## 📦 Instalación

### Opción 1: Instalación Automática (Recomendada)

Ejecute el instalador automático que configurará todo el entorno:

```bash
python setup_automatico.py
```

O simplemente haga doble clic en:
```
INSTALAR.bat
```

El instalador se encargará de:
- Instalar Python 3.11 (32-bit y 64-bit)
- Instalar Node.js
- Instalar SQL Server Express
- Instalar drivers ODBC
- Configurar entornos virtuales
- Instalar todas las dependencias
- Crear base de datos
- Ejecutar migraciones

### Opción 2: Instalación Manual

#### Requisitos Previos
- Python 3.11 (32-bit y 64-bit)
- Node.js 14+
- SQL Server (cualquier edición)
- ODBC Driver 17 para SQL Server
- Firebird ODBC Driver (32-bit)

#### Pasos

1. **Clonar el repositorio**
   ```bash
   git clone <repository-url>
   cd fraud_detection_system
   ```

2. **Crear entornos virtuales**
   ```bash
   # Entorno 64-bit (principal)
   python -m venv venv
   venv\\Scripts\\activate

   # Entorno 32-bit (para Firebird)
   C:\\Python311-32\\python.exe -m venv venv32
   ```

3. **Instalar dependencias Python**
   ```bash
   # En entorno 64-bit
   pip install -r requirements.txt
   ```

4. **Instalar dependencias Node.js**
   ```bash
   cd frontend
   npm install
   ```

5. **Configurar variables de entorno**

   Edite `.env` en la raíz del proyecto con sus configuraciones.

6. **Crear base de datos**
   ```bash
   sqlcmd -S "TU_SERVIDOR\\INSTANCIA" -E -Q "CREATE DATABASE FraudDetectionDB"
   ```

7. **Ejecutar migraciones**
   ```bash
   alembic upgrade head
   ```

## 🚀 Uso

### Iniciar el Sistema Completo

```bash
iniciar_sistema.bat
```

### Iniciar Componentes Por Separado

**Backend (64-bit)**
```bash
iniciar_backend.bat
```

**Backend (32-bit con Firebird)**
```bash
iniciar_backend_32bit.bat
```

**Frontend**
```bash
iniciar_frontend.bat
```

### Acceso

- **Aplicación Web**: http://localhost:5173
- **API Backend**: http://localhost:8000
- **Documentación API**: http://localhost:8000/docs
- **API Alternativa**: http://localhost:8000/redoc

## 📊 Arquitectura

### Detectores de Fraude

El sistema usa un patrón de Factory para cargar dinámicamente detectores:

- **InvoiceAnomalyDetector**: Detecta anomalías en facturas (montos redondos, descuentos excesivos, horarios inusuales)
- **FuelTheftDetector**: Identifica posible robo de combustible
- **DataManipulationDetector**: Detecta manipulación de datos

### Flujo de Detección

1. Scheduler ejecuta detección cada 5 minutos
2. DetectorFactory carga todos los detectores activos
3. Cada detector analiza su conjunto de datos
4. Casos detectados se guardan en SQL Server
5. WebSocket notifica a clientes conectados en tiempo real

### Estructura de Base de Datos

- **FraudCase**: Casos de fraude detectados
- **FraudConfirmation**: Confirmaciones/rechazos de casos
- **DetectorConfig**: Configuración de detectores
- **AuditLog**: Registro de auditoría de todas las acciones
- **FraudMetrics**: Métricas agregadas para reportes

## 🔧 Configuración

### Variables de Entorno Principales

```env
# SQL Server
DB_SERVER=SERVIDOR\\INSTANCIA
DB_DATABASE=FraudDetectionDB
DB_TRUSTED_CONNECTION=yes

# Firebird
FIREBIRD_DSN=DRIVER={Firebird/InterBase(r) driver};DBNAME=...

# API
API_HOST=0.0.0.0
API_PORT=8000

# Seguridad
SECRET_KEY=tu-clave-secreta-aqui

# Detección
DETECTION_INTERVAL_SECONDS=300
DETECTION_BATCH_SIZE=1000
```

## 🧪 Testing

```bash
# Tests Python
pytest

# Tests con cobertura
pytest --cov=backend

# Verificar sistema
python verificar_sistema.py
```

## 📝 Desarrollo

### Agregar Nuevo Detector

1. Crear archivo `mi_detector.py` en `backend/services/detectors/`
2. Heredar de `BaseDetector`
3. Implementar método `detect()`
4. El sistema lo cargará automáticamente

```python
from .base_detector import BaseDetector

class MiDetector(BaseDetector):
    def detect(self) -> int:
        # Tu lógica aquí
        return casos_detectados
```

### Convenciones de Código

- **Python**: Black formatter (88 caracteres)
- **TypeScript**: Prettier + ESLint
- **Git**: Conventional Commits

## 📖 Documentación Adicional

- [INSTRUCCIONES_INSTALACION.md](INSTRUCCIONES_INSTALACION.md) - Guía detallada de instalación
- [DEPENDENCIAS_FALTANTES.md](DEPENDENCIAS_FALTANTES.md) - Análisis de dependencias
- [README_INSTALACION.txt](README_INSTALACION.txt) - Guía rápida

## 🤝 Contribución

1. Fork el proyecto
2. Cree su rama de características (`git checkout -b feature/AmazingFeature`)
3. Commit sus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abra un Pull Request

## 📄 Licencia

Este proyecto es privado y propietario.

## 👥 Autores

- Equipo de Desarrollo - Sistema de Detección de Fraude

## 🙏 Agradecimientos

- FastAPI por el excelente framework
- Material-UI por los componentes de UI
- Comunidad de Python y React

---

**Versión**: 1.0.0
**Última actualización**: 2025-11-17
"""

# ============================================================================
# FUNCIONES PRINCIPALES
# ============================================================================

def create_file(file_path: Path, content: str, description: str) -> bool:
    """Crea un archivo con el contenido especificado."""
    try:
        # Crear directorio si no existe
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Verificar si ya existe
        if file_path.exists():
            print_warning(f"{description} ya existe en: {file_path}")
            response = input(f"  ¿Sobrescribir? (s/n): ")
            if response.lower() not in ['s', 'si', 'sí', 'y', 'yes']:
                print_warning(f"  Saltando {description}")
                return False

            # Crear backup
            backup_path = file_path.with_suffix(file_path.suffix + '.backup')
            file_path.rename(backup_path)
            print_warning(f"  Backup creado: {backup_path}")

        # Escribir archivo
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print_success(f"{description} creado: {file_path}")
        return True

    except Exception as e:
        print_error(f"Error al crear {description}: {e}")
        return False

def main():
    """Función principal."""
    print_header("COMPLETAR CONFIGURACIONES FALTANTES")

    # Obtener rutas
    project_root = Path(__file__).parent.absolute()
    frontend_dir = project_root / 'frontend'

    print(f"Directorio del proyecto: {project_root}\n")

    # Contador de éxitos
    created = 0
    total = 0

    # ========================================================================
    # CONFIGURACIONES DE BACKEND
    # ========================================================================
    print_header("CONFIGURACIONES DE BACKEND")

    # 1. alembic.ini
    total += 1
    if create_file(
        project_root / 'alembic.ini',
        ALEMBIC_INI_CONTENT,
        "alembic.ini"
    ):
        created += 1

    # 2. .gitignore
    total += 1
    if create_file(
        project_root / '.gitignore',
        GITIGNORE_CONTENT,
        ".gitignore"
    ):
        created += 1

    # 3. README.md
    total += 1
    if create_file(
        project_root / 'README.md',
        README_CONTENT,
        "README.md"
    ):
        created += 1

    # ========================================================================
    # CONFIGURACIONES DE FRONTEND
    # ========================================================================
    print_header("CONFIGURACIONES DE FRONTEND")

    if not frontend_dir.exists():
        print_error(f"Directorio frontend no encontrado: {frontend_dir}")
    else:
        # 4. .env
        total += 1
        if create_file(
            frontend_dir / '.env',
            FRONTEND_ENV_CONTENT,
            "frontend/.env"
        ):
            created += 1

        # 5. .eslintrc.json
        total += 1
        if create_file(
            frontend_dir / '.eslintrc.json',
            ESLINTRC_CONTENT,
            "frontend/.eslintrc.json"
        ):
            created += 1

        # 6. .prettierrc
        total += 1
        if create_file(
            frontend_dir / '.prettierrc',
            PRETTIERRC_CONTENT,
            "frontend/.prettierrc"
        ):
            created += 1

        # 7. tsconfig.node.json
        total += 1
        if create_file(
            frontend_dir / 'tsconfig.node.json',
            TSCONFIG_NODE_CONTENT,
            "frontend/tsconfig.node.json"
        ):
            created += 1

    # ========================================================================
    # RESUMEN
    # ========================================================================
    print_header("RESUMEN")

    print(f"Archivos creados/actualizados: {created}/{total}")

    if created == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ Todas las configuraciones completadas!{Colors.RESET}")
    elif created > 0:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠ Algunas configuraciones completadas ({created}/{total}){Colors.RESET}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ No se completaron configuraciones{Colors.RESET}")

    print(f"\n{Colors.CYAN}Próximos pasos:{Colors.RESET}")
    print("  1. Revise los archivos creados")
    print("  2. Edite .env con sus configuraciones específicas")
    print("  3. Edite frontend/.env si es necesario")
    print("  4. Ejecute: python verificar_sistema.py")
    print()

if __name__ == '__main__':
    try:
        main()
        input("\nPresione ENTER para salir...")
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Operación cancelada{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n{Colors.RED}Error: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        input("\nPresione ENTER para salir...")
        sys.exit(1)
