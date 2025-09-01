# backend/Modelo.py - Script de Predicción con Parámetros Dinámicos
import warnings
warnings.filterwarnings('ignore')
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MaxNLocator
import argparse
import sys
import os
from tkinter import messagebox
from statsmodels.tsa.statespace.sarimax import SARIMAX
import numpy as np
from sklearn.metrics import mean_squared_error


def calcular_metricas_modelo(serie, order, seasonal_order):
    """
    Calcula las métricas del modelo SARIMAX con parámetros dinámicos.
    """
    try:
        # Usar validación dinámica basada en cantidad de datos
        if len(serie) >= 60:  # 5+ años de datos mensuales
            pct_validacion = 0.30
        elif len(serie) >= 36:  # 3-5 años
            pct_validacion = 0.25
        else:  # Menos de 3 años
            pct_validacion = 0.20
            
        n_test = max(6, int(len(serie) * pct_validacion))
        train_data = serie[:-n_test]
        test_data = serie[-n_test:]
        
        # Ajustar modelo con datos de entrenamiento
        model = SARIMAX(
            train_data,
            order=order,
            seasonal_order=seasonal_order,
            enforce_stationarity=False,
            enforce_invertibility=False
        )
        results = model.fit(disp=False)
        
        # Hacer predicciones para el período de prueba
        pred = results.get_forecast(steps=n_test)
        pred_mean = pred.predicted_mean
        
        # Calcular múltiples métricas
        rmse = np.sqrt(mean_squared_error(test_data, pred_mean))
        mae = np.mean(np.abs(test_data - pred_mean))
        
        # Calcular MAPE (Error Porcentual Absoluto Medio)
        epsilon = 1e-8
        mape = np.mean(np.abs((test_data - pred_mean) / (test_data + epsilon))) * 100
        
        # Calcular coeficiente de determinación (R²) para validación
        ss_res = np.sum((test_data - pred_mean) ** 2)
        ss_tot = np.sum((test_data - np.mean(test_data)) ** 2)
        r2_score = 1 - (ss_res / (ss_tot + epsilon))
        
        # Calcular porcentaje de precisión basado en múltiples métricas
        precision_mape = max(0, 100 - mape)
        precision_r2 = max(0, r2_score * 100)
        
        mean_actual = np.mean(test_data)
        precision_rmse = max(0, (1 - rmse/mean_actual) * 100)
        
        # Precisión compuesta (promedio ponderado)
        precision_final = (precision_mape * 0.4 + precision_r2 * 0.4 + precision_rmse * 0.2)
        precision_final = max(0, min(100, precision_final))
        
        return {
            'rmse': rmse,
            'mae': mae,
            'mape': mape,
            'r2_score': r2_score,
            'precision_final': precision_final,
            'aic': results.aic,
            'bic': results.bic,
            'n_test': n_test,
            'pct_validacion': pct_validacion,
            'precision_mape': precision_mape,
            'precision_r2': precision_r2,
            'precision_rmse': precision_rmse
        }
        
    except Exception as e:
        print(f"ERROR calculando métricas: {e}")
        return None


def analizar_saidi(file_path, order=(4, 0, 0), seasonal_order=(1, 0, 0, 8)):
    try:
        print(f"Analizando archivo: {file_path}")
        print(f"Parámetros SARIMAX: order={order}, seasonal_order={seasonal_order}")
        
        # === Cargar datos ===
        df = pd.read_excel(file_path, sheet_name="Hoja1")

        # Mostrar nombres de columnas detectados (para depuración)
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

        # Identificar meses faltantes (NaN)
        faltantes = df[df[col_saidi].isna()]
        historico = df[df[col_saidi].notna()]

        if faltantes.empty:
            print("INFO: No hay meses faltantes para predecir.")
            # Crear datos simulados para mostrar la funcionalidad
            ultimo_mes = historico.index[-1]
            fechas_futuras = pd.date_range(start=ultimo_mes + pd.DateOffset(months=1), periods=6, freq='MS')
            for fecha in fechas_futuras:
                df.loc[fecha, col_saidi] = np.nan
            faltantes = df[df[col_saidi].isna()]
            print(f"INFO: Creando {len(faltantes)} predicciones futuras para demostración.")

        print(f"\n" + "="*60)
        print("ANÁLISIS SAIDI CON PARÁMETROS DINÁMICOS")
        print(f"Dataset: {len(historico)} observaciones desde {historico.index[0].strftime('%Y-%m')} hasta {historico.index[-1].strftime('%Y-%m')}")
        print(f"order = {order}")
        print(f"seasonal_order = {seasonal_order}")
        print("="*60)
        
        # Calcular métricas del modelo
        metricas = calcular_metricas_modelo(historico[col_saidi], order, seasonal_order)
        
        if metricas:
            print(f"MÉTRICAS DEL MODELO:")
            print(f"• RMSE: {metricas['rmse']:.4f}")
            print(f"• MAE: {metricas['mae']:.4f}")
            print(f"• MAPE: {metricas['mape']:.1f}%")
            print(f"• R²: {metricas['r2_score']:.3f}")
            print(f"• Precisión Final: {metricas['precision_final']:.1f}%")
            print(f"• AIC: {metricas['aic']:.2f}")
            print(f"• BIC: {metricas['bic']:.2f}")
            print(f"• Validación: {metricas['pct_validacion']*100:.0f}% ({metricas['n_test']} obs.)")
            
            # Interpretación de precisión
            precision = metricas['precision_final']
            if precision >= 90:
                interpretacion = "EXCELENTE - Predicciones muy confiables"
            elif precision >= 80:
                interpretacion = "BUENO - Predicciones confiables"
            elif precision >= 70:
                interpretacion = "ACEPTABLE - Predicciones moderadamente confiables"
            elif precision >= 60:
                interpretacion = "REGULAR - Usar con precaución"
            else:
                interpretacion = "BAJO - Modelo poco confiable"
                
            print(f"\nINTERPRETACIÓN: {interpretacion}")
        else:
            print("No se pudieron calcular las métricas de validación.")
            metricas = {'precision_final': 0}  # Fallback para evitar errores

        # Ajustar modelo final con todos los datos históricos
        try:
            model = SARIMAX(
                historico[col_saidi],
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

        # Predecir para los meses faltantes
        try:
            pred = results.get_prediction(start=faltantes.index[0], end=faltantes.index[-1])
            pred_mean = pred.predicted_mean
            print(f"✓ Predicciones generadas para {len(pred_mean)} períodos")
        except Exception as e:
            print(f"ERROR: No se pudieron generar predicciones: {e}")
            sys.exit(1)

        # Completar columna con predicción
        df_pred = df.copy()
        df_pred.loc[faltantes.index, col_saidi] = pred_mean

        # === MOSTRAR RESUMEN ===
        print(f"\n" + "="*60)
        print("RESUMEN DE PREDICCIONES")
        print("="*60)
        print(f"Predicciones generadas: {len(pred_mean)}")
        print(f"Período de entrenamiento: {historico.index[0].strftime('%Y-%m')} a {historico.index[-1].strftime('%Y-%m')}")
        print(f"Período de predicción: {faltantes.index[0].strftime('%Y-%m')} a {faltantes.index[-1].strftime('%Y-%m')}")
        
        print(f"\nValores predichos:")
        for fecha, valor in zip(faltantes.index, pred_mean):
            print(f"• {fecha.strftime('%Y-%m')}: {valor:.2f}")
        print("="*60)

        # === GRÁFICA MEJORADA ===
        # Crear figura con tamaño optimizado para pantalla completa
        fig = plt.figure(figsize=(16, 10))
        
        # Configurar pantalla completa de manera segura
        mng = fig.canvas.manager
        try:
            if hasattr(mng, 'window') and hasattr(mng.window, 'state'):
                mng.window.state('zoomed')
                try:
                    mng.window.resizable(False, False)
                except:
                    print("Info: La ventana se maximizó pero puede ser redimensionable")
            elif hasattr(mng, 'window') and hasattr(mng.window, 'showMaximized'):
                mng.window.showMaximized()
            else:
                if hasattr(mng, 'full_screen_toggle'):
                    mng.full_screen_toggle()
        except Exception as e:
            print(f"Info: Usando configuración de ventana estándar: {e}")

        # Línea azul: datos históricos
        plt.plot(historico.index, historico[col_saidi], label="SAIDI Histórico", 
                color="blue", linewidth=3, marker='o', markersize=5)
        
        # Etiquetas para puntos históricos (más espaciadas)
        for i, (x, y) in enumerate(zip(historico.index, historico[col_saidi])):
            if i % max(1, len(historico)//6) == 0:
                plt.text(x, y+0.3, f"{y:.1f}", color="blue", fontsize=8, 
                        ha='center', va='bottom', rotation=0, alpha=0.8, weight='bold')

        # Línea naranja: predicciones (conectada con el último punto histórico)
        if not historico.empty and not pred_mean.empty:
            ultimo_real_x = historico.index[-1]
            ultimo_real_y = historico[col_saidi].iloc[-1]
            x_pred = [ultimo_real_x] + list(pred_mean.index)
            y_pred = [ultimo_real_y] + list(pred_mean.values)
            plt.plot(x_pred, y_pred, label="Predicción SAIDI", 
                    color="orange", linewidth=3, marker='^', markersize=7)
            
            # Etiquetas para puntos predichos
            for x, y in zip(pred_mean.index, pred_mean.values):
                plt.text(x, y+0.4, f"{y:.1f}", color="orange", fontsize=9, 
                        ha='center', va='bottom', rotation=0, weight='bold')

        # Otras líneas si existen
        if "Esperados" in df.columns:
            esperados_plot = df["Esperados"]
            plt.plot(esperados_plot.index, esperados_plot, label="CMI", 
                    color="green", linewidth=2, marker='s')
            
        if "Estandar de calidad" in df.columns:
            estandar_plot = df["Estandar de calidad"]
            plt.plot(estandar_plot.index, estandar_plot, label="CREG", 
                    color="red", linewidth=2, marker='d')

        # Línea vertical que separa histórico de predicción
        if not historico.empty:
            plt.axvline(x=historico.index[-1], color='gray', linestyle='--', 
                       alpha=0.8, linewidth=2)
            
            y_pos = plt.ylim()[1] * 0.75
            plt.text(historico.index[-1], y_pos, 'Inicio\nPredicción', 
                    ha='center', va='center', color='gray', fontsize=10, weight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgray', alpha=0.9, edgecolor='gray'))

        # Configuración mejorada del eje X para fechas mensuales
        ax = plt.gca()
        
        # Establecer límites del eje X para mostrar todo el rango de datos
        x_min = min(historico.index[0], df.index[0])
        x_max = max(historico.index[-1], df.index[-1])
        plt.xlim(x_min, x_max)
        
        # Establecer límites del eje Y con margen
        all_values = list(historico[col_saidi].values) + list(pred_mean.values)
        if "Esperados" in df.columns:
            all_values.extend(df["Esperados"].dropna().values)
        if "Estandar de calidad" in df.columns:
            all_values.extend(df["Estandar de calidad"].dropna().values)
            
        y_min = min(all_values) * 0.95
        y_max = max(all_values) * 1.05
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
        precision_text = f" - Precisión: {metricas['precision_final']:.1f}%" if metricas['precision_final'] > 0 else ""
        plt.title(f"SAIDI: Histórico vs Predicción SARIMAX{order}x{seasonal_order}{precision_text}", 
                 fontsize=18, fontweight='bold', pad=25)
        
        plt.xlabel("Fecha", fontsize=14, weight='bold')
        plt.ylabel("SAIDI (minutos)", fontsize=14, weight='bold')
        
        # Leyenda optimizada para pantalla completa
        plt.legend(fontsize=11, loc='upper center', bbox_to_anchor=(0.25, -0.04), 
                  ncol=2, frameon=True, shadow=True, fancybox=True)
        
        # Grid mejorado
        plt.grid(True, alpha=0.4, linestyle='-', linewidth=0.8)
        
        # Etiquetas del eje Y optimizadas
        plt.yticks(fontsize=11)
        
        # Ajustar márgenes para pantalla completa fija
        plt.tight_layout()
        plt.subplots_adjust(top=0.93, bottom=0.3, left=0.038, right=0.787)
        
        # Texto explicativo con información de parámetros
        plt.figtext(0.5, 0.02, 
                   f"Modelo SARIMAX{order}x{seasonal_order} - Línea azul: datos históricos, naranja: predicciones futuras", 
                   ha='center', fontsize=12, style='italic', color='darkblue', weight='bold',
                   bbox=dict(boxstyle='round,pad=0.4', facecolor='lightyellow', alpha=0.8))
        
        # Configurar evento para mantener maximización
        def on_resize(event):
            try:
                if hasattr(mng, 'window') and hasattr(mng.window, 'state'):
                    current_state = str(mng.window.state()).lower()
                    if 'zoom' not in current_state and 'normal' in current_state:
                        mng.window.state('zoomed')
            except:
                pass
        
        # Conectar el evento de redimensionamiento de manera segura
        try:
            fig.canvas.mpl_connect('resize_event', on_resize)
        except:
            pass
        
        # Mostrar la gráfica
        plt.show()

    except Exception as e:
        print(f"ERROR: Ocurrió un error: {str(e)}")
        sys.exit(1)


def main():
    """Función principal con soporte para argumentos de línea de comandos y parámetros dinámicos"""
    parser = argparse.ArgumentParser(description='Predicción SAIDI con parámetros SARIMAX configurables')
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
    
    print("PREDICTOR SAIDI CON PARÁMETROS DINÁMICOS")
    print("="*50)
    print("Generando predicciones SAIDI usando parámetros SARIMAX configurables.")
    print(f"Parámetros: SARIMAX{order}x{seasonal_order}")
    print("="*50)
    
    analizar_saidi(args.file, order, seasonal_order)
    print("Proceso completado exitosamente.")


if __name__ == "__main__":
    main()