# bridge_diagnostics.py - Herramienta de diagnóstico para el bridge
import os
import sys
import json
from datetime import datetime

def diagnose_bridge_issue():
    """Función para diagnosticar problemas con el bridge"""
    print("="*60)
    print("DIAGNÓSTICO DEL BRIDGE DE PARÁMETROS")
    print("="*60)
    
    # 1. Verificar estructura de directorios
    print("\n1. ESTRUCTURA DE DIRECTORIOS:")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"   Directorio actual: {current_dir}")
    
    # Buscar archivos bridge
    bridge_locations = [
        os.path.join(current_dir, 'parametros_bridge.py'),
        os.path.join(current_dir, 'backend', 'parametros_bridge.py'),
        os.path.join(os.path.dirname(current_dir), 'parametros_bridge.py'),
        os.path.join(os.path.dirname(current_dir), 'backend', 'parametros_bridge.py')
    ]
    
    bridge_found = False
    for location in bridge_locations:
        if os.path.exists(location):
            print(f"   ✓ Encontrado: {location}")
            bridge_found = True
        else:
            print(f"   ✗ No encontrado: {location}")
    
    if not bridge_found:
        print("   ⚠ PROBLEMA: No se encontró parametros_bridge.py en ninguna ubicación esperada")
        return False
    
    # 2. Verificar archivo de datos del bridge
    print("\n2. ARCHIVO DE DATOS DEL BRIDGE:")
    bridge_data_paths = [
        os.path.join(current_dir, 'temp', 'parametros_bridge.json'),
        os.path.join(os.path.dirname(current_dir), 'temp', 'parametros_bridge.json')
    ]
    
    data_found = False
    for data_path in bridge_data_paths:
        if os.path.exists(data_path):
            print(f"   ✓ Archivo de datos encontrado: {data_path}")
            try:
                with open(data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"      - Timestamp: {data.get('timestamp', 'N/A')}")
                    print(f"      - Status: {data.get('status', 'N/A')}")
                    print(f"      - Top models: {len(data.get('top_models', []))}")
                    data_found = True
                    
                    # Mostrar detalles de los modelos
                    if 'top_models' in data:
                        print("      - Modelos disponibles:")
                        for i, model in enumerate(data['top_models'][:3], 1):
                            order = model.get('order', 'N/A')
                            precision = model.get('precision_final', 0)
                            print(f"        #{i}: order={order}, precisión={precision:.1f}%")
                            
            except Exception as e:
                print(f"   ✗ Error leyendo datos: {e}")
        else:
            print(f"   ✗ No encontrado: {data_path}")
    
    if not data_found:
        print("   ⚠ PROBLEMA: No se encontraron datos del bridge")
        return False
    
    # 3. Verificar importación
    print("\n3. PRUEBA DE IMPORTACIÓN:")
    try:
        # Agregar rutas al path
        for location in bridge_locations:
            if os.path.exists(location):
                dir_path = os.path.dirname(location)
                if dir_path not in sys.path:
                    sys.path.insert(0, dir_path)
        
        from backend.parametros_bridge import get_updated_presets, clear_bridge_data
        print("   ✓ Importación exitosa")
        
        # Probar funciones
        presets = get_updated_presets()
        if presets:
            print(f"   ✓ Presets cargados: {len(presets)} presets disponibles")
            for preset_name, preset_data in presets.items():
                model = preset_data['model']
                desc = preset_data['description']
                print(f"      - {preset_name}: {desc}")
        else:
            print("   ⚠ No se pudieron cargar presets")
            
    except ImportError as e:
        print(f"   ✗ Error de importación: {e}")
        return False
    except Exception as e:
        print(f"   ✗ Error ejecutando funciones: {e}")
        return False
    
    print("\n✅ DIAGNÓSTICO COMPLETADO - El bridge parece estar funcionando correctamente")
    return True

def fix_selector_import():
    """Generar código corregido para selectorOrder.py"""
    print("\n" + "="*60)
    print("CÓDIGO CORREGIDO PARA SELECTORORDER.PY")
    print("="*60)
    
    corrected_import = '''# selectorOrder.py - IMPORTACIÓN CORREGIDA
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import os
import sys

# IMPORTACIÓN MEJORADA DEL BRIDGE
BRIDGE_AVAILABLE = False

def setup_bridge_import():
    """Configurar importación del bridge con múltiples rutas"""
    global BRIDGE_AVAILABLE
    
    # Lista de posibles ubicaciones del bridge
    current_dir = os.path.dirname(os.path.abspath(__file__))
    possible_paths = [
        current_dir,  # Mismo directorio
        os.path.join(current_dir, 'backend'),  # Subdirectorio backend
        os.path.dirname(current_dir),  # Directorio padre
        os.path.join(os.path.dirname(current_dir), 'backend')  # backend en directorio padre
    ]
    
    for path in possible_paths:
        bridge_file = os.path.join(path, 'parametros_bridge.py')
        if os.path.exists(bridge_file):
            if path not in sys.path:
                sys.path.insert(0, path)
            try:
                global get_updated_presets, clear_bridge_data
                from parametros_bridge import get_updated_presets, clear_bridge_data
                BRIDGE_AVAILABLE = True
                print(f"✓ Bridge cargado desde: {path}")
                return True
            except ImportError as e:
                continue
    
    print("⚠ Bridge no disponible - funcionalidad limitada")
    return False

# Llamar a la función de setup
setup_bridge_import()'''
    
    print(corrected_import)
    
    # Crear archivo temporal con la corrección
    fix_file = 'selector_import_fix.py'
    with open(fix_file, 'w', encoding='utf-8') as f:
        f.write(corrected_import)
    
    print(f"\n✓ Código de corrección guardado en: {fix_file}")

if __name__ == "__main__":
    print("Ejecutando diagnóstico del bridge...")
    success = diagnose_bridge_issue()
    
    if not success:
        print("\n🔧 Generando solución...")
        fix_selector_import()
    else:
        print("\n✅ El bridge está funcionando correctamente")
        print("Si el problema persiste, verifica que selectorOrder.py use el código de importación mejorado")
    
    print("\n" + "="*60)