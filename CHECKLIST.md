# Checklist - Ingeniería Inversa del Protocolo CCN

> **Objetivo:** Identificar completamente el protocolo CCN del termostato Carrier CRC2-NTC para emular su comportamiento  
> **Método:** Análisis diferencial con variación controlada de estados  
> **Hardware:** Adaptador USB-RS485 (CH341) + Conexión 3-hilos (+12V, GND, Datos)

---

## 📋 Índice de Fases

1. [Fase 0: Preparación del Entorno](#fase-0-preparación-del-entorno)
2. [Fase 1: Caracterización Temporal](#fase-1-caracterización-temporal)
3. [Fase 2: Análisis Diferencial por Control](#fase-2-análisis-diferencial-por-control)
4. [Fase 3: Ingeniería Inversa del Checksum](#fase-3-ingeniería-inversa-del-checksum)
5. [Fase 4: Validación y Emulación](#fase-4-validación-y-emulación)

---

## Fase 0: Preparación del Entorno

### 0.1 Verificación de Hardware

- [ ] Conectar adaptador USB-RS485 a puerto USB
- [ ] Verificar detección: `ls -la /dev/ttyUSB*`
- [ ] Verificar permisos: `sudo usermod -a -G dialout $USER` (si es necesario)
- [ ] Conectar termostato: P→+12V, G→GND, C→RS485-A/B
- [ ] Verificar LED de actividad en el adaptador

### 0.2 Preparación de Scripts

- [ ] Verificar `USB2RS485.py` funciona correctamente
- [ ] Crear directorio de capturas: `mkdir -p dumps/phase1 dumps/phase2 dumps/phase3`
- [ ] Preparar script de captura automatizada (ver abajo)

### 0.3 Script de Captura Base

```bash
#!/bin/bash
# capture.sh - Script base para capturas sistemáticas

STATE_NAME=$1
POSITIONS=$2  # formato: "0,0,1,0,0,1"
BAUDRATE=${3:-2400}
DURATION=${4:-30}  # segundos de captura

TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
FILENAME="dumps/phase2/${STATE_NAME}_${TIMESTAMP}.csv"

echo "Capturando estado: $STATE_NAME"
echo "Posiciones: $POSITIONS"
echo "Duración: ${DURATION}s"
echo "Configura el termostato y presiona ENTER para iniciar..."
read

python3 USB2RS485.py << EOF
1
/dev/ttyUSB0
$BAUDRATE
s
$POSITIONS
EOF

echo "Captura guardada. Presiona ENTER para finalizar..."
read
```

---

## Fase 1: Caracterización Temporal

### 1.1 Medición de Intervalos entre Tramas

**Objetivo:** Determinar período de transmisión cíclica

```python
# timing_analysis.py
import serial
import time
import statistics

ser = serial.Serial('/dev/ttyUSB0', 2400, timeout=0.1)
intervals = []
last_time = time.time()

print("Midiendo intervalos... Ctrl+C para detener")
try:
    while len(intervals) < 100:
        if ser.read(1):
            now = time.time()
            interval = (now - last_time) * 1000  # ms
            if interval > 10:  # Filtrar ruido
                intervals.append(interval)
                print(f"Intervalo {len(intervals)}: {interval:.2f} ms")
            last_time = now
except KeyboardInterrupt:
    pass

print(f"\nEstadísticas:")
print(f"  Muestras: {len(intervals)}")
print(f"  Media: {statistics.mean(intervals):.2f} ms")
print(f"  Mediana: {statistics.median(intervals):.2f} ms")
print(f"  Desv. estándar: {statistics.stdev(intervals):.2f} ms")
print(f"  Min: {min(intervals):.2f} ms, Max: {max(intervals):.2f} ms")
```

- [ ] Ejecutar script durante 2-3 minutos
- [ ] Anotar período medio de transmisión: _____ ms
- [ ] Calcular jitter (desviación): _____ ms

### 1.2 Medición de Tiempo de Trama

```python
# frame_duration.py
import serial
import time

ser = serial.Serial('/dev/ttyUSB0', 2400, timeout=0.1)

# A 2400 baudios: 1 bit = 416.67 µs
# 1 byte (8N1) = 10 bits = 4.167 ms
# 88 bytes = 366.67 ms teóricos

print("Midiendo duración de tramas...")
for i in range(10):
    start = time.time()
    data = ser.read(88)  # Leer una trama completa
    if len(data) == 88:
        duration = (time.time() - start) * 1000
        print(f"Trama {i+1}: {duration:.2f} ms")
```

- [ ] Verificar duración teórica vs real
- [ ] Confirmar que todas las tramas son exactamente 88 bytes

### 1.3 Análisis de Jitter y Estabilidad

- [ ] Capturar 100 tramas seguidas sin cambiar controles
- [ ] Verificar que el contenido es idéntico (bit-perfect) o varía ligeramente
- [ ] Identificar si hay contador de secuencia o timestamp

---

## Fase 2: Análisis Diferencial por Control

### 2.1 Captura Base - Todos los Controles en OFF

```
Estado: TODOS_OFF
Posiciones: 0,0,0,0,0,0 (fan=stop, cold=off, hot=off, dry=off)
Archivo: dumps/phase2/ALL_OFF_XXXXXX.csv
Cantidad: 20 tramas mínimo
```

- [ ] Apagar termostato o poner en modo standby
- [ ] Capturar 20 tramas
- [ ] Verificar consistencia interna

### 2.2 Variación de Velocidad del Ventilador

| Estado | Posiciones | Archivo Esperado | Prioridad |
|--------|------------|------------------|-----------|
| FAN_STOP | 0,0,0,0,0,0 | `FAN_STOP_*.csv` | ⭐⭐⭐ |
| FAN_LOW | 1,0,0,0,0,0 | `FAN_LOW_*.csv` | ⭐⭐⭐ |
| FAN_MED | 0,1,0,0,0,0 | `FAN_MED_*.csv` | ⭐⭐⭐ |
| FAN_HIGH | 0,0,1,0,0,0 | `FAN_HIGH_*.csv` | ⭐⭐⭐ |

Para cada estado:
- [ ] Configurar termostato (solo cambiar velocidad fan)
- [ ] Esperar 5 segundos a estabilización
- [ ] Capturar 10-15 tramas
- [ ] Anotar en README qué LED/iconos muestra el display

### 2.3 Variación de Modos (con ventilador en MED)

| Estado | Posiciones | Archivo Esperado | Display |
|--------|------------|------------------|---------|
| MODE_COOL | 0,1,0,1,0,0 | `MODE_COOL_*.csv` | ❄️ + ventilador |
| MODE_HEAT | 0,1,0,0,1,0 | `MODE_HEAT_*.csv` | ☀️ + ventilador |
| MODE_DRY | 0,1,0,0,0,1 | `MODE_DRY_*.csv` | 💧 + ventilador |
| MODE_FAN | 0,1,0,0,0,0 | `MODE_FAN_*.csv` | Solo ventilador |

Para cada modo:
- [ ] Seleccionar modo en termostato
- [ ] Verificar que el icono correspondiente está activo
- [ ] Capturar 10-15 tramas

### 2.4 Combinaciones Modo + Velocidad

| Estado | Posiciones | Archivo Esperado |
|--------|------------|------------------|
| COOL_LOW | 1,0,0,1,0,0 | `COOL_LOW_*.csv` |
| COOL_HIGH | 0,0,1,1,0,0 | `COOL_HIGH_*.csv` |
| HEAT_MED | 0,1,0,0,1,0 | `HEAT_MED_*.csv` |
| DRY_LOW | 1,0,0,0,0,1 | `DRY_LOW_*.csv` |

- [ ] Capturar combinaciones prioritarias

### 2.5 Análisis de Temperatura/Setpoint

Si el termostato permite ajustar temperatura de consigna:

| Estado | Setpoint | Archivo Esperado |
|--------|----------|------------------|
| TEMP_16C | 16°C | `TEMP_16C_*.csv` |
| TEMP_20C | 20°C | `TEMP_20C_*.csv` |
| TEMP_24C | 24°C | `TEMP_24C_*.csv` |
| TEMP_28C | 28°C | `TEMP_28C_*.csv` |

- [ ] Capturar con modo COOL + MED fijo, variando solo setpoint
- [ ] Verificar si el display muestra temperatura ambiente o setpoint

### 2.6 Script de Análisis Diferencial

```python
# diff_analysis.py
import csv
import os
from collections import defaultdict

def load_frame(filepath):
    """Carga la primera trama de un CSV"""
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f, delimiter=';')
        row = next(reader)
        return [int(x) for x in row['Trama'].split(',')]

def compare_frames(frame1, frame2, label1="Base", label2="Target"):
    """Compara dos tramas y muestra diferencias"""
    print(f"\n{'='*60}")
    print(f"Comparación: {label1} vs {label2}")
    print(f"{'='*60}")
    
    diff_positions = []
    for i, (a, b) in enumerate(zip(frame1, frame2)):
        if a != b:
            diff_positions.append(i)
            print(f"  Pos {i:2d}: 0x{a:02X} ({a:3d}) → 0x{b:02X} ({b:3d})")
    
    print(f"\nTotal bytes diferentes: {len(diff_positions)}")
    print(f"Posiciones: {diff_positions}")
    return diff_positions

# Uso:
# base = load_frame("dumps/phase2/ALL_OFF_xxx.csv")
# fan_low = load_frame("dumps/phase2/FAN_LOW_xxx.csv")
# compare_frames(base, fan_low, "ALL_OFF", "FAN_LOW")
```

- [ ] Ejecutar análisis para cada par de estados
- [ ] Crear matriz de correlación control→bytes

### 2.7 Matriz de Correlación

Documentar en archivo de texto:

```
CORRELACIÓN CONTROL → BYTES
===========================

FAN Speed (STOP/LOW/MED/HIGH):
  - Bytes afectados: [_, _, _]
  - Valores observados:
    * STOP: 0x__
    * LOW:  0x__
    * MED:  0x__
    * HIGH: 0x__

Mode (COOL/HEAT/DRY/FAN):
  - Bytes afectados: [_, _, _]
  - Valores observados:
    * COOL: 0x__
    * HEAT: 0x__
    * DRY:  0x__
    * FAN:  0x__

Setpoint:
  - Bytes afectados: [_]
  - Codificación: Lineal/Tabla/Offset?
```

---

## Fase 3: Ingeniería Inversa del Checksum

### 3.1 Identificación de Bytes de Checksum

Candidatos (posiciones que varían "aleatoriamente"):
- Posición 86: _____
- Posición 87: _____

### 3.2 Prueba de Algoritmos

```python
# checksum_crack.py

def crc8_ccitt(data):
    """CRC-8 CCITT (0x07)"""
    crc = 0
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ 0x07
            else:
                crc <<= 1
        crc &= 0xFF
    return crc

def crc8_rohc(data):
    """CRC-8 ROHC (0x07, init=0xFF)"""
    crc = 0xFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ 0x07
            else:
                crc <<= 1
        crc &= 0xFF
    return crc

def test_checksum(frame, checksum_pos=-1):
    data = frame[:checksum_pos]
    expected = frame[checksum_pos]
    
    tests = {
        'xor_all': 0,
        'sum_mod256': sum(data) & 0xFF,
        'sum_inv': (~sum(data)) & 0xFF,
        'xor_reduce': 0,
        'crc8_ccitt': crc8_ccitt(data),
        'crc8_rohc': crc8_rohc(data),
        'fletcher8': (sum(data) & 0xFF) ^ ((sum(data) >> 8) & 0xFF),
    }
    
    for name in tests:
        tests['xor_reduce'] ^= tests['xor_all']
    
    return {name: (val == expected) for name, val in tests.items()}

# Probar con múltiples tramas
# Si ninguno coincide, probar con polinomios: 0x31, 0x9B, 0xD5
```

- [ ] Probar CRC-8 con polinomios: 0x07, 0x31, 0x9B, 0xD5, 0xA6
- [ ] Probar checksum por bloques (cada bloque entre 0x00 tiene su propio CRC)
- [ ] Probar XOR acumulativo con inicialización != 0

### 3.3 Análisis de Mutación

```python
# Mutar un bit y observar cambio en checksum
def mutate_and_check(original, position):
    """Muta un byte y compara checksum resultante"""
    mutated = original.copy()
    mutated[position] ^= 0x01  # Flip LSB
    
    orig_crc = original[-1]
    mut_crc = mutated[-1]
    
    print(f"Mutación pos {position}: CRC 0x{orig_crc:02X} → 0x{mut_crc:02X}")
    print(f"  Diferencia: 0x{(orig_crc ^ mut_crc):02X}")
```

- [ ] Mutar cada byte de datos y observar efecto en checksum
- [ ] Si el cambio es lineal → probablemente XOR o suma
- [ ] Si el cambio es no lineal → CRC polinomial

---

## Fase 4: Validación y Emulación

### 4.1 Construcción de Parser CCN

```python
# ccn_parser.py

class CCNFrame:
    """Parser de trama CCN de 88 bytes"""
    
    # Offset mapping (actualizar tras análisis)
    OFFSET_FAN = 3      # Hipótesis
    OFFSET_MODE = 7     # Hipótesis
    OFFSET_TEMP = 13    # Hipótesis
    OFFSET_CRC = 86     # Hipótesis
    
    FAN_VALUES = {
        0x21: 'STOP',
        0x61: 'LOW',
        0x63: 'MED',
        0x68: 'HIGH',
    }
    
    MODE_VALUES = {
        0x69: 'IDLE',
        0x28: 'COOL',
        0x68: 'HEAT',
        0x6B: 'DRY',
    }
    
    def __init__(self, data):
        if len(data) != 88:
            raise ValueError(f"Trama debe ser 88 bytes, recibido {len(data)}")
        self.data = data
    
    def parse(self):
        return {
            'fan_speed': self.FAN_VALUES.get(self.data[self.OFFSET_FAN], 'UNKNOWN'),
            'mode': self.MODE_VALUES.get(self.data[self.OFFSET_MODE], 'UNKNOWN'),
            'raw': self.data,
            'valid_crc': self._verify_crc(),
        }
    
    def _verify_crc(self):
        # Implementar tras descubrir algoritmo
        return True
```

### 4.2 Generador de Tramas

```python
# ccn_generator.py

def generate_frame(fan='MED', mode='COOL', temp=22):
    """Genera una trama CCN con los parámetros dados"""
    frame = bytearray(88)
    
    # Header fijo
    frame[0:3] = [0x00, 0x00, 0x08]
    
    # Fan (actualizar valores reales tras análisis)
    fan_map = {'STOP': 0x21, 'LOW': 0x61, 'MED': 0x63, 'HIGH': 0x68}
    frame[3] = fan_map.get(fan, 0x63)
    
    # Mode (actualizar valores reales)
    mode_map = {'IDLE': 0x69, 'COOL': 0x28, 'HEAT': 0x68, 'DRY': 0x6B}
    frame[7] = mode_map.get(mode, 0x28)
    
    # Resto de campos (copiar de trama de referencia)
    # ... completar según análisis
    
    # Calcular y añadir CRC
    frame[86] = calculate_crc(frame[:86])
    frame[87] = 0x08  # Separador final?
    
    return bytes(frame)
```

### 4.3 Prueba de Emulación

```python
# emulation_test.py
import serial
import time

ser = serial.Serial('/dev/ttyUSB0', 2400, timeout=1)

# Generar trama emulada
frame = generate_frame(fan='MED', mode='COOL')

print("Transmitiendo trama emulada...")
for i in range(10):
    ser.write(frame)
    time.sleep(0.5)  # Ajustar según período medido

print("Tramas enviadas. Verificar si el NTC reacciona.")
```

- [ ] Transmitir trama emulada y observar reacción del NTC
- [ ] Si el NTC acepta la trama → checksum correcto
- [ ] Si no hay reacción → revisar checksum o estructura

### 4.4 Integración con ML

- [ ] Actualizar `trainning_tools.py` con mapeo de bytes conocidos
- [ ] Entrenar modelo con dataset completo de estados
- [ ] Validar precisión de predicción > 95%

---

## 📊 Registro de Progreso

### Registro de Capturas

| Fase | Estado | Fecha | Archivo | Tramas | Notas |
|------|--------|-------|---------|--------|-------|
| 2.1 | ALL_OFF | | | | |
| 2.2 | FAN_STOP | | | | |
| 2.2 | FAN_LOW | | | | |
| 2.2 | FAN_MED | | | | |
| 2.2 | FAN_HIGH | | | | |
| 2.3 | MODE_COOL | | | | |
| 2.3 | MODE_HEAT | | | | |
| 2.3 | MODE_DRY | | | | |

### Descubrimientos Clave

```
[Fecha] - Hallazgo: Los bytes 3-5 codifican velocidad del ventilador
[Fecha] - Hallazgo: El checksum es CRC-8 con polinomio 0x__
[Fecha] - Hallazgo: La temperatura se codifica en posición __
```

---

## 🔧 Herramientas Adicionales

### Visualización Hexadecimal en Tiempo Real

```bash
# Ver tramas en tiempo real en formato hex
python3 -c "
import serial
ser = serial.Serial('/dev/ttyUSB0', 2400, timeout=0.1)
while True:
    data = ser.read(88)
    if len(data) == 88:
        print(' '.join(f'{b:02X}' for b in data[:16]))
"
```

### Decodificador Rápido

```bash
# Decodificar un CSV recién capturado
python3 -c "
import csv, sys
with open(sys.argv[1]) as f:
    row = next(csv.DictReader(f, delimiter=';'))
    frame = [int(x) for x in row['Trama'].split(',')]
    print('Frame:', ' '.join(f'{b:02X}' for b in frame))
" dumps/phase2/ARCHIVO.csv
```

---

## ✅ Criterios de Éxito

### Nivel 1: Básico (Reversible)
- [ ] Identificar bytes que codifican FAN speed (4 estados)
- [ ] Identificar bytes que codifican MODE (COOL/HEAT/DRY)
- [ ] Determinar algoritmo de checksum

### Nivel 2: Intermedio (Emulable)
- [ ] Generar trama válida que el NTC acepte
- [ ] Emular cambio de modo remoto
- [ ] Parser que decodee 100% de tramas capturadas

### Nivel 3: Avanzado (Reemplazo Completo)
- [ ] Implementar control remoto completo del NTC
- [ ] Integrar con sistema de automatización (Home Assistant, etc.)
- [ ] Documentación completa del protocolo CCN para CRC2-NTC

---

*Checklist v1.0 - Proyecto TermostatoAC-Carrier*
