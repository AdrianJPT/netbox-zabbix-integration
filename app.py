from flask import Flask, jsonify, request,redirect
import json
import requests
import traceback
# RESOLVE IP ADDRESS
import ipaddress 
import lib_zabbix as za

from credentials import *
import nb_local_lib as ntbx


# ZABBIXs
from pyzabbix import ZabbixAPI, ZabbixAPIException



app = Flask(__name__)

ZABBIX_SERVER = Zabbix_Url

zapi = ZabbixAPI(ZABBIX_SERVER)
zapi.login(Zabbix_User, Zabbix_Password)

zabbix_url = str(Zabbix_Url)
zabbix_token = Zabbix_Token


@app.route('/create', methods=['POST'])
def zabbix_host_create():

    ## LEER REQUEST DE NETBOX
    if(request.data):
        reading_post = request.get_json()
        nb_device_name = reading_post['data']['name']
        nb_site_name = reading_post['data']['site']['name']
    
        
        # HOSTGROUP - SITES | 
        try:
            # HOSTGROUP - SITES | TEMPLATE - PLATFORM                
            nb_platform = reading_post['data']['platform']['name']
            print(nb_platform)
            template = zapi.template.get(filter={'host': nb_platform})
            
            find_hostgroup = zapi.hostgroup.get(filter={"name": nb_site_name},output=['groupid'])
            # Validate HOSTGROPS
            if(len(find_hostgroup) != 0):
                zapi.host.create(
                
                host=nb_device_name,
                interfaces=[{
                    'type': 1,
                    'main': 1,
                    'useip': 0,
                    'ip': '',
                    'dns': 'UPDATE_IP',
                    'port': '9999'
                }],
                groups=[{'groupid': find_hostgroup[0]['groupid']}],
                templates=[{'templateid': template[0]['templateid']}]
                )
                
                print(f"ZABBIX | SUCCESS | Created ({nb_device_name})")
                
            else:
                print(f'HostGroup {nb_site_name} not found in ZABBIX')
                
            # HOSTGROUP - SITES 
             
        except :
            print("NO PLATFORM SELECTED")
            
        
        try:
                find_hostgroup = zapi.hostgroup.get(filter={"name": nb_site_name}, output=['groupid'])
                if(len(find_hostgroup) != 0):
                    zapi.host.create(
                        
                        host = nb_device_name,
                        interfaces=[{
                            'type': 1,
                            'main': 1,
                            'useip': 0,
                            'ip': '',
                            'dns': 'UPDATE_IP',
                            'port': '9999'
                        }],
                        groups = [{"groupid": find_hostgroup[0]['groupid']}])
                    
                    print(f"ZABBIX | SUCCESS | Creado ({nb_device_name})")
                else:
                    print(f'HostGroup {nb_site_name} not found in ZABBIX')
                    
        except ZabbixAPIException as e:
            print("DEVICE NOT CREATED")
            
    return jsonify({"msg":"Correct"})

@app.route('/update', methods=['POST'])
def zabbix_host_update():
    if(request.data):

        # LEER NOMBRE DEL DEVICE NETBOX
        reading_post = request.get_json()
        
        # Mandatory
        nb_device_name = reading_post['data']['name']
        nb_device_name = reading_post['data']['name']
        nb_device_role = ""
        # OPTIONAL
        
        
        # TRAER LA INFO DE ZABBIX
        hosts_zabbix = zapi.host.get(output=["hostid", "name", "interfaces"], filter={"name": nb_device_name}, selectInterfaces=["interfaceid", "ip", "dns"], selectGroups=["groupid"])
        
        # Update Platform 
        za.update_Template_Host(nb_device_name, reading_post['snapshots']['prechange']['platform'], reading_post['snapshots']['postchange']['platform'])
        
        # Update Site
        
        
        # Change name
        if(reading_post['snapshots']['prechange']['name'] != nb_device_name):
            before_nb_device_name = reading_post['snapshots']['prechange']['name']
            
            za.update_Hostname(before_nb_device_name, nb_device_name)
        
        # Add and IP
        
        # Remove and IP 
    
        # ADD IP  
        
        
        # SI YA EXISTIA EL NB DEVICE Y EN ZABBIX NO, SE CREARA UNO
        if len(hosts_zabbix) != 0:
            # SI EXISTE EN ZABBIX
            zab_host_id = hosts_zabbix[0]['hostid']     
            # IDENTIFICAR SI EXISTE ALGUNA INTERFAZ
            zab_host_int = hosts_zabbix[0]['interfaces']

            if len(zab_host_int) != 0:
                print(f'Interface device exists')
                # OBTNER EL ID DE LA INTERFAZ
                zab_host_int_id = hosts_zabbix[0]['interfaces'][0]['interfaceid']

                # VALIDAR SI SE ESTA QUITANDO O ACTUALIZANDO LA IP
                if reading_post['data']['primary_ip'] != None:
                    print("Updating interface")

                    request_nb_primary_ip = reading_post['data']['primary_ip']['address']
                    convert_to_ip = ipaddress.IPv4Interface(request_nb_primary_ip)
                    nb_primary_ip = str(convert_to_ip.ip)

                    zapi.hostinterface.update(interfaceid=zab_host_int_id, ip=nb_primary_ip)

                    print(f"ZABBIX | SUCCESS | IP updated: ({nb_primary_ip}), Interface id: ({zab_host_int_id})")

                else:
                    # BORRANDO INTERFAZ ZAbbix HOST
                    
                    requests.put(zabbix_url, json={
                            "jsonrpc": "2.0",
                            "method": "hostinterface.delete",
                            "params": [
                                zab_host_int_id
                            ],
                            "auth": zabbix_token,
                            "id": 1})
                    print(f"ZABBIX | SUCCESS | Remove IP from host({nb_device_name})")
            else:           
            # NO TIENE INTERFAZ CREAR UNA Y ASOCIAR UNA IP
                try:
                    # QUITAR LA MASK del CIDR, VALIDAR LA IP EN EL REQUEST Y ACTUALIZAR
                    request_nb_primary_ip = reading_post['data']['primary_ip']['address']
                    convert_to_ip = ipaddress.IPv4Interface(request_nb_primary_ip)
                    nb_primary_ip = str(convert_to_ip.ip)
                    
                    # AGREGAR LA INTERFAZ Y IP AL ZABBIX HOST
                    print("ooooooooooooooooooooooooooo_1") #AQUI NO ES
                    zapi.host.update(hostid = zab_host_id, name = nb_device_name, interfaces = [{
                                                    
                                                    "type": 1,
                                                    "main": 1,
                                                    "useip": 1, 
                                                    "ip": nb_primary_ip,
                                                    "dns": "",
                                                    "port": "10050"
                                                }]
                                                ,
                                                groups = [
                                                    {
                                                        "groupid": "1"
                                                    }
                                                ]
                                                )
                    print(f"ZABBIX | SUCCESS | IP updated ({nb_primary_ip}) in Zabbix Server")

                except Exception as e:
                    print("ZABBIX | WARNING | ", e.__class__, f"ocurrio para ({nb_device_name}).")
                    print(f"ZABBIX | SUCCESS | IP: ({nb_primary_ip}) ")
                    print(f"ZABBIX | WARNING | IP not found in netbox")
        
        #CUANDO NO EXITE EN ZABBIX PERO EL NETBOX SÍ
        else:

            # VER SI CREAR CON IP O SIN IP
            if reading_post['data']['primary_ip'] != None: 
                # CREAR CON IP
                print("Creating IP")
                request_nb_primary_ip = reading_post['data']['primary_ip']['address']
                convert_to_ip = ipaddress.IPv4Interface(request_nb_primary_ip)
                nb_primary_ip = str(convert_to_ip.ip)            

                print("ooooooooooooooooooooooooooo_2") #AQUI NO ES
                zapi.host.create(host = nb_device_name,
                    groups = [
                                {
                                    "groupid": "1"
                                }
                            ],
                    interfaces = [{
                                                
                        "type": 1,
                        "main": 1,
                        "useip": 1,
                        "ip": nb_primary_ip,
                        "dns": "",
                        "port": "10050"
                    }])

                print(f"ZABBIX | SUCCESS | Host ({nb_device_name}) created with ip ({nb_primary_ip})")

            else:
                # CREAR SOLAMENTE EL HOST SIN IP
                print("CREAND SIN IP")
                zapi.host.create(host = nb_device_name,
                    groups = [
                                {
                                    "groupid": "1"
                                }
                            ]
                            )
                
                print(f"ZABBIX | SUCCESS | Se creo el host ({nb_device_name}) , porque no exitia en Zabbix Server")


        
    return jsonify({"msg":"Correct"})    
    
@app.route('/delete', methods=['DELETE'])
def zabbix_host_delete():

    ## LEER REQUEST DE NETBOX
    if(request.data):
        reading_post = request.get_json()
        nb_device_name = reading_post['data']['name']


        hosts_zabbix = zapi.host.get(output=["hostid", "name", "interfaces"], filter={"name": nb_device_name}, selectInterfaces=["interfaceid", "ip", "dns"], selectGroups=["groupid"])

        zab_host_id = hosts_zabbix[0]['hostid']     # IDENTIFICAR AL HOST POR EL ID Y EL NETBOX NAME
        
        print("")
        print(f"ZABBIX | Eliminando ... ({nb_device_name})")

        try:
            zapi.host.delete(hostid = zab_host_id)

            print(f"ZABBIX | SUCCESS | Eliminado ... ({nb_device_name}) ")

        except Exception as e:
            # ESTO SE EJECUTA SI YA EXISTE EN ZABBIX
            print("ZABBIX | ERROR | ", e.__class__, f"ocurrio para ({nb_device_name}).")
            print(f"ZABBIX | SUCCESS | ({nb_device_name}) Device no existia en Zabbix, Pero se creo Correctamente")

    return jsonify({"msg": "Correct"})


if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=5000)
