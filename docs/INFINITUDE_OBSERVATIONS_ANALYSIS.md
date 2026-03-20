# Análisis: Infinity Operating Observations → Aplicación a CCN

> **Fuente:** https://github.com/nebulous/infinitude/wiki/Infinity---Operating-Observations  
> **Autor:** Infinitude (nebulous)  
> **Protocolo:** Carrier Infinity ABCD  
> **Aplicación:** CCN Legacy (tu CRC2-NTC)

---

## 📋 Resumen de Observaciones Clave

La wiki de Infinitude documenta comportamientos observados del bus Infinity. Aunque el protocolo es diferente (ABCD vs CCN), muchos conceptos de **operación del sistema HVAC** son aplicables.

---

## 1. Estructura de Frames y Timing

### Infinitude (Infinity ABCD)
```
Observación: Los frames tienen origen, destino y tipo.
Ejemplo: 2001 -> 4001: READ 000302

Timing: ~10 frames/segundo en bus activo
Latencia: <100ms entre READ y RESPONSE
```

### Aplicación a CCN (tu caso)
```
Tu observación: Tramas unidireccionales (solo broadcast)
Timing: ~5-10 tramas/segundo (2400 baudios vs 38400)
Latencia: N/A (no hay request/response, solo broadcast cíclico)

Lección: Tu protocolo es más simple (maestro único = termostato)
```

**Insight:** CCN es más antiguo y usa broadcast, no tiene el modelo maestro/esclavo complejo de Infinity.

---

## 2. Descubrimiento de Campos (Field Mapping)

### Infinitude - Método de Descubrimiento
```
Técnica usada:
1. Cambiar un parámetro en el termostato
2. Capturar tráfico antes y después
3. Comparar bytes cambiados
4. Correlacionar con valor mostrado

Ejemplo real:
- Cambiar setpoint de 72°F a 74°F
- Buscar qué bytes cambiaron de 0x48 a 0x4A
- Descubrir: Bytes 4-5 de tabla 0003 = setpoint
```

### Aplicación a CCN
```python
# Método idéntico para tu protocolo
# En tu CHECKLIST.md Fase 2:

# 1. Capturar FAN_STOP (0,0,0,0,0,0)
# 2. Capturar FAN_LOW (1,0,0,0,0,0)  
# 3. Comparar con diff_analysis.py
# 4. Resultado: Bytes 3-5 cambian

# Tu descubrimiento:
# FAN_STOP: bytes = [0x21, 0x21, 0x08]
# FAN_LOW:  bytes = [0x61, 0x63, 0x08]
# FAN_MED:  bytes = [0x63, ...]
# FAN_HIGH: bytes = [0x68, ...]
```

**Validación:** Tu metodología es **idéntica** a la que usaron en Infinitude. ✅

---

## 3. Estructura de Tablas vs Bloques Delimitados

### Infinitude (ABCD)
```
Las tablas tienen estructura fija:
- Tabla 0001: Info del sistema
- Tabla 0003: Configuración de zona
- Tabla 0005: Histórico
- Cada tabla tiene offsets específicos

Ejemplo de estructura de tabla:
0003 02 0411  <- Offset 02 = temperatura actual
     ^^ ^^^^
     offset valor (0x0411 = 1041 = 74.1°F aprox)
```

### CCN Legacy (tu caso)
```
Estructura diferente: Bloques delimitados

00 00 08 [BLOQUE A] 00 [BLOQUE B] 00 00 08 [BLOQUE C] ...
^^^^^^   ^^^^^^^^^   ^  ^^^^^^^^^
STX      Datos       Sep Datos

Los bloques NO son tablas con offsets,
son estructuras de longitud variable
```

**Insight:**
- **Infinity:** Bases de datos con offsets (como registros Modbus)
- **CCN:** Stream de datos con delimitadores (más parecido a un protocolo de transporte)

---

## 4. Codificación de Temperaturas

### Infinitude (ABCD)
```
Observación: Las temperaturas usan codificación específica
- Temperatura real = Valor / 10 (o similar)
- Ejemplo: 0x0411 = 1041 → 74.1°F
- También hay valores en Celsius internamente
```

### Aplicación a CCN
```
Hipótesis para tu protocolo:

Los valores como 0x21 (33), 0x61 (97), 0x68 (104)
podrían ser:
- Offset de temperatura (ej: 0x21 = 33 → 16°C base)
- Escalas: (valor - 17) = °C ?

Prueba propuesta:
1. Poner termostato a 16°C, capturar → valor X
2. Poner a 20°C, capturar → valor Y  
3. Poner a 24°C, capturar → valor Z
4. Ver correlación lineal: Y = X + 4?
```

---

## 5. Estados del Sistema (System States)

### Infinitude - Estados Observados
```
El sistema tiene máquina de estados:
- IDLE: Sistema inactivo
- COOLING: Enfriando activo
- HEATING: Calentando activo
- FAN_ONLY: Solo ventilador
- DEFROST: Descongelación

Cada estado se refleja en bits específicos de las tablas
```

### Aplicación a CCN
```python
# Tu protocolo tiene estados similares codificados en bytes:

ESTADOS_FAN = {
    0x21: 'STOP',    # !
    0x61: 'LOW',     # a
    0x63: 'MED',     # c  
    0x68: 'HIGH',    # h
}

ESTADOS_MODO = {
    0x69: 'IDLE',    # i
    0x28: 'COOL',    # (
    0x68: 'HEAT',    # h
    0x6B: 'DRY',     # k
}

# Posiblemente combinados:
# Byte 7-8 podrían ser máquina de estados compleja
```

---

## 6. Broadcast vs Request/Response

### Infinitude (ABCD)
```
Observación: El bus usa principalmente request/response
- SAM (System Access Module) solicita datos
- Termostato responde
- Aire acondicionado responde
- Estructura: Origen → Destino: TIPO Datos
```

### CCN (tu caso)
```
Observación clave de tu dump:
- Solo hay broadcast desde termostato
- No hay direccionamiento origen/destino
- No hay respuestas
- Es monodireccional

Esto indica:
- CCN es más primitivo que ABCD
- No hay coordinación maestro/esclavo
- El termostato "grita" su estado periódicamente
- El receptor (fancoil) escucha y actúa
```

**Implicación:** Tu protocolo es **más simple** de emular porque no necesitas manejar conversaciones bidireccionales.

---

## 7. Checksum/CRC

### Infinitude (ABCD)
```
El protocolo ABCD incluye checksum en cada frame.
Tipo de CRC: Posiblemente CRC-16 o similar.
Ubicación: Al final del frame.

Nota: No documentan el algoritmo exacto públicamente
```

### Aplicación a CCN
```
Tu protocolo también tiene checksum (pendiente de identificar)

Posiciones candidatas:
- Últimos 1-2 bytes de la trama (86-87 en trama de 88)
- Tipo: Desconocido (no es XOR simple ni suma)

Método de Infinitude para crackearlo:
1. Mutar 1 bit en datos conocidos
2. Observar cambio en checksum
3. Si lineal → suma/XOR
4. Si no lineal → CRC polinomial
```

**Script recomendado** (basado en método Infinitude):
```python
# mutation_analysis.py
def analyze_checksum_behavior(frames):
    """
    Método de Infinitude adaptado:
    Buscar tramas que difieran en 1 bit
    y comparar checksum resultante
    """
    for i, frame1 in enumerate(frames):
        for frame2 in frames[i+1:]:
            diff_bytes = [j for j, (a,b) in enumerate(zip(frame1, frame2)) if a != b]
            if len(diff_bytes) == 1:
                pos = diff_bytes[0]
                crc1, crc2 = frame1[-1], frame2[-1]
                print(f"Mutación byte {pos}: CRC 0x{crc1:02X} → 0x{crc2:02X}")
                print(f"  Diferencia: 0x{(crc1 ^ crc2):02X}")
```

---

## 8. Polling y Prioridades

### Infinitude (ABCD)
```
Observación: El SAM hace polling periódico a todos los dispositivos.
Frecuencia: ~1 segundo para cada dispositivo principal.
Prioridad: Termostato > Unidad exterior > Unidad interior
```

### Aplicación a CCN
```
Tu protocolo NO tiene polling:
- El termostato transmite cíclicamente sin ser solicitado
- Periodo: Estimado 500-2000ms (pendiente de medir)
- No hay concepto de prioridad (solo 1 emisor)

Vantaja para emulación:
- No necesitas responder a solicitudes
- Solo replicar el patrón de broadcast
```

---

## 9. Comandos de Control

### Infinitude (ABCD)
```
Para cambiar temperatura:
1. SAM envía WRITE a tabla específica
2. Termostato actualiza
3. Termostato confirma
4. Sistema reacciona

Ejemplo de secuencia compleja
```

### Aplicación a CCN
```
Tu protocolo NO permite escritura directa:
- El termostato no recibe comandos
- Es output-only (broadcast)
- Para "controlar" el sistema, debes:
  a) Emular el termostato completo, O
  b) Interceptar entre termostato y fancoil

Estrategia de emulación (de Infinitude):
Modo "Man in the Middle":
- Leer trama real del termostato
- Modificar bytes específicos (temperatura, modo)
- Reenviar trama modificada al fancoil
```

---

## 📊 Matriz de Aplicabilidad

| Concepto Infinitude | Aplicable a CCN | Complejidad | Estado |
|--------------------|-----------------|-------------|--------|
| **Análisis diferencial** | ✅ Sí | Media | Implementado en CHECKLIST.md |
| **Field mapping** | ✅ Sí | Media | Parcial (fan identificado) |
| **Codificación temp** | ⚠️ Hipótesis | Alta | Pendiente |
| **Máquina de estados** | ✅ Sí | Baja | Parcial |
| **Request/response** | ❌ No aplica | - | N/A (broadcast only) |
| **Tablas con offsets** | ❌ No | - | Estructura diferente |
| **Cracking CRC** | ✅ Sí | Alta | Pendiente |
| **Polling** | ❌ No aplica | - | N/A (cíclico) |
| **MITM para control** | ✅ Sí | Alta | Posible |

---

## 🎯 Conclusiones Clave

### 1. Tu Protocolo es Más Simple
```
CCN vs ABCD:
+ No hay polling complejo
+ No hay direccionamiento
+ No hay múltiples maestros
+ Broadcast unidireccional

- Menos documentado
- Menos proyectos de referencia
- Checksum desconocido
```

### 2. Metodología Válida
La técnica de Infinitude (**análisis diferencial por cambio de estado**) es **aplicable 100%** a tu caso.

### 3. Diferencias Estructurales Importantes
```
Infinitude (ABCD):          Tu CCN:
├── Tablas con offsets      ├── Bloques delimitados
├── Request/Response        ├── Broadcast cíclico
├── Múltiples dispositivos  ├── Single emitter
├── Complejo                ├── Simple
└── CRC conocido            └── CRC desconocido
```

### 4. Estrategia Adaptada
Basado en Infinitude, tu estrategia debería ser:

```
1. CAPTURA SISTEMÁTICA (Fase 2 del CHECKLIST)
   └── Crear matriz de estados FAN × MODE
   
2. ANÁLISIS DIFERENCIAL (Método Infinitude)
   └── diff_analysis.py → identificar bytes por función
   
3. CRACKING CRC (Adaptar método Infinitude)
   └── mutation_analysis.py → identificar algoritmo
   
4. EMULACIÓN (Concepto de Infinitude)
   └── Modo repetidor con modificación MITM
   
5. API/INTEGRACIÓN (Inspirado en Infinitude)
   └── Flask API similar para Home Assistant
```

---

## 🔗 Referencias Cruzadas

| Documento | Sección Relevante |
|-----------|-------------------|
| `CHECKLIST.md` | Fase 2: Análisis diferencial |
| `CCN_PROTOCOL_ANALYSIS.md` | Sección 6: Checksum |
| `AGENTS.md` | Módulos: devices_interface.py |
| Infinitude Wiki | Operating Observations (original) |

---

## 💡 Recomendación Final

**Léete completo** la wiki de Infinitude Operating Observations, pero ten en cuenta:

> "El protocolo CCN es una versión anterior y más simple del ABCD. 
> Lo que funciona para ABCD en términos de metodología, 
> funciona para CCN, pero las estructuras de datos son diferentes."

Tu ventaja: CCN es **más fácil de emular** porque es unidireccional.
Tu desventaja: Hay **menos documentación** disponible.

---

*Análisis generado para adaptar metodología Infinitude a CCN Legacy*
