# TermostatoAC-Carrier

[Español](README_es.md) Spanish Version

-----

**INDEX**

- [TermostatoAC-Carrier](#termostatoac-carrier)
  - [Introduction](#introduction)
  - [Thermostat Description](#thermostat-description)
  - [Components to Use](#components-to-use)
  - [Software](#software)
  - [Data Readings](#data-readings)

-----

## Introduction

This project aims to address the lack of updates for the thermostat of a well-known American air conditioning brand by replacing it with a compatible device that also expands programming options, enables remote access, and provides a more modern interface.

## Thermostat Description

This project deals with the **CRC2-NTC** thermostat from Carrier. It is an obsolete thermostat that the company no longer provides.

![Thermostat](./images/termostato.jpg)

Installation and user manuals can still be found online. Here are two links to view them:

[Installation Manual](https://www.manualslib.com/manual/2206657/Carrier-Crc2-Ntc.html)  
[User Manual](https://www.manualslib.com/manual/2206660/Carrier-Crc2-Ntc.html)

Within the installation manual, we can find the following image, which helps us understand how to handle the three connection elements:

![Connection Pins](./images/pins.png)

In this case, we only have 3 connection pins:
 * **P**: for Power with 12v
 * **G**: for GND
 * **C**: for data transmission

The thermostat emits a series of data at regular intervals, which we want to analyze to understand how the system operates.

## Components to Use
To perform thermostat readings, I use the following adapter:

![RS485_adapter](./images/USB_R485_12v_adapter.png)

I bought it on Aliexpress from this store: [USB to RS485 Adapter](https://es.aliexpress.com/item/1005006111904749.html?spm=a2g0o.order_list.order_list_main.85.4fd6194dqfCvY1&gatewayAdapt=glo2esp)

## Software

## Data Readings

Below is a table indicating, for each thermostat state, the file that includes 4 complete readings of the stream received by the script.

| Thermostat State | Fan | Temperature | Reading File |
| --- | --- | --- | --- |
| Off | * | * | [File](datos_hex_2024-08-23_17-21-54.txt) |
| Heat | 1 | 24º | [File](datos_hex_2024-08-23_17-26-08.txt) |
| Heat | 2 | 24º | [File](datos_hex_2024-08-23_17-27-53.txt) |
| Fan | 1 | - | [File](datos_hex_2024-08-24_09-43-15.txt) |
