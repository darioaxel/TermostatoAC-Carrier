import serial
import time
from datetime import datetime
import os
import config as config_mod
import trama_tools
import json
from typing import Union, Optional, List





def enviar_trama(port:str, baudrate:int, timeout:Union[float,int], file_name:str, repeticiones:int, intervalo: int = 5):
    """
    Envía una trama de datos a través de un puerto serial específico.

    :param port: El nombre del puerto serial, por defecto '/dev/ttyUSB0'.
    :param baudrate: La velocidad en baudios, por defecto 2400.
    :param timeout: El tiempo de espera en segundos para la lectura del puerto, por defecto 1 segundo.
    :param file_name: Fichero de contien la trama a enviar
    """
    try:
        with serial.Serial(port, baudrate, timeout=timeout) as ser:
            print(f"Conectado al puerto {port} con velocidad {baudrate} baudios.")
            i = 0
            while i < intervalo:
                if not send_data_from(ser,file_name):
                    print("Error al enviar trama")
                    break
        print("Fin.")

    except serial.SerialException as e:
        print(f"Error al abrir el puerto serial: {e}")
    except KeyboardInterrupt:
        print("Lectura interrumpida por el usuario.")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")

def modo_repetidor(port: str, port_salida: str, baudrate: int, timeout:Union[float,int]):
    """
    Repite la lectura de datos desde un puerto serial específico.

    :param port: El nombre del puerto serial, por defecto '/dev/ttyUSB0'.
    :param baudrate: La velocidad en baudios, por defecto 2400.
    :param timeout: El tiempo de espera en segundos para la lectura del puerto, por defecto 1 segundo.
    :param send_data: Si es True, envía datos al puerto serial.
    """
    try:
        with serial.Serial(port, baudrate, timeout=timeout) as ser:
            print(f"Conectado al puerto {port} con velocidad {baudrate} baudios.") 

            with serial.Serial(port_salida, baudrate, timeout=timeout) as ser_salida:
                print(f"Conectado al puerto {port_salida} con velocidad {baudrate} baudios.")

                while True:
                    file_name = read_data_from(ser,baudrate,timeout,None,None)
                    if not send_data_from(ser_salida,file_name):
                        print("Error al enviar trama")   
                        break
                
    except serial.SerialException as e:
        print(f"Error al abrir el puerto serial: {e}")
    except KeyboardInterrupt:
        print("Lectura interrumpida por el usuario.")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")

def read_serial_data(port: str, baudrate: int, save_to_file: bool, posiciones: str, timeout:Union[float,int]):
    """
    Lee y muestra los datos recibidos desde un puerto serial específico.
    Detecta la finalización de un stream de bits y lo guarda en un archivo
    junto con un comentario que indique que el stream ha terminado.
    
    :param port: El nombre del puerto serial, por defecto '/dev/ttyUSB0'.
    :param baudrate: La velocidad en baudios, por defecto 2400.
    :param timeout: El tiempo de espera en segundos para la lectura del puerto, por defecto 1 segundo.
    :param save_to_file: Si es True, guarda los datos en un archivo de texto.
    """

    hex_file = None
    hex_filename = None
    try:
        # Inicializa la conexión serial
        if save_to_file:
            hex_file = {
                "files" : [],
                "baudrate" : int(baudrate),
                "posiciones" : posiciones
            }

        with serial.Serial(port, baudrate, timeout=timeout) as ser:
            print(f"Conectado al puerto {port} con velocidad {baudrate} baudios.")               
                # Escribe un comentario con la velocidad en baudios en el archivo hexadecimal
            read_data_from(ser,baudrate,timeout,posiciones, hex_file)
                        
    except serial.SerialException as e:
        print(f"Error al abrir el puerto serial: {e}")
    except KeyboardInterrupt:
        print("Lectura interrumpida por el usuario.")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")
    finally:

        if hex_file:
            trama_tools.crear_lista_json(hex_file)

            
        else:
            print("No se pudo guardar el archivo de datos.")
        

def detect_baud_rate(port: str, timeout:Union[float,int]):
    """
    Intenta detectar la velocidad de transmisión de datos (baud rate) de un dispositivo serial.
    Guarda los resultados de las pruebas en un archivo de texto.
    
    :param port: El nombre del puerto serial, por defecto '/dev/ttyUSB0'.
    :param timeout: El tiempo de espera en segundos para la lectura del puerto, por defecto 1 segundo.
    """
    baud_rates_to_test = [300, 1200, 2400, 4800, 9600]
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f'prueba_baudrates_{timestamp}.txt'

    with open(filename, 'w') as file:
        for baudrate in baud_rates_to_test:
            try:
                with serial.Serial(port, baudrate, timeout=timeout) as ser:
                    file.write(f"--- Prueba con {baudrate} baudios ---\n")
                    print(f"Probando velocidad {baudrate} baudios...")
                    time.sleep(2)  # Da tiempo para recibir datos

                    data = ser.read(1024)
                    if data:
                        # Convierte los datos a hexadecimal
                        hex_data = ' '.join(f'{b:02x}' for b in data)
                        file.write(f"Recibido (hexadecimal): {hex_data}\n")
                        
                        print(f"Datos recibidos con éxito a {baudrate} baudios.")
                    else:
                        file.write("No se recibieron datos.\n")
            except serial.SerialException as e:
                print(f"Error al probar {baudrate} baudios: {e}")
            except Exception as e:
                print(f"Ocurrió un error inesperado: {e}")
    
    print(f"Pruebas finalizadas. Los resultados se guardaron en {filename}")

def measure_time_between_messages(port:str, baudrate:int, timeout:Union[float,int]):
    """
    Mide el tiempo en milisegundos entre la recepción de mensajes en el puerto serial.
    
    :param port: El nombre del puerto serial, por defecto '/dev/ttyUSB0'.
    :param baudrate: La velocidad en baudios, por defecto 2400.
    :param timeout: El tiempo de espera en segundos para la lectura del puerto, por defecto 1 segundo.
    """
    try:
        # Inicializa la conexión serial
        with serial.Serial(port, baudrate, timeout=timeout) as ser:
            print(f"Conectado al puerto {port} con velocidad {baudrate} baudios.")
            
            last_time = None
            while True:
                # Lee datos del puerto
                data = ser.read(1024)  # Lee hasta 1024 bytes
                if data:
                    current_time = time.time()
                    if last_time is not None:
                        time_diff_ms = (current_time - last_time) * 1000  # Diferencia en milisegundos
                        print(f"Tiempo entre mensajes: {time_diff_ms:.2f} ms")
                    last_time = current_time
                else:
                    # Si no se reciben datos, se resetea el temporizador
                    last_time = None
    except serial.SerialException as e:
        print(f"Error al abrir el puerto serial: {e}")
    except KeyboardInterrupt:
        print("Lectura interrumpida por el usuario.")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")

def calculate_message_size(port:str, baudrate:int, timeout:Union[float,int], inactivity_timeout:Union[float,int]):
    """
    Realiza 20 lecturas de mensajes completos desde el puerto serial basándose en un período de inactividad,
    calcula el tamaño en bytes de cada uno, y guarda los resultados en un archivo si se recibieron datos.

    :param port: El nombre del puerto serial, por defecto '/dev/ttyCH341USB0'.
    :param baudrate: La velocidad en baudios, por defecto 2400.
    :param timeout: El tiempo de espera en segundos para la lectura del puerto, por defecto 1 segundo.
    :param inactivity_timeout: El tiempo de inactividad en segundos que determina el final de un mensaje.
    """
    # Genera el nombre del archivo basado en la fecha y hora actuales
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"lecturas_de_tamaño_de_mensaje_{timestamp}.txt"
    
    try:
        # Inicializa la conexión serial
        with serial.Serial(port, baudrate, timeout=timeout) as ser:
            print(f"Conectado al puerto {port} con velocidad {baudrate} baudios.")
            print(f"Guardando resultados en el archivo: {filename}\n")

            # Abre el archivo para escribir los resultados
            with open(filename, 'w') as file:
                valid_readings = 0
                for i in range(20):
                    print(f"Esperando el inicio del mensaje {i+1}/20...")
                    message_data = bytearray()
                    last_received_time = time.time()

                    while True:
                        data = ser.read(1024)  # Lee hasta 1024 bytes
                        if data:
                            message_data.extend(data)
                            last_received_time = time.time()
                        else:
                            # Si no se reciben datos, verificar si hemos superado el inactivity_timeout
                            current_time = time.time()
                            if current_time - last_received_time > inactivity_timeout:
                                # Se considera que el mensaje ha terminado si el tiempo de inactividad supera el límite
                                break

                    if message_data:
                        # Calcula el tamaño del mensaje
                        message_size = len(message_data)
                        print(f"Tamaño del mensaje {i+1}: {message_size} bytes")

                        # Escribe el resultado en el archivo con timestamp
                        file.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Mensaje {i+1}: {message_size} bytes\n")
                        valid_readings += 1
                    else:
                        print(f"No se recibieron datos para el mensaje {i+1}.")

                if valid_readings == 0:
                    print("No se recibieron datos en ninguna de las lecturas.")
                else:
                    print(f"\nLecturas completadas. {valid_readings} resultados válidos guardados en {filename}.")

    except serial.SerialException as e:
        print(f"Error al abrir el puerto serial: {e}")
    except KeyboardInterrupt:
        print("Lectura interrumpida por el usuario.")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")


def send_data_from(ser : "serial.Serial", file_name : str) -> bool:
    try:
        print("Enviando trama %s" % file_name)
        lista_tramas = trama_tools.cargar_trama_bytes(file_name)
        for trama in lista_tramas:
            ser.write(trama["data"])
            time.sleep(trama["timeout"])
        print("OK")
        return True
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")
        return False
    

def read_data_from(ser, baudrate, timeout, posiciones=None, hex_file: Optional[List[str]] = None) -> Optional[str]:
    stream_data = []
    while True:
        tiempo_inicio_trama = datetime.now()
        # Lee datos del puerto
        data = ser.read(1)
        tiempo_primer_byte = datetime.now()
        data += ser.read(1023)
        tiempo_final_byte = datetime.now()
        valid = True
        if data:
            dec_data = data
            stream_data.append([dec_data,[tiempo_inicio_trama, tiempo_primer_byte, tiempo_final_byte]])
            print(f"Recibido (decimal): {dec_data} ({len(data)} bytes)")
        else:
            if not stream_data:
                continue
            total_data = []
            total_times = []
            for data in stream_data:
                for byte, time_ in data:
                    total_data.append(byte)
                    total_times.append([time_, len(byte)])

            valid = trama_tools.validar_trama_bytes(total_data)
            if valid:
                file_name = trama_tools.guardar_trama_bytes(stream_data, total_times, baudrate, timeout, posiciones)
                if hex_file:
                    hex_file["files"].append(file_name)
                else:
                    return file_name
            stream_data = []
            print("# STREAM TERMINADO %s bytes" % (len(total_data)))

def main_menu():
    while True:

        print("\n--- MENÚ PRINCIPAL ---")
        print("1. Leer datos del puerto serial")
        print("2. Detectar velocidad de transmisión (baud rate)")
        print("3. Medir tiempo entre mensajes")
        print("4. Determinar tamaño del mensaje")
        print("5. Modo repetidor")
        print("6. Enviar trama")
        print("7. Salir")

        choice = input("Selecciona una opción: ")

        current_port = config_mod.CONFIG.get(section='CONFIG', option='port')
        current_port_salida = config_mod.CONFIG.get(section='CONFIG', option='portsalida')
        current_baudrate = config_mod.CONFIG.get(section='CONFIG', option='baudrate')
        trama_file = config_mod.CONFIG.get(section='CONFIG', option='tramafile')
        repeticiones_envio = config_mod.CONFIG.get(section='CONFIG', option='repeticionesenvio')
        save_file = config_mod.CONFIG.get(section='CONFIG', option='savefile')
        posiciones_config = config_mod.CONFIG.get(section='CONFIG', option='posiciones')
        default_timeout = config_mod.CONFIG.get(section='CONFIG', option='timeout')

        if choice == '1':
            port = input("Introduce el puerto serial (por defecto '%s'): " %(current_port)) or current_port
            baudrate = input("Introduce la velocidad en baudios (por defecto '%s'): " %(current_baudrate)) or current_baudrate
            save_option = input("¿Quieres guardar los datos en un archivo? (por defecto '%s'): " %(save_file)) or save_file
            save_to_file = save_option.strip().lower() == 's'
            posiciones = None
            if save_to_file:
                posiciones = input("Introduce las posiciones de los 3 controles:\n\t* Ventilador: [0,0,0] -parado, [1,0,0] - mínimo, [0,1,0] - medio, [0,0,1] - maximo\n\t* Frio: 0,1\n\t* Calor: 0,1\n\t* Seco: 0,1\nEjemplo (Ventilador medio [0,1,0], Frio 1, Calor 0, Seco 0): (Por defecto: %s)\n:" %(posiciones_config)) or posiciones_config
                if posiciones:
                    posiciones = posiciones.replace(" ", "")
                    if "," not in posiciones:
                        posiciones = ",".join(posiciones.split())
            config_mod.actualizar_configuracion({'port': port, 'baudrate': baudrate, 'posiciones': posiciones, 'savefile': save_to_file})
            read_serial_data(port=port, baudrate=int(baudrate), save_to_file=save_to_file, posiciones=posiciones, timeout=default_timeout)
        elif choice == '2':
            port = input("Introduce el puerto serial (por defecto '%s'): " %(current_port)) or current_port
            config_mod.actualizar_configuracion({'port': port})
            detect_baud_rate(port=port,timeout=5)
        elif choice == '3':
            port = input("Introduce el puerto serial (por defecto '%s'): " %(current_port)) or current_port
            baudrate = input("Introduce la velocidad en baudios (por defecto '%s'): " %(current_baudrate)) or current_baudrate
            config_mod.actualizar_configuracion({'port': port, 'baudrate': baudrate})
            measure_time_between_messages(port=port, baudrate=int(baudrate), timeout=5)
        elif choice == '4':
            port = input("Introduce el puerto serial (por defecto '%s'): " %(current_port)) or current_port
            baudrate = input("Introduce la velocidad en baudios (por defecto '%s'): " %(current_baudrate)) or current_baudrate
            config_mod.actualizar_configuracion({'port': port, 'baudrate': baudrate})
            calculate_message_size(port=port, baudrate=int(baudrate),timeout=default_timeout,inactivity_timeout=2)
        elif choice == '5':
            port_entrada = input("Introduce el puerto serial de entrada (por defecto '%s'): " %(current_port)) or current_port
            port_salida = input("Introduce el puerto serial de salida (por defecto '%s'): " %(current_port_salida)) or current_port_salida
            baudrate = input("Introduce la velocidad en baudios (por defecto '%s'): " %(current_baudrate)) or current_baudrate
            config_mod.actualizar_configuracion({'port': port_entrada,'porsalida': port_salida, 'baudrate': baudrate})
            modo_repetidor(port=port,port_salida=port_salida,baudrate= int(baudrate), timeout=default_timeout)
        elif choice == '6':
            port = input("Introduce el puerto serial (por defecto '%s'): " %(current_port)) or current_port
            baudrate = input("Introduce la velocidad en baudios (por defecto '%s'): " %(current_baudrate)) or current_baudrate
            fichero = input("Introduce el nombre del fichero con las tramas a enviar (por defecto '%s'): " %(trama_file)) or trama_file
            repeticiones = input("Introduce el número de repeticiones (por defecto '%s'): " %(repeticiones_envio)) or repeticiones_envio
            config_mod.actualizar_configuracion({'port': port, 'baudrate': baudrate, 'tramafile': fichero, 'repeticionesenvio' : repeticiones})
            enviar_trama(port=port, baudrate=int(baudrate), fichero=fichero, repeticiones=int(repeticiones))
        elif choice == '7':
            print("Saliendo del programa.")
            break
        else:
            print("Opción no válida. Por favor, selecciona una opción del menú.")

if __name__ == "__main__":
    main_menu()
