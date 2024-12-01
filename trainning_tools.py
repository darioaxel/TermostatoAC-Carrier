import ia_tools
import graphics_tools
import sys
import os
import numpy as np
import tensorflow as tf
from datetime import datetime
import config as config_mod


LISTA_CLASES = ["fan1","fan2","fan3","cold","hot","dry"]

CONFIG = config_mod.cargar_configuracion()

def preprocess_fn(data, result):
    return data, result

def crear_dataset(datas, results):

    dataset = tf.data.Dataset.from_tensor_slices((datas, results))
    dataset.map(preprocess_fn)

    return dataset.prefetch(buffer_size=tf.data.experimental.AUTOTUNE)

def calcular_predicciones(fichero):
    fichero_path = os.path.join(os.path.dirname(__file__), fichero)
    dataset, resultset = leer_fichero(fichero_path)
    lista_predicciones = []
    for data in dataset:
        lista_predicciones.append(crear_dataset([data], None))
    
    return lista_predicciones

def normalizar_datos(datos, check_size = False):
    if check_size and len(datos) != 91:
        print("Datos incorrectos, no tiene 91 elementos")
        return False

    return np.array([datos], dtype=np.float32)

def leer_fichero(file_name):
    total_data = []
    total_results = []
    print("Leyendo fichero %s" % file_name)
    with open(file_name, "r") as f:
        # print("recogiendo datos de %s" % file_name)
        data_crudo = f.read()
        datas = data_crudo.split("\n")[1:]
        for data in datas:
            if not data:
                continue
            data_list = data.split(",")

            datos, resultado = data.split(";")
            datos_list = [int(dato) for dato in datos.split(",")]

            resultado_list = resultado.split(",")
            while len(resultado_list) < 8:
                resultado_list.insert(0, "0")
            byte_value = int("".join(resultado_list), 2)
            resultado_list = [byte_value]

            while len(resultado_list) < len(LISTA_CLASES):
                resultado_list.append(0)

            datos_list = normalizar_datos(datos_list, True)
            if datos_list is False:
                print("Omitiendo linea de fichero %s" % file_name)
                continue

            resultado_list = normalizar_datos(resultado_list)
            total_data.append(datos_list)
            total_results.append(resultado_list)
    return total_data, total_results


def recoger_dataset(folder = None):
    print("Recoger datasets ....")
    total_data = []
    total_results = []
    folder_name = folder if folder else CONFIG.get(section='CONFIG', option='dumpsfolder')
    print("Comprobando folder %s" % folder_name)
    num_ficheros = 0
    for file in os.listdir(folder_name):
        nombre_fichero = os.path.join(folder_name, file)
        if not nombre_fichero.endswith("csv"):
            continue
        num_ficheros += 1
        # print("Recogiendo datos de %s" % nombre_fichero)
        data, results = leer_fichero(nombre_fichero)
        total_data.extend(data)
        total_results.extend(results)
    
    print("Recolectadas %d tramas de %s ficheros" % (len(total_data), num_ficheros))

    return crear_dataset(total_data, total_results)

def recoger_modelo(layers):
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
            data_pred = crear_dataset(data, None)
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