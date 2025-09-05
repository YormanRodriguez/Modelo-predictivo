# excel_manager.py
"""
Gestor global para manejar la carga y validación de archivos Excel
"""
import pandas as pd
import os
from typing import Optional, Dict, Any
import tkinter as tk
from tkinter import filedialog, messagebox

class ExcelManager:
    """Gestor singleton para manejar archivos Excel globalmente"""
    
    _instance = None
    _excel_data = None
    _file_path = None
    _validated = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def load_excel(cls, file_path: str) -> bool:
        """
        Cargar archivo Excel desde una ruta específica
        Returns: True si se cargó exitosamente, False si falló
        """
        try:
            # Verificar que el archivo existe
            if not os.path.exists(file_path):
                print(f"Error: Archivo no encontrado: {file_path}")
                return False
                
            # Verificar extensión
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in ['.xlsx', '.xls']:
                print(f"Error: Formato de archivo no válido: {file_ext}")
                return False
                
            print(f"Cargando archivo: {file_path}")
            
            # Intentar leer el archivo
            try:
                # Primero intentar leer la Hoja1, si no existe, leer la primera hoja
                try:
                    df = pd.read_excel(file_path, sheet_name="Hoja1")
                except:
                    # Si no hay Hoja1, leer la primera hoja disponible
                    df = pd.read_excel(file_path, sheet_name=0)
                    
            except Exception as e:
                print(f"Error al leer Excel: {str(e)}")
                return False
            
            # Validar estructura del archivo
            validation_result = cls._validate_excel_structure(df, file_path)
            
            if validation_result['valid']:
                cls._excel_data = df
                cls._file_path = file_path
                cls._validated = True
                
                print("Archivo Excel cargado y validado exitosamente")
                print(f"Dimensiones: {df.shape[0]} filas x {df.shape[1]} columnas")
                print(f"Columnas detectadas: {list(df.columns)}")
                
                return True
            else:
                print(f"Error de validación: {validation_result['error']}")
                return False
                
        except Exception as e:
            print(f"Error inesperado al cargar Excel: {str(e)}")
            return False
    
    @classmethod
    def load_excel_file(cls, parent_window=None) -> bool:
        """
        Cargar archivo Excel con validación completa
        Returns: True si se cargó exitosamente, False si falló
        """
        try:
            # Ocultar ventana padre temporalmente si existe
            if parent_window:
                parent_window.withdraw()
            
            # Abrir dialog para seleccionar archivo
            file_path = filedialog.askopenfilename(
                title="Seleccionar archivo Excel - SAIDI Analysis Pro",
                filetypes=[
                    ("Archivos Excel", "*.xlsx *.xls"),
                    ("Todos los archivos", "*.*")
                ],
                initialdir=os.getcwd()
            )
            
            # Restaurar ventana padre
            if parent_window:
                parent_window.deiconify()
                parent_window.lift()
            
            if not file_path:
                return False
                
            # Intentar cargar el archivo
            print(f"Cargando archivo: {file_path}")
            df = pd.read_excel(file_path, sheet_name="Hoja1")
            
            # Validar estructura del archivo
            validation_result = cls._validate_excel_structure(df, file_path)
            
            if validation_result['valid']:
                cls._excel_data = df
                cls._file_path = file_path
                cls._validated = True
                
                print("Archivo Excel cargado y validado exitosamente")
                print(f"Dimensiones: {df.shape[0]} filas x {df.shape[1]} columnas")
                print(f"Columnas detectadas: {list(df.columns)}")
                
                messagebox.showinfo(
                    "Excel Cargado Exitosamente",
                    f"Archivo: {os.path.basename(file_path)}\n"
                    f"Dimensiones: {df.shape[0]} filas x {df.shape[1]} columnas\n"
                    f"Columnas detectadas: {', '.join(df.columns[:3])}{'...' if len(df.columns) > 3 else ''}\n\n"
                    f"Estructura validada correctamente"
                )
                return True
            else:
                messagebox.showerror(
                    "Error de Validación",
                    f"El archivo Excel no tiene la estructura esperada:\n\n"
                    f"{validation_result['error']}\n\n"
                    f"Estructura esperada:\n"
                    f"- Columna 1: Fecha (formato fecha)\n"
                    f"- Columna 2: SAIDI o SAIDI Histórico (valores numéricos)\n"
                    f"- Columnas adicionales opcionales: CMI, CREG, etc."
                )
                return False
                
        except FileNotFoundError:
            messagebox.showerror("Error", "El archivo seleccionado no existe.")
            return False
        except PermissionError:
            messagebox.showerror("Error", "No se tienen permisos para leer el archivo.\nAsegúrese de que el archivo no esté abierto en Excel.")
            return False
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar el archivo Excel:\n{str(e)}")
            print(f"Error detallado: {str(e)}")
            return False
    
    @classmethod
    def _validate_excel_structure(cls, df: pd.DataFrame, file_path: str) -> Dict[str, Any]:
        """Validar que el Excel tenga la estructura correcta para SAIDI"""
        try:
            # Verificar que no esté vacío
            if df.empty:
                return {'valid': False, 'error': 'El archivo está vacío'}
            
            if len(df.columns) < 2:
                return {'valid': False, 'error': 'Se necesitan al menos 2 columnas (Fecha y SAIDI)'}
            
            # Verificar columna de fecha (primera columna)
            fecha_col = df.columns[0]
            try:
                # Intentar convertir a datetime
                pd.to_datetime(df.iloc[:, 0])
            except:
                return {'valid': False, 'error': f'La primera columna "{fecha_col}" no contiene fechas válidas'}
            
            # Verificar columna SAIDI
            saidi_found = False
            saidi_col = None
            
            for col in df.columns[1:]:  # Buscar desde la segunda columna
                if 'SAIDI' in str(col).upper():
                    saidi_col = col
                    saidi_found = True
                    break
            
            if not saidi_found:
                return {'valid': False, 'error': 'No se encontró una columna con "SAIDI" en el nombre'}
            
            # Verificar que la columna SAIDI tenga datos numéricos
            saidi_data = df[saidi_col].dropna()
            if saidi_data.empty:
                return {'valid': False, 'error': f'La columna "{saidi_col}" no contiene datos válidos'}
            
            try:
                pd.to_numeric(saidi_data)
            except:
                return {'valid': False, 'error': f'La columna "{saidi_col}" no contiene valores numéricos válidos'}
            
            # Verificar que haya suficientes datos históricos
            datos_historicos = len(saidi_data)
            if datos_historicos < 12:
                return {'valid': False, 'error': f'Se necesitan al menos 12 observaciones históricas, se encontraron {datos_historicos}'}
            
            return {
                'valid': True, 
                'fecha_col': fecha_col,
                'saidi_col': saidi_col,
                'datos_historicos': datos_historicos
            }
            
        except Exception as e:
            return {'valid': False, 'error': f'Error durante la validación: {str(e)}'}
    
    @classmethod
    def is_excel_loaded(cls) -> bool:
        """Verificar si hay un Excel cargado y validado"""
        return cls._validated and cls._excel_data is not None
    
    @classmethod
    def get_excel_data(cls) -> Optional[pd.DataFrame]:
        """Obtener los datos del Excel cargado"""
        if cls.is_excel_loaded():
            return cls._excel_data.copy()  # Retornar copia para evitar modificaciones
        return None
    
    @classmethod
    def get_file_path(cls) -> Optional[str]:
        """Obtener la ruta del archivo Excel cargado"""
        return cls._file_path if cls.is_excel_loaded() else None
    
    @classmethod
    def get_file_name(cls) -> Optional[str]:
        """Obtener solo el nombre del archivo Excel cargado"""
        if cls._file_path:
            return os.path.basename(cls._file_path)
        return None
    
    @classmethod
    def clear_excel(cls):
        """Limpiar los datos cargados"""
        cls._excel_data = None
        cls._file_path = None
        cls._validated = False
        print("Excel data cleared")
    
    @classmethod
    def get_excel_info(cls) -> Dict[str, Any]:
        """Obtener información resumida del Excel cargado"""
        if not cls.is_excel_loaded():
            return {'loaded': False}
        
        df = cls._excel_data
        return {
            'loaded': True,
            'file_name': cls.get_file_name(),
            'file_path': cls._file_path,
            'rows': df.shape[0],
            'columns': df.shape[1],
            'column_names': list(df.columns),
            'has_saidi': any('SAIDI' in str(col).upper() for col in df.columns),
            'date_range': {
                'start': df.iloc[:, 0].min() if not df.empty else None,
                'end': df.iloc[:, 0].max() if not df.empty else None
            }
        }