# set_venv32_default.py
import os
import json
import sys

def set_venv32_default():
    """Configura venv32 (32 bits) como el entorno predeterminado en VSCode"""
    
    # Ruta del proyecto
    project_path = r"C:\Users\steve\Desktop\Trabajos\Petrolrios\Poryecto\fraud_detection_system"
    vscode_dir = os.path.join(project_path, ".vscode")
    settings_file = os.path.join(vscode_dir, "settings.json")
    
    # Configuración para venv32
    settings = {
        "python.defaultInterpreterPath": "./venv32/Scripts/python.exe",
        "python.terminal.activateEnvironment": True,
        "python.terminal.activateEnvInCurrentTerminal": True,
        "terminal.integrated.defaultProfile.windows": "PowerShell",
        "terminal.integrated.env.windows": {
            "PYTHON_ENV": "32bit"
        }
    }
    
    # Crear directorio .vscode si no existe
    if not os.path.exists(vscode_dir):
        os.makedirs(vscode_dir)
        print(f"✓ Directorio .vscode creado")
    
    # Escribir configuración
    with open(settings_file, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=4)
    
    print("="*60)
    print("✅ CONFIGURACIÓN COMPLETADA - Python 32 bits")
    print("="*60)
    print()
    print("Entorno predeterminado: venv32 (32 bits)")
    print("Ruta: ./venv32/Scripts/python.exe")
    print()
    print("Para que los cambios surtan efecto:")
    print("1. Cierra VSCode completamente")
    print("2. Vuelve a abrir VSCode")
    print("3. Las nuevas terminales usarán venv32")
    print()
    print("Para verificar:")
    print('   python -c "import sys; print(sys.version)"')
    print("   Debe mostrar: [MSC v.1944 32 bit (Intel)]")
    print("="*60)

if __name__ == "__main__":
    try:
        set_venv32_default()
        input("\nPresiona Enter para salir...")
    except Exception as e:
        print(f"❌ Error: {e}")
        input("\nPresiona Enter para salir...")