# backend/visual.py - Script de Validación con Parámetros Dinámicos
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MaxNLocator
import argparse
import sys
import os
from statsmodels.tsa.statespace.sarimax import SARIMAX
import numpy as np
from sklearn.metrics import mean_squared_error


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


def generar_grafica_validacion(file_path, order=(4, 0, 0), seasonal_order=(1, 0, 0, 8)):
    """Genera la gráfica de validación del modelo SARIMAX con parámetros dinámicos."""
    try:
        print(f"Generando gráfica de validación para: {file_path}")
        print(f"Parámetros SARIMAX: order={order}, seasonal_order={seasonal_order}")
        
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
            print("ERROR: No se encontró la columna SAIDI ni SAIDI Histórico.")
            sys.exit(1)

        # Obtener solo datos históricos (sin NaN)
        historico = df[df[col_saidi].notna()]
        
        if len(historico) < 12:
            print("ERROR: Se necesitan al menos 12 observaciones históricas para el análisis.")
            sys.exit(1)

        print(f"\nDataset: {len(historico)} observaciones desde {historico.index[0].strftime('%Y-%m')} hasta {historico.index[-1].strftime('%Y-%m')}")

        # === Dividir datos: basado en cantidad de datos disponibles ===
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

        # === Entrenar modelo con parámetros dinámicos ===
        print(f"\nEntrenando modelo SARIMAX con:")
        print(f"order = {order}")
        print(f"seasonal_order = {seasonal_order}")
        
        # Ajustar modelo con datos de entrenamiento
        try:
            model = SARIMAX(
                datos_entrenamiento,
                order=order,
                seasonal_order=seasonal_order,
                enforce_stationarity=False,
                enforce_invertibility=False
            )
            results = model.fit(disp=False)
            print("✓ Modelo ajustado exitosamente")
        except Exception as e:
            print(f"ERROR: No se pudo ajustar el modelo: {e}")
            print("Los parámetros seleccionados pueden no ser compatibles con los datos.")
            sys.exit(1)
        
        # Hacer predicciones para el período de validación
        try:
            pred = results.get_forecast(steps=n_test)
            predicciones_validacion = pred.predicted_mean
            print(f"✓ Predicciones de validación generadas para {len(predicciones_validacion)} períodos")
        except Exception as e:
            print(f"ERROR: No se pudieron generar predicciones: {e}")
            sys.exit(1)
        
        # Calcular métricas
        metricas = calcular_metricas_validacion(datos_validacion.values, predicciones_validacion.values)
        
        print(f"\n=== MÉTRICAS DEL MODELO ===")
        print(f"RMSE: {metricas['rmse']:.4f}")
        print(f"MAE: {metricas['mae']:.4f}")
        print(f"MAPE: {metricas['mape']:.1f}%")
        print(f"R²: {metricas['r2_score']:.3f}")
        print(f"PRECISIÓN FINAL: {metricas['precision_final']:.1f}%")
        print(f"├─ Componente MAPE: {metricas['precision_mape']:.1f}%")
        print(f"├─ Componente R²: {metricas['precision_r2']:.1f}%") 
        print(f"└─ Componente RMSE: {metricas['precision_rmse']:.1f}%")

        # === CREAR GRÁFICA DE VALIDACIÓN EN PANTALLA COMPLETA FIJA ===
        # Crear figura con tamaño optimizado para pantalla completa
        fig = plt.figure(figsize=(16, 10))
        
        # Forzar pantalla completa de manera segura sin errores
        mng = fig.canvas.manager
        try:
            # Para TkAgg (Windows/Linux) - más común y estable
            if hasattr(mng, 'window') and hasattr(mng.window, 'state'):
                # Maximizar ventana
                mng.window.state('zoomed')
                
                # Intentar deshabilitar redimensionamiento de manera segura
                try:
                    mng.window.resizable(False, False)
                except:
                    # Si no se puede deshabilitar redimensionamiento, continuar
                    print("Info: La ventana se maximizó pero puede ser redimensionable")
                    
            # Para Qt backends (solo si están disponibles)
            elif hasattr(mng, 'window') and hasattr(mng.window, 'showMaximized'):
                mng.window.showMaximized()
                
                # Intentar fijar tamaño solo si Qt está disponible
                try:
                    # Verificar si QtCore está disponible antes de importar
                    import sys
                    if 'PyQt5' in sys.modules or 'PyQt4' in sys.modules or 'PySide' in sys.modules:
                        mng.window.setFixedSize(mng.window.size())
                except ImportError:
                    # Qt no está disponible, usar alternativa
                    pass
                except:
                    # Cualquier otro error de Qt, continuar sin fijar tamaño
                    pass
            
            # Para otros backends
            else:
                # Intentar maximizar de forma genérica
                if hasattr(mng, 'full_screen_toggle'):
                    mng.full_screen_toggle()
                    
        except Exception as e:
            print(f"Info: Usando configuración de ventana estándar (no se pudo configurar pantalla completa): {e}")
            # Continuar normalmente sin pantalla completa forzada

        # Línea azul sólida: Datos de entrenamiento
        plt.plot(datos_entrenamiento.index, datos_entrenamiento.values, 
                label=f"Datos de Entrenamiento ({100-int(pct_validacion*100)}% - {len(datos_entrenamiento)} obs.)", 
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

        # Línea azul punteada: Datos reales de validación - CON CONEXIÓN
        plt.plot(fechas_validacion_extendidas, valores_validacion_extendidos, 
                label=f"Datos Reales de Validación ({int(pct_validacion*100)}% - {len(datos_validacion)} obs.)", 
                color="navy", linewidth=3, linestyle=':', marker='s', markersize=7)

        # Línea naranja: Predicciones del modelo - CON CONEXIÓN
        plt.plot(fechas_validacion_extendidas, valores_prediccion_extendidos, 
                label="Predicciones del Modelo", 
                color="orange", linewidth=3, marker='^', markersize=7)

        # Etiquetas para puntos de entrenamiento (más espaciadas)
        for i, (x, y) in enumerate(zip(datos_entrenamiento.index, datos_entrenamiento.values)):
            if i % max(1, len(datos_entrenamiento)//6) == 0:  # Menos etiquetas
                plt.text(x, y+0.3, f"{y:.1f}", color="blue", fontsize=8, 
                        ha='center', va='bottom', rotation=0, alpha=0.8, weight='bold')

        # Etiquetas para datos de validación reales (sin incluir el punto de conexión)
        for x, y in zip(datos_validacion.index, datos_validacion.values):
            plt.text(x, y+0.4, f"{y:.1f}", color="navy", fontsize=9, 
                    ha='center', va='bottom', rotation=0, weight='bold')

        # Etiquetas para predicciones (sin incluir el punto de conexión)
        for x, y in zip(predicciones_validacion.index, predicciones_validacion.values):
            plt.text(x, y-0.5, f"{y:.1f}", color="orange", fontsize=9, 
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
        y_pos = plt.ylim()[1] * 0.75
        plt.text(separacion_x, y_pos, 'División\nEntrenamiento/Validación', 
                ha='center', va='center', color='gray', fontsize=10, weight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgray', alpha=0.9, edgecolor='gray'))

        # === CUADROS DE TEXTO OPTIMIZADOS PARA PANTALLA COMPLETA ===
        # Cuadro de métricas - posición superior izquierda
        info_metricas = (f"MÉTRICAS\n"
                        f"RMSE: {metricas['rmse']:.3f} | MAE: {metricas['mae']:.3f}\n"
                        f"MAPE: {metricas['mape']:.1f}% | R²: {metricas['r2_score']:.3f}\n"
                        f"Precisión: {metricas['precision_final']:.1f}%")
        
        plt.text(0.01, 0.22, info_metricas, transform=plt.gca().transAxes, 
                fontsize=10, verticalalignment='top', 
                bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', alpha=0.9, edgecolor='navy'))

        # Cuadro de componentes - posición inferior izquierda
        info_componentes = (f"COMPONENTES PRECISIÓN\n"
                           f"MAPE: {metricas['precision_mape']:.1f}% | R²: {metricas['precision_r2']:.1f}%\n"
                           f"RMSE: {metricas['precision_rmse']:.1f}% | Formula: 0.4+0.4+0.2")
        
        plt.text(0.01, 0.09, info_componentes, transform=plt.gca().transAxes, 
                fontsize=9, verticalalignment='top',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='wheat', alpha=0.9, edgecolor='orange'))

        # Cuadro de parámetros - posición inferior derecha MÁS ABAJO
        info_parametros = (f"PARÁMETROS\n"
                          f"order = {order} | seasonal = {seasonal_order}\n"
                          f"Train: {len(datos_entrenamiento)} | Valid: {len(datos_validacion)}")
        
        plt.text(0.985, 0.08, info_parametros, transform=plt.gca().transAxes, 
                fontsize=9, verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='lightgreen', alpha=0.9, edgecolor='green'))

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

        plt.text(0.985, 0.97, f"{interpretacion}\n{precision:.1f}%", 
                transform=plt.gca().transAxes, fontsize=12, weight='bold',
                verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round,pad=0.5', facecolor=color_interp, alpha=0.8, edgecolor='black'),
                color='black')

        # === CONFIGURACIÓN MEJORADA DEL EJE X PARA FECHAS MENSUALES ===
        ax = plt.gca()
        
        # FORZAR LÍMITES CORRECTOS DE LOS EJES
        # Establecer límites del eje X para mostrar todo el rango de datos
        x_min = min(historico.index[0], datos_entrenamiento.index[0])
        x_max = max(historico.index[-1], datos_validacion.index[-1])
        plt.xlim(x_min, x_max)
        
        # Establecer límites del eje Y con margen
        y_min = min(historico[col_saidi].min(), predicciones_validacion.min()) * 0.95
        y_max = max(historico[col_saidi].max(), predicciones_validacion.max()) * 1.05
        plt.ylim(y_min, y_max)
        
        # Configurar formato de fechas mensuales en español
        meses_espanol = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 
                        'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        
        # Configurar localizador para mostrar cada 3 meses
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        ax.xaxis.set_minor_locator(mdates.MonthLocator())
        
        # Crear etiquetas personalizadas solo para los meses principales
        fechas_principales = pd.date_range(start=x_min, end=x_max, freq='3MS')
        labels_personalizadas = []
        for fecha in fechas_principales:
            mes_nombre = meses_espanol[fecha.month - 1]
            labels_personalizadas.append(f"{mes_nombre}-{fecha.year}")
        
        # Aplicar etiquetas personalizadas
        if len(fechas_principales) > 0:
            ax.set_xticks(fechas_principales)
            ax.set_xticklabels(labels_personalizadas, rotation=0, ha='center', fontsize=10)

        # Configuración del gráfico principal con título dinámico
        plt.title(f"Validación del Modelo SARIMAX{order}x{seasonal_order} - Análisis de Precisión", 
                 fontsize=18, fontweight='bold', pad=25)
        
        plt.xlabel("Fecha", fontsize=14, weight='bold')
        plt.ylabel("SAIDI (minutos)", fontsize=14, weight='bold')
        
        # Leyenda optimizada para pantalla completa fija - MÁS A LA IZQUIERDA
        plt.legend(fontsize=11, loc='upper center', bbox_to_anchor=(0.25, -0.04), 
                  ncol=2, frameon=True, shadow=True, fancybox=True)
        
        # Grid mejorado
        plt.grid(True, alpha=0.4, linestyle='-', linewidth=0.8)
        
        # Etiquetas del eje Y optimizadas
        plt.yticks(fontsize=11)
        
        # Ajustar márgenes para pantalla completa fija
        plt.tight_layout()
        plt.subplots_adjust(top=0.93, bottom=0.3, left=0.038, right=0.787)
        
        # Texto explicativo optimizado para pantalla completa con información de parámetros
        plt.figtext(0.5, 0.02, 
                   f"Modelo SARIMAX{order}x{seasonal_order} - Entre más cerca estén las líneas azul punteada (real) y naranja (predicha), mejor es el modelo", 
                   ha='center', fontsize=12, style='italic', color='darkblue', weight='bold',
                   bbox=dict(boxstyle='round,pad=0.4', facecolor='lightyellow', alpha=0.8))
        
        # Configurar evento para mantener maximización (de manera segura)
        def on_resize(event):
            """Intentar mantener la ventana maximizada sin causar errores"""
            try:
                if hasattr(mng, 'window') and hasattr(mng.window, 'state'):
                    current_state = str(mng.window.state()).lower()
                    if 'zoom' not in current_state and 'normal' in current_state:
                        mng.window.state('zoomed')
            except:
                # Si hay cualquier error, simplemente continuar sin intervenir
                pass
        
        # Conectar el evento de redimensionamiento de manera segura
        try:
            fig.canvas.mpl_connect('resize_event', on_resize)
        except:
            # Si no se puede conectar el evento, continuar normalmente
            pass
        
        # Mostrar la gráfica
        plt.show()

        # === RESUMEN EN CONSOLA ===
        print(f"\n" + "="*70)
        print("RESUMEN DE VALIDACIÓN DEL MODELO")
        print("="*70)
        print(f"Parámetros utilizados: SARIMAX{order}x{seasonal_order}")
        print(f"Período de entrenamiento: {datos_entrenamiento.index[0].strftime('%Y-%m')} a {datos_entrenamiento.index[-1].strftime('%Y-%m')}")
        print(f"Período de validación: {datos_validacion.index[0].strftime('%Y-%m')} a {datos_validacion.index[-1].strftime('%Y-%m')}")
        print(f"Precisión del modelo: {precision:.1f}% - {interpretacion}")
        print(f"Error promedio (MAE): {metricas['mae']:.3f} minutos")
        print(f"Error cuadrático (RMSE): {metricas['rmse']:.3f}")
        print(f"Correlación (R²): {metricas['r2_score']:.3f}")
        print(f"Error porcentual (MAPE): {metricas['mape']:.1f}%")
        
        print(f"\nINTERPRETACIÓN:")
        print(f"   El modelo SARIMAX{order}x{seasonal_order} predice con {precision:.1f}% de precisión")
        print(f"   En promedio se equivoca por {metricas['mae']:.2f} minutos")
        
        if precision >= 70:
            print("El modelo es confiable para hacer predicciones futuras")
        else:
            print("El modelo tiene baja precisión, considere ajustar parámetros")
        
        print("="*70)

    except Exception as e:
        print(f"ERROR: Ocurrió un error: {str(e)}")
        sys.exit(1)


def main():
    """Función principal con soporte para argumentos de línea de comandos y parámetros dinámicos"""
    parser = argparse.ArgumentParser(description='Gráfica de Validación SAIDI con parámetros SARIMAX configurables')
    parser.add_argument('--file', required=True, help='Ruta del archivo Excel')
    parser.add_argument('--order', nargs=3, type=int, default=[4, 0, 0], 
                       help='Parámetros order (p d q) para SARIMAX. Default: 4 0 0')
    parser.add_argument('--seasonal-order', nargs=4, type=int, default=[1, 0, 0, 8],
                       help='Parámetros seasonal_order (P D Q s) para SARIMAX. Default: 1 0 0 8')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        print(f"ERROR: El archivo {args.file} no existe.")
        sys.exit(1)
    
    # Convertir argumentos a tuplas
    order = tuple(args.order)
    seasonal_order = tuple(args.seasonal_order)
    
    print("GENERADOR DE GRÁFICA DE VALIDACIÓN SAIDI CON PARÁMETROS DINÁMICOS")
    print("="*50)
    print("Generando gráfica que muestra la precisión del modelo")
    print("comparando predicciones vs datos históricos conocidos.")
    print(f"Parámetros: SARIMAX{order}x{seasonal_order}")
    print("="*50)
    
    generar_grafica_validacion(args.file, order, seasonal_order)
    print("Proceso completado exitosamente.")


if __name__ == "__main__":
    main()