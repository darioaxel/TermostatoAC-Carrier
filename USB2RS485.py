import serial
import time
from datetime import datetime
import os

def read_serial_data(port='/dev/ttyUSB0', baudrate=2400, timeout=1, save_to_file=False, posiciones=""):
    """
    Lee y muestra los datos recibidos desde un puerto serial específico.
    Detecta la finalización de un stream de bits y lo guarda en un archivo
    junto con un comentario que indique que el stream ha terminado.
    
    :param port: El nombre del puerto serial, por defecto '/dev/ttyUSB0'.
    :param baudrate: La velocidad en baudios, por defecto 2400.
    :param timeout: El tiempo de espera en segundos para la lectura del puerto, por defecto 1 segundo.
    :param save_to_file: Si es True, guarda los datos en un archivo de texto.
    """
    try:
        # Inicializa la conexión serial
        with serial.Serial(port, baudrate, timeout=timeout) as ser:
            print(f"Conectado al puerto {port} con velocidad {baudrate} baudios.")

            hex_file = None
            
            if save_to_file:
                timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                hex_filename = os.path.abspath(os.path.join(os.path.dirname(__name__), "dumps", f'datos_hex_{baudrate}_{"-".join(posiciones.split(","))}_{timestamp}.csv'))
                if not os.path.exists(os.path.dirname(hex_filename)):
                    os.makedirs(os.path.dirname(hex_filename))
                hex_file = open(hex_filename, 'w')
                
                # Escribe un comentario con la velocidad en baudios en el archivo hexadecimal
                hex_file.write(f"Trama;Posiciones\n")
                print(f"Guardando datos en {hex_filename}")

            stream_active = False
            stream_data = []

            while True:
                # Lee datos del puerto
                data = ser.read(1024)  # Lee hasta 1024 bytes
                if data:
                    stream_active = True
                    # Convierte los datos a hexadecimal y los agrega al stream actual
                    # hex_data = ' '.join(f'{b:02x}' for b in data)
                    hex_data = ','.join(str(b) for b in data)
                    stream_data.append(hex_data)
                    print(f"Recibido (hexadecimal): {hex_data}")
                else:
                    if stream_active:
                        # Si el stream estaba activo pero ya no hay más datos, finaliza el stream
                        if save_to_file:
                            # Escribe el stream completo en el archivo
                            total_data = ','.join(stream_data)
                            hex_file.write(";".join([total_data, posiciones])+ "\n")
                            # hex_file.write("# STREAM TERMINADO\n")
                        print("# STREAM TERMINADO")
                        
                        # Resetea para el siguiente stream
                        stream_active = False
                        stream_data = []
    except serial.SerialException as e:
        print(f"Error al abrir el puerto serial: {e}")
    except KeyboardInterrupt:
        print("Lectura interrumpida por el usuario.")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")
    finally:
        if save_to_file: 
            if hex_file:
                hex_file.close()
            else:
                print("No se pudo guardar el archivo de datos.")
            print(f"Datos guardados en {hex_filename}")

def detect_baud_rate(port='/dev/ttyUSB0', timeout=1):
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

def measure_time_between_messages(port='/dev/ttyUSB0', baudrate=2400, timeout=1):
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

def calculate_message_size(port='/dev/ttyUSB0', baudrate=2400, timeout=1, inactivity_timeout=2):
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

def main_menu():
    while True:
        print("\n--- MENÚ PRINCIPAL ---")
        print("1. Leer datos del puerto serial")
        print("2. Detectar velocidad de transmisión (baud rate)")
        print("3. Medir tiempo entre mensajes")
        print("4. Determinar tamaño del mensaje")
        print("5. Salir")

        choice = input("Selecciona una opción: ")

        if choice == '1':
            port = input("Introduce el puerto serial (por defecto '/dev/ttyUSB0'): ") or '/dev/ttyUSB0'
            baudrate = input("Introduce la velocidad en baudios (por defecto 2400): ") or '2400'
            save_option = input("¿Quieres guardar los datos en un archivo? (S/n): ").strip().lower()
            save_to_file = save_option == 's' or not save_option
            posiciones = None
            if save_to_file:
                posiciones = input("Introduce las posiciones de los 3 controles:\n\t* Ventilador: [0,0,0] -parado, [1,0,0] - mínimo, [0,1,0] - medio, [0,0,1] - maximo\n\t* Frio: 0,1\n\t* Calor: 0,1\n\t* Seco: 0,1\nEjemplo (Ventilador medio [0,1,0], Frio 1, Calor 0, Seco 0): 010 1 0 0\n:") or '0,0,0,0,0,0'
                if posiciones:
                    posiciones = posiciones.replace(" ", "")
                    if "," not in posiciones:
                        posiciones = ",".join(posiciones.split())
            
            read_serial_data(port, int(baudrate), save_to_file=save_to_file, posiciones=posiciones)
        elif choice == '2':
            port = input("Introduce el puerto serial (por defecto '/dev/ttyUSB0'): ") or '/dev/ttyUSB0'
            detect_baud_rate(port)
        elif choice == '3':
            port = input("Introduce el puerto serial (por defecto '/dev/ttyUSB0'): ") or '/dev/ttyUSB0'
            baudrate = input("Introduce la velocidad en baudios (por defecto 2400): ") or '2400'
            measure_time_between_messages(port, int(baudrate))
        elif choice == '4':
            port = input("Introduce el puerto serial (por defecto '/dev/ttyUSB0'): ") or '/dev/ttyUSB0'
            baudrate = input("Introduce la velocidad en baudios (por defecto 2400): ") or '2400'
            calculate_message_size(port, int(baudrate))
        elif choice == '5':
            print("Saliendo del programa.")
            break
        else:
            print("Opción no válida. Por favor, selecciona una opción del menú.")

if __name__ == "__main__":
    main_menu()
