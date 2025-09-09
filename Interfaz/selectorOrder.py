# selectorOrder.py
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
import sys
import time 

# IMPORTAR EL BRIDGE DE COMUNICACIÓN
BRIDGE_AVAILABLE = False
get_updated_presets = None
clear_bridge_data = None

# CONFIGURAR RUTA PARA IMPORTAR DESDE BACKEND
BRIDGE_AVAILABLE = False
get_updated_presets = None
clear_bridge_data = None

def setup_bridge_import():
    """Configurar importación del bridge desde backend"""
    global BRIDGE_AVAILABLE, get_updated_presets, clear_bridge_data
    
    print("DEBUG: Configurando bridge para estructura Interfaz/backend...")
    
    # Obtener directorio actual (Interfaz)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"DEBUG: Directorio actual (Interfaz): {current_dir}")
    
    # Directorio padre (raíz del proyecto)
    parent_dir = os.path.dirname(current_dir)
    print(f"DEBUG: Directorio padre: {parent_dir}")
    
    # Directorio backend
    backend_dir = os.path.join(parent_dir, 'backend')
    print(f"DEBUG: Directorio backend: {backend_dir}")
    
    # Verificar que existe parametros_bridge.py en backend
    bridge_file = os.path.join(backend_dir, 'parametros_bridge.py')
    print(f"DEBUG: Buscando bridge en: {bridge_file}")
    
    if os.path.exists(bridge_file):
        print("DEBUG: Archivo bridge encontrado")
        
        # Agregar backend al path
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)
            print(f"DEBUG: Backend agregado al sys.path: {backend_dir}")
        
        try:
            # Importar desde backend
            import parametros_bridge # type: ignore
            get_updated_presets = parametros_bridge.get_updated_presets
            clear_bridge_data = parametros_bridge.clear_bridge_data
            
            BRIDGE_AVAILABLE = True
            print("Bridge de parámetros cargado desde backend")
            
            # Probar funciones
            try:
                presets = get_updated_presets()
                if presets:
                    print(f"Presets dinámicos disponibles: {len(presets)}")
                    for preset_name, preset_data in presets.items():
                        model = preset_data['model']
                        precision = model.get('precision_final', 0)
                        print(f"  - {preset_name}: Precisión {precision:.1f}%")
                else:
                    print("No hay presets optimizados disponibles (ejecute primero el optimizador)")
                return True
                
            except Exception as func_error:
                print(f"Error probando funciones bridge: {func_error}")
                return True  # Bridge disponible pero sin datos
                
        except ImportError as import_error:
            print(f"Error importando bridge: {import_error}")
            return False
            
    else:
        print("No se encontró parametros_bridge.py en backend")
        return False

# Ejecutar configuración del bridge
setup_bridge_import()


# Variables globales para almacenar los parámetros seleccionados
SELECTED_ORDER = (4, 0, 0)  # Valores por defecto
SELECTED_SEASONAL_ORDER = (1, 0, 0, 8)  # Valores por defecto
PARAMETERS_CONFIRMED = False
CURRENT_WINDOW = None

# RESTO DEL CÓDIGO DE LA CLASE PERMANECE IGUAL
class ParameterSelectorWindow:
    def __init__(self, parent, callback_function, module_name):
        self.parent = parent
        self.callback_function = callback_function
        self.module_name = module_name
        self.window = None
        self.confirmed = False
        
        # Variables para los parámetros
        self.order_vars = {'p': tk.IntVar(), 'd': tk.IntVar(), 'q': tk.IntVar()}
        self.seasonal_vars = {'P': tk.IntVar(), 'D': tk.IntVar(), 'Q': tk.IntVar(), 's': tk.IntVar()}
        
        # NUEVA VARIABLE PARA PRESETS DINÁMICOS
        self.dynamic_presets = None
        self.presets_loaded = False
        
        # Cargar valores por defecto
        self.load_default_values()
        
        # CARGAR PRESETS ACTUALIZADOS DEL BRIDGE
        self.load_bridge_presets()
        
        self.create_window()
        
    def load_default_values(self):
        """Cargar valores por defecto basados en los parámetros actuales globales"""
        global SELECTED_ORDER, SELECTED_SEASONAL_ORDER
        
        self.order_vars['p'].set(SELECTED_ORDER[0])
        self.order_vars['d'].set(SELECTED_ORDER[1])
        self.order_vars['q'].set(SELECTED_ORDER[2])
        
        self.seasonal_vars['P'].set(SELECTED_SEASONAL_ORDER[0])
        self.seasonal_vars['D'].set(SELECTED_SEASONAL_ORDER[1])
        self.seasonal_vars['Q'].set(SELECTED_SEASONAL_ORDER[2])
        self.seasonal_vars['s'].set(SELECTED_SEASONAL_ORDER[3])
        
    def load_bridge_presets(self):
        """FUNCIÓN MEJORADA: Cargar presets desde el bridge"""
        if not BRIDGE_AVAILABLE or get_updated_presets is None:
            print("DEBUG: Bridge no disponible para cargar presets")
            return
            
        try:
            print("DEBUG: Cargando presets desde bridge...")
            updated_presets = get_updated_presets()
            if updated_presets:
                self.dynamic_presets = updated_presets
                self.presets_loaded = True
                print("Presets dinámicos cargados exitosamente:")
                for preset_name, preset_data in updated_presets.items():
                    model = preset_data['model']
                    precision = model.get('precision_final', 0)
                    order = model.get('order')
                    print(f"  - {preset_name}: order={order}, precisión={precision:.1f}%")
            else:
                print("DEBUG: get_updated_presets() retornó None - no hay datos optimizados")
                
        except Exception as e:
            print(f"ERROR: Cargando presets del bridge: {e}")
            import traceback
            traceback.print_exc()


class ParameterSelectorWindow:
    def __init__(self, parent, callback_function, module_name):
        self.parent = parent
        self.callback_function = callback_function
        self.module_name = module_name
        self.window = None
        self.confirmed = False
        
        # Variables para los parámetros
        self.order_vars = {'p': tk.IntVar(), 'd': tk.IntVar(), 'q': tk.IntVar()}
        self.seasonal_vars = {'P': tk.IntVar(), 'D': tk.IntVar(), 'Q': tk.IntVar(), 's': tk.IntVar()}
        
        # NUEVA VARIABLE PARA PRESETS DINÁMICOS
        self.dynamic_presets = None
        self.presets_loaded = False
        
        # Cargar valores por defecto
        self.load_default_values()
        
        # CARGAR PRESETS ACTUALIZADOS DEL BRIDGE
        self.load_bridge_presets()
        
        self.create_window()
        
    def load_default_values(self):
        """Cargar valores por defecto basados en los parámetros actuales globales"""
        global SELECTED_ORDER, SELECTED_SEASONAL_ORDER
        
        self.order_vars['p'].set(SELECTED_ORDER[0])
        self.order_vars['d'].set(SELECTED_ORDER[1])
        self.order_vars['q'].set(SELECTED_ORDER[2])
        
        self.seasonal_vars['P'].set(SELECTED_SEASONAL_ORDER[0])
        self.seasonal_vars['D'].set(SELECTED_SEASONAL_ORDER[1])
        self.seasonal_vars['Q'].set(SELECTED_SEASONAL_ORDER[2])
        self.seasonal_vars['s'].set(SELECTED_SEASONAL_ORDER[3])
        
    def load_bridge_presets(self):
        """NUEVA FUNCIÓN: Cargar presets desde el bridge"""
        if not BRIDGE_AVAILABLE:
            print("Bridge no disponible, usando presets por defecto")
            return
            
        try:
            updated_presets = get_updated_presets()
            if updated_presets:
                self.dynamic_presets = updated_presets
                self.presets_loaded = True
                print("Presets dinámicos cargados desde bridge:")
                for preset_name, preset_data in updated_presets.items():
                    model = preset_data['model']
                    print(f"  - {preset_name}: order={model['order']}, seasonal_order={model['seasonal_order']}")
            else:
                print("No se encontraron presets actualizados en bridge")
                
        except Exception as e:
            print(f"Error cargando presets del bridge: {e}")
        
    def create_window(self):
        """Crear la ventana de selección de parámetros - DISEÑO ORIGINAL OPTIMIZADO"""
        global CURRENT_WINDOW
        
        # Si ya hay una ventana abierta, enfocarla
        if CURRENT_WINDOW and CURRENT_WINDOW.winfo_exists():
            CURRENT_WINDOW.lift()
            CURRENT_WINDOW.focus_force()
            return
            
        # Crear nueva ventana
        self.window = tk.Toplevel(self.parent)
        CURRENT_WINDOW = self.window
        
        # Configuración de la ventana - TAMAÑO AJUSTADO PARA MOSTRAR STATUS
        window_height = 680 if self.presets_loaded else 620
        self.window.title(f"Configurar Parámetros SARIMAX - {self.module_name}")
        self.window.geometry(f"650x{window_height}")
        self.window.resizable(True, True)
        self.window.configure(bg='#f8fafc')
        
        # Hacer que la ventana sea modal
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Centrar la ventana
        self.center_window(window_height)
        
        # Configurar el cierre de la ventana
        self.window.protocol("WM_DELETE_WINDOW", self.on_cancel)
        
        # Crear contenido con SCROLL para seguridad
        self.create_content_with_scroll()
        
        # Enfocar la ventana
        self.window.focus_force()
        
    def center_window(self, height):
        """Centrar la ventana en la pantalla"""
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (650 // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"650x{height}+{x}+{y}")
        
    def create_content_with_scroll(self):
        """Crear contenido con scroll como respaldo para pantallas muy pequeñas"""
        # Frame principal con scroll
        canvas = tk.Canvas(self.window, bg='#f8fafc')
        scrollbar = ttk.Scrollbar(self.window, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#f8fafc')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Scroll con rueda del mouse
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Empaquetar canvas y scrollbar
        canvas.pack(side="left", fill="both", expand=True, padx=(20, 0), pady=20)
        scrollbar.pack(side="right", fill="y", padx=(0, 20), pady=20)
        
        # Crear el contenido original pero con espaciado optimizado
        self.create_optimized_content(scrollable_frame)
        
    def create_optimized_content(self, parent):
        """Crear el contenido original con espaciado optimizado y bridge status"""
        # Título principal - ESPACIADO REDUCIDO
        title_label = tk.Label(parent, 
                              text=f"Configuración de Parámetros SARIMAX",
                              font=('Segoe UI', 16, 'bold'),
                              bg='#f8fafc', fg='#1e40af')
        title_label.pack(pady=(0, 3))
        
        # Subtítulo con el módulo - ESPACIADO REDUCIDO
        subtitle_label = tk.Label(parent,
                                 text=f"Módulo: {self.module_name}",
                                 font=('Segoe UI', 12),
                                 bg='#f8fafc', fg='#6b7280')
        subtitle_label.pack(pady=(0, 5))
        
        # NUEVA SECCIÓN: STATUS DEL BRIDGE
        if BRIDGE_AVAILABLE:
            self.create_bridge_status_section(parent)
        
        # Sección de información - ESPACIADO REDUCIDO
        self.create_info_section(parent)
        
        # Sección de parámetros no estacionales - ESPACIADO REDUCIDO
        self.create_order_section(parent)
        
        # Sección de parámetros estacionales - ESPACIADO REDUCIDO
        self.create_seasonal_section(parent)
        
        # Sección de presets - ESPACIADO REDUCIDO CON PRESETS DINÁMICOS
        self.create_presets_section(parent)
        
        # Sección de validación - ESPACIADO REDUCIDO
        self.create_validation_section(parent)
        
        # Botones de acción - ESPACIADO REDUCIDO
        self.create_action_buttons(parent)
        
    def create_bridge_status_section(self, parent):
        """NUEVA FUNCIÓN: Mostrar status del bridge"""
        if not BRIDGE_AVAILABLE:
            return
            
        status_frame = tk.LabelFrame(parent, text="🔗 Estado de la Conexión con Optimizador", 
                                    font=('Segoe UI', 11, 'bold'),
                                    bg='#f8fafc', fg='#7c3aed',
                                    relief='ridge', bd=2)
        status_frame.pack(fill='x', pady=(0, 10))
        
        # Contenido del status
        status_content = tk.Frame(status_frame, bg='#f8fafc')
        status_content.pack(fill='x', padx=15, pady=8)
        
        if self.presets_loaded:
            # Bridge funcionando correctamente
            status_icon = "Funcionando"
            status_text = "Conectado - Presets actualizados con resultados de optimización"
            status_color = '#10b981'
            bg_color = '#ecfdf5'
            
            # Mostrar información adicional
            info_text = ("Los presets 'Conservador', 'Solo Tendencia' y 'Agresivo' han sido actualizados "
                        "automáticamente con los mejores parámetros encontrados por el optimizador.")
        else:
            # Bridge no tiene datos
            status_icon = "Advertencia"
            status_text = "Desconectado - Usando presets predeterminados"
            status_color = '#f59e0b'
            bg_color = '#fffbeb'
            
            info_text = ("No se detectaron parámetros optimizados. Para obtener presets personalizados, "
                        "ejecute primero el optimizador de parámetros.")
        
        # Label principal del status
        status_label = tk.Label(status_content,
                               text=f"{status_icon} {status_text}",
                               font=('Segoe UI', 10, 'bold'),
                               bg=bg_color, fg=status_color,
                               relief='solid', bd=1,
                               padx=10, pady=6)
        status_label.pack(fill='x')
        
        # Información adicional
        info_label = tk.Label(status_content,
                             text=info_text,
                             font=('Segoe UI', 9),
                             bg='#f8fafc', fg='#6b7280',
                             wraplength=550, justify='left')
        info_label.pack(pady=(5, 0))
        
        # Botón para limpiar bridge si hay datos
        if self.presets_loaded:
            clear_button = tk.Button(status_content,
                                   text="Limpiar y usar presets originales",
                                   font=('Segoe UI', 8),
                                   bg='#ef4444', fg='white',
                                   relief='flat', cursor='hand2',
                                   command=self.clear_bridge_and_reload)
            clear_button.pack(pady=(5, 0))
        
    def clear_bridge_and_reload(self):
        """Limpiar bridge y recargar presets originales"""
        if messagebox.askyesno("Confirmar Limpieza", 
                              "¿Desea limpiar los presets optimizados y volver a los originales?\n"
                              "Esta acción no se puede deshacer."):
            try:
                if BRIDGE_AVAILABLE:
                    clear_bridge_data()
                
                # Recargar ventana
                self.window.destroy()
                self.__init__(self.parent, self.callback_function, self.module_name)
                
                messagebox.showinfo("Limpieza Completada", 
                                   "Los presets han sido restaurados a los valores originales.")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error limpiando bridge: {e}")
        
    def create_info_section(self, parent):
        """Crear sección de información sobre SARIMAX - VERSIÓN COMPACTA"""
        info_frame = tk.LabelFrame(parent, text="ℹInformación sobre Parámetros SARIMAX", 
                                  font=('Segoe UI', 11, 'bold'),
                                  bg='#f8fafc', fg='#1e40af',
                                  relief='ridge', bd=2)
        info_frame.pack(fill='x', pady=(0, 10))
        
        info_text = tk.Text(info_frame, height=3, wrap='word', font=('Segoe UI', 9),
                           bg='#ffffff', fg='#374151', relief='flat', bd=5)
        info_text.pack(fill='x', padx=10, pady=8)
        
        info_content = """SARIMAX(p,d,q)x(P,D,Q,s):
• p, P: Componentes autoregresivos (AR) - Valores típicos: 0-5
• d, D: Diferenciación para estacionariedad - Valores típicos: 0-2  
• q, Q: Componentes de media móvil (MA) - Valores típicos: 0-5 • s: Periodicidad estacional"""
        
        info_text.insert('1.0', info_content)
        info_text.config(state='disabled')
        
    def create_order_section(self, parent):
        """Crear sección de parámetros no estacionales - ESPACIADO OPTIMIZADO"""
        order_frame = tk.LabelFrame(parent, text="Parámetros No Estacionales - order(p,d,q)", 
                                   font=('Segoe UI', 11, 'bold'),
                                   bg='#f8fafc', fg='#059669',
                                   relief='ridge', bd=2)
        order_frame.pack(fill='x', pady=(0, 10))
        
        # Grid para los parámetros - ESPACIADO REDUCIDO
        params_frame = tk.Frame(order_frame, bg='#f8fafc')
        params_frame.pack(fill='x', padx=15, pady=10)
        
        # Configurar grid
        for i in range(4):
            params_frame.grid_columnconfigure(i, weight=1)
        
        # Headers
        headers = ['Parámetro', 'p (AR)', 'd (Diferenciación)', 'q (MA)']
        for i, header in enumerate(headers):
            label = tk.Label(params_frame, text=header, font=('Segoe UI', 10, 'bold'),
                           bg='#f8fafc', fg='#374151')
            label.grid(row=0, column=i, pady=(0, 6), padx=5)
        
        # Descripción
        tk.Label(params_frame, text="Descripción:", font=('Segoe UI', 9),
                bg='#f8fafc', fg='#6b7280').grid(row=1, column=0, sticky='w', padx=5)
        
        descriptions = ['Orden autoregresivo', 'Grado de diferenciación', 'Orden media móvil']
        for i, desc in enumerate(descriptions):
            tk.Label(params_frame, text=desc, font=('Segoe UI', 8),
                    bg='#f8fafc', fg='#6b7280', wraplength=100).grid(row=1, column=i+1, padx=5)
        
        # Controles - AGREGAMOS CALLBACK PARA ACTUALIZACIÓN AUTOMÁTICA
        tk.Label(params_frame, text="Valor:", font=('Segoe UI', 9, 'bold'),
                bg='#f8fafc', fg='#374151').grid(row=2, column=0, pady=(6, 0), padx=5)
        
        param_names = ['p', 'd', 'q']
        for i, param in enumerate(param_names):
            spinbox = tk.Spinbox(params_frame, from_=0, to=10, width=8,
                               textvariable=self.order_vars[param],
                               font=('Segoe UI', 10), justify='center',
                               bg='white', relief='solid', bd=1,
                               command=self.update_preview)
            spinbox.grid(row=2, column=i+1, pady=(6, 0), padx=5)
            # También actualizar cuando se cambie manualmente el valor
            self.order_vars[param].trace('w', lambda *args: self.update_preview())
            
    def create_seasonal_section(self, parent):
        """Crear sección de parámetros estacionales - ESPACIADO OPTIMIZADO"""
        seasonal_frame = tk.LabelFrame(parent, text="Parámetros Estacionales - seasonal_order(P,D,Q,s)", 
                                      font=('Segoe UI', 11, 'bold'),
                                      bg='#f8fafc', fg='#dc2626',
                                      relief='ridge', bd=2)
        seasonal_frame.pack(fill='x', pady=(0, 10))
        
        # Grid para los parámetros estacionales - ESPACIADO REDUCIDO
        seasonal_params_frame = tk.Frame(seasonal_frame, bg='#f8fafc')
        seasonal_params_frame.pack(fill='x', padx=15, pady=10)
        
        # Configurar grid
        for i in range(5):
            seasonal_params_frame.grid_columnconfigure(i, weight=1)
        
        # Headers
        headers = ['Parámetro', 'P (AR Est.)', 'D (Dif. Est.)', 'Q (MA Est.)', 's (Período)']
        for i, header in enumerate(headers):
            label = tk.Label(seasonal_params_frame, text=header, font=('Segoe UI', 10, 'bold'),
                           bg='#f8fafc', fg='#374151')
            label.grid(row=0, column=i, pady=(0, 6), padx=5)
        
        # Descripción
        tk.Label(seasonal_params_frame, text="Descripción:", font=('Segoe UI', 9),
                bg='#f8fafc', fg='#6b7280').grid(row=1, column=0, sticky='w', padx=5)
        
        seasonal_descriptions = ['AR estacional', 'Diferenciación estacional', 'MA estacional', 'Periodicidad']
        for i, desc in enumerate(seasonal_descriptions):
            tk.Label(seasonal_params_frame, text=desc, font=('Segoe UI', 8),
                    bg='#f8fafc', fg='#6b7280', wraplength=80).grid(row=1, column=i+1, padx=5)
        
        # Controles - AGREGAMOS CALLBACK PARA ACTUALIZACIÓN AUTOMÁTICA
        tk.Label(seasonal_params_frame, text="Valor:", font=('Segoe UI', 9, 'bold'),
                bg='#f8fafc', fg='#374151').grid(row=2, column=0, pady=(6, 0), padx=5)
        
        param_names = ['P', 'D', 'Q']
        max_values = [5, 2, 5]
        for i, (param, max_val) in enumerate(zip(param_names, max_values)):
            spinbox = tk.Spinbox(seasonal_params_frame, from_=0, to=max_val, width=8,
                               textvariable=self.seasonal_vars[param],
                               font=('Segoe UI', 10), justify='center',
                               bg='white', relief='solid', bd=1,
                               command=self.update_preview)
            spinbox.grid(row=2, column=i+1, pady=(6, 0), padx=5)
            # También actualizar cuando se cambie manualmente el valor
            self.seasonal_vars[param].trace('w', lambda *args: self.update_preview())
        
        # Spinbox especial para 's' (periodicidad) - CON CALLBACK
        s_spinbox = tk.Spinbox(seasonal_params_frame, from_=1, to=24, width=8,
                              textvariable=self.seasonal_vars['s'],
                              font=('Segoe UI', 10), justify='center',
                              bg='white', relief='solid', bd=1,
                              command=self.update_preview)
        s_spinbox.grid(row=2, column=4, pady=(6, 0), padx=5)
        # También actualizar cuando se cambie manualmente el valor
        self.seasonal_vars['s'].trace('w', lambda *args: self.update_preview())
        
    def create_presets_section(self, parent):
        """Crear sección de configuraciones predefinidas - CON PRESETS DINÁMICOS"""
        presets_frame = tk.LabelFrame(parent, text="Configuraciones Predefinidas", 
                                     font=('Segoe UI', 11, 'bold'),
                                     bg='#f8fafc', fg='#7c3aed',
                                     relief='ridge', bd=2)
        presets_frame.pack(fill='x', pady=(0, 10))
        
        # Frame para los botones de preset - ESPACIADO REDUCIDO
        buttons_frame = tk.Frame(presets_frame, bg='#f8fafc')
        buttons_frame.pack(fill='x', padx=15, pady=10)
        
        # DEFINIR PRESETS (DINÁMICOS O ESTÁTICOS)
        if self.presets_loaded and self.dynamic_presets:
            # Usar presets dinámicos del bridge
            presets = self.get_dynamic_presets()
        else:
            # Usar presets estáticos originales
            presets = [
                ("Optimizado (Actual)", (4, 0, 0), (1, 0, 0, 8), "Parámetros optimizados"),
                ("Conservador", (1, 1, 1), (1, 1, 1, 12), "Modelo simple y estable"),
                ("Agresivo", (3, 1, 2), (2, 1, 1, 12), "Modelo más complejo"),
                ("Solo Tendencia", (2, 1, 0), (0, 0, 0, 8), "Modelo sobre ajustado")
            ]
        
        # Crear botones de preset en grid 2x2
        for i, (name, order, seasonal, desc) in enumerate(presets):
            row = i // 2
            col = i % 2
            
            # Color especial para presets dinámicos
            if self.presets_loaded and name in ['Conservador', 'Solo Tendencia', 'Agresivo']:
                bg_color = '#dbeafe'  # Azul claro para presets optimizados
                text_color = '#1e40af'
            else:
                bg_color = '#e5e7eb'  # Gris para presets normales
                text_color = '#374151'
            
            preset_btn = tk.Button(buttons_frame, text=name,
                                 command=lambda o=order, s=seasonal: self.apply_preset(o, s),
                                 font=('Segoe UI', 9, 'bold'),
                                 bg=bg_color, fg=text_color,
                                 relief='raised', bd=1, cursor='hand2',
                                 width=20, height=2)
            preset_btn.grid(row=row*2, column=col, padx=10, pady=4, sticky='ew')
            
            # Descripción del preset - TEXTO MÁS PEQUEÑO
            desc_label = tk.Label(buttons_frame, text=desc, font=('Segoe UI', 7),
                                bg='#f8fafc', fg='#6b7280')
            desc_label.grid(row=row*2+1, column=col, padx=10, pady=(0, 6))
        
        # Configurar peso de columnas
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)
        
    def get_dynamic_presets(self):
        """NUEVA FUNCIÓN: Obtener presets dinámicos del bridge"""
        if not self.dynamic_presets:
            return []
        
        # Extraer parámetros de los modelos del bridge
        presets = []
        
        # Preset "Optimizado" siempre es el mismo
        presets.append(("Optimizado (Actual)", (4, 0, 0), (1, 0, 0, 8), "Parámetros optimizados"))
        
        # Mapear presets dinámicos según especificación:
        # Top 1 -> Conservador, Top 2 -> Solo Tendencia, Top 3 -> Agresivo
        preset_mapping = [
            ("Conservador", "Top #1 del optimizador"),
            ("Solo Tendencia", "Top #2 del optimizador"), 
            ("Agresivo", "Top #3 del optimizador")
        ]
        
        for i, (preset_name, desc_suffix) in enumerate(preset_mapping):
            if preset_name in self.dynamic_presets:
                model_data = self.dynamic_presets[preset_name]['model']
                order = tuple(model_data['order'])
                seasonal_order = tuple(model_data['seasonal_order'])
                precision = model_data.get('precision_final', 0)
                
                description = f"{desc_suffix} (Precisión: {precision:.1f}%)"
                presets.append((preset_name, order, seasonal_order, description))
        
        return presets
        
    def create_validation_section(self, parent):
        """Crear sección de validación de parámetros - SIN BOTÓN REDUNDANTE"""
        validation_frame = tk.LabelFrame(parent, text="Vista Previa de Configuración", 
                                        font=('Segoe UI', 11, 'bold'),
                                        bg='#f8fafc', fg='#ea580c',
                                        relief='ridge', bd=2)
        validation_frame.pack(fill='x', pady=(0, 10))
        
        # Frame para mostrar la configuración actual - ESPACIADO REDUCIDO
        preview_frame = tk.Frame(validation_frame, bg='#f8fafc')
        preview_frame.pack(fill='x', padx=15, pady=10)
        
        # Label para mostrar la configuración - MÁS PROMINENTE
        self.config_preview_label = tk.Label(preview_frame,
                                           font=('Segoe UI', 14, 'bold'),
                                           bg='#ffffff', fg='#1e40af',
                                           relief='solid', bd=2, padx=20, pady=12)
        self.config_preview_label.pack(fill='x')
        
        # Texto informativo sobre actualización automática
        info_label = tk.Label(preview_frame,
                             text="La vista previa se actualiza automáticamente al cambiar los parámetros",
                             font=('Segoe UI', 9, 'italic'),
                             bg='#f8fafc', fg='#6b7280')
        info_label.pack(pady=(6, 0))
        
        # Actualizar vista previa inicial
        self.update_preview()
        
    def create_action_buttons(self, parent):
        """Crear botones de acción - DISEÑO ORIGINAL CON ESPACIADO OPTIMIZADO"""
        # Separador visual - MÁS DELGADO
        separator = tk.Frame(parent, bg='#d1d5db', height=2)
        separator.pack(fill='x', pady=(10, 8))
        
        # Texto de instrucción - MÁS COMPACTO
        instruction_label = tk.Label(parent,
                                   text="SELECCIONE UNA ACCIÓN PARA CONTINUAR",
                                   font=('Segoe UI', 11, 'bold'),
                                   bg='#dbeafe', fg='#1e40af',
                                   relief='solid', bd=2, padx=10, pady=6)
        instruction_label.pack(fill='x', pady=(0, 10))
        
        buttons_frame = tk.Frame(parent, bg='#f8fafc')
        buttons_frame.pack(fill='x', pady=(8, 0))
        
        # Frame interno para centrar los botones
        center_frame = tk.Frame(buttons_frame, bg='#f8fafc')
        center_frame.pack(expand=True)
        
        # Botón Cancelar - TAMAÑO LIGERAMENTE REDUCIDO
        cancel_btn = tk.Button(center_frame, text="CANCELAR",
                              command=self.on_cancel,
                              font=('Segoe UI', 11, 'bold'),
                              bg='#ef4444', fg='white',
                              relief='raised', bd=3, cursor='hand2',
                              width=16, height=2,
                              activebackground='#dc2626',
                              activeforeground='white')
        cancel_btn.pack(side='left', padx=(0, 12))
        
        # Botón Confirmar y Ejecutar - TAMAÑO LIGERAMENTE REDUCIDO
        confirm_btn = tk.Button(center_frame, text="CONFIRMAR Y EJECUTAR ANÁLISIS",
                               command=self.on_confirm,
                               font=('Segoe UI', 11, 'bold'),
                               bg='#059669', fg='white',
                               relief='raised', bd=3, cursor='hand2',
                               width=32, height=2,
                               activebackground='#047857',
                               activeforeground='white')
        confirm_btn.pack(side='right')
        
        # Agregar efectos hover mejorados
        self.add_hover_effects(cancel_btn, '#dc2626', '#ef4444')
        self.add_hover_effects(confirm_btn, '#047857', '#059669')
        
        # Hacer que el botón de confirmar parpadee levemente para llamar la atención
        def highlight_confirm():
            try:
                if confirm_btn.winfo_exists():
                    current_bg = confirm_btn.cget('bg')
                    if current_bg == '#059669':
                        confirm_btn.config(bg='#10b981')
                    else:
                        confirm_btn.config(bg='#059669')
                    # Repetir cada 1.5 segundos
                    self.window.after(1500, highlight_confirm)
            except:
                pass
        
        # Iniciar el parpadeo después de 2 segundos
        self.window.after(2000, highlight_confirm)
        
        # Atajos de teclado
        self.window.bind('<Return>', lambda e: self.on_confirm())  # Enter para confirmar
        self.window.bind('<Escape>', lambda e: self.on_cancel())   # Escape para cancelar
        
        # Mostrar atajos de teclado - MÁS COMPACTO
        shortcuts_label = tk.Label(buttons_frame,
                                  text="Atajos de Teclado: Enter = Confirmar | Escape = Cancelar",
                                  font=('Segoe UI', 9, 'italic'),
                                  bg='#f8fafc', fg='#6b7280')
        shortcuts_label.pack(pady=(6, 0))
        
    def add_hover_effects(self, button, hover_color, normal_color):
        """Agregar efectos hover a botones"""
        def on_enter(e):
            button.config(bg=hover_color)
        
        def on_leave(e):
            button.config(bg=normal_color)
            
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        
    def apply_preset(self, order, seasonal_order):
        """Aplicar configuración predefinida"""
        # Actualizar variables
        self.order_vars['p'].set(order[0])
        self.order_vars['d'].set(order[1])
        self.order_vars['q'].set(order[2])
        
        self.seasonal_vars['P'].set(seasonal_order[0])
        self.seasonal_vars['D'].set(seasonal_order[1])
        self.seasonal_vars['Q'].set(seasonal_order[2])
        self.seasonal_vars['s'].set(seasonal_order[3])
        
        # La vista previa se actualiza automáticamente gracias a los trace callbacks
        
    def update_preview(self):
        """Actualizar la vista previa de la configuración"""
        try:
            # Obtener valores actuales
            p = self.order_vars['p'].get()
            d = self.order_vars['d'].get()
            q = self.order_vars['q'].get()
            
            P = self.seasonal_vars['P'].get()
            D = self.seasonal_vars['D'].get()
            Q = self.seasonal_vars['Q'].get()
            s = self.seasonal_vars['s'].get()
            
            # Crear texto de configuración
            config_text = f"SARIMAX({p},{d},{q})x({P},{D},{Q},{s})"
            
            # Validar parámetros
            if self.validate_parameters():
                self.config_preview_label.config(text=config_text, fg='#1e40af', bg='#dbeafe')
            else:
                self.config_preview_label.config(text=f"{config_text} - REVISAR PARÁMETROS", 
                                                fg='#dc2626', bg='#fee2e2')
                
        except Exception as e:
            self.config_preview_label.config(text="Error al generar vista previa", 
                                            fg='#dc2626', bg='#fee2e2')
            
    def validate_parameters(self):
        """Validar que los parámetros sean válidos"""
        try:
            # Verificar rangos básicos
            p = self.order_vars['p'].get()
            d = self.order_vars['d'].get()
            q = self.order_vars['q'].get()
            
            P = self.seasonal_vars['P'].get()
            D = self.seasonal_vars['D'].get()
            Q = self.seasonal_vars['Q'].get()
            s = self.seasonal_vars['s'].get()
            
            # Validaciones básicas
            if not (0 <= p <= 10 and 0 <= d <= 2 and 0 <= q <= 10):
                return False
                
            if not (0 <= P <= 5 and 0 <= D <= 2 and 0 <= Q <= 5):
                return False
                
            if not (1 <= s <= 24):
                return False
                
            return True
            
        except:
            return False
            
    def on_confirm(self):
        """Confirmar parámetros y ejecutar función"""
        if not self.validate_parameters():
            messagebox.showerror("Parámetros Inválidos", 
                               "Los parámetros ingresados no son válidos.\n"
                               "Por favor revise los valores e intente nuevamente.")
            return
            
        # Obtener valores finales
        order = (self.order_vars['p'].get(), 
                self.order_vars['d'].get(), 
                self.order_vars['q'].get())
        
        seasonal_order = (self.seasonal_vars['P'].get(), 
                         self.seasonal_vars['D'].get(), 
                         self.seasonal_vars['Q'].get(), 
                         self.seasonal_vars['s'].get())
        
        # Actualizar variables globales
        global SELECTED_ORDER, SELECTED_SEASONAL_ORDER, PARAMETERS_CONFIRMED
        SELECTED_ORDER = order
        SELECTED_SEASONAL_ORDER = seasonal_order
        PARAMETERS_CONFIRMED = True
        
        print(f"DEBUG: Parámetros confirmados - order: {order}, seasonal_order: {seasonal_order}")
        
        # Cerrar ventana
        self.close_window()
        
        # Ejecutar callback con un delay pequeño para asegurar que la ventana se cierre
        def execute_callback():
            time.sleep(0.1)  # Pequeño delay
            if self.callback_function:
                self.callback_function()
        
        thread = threading.Thread(target=execute_callback)
        thread.daemon = True
        thread.start()
        
    def on_cancel(self):
        """Cancelar selección de parámetros"""
        global PARAMETERS_CONFIRMED
        PARAMETERS_CONFIRMED = False
        self.close_window()
        
    def close_window(self):
        """Cerrar la ventana de manera segura"""
        global CURRENT_WINDOW
        if self.window:
            try:
                self.window.grab_release()
                self.window.destroy()
                CURRENT_WINDOW = None
            except:
                pass


def show_parameter_selector(parent, callback_function, module_name="Análisis SAIDI"):
    """Función principal para mostrar el selector de parámetros"""
    global PARAMETERS_CONFIRMED
    PARAMETERS_CONFIRMED = False
    
    selector = ParameterSelectorWindow(parent, callback_function, module_name)
    return selector


def get_selected_parameters():
    """Obtener los parámetros seleccionados"""
    global SELECTED_ORDER, SELECTED_SEASONAL_ORDER, PARAMETERS_CONFIRMED
    return SELECTED_ORDER, SELECTED_SEASONAL_ORDER, PARAMETERS_CONFIRMED


def reset_parameters():
    """Resetear parámetros a valores por defecto"""
    global SELECTED_ORDER, SELECTED_SEASONAL_ORDER, PARAMETERS_CONFIRMED
    SELECTED_ORDER = (4, 0, 0)
    SELECTED_SEASONAL_ORDER = (1, 0, 0, 8)
    PARAMETERS_CONFIRMED = False


if __name__ == "__main__":
    # Prueba independiente del selector
    root = tk.Tk()
    root.title("Prueba Selector")
    root.geometry("300x200")
    
    def test_callback():
        order, seasonal_order, confirmed = get_selected_parameters()
        if confirmed:
            print(f"Parámetros seleccionados:")
            print(f"order: {order}")
            print(f"seasonal_order: {seasonal_order}")
        else:
            print("Selección cancelada")
    
    btn = tk.Button(root, text="Abrir Selector", 
                   command=lambda: show_parameter_selector(root, test_callback, "Prueba"))
    btn.pack(expand=True)
    
    root.mainloop()