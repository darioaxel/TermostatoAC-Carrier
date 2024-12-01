import configparser

def cargar_configuracion():
    config = configparser.ConfigParser()
    config.read('config.ini')
    if not config.has_section('CONFIG'):
        config.add_section('CONFIG')
        config.set('CONFIG', 'dumpsfolder', 'dumps')
        config.set('CONFIG', 'modelofolder', 'models')
        config.set('CONFIG', 'port', '/dev/ttyUSB0')
        config.set('CONFIG', 'portsalida', '/dev/ttyUSB0')
        config.set('CONFIG', 'baudrate', '2400')
        config.set('CONFIG', 'tramafile', 'dumps/trama.bin')
        config.set('CONFIG', 'posiciones', '000000')
        config.set('CONFIG', 'savefile', 's')
        guardar_configuracion(config)

    return config

def guardar_configuracion(config):
    with open('config.ini', 'w') as configfile:
        config.write(configfile)

def actualizar_configuracion(data):
    config = cargar_configuracion()
    updated = False
    for key, val in data:
        current_val = config.get(section='CONFIG', option=key)
        if current_val == val:
            continue
        updated = True
        config.set('CONFIG', key, val)
    if updated:
        guardar_configuracion(config)