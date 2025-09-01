# python_saidi_gui.py - Interfaz Principal que permanece visible durante ejecución
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import os
import threading
import tempfile
import json
import time

# Importar módulos locales
from excel_manager import ExcelManager
from ui_components import UIComponents
from ParametroV import ProgressWindow, PROGRESS_DATA
from tkinter import filedialog
import pandas as pd

# NUEVA IMPORTACIÓN: Selector de parámetros
from selectorOrder import show_parameter_selector, get_selected_parameters, reset_parameters


class SAIDIAnalysisGUI:
    def __init__(self, root):
        self.root = root
        self.temp_progress_file = None
        self.progress_window = None
        self.module_buttons = {}
        self.excel_components = {}
        
        # Variables de control para evitar ejecuciones múltiples
        self.is_running_prediction = False
        self.is_running_behavior = False
        self.is_running_optimization = False
        
        # Variable para controlar visibilidad - SIMPLIFICADA
        self.window_initialized = False
        
        # NUEVAS VARIABLES: Para almacenar parámetros pendientes de ejecutar
        self.pending_prediction_params = None
        self.pending_behavior_params = None
        
        # Verificar estructura de directorios al inicio
        self.verify_directory_structure()
        
        self.setup_main_window()
        self.create_main_interface()
        
        # Marcar como inicializada después de crear todo
        self.window_initialized = True

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
            
        print("✓ Estructura de directorios verificada correctamente")
        return True
        
    def setup_main_window(self):
        """Configuración principal de la ventana - SIMPLIFICADA"""
        self.root.title("SAIDI Analysis Pro - Sistema de Análisis Predictivo")
        
        # Pantalla completa
        self.root.state('zoomed')  # Windows
        # Para Linux/Mac usar: self.root.attributes('-zoomed', True)
        
        self.root.configure(bg='#f8fafc')
        
        # Evitar que la ventana se cierre accidentalmente
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close_attempt)
        
        # Configurar estilo
        self.setup_styles()
        
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
                return  # No cerrar
                
        # Confirmar cierre
        if messagebox.askokcancel("Salir", "¿Desea cerrar SAIDI Analysis Pro?"):
            # Limpiar datos globales al salir
            ExcelManager.clear_excel()
            self.root.destroy()
        
    def setup_styles(self):
        """Configurar estilos personalizados"""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
    def create_main_interface(self):
        """Crear la interfaz principal"""
        # Frame principal con padding optimizado
        main_frame = tk.Frame(self.root, bg='#f8fafc')
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Header más compacto
        self.create_header(main_frame)
        
        # Sección de carga de Excel más compacta - MANEJADA DIRECTAMENTE
        self.create_excel_load_section(main_frame)
        
        # Contenedor de módulos más compacto
        self.module_buttons = UIComponents.create_analysis_modules(
            main_frame,
            module_callbacks={
                'prediction': self.run_prediction,  # MODIFICADO: Ahora abre selector primero
                'behavior': self.run_behavior_analysis,  # MODIFICADO: Ahora abre selector primero
                'optimization': self.run_parameter_optimization
            }
        )
        
        # Footer posicionado al final sin espacio extra
        self.create_footer(main_frame)
        
        # Estado inicial de botones - CORREGIDO: Verificar inmediatamente si ya hay Excel
        self.update_modules_state()
        
    def create_header(self, parent):
        """Crear el header más compacto"""
        # Frame principal del header más pequeño
        header_frame = tk.Frame(parent, bg='#2563eb', height=50)
        header_frame.pack(fill='x', pady=(0, 10))
        header_frame.pack_propagate(False)
        
        # Simular gradiente con un frame más pequeño
        gradient_frame = tk.Frame(header_frame, bg='#1e40af', height=6)
        gradient_frame.pack(fill='x', side='bottom')
        
        # Título principal más compacto
        title_label = tk.Label(header_frame, 
                              text="SAIDI Analysis Pro",
                              font=('Segoe UI', 18, 'bold'),
                              bg='#2563eb', fg='white')
        title_label.pack(pady=(8, 2))
        
        # Subtítulo más pequeño
        subtitle_label = tk.Label(header_frame,
                                 text="Sistema Integral de Análisis Predictivo SAIDI",
                                 font=('Segoe UI', 9),
                                 bg='#2563eb', fg='#bfdbfe')
        subtitle_label.pack()
        
    def create_footer(self, parent):
        """Crear el footer más compacto y pegado al final"""
        footer_frame = tk.Frame(parent, bg='#f8fafc')
        footer_frame.pack(fill='x', side='bottom', pady=(5, 0))
        
        # Línea separadora más delgada
        separator = tk.Frame(footer_frame, bg='#d1d5db', height=1)
        separator.pack(fill='x', pady=(0, 5))
        
        # Información del footer más compacta
        footer_label = tk.Label(footer_frame,
                               text="© 2025 SAIDI Analysis Pro | Sistema de Análisis Predictivo de Calidad del Servicio Eléctrico",
                               font=('Segoe UI', 8), bg='#f8fafc', fg='#4b5563',
                               wraplength=1200)
        footer_label.pack(pady=(0, 2))
        
        # Status bar más compacto
        self.status_var = tk.StringVar()
        self.status_var.set("Sistema listo - Cargar archivo Excel para comenzar")
        
        status_label = tk.Label(footer_frame,
                               textvariable=self.status_var,
                               font=('Segoe UI', 8), bg='#f8fafc', fg='#6b7280',
                               wraplength=1200)
        status_label.pack(pady=(0, 2))

    def create_excel_load_section(self, parent):
        """Crear sección de carga de Excel - MANEJADA DIRECTAMENTE"""
        # Frame principal para la sección Excel
        excel_frame = tk.LabelFrame(parent, text="📊 Carga de Datos Excel", 
                                   font=('Segoe UI', 11, 'bold'),
                                   bg='#f8fafc', fg='#1e40af',
                                   relief='ridge', bd=2)
        excel_frame.pack(fill='x', pady=(0, 15), padx=10)
        
        # Frame interno con padding
        inner_frame = tk.Frame(excel_frame, bg='#f8fafc')
        inner_frame.pack(fill='x', padx=20, pady=15)
        
        # Frame para botón y información del archivo
        button_frame = tk.Frame(inner_frame, bg='#f8fafc')
        button_frame.pack(fill='x')
        
        # Botón de selección de archivo
        self.excel_button = tk.Button(button_frame,
                                     text="📁 SELECCIONAR ARCHIVO EXCEL",
                                     command=self.select_excel_file,  # MÉTODO PROPIO
                                     font=('Segoe UI', 10, 'bold'),
                                     bg='#059669', fg='white',
                                     relief='raised', bd=2,
                                     cursor='hand2',
                                     padx=20, pady=10)
        self.excel_button.pack(side='left')
        
        # Información del archivo cargado
        self.file_info_frame = tk.Frame(button_frame, bg='#f8fafc')
        self.file_info_frame.pack(side='left', fill='x', expand=True, padx=(20, 0))
        
        # Label para mostrar información del archivo
        self.file_info_label = tk.Label(self.file_info_frame,
                                       text="No hay archivo cargado",
                                       font=('Segoe UI', 9),
                                       bg='#f8fafc', fg='#6b7280',
                                       anchor='w')
        self.file_info_label.pack(fill='x')
        
        # Label para información adicional
        self.file_details_label = tk.Label(self.file_info_frame,
                                          text="Seleccione un archivo .xlsx o .xls para comenzar",
                                          font=('Segoe UI', 8),
                                          bg='#f8fafc', fg='#9ca3af',
                                          anchor='w')
        self.file_details_label.pack(fill='x')
        
        # Agregar efectos hover al botón
        self.add_button_hover_effects(self.excel_button, '#047857', '#059669')
        
        # Guardar referencia de componentes
        self.excel_components = {
            'button': self.excel_button,
            'info_label': self.file_info_label,
            'details_label': self.file_details_label,
            'frame': excel_frame
        }

    def add_button_hover_effects(self, button, hover_color, normal_color):
        """Agregar efectos hover a botones"""
        def on_enter(e):
            button.config(bg=hover_color)
        
        def on_leave(e):
            button.config(bg=normal_color)
            
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)

    def select_excel_file(self):
        """Seleccionar archivo Excel sin cerrar la ventana principal"""
        try:
            # Actualizar status antes de mostrar el diálogo
            self.update_status("Abriendo selector de archivos...")
            
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
            
            # Mostrar diálogo de selección - DEBE aparecer encima de la ventana principal
            file_path = filedialog.askopenfilename(
                parent=self.root,  # IMPORTANTE: especificar parent
                title="Seleccionar Archivo Excel - SAIDI Analysis Pro",
                filetypes=filetypes,
                initialdir=os.getcwd()
            )
            
            # RESTAURAR PANTALLA COMPLETA inmediatamente después del diálogo
            self.ensure_fullscreen()
            
            # La ventana principal nunca se cierra porque especificamos parent
            
            if file_path:
                # Procesar el archivo seleccionado
                self.process_selected_excel(file_path)
            else:
                # Usuario canceló la selección
                self.update_status("Selección de archivo cancelada")
                
        except Exception as e:
            print(f"ERROR en select_excel_file: {e}")
            messagebox.showerror("Error", f"Error al seleccionar archivo: {str(e)}")
            self.update_status("Error al seleccionar archivo")
            # Restaurar pantalla completa incluso en caso de error
            self.ensure_fullscreen()

    def process_selected_excel(self, file_path):
        """Procesar el archivo Excel seleccionado"""
        try:
            self.update_status("Validando archivo Excel...")
            
            # Verificar que el archivo existe
            if not os.path.exists(file_path):
                messagebox.showerror("Error", "El archivo seleccionado no existe.")
                self.update_status("Error: Archivo no encontrado")
                self.ensure_fullscreen()
                return
            
            # Verificar extensión
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in ['.xlsx', '.xls']:
                messagebox.showerror("Error", "Por favor seleccione un archivo Excel válido (.xlsx o .xls)")
                self.update_status("Error: Formato de archivo no válido")
                self.ensure_fullscreen()
                return
            
            # Intentar leer el archivo para validación rápida
            try:
                df = pd.read_excel(file_path, nrows=5)
                if df.empty:
                    messagebox.showerror("Error", "El archivo Excel está vacío.")
                    self.update_status("Error: Archivo vacío")
                    self.ensure_fullscreen()
                    return
                    
            except Exception as e:
                messagebox.showerror("Error", f"No se puede leer el archivo Excel:\n{str(e)}")
                self.update_status("Error: No se puede leer el archivo")
                self.ensure_fullscreen()
                return
            
            # Cargar el archivo usando ExcelManager
            self.update_status("Cargando y validando estructura del archivo...")
            success = ExcelManager.load_excel(file_path)
            
            if success:
                # Actualizar interfaz con información del archivo
                self.update_excel_info_display(file_path)
                
                # CORRECCIÓN CRÍTICA: Habilitar módulos después de cargar
                self.on_excel_loaded()
                
                # Restaurar pantalla completa después de cargar Excel
                self.ensure_fullscreen()
                
                print(f"✓ Excel cargado exitosamente: {file_path}")
                
                # Mostrar mensaje de éxito más discreto en el status
                excel_info = ExcelManager.get_excel_info()
                self.update_status(f"✓ Excel cargado: {excel_info['file_name']} - {excel_info['rows']} filas, {excel_info['columns']} columnas - Sistema listo")
                
            else:
                # El error ya se mostró en ExcelManager.load_excel()
                self.update_status("Error al cargar el archivo")
                self.ensure_fullscreen()
                
        except Exception as e:
            print(f"ERROR en process_selected_excel: {e}")
            messagebox.showerror("Error", f"Error inesperado al procesar el archivo:\n{str(e)}")
            self.update_status("Error inesperado")
            self.ensure_fullscreen()
    def update_excel_info_display(self, file_path):
        """Actualizar la información mostrada del archivo Excel"""
        try:
            # Obtener información del archivo
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            file_size_mb = file_size / (1024 * 1024)
            
            # Obtener información adicional del Excel
            try:
                df = pd.read_excel(file_path, nrows=0)  # Solo headers
                columns_count = len(df.columns)
                
                # Contar filas (más eficiente)
                df_full = pd.read_excel(file_path)
                rows_count = len(df_full)
                
                details_text = f"📋 {rows_count:,} filas, {columns_count} columnas • {file_size_mb:.1f} MB"
                
            except:
                details_text = f"📋 Archivo válido • {file_size_mb:.1f} MB"
            
            # Actualizar labels
            self.file_info_label.config(
                text=f"✅ {file_name}",
                fg='#059669'  # Verde para éxito
            )
            
            self.file_details_label.config(
                text=details_text,
                fg='#374151'  # Gris oscuro para detalles
            )
            
            # Cambiar texto del botón
            self.excel_button.config(text="📁 CAMBIAR ARCHIVO EXCEL")
            
        except Exception as e:
            print(f"ERROR en update_excel_info_display: {e}")
            # Fallback básico
            file_name = os.path.basename(file_path)
            self.file_info_label.config(text=f"✅ {file_name}", fg='#059669')
            self.file_details_label.config(text="Archivo cargado correctamente", fg='#374151')

    def ensure_fullscreen(self):
        """Asegurar que la ventana esté en pantalla completa"""
        try:
            # Forzar que la ventana vuelva al estado maximizado
            self.root.state('zoomed')  # Windows
            
            # Para sistemas Linux/Mac, usar también:
            # self.root.attributes('-zoomed', True)
            
            # Traer la ventana al frente
            self.root.lift()
            
            # Forzar actualización de la ventana
            self.root.update_idletasks()
            self.root.update()
            
            print("✓ Ventana restaurada a pantalla completa")
            
        except Exception as e:
            print(f"ERROR en ensure_fullscreen: {e}")
            try:
                # Fallback: intentar maximizar de forma alternativa
                self.root.wm_state('zoomed')
            except:
                pass
        
    def update_status(self, message):
        """Actualizar el status bar - SIMPLIFICADO"""
        self.status_var.set(message)
        self.root.update_idletasks()
        
    def on_excel_loaded(self):
        """Callback ejecutado cuando se carga un Excel exitosamente - CORREGIDO"""
        print("DEBUG: on_excel_loaded() iniciado")
        
        # CORRECCIÓN: Verificar que ExcelManager efectivamente tiene datos cargados
        if not ExcelManager.is_excel_loaded():
            print("ERROR: on_excel_loaded llamado pero ExcelManager reporta no cargado")
            return
        
        # CORRECCIÓN: Usar after() para asegurar que la interfaz se actualice correctamente
        def update_interface():
            try:
                print("DEBUG: Actualizando interfaz después de cargar Excel")
                self.update_modules_state()
                excel_info = ExcelManager.get_excel_info()
                self.update_status(f"Excel cargado: {excel_info['file_name']} - Sistema listo para análisis")
                print("✓ Módulos habilitados después de cargar Excel")
            except Exception as e:
                print(f"ERROR en update_interface: {e}")
        
        # Ejecutar actualización de interfaz con un pequeño delay
        self.root.after(100, update_interface)
        
        # Asegurar pantalla completa después de cargar Excel  
        self.root.after(200, self.ensure_fullscreen)
        
    def update_modules_state(self):
        """Actualizar el estado de los módulos basado en si hay Excel cargado - CORREGIDO"""
        # CORRECCIÓN: Verificar directamente con ExcelManager
        excel_loaded = ExcelManager.is_excel_loaded()
        print(f"DEBUG: update_modules_state - Excel loaded: {excel_loaded}")
        
        if not excel_loaded:
            print("DEBUG: No hay Excel cargado, botones permanecen deshabilitados")
            return
            
        # CORRECCIÓN: Actualizar botones directamente usando UIComponents
        success = UIComponents.update_module_buttons_state(self.module_buttons)
        
        if success:
            print("DEBUG: ✓ Botones de módulos actualizados exitosamente")
        else:
            print("DEBUG: ✗ Error al actualizar botones de módulos")

    # ============================================================================
    # NUEVAS FUNCIONES: Integración con Selector de Parámetros
    # ============================================================================
    
    def run_prediction(self):
        """MODIFICADO: Ejecutar análisis predictivo con selector de parámetros"""
        # Verificar que no esté ejecutándose ya
        if self.is_running_prediction:
            messagebox.showwarning("Proceso en Ejecución", 
                                 "El análisis predictivo ya se está ejecutando.\n"
                                 "Por favor espere a que termine.")
            return
            
        if not ExcelManager.is_excel_loaded():
            messagebox.showerror("Error", "Debe cargar un archivo Excel primero.")
            return
            
        # Mostrar selector de parámetros ANTES de ejecutar
        self.update_status("Configurando parámetros para análisis predictivo...")
        print("DEBUG: Abriendo selector de parámetros para predicción...")
        
        # Mostrar el selector de parámetros
        show_parameter_selector(self.root, self.execute_prediction_with_params, "Análisis Predictivo SAIDI")
        
    def execute_prediction_with_params(self):
        """NUEVA FUNCIÓN: Ejecutar predicción con los parámetros seleccionados"""
        try:
            # Obtener parámetros seleccionados
            order, seasonal_order, confirmed = get_selected_parameters()
            
            if not confirmed:
                self.update_status("Análisis predictivo cancelado por el usuario")
                print("DEBUG: Usuario canceló la selección de parámetros")
                return
                
            print(f"DEBUG: Ejecutando predicción con parámetros - order: {order}, seasonal_order: {seasonal_order}")
            
            # Marcar como en ejecución y actualizar interfaz
            self.is_running_prediction = True
            self.update_running_state('prediction', True)
            
            excel_info = ExcelManager.get_excel_info()
            self.update_status(f"Ejecutando análisis predictivo SARIMAX{order}x{seasonal_order} con {excel_info['file_name']}...")
            
            backend_script = os.path.join("backend", "Modelo.py")
            file_path = ExcelManager.get_file_path()
            
            # MODIFICADO: Ejecutar script con parámetros personalizados
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
        """MODIFICADO: Ejecutar análisis de comportamiento con selector de parámetros"""
        # Verificar que no esté ejecutándose ya
        if self.is_running_behavior:
            messagebox.showwarning("Proceso en Ejecución", 
                                 "El análisis de comportamiento ya se está ejecutando.\n"
                                 "Por favor espere a que termine.")
            return
            
        if not ExcelManager.is_excel_loaded():
            messagebox.showerror("Error", "Debe cargar un archivo Excel primero.")
            return
            
        # Mostrar selector de parámetros ANTES de ejecutar
        self.update_status("Configurando parámetros para análisis de comportamiento...")
        print("DEBUG: Abriendo selector de parámetros para análisis de comportamiento...")
        
        # Mostrar el selector de parámetros
        show_parameter_selector(self.root, self.execute_behavior_with_params, "Análisis de Precisión del Modelo")
        
    def execute_behavior_with_params(self):
        """NUEVA FUNCIÓN: Ejecutar análisis de comportamiento con los parámetros seleccionados"""
        try:
            # Obtener parámetros seleccionados
            order, seasonal_order, confirmed = get_selected_parameters()
            
            if not confirmed:
                self.update_status("Análisis de comportamiento cancelado por el usuario")
                print("DEBUG: Usuario canceló la selección de parámetros")
                return
                
            print(f"DEBUG: Ejecutando análisis de comportamiento con parámetros - order: {order}, seasonal_order: {seasonal_order}")
            
            # Marcar como en ejecución y actualizar interfaz
            self.is_running_behavior = True
            self.update_running_state('behavior', True)
            
            excel_info = ExcelManager.get_excel_info()
            self.update_status(f"Generando análisis de precisión SARIMAX{order}x{seasonal_order} con {excel_info['file_name']}...")
            
            backend_script = os.path.join("backend", "visual.py")
            file_path = ExcelManager.get_file_path()
            
            # MODIFICADO: Ejecutar script con parámetros personalizados
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
        """NUEVA FUNCIÓN: Ejecutar script con parámetros SARIMAX personalizados"""
        def run_in_thread():
            try:
                self.update_status(f"Ejecutando {description}...")
                
                # Verificar que el archivo existe
                if not os.path.exists(script_path):
                    messagebox.showerror("Error", 
                                       f"No se encuentra el archivo {script_path}\n"
                                       f"Estructura esperada:\n"
                                       f"  - Interfaz/ (carpeta actual)\n"
                                       f"  - backend/ (scripts de Python)\n"
                                       f"    - {os.path.basename(script_path)}")
                    self.update_status("Error: Archivo no encontrado")
                    if callback_finished:
                        self.root.after(100, callback_finished)
                    return
                    
                # Crear el entorno con la codificación correcta
                env = os.environ.copy()
                env['PYTHONIOENCODING'] = 'utf-8'
                
                # Cambiar al directorio backend temporalmente
                backend_dir = os.path.dirname(script_path)
                script_name = os.path.basename(script_path)
                
                # NUEVA PARTE: Preparar argumentos con parámetros personalizados
                cmd_args = [
                    sys.executable, script_name, 
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
                
                print(f"Ejecutando: {' '.join(cmd_args)} en directorio {backend_dir}")
                
                # Ejecutar proceso en segundo plano SIN interferir con la ventana
                process = subprocess.Popen(cmd_args, 
                                         env=env,
                                         cwd=backend_dir,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE,
                                         creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                
                # Esperar a que termine el proceso SIN manipular la ventana
                return_code = process.wait()
                
                if return_code == 0:
                    excel_info = ExcelManager.get_excel_info()
                    self.update_status(f"{description} completado con {excel_info['file_name']}")
                    print(f"✓ {description} ejecutado correctamente")
                        
                else:
                    self.update_status(f"Error en {description}")
                    print(f"✗ Error en {description} - Código: {return_code}")
                    
            except Exception as e:
                self.update_status("Error inesperado")
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
    # FUNCIONES ORIGINALES (sin cambios para optimización)
    # ============================================================================
            
    def on_prediction_finished(self):
        """Callback cuando termina el análisis predictivo"""
        print("DEBUG: Análisis predictivo terminado")
        self.is_running_prediction = False
        self.update_running_state('prediction', False)
        self.update_status("Análisis predictivo completado. Sistema listo para nuevas operaciones.")
            
    def on_behavior_finished(self):
        """Callback cuando termina el análisis de comportamiento"""
        print("DEBUG: Análisis de comportamiento terminado")
        self.is_running_behavior = False
        self.update_running_state('behavior', False)
        self.update_status("Análisis de comportamiento completado. Sistema listo para nuevas operaciones.")
        
    def update_running_state(self, module_key, is_running):
        """Actualizar el estado visual del módulo cuando está ejecutándose"""
        if module_key in self.module_buttons:
            button = self.module_buttons[module_key]
            if is_running:
                # Cambiar apariencia cuando está ejecutándose
                button.config(
                    text="🔄 EJECUTANDO...",
                    bg='#f59e0b',  # Color naranja para indicar ejecución
                    state='disabled',
                    cursor='wait'
                )
                # Remover hover effects temporalmente
                button.unbind("<Enter>")
                button.unbind("<Leave>")
            else:
                # Restaurar estado normal
                original_texts = {
                    'prediction': 'INICIAR PREDICCIÓN',
                    'behavior': 'ANÁLISIS DE PRECISIÓN',
                    'optimization': 'OPTIMIZAR PARÁMETROS'
                }
                button.config(
                    text=original_texts.get(module_key, 'EJECUTAR'),
                    bg=button.original_color,
                    state='normal',
                    cursor='hand2'
                )
                # Restaurar hover effects
                UIComponents.add_hover_effects(
                    button, 
                    UIComponents.darken_color(button.original_color),
                    button.original_color
                )
            
    def run_parameter_optimization(self):
        """Ejecutar optimización de parámetros con ventana de progreso - SIMPLIFICADO"""
        # Verificar que no esté ejecutándose ya
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
            self.update_running_state('optimization', True)
            
            excel_info = ExcelManager.get_excel_info()
            self.update_status(f"Iniciando optimización de parámetros con {excel_info['file_name']}...")
            
            # Crear archivo temporal para comunicación
            self.temp_progress_file = tempfile.mktemp(suffix='_saidi_progress.json')
            
            # Inicializar datos globales
            global PROGRESS_DATA
            PROGRESS_DATA = {
                'percentage': 0,
                'current_model': '',
                'status': 'Iniciando proceso...',
                'top_models': []
            }
            
            # Mostrar ventana de progreso
            self.progress_window = ProgressWindow(self.root)
            
            # Configurar callback para cuando se cierre la ventana de progreso
            if hasattr(self.progress_window, 'window'):
                self.progress_window.window.protocol("WM_DELETE_WINDOW", self.on_optimization_window_closed)
            
            # Iniciar proceso en hilo separado
            backend_script = os.path.join("backend", "Parametro.py")
            file_path = ExcelManager.get_file_path()
            self.start_optimization_process(file_path, backend_script)
        else:
            self.update_status("Optimización cancelada por el usuario")

    def on_optimization_window_closed(self):
        """Callback cuando se cierra la ventana de optimización"""
        self.is_running_optimization = False
        self.update_running_state('optimization', False)
        if self.progress_window:
            self.progress_window.cancelled = True
            
    def start_optimization_process(self, file_path, backend_script):
        """Iniciar el proceso de optimización en un hilo separado - SIMPLIFICADO"""
        def run_optimization():
            try:
                # Ejecutar el script de optimización
                env = os.environ.copy()
                env['PYTHONIOENCODING'] = 'utf-8'
                
                cmd_args = [sys.executable, backend_script, '--file', file_path, 
                           '--progress', self.temp_progress_file]
                
                print(f"DEBUG: Iniciando proceso: {' '.join(cmd_args)}")
                process = subprocess.Popen(cmd_args, env=env)
                
                # Monitorear progreso
                self.monitor_progress()
                
                # Esperar a que termine el proceso
                process.wait()
                
                if process.returncode == 0:
                    self.update_status("Optimización completada exitosamente")
                    print("DEBUG: Proceso completado exitosamente")
                    # Dar tiempo extra para procesar resultados finales
                    time.sleep(2)
                    if self.progress_window and not self.progress_window.results_shown:
                        self.progress_window.check_and_show_results()
                else:
                    self.update_status("Error en optimización")
                    messagebox.showerror("Error", "Error durante la optimización")
                    
            except Exception as e:
                self.update_status("Error inesperado")
                messagebox.showerror("Error", f"Error inesperado: {str(e)}")
                print(f"ERROR: {e}")
            finally:
                # Asegurar que se marque como terminado
                self.root.after(1000, self.on_optimization_finished)
                
        thread = threading.Thread(target=run_optimization)
        thread.daemon = True
        thread.start()
        
    def on_optimization_finished(self):
        """Callback cuando termina la optimización"""
        self.is_running_optimization = False
        self.update_running_state('optimization', False)
        self.update_status("Optimización de parámetros completada. Sistema listo para nuevas operaciones.")
        
    def monitor_progress(self):
        """Monitorear el progreso del proceso - SIMPLIFICADO"""
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
        
    def run_script_in_background(self, script_path, description, selected_file, callback_finished=None):
        """Ejecutar script en segundo plano - COMPLETAMENTE SIMPLIFICADO"""
        def run_in_thread():
            try:
                self.update_status(f"Ejecutando {description}...")
                
                # Verificar que el archivo existe
                if not os.path.exists(script_path):
                    messagebox.showerror("Error", 
                                       f"No se encuentra el archivo {script_path}\n"
                                       f"Estructura esperada:\n"
                                       f"  - Interfaz/ (carpeta actual)\n"
                                       f"  - backend/ (scripts de Python)\n"
                                       f"    - {os.path.basename(script_path)}")
                    self.update_status("Error: Archivo no encontrado")
                    if callback_finished:
                        self.root.after(100, callback_finished)
                    return
                    
                # Crear el entorno con la codificación correcta
                env = os.environ.copy()
                env['PYTHONIOENCODING'] = 'utf-8'
                
                # Cambiar al directorio backend temporalmente
                backend_dir = os.path.dirname(script_path)
                script_name = os.path.basename(script_path)
                
                # Preparar argumentos del comando
                cmd_args = [sys.executable, script_name, '--file', os.path.abspath(selected_file)]
                
                print(f"Ejecutando: {' '.join(cmd_args)} en directorio {backend_dir}")
                
                # Ejecutar proceso en segundo plano SIN interferir con la ventana
                process = subprocess.Popen(cmd_args, 
                                         env=env,
                                         cwd=backend_dir,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE,
                                         creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                
                # Esperar a que termine el proceso SIN manipular la ventana
                return_code = process.wait()
                
                if return_code == 0:
                    excel_info = ExcelManager.get_excel_info()
                    self.update_status(f"{description} completado con {excel_info['file_name']}")
                    print(f"✓ {description} ejecutado correctamente")
                        
                else:
                    self.update_status(f"Error en {description}")
                    print(f"✗ Error en {description} - Código: {return_code}")
                    
            except Exception as e:
                self.update_status("Error inesperado")
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


def main():
    """Función principal"""
    root = tk.Tk()
    app = SAIDIAnalysisGUI(root)
    
    # Iniciar aplicación
    root.mainloop()

if __name__ == "__main__":
    main()