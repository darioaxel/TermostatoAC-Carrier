# Checklist - Ingeniería Inversa del Protocolo CCN

> **Objetivo:** Identificar completamente el protocolo CCN del termostato Carrier CRC2-NTC para emular su comportamiento  
> **Método:** Análisis diferencial con variación controlada de estados  
> **Hardware:** Adaptador USB-RS485 (CH341) + Conexión 3-hilos (+12V, GND, Datos)  
> **Versión:** 2.0 (actualizado para arquitectura curryrtoolslib)

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

### 0.2 Preparación de Entorno Python

```bash
# Instalar dependencias
pip install pyserial tensorflow numpy matplotlib

# Verificar instalación
python3 -c "import serial; print('pyserial OK')"
python3 -c "import tensorflow; print('tensorflow OK')"
```

### 0.3 Estructura de Directorios

```bash
# Crear estructura para análisis
mkdir -p dumps/phase1 dumps/phase2 dumps/phase3 dumps/analysis
mkdir -p models
mkdir -p scripts/analysis
```

### 0.4 Script de Captura Automatizado

```bash
#!/bin/bash
# capture.sh - Script base para capturas sistemáticas

STATE_NAME=$1
POSITIONS=$2  # formato: "0,0,1,0,0,1"
BAUDRATE=${3:-2400}
TIMEOUT=${4:-0.1}

echo "=============================================="
echo "Captura de estado: $STATE_NAME"
echo "Posiciones: $POSITIONS"
echo "=============================================="
echo ""
echo "Configura el termostato con el estado indicado"
echo "y presiona ENTER para iniciar captura..."
read

echo "Iniciando captura (Ctrl+C para detener)..."
python3 curryrtool.py device read \
    -p /dev/ttyUSB0 \
    -b $BAUDRATE \
    -t $TIMEOUT \
    -o "$POSITIONS" \
    -s

echo ""
echo "Captura finalizada. Verificar archivos en dumps/"
ls -lt dumps/*.bin 2>/dev/null | head -5
echo ""
echo "Presiona ENTER para continuar..."
read
```

Hacer ejecutable:
```bash
chmod +x capture.sh
```

---

## Fase 1: Caracterización Temporal

### 1.1 Medición de Intervalos entre Tramas

**Objetivo:** Determinar período de transmisión cíclica y jitter

```python
# scripts/analysis/timing_analysis.py
import serial
import time
import statistics

def measure_timing(port='/dev/ttyUSB0', baudrate=2400, samples=100):
    ser = serial.Serial(port, baudrate, timeout=0.1)
    intervals = []
    last_time = time.time()
    
    print(f"Midiendo {samples} intervalos... Ctrl+C para detener")
    try:
        while len(intervals) < samples:
            # Leer byte a byte para detectar inicio de trama
            if ser.read(1):
                now = time.time()
                interval = (now - last_time) * 1000  # ms
                if 10 < interval < 5000:  # Filtrar ruido y gaps largos
                    intervals.append(interval)
                    print(f"Intervalo {len(intervals)}: {interval:.2f} ms")
                last_time = now
    except KeyboardInterrupt:
        pass
    finally:
        ser.close()
    
    if intervals:
        print(f"\n{'='*50}")
        print(f"ESTADÍSTICAS DE TIMING")
        print(f"{'='*50}")
        print(f"Muestras: {len(intervals)}")
        print(f"Media: {statistics.mean(intervals):.2f} ms")
        print(f"Mediana: {statistics.median(intervals):.2f} ms")
        print(f"Desv. estándar: {statistics.stdev(intervals):.2f} ms")
        print(f"Min: {min(intervals):.2f} ms")
        print(f"Max: {max(intervals):.2f} ms")
        print(f"Jitter (max-min): {max(intervals)-min(intervals):.2f} ms")
        
        # Guardar resultados
        with open('dumps/analysis/timing_stats.txt', 'w') as f:
            f.write(f"Timing analysis - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Mean: {statistics.mean(intervals):.2f} ms\n")
            f.write(f"StdDev: {statistics.stdev(intervals):.2f} ms\n")
            f.write(f"Samples: {len(intervals)}\n")

if __name__ == '__main__':
    measure_timing()
```

- [ ] Ejecutar durante 2-3 minutos
- [ ] Anotar período medio de transmisión: _____ ms
- [ ] Calcular jitter (desviación): _____ ms
- [ ] **Resultado esperado:** Período cíclico regular, posiblemente 500-2000ms

### 1.2 Análisis de Tamaños de Trama

```python
# scripts/analysis/frame_sizes.py
import serial
import time
from collections import Counter

def analyze_frame_sizes(port='/dev/ttyUSB0', baudrate=2400, duration=60):
    ser = serial.Serial(port, baudrate, timeout=0.1)
    sizes = []
    start_time = time.time()
    
    print(f"Analizando tamaños de trama durante {duration}s...")
    
    while time.time() - start_time < duration:
        # Detectar inicio de trama (0x00)
        byte = ser.read(1)
        if byte == b'\x00':
            # Leer resto de la trama
            data = b'\x00' + ser.read(93)  # Máximo posible
            if len(data) >= 85:
                sizes.append(len(data))
                print(f"Trama detectada: {len(data)} bytes", end='\r')
    
    ser.close()
    
    print(f"\n\n{'='*50}")
    print(f"DISTRIBUCIÓN DE TAMAÑOS")
    print(f"{'='*50}")
    
    counter = Counter(sizes)
    for size, count in sorted(counter.items()):
        pct = (count / len(sizes)) * 100
        bar = '█' * int(pct / 2)
        print(f"{size:2d} bytes: {count:4d} ({pct:5.1f}%) {bar}")
    
    print(f"\nTotal tramas: {len(sizes)}")
    
    # Guardar resultados
    with open('dumps/analysis/frame_sizes.txt', 'w') as f:
        f.write(f"Frame size analysis\n")
        for size, count in sorted(counter.items()):
            f.write(f"{size}: {count}\n")

if __name__ == '__main__':
    analyze_frame_sizes()
```

- [ ] Verificar qué tamaños aparecen (85, 88, 91, 94)
- [ ] Anotar frecuencia de cada tamaño
- [ ] **Resultado esperado:** 88 bytes dominante, otros según estado

### 1.3 Validación de Estructura

```python
# scripts/analysis/validate_frames.py
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from curryrtoolslib.utils import trama as trama_tools

def validate_captured_frames():
    """Valida todas las tramas capturadas en dumps/"""
    dumps_folder = 'dumps'
    
    info_files = [f for f in os.listdir(dumps_folder) if f.endswith('.info')]
    
    print(f"Validando {len(info_files)} capturas...")
    
    for info_file in info_files:
        info_path = os.path.join(dumps_folder, info_file)
        bin_path = info_path.replace('.info', '.bin')
        
        if not os.path.exists(bin_path):
            print(f"⚠️  Faltan datos binarios para {info_file}")
            continue
        
        # Cargar metadatos
        with open(info_path) as f:
            info = json.load(f)
        
        # Cargar y validar tramas
        resultados = trama_tools.cargar_trama_bytes(bin_path)
        
        if resultados:
            print(f"✅ {info_file}: {len(resultados)} tramas válidas")
        else:
            print(f"❌ {info_file}: Error de validación")

if __name__ == '__main__':
    validate_captured_frames()
```

---

## Fase 2: Análisis Diferencial por Control

### 2.1 Captura Base - Todos los Controles en OFF

```bash
# Estado: TODOS_OFF
./capture.sh "ALL_OFF" "0,0,0,0,0,0"

# O manualmente:
python3 curryrtool.py device read -p /dev/ttyUSB0 -b 2400 -t 0.1 -o "0,0,0,0,0,0" -s
```

- [ ] Apagar termostato o poner en modo standby
- [ ] Capturar mínimo 20 tramas
- [ ] Verificar consistencia interna

### 2.2 Variación de Velocidad del Ventilador

| Estado | Posiciones | Comando | Prioridad |
|--------|------------|---------|-----------|
| FAN_STOP | 0,0,0,0,0,0 | `./capture.sh FAN_STOP "0,0,0,0,0,0"` | ⭐⭐⭐ |
| FAN_LOW | 1,0,0,0,0,0 | `./capture.sh FAN_LOW "1,0,0,0,0,0"` | ⭐⭐⭐ |
| FAN_MED | 0,1,0,0,0,0 | `./capture.sh FAN_MED "0,1,0,0,0,0"` | ⭐⭐⭐ |
| FAN_HIGH | 0,0,1,0,0,0 | `./capture.sh FAN_HIGH "0,0,1,0,0,0"` | ⭐⭐⭐ |

Para cada estado:
- [ ] Configurar termostato (solo cambiar velocidad fan)
- [ ] Esperar 5 segundos a estabilización
- [ ] Capturar 10-15 tramas
- [ ] Anotar en README qué LED/iconos muestra el display

### 2.3 Variación de Modos (con ventilador en MED)

| Estado | Posiciones | Comando | Display |
|--------|------------|---------|---------|
| MODE_COOL | 0,1,0,1,0,0 | `./capture.sh MODE_COOL "0,1,0,1,0,0"` | ❄️ + ventilador |
| MODE_HEAT | 0,1,0,0,1,0 | `./capture.sh MODE_HEAT "0,1,0,0,1,0"` | ☀️ + ventilador |
| MODE_DRY | 0,1,0,0,0,1 | `./capture.sh MODE_DRY "0,1,0,0,0,1"` | 💧 + ventilador |
| MODE_FAN | 0,1,0,0,0,0 | `./capture.sh MODE_FAN "0,1,0,0,0,0"` | Solo ventilador |

Para cada modo:
- [ ] Seleccionar modo en termostato
- [ ] Verificar que el icono correspondiente está activo
- [ ] Capturar 10-15 tramas

### 2.4 Combinaciones Modo + Velocidad

| Estado | Posiciones | Comando |
|--------|------------|---------|
| COOL_LOW | 1,0,0,1,0,0 | `./capture.sh COOL_LOW "1,0,0,1,0,0"` |
| COOL_HIGH | 0,0,1,1,0,0 | `./capture.sh COOL_HIGH "0,0,1,1,0,0"` |
| HEAT_MED | 0,1,0,0,1,0 | `./capture.sh HEAT_MED "0,1,0,0,1,0"` |
| DRY_LOW | 1,0,0,0,0,1 | `./capture.sh DRY_LOW "1,0,0,0,0,1"` |

- [ ] Capturar combinaciones prioritarias

### 2.5 Análisis de Temperatura/Setpoint

Si el termostato permite ajustar temperatura de consigna:

| Estado | Setpoint | Comando |
|--------|----------|---------|
| TEMP_16C | 16°C | `./capture.sh TEMP_16C "0,1,0,1,0,0"` |
| TEMP_20C | 20°C | `./capture.sh TEMP_20C "0,1,0,1,0,0"` |
| TEMP_24C | 24°C | `./capture.sh TEMP_24C "0,1,0,1,0,0"` |
| TEMP_28C | 28°C | `./capture.sh TEMP_28C "0,1,0,1,0,0"` |

- [ ] Capturar con modo COOL + MED fijo, variando solo setpoint
- [ ] Verificar si el display muestra temperatura ambiente o setpoint

### 2.6 Script de Análisis Diferencial

```python
# scripts/analysis/diff_analysis.py
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from curryrtoolslib.utils import trama as trama_tools

def load_first_frame(info_file):
    """Carga la primera trama de un archivo .info/.bin"""
    bin_file = info_file.replace('.info', '.bin')
    resultados = trama_tools.cargar_trama_bytes(bin_file)
    if resultados:
        return list(resultados[0]['data'])
    return None

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

def main():
    dumps_folder = 'dumps/phase2'
    
    # Buscar archivos de estados conocidos
    states = {
        'ALL_OFF': None,
        'FAN_LOW': None,
        'FAN_MED': None,
        'FAN_HIGH': None,
        'MODE_COOL': None,
        'MODE_HEAT': None,
        'MODE_DRY': None,
    }
    
    # Cargar tramas
    for filename in os.listdir(dumps_folder):
        if filename.endswith('.info'):
            for state_name in states.keys():
                if state_name in filename:
                    filepath = os.path.join(dumps_folder, filename)
                    states[state_name] = load_first_frame(filepath)
                    print(f"Cargado {state_name}: {filepath}")
    
    # Comparaciones clave
    if states['ALL_OFF'] and states['FAN_LOW']:
        compare_frames(states['ALL_OFF'], states['FAN_LOW'], "ALL_OFF", "FAN_LOW")
    
    if states['FAN_MED'] and states['MODE_COOL']:
        compare_frames(states['FAN_MED'], states['MODE_COOL'], "FAN_MED", "MODE_COOL")

if __name__ == '__main__':
    main()
```

- [ ] Ejecutar análisis para cada par de estados
- [ ] Crear matriz de correlación control→bytes

### 2.7 Matriz de Correlación

Documentar en `dumps/analysis/correlation_matrix.md`:

```markdown
# Matriz de Correlación Control → Bytes

## FAN Speed (STOP/LOW/MED/HIGH)
- Bytes afectados: [_, _, _]
- Valores observados:
  * STOP: 0x__
  * LOW:  0x__
  * MED:  0x__
  * HIGH: 0x__

## Mode (COOL/HEAT/DRY/FAN)
- Bytes afectados: [_, _, _]
- Valores observados:
  * COOL: 0x__
  * HEAT: 0x__
  * DRY:  0x__
  * FAN:  0x__

## Setpoint (Temperatura)
- Bytes afectados: [_]
- Codificación: Lineal/Tabla/Offset?
- 16°C: 0x__
- 20°C: 0x__
- 24°C: 0x__
- 28°C: 0x__
```

---

## Fase 3: Ingeniería Inversa del Checksum

### 3.1 Identificación de Bytes de Checksum

Candidatos (posiciones que varían "aleatoriamente"):
- Posición -2: _____ (penúltimo byte)
- Posición -1: _____ (último byte)

### 3.2 Prueba de Algoritmos

```python
# scripts/analysis/checksum_crack.py
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from curryrtoolslib.utils import trama as trama_tools

def crc8_ccitt(data, poly=0x07, init=0x00):
    """CRC-8 CCITT"""
    crc = init
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ poly
            else:
                crc <<= 1
        crc &= 0xFF
    return crc

def crc8_rohc(data, poly=0x07):
    """CRC-8 ROHC (init=0xFF)"""
    return crc8_ccitt(data, poly, init=0xFF)

def test_checksum(frame, checksum_pos=-1):
    """Prueba múltiples algoritmos contra la trama"""
    data = frame[:checksum_pos]
    expected = frame[checksum_pos]
    
    results = {}
    
    # XOR simple
    xor_val = 0
    for b in data:
        xor_val ^= b
    results['xor_all'] = xor_val
    results['xor_match'] = xor_val == expected
    
    # Suma
    sum_val = sum(data) & 0xFF
    results['sum_mod256'] = sum_val
    results['sum_match'] = sum_val == expected
    
    # Suma invertida
    sum_inv = (~sum(data)) & 0xFF
    results['sum_inv'] = sum_inv
    results['sum_inv_match'] = sum_inv == expected
    
    # Fletcher-8
    sum1 = sum(data) & 0xFF
    sum2 = sum(sum(data[:i+1]) for i in range(len(data))) & 0xFF
    fletcher = (sum1 ^ sum2)
    results['fletcher8'] = fletcher
    results['fletcher_match'] = fletcher == expected
    
    # CRC-8 con diferentes polinomios
    polys = [0x07, 0x31, 0x9B, 0xD5, 0xA6, 0xE0]
    for poly in polys:
        crc = crc8_ccitt(data, poly)
        results[f'crc8_0x{poly:02X}'] = crc
        results[f'crc8_0x{poly:02X}_match'] = crc == expected
    
    return results, expected

def analyze_frames():
    """Analiza todas las tramas capturadas"""
    dumps_folder = 'dumps/phase2'
    
    for filename in os.listdir(dumps_folder):
        if not filename.endswith('.info'):
            continue
        
        bin_path = os.path.join(dumps_folder, filename.replace('.info', '.bin'))
        resultados = trama_tools.cargar_trama_bytes(bin_path)
        
        if not resultados:
            continue
        
        print(f"\n{'='*60}")
        print(f"Analizando: {filename}")
        print(f"{'='*60}")
        
        # Usar primera trama como referencia
        frame = list(resultados[0]['data'])
        
        results, expected = test_checksum(frame)
        
        print(f"Checksum esperado: 0x{expected:02X}")
        print("\nResultados:")
        for key, val in results.items():
            if key.endswith('_match'):
                status = "✅" if val else "❌"
                algo = key.replace('_match', '')
                print(f"  {status} {algo}: 0x{results[algo]:02X}")

if __name__ == '__main__':
    analyze_frames()
```

- [ ] Probar CRC-8 con polinomios: 0x07, 0x31, 0x9B, 0xD5, 0xA6, 0xE0
- [ ] Probar checksum por bloques (cada bloque entre 0x00 tiene su propio CRC)
- [ ] Probar XOR acumulativo con inicialización != 0

### 3.3 Análisis de Mutación

```python
# scripts/analysis/mutation_analysis.py

def mutate_and_compare(original, position, all_frames):
    """Muta un byte y compara cómo cambia el checksum"""
    print(f"\nMutación en posición {position}:")
    
    # Buscar tramas que difieran solo en esa posición
    candidates = []
    for frame in all_frames:
        diff_count = sum(1 for a, b in zip(original, frame) if a != b)
        if diff_count == 1:  # Difieren en un solo byte
            diff_pos = next(i for i, (a, b) in enumerate(zip(original, frame)) if a != b)
            if diff_pos == position:
                candidates.append((original[position], frame[position], frame[-1]))
    
    if candidates:
        print(f"  Encontradas {len(candidates)} tramas relacionadas")
        for orig_val, new_val, crc in candidates:
            crc_diff = crc ^ original[-1]
            print(f"  0x{orig_val:02X} → 0x{new_val:02X}: CRC diff = 0x{crc_diff:02X}")
            
            # Si crc_diff es lineal con el cambio, probablemente es XOR
            val_diff = orig_val ^ new_val
            if crc_diff == val_diff:
                print(f"    → Patrón XOR detectado!")
            elif crc_diff == (new_val - orig_val) & 0xFF:
                print(f"    → Patrón de suma detectado!")
```

- [ ] Mutar cada byte de datos y observar efecto en checksum
- [ ] Si el cambio es lineal → probablemente XOR o suma
- [ ] Si el cambio es no lineal → CRC polinomial

---

## Fase 4: Validación y Emulación

### 4.1 Construcción de Parser CCN

```python
# scripts/ccn_parser.py

class CCNFrame:
    """Parser de trama CCN"""
    
    # Offset mapping (actualizar tras análisis completo)
    OFFSET_FAN = 3
    OFFSET_MODE = 7
    OFFSET_TEMP = 13
    
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
        self.data = list(data) if isinstance(data, bytes) else data
        self.size = len(self.data)
    
    def parse(self):
        return {
            'size': self.size,
            'fan_speed': self.FAN_VALUES.get(self.data[self.OFFSET_FAN], 'UNKNOWN'),
            'mode': self.MODE_VALUES.get(self.data[self.OFFSET_MODE], 'UNKNOWN'),
            'header_valid': self.data[0:3] == [0x00, 0x00, 0x08],
            'raw_hex': ' '.join(f'{b:02X}' for b in self.data[:16]) + '...',
        }
    
    def __str__(self):
        parsed = self.parse()
        return f"CCN Frame ({parsed['size']}b): {parsed['fan_speed']} / {parsed['mode']}"

# Uso:
# frame = CCNFrame(data)
# print(frame.parse())
```

### 4.2 Generador de Tramas

```python
# scripts/ccn_generator.py

def calculate_crc(data, algorithm='unknown'):
    """Calcula checksum según algoritmo descubierto"""
    if algorithm == 'xor':
        crc = 0
        for b in data:
            crc ^= b
        return crc
    elif algorithm.startswith('crc8'):
        # Implementar según descubrimiento
        pass
    return 0x00  # Placeholder

def generate_frame(fan='MED', mode='COOL', temp=22, size=88):
    """Genera una trama CCN con los parámetros dados"""
    frame = [0] * size
    
    # Header fijo
    frame[0:3] = [0x00, 0x00, 0x08]
    
    # Fan (actualizar valores reales tras análisis)
    fan_map = {'STOP': 0x21, 'LOW': 0x61, 'MED': 0x63, 'HIGH': 0x68}
    frame[3] = fan_map.get(fan, 0x63)
    
    # Mode (actualizar valores reales tras análisis)
    mode_map = {'IDLE': 0x69, 'COOL': 0x28, 'HEAT': 0x68, 'DRY': 0x6B}
    frame[7] = mode_map.get(mode, 0x28)
    
    # Resto de campos (copiar de trama de referencia o calcular)
    # ... completar según análisis
    
    # Calcular y añadir CRC
    frame[-2] = calculate_crc(frame[:-2])
    frame[-1] = 0x08  # Separador final
    
    return bytes(frame)

# Uso:
# frame = generate_frame(fan='MED', mode='COOL', size=88)
```

### 4.3 Prueba de Emulación

```bash
# Usar el comando write de curryrtool
python3 curryrtool.py device write \
    -p /dev/ttyUSB0 \
    -b 2400 \
    -t 0.1 \
    -f dumps/phase2/FAN_MED_<uuid>.bin \
    -r 10 \
    -i 1
```

**Verificación:**
- [ ] Transmitir trama emulada
- [ ] Observar si el NTC reacciona (cambia display, activa relés, etc.)
- [ ] Si el NTC acepta la trama → checksum correcto
- [ ] Si no hay reacción → revisar checksum o estructura

### 4.4 Integración con ML

```bash
# Entrenar modelo con todas las capturas
python3 curryrtool.py trainning entrenar epocas=20000 save

# Probar predicción
python3 curryrtool.py trainning prediccion \
    modelo=models/modelo.keras \
    trama=0,0,8,8,33,33,...
```

- [ ] Actualizar modelo con dataset completo de estados
- [ ] Validar precisión de predicción > 95%
- [ ] Documentar qué bytes son más relevantes para el modelo

---

## 📊 Registro de Progreso

### Registro de Capturas

| Fase | Estado | Fecha | Archivo | Tramas | Tamaño | Notas |
|------|--------|-------|---------|--------|--------|-------|
| 2.1 | ALL_OFF | | | | | |
| 2.2 | FAN_STOP | | | | | |
| 2.2 | FAN_LOW | | | | | |
| 2.2 | FAN_MED | | | | | |
| 2.2 | FAN_HIGH | | | | | |
| 2.3 | MODE_COOL | | | | | |
| 2.3 | MODE_HEAT | | | | | |
| 2.3 | MODE_DRY | | | | | |

### Descubrimientos Clave

```markdown
## Log de Descubrimientos

### 2026-03-XX
- **Hallazgo:** Los bytes 3-5 codifican velocidad del ventilador
- **Evidencia:** FAN_LOW=0x61, FAN_MED=0x63, FAN_HIGH=0x68
- **Archivo:** dumps/phase2/FAN_*.info

### 2026-03-XX
- **Hallazgo:** El checksum es CRC-8 con polinomio 0x__
- **Evidencia:** Verificación en 100 tramas
- **Script:** checksum_crack.py

### 2026-03-XX
- **Hallazgo:** La temperatura se codifica en posición __
- **Evidencia:** Correlación 0x__ = 20°C, 0x__ = 24°C
```

---

## 🔧 Herramientas Rápidas

### Ver Tramas en Tiempo Real

```bash
python3 -c "
import serial
ser = serial.Serial('/dev/ttyUSB0', 2400, timeout=0.1)
while True:
    data = ser.read(88)
    if len(data) >= 85:
        print(' '.join(f'{b:02X}' for b in data[:16]), f'... ({len(data)}b)')
"
```

### Decodificar Última Captura

```bash
python3 -c "
import os, json, glob
files = glob.glob('dumps/*.info')
latest = max(files, key=os.path.getctime)
with open(latest) as f:
    info = json.load(f)
print(f'Archivo: {latest}')
print(f'Valores: {info[\"values\"]}')
print(f'Tramas: {info[\"blocks\"]}')
print(f'Tamaño: {info[\"times\"][0][1]} bytes')
"
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
- [ ] Publicar especificación del protocolo

---

## 📚 Referencias

- `AGENTS.md` - Documentación completa de la arquitectura
- `CCN_PROTOCOL_ANALYSIS.md` - Análisis técnico detallado
- `curryrtoolslib/utils/trama.py` - Código de manejo de tramas
- `curryrtoolslib/interfaces/devices_interface.py` - Captura y emulación

---

*Checklist v2.0 - Actualizado para arquitectura curryrtoolslib (Marzo 2026)*
