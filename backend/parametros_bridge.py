# parametros_bridge.py - Puente de comunicación entre Parametro.py y selectorOrder.py
import json
import os
from datetime import datetime
import threading
import time

class ParametrosBridge:
    """Clase para comunicación entre Parametro.py y selectorOrder.py"""
    
    def __init__(self):
        self.bridge_file = "temp/parametros_bridge.json"
        self.last_update = None
        self.top_models = []
        
    def ensure_temp_directory(self):
        """Asegurar que existe el directorio temporal"""
        temp_dir = os.path.dirname(self.bridge_file)
        if temp_dir and not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
    
    def save_top_models(self, top_models):
        """Guardar los top 3 modelos desde Parametro.py"""
        try:
            self.ensure_temp_directory()
            
            # Preparar datos para guardar
            bridge_data = {
                'timestamp': datetime.now().isoformat(),
                'top_models': top_models,
                'status': 'updated',
                'source': 'Parametro.py'
            }
            
            # Guardar archivo
            with open(self.bridge_file, 'w', encoding='utf-8') as f:
                json.dump(bridge_data, f, ensure_ascii=False, indent=2)
            
            self.top_models = top_models
            self.last_update = datetime.now()
            
            print(f"Top models guardados en bridge: {len(top_models)} modelos")
            return True
            
        except Exception as e:
            print(f"Error guardando top models: {e}")
            return False
    
    def load_top_models(self):
        """Cargar los top 3 modelos para selectorOrder.py"""
        try:
            if not os.path.exists(self.bridge_file):
                return None
                
            with open(self.bridge_file, 'r', encoding='utf-8') as f:
                bridge_data = json.load(f)
            
            top_models = bridge_data.get('top_models', [])
            if len(top_models) >= 3:
                print(f"Top models cargados desde bridge: {len(top_models)} modelos")
                return top_models
            else:
                print(f"Insuficientes modelos en bridge: {len(top_models)}")
                return None
                
        except Exception as e:
            print(f"Error cargando top models: {e}")
            return None
    
    def clear_bridge(self):
        """Limpiar el archivo de comunicación"""
        try:
            if os.path.exists(self.bridge_file):
                os.remove(self.bridge_file)
                print("Bridge file limpiado")
        except Exception as e:
            print(f"Error limpiando bridge: {e}")

# Instancia global del bridge
bridge = ParametrosBridge()

def update_selector_presets_from_top_models():
    """Actualizar los presets del selector con los top 3 modelos"""
    top_models = bridge.load_top_models()
    
    if not top_models or len(top_models) < 3:
        print("No hay suficientes modelos para actualizar presets")
        return None
    
    # Mapear modelos a presets según tu especificación:
    # Top 1 -> Conservador
    # Top 2 -> Solo Tendencia  
    # Top 3 -> Agresivo
    
    preset_mapping = {
        'Conservador': {
            'model': top_models[0],  # Top 1
            'description': f"Modelo optimizado (Precisión: {top_models[0].get('precision_final', 0):.1f}%)"
        },
        'Solo Tendencia': {
            'model': top_models[1],  # Top 2
            'description': f"Segundo mejor modelo (Precisión: {top_models[1].get('precision_final', 0):.1f}%)"
        },
        'Agresivo': {
            'model': top_models[2],  # Top 3
            'description': f"Tercer mejor modelo (Precisión: {top_models[2].get('precision_final', 0):.1f}%)"
        }
    }
    
    return preset_mapping

# Funciones para integrar con Parametro.py
def save_top_models_to_bridge(top_models):
    """Función para que Parametro.py guarde los top models"""
    return bridge.save_top_models(top_models)

def get_updated_presets():
    """Función para que selectorOrder.py obtenga presets actualizados"""
    return update_selector_presets_from_top_models()

def clear_bridge_data():
    """Función para limpiar datos del bridge"""
    bridge.clear_bridge()

# Funciones de utilidad
def format_model_info(model_data):
    """Formatear información del modelo para mostrar"""
    order = model_data.get('order', 'N/A')
    seasonal_order = model_data.get('seasonal_order', 'N/A')
    precision = model_data.get('precision_final', 0)
    
    return f"SARIMAX{order}x{seasonal_order} - {precision:.1f}%"

def validate_model_parameters(order, seasonal_order):
    """Validar que los parámetros del modelo sean válidos"""
    try:
        # Validar order (p, d, q)
        if not (isinstance(order, tuple) and len(order) == 3):
            return False
        p, d, q = order
        if not all(isinstance(x, int) and 0 <= x <= 10 for x in [p, q]):
            return False
        if not (isinstance(d, int) and 0 <= d <= 2):
            return False
            
        # Validar seasonal_order (P, D, Q, s)
        if not (isinstance(seasonal_order, tuple) and len(seasonal_order) == 4):
            return False
        P, D, Q, s = seasonal_order
        if not all(isinstance(x, int) and 0 <= x <= 5 for x in [P, Q]):
            return False
        if not (isinstance(D, int) and 0 <= D <= 2):
            return False
        if not (isinstance(s, int) and 1 <= s <= 24):
            return False
            
        return True
        
    except Exception:
        return False

if __name__ == "__main__":
    # Pruebas del bridge
    print("=== PRUEBA DEL BRIDGE DE PARÁMETROS ===")
    
    # Simular top models desde Parametro.py
    test_models = [
        {
            'order': (2, 1, 1),
            'seasonal_order': (1, 1, 1, 12),
            'precision_final': 89.5,
            'rmse': 0.1234,
            'mape': 10.5,
            'r2_score': 0.895,
            'aic': 42.1
        },
        {
            'order': (1, 1, 2),
            'seasonal_order': (0, 1, 1, 12),
            'precision_final': 86.2,
            'rmse': 0.1456,
            'mape': 13.8,
            'r2_score': 0.862,
            'aic': 45.7
        },
        {
            'order': (3, 1, 0),
            'seasonal_order': (2, 1, 0, 12),
            'precision_final': 83.1,
            'rmse': 0.1678,
            'mape': 16.9,
            'r2_score': 0.831,
            'aic': 48.3
        }
    ]
    
    # Guardar modelos
    print("\n1. Guardando top models...")
    success = save_top_models_to_bridge(test_models)
    print(f"   Resultado: {'Éxito' if success else 'Error'}")
    
    # Obtener presets actualizados
    print("\n2. Obteniendo presets actualizados...")
    presets = get_updated_presets()
    
    if presets:
        print("   Presets actualizados:")
        for preset_name, preset_data in presets.items():
            model = preset_data['model']
            desc = preset_data['description']
            print(f"   - {preset_name}: {format_model_info(model)}")
            print(f"     {desc}")
    else:
        print("   No se pudieron obtener presets")
    
    # Limpiar
    print("\n3. Limpiando bridge...")
    clear_bridge_data()
    print("   Bridge limpiado")