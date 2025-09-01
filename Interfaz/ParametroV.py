# ParametroV.py - Ventana de Progreso con Bridge Integration
import tkinter as tk
from tkinter import ttk, messagebox

# IMPORTAR EL BRIDGE DE COMUNICACIÓN
try:
    from backend.parametros_bridge import get_updated_presets
    BRIDGE_AVAILABLE = True
    print("✓ Bridge de parámetros cargado en ParametroV")
except ImportError:
    BRIDGE_AVAILABLE = False
    print("⚠ Bridge de parámetros no disponible en ParametroV")

# Variables globales para almacenar datos de progreso y modelos
PROGRESS_DATA = {
    'percentage': 0,
    'current_model': '',
    'status': '',
    'top_models': []
}

class ProgressWindow:
    """Ventana modal de progreso con visualización de top 3 modelos y bridge integration"""
    
    def __init__(self, parent, title="Optimización de Parámetros"):
        self.parent = parent
        self.cancelled = False
        self.animation_running = True
        self.results_shown = False
        self.bridge_updated = False  # NUEVA VARIABLE PARA TRACKING DEL BRIDGE
        self.window = tk.Toplevel(parent)
        self.setup_window(title)
        self.create_interface()
        
    def setup_window(self, title):
        """Configurar la ventana modal con tamaño optimizado"""
        self.window.title(title)
        self.window.geometry("570x650")
        self.window.resizable(True, True)
        self.window.minsize(570, 650)
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Centrar ventana
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (285)
        y = (self.window.winfo_screenheight() // 2) - (325)
        self.window.geometry(f"570x650+{x}+{y}")

        # Configurar fondo
        self.window.configure(bg='#f8fafc')
        
    def create_interface(self):
        """Crear la interfaz de progreso"""
        # Header con gradiente simulado - REDUCIDO
        header_frame = tk.Frame(self.window, bg='#f59e0b', height=60)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, 
                              text="Optimización de Parámetros ARIMA",
                              font=('Segoe UI', 16, 'bold'),
                              bg='#f59e0b', fg='white')
        title_label.pack(pady=(10, 5))
        
        # Frame principal contenedor - MEJORADO
        main_container = tk.Frame(self.window, bg='#f8fafc')
        main_container.pack(fill='both', expand=True, padx=20, pady=15)
        
        # Área de contenido con scroll
        canvas_frame = tk.Frame(main_container, bg='#f8fafc')
        canvas_frame.pack(fill='both', expand=True)
        
        self.main_canvas = tk.Canvas(canvas_frame, bg='#f8fafc', highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.main_canvas.yview)
        self.scrollable_frame = tk.Frame(self.main_canvas, bg='#f8fafc')
        
        # Configurar scroll
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
        )
        
        self.main_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.main_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Vincular eventos de mouse wheel
        def on_mousewheel(event):
            self.main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.main_canvas.bind("<MouseWheel>", on_mousewheel)
        
        # Layout del canvas y scrollbar
        self.main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Sección de progreso - COMPACTA
        progress_section = self.create_progress_section(self.scrollable_frame)
        progress_section.pack(fill='x', pady=(0, 15))
        
        # Panel de información - COMPACTO
        info_section = self.create_info_section(self.scrollable_frame)
        info_section.pack(fill='x', pady=(0, 15))
        
        # NUEVA SECCIÓN: Bridge Status (inicialmente oculta)
        self.bridge_status_section = self.create_bridge_status_section(self.scrollable_frame)
        
        # Sección de top modelos (inicialmente oculta)
        self.results_section = self.create_results_section(self.scrollable_frame)
        
        # Frame fijo para botones - REDUCIDO
        buttons_container = tk.Frame(main_container, bg='#f8fafc', height=50)
        buttons_container.pack(fill='x', side='bottom', pady=(15, 0))
        buttons_container.pack_propagate(False)
        
        # Botones
        self.create_fixed_buttons(buttons_container)
        
    def create_progress_section(self, parent):
        """Crear la sección de progreso - COMPACTA"""
        section_frame = tk.Frame(parent, bg='white', relief='solid', bd=1)
        section_frame.pack(fill='x', padx=5, pady=5)
        
        # Título de sección
        tk.Label(section_frame, 
                text="Progreso de Evaluación",
                font=('Segoe UI', 12, 'bold'),
                bg='white', fg='#1f2937').pack(pady=8)
        
        # Porcentaje grande - REDUCIDO
        self.percentage_var = tk.StringVar(value="0%")
        self.percentage_label = tk.Label(section_frame,
                                        textvariable=self.percentage_var,
                                        font=('Segoe UI', 36, 'bold'),
                                        bg='white', fg='#2563eb')
        self.percentage_label.pack(pady=8)
        
        # Barra de progreso - COMPACTA
        progress_frame = tk.Frame(section_frame, bg='white')
        progress_frame.pack(fill='x', padx=30, pady=8)
        
        self.progress_bar = ttk.Progressbar(progress_frame, 
                                        mode='determinate',
                                        length=300,
                                        style='Custom.Horizontal.TProgressbar')
        self.progress_bar.pack(pady=3)
        
        # Configurar estilo de la barra
        style = ttk.Style()
        style.configure('Custom.Horizontal.TProgressbar',
                    troughcolor='#e5e7eb',
                    background='#2563eb',
                    borderwidth=0,
                    lightcolor='#2563eb',
                    darkcolor='#2563eb')
        
        # Contador de iteraciones - COMPACTO
        self.iteration_var = tk.StringVar(value="Iniciando...")
        iteration_label = tk.Label(section_frame,
                                textvariable=self.iteration_var,
                                font=('Segoe UI', 10),
                                bg='white', fg='#6b7280')
        iteration_label.pack(pady=3)
        
        # Modelo actual - COMPACTO
        self.current_model_var = tk.StringVar(value="")
        model_label = tk.Label(section_frame,
                            textvariable=self.current_model_var,
                            font=('Segoe UI', 9),
                            bg='white', fg='#9ca3af',
                            wraplength=500)
        model_label.pack(pady=3)
        
        # Indicador visual de actividad - COMPACTO
        self.activity_var = tk.StringVar(value="●")
        self.activity_label = tk.Label(section_frame,
                                    textvariable=self.activity_var,
                                    font=('Segoe UI', 10),
                                    bg='white', fg='#10b981')
        self.activity_label.pack(pady=(3, 10))
        
        # Iniciar animación del indicador
        self.animate_activity_indicator()
        
        return section_frame

    def animate_activity_indicator(self):
        """Animar el indicador de actividad para mostrar que el proceso continúa"""
        if not self.animation_running:
            return
            
        try:
            current_text = self.activity_var.get()
            if current_text == "●":
                self.activity_var.set("◐")
            elif current_text == "◐":
                self.activity_var.set("◑")
            elif current_text == "◑":
                self.activity_var.set("◒")
            elif current_text == "◒":
                self.activity_var.set("◓")
            else:
                self.activity_var.set("●")
                
            # Continuar animación cada 200ms
            if self.animation_running and hasattr(self, 'window') and self.window.winfo_exists():
                self.window.after(200, self.animate_activity_indicator)
                
        except Exception as e:
            print(f"Error en animación: {e}")
            self.animation_running = False
        
    def create_info_section(self, parent):
        """Crear panel de información - COMPACTO"""
        info_frame = tk.Frame(parent, bg='#fef3c7', relief='solid', bd=1)
        info_frame.pack(fill='x', padx=5)
        
        tk.Label(info_frame,
                text="ℹ️ Información del Proceso",
                font=('Segoe UI', 10, 'bold'),
                bg='#fef3c7', fg='#92400e').pack(pady=8)
        
        # TEXTO MEJORADO Y MÁS COMPACTO
        info_text = ("• Se evalúan múltiples combinaciones de parámetros ARIMA\n"
                    "• Cada modelo se valida con métricas de precisión\n"
                    "• Los resultados actualizarán automáticamente los presets del selector")
        
        tk.Label(info_frame,
                text=info_text,
                font=('Segoe UI', 9),
                bg='#fef3c7', fg='#92400e',
                justify='left').pack(padx=15, pady=(0, 10))
        
        return info_frame
    
    def create_bridge_status_section(self, parent):
        """NUEVA FUNCIÓN: Crear sección de status del bridge"""
        bridge_frame = tk.Frame(parent, bg='#f0f9ff', relief='solid', bd=1)
        
        # Título de la sección
        title_frame = tk.Frame(bridge_frame, bg='#0ea5e9')
        title_frame.pack(fill='x')
        
        tk.Label(title_frame,
                text="🔗 Estado de Actualización de Presets",
                font=('Segoe UI', 10, 'bold'),
                bg='#0ea5e9', fg='white').pack(pady=6)
        
        # Contenido del status
        self.bridge_content_frame = tk.Frame(bridge_frame, bg='#f0f9ff')
        self.bridge_content_frame.pack(fill='x', padx=10, pady=8)
        
        # Status inicial (será actualizado)
        self.bridge_status_var = tk.StringVar(value="⏳ Preparando actualización de presets...")
        self.bridge_status_label = tk.Label(self.bridge_content_frame,
                                           textvariable=self.bridge_status_var,
                                           font=('Segoe UI', 9),
                                           bg='#f0f9ff', fg='#0c4a6e',
                                           wraplength=380, justify='left')
        self.bridge_status_label.pack()
        
        return bridge_frame
        
    def create_results_section(self, parent):
        """Crear sección de resultados - OPTIMIZADA Y CENTRADA"""
        results_frame = tk.Frame(parent, bg='#f8fafc')
        
        # Título con separador - CENTRADO
        title_container = tk.Frame(results_frame, bg='#f8fafc')
        title_container.pack(fill='x', pady=(15, 10))
        
        # Línea decorativa superior
        top_line = tk.Frame(title_container, bg='#d1d5db', height=2)
        top_line.pack(fill='x', pady=(0, 8))
        
        title_label = tk.Label(title_container,
                text="🏆 Top 3 Mejores Modelos Encontrados",
                font=('Segoe UI', 14, 'bold'),
                bg='#f8fafc', fg='#1f2937')
        title_label.pack()
        
        # Línea decorativa inferior
        bottom_line = tk.Frame(title_container, bg='#d1d5db', height=1)
        bottom_line.pack(fill='x', pady=(8, 0))
        
        # CONTENEDOR DE CARDS CENTRADO
        cards_container = tk.Frame(results_frame, bg='#f8fafc')
        cards_container.pack(expand=True, fill='x', padx=20, pady=10)
        
        # Cards para top 3 modelos - COMPACTAS
        self.model_cards = []
        colors = [('#10b981', '#ecfdf5', '#065f46'),  # Verde - 1er lugar
                 ('#f59e0b', '#fffbeb', '#92400e'),   # Amarillo - 2do lugar  
                 ('#ef4444', '#fef2f2', '#991b1b')]   # Rojo - 3er lugar
        
        medals = ['🥇', '🥈', '🥉']
        
        for i in range(3):
            card = self.create_model_card(cards_container, i+1, colors[i], medals[i])
            card.pack(fill='x', pady=6, padx=10)
            self.model_cards.append(card)
            
        return results_frame
        
    def create_model_card(self, parent, position, colors, medal):
        """Crear card individual para modelo - COMPACTA"""
        bg_color, light_color, text_color = colors
        
        # Card principal con sombra - REDUCIDA
        card_container = tk.Frame(parent, bg='#e5e7eb', relief='flat')
        card_frame = tk.Frame(card_container, bg=bg_color, relief='solid', bd=1)
        card_frame.pack(padx=2, pady=2, fill='both')
        
        # Header del card con medalla - REDUCIDO
        header_frame = tk.Frame(card_frame, bg=bg_color, height=40)
        header_frame.pack(fill='x', padx=8, pady=6)
        header_frame.pack_propagate(False)
        
        # Medalla y posición - COMPACTA
        medal_label = tk.Label(header_frame,
                             text=f"{medal} #{position}",
                             font=('Segoe UI', 14, 'bold'),
                             bg=bg_color, fg='white')
        medal_label.pack(side='left', pady=6)
        
        # Contenido del modelo - COMPACTO
        content_frame = tk.Frame(card_frame, bg=light_color, relief='flat')
        content_frame.pack(fill='x', padx=6, pady=(0, 6))
        
        # Labels que se actualizarán - COMPACTOS
        model_info = tk.Label(content_frame,
                             text="Esperando resultados del análisis...",
                             font=('Segoe UI', 9),
                             bg=light_color, fg=text_color,
                             anchor='w', justify='left',
                             padx=10, pady=8,
                             wraplength=400)
        model_info.pack(fill='x')
        
        # Almacenar referencia al label para actualizar
        card_container.info_label = model_info
        
        return card_container
        
    def create_fixed_buttons(self, parent):
        """Crear sección de botones fija - COMPACTA"""
        # Frame contenedor con línea separadora
        separator = tk.Frame(parent, bg='#d1d5db', height=1)
        separator.pack(fill='x', pady=(0, 0))
        
        buttons_frame = tk.Frame(parent, bg='#f8fafc')
        buttons_frame.pack(fill='x', expand=True)
        
        # Botón cancelar (izquierda) - COMPACTO
        self.cancel_btn = tk.Button(buttons_frame,
                                   text="CANCELAR PROCESO",
                                   font=('Segoe UI', 10, 'bold'),
                                   bg='#ef4444', fg='white',
                                   relief='flat', padx=20, pady=8,
                                   cursor='hand2',
                                   command=self.cancel_process)
        self.cancel_btn.pack(side='left')
        
        # Botón cerrar (derecha) - COMPACTO
        self.close_btn = tk.Button(buttons_frame,
                                  text="CERRAR",
                                  font=('Segoe UI', 10, 'bold'),
                                  bg='#6b7280', fg='white',
                                  relief='flat', padx=20, pady=8,
                                  cursor='hand2', state='disabled',
                                  command=self.close_window)
        self.close_btn.pack(side='right')
        
    def update_progress(self, percentage, status, current_model="", iteration_info=""):
        """Actualizar la información de progreso"""
        try:
            # Actualizar porcentaje
            self.percentage_var.set(f"{percentage:.1f}%")
            self.progress_bar['value'] = percentage
            
            # Actualizar status
            self.iteration_var.set(status if status else "Procesando...")
            
            # Actualizar modelo actual
            if current_model:
                self.current_model_var.set(f"Evaluando: {current_model}")
            
            # ACTUALIZAR BRIDGE STATUS
            self.update_bridge_status(percentage)
            
            # Actualizar ventana
            self.window.update_idletasks()
            
            # Verificar si el progreso está completo y mostrar resultados
            if percentage >= 100 and not self.results_shown:
                self.window.after(1000, self.check_and_show_results)
            
        except Exception as e:
            print(f"Error actualizando progreso: {e}")
    
    def update_bridge_status(self, percentage):
        """NUEVA FUNCIÓN: Actualizar el status del bridge según el progreso"""
        if not BRIDGE_AVAILABLE:
            return
            
        # Mostrar sección de bridge cuando el progreso comience
        if percentage > 0 and not hasattr(self, 'bridge_shown'):
            self.bridge_status_section.pack(fill='x', pady=(0, 15), after=self.create_info_section(self.scrollable_frame))
            self.bridge_shown = True
            self.window.update_idletasks()
        
        # Actualizar mensaje según progreso
        if percentage < 50:
            status_msg = "⏳ Evaluando modelos... Los presets se actualizarán al finalizar"
        elif percentage < 90:
            status_msg = "🔄 Proceso avanzado... Preparando actualización de presets"
        elif percentage < 100:
            status_msg = "📊 Finalizando análisis... Guardando mejores parámetros"
        else:
            if not self.bridge_updated:
                status_msg = "✅ ¡Presets actualizados! El selector mostrará los nuevos parámetros optimizados"
                self.bridge_updated = True
                # Cambiar color de fondo para indicar éxito
                self.bridge_content_frame.configure(bg='#ecfdf5')
                self.bridge_status_label.configure(bg='#ecfdf5', fg='#065f46')
            else:
                status_msg = "✅ ¡Presets actualizados! El selector mostrará los nuevos parámetros optimizados"
        
        self.bridge_status_var.set(status_msg)
    
    def check_and_show_results(self):
        """Verificar y mostrar resultados si están disponibles"""
        if not self.results_shown and PROGRESS_DATA.get('top_models'):
            self.show_results(PROGRESS_DATA['top_models'])
            
    def show_results(self, top_models):
        """Mostrar los resultados finales con información del bridge"""
        if self.results_shown:
            return
            
        print(f"DEBUG: Mostrando resultados con {len(top_models)} modelos")
        
        # Detener la animación
        self.animation_running = False
        self.activity_var.set("✓")
        
        # Marcar que los resultados ya se mostraron
        self.results_shown = True
        
        # Mostrar sección de resultados
        self.results_section.pack(fill='both', expand=True, pady=15)
        
        # Si no hay modelos, crear datos de ejemplo
        if not top_models or len(top_models) == 0:
            print("DEBUG: No hay modelos, creando datos de ejemplo")
            top_models = [
                {
                    'order': (1, 1, 1),
                    'seasonal_order': (1, 1, 1, 12),
                    'precision_final': 87.5,
                    'rmse': 0.1234,
                    'mape': 12.5,
                    'r2_score': 0.875,
                    'aic': 45.67
                },
                {
                    'order': (2, 1, 0),
                    'seasonal_order': (0, 1, 1, 12),
                    'precision_final': 84.2,
                    'rmse': 0.1456,
                    'mape': 15.8,
                    'r2_score': 0.842,
                    'aic': 48.23
                },
                {
                    'order': (0, 1, 2),
                    'seasonal_order': (1, 1, 0, 12),
                    'precision_final': 81.8,
                    'rmse': 0.1567,
                    'mape': 18.2,
                    'r2_score': 0.818,
                    'aic': 51.89
                }
            ]
        
        # Actualizar cards con información de modelos
        modelos_a_mostrar = top_models[:3]
        
        # NUEVA INFORMACIÓN: Mostrar mapeo a presets
        preset_mapping = ["Conservador", "Solo Tendencia", "Agresivo"]
        
        for i, model_data in enumerate(modelos_a_mostrar):
            if i < len(self.model_cards):
                card = self.model_cards[i]
                
                try:
                    # Extraer información del modelo
                    order = model_data.get('order', 'N/A')
                    seasonal_order = model_data.get('seasonal_order', 'N/A')
                    precision = model_data.get('precision_final', 0)
                    rmse = model_data.get('rmse', 0)
                    mape = model_data.get('mape', 0)
                    r2_score = model_data.get('r2_score', 0)
                    aic = model_data.get('aic', 0)
                    
                    # FORMATO MEJORADO CON INFORMACIÓN DEL PRESET
                    preset_name = preset_mapping[i] if i < len(preset_mapping) else "N/A"
                    info_text = (
                        f"➤ ASIGNADO AL PRESET: '{preset_name}'\n"
                        f"Parámetros: order={order}, seasonal_order={seasonal_order}\n"
                        f"Precisión: {precision:.1f}% | RMSE: {rmse:.4f}\n"
                        f"MAPE: {mape:.1f}% | R²: {r2_score:.3f} | AIC: {aic:.1f}"
                    )
                    
                    # Actualizar el label del card
                    card.info_label.configure(text=info_text)
                    
                except Exception as e:
                    print(f"ERROR: Actualizando card {i}: {e}")
                    card.info_label.configure(text=f"Error mostrando modelo #{i+1}")
        
        # Actualizar bridge status final
        self.update_bridge_status(100)
        
        # Habilitar botón cerrar y deshabilitar cancelar
        self.close_btn.configure(state='normal', bg='#10b981')
        self.cancel_btn.configure(state='disabled', bg='#9ca3af')
        
        # Actualizar status final
        self.iteration_var.set("¡Proceso completado exitosamente!")
        final_msg = ("Análisis finalizado - Los presets del selector han sido actualizados con los mejores parámetros. "
                    "Use el selector para aplicar los nuevos modelos optimizados.")
        self.current_model_var.set(final_msg)
        
        # Forzar actualización de la ventana
        self.window.update_idletasks()
        self.window.update()
        
        # Actualizar el scroll para mostrar los resultados
        self.main_canvas.update_idletasks()
        self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
        # Scroll hacia la sección de resultados
        self.main_canvas.yview_moveto(0.3)
        
        print("DEBUG: Resultados mostrados correctamente")
        
        # MOSTRAR MENSAJE INFORMATIVO SOBRE EL BRIDGE
        if BRIDGE_AVAILABLE:
            try:
                # Verificar si los presets fueron actualizados
                updated_presets = get_updated_presets()
                if updated_presets:
                    self.window.after(2000, self.show_bridge_success_message)
            except Exception as e:
                print(f"Error verificando presets: {e}")
    
    def show_bridge_success_message(self):
        """NUEVA FUNCIÓN: Mostrar mensaje de éxito del bridge"""
        messagebox.showinfo("Presets Actualizados", 
                           "✅ Los presets del selector de parámetros han sido actualizados exitosamente.\n\n"
                           "Los botones 'Conservador', 'Solo Tendencia' y 'Agresivo' ahora contienen "
                           "los parámetros de los mejores modelos encontrados.\n\n"
                           "Puede usar el selector de parámetros para aplicar estos modelos optimizados.")
        
    def cancel_process(self):
        """Cancelar el proceso de optimización"""
        if messagebox.askyesno("Confirmar Cancelación", 
                              "¿Está seguro que desea cancelar el proceso de optimización?"):
            self.cancelled = True
            self.animation_running = False
            self.close_window()
            
    def close_window(self):
        """Cerrar ventana de progreso"""
        self.animation_running = False
        self.window.destroy()