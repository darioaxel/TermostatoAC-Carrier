import numpy as np
import matplotlib.pyplot as plt

def genera_predicciones(datos, modelo, nombre_clases):
    for trama, etiquetas in datos.take(1):
        trama = trama.numpy()
        etiquetas = etiquetas.numpy()
        predicciones = modelo.predict(trama)

    filas = 5
    columnas = 5
    num_imagenes = filas*columnas
    print("NUM IMAGENES", num_imagenes)
    plt.figure(figsize=(2*2*columnas, 2*filas))
    for i in range(num_imagenes):
        print("i", i)
        plt.subplot(filas, 2*columnas, 2*i+1)
        graficar_trama(i, predicciones, etiquetas, trama, nombre_clases)
        plt.subplot(filas, 2*columnas, 2*i+2)
        graficar_valor_array(i, predicciones, etiquetas)
    plt.legend()
    plt.show()

def graficar_trama(i, predicciones, etiquetas_reales, datos, nombre_clases):
    prediccion, etiqueta_real, dato = predicciones[i], etiquetas_reales[i], datos[i]
    plt.grid(False)
    plt.xticks([])
    plt.yticks([])

    plt.imshow(dato[...,0], cmap=plt.cm.binary)
    etiqueta_prediccion = np.argmax(prediccion)

    color = 'blue' if etiqueta_prediccion == etiqueta_real else 'red'

    plt.xlabel("{} {:2.0f}% ({})".format(
        nombre_clases[etiqueta_prediccion],
        100*np.max(prediccion),
        nombre_clases[etiqueta_real]),
        color=color)
    
def graficar_valor_array(i, predicciones, etiquetas):
    prediccion, etiqueta_real = predicciones[i], etiquetas[i]
    plt.grid(False)
    plt.xticks(range(10))
    plt.yticks([])
    grafica = plt.bar(range(10), prediccion, color="#777777")
    plt.ylim([0, 1])
    etiqueta_prediccion = np.argmax(prediccion)

    grafica[etiqueta_prediccion].set_color('red')
    grafica[etiqueta_real].set_color('blue')

def mostrar_graf(historial):
    import matplotlib.pyplot as plt
    plt.plot(historial.history['accuracy'], label='Precisión')
    plt.plot(historial.history['loss'], label='Pérdida')
    plt.xlabel('Época')
    plt.ylabel('Precisión')
    plt.legend()
    plt.show()
