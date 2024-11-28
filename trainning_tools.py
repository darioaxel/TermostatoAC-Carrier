import ia_tools
import graphics_tools
import sys
import os
import numpy as np
import tensorflow as tf
from datetime import datetime


LISTA_CLASES = ["fan1","fan2","fan3","cold","hot","dry"]
FOLDER_DUMPS = "dumps"

def preprocess_fn(data, result):
    return data, result

def crear_dataset(datas, results):

    dataset = tf.data.Dataset.from_tensor_slices((datas, results))
    dataset.map(preprocess_fn)

    return dataset.prefetch(buffer_size=tf.data.experimental.AUTOTUNE)

def calcular_predicciones(fichero):
    fichero_path = os.path.join(os.path.dirname(__file__), fichero)
    dataset, resultset = leer_fichero(fichero_path)

    
    return crear_dataset(dataset, None)

def normalizar_datos(datos):
    return np.array([datos], dtype=np.float32)

def leer_fichero(file_name):
    total_data = []
    total_results = []
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
            resultado_list = [float(dato) for dato in resultado.split(",")]
            
            while len(datos_list) < 91:
                datos_list.append(0)
            
            while len(resultado_list) < len(LISTA_CLASES):
                resultado_list.append(0)

            datos_list = normalizar_datos(datos_list)
            resultado_list = normalizar_datos(resultado_list)
            total_data.append(datos_list)
            total_results.append(resultado_list)
    
    return total_data, total_results


def recoger_dataset(folder = None):
    print("Recoger datasets ....")
    total_data = []
    total_results = []
    folder_name = folder if folder else FOLDER_DUMPS
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

def recoger_modelo(layers_cnt=1, neuronas=10):
    modelo = ia_tools.init_modelo(input_schema=(91,1), layers_cnt=int(layers_cnt),npc=int(neuronas))
    return modelo

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

    elif accion == "entrenar":  

        epocas = 100
        dataset_folder = None
        nombre_modelo = None
        save_modelo = False
        layers = 1
        neuronas = 10

        for arg in sys.argv:
            if arg.startswith("epocas="):
                epocas = int(arg.split("=")[1])
            elif arg.startswith("modelo="):
                nombre_modelo = arg.split("=")[1]
            elif arg.startswith("layers="):
                layers = arg.split("=")[1]
            elif arg.startswith("neuronas="):
                neuronas = arg.split("=")[1]
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
   

        modelo = ia_tools.load_modelo(nombre_modelo) if nombre_modelo else recoger_modelo(layers_cnt=layers, neuronas=neuronas)

        dataset = recoger_dataset(dataset_folder)
        result = ia_tools.entrenar_datos(dataset, None, epocas, len(dataset), modelo)
        if save_modelo:
            ia_tools.save_modelo(modelo, "modelo_%s_%s_%s_%s.keras" % (datetime.now().strftime("%Y%m%d_%H%M%S"), epocas, layers, neuronas))
        graphics_tools.mostrar_graf(result)
    elif accion == "prediccion":
        
        nombre_fichero = None
        nombre_modelo = None
        trama = None

        for arg in sys.argv:
            print("*%s" % arg)
            if arg.startswith("modelo="):
                nombre_modelo = arg.split("=")[1]
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
        if nombre_fichero:
            data_pred = calcular_predicciones(nombre_fichero)
        elif trama:
            trama = normalizar_datos(trama)
            data = [np.array([trama], dtype=np.float32)]
            data_pred = crear_dataset(data, None)

        if not data_pred:
            print("No se ha especificado un fichero o una trama")
            return

        ia_tools.predecir(data_pred.take(1), modelo, LISTA_CLASES)

if __name__ == "__main__":
    main()