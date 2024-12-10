from . common_interface import CommonInterface
from .. utils import trama as trama_tools
from .. import CONFIG
import serial
from datetime import datetime
import time
import sys
import os
import traceback
import optparse


from typing import List, Union, Optional

class DeviceInterface(CommonInterface):

    valid_sizes: List[int]

    def __init__(self):
        super().__init__()

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
        parser.add_option('-i', '--interval', dest='intervalo', help='Tiempo de envio entre tramas')
        
        (options, args) = parser.parse_args(custom_argv)
        return self.load_config(options)
               
    def execute_actions(self):
        """
        Ejecuta las acciones especificadas en los argumentos de línea de comandos.
        """
        if len(sys.argv) < 3:
            print("Uso: %s device <action>" % sys.argv[0])
            print("Acciones válidas: menu, read, write")
            sys.exit(1)

        action = sys.argv[2]
        if action == "menu":
            main_menu(self)
        elif action == "read":

            if not self.check_not_null(['port','baudrate','timeout','posiciones']):
                print("Uso: %s device read -p <port> -b <baudrate> -t <timeout> -o <posiciones>" % sys.argv[0])
                sys.exit(1)

            port = self.config['port']
            baudrate = self.config['baudrate']
            timeout = self.config['timeout']
            posiciones = self.config['posiciones']
            save_to_file = str(self.config['savefile']).lower() in ["s","true"]
            self.read_serial_data(port=port, baudrate=int(baudrate), timeout=float(timeout), posiciones=posiciones, save_to_file=save_to_file)
        elif action == "write":

            if not self.check_not_null(['port','baudrate','timeout','tramafile','repeticionesenvio','intervalo']):
                print("Uso: %s device write -p <port> -b <baudrate> -t <timeout> -f <file_name> -r <repeticiones> -i <intervalo>" % sys.argv[0])
                sys.exit(1)

            port = self.config['port']
            baudrate = self.config['baudrate']
            timeout = self.config['timeout']
            posiciones = self.config['posiciones']
            file_name = self.config['tramafile']
            repeticiones = self.config['repeticionesenvio']
            intervalo = self.config['intervalo']

            self.enviar_trama(port=port, baudrate=int(baudrate), timeout=float(timeout), file_name=file_name, repeticiones=int(repeticiones), intervalo=int(intervalo))
        
        elif action == "repeat":
            if not self.check_not_null(['port','baudrate','timeout','portsalida']):
                print("Uso: %s device repetidor -p <port> -r <port_salida> -b <baudrate> -t <timeout>" % sys.argv[0])
                sys.exit(1)

            port = self.config['port']
            port_salida = self.config['portsalida']
            baudrate = self.config['baudrate']
            timeout = self.config['timeout']

            self.modo_repetidor(port=port, port_salida=port_salida, baudrate=int(baudrate), timeout=float(timeout))
        else:
            print("Acción %s no válida." % action)


    def enviar_trama(self, port:str, baudrate:int, timeout:Union[float,int], file_name:str, repeticiones:int, intervalo: int = 5):
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
                while i < repeticiones:
                    if not self.send_data_from(ser,file_name):
                        print("Error al enviar trama")
                        break
                    i += 1
                    print("Trama enviada %d/%d. Esperando %s seg. para nuevo envio" % (i,repeticiones, intervalo))
                    time.sleep(intervalo)
                    
            print("Fin.")

        except serial.SerialException as e:
            print(f"Error al abrir el puerto serial: {e}")
        except KeyboardInterrupt:
            print("Lectura interrumpida por el usuario.")
        except Exception as e:
            print(f"Ocurrió un error inesperado: {e}")

    def modo_repetidor(self, port: str, port_salida: str, baudrate: int, timeout:Union[float,int]):
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
                        file_name = self.read_data_from(ser,baudrate,timeout,None,None)
                        if not self.send_data_from(ser_salida,"%s.bin" % file_name):
                            print("Error al enviar trama")   
                            break
                    
        except serial.SerialException as e:
            print(f"Error al abrir el puerto serial: {e}")
        except KeyboardInterrupt:
            print("Lectura interrumpida por el usuario.")
        except Exception as e:
            print(f"Ocurrió un error inesperado: {e}")

    def read_serial_data(self, port: str, baudrate: int, save_to_file: bool, posiciones: str, timeout:Union[float,int]):
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
                print("Save to file activado")
                hex_file = {
                    "files" : [],
                    "baudrate" : int(baudrate),
                    "posiciones" : posiciones
                }

            with serial.Serial(port, baudrate, timeout=timeout) as ser:
                print(f"Conectado al puerto {port} con velocidad {baudrate} baudios.")               
                    # Escribe un comentario con la velocidad en baudios en el archivo hexadecimal
                self.read_data_from(ser,baudrate,timeout,posiciones, hex_file)
                            
        except serial.SerialException as e:
            print(f"Error al abrir el puerto serial: {e}")
        except KeyboardInterrupt:
            print("Lectura interrumpida por el usuario.")
        except Exception as e:
            print(f"Ocurrió un error inesperado: {e}")
            traceback.print_exc()
        finally:
            if hex_file:
                trama_tools.crear_lista_json(lista=hex_file, posiciones=posiciones, baudrate=baudrate)        

    def detect_baud_rate(self, port: str, timeout:Union[float,int]):
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

    def measure_time_between_messages(self, port:str, baudrate:int, timeout:Union[float,int]):
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

    def calculate_message_size(self, port:str, baudrate:int, timeout:Union[float,int], inactivity_timeout:Union[float,int]):
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


    def send_data_from(self, ser : "serial.Serial", file_name : str) -> bool:
        try:
            file_name_path = os.path.join(CONFIG.get("dumpsfolder"), file_name)
            # print("Enviando trama %s" % file_name_path)
            lista_tramas = trama_tools.cargar_trama_bytes(file_name_path)
            last_timeout = None
            for num, trama in enumerate(lista_tramas):
                new_timeout = datetime.strptime(trama["time"], "%Y-%m-%d %H:%M:%S.%f")
                if last_timeout:
                    wait_until = new_timeout - last_timeout
                    wait_until = wait_until.total_seconds()
                    current_timeout = float(trama["timeout"])
                    #print("Waiting ...", wait_until)
                    #print("Timeout ...", current_timeout)
                    fixed_waiting = wait_until - current_timeout
                    # print("Waiting ...", fixed_waiting)
                    time.sleep(fixed_waiting)
                last_timeout = new_timeout
                print("Enviado %s/%s : %s (%s bytes)" % (0, num+1, [hex(val) for val in trama["data"]], len(trama["data"])))
                ser.write(trama["data"])

            print("OK")
            return True
        except Exception as e:
            print(f"Ocurrió un error inesperado: {e}")
            return False
    

    def read_data_from(self, ser, baudrate, timeout, posiciones=None, hex_file: Optional[List[str]] = None) -> Optional[str]:
        stream_data = []
        i = 0
        print("## ESPERANDO TRAMA %s" % i)
        x = 0
        tiempos_trama = []
        while True:
            data = b""
            while True:
                tiempo_inicio = datetime.now()
                new_data = ser.read(1)
                tiempos_trama.append(str(tiempo_inicio))
                if new_data:
                    data += new_data
                else:
                    break
                
            valid = True
            if data:
                if x == 0:
                    tiempos_trama = [tiempos_trama[-1]]
                stream_data.append([data, tiempos_trama])
                tiempos_trama = []
                print(f"Recibido {i}/{x+1}: {[hex(val) for val in data]} ({len(data)} bytes)")
                x+=1
            else:
                if not stream_data:
                    continue
                total_data = []
                total_times = []
                full_data = []
                for byte_, time_ in stream_data:
                    total_data.append(byte_)
                    total_times.append([time_, len(byte_)])
                    full_data += byte_

                valid = trama_tools.validar_trama_bytes(full_data)
                if valid:
                    file_name = trama_tools.guardar_trama_bytes(total_data, total_times, baudrate, timeout, posiciones)
                    if hex_file:
                        hex_file["files"].append(file_name)
                    else:
                        return file_name
                stream_data = []
                
                print("# STREAM TERMINADO %s bytes" % (len(full_data)))
                i+= 1
                x= 0
                print("## ESPERANDO TRAMA %s" % i)

def main_menu(iface: 'DeviceInterface'):
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

        current_port = CONFIG.get('port')
        current_port_salida = CONFIG.get('portsalida')
        current_baudrate = CONFIG.get('baudrate')
        trama_file = CONFIG.get('tramafile')
        repeticiones_envio = CONFIG.get('repeticionesenvio')
        save_file = CONFIG.get('savefile')
        posiciones_config = CONFIG.get('posiciones')
        default_timeout = CONFIG.get('timeout')

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
            CONFIG.update({'port': port, 'baudrate': baudrate, 'posiciones': posiciones, 'savefile': 's' if save_to_file else 'n'})
            iface.read_serial_data(port=port, baudrate=int(baudrate), save_to_file=save_to_file, posiciones=posiciones, timeout=float(default_timeout))
        elif choice == '2':
            port = input("Introduce el puerto serial (por defecto '%s'): " %(current_port)) or current_port
            CONFIG.update({'port': port})
            iface.detect_baud_rate(port=port,timeout=5)
        elif choice == '3':
            port = input("Introduce el puerto serial (por defecto '%s'): " %(current_port)) or current_port
            baudrate = input("Introduce la velocidad en baudios (por defecto '%s'): " %(current_baudrate)) or current_baudrate
            CONFIG.update({'port': port, 'baudrate': baudrate})
            iface.measure_time_between_messages(port=port, baudrate=int(baudrate), timeout=5)
        elif choice == '4':
            port = input("Introduce el puerto serial (por defecto '%s'): " %(current_port)) or current_port
            baudrate = input("Introduce la velocidad en baudios (por defecto '%s'): " %(current_baudrate)) or current_baudrate
            CONFIG.update({'port': port, 'baudrate': baudrate})
            iface.calculate_message_size(port=port, baudrate=int(baudrate),timeout=float(default_timeout),inactivity_timeout=2)
        elif choice == '5':
            port_entrada = input("Introduce el puerto serial de entrada (por defecto '%s'): " %(current_port)) or current_port
            port_salida = input("Introduce el puerto serial de salida (por defecto '%s'): " %(current_port_salida)) or current_port_salida
            baudrate = input("Introduce la velocidad en baudios (por defecto '%s'): " %(current_baudrate)) or current_baudrate
            CONFIG.update({'port': port_entrada,'porsalida': port_salida, 'baudrate': baudrate})
            iface.modo_repetidor(port=port,port_salida=port_salida,baudrate=int(baudrate), timeout=float(default_timeout))
        elif choice == '6':
            port = input("Introduce el puerto serial (por defecto '%s'): " %(current_port)) or current_port
            baudrate = input("Introduce la velocidad en baudios (por defecto '%s'): " %(current_baudrate)) or current_baudrate
            fichero = input("Introduce el nombre del fichero con las tramas a enviar (por defecto '%s'): " %(trama_file)) or trama_file
            repeticiones = input("Introduce el número de repeticiones (por defecto '%s'): " %(repeticiones_envio)) or repeticiones_envio
            CONFIG.update({'port': port, 'baudrate': baudrate, 'tramafile': fichero, 'repeticionesenvio' : repeticiones})
            iface.enviar_trama(port=port, baudrate=int(baudrate), fichero=fichero, repeticiones=int(repeticiones))
        elif choice == '7':
            print("Saliendo del programa.")
            break
        else:
            print("Opción no válida. Por favor, selecciona una opción del menú.")