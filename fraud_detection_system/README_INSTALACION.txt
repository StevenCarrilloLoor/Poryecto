╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║          INSTALACIÓN AUTOMÁTICA - SISTEMA DE DETECCIÓN DE FRAUDE        ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝


📦 INSTALACIÓN RÁPIDA
═══════════════════════════════════════════════════════════════════════════

  Opción 1 (Más fácil):
  ─────────────────────
    Haga doble clic en:  INSTALAR.bat


  Opción 2 (Alternativa):
  ───────────────────────
    1. Abra CMD o PowerShell
    2. Ejecute: python setup_automatico.py


🔧 QUÉ SE INSTALARÁ AUTOMÁTICAMENTE
═══════════════════════════════════════════════════════════════════════════

  ✓ Python 3.11 (32-bit y 64-bit)
  ✓ Node.js LTS
  ✓ SQL Server Express 2022
  ✓ ODBC Driver 17 para SQL Server
  ✓ Firebird ODBC Driver
  ✓ Todas las dependencias Python
  ✓ Todas las dependencias Node.js
  ✓ Configuración de base de datos
  ✓ Scripts de inicio


⚙️ DESPUÉS DE LA INSTALACIÓN
═══════════════════════════════════════════════════════════════════════════

  1. Edite el archivo .env para configurar:
     - Ruta a la base de datos Firebird (FIREBIRD_DSN)
     - Credenciales de SQL Server (si es necesario)

  2. Inicie el sistema:
     - Doble clic en: iniciar_sistema.bat

     O inicie componentes por separado:
     - iniciar_backend.bat (backend 64-bit)
     - iniciar_backend_32bit.bat (backend 32-bit con Firebird)
     - iniciar_frontend.bat (frontend)


🌐 ACCEDER A LA APLICACIÓN
═══════════════════════════════════════════════════════════════════════════

  Frontend:  http://localhost:5173
  Backend:   http://localhost:8000
  API Docs:  http://localhost:8000/docs


📖 DOCUMENTACIÓN COMPLETA
═══════════════════════════════════════════════════════════════════════════

  Para instrucciones detalladas, abra:
    INSTRUCCIONES_INSTALACION.md


⚠️ IMPORTANTE
═══════════════════════════════════════════════════════════════════════════

  - Se requieren permisos de administrador (se solicitan automáticamente)
  - Asegúrese de tener conexión a Internet
  - La instalación puede tomar 10-30 minutos dependiendo de su conexión
  - Python 32-bit es NECESARIO para conectarse a Firebird


📝 ARCHIVOS CREADOS
═══════════════════════════════════════════════════════════════════════════

  Instalación:
    • setup_automatico.py ............... Script principal de instalación
    • INSTALAR.bat ...................... Ejecutar instalación (doble clic)
    • INSTRUCCIONES_INSTALACION.md ...... Guía completa paso a paso
    • README_INSTALACION.txt ............ Este archivo

  Scripts de inicio (se crean después de instalar):
    • iniciar_sistema.bat ............... Inicia todo el sistema
    • iniciar_backend.bat ............... Solo backend (64-bit)
    • iniciar_backend_32bit.bat ......... Solo backend (32-bit + Firebird)
    • iniciar_frontend.bat .............. Solo frontend

  Configuración (se crean después de instalar):
    • .env .............................. Archivo de configuración
    • venv/ ............................. Entorno virtual Python 64-bit
    • venv32/ ........................... Entorno virtual Python 32-bit


🆘 PROBLEMAS COMUNES
═══════════════════════════════════════════════════════════════════════════

  "Python no está instalado":
    → Instale Python 3.8+ desde: https://www.python.org/downloads/
    → Marque "Add Python to PATH" durante la instalación

  "Error al crear base de datos":
    → Verifique que SQL Server esté ejecutándose
    → Puede crear manualmente: sqlcmd -S "PC\SQLTRABAJO" -E -Q "CREATE DATABASE FraudDetectionDB"

  "Firebird no conecta":
    → Use el backend de 32-bit: iniciar_backend_32bit.bat
    → Verifique la ruta en el archivo .env

  "Frontend no muestra datos":
    → Verifique que el backend esté ejecutándose (puerto 8000)
    → Abra: http://localhost:8000/docs


═══════════════════════════════════════════════════════════════════════════

  ¿Listo para instalar?

  👉 Haga doble clic en: INSTALAR.bat

═══════════════════════════════════════════════════════════════════════════
