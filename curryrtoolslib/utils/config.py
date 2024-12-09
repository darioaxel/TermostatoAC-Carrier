import configparser
import os

class ConfigurationManager:

    config : 'configparser.ConfigParser'
    file_name: str
    lista_config = {
        'dumpsfolder': 'dumps',
        'modelofolder': 'models',
        'port': '/dev/ttyUSB0',
        'baudrate': '2400',
        'tramafile': 'dumps/trama.bin',
        'posiciones': '000000',
        'savefile': 's',
        'timeout': '0.1',
        'repeticionesenvio' : ' 30',
        'portsalida': '/dev/ttyUSB1'

    }

    def __init__(self):

        folder = os.path.join(os.path.expanduser('~'), '.config', 'curryrtools')
        if not os.path.exists(folder):
            os.makedirs(folder)

        self.file_name = os.path.join(folder , 'config.ini')
        self.load_config()

        

    def get(self, key):
        try:
            return self.config.get(section='CONFIG', option=key)
        except Exception as e:
            print(f"Error al obtener la clave {key}: {e}")
            if key in self.lista_config:
                print(f"Se ha creado la clave {key} con el valor {self.lista_config[key]}")
                self.set(key, self.lista_config[key])
                return self.lista_config[key]
            
    def set(self, key, val):
        self.update({key: val})

    def update(self, data: dict[str: str]):
        need_update = False
        for key, val in data.items():
            current_val = None
            try:
                current_val = self.config.get(section='CONFIG', option=key)
            except Exception as e:
                print(f"Error al obtener la clave {key}: {e}")
            if current_val is None or current_val != val:
                self.config.set('CONFIG', key, str(val))
                need_updated = True
            
                
        if need_updated:
            self.save_config_file()
    
    def load_config(self):

        self.config = configparser.ConfigParser()
        self.config.read(self.file_name)
        if not self.config.has_section('CONFIG'):
            print("Cargando configuración inicial")
            self.config.add_section('CONFIG')
            self.get('dumpsfolder')
            self.get('modelofolder')
            self.get('port')
            self.get('baudrate')
            self.get('tramafile')
            self.get('posiciones')
            self.get('savefile')
            self.get('timeout')
            self.get('repeticionesenvio')
            self.get('portsalida')           

    def save_config_file(self):
        with open(self.file_name, 'w') as configfile:
            self.config.write(configfile)

    def __attr__(self, name):
        if name in self.config.keys():
            return self.get(name)
        else:
            raise Exception("No existe la clave %s" % name)
        
    def get_keys(self):
        return self.config.options('CONFIG')

