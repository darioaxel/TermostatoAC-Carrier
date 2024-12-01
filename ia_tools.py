import tensorflow as tf
import tensorflow_datasets as tfds
import os
import config as config_mod

CONFIG = config_mod.cargar_configuracion()

TAMANO_LOTE = 10

def inicializar_dataset(nombre):
    datos, metadatatos = tfds.load(nombre, with_info=True, as_supervised=True)
    datos_entrenamiento, datos_prueba = datos['train'], datos['test']
    print(datos_entrenamiento)
    print(datos_prueba)

    datos_entrenamiento = datos_entrenamiento.map(normalizar)
    datos_prueba = datos_prueba.map(normalizar)
    datos_entrenamiento = datos_entrenamiento.cache()
    datos_prueba = datos_prueba.cache()

    return datos_entrenamiento, datos_prueba, metadatatos

def inicializar_datos(nombre_repo):
    print("Inicializando datos...")
    datos_entrenamiento, datos_prueba, metadatos = inicializar_dataset(nombre_repo)
    num_entrenamiento = metadatos.splits['train'].num_examples
    datos_entrenamiento = datos_entrenamiento.repeat().shuffle(num_entrenamiento).batch(TAMANO_LOTE)
    datos_prueba = datos_prueba.batch(TAMANO_LOTE)
    return datos_entrenamiento, datos_prueba, metadatos

def normalizar(datos, tipos):
    datos = tf.cast(datos, tf.float32)
    datos /= 255 # pasa de 0..255 a 0...1
    return datos, tipos


def init_modelo(input_schema, output_shapes=1, layers=[10,10,10], opt=0.001):
    print("Inicializando modelo...")
    print("Input schema: %s" % str(input_schema))
    print("Output shapes: %s" % str(output_shapes))
    print("Layers: %s" % str(layers))

    layers_list = []
    layers_list.append(tf.keras.layers.Flatten(input_shape=input_schema)) # 91, 1, 1 - blanco y negro
    for layer in layers:
        #print("*  +++ add Layer %d" % num)
        layers_list.append(tf.keras.layers.Dense(int(layer), activation=tf.nn.relu))
    
    #layers_list.append(tf.keras.layers.Dense(output_shapes, activation=tf.nn.relu))
    layers_list.append(tf.keras.layers.Dense(output_shapes, activation=tf.nn.sigmoid))
    #tf.keras.layers.Dense(10, activation=tf.nn.softmax) # Para redes de clasificación
    modelo = tf.keras.Sequential(layers_list)
    modelo.compile(
        optimizer=tf.keras.optimizers.Adam(opt),
        # loss='categorical_crossentropy',
        # loss=tf.keras.losses.BinaryCrossentropy(from_logits=True),
        loss='mean_squared_error',
        metrics=['accuracy']
    )
    return modelo


def predecir(trama, modelo, lista_clases):
    print("Predecir...", lista_clases)
    #trama = np.array(trama)
    prediccion = modelo.predict(trama)
    print(prediccion)
    str_val = bin(int(prediccion[0][0]))[2:].zfill(8)
    for control in ["FAN","COLD","DRY","HOT"]:
        val = "OFF"
        if control == "FAN":
            sub_str = str_val[2:5]
            val =  "1" if sub_str == "100" else "2" if sub_str == "010" else "3" if sub_str == "001" else "0"
        elif control == "COLD":
            val = "ON" if str_val[5] == "1" else "OFF"
        elif control == "DRY":
            val = "ON" if str_val[6] == "1" else "OFF"
        elif control == "HOT":
            val = "ON" if str_val[7] == "1" else "OFF"
        else:
            val = "???"
        print("%s: %s" % (control, val))
    """ posiciones=""
    for num, clase in enumerate(lista_clases):
        pos = "ON" if prediccion[0][num] == 1.0 else "OFF"
        posiciones += "1" if pos == "ON" else "0"
        print("%s : %s (accuracy:%s)" % (clase, pos, prediccion[0][num]))
    #nombre_clases[np.argmax(prediccion[0])]
    print(posiciones) """


def entrenar_datos(datos, resultados, epocas, num_datos, modelo, verb=True):

    print("Entrenando modelo durante %d epocas ..." % (epocas))
    print("Datos: %d" % num_datos)
    print("*", modelo)
    result = modelo.fit(datos, resultados,epochs=epocas, verbose=verb) #, steps_per_epoch=math.ceil(num_datos/TAMANO_LOTE)
    print("Entrenamiento finalizado")
    return result


def load_modelo(nombre_modelo):
    nombre_modelo = os.path.basename(nombre_modelo)
    if os.path.exists(nombre_modelo):
        nombre_modelo_path = nombre_modelo
    else:
        nombre_modelo_path = os.path.join(os.path.dirname(__file__),CONFIG.get(section='CONFIG', option='modelsfolder'), nombre_modelo)
    if not os.path.exists(nombre_modelo_path):
        print("No existe el modelo %s" % nombre_modelo_path)
        return None
    model = tf.keras.models.load_model(nombre_modelo_path) 
    model.summary()
    return model

def save_modelo(modelo, nombre_modelo):
    nombre_modelo = os.path.basename(nombre_modelo)
    folder_modelos = os.path.join(os.path.dirname(__file__), CONFIG.get(section='CONFIG', option='modelsfolder'))
    if not os.path.exists(folder_modelos):
        os.mkdir(folder_modelos)
    nombre_modelo = os.path.join(folder_modelos, nombre_modelo)

    modelo.save(nombre_modelo)
    print("Modelo guardado en %s" % nombre_modelo)

def recoge_datos_modelo(modelo):
    layers = []
    epocas = None
    for capa in modelo.layers:
        layers.append(str(capa.output.shape[1]))

    return epocas, layers

def mostrar_pesos_modelo(modelo):
    print("Mostrando pesos de la red neuronal")
    for num,capa in enumerate(modelo.layers):
        print("Capa", num)
        print(capa.get_weights())
        print("----")
        print(capa.get_config())
        if hasattr(capa, "output_shape"):
            print("----")
            print(capa.output_shape)

        if hasattr(capa, "input_shape"):
            print("----")
            print(capa.input_shape)
        
        print("----")
        print(capa.output)
        print("\n\n")
        
