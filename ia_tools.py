
from graphics_tools import genera_predicciones

import tensorflow as tf
import tensorflow_datasets as tfds
import math
import numpy as np
import os

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


def init_modelo(input_schema, output_shapes=6, npc=10, layers_cnt=3, opt=0.0001):
    print("Inicializando modelo...")

    layers_list = []
    layers_list.append(tf.keras.layers.Flatten(input_shape=input_schema)) # 91, 1, 1 - blanco y negro
    for num in range(layers_cnt):
        #print("*  +++ add Layer %d" % num)
        layers_list.append(tf.keras.layers.Dense(npc, activation=tf.nn.relu))
    
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
    posiciones=""
    for num, clase in enumerate(lista_clases):
        pos = "ON" if prediccion[0][num] == 1.0 else "OFF"
        posiciones += "1" if pos == "ON" else "0"
        print("%s : %s (accuracy:%s)" % (clase, pos, prediccion[0][num]))
    #nombre_clases[np.argmax(prediccion[0])]
    print(posiciones)

def entrenar_datos(datos, resultados, epocas, num_datos, modelo):

    print("Entrenando modelo...")
    print("Épocas: %d" % epocas)
    print("Datos: " + str(num_datos))
    return modelo.fit(datos, resultados,epochs=epocas) #, steps_per_epoch=math.ceil(num_datos/TAMANO_LOTE)

def run(epocas):
    
    datos_entrenamiento, datos_prueba, metadatos = inicializar_datos('fashion_mnist')

    num_entrenamiento = metadatos.splits['train'].num_examples
    num_prueba = metadatos.splits['test'].num_examples
    nombre_clases = metadatos.features['label'].names
    print("Número de ejemplos de entrenamiento: {}".format(num_entrenamiento))
    print("Número de ejemplos de prueba: {}".format(num_prueba))
    print("Nombres de las clases: {}".format(nombre_clases))
    modelo = init_modelo((28,28,1))
    entrenar_datos(datos_entrenamiento, None, epocas, num_entrenamiento, modelo)

    genera_predicciones(datos_prueba, modelo, nombre_clases) 


def load_modelo(nombre_modelo):
    nombre_modelo = os.path.basename(nombre_modelo)
    if os.path.exists(nombre_modelo):
        nombre_modelo_path = nombre_modelo
    else:
        nombre_modelo_path = os.path.join(os.path.dirname(__file__),'models', nombre_modelo)
    if not os.path.exists(nombre_modelo_path):
        print("No existe el modelo %s" % nombre_modelo_path)
        return None
    model = tf.keras.models.load_model(nombre_modelo_path) 
    model.summary()
    return model

def save_modelo(modelo, nombre_modelo):
    nombre_modelo = os.path.basename(nombre_modelo)
    folder_modelos = os.path.join(os.path.dirname(__file__), "models")
    if not os.path.exists(folder_modelos):
        os.mkdir(folder_modelos)
    nombre_modelo = os.path.join(folder_modelos, nombre_modelo)

    modelo.save(nombre_modelo)
    print("Modelo guardado en %s" % nombre_modelo)

if __name__ == "__main__":
    run(50)