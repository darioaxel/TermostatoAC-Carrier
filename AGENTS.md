# TermostatoAC-Carrier - Guía para Agentes de Código

## Visión General del Proyecto

Este proyecto tiene como objetivo analizar los datos emitidos por el termostato **Carrier CRC2-NTC** (un modelo obsoleto) mediante comunicación RS485, con el fin de entender su funcionamiento interno y eventualmente reemplazarlo con un dispositivo compatible que permita programación avanzada, acceso remoto y una interfaz moderna.

El proyecto combina:
- **Comunicación Serial**: Lectura y escritura de datos del termostato vía USB-RS485
- **Machine Learning**: Entrenamiento de modelos neuronales para predecir el estado del termostato
- **Análisis de Protocolos**: Ingeniería inversa del protocolo CCN (Carrier Comfort Network)

---

## Stack Tecnológico

- **Lenguaje**: Python 3
- **Librerías Principales**:
  - `pyserial` - Comunicación con el puerto serie
  - `tensorflow` / `keras` - Entrenamiento de modelos de machine learning
  - `numpy` - Procesamiento numérico
  - `matplotlib` - Visualización de gráficos
  - `optparse` - Interfaz de línea de comandos

---

## Estructura del Proyecto

```
TermostatoAC-Carrier/
├── curryrtool.py              # Entry point principal de la aplicación
├── curryrtoolslib/            # Paquete Python con la lógica completa
│   ├── interfaces/            # Interfaces de usuario (CLI)
│   │   ├── common_interface.py      # Clase base para interfaces
│   │   ├── devices_interface.py     # Comunicación serial (read/write/repeat)
│   │   └── trainning_interface.py   # Entrenamiento y predicción ML
│   ├── utils/                 # Utilidades
│   │   ├── ia.py              # Funciones TensorFlow/Keras
│   │   ├── trama.py           # Gestión de tramas (85/88/91/94 bytes)
│   │   ├── graphics.py        # Visualización de datos
│   │   └── config.py          # Gestión de configuración
│   ├── loader/                # Bootstrap y entry points
│   │   ├── main.py            # Inicialización de la aplicación
│   │   └── entry_points.py    # Router de comandos
│   └── __init__.py            # Configuración global
├── dumps/                     # Datos capturados del termostato
│   ├── *.bin                  # Tramas en formato binario
│   └── *.info                 # Metadatos JSON de las tramas
├── models/                    # Modelos entrenados (Keras .keras)
├── images/                    # Documentación visual (fotos, diagramas)
├── CH341SER/                  # Drivers para el adaptador USB-RS485
├── README.md                  # Documentación en inglés
├── README_es.md               # Documentación en español (principal)
├── CCN_PROTOCOL_ANALYSIS.md   # Análisis técnico del protocolo CCN
├── CHECKLIST.md               # Guía de ingeniería inversa
└── .gitignore                 # Excluye: *.zip, CH341SER, dumps, models, __pycache__
```

---

## Módulos Principales

### 1. curryrtool.py (Entry Point)
**Propósito**: Punto de entrada principal de la aplicación.

**Uso**:
```bash
python3 curryrtool.py <comando> <acción> [opciones]
```

**Comandos disponibles**:
- `device` - Operaciones de comunicación serial
- `trainning` - Entrenamiento y predicción ML

---

### 2. devices_interface.py
**Propósito**: Interfaz completa de comunicación con el termostato.

**Acciones disponibles**:

| Acción | Descripción | Parámetros requeridos |
|--------|-------------|----------------------|
| `menu` | Menú interactivo CLI | - |
| `read` | Lee datos del puerto serie | `-p`, `-b`, `-t`, `-o` |
| `write` | Envía trama al termostato | `-p`, `-b`, `-t`, `-f`, `-r`, `-i` |
| `repeat` | Modo repetidor (sniffer) | `-p`, `-r`, `-b`, `-t` |

**Ejemplos**:

```bash
# Leer datos y guardar en archivo
python3 curryrtool.py device read -p /dev/ttyUSB0 -b 2400 -t 0.1 -o "0,0,1,0,0,1"

# Enviar trama previamente capturada
python3 curryrtool.py device write -p /dev/ttyUSB0 -b 2400 -t 0.1 \
    -f dumps/trama.bin -r 30 -i 5

# Modo repetidor (lee de un puerto y reenvía a otro)
python3 curryrtool.py device repeat -p /dev/ttyUSB0 -r /dev/ttyUSB1 -b 2400 -t 0.1
```

**Parámetros de línea de comandos**:
- `-p, --port`: Puerto serial (default: `/dev/ttyUSB0`)
- `-b, --baudrate`: Velocidad en baudios (default: `2400`)
- `-t, --timeout`: Timeout de lectura en segundos (default: `0.1`)
- `-o, --posiciones`: Estado de los controles, formato "FAN1,FAN2,FAN3,COLD,HOT,DRY"
- `-f, --tramafile`: Archivo de trama a enviar (formato .bin)
- `-r, --repeticiones`: Número de veces a enviar la trama
- `-i, --intervalo`: Tiempo entre envíos en segundos
- `-s, --savefile`: Guardar datos capturados (default: True)

---

### 3. trainning_interface.py
**Propósito**: Interfaz de entrenamiento y predicción con Machine Learning.

**Acciones disponibles**:

| Acción | Descripción |
|--------|-------------|
| `entrenar` | Entrena un modelo neuronal con datos capturados |
| `prediccion` | Predice estado a partir de una trama |

**Ejemplos**:
```bash
# Entrenar nuevo modelo
python3 curryrtool.py trainning entrenar epocas=20000 layers=1 neuronas=79 save

# Entrenar modelo existente
python3 curryrtool.py trainning entrenar modelo=models/mi_modelo.keras epocas=5000 save

# Realizar predicción
python3 curryrtool.py trainning prediccion modelo=models/modelo.keras trama=0,0,8,8,97,9...
```

**Clases de salida** (6 valores binarios):
- `fan1`, `fan2`, `fan3` - Estado del ventilador (3 posiciones)
- `cold` - Modo frío activo
- `hot` - Modo calor activo
- `dry` - Modo seco activo

---

### 4. trama.py
**Propósito**: Gestión y procesamiento de tramas del protocolo CCN.

**Funciones principales**:
- `validar_trama_bytes()` - Valida estructura de trama (header `0x00, 0x08`)
- `guardar_trama_bytes()` - Guarda trama en formato binario (.bin) + metadatos (.info)
- `cargar_trama_bytes()` - Carga trama desde archivo binario
- `normalizar_datos()` - Prepara datos para entrada a la red neuronal
- `normalizar_bloque()` - Elimina bytes no necesarios (delimitadores)

**Tamaños de trama soportados**: 85, 88, 91, 94 bytes

**Formato de almacenamiento**:
```
dumps/
├── <uuid>.bin       # Datos binarios crudos de la trama
└── <uuid>.info      # Metadatos JSON (timestamp, baudrate, valores, etc.)
```

---

### 5. ia.py
**Propósito**: Funciones de bajo nivel para TensorFlow/Keras.

**Funciones principales**:
- `init_modelo()` - Crea modelo secuencial con capas Dense
  - Input: Variable (85/88/91/94 bytes normalizados)
  - Output: 6 neuronas (sigmoid) - estados binarios
  - Optimizador: Adam
  - Loss: mean_squared_error
- `load_modelo()` / `save_modelo()` - Persistencia de modelos
- `entrenar_datos()` - Wrapper de model.fit()
- `predecir()` - Realiza predicciones

---

### 6. config.py
**Propósito**: Gestión centralizada de configuración.

**Almacenamiento**: `~/.config/curryrtools/config.ini`

**Configuraciones por defecto**:
```ini
[CONFIG]
dumpsfolder = dumps
modelofolder = models
port = /dev/ttyUSB0
baudrate = 2400
timeout = 0.1
posiciones = 000000
savefile = s
repeticionesenvio = 30
portsalida = /dev/ttyUSB1
neuronasfirstlayer = 79
```

---

## Flujo de Trabajo Típico

### 1. Captura de Datos

```bash
# Capturar datos con estado específico del termostato
python3 curryrtool.py device read -p /dev/ttyUSB0 -b 2400 -t 0.1 -o "0,1,0,1,0,0"

# Los archivos se guardan en dumps/ como:
# - <uuid>.bin (datos binarios)
# - <uuid>.info (metadatos JSON)
```

### 2. Entrenamiento

```bash
# Entrenar modelo con todos los datos capturados
python3 curryrtool.py trainning entrenar epocas=20000 save

# Modelo guardado en models/modelo_{timestamp}_{epocas}.keras
```

### 3. Predicción

```bash
# Predecir estado desde línea de comandos
python3 curryrtool.py trainning prediccion modelo=models/modelo.keras trama=0,0,8,...

# O usar el modo interactivo
python3 curryrtool.py trainning menu
```

### 4. Emulación (Repetición de Tramas)

```bash
# Reproducir trama capturada para emular el termostato
python3 curryrtool.py device write \
    -p /dev/ttyUSB0 -b 2400 -t 0.1 \
    -f dumps/<uuid>.bin -r 100 -i 0.5
```

---

## Configuración del Entorno

### Permisos de dispositivo (Linux)

Para acceder al puerto USB sin sudo:
```bash
sudo usermod -a -G dialout $USER
# Requiere cerrar sesión y volver a iniciar
```

### Hardware requerido

- Adaptador USB a RS485 (basado en CH341)
- Conexión al termostato:
  - P (Power) → 12V
  - G (Ground) → GND
  - C (Data) → A/B del adaptador (verificar polaridad)

### Parámetros de comunicación

- Puerto por defecto: `/dev/ttyUSB0`
- Baudrate: 2400 (detectado automáticamente)
- Timeout: 0.1 segundos (configurable)
- Tamaños de trama: 85, 88, 91, 94 bytes (según estado del termostato)

---

## Convenciones de Código

- **Idioma**: Código y comentarios en español
- **Nombres de variables**: snake_case (ej: `datos_entrenamiento`, `nombre_modelo`)
- **Constantes globales**: UPPER_CASE (ej: `VALID_SIZES`, `CONFIG`)
- **Encoding**: UTF-8
- **Indentación**: 4 espacios
- **Type hints**: Uso de anotaciones de tipo (`List[int]`, `Dict[str, Any]`)

---

## Gestión de Dependencias

**Nota importante**: El proyecto no incluye archivo `requirements.txt` ni `pyproject.toml`. Las dependencias deben instalarse manualmente:

```bash
pip install pyserial tensorflow numpy matplotlib
```

---

## Estrategia de Testing

Actualmente **no hay tests automatizados**. El proyecto se prueba de forma manual:
- Verificación de lectura de datos en tiempo real
- Comprobación visual de gráficas de entrenamiento
- Validación de predicciones contra estados conocidos
- Pruebas de emulación con tramas capturadas

---

## Estructura de Datos

### Formato Binario (dumps/*.bin + *.info)

**Archivo .bin**: Datos crudos de la trama (88 bytes típicamente)

**Archivo .info** (JSON):
```json
{
    "stream": "dumps/<uuid>.bin",
    "blocks": 10,
    "timeout": 0.1,
    "baudrate": 2400,
    "times": [["2024-11-27T21:16:00", 88], ...],
    "uuid": "<uuid>",
    "values": "0,0,1,0,0,1"
}
```

### Campos de valores

- **values**: 6 valores binarios separados por comas:
  - `[fan1, fan2, fan3, cold, hot, dry]`
  - Ejemplo `0,0,1,0,0,1` = Fan medio, Dry activo

### Modelos entrenados

- Guardados en carpeta `models/` (creada automáticamente)
- Formato: Keras (.keras)
- Convención de nombres: `modelo_{YYYYMMDD}_{HHMMSS}_{epocas}.keras`

---

## Consideraciones de Seguridad

- El módulo `devices_interface.py` requiere acceso al puerto serie (`/dev/ttyUSB0`)
- Los datos del termostato no contienen información sensible
- Los modelos entrenados se guardan localmente
- **Precaución**: El modo `write` puede alterar el estado del termostato si se conecta a un bus con otros dispositivos

---

## Notas para Desarrolladores

1. **CurryRToolsLib**: El paquete `curryrtoolslib/` ahora contiene implementación completa. La refactorización desde scripts sueltos a paquete estructurado está terminada.

2. **Múltiples tamaños de trama**: El protocolo CCN genera tramas de diferentes tamaños según el estado:
   - 85 bytes: Estados simples
   - 88 bytes: Estados con modo activo (cool/heat/dry)
   - 91 bytes: Estados extendidos
   - 94 bytes: Estados complejos o con sensores adicionales

3. **Normalización**: Los datos se normalizan dividiendo por 255 (conversión a float 0-1) antes de entrar a la red neuronal.

4. **Arquitectura del modelo**: Red neuronal secuencial con:
   - Capa de entrada variable según tamaño de trama
   - 1-N capas Dense con activación ReLU
   - Capa de salida Dense(6, sigmoid)

5. **Modo repetidor**: La funcionalidad `repeat` permite usar el adaptador como puente/sniffer entre dos puertos serie.

---

## Referencias de Documentación Adicional

- `CCN_PROTOCOL_ANALYSIS.md` - Análisis técnico detallado del protocolo Carrier Comfort Network
- `CHECKLIST.md` - Guía paso a paso para ingeniería inversa del protocolo
- `README_es.md` - Documentación general del proyecto

---

*Documento actualizado para reflejar la arquitectura actual del proyecto (Marzo 2026)*
