from datetime import datetime, timedelta
import json
import requests
import os  # Importar os para manejar rutas de directorios

# Definir el directorio por defecto donde se guardarán los archivos JSON
DEFAULT_BASE_PATH = "/app/data"  # Ruta en el contenedor

def build_url(channel_id):
    return f"https://api.thingspeak.com/channels/{channel_id}/feeds.json"

def add_common_params(params, api_key=None, results=8000, start=None):
    """Agregar parámetros comunes como clave API, límite de resultados y fecha de inicio."""
    if api_key:
        params['api_key'] = api_key
    params['results'] = results
    if start:
        params['start'] = start  # Parámetro de inicio para la paginación
    return params

def fetch_data(url, params, filename, base_path=DEFAULT_BASE_PATH):
    """Obtener datos usando paginación y almacenarlos en un archivo JSON."""
    all_data = []
    channel_info = None
    lote = 1  # Contador de lotes
    max_lotes = 100  # Límite para evitar bucles infinitos
    last_entry_time = None

    # Crear el directorio si no existe
    os.makedirs(base_path, exist_ok=True)

    # Combinar el base_path y filename
    filename = os.path.join(base_path, filename)

    while lote <= max_lotes:
        print(f"Descargando lote {lote}...")

        try:
            # Realizar la solicitud con un timeout
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if not channel_info:
                    channel_info = data['channel']
                feeds = data['feeds']
                if not feeds:
                    print("No se encontraron más datos. Finalizando descarga.")
                    break

                all_data.extend(feeds)

                # Si hay menos resultados de los esperados, se ha llegado al final
                if len(feeds) < params['results']:
                    print(f"Último lote recibido con {len(feeds)} entradas. Se ha llegado al final.")
                    break

                # Obtener el último timestamp y ajustarlo para el siguiente lote
                last_entry_time = feeds[-1]['created_at']
                last_entry_datetime = datetime.strptime(last_entry_time, '%Y-%m-%dT%H:%M:%SZ') + timedelta(seconds=1)
                params['start'] = last_entry_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')

                lote += 1  # Incrementar el contador de lote

            else:
                print(f"Error {response.status_code}: {response.text}")
                break

        except requests.exceptions.Timeout:
            print("Se ha superado el tiempo de espera para la solicitud. Reintentando...")
            continue

    result = {
        "channel": channel_info,
        "feeds": all_data
    }

    # Guardar el resultado en un archivo
    with open(filename, 'w') as file:
        json.dump(result, file, indent=4)
    print(f"Datos guardados en '{filename}'")
    print(f"Total de entradas descargadas: {len(all_data)}")

def fetch_all_data(channel_id, api_key=None):
    """Obtener todos los datos de un canal de ThingSpeak."""
    url = build_url(channel_id)
    params = add_common_params({}, api_key)
    filename = 'datosRecuperados_all.json'
    fetch_data(url, params, filename)

def get_data_by_fields(channel_id, fields, api_key=None, results=8000):
    """Obtener datos de campos específicos."""
    for field in fields:
        url = f"https://api.thingspeak.com/channels/{channel_id}/fields/{field}.json"
        params = add_common_params({}, api_key, results)
        filename = f'datosRecuperados_field_{field}.json'
        fetch_data(url, params, filename)

def get_data_from_date(channel_id, start_date=None, end_date=None, api_key=None, results=8000):
    """Obtener datos entre dos fechas."""
    url = build_url(channel_id)
    params = add_common_params({}, api_key, results)
    
    start_datetime = f"{start_date}"
    end_datetime = f"{end_date}"
    
    params['start'] = start_datetime
    params['end'] = end_datetime
    
    filename = f'datosRecuperados_date_{start_date}_to_{end_date}.json'
    fetch_data(url, params, filename)

def get_data_from_date_forward(channel_id, start_date=None, api_key=None, results=8000):
    """Obtener datos desde una fecha hacia adelante."""
    url = build_url(channel_id)
    params = add_common_params({}, api_key, results)

    if start_date:
        start_datetime = f"{start_date}"
        params['start'] = start_datetime  # Establecer la fecha de inicio

    filename = f'datosRecuperados_forward_{start_date}.json'
    fetch_data(url, params, filename)

def get_data_from_date_backward(channel_id, start_date=None, api_key=None, results=8000):
    """Obtener datos desde una fecha hacia atrás."""
    url = build_url(channel_id)
    params = add_common_params({}, api_key, results)

    if start_date:
        start_datetime = f"{start_date}"
        params['end'] = start_datetime  # Establecer la fecha de fin

    filename = f'datosRecuperados_backward_{start_date}.json'
    fetch_data(url, params, filename)
