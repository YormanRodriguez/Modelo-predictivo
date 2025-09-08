# main.py - Lanzador Principal con Soporte PyInstaller

import sys
import os
import tkinter as tk
from tkinter import messagebox
import traceback
import logging
import tempfile


class SAIDILauncher:
    """Lanzador principal con verificación de entorno y soporte PyInstaller"""
    
    def __init__(self):
        # Detectar si está ejecutándose desde PyInstaller
        self.is_frozen = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
        
        if self.is_frozen:
            # PyInstaller executable
            self.project_root = sys._MEIPASS
            self.executable_dir = os.path.dirname(sys.executable)
            self.mode = "PyInstaller"
        else:
            # Desarrollo normal
            self.project_root = os.path.dirname(os.path.abspath(__file__))
            self.executable_dir = self.project_root
            self.mode = "Desarrollo"
            
        self.interfaz_path = os.path.join(self.project_root, 'Interfaz')
        self.backend_path = os.path.join(self.project_root, 'backend')
        
        # Configurar logging
        self.setup_logging()
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"SAIDI Launcher iniciado - Modo: {self.mode}")
        self.logger.info(f"Directorio raíz: {self.project_root}")
        self.logger.info(f"Directorio ejecutable: {self.executable_dir}")
        
    def setup_logging(self):
        """Configurar sistema de logging adaptativo"""
        log_level = logging.INFO
        
        # Configurar handlers según el modo
        handlers = []
        
        if self.is_frozen:
            # En executable, log a archivo en directorio del ejecutable
            try:
                log_file = os.path.join(self.executable_dir, "saidi_launcher.log")
                file_handler = logging.FileHandler(log_file, encoding='utf-8', mode='w')
                file_handler.setFormatter(logging.Formatter(
                    '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
                ))
                handlers.append(file_handler)
            except Exception as e:
                # Si no se puede escribir archivo, usar temp
                try:
                    temp_log = tempfile.NamedTemporaryFile(
                        mode='w', suffix='.log', prefix='saidi_launcher_', 
                        delete=False, encoding='utf-8'
                    )
                    temp_log.close()
                    file_handler = logging.FileHandler(temp_log.name, encoding='utf-8')
                    file_handler.setFormatter(logging.Formatter(
                        '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
                    ))
                    handlers.append(file_handler)
                    print(f"Log temporal creado: {temp_log.name}")
                except:
                    pass
        
        # Siempre incluir consola (si está disponible)
        try:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter('[LAUNCHER] %(levelname)s: %(message)s'))
            handlers.append(console_handler)
        except:
            pass
        
        # Configurar logging raíz
        logging.basicConfig(
            level=log_level,
            handlers=handlers,
            force=True
        )
        
    def verify_project_structure(self):
        """Verificar estructura del proyecto según el modo de ejecución"""
        self.logger.info("Verificando estructura del proyecto...")
        
        if self.is_frozen:
            return self._verify_frozen_structure()
        else:
            return self._verify_development_structure()
    
    def _verify_frozen_structure(self):
        """Verificación para executable PyInstaller"""
        self.logger.info("Verificación PyInstaller: Comprobando recursos embebidos")
        
        # En PyInstaller, los archivos están embebidos
        # Verificar que _MEIPASS existe y contiene archivos básicos
        if not os.path.exists(self.project_root):
            error_msg = (f"Error en executable PyInstaller.\n\n"
                        f"Directorio de recursos no encontrado: {self.project_root}\n\n"
                        f"El executable puede estar corrupto.")
            self.logger.error(error_msg)
            self.show_error_dialog("Error de Executable", error_msg)
            return False
        
        # Verificar directorios críticos embebidos
        critical_dirs = ['Interfaz', 'backend']
        missing_dirs = []
        
        for dir_name in critical_dirs:
            dir_path = os.path.join(self.project_root, dir_name)
            if not os.path.exists(dir_path):
                missing_dirs.append(dir_name)
                self.logger.error(f"Directorio embebido faltante: {dir_name}")
        
        if missing_dirs:
            error_msg = (f"Executable incompleto.\n\n"
                        f"Directorios faltantes: {', '.join(missing_dirs)}\n\n"
                        f"Recompile el executable con PyInstaller.")
            self.logger.error(error_msg)
            self.show_error_dialog("Error de Executable", error_msg)
            return False
        
        # Verificar archivos Python críticos
        critical_files = {
            'Interfaz': ['main_interface.py', 'excel_manager.py', 'ui_components.py'],
            'backend': ['Modelo.py', 'Parametro.py', 'visual.py']
        }
        
        missing_files = []
        for dir_name, files in critical_files.items():
            for file_name in files:
                file_path = os.path.join(self.project_root, dir_name, file_name)
                if not os.path.exists(file_path):
                    missing_files.append(f"{dir_name}/{file_name}")
                    self.logger.error(f"Archivo embebido faltante: {dir_name}/{file_name}")
        
        if missing_files:
            error_msg = (f"Executable incompleto.\n\n"
                        f"Archivos faltantes: {len(missing_files)} archivos\n"
                        f"Primeros faltantes: {', '.join(missing_files[:5])}\n\n"
                        f"Recompile el executable incluyendo todos los archivos.")
            self.logger.error(error_msg)
            self.show_error_dialog("Error de Executable", error_msg)
            return False
        
        self.logger.info("Estructura PyInstaller verificada correctamente")
        return True
    
    def _verify_development_structure(self):
        """Verificación para desarrollo normal"""
        self.logger.info("Verificación desarrollo: Comprobando directorios y archivos")
        
        # Directorios requeridos
        required_dirs = {
            'Interfaz': self.interfaz_path,
            'backend': self.backend_path
        }
        
        missing_dirs = []
        for dir_name, dir_path in required_dirs.items():
            if not os.path.exists(dir_path):
                missing_dirs.append(dir_name)
                self.logger.error(f"Directorio faltante: {dir_name}")
                
        if missing_dirs:
            error_msg = (f"Error en estructura del proyecto.\n\n"
                        f"Directorios faltantes: {', '.join(missing_dirs)}\n\n"
                        f"Estructura esperada:\n"
                        f"  proyecto/\n"
                        f"  ├── main.py (este archivo)\n"
                        f"  ├── path_utils.py\n"
                        f"  ├── Interfaz/\n"
                        f"  └── backend/")
            self.logger.error(error_msg)
            self.show_error_dialog("Error de Estructura", error_msg)
            return False
            
        # Archivos críticos en cada directorio
        critical_files = {
            'Interfaz': ['main_interface.py', 'main_interface_ui.py', 'excel_manager.py', 'ui_components.py'],
            'backend': ['Modelo.py', 'Parametro.py', 'visual.py']
        }
        
        missing_files = []
        for dir_name, files in critical_files.items():
            for file_name in files:
                if dir_name == 'Interfaz':
                    file_path = os.path.join(self.interfaz_path, file_name)
                else:
                    file_path = os.path.join(self.backend_path, file_name)
                    
                if not os.path.exists(file_path):
                    missing_files.append(f"{dir_name}/{file_name}")
                    self.logger.error(f"Archivo faltante: {dir_name}/{file_name}")
                
        # Reportar archivos faltantes
        if missing_files:
            error_msg = (f"Archivos críticos faltantes:\n\n"
                        f"{chr(10).join(['• ' + f for f in missing_files])}\n\n"
                        f"La aplicación puede no funcionar correctamente.")
            self.logger.warning(error_msg)
            
            # Preguntar si desea continuar
            root = tk.Tk()
            root.withdraw()
            continue_anyway = messagebox.askyesno(
                "Archivos Faltantes",
                f"{error_msg}\n\n¿Desea intentar ejecutar la aplicación de todas formas?"
            )
            root.destroy()
            
            if not continue_anyway:
                return False
                
        self.logger.info("Estructura de desarrollo verificada correctamente")
        return True
        
    def setup_python_path(self):
        """Configurar el path de Python adaptativo"""
        self.logger.info("Configurando paths de Python...")
        
        # Rutas a agregar según el modo
        paths_to_add = [self.project_root]
        
        if not self.is_frozen:
            # En desarrollo, agregar subdirectorios
            paths_to_add.extend([self.interfaz_path, self.backend_path])
        else:
            # En PyInstaller, solo la raíz (ya contiene todo)
            self.logger.info("Modo PyInstaller: usando estructura embebida")
        
        # Agregar al sys.path
        for path in paths_to_add:
            if path not in sys.path:
                sys.path.insert(0, path)
                self.logger.info(f"Agregado al path: {os.path.relpath(path, self.project_root) if not self.is_frozen else 'raíz embebida'}")
                
        self.logger.info("Python paths configurados correctamente")
        
    def verify_dependencies(self):
        """Verificar dependencias según el modo"""
        self.logger.info("Verificando dependencias...")
        
        critical_modules = [
            ('tkinter', 'Interfaz gráfica'),
            ('pandas', 'Manejo de datos Excel'),
            ('numpy', 'Cálculos numéricos'), 
            ('matplotlib', 'Gráficos y visualizaciones'),
            ('statsmodels', 'Modelos estadísticos SARIMAX')
        ]
        
        # En PyInstaller, también verificar módulos específicos
        if self.is_frozen:
            critical_modules.extend([
                ('openpyxl', 'Lectura de Excel'),
                ('sklearn', 'Machine Learning'),
                ('pmdarima', 'Auto ARIMA')
            ])
        
        missing_modules = []
        
        for module_name, description in critical_modules:
            try:
                __import__(module_name)
                self.logger.debug(f"✓ {module_name}: Disponible")
            except ImportError as e:
                missing_modules.append((module_name, description, str(e)))
                self.logger.error(f"✗ {module_name}: FALTANTE ({e})")

        if missing_modules:
            if self.is_frozen:
                # En executable, es error crítico
                error_msg = (f"Executable incompleto - Dependencias faltantes:\n\n")
                for module, desc, error in missing_modules:
                    error_msg += f"• {module}: {desc}\n  Error: {error}\n\n"
                error_msg += "El executable debe recompilarse incluyendo todas las dependencias."
                
                self.logger.error(error_msg)
                self.show_error_dialog("Executable Incompleto", error_msg)
                return False
            else:
                # En desarrollo, dar instrucciones de instalación
                error_msg = (f"Dependencias faltantes detectadas:\n\n")
                for module, desc, _ in missing_modules:
                    error_msg += f"• {module}: {desc}\n"
                
                error_msg += (f"\nPara instalar las dependencias:\n"
                             f"pip install -r requirements_fixed.txt\n\n"
                             f"O instalar manualmente:\n"
                             f"pip install pandas numpy matplotlib statsmodels pmdarima scikit-learn openpyxl")
                
                self.logger.error(error_msg)
                self.show_error_dialog("Dependencias Faltantes", error_msg)
                return False
            
        self.logger.info("Todas las dependencias están disponibles")
        return True
        
    def show_error_dialog(self, title, message):
        """Mostrar diálogo de error con fallback robusto"""
        self.logger.info(f"Mostrando diálogo: {title}")
        try:
            root = tk.Tk()
            root.withdraw()  # Ocultar ventana principal
            root.attributes('-topmost', True)  # Traer al frente
            messagebox.showerror(title, message)
            root.destroy()
        except Exception as e:
            # Fallback si tkinter no funciona
            self.logger.error(f"Error mostrando diálogo: {e}")
            print(f"\n{'='*60}")
            print(f"ERROR: {title}")
            print(f"{'='*60}")
            print(message)
            print(f"{'='*60}\n")
            
            # En Windows, también intentar mostrar ventana de consola
            if os.name == 'nt':
                try:
                    import ctypes
                    ctypes.windll.user32.MessageBoxW(0, message, title, 0x10)  # MB_ICONERROR
                except:
                    pass
            
    def launch_application(self):
        """Lanzar la aplicación principal con manejo de errores"""
        self.logger.info("Iniciando aplicación principal...")
        
        try:
            # Intentar importar path_utils si está disponible
            try:
                import path_utils
                self.logger.info("Sistema de rutas PyInstaller cargado")
                path_utils_available = True
            except ImportError as e:
                self.logger.warning(f"Sistema de rutas no disponible: {e}")
                path_utils_available = False
            
            # Cambiar al directorio de Interfaz para imports
            if not self.is_frozen:
                original_cwd = os.getcwd()
                os.chdir(self.interfaz_path)
                self.logger.info(f"Cambiado directorio de trabajo a: {self.interfaz_path}")
            
            # Importar la aplicación principal
            try:
                from main_interface import SAIDIAnalysisApp
                self.logger.info("Módulos principales importados correctamente")
            except ImportError as e:
                self.logger.error(f"Error importando main_interface: {e}")
                
                # Intentar diagnóstico adicional
                if self.is_frozen:
                    error_msg = (f"Error en executable PyInstaller:\n\n"
                                f"No se puede importar main_interface.py\n"
                                f"Error: {str(e)}\n\n"
                                f"El executable puede estar incompleto o corrupto.")
                else:
                    error_msg = (f"Error importando módulos de la aplicación:\n\n"
                                f"{str(e)}\n\n"
                                f"Verifique que todos los archivos estén en Interfaz/\n"
                                f"Directorio actual: {os.getcwd()}")
                
                self.show_error_dialog("Error de Importación", error_msg)
                return
            
            # Crear ventana principal
            self.logger.info("Creando ventana principal...")
            root = tk.Tk()
            
            # Configurar título con información del modo
            title = "SAIDI Analysis Pro"
            if self.is_frozen:
                title += " (Ejecutable)"
            else:
                title += " (Desarrollo)"
            root.title(title)
            
            # Configurar manejador de errores global
            def handle_exception(exc_type, exc_value, exc_traceback):
                if issubclass(exc_type, KeyboardInterrupt):
                    sys.__excepthook__(exc_type, exc_value, exc_traceback)
                    return
                    
                error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
                self.logger.error(f"ERROR NO MANEJADO:\n{error_msg}")
                
                # Mostrar error al usuario
                try:
                    error_dialog_msg = (f"Ha ocurrido un error inesperado en la aplicación.\n\n"
                                      f"Error: {exc_type.__name__}: {str(exc_value)}\n\n"
                                      f"Modo: {self.mode}\n\n"
                                      f"La aplicación se cerrará.")
                    
                    if self.is_frozen:
                        error_dialog_msg += f"\n\nRevise el archivo de log en:\n{self.executable_dir}"
                    else:
                        error_dialog_msg += "\n\nRevise la consola para más detalles."
                    
                    messagebox.showerror("Error Inesperado", error_dialog_msg)
                except Exception as dialog_error:
                    self.logger.error(f"Error mostrando diálogo de error: {dialog_error}")
                    
                # Cerrar aplicación
                try:
                    root.quit()
                except:
                    sys.exit(1)
            
            # Configurar manejador de excepciones
            sys.excepthook = handle_exception
            
            # Crear instancia de la aplicación
            self.logger.info("Inicializando interfaz principal...")
            app = SAIDIAnalysisApp(root)
            
            # Información de inicio exitoso
            self.logger.info("="*50)
            self.logger.info("SAIDI ANALYSIS PRO INICIADO CORRECTAMENTE")
            self.logger.info(f"Modo: {self.mode}")
            self.logger.info(f"Directorio raíz: {self.project_root}")
            self.logger.info(f"Directorio ejecutable: {self.executable_dir}")
            if path_utils_available:
                self.logger.info("Sistema de rutas PyInstaller: ACTIVO")
            else:
                self.logger.info("Sistema de rutas PyInstaller: NO DISPONIBLE")
            self.logger.info("="*50)
            
            # Mostrar información en consola también
            print(f"\n🚀 SAIDI Analysis Pro iniciado correctamente")
            print(f"📁 Modo: {self.mode}")
            if self.is_frozen:
                print(f"📍 Ejecutable: {sys.executable}")
                print(f"💾 Logs: {self.executable_dir}")
            
            # Iniciar loop principal de tkinter
            root.mainloop()
            
            # Restaurar directorio original si es necesario
            if not self.is_frozen:
                os.chdir(original_cwd)
                self.logger.info("Directorio de trabajo restaurado")
                
        except ImportError as e:
            error_msg = (f"Error importando módulos de la aplicación:\n\n"
                        f"{str(e)}\n\n"
                        f"Modo: {self.mode}")
            
            if self.is_frozen:
                error_msg += (f"\nEl executable puede estar incompleto o corrupto.\n"
                             f"Directorio de recursos: {self.project_root}")
            else:
                error_msg += (f"\nVerifique que todos los archivos estén presentes.\n"
                             f"Directorio Interfaz: {self.interfaz_path}")
                             
            self.logger.error(error_msg)
            self.show_error_dialog("Error de Importación", error_msg)
            
        except Exception as e:
            error_msg = (f"Error inesperado al iniciar la aplicación:\n\n"
                        f"{str(e)}\n\n"
                        f"Modo: {self.mode}")
            
            if self.is_frozen:
                error_msg += f"\n\nRevise el archivo de log en:\n{self.executable_dir}"
            else:
                error_msg += "\n\nRevise la consola para más detalles."
                
            self.logger.error(error_msg)
            self.logger.error(f"TRACEBACK COMPLETO:\n{traceback.format_exc()}")
            self.show_error_dialog("Error de Inicio", error_msg)
            
    def run(self):
        """Ejecutar el launcher completo"""
        print("=" * 60)
        print("SAIDI ANALYSIS PRO - LAUNCHER AVANZADO")
        print("=" * 60)
        print(f"Modo de ejecución: {self.mode}")
        print(f"Directorio del proyecto: {self.project_root}")
        print(f"Directorio ejecutable: {self.executable_dir}")
        print()
        
        self.logger.info("Iniciando proceso de verificación completo")
        
        # Paso 1: Verificar estructura
        if not self.verify_project_structure():
            self.logger.error("Verificación de estructura falló")
            print("❌ Verificación de estructura falló. Abortando.")
            self._wait_for_input()
            return False
            
        print("✅ Estructura del proyecto verificada")
        
        # Paso 2: Configurar paths
        self.setup_python_path()
        print("✅ Paths de Python configurados")
        
        # Paso 3: Verificar dependencias  
        if not self.verify_dependencies():
            self.logger.error("Verificación de dependencias falló")
            print("❌ Verificación de dependencias falló. Abortando.")
            self._wait_for_input()
            return False
            
        print("✅ Dependencias verificadas")
        
        print()
        print("=" * 60)
        print("🎯 TODAS LAS VERIFICACIONES COMPLETADAS EXITOSAMENTE")
        print("=" * 60)
        print()
        
        # Paso 4: Lanzar aplicación
        try:
            self.launch_application()
            self.logger.info("Aplicación finalizó correctamente")
            return True
            
        except KeyboardInterrupt:
            self.logger.info("Aplicación interrumpida por el usuario")
            print("\n⏹️  Aplicación interrumpida por el usuario")
            return True
            
        except Exception as e:
            self.logger.error(f"Error crítico en launcher: {e}")
            print(f"\n💥 Error crítico: {e}")
            return False
    
    def _wait_for_input(self):
        """Esperar input del usuario en Windows"""
        if os.name == 'nt' and not self.is_frozen:
            try:
                input("\nPresione Enter para salir...")
            except:
                pass


def main():
    """Función principal del launcher"""
    launcher = None
    try:
        launcher = SAIDILauncher()
        success = launcher.run()
        
        if success:
            print("\n🎉 SAIDI Analysis Pro se ejecutó correctamente")
        else:
            print("\n⚠️  SAIDI Analysis Pro terminó con errores")
            
    except KeyboardInterrupt:
        print("\n⏹️  Ejecución interrumpida por el usuario")
        if launcher:
            launcher.logger.info("Ejecución interrumpida por el usuario")
        
    except Exception as e:
        error_msg = f"Error crítico en el launcher: {e}"
        print(f"\n💥 {error_msg}")
        
        if launcher:
            launcher.logger.error(f"{error_msg}\nTRACEBACK: {traceback.format_exc()}")
        else:
            print(f"TRACEBACK: {traceback.format_exc()}")
        
    finally:
        # Pausa final para ver mensajes en Windows (solo en desarrollo)
        if os.name == 'nt':
            is_frozen = getattr(sys, 'frozen', False)
            if not is_frozen:  # Solo en desarrollo
                try:
                    input("\n⏸️  Presione Enter para salir...")
                except:
                    pass


if __name__ == "__main__":
    main()