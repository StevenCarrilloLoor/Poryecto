# Instalación Automática - Sistema de Detección de Fraude

Este documento describe cómo usar el script de instalación automática para configurar el sistema en cualquier computadora.

## 📋 Requisitos Previos

- **Sistema Operativo:** Windows 10/11
- **Conexión a Internet** (para descargar los instaladores)
- **Permisos de Administrador** (se solicitarán automáticamente)
- **Espacio en disco:** Mínimo 5 GB libres

## 🚀 Instalación Rápida

### Opción 1: Ejecutar directamente (Recomendado)

1. Descargue o clone el proyecto en su computadora

2. Abra una ventana de PowerShell o CMD y navegue hasta la carpeta del proyecto:
   ```cmd
   cd ruta\a\fraud_detection_system
   ```

3. Ejecute el script de instalación:
   ```cmd
   python setup_automatico.py
   ```

4. El script solicitará permisos de administrador automáticamente

5. Siga las instrucciones en pantalla

### Opción 2: Doble clic

1. Busque el archivo `setup_automatico.py` en el explorador de archivos

2. Haga doble clic sobre él

3. Si Windows pregunta con qué programa abrirlo, seleccione Python

## 📦 Componentes que se Instalan

El script instalará automáticamente:

### ✅ Software Base
- **Python 3.11 64-bit** - Para el backend principal
- **Python 3.11 32-bit** - Para compatibilidad con Firebird
- **Node.js LTS** - Para el frontend React
- **SQL Server Express 2022** - Base de datos principal
- **ODBC Driver 17 para SQL Server** - Conexión a SQL Server
- **Firebird ODBC Driver** - Conexión a la base de datos Firebird legacy

### ✅ Configuración del Proyecto
- Entornos virtuales Python (`venv` y `venv32`)
- Todas las dependencias Python del `requirements.txt`
- Todas las dependencias Node.js del `package.json`
- Archivo de configuración `.env`
- Base de datos `FraudDetectionDB` en SQL Server
- Migraciones de base de datos (tablas, índices, etc.)

### ✅ Scripts de Inicio
- `iniciar_backend.bat` - Inicia el servidor backend (64-bit)
- `iniciar_backend_32bit.bat` - Inicia el servidor backend con soporte Firebird (32-bit)
- `iniciar_frontend.bat` - Inicia el servidor de desarrollo frontend
- `iniciar_sistema.bat` - Inicia todo el sistema completo

## ⚙️ Configuración Post-Instalación

Después de ejecutar el script, necesitará configurar algunas cosas:

### 1. Configurar Base de Datos Firebird

Edite el archivo `.env` y actualice la ruta a su base de datos Firebird:

```env
FIREBIRD_DSN=DRIVER=Firebird/InterBase(r) driver;UID=sysdba;PWD=su_password;DBNAME=localhost:C:\ruta\a\su\base\de\datos.fdb;
```

### 2. Configurar SQL Server (Opcional)

Si no usa autenticación de Windows, edite las credenciales en el archivo `.env`:

```env
DB_SERVER=NOMBRE_COMPUTADORA\SQLTRABAJO
DB_USERNAME=su_usuario
DB_PASSWORD=su_password
DB_TRUSTED_CONNECTION=no
```

### 3. Configurar Clave Secreta (Producción)

Para entornos de producción, cambie la clave secreta:

```env
SECRET_KEY=genere-una-clave-segura-aleatoria-aqui
```

## 🎯 Cómo Iniciar el Sistema

### Opción 1: Iniciar Todo (Más Fácil)

Simplemente ejecute:
```cmd
iniciar_sistema.bat
```

Esto abrirá dos ventanas:
- Una para el backend (puerto 8000)
- Una para el frontend (puerto 5173)

### Opción 2: Iniciar Componentes Separados

**Backend (64-bit - principal):**
```cmd
iniciar_backend.bat
```

**Backend (32-bit - con Firebird):**
```cmd
iniciar_backend_32bit.bat
```

**Frontend:**
```cmd
iniciar_frontend.bat
```

### Opción 3: Forma Manual

**Backend:**
```cmd
cd backend
venv\Scripts\activate
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```cmd
cd frontend
npm run dev
```

## 🌐 Acceder a la Aplicación

Una vez iniciado el sistema:

- **Frontend (Aplicación Web):** http://localhost:5173
- **API Backend:** http://localhost:8000
- **Documentación API:** http://localhost:8000/docs
- **Documentación Alternativa:** http://localhost:8000/redoc

## 🔧 Solución de Problemas

### El script dice que Python no está instalado

Si ya tiene Python instalado pero el script no lo detecta:
1. Abra una nueva ventana de CMD/PowerShell
2. Ejecute `python --version`
3. Si funciona, el problema es que el PATH no está actualizado
4. Reinicie su computadora y vuelva a intentar

### Error al crear la base de datos SQL Server

Si obtiene un error al crear la base de datos:
1. Verifique que SQL Server esté instalado y ejecutándose
2. Puede crear la base de datos manualmente:
   ```cmd
   sqlcmd -S "NOMBRE_PC\SQLTRABAJO" -E -Q "CREATE DATABASE FraudDetectionDB"
   ```

### Error al instalar dependencias Node.js

Si hay errores al instalar paquetes npm:
1. Navegue a la carpeta frontend: `cd frontend`
2. Elimine la carpeta `node_modules` si existe
3. Elimine el archivo `package-lock.json` si existe
4. Ejecute: `npm install`

### Firebird no se conecta

Si obtiene errores de conexión a Firebird:
1. Verifique que el driver ODBC de Firebird esté instalado:
   - Abra el "Administrador de orígenes de datos ODBC" (32-bit)
   - Vaya a la pestaña "Controladores"
   - Busque "Firebird/InterBase"
2. Verifique la ruta en el archivo `.env`
3. Use el backend de 32-bit: `iniciar_backend_32bit.bat`

### El frontend no muestra datos

Si el frontend carga pero no muestra datos:
1. Verifique que el backend esté ejecutándose (puerto 8000)
2. Abra http://localhost:8000/docs para verificar la API
3. Revise la consola del navegador (F12) para ver errores
4. Verifique que el archivo `.env` esté configurado correctamente

### Permisos de Administrador

Si el script no solicita permisos de administrador:
1. Cierre todas las ventanas de CMD/PowerShell
2. Haga clic derecho en el ícono de CMD o PowerShell
3. Seleccione "Ejecutar como administrador"
4. Navegue a la carpeta del proyecto
5. Ejecute: `python setup_automatico.py`

## 🔄 Reinstalar Componentes

Si necesita reinstalar algún componente:

### Reinstalar entornos virtuales Python
```cmd
# Eliminar entornos existentes
rmdir /s /q venv
rmdir /s /q venv32

# Volver a ejecutar el script
python setup_automatico.py
```

### Reinstalar dependencias Node.js
```cmd
cd frontend
rmdir /s /q node_modules
del package-lock.json
npm install
```

### Reinstalar base de datos
```cmd
# Eliminar base de datos
sqlcmd -S "NOMBRE_PC\SQLTRABAJO" -E -Q "DROP DATABASE FraudDetectionDB"

# Volver a ejecutar el script
python setup_automatico.py
```

## 📝 Notas Importantes

### Python 32-bit vs 64-bit

Este proyecto usa **DOS versiones de Python**:

- **Python 64-bit (venv)**: Versión principal, más rápida, para la mayoría del trabajo
- **Python 32-bit (venv32)**: Solo para conectarse a Firebird (el driver ODBC de Firebird solo funciona en 32-bit)

**¿Cuál usar?**
- Si NO necesita conectarse a Firebird: use `iniciar_backend.bat` (64-bit)
- Si SÍ necesita conectarse a Firebird: use `iniciar_backend_32bit.bat` (32-bit)

### SQL Server Instances

El proyecto está configurado para usar la instancia `SQLTRABAJO` de SQL Server.

Si su SQL Server tiene un nombre diferente:
1. Abra el archivo `.env`
2. Cambie la línea `DB_SERVER=`:
   ```env
   DB_SERVER=SU_NOMBRE_PC\SU_INSTANCIA
   ```

### Actualizaciones Futuras

Cuando clone el proyecto en otra computadora:
1. Solo necesita ejecutar `python setup_automatico.py` una vez
2. El script detectará qué ya está instalado
3. Solo instalará lo que falta

## 📞 Ayuda Adicional

Si encuentra problemas no cubiertos aquí:

1. Revise los logs del script (se muestran en la consola)
2. Verifique el archivo `.env` para configuración incorrecta
3. Revise los logs de la aplicación:
   - Backend: Mensajes en la consola donde ejecutó `iniciar_backend.bat`
   - Frontend: Consola del navegador (F12 > Console)
4. Verifique que todos los servicios estén ejecutándose:
   - SQL Server: Servicios de Windows > SQL Server (SQLTRABAJO)
   - Backend: http://localhost:8000/docs debe responder
   - Frontend: http://localhost:5173 debe cargar

## 🎉 ¡Listo!

Una vez completada la instalación, su sistema estará completamente funcional y listo para detectar fraudes.

**Disfrute del Sistema de Detección de Fraude!** 🚀
