from . common_interface import CommonInterface
from .. import CONFIG
from .. utils import ia as ia_tools
from .. utils import trama as trama_tools
from .. utils import graphics
from datetime import datetime
import optparse
import sys
import os
import numpy as np

LISTA_CLASES = ["fan1","fan2","fan3","cold","hot","dry"]


from typing import List, Union, Optional, Any

class TrainningInterface(CommonInterface):

    valid_sizes: List[int]

    def __init__(self):
        super().__init__()
               
    def execute_actions(self):
        action = sys.argv[2]
        if action == "menu":
            main_menu(self)
        elif action == "pesos":
            
            if not self.check_not_null(['modelfile']):
                print("Uso: %s trainning pesos -m <file>" % sys.argv[0])
                sys.exit(1)

            nombre_modelo = self.config['modelfile']
            modelo = ia_tools.load_modelo(nombre_modelo, self.config['modelofolder'])
            if modelo:
                ia_tools.mostrar_pesos_modelo(modelo)

        elif action == "entrenar":
            if not self.check_not_null(['layers','epocs','dumpsfolder']):
                print("Uso: %s trainning begin -m <file>" % sys.argv[0])
                sys.exit(1)

            nombre_modelo = self.config['modelfile']
            layers = self.config['layers'].split(",")
            epocas = int(self.config['epocs'])
            dataset_folder = self.config['dumpsfolder']
            save_modelo = self.config["savefile"]
            modelo = ia_tools.load_modelo(nombre_modelo, self.config['modelofolder']) if nombre_modelo else self.recoger_modelo(layers=layers)

            dataset = self.recoger_dataset(dataset_folder)
            result = ia_tools.entrenar_datos(dataset, None, epocas, len(dataset), modelo)
            if save_modelo:
                epocas_entrenadas, layers_modelo = ia_tools.recoge_datos_modelo(modelo)
                if not epocas_entrenadas:
                    epocas_entrenadas = epocas
                time_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                ia_tools.save_modelo(self.config, modelo, "modelo__%s__%s_%s.keras" % ("_".join(layers_modelo), epocas_entrenadas, time_stamp))
            graphics.mostrar_graf(result)

        else:
            print("Accion %s no reconocida" % (action))

    def parse_args(self, custom_argv: Optional[List[str]] = None) -> optparse.Values:
        parser = optparse.OptionParser()
        parser.add_option('-m', '--model_file', dest='modelfile', help='Archivo del modelo', default=None)
        parser.add_option('-l', '--layers', dest='layers', help='Capas', default="20,20,20")
        parser.add_option('-e', '--epocs', dest='epocs', help='Epocas', default="10000")
        parser.add_option('-s', '--savefile', dest='savefile', help='Guardar archivo del modelo entrenado', action="store_true", default=True)
        
        (options, args) = parser.parse_args(custom_argv)
        return self.load_config(options)


    def calcular_predicciones(self, fichero :str) -> List[Any]:
        fichero_path = os.path.join(os.path.dirname(__file__), fichero)
        dataset, resultset = self.leer_fichero(fichero_path)
        lista_predicciones = []
        for data in dataset:
            lista_predicciones.append(ia_tools.crear_dataset([data], None))
        
        return lista_predicciones

    def normalizar_datos(self, datos : List[int]) -> list[int]:
        while len(datos) < 94:
            datos.append(0)

        return np.array([datos], dtype=np.float32)

    def leer_fichero(self, file_name: str) -> Union[List[int], List[int]]:
        print("Leyendo fichero %s" % file_name) 
        total_data = []
        total_results = []
        file_data = trama_tools.cargar_trama_bytes(file_name)
        datos_list = []
        for data in file_data:
            for valor in data["data"]:
                datos_list.append(int(valor))
        
        datos_list = self.normalizar_datos(datos_list)

        if datos_list is False:
            print("Omitiendo linea de fichero %s" % file_name)
            return [], []

        resultado_list = [int(valor) for valor in file_data[0]["values"]]

        while len(resultado_list) < 8:
            resultado_list.insert(0, 0)

        total_data.append(datos_list)
        total_results.append(resultado_list)

        return total_data, total_results


    def recoger_dataset(self, folder_name : str):
        print("Recoger datasets ....")
        total_data = []
        total_results = []
        print("Comprobando folder %s" % folder_name)
        num_ficheros = 0
        for file in os.listdir(folder_name):
            nombre_fichero = os.path.join(folder_name, file)
            if not nombre_fichero.endswith(".json"):
                continue
            
            lista_ficheros = trama_tools.resuelve_nombre_binarios_lista(nombre_fichero)
            for nombre_fichero_sin_ext in lista_ficheros:
                nombre_fichero_bin = "%s.bin" % nombre_fichero_sin_ext
                ruta_fichero = os.path.join(folder_name, nombre_fichero_bin)
                if not os.path.exists(ruta_fichero):
                    print("No existe el fichero %s" % ruta_fichero)
                    continue
                num_ficheros += 1

                data, results = self.leer_fichero(ruta_fichero)
                # print("Recogido fichero %s con %s tramas" % (nombre_fichero_bin, data[0]))
                total_data.extend(data)
                total_results.extend(results)
        
        # print("Recolectadas %d tramas de %s ficheros" % (len(total_data), num_ficheros))

        return ia_tools.crear_dataset(total_data, total_results)

    def recoger_modelo(self, layers : List[int]) -> Any:
        print("Recoger modelo ....")
        print("Layers: %s" % layers)
        return ia_tools.init_modelo(input_schema=(94,1), layers=layers, output_shapes=1)

def main_menu(iface):
    # recogemos argumentos
    if not len(sys.argv) > 1:
        print("No se ha especificado ninguna acción")
        return
    
    accion = sys.argv[1]
    if accion == "pesos":
        for arg in sys.argv:
            if arg.startswith("modelo="):
                nombre_modelo = arg.split("=")[1]
                modelo = ia_tools.load_modelo(nombre_modelo, iface.config['modelofolder'])
                if modelo:
                    ia_tools.mostrar_pesos_modelo(modelo)
            else:
                pos = sys.argv.index(arg)
                if pos < 2:
                    continue
                print("Argumento %s %s desconocido" % (pos, arg))
            return

    if accion == "entrenar":  

        epocas = None
        dataset_folder = iface.config['dumpsfolder']
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
                dataset_folder = iface.recoger_dataset(arg.split("=")[1])
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


        modelo = ia_tools.load_modelo(nombre_modelo, iface.config['modelofolder']) if nombre_modelo else iface.recoger_modelo(layers=layers)

        dataset = iface.recoger_dataset(dataset_folder)
        result = ia_tools.entrenar_datos(dataset, None, epocas, len(dataset), modelo)
        if save_modelo:
            epocas_entrenadas, layers_modelo = ia_tools.recoge_datos_modelo(modelo)
            if not epocas_entrenadas:
                epocas_entrenadas = epocas
            time_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ia_tools.save_modelo(modelo, "modelo__%s__%s_%s.keras" % ("_".join(layers_modelo), epocas_entrenadas, time_stamp))
        graphics.mostrar_graf(result)
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

        modelo = ia_tools.load_modelo(nombre_modelo, iface.config['modelofolder'])
        data_pred = None

        lista_tramas = []

        if nombre_fichero:
            print("Nombre fichero %s" % nombre_fichero)
            lista_tramas = iface.calcular_predicciones(nombre_fichero)
        elif trama:
            trama = iface.normalizar_datos(trama, True)
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