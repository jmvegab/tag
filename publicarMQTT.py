import paho.mqtt.client as mqtt
import mysql.connector
from mysql.connector import Error

import os

# Configuración de las credenciales MQTT
MQTT_USERNAME = "HA87PA8pMRUeIzksBBU5KTI"
MQTT_PASSWORD = "wBdlHkSB5C3T21DvvKuHw3W9"
MQTT_CLIENT_ID = "HA87PA8pMRUeIzksBBU5KTI"
MQTT_BROKER = "mqtt3.thingspeak.com"
MQTT_PORT = 1883
CHANNEL_ID = 2694778  # ID del canal de estadísticas en ThingSpeak
MQTT_TOPIC = f"channels/{CHANNEL_ID}/publish"

# Función para calcular la media de los atributos desde la base de datos
def calcular_media():
    # Conectar a la base de datos MySQL
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
        
    except mysql.connector.Error as e:
        print(f"Error al conectar a MySQL: {e}")
        return None  # Retornar None en caso de error

    # Si la conexión fue exitosa, crear el cursor y proceder con la consulta
    cursor = conexion.cursor(dictionary=True)

    # Realizar consulta para obtener la media de cada atributo
    query = """
    SELECT 
        AVG(temperatura) AS media_temperatura, 
        AVG(humedad) AS media_humedad, 
        AVG(presion) AS media_presion, 
        AVG(calidad_aire) AS media_calidad_aire, 
        AVG(viento) AS media_viento
    FROM Tfg;
    """
    cursor.execute(query)
    resultado = cursor.fetchone()

    # Cerrar el cursor y la conexión a la base de datos
    cursor.close()
    conexion.close()

    return resultado


# Publicar la media en ThingSpeak usando MQTT
def publicar_media():
    # Calcular la media de los atributos
    medias = calcular_media()
    if medias:
        # Crear el payload con las medias
        payload = {
            "field1": round(medias['media_temperatura'], 2),
            "field2": round(medias['media_humedad'], 2),
            "field3": round(medias['media_presion'], 2),
            "field4": round(medias['media_calidad_aire'], 2),
            "field5": round(medias['media_viento'], 2)
        }
        
        # Publicar los datos en el canal de ThingSpeak
        client = mqtt.Client(client_id=MQTT_CLIENT_ID)
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        client.connect(MQTT_BROKER, MQTT_PORT, 60)

        # Convertir el payload a formato URL para enviarlo
        payload_str = '&'.join([f"{key}={value}" for key, value in payload.items()])
        
        # Publicar el mensaje
        client.publish(MQTT_TOPIC, payload_str)
        print(f"Media publicada: {payload_str}")

        # Desconectar del broker MQTT
        client.disconnect()

# Ejecutar la publicación de la media
if __name__ == "__main__":
    publicar_media()
