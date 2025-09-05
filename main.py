# main.py - Lanzador Principal de SAIDI Analysis Pro

import sys
import os
import tkinter as tk
from tkinter import messagebox
import traceback


class SAIDILauncher:
    """Lanzador principal con verificación de entorno y manejo de errores"""
    
    def __init__(self):
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.interfaz_path = os.path.join(self.project_root, 'Interfaz')
        self.backend_path = os.path.join(self.project_root, 'backend')
        
    def verify_project_structure(self):
        """Verificar que la estructura del proyecto sea correcta"""
        print("🔍 Verificando estructura del proyecto...")
        
        # Directorios requeridos
        required_dirs = {
            'Interfaz': self.interfaz_path,
            'backend': self.backend_path
        }
        
        missing_dirs = []
        for dir_name, dir_path in required_dirs.items():
            if not os.path.exists(dir_path):
                missing_dirs.append(dir_name)
                
        if missing_dirs:
            error_msg = (f"Error en estructura del proyecto.\n\n"
                        f"Directorios faltantes: {', '.join(missing_dirs)}\n\n"
                        f"Estructura esperada:\n"
                        f"  proyecto/\n"
                        f"  ├── main.py (este archivo)\n"
                        f"  ├── Interfaz/\n"
                        f"  └── backend/")
            print(error_msg)
            self.show_error_dialog("Error de Estructura", error_msg)
            return False
            
        # Archivos críticos en Interfaz
        interfaz_files = [
            'main_interface.py',
            'main_interface_ui.py', 
            'excel_manager.py',
            'ui_components.py'
        ]
        
        missing_interfaz = []
        for file in interfaz_files:
            file_path = os.path.join(self.interfaz_path, file)
            if not os.path.exists(file_path):
                missing_interfaz.append(file)
                
        # Archivos críticos en backend
        backend_files = [
            'Modelo.py',
            'Parametro.py', 
            'visual.py'
        ]
        
        missing_backend = []
        for file in backend_files:
            file_path = os.path.join(self.backend_path, file)
            if not os.path.exists(file_path):
                missing_backend.append(file)
                
        # Reportar archivos faltantes
        if missing_interfaz or missing_backend:
            error_details = []
            if missing_interfaz:
                error_details.append(f"Interfaz/: {', '.join(missing_interfaz)}")
            if missing_backend:
                error_details.append(f"backend/: {', '.join(missing_backend)}")
                
            error_msg = (f"Archivos críticos faltantes:\n\n"
                        f"{chr(10).join(error_details)}\n\n"
                        f"La aplicación puede no funcionar correctamente.")
            print(error_msg)
            
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
                
        print("Estructura del proyecto verificada correctamente")
        return True
        
    def setup_python_path(self):
        """Configurar el path de Python para importar módulos"""
        print("Configurando paths de Python...")
        
        # Agregar directorios al sys.path
        paths_to_add = [
            self.project_root,      # Raíz del proyecto
            self.interfaz_path,     # Carpeta Interfaz
            self.backend_path       # Carpeta backend
        ]
        
        for path in paths_to_add:
            if path not in sys.path:
                sys.path.insert(0, path)
                print(f"Agregado: {os.path.relpath(path, self.project_root)}")
                
        print("Python paths configurados correctamente")
        
    def verify_dependencies(self):
        """Verificar que las dependencias principales estén disponibles"""
        print("Verificando dependencias principales...")
        
        critical_modules = [
            ('tkinter', 'Interfaz gráfica'),
            ('pandas', 'Manejo de datos Excel'),
            ('numpy', 'Cálculos numéricos'), 
            ('matplotlib', 'Gráficos y visualizaciones'),
            ('statsmodels', 'Modelos estadísticos SARIMAX')
        ]
        
        missing_modules = []
        
        for module_name, description in critical_modules:
            try:
                __import__(module_name)
                print(f"  {module_name}: OK")
            except ImportError:
                missing_modules.append((module_name, description))
                print(f" {module_name}: FALTANTE")

        if missing_modules:
            error_msg = (f" Dependencias faltantes detectadas:\n\n")
            for module, desc in missing_modules:
                error_msg += f"• {module}: {desc}\n"
            
            error_msg += (f"\nPara instalar las dependencias:\n"
                         f"pip install -r requirements_fixed.txt\n\n"
                         f"O instalar manualmente:\n"
                         f"pip install pandas numpy matplotlib statsmodels pmdarima scikit-learn openpyxl")
            
            print(error_msg)
            self.show_error_dialog("Dependencias Faltantes", error_msg)
            return False
            
        print("Todas las dependencias principales están disponibles")
        return True
        
    def show_error_dialog(self, title, message):
        """Mostrar diálogo de error"""
        try:
            root = tk.Tk()
            root.withdraw()  # Ocultar ventana principal
            messagebox.showerror(title, message)
            root.destroy()
        except:
            # Fallback si tkinter no funciona
            print(f"\n{'='*60}")
            print(f"ERROR: {title}")
            print(f"{'='*60}")
            print(message)
            print(f"{'='*60}\n")
            
    def launch_application(self):
        """Lanzar la aplicación principal"""
        print("Iniciando SAIDI Analysis Pro...")
        
        try:
            # Importar la aplicación principal
            from main_interface import SAIDIAnalysisApp
            
            print("Módulos importados correctamente")
            
            # Crear ventana principal
            root = tk.Tk()
            
            # Configurar manejador de errores global
            def handle_exception(exc_type, exc_value, exc_traceback):
                if issubclass(exc_type, KeyboardInterrupt):
                    sys.__excepthook__(exc_type, exc_value, exc_traceback)
                    return
                    
                error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
                print(f"ERROR NO MANEJADO:\n{error_msg}")
                
                # Mostrar error al usuario
                try:
                    messagebox.showerror(
                        "Error Inesperado",
                        f"Ha ocurrido un error inesperado en la aplicación.\n\n"
                        f"Error: {exc_type.__name__}: {str(exc_value)}\n\n"
                        f"La aplicación se cerrará. Revise la consola para más detalles."
                    )
                except:
                    pass
                    
                # Cerrar aplicación
                try:
                    root.quit()
                except:
                    sys.exit(1)
            
            # Configurar manejador de excepciones
            sys.excepthook = handle_exception
            
            # Crear instancia de la aplicación
            print("Inicializando interfaz principal...")
            app = SAIDIAnalysisApp(root)
            
            print("SAIDI Analysis Pro iniciado correctamente")
            print("Ejecutándose en modo gráfico...")
            print(f"Directorio de trabajo: {self.project_root}")
            
            # Iniciar loop principal de tkinter
            root.mainloop()
            
        except ImportError as e:
            error_msg = (f"Error importando módulos de la aplicación:\n\n"
                        f"{str(e)}\n\n"
                        f"Verifique que todos los archivos estén presentes en la carpeta Interfaz/")
            print(error_msg)
            self.show_error_dialog("Error de Importación", error_msg)
            
        except Exception as e:
            error_msg = (f"Error inesperado al iniciar la aplicación:\n\n"
                        f"{str(e)}\n\n"
                        f"Revise la consola para más detalles.")
            print(error_msg)
            print(f"TRACEBACK COMPLETO:\n{traceback.format_exc()}")
            self.show_error_dialog("Error de Inicio", error_msg)
            
    def run(self):
        """Ejecutar el launcher completo"""
        print("=" * 60)
        print("SAIDI ANALYSIS PRO - LAUNCHER")
        print("=" * 60)
        print(f"Directorio del proyecto: {self.project_root}")
        print()
        
        # Paso 1: Verificar estructura
        if not self.verify_project_structure():
            print("Verificación de estructura falló. Abortando.")
            input("Presione Enter para salir...")
            return False
            
        # Paso 2: Configurar paths
        self.setup_python_path()
        
        # Paso 3: Verificar dependencias  
        if not self.verify_dependencies():
            print("Verificación de dependencias falló. Abortando.")
            input("Presione Enter para salir...")
            return False
            
        print()
        print("=" * 60)
        print("TODAS LAS VERIFICACIONES COMPLETADAS EXITOSAMENTE")
        print("=" * 60)
        print()
        
        # Paso 4: Lanzar aplicación
        self.launch_application()
        
        return True


def main():
    """Función principal del launcher"""
    try:
        launcher = SAIDILauncher()
        success = launcher.run()
        
        if success:
            print("\nSAIDI Analysis Pro se ejecutó correctamente")
        else:
            print("\nSAIDI Analysis Pro no se pudo iniciar")
            
    except KeyboardInterrupt:
        print("\nEjecución interrumpida por el usuario")
        
    except Exception as e:
        print(f"\nError crítico en el launcher: {e}")
        print(f"TRACEBACK: {traceback.format_exc()}")
        
    finally:
        # Pausa final para ver mensajes en Windows
        if os.name == 'nt':
            try:
                input("\nPresione Enter para salir...")
            except:
                pass


if __name__ == "__main__":
    main()