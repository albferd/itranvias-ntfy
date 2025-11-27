# encoding = utf-8
import ast
import json
import re
from datetime import datetime
from logging import warning
from time import sleep

import requests

from albertcode import drawtable


'''
Cómo funcionará esto:
1 - Pedir una parada de bus, línea y minutos a los que se quiera vigilar ( tener valores por defecto también)
2- Mirar api cada
'''
LOADING = ['-', '\\', '|', '/']
# Variables
NTFY_HOST = "https://ntfy.sh/"
NTFY_TOPIC = "testchannel-udc"  # Este es también una contraseña; si tienes el 'topic' puedes recibir sus notificaciones
# Técnicamente, se puede bloquear con una cuenta de usuario pero eh
NTFY_PRIORITIES = {
    "max": 5,
    "high": 4,
    "normal": 3,
    "low": 2,
    "min": 1,
}
NOTIFICATION_MINUTES_TRESHOLD = 3
# NOTIFICATION_TEMPLATE = t'{e}'
ITRANVIAS_CHECK_DELAY = 10
ITRANVIAS_URL_ROOT = "https://itranvias.com/queryitr_v3.php"
ITRANVIAS_STOPS_FILE = "paradas.json"
ITRANVIAS_LINES_FILE = "lineas.json"

CONN_MAX_RETRIES = 3

all_stops = []
all_lines = []
line_internal_id = 100

def bus_loop():
    counter = 0
    while True:
        try:
            autobuses = query_buses_at_stop(stop_id, line_internal_id)
            time = int(re.sub('<', '', autobuses[0]['tiempo']))
            print(f"\rPróximo bus en {autobuses[0]['tiempo']} minutos...{LOADING[counter % 4]}",
                  end="")  # todo:use better cr
            if time <= NOTIFICATION_MINUTES_TRESHOLD:
                send_notification(
                    topic=NTFY_TOPIC,
                    title="Bus cerca",
                    message=f'El autobús de l.{line_entered} llega en {time} '
                            f'minutos a {stop_name}...',
                    priority=NTFY_PRIORITIES['max'],
                    tags="bus")
                print("\nNotification sent")
                break
            counter += 1
            sleep(ITRANVIAS_CHECK_DELAY)
        except KeyboardInterrupt:
            print("Ok ok ya paro")
            break


def send_notification(host=NTFY_HOST, topic="test", title="", message="", priority=NTFY_PRIORITIES['normal'],
                      tags=""):
    data = {
        "topic": topic,
        "message": message,
        "title": title,
        "priority": priority,
    }
    requests.post(host, json.dumps(data))


def query_bus_stops():
    pass


def search_line_id_by_name(text="", lines=None):
    if lines is None:
        lines = all_lines
    matching_line = None
    for location in lines:
        if location['lineName'] == text:  # Entered line -> internal ID converter
            matching_line = location['lineId']
            break
    return matching_line


def search_places(text="", places=None):
    if places is None:
        places = all_stops
    matching_places = []
    for location in places:
        if text.lower() in location['name'].lower():
            matching_places.append(location)

    return matching_places


def search_name_by_id(id_n=0, places=None):
    if places is None:
        places = all_stops
        # si no hago esto pycharm me asesina
        # es equivalente a (... places = all_stops): FYI
    matching_place = None
    for location in places:
        if location['id'] == id_n:
            matching_place = location['name']
            break
    if matching_place is None:
        warning(f"Place with id {id_n} not found")
    return matching_place


def query_buses_at_stop(internal_stop_id, line_n=None):
    rq_parameters = {
        "func": 0,  # Para pedir info de parada f = 0
        "dato": internal_stop_id,  # Lo que hace 'dato' depende de cuál 'func' hayas escogido. Tremenda API.
        # En este caso; dato = id de la parada que quieres ver
        "_": (datetime.now() - datetime(1970, 1, 1)).total_seconds()  # timestamp (opcional??)
    }
    retry_count = 0
    while True:
        try:  # Retry if failed
            response_dict = json.loads(requests.get(ITRANVIAS_URL_ROOT, params=rq_parameters).content)
            retry_count = 0
            break
        except:
            retry_count += 1
            if retry_count > CONN_MAX_RETRIES:
                print("\nNo parece que tengas internet; tienes wifi?.")
                quit(6)
            print(f"\rNo se pudo conectar con Itranvias. Reintento {retry_count} de {CONN_MAX_RETRIES}", end="")
            sleep(1)
    if line_n is None:  # Si no se especifica línea; devolverlas todas
        return response_dict
        # 4. Extraer sólo los autobuses de la línea necesaria
    try:
        lines_of_stop = response_dict['buses']['lineas']
    except KeyError:
        quit(7)
    chosen_line = None
    for line in lines_of_stop:
        if line['linea'] == line_internal_id:  # Chosen line
            chosen_line = line
            break
    if chosen_line is None:
        print(f"La línea {line_entered} no pasa por {stop_name}; o ya no hay más autobuses hoy de esa línea...")
        quit(8)
    return chosen_line['buses']


if __name__ == '__main__':
    debugOn = 1
    if debugOn:
        print("debug mode enabled")
    with open(ITRANVIAS_STOPS_FILE, 'r', encoding="utf8") as file:
        all_stops = ast.literal_eval(file.read())
    with open(ITRANVIAS_LINES_FILE, 'r', encoding="utf8") as file:
        all_lines = ast.literal_eval(file.read())
    # 1. Pedir línea
    print('Introduce el nombre de la parada o su número...')
    stop_entered = input('$> ')
    if not stop_entered.isnumeric():
        matching = search_places(stop_entered)
        # todo si se quiere: avisar si hay demasiadas
        if len(matching) == 0:
            print(f'No existe ninguna parada con ese nombre...')
            quit(3)

        elif len(matching) == 1:
            print(f'Se encontró {len(matching)} parada al buscar por \'{stop_entered}\':')
            print(matching[0]['name'])
            stop_entered = matching[0]['id']
        else:
            drawn = []
            for stop in matching:
                drawn.append([stop['name'], stop['id']])
            drawtable(drawn)
            print('Escoge su número.')
            stop_entered = int(input('$> '))

    stop_name = search_name_by_id(int(stop_entered))
    if stop_name is None:
        print(f"La parada con id {stop_entered} no existe.")
        quit(2)
    stop_id = stop_entered
    print(f'Parada {stop_id}: {stop_name}')

    # 2. Pedir línea
    print('Introduce la línea que vayas a usar:')
    line_entered = input('$> ')
    line_internal_id = search_line_id_by_name(line_entered)
    if line_internal_id is None:
        print("Línea no encontrada...")
        quit(4)

    # 3. Hacer la petición y extraer solo el bus necesario
    buses = query_buses_at_stop(stop_id, line_internal_id)
    # todo: remove debug
    if debugOn:
        # debug
        bus_array = []
        for bus in buses:  # convert to array of arrays to throw at drawtable
            bus_array.append([bus['bus'], bus['tiempo']])
        drawtable(bus_array, hlines=False)
        sleep(2)
    # 5. Bucle de comprobar:
    bus_loop()
        # También se puede comprobar si quieres mirar un bus en específico :v
