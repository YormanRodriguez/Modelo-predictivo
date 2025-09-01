# backend/Parametro.py - Comunicación con Frontend
import warnings
warnings.filterwarnings('ignore')
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
from statsmodels.tsa.statespace.sarimax import SARIMAX
from pmdarima import auto_arima
import numpy as np
from sklearn.metrics import mean_squared_error
import argparse
import json
import os
import sys

# Variables globales para la interfaz
PROGRESS_PERCENTAGE = 0
CURRENT_MODEL = ""
STATUS_MESSAGE = ""
TOP_3_MODELS = []

def update_progress(progress_file, progress, status, current_model=""):
    """Actualizar el archivo de progreso para comunicación con frontend"""
    global PROGRESS_PERCENTAGE, CURRENT_MODEL, STATUS_MESSAGE
    
    # Actualizar variables globales
    PROGRESS_PERCENTAGE = progress
    CURRENT_MODEL = current_model
    STATUS_MESSAGE = status
    
    if progress_file and os.path.dirname(progress_file):
        try:
            # Asegurar que el directorio existe
            os.makedirs(os.path.dirname(progress_file), exist_ok=True)
            
            # Verificar si se solicitó cancelación
            cancel_file = progress_file.replace('.json', '_cancel.json')
            if os.path.exists(cancel_file):
                print("Cancelación detectada por el usuario")
                return False  # Señal de cancelación
            
            # Escribir archivo de progreso
            progress_data = {
                'progress': progress,
                'status': status,
                'current_model': current_model,
                'top_models': TOP_3_MODELS,
                'timestamp': pd.Timestamp.now().isoformat()
            }
            
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, ensure_ascii=False, indent=2)
                
            return True
            
        except Exception as e:
            print(f"Error actualizando progreso: {e}")
            return True
    return True

def cargar_excel():
    """Abrir un cuadro de diálogo para seleccionar el archivo Excel"""
    root = tk.Tk()
    root.withdraw()  
    file_path = filedialog.askopenfilename(
        title="Seleccionar archivo Excel",
        filetypes=[("Archivos Excel", "*.xlsx *.xls")]
    )
    if not file_path:
        messagebox.showerror("Error", "No se seleccionó ningún archivo.")
        return None
    return file_path

def evaluar_modelo_completo(serie, order, seasonal_order):
    """Evalúa un modelo SARIMAX con múltiples métricas"""
    try:
        if len(serie) >= 60:
            pct_validacion = 0.30
        elif len(serie) >= 36:
            pct_validacion = 0.25
        else:
            pct_validacion = 0.20
            
        n_test = max(6, int(len(serie) * pct_validacion))
        train_data = serie[:-n_test]
        test_data = serie[-n_test:]
        
        model = SARIMAX(
            train_data,
            order=order,
            seasonal_order=seasonal_order,
            enforce_stationarity=False,
            enforce_invertibility=False
        )
        results = model.fit(disp=False)
        
        pred = results.get_forecast(steps=n_test)
        pred_mean = pred.predicted_mean
        
        rmse = np.sqrt(mean_squared_error(test_data, pred_mean))
        mae = np.mean(np.abs(test_data - pred_mean))
        
        epsilon = 1e-8
        mape = np.mean(np.abs((test_data - pred_mean) / (test_data + epsilon))) * 100
        
        ss_res = np.sum((test_data - pred_mean) ** 2)
        ss_tot = np.sum((test_data - np.mean(test_data)) ** 2)
        r2_score = 1 - (ss_res / (ss_tot + epsilon))
        
        precision_mape = max(0, 100 - mape)
        precision_r2 = max(0, r2_score * 100)
        
        mean_actual = np.mean(test_data)
        precision_rmse = max(0, (1 - rmse/mean_actual) * 100)
        
        precision_final = (precision_mape * 0.4 + precision_r2 * 0.4 + precision_rmse * 0.2)
        precision_final = max(0, min(100, precision_final))
        
        aic = results.aic
        bic = results.bic
        
        complexity_penalty = sum(order) + sum(seasonal_order[:3])
        composite_score = rmse + (complexity_penalty * 0.1)
        
        return {
            'rmse': rmse,
            'mae': mae,
            'mape': mape,
            'r2_score': r2_score,
            'precision_mape': precision_mape,
            'precision_r2': precision_r2, 
            'precision_rmse': precision_rmse,
            'precision_final': precision_final,
            'aic': aic,
            'bic': bic,
            'composite_score': composite_score,
            'n_params': complexity_penalty,
            'n_test': n_test,
            'pct_validacion': pct_validacion
        }
        
    except Exception as e:
        return {
            'rmse': float('inf'),
            'mae': float('inf'),
            'mape': 100,
            'r2_score': -1,
            'precision_mape': 0,
            'precision_r2': 0,
            'precision_rmse': 0,
            'precision_final': 0,
            'aic': float('inf'),
            'bic': float('inf'),
            'composite_score': float('inf'),
            'n_params': 999,
            'n_test': 0,
            'pct_validacion': 0
        }

def actualizar_top_3_modelos(order, seasonal_order, metrics):
    """Actualizar la lista de top 3 modelos basado en precisión"""
    global TOP_3_MODELS
    
    modelo_info = {
        'order': order,
        'seasonal_order': seasonal_order,
        'precision_final': metrics['precision_final'],
        'rmse': metrics['rmse'],
        'mape': metrics['mape'],
        'r2_score': metrics['r2_score'],
        'aic': metrics['aic']
    }
    
    TOP_3_MODELS.append(modelo_info)
    TOP_3_MODELS.sort(key=lambda x: x['precision_final'], reverse=True)
    
    if len(TOP_3_MODELS) > 3:
        TOP_3_MODELS = TOP_3_MODELS[:3]

class AutoArimaWithMultipleMetrics:
    """Wrapper personalizado para auto_arima con comunicación frontend"""
    
    def __init__(self, serie, progress_file=None):
        self.serie = serie
        self.progress_file = progress_file
        self.iteracion = 0
        self.total_iteraciones = 0
        self.mejor_rmse = float('inf')
        self.mejor_composite = float('inf')
        self.mejor_precision = 0
        self.mejor_params_rmse = None
        self.mejor_params_composite = None
        self.mejor_params_precision = None
        self.resultados = []
        
    def set_total_iterations(self, total):
        """Establecer el total de iteraciones para calcular progreso"""
        self.total_iteraciones = total
        print(f"Total de combinaciones a evaluar: {total}")
        
    def evaluar_y_mostrar(self, order, seasonal_order):
        """Evalúa un modelo y actualiza progreso para la interfaz"""
        self.iteracion += 1
        
        progress_percentage = (self.iteracion / self.total_iteraciones) * 100 if self.total_iteraciones > 0 else 0
        
        if self.progress_file and self.total_iteraciones > 0:
            model_info = f"order={order}, seasonal_order={seasonal_order}"
            status = f"Evaluando modelo {self.iteracion} de {self.total_iteraciones} ({progress_percentage:.1f}%)"
            
            # Verificar cancelación
            if not update_progress(self.progress_file, progress_percentage, status, model_info):
                print("Proceso cancelado por el usuario")
                sys.exit(0)
        
        metrics = evaluar_modelo_completo(self.serie, order, seasonal_order)
        actualizar_top_3_modelos(order, seasonal_order, metrics)
        
        print(f"[{progress_percentage:5.1f}%] Modelo {self.iteracion:3d}/{self.total_iteraciones}: "
              f"order={order}, seasonal_order={seasonal_order}")
        print(f"         RMSE={metrics['rmse']:.4f}, Precisión={metrics['precision_final']:.1f}%, "
              f"MAPE={metrics['mape']:.1f}%, R²={metrics['r2_score']:.3f}")
        
        self.resultados.append({
            'order': order,
            'seasonal_order': seasonal_order,
            'metrics': metrics
        })
        
        if metrics['rmse'] < self.mejor_rmse:
            self.mejor_rmse = metrics['rmse']
            self.mejor_params_rmse = (order, seasonal_order)
            print(f"         *** NUEVO MEJOR RMSE: {metrics['rmse']:.4f} ***")
        
        if metrics['composite_score'] < self.mejor_composite:
            self.mejor_composite = metrics['composite_score']
            self.mejor_params_composite = (order, seasonal_order)
            print(f"         *** NUEVO MEJOR SCORE COMPUESTO: {metrics['composite_score']:.4f} ***")
        
        if metrics['precision_final'] > self.mejor_precision:
            self.mejor_precision = metrics['precision_final']
            self.mejor_params_precision = (order, seasonal_order)
            print(f"         *** NUEVA MEJOR PRECISIÓN: {metrics['precision_final']:.1f}% ***")
        
        return metrics['rmse']
    
    def get_resumen_final(self):
        """Proporciona un resumen final con los mejores modelos"""
        print("\n" + "="*80)
        print("RESUMEN FINAL - TOP 3 MODELOS ENCONTRADOS")
        print("="*80)
        
        for i, modelo in enumerate(TOP_3_MODELS, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
            print(f"\n{medal} PUESTO #{i}:")
            print(f"   Parámetros: order={modelo['order']}, seasonal_order={modelo['seasonal_order']}")
            print(f"   Precisión: {modelo['precision_final']:.1f}% | RMSE: {modelo['rmse']:.4f}")
            print(f"   MAPE: {modelo['mape']:.1f}% | R²: {modelo['r2_score']:.3f} | AIC: {modelo['aic']:.1f}")
        
        if TOP_3_MODELS:
            best_model = TOP_3_MODELS[0]
            precision = best_model['precision_final']
            
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
                
            print(f"\nINTERPRETACIÓN DEL MEJOR MODELO:")
            print(f"   Precisión: {precision:.1f}% - {interpretacion}")
        
        print("="*80)
        return self.mejor_params_composite

def analizar_saidi(file_path, progress_file=None):
    """Función principal de análisis SAIDI"""
    try:
        print(f"Iniciando análisis SAIDI con archivo: {file_path}")
        
        if progress_file:
            update_progress(progress_file, 5, "Cargando datos del archivo Excel...", "")
        
        # Cargar datos
        df = pd.read_excel(file_path, sheet_name="Hoja1")
        print("Columnas encontradas:", df.columns.tolist())

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
            error_msg = "No se encontró la columna SAIDI ni SAIDI Histórico."
            print(error_msg)
            if progress_file:
                update_progress(progress_file, 0, f"Error: {error_msg}", "")
            return

        if progress_file:
            update_progress(progress_file, 10, "Datos cargados correctamente. Preparando análisis...", "")

        # Identificar meses faltantes
        faltantes = df[df[col_saidi].isna()]
        historico = df[df[col_saidi].notna()]

        if faltantes.empty:
            msg = "No hay meses faltantes para predecir."
            print(msg)
            if progress_file:
                update_progress(progress_file, 100, msg, "")
            return

        print(f"Datos históricos: {len(historico)} observaciones")
        print(f"Meses faltantes: {len(faltantes)} observaciones")

        # Crear evaluador personalizado
        evaluador = AutoArimaWithMultipleMetrics(historico[col_saidi], progress_file)

        # Búsqueda exhaustiva de parámetros
        print("\n" + "="*80)
        print("BÚSQUEDA EXHAUSTIVA DE PARÁMETROS ÓPTIMOS")
        print(f"Dataset: {len(historico)} observaciones desde {historico.index[0].strftime('%Y-%m')} hasta {historico.index[-1].strftime('%Y-%m')}")
        print("="*80)
        
        from itertools import product
        
        # Rangos de parámetros (reducidos para testing, expandir en producción)
        p_range = range(0, 5)   
        d_range = range(0, 4)  
        q_range = range(0, 4)   
        P_range = range(0, 5)   
        D_range = range(0, 4)   
        Q_range = range(0, 4)   
        s_range = range(8, 16) 
        
        mejor_modelo_global = None
        total_combinations = len(p_range) * len(d_range) * len(q_range) * len(P_range) * len(D_range) * len(Q_range) * len(s_range)
        
        evaluador.set_total_iterations(total_combinations)
        
        if progress_file:
            update_progress(progress_file, 15, f"Iniciando evaluación de {total_combinations} combinaciones", 
                          "Preparando búsqueda exhaustiva...")
        
        # Evaluar combinaciones
        for p, d, q in product(p_range, d_range, q_range):
            for P, D, Q in product(P_range, D_range, Q_range):
                for s in s_range:
                    order = (p, d, q)
                    seasonal_order = (P, D, Q, s)

                    rmse = evaluador.evaluar_y_mostrar(order, seasonal_order)
                    
                    try:
                        temp_model = SARIMAX(
                            historico[col_saidi],
                            order=order,
                            seasonal_order=seasonal_order,
                            enforce_stationarity=False,
                            enforce_invertibility=False
                        )
                        temp_results = temp_model.fit(disp=False)
                        
                        if order == evaluador.mejor_params_composite[0] and seasonal_order == evaluador.mejor_params_composite[1]:
                            mejor_modelo_global = temp_results
                            
                    except:
                        continue
        
        if progress_file:
            update_progress(progress_file, 90, "Análisis completado, generando resultados finales", 
                          "Preparando resumen de resultados...")
        
        mejor_params_final = evaluador.get_resumen_final()

        # Usar auto_arima como respaldo si es necesario
        if mejor_modelo_global is None:
            print("\nUsando auto_arima como respaldo...")
            if progress_file:
                update_progress(progress_file, 95, "Usando auto_arima como respaldo", 
                              "Generando modelo final...")
            
            auto_model = auto_arima(
                historico[col_saidi],
                seasonal=True,
                m=12,
                trace=True,
                error_action='ignore',
                suppress_warnings=True,
                stepwise=True
            )
            
            order = auto_model.order
            seasonal_order = auto_model.seasonal_order
            
            model = SARIMAX(
                historico[col_saidi],
                order=order,
                seasonal_order=seasonal_order,
                enforce_stationarity=False,
                enforce_invertibility=False
            )
            results = model.fit(disp=False)
        else:
            results = mejor_modelo_global
            order = mejor_params_final[0]
            seasonal_order = mejor_params_final[1]

        print(f"\nModelo final seleccionado:")
        print(f"order={order}")
        print(f"seasonal_order={seasonal_order}")

        if progress_file:
            update_progress(progress_file, 98, "Generando predicciones finales", 
                          f"Modelo: order={order}, seasonal_order={seasonal_order}")

        # Generar predicciones
        pred = results.get_prediction(start=faltantes.index[0], end=faltantes.index[-1])
        pred_mean = pred.predicted_mean

        df_pred = df.copy()
        df_pred.loc[faltantes.index, col_saidi] = pred_mean

        print(f"\n" + "="*60)
        print("RESUMEN DEL MODELO SELECCIONADO")
        print("="*60)
        print(f"AIC: {results.aic:.2f}")
        print(f"BIC: {results.bic:.2f}")
        print(f"Predicciones generadas: {len(pred_mean)}")
        print(f"Período de entrenamiento: {historico.index[0].strftime('%Y-%m')} a {historico.index[-1].strftime('%Y-%m')}")
        print(f"Período de predicción: {faltantes.index[0].strftime('%Y-%m')} a {faltantes.index[-1].strftime('%Y-%m')}")
        
        print(f"\nPREDICCIONES GENERADAS:")
        for fecha, valor in zip(faltantes.index, pred_mean):
            print(f"   {fecha.strftime('%Y-%m')}: {valor:.2f}")
        
        print("="*60)
        
        # Progreso final con top 3 modelos
        if progress_file:
            final_status = f"Proceso completado. Predicciones: {len(pred_mean)}. Top modelo: {TOP_3_MODELS[0]['precision_final']:.1f}% precisión"
            update_progress(progress_file, 100, final_status, 
                          f"Finalizado - {len(TOP_3_MODELS)} modelos evaluados")

    except Exception as e:
        error_msg = f"Error durante el análisis: {str(e)}"
        print(error_msg)
        if progress_file:
            update_progress(progress_file, 0, f"Error: {error_msg}", "")
        raise

def main():
    """Función principal con soporte para argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(description='Análisis SAIDI con optimización de parámetros')
    parser.add_argument('--file', type=str, help='Ruta del archivo Excel')
    parser.add_argument('--progress', type=str, help='Archivo de progreso para comunicación con frontend')
    
    args = parser.parse_args()
    
    # Verificar argumentos
    if args.file:
        if not os.path.exists(args.file):
            print(f"Error: El archivo {args.file} no existe.")
            sys.exit(1)
        file_path = args.file
    else:
        # Usar selector de archivos si no se proporciona archivo
        file_path = cargar_excel()
    
    if file_path:
        print(f"Iniciando análisis con archivo: {file_path}")
        if args.progress:
            print(f"Archivo de progreso: {args.progress}")
        
        try:
            analizar_saidi(file_path, args.progress)
            print("Análisis completado exitosamente.")
        except Exception as e:
            print(f"Error durante el análisis: {e}")
            sys.exit(1)
    else:
        print("No se seleccionó ningún archivo.")
        sys.exit(1)

if __name__ == "__main__":
    main()