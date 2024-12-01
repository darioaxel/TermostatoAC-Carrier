VALID_SIZES=[85,88,91,94]

def pre_proccess_trama(trama, file_time):
    """
    Preprocesa una trama de datos para su envío.

    :param trama: La trama de datos a preprocesar.
    :return: La trama preprocesada.
    """
    times_trama = []    
    with open("%s.time" % file_time, "r") as f:
        for linea in f.readlines():
            times_trama.append(float(linea.strip()))

    lineas = []
    linea_actual = []
    for num, byte_str in enumerate(trama):
        byte = byte_str.encode()
        if byte == b"\x00":
            if num < len(trama) - 1 and trama[num + 1].encode() == b"\x08":
                if linea_actual:
                    lineas.append(linea_actual)
                linea_actual = []
        linea_actual.append(byte)
    
    if linea_actual:
        lineas.append(linea_actual)

    return [[linea, times_trama[num]] for num, linea in  enumerate(lineas)]

def validar_trama_bytes(trama_bytes):
    valid = True
    if not trama_bytes[0:2] != [b"\x00",b"\x08"]:
        print("Trama inválida (No comienza por 0,8)",trama_bytes)
        valid = False
    elif len(trama_bytes) not in VALID_SIZES:
        print("Trama inválida (No tiene %s bytes):" % (VALID_SIZES), trama_bytes)
        valid = False
    
    return valid