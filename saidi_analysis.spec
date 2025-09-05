# saidi_analysis.spec - Configuración PyInstaller para SAIDI Analysis Pro
# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Configuración básica
app_name = 'SAIDI_Analysis_Pro'
main_script = 'main.py'

# Detectar directorio del proyecto
project_dir = os.path.dirname(os.path.abspath('saidi_analysis.spec'))
interfaz_dir = os.path.join(project_dir, 'Interfaz')
backend_dir = os.path.join(project_dir, 'backend')

print(f"Proyecto: {project_dir}")
print(f"Interfaz: {interfaz_dir}")
print(f"Backend: {backend_dir}")

# ============================================================================
# ANÁLISIS DE DEPENDENCIAS
# ============================================================================

# Módulos Python a incluir explícitamente
hiddenimports = [
    # Módulos principales del proyecto
    'main_interface',
    'main_interface_ui', 
    'excel_manager',
    'ui_components',
    'ParametroV',
    'selectorOrder',
    'path_utils',
    
    # Backend
    'Modelo',
    'Parametro', 
    'visual',
    'parametros_bridge',
    
    # Dependencias científicas
    'numpy',
    'pandas',
    'scipy',
    'scipy.stats',
    'scipy.special',
    'scipy.linalg',
    'scipy.optimize',
    
    # Statsmodels y dependencias
    'statsmodels',
    'statsmodels.api',
    'statsmodels.tsa',
    'statsmodels.tsa.statespace',
    'statsmodels.tsa.statespace.sarimax',
    'statsmodels.tsa.arima',
    'statsmodels.tsa.arima.model',
    'statsmodels.base',
    'statsmodels.iolib',
    'statsmodels.tools',
    
    # Pmdarima
    'pmdarima',
    'pmdarima.arima',
    'pmdarima.preprocessing',
    
    # Sklearn
    'sklearn',
    'sklearn.metrics',
    'sklearn.base',
    'sklearn.utils',
    'sklearn.preprocessing',
    
    # Matplotlib y backends
    'matplotlib',
    'matplotlib.pyplot',
    'matplotlib.backends',
    'matplotlib.backends.backend_tkagg',
    'matplotlib.backends.backend_agg',
    'matplotlib.dates',
    'matplotlib.ticker',
    'matplotlib.figure',
    'matplotlib.font_manager',
    
    # Excel y archivos
    'openpyxl',
    'openpyxl.reader',
    'openpyxl.writer',
    'xlrd',
    'xlsxwriter',
    
    # Tkinter adicionales
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    
    # Otros
    'warnings',
    'argparse',
    'threading',
    'subprocess',
    'tempfile',
    'logging',
    'json',
    'datetime',
    'time',
    'itertools',
    'traceback'
]

# Recopilar submódulos adicionales automáticamente
try:
    hiddenimports.extend(collect_submodules('statsmodels'))
    hiddenimports.extend(collect_submodules('pmdarima'))
    hiddenimports.extend(collect_submodules('matplotlib'))
    print("Submódulos automáticos recopilados")
except Exception as e:
    print(f"Error recopilando submódulos: {e}")

# ============================================================================
# ARCHIVOS DE DATOS Y RECURSOS
# ============================================================================

# Archivos de datos a incluir
datas = []

# Incluir todos los archivos Python del proyecto
project_files = [
    # Interfaz
    (os.path.join(interfaz_dir, '*.py'), 'Interfaz'),
    
    # Backend  
    (os.path.join(backend_dir, '*.py'), 'backend'),
    
    # Archivo de utilidades en raíz
    ('path_utils.py', '.'),
]

# Agregar archivos del proyecto
for src_pattern, dst_dir in project_files:
    import glob
    for file_path in glob.glob(src_pattern):
        if os.path.isfile(file_path):
            relative_path = os.path.relpath(file_path, project_dir)
            datas.append((file_path, dst_dir))
            print(f"Incluido: {relative_path} -> {dst_dir}")

# Datos de dependencias científicas
try:
    # Matplotlib
    import matplotlib
    matplotlib_data = collect_data_files('matplotlib', include_py_files=False)
    datas.extend(matplotlib_data)
    print(f"Matplotlib: {len(matplotlib_data)} archivos de datos")
    
    # Statsmodels
    statsmodels_data = collect_data_files('statsmodels', include_py_files=False) 
    datas.extend(statsmodels_data)
    print(f"Statsmodels: {len(statsmodels_data)} archivos de datos")
    
    # Pandas
    pandas_data = collect_data_files('pandas', include_py_files=False)
    datas.extend(pandas_data)
    print(f"Pandas: {len(pandas_data)} archivos de datos")
    
except Exception as e:
    print(f"Error recopilando datos: {e}")

# Archivos de configuración adicionales
config_files = [
    'requirements_fixed.txt',
    'README.md'
]

for config_file in config_files:
    config_path = os.path.join(project_dir, config_file)
    if os.path.exists(config_path):
        datas.append((config_path, '.'))
        print(f"Config: {config_file}")

# ============================================================================
# ANÁLISIS PRINCIPAL
# ============================================================================

a = Analysis(
    [main_script],
    pathex=[
        project_dir,
        interfaz_dir, 
        backend_dir
    ],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Excluir módulos innecesarios para reducir tamaño
        'IPython',
        'jupyter',
        'notebook',
        'qtpy',
        'PyQt5',
        'PyQt6', 
        'PySide2',
        'PySide6',
        'wx',
        'tornado',
        'zmq',
        'sphinx',
        'pytest',
        'setuptools',
        'distutils',
        'pkg_resources'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# ============================================================================
# PROCESAMIENTO POST-ANÁLISIS
# ============================================================================

# Remover duplicados y archivos innecesarios
print("Limpiando análisis...")

# Filtrar binarios duplicados
seen_binaries = set()
filtered_binaries = []
for binary in a.binaries:
    binary_name = binary[0]
    if binary_name not in seen_binaries:
        filtered_binaries.append(binary)
        seen_binaries.add(binary_name)

a.binaries = filtered_binaries
print(f"Binarios únicos: {len(a.binaries)}")

# Filtrar datos duplicados  
seen_datas = set()
filtered_datas = []
for data in a.datas:
    data_name = data[1]  # Destino
    if data_name not in seen_datas:
        filtered_datas.append(data)
        seen_datas.add(data_name)

a.datas = filtered_datas
print(f"Datos únicos: {len(a.datas)}")

# ============================================================================
# CREACIÓN DEL EJECUTABLE
# ============================================================================

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Configuración del ejecutable principal
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=app_name,
    debug=False,          # Cambiar a True para debug
    bootloader_ignore_signals=False,
    strip=False,          # Mantener símbolos para mejor debugging
    upx=True,            # Comprimir con UPX si está disponible
    console=False,        # False para aplicación GUI
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,           # Agregar icono si está disponible
    version=None         # Agregar información de versión si está disponible
)

# Crear distribución completa
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=app_name
)

# ============================================================================
# INFORMACIÓN FINAL
# ============================================================================

print("\n" + "="*60)
print("CONFIGURACIÓN PYINSTALLER COMPLETADA")
print("="*60)
print(f"Nombre: {app_name}")
print(f"Script principal: {main_script}")
print(f"Directorio salida: dist/{app_name}/")
print(f"Ejecutable:")