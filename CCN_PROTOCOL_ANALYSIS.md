# Análisis del Protocolo CCN - Carrier CRC2-NTC

> **Proyecto:** Reverse Engineering del Termostato Carrier CRC2-NTC  
> **Fecha:** Marzo 2026  
> **Arquitectura de Hardware:** 3 hilos (+12V, GND, Datos)  
> **Versión del Documento:** 2.0 (actualizado para arquitectura actual)

---

## 1. Visión General del Protocolo

### 1.1 Identificación
| Parámetro | Valor |
|-----------|-------|
| **Protocolo** | CCN (Carrier Comfort Network) |
| **Tipo** | Propietario de Carrier |
| **Capa física** | RS-485 (single-wire sobre 3-hilo) |
| **Alimentación** | +12V DC sobre el mismo bus |
| **Arquitectura** | Broadcast unidireccional (simplex) |

### 1.2 Características de la Capa Física
```
Conexión de 3 hilos:
    P (Power)  ────────► +12V
    G (Ground) ────────► GND  
    C (Data)   ────────► RS-485 Data (Half-duplex simplex)
```

- **Modo de transmisión:** El termostato transmite de forma **automática y cíclica**
- **Comunicación:** **Unidireccional** (solo transmite, no recibe comandos)
- **Rol del termostato:** **Broadcast emitter** (emisor periódico de estado)

---

## 2. Parámetros de Comunicación

| Parámetro | Valor Detectado | Notas |
|-----------|-----------------|-------|
| **Baudrate** | 2400 baudios | Confirmado por detección automática |
| **Bits de datos** | 8 | Estándar RS-485 |
| **Paridad** | Ninguna | No detectada |
| **Bits de parada** | 1 | Inferido |
| **Longitud de trama** | **Variable: 85/88/91/94 bytes** | Dependiendo del estado del termostato |
| **Timeout recomendado** | 0.1 segundos | Configurado en `curryrtoolslib/utils/config.py` |

> **Nota importante:** A diferencia de lo documentado inicialmente (88 bytes fijos), el protocolo CCN genera tramas de **múltiples tamaños**. Ver sección 2.3.

---

## 3. Estructura de la Trama

### 3.1 Múltiples Tamaños de Trama

El protocolo CCN del CRC2-NTC genera tramas de diferentes longitudes según la complejidad del estado:

| Tamaño | Contexto detectado | Frecuencia |
|--------|-------------------|------------|
| **85 bytes** | Estados simples (fan only) | Baja |
| **88 bytes** | Estados con modo activo (cool/heat/dry) | **Alta** |
| **91 bytes** | Estados extendidos | Media |
| **94 bytes** | Estados complejos/con sensores | Baja |

**Validación en código:**
```python
# De curryrtoolslib/utils/trama.py
VALID_SIZES = [85, 88, 91, 94]
```

### 3.2 Diagrama de la Trama (88 bytes - caso más común)

```
┌─────────┬─────────┬─────────┬──────────────────┬─────────┬──────────────────┐
│  STX    │ Header  │  SEP    │   DATA BLOCK A   │  SEP    │   DATA BLOCK B   │
│ 3 bytes │         │ 1 byte  │     11 bytes     │ 1 byte  │     14 bytes     │
├─────────┴─────────┴─────────┴──────────────────┴─────────┴──────────────────┤
│ 0x00 │ 0x00 │ 0x08 │ 0x??-0x?? │ 0x00 │ 0x??-0x?? │ 0x00 │ 0x00 │ 0x08 │ ... │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────┬──────────────────┬─────────┬──────────────────────────────────────┐
│  SEP    │   DATA BLOCK C   │  SEP    │        DATA BLOCKS D-G               │
│ 2 bytes │     12 bytes     │ 3 bytes │            40 bytes                  │
├─────────┴──────────────────┴─────────┴──────────────────────────────────────┤
│ 0x00 │ 0x00 │ 0x??-0x?? │ 0x00 │ 0x00 │ 0x08 │ 0x??-0x?? ... 0x08 │ 0x??   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Bytes Fijos (Delimitadores)

| Posición | Valor Hex | Función | Frecuencia |
|----------|-----------|---------|------------|
| 0-1 | `0x00 0x00` | STX / Start of Frame | 100% |
| 2 | `0x08` | Separador inicial | 100% |
| 15 | `0x00` | Delimitador de bloque A | 100% |
| 16 | `0x00` | Separador de bloque B | 100% |
| 17 | `0x08` | Separador de bloque B | 100% |
| 30 | `0x00` | Delimitador de bloque B | 100% |
| 31 | `0x00` | Separador de bloque C | 100% |
| 32 | `0x08` | Separador de bloque C | 100% |
| 45 | `0x00` | Delimitador de bloque C | 100% |
| 46 | `0x00` | Separador de bloque D | 100% |
| 47 | `0x08` | Separador de bloque D | 100% |
| 58 | `0x08` | Separador de bloque E | 100% |

**Validación en código:**
```python
# De curryrtoolslib/utils/trama.py línea 13
if not trama_bytes[0:2] != [b"\x00", b"\x08"]:
    print("Trama inválida (No comienza por 0,8)")
```

### 3.4 Bytes Variables (Datos Útiles)

**72 bytes de carga útil** distribuidos en bloques de datos entre los delimitadores.

---

## 4. Análisis de Valores

### 4.1 Conjunto de Valores Válidos

El protocolo CCN utiliza un **alfabeto extremadamente limitado** de solo 12 valores:

| Dec | Hex | ASCII | Frecuencia Observada | Probable Uso |
|-----|-----|-------|---------------------|--------------|
| 0 | `0x00` | NUL | Alto | Delimitador |
| 8 | `0x08` | BS | Alto | Separador de campo |
| 9 | `0x09` | TAB | Bajo | Dato variable |
| 11 | `0x0B` | VT | Bajo | Dato variable |
| 33 | `0x21` | `!` | Medio | Dato variable (¡= '!') |
| 40 | `0x28` | `(` | Medio | Dato variable |
| 41 | `0x29` | `)` | Medio | Dato variable |
| 97 | `0x61` | `a` | Alto | Dato variable (¡= 'a') |
| 99 | `0x63` | `c` | Medio | Dato variable (¡= 'c') |
| 104 | `0x68` | `h` | Alto | Dato variable (¡= 'h') |
| 105 | `0x69` | `i` | Alto | Dato variable (¡= 'i') |
| 107 | `0x6B` | `k` | Medio | Dato variable (¡= 'k') |

### 4.2 Observaciones sobre Codificación

- **Rango:** 0-107 decimal (nunca > 0x6B)
- **Patrón ASCII:** Los valores imprimibles (`0x21`, `0x61-0x6B`) sugieren:
  - Posible codificación de comandos/modos con caracteres legibles
  - `h`, `i`, `k` pueden ser abreviaturas de funciones (Heat, Indoor, Cool?)
  - `a`, `c` podrían indicar estados (Auto, Cool)

### 4.3 Normalización de Datos

El código actual elimina ciertos bytes "no necesarios" durante el preprocesamiento:

```python
# De curryrtoolslib/utils/trama.py líneas 115-127
def normalizar_bloque(bloque: int, data: List[int]) -> List[int]:
    """Elimina posiciones datos no necesarios conocidos."""
    result = []
    for pos, valor in enumerate(data):
        if pos in [0]:  # Elimina 0x00 iniciales
            continue
        elif bloque in [0, 1, 2]:
            if pos in [1, 2, 3, 4] and valor == 8:  # elimina 0x08 de campos 1-4
                continue
        elif bloque in [3, 4, 5]:
            if pos in [1, 2] and valor == 8:  # elimina 0x08 de campos 5-6
                continue
        result.append(valor)
    return result
```

---

## 5. Captura y Almacenamiento de Datos

### 5.1 Formato Binario (Actual)

El proyecto ha migrado de CSV a formato binario para mayor eficiencia:

```python
# Estructura de archivos generados por devices_interface.py

Archivo .bin:
- Contenido: Datos crudos de la trama (bytes)
- Tamaño: Variable según trama (85/88/91/94 bytes por mensaje)

Archivo .info (JSON):
{
    "stream": "dumps/<uuid>.bin",
    "blocks": 10,           // Número de tramas capturadas
    "timeout": 0.1,         // Timeout de lectura
    "baudrate": 2400,       // Velocidad
    "times": [              // Timestamps y tamaños
        ["2024-11-27T21:16:00.123", 88],
        ["2024-11-27T21:16:00.456", 88],
        ...
    ],
    "uuid": "uuid-v4",
    "values": "0,0,1,0,0,1"  // Estado de controles capturado
}
```

### 5.2 Comando de Captura Actual

```bash
python3 curryrtool.py device read \
    -p /dev/ttyUSB0 \
    -b 2400 \
    -t 0.1 \
    -o "0,0,1,0,0,1" \
    -s
```

**Parámetros**:
- `-p`: Puerto serial
- `-b`: Baudrate
- `-t`: Timeout entre lecturas
- `-o`: Estado de controles (fan1,fan2,fan3,cold,hot,dry)
- `-s`: Guardar a archivo

### 5.3 Formato Legacy (CSV)

Los datos antiguos se mantienen en formato CSV para referencia:

```csv
Trama;Posiciones
0,0,8,8,33,33,...;0,0,1,0,0,1
```

Ubicación: `dumps/datos_hex_2400_0-0-1-0-0-1_2024-11-27_21-16-00.csv`

---

## 6. Checksum y Verificación de Integridad

### 6.1 Candidatos Probados (Sin éxito)

| Algoritmo | Resultado | Notas |
|-----------|-----------|-------|
| XOR de todos los bytes | No coincide | Último byte ≠ XOR(data) |
| Suma módulo 256 | No coincide | Penúltimo byte ≠ SUM(data) |
| Suma invertida | No coincide | |
| Fletcher-8 | No coincide | |
| CRC-8 (polinomios estándar) | No probado exhaustivamente | Requiere más muestras |

### 6.2 Observaciones del Checksum

- **Longitud probable:** 1-2 bytes al final de la trama (posiciones 86-87 en trama de 88)
- **Tipo probable:** CRC-8 con polinomio propietario de Carrier
- **Alternativa:** Suma ponderada o checksum por bloques

### 6.3 Script de Análisis de Checksum

```python
# checksum_analysis.py - Script recomendado para fase de investigación

def test_checksum_algorithms(frame):
    """Prueba múltiples algoritmos de checksum contra la trama"""
    data = frame[:-1]  # Asumiendo último byte es CRC
    expected_crc = frame[-1]
    
    results = {}
    
    # XOR simple
    xor_val = 0
    for b in data:
        xor_val ^= b
    results['xor_all'] = xor_val == expected_crc
    
    # Suma módulo 256
    results['sum_mod256'] = (sum(data) & 0xFF) == expected_crc
    
    # CRC-8 con diferentes polinomios
    polys = [0x07, 0x31, 0x9B, 0xD5, 0xA6]
    for poly in polys:
        crc = crc8(data, poly)
        results[f'crc8_0x{poly:02X}'] = crc == expected_crc
    
    return results
```

---

## 7. Emulación y Transmisión

### 7.1 Envío de Tramas Capturadas

El sistema permite reproducir tramas capturadas para emular el comportamiento del termostato:

```bash
python3 curryrtool.py device write \
    -p /dev/ttyUSB0 \
    -b 2400 \
    -t 0.1 \
    -f dumps/<uuid>.bin \
    -r 100 \
    -i 5
```

**Parámetros**:
- `-f`: Archivo de trama (.bin)
- `-r`: Número de repeticiones
- `-i`: Intervalo entre envíos (segundos)

### 7.2 Modo Repetidor (Sniffer)

Para capturar tráfico bidireccional o actuar como puente:

```bash
python3 curryrtool.py device repeat \
    -p /dev/ttyUSB0 \      # Puerto de entrada
    -r /dev/ttyUSB1 \      # Puerto de salida
    -b 2400 \
    -t 0.1
```

---

## 8. Comparativa con Otros Protocolos

### 8.1 vs Modbus RTU

| Característica | Modbus RTU | CCN (Carrier) |
|----------------|------------|---------------|
| Silencio entre tramas | 3.5 caracteres | No requerido (delimitadores) |
| Dirección esclavo | Byte 0 | No identificada |
| Código función | Byte 1 | No identificado |
| CRC | 2 bytes (LSB-MSB) | 1-2 bytes (formato desconocido) |
| Longitud | Variable | **Variable: 85/88/91/94 bytes** |

### 8.2 vs BACnet MS/TP

| Característica | BACnet MS/TP | CCN (Carrier) |
|----------------|--------------|---------------|
| Preamble | `0x55 0xFF` | `0x00 0x00 0x08` |
| Frame Type | Byte 2 | No identificado |
| Dirección | Bytes 3-4 | No identificada |
| Longitud máxima | 501 bytes | **94 bytes** |

---

## 9. Hipótesis sobre la Codificación

### 9.1 Modelo de Codificación "Carrier ASCII"

La limitación a valores 0-107 sugiere una codificación de 7-bits con restricciones:

```
Bits válidos: 0xxx xxxx (0-127 range, bit 7 siempre 0)
Subconjunto usado: 0xxx xxxx donde xxx xxxx ∈ {0,8-11,33,40-41,97-99,104-105,107}
```

### 9.2 Posible Estructura de Comandos

Los valores ASCII imprimibles (`!`, `a`, `c`, `h`, `i`, `k`) podrían representar:

| Código | Posible Significado | Contexto HVAC |
|--------|---------------------|---------------|
| `!` (0x21) | Stop / Off | Fan stopped |
| `a` (0x61) | Auto | Modo automático |
| `c` (0x63) | Cool | Modo refrigeración |
| `h` (0x68) | Heat | Modo calefacción |
| `i` (0x69) | Indoor / Idle | Estado interior |
| `k` (0x6B) | ? | Estado especial |

### 9.3 Codificación Numérica

Para valores numéricos (temperaturas, setpoints):
- Posible **offset + escala**: Valor = (byte - offset) × escala
- Ejemplo: Si `0x21` = 16°C, entonces offset = 17 (0x21 - 17 = 0, escala 1°C)

---

## 10. Limitaciones Actuales del Análisis

### 10.1 Datos Insuficientes

1. **Dataset limitado:** Solo 13 tramas CSV antiguas + capturas binarias recientes
2. **Sin variación de estados sistemática:** No se ha capturado todas las combinaciones fan×modo
3. **Sin referencia temporal detallada:** Intervalos entre tramas no medidos con precisión
4. **Sin temperatura variable:** No se han capturado diferentes setpoints documentados

### 10.2 Aspectos No Resueltos

- [ ] Algoritmo de checksum exacto
- [ ] Codificación de temperatura ambiente
- [ ] Codificación de temperatura setpoint
- [ ] Identificación de bits de error/alarmas
- [ ] Formato de dirección de dispositivo (si existe)
- [ ] Correlación exacta byte-a-byte para cada control

---

## 11. Herramientas de Análisis Disponibles

### 11.1 En el Proyecto

| Script/Función | Ubicación | Propósito |
|----------------|-----------|-----------|
| `curryrtool.py` | Raíz | CLI principal |
| `devices_interface.py` | `interfaces/` | Captura y emulación |
| `trama.py` | `utils/` | Validación y normalización |
| `ia.py` | `utils/` | Modelos ML para clasificación |

### 11.2 Scripts Recomendados (Ver CHECKLIST.md)

- `timing_analysis.py` - Medir período cíclico
- `diff_analysis.py` - Comparar tramas entre estados
- `checksum_crack.py` - Probar algoritmos CRC

---

## 12. Conclusión

El protocolo CCN del termostato Carrier CRC2-NTC es un protocolo **propietario, unidireccional y cíclico** con las siguientes características distintivas:

1. **Tramas variables de 85-94 bytes** (no fijas como inicialmente se pensó)
2. **Alfabeto limitado a 12 valores** (0-107, subconjunto ASCII)
3. **Estructura de bloques** separados por bytes `0x00` y `0x08`
4. **Transmisión automática** sin requerir polling del maestro
5. **Codificación posiblemente semántica** usando caracteres ASCII (`a`, `c`, `h`, `i`)
6. **Formato binario optimizado** (.bin + .info JSON) para almacenamiento eficiente

Para completar el análisis y habilitar la emulación completa del termostato, es necesario realizar **capturas sistemáticas con variación controlada de cada parámetro** (ver `CHECKLIST.md`).

---

## 13. Referencias y Recursos

### 13.1 Documentación Carrier

- NTC Controller Manual (CCN reference)
- CRC2 Installation Manual (IOM 126H69)
- Carrier Comfort Network specification (no público)

### 13.2 Recursos del Proyecto

| Archivo | Descripción |
|---------|-------------|
| `AGENTS.md` | Guía completa de la arquitectura actual |
| `CHECKLIST.md` | Guía paso a paso para reverse engineering |
| `README_es.md` | Documentación general del proyecto |
| `curryrtool.py` | CLI principal |
| `curryrtoolslib/` | Código fuente del paquete |

---

*Documento actualizado para reflejar la arquitectura actual del proyecto (Marzo 2026)*
*Versión 2.0 - Incluye múltiples tamaños de trama y formato binario*
