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

    def parse_args(self, custom_argv: Optional[List[str]] = None) -> optparse.Values:
        parser = optparse.OptionParser()
        parser.add_option('-d', '--dumpsfolder', dest='dumpsfolder', help='Carpeta de dumps')
        parser.add_option('-m', '--model_file', dest='modelfile', help='Archivo del modelo', default=None)
        parser.add_option('-f', '--file_name', dest='tramafile', help='Archivo con trama o lista de tramas', default=None)
        parser.add_option('-l', '--layers', dest='layers', help='Capas', default="20,20,20")
        parser.add_option('-e', '--epocs', dest='epocs', help='Epocas', default="10000")
        parser.add_option('-s', '--savefile', dest='savefile', help='Guardar archivo del modelo entrenado', action="store_true", default=True)
        parser.add_option('-o', '--opt', dest='optimizado', help='Afinado', default="0.001")
        (options, args) = parser.parse_args(custom_argv)
        return self.load_config(options)
               
    def execute_actions(self):
        action = sys.argv[2]
        if action == "pesos":
            
            if not self.check_not_null(['modelfile']):
                print("Uso: %s trainning pesos -m <file>" % sys.argv[0])
                sys.exit(1)

            nombre_modelo = self.config['modelfile']
            modelo = ia_tools.load_modelo(nombre_modelo, self.config['modelofolder'])
            if modelo:
                ia_tools.mostrar_pesos_modelo(modelo)

        elif action == "entrenar":
            if not self.check_not_null(['layers','epocs','dumpsfolder','optimizado']):
                print("Uso: %s trainning begin -m <file> -o <optimizado>" % sys.argv[0])
                sys.exit(1)

            nombre_modelo = self.config['modelfile']
            epocas = int(self.config['epocs'])

            modelo = ia_tools.load_modelo(nombre_modelo, self.config['modelofolder']) if nombre_modelo else self.crear_modelo()

            datos = self.recoger_dataset()


            result = ia_tools.entrenar_datos(datos=datos, epocas=epocas, num_datos=len(datos), modelo=modelo)
            if self.config["savefile"]:
                epocas_entrenadas, layers_modelo = ia_tools.recoge_datos_modelo(modelo)
                if not epocas_entrenadas:
                    epocas_entrenadas = epocas
                time_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                ia_tools.save_modelo(self.config, modelo, "modelo__%s__%s_%s.keras" % ("_".join(layers_modelo), epocas_entrenadas, time_stamp))
            graphics.mostrar_graf(result)
        elif action == "predecir":
            if not self.check_not_null(['modelfile','tramafile']):
                print("Uso: %s trainning predecir -m <file>" % sys.argv[0])
                sys.exit(1)

            modelo = ia_tools.load_modelo(self.config['modelfile'], self.config['modelofolder'])
            lista_tramas = self.calcular_predicciones()

            print("Procesando %s predicciones" % len(lista_tramas))
            for trama_ in lista_tramas:
                ia_tools.predecir(trama_.take(1), modelo, LISTA_CLASES)
            else:
                print("No se han encontrado tramas que procesar")

        else:
            print("Accion %s no reconocida" % (action))

    def calcular_predicciones(self) -> List[Any]:
        fichero : str =  self.config['tramafile']
        if not fichero:
            return []
        fichero_path = os.path.join(self.config["dumpsfolder"], fichero)
        lista_ficheros = []
        if "_" in fichero:
            lista_ficheros = [os.path.join(self.config["dumpsfolder"], "%s.bin" % file_name) for file_name in trama_tools.resuelve_nombre_binarios_lista(fichero_path)]
        else:
            lista_ficheros.append(fichero_path)

        lista_predicciones = []
        for fichero_path in lista_ficheros:
            dataset, resultset = self.leer_fichero(fichero_path)
            for data in dataset:
                lista_predicciones.append(data)
        
        return [ia_tools.crear_dataset([data], None) for data in lista_predicciones]

    def normalizar_datos(self, datos : List[int], check_size: bool = False) -> list[int]:
        if check_size:
            while len(datos) < 94:
                datos.append(0)

        return np.array([datos], dtype=np.float32)

    def leer_fichero(self, file_name: str) -> Union[List[int], List[int]]:
        # print("Leyendo fichero %s." % file_name) 
        total_data = []
        total_results = []
        file_data = trama_tools.cargar_trama_bytes(file_name)
        datos_list = []
        for data in file_data:
            for valor in data["data"]:
                datos_list.append(int(valor))
        
        datos_list = self.normalizar_datos(datos_list, True)

        if datos_list is False:
            print("Omitiendo linea de fichero %s" % file_name)
            return [], []

        resultado_list = [int(valor) for valor in file_data[0]["values"]]

        while len(resultado_list) < 8:
            resultado_list.insert(0, 0)

        total_data.append(datos_list)
        result_formated = self.normalizar_datos(int("".join([str(bit) for bit in resultado_list]),2))
        total_results.append(result_formated)

        return total_data, total_results


    def recoger_dataset(self):
        print("Recoger datasets ....")
        folder_name = self.config['dumpsfolder']
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

    def crear_modelo(self) -> Any:
        #print("Creando modelo ....")
        conf_layer = self.config['layers']
        layers = []
        if "," in conf_layer:
            layers = [int(layer) for layer in conf_layer.split(",")]
        elif "*" in conf_layer:
            num, neu = conf_layer.split("*")
            for i in range(int(num)):
                layers.append(int(neu))
        else:
            raise Exception("Error en la configuración de capas")
            
        optimizado = float(self.config['optimizado'])
        #print("Creando modelo ....")
        #print("Layers: %s" % layers)
        print("Optimizado: %s" % optimizado)
        return ia_tools.init_modelo(input_schema=(94,1), layers=layers, output_shapes=1, opt=optimizado)