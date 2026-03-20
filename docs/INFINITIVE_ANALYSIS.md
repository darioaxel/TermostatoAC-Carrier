# Análisis: Qué Aprender del Proyecto Infinitive

> **Repositorio:** https://github.com/acd/infinitive  
> **Protocolo:** Carrier Infinity ABCD bus  
> **Comparación:** Infinitive vs Tu CRC2-NTC (CCN)

---

## 🔍 Resumen de Diferencias Clave

| Característica | Infinitive (Infinity) | Tu CRC2-NTC (CCN) | ¿Aplicable? |
|----------------|----------------------|-------------------|-------------|
| **Bus físico** | RS485 (A, B, GND) | 3 hilos (P, G, C) | ❌ Diferente |
| **Velocidad** | 38400 baudios | 2400 baudios | ❌ Diferente |
| **Protocolo** | ABCD (moderno) | CCN (legacy) | ⚠️ Parcial |
| **Direccionamiento** | Sí (2001, 4001) | No (broadcast) | ❌ Diferente |
| **Alimentación** | 24VAC separada | +12V integrada | ❌ Diferente |
| **Estructura** | Frame con header | Frame con delimitadores | ⚠️ Similar |

**Conclusión previa:** No puedes usar Infinitive *directamente*, pero sí puedes **aprender su metodología**.

---

## ✅ Qué PUEDES Aprovechar de Infinitive

### 1. Metodología de Análisis de Frames

Infinitive descubrió que los frames ABCD tienen estructura:
```
2001 -> 4001: READ     000302
4001 -> 2001: RESPONSE 000302041100000414000004020000
^^^^    ^^^^  ^^^^^^   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Origen  Dest  Tipo     Datos
```

**Aplicación a tu CCN:**
```
Tu dump CCN:
00 00 08 21 21 08 61 69 68 09 29 6B 68 69 00 ...
^^^^^^
Header (STX + separador) - similar concepto de delimitación
```

**Lección:** Busca patrones de delimitación en tus tramas (ya encontraste `0x00 0x00 0x08`).

---

### 2. Técnica de Descubrimiento de Campos

Infinitive usó **comparación de estados**:
1. Capturar trama con modo "COOL"
2. Capturar trama con modo "HEAT"  
3. Comparar bytes que cambian
4. Correlacionar con funciones

**Esto es EXACTAMENTE lo que te propuse en CHECKLIST.md**

**Ejemplo de Infinitive:**
```
READ    000302     → Solicitud de temperatura
RESPONSE 000302... → Respuesta con valor codificado
         ^^^^^^
         Offset de temperatura
```

**Tu aplicación:**
```python
# En tu CHECKLIST.md - Análisis diferencial
# FAN_STOP vs FAN_LOW vs FAN_MED vs FAN_HIGH
# Ver qué bytes cambian en cada modo
```

---

### 3. Estructura de Tablas de Configuración

Infinitive descubrió que Infinity usa **tablas con offsets**:
- Tabla `0003` → Configuración de zona
- Offset `02` → Temperatura
- Offset `16` → Humedad

**Aplicación a CCN:**
Tu protocolo probablemente tiene **bloques funcionales**:
```
Bytes 3-5  → Configuración ventilador (ya detectado)
Bytes 7-9  → Modo de operación
Bytes X-Y  → Temperatura setpoint (pendiente de descubrir)
```

---

### 4. Recursos de Referencia

Infinitive menciona estos recursos que pueden tener info sobre CCN:
- **Cocoontech's Carrier Infinity Thread** → Foro con información histórica
- **Infinitude Wiki** → Documentación del protocolo ABCD (parcialmente aplicable a CCN)

**Búsquedas recomendadas:**
```
Site:cocoontech.com "CRC2" OR "CCN" OR "Carrier Comfort Network"
Site:cocoontech.com "RS485" "2400 baud" "Carrier"
```

---

### 5. Concepto de "Passive Sniffing"

Infinitive funciona en modo **pasivo** (sniffing) + **activo** (escritura).

**Tu aplicación:**
```bash
# Modo pasivo (ya lo haces)
python3 curryrtool.py device read -p /dev/ttyUSB0 ...

# Modo repetidor (similar a Infinitive)
python3 curryrtool.py device repeat -p /dev/ttyUSB0 -r /dev/ttyUSB1 ...
```

---

## ❌ Qué NO Puedes Aplicar Directamente

### 1. Código Fuente de Infinitive

**Problema:** Escrito en Go, para protocolo ABCD, a 38400 baudios.

```go
// Código Infinitive (github.com/acd/infinitive)
// NO es compatible con tu CCN

frame := ReadFrame()  // Espera formato ABCD
// Tu CCN usa formato diferente (delimitadores 0x00, 0x08)
```

**Alternativa:** Usar la **lógica** pero no el código.

---

### 2. Estructura de Frames ABCD

**Formato Infinitive:**
```
Origen (2 bytes) → Destino (2 bytes) → Tipo (1 byte) → Datos (N bytes)
2001                4001                 READ            000302
```

**Tu formato CCN:**
```
Delimitadores (0x00, 0x08) → Bloques de datos → Checksum
00 00 08 21 21 08 ... 08
```

**Son incompatibles.**

---

### 3. Velocidad y Timing

| Parámetro | Infinitive | Tu CCN |
|-----------|-----------|--------|
| Baudios | 38400 | 2400 |
| Tiempo/bit | 26 µs | 416 µs |
| Frames/seg | ~30-50 | ~5-10 |

**Consecuencia:** Los timeouts y lógica de timing de Infinitive no aplican.

---

## 🔧 Adaptaciones Prácticas

### Estrategia 1: Usar Infinitive como "Inspiración Metodológica"

| Paso Infinitive | Adaptación a CCN |
|-----------------|------------------|
| 1. Sniffing pasivo | Usa `curryrtool.py device read` |
| 2. Identificar tipos de frames | Clasificar por tamaño (85/88/91/94) |
| 3. Comparar estados | CHECKLIST.md Fase 2 (diferencial) |
| 4. Mapear offsets | Mapear posiciones de bytes |
| 5. Implementar escritura | `curryrtool.py device write` |
| 6. API REST | Podrías añadir similar a Infinitive |

---

### Estrategia 2: Buscar Implementaciones CCN Específicas

Buscar proyectos similares pero para **CCN legacy**:

```bash
# Búsquedas GitHub
github.com "Carrier" "CCN" "RS485"
github.com "Carrier" "Comfort Network" "thermostat"
github.com "CRC2" OR "NTC" "protocol"

# Foros
cocoontech.com/forums/threads/carrier-ccn
hvac-talk.com "CCN" "protocol"
```

---

### Estrategia 3: Crear Tu Propio "Infinitive para CCN"

Basándote en la arquitectura de Infinitive:

```python
# Estructura propuesta (adaptación de Infinitive)

class CCNFrame:
    """Similar a infinitive/frame.go pero para CCN"""
    
    def __init__(self, raw_bytes):
        self.raw = raw_bytes
        self.size = len(raw_bytes)
        self.valid = self.validate()
    
    def validate(self):
        # Validar delimitadores (tu descubrimiento)
        return self.raw[0:3] == [0x00, 0x00, 0x08]
    
    def parse(self):
        return {
            'fan': self.parse_fan(),
            'mode': self.parse_mode(),
            'temp': self.parse_temp(),
        }

# Web API (como Infinitive)
from flask import Flask
app = Flask(__name__)

@app.route('/api/status')
def get_status():
    frame = read_last_ccn_frame()
    return jsonify(frame.parse())
```

---

## 📊 Matriz de Correspondencia de Campos

Intentar mapear campos de Infinitive a tu CCN:

| Función | Infinitive (ABCD) | Tu CCN (CCN) | Estado |
|---------|-------------------|--------------|--------|
| **Fan Mode** | Tabla 0003, offset X | Bytes 3-5 | ✅ Identificado |
| **Mode (COOL/HEAT)** | Tabla 0003, offset Y | Byte 7-8 | ⚠️ Hipótesis |
| **Setpoint** | Tabla 0003, offset 02 | Byte ? | ❓ Pendiente |
| **Temp actual** | Tabla 0003, offset ? | Byte ? | ❓ Pendiente |
| **Humedad** | Tabla 0003, offset 16 | No aplica | N/A (CRC2 no tiene) |

---

## 🎯 Conclusión y Recomendaciones

### Lo que Infinitive PUEDE aportarte:

1. **Validación de metodología:** Tu enfoque de análisis diferencial es el correcto (igual que usaron en Infinitive)
2. **Inspiración arquitectónica:** Puedes crear una API REST similar para tu CCN
3. **Recursos:** Foros como Cocoontech pueden tener hilos históricos sobre CCN
4. **Herramientas:** Concepto de "passive sniffing" + "active control"

### Lo que NO puedes usar:

1. **Código fuente directamente:** Protocolos incompatibles
2. **Decodificación de frames:** Formato ABCD ≠ formato CCN
3. **Velocidades y timings:** 38400 ≠ 2400 baudios

---

## 🚀 Siguiente Paso Sugerido

### Opción A: Investigación en Foros
Visitar Cocoontech y buscar información específica de CCN:
```
https://cocoontech.com/forums/
Buscar: "Carrier CCN", "CRC2", "2400 baud", "RS485 thermostat"
```

### Opción B: Contactar Comunidad
Infinitive tiene developers activos. Podrías preguntar:
> "¿Alguien tiene información del protocolo CCN legacy a 2400 baudios usado en termostatos CRC2-NTC?"

### Opción C: Seguir tu CHECKLIST.md
La metodología es la misma que usó Infinitive. Continuar con:
1. Capturas sistemáticas por estado
2. Análisis diferencial
3. Identificación de checksum
4. Emulación

---

## 📚 Referencias Cruzadas

| Recurso | Tema | Utilidad para CCN |
|---------|------|-------------------|
| [Infinitive Wiki](https://github.com/acd/infinitive/wiki) | Protocolo ABCD | Baja (diferente protocolo) |
| [Cocoontech Forum](https://cocoontech.com/forums/) | Carrier HVAC | Media (puede haber info CCN) |
| [Infinitude](https://github.com/nebulous/infinitude) | Alternative Infinity | Baja (también ABCD) |
| [InfinitESP](https://github.com/nebulous/infinitesp) | ESP32 ABCD | Baja (hardware diferente) |

---

*Documento generado para comparación metodológica*
