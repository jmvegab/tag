import sys
import logging
import os
from datetime import datetime, timezone
from subprocess import call

# Importar funciones del archivo de ThingSpeak
from thingspeak import (
    get_data_from_date_backward,
    get_data_from_date_forward,
    fetch_all_data,
    get_data_by_fields,
    get_data_from_date
)

# Configuración del sistema de logging
def setup_logger():
    """Configura el sistema de logging con archivo rotativo diario."""
    log_filename = datetime.now().strftime('logs_%Y-%m-%d.log')  # Archivo de log por día
    logging.basicConfig(
        filename=log_filename,
        level=logging.DEBUG,  # Captura todos los niveles de log
        format='%(asctime)s - %(levelname)s - %(message)s',  # Formato detallado
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def log_action(action, level='info'):
    """Registra una acción en el log con un nivel específico."""
    if level == 'info':
        logging.info(action)
    elif level == 'warning':
        logging.warning(action)
    elif level == 'error':
        logging.error(action)
    else:
        logging.debug(action)

def log_exception(e):
    """Registra excepciones o errores."""
    logging.exception(f"Excepción capturada: {e}")

# Inicializar el sistema de logging
setup_logger()

def mostrar_comandos_disponibles():
    """Muestra los comandos disponibles en el menú."""
    print("\n*** Comandos Disponibles ***")
    print("-tspk -fetch_all    -> Descargar toda la información en ThingSpeak")
    print("-tspk -f <campos>   -> Descargar información de los campos especificados (ej: 1,2) en ThingSpeak")
    print("-tspk -d <fecha_inicio> <hora_inicio> <fecha_fin> <hora_fin> -> Descargar entre dos fechas y horas")
    print("-tspk -dfwd <fecha> -> Descargar información desde una fecha hacia adelante")
    print("-tspk -db <fecha>   -> Descargar información desde una fecha hacia atrás")
    print("salir               -> Salir del programa\n")

# Función para obtener la fecha y hora en formato ISO 8601 completo, con zona horaria UTC
def format_date_time_input(date_str, time_str):
    try:
        dt = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %H:%M:%S")
        dt_utc = dt.replace(tzinfo=timezone.utc)
        return dt_utc.isoformat()
    except ValueError:
        log_action(f"Error en formato de fecha/hora: {date_str} {time_str}", level='error')
        raise ValueError("Formato de fecha u hora no válido.")

def parse_fields(fields_str):
    """Convierte una cadena de campos separados por comas a una lista."""
    return fields_str.split(',')

def ejecutar_mysql_bot_y_mqtt(nombre_archivo_json):
    """Ejecuta el módulo de MySQL, el bot de Telegram y luego MQTT con el nombre del archivo JSON generado."""
    ruta_archivo_json = os.path.join("/app/data", nombre_archivo_json)  # Construir la ruta completa del archivo
    print(f"Procesando el archivo JSON: {ruta_archivo_json}")  # Imprimir la ruta completa del archivo JSON que se está pasando
    
    # Ejecutar mysql.py con la ruta completa del archivo generado
    call(['python3', 'mySQL.py', ruta_archivo_json])
    
    # Ejecutar botTelegram.py pasando la ruta completa del archivo generado como argumento
    call(['python3', 'botTelegram.py', ruta_archivo_json])  # Asegúrate de pasar la ruta completa
    
    # Ejecutar publicarMQTT.py para publicar en el canal MQTT (si este script no requiere del archivo JSON)
    call(['python3', 'publicarMQTT.py'])

def handle_command(args):
    """Procesa los comandos dados por el usuario."""
    if len(args) == 1 and args[0].lower() == 'salir':
        print("Saliendo del programa...")
        sys.exit()

    if len(args) < 2:
        mostrar_comandos_disponibles()
        return

    platform = args[0]  # La plataforma seleccionada
    command = args[1]   # El comando ingresado

    if platform == '-tspk':  # ThingSpeak seleccionado
        channel_id = input("Introduce el Channel ID de ThingSpeak: ")

        if command == '-fetch_all':
            log_action("Comando ejecutado: Descargar toda la información", level='info')
            archivo_generado = 'datosRecuperados_all.json'
            fetch_all_data(channel_id)
            ejecutar_mysql_bot_y_mqtt(archivo_generado)

        elif command == '-f':
            if len(args) < 3:
                print("Debe proporcionar los campos con el comando `-f`.")
                return
            fields = parse_fields(args[2])
            log_action(f"Comando ejecutado: Descargar información por campos {fields}", level='info')
            field_str = ','.join(fields)  # Convertir lista en cadena sin corchetes
            archivo_generado = f'datosRecuperados_field_{field_str}.json'
            get_data_by_fields(channel_id, fields)
            ejecutar_mysql_bot_y_mqtt(archivo_generado)

        elif command == '-d':
            if len(args) < 6:
                print("Debe proporcionar fecha de inicio, hora de inicio, fecha de fin y hora de fin con el comando `-d`.")
                print("Ejemplo: -d 01/01/2023 00:00:00 02/01/2023 23:59:59")
                return
            start_date = format_date_time_input(args[2], args[3])
            end_date = format_date_time_input(args[4], args[5])
            log_action(f"Comando ejecutado: Descargar información entre {start_date} y {end_date}", level='info')
            archivo_generado = f'datosRecuperados_date_{start_date}_to_{end_date}.json'
            get_data_from_date(channel_id, start_date=start_date, end_date=end_date)
            ejecutar_mysql_bot_y_mqtt(archivo_generado)

        elif command == '-dfwd':
            if len(args) < 3:
                print("Debe proporcionar la fecha de inicio con el comando `-dfwd`.")
                return
            start_date = format_date_time_input(args[2], "00:00:00")
            log_action(f"Comando ejecutado: Descargar información desde {start_date} hacia adelante", level='info')
            archivo_generado = f'datosRecuperados_forward_{start_date}.json'
            get_data_from_date_forward(channel_id, start_date=start_date)
            ejecutar_mysql_bot_y_mqtt(archivo_generado)

        elif command == '-db':
            if len(args) < 3:
                print("Debe proporcionar la fecha de inicio con el comando `-db`.")
                return
            start_date = format_date_time_input(args[2], "00:00:00")
            log_action(f"Comando ejecutado: Descargar información desde {start_date} hacia atrás", level='info')
            archivo_generado = f'datosRecuperados_backward_{start_date}.json'
            get_data_from_date_backward(channel_id, start_date=start_date)
            ejecutar_mysql_bot_y_mqtt(archivo_generado)

        else:
            print("Comando no reconocido para ThingSpeak.")
            mostrar_comandos_disponibles()

    elif platform == '-ttn':  # The Things Network seleccionado
        print("Funcionalidad para The Things Network aún no implementada.")
        log_action("Funcionalidad de The Things Network seleccionada pero no implementada", level='info')
    else:
        print("Plataforma no reconocida. Usa `-tspk` para ThingSpeak o `-ttn` para The Things Network.")
        mostrar_comandos_disponibles()

def main():
    # Mostrar comandos disponibles al iniciar
    mostrar_comandos_disponibles()

    while True:
        print("\n*** Menú Principal ***")
        command_input = input("Introduce un comando (o 'salir' para terminar): ").split()

        # Manejar comando de salida antes de procesar otros comandos
        if 'salir' in command_input:
            print("Saliendo del programa...")
            sys.exit()

        handle_command(command_input)

if __name__ == "__main__":
    main()
