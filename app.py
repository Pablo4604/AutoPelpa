import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
import time
from flask import Flask, render_template

app = Flask(__name__)

def get_time_range():
    """
    Siempre devuelve el rango de las próximas 24 horas en ART
    """
    art_tz = timezone(timedelta(hours=-3))
    start_time = datetime.now(art_tz)
    end_time = start_time + timedelta(hours=24)
    
    print(f"🔍 Rango de búsqueda automático: Próximas 24 horas (ART)")
    print(f"   Desde: {start_time.strftime('%Y-%m-%d %H:%M')} ART")
    print(f"   Hasta: {end_time.strftime('%Y-%m-%d %H:%M')} ART")
    
    return start_time, end_time

def get_flight_data_from_fr24(url, flight_type):
    """
    Obtiene datos de FlightRadar24 para llegadas o salidas
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Referer': 'https://www.flightradar24.com/',
        'Origin': 'https://www.flightradar24.com'
    }
    
    try:
        print(f"📥 Obteniendo {flight_type}...")
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            flights = data.get('result', {}).get('response', {}).get('airport', {}).get('pluginData', {}).get('schedule', {}).get(flight_type, {}).get('data', [])
            print(f"✅ {len(flights)} {flight_type} obtenidos")
            return flights
        else:
            print(f"❌ Error HTTP {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Error al obtener {flight_type}: {e}")
        return []

def process_flight_data(flights, flight_type, start_timestamp, end_timestamp):
    """
    Procesa los datos de vuelos y filtra por Aerolíneas Argentinas y rango horario
    """
    processed_data = []
    
    for flight in flights:
        try:
            # Información de la aerolínea
            airline = flight.get('flight', {}).get('airline', {})
            airline_code = airline.get('code', {}).get('iata', '')
            
            # Solo procesar vuelos de Aerolíneas Argentinas (AR)
            if airline_code != 'AR':
                continue
            
            # Número de vuelo (corregido para evitar duplicación ARAR)
            flight_number_data = flight.get('flight', {}).get('identification', {}).get('number', {})
            flight_number = flight_number_data.get('default', '') or flight_number_data.get('number', '')
            
            # Remover "AR" duplicado si existe
            if flight_number.startswith('AR'):
                flight_number = flight_number[2:]
            
            # Matrícula
            registration = flight.get('flight', {}).get('aircraft', {}).get('registration', '')
            
            # Tiempos - usar estimated o scheduled como fallback
            time_data = flight.get('flight', {}).get('time', {})
            scheduled_time = time_data.get('scheduled', {}).get(f"{'arrival' if flight_type == 'arrivals' else 'departure'}", 0)
            estimated_time = time_data.get('estimated', {}).get(f"{'arrival' if flight_type == 'arrivals' else 'departure'}", 0)
            
            # Usar estimated si está disponible, sino scheduled
            flight_time = estimated_time if estimated_time else scheduled_time
            
            # Filtrar por rango de tiempo
            if not (start_timestamp <= flight_time <= end_timestamp):
                continue
            
            # Aeropuertos
            if flight_type == 'arrivals':
                origin = flight.get('flight', {}).get('airport', {}).get('origin', {}).get('code', {}).get('iata', '')
                destination = 'COR'
            else:
                origin = 'COR'
                destination = flight.get('flight', {}).get('airport', {}).get('destination', {}).get('code', {}).get('iata', '')
            
            # Convertir timestamp a formato HH:MM (en ART)
            art_tz = timezone(timedelta(hours=-3))
            time_dt = datetime.fromtimestamp(flight_time, tz=art_tz) if flight_time else None
            time_str = time_dt.strftime('%H:%M') if time_dt else ''
            
            flight_info = {
                'tipo': 'Llegada' if flight_type == 'arrivals' else 'Salida',
                'numero_vuelo': f"AR{flight_number}",
                'hora': time_str,
                'aeropuerto': origin if flight_type == 'arrivals' else destination,
                'matricula': registration,
                'timestamp': flight_time
            }
            
            processed_data.append(flight_info)
            
        except Exception as e:
            print(f"Error procesando vuelo: {e}")
            continue
    
    return processed_data

def combine_arrivals_departures(arrivals, departures):
    """
    Combina llegadas y salidas por matrícula según las reglas especificadas
    """
    combined_data = []
    processed_matriculas = set()
    
    # Excepciones - vuelos que deben permanecer separados
    exception_vuelos = {'AR1550', 'AR1587', 'AR1552', 'AR1551', 'AR1553'}
    
    # Primero procesar las excepciones
    for flight in arrivals + departures:
        if flight['numero_vuelo'] in exception_vuelos:
            if flight['tipo'] == 'Llegada':
                combined_data.append({
                    'llegada': flight['numero_vuelo'],
                    'salida': '',
                    'hora_llegada': flight['hora'],
                    'hora_salida': '',
                    'origen': flight['aeropuerto'],
                    'destino': '',
                    'matricula': flight['matricula']
                })
            else:
                combined_data.append({
                    'llegada': '',
                    'salida': flight['numero_vuelo'],
                    'hora_llegada': '',
                    'hora_salida': flight['hora'],
                    'origen': '',
                    'destino': flight['aeropuerto'],
                    'matricula': flight['matricula']
                })
            processed_matriculas.add(flight['matricula'])
    
    # Combinar llegadas y salidas normales por matrícula
    for arrival in arrivals:
        if arrival['matricula'] in processed_matriculas or arrival['numero_vuelo'] in exception_vuelos:
            continue
        
        # Buscar salida correspondiente
        matching_departure = None
        for departure in departures:
            if (departure['matricula'] == arrival['matricula'] and 
                departure['matricula'] not in processed_matriculas and
                departure['numero_vuelo'] not in exception_vuelos):
                matching_departure = departure
                break
        
        if matching_departure:
            combined_data.append({
                'llegada': arrival['numero_vuelo'],
                'salida': matching_departure['numero_vuelo'],
                'hora_llegada': arrival['hora'],
                'hora_salida': matching_departure['hora'],
                'origen': arrival['aeropuerto'],
                'destino': matching_departure['aeropuerto'],
                'matricula': arrival['matricula']
            })
            processed_matriculas.add(arrival['matricula'])
            processed_matriculas.add(matching_departure['matricula'])
        else:
            # Solo llegada
            combined_data.append({
                'llegada': arrival['numero_vuelo'],
                'salida': '',
                'hora_llegada': arrival['hora'],
                'hora_salida': '',
                'origen': arrival['aeropuerto'],
                'destino': '',
                'matricula': arrival['matricula']
            })
            processed_matriculas.add(arrival['matricula'])
    
    # Agregar salidas sin llegada correspondiente
    for departure in departures:
        if (departure['matricula'] not in processed_matriculas and 
            departure['numero_vuelo'] not in exception_vuelos):
            combined_data.append({
                'llegada': '',
                'salida': departure['numero_vuelo'],
                'hora_llegada': '',
                'hora_salida': departure['hora'],
                'origen': '',
                'destino': departure['aeropuerto'],
                'matricula': departure['matricula']
            })
            processed_matriculas.add(departure['matricula'])
    
    return combined_data

def export_to_excel(combined_data):
    """
    Exporta los datos combinados a Excel - SIEMPRE con nombre "vuelos.xlsx"
    """
    if not combined_data:
        print("No hay datos para exportar")
        return False
    
    # Crear DataFrame
    df = pd.DataFrame(combined_data)
    
    # Ordenar por matrícula y luego por hora de llegada/salida
    if 'hora_llegada' in df.columns and 'hora_salida' in df.columns:
        df['orden_temporal'] = df['hora_llegada'].where(df['hora_llegada'] != '', df['hora_salida'])
        df = df.sort_values('orden_temporal')
        df = df.drop('orden_temporal', axis=1)
    
    # Columnas en el orden correcto
    column_order = ['llegada', 'salida', 'hora_llegada', 'hora_salida', 'origen', 'destino', 'matricula']
    df = df[column_order]
    
    # Reemplazar NaN y None con celdas vacías
    df = df.fillna('')
    
    # NOMBRE FIJO - SIEMPRE "vuelos.xlsx"
    filename = "vuelos.xlsx"
    
    # Exportar a Excel
    try:
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Vuelos COR', index=False)
            
            # Autoajustar columnas
            worksheet = writer.sheets['Vuelos COR']
            for idx, col in enumerate(df.columns):
                max_length = max(df[col].astype(str).apply(len).max(), len(col))
                worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 20)
        
        print(f"\n✅ Datos exportados exitosamente a: {filename}")
        print(f"📊 Total de registros: {len(df)}")
        return True
        
    except Exception as e:
        print(f"❌ Error al exportar a Excel: {e}")
        return False

def main():
    """
    Función principal - Ejecución automática de 24 horas
    Retorna los datos combinados en lugar de exportar
    """
    print("=" * 60)
    print("       SISTEMA AUTOMÁTICO DE VUELOS - AEROLÍNEAS AR")
    print("           Aeropuerto de Córdoba (COR)")
    print("=" * 60)
    print()
    
    # Obtener rango de tiempo automático (siempre 24 horas)
    start_time, end_time = get_time_range()
    start_timestamp = int(start_time.timestamp())
    end_timestamp = int(end_time.timestamp())
    
    # URLs de FlightRadar24
    arrivals_url = "https://api.flightradar24.com/common/v1/airport.json?code=COR&plugin[]=schedule&plugin-setting[schedule][mode]=arrivals&page=1&limit=100"
    departures_url = "https://api.flightradar24.com/common/v1/airport.json?code=COR&plugin[]=schedule&plugin-setting[schedule][mode]=departures&page=1&limit=100"
    
    # Obtener y procesar llegadas
    arrivals_raw = get_flight_data_from_fr24(arrivals_url, 'arrivals')
    arrivals_processed = process_flight_data(arrivals_raw, 'arrivals', start_timestamp, end_timestamp)
    
    # Obtener y procesar salidas
    departures_raw = get_flight_data_from_fr24(departures_url, 'departures')
    departures_processed = process_flight_data(departures_raw, 'departures', start_timestamp, end_timestamp)
    
    print(f"\n📊 Resumen:")
    print(f"   Llegadas AR encontradas: {len(arrivals_processed)}")
    print(f"   Salidas AR encontradas: {len(departures_processed)}")
    
    if not arrivals_processed and not departures_processed:
        print("❌ No se encontraron vuelos de Aerolíneas Argentinas en el rango de 24 horas")
        return []
    
    # Combinar llegadas y salidas
    print("🔄 Combinando llegadas y salidas por matrícula...")
    combined_data = combine_arrivals_departures(arrivals_processed, departures_processed)
    
    if not combined_data:
        print("❌ No se pudieron combinar los datos")
        return []
    
    # Ordenar los datos combinados por tiempo (hora_llegada o hora_salida)
    for item in combined_data:
        item['orden_temporal'] = item['hora_llegada'] if item['hora_llegada'] else item['hora_salida']
    combined_data.sort(key=lambda x: x['orden_temporal'])
    for item in combined_data:
        del item['orden_temporal']
    
    return combined_data

@app.route('/')
def index():
    combined_data = main()
    return render_template('index.html', data=combined_data)

if __name__ == "__main__":
    app.run(debug=True)