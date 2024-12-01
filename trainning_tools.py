import ia_tools
import graphics_tools
import trama_tools
import config as config_mod

from datetime import datetime
import numpy as np
import os
import sys

from typing import List, Optional, Any


LISTA_CLASES = ["fan1","fan2","fan3","cold","hot","dry"]

def calcular_predicciones(fichero :str) -> List[Any]:
    fichero_path = os.path.join(os.path.dirname(__file__), fichero)
    dataset, resultset = leer_fichero(fichero_path)
    lista_predicciones = []
    for data in dataset:
        lista_predicciones.append(ia_tools.crear_dataset([data], None))
    
    return lista_predicciones

def normalizar_datos(datos : List[int]) -> list[int]:
    while len(datos) < 94:
        datos.append(0)

    return np.array([datos], dtype=np.float32)

def leer_fichero(file_name: str) -> List[List[int], List[int]]:
    total_data = []
    total_results = []
    file_data = trama_tools.cargar_trama_bytes(file_name)
    
    for data in file_data:
        datos_list = []
        resultado = [int(valor) for valor in data["values"]]
        while len(resultado) < 8:
            resultado.insert(0, "0")

        byte_value = int("".join(resultado), 2)
        resultado_list = [byte_value]


        for valor in data["data"]:
            datos_list.append(int(valor))
    
        datos_list = normalizar_datos(datos_list)
        if datos_list is False:
            print("Omitiendo linea de fichero %s" % file_name)
            continue

        total_data.append(datos_list)
        total_results.append(resultado_list)

    return total_data, total_results


def recoger_dataset(folder : Optional[str] = None):
    print("Recoger datasets ....")
    total_data = []
    total_results = []
    folder_name = folder if folder else config_mod.CONFIG.get(section='CONFIG', option='dumpsfolder')
    print("Comprobando folder %s" % folder_name)
    num_ficheros = 0
    for file in os.listdir(folder_name):
        nombre_fichero = os.path.join(folder_name, file)
        if not nombre_fichero.endswith(".json"):
            continue
        
        lista_ficheros = trama_tools.resuelve_nombre_binarios_lista(nombre_fichero)
        for nombre_fichero_bin in lista_ficheros:
            ruta_fichero = os.path.join(folder_name, nombre_fichero_bin)
            if not os.path.exists(ruta_fichero):
                print("No existe el fichero %s" % ruta_fichero)
                continue
            num_ficheros += 1

            data, results = leer_fichero(ruta_fichero)
            total_data.extend(data)
            total_results.extend(results)
    
    print("Recolectadas %d tramas de %s ficheros" % (len(total_data), num_ficheros))

    return ia_tools.crear_dataset(total_data, total_results)

def recoger_modelo(layers : List[int]) -> Any:
    return ia_tools.init_modelo(input_schema=(91,1), layers=layers, output_shapes=1)

def main():
    # recogemos argumentos
    if not len(sys.argv) > 1:
        print("No se ha especificado ninguna acción")
        return
    
    accion = sys.argv[1]
    if accion == "pesos":
        for arg in sys.argv:
            if arg.startswith("modelo="):
                nombre_modelo = arg.split("=")[1]
                modelo = ia_tools.load_modelo(nombre_modelo)
                ia_tools.mostrar_pesos_modelo(modelo)
            else:
                pos = sys.argv.index(arg)
                if pos < 2:
                    continue
                print("Argumento %s %s desconocido" % (pos, arg))
            return

    if accion == "entrenar":  

        epocas = None
        dataset_folder = None
        nombre_modelo = None
        save_modelo = False
        layers = None
        neuronas = None

        for arg in sys.argv:
            if arg.startswith("epocas="):
                epocas = int(arg.split("=")[1])
            elif arg.startswith("modelo="):
                nombre_modelo = arg.split("=")[1]
            elif arg.startswith("layers="):
                layers = arg.split("=")[1].split(",")
            elif arg.startswith("dataset="):
                dataset_folder = recoger_dataset(arg.split("=")[1])
            elif arg == "save":
                save_modelo = True
            else:
                pos = sys.argv.index(arg)
                if pos < 2:
                    continue
                print("Argumento %s %s desconocido" % (pos, arg))
                return

        if not epocas:
            epocas = 1000
        
        if not layers:
            layers = [10]


        modelo = ia_tools.load_modelo(nombre_modelo) if nombre_modelo else recoger_modelo(layers=layers)

        dataset = recoger_dataset(dataset_folder)
        result = ia_tools.entrenar_datos(dataset, None, epocas, len(dataset), modelo)
        if save_modelo:
            epocas_entrenadas, layers_modelo = ia_tools.recoge_datos_modelo(modelo)
            if not epocas_entrenadas:
                epocas_entrenadas = epocas
            time_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ia_tools.save_modelo(modelo, "modelo__%s__%s_%s.keras" % ("_".join(layers_modelo), epocas_entrenadas, time_stamp))
        graphics_tools.mostrar_graf(result)
    elif accion == "prediccion":
        
        nombre_fichero = None
        nombre_modelo = None
        trama = None

        for arg in sys.argv:
            print("*%s" % arg)
            if arg.startswith("modelo="):
                nombre_modelo = arg.split("=")[1]
            elif arg.startswith("fichero="):
                nombre_fichero = arg.split("=")[1]
            elif arg.startswith("trama="):
                trama = arg.split("=")[1].split(",")
                trama = [int(t) for t in trama]
            else:
                pos = sys.argv.index(arg)
                if pos < 2:
                    continue
                print("Argumento %s %s desconocido" % (pos, arg))
                return
        
        if not nombre_modelo:
            print("No se ha especificado un modelo")
            return

        modelo = ia_tools.load_modelo(nombre_modelo)
        data_pred = None

        lista_tramas = []

        if nombre_fichero:
            print("Nombre fichero %s" % nombre_fichero)
            lista_tramas = calcular_predicciones(nombre_fichero)
        elif trama:
            trama = normalizar_datos(trama, True)
            data = [np.array([trama], dtype=np.float32)]
            data_pred = ia_tools.crear_dataset(data, None)
            lista_tramas.append(data_pred)

        if not lista_tramas:
            print("No se ha especificado un fichero o una trama")
            return

        print("Procesando %s predicciones" % len(lista_tramas))
        for trama_ in lista_tramas:
            ia_tools.predecir(trama_.take(1), modelo, LISTA_CLASES)

    else:
        print("Acción %s desconocida" % accion)
        return

if __name__ == "__main__":
    main()