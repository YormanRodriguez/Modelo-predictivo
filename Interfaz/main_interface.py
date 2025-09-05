# main_interface.py - Lógica de negocio separada de la interfaz
"""
Aplicación principal SAIDI Analysis Pro
Lógica de negocio separada de los componentes de interfaz
"""
import tkinter as tk
from tkinter import messagebox, filedialog
import subprocess
import sys
import os
import threading
import tempfile
import json
import time
import pandas as pd

# Importar módulos locales
from excel_manager import ExcelManager
from main_interface_ui import MainInterfaceUI
from ParametroV import ProgressWindow, PROGRESS_DATA
from selectorOrder import show_parameter_selector, get_selected_parameters, reset_parameters


class SAIDIAnalysisApp:
    """Aplicación principal SAIDI Analysis Pro - Solo lógica de negocio"""
    
    def __init__(self, root):
        self.root = root
        
        # Variables de control para evitar ejecuciones múltiples
        self.is_running_prediction = False
        self.is_running_behavior = False
        self.is_running_optimization = False
        
        # Variables para archivos temporales y ventanas de progreso
        self.temp_progress_file = None
        self.progress_window = None
        
        # Crear callbacks para la UI
        callbacks = {
            'on_window_close': self.on_window_close_attempt,
            'select_excel_file': self.select_excel_file,
            'run_prediction': self.run_prediction,
            'run_behavior_analysis': self.run_behavior_analysis,
            'run_parameter_optimization': self.run_parameter_optimization
        }
        
        # Inicializar UI
        self.ui = MainInterfaceUI(root, callbacks)
        
        # Verificar estructura de directorios
        self.verify_directory_structure()
        
        # Configurar interfaz
        self.setup_application()

    def verify_directory_structure(self):
        """Verificar que existe la estructura de directorios correcta"""
        backend_dir = "backend"
        required_files = ["Modelo.py", "Parametro.py", "visual.py"]
        
        if not os.path.exists(backend_dir):
            messagebox.showerror("Error de Estructura", 
                               f"No se encuentra el directorio '{backend_dir}'\n"
                               f"Estructura esperada:\n"
                               f"  - Interfaz/ (carpeta actual)\n"
                               f"  - backend/ (scripts de Python)")
            return False
            
        missing_files = []
        for file in required_files:
            file_path = os.path.join(backend_dir, file)
            if not os.path.exists(file_path):
                missing_files.append(file)
        
        if missing_files:
            messagebox.showwarning("Archivos Faltantes", 
                                 f"Archivos faltantes en {backend_dir}/:\n" + 
                                 "\n".join([f"- {file}" for file in missing_files]) +
                                 "\n\nLa aplicación puede no funcionar correctamente.")
            return False
            
        print("Estructura de directorios verificada correctamente")
        return True
        
    def setup_application(self):
        """Configurar la aplicación completa"""
        self.ui.setup_main_window()
        self.ui.create_main_interface()

    def on_window_close_attempt(self):
        """Manejar intento de cierre de ventana"""
        if any([self.is_running_prediction, self.is_running_behavior, self.is_running_optimization]):
            response = messagebox.askyesno(
                "Procesos en Ejecución", 
                "Hay procesos ejecutándose en segundo plano.\n\n"
                "¿Desea cerrar la aplicación de todas formas?\n"
                "Los procesos continuarán ejecutándose."
            )
            if not response:
                return
                
        # Confirmar cierre
        if messagebox.askokcancel("Salir", "¿Desea cerrar SAIDI Analysis Pro?"):
            # Limpiar datos globales al salir
            ExcelManager.clear_excel()
            self.root.destroy()

    # ============================================================================
    # GESTIÓN DE ARCHIVOS EXCEL
    # ============================================================================
    
    def select_excel_file(self):
        """Seleccionar archivo Excel sin cerrar la ventana principal"""
        try:
            self.ui.update_status("Abriendo selector de archivos...")
            
            # Asegurar que la ventana esté en primer plano antes del diálogo
            self.root.lift()
            self.root.update()
            
            # Configurar el diálogo de archivo
            filetypes = [
                ('Archivos Excel', '*.xlsx *.xls'),
                ('Excel 2007+', '*.xlsx'),
                ('Excel 97-2003', '*.xls'),
                ('Todos los archivos', '*.*')
            ]
            
            # Mostrar diálogo de selección
            file_path = filedialog.askopenfilename(
                parent=self.root,
                title="Seleccionar Archivo Excel - SAIDI Analysis Pro",
                filetypes=filetypes,
                initialdir=os.getcwd()
            )
            
            # Restaurar pantalla completa
            self.ui.ensure_fullscreen()
            
            if file_path:
                self.process_selected_excel(file_path)
            else:
                self.ui.update_status("Selección de archivo cancelada")
                
        except Exception as e:
            print(f"ERROR en select_excel_file: {e}")
            messagebox.showerror("Error", f"Error al seleccionar archivo: {str(e)}")
            self.ui.update_status("Error al seleccionar archivo")
            self.ui.ensure_fullscreen()

    def process_selected_excel(self, file_path):
        """Procesar el archivo Excel seleccionado"""
        try:
            self.ui.update_status("Validando archivo Excel...")
            
            # Verificar que el archivo existe
            if not os.path.exists(file_path):
                messagebox.showerror("Error", "El archivo seleccionado no existe.")
                self.ui.update_status("Error: Archivo no encontrado")
                self.ui.ensure_fullscreen()
                return
            
            # Verificar extensión
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in ['.xlsx', '.xls']:
                messagebox.showerror("Error", "Por favor seleccione un archivo Excel válido (.xlsx o .xls)")
                self.ui.update_status("Error: Formato de archivo no válido")
                self.ui.ensure_fullscreen()
                return
            
            # Validación rápida del archivo
            try:
                df = pd.read_excel(file_path, nrows=5)
                if df.empty:
                    messagebox.showerror("Error", "El archivo Excel está vacío.")
                    self.ui.update_status("Error: Archivo vacío")
                    self.ui.ensure_fullscreen()
                    return
                    
            except Exception as e:
                messagebox.showerror("Error", f"No se puede leer el archivo Excel:\n{str(e)}")
                self.ui.update_status("Error: No se puede leer el archivo")
                self.ui.ensure_fullscreen()
                return
            
            # Cargar el archivo usando ExcelManager
            self.ui.update_status("Cargando y validando estructura del archivo...")
            success = ExcelManager.load_excel(file_path)
            
            if success:
                # Actualizar interfaz
                self.ui.update_excel_info_display(file_path)
                self.on_excel_loaded()
                self.ui.ensure_fullscreen()
                
                print(f"Excel cargado exitosamente: {file_path}")
                
                excel_info = ExcelManager.get_excel_info()
                self.ui.update_status(f"Excel cargado: {excel_info['file_name']} - {excel_info['rows']} filas, {excel_info['columns']} columnas - Sistema listo")
                
            else:
                self.ui.update_status("Error al cargar el archivo")
                self.ui.ensure_fullscreen()
                
        except Exception as e:
            print(f"ERROR en process_selected_excel: {e}")
            messagebox.showerror("Error", f"Error inesperado al procesar el archivo:\n{str(e)}")
            self.ui.update_status("Error inesperado")
            self.ui.ensure_fullscreen()
        
    def on_excel_loaded(self):
        """Callback ejecutado cuando se carga un Excel exitosamente"""
        print("DEBUG: on_excel_loaded() iniciado")
        
        if not ExcelManager.is_excel_loaded():
            print("ERROR: on_excel_loaded llamado pero ExcelManager reporta no cargado")
            return
        
        # Usar after() para asegurar que la interfaz se actualice correctamente
        def update_interface():
            try:
                print("DEBUG: Actualizando interfaz después de cargar Excel")
                self.ui.update_modules_state()
                excel_info = ExcelManager.get_excel_info()
                self.ui.update_status(f"Excel cargado: {excel_info['file_name']} - Sistema listo para análisis")
                print("Módulos habilitados después de cargar Excel")
            except Exception as e:
                print(f"ERROR en update_interface: {e}")
        
        # Ejecutar actualización de interfaz con un pequeño delay
        self.root.after(100, update_interface)
        
        # Asegurar pantalla completa después de cargar Excel  
        self.root.after(200, self.ui.ensure_fullscreen)

    # ============================================================================
    # MÓDULOS DE ANÁLISIS CON SELECTOR DE PARÁMETROS
    # ============================================================================
    
    def run_prediction(self):
        """Ejecutar análisis predictivo con selector de parámetros"""
        if self.is_running_prediction:
            messagebox.showwarning("Proceso en Ejecución", 
                                 "El análisis predictivo ya se está ejecutando.\n"
                                 "Por favor espere a que termine.")
            return
            
        if not ExcelManager.is_excel_loaded():
            messagebox.showerror("Error", "Debe cargar un archivo Excel primero.")
            return
            
        # Mostrar selector de parámetros
        self.ui.update_status("Configurando parámetros para análisis predictivo...")
        print("DEBUG: Abriendo selector de parámetros para predicción...")
        
        show_parameter_selector(self.root, self.execute_prediction_with_params, "Análisis Predictivo SAIDI")
        
    def execute_prediction_with_params(self):
        """Ejecutar predicción con los parámetros seleccionados"""
        try:
            order, seasonal_order, confirmed = get_selected_parameters()
            
            if not confirmed:
                self.ui.update_status("Análisis predictivo cancelado por el usuario")
                print("DEBUG: Usuario canceló la selección de parámetros")
                return
                
            print(f"DEBUG: Ejecutando predicción con parámetros - order: {order}, seasonal_order: {seasonal_order}")
            
            # Marcar como en ejecución y actualizar interfaz
            self.is_running_prediction = True
            self.ui.update_running_state('prediction', True)
            
            excel_info = ExcelManager.get_excel_info()
            self.ui.update_status(f"Ejecutando análisis predictivo SARIMAX{order}x{seasonal_order} con {excel_info['file_name']}...")
            
            backend_script = os.path.join("backend", "Modelo.py")
            file_path = ExcelManager.get_file_path()
            
            # Ejecutar script con parámetros personalizados
            self.run_script_with_parameters(
                script_path=backend_script,
                description=f"Análisis predictivo SARIMAX{order}x{seasonal_order}",
                selected_file=file_path,
                order=order,
                seasonal_order=seasonal_order,
                callback_finished=self.on_prediction_finished
            )
            
        except Exception as e:
            print(f"ERROR en execute_prediction_with_params: {e}")
            messagebox.showerror("Error", f"Error al ejecutar análisis predictivo: {str(e)}")
            self.on_prediction_finished()
            
    def run_behavior_analysis(self):
        """Ejecutar análisis de comportamiento con selector de parámetros"""
        if self.is_running_behavior:
            messagebox.showwarning("Proceso en Ejecución", 
                                 "El análisis de comportamiento ya se está ejecutando.\n"
                                 "Por favor espere a que termine.")
            return
            
        if not ExcelManager.is_excel_loaded():
            messagebox.showerror("Error", "Debe cargar un archivo Excel primero.")
            return
            
        # Mostrar selector de parámetros
        self.ui.update_status("Configurando parámetros para análisis de comportamiento...")
        print("DEBUG: Abriendo selector de parámetros para análisis de comportamiento...")
        
        show_parameter_selector(self.root, self.execute_behavior_with_params, "Análisis de Precisión del Modelo")
        
    def execute_behavior_with_params(self):
        """Ejecutar análisis de comportamiento con los parámetros seleccionados"""
        try:
            order, seasonal_order, confirmed = get_selected_parameters()
            
            if not confirmed:
                self.ui.update_status("Análisis de comportamiento cancelado por el usuario")
                print("DEBUG: Usuario canceló la selección de parámetros")
                return
                
            print(f"DEBUG: Ejecutando análisis de comportamiento con parámetros - order: {order}, seasonal_order: {seasonal_order}")
            
            # Marcar como en ejecución y actualizar interfaz
            self.is_running_behavior = True
            self.ui.update_running_state('behavior', True)
            
            excel_info = ExcelManager.get_excel_info()
            self.ui.update_status(f"Generando análisis de precisión SARIMAX{order}x{seasonal_order} con {excel_info['file_name']}...")
            
            backend_script = os.path.join("backend", "visual.py")
            file_path = ExcelManager.get_file_path()
            
            # Ejecutar script con parámetros personalizados
            self.run_script_with_parameters(
                script_path=backend_script,
                description=f"Análisis de precisión SARIMAX{order}x{seasonal_order}",
                selected_file=file_path,
                order=order,
                seasonal_order=seasonal_order,
                callback_finished=self.on_behavior_finished
            )
            
        except Exception as e:
            print(f"ERROR en execute_behavior_with_params: {e}")
            messagebox.showerror("Error", f"Error al ejecutar análisis de comportamiento: {str(e)}")
            self.on_behavior_finished()

    def run_script_with_parameters(self, script_path, description, selected_file, order, seasonal_order, callback_finished=None):
        """Ejecutar script con parámetros SARIMAX personalizados"""
        def run_in_thread():
            try:
                self.ui.update_status(f"Ejecutando {description}...")
                
                # Verificar que el archivo existe
                if not os.path.exists(script_path):
                    messagebox.showerror("Error", 
                                    f"No se encuentra el archivo {script_path}\n"
                                    f"Estructura esperada:\n"
                                    f"  - Interfaz/ (carpeta actual)\n"
                                    f"  - backend/ (scripts de Python)\n"
                                    f"    - {os.path.basename(script_path)}")
                    self.ui.update_status("Error: Archivo no encontrado")
                    if callback_finished:
                        self.root.after(100, callback_finished)
                    return
                    
                # Crear el entorno con la codificación correcta
                env = os.environ.copy()
                env['PYTHONIOENCODING'] = 'utf-8'
                
                # Crear comando con parámetros
                cmd_args = [
                    sys.executable, script_path, 
                    '--file', os.path.abspath(selected_file),
                    '--order'
                ]
                
                # Agregar parámetros order
                for param in order:
                    cmd_args.append(str(param))
                    
                cmd_args.append('--seasonal-order')
                
                # Agregar parámetros seasonal_order
                for param in seasonal_order:
                    cmd_args.append(str(param))
                
                print(f"Ejecutando: {' '.join(cmd_args)}")
                
                # Ejecutar proceso en segundo plano
                process = subprocess.Popen(cmd_args, 
                                        env=env,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                
                # Esperar a que termine el proceso
                return_code = process.wait()
                
                if return_code == 0:
                    excel_info = ExcelManager.get_excel_info()
                    self.ui.update_status(f"{description} completado con {excel_info['file_name']}")
                    print(f"{description} ejecutado correctamente")
                        
                else:
                    self.ui.update_status(f"Error en {description}")
                    print(f"Error en {description} - Código: {return_code}")
                    
            except Exception as e:
                self.ui.update_status("Error inesperado")
                print(f"ERROR: {e}")
                messagebox.showerror("Error", f"Error inesperado: {str(e)}")
            finally:
                # Ejecutar callback cuando el proceso termine
                print(f"DEBUG: Proceso terminado, ejecutando callback...")
                if callback_finished:
                    self.root.after(500, callback_finished)
        
        thread = threading.Thread(target=run_in_thread)
        thread.daemon = True
        thread.start()

    # ============================================================================
    # OPTIMIZACIÓN DE PARÁMETROS
    # ============================================================================
        
    def run_parameter_optimization(self):
        """Ejecutar optimización de parámetros con ventana de progreso"""
        if self.is_running_optimization:
            messagebox.showwarning("Proceso en Ejecución", 
                                "La optimización de parámetros ya se está ejecutando.\n"
                                "Por favor espere a que termine.")
            return
            
        if not ExcelManager.is_excel_loaded():
            messagebox.showerror("Error", "Debe cargar un archivo Excel primero.")
            return
            
        # Advertencia sobre el tiempo de procesamiento
        response = messagebox.askyesno("Advertencia - Proceso Extenso",
                                    "La optimización de parámetros puede tardar más de 12 horas.\n\n"
                                    "Se mostrará una ventana de progreso con información detallada.\n\n"
                                    "¿Desea continuar?")
        
        if response:
            # Marcar como en ejecución
            self.is_running_optimization = True
            self.ui.update_running_state('optimization', True)
            
            excel_info = ExcelManager.get_excel_info()
            self.ui.update_status(f"Iniciando optimización de parámetros con {excel_info['file_name']}...")
            
            # Crear archivo temporal válido
            try:
                temp_dir = tempfile.gettempdir()
                temp_filename = f"saidi_progress_{int(time.time())}.json"
                self.temp_progress_file = os.path.join(temp_dir, temp_filename)
                
                # Verificar que el directorio existe y es escribible
                if not os.path.exists(temp_dir):
                    os.makedirs(temp_dir, exist_ok=True)
                
                # Inicializar el archivo con datos básicos
                initial_data = {
                    'progress': 0,
                    'status': 'Iniciando proceso...',
                    'current_model': '',
                    'top_models': [],
                    'timestamp': pd.Timestamp.now().isoformat() if 'pd' in globals() else str(time.time()),
                    'pid': os.getpid()
                }
                
                with open(self.temp_progress_file, 'w', encoding='utf-8') as f:
                    json.dump(initial_data, f, ensure_ascii=False, indent=2)
                
                print(f"Archivo de progreso creado: {self.temp_progress_file}")
                
            except Exception as e:
                print(f"ERROR creando archivo de progreso: {e}")
                messagebox.showerror("Error", f"No se pudo crear archivo temporal: {str(e)}")
                self.is_running_optimization = False
                self.ui.update_running_state('optimization', False)
                return
            
            # Inicializar datos globales
            global PROGRESS_DATA
            PROGRESS_DATA = {
                'percentage': 0,
                'current_model': '',
                'status': 'Iniciando proceso...',
                'top_models': []
            }
            
            # Crear ventana de progreso
            self.progress_window = ProgressWindow(self.root, 
                                                title="Optimización de Parámetros", 
                                                progress_file=self.temp_progress_file)
            
            # Configurar callback para cuando se cierre la ventana de progreso
            if hasattr(self.progress_window, 'window'):
                self.progress_window.window.protocol("WM_DELETE_WINDOW", self.on_optimization_window_closed)
            
            # Iniciar proceso en hilo separado
            backend_script = os.path.join("backend", "Parametro.py")
            file_path = ExcelManager.get_file_path()
            self.start_optimization_process(file_path, backend_script)
        else:
            self.ui.update_status("Optimización cancelada por el usuario")

    def on_optimization_window_closed(self):
        """Callback cuando se cierra la ventana de optimización"""
        self.is_running_optimization = False
        self.ui.update_running_state('optimization', False)
        if self.progress_window:
            self.progress_window.cancelled = True
            
    def start_optimization_process(self, file_path, backend_script):
        """Iniciar el proceso de optimización en un hilo separado"""
        def run_optimization():
            try:
                # Verificar que el archivo de progreso existe antes de iniciar el proceso
                if not os.path.exists(self.temp_progress_file):
                    print(f"ERROR: Archivo de progreso no existe: {self.temp_progress_file}")
                    self.ui.update_status("Error: No se pudo crear archivo de comunicación")
                    return
                
                # Ejecutar el script de optimización
                env = os.environ.copy()
                env['PYTHONIOENCODING'] = 'utf-8'
                
                cmd_args = [sys.executable, backend_script, 
                        '--file', file_path, 
                        '--progress', self.temp_progress_file]
                
                print(f"DEBUG: Iniciando proceso con archivo de progreso: {self.temp_progress_file}")
                print(f"DEBUG: Comando: {' '.join(cmd_args)}")
                
                # Verificar que el backend script existe
                if not os.path.exists(backend_script):
                    print(f"ERROR: Script backend no existe: {backend_script}")
                    self.ui.update_status("Error: Script backend no encontrado")
                    return
                
                # Ejecutar desde el directorio actual (Interfaz)
                process = subprocess.Popen(cmd_args, env=env)
                
                # Monitorear progreso
                self.monitor_progress()
                
                # Esperar a que termine el proceso
                process.wait()
                
                if process.returncode == 0:
                    self.ui.update_status("Optimización completada exitosamente")
                    print("DEBUG: Proceso completado exitosamente")
                    # Dar tiempo extra para procesar resultados finales
                    time.sleep(2)
                    if self.progress_window and not self.progress_window.results_shown:
                        self.progress_window.check_and_show_results()
                elif process.returncode == 130:  # Código de cancelación
                    self.ui.update_status("Optimización cancelada por el usuario")
                    print("DEBUG: Proceso cancelado por el usuario")
                else:
                    self.ui.update_status("Error en optimización")
                    messagebox.showerror("Error", f"Error durante la optimización (código: {process.returncode})")
                    
            except Exception as e:
                self.ui.update_status("Error inesperado")
                messagebox.showerror("Error", f"Error inesperado: {str(e)}")
                print(f"ERROR: {e}")
            finally:
                # Asegurar que se marque como terminado
                self.root.after(1000, self.on_optimization_finished)
                
        thread = threading.Thread(target=run_optimization)
        thread.daemon = True
        thread.start()

    def monitor_progress(self):
        """Monitorear el progreso del proceso"""
        def update_progress():
            try:
                if os.path.exists(self.temp_progress_file):
                    with open(self.temp_progress_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    print(f"DEBUG: Datos leídos del archivo: {data.keys()}")
                    
                    # Actualizar variables globales
                    global PROGRESS_DATA
                    PROGRESS_DATA['percentage'] = data.get('progress', 0)
                    PROGRESS_DATA['status'] = data.get('status', '')
                    PROGRESS_DATA['current_model'] = data.get('current_model', '')
                    PROGRESS_DATA['top_models'] = data.get('top_models', [])
                    
                    print(f"DEBUG: Progreso: {PROGRESS_DATA['percentage']}%, Top models: {len(PROGRESS_DATA['top_models'])}")
                    
                    # Actualizar ventana de progreso
                    if self.progress_window and hasattr(self.progress_window, 'window') and self.progress_window.window.winfo_exists():
                        self.progress_window.update_progress(
                            PROGRESS_DATA['percentage'],
                            PROGRESS_DATA['status'],
                            PROGRESS_DATA['current_model']
                        )
                        
                        # Si el proceso terminó y hay modelos, mostrar resultados
                        if (PROGRESS_DATA['percentage'] >= 100 and 
                            PROGRESS_DATA['top_models'] and 
                            not self.progress_window.results_shown):
                            
                            print(f"DEBUG: Mostrando resultados finales - {len(PROGRESS_DATA['top_models'])} modelos")
                            self.progress_window.show_results(PROGRESS_DATA['top_models'])
                            
                            # Limpiar el archivo temporal
                            try:
                                os.remove(self.temp_progress_file)
                            except:
                                pass
                            return
                            
                # Continuar monitoreando si el proceso no ha terminado
                if (self.progress_window and 
                    not self.progress_window.cancelled and 
                    hasattr(self.progress_window, 'window') and 
                    self.progress_window.window.winfo_exists() and
                    not self.progress_window.results_shown):
                    
                    self.root.after(500, update_progress)
                    
            except FileNotFoundError:
                # El archivo aún no existe, continuar monitoreando
                if (self.progress_window and 
                    not self.progress_window.cancelled and 
                    hasattr(self.progress_window, 'window') and 
                    self.progress_window.window.winfo_exists() and
                    not self.progress_window.results_shown):
                    self.root.after(500, update_progress)
                    
            except json.JSONDecodeError as e:
                print(f"DEBUG: Error JSON: {e} - continuando...")
                if (self.progress_window and 
                    not self.progress_window.cancelled and 
                    hasattr(self.progress_window, 'window') and 
                    self.progress_window.window.winfo_exists() and
                    not self.progress_window.results_shown):
                    self.root.after(500, update_progress)
                    
            except Exception as e:
                print(f"ERROR: Monitoreando progreso: {e}")
                if (self.progress_window and 
                    not self.progress_window.cancelled and 
                    hasattr(self.progress_window, 'window') and 
                    self.progress_window.window.winfo_exists() and
                    not self.progress_window.results_shown):
                    self.root.after(1000, update_progress)
                
        update_progress()
            
    def on_prediction_finished(self):
        """Callback cuando termina el análisis predictivo"""
        print("DEBUG: Análisis predictivo terminado")
        self.is_running_prediction = False
        self.ui.update_running_state('prediction', False)
        self.ui.update_status("Análisis predictivo completado. Sistema listo para nuevas operaciones.")
            
    def on_behavior_finished(self):
        """Callback cuando termina el análisis de comportamiento"""
        print("DEBUG: Análisis de comportamiento terminado")
        self.is_running_behavior = False
        self.ui.update_running_state('behavior', False)
        self.ui.update_status("Análisis de comportamiento completado. Sistema listo para nuevas operaciones.")
        
    def on_optimization_finished(self):
        """Callback cuando termina la optimización"""
        self.is_running_optimization = False
        self.ui.update_running_state('optimization', False)
        
        # Limpiar archivo temporal al finalizar
        if hasattr(self, 'temp_progress_file') and self.temp_progress_file:
            try:
                if os.path.exists(self.temp_progress_file):
                    os.remove(self.temp_progress_file)
                    print(f"Archivo temporal limpiado: {self.temp_progress_file}")
            except Exception as e:
                print(f"Advertencia: No se pudo limpiar archivo temporal: {e}")
            finally:
                self.temp_progress_file = None
        
        self.ui.update_status("Optimización de parámetros completada. Sistema listo para nuevas operaciones.")


def main():
    """Función principal de la aplicación"""
    root = tk.Tk()
    app = SAIDIAnalysisApp(root)
    
    # Iniciar aplicación
    root.mainloop()


if __name__ == "__main__":
    main()