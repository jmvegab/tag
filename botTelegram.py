import mysql.connector
from mysql.connector import Error

import requests
import os
import re
import json  # Asegúrate de importar json
from datetime import datetime
import sys  # Importar sys para recibir argumentos

# Datos de acceso a la base de datos MySQL
def conectar_mysql():
    try:
        # Intentar conectar a la base de datos
        conexion = mysql.connector.connect(
            host="terraform-20241015231624167800000003.cjia444qy3ck.us-east-1.rds.amazonaws.com",  # Endpoint de tu base de datos RDS
            user="root",       # Usuario de la base de datos
            password="password123",    # Contraseña de la base de datos
            database="mydatabase"  # Especificar la base de datos
        )
        
        if conexion.is_connected():
            print("Conexión exitosa a la base de datos MySQL")
        return conexion
    except Error as e:
        print(f"Error al conectar a MySQL: {e}")
        return None

# Datos del bot de Telegram
BOT_TOKEN = "8042050269:AAHTKqZs_BAu04ccXvvxGwyA1niNgbWGNZY"
CHAT_ID = "1301939829"

# Umbrales para los atributos
UMBRAL_TEMPERATURA_MIN = -9
UMBRAL_TEMPERATURA_MAX = 39
UMBRAL_HUMEDAD_MIN = 15
UMBRAL_HUMEDAD_MAX = 98
UMBRAL_PRESION_MIN = 950
UMBRAL_PRESION_MAX = 1050
UMBRAL_CALIDAD_AIRE_MAX = 490
UMBRAL_VIENTO_MAX = 25

# Función para enviar alerta a Telegram
def enviar_alerta(entry_id, created_at, campo, valor, limite_min, limite_max):
    mensaje = (f"⚠️ Alerta:\n"
               f"Entrada con ID: {entry_id}\n"
               f"Fecha: {created_at}\n"
               f"{campo} superó el rango permitido: {valor} (límite: {limite_min}-{limite_max})")
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': mensaje}
    requests.post(url, data=payload)

# Función para realizar la consulta SQL según el tipo de archivo
def consulta_por_tipo(cursor, nombre_tabla, nombre_archivo):
    print(f"Procesando archivo: {nombre_archivo}")  # Para verificar el archivo correcto

    # Caso 1: Si es 'datosRecuperados_all.json'
    if nombre_archivo == '/app/data/datosRecuperados_all.json':
        cursor.execute(f"SELECT * FROM `{nombre_tabla}`")
        return cursor.fetchall()

    # Caso 2: Si es un Field específico, extraemos el número de Field
    match_field = re.match(r"/app/data/datosRecuperados_field_(\d+)\.json", nombre_archivo)
    if match_field:
        field_number = int(match_field.group(1)) + 2  # Ajuste para que coincida con las columnas en la tabla
        if field_number == 3:
            field_column = "temperatura"
        elif field_number == 4:
            field_column = "humedad"
        elif field_number == 5:
            field_column = "presion"
        elif field_number == 6:
            field_column = "calidad_aire"
        elif field_number == 7:
            field_column = "viento"
        else:
            raise ValueError("El número de Field no corresponde a ninguna columna conocida.")
        
        cursor.execute(f"SELECT entry_id, created_at, {field_column} FROM `{nombre_tabla}`")
        return cursor.fetchall()

    # Caso 3: Si es entre dos fechas
    match_dates = re.match(r"/app/data/datosRecuperados_date_(.+)_to_(.+)\.json", nombre_archivo)
    if match_dates:
        start_date = match_dates.group(1)
        end_date = match_dates.group(2)
        cursor.execute(f"SELECT * FROM `{nombre_tabla}` WHERE created_at BETWEEN '{start_date}' AND '{end_date}'")
        return cursor.fetchall()

    # Caso 4: Si es hacia adelante desde una fecha
    match_forward = re.match(r"/app/data/datosRecuperados_forward_(.+)\.json", nombre_archivo)
    if match_forward:
        start_date = match_forward.group(1)
        cursor.execute(f"SELECT * FROM `{nombre_tabla}` WHERE created_at >= '{start_date}'")
        return cursor.fetchall()

    # Caso 5: Si es hacia atrás desde una fecha
    match_backward = re.match(r"/app/data/datosRecuperados_backward_(.+)\.json", nombre_archivo)
    if match_backward:
        start_date = match_backward.group(1)
        print(f"Start date (forward): {start_date}")  # Imprimir la fecha hacia adelante
        cursor.execute(f"SELECT * FROM `{nombre_tabla}` WHERE created_at <= '{start_date}'")
        return cursor.fetchall()

    return []  # Si no coincide ningún caso

# Función para comprobar los datos de la base de datos y generar alertas
def comprobar_datos_y_enviar_alertas(nombre_archivo):
    conexion = conectar_mysql()
    cursor = conexion.cursor(dictionary=True)

    # Abrir el archivo JSON para obtener el nombre de la tabla
    with open(nombre_archivo, 'r') as archivo:
        datos_json = json.load(archivo)
        nombre_tabla = datos_json['channel']['name']  # Obtener el nombre de la tabla del campo 'name'

    # Consultar según el tipo de archivo
    registros = consulta_por_tipo(cursor, nombre_tabla, nombre_archivo)

    # Revisar cada registro y comprobar si se superan los umbrales
    for registro in registros:
        entry_id = registro['entry_id']
        created_at = registro['created_at']
        temperatura = registro.get('temperatura')
        humedad = registro.get('humedad')
        presion = registro.get('presion')
        calidad_aire = registro.get('calidad_aire')
        viento = registro.get('viento')

        # Comprobar si los valores superan los umbrales
        if temperatura is not None and (temperatura < UMBRAL_TEMPERATURA_MIN or temperatura > UMBRAL_TEMPERATURA_MAX):
            enviar_alerta(entry_id, created_at, "Temperatura", temperatura, UMBRAL_TEMPERATURA_MIN, UMBRAL_TEMPERATURA_MAX)
        if humedad is not None and (humedad < UMBRAL_HUMEDAD_MIN or humedad > UMBRAL_HUMEDAD_MAX):
            enviar_alerta(entry_id, created_at, "Humedad", humedad, UMBRAL_HUMEDAD_MIN, UMBRAL_HUMEDAD_MAX)
        if presion is not None and (presion < UMBRAL_PRESION_MIN or presion > UMBRAL_PRESION_MAX):
            enviar_alerta(entry_id, created_at, "Presión", presion, UMBRAL_PRESION_MIN, UMBRAL_PRESION_MAX)
        if calidad_aire is not None and calidad_aire > UMBRAL_CALIDAD_AIRE_MAX:
            enviar_alerta(entry_id, created_at, "Calidad del aire", calidad_aire, 0, UMBRAL_CALIDAD_AIRE_MAX)
        if viento is not None and viento > UMBRAL_VIENTO_MAX:
            enviar_alerta(entry_id, created_at, "Velocidad del viento", viento, 0, UMBRAL_VIENTO_MAX)

    # Cerrar la conexión
    cursor.close()
    conexion.close()

# Ejecutar la comprobación y envío de alertas
if __name__ == "__main__":
    if len(sys.argv) > 1:
        nombre_archivo_json = sys.argv[1]
    else:
        nombre_archivo_json = 'datosRecuperados_all.json'  # Valor predeterminado si no se pasa argumento
    comprobar_datos_y_enviar_alertas(nombre_archivo_json)
