# Codigo antes de crear modulos
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog, messagebox
from statsmodels.tsa.statespace.sarimax import SARIMAX
import numpy as np
from sklearn.metrics import mean_squared_error

def cargar_excel():
    """Abrir un cuadro de diálogo para seleccionar el archivo Excel."""
    root = tk.Tk()
    root.withdraw()  
    file_path = filedialog.askopenfilename(
        title="Seleccionar archivo Excel - Gráfica de Validación SAIDI",
        filetypes=[("Archivos Excel", "*.xlsx *.xls")]
    )
    if not file_path:
        messagebox.showerror("Error", "No se seleccionó ningún archivo.")
        return None
    return file_path

def calcular_metricas_validacion(datos_reales, predicciones):
    """Calcula las métricas de validación del modelo usando la MISMA fórmula del script principal."""
    rmse = np.sqrt(mean_squared_error(datos_reales, predicciones))
    mae = np.mean(np.abs(datos_reales - predicciones))
    
    # Calcular MAPE (Error Porcentual Absoluto Medio) - IGUAL que el script principal
    epsilon = 1e-8
    mape = np.mean(np.abs((datos_reales - predicciones) / (datos_reales + epsilon))) * 100
    
    # Calcular R² para validación - IGUAL que el script principal
    ss_res = np.sum((datos_reales - predicciones) ** 2)
    ss_tot = np.sum((datos_reales - np.mean(datos_reales)) ** 2)
    r2_score = 1 - (ss_res / (ss_tot + epsilon))
    
    # Calcular porcentaje de precisión - EXACTAMENTE IGUAL que el script principal
    precision_mape = max(0, 100 - mape)
    precision_r2 = max(0, r2_score * 100)
    mean_actual = np.mean(datos_reales)
    precision_rmse = max(0, (1 - rmse/mean_actual) * 100)
    
    # Precisión compuesta - MISMA PONDERACIÓN que el script principal
    precision_final = (precision_mape * 0.4 + precision_r2 * 0.4 + precision_rmse * 0.2)
    precision_final = max(0, min(100, precision_final))
    
    return {
        'rmse': rmse,
        'mae': mae,
        'mape': mape,
        'r2_score': r2_score,
        'precision_mape': precision_mape,
        'precision_r2': precision_r2,
        'precision_rmse': precision_rmse,
        'precision_final': precision_final
    }

def generar_grafica_validacion(file_path):
    """Genera la gráfica de validación del modelo SARIMAX."""
    try:
        # === Cargar datos ===
        df = pd.read_excel(file_path, sheet_name="Hoja1")
        print("Columnas encontradas en el Excel:", df.columns.tolist())

        # Detectar columna de fecha
        if "Fecha" in df.columns:
            df["Fecha"] = pd.to_datetime(df["Fecha"])
            df.set_index("Fecha", inplace=True)
        else:
            df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0])
            df.set_index(df.columns[0], inplace=True)

        # Detectar columna de SAIDI
        col_saidi = "SAIDI" if "SAIDI" in df.columns else "SAIDI Histórico"
        if col_saidi not in df.columns:
            messagebox.showerror("Error", "No se encontró la columna SAIDI ni SAIDI Histórico.")
            return

        # Obtener solo datos históricos (sin NaN)
        historico = df[df[col_saidi].notna()]
        
        if len(historico) < 12:
            messagebox.showerror("Error", "Se necesitan al menos 12 observaciones históricas para el análisis.")
            return

        print(f"\nDataset: {len(historico)} observaciones desde {historico.index[0].strftime('%Y-%m')} hasta {historico.index[-1].strftime('%Y-%m')}")

        # === Dividir datos: 70% entrenamiento, 30% validación ===
        if len(historico) >= 60:  # 5+ años
            pct_validacion = 0.30
        elif len(historico) >= 36:  # 3-5 años
            pct_validacion = 0.25
        else:  # Menos de 3 años
            pct_validacion = 0.20
            
        n_test = max(6, int(len(historico) * pct_validacion))
        datos_entrenamiento = historico[col_saidi][:-n_test]
        datos_validacion = historico[col_saidi][-n_test:]
        
        print(f"División: {len(datos_entrenamiento)} datos entrenamiento, {len(datos_validacion)} datos validación")
        print(f"Porcentaje validación: {pct_validacion*100:.0f}%")

        # === Entrenar modelo con parámetros fijos ===
        order = (4, 0, 0)
        seasonal_order = (1, 0, 0, 8)
        
        print(f"\nEntrenando modelo SARIMAX con:")
        print(f"order = {order}")
        print(f"seasonal_order = {seasonal_order}")
        
        # Ajustar modelo con datos de entrenamiento
        model = SARIMAX(
            datos_entrenamiento,
            order=order,
            seasonal_order=seasonal_order,
            enforce_stationarity=False,
            enforce_invertibility=False
        )
        results = model.fit(disp=False)
        
        # Hacer predicciones para el período de validación
        pred = results.get_forecast(steps=n_test)
        predicciones_validacion = pred.predicted_mean
        
        # Calcular métricas
        metricas = calcular_metricas_validacion(datos_validacion.values, predicciones_validacion.values)
        
        print(f"\n=== MÉTRICAS DEL MODELO (MISMAS QUE LA INTERFAZ) ===")
        print(f"RMSE: {metricas['rmse']:.4f}")
        print(f"MAE: {metricas['mae']:.4f}")
        print(f"MAPE: {metricas['mape']:.1f}%")
        print(f"R²: {metricas['r2_score']:.3f}")
        print(f"PRECISIÓN FINAL: {metricas['precision_final']:.1f}%")
        print(f"├─ Componente MAPE: {metricas['precision_mape']:.1f}%")
        print(f"├─ Componente R²: {metricas['precision_r2']:.1f}%") 
        print(f"└─ Componente RMSE: {metricas['precision_rmse']:.1f}%")

        # === CREAR GRÁFICA DE VALIDACIÓN CON CONEXIÓN VISUAL ===
        plt.figure()  # crea la figura sin forzar tamaño fijo

        # Obtener el manejador de la ventana
        mng = plt.get_current_fig_manager()

        try:
         # Opción 1: En Windows con backend TkAgg
            mng.window.state('zoomed')   # maximiza la ventana

        except Exception:
            try:
                # Opción 2: En backends como Qt5Agg
                mng.window.showMaximized()
            except Exception:
                # Opción 3: método genérico de Matplotlib
                mng.full_screen_toggle()

        # Línea azul sólida: Datos de entrenamiento (70%)
        plt.plot(datos_entrenamiento.index, datos_entrenamiento.values, 
                label=f"Datos de Entrenamiento (70% - {len(datos_entrenamiento)} obs.)", 
                color="blue", linewidth=3, marker='o', markersize=5)

        # === SOLUCIÓN PARA CONEXIÓN VISUAL ===
        # Obtener el último punto de entrenamiento
        ultimo_punto_entrenamiento = datos_entrenamiento.iloc[-1]
        fecha_ultimo_entrenamiento = datos_entrenamiento.index[-1]
        
        # Crear arrays extendidos que incluyan el punto de conexión
        # Para datos reales de validación: agregar el último punto de entrenamiento al inicio
        fechas_validacion_extendidas = [fecha_ultimo_entrenamiento] + list(datos_validacion.index)
        valores_validacion_extendidos = [ultimo_punto_entrenamiento] + list(datos_validacion.values)
        
        # Para predicciones: agregar el último punto de entrenamiento al inicio
        valores_prediccion_extendidos = [ultimo_punto_entrenamiento] + list(predicciones_validacion.values)

        # Línea azul punteada: Datos reales de validación (30%) - CON CONEXIÓN
        plt.plot(fechas_validacion_extendidas, valores_validacion_extendidos, 
                label=f"Datos Reales de Validación (30% - {len(datos_validacion)} obs.)", 
                color="navy", linewidth=3, linestyle=':', marker='s', markersize=7)

        # Línea naranja: Predicciones del modelo - CON CONEXIÓN
        plt.plot(fechas_validacion_extendidas, valores_prediccion_extendidos, 
                label=f"Predicciones del Modelo", 
                color="orange", linewidth=3, marker='^', markersize=7)

        # Etiquetas para puntos de entrenamiento (más espaciadas)
        for i, (x, y) in enumerate(zip(datos_entrenamiento.index, datos_entrenamiento.values)):
            if i % max(1, len(datos_entrenamiento)//6) == 0:  # Menos etiquetas
                plt.text(x, y+0.3, f"{y:.1f}", color="blue", fontsize=9, 
                        ha='center', va='bottom', rotation=0, alpha=0.8, weight='bold')

        # Etiquetas para datos de validación reales (sin incluir el punto de conexión)
        for x, y in zip(datos_validacion.index, datos_validacion.values):
            plt.text(x, y+0.4, f"{y:.1f}", color="navy", fontsize=10, 
                    ha='center', va='bottom', rotation=0, weight='bold')

        # Etiquetas para predicciones (sin incluir el punto de conexión)
        for x, y in zip(predicciones_validacion.index, predicciones_validacion.values):
            plt.text(x, y-0.5, f"{y:.1f}", color="orange", fontsize=10, 
                    ha='center', va='top', rotation=0, weight='bold')

        # Área sombreada para resaltar diferencias - INCLUYENDO EL PUNTO DE CONEXIÓN
        plt.fill_between(fechas_validacion_extendidas, 
                        valores_validacion_extendidos, 
                        valores_prediccion_extendidos,
                        alpha=0.2, color='red', 
                        label='Área de Error')

        # Línea vertical que separa entrenamiento de validación
        separacion_x = datos_entrenamiento.index[-1]
        plt.axvline(x=separacion_x, color='gray', linestyle='--', alpha=0.8, linewidth=2)
        
        # Posicionar etiqueta de división más arriba
        y_pos = plt.ylim()[1] * 0.70
        plt.text(separacion_x, y_pos, 'División\nEntrenamiento/Validación', 
                ha='center', va='center', color='gray', fontsize=12, weight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgray', alpha=0.9, edgecolor='gray'))

        # Cuadro de métricas - posición superior izquierda
        info_metricas = (f"MÉTRICAS DEL MODELO\n"
                        f"• RMSE: {metricas['rmse']:.3f}\n"
                        f"• MAE: {metricas['mae']:.3f}\n"
                        f"• MAPE: {metricas['mape']:.1f}%\n"
                        f"• R²: {metricas['r2_score']:.3f}\n"
                        f"• Precisión Final: {metricas['precision_final']:.1f}%")
        
        plt.text(0.009, 0.3, info_metricas, transform=plt.gca().transAxes, 
                fontsize=11, verticalalignment='top', 
                bbox=dict(boxstyle='round,pad=0.8', facecolor='lightblue', alpha=0.9, edgecolor='navy'))

        # Cuadro de componentes de precisión - posición inferior izquierda
        info_componentes = (f"COMPONENTES DE PRECISIÓN\n"
                           f"• Por MAPE: {metricas['precision_mape']:.1f}%\n"
                           f"• Por R²: {metricas['precision_r2']:.1f}%\n" 
                           f"• Por RMSE: {metricas['precision_rmse']:.1f}%\n"
                           f"Formula: (MAPE×0.4 + R²×0.4 + RMSE×0.2)")
        
        plt.text(0.007, 0.12, info_componentes, transform=plt.gca().transAxes, 
                fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round,pad=0.6', facecolor='wheat', alpha=0.9, edgecolor='orange'))

        # Cuadro de parámetros - posición inferior derecha
        info_parametros = (f"PARÁMETROS DEL MODELO\n"
                          f"• order = {order}\n"
                          f"• seasonal_order = {seasonal_order}\n"
                          f"• Entrenamiento: {len(datos_entrenamiento)} obs.\n"
                          f"• Validación: {len(datos_validacion)} obs.")
        
        plt.text(0.995, 0.119, info_parametros, transform=plt.gca().transAxes, 
                fontsize=10, verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round,pad=0.6', facecolor='lightgreen', alpha=0.9, edgecolor='green'))

        # Calificación del modelo - posición superior derecha
        precision = metricas['precision_final']
        if precision >= 90:
            interpretacion = "EXCELENTE"
            color_interp = "green"
        elif precision >= 80:
            interpretacion = "BUENO" 
            color_interp = "limegreen"
        elif precision >= 70:
            interpretacion = "ACEPTABLE"
            color_interp = "orange"
        elif precision >= 60:
            interpretacion = "REGULAR"
            color_interp = "red"
        else:
            interpretacion = "BAJO"
            color_interp = "darkred"

        plt.text(0.99, 0.979, f"CALIFICACIÓN\n{interpretacion}\n{precision:.1f}%", 
                transform=plt.gca().transAxes, fontsize=14, weight='bold',
                verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round,pad=0.8', facecolor=color_interp, alpha=0.8, edgecolor='black'),
                color='black')

        # Configuración del gráfico principal
        plt.title(f"Validación del Modelo SARIMAX - Análisis de Precisión", 
                 fontsize=17, fontweight='bold', pad=25)
        
        plt.xlabel("Fecha", fontsize=14, weight='bold')
        plt.ylabel("SAIDI (minutos)", fontsize=14, weight='bold')
        
        # Leyenda en posición central-superior
        plt.legend(fontsize=12, loc='upper center', bbox_to_anchor=(0.85, -0.04), 
                  ncol=2, frameon=True, shadow=True, fancybox=True)
        
        # Grid mejorado
        plt.grid(True, alpha=0.4, linestyle='-', linewidth=0.8)
        
        # Mejorar las etiquetas del eje X
        plt.xticks(fontsize=11, rotation=0)
        plt.yticks(fontsize=11)
        
        # Ajustar márgenes para aprovechar el espacio
        plt.tight_layout()
        plt.subplots_adjust(top=0.90, bottom=0.12, left=0.08, right=0.92)
        
        # Texto explicativo en la parte inferior - más prominente
        plt.figtext(0.3, 0.04, 
                   "Entre más cerca estén las líneas azul punteada (real) y naranja (predicha), mejor es el modelo", 
                   ha='center', fontsize=13, style='italic', color='darkblue', weight='bold',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow', alpha=0.8))
        
        plt.show()

        # === RESUMEN EN CONSOLA ===
        print(f"\n" + "="*70)
        print("RESUMEN DE VALIDACIÓN DEL MODELO")
        print("="*70)
        print(f"Período de entrenamiento: {datos_entrenamiento.index[0].strftime('%Y-%m')} a {datos_entrenamiento.index[-1].strftime('%Y-%m')}")
        print(f"Período de validación: {datos_validacion.index[0].strftime('%Y-%m')} a {datos_validacion.index[-1].strftime('%Y-%m')}")
        print(f"Precisión del modelo: {precision:.1f}% - {interpretacion}")
        print(f"Error promedio (MAE): {metricas['mae']:.3f} minutos")
        print(f"Error cuadrático (RMSE): {metricas['rmse']:.3f}")
        print(f"Correlación (R²): {metricas['r2_score']:.3f}")
        print(f"Error porcentual (MAPE): {metricas['mape']:.1f}%")
        
        print(f"\nINTERPRETACIÓN:")
        print(f"   El modelo predice con {precision:.1f}% de precisión")
        print(f"   En promedio se equivoca por {metricas['mae']:.2f} minutos")
        
        if precision >= 70:
            print("El modelo es confiable para hacer predicciones futuras")
        else:
            print("El modelo tiene baja precisión, usar con precaución")
        
        print("="*70)

    except Exception as e:
        messagebox.showerror("Error", f"Ocurrió un error: {str(e)}")
        print(f"Error detallado: {str(e)}")

def main():
    """Función principal."""
    print("GENERADOR DE GRÁFICA DE VALIDACIÓN SAIDI")
    print("="*50)
    print("Este script genera una gráfica que muestra qué tan bien")
    print("el modelo predice datos históricos conocidos.")
    print("="*50)
    
    archivo = cargar_excel()
    if archivo:
        generar_grafica_validacion(archivo)
    else:
        print("No se seleccionó ningún archivo.")

if __name__ == "__main__":
    main()