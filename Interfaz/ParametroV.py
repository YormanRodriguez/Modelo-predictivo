# ParametroV.py 
import tkinter as tk
from tkinter import ttk, messagebox
import os
import json
from datetime import datetime
import tempfile

# AGREGAR: Importar sistema de rutas PyInstaller
try:
    from path_utils import path_manager, get_temp_file, cleanup_old_temp_files, is_frozen
    PATH_UTILS_AVAILABLE = True
    print("Sistema de rutas PyInstaller cargado en ParametroV.py")
except ImportError:
    PATH_UTILS_AVAILABLE = False
    print("Sistema de rutas no disponible en ParametroV.py - modo compatibilidad")

# IMPORTAR EL BRIDGE DE COMUNICACIÓN
try:
    from backend.parametros_bridge import get_updated_presets
    BRIDGE_AVAILABLE = True
    print("Bridge de parámetros cargado en ParametroV")
except ImportError:
    BRIDGE_AVAILABLE = False
    print("Bridge de parámetros no disponible en ParametroV")

# Variables globales para almacenar datos de progreso y modelos
PROGRESS_DATA = {
    'percentage': 0,
    'current_model': '',
    'status': '',
    'top_models': []
}

class ProgressWindow:
    """Ventana modal de progreso con resultados integrados en la misma interfaz - COLORES CORPORATIVOS"""
    
    def __init__(self, parent, title="Optimización de Parámetros", progress_file=None):
        self.parent = parent
        self.cancelled = False
        self.animation_running = True
        self.results_shown = False
        self.bridge_updated = False
        
        # CORRECCIÓN CRÍTICA: Asegurar que progress_file sea válido con path_utils
        if progress_file and os.path.dirname(progress_file):
            self.progress_file = progress_file
        else:
            # Crear archivo temporal usando path_utils si está disponible
            if PATH_UTILS_AVAILABLE:
                self.progress_file = path_manager.get_temp_file('saidi_progress.json')
            else:
                self.progress_file = tempfile.mktemp(suffix='_progress.json', prefix='saidi_')
            print(f"Progress file corregido: {self.progress_file}")
            
        # NUEVA VARIABLE: Archivo de cancelación específico
        self.cancel_file = self.progress_file.replace('.json', '_cancel.json')
        
        # Referencias para contenedores dinámicos
        self.main_container = None
        self.progress_section = None
        self.info_section = None
        self.results_section = None
        
        self.window = tk.Toplevel(parent)
        self.setup_window(title)
        self.create_interface()
        
        # NUEVO: Limpiar archivos de cancelación previos al inicio
        self.cleanup_previous_cancellation_files()
        
    def cleanup_previous_cancellation_files(self):
        """NUEVA FUNCIÓN: Limpiar archivos de cancelación previos"""
        try:
            if os.path.exists(self.cancel_file):
                os.remove(self.cancel_file)
                print(f"Archivo de cancelación previo eliminado: {self.cancel_file}")
        except Exception as e:
            print(f"Error limpiando archivos previos: {e}")
        
    def setup_window(self, title):
        """Configurar la ventana modal con tamaño optimizado y redimensionable"""
        self.window.title(title)
        self.window.geometry("620x700")  # Ligeramente más grande para resultados
        self.window.resizable(True, True)
        self.window.minsize(620, 700)
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Centrar ventana
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (310)
        y = max(30, (self.window.winfo_screenheight() // 2) - (350))
        self.window.geometry(f"620x700+{x}+{y}")

        # Configurar fondo
        self.window.configure(bg='#f8fafc')
        
        # MODIFICADO: Manejar el cierre de ventana con mejor lógica
        self.window.protocol("WM_DELETE_WINDOW", self.on_window_close)
        
    def create_cancellation_file(self):
        """FUNCIÓN CORREGIDA: Crear archivo de cancelación con validación robusta"""
        try:
            # Verificar que el directorio base existe con path_utils
            cancel_dir = os.path.dirname(self.cancel_file)
            if not cancel_dir:  # Si no hay directorio, usar temp con path_utils
                if PATH_UTILS_AVAILABLE:
                    self.cancel_file = path_manager.get_temp_file('saidi_cancel.json')
                else:
                    self.cancel_file = tempfile.mktemp(suffix='_cancel.json', prefix='saidi_')
                cancel_dir = os.path.dirname(self.cancel_file)
                
            # Crear directorio si no existe
            os.makedirs(cancel_dir, exist_ok=True)
            
            # Crear el archivo con datos de cancelación
            cancel_data = {
                'cancelled_at': datetime.now().isoformat(),
                'cancelled_by': 'user_interface',
                'reason': 'user_requested_cancellation',
                'progress_file': self.progress_file,
                'pid': os.getpid()
            }
            
            # Escribir archivo de cancelación con manejo de errores
            with open(self.cancel_file, 'w', encoding='utf-8') as f:
                json.dump(cancel_data, f, ensure_ascii=False, indent=2)
            
            print(f"Archivo de cancelación creado: {self.cancel_file}")
            return True
            
        except PermissionError as e:
            print(f"Error de permisos creando archivo de cancelación: {e}")
            # Intentar crear en directorio temporal como fallback con path_utils
            try:
                if PATH_UTILS_AVAILABLE:
                    fallback_file = path_manager.get_temp_file('saidi_cancel_fallback.json')
                else:
                    fallback_file = tempfile.mktemp(suffix='_cancel_fallback.json', prefix='saidi_')
                
                with open(fallback_file, 'w', encoding='utf-8') as f:
                    json.dump(cancel_data, f, ensure_ascii=False, indent=2)
                self.cancel_file = fallback_file
                print(f"Archivo de cancelación creado en fallback: {fallback_file}")
                return True
            except Exception as fallback_error:
                print(f"Error en fallback: {fallback_error}")
                return False
                
        except Exception as e:
            print(f"Error inesperado creando archivo de cancelación: {e}")
            return False

    def cancel_process(self):
        """FUNCIÓN CORREGIDA: Cancelar el proceso con manejo robusto de errores"""
        if messagebox.askyesno("Confirmar Cancelación", 
                              "¿Está seguro que desea cancelar el proceso de optimización?\n\n"
                              "Esto detendrá inmediatamente todas las iteraciones en curso."):
            
            print("Usuario solicitó cancelación del proceso")
            
            # Marcar como cancelado localmente PRIMERO
            self.cancelled = True
            self.animation_running = False
            
            # Intentar crear archivo de cancelación
            cancel_success = self.create_cancellation_file()
            
            # ACTUALIZAR INTERFAZ INMEDIATAMENTE (independiente del éxito del archivo)
            self.update_cancellation_ui()
            
            if cancel_success:
                print("✓ Cancelación procesada exitosamente")
            else:
                print("⚠ Cancelación procesada con limitaciones")

    def update_cancellation_ui(self):
        """NUEVA FUNCIÓN: Actualizar interfaz para mostrar cancelación - COLORES CORPORATIVOS"""
        try:
            # Actualizar indicadores visuales
            self.percentage_var.set("CANCELADO")
            self.iteration_var.set("Proceso cancelado por el usuario")
            self.current_model_var.set("Deteniendo iteraciones y limpiando recursos...")
            self.activity_var.set("⚠")
            
            # Actualizar botones - COLORES CORPORATIVOS
            self.cancel_btn.configure(
                state='disabled', 
                bg='#a1a1a5',  # Color corporativo gris
                text="CANCELADO"
            )
            
            self.close_btn.configure(
                state='normal', 
                bg='#dc2626',  # Rojo para cerrar cancelado
                text="CERRAR (CANCELADO)"
            )
            
            # Actualizar barra de progreso para mostrar cancelación
            try:
                self.progress_bar.configure(style='Cancelled.Horizontal.TProgressbar')
                style = ttk.Style()
                style.configure('Cancelled.Horizontal.TProgressbar',
                            troughcolor='#fee2e2',
                            background='#dc2626',
                            borderwidth=0)
            except:
                pass  # Continuar aunque falle el estilo
                
            print("Interfaz de cancelación actualizada")
            
        except Exception as e:
            print(f"Error actualizando interfaz de cancelación: {e}")
    
    def create_interface(self):
        """Crear la interfaz de progreso inicial - COLORES CORPORATIVOS"""
        # Header con gradiente simulado - DINÁMICO - COLORES CORPORATIVOS
        self.header_frame = tk.Frame(self.window, bg='#9fcf67', height=60)  # Verde claro corporativo
        self.header_frame.pack(fill='x')
        self.header_frame.pack_propagate(False)
        
        self.title_label = tk.Label(self.header_frame, 
                              text="Optimización de Parámetros ARIMA",
                              font=('Segoe UI', 16, 'bold'),
                              bg='#9fcf67', fg='white')
        self.title_label.pack(pady=(10, 5))
        
        # Frame principal contenedor - GUARDAR REFERENCIA
        self.main_container = tk.Frame(self.window, bg='#f8fafc')
        self.main_container.pack(fill='both', expand=True, padx=20, pady=15)
        
        # Sección de progreso - GUARDAR REFERENCIA
        self.progress_section = self.create_progress_section(self.main_container)
        self.progress_section.pack(fill='x', pady=(0, 15))
        
        # Sección de información - GUARDAR REFERENCIA
        self.info_section = self.create_info_section(self.main_container)
        self.info_section.pack(fill='x', pady=(0, 15))
        
        # Botones
        self.buttons_container = tk.Frame(self.main_container, bg='#f8fafc', height=50)
        self.buttons_container.pack(fill='x', side='bottom', pady=(15, 0))
        self.buttons_container.pack_propagate(False)
        
        self.create_fixed_buttons(self.buttons_container)
        
    def create_progress_section(self, parent):
        """Crear la sección de progreso - COLORES CORPORATIVOS"""
        section_frame = tk.Frame(parent, bg='white', relief='solid', bd=1)
        
        # Título de sección - COLOR CORPORATIVO
        tk.Label(section_frame, 
                text="Progreso de Evaluación",
                font=('Segoe UI', 12, 'bold'),
                bg='white', fg='#0d9648').pack(pady=8)  # Verde oscuro corporativo
        
        # Porcentaje grande - COLOR CORPORATIVO
        self.percentage_var = tk.StringVar(value="0%")
        self.percentage_label = tk.Label(section_frame,
                                        textvariable=self.percentage_var,
                                        font=('Segoe UI', 36, 'bold'),
                                        bg='white', fg='#9fcf67')  # Verde claro corporativo
        self.percentage_label.pack(pady=8)
        
        # Barra de progreso
        progress_frame = tk.Frame(section_frame, bg='white')
        progress_frame.pack(fill='x', padx=30, pady=8)
        
        self.progress_bar = ttk.Progressbar(progress_frame, 
                                        mode='determinate',
                                        length=300)
        self.progress_bar.pack(pady=3)
        
        # Contador de iteraciones
        self.iteration_var = tk.StringVar(value="Iniciando...")
        iteration_label = tk.Label(section_frame,
                                textvariable=self.iteration_var,
                                font=('Segoe UI', 10),
                                bg='white', fg='#6b7280')
        iteration_label.pack(pady=3)
        
        # Modelo actual
        self.current_model_var = tk.StringVar(value="")
        model_label = tk.Label(section_frame,
                            textvariable=self.current_model_var,
                            font=('Segoe UI', 9),
                            bg='white', fg='#9ca3af',
                            wraplength=500)
        model_label.pack(pady=3)
        
        # Indicador visual de actividad - COLOR CORPORATIVO
        self.activity_var = tk.StringVar(value="●")
        self.activity_label = tk.Label(section_frame,
                                    textvariable=self.activity_var,
                                    font=('Segoe UI', 10),
                                    bg='white', fg='#0d9648')  # Verde oscuro corporativo
        self.activity_label.pack(pady=(3, 10))
        
        # Iniciar animación del indicador
        self.animate_activity_indicator()
        
        return section_frame

    def create_info_section(self, parent):
        """Crear panel de información - COLORES CORPORATIVOS"""
        info_frame = tk.Frame(parent, bg='#f0f9f0', relief='solid', bd=1)  # Verde muy claro corporativo
        
        tk.Label(info_frame,
                text="ℹ️ Información del Proceso",
                font=('Segoe UI', 10, 'bold'),
                bg='#f0f9f0', fg='#0d9648').pack(pady=8)  # Verde oscuro corporativo
        
        info_text = ("• Se evalúan múltiples combinaciones de parámetros ARIMA\n"
                    "• Cada modelo se valida con métricas de precisión\n"
                    "• Los resultados actualizarán automáticamente los presets del selector")
        
        tk.Label(info_frame,
                text=info_text,
                font=('Segoe UI', 9),
                bg='#f0f9f0', fg='#0d9648',  # Verde oscuro corporativo
                justify='left').pack(padx=15, pady=(0, 10))
        
        return info_frame

    def create_results_section(self, parent, top_models):
        """NUEVA FUNCIÓN: Crear sección de resultados integrada - COLORES CORPORATIVOS"""
        # Crear frame principal para resultados con el mismo estilo - COLOR CORPORATIVO
        results_frame = tk.Frame(parent, bg='#f0f9f0', relief='solid', bd=1)  # Verde muy claro corporativo
        
        # Header de resultados - COLOR CORPORATIVO
        header_frame = tk.Frame(results_frame, bg='#0d9648', height=50)  # Verde oscuro corporativo
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame,
                text="🎉 RESULTADOS DE LA OPTIMIZACIÓN",
                font=('Segoe UI', 14, 'bold'),
                bg='#0d9648', fg='white').pack(pady=12)
        
        # Contenido scrollable para los resultados
        canvas = tk.Canvas(results_frame, bg='#f0f9f0', height=300)
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#f0f9f0')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Mostrar top modelos
        if len(top_models) >= 3:
            medals = ["🥇", "🥈", "🥉"]
            medal_colors = ["#ffd700", "#c0c0c0", "#cd7f32"]
            
            for i, (medal, color, model) in enumerate(zip(medals, medal_colors, top_models[:3])):
                self.create_model_card(scrollable_frame, i+1, medal, model, color)
        
        elif len(top_models) > 0:
            # Menos de 3 modelos pero al menos 1
            for i, model in enumerate(top_models):
                medal = f"#{i+1}"
                color = "#0d9648"  # Verde corporativo
                self.create_model_card(scrollable_frame, i+1, medal, model, color)
        
        # Información adicional - COLORES CORPORATIVOS
        info_frame = tk.Frame(scrollable_frame, bg='#e8f5e8', relief='solid', bd=1)  # Verde claro corporativo
        info_frame.pack(fill='x', padx=15, pady=10)
        
        tk.Label(info_frame,
                text="✅ Bridge de Parámetros Actualizado",
                font=('Segoe UI', 10, 'bold'),
                bg='#e8f5e8', fg='#0d9648').pack(pady=5)  # Verde oscuro corporativo
        
        tk.Label(info_frame,
                text="Los presets del selector de parámetros han sido actualizados automáticamente\ncon estos modelos optimizados.",
                font=('Segoe UI', 9),
                bg='#e8f5e8', fg='#0d9648',  # Verde oscuro corporativo
                justify='center').pack(pady=(0, 5))
        
        # Configurar canvas y scrollbar
        canvas.pack(side="left", fill="both", expand=True, padx=15, pady=15)
        scrollbar.pack(side="right", fill="y")
        
        return results_frame

    def create_model_card(self, parent, rank, medal, model, color):
        """Crear una tarjeta individual para cada modelo"""
        card_frame = tk.Frame(parent, bg='white', relief='solid', bd=2)
        card_frame.pack(fill='x', padx=10, pady=5)
        
        # Header de la tarjeta
        header = tk.Frame(card_frame, bg=color, height=35)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        tk.Label(header,
                text=f"{medal} MODELO #{rank}",
                font=('Segoe UI', 11, 'bold'),
                bg=color, fg='white').pack(pady=6)
        
        # Contenido de la tarjeta
        content = tk.Frame(card_frame, bg='white')
        content.pack(fill='x', padx=15, pady=10)
        
        # Información del modelo en grid
        precision = model.get('precision_final', 0)
        order = model.get('order', 'N/A')
        seasonal_order = model.get('seasonal_order', 'N/A') 
        rmse = model.get('rmse', 0)
        mape = model.get('mape', 0)
        r2_score = model.get('r2_score', 0)
        
        # Fila 1: Precisión destacada - COLOR CORPORATIVO
        precision_frame = tk.Frame(content, bg='#f0f9f0', relief='solid', bd=1)  # Verde muy claro corporativo
        precision_frame.pack(fill='x', pady=(0, 5))
        
        tk.Label(precision_frame,
                text=f"PRECISIÓN: {precision:.1f}%",
                font=('Segoe UI', 12, 'bold'),
                bg='#f0f9f0', fg='#0d9648').pack(pady=5)  # Verde oscuro corporativo
        
        # Fila 2: Parámetros
        params_frame = tk.Frame(content, bg='white')
        params_frame.pack(fill='x', pady=2)
        
        tk.Label(params_frame,
                text="Parámetros ARIMA:",
                font=('Segoe UI', 9, 'bold'),
                bg='white', fg='#374151').pack(side='left')
        
        tk.Label(params_frame,
                text=f"order={order}",
                font=('Segoe UI', 9),
                bg='white', fg='#6b7280').pack(side='right')
        
        # Fila 3: Parámetros estacionales
        seasonal_frame = tk.Frame(content, bg='white')
        seasonal_frame.pack(fill='x', pady=2)
        
        tk.Label(seasonal_frame,
                text="Estacionales:",
                font=('Segoe UI', 9, 'bold'),
                bg='white', fg='#374151').pack(side='left')
                
        tk.Label(seasonal_frame,
                text=f"seasonal_order={seasonal_order}",
                font=('Segoe UI', 9),
                bg='white', fg='#6b7280').pack(side='right')
        
        # Fila 4: Métricas adicionales
        metrics_frame = tk.Frame(content, bg='#fafafa', relief='solid', bd=1)
        metrics_frame.pack(fill='x', pady=(5, 0))
        
        metrics_text = f"RMSE: {rmse:.4f} | MAPE: {mape:.1f}% | R²: {r2_score:.3f}"
        tk.Label(metrics_frame,
                text=metrics_text,
                font=('Segoe UI', 8),
                bg='#fafafa', fg='#6b7280').pack(pady=3)
        
    def create_fixed_buttons(self, parent):
        """Crear sección de botones fija - COLORES CORPORATIVOS"""
        buttons_frame = tk.Frame(parent, bg='#f8fafc')
        buttons_frame.pack(fill='x', expand=True)
        
        # Botón cancelar (izquierda) - COLOR ROJO ARMONIOSO
        self.cancel_btn = tk.Button(buttons_frame,
                                   text="CANCELAR PROCESO",
                                   font=('Segoe UI', 10, 'bold'),
                                   bg='#dc2626', fg='white',
                                   relief='flat', padx=20, pady=8,
                                   cursor='hand2',
                                   command=self.cancel_process)
        self.cancel_btn.pack(side='left')
        
        # Botón cerrar (derecha) - COLOR CORPORATIVO GRIS
        self.close_btn = tk.Button(buttons_frame,
                                  text="CERRAR",
                                  font=('Segoe UI', 10, 'bold'),
                                  bg='#a1a1a5', fg='white',  # Color corporativo gris
                                  relief='flat', padx=20, pady=8,
                                  cursor='hand2', state='disabled',
                                  command=self.close_window)
        self.close_btn.pack(side='right')

    def animate_activity_indicator(self):
        """Animar el indicador de actividad"""
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
                
            if self.animation_running and hasattr(self, 'window') and self.window.winfo_exists():
                self.window.after(200, self.animate_activity_indicator)
                
        except Exception as e:
            print(f"Error en animación: {e}")
            self.animation_running = False

    def update_progress(self, percentage, status, current_model="", iteration_info=""):
        """Actualizar la información de progreso"""
        # Si está cancelado, no actualizar más
        if self.cancelled:
            return
            
        try:
            self.percentage_var.set(f"{percentage:.1f}%")
            self.progress_bar['value'] = percentage
            self.iteration_var.set(status if status else "Procesando...")
            
            if current_model:
                self.current_model_var.set(f"Evaluando: {current_model}")
            
            self.window.update_idletasks()
            
        except Exception as e:
            print(f"Error actualizando progreso: {e}")

    # ====== MÉTODOS MODIFICADOS PARA INTEGRAR RESULTADOS ======
    
    def check_and_show_results(self):
        """Verificar si hay resultados y mostrarlos EN LA MISMA INTERFAZ"""
        try:
            # Importar datos globales
            global PROGRESS_DATA
            
            if PROGRESS_DATA.get('top_models') and len(PROGRESS_DATA['top_models']) > 0:
                print(f"check_and_show_results: Encontrados {len(PROGRESS_DATA['top_models'])} modelos")
                self.show_results(PROGRESS_DATA['top_models'])
            else:
                print("check_and_show_results: No hay modelos disponibles para mostrar")
                # Mostrar mensaje de finalización sin resultados
                self.show_completion_message()
                
        except Exception as e:
            print(f"Error en check_and_show_results: {e}")
            self.show_completion_message()

    def show_results(self, top_models):
        """MÉTODO MODIFICADO: Transformar la interfaz para mostrar resultados - COLORES CORPORATIVOS"""
        try:
            if self.results_shown:
                return
                
            self.results_shown = True
            self.animation_running = False
            
            print(f"show_results: Transformando interfaz para mostrar {len(top_models)} modelos")
            
            # PASO 1: Actualizar header - COLOR CORPORATIVO
            self.title_label.config(text="✅ Optimización Completada Exitosamente",
                                   bg='#0d9648')  # Verde oscuro corporativo
            self.header_frame.config(bg='#0d9648')
            
            # PASO 2: Ocultar sección de progreso
            self.progress_section.pack_forget()
            
            # PASO 3: Ocultar sección de información
            self.info_section.pack_forget()
            
            # PASO 4: Crear y mostrar sección de resultados
            self.results_section = self.create_results_section(self.main_container, top_models)
            self.results_section.pack(fill='both', expand=True, pady=(0, 15))
            
            # PASO 5: Actualizar botones - COLORES CORPORATIVOS
            self.cancel_btn.configure(
                state='disabled',
                bg='#a1a1a5',  # Color corporativo gris
                text="COMPLETADO"
            )
            
            self.close_btn.configure(
                state='normal',
                bg='#0d9648',  # Verde oscuro corporativo
                text="CERRAR RESULTADOS"
            )
            
            # PASO 6: Actualizar bridge
            self.update_bridge_with_results(top_models)
            
            # PASO 7: Redimensionar ventana si es necesario
            # PASO 7: Redimensionar ventana si es necesario
            self.window.update_idletasks()
            x = (self.window.winfo_screenwidth() // 2) - 325  # 650/2 = 325
            y = max(30, (self.window.winfo_screenheight() // 2) - 475)  # 375 + 100 = 475 (sube 100px más)
            self.window.geometry(f"650x750+{x}+{y}")
                        
            print("✅ Interfaz transformada exitosamente para mostrar resultados")
            
        except Exception as e:
            print(f"Error en show_results: {e}")
            self.show_completion_message()

    def show_completion_message(self):
        """Mostrar mensaje de finalización simple transformando la interfaz - COLORES CORPORATIVOS"""
        try:
            self.results_shown = True
            self.animation_running = False
            
            # Actualizar header - COLOR CORPORATIVO GRIS
            self.title_label.config(text="✅ Proceso Completado",
                                   bg='#a1a1a5')  # Color corporativo gris
            self.header_frame.config(bg='#a1a1a5')
            
            # Ocultar progreso e info
            self.progress_section.pack_forget()
            self.info_section.pack_forget()
            
            # Crear mensaje simple
            completion_frame = tk.Frame(self.main_container, bg='#f3f4f6', relief='solid', bd=1)
            completion_frame.pack(fill='both', expand=True, pady=(0, 15))
            
            tk.Label(completion_frame,
                    text="Proceso de optimización completado",
                    font=('Segoe UI', 14, 'bold'),
                    bg='#f3f4f6', fg='#374151').pack(pady=50)
            
            tk.Label(completion_frame,
                    text="No se encontraron suficientes modelos para mostrar resultados detallados.",
                    font=('Segoe UI', 10),
                    bg='#f3f4f6', fg='#6b7280').pack(pady=10)
            
            # Actualizar botones - COLORES CORPORATIVOS
            self.cancel_btn.configure(
                state='disabled',
                bg='#a1a1a5',  # Color corporativo gris
                text="COMPLETADO"
            )
            
            self.close_btn.configure(
                state='normal',
                bg='#a1a1a5',  # Color corporativo gris
                text="CERRAR"
            )
            
        except Exception as e:
            print(f"Error en show_completion_message: {e}")

    def update_bridge_with_results(self, top_models):
        """Actualizar bridge de parámetros con los resultados"""
        try:
            # Verificar si el bridge está disponible
            global BRIDGE_AVAILABLE
            
            if BRIDGE_AVAILABLE and len(top_models) >= 3:
                print("Actualizando bridge de parámetros...")
                
                # Importar bridge functions
                try:
                    from backend.parametros_bridge import save_top_models_to_bridge
                    success = save_top_models_to_bridge(top_models)
                    
                    if success:
                        print("✓ Bridge actualizado correctamente")
                    else:
                        print("⚠ Error actualizando bridge")
                        
                except Exception as bridge_error:
                    print(f"Error importando/ejecutando bridge: {bridge_error}")
            else:
                print(f"Bridge no disponible o insuficientes modelos: {len(top_models)}")
                
        except Exception as e:
            print(f"Error en update_bridge_with_results: {e}")

    def on_window_close(self):
        """Manejar cierre de ventana con X"""
        if not self.cancelled and not self.results_shown:
            if messagebox.askyesno("Cerrar Ventana", 
                                  "El proceso de optimización está en curso.\n\n"
                                  "¿Desea cancelar el proceso y cerrar la ventana?"):
                self.cancel_process()
                self.close_window()
        else:
            self.close_window()
            
    def close_window(self):
        """Cerrar ventana de progreso"""
        print("Cerrando ventana de progreso...")
        self.animation_running = False
        
        # Limpiar archivos de cancelación al cerrar
        try:
            if os.path.exists(self.cancel_file):
                os.remove(self.cancel_file)
                print(f"✓ Archivo de cancelación limpiado: {self.cancel_file}")
        except:
            pass
        
        try:
            self.window.destroy()
        except:
            pass

# FUNCIÓN DE UTILIDAD MEJORADA
def create_progress_window(parent, progress_file=None):
    """Función de utilidad para crear ventana de progreso desde otros módulos"""
    return ProgressWindow(parent, "Optimización de Parámetros", progress_file)