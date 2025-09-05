# main_interface_ui.py - Componentes de interfaz separados de la lógica
"""
Componentes de interfaz de usuario para la ventana principal
Separado de la lógica de negocio para mejor organización
"""
import tkinter as tk
from tkinter import ttk
import os
import pandas as pd
from excel_manager import ExcelManager
from ui_components import UIComponents


class MainInterfaceUI:
    """Clase para manejar todos los componentes visuales de la interfaz principal"""
    
    def __init__(self, root, callbacks):
        """
        Inicializar componentes de UI
        Args:
            root: Ventana principal de tkinter
            callbacks: Dict con funciones callback para eventos
        """
        self.root = root
        self.callbacks = callbacks
        self.style = None
        self.status_var = None
        self.excel_components = {}
        self.module_buttons = {}
        
    def setup_main_window(self):
        """Configuración principal de la ventana"""
        self.root.title("SAIDI Analysis Pro - Sistema de Análisis Predictivo")
        
        # Pantalla completa
        self.root.state('zoomed')  # Windows
        # Para Linux/Mac usar: self.root.attributes('-zoomed', True)
        
        self.root.configure(bg='#f8fafc')
        
        # Evitar que la ventana se cierre accidentalmente
        self.root.protocol("WM_DELETE_WINDOW", self.callbacks['on_window_close'])
        
        # Configurar estilo
        self.setup_styles()
        
    def setup_styles(self):
        """Configurar estilos personalizados"""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
    def create_main_interface(self):
        """Crear la interfaz principal completa"""
        # Frame principal con padding optimizado
        main_frame = tk.Frame(self.root, bg='#f8fafc')
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Header más compacto
        self.create_header(main_frame)
        
        # Sección de carga de Excel
        self.create_excel_load_section(main_frame)
        
        # Contenedor de módulos
        self.module_buttons = UIComponents.create_analysis_modules(
            main_frame,
            module_callbacks={
                'prediction': self.callbacks['run_prediction'],
                'behavior': self.callbacks['run_behavior_analysis'],
                'optimization': self.callbacks['run_parameter_optimization']
            }
        )
        
        # Footer
        self.create_footer(main_frame)
        
        # Estado inicial de botones
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
                              text="SAIDI Analysis",
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
        """Crear el footer más compacto"""
        footer_frame = tk.Frame(parent, bg='#f8fafc')
        footer_frame.pack(fill='x', side='bottom', pady=(5, 0))
        
        # Línea separadora más delgada
        separator = tk.Frame(footer_frame, bg='#d1d5db', height=1)
        separator.pack(fill='x', pady=(0, 5))
        
        # Información del footer más compacta
        footer_label = tk.Label(footer_frame,
                               text="© 2025 SAIDI Analysis | Sistema de Análisis Predictivo de Calidad del Servicio Eléctrico",
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
        """Crear sección de carga de Excel"""
        # Frame principal para la sección Excel
        excel_frame = tk.LabelFrame(parent, text="Carga de Datos Excel", 
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
                                     text="SELECCIONAR ARCHIVO EXCEL",
                                     command=self.callbacks['select_excel_file'],
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
                text=f" {file_name}",
                fg='#059669'  # Verde para éxito
            )
            
            self.file_details_label.config(
                text=details_text,
                fg='#374151'  # Gris oscuro para detalles
            )
            
            # Cambiar texto del botón
            self.excel_button.config(text="CAMBIAR ARCHIVO EXCEL")
            
        except Exception as e:
            print(f"ERROR en update_excel_info_display: {e}")
            # Fallback básico
            file_name = os.path.basename(file_path)
            self.file_info_label.config(text=f"{file_name}", fg='#059669')
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
        """Actualizar el status bar"""
        if self.status_var:
            self.status_var.set(message)
            self.root.update_idletasks()
        
    def update_modules_state(self):
        """Actualizar el estado de los módulos basado en si hay Excel cargado"""
        excel_loaded = ExcelManager.is_excel_loaded()
        print(f"DEBUG UI: update_modules_state - Excel loaded: {excel_loaded}")
        
        if not excel_loaded:
            print("DEBUG UI: No hay Excel cargado, botones permanecen deshabilitados")
            return
            
        # Actualizar botones usando UIComponents
        success = UIComponents.update_module_buttons_state(self.module_buttons)
        
        if success:
            print("DEBUG UI: ✓ Botones de módulos actualizados exitosamente")
        else:
            print("DEBUG UI: ✗ Error al actualizar botones de módulos")

    def update_running_state(self, module_key, is_running):
        """Actualizar el estado visual del módulo cuando está ejecutándose"""
        if module_key in self.module_buttons:
            button = self.module_buttons[module_key]
            if is_running:
                # Cambiar apariencia cuando está ejecutándose
                button.config(
                    text="EJECUTANDO...",
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

    def get_excel_components(self):
        """Obtener referencias a componentes de Excel"""
        return self.excel_components
    
    def get_module_buttons(self):
        """Obtener referencias a botones de módulos"""
        return self.module_buttons