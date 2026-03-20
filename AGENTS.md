# TermostatoAC-Carrier - Guía para Agentes de Código

## Visión General del Proyecto

Este proyecto tiene como objetivo analizar los datos emitidos por el termostato **Carrier CRC2-NTC** (un modelo obsoleto) mediante comunicación RS485, con el fin de entender su funcionamiento interno y eventualmente reemplazarlo con un dispositivo compatible que permita programación avanzada, acceso remoto y una interfaz moderna.

El proyecto combina:
- **Comunicación Serial**: Lectura de datos del termostato vía USB-RS485
- **Machine Learning**: Entrenamiento de modelos neuronales para predecir el estado del termostato a partir de las tramas de datos
- **Análisis de Datos**: Procesamiento y visualización de las tramas hexadecimales

---

## Stack Tecnológico

- **Lenguaje**: Python 3
- **Librerías Principales**:
  - `pyserial` - Comunicación con el puerto serie
  - `tensorflow` / `keras` - Entrenamiento de modelos de machine learning
  - `numpy` - Procesamiento numérico
  - `matplotlib` - Visualización de gráficos
  - `tensorflow-datasets` - Carga de datasets (referencia)

---

## Estructura del Proyecto

```
TermostatoAC-Carrier/
├── USB2RS485.py          # Script principal de comunicación serial
├── trainning_tools.py    # CLI para entrenamiento y predicción
├── ia_tools.py           # Utilidades de TensorFlow/Keras
├── graphics_tools.py     # Visualización de predicciones
├── curryrtoolslib/       # Paquete Python (estructura preparada, casi vacía)
│   ├── loader/           # (vacío, solo __pycache__)
│   └── utils/            # (vacío, solo __pycache__)
├── dumps/                # Datos capturados del termostato (CSV)
├── images/               # Documentación visual (fotos, diagramas)
├── CH341SER/             # Drivers para el adaptador USB-RS485
├── README.md             # Documentación en inglés
├── README_es.md          # Documentación en español (principal)
└── .gitignore            # Excluye: *.zip, CH341SER, dumps, models, __pycache__
```

---

## Módulos Principales

### 1. USB2RS485.py
**Propósito**: Interfaz de comunicación con el termostato vía RS485.

**Funciones clave**:
- `read_serial_data()` - Lee datos del puerto serie y opcionalmente guarda en CSV
- `detect_baud_rate()` - Detecta automáticamente la velocidad de transmisión
- `measure_time_between_messages()` - Mide intervalos entre mensajes
- `calculate_message_size()` - Calcula tamaño de mensajes
- `main_menu()` - Menú interactivo CLI

**Uso típico**:
```bash
python3 USB2RS485.py
# Seleccionar opción 1 para lectura de datos
# Por defecto: puerto /dev/ttyUSB0, baudrate 2400
```

**Formato de salida (dumps/)**:
- Archivos CSV con nombre: `datos_hex_{baudrate}_{posiciones}_{timestamp}.csv`
- Estructura: columna "Trama" (valores hexadecimales separados por comas) y "Posiciones" (estado de los controles)
- Las tramas tienen 91 bytes de longitud (padded con ceros si es necesario)

### 2. trainning_tools.py
**Propósito**: Interfaz de línea de comandos para entrenamiento y predicción.

**Acciones disponibles**:

| Acción | Descripción | Parámetros |
|--------|-------------|------------|
| `entrenar` | Entrena un modelo neuronal | `epocas=`, `modelo=`, `dataset=`, `layers=`, `neuronas=`, `save` |
| `prediccion` | Predice estado a partir de trama | `modelo=`, `trama=` |

**Ejemplos**:
```bash
# Entrenar nuevo modelo
python3 trainning_tools.py entrenar epocas=20000 layers=1 neuronas=10 save

# Entrenar modelo existente
python3 trainning_tools.py entrenar modelo=models/mi_modelo.keras epocas=5000 save

# Realizar predicción
python3 trainning_tools.py prediccion modelo=models/modelo_20241128_120059_10.keras trama=0,0,8,8,97,9...
```

**Clases de salida** (6 valores binarios):
- `fan1`, `fan2`, `fan3` - Estado del ventilador (3 posiciones)
- `cold` - Modo frío activo
- `hot` - Modo calor activo
- `dry` - Modo seco activo

### 3. ia_tools.py
**Propósito**: Funciones de bajo nivel para TensorFlow/Keras.

**Funciones principales**:
- `init_modelo()` - Crea modelo secuencial con capas Dense
  - Input: (91, 1) - trama de 91 bytes
  - Output: 6 neuronas (sigmoid) - estados binarios
  - Optimizador: Adam
  - Loss: mean_squared_error
- `load_modelo()` / `save_modelo()` - Persistencia de modelos
- `entrenar_datos()` - Wrapper de model.fit()
- `predecir()` - Realiza predicciones y muestra resultados formateados

### 4. graphics_tools.py
**Propósito**: Visualización de resultados del modelo.

**Funciones**:
- `genera_predicciones()` - Muestra grid de predicciones vs valores reales
- `mostrar_graf()` - Gráfica de precisión y pérdida durante entrenamiento

---

## Flujo de Trabajo Típico

1. **Captura de datos**:
   ```bash
   python3 USB2RS485.py
   # Opción 1 → Guardar con posiciones de controles (ej: 010100)
   ```

2. **Entrenamiento**:
   ```bash
   python3 trainning_tools.py entrenar epocas=20000 save
   # Modelo guardado en models/modelo_{timestamp}_{epocas}.keras
   ```

3. **Predicción**:
   ```bash
   python3 trainning_tools.py prediccion modelo=models/modelo_xxx.keras trama=0,0,8,...
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
  - C (Data) → B- del adaptador

### Parámetros de comunicación
- Puerto por defecto: `/dev/ttyUSB0`
- Baudrate: 2400 (detectado automáticamente)
- Timeout: 1 segundo

---

## Convenciones de Código

- **Idioma**: Código y comentarios en español
- **Nombres de variables**: snake_case (ej: `datos_entrenamiento`, `nombre_modelo`)
- **Constantes globales**: UPPER_CASE (ej: `LISTA_CLASES`, `TAMANO_LOTE`)
- **Encoding**: UTF-8
- **Indentación**: 4 espacios

---

## Gestión de Dependencias

**Nota importante**: El proyecto no incluye archivo `requirements.txt` ni `pyproject.toml`. Las dependencias deben instalarse manualmente:

```bash
pip install pyserial tensorflow numpy matplotlib tensorflow-datasets
```

---

## Estrategia de Testing

Actualmente **no hay tests automatizados**. El proyecto se prueba de forma manual:
- Verificación de lectura de datos en tiempo real
- Comprobación visual de gráficas de entrenamiento
- Validación de predicciones contra estados conocidos

---

## Estructura de Datos

### Formato CSV (dumps/)
```csv
Trama;Posiciones
0,0,8,8,33,33,...;0,0,1,0,0,1
```

- **Trama**: Valores decimales de bytes (0-255), 91 elementos
- **Posiciones**: 6 valores binarios separados por comas:
  - `[fan1, fan2, fan3, cold, hot, dry]`
  - Ejemplo `0,0,1,0,0,1` = Fan medio, Dry activo

### Modelos entrenados
- Guardados en carpeta `models/` (creada automáticamente)
- Formato: Keras (.keras)
- Convención de nombres: `modelo_{YYYYMMDD}_{HHMMSS}_{epocas}.keras`

---

## Consideraciones de Seguridad

- El script `USB2RS485.py` requiere acceso al puerto serie (`/dev/ttyUSB0`)
- Los datos del termostato no contienen información sensible
- Los modelos entrenados se guardan localmente

---

## Notas para Desarrolladores

1. **CurryRToolsLib**: El paquete `curryrtoolslib/` está estructurado como librería Python pero actualmente no contiene implementaciones (solo `__pycache__`). Es una estructura preparada para futura modularización.

2. **Datos de entrenamiento**: El modelo espera tramas de exactamente 91 bytes. Los datos se normalizan dividiendo por 255 (conversión a float 0-1).

3. **Arquitectura del modelo**: Red neuronal secuencial con:
   - Capa Flatten (input: 91x1)
   - 1-N capas Dense con activación ReLU
   - Capa de salida Dense(6, sigmoid)

4. **Dataset mínimo**: Se recomienda recolectar múltiples archivos CSV en `dumps/` con diferentes estados del termostato para un entrenamiento efectivo.
