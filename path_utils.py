# path_utils.py - Utilidad para manejo de rutas compatible con PyInstaller
"""
Utilidad para resolver rutas correctamente tanto en desarrollo como en executable
Compatible con PyInstaller one-file y one-folder modes
"""
import os
import sys
import tempfile
import logging
from typing import Optional, Union

# Configurar logging para debug
logger = logging.getLogger(__name__)

class PathManager:
    """Gestor centralizado de rutas para desarrollo y PyInstaller"""
    
    def __init__(self):
        self._base_path = None
        self._executable_dir = None
        self._temp_dir = None
        self._is_frozen = None
        
    @property
    def is_frozen(self) -> bool:
        """Verificar si está ejecutándose desde PyInstaller executable"""
        if self._is_frozen is None:
            self._is_frozen = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
        return self._is_frozen
    
    @property
    def base_path(self) -> str:
        """Obtener ruta base del proyecto"""
        if self._base_path is None:
            if self.is_frozen:
                # PyInstaller: usar directorio temporal donde se extraen archivos
                self._base_path = sys._MEIPASS
                logger.info(f"PyInstaller mode - Base path: {self._base_path}")
            else:
                # Desarrollo: directorio del archivo principal
                self._base_path = os.path.dirname(os.path.abspath(__file__))
                logger.info(f"Development mode - Base path: {self._base_path}")
                
        return self._base_path
    
    @property
    def executable_dir(self) -> str:
        """Directorio donde está el ejecutable (para archivos persistentes)"""
        if self._executable_dir is None:
            if self.is_frozen:
                # PyInstaller: directorio del executable
                self._executable_dir = os.path.dirname(sys.executable)
            else:
                # Desarrollo: mismo que base_path
                self._executable_dir = self.base_path
                
        return self._executable_dir
    
    @property
    def temp_dir(self) -> str:
        """Directorio temporal para archivos temporales"""
        if self._temp_dir is None:
            if self.is_frozen:
                # PyInstaller: usar temp del sistema con subfolder
                app_temp = os.path.join(tempfile.gettempdir(), "SAIDI_Analysis_Pro")
            else:
                # Desarrollo: temp en directorio del proyecto
                app_temp = os.path.join(self.base_path, "temp")
                
            os.makedirs(app_temp, exist_ok=True)
            self._temp_dir = app_temp
            
        return self._temp_dir
    
    def get_resource_path(self, relative_path: str) -> str:
        """
        Obtener ruta absoluta a un recurso
        
        Args:
            relative_path: Ruta relativa desde la base del proyecto
            
        Returns:
            Ruta absoluta al recurso
        """
        full_path = os.path.join(self.base_path, relative_path)
        
        # Verificar que el archivo existe
        if not os.path.exists(full_path):
            logger.warning(f"Recurso no encontrado: {full_path}")
            
        return os.path.normpath(full_path)
    
    def get_backend_script(self, script_name: str) -> str:
        """
        Obtener ruta a script del backend
        
        Args:
            script_name: Nombre del script (ej: "Modelo.py")
            
        Returns:
            Ruta absoluta al script
        """
        return self.get_resource_path(os.path.join("backend", script_name))
    
    def get_interfaz_file(self, file_name: str) -> str:
        """
        Obtener ruta a archivo de Interfaz
        
        Args:
            file_name: Nombre del archivo
            
        Returns:
            Ruta absoluta al archivo
        """
        return self.get_resource_path(os.path.join("Interfaz", file_name))
    
    def get_temp_file(self, filename: str) -> str:
        """
        Crear ruta para archivo temporal
        
        Args:
            filename: Nombre del archivo temporal
            
        Returns:
            Ruta completa al archivo temporal
        """
        return os.path.join(self.temp_dir, filename)
    
    def get_config_file(self, filename: str) -> str:
        """
        Obtener ruta para archivo de configuración (persistente)
        
        Args:
            filename: Nombre del archivo de configuración
            
        Returns:
            Ruta al archivo de configuración
        """
        config_dir = os.path.join(self.executable_dir, "config")
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, filename)
    
    def verify_structure(self) -> dict:
        """
        Verificar estructura de directorios necesaria
        
        Returns:
            Dict con resultado de verificación
        """
        result = {
            'valid': True,
            'mode': 'PyInstaller' if self.is_frozen else 'Development',
            'base_path': self.base_path,
            'executable_dir': self.executable_dir,
            'temp_dir': self.temp_dir,
            'missing_dirs': [],
            'missing_files': []
        }
        
        # Verificar directorios críticos
        critical_dirs = []
        if not self.is_frozen:
            # Solo verificar en desarrollo
            critical_dirs = ['backend', 'Interfaz']
            
        for dir_name in critical_dirs:
            dir_path = self.get_resource_path(dir_name)
            if not os.path.exists(dir_path):
                result['missing_dirs'].append(dir_name)
                result['valid'] = False
        
        # Verificar archivos críticos
        critical_files = {
            'backend': ['Modelo.py', 'Parametro.py', 'visual.py', 'parametros_bridge.py'],
            'Interfaz': ['main_interface.py', 'excel_manager.py', 'ui_components.py']
        }
        
        for dir_name, files in critical_files.items():
            if not self.is_frozen or dir_name in ['config']:  # Siempre verificar config
                for file_name in files:
                    if dir_name == 'backend':
                        file_path = self.get_backend_script(file_name)
                    elif dir_name == 'Interfaz':
                        file_path = self.get_interfaz_file(file_name)
                    else:
                        file_path = self.get_resource_path(os.path.join(dir_name, file_name))
                        
                    if not os.path.exists(file_path):
                        result['missing_files'].append(f"{dir_name}/{file_name}")
                        result['valid'] = False
        
        return result
    
    def create_progress_file(self, prefix: str = "saidi_progress") -> str:
        """
        Crear archivo de progreso temporal único
        
        Args:
            prefix: Prefijo para el archivo
            
        Returns:
            Ruta al archivo de progreso
        """
        import time
        timestamp = int(time.time())
        filename = f"{prefix}_{timestamp}.json"
        return self.get_temp_file(filename)
    
    def cleanup_temp_files(self, pattern: str = "saidi_*"):
        """
        Limpiar archivos temporales antiguos
        
        Args:
            pattern: Patrón de archivos a limpiar
        """
        import glob
        import time
        
        try:
            temp_pattern = os.path.join(self.temp_dir, pattern)
            current_time = time.time()
            
            for file_path in glob.glob(temp_pattern):
                try:
                    # Eliminar archivos más antiguos de 1 hora
                    if os.path.isfile(file_path):
                        file_age = current_time - os.path.getmtime(file_path)
                        if file_age > 3600:  # 1 hora en segundos
                            os.remove(file_path)
                            logger.info(f"Archivo temporal limpiado: {file_path}")
                            
                except OSError as e:
                    logger.warning(f"No se pudo limpiar archivo temporal {file_path}: {e}")
                    
        except Exception as e:
            logger.error(f"Error limpiando archivos temporales: {e}")

# Instancia global del gestor de rutas
path_manager = PathManager()

# Funciones de conveniencia para compatibilidad
def get_base_path() -> str:
    """Obtener ruta base del proyecto"""
    return path_manager.base_path

def get_resource_path(relative_path: str) -> str:
    """Obtener ruta a recurso"""
    return path_manager.get_resource_path(relative_path)

def get_backend_script_path(script_name: str) -> str:
    """Obtener ruta a script del backend"""
    return path_manager.get_backend_script(script_name)

def ensure_temp_dir() -> str:
    """Asegurar que existe directorio temporal"""
    return path_manager.temp_dir

def is_frozen() -> bool:
    """Verificar si está en modo PyInstaller"""
    return path_manager.is_frozen

def get_executable_dir() -> str:
    """Obtener directorio del ejecutable"""
    return path_manager.executable_dir

def verify_project_structure() -> dict:
    """Verificar estructura del proyecto"""
    return path_manager.verify_structure()

# Funciones específicas para la aplicación SAIDI
def get_modelo_script() -> str:
    """Ruta al script Modelo.py"""
    return path_manager.get_backend_script("Modelo.py")

def get_parametro_script() -> str:
    """Ruta al script Parametro.py"""
    return path_manager.get_backend_script("Parametro.py")

def get_visual_script() -> str:
    """Ruta al script visual.py"""
    return path_manager.get_backend_script("visual.py")

def get_bridge_script() -> str:
    """Ruta al script parametros_bridge.py"""
    return path_manager.get_backend_script("parametros_bridge.py")

def create_progress_file(prefix: str = "saidi_progress") -> str:
    """Crear archivo de progreso único"""
    return path_manager.create_progress_file(prefix)

def cleanup_old_temp_files():
    """Limpiar archivos temporales antiguos"""
    path_manager.cleanup_temp_files()

# Configurar logging básico
def setup_logging():
    """Configurar logging para debug de rutas"""
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('[PATH] %(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

# Auto-setup cuando se importa el módulo
setup_logging()

# Debug inicial
logger.info(f"PathManager initialized - Frozen: {path_manager.is_frozen}")
logger.info(f"Base path: {path_manager.base_path}")
logger.info(f"Executable dir: {path_manager.executable_dir}")
logger.info(f"Temp dir: {path_manager.temp_dir}")

if __name__ == "__main__":
    # Prueba del sistema de rutas
    print("=== PRUEBA DEL SISTEMA DE RUTAS ===")
    
    print(f"Modo PyInstaller: {is_frozen()}")
    print(f"Ruta base: {get_base_path()}")
    print(f"Directorio ejecutable: {get_executable_dir()}")
    print(f"Directorio temporal: {ensure_temp_dir()}")
    
    print("\nRutas de scripts:")
    print(f"Modelo.py: {get_modelo_script()}")
    print(f"Parametro.py: {get_parametro_script()}")
    print(f"visual.py: {get_visual_script()}")
    
    print("\nVerificación de estructura:")
    structure = verify_project_structure()
    print(f"Válida: {structure['valid']}")
    print(f"Modo: {structure['mode']}")
    
    if structure['missing_dirs']:
        print(f"Directorios faltantes: {structure['missing_dirs']}")
    if structure['missing_files']:
        print(f"Archivos faltantes: {structure['missing_files']}")
    
    print("\nPrueba de archivo temporal:")
    temp_file = create_progress_file("test")
    print(f"Archivo temporal: {temp_file}")
    
    print("\nLimpieza de archivos temporales...")
    cleanup_old_temp_files()
    
    print("=== PRUEBA COMPLETADA ===")