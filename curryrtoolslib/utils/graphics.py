import numpy as np
import matplotlib.pyplot as plt

def mostrar_graf(historial):
    import matplotlib.pyplot as plt
    plt.plot(historial.history['accuracy'], label='Precisión')
    plt.plot(resolve_loss(historial.history['accuracy']), label='Pérdida')
    plt.xlabel('Época')
    plt.ylabel('Precisión')
    plt.legend()
    plt.show()

def resolve_loss(loss):
    return [1 - x for x in loss]
         