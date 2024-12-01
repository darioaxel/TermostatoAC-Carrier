import config as config_mod
from datetime import datetime
import uuid
import os
import json
from typing import List, Any

VALID_SIZES=[85,88,91,94]

""" def pre_proccess_trama(trama: str, file_time: str):
    
    # Preprocesa una trama de datos para su envío.

    # :param trama: La trama de datos a preprocesar.
    # :return: La trama preprocesada.

    times_trama = []    
    with open("%s.time" % file_time, "r") as f:
        for linea in f.readlines():
            times_trama.append(float(linea.strip()))

    lineas = []
    linea_actual = []
    for num, byte_str in enumerate(trama):
        byte = byte_str.encode()
        if byte == b"\x00":
            if num < len(trama) - 1 and trama[num + 1].encode() == b"\x08":
                if linea_actual:
                    lineas.append(linea_actual)
                linea_actual = []
        linea_actual.append(byte)
    
    if linea_actual:
        lineas.append(linea_actual)

    return [[linea, times_trama[num]] for num, linea in  enumerate(lineas)] """

def validar_trama_bytes(trama_bytes: List[bytes]) -> bool:
    valid = True
    if not trama_bytes[0:2] != [b"\x00",b"\x08"]:
        print("Trama inválida (No comienza por 0,8)",trama_bytes)
        valid = False
    elif len(trama_bytes) not in VALID_SIZES:
        print("Trama inválida (No tiene %s bytes):" % (VALID_SIZES), trama_bytes)
        valid = False
    
    return valid

def guardar_trama_bytes(stream: List[bytes], times_arr : List[List[float]], baudrate: int, timeout : float, values : str = ""):
    folder_dums = config_mod.CONFIG.get(section='CONFIG', option='dumsfolder')
    file_name = str(uuid.uuid4())
    trama_file = os.path.join(folder_dums, "%s.bin" % file_name)
    info_file = os.path.join(folder_dums, "%s.info" % file_name)

    with open(trama_file, "wb") as f:
        for data in stream:
            f.write(data)

    info_json = {}
    info_json["stream"] = trama_file
    info_json["blocks"] = len(times_arr)
    info_json["timeout"] = timeout
    info_json["baudrate"] = baudrate
    info_json["times"] = {}
    info_json["uuid"] = file_name
    info_json["values"] = values or ""
    for num, time_arr in enumerate(times_arr):
        time = time_arr[0]
        size = time_arr[1]

        info_json["times"][num] = {
            "size" : size,
            "begin" : time[0],
            "first" : time[1],
            "final" : time[2]
        }
        
    json.dump(info_json, open(info_file, "w"))

    return file_name

def resuelve_nombre_binarios_lista(nombre_lista):
    if not os.path.exists(nombre_lista):
        print("No existe el fichero %s" % nombre_lista)
        return []

    data_json = json.load(open(nombre_lista, "r"))
    return data_json["files"]

def crear_lista_json(lista: dict[str, Any], posiciones: str, baudrate: int) -> bool:

    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    dumps_folder = os.path.abspath(config_mod.CONFIG.get(section='CONFIG', option='dumpsfolder'))
    hex_filename = os.path.abspath(os.path.join(dumps_folder, 'dump_list_%s.json'% (timestamp)))
    # f'datos_hex_{baudrate}_{"-".join(posiciones.split(","))}
    json.dump(lista, open(hex_filename, "w"))
    print(f"Datos guardados en {hex_filename}")

    return True


def cargar_trama_bytes(file_name: str) -> List[List[bytes], List[float]]:
    folder_dums = config_mod.CONFIG.get(section='CONFIG', option='dumsfolder')
    trama_file = file_name if "/" in file_name else os.path.join(folder_dums, "%s.bin" % file_name)
    info_file = trama_file.replace(".bin", ".info")

    if not os.path.exists(trama_file):
        print("No existe el fichero %s" % trama_file)
        return None, None

    if not os.path.exists(info_file):
        print("No existe el fichero %s" % info_file)
        return None, None

    info_json = json.load(open(info_file, "r"))
    stream = open(trama_file, "rb").read()

    result = []

    pos_stream = 0
    for num, block in enumerate(info_json["blocks"]):
        data = stream[pos_stream : pos_stream + block["size"]]
        pos_stream += block["size"]
        timeout = calcular_timeout(block, info_json["timeout"])
        new_data = {
            "data" : data,
            "timeout" : timeout,
            "values" : info_json["values"]
        }
        result.append(new_data)

    return result

def calcular_timeout(block : dict[str, float], default_timeout: float) -> float:
    """Calcula el timepo que hay que dejar para enviar la siguiente trama."""
    return (block["final"] - default_timeout) - (block["first"]  - block["begin"])