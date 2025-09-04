# set_venv64_default.py
import os
import json
import sys

def set_venv64_default():
    """Configura venv (64 bits) como el entorno predeterminado en VSCode"""
    
    # Ruta del proyecto
    project_path = r"C:\Users\steve\Desktop\Trabajos\Petrolrios\Poryecto\fraud_detection_system"
    vscode_dir = os.path.join(project_path, ".vscode")
    settings_file = os.path.join(vscode_dir, "settings.json")
    
    # Configuración para venv (64 bits)
    settings = {
        "python.defaultInterpreterPath": "./venv/Scripts/python.exe",
        "python.terminal.activateEnvironment": True,
        "python.terminal.activateEnvInCurrentTerminal": True,
        "terminal.integrated.defaultProfile.windows": "PowerShell",
        "terminal.integrated.env.windows": {
            "PYTHON_ENV": "64bit"
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
    print("✅ CONFIGURACIÓN COMPLETADA - Python 64 bits")
    print("="*60)
    print()
    print("Entorno predeterminado: venv (64 bits)")
    print("Ruta: ./venv/Scripts/python.exe")
    print()
    print("Para que los cambios surtan efecto:")
    print("1. Cierra VSCode completamente")
    print("2. Vuelve a abrir VSCode")
    print("3. Las nuevas terminales usarán venv")
    print()
    print("Para verificar:")
    print('   python -c "import sys; print(sys.version)"')
    print("   Debe mostrar: [MSC v.xxxx 64 bit (AMD64)]")
    print("="*60)

if __name__ == "__main__":
    try:
        set_venv64_default()
        input("\nPresiona Enter para salir...")
    except Exception as e:
        print(f"❌ Error: {e}")
        input("\nPresiona Enter para salir...")