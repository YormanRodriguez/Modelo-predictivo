# ParametroV.py - Corrección del sistema de cancelación
import tkinter as tk
from tkinter import ttk, messagebox
import os
import json
from datetime import datetime
import tempfile

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
    
    def __init__(self, parent, title="Optimización de Parámetros", progress_file=None):
        self.parent = parent
        self.cancelled = False
        self.animation_running = True
        self.results_shown = False
        self.bridge_updated = False
        
        # CORRECCIÓN CRÍTICA: Asegurar que progress_file sea válido
        if progress_file and os.path.dirname(progress_file):
            self.progress_file = progress_file
        else:
            # Crear archivo temporal en directorio válido
            self.progress_file = tempfile.mktemp(suffix='_progress.json', prefix='saidi_')
            print(f"⚠ Progress file corregido: {self.progress_file}")
            
        # NUEVA VARIABLE: Archivo de cancelación específico
        self.cancel_file = self.progress_file.replace('.json', '_cancel.json')
        
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
                print(f"✓ Archivo de cancelación previo eliminado: {self.cancel_file}")
        except Exception as e:
            print(f"⚠ Error limpiando archivos previos: {e}")
        
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
        
        # MODIFICADO: Manejar el cierre de ventana con mejor lógica
        self.window.protocol("WM_DELETE_WINDOW", self.on_window_close)
        
    def create_cancellation_file(self):
        """FUNCIÓN CORREGIDA: Crear archivo de cancelación con validación robusta"""
        try:
            # Verificar que el directorio base existe
            cancel_dir = os.path.dirname(self.cancel_file)
            if not cancel_dir:  # Si no hay directorio, usar temp
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
            
            print(f"✓ Archivo de cancelación creado: {self.cancel_file}")
            return True
            
        except PermissionError as e:
            print(f"✗ Error de permisos creando archivo de cancelación: {e}")
            # Intentar crear en directorio temporal como fallback
            try:
                fallback_file = tempfile.mktemp(suffix='_cancel_fallback.json', prefix='saidi_')
                with open(fallback_file, 'w', encoding='utf-8') as f:
                    json.dump(cancel_data, f, ensure_ascii=False, indent=2)
                self.cancel_file = fallback_file
                print(f"✓ Archivo de cancelación creado en fallback: {fallback_file}")
                return True
            except Exception as fallback_error:
                print(f"✗ Error en fallback: {fallback_error}")
                return False
                
        except Exception as e:
            print(f"✗ Error inesperado creando archivo de cancelación: {e}")
            return False

    def cancel_process(self):
        """FUNCIÓN CORREGIDA: Cancelar el proceso con manejo robusto de errores"""
        if messagebox.askyesno("Confirmar Cancelación", 
                              "¿Está seguro que desea cancelar el proceso de optimización?\n\n"
                              "Esto detendrá inmediatamente todas las iteraciones en curso."):
            
            print("🚫 Usuario solicitó cancelación del proceso")
            
            # Marcar como cancelado localmente PRIMERO
            self.cancelled = True
            self.animation_running = False
            
            # Intentar crear archivo de cancelación
            cancel_success = self.create_cancellation_file()
            
            # ACTUALIZAR INTERFAZ INMEDIATAMENTE (independiente del éxito del archivo)
            self.update_cancellation_ui()
            
            if cancel_success:
                # Mostrar mensaje de éxito
                messagebox.showinfo("Proceso Cancelado", 
                                   "🚫 Solicitud de cancelación enviada correctamente.\n\n"
                                   "Las iteraciones se detendrán en los próximos momentos.\n"
                                   "Puede cerrar esta ventana cuando lo desee.")
                print("✓ Cancelación procesada exitosamente")
            else:
                # Mostrar advertencia pero permitir continuar
                messagebox.showwarning("Cancelación con Limitaciones",
                                     "⚠ No se pudo crear el archivo de cancelación automática.\n\n"
                                     "Sin embargo, el proceso ha sido marcado como cancelado localmente.\n"
                                     "Si el proceso continúa, puede cerrar la aplicación principal para detenerlo.")
                print("⚠ Cancelación procesada con limitaciones")

    def update_cancellation_ui(self):
        """NUEVA FUNCIÓN: Actualizar interfaz para mostrar cancelación"""
        try:
            # Actualizar indicadores visuales
            self.percentage_var.set("CANCELADO")
            self.iteration_var.set("🚫 Proceso cancelado por el usuario")
            self.current_model_var.set("Deteniendo iteraciones y limpiando recursos...")
            self.activity_var.set("⚠️")
            
            # Actualizar botones
            self.cancel_btn.configure(
                state='disabled', 
                bg='#9ca3af', 
                text="CANCELADO"
            )
            
            self.close_btn.configure(
                state='normal', 
                bg='#ef4444',
                text="CERRAR (CANCELADO)"
            )
            
            # Actualizar barra de progreso para mostrar cancelación
            try:
                self.progress_bar.configure(style='Cancelled.Horizontal.TProgressbar')
                style = ttk.Style()
                style.configure('Cancelled.Horizontal.TProgressbar',
                            troughcolor='#fee2e2',
                            background='#ef4444',
                            borderwidth=0)
            except:
                pass  # Continuar aunque falle el estilo
                
            print("✓ Interfaz de cancelación actualizada")
            
        except Exception as e:
            print(f"⚠ Error actualizando interfaz de cancelación: {e}")

    # [Resto de métodos permanecen igual - solo agrego el método create_interface y otros necesarios para completitud]
    
    def create_interface(self):
        """Crear la interfaz de progreso"""
        # Header con gradiente simulado
        header_frame = tk.Frame(self.window, bg='#f59e0b', height=60)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, 
                              text="Optimización de Parámetros ARIMA",
                              font=('Segoe UI', 16, 'bold'),
                              bg='#f59e0b', fg='white')
        title_label.pack(pady=(10, 5))
        
        # Frame principal contenedor
        main_container = tk.Frame(self.window, bg='#f8fafc')
        main_container.pack(fill='both', expand=True, padx=20, pady=15)
        
        # Sección de progreso
        progress_section = self.create_progress_section(main_container)
        progress_section.pack(fill='x', pady=(0, 15))
        
        # Sección de información
        info_section = self.create_info_section(main_container)
        info_section.pack(fill='x', pady=(0, 15))
        
        # Botones
        buttons_container = tk.Frame(main_container, bg='#f8fafc', height=50)
        buttons_container.pack(fill='x', side='bottom', pady=(15, 0))
        buttons_container.pack_propagate(False)
        
        self.create_fixed_buttons(buttons_container)
        
    def create_progress_section(self, parent):
        """Crear la sección de progreso"""
        section_frame = tk.Frame(parent, bg='white', relief='solid', bd=1)
        
        # Título de sección
        tk.Label(section_frame, 
                text="Progreso de Evaluación",
                font=('Segoe UI', 12, 'bold'),
                bg='white', fg='#1f2937').pack(pady=8)
        
        # Porcentaje grande
        self.percentage_var = tk.StringVar(value="0%")
        self.percentage_label = tk.Label(section_frame,
                                        textvariable=self.percentage_var,
                                        font=('Segoe UI', 36, 'bold'),
                                        bg='white', fg='#2563eb')
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
        
        # Indicador visual de actividad
        self.activity_var = tk.StringVar(value="●")
        self.activity_label = tk.Label(section_frame,
                                    textvariable=self.activity_var,
                                    font=('Segoe UI', 10),
                                    bg='white', fg='#10b981')
        self.activity_label.pack(pady=(3, 10))
        
        # Iniciar animación del indicador
        self.animate_activity_indicator()
        
        return section_frame

    def create_info_section(self, parent):
        """Crear panel de información"""
        info_frame = tk.Frame(parent, bg='#fef3c7', relief='solid', bd=1)
        
        tk.Label(info_frame,
                text="ℹ️ Información del Proceso",
                font=('Segoe UI', 10, 'bold'),
                bg='#fef3c7', fg='#92400e').pack(pady=8)
        
        info_text = ("• Se evalúan múltiples combinaciones de parámetros ARIMA\n"
                    "• Cada modelo se valida con métricas de precisión\n"
                    "• Los resultados actualizarán automáticamente los presets del selector")
        
        tk.Label(info_frame,
                text=info_text,
                font=('Segoe UI', 9),
                bg='#fef3c7', fg='#92400e',
                justify='left').pack(padx=15, pady=(0, 10))
        
        return info_frame
        
    def create_fixed_buttons(self, parent):
        """Crear sección de botones fija"""
        buttons_frame = tk.Frame(parent, bg='#f8fafc')
        buttons_frame.pack(fill='x', expand=True)
        
        # Botón cancelar (izquierda)
        self.cancel_btn = tk.Button(buttons_frame,
                                   text="CANCELAR PROCESO",
                                   font=('Segoe UI', 10, 'bold'),
                                   bg='#ef4444', fg='white',
                                   relief='flat', padx=20, pady=8,
                                   cursor='hand2',
                                   command=self.cancel_process)
        self.cancel_btn.pack(side='left')
        
        # Botón cerrar (derecha)
        self.close_btn = tk.Button(buttons_frame,
                                  text="CERRAR",
                                  font=('Segoe UI', 10, 'bold'),
                                  bg='#6b7280', fg='white',
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