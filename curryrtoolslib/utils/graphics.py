import numpy as np
import matplotlib.pyplot as plt

def mostrar_graf(historial):
    import matplotlib.pyplot as plt
    plt.plot(historial.history['accuracy'], label='Precisión')
    plt.plot(historial.history['loss'], label='Pérdida')
    plt.xlabel('Época')
    plt.ylabel('Precisión')
    plt.legend()
    plt.show()
         