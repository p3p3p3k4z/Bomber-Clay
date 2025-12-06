import PyInstaller.__main__
import os
import sys
import shutil

# Nombre del ejecutable
APP_NAME = "Bomber-Clay"

ASSETS_DIR = "assets"

def build():
    # Limpiar builds anteriores
    if os.path.exists("build"): shutil.rmtree("build")
    if os.path.exists("dist"): shutil.rmtree("dist")

    # Separador de rutas según el sistema ( : en Linux, ; en Windows)
    # Si usas Wine, Python creerá que es Windows, así que usará ; correctamente.
    separator = ";" if os.name == "nt" or sys.platform == "win32" else ":"

    print(f"--- INICIANDO CONSTRUCCIÓN DE {APP_NAME} ---")
    
    PyInstaller.__main__.run([
        'main.py',                       # Archivo principal
        '--name=%s' % APP_NAME,          # Nombre del exe
        '--onefile',                     # Todo en un solo archivo
        '--noconsole',                   # No mostrar ventana negra de consola
        f'--add-data={ASSETS_DIR}{separator}{ASSETS_DIR}', # Incluir carpeta assets
        '--clean',                       # Limpiar caché
    ])

    print("\n--- CONSTRUCCIÓN FINALIZADA ---")
    print(f"Busca tu ejecutable en la carpeta 'dist/'")

if __name__ == "__main__":
    build()

#wine python -m pip install pygame pyinstaller
#wine python build.py