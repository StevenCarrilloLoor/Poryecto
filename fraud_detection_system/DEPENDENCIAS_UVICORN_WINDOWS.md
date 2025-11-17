# Dependencias Opcionales de Uvicorn en Windows

Cuando ejecutas `uvicorn` en Windows, puede mostrar advertencias sobre dependencias faltantes:

## 🔴 DEPENDENCIAS OPCIONALES PERO RECOMENDADAS

### 1. **colorama**
- **Para qué**: Colores en la terminal de Windows (output bonito con colores)
- **Sin esto**: Terminal funciona pero sin colores (blanco y negro)
- **Mensaje típico**: `"Install 'colorama' for colored terminal output"`
- **Versión**: `colorama>=0.4.0`

### 2. **watchfiles**
- **Para qué**: Auto-reload rápido (detectar cambios en archivos)
- **Sin esto**: Usa polling (más lento, consume más CPU)
- **Mensaje típico**: `"watchfiles not installed, using default file watcher"`
- **Versión**: `watchfiles>=0.18.0`
- **Nota**: Debería venir con `uvicorn[standard]` pero a veces falla en Windows

### 3. **httptools**
- **Para qué**: Parser HTTP más rápido
- **Sin esto**: Usa el parser por defecto (más lento)
- **Versión**: `httptools>=0.5.0`
- **Nota**: Debería venir con `uvicorn[standard]`

### 4. **python-dotenv**
- **Para qué**: Cargar variables de entorno desde .env
- **Sin esto**: No carga .env automáticamente
- **Versión**: `python-dotenv>=0.13`
- **Nota**: YA ESTÁ en requirements.txt

## 📝 LO QUE PROBABLEMENTE FALTA

Basado en tu descripción ("rainbow" o "unicorn"), **casi seguro** falta:

```txt
colorama==0.4.6
watchfiles==0.21.0
```

Estos hacen que uvicorn se vea bonito con colores y funcione mejor en Windows.

## ✅ CÓMO AGREGAR A REQUIREMENTS.TXT

Agregar después de la línea de uvicorn:

```txt
# Core Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
colorama==0.4.6          # ← AGREGAR: Colores en terminal Windows
watchfiles==0.21.0       # ← AGREGAR: Auto-reload rápido
python-multipart==0.0.6
websockets==12.0
```

## 🔧 CÓMO AGREGAR A SETUP_AUTOMATICO.PY

En la lista de `pythonPackages` (línea ~558), agregar:

```python
$pythonPackages = @(
    "fastapi==0.115.0",
    "uvicorn[standard]==0.32.0",
    "colorama==0.4.6",        # ← AGREGAR
    "watchfiles==0.21.0",     # ← AGREGAR
    # ... resto de paquetes
)
```

Y en la lista de paquetes esenciales para 32-bit (línea ~639):

```python
essential_packages = [
    'fastapi==0.115.0',
    'uvicorn[standard]==0.32.0',
    'colorama==0.4.6',           # ← AGREGAR
    'watchfiles==0.21.0',        # ← AGREGAR
    # ... resto
]
```

---

**Conclusión**: Probablemente cuando ejecutabas el proyecto, uvicorn mostraba una advertencia sobre instalar `colorama` para tener colores bonitos en Windows (rainbow = colores) y mejorar el rendimiento con `watchfiles`.
