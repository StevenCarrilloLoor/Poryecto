# 🚀 Pasos para Instalación Completa del Proyecto

Este documento describe los pasos **exactos** para instalar el proyecto en cualquier computadora nueva.

## 📋 Dependencias Encontradas (Análisis Profundo)

Después del análisis exhaustivo, se encontraron las siguientes dependencias faltantes:

### ✅ YA SOLUCIONADO
1. **requests** (Python) - Agregado a requirements.txt

### ⬜ PENDIENTE DE SOLUCIÓN MANUAL

2. **Microsoft Visual C++ 14.0+ Build Tools**
   - **¿Por qué?**: Necesario para compilar `pyodbc` y otros paquetes binarios
   - **¿Cuándo falla?**: Durante `pip install pyodbc`
   - **Error típico**: `error: Microsoft Visual C++ 14.0 or greater is required`
   - **Solución**:
     - Descargar: https://visualstudio.microsoft.com/visual-cpp-build-tools/
     - Instalar con componentes:
       - "Desktop development with C++"
       - "MSVC v143 - VS 2022 C++ x64/x86 build tools"
       - "Windows 11 SDK" (o Windows 10 SDK)

---

## 🔧 Instalación en 3 Pasos

### PASO 1: Ejecutar Instalador Automático

```bash
# Opción 1: Doble clic
INSTALAR.bat

# Opción 2: Desde consola
python setup_automatico.py
```

**Qué hace**:
- Instala Python 3.11 (32-bit y 64-bit)
- Instala Node.js LTS
- Instala SQL Server Express (descarga instalador)
- Instala ODBC Driver 17 para SQL Server
- Instala Firebird ODBC Driver
- Crea entornos virtuales (venv y venv32)
- Instala todas las dependencias Python
- Instala todas las dependencias Node.js
- Crea base de datos FraudDetectionDB
- Ejecuta migraciones
- Crea scripts de inicio

### PASO 2: Completar Configuraciones

```bash
# Opción 1: Doble clic
COMPLETAR_CONFIG.bat

# Opción 2: Desde consola
python completar_configuracion.py
```

**Qué hace**:
- Crea/completa `alembic.ini` (configuración de migraciones)
- Crea/completa `.gitignore` (reglas de exclusión de git)
- Crea `README.md` (documentación del proyecto)
- Crea `frontend/.env` (variables de entorno del frontend)
- Crea `frontend/.eslintrc.json` (configuración de ESLint)
- Crea `frontend/.prettierrc` (configuración de Prettier)
- Crea `frontend/tsconfig.node.json` (configuración TypeScript para Vite)

### PASO 3: Configurar Variables de Entorno

Edite los archivos `.env`:

#### Backend `.env` (raíz del proyecto)

```env
# Actualizar estas líneas:
DB_SERVER=TU_NOMBRE_PC\SQLTRABAJO
FIREBIRD_DSN=DRIVER=Firebird/InterBase(r) driver;...TU_RUTA...
SECRET_KEY=genera-una-clave-secreta-aleatoria
```

#### Frontend `frontend/.env`

```env
# Ya viene configurado correctamente, pero puede verificar:
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

---

## ✅ Verificación

Después de completar los 3 pasos, verifique la instalación:

```bash
# Opción 1: Doble clic
VERIFICAR.bat

# Opción 2: Desde consola
python verificar_sistema.py
```

**Debe mostrar**:
- ✓ Python 64-bit
- ✓ Python 32-bit
- ✓ Node.js
- ✓ npm
- ✓ SQL Server
- ✓ ODBC Driver 17
- ✓ Firebird ODBC Driver
- ✓ Entornos virtuales (venv y venv32)
- ✓ Dependencias Python instaladas
- ✓ Dependencias Node.js instaladas
- ✓ Archivos de configuración

**Objetivo**: 100% de verificaciones completadas

---

## 🎯 Iniciar el Sistema

Una vez todo verificado:

```bash
# Opción 1: Iniciar todo (recomendado)
iniciar_sistema.bat

# Opción 2: Componentes separados
iniciar_backend.bat        # Backend 64-bit (principal)
iniciar_backend_32bit.bat  # Backend 32-bit (si usa Firebird)
iniciar_frontend.bat       # Frontend
```

**Acceso**:
- Frontend: http://localhost:5173
- API Backend: http://localhost:8000
- Documentación API: http://localhost:8000/docs

---

## 🔴 Si Algo Falla

### Error: "pyodbc installation failed"

**Causa**: Falta Microsoft Visual C++ Build Tools

**Solución**:
1. Instalar Visual C++ Build Tools (ver arriba)
2. Reiniciar
3. Ejecutar nuevamente:
   ```bash
   venv\Scripts\activate
   pip install pyodbc
   ```

### Error: "Frontend no muestra datos"

**Causa**: Backend no está ejecutándose o variables mal configuradas

**Solución**:
1. Verificar que backend esté corriendo: http://localhost:8000/docs
2. Revisar `frontend/.env` tenga las URLs correctas
3. Revisar consola del navegador (F12 > Console) para ver errores

### Error: "No se puede conectar a Firebird"

**Causa**: Usando Python 64-bit en vez de 32-bit

**Solución**:
- Usar el backend de 32-bit: `iniciar_backend_32bit.bat`
- Verificar que el driver ODBC de Firebird esté instalado (32-bit)

### Error: "Base de datos no existe"

**Causa**: Base de datos FraudDetectionDB no fue creada

**Solución**:
```bash
sqlcmd -S "TU_PC\SQLTRABAJO" -E -Q "CREATE DATABASE FraudDetectionDB"
alembic upgrade head
```

---

## 📊 Arquitectura de Instalación

```
fraud_detection_system/
│
├── setup_automatico.py         # 🔧 Paso 1: Instala software y dependencias
├── completar_configuracion.py  # 📝 Paso 2: Crea archivos de configuración
├── verificar_sistema.py        # ✅ Verifica que todo esté instalado
│
├── INSTALAR.bat               # Ejecuta Paso 1 (doble clic)
├── COMPLETAR_CONFIG.bat       # Ejecuta Paso 2 (doble clic)
├── VERIFICAR.bat              # Ejecuta verificación (doble clic)
│
├── iniciar_sistema.bat        # Inicia todo el sistema
├── iniciar_backend.bat        # Inicia solo backend 64-bit
├── iniciar_backend_32bit.bat  # Inicia solo backend 32-bit
├── iniciar_frontend.bat       # Inicia solo frontend
│
└── [documentación]
    ├── INSTRUCCIONES_INSTALACION.md    # Guía detallada
    ├── DEPENDENCIAS_FALTANTES.md       # Análisis de dependencias
    ├── README_INSTALACION.txt          # Guía rápida
    └── PASOS_INSTALACION_COMPLETA.md   # Este archivo
```

---

## 📝 Checklist de Instalación

Marque cada paso a medida que lo complete:

- [ ] Descargar/clonar proyecto
- [ ] Ejecutar `INSTALAR.bat` (o `python setup_automatico.py`)
  - [ ] Python 3.11 instalado (32 y 64 bits)
  - [ ] Node.js instalado
  - [ ] SQL Server instalado/accesible
  - [ ] ODBC Drivers instalados
  - [ ] Entornos virtuales creados
  - [ ] Dependencias Python instaladas
  - [ ] Dependencias Node.js instaladas
  - [ ] Base de datos creada
- [ ] **(Si falla pyodbc)** Instalar Visual C++ Build Tools
- [ ] Ejecutar `COMPLETAR_CONFIG.bat` (o `python completar_configuracion.py`)
  - [ ] alembic.ini creado
  - [ ] .gitignore creado
  - [ ] README.md creado
  - [ ] frontend/.env creado
  - [ ] frontend/.eslintrc.json creado
  - [ ] frontend/.prettierrc creado
  - [ ] frontend/tsconfig.node.json creado
- [ ] Editar `.env` (raíz) con tus configuraciones
  - [ ] DB_SERVER actualizado
  - [ ] FIREBIRD_DSN actualizado
  - [ ] SECRET_KEY generado
- [ ] (Opcional) Editar `frontend/.env` si es necesario
- [ ] Ejecutar `VERIFICAR.bat` (o `python verificar_sistema.py`)
- [ ] Verificar que muestre 100% completado
- [ ] Ejecutar `iniciar_sistema.bat`
- [ ] Abrir http://localhost:5173
- [ ] ✅ **¡SISTEMA FUNCIONANDO!**

---

## 🆘 Soporte

Si después de seguir todos los pasos sigue teniendo problemas:

1. Ejecute `python verificar_sistema.py` y anote qué falta
2. Revise los logs en la consola donde ejecutó los scripts
3. Revise el archivo `fraud_detection.log`
4. Revise la consola del navegador (F12) para errores de frontend

**Documentos útiles**:
- `INSTRUCCIONES_INSTALACION.md` - Guía detallada con troubleshooting
- `DEPENDENCIAS_FALTANTES.md` - Análisis completo de dependencias
- `README.md` - Documentación del proyecto

---

## 🎉 Resumen

**3 comandos para tener todo funcionando**:

```bash
1. INSTALAR.bat           # Instala todo el software
2. COMPLETAR_CONFIG.bat   # Crea configuraciones
3. iniciar_sistema.bat    # Inicia el sistema
```

**¡Eso es todo!** 🚀

---

**Última actualización**: 2025-11-17
**Versión del documento**: 1.0
