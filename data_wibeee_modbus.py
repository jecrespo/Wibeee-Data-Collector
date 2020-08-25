#!/usr/bin/python3
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------- #
# Uso de WiBeee como sistema de recolección de datos de circuitos electricos mediante modbus
# Tarea programada en Raspberry Pi mediante cron cada 1 minuto
# Guarda datos en BBDD MySQL llamada WiBeee en Raspberry Pi
#
# Ficha Técnica: http://circutor.es/docs/FT_Wi-Beee_SP.pdf
# Manual: http://docs.circutor.com/docs/M064B01-01.pdf
#
# ¡¡IMPORTANTE!! Modbus Map cambia en la versión 4.4.70, por lo que los scripts deben tenerlo en cuenta.
# Ver directorio docs con los Modbus Maps
# ModBUS TCP Specification v7 for Wibeee family
# From v3.X.570 firmware version
# From v4.4.480 / v5.4.480 firmware version
#
# Parámetros wibeee monofásico (11 parámetros):
# V1 - Tensión fase L1, I1 - Corriente L1, frec1 - Frecuencia L1, frect - Frecuencia Total
# pac1 - Potencia Activa L1, preac1 - Potencia Reactiva L1, pap1 - Potencia Aparente L1,
# fp1 - Factor de potencia L1,
# eac1- Energía activa L1, ereacind1 - Energía reactiva inductiva L1, ereaccap1 - Energía reactiva capacitiva L1
# --------------------------------------------------------------------------- # 

# --------------------------------------------------------------------------- # 
# configure the client logging for debug purposes
# --------------------------------------------------------------------------- # 
import logging
logging.basicConfig()
log = logging.getLogger()
#log.setLevel(logging.DEBUG)

# --------------------------------------------------------------------------- # 
# configure BBDD
# instalar como administrador: pip install mysql-connector-python
# --------------------------------------------------------------------------- # 
import mysql.connector as my_dbapi

# --------------------------------------------------------------------------- # 
# Instalar pymodbus: pip install pymodbus
# get data from modbus
# --------------------------------------------------------------------------- #
from pymodbus.client.sync import ModbusTcpClient

#para conversion de varios bytes en entero de los valores de modbus
import struct

# pueden añadirse tantos wibeee como se quiera
monitores_energia = {'consumo casa':{'ip':'192.168.1.2','V1':0,'I1':0,'frec1':0,'frect':0,
	'pac1':0,'preac1':0,'pap1':0,'fp1':0,'eac1':0,'ereacind1':0,'ereaccap1':0}}
	
modbus_registers = {'V1':0x00,'I1':0x03,'frec1':0x06,'frect':0x09,
	'pac1':0x0a,'preac1':0x0e,'pap1':0x12,'fp1':0x16,'eac1':0x1a,'ereacind1':0x22,'ereaccap1':0x2a}
    
#version dos del modbus mapping a partir de la versión 4.4.70
modbus_registers_V2 = {'V1':0x3a,'I1':0x30,'frec1':0x3e,'frect':0x41,
	'pac1':0x00,'preac1':0x08,'pap1':0x10,'fp1':0x42,'eac1':0x18,'ereacind1':0x20,'ereaccap1':0x28}

#los valores de energía usan dos valores y el resto uno
modbus_len = {'V1':1,'I1':1,'frec1':1,'frect':1,
	'pac1':1,'preac1':1,'pap1':1,'fp1':1,'eac1':2,'ereacind1':2,'ereaccap1':2}

#version dos del modbus mapping a partir de la versión 4.4.70
modbus_len_V2 = {'V1':1,'I1':2,'frec1':1,'frect':1,
	'pac1':2,'preac1':2,'pap1':2,'fp1':1,'eac1':2,'ereacind1':2,'ereaccap1':2}

#potencias en kW, kVar y kVA y energías en kWh, kVarh
modbus_multiplicador = {'V1':10,'I1':10,'frec1':10,'frect':10,'pac1':100,'preac1':100,
	'pap1':100,'fp1':100,'eac1':1,'ereacind1':1,'ereaccap1':1}

#version dos del modbus mapping a partir de la versión 4.4.70    
modbus_multiplicador_V2 = {'V1':100,'I1':100,'frec1':100,'frect':100,'pac1':1000,'preac1':1000,
	'pap1':1000,'fp1':100,'eac1':100,'ereacind1':100,'ereaccap1':100}

# Consulta monitores modelo
for monitor in monitores_energia:
    try: 
        client = ModbusTcpClient(monitores_energia[monitor]['ip'], port=502, timeout=10)
        client.connect()
        log.debug("Reading Registers")
        for medida, registro in modbus_registers.items():
            read = client.read_holding_registers(registro, modbus_len[medida])
            if modbus_len[medida] == 2:
                dato = struct.pack("<H",read.registers[0]) #primer registro 
                dato2 = struct.pack("<H",read.registers[1]) #segundo registro
                valor = struct.unpack("<i",dato+dato2) #al estar en little endian van en el orden
                #print(valor[0])
                monitores_energia[monitor][medida] = valor[0]/modbus_multiplicador[medida]
            else:
                dato = struct.pack("<H",read.registers[0]) #primer registro
                valor = struct.unpack("<h",dato)
                monitores_energia[monitor][medida] = valor[0]/modbus_multiplicador[medida]
            print(monitor + "--> " + medida + " : " + str(monitores_energia[monitor][medida]))
        client.close()
    except:
        print("Error en monitor " + monitor)

# --------------------------------------------------------------------------- # 
# BBDD wibeee
# Tablas: una tabla con el nombre del monitor por cada wibeee
#
# Crear tabla:
# ¿poner SQL de creación de la tabla por cada wibeee?
# --------------------------------------------------------------------------- # 

cnx_my = my_dbapi.connect(user='usuario', password='password', host='localhost', database='WiBeee')
cursor_my = cnx_my.cursor()

for monitor in monitores_energia:
        query_my = "INSERT INTO " + monitor + " (V1,I1,frec1,frect,pac1,preac1,pap1,fp1,eac1,ereacind1,ereaccap1) VALUES ('" +\
        str(monitores_energia[monitor]['V1']) + "," + str(monitores_energia[monitor]['I1']) + "," + str(monitores_energia[monitor]['frec1']) + "," +\
        str(monitores_energia[monitor]['frect']) + "," + str(monitores_energia[monitor]['pac1']) + "," + str(monitores_energia[monitor]['preac1']) + "," +\
        str(monitores_energia[monitor]['pap1']) + "," + str(monitores_energia[monitor]['fp1']) + "," + str(monitores_energia[monitor]['eac1']) + "," +\
        str(monitores_energia[monitor]['ereacind1']) + "," + str(monitores_energia[monitor]['ereaccap1']) + ")"
        cursor_my.execute(query_my)
        cnx_my.commit()

cnx_my.close()