import serial
import time
from datetime import datetime

def read_serial_data(port='/dev/ttyUSB0', baudrate=9600, timeout=1, save_to_file=False):
    """
    Lee y muestra los datos recibidos desde un puerto serial específico.
    Detecta la finalización de un stream de bits y lo guarda en un archivo
    junto con un comentario que indique que el stream ha terminado.
    
    :param port: El nombre del puerto serial, por defecto '/dev/ttyUSB0'.
    :param baudrate: La velocidad en baudios, por defecto 9600.
    :param timeout: El tiempo de espera en segundos para la lectura del puerto, por defecto 1 segundo.
    :param save_to_file: Si es True, guarda los datos en un archivo de texto.
    """
    try:
        # Inicializa la conexión serial
        with serial.Serial(port, baudrate, timeout=timeout) as ser:
            print(f"Conectado al puerto {port} con velocidad {baudrate} baudios.")
            
            if save_to_file:
                timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                hex_filename = f'datos_hex_{timestamp}.txt'
                hex_file = open(hex_filename, 'w')
                
                # Escribe un comentario con la velocidad en baudios en el archivo hexadecimal
                hex_file.write(f"# Velocidad en baudios: {baudrate}\n")
                print(f"Guardando datos en {hex_filename}")

            stream_active = False
            stream_data = []

            while True:
                # Lee datos del puerto
                data = ser.read(1024)  # Lee hasta 1024 bytes
                if data:
                    stream_active = True
                    # Convierte los datos a hexadecimal y los agrega al stream actual
                    hex_data = ' '.join(f'{b:02x}' for b in data)
                    stream_data.append(hex_data)
                    print(f"Recibido (hexadecimal): {hex_data}")
                else:
                    if stream_active:
                        # Si el stream estaba activo pero ya no hay más datos, finaliza el stream
                        if save_to_file:
                            # Escribe el stream completo en el archivo
                            hex_file.write("\n".join(stream_data) + "\n")
                            hex_file.write("# STREAM TERMINADO\n")
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
            hex_file.close()
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

def main_menu():
    while True:
        print("\n--- MENÚ PRINCIPAL ---")
        print("1. Leer datos del puerto serial")
        print("2. Detectar velocidad de transmisión (baud rate)")
        print("3. Salir")

        choice = input("Selecciona una opción: ")

        if choice == '1':
            port = input("Introduce el puerto serial (por defecto '/dev/ttyUSB0'): ") or '/dev/ttyUSB0'
            baudrate = input("Introduce la velocidad en baudios (por defecto 9600): ") or '9600'
            save_option = input("¿Quieres guardar los datos en un archivo? (s/n): ").strip().lower()
            save_to_file = save_option == 's'
            read_serial_data(port, int(baudrate), save_to_file=save_to_file)
        elif choice == '2':
            port = input("Introduce el puerto serial (por defecto '/dev/ttyUSB0'): ") or '/dev/ttyUSB0'
            detect_baud_rate(port)
        elif choice == '3':
            print("Saliendo del programa.")
            break
        else:
            print("Opción no válida. Por favor, selecciona una opción del menú.")

if __name__ == "__main__":
    main_menu()
