# Análisis del Protocolo CCN - Carrier CRC2-NTC

> **Proyecto:** Reverse Engineering del Termostato Carrier CRC2-NTC  
> **Fecha:** Marzo 2026  
> **Arquitectura de Hardware:** 3 hilos (+12V, GND, Datos)

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
| **Longitud de trama** | **88 bytes** | Fija, sin variación |
| **Intervalo entre tramas** | *Pendiente de medición* | ~cientos de ms estimado |

---

## 3. Estructura de la Trama (88 bytes)

### 3.1 Diagrama de la Trama

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

### 3.2 Bytes Fijos (Delimitadores)

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

**Total bytes fijos:** 16 de 88 (18% de overhead de sincronización)

### 3.3 Bytes Variables (Datos Útiles)

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
| 33 | `0x21` | `!` | Medio | Dato variable |
| 40 | `0x28` | `(` | Medio | Dato variable |
| 41 | `0x29` | `)` | Medio | Dato variable |
| 97 | `0x61` | `a` | Alto | Dato variable |
| 99 | `0x63` | `c` | Medio | Dato variable |
| 104 | `0x68` | `h` | Alto | Dato variable |
| 105 | `0x69` | `i` | Alto | Dato variable |
| 107 | `0x6B` | `k` | Medio | Dato variable |

### 4.2 Observaciones sobre Codificación

- **Rango:** 0-107 decimal (nunca > 0x6B)
- **Patrón ASCII:** Los valores imprimibles (`0x21`, `0x61-0x6B`) sugieren:
  - Posible codificación de comandos/modos con caracteres legibles
  - `h`, `i`, `k` pueden ser abreviaturas de funciones (Heat, Indoor, Cool?)
  - `a`, `c` podrían indicar estados (Auto, Cool)

### 4.3 Distribución de Entropía

```
Bytes de baja entropía (fijos):     16 bytes  ████████░░░░░░░░░░
Bytes de media entropía (semi-fijos): ~8 bytes  ████░░░░░░░░░░░░░░
Bytes de alta entropía (datos):     ~64 bytes  ████████████████████████████░░░░
Bytes candidatos a CRC:             ~4 bytes   ██░░░░░░░░░░░░░░░░
```

---

## 5. Campos Funcionales Identificados

### 5.1 Posiciones Candidatas por Función

Basado en análisis diferencial preliminar:

| Offset | Longitud | Función Probable | Observación |
|--------|----------|------------------|-------------|
| 3-5 | 3 bytes | **Velocidad ventilador** | Cambia con FAN1/FAN2/FAN3 |
| 6 | 1 byte | Separador fijo | Siempre `0x08` |
| 7 | 1 byte | **Modo de operación** | `0x21`=STOP, `0x61`=LOW, `0x63`=MED |
| 8 | 1 byte | **Indicador de modo** | `0x69`, `0x28`, `0x68` - correlaciona con cold/hot/dry |
| 9 | 1 byte | Sub-modo/estado | `0x68`, `0x28` variantes |
| 10 | 1 byte | Control bits | `0x09` vs `0x0B` |
| 11-12 | 2 bytes | Estado extendido | Pareja de valores `0x29/0x69/0x6B` |
| 13 | 1 byte | **Temperatura/Setpoint** | `0x21`, `0x28`, `0x61`, `0x63`, `0x68` |

### 5.2 Estructura de Bloques de Datos

```
Bloque A (Bytes 3-14): Configuración principal
├─ Bytes 3-5:  Fan speed encoding
├─ Byte 6:     Separador (0x08)
├─ Bytes 7-9:  Modo + estado activo
├─ Bytes 10-12: Flags de control
└─ Bytes 13-14: Setpoint / Temperatura

Bloque B (Bytes 18-29): Configuración secundaria (repetición/redundancia?)
Bloque C (Bytes 33-44): Estado extendido
Bloque D (Bytes 48-57): Datos de display/indicadores
Bloque E (Bytes 59-71): Datos de sensores
Bloque F (Bytes 72-84): Datos de control
Bloque G (Bytes 85-87): Checksum + terminación
```

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

- **Longitud probable:** 1-2 bytes al final de la trama (posiciones 86-87)
- **Tipo probable:** CRC-8 con polinomio propietario de Carrier
- **Alternativa:** Suma ponderada o checksum por bloques

---

## 7. Comparativa con Otros Protocolos

### 7.1 vs Modbus RTU

| Característica | Modbus RTU | CCN (Carrier) |
|----------------|------------|---------------|
| Silencio entre tramas | 3.5 caracteres | No requerido (delimitadores) |
| Dirección esclavo | Byte 0 | No identificada |
| Código función | Byte 1 | No identificado |
| CRC | 2 bytes (LSB-MSB) | 1-2 bytes (formato desconocido) |
| Longitud | Variable | **Fija: 88 bytes** |

### 7.2 vs BACnet MS/TP

| Característica | BACnet MS/TP | CCN (Carrier) |
|----------------|--------------|---------------|
| Preamble | `0x55 0xFF` | `0x00 0x00 0x08` |
| Frame Type | Byte 2 | No identificado |
| Dirección | Bytes 3-4 | No identificada |
| Longitud máxima | 501 bytes | **88 bytes fijos** |

---

## 8. Hipótesis sobre la Codificación

### 8.1 Modelo de Codificación "Carrier ASCII"

La limitación a valores 0-107 sugiere una codificación de 7-bits con restricciones:

```
Bits válidos: 0xxx xxxx (0-127 range, bit 7 siempre 0)
Subconjunto usado: 0xxx xxxx donde xxx xxxx ∈ {0,8-11,33,40-41,97-99,104-105,107}
```

### 8.2 Posible Estructura de Comandos

Los valores ASCII imprimibles (`!`, `a`, `c`, `h`, `i`, `k`) podrían representar:

| Código | Posible Significado | Contexto HVAC |
|--------|---------------------|---------------|
| `!` (0x21) | Stop / Off | Fan stopped |
| `a` (0x61) | Auto | Modo automático |
| `c` (0x63) | Cool | Modo refrigeración |
| `h` (0x68) | Heat | Modo calefacción |
| `i` (0x69) | Indoor / Idle | Estado interior |
| `k` (0x6B) | ? | Estado especial |

### 8.3 Codificación Numérica

Para valores numéricos (temperaturas, setpoints):
- Posible **offset + escala**: Valor = (byte - offset) × escala
- Ejemplo: Si `0x21` = 16°C, entonces offset = 17 (0x21 - 17 = 0, escala 1°C)

---

## 9. Limitaciones Actuales del Análisis

### 9.1 Datos Insuficientes

1. **Dataset limitado:** Solo 13 tramas capturadas, todas con mismo estado (fan=med, dry=ON)
2. **Sin variación de estados:** No se ha capturado transición entre modos
3. **Sin referencia temporal:** No se ha medido intervalo entre tramas
4. **Sin temperatura variable:** No se han capturado diferentes setpoints

### 9.2 Aspectos No Resueltos

- [ ] Algoritmo de checksum exacto
- [ ] Codificación de temperatura ambiente
- [ ] Codificación de temperatura setpoint
- [ ] Identificación de bits de error/alarmas
- [ ] Formato de dirección de dispositivo (si existe)

---

## 10. Referencias y Recursos

### 10.1 Documentación Carrier

- NTC Controller Manual (CCN reference)
- CRC2 Installation Manual (IOM 126H69)
- Carrier Comfort Network specification (no público)

### 10.2 Recursos del Proyecto

| Archivo | Descripción |
|---------|-------------|
| `USB2RS485.py` | Captura de datos serie |
| `trainning_tools.py` | Entrenamiento ML para predicción de estados |
| `ia_tools.py` | Modelos TensorFlow para clasificación |
| `dumps/*.csv` | Dataset de tramas capturadas |

---

## 11. Conclusión

El protocolo CCN del termostato Carrier CRC2-NTC es un protocolo **propietario, unidireccional y cíclico** con las siguientes características distintivas:

1. **Trama fija de 88 bytes** con delimitadores predecibles
2. **Alfabeto limitado a 12 valores** (0-107, subconjunto ASCII)
3. **Estructura de bloques** separados por bytes `0x00` y `0x08`
4. **Transmisión automática** sin requerir polling del maestro
5. **Codificación posiblemente semántica** usando caracteres ASCII (`a`, `c`, `h`, `i`)

Para completar el análisis y habilitar la emulación del termostato, es necesario realizar **capturas sistemáticas con variación controlada de cada parámetro** (ver `CHECKLIST.md`).

---

*Documento generado para el proyecto TermostatoAC-Carrier*  
*Licencia: Open Source para investigación y desarrollo*
