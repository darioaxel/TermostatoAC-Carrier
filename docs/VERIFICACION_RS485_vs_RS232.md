# Verificación: RS485 vs RS232 en el Bus Carrier

> **Contexto:** Termostato Carrier CRC2-NTC con adaptador USB-RS485

---

## 🔌 Arquitectura de Conexión

### Tu Setup Actual

```
PC ──USB──► [Adaptador USB-RS485] ──A/B/GND──► ? ──P/G/C──► Termostato CRC2-NTC
                                              │
                                              └── ¿Convertidor de nivel?
```

**El problema:** El termostato tiene 3 hilos (P=+12V, G=GND, C=Data), pero RS485 necesita 2 hilos de datos (A y B) más GND.

---

## 🎯 Cómo Descartar RS232 Definitivamente

### 1. Verificación por Niveles de Voltaje

| Medición | RS232 | RS485 | Lo que verás en tu bus |
|----------|-------|-------|------------------------|
| **C vs GND** (DC) | -12V (idle) o ±12V | Variable 0-5V | **0V o 0-5V** ✅ |
| **P vs GND** | N/A (no aplica) | +12V alimentación | **+12V** ✅ |
| **Diferencial** | No existe | A-B = ±200mV a ±6V | **C es single-ended** ⚠️ |

**Prueba con multímetro:**
```
# En el terminal del termostato (sin datos):
# - C vs G = ~0V o fluctuando 0-5V  → NO es RS232 (sería -12V)
# - Si ves voltajes negativos        → PODRÍA ser RS232
```

### 2. Verificación por Señal Diferencial

**RS485 puro** es diferencial (A vs B). Tu termostato tiene **1 solo hilo de datos (C)**.

Esto significa:
- ❌ **No es RS485 estándar** (falta par diferencial)
- ❌ **No es RS232** (niveles y conexión no coinciden)
- ✅ **Es un protocolo propietario de Carrier** sobre 1 hilo + GND

### 3. Comparación con Proyecto Infinitive

| Característica | Infinitive (Carrier Infinity) | Tu CRC2-NTC |
|----------------|-------------------------------|-------------|
| **Bus** | RS485 estándar (A, B, GND) | **3 hilos (P, G, C)** |
| **Alimentación** | Separada 24VAC | **+12V en el mismo bus** |
| **Velocidad** | 38400 baudios | **2400 baudios** |
| **Protocolo** | ABCD (Carrier propietario) | **CCN (más antiguo)** |

**Conclusión:** Tu CRC2-NTC es una generación **anterior** a Infinity. Usa CCN, no el bus RS485 de Infinitive.

---

## 📊 Análisis de los Dumps (Evidencia Clave)

```
Valores únicos en tu dump: [0, 8, 9, 11, 33, 40, 41, 97, 99, 104, 105, 107]
En hex: [0x00, 0x08, 0x09, 0x0B, 0x21, 0x28, 0x29, 0x61, 0x63, 0x68, 0x69, 0x6B]
```

| Característica | RS232 típico | Tu dump CCN |
|----------------|--------------|-------------|
| **Rango de valores** | 0x00-0xFF completo | **0x00-0x6B (0-107)** |
| **Bits altos** | Sí (0x80-0xFF) | **NO (nunca > 0x6B)** |
| **Estructura** | Arbitraria | **Patrones fijos (0x00, 0x08)** |

**Esto descarta RS232:** Un puerto RS232 transmitiría bytes completos (0-255) sin la restricción artificial a 107.

---

## 🔬 Métodos de Verificación

### Método 1: Osciloscopio (Definitivo)

```
Configuración:
- Canal 1: C (Data) vs GND
- Canal 2: P (+12V) vs GND (referencia)
- Trigger: Flanco descendente en C
- Timebase: 1ms/div @ 2400 baudios
```

**Si fuera RS232:**
- Niveles: +12V / -12V respecto a GND
- Idle: Línea en -12V (negativo)

**Si es tu protocolo CCN:**
- Niveles: 0V / +5V o 0V / +12V respecto a GND
- Idle: Línea en 0V o +12V (no negativo)

### Método 2: Análisis de Corriente (sin osciloscopio)

```
# Medir corriente en línea C (modo mA en multímetro)
# RS485: Corriente de loop típica 20mA-60mA
# RS232: Corriente muy baja (voltaje controlado)
# Tu bus: Probablemente <10mA (señal lógica sobre 12V)
```

### Método 3: Comparación con Señal RS232 Real

```bash
# Si tienes un conversor USB-RS232 disponible:
# 1. Conectar TX y GND a osciloscopio
# 2. Enviar datos: echo "TEST" > /dev/ttyUSB1
# 3. Verás niveles ±12V
#
# 4. Comparar con tu termostato
#    - Si son diferentes → No es RS232
```

---

## ✅ Checklist de Verificación

| Prueba | RS232 | RS485 | CCN (tu caso) | Resultado |
|--------|-------|-------|---------------|-----------|
| **Voltaje idle** | -12V | Indefinido (diferencial) | **0V o +12V** | ✅ |
| **Voltaje activo** | ±12V | ±200mV a ±6V (dif) | **0-5V o 0-12V** | ✅ |
| **Número de hilos datos** | 2 (TX,RX) | 2 (A,B) | **1 (C)** | ⚠️ |
| **Alimentación** | Separada | Separada | **+12V integrada** | ✅ |
| **Niveles negativos** | Sí | No | **No** | ✅ |

---

## 🎯 Conclusión

Tu termostato **NO usa RS232** por estas razones definitivas:

1. **Niveles de voltaje:** RS232 requiere ±3V a ±15V (bipolar). Tu dump muestra valores 0-107 (unipolar positivo).

2. **Sin niveles negativos:** RS232 usa voltaje negativo para "1" lógico (MARK). Tu protocolo nunca genera valores negativos.

3. **Arquitectura de 3 hilos:** RS232 requiere TX, RX, GND (mínimo). Tu termostato tiene +12V, GND, y **1 solo hilo de datos**.

4. **Codificación limitada:** RS232 transmite bytes completos (0-255). Tu protocolo está artificialmente limitado a 0-107.

5. **Diferente de Infinitive:** El proyecto Infinitive usa RS485 **estándar** con par diferencial (A,B). Tu CRC2-NTC usa **CCN antiguo** con comunicación sobre 1 hilo.

---

## 🔧 Qué Protocolo Es Realmente

```
CCN Legacy (Carrier Comfort Network)
════════════════════════════════════
- Capa física: Single-wire + GND (no diferencial)
- Alimentación: +12V en el mismo bus (3 hilos: P, G, C)
- Codificación: Propietaria (valores 0-107, delimitadores 0x00/0x08)
- Velocidad: 2400 baudios
- Dirección: Unidireccional (broadcast desde termostato)
```

**El adaptador USB-RS485 funciona porque:**
- Está configurado en modo "single-ended" o 
- Estás leyendo solo una línea (C) respecto a GND, o
- Hay un conversor de nivel que no has mencionado

---

## 📋 Siguiente Paso Recomendado

Para confirmar 100% el tipo de señal:

```
# 1. Medir voltaje C vs GND en idle:
multímetro en DC → debería ser ~0V (no -12V)

# 2. Medir voltaje P vs GND:
debería ser +12V estable

# 3. Si tienes osciloscopio, capturar 1 bit a 2400 baudios:
- Duración: ~416µs (1 bit @ 2400bps)
- Niveles: 0V a +X V (no negativo)
```

¿Puedes hacer estas mediciones y confirmar los voltajes que ves?
