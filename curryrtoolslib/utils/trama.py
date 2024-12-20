import numpy as np
from datetime import datetime
import json
import uuid
import os
from typing import List, Any, Union, Dict, Tuple
from .. import CONFIG

VALID_SIZES = [85,88,91,94]

def validar_trama_bytes(trama_bytes: List[bytes]) -> bool:
    valid = True
    if not trama_bytes[0:2] != [b"\x00",b"\x08"]:
        print("Trama inválida (No comienza por 0,8)",trama_bytes)
        valid = False
    elif len(trama_bytes) not in VALID_SIZES:
        print("Trama inválida (No tiene %s bytes):" % (VALID_SIZES), trama_bytes)
        valid = False
    
    return valid

def guardar_trama_bytes(stream_arr: List[bytes], times_arr : List[List[str]], baudrate: int, timeout : float, values : str = "") -> str:
    folder_dums = CONFIG.get('dumpsfolder')
    file_name = str(uuid.uuid4())
    trama_file = os.path.join(folder_dums, "%s.bin" % file_name)
    info_file = os.path.join(folder_dums, "%s.info" % file_name)

    with open(trama_file, "wb") as f:
        for data in stream_arr:
            f.write(data)

    info_json: Dict[str,Union[str,int, float, List[List[str]]]] = {}
    info_json["stream"] = trama_file
    info_json["blocks"] = len(times_arr)
    info_json["timeout"] = timeout
    info_json["baudrate"] = baudrate
    info_json["times"] = times_arr
    info_json["uuid"] = file_name
    info_json["values"] = values or ""
    with open(info_file, "w") as f:
        json.dump(info_json, f, indent=4, sort_keys=True)

    return file_name

def resuelve_nombre_binarios_lista(nombre_lista):
    if not os.path.exists(nombre_lista):
        print("No existe el fichero %s" % nombre_lista)
        return []

    data_json = json.load(open(nombre_lista, "r"))
    return data_json["files"]

def crear_lista_json(lista: dict[str, Any], posiciones: str, baudrate: int) -> bool:

    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    dumps_folder = os.path.abspath(CONFIG.get('dumpsfolder'))
    hex_filename = os.path.abspath(os.path.join(dumps_folder, 'dump_list_%s.json'% (timestamp)))
    # f'datos_hex_{baudrate}_{"-".join(posiciones.split(","))}
    json.dump(lista, open(hex_filename, "w"), indent=4, sort_keys=True)
    print(f"Datos guardados en {hex_filename}")

    return True


def cargar_trama_bytes(trama_file: str) -> Union[Tuple[None, None] ,List[Dict[str, Any]]]:

    info_file = trama_file.replace(".bin", ".info")

    if not os.path.exists(trama_file):
        print("No existe el fichero %s" % trama_file)
        return None, None

    if not os.path.exists(info_file):
        print("No existe el fichero %s" % info_file)
        return None, None

    info_json = json.load(open(info_file, "r"))
    stream = open(trama_file, "rb").read()

    result: List[Dict[str, Any]] = []

    pos_stream = 0
    last_time = None
    for times, size_ in info_json["times"]:
        data = stream[pos_stream : pos_stream + size_]
        pos_stream += size_
        new_data = {
            "data" : data,
            "timeout" : info_json["timeout"],
            "time" : times[0],
            "values" : info_json["values"]
        }
        result.append(new_data)

    return result


def normalizar_datos(layer_size: int, datos : List[int], check_size: bool = False) -> Union[bool, List[Tuple[List[int], Any]]]:
    if check_size:
        orig_size = len(datos)

        while len(datos) < layer_size:
            datos.append(0)

        datos_size = len(datos)
        if datos_size > layer_size:
            print("Error en la trama, demasiados datos (%s). Limite: %s" % (datos_size, layer_size))
            print(datos)
            return False
        #if datos_size > orig_size:
        #    print(" *** Trama normalizada de %s a %s" % (orig_size, datos_size))

    return np.array([datos], dtype=np.float32) # type: ignore[return-value]

def normalizar_bloque(bloque: int, data: List[int]) -> List[int]:
    """Elimina posiciones datos no necesarios conocidos."""
    result = []
    for pos,valor in enumerate(data):
        if pos in [0]: #Elimina 0x00 iniciales
            continue
        elif bloque in [0,1,2]:
            if pos in [1,2,3,4] and valor == 8: # elimina los 0x08 de los campos 1,2,3,4.
                continue
        elif bloque in [3,4,5]:
            if pos in [1,2] and valor == 8: # elimina los 0x04 de los campos 5,6,7,8.
                continue
        result.append(valor)

    return result

