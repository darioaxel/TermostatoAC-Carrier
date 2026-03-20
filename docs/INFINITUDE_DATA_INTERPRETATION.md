# Análisis: Infinity Data Interpretation → Aplicación a CCN

> **Fuente:** https://github.com/nebulous/infinitude/wiki/Infinity---interpreting-data  
> **Autor:** Infinitude (nebulous)  
> **Tema:** Decodificación de valores en protocolo ABCD  
> **Aplicación:** CCN Legacy (tu CRC2-NTC)

---

## 📋 Introducción

Esta wiki de Infinitude explica **cómo interpretar los valores** dentro de los frames ABCD. Aunque el formato de frames es diferente al CCN, las **técnicas de decodificación** son aplicables.

---

## 1. Tipos de Datos en ABCD vs CCN

### 1.1 Enteros de 8 bits (Byte)

**Infinitude (ABCD):**
```
Formato: Byte directo (0x00 - 0xFF)
Ejemplo: 0x42 = 66 (decimal)
Uso típico: Estados binarios, flags, modos pequeños
```

**Tu CCN:**
```
Formato: Byte limitado (0x00 - 0x6B, solo 12 valores)
Ejemplo: 0x21 = 33 = '!' (ASCII) = FAN_STOP
         0x61 = 97 = 'a' (ASCII) = FAN_LOW

Uso: Codificación ASCII semántica (letras con significado)
```

**Insight:** Tu CCN usa un subconjunto intencional de bytes, posiblemente para:
- **Legibilidad:** Las letras a, c, h, i tienen significado mnemónico
- **Validación:** Limitar valores válidos detecta errores
- **Compatibilidad:** Evitar caracteres de control problemáticos

---

### 1.2 Enteros de 16 bits (Word)

**Infinitude (ABCD):**
```
Formato: Big-endian (MSB primero)
Ejemplo: 0x04 0x11 = 0x0411 = 1041 decimal
Uso típico: Temperaturas (×10 para 1 decimal)
         1041 = 74.1°F
```

**Tu CCN - Hipótesis:**
```
Posible formato: Pares de bytes para temperatura
Ejemplo candidato: 0x21 0x08 = ?

Hipótesis de decodificación:
- Opción A: Temperatura = (byte - 17) °C
  0x21 (33) - 17 = 16°C
  0x61 (97) - 17 = 80°C (¿demasiado alto?)
  
- Opción B: Escala diferente
  Valor bajo (0x21, 0x28, 0x29) = Temperaturas menores
  Valor alto (0x61, 0x63, 0x68, 0x69, 0x6B) = Temperaturas mayores
  
- Opción C: No es temperatura directa
  Podría ser índice a tabla de temperaturas
```

**Prueba propuesta:**
```python
# Capturar con diferentes setpoints:
# setpoint 16°C → valor X
# setpoint 20°C → valor Y
# setpoint 24°C → valor Z

# Si X, Y, Z están en posiciones conocidas:
# Y - X debería ser proporcional a 4°C de diferencia
```

---

### 1.3 Temperaturas con Decimal

**Infinitude (ABCD):**
```
Fórmula documentada:
  Valor_real = Valor_raw / 10
  
Ejemplo real:
  0x0411 = 1041 → 104.1°F (pero Infinitude dice 74.1°F)
  
Corrección: Parece haber un offset
  Temp_F = (Valor_raw × factor) + offset
  
Para °C a veces usan:
  Temp_C = (Valor_raw - 320) / 18  (aproximado)
```

**Tu CCN - Análisis:**
```
Los valores 0x21-0x6B no tienen suficiente rango para:
- Temperaturas típicas HVAC (-10°C a 50°C) × 10 = -100 a 500

Por tanto, en CCN probablemente:
1. La temperatura NO está en los valores ASCII (0x21, 0x61, etc.)
2. Podría estar en bytes que no hemos identificado aún
3. O usar codificación diferente (índices, no valores absolutos)
```

---

## 2. Flags y Bits de Estado

### 2.1 Codificación de Flags (ABCD)

**Infinitude:**
```
Los flags se codifican como bits dentro de bytes:

Byte de estado:
  Bit 7: Compresor activo
  Bit 6: Ventilador activo  
  Bit 5: Calefacción activa
  Bit 4-0: Reservados

Ejemplo: 0xC0 = 11000000b
         Bit 7=1 (compresor ON)
         Bit 6=1 (ventilador ON)
```

**Tu CCN - Análisis de posibles flags:**
```
Valores observados que podrían ser flags:
0x09 (00001001b) vs 0x0B (00001011b)
Diferencia: Bit 1

0x28 (00101000b) vs 0x68 (01101000b)
Diferencia: Bit 6 (0x40)

Posible interpretación:
- 0x09: Flag X activo, flag Y inactivo
- 0x0B: Flag X activo, flag Y activo
- 0x28: Modo base (¿COOL?)
- 0x68: Modo + flag adicional (¿HEAT? mismo bit que en ASCII 'h')
```

---

### 2.2 Estados Enumerados

**Infinitude (ABCD):**
```
Modos de operación codificados como enum:
0x00 = OFF
0x01 = AUTO
0x02 = COOL
0x03 = HEAT
0x04 = FAN_ONLY
0x05 = EMERGENCY_HEAT
```

**Tu CCN (Observado):**
```
Valores candidatos para modos:
0x28 (40) = '(' → ¿COOL?
0x68 (104) = 'h' → ¿HEAT? ('h' de heat)
0x69 (105) = 'i' → ¿IDLE? ('i' de idle/inactive)
0x6B (107) = 'k' → ¿DRY? (¿de 'kool'?)
0x21 (33) = '!' → ¿STOP/EMERGENCY?

Esta codificación mnemónica es coherente con el uso de ASCII
para hacer el protocolo más legible en debugging.
```

---

## 3. Timestamps y Secuencias

### 3.1 Contadores de Secuencia

**Infinitude (ABCD):**
```
Algunos frames incluyen contadores que incrementan:
- Contador de mensajes
- Timestamp relativo
- Secuencia de comunicación

Útil para:
- Detectar pérdida de mensajes
- Ordenar eventos
- Sincronización
```

**Tu CCN - ¿Existe secuencia?**
```
Observación de tu dump:
Las 13 tramas son muy similares, no hay contador obvio.

Posibles ubicaciones:
- Bytes 8-9 varían: 0x69/0x68, 0x28/0x68
  Podría ser timestamp cifrado o estado dinámico
  
- No hay byte que incremente monotónicamente
  El protocolo CCN podría NO tener secuencia explícita
  (se confía en el orden de recepción)
```

---

## 4. Técnicas de Decodificación de Infinitude

### 4.1 Método de Correlación

**Proceso usado en Infinitude:**
```
1. Leer valor mostrado en pantalla del termostato
   (ej: "Target temp: 74°F")

2. Buscar ese valor (o múltiplo/fracción) en el frame
   - 74 × 1 = 0x4A (74) → No está
   - 74 × 10 = 740 = 0x02E4 → Buscar
   - 74.1°F → 741 = 0x02E5 → ¡Encontrado!

3. Verificar cambiando el valor y observando el mismo offset

4. Documentar: Offset X = Temperatura × 10
```

**Adaptación a CCN:**
```python
# Método análogo para tu protocolo:

# 1. Mostrar valor en termostato
#    (ej: "Ventilador: MEDIO")

# 2. Buscar correlación en bytes
#    FAN_STOP → byte = 0x21
#    FAN_LOW  → byte = 0x61
#    FAN_MED  → byte = 0x63
#    FAN_HIGH → byte = 0x68

# 3. Patrón observado:
#    Los valores NO son secuenciales (0x21, 0x61, 0x63, 0x68)
#    Esto sugiere codificación NO lineal (índices a tabla)

# 4. Documentar:
#    Byte 3 (o posición X) = Índice a tabla de velocidades
#    Tabla: {0x21: STOP, 0x61: LOW, 0x63: MED, 0x68: HIGH}
```

---

### 4.2 Método de Diferencias

**Infinitude:**
```
Comparar frames consecutivos:
Frame N:   ... 0x48 ...
Frame N+1: ... 0x49 ...
           
Diferencia: +1 en ese byte
Contexto: El usuario subió temperatura 0.1°F
Conclusión: Ese byte es temperatura × 10
```

**Tu CCN:**
```python
# Análisis de tu dump:
# Las 13 tramas varían en múltiples posiciones
# No hay un byte que incremente monotónicamente

# Esto indica:
# - CCN no tiene contador de secuencia
# - O el contador está cifrado/encodeado
# - O no es relevante (broadcast cíclico simple)

# Lo que SÍ varía sistemáticamente:
# Bytes 3-5: Fan (conocido)
# Bytes 8-9: Posible estado dinámico
# Bytes finales: Checksum (cambia siempre)
```

---

## 5. Decodificación Específica por Tipo

### 5.1 Temperaturas

**Fórmulas típicas en HVAC (de Infinitude):**
```
# Fahrenheit
Temp_F = (raw × 9/10) + 32      # Variante 1
Temp_F = raw / 10               # Variante 2
Temp_F = (raw - 320) / 18       # °C→F conversion

# Celsius
Temp_C = (raw - offset) / scale
```

**Hipótesis para CCN:**
```
Los valores 0x21-0x6B podrían ser:
- Setpoints discretos (16°C, 18°C, 20°C...) en lugar de continuo
- Índices a tabla de temperaturas predefinidas
- Códigos de modo que incluyen temperatura implícita

Ejemplo:
0x21 = Modo X + 16°C
0x61 = Modo X + 20°C
0x68 = Modo X + 24°C
```

**Prueba crítica:**
```python
# Necesitas capturar con setpoint VARIABLE
# Mismo modo, misma velocidad fan, diferente temperatura

# Si bytes cambian → Has encontrado temperatura
# Si bytes iguales → Temperatura no se transmite (¿calculada localmente?)
```

---

### 5.2 Presiones y Sensores

**Infinitude (ABCD):**
```
Presiones, corrientes, etc. usan escalas específicas:
Presión_Suc = raw × factor + offset
Amperaje = raw / 10

Factores empíricos determinados por correlación
```

**Tu CCN:**
```
El CRC2-NTC es un termostato simple, probablemente NO transmite:
- Presiones de refrigerante
- Corrientes eléctricas
- Velocidades de compresor

Sí transmite (observado):
- Estado de controles (fan, modo)
- Posiblemente temperatura ambiente
- Posiblemente setpoint

No transmite (especulación):
- Datos de presión (el fancoil no los usa)
- Alarmas técnicas detalladas
```

---

## 6. Estrategia de Decodificación Adaptada

### Fase 1: Mapeo de Estados Conocidos (Prioridad ALTA)

```python
# Basado en Infinitude, adaptado a CCN:

ESTADO_MAPEADO = {
    # FAN: mapeo parcialmente conocido
    'FAN': {
        0x21: 'STOP',   # '!' 
        0x61: 'LOW',    # 'a'
        0x63: 'MED',    # 'c'
        0x68: 'HIGH',   # 'h'
    },
    
    # MODE: hipótesis basada en letras ASCII
    'MODE': {
        0x28: 'COOL',   # '(' →¿codificación Carrier?
        0x68: 'HEAT',   # 'h' → 'heat'
        0x69: 'IDLE',   # 'i' → 'idle'
        0x6B: 'DRY',    # 'k' →¿variante de 'cool'?
    },
}

# Técnica de Infinitude: Verificar cambiando estado
# y observando qué byte cambia consistentemente
```

---

### Fase 2: Decodificación de Temperatura (Prioridad MEDIA)

```python
# Método de correlación (de Infinitude):

def decode_temperature(tramas_con_diferentes_setpoints):
    """
    1. Capturar con setpoint 16°C, 20°C, 24°C
    2. Buscar byte(s) que cambien proporcionalmente
    3. Calcular: Δbyte / Δtemp = factor
    4. Verificar: factor debe ser consistente
    """
    
    # Ejemplo de resultado esperado:
    # 16°C → byte = X
    # 20°C → byte = X + 4×factor
    # 24°C → byte = X + 8×factor
    
    # Si factor = 1: Codificación directa (°C + offset)
    # Si factor = 0.5: Codificación ×2
    # Si factor variable: Codificación no lineal (índice)
```

---

### Fase 3: Identificación de Flags (Prioridad BAJA)

```python
# Análisis de bits (técnica Infinitude):

def analyze_flags(tramas):
    """
    Buscar bits que cambian independientemente
    Ejemplo:
    - 0x09 (00001001) vs 0x0B (00001011)
      Bit 1 cambia: posible flag binario
    
    - 0x28 (00101000) vs 0x68 (01101000)
      Bit 6 cambia: posible cambio de modo
    """
```

---

## 7. Herramientas Recomendadas

### 7.1 Basadas en Infinitude

```python
# data_decoder.py - Adaptación de técnicas Infinitude

class CCNDecoder:
    """Decodificador de valores CCN basado en métodos Infinitude"""
    
    # Tablas de decodificación (poblar tras análisis)
    FAN_TABLE = {
        0x21: 'STOP',
        0x61: 'LOW',
        0x63: 'MED',
        0x68: 'HIGH',
    }
    
    MODE_TABLE = {
        0x28: 'COOL',
        0x68: 'HEAT',
        0x69: 'IDLE',
        0x6B: 'DRY',
    }
    
    def decode_frame(self, frame):
        """Decodifica una trama completa"""
        return {
            'fan': self.FAN_TABLE.get(frame[3], 'UNKNOWN'),
            'mode': self.MODE_TABLE.get(frame[7], 'UNKNOWN'),
            'temp_setpoint': self._decode_temp(frame),  # Pendiente
            'raw': frame,
        }
    
    def _decode_temp(self, frame):
        """Decodificación de temperatura (pendiente de análisis)"""
        # Implementar tras capturas con setpoint variable
        return None
```

---

## 8. Comparativa Final: ABCD vs CCN

| Característica | ABCD (Infinitude) | CCN (Tu protocolo) | Estrategia Adaptada |
|----------------|-------------------|-------------------|---------------------|
| **Números** | Directos (big-endian) | ASCII mnemónico | Tablas de lookup |
| **Temperaturas** | Raw × factor | ¿Índice a tabla? | Correlación empírica |
| **Flags** | Bits en bytes | Posible bits en bytes | Análisis AND/XOR |
| **Secuencia** | Contadores explícitos | No evidente | Ignorar o buscar cifrado |
| **Estados** | Enums (0x00-0x05) | ASCII ('a', 'h', 'i') | Tablas de caracteres |
| **Complejidad** | Alta (tablas, offsets) | Media (bloques simples) | Más fácil de mapear |

---

## 9. Conclusiones y Próximos Pasos

### 9.1 Qué Aprender de Infinitude

1. **Técnica de correlación:** Mostrar valor → Buscar en frame → Verificar
2. **Método de diferencias:** Comparar consecutivos para detectar contadores
3. **Análisis de bits:** Flags = bits que cambian independientemente
4. **Tablas de decodificación:** Mapeo explícito byte→significado

### 9.2 Diferencias a Tener en Cuenta

1. **CCN NO usa:** Enteros de 16 bits big-endian para temperatura
2. **CCN usa:** Codificación ASCII mnemónica para estados
3. **CCN NO tiene:** Contadores de secuencia evidentes
4. **CCN tiene:** Estructura de bloques más simple que tablas ABCD

### 9.3 Plan de Acción Inmediato

```bash
# 1. Completar mapeo de FAN (ya parcial)
python3 CHECKLIST.md/Fase2/capture.sh FAN_STOP "0,0,0,0,0,0"
python3 CHECKLIST.md/Fase2/capture.sh FAN_LOW "1,0,0,0,0,0"
python3 CHECKLIST.md/Fase2/capture.sh FAN_MED "0,1,0,0,0,0"
python3 CHECKLIST.md/Fase2/capture.sh FAN_HIGH "0,0,1,0,0,0"

# 2. Mapeo de MODE con FAN constante (MED)
python3 CHECKLIST.md/Fase2/capture.sh MODE_COOL "0,1,0,1,0,0"
python3 CHECKLIST.md/Fase2/capture.sh MODE_HEAT "0,1,0,0,1,0"
python3 CHECKLIST.md/Fase2/capture.sh MODE_DRY "0,1,0,0,0,1"

# 3. Búsqueda de temperatura
python3 CHECKLIST.md/Fase2/capture.sh TEMP_16 "0,1,0,1,0,0"  # Set 16°C
python3 CHECKLIST.md/Fase2/capture.sh TEMP_20 "0,1,0,1,0,0"  # Set 20°C
python3 CHECKLIST.md/Fase2/capture.sh TEMP_24 "0,1,0,1,0,0"  # Set 24°C

# 4. Análisis con diff_analysis.py
python3 scripts/analysis/diff_analysis.py
```

### 9.4 Recursos Cruzados

| Documento Infinitude | Adaptación CCN | Ubicación en tu proyecto |
|---------------------|----------------|--------------------------|
| Interpreting Data | Este documento | `docs/INFINITUDE_DATA_INTERPRETATION.md` |
| Operating Observations | Arquitectura del bus | `docs/INFINITUDE_OBSERVATIONS_ANALYSIS.md` |
| Frame Structure | CCN Protocol Analysis | `CCN_PROTOCOL_ANALYSIS.md` Sección 3 |

---

*Análisis de decodificación adaptado de Infinitude a CCN Legacy*
