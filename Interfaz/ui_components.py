# ui_components.py 
"""
Componentes reutilizables de la interfaz de usuario - CORREGIDO
ACTUALIZADO CON COLORES CORPORATIVOS: #9fcf67 (verde claro) y #0d9648 (verde oscuro)
"""
import tkinter as tk
from tkinter import ttk
from typing import Dict, Callable, Any
from excel_manager import ExcelManager

class UIComponents:
    """Clase para manejar componentes reutilizables de la UI"""
    
    @staticmethod
    def create_excel_load_section(parent, callback_after_load=None):
        """
        Crear la sección de carga de Excel con indicador de estado más compacta - COLORES CORPORATIVOS
        Args:
            parent: Widget padre
            callback_after_load: Función a ejecutar después de cargar el Excel
        Returns: dict con referencias a los widgets creados
        """
        # Frame principal para la sección de Excel más compacto
        excel_frame = tk.Frame(parent, bg='#f8fafc', relief='solid', bd=1)
        excel_frame.pack(fill='x', padx=15, pady=8)  # Reducido padding
        
        # Header de la sección más pequeño - COLOR CORPORATIVO SECUNDARIO
        header_frame = tk.Frame(excel_frame, bg='#0d9648', height=40)  # Reducido de 50 a 40
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        header_label = tk.Label(header_frame, 
                               text="CARGAR ARCHIVO EXCEL",
                               font=('Segoe UI', 12, 'bold'),  # Reducido de 14 a 12
                               bg='#0d9648', fg='white')
        header_label.pack(pady=8)  # Reducido padding
        
        # Contenido de la sección más compacto
        content_frame = tk.Frame(excel_frame, bg='white')
        content_frame.pack(fill='both', expand=True, padx=15, pady=10)  # Reducido padding
        
        # Información del archivo más compacta
        info_frame = tk.Frame(content_frame, bg='white')
        info_frame.pack(fill='x', pady=(0, 8))  # Reducido padding
        
        file_info_var = tk.StringVar()
        file_info_var.set("Ningún archivo seleccionado")
        
        file_info_label = tk.Label(info_frame, 
                                  textvariable=file_info_var,
                                  font=('Segoe UI', 9),  # Reducido de 10 a 9
                                  bg='white', fg='#64748b',
                                  wraplength=400)
        file_info_label.pack(side='left')
        
        # Frame para botones más compacto
        buttons_frame = tk.Frame(content_frame, bg='white')
        buttons_frame.pack(fill='x')
        
        # Botón de cargar Excel más pequeño - COLOR CORPORATIVO PRIMARIO
        load_button = tk.Button(buttons_frame, 
                               text="SELECCIONAR ARCHIVO EXCEL",
                               font=('Segoe UI', 10, 'bold'),  # Reducido de 11 a 10
                               bg='#9fcf67', fg='white',
                               relief='flat', padx=15, pady=6,  # Reducido padding
                               cursor='hand2')
        load_button.pack(side='left', padx=(0, 10))  # Reducido padding
        
        # Indicador de estado más pequeño - COLOR CORPORATIVO GRIS
        status_button = tk.Button(buttons_frame,
                                 text="EXCEL NO CARGADO",
                                 font=('Segoe UI', 9, 'bold'),  # Reducido de 10 a 9
                                 bg='#a1a1a5', fg='white',
                                 relief='flat', padx=12, pady=6,  # Reducido padding
                                 state='disabled')
        status_button.pack(side='left')
        
        # Función para manejar la carga de Excel
        def handle_excel_load():
            # Cambiar estado visual durante la carga - COLORES CORPORATIVOS
            load_button.config(state='disabled', text='CARGANDO...', bg='#a1a1a5')
            status_button.config(text='CARGANDO...', bg='#a1a1a5')
            parent.update_idletasks()
            
            # Intentar cargar el Excel
            if ExcelManager.load_excel_file(parent_window=parent.winfo_toplevel()):
                # Excel cargado exitosamente
                excel_info = ExcelManager.get_excel_info()
                file_name = excel_info['file_name']
                
                # Actualizar información del archivo - COLOR CORPORATIVO PARA ÉXITO
                file_info_text = (f"✓ Archivo: {file_name}\n"
                                f"✓ Dimensiones: {excel_info['rows']} filas x {excel_info['columns']} columnas")
                file_info_var.set(file_info_text)
                file_info_label.config(fg='#0d9648')
                
                # Actualizar estados de botones - COLORES CORPORATIVOS
                load_button.config(text='CAMBIAR ARCHIVO', bg='#a1a1a5', state='normal')
                status_button.config(text='EXCEL CARGADO', bg='#9fcf67')
                
                # Ejecutar callback si existe
                if callback_after_load:
                    callback_after_load()
                    
                print(f"✓ Excel cargado: {file_name}")
                
            else:
                # Error al cargar - COLOR ROJO ARMONIOSO
                load_button.config(state='normal', text='SELECCIONAR ARCHIVO EXCEL', bg='#9fcf67')
                status_button.config(text='ERROR DE CARGA', bg='#dc2626')
                
        # Función para verificar estado inicial
        def check_initial_state():
            if ExcelManager.is_excel_loaded():
                # Ya hay un Excel cargado
                excel_info = ExcelManager.get_excel_info()
                file_name = excel_info['file_name']
                
                file_info_text = (f"✓ Archivo: {file_name}\n"
                                f"✓ Dimensiones: {excel_info['rows']} filas x {excel_info['columns']} columnas")
                file_info_var.set(file_info_text)
                file_info_label.config(fg='#0d9648')
                
                load_button.config(text='CAMBIAR ARCHIVO', bg='#a1a1a5')
                status_button.config(text='EXCEL CARGADO', bg='#9fcf67')
                
                if callback_after_load:
                    callback_after_load()
        
        # Configurar comando del botón
        load_button.config(command=handle_excel_load)
        
        # Efectos hover - COLORES CORPORATIVOS
        UIComponents.add_hover_effects(load_button, '#0d9648', None)  # Se determinará dinámicamente
        
        # Verificar estado inicial
        check_initial_state()
        
        return {
            'excel_frame': excel_frame,
            'load_button': load_button,
            'status_button': status_button,
            'file_info_var': file_info_var,
            'file_info_label': file_info_label
        }
    
    @staticmethod
    def create_analysis_modules(parent, module_callbacks: Dict[str, Callable]):
        """
        Crear los módulos de análisis con cards uniformes y más compactas - COLORES CORPORATIVOS
        Args:
            parent: Widget padre
            module_callbacks: Dict con callbacks para cada módulo
        Returns: dict con referencias a los botones de módulos
        """
        modules_frame = tk.Frame(parent, bg='#f8fafc')
        modules_frame.pack(fill='both', expand=True, pady=10)  # Reducido significativamente
        
        # Configurar grid para 3 columnas uniformes
        for i in range(3):
            modules_frame.columnconfigure(i, weight=1, uniform="modules")  # uniform asegura mismo ancho
        modules_frame.rowconfigure(0, weight=1)
        
        module_buttons = {}
        
        # Configuraciones de módulos - COLORES CORPORATIVOS
        modules_config = [
            {
                'key': 'prediction',
                'icon': '📊',
                'title': 'Predicción SAIDI',
                'description': 'Genera predicciones para períodos faltantes utilizando modelos SARIMAX optimizados.',
                'color': '#9fcf67',  # Verde claro corporativo
                'button_text': 'INICIAR PREDICCIÓN',
                'callback': module_callbacks.get('prediction')
            },
            {
                'key': 'behavior',
                'icon': '📈', 
                'title': 'Comportamiento del Modelo',
                'description': 'Visualiza la precisión del modelo mediante gráficas comparativas.',
                'color': '#0d9648',  # Verde oscuro corporativo
                'button_text': 'ANÁLISIS DE PRECISIÓN',
                'callback': module_callbacks.get('behavior')
            },
            {
                'key': 'optimization',
                'icon': '⚙️',
                'title': 'Optimización de Parámetros', 
                'description': 'Búsqueda exhaustiva de parámetros óptimos mediante algoritmos ARIMA.',
                'color': '#7bb15a',  # Verde medio armonioso con la paleta
                'button_text': 'OPTIMIZAR PARÁMETROS',
                'callback': module_callbacks.get('optimization')
            }
        ]
        
        for i, config in enumerate(modules_config):
            button = UIComponents._create_module_card(
                modules_frame, 0, i, config
            )
            module_buttons[config['key']] = button
        
        # CRÍTICO: Actualizar estado inmediatamente después de crear botones
        print(f"DEBUG: Botones creados: {list(module_buttons.keys())}")
        UIComponents.update_module_buttons_state(module_buttons)
        print(f"DEBUG: Estados actualizados")
        
        return module_buttons
    
    @staticmethod
    def _create_module_card(parent, row, col, config):
        """Crear una card de módulo individual con tamaño uniforme y más compacta - COLORES CORPORATIVOS"""
        # Frame principal de la card con altura fija para uniformidad
        card_frame = tk.Frame(parent, bg='white', relief='solid', bd=1, 
                             height=280, width=300)  # Altura fija reducida de ~350 a 280
        card_frame.grid(row=row, column=col, padx=8, pady=5, sticky='nsew')  # Reducido padding
        card_frame.grid_propagate(False)  # IMPORTANTE: Evita que se redimensione
        card_frame.pack_propagate(False)  # IMPORTANTE: Mantiene tamaño fijo
        
        # Header con ícono más compacto - COLOR CORPORATIVO
        header_frame = tk.Frame(card_frame, bg=config['color'], height=45)  # Reducido de 60 a 45
        header_frame.pack(fill='x', pady=(0, 8))  # Reducido padding
        header_frame.pack_propagate(False)
        
        icon_label = tk.Label(header_frame, text=config['icon'], 
                             font=('Segoe UI', 18),  # Reducido de 24 a 18
                             bg=config['color'], fg='white')
        icon_label.pack(pady=8)  # Reducido padding
        
        # Contenido más compacto con altura controlada
        content_frame = tk.Frame(card_frame, bg='white', height=220)  # Altura fija para contenido
        content_frame.pack(fill='x', padx=12, pady=(0, 10))  # Reducido padding
        content_frame.pack_propagate(False)
        
        # Título más pequeño
        title_label = tk.Label(content_frame, text=config['title'],
                              font=('Segoe UI', 11, 'bold'),  # Reducido de 14 a 11
                              bg='white', fg='#1f2937')
        title_label.pack(pady=(5, 6))  # Reducido padding
        
        # Descripción más compacta con altura fija
        desc_frame = tk.Frame(content_frame, bg='white', height=80)  # Altura fija para descripción
        desc_frame.pack(fill='x', pady=(0, 8))
        desc_frame.pack_propagate(False)
        
        desc_label = tk.Label(desc_frame, text=config['description'],
                             font=('Segoe UI', 8), bg='white', fg='#6b7280',  # Reducido de 10 a 8
                             wraplength=180, justify='center')
        desc_label.pack(pady=5)
        
        # CORRECCIÓN CRÍTICA: Determinar estado inicial basado en Excel
        excel_loaded = ExcelManager.is_excel_loaded()
        initial_state = 'normal' if excel_loaded else 'disabled'
        initial_bg = config['color'] if excel_loaded else '#a1a1a5'  # Color corporativo gris para deshabilitado
        
        # Botón más compacto - CORREGIDO con estado inicial apropiado
        button = tk.Button(content_frame, text=config['button_text'],
                          font=('Segoe UI', 8, 'bold'),  # Reducido de 10 a 8
                          bg=initial_bg, fg='white', relief='flat',
                          padx=10, pady=6, cursor='hand2',  # Reducido padding
                          state=initial_state,
                          command=config['callback'] if excel_loaded else None)  # COMANDO ASIGNADO
        button.pack(pady=(10, 5))  # Posicionado cerca del final
        
        # CORRECCIÓN: Almacenar propiedades originales correctamente
        button.original_color = config['color']
        button.original_command = config['callback']
        button.original_text = config['button_text']
        
        # CORRECCIÓN: Configurar hover effects si está habilitado - COLORES CORPORATIVOS
        if excel_loaded:
            UIComponents.add_hover_effects(
                button, 
                UIComponents.darken_color(config['color']),
                config['color']
            )
        
        print(f"DEBUG: Botón {config['key']} creado con estado: {initial_state}, color: {initial_bg}")
        
        return button
    
    @staticmethod
    def update_module_buttons_state(module_buttons: Dict[str, tk.Button]):
        """
        Actualizar el estado de los botones de módulo basado en si hay Excel cargado - CORREGIDO
        """
        excel_loaded = ExcelManager.is_excel_loaded()
        print(f"DEBUG: Actualizando estado de botones - Excel loaded: {excel_loaded}")
        
        buttons_updated = 0
        for key, button in module_buttons.items():
            try:
                if not button or not button.winfo_exists():
                    print(f"DEBUG: Botón {key} no existe")
                    continue
                    
                if excel_loaded:
                    # CORRECCIÓN CRÍTICA: Habilitar botón con 'normal' en lugar de '0'
                    button.config(
                        state='normal',  # CORREGIDO: usar 'normal' en lugar de '0'
                        bg=button.original_color,
                        command=button.original_command,
                        cursor='hand2'
                    )
                    # Restaurar efectos hover - COLORES CORPORATIVOS
                    UIComponents.add_hover_effects(
                        button, 
                        UIComponents.darken_color(button.original_color),
                        button.original_color
                    )
                    print(f"DEBUG: Botón {key} habilitado - color: {button.original_color}")
                else:
                    # Deshabilitar botón - COLOR CORPORATIVO GRIS
                    button.config(
                        state='disabled',
                        bg='#a1a1a5',  # Color corporativo gris
                        command=None,
                        cursor='arrow'
                    )
                    # Remover efectos hover
                    button.unbind("<Enter>")
                    button.unbind("<Leave>")
                    print(f"DEBUG: Botón {key} deshabilitado")
                    
                buttons_updated += 1
                
            except Exception as e:
                print(f"ERROR: Actualizando botón {key}: {e}")
        
        print(f"DEBUG: {buttons_updated} botones procesados de {len(module_buttons)}")
        return buttons_updated == len(module_buttons)
    
    @staticmethod
    def add_hover_effects(button, hover_color, normal_color):
        """Agregar efectos hover a los botones - MEJORADO"""
        # Primero limpiar eventos existentes
        button.unbind("<Enter>")
        button.unbind("<Leave>")
        
        def on_enter(e):
            if button['state'] == 'normal':  # Solo aplicar hover si está habilitado
                current_color = normal_color if normal_color else button.original_color
                hover = hover_color if hover_color else UIComponents.darken_color(current_color)
                button.configure(bg=hover)
                
        def on_leave(e):
            if button['state'] == 'normal':
                current_color = normal_color if normal_color else button.original_color
                button.configure(bg=current_color)
                
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
    
    @staticmethod
    def darken_color(hex_color):
        """Oscurecer un color hexadecimal para efectos hover - COLORES CORPORATIVOS"""
        color_map = {
            '#9fcf67': '#0d9648',  # Verde claro -> verde oscuro corporativo
            '#0d9648': '#0a7a3a',  # Verde oscuro -> más oscuro
            '#7bb15a': '#5e8e45',  # Verde medio -> más oscuro
            '#a1a1a5': '#8a8a8e'   # Gris -> más oscuro
        }
        return color_map.get(hex_color, hex_color)