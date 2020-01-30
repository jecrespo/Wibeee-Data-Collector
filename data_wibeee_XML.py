#!/usr/bin/python3
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------- #
# Uso de WiBeee como sistema de recolección de datos de circuitos electricos mediante XML HTTP
# Tarea programada en Raspberry Pi mediante cron cada 1 minuto
# Guarda datos en BBDD influxDB llamada WiBeee en Raspberry Pi
# para luego visualizar los datos en grafana también instalado en Raspberry Pi
#
# Ficha Técnica: http://circutor.es/docs/FT_Wi-Beee_SP.pdf
# Manual: http://docs.circutor.com/docs/M064B01-01.pdf

# Parámetros wibeee monofásico (11 parámetros):
# V1 - Tensión fase L1 (vrms1), I1 - Corriente L1 (irms1), frec1 - Frecuencia L1 (frec1),
# pac1 - Potencia Activa L1 (pac1), preac1 - Potencia Reactiva L1 (preac1), pap1 - Potencia Aparente L1 (pap1),
# fp1 - Factor de potencia L1 (fpot1),
# eac1- Energía activa L1 (eac1), ereacind1 - Energía reactiva inductiva L1 (ereactl1), ereaccap1 - Energía reactiva capacitiva L1 (ereactc1)
# --------------------------------------------------------------------------- # 

# --------------------------------------------------------------------------- # 
# Uso acceso por XML mediante peticiones GET
# instalar como administrador: pip install requests
# --------------------------------------------------------------------------- # 
import requests
import xml.etree.ElementTree as ET

# --------------------------------------------------------------------------- # 
# configure BBDD
# instalar como administrador: pip install influxdb
# cliente python: https://github.com/influxdata/influxdb-python y https://www.influxdata.com/blog/getting-started-python-influxdb/
# --------------------------------------------------------------------------- # 
from influxdb import InfluxDBClient

monitores_energia = {'consumo casa':{'ip':'192.168.1.2','data':{}}}

parametros_guardar = ['vrms1','irms1','freq1','pac1','pap1','preac1',\
                      'fpot1','eac1','ereactl1','ereactc1']

# Consulta monitores modelo
for monitor in monitores_energia:
        url = "http://" + monitores_energia[monitor]['ip'] + "/services/user/values.xml"
        querystring = {"id":monitor} #para saber el id llamar a http://192.168.1.2/services/user/devices.xml
        response = requests.request("GET", url, params=querystring)
        #print(response.text)
        root = ET.fromstring(response.text)
        for elem in root.iter('variable'):
                for item in elem:
                        if item.tag == 'id':
                               parametro = item.text
                        if item.tag == 'value':
                                valor = item.text
                monitores_energia[monitor]['data'][parametro]=valor

#muestro todos los datos
for monitor in monitores_energia:
	print("Número de parámetros recogidos: {}".format(len(monitores_energia[monitor]['data'].keys()))) #numero de parámetros
    print ("Monitor:",monitor)
    print ("IP:",monitores_energia[monitor]['ip'])
    print("Data:")
    for param in monitores_energia[monitor]['data']:
        print ('\t',param,':',monitores_energia[monitor]['data'][param])

# --------------------------------------------------------------------------- # 
# BBDD InfluxDB en localhost
# BBDD: wibeee
# measurement (tabla): data
# uso el tag monitor para filtrar por monitor
# Crear la BBDD en influxdb con el comando: CREATE DATABASE wibeee
# --------------------------------------------------------------------------- # 

for monitor in monitores_energia:
        datos_guardar = {}
        for p in parametros_guardar:
                print(p,monitores_energia[monitor]['data'][p])
                datos_guardar[p]=monitores_energia[monitor]['data'][p]
        datos = [{"measurement":"data","tags":{"monitor":monitor},"fields":datos_guardar}]

dbClient = InfluxDBClient('localhost', 8086, 'root', 'root', 'wibeee')
dbClient.write_points(datos)

# Query the IPs from logins have been made
Records = dbClient.query('select * from data;')
# Print the time series query results
print("resultado:",Records)

# --------------------------------------------------------------------------- # 
# Guardo datos en Fiware llamado a iotagent ultralight
# --------------------------------------------------------------------------- # 

url = "http://127.0.0.1:7896/iot/d?k=4jggokgpepnvsb2uvd59oz&i=wibee1.casa"

payload = "v1|"+monitores_energia['consumo casa']['data']['vrms1']+"|\
v2|"+monitores_energia['consumo casa']['data']['vrms2']+"|\
v3|"+monitores_energia['consumo casa']['data']['vrms3']+"|\
i1|"+monitores_energia['consumo casa']['data']['irms1']+"|\
i2|"+monitores_energia['consumo casa']['data']['irms2']+"|\
i3|"+monitores_energia['consumo casa']['data']['irms3']+"|\
p1|"+monitores_energia['consumo casa']['data']['pac1']+"|\
p2|"+monitores_energia['consumo casa']['data']['pac2']+"|\
p3|"+monitores_energia['consumo casa']['data']['pac3']+"|\
potencia_activa_total|"+monitores_energia['consumo casa']['data']['pact']+"|\
potencia_reactiva_total|"+monitores_energia['consumo casa']['data']['preact']+"|\
factor_potencia|"+monitores_energia['consumo casa']['data']['fpott']+"\r"

headers = {
  'Content-Type': 'text/plain'
}

response = requests.request("POST", url, headers=headers, data = payload)
print(response.text.encode('utf8'))
