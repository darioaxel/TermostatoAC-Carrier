# TermostatoAC-Carrier

[English](README.md) Version inglés

-----

**ÍNDICE**

- [TermostatoAC-Carrier](#termostatoac-carrier)
  - [Introducción](#introducción)
  - [Descripción del termostato](#descripción-del-termostato)
  - [Componentes a utilizar](#componentes-a-utilizar)
  - [Software](#software)
  - [Lecturas de datos](#lecturas-de-datos)

-----

## Introducción

Este proyecto pretende solucionar la falta de actualizaciones para el termostato de una conocida marca de aire acondicionado americana mediante su sustitución por un dispositivo compatible que, además, permita ampliar las opciones de programación, acceso remoto y una interfaz más moderna.

## Descripción del termostato

Este proyecto trata con el termostato **CRC2-NTC** de Carrier. Se trata de un termostato obsoleto que la propia empresa ya no provee.

![Termostato](./images/termostato.jpg)


Aún se pueden encontrar las instrucciones de instalación y para el usuario en internet. Adjunto dos enlaces para verlas:

[Manual de Instalación](https://www.manualslib.com/manual/2206657/Carrier-Crc2-Ntc.html)
[Manual de Usuario](https://www.manualslib.com/manual/2206660/Carrier-Crc2-Ntc.html) 

Dentro del manual de instalación podemos encontrar la siguiente imágen, que nos permite entender como tratar los tres elementos de conexión:

![Pins de conexión](./images/pins.png)

En este caso, nos encontramos con tan solo 3 pins de conexión:
 * **P**: para Power con 12v
 * **G**: para GND
 * **C**: para la emisión de datos 

El termostato emite cada X tiempo una serie de datos que son aquellos que queremos analizar para poder entender el funcionamiento del sistema. 

## Componentes a utilizar

## Software


## Lecturas de datos

A continuación se incluye una tabla en la que se indica, para cada uno de los estados del termostato, el fichero que incluye 4 lecturas completas del stream que se ha recibido el script.

| Estado del termostato | Ventilador | Temperatura | Fichero de lectura |
| --- | --- | --- | --- |
| Apagado | * | * | [Fichero](datos_hex_2024-08-23_17-21-54.txt) |
| Calor | 1 | 24º | [Fichero](datos_hex_2024-08-23_17-26-08.txt) |
| Calor | 2 | 24º | [Fichero](datos_hex_2024-08-23_17-27-53.txt) |
| Ventilador| 1 | - | [Fichero](datos_hex_2024-08-24_09-43-15.txt) |
