import mysql.connector
import json
import sys
from datetime import datetime

# Función para conectarse a MySQL
import mysql.connector
from mysql.connector import Error

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


# Crear la base de datos 'the_things_speak' si no existe
def crear_base_datos_si_no_existe(cursor):
    cursor.execute("CREATE DATABASE IF NOT EXISTS mydatabase")
    cursor.execute("USE mydatabase")

# Crear la tabla con el nombre del archivo JSON si no existe
def crear_tabla_si_no_existe(cursor, nombre_tabla):
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS `{nombre_tabla}` (
        entry_id INT PRIMARY KEY,
        created_at DATETIME,
        temperatura FLOAT,
        humedad FLOAT,
        presion FLOAT,
        calidad_aire INT,
        viento FLOAT
    )
    """)

# Convertir el formato de 'created_at' de ISO 8601 a 'YYYY-MM-DD HH:MM:SS'
def convertir_formato_fecha(fecha_iso):
    try:
        # Convertir la fecha de ISO 8601 a formato compatible con MySQL
        fecha_formateada = datetime.strptime(fecha_iso, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M:%S")
        return fecha_formateada
    except ValueError:
        return None  # Si la conversión falla, devuelve None

# Insertar o actualizar los datos en la tabla
def insertar_o_actualizar_datos(cursor, datos, nombre_tabla):
    for feed in datos['feeds']:
        entry_id = feed['entry_id']
        created_at_iso = feed['created_at']
        created_at = convertir_formato_fecha(created_at_iso)  # Convertir la fecha al formato correcto
        if not created_at:
            print(f"Error al convertir la fecha: {created_at_iso}")
            continue  # Saltar esta fila si la fecha no se pudo convertir

        temperatura = feed.get('field1')
        humedad = feed.get('field2')
        presion = feed.get('field3')
        calidad_aire = feed.get('field4')
        viento = feed.get('field5')

        # Verificar si la entrada ya existe
        cursor.execute(f"SELECT COUNT(*) FROM `{nombre_tabla}` WHERE entry_id = %s", (entry_id,))
        existe = cursor.fetchone()[0]

        if existe:
            # Actualizar datos si ya existe
            cursor.execute(f"""
            UPDATE `{nombre_tabla}` 
            SET created_at = %s, temperatura = %s, humedad = %s, presion = %s, calidad_aire = %s, viento = %s
            WHERE entry_id = %s
            """, (created_at, temperatura, humedad, presion, calidad_aire, viento, entry_id))
            print(f"Datos actualizados para entry_id: {entry_id}")
        else:
            # Insertar datos si no existe
            cursor.execute(f"""
            INSERT INTO `{nombre_tabla}` (entry_id, created_at, temperatura, humedad, presion, calidad_aire, viento) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (entry_id, created_at, temperatura, humedad, presion, calidad_aire, viento))
            print(f"Datos insertados para entry_id: {entry_id}")

# Función principal para procesar el archivo JSON
def procesar_json_a_mysql(nombre_archivo):
    # Abrir el archivo JSON
    with open(nombre_archivo, 'r') as archivo:
        datos = json.load(archivo)

    # Obtener el nombre de la tabla desde el campo 'name' en el archivo JSON
    nombre_tabla = datos['channel']['name']

    # Conectar a la base de datos MySQL
    conexion = conectar_mysql()
    cursor = conexion.cursor()

    # Crear la base de datos si no existe y seleccionarla
    crear_base_datos_si_no_existe(cursor)

    # Crear la tabla si no existe
    crear_tabla_si_no_existe(cursor, nombre_tabla)

    # Insertar o actualizar los datos
    insertar_o_actualizar_datos(cursor, datos, nombre_tabla)

    # Confirmar los cambios
    conexion.commit()

    # Cerrar la conexión
    cursor.close()
    conexion.close()
    print(f"Proceso completado y datos guardados/actualizados en la tabla '{nombre_tabla}' en MySQL.")

# Asegúrate de que se está llamando al archivo JSON correcto desde el menú
if __name__ == "__main__":
    # Reemplaza 'datosRecuperados_all.json' por el archivo que pasas desde el menú
    if len(sys.argv) > 1:
        archivo_json = sys.argv[1]  # Obtiene el archivo que se le pasa como argumento
        procesar_json_a_mysql(archivo_json)  # Procesa el archivo correcto
    else:
        print("Por favor, proporciona un archivo JSON.")
