from .. import CONFIG
from typing import Optional, List, Union, Dict
import optparse
import traceback


class CommonInterface:

    config: Dict[str, Union[str, int, float]]

    def __init__(self):

        self.config = {}

    def load_config(self, arguments):

        try:
            for key in CONFIG.get_keys():
                valor = getattr(arguments, key, None)
                if valor is None:
                    valor = CONFIG.get(key)

                if valor is not None:
                    self.config[key] = valor
                else:
                    raise Exception("No existe la clave %s" % key)
                
            for arg in arguments.__dict__.keys():
                if arg not in CONFIG.get_keys():
                    val = getattr(arguments, arg, None)
                    # print("Argumento extra %s -> %s" % (arg, val))
                    self.config[arg] = val

        except Exception as e:
            print(f"Error al cargar la configuración: {e}")
            print(traceback.format_exc())
            return False
        
        return True


    def parse_args(self, custom_argv: Optional[List[str]] = None) -> optparse.Values:
        parser = optparse.OptionParser()
        parser.add_option('-p', '--port', dest='port', help='Puerto de comunicacion')
        parser.add_option('-b', '--baudrate', dest='baudrate', help='Baudrate')
        parser.add_option('-t', '--timeout', dest='timeout', help='Timeout')
        parser.add_option('-d', '--dumpsfolder', dest='dumpsfolder', help='Carpeta de dumps')
        parser.add_option('-m', '--modelofolder', dest='modelofolder', help='Carpeta de modelos')
        parser.add_option('-f', '--tramafile', dest='tramafile', help='Archivo de trama')
        parser.add_option('-s', '--savefile', dest='savefile', help='Guardar archivo de trama', action="store_true", default=True)
        parser.add_option('-o', '--posiciones', dest='posiciones', help='Posiciones de los modulos')
        parser.add_option('-r', '--portsalida', dest='portsalida', help='Puerto de salida')
        
        (options, args) = parser.parse_args(custom_argv)
        return self.load_config(options)
    
    def check_not_null(self, lista_campos: List[str]) -> bool:
        for nombre_campo in lista_campos: 
            valor = self.config[nombre_campo] if nombre_campo in self.config else None
            if not valor or valor == "None":
                print("El campo %s es obligatorio" % nombre_campo)
                return False

        return True
