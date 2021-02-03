from flask import Flask, render_template, jsonify, url_for
app = Flask(__name__)

import paramiko, getpass, time, netifaces, re
from paramiko import SSHClient

# Command for the route table
route_table = 'show ip route\n'
# User Credentials
username = 'admin'
password = 'cisco'

routers = {}

# Retrieving the local gateway
gateway = netifaces.gateways()['default'][2][0]

# Max Length 
max_buffer = 65535

def clear_buffer(connection):
    if connection.recv_ready():
        return connection.recv(max_buffer)
""" This function returns back the wildcard of the specified mask """
def getWildCard(mask):
    numbers = [ bin(int(number))[2:] for number in mask.split('.')]
    bin_numbers = [ number if len(number)==8 else '0'*(8-len(number))+number for number in numbers]
    wildcard = []
    for bin_number in bin_numbers:
        not_bin_number = [] 
        for bit in bin_number:
            if bit == '0':
                not_bin_number.append('1')
            else:
                not_bin_number.append('0')
        wildcard.append( str( int(''.join(not_bin_number), 2) ) )
    return '.'.join(wildcard)

def getNetworkID(ip):
    numbers = ip.split('.')
    numbers[-1] = '0'
    return '.'.join(numbers)

def getNetworsRouter(router_prompt, routers):
    router_info = {}
    networks = [ network for network in routers[router_prompt].keys() ]
    masks = [ mask for mask in routers[router_prompt].values() ]
    for router in routers.keys():
        if router!= router_prompt:
            for network, mask in zip( networks, masks ):
                if network in routers[router].keys():
                    router_info[router] = [ network, getNetworkID(network) , mask, getWildCard(mask) ]
    return router_info

def getNetworksDirectlyConnected( routing_table ):
    routes = list( re.findall( 'C\s+([0-9.]+)', routing_table ) )
    masks  = list( re.findall( 'C\s+[0-9.]+/([0-9]+)', routing_table ) )
    return routes, { route.replace('252', '253') if route.endswith('.252') else route: '255.255.255.0' if mask == '24' else '255.255.255.252' for route, mask in list(zip(routes, masks)) }

def searchTopology( devices ):
    for device in devices:
        connection = SSHClient()
        connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        connection.connect(device, username=username, password=password, look_for_keys=False, allow_agent=False)
        new_connection = connection.invoke_shell()
        output = clear_buffer(new_connection)
        time.sleep(2)
        new_connection.send("terminal length 0\n")
        output = clear_buffer(new_connection)
        try:
            router = output.decode('utf-8')
        except:
            print('The router interface is down')
            new_connection.close()
            continue
        router = router[2:4]
        # If the router is already in the list of routers, close the ssh connection
        if router in routers:
            print(f'The router {router} is already visited')
            new_connection.close()
            continue
        # Retrieving the routing table
        new_connection.send(route_table)
        time.sleep(2)
        table = new_connection.recv(max_buffer).decode('utf-8')
        routes, routers[router] = getNetworksDirectlyConnected( table )
        # Filtering the obtained list
        dispositivos = [route.replace('252', '253') for route in routes if route.endswith('.252') ]
        for dispositivo in dispositivos:
            print(f'Obtaining the devices that are directly connected to this router: {dispositivo}')
            new_connection.send(f'ssh -l {username} {dispositivo} \n')
            time.sleep(2)
            new_connection.send(f'{password}\n')
            time.sleep(2) 
            new_connection.send(route_table)
            time.sleep(2)
            # Obtaining the routing table for every single router
            table = new_connection.recv(max_buffer).decode('utf-8')
            router =  table[-3] + table[-2]
            _, routers[router] = getNetworksDirectlyConnected( table )
            new_connection.send('exit\n')
            time.sleep(2)
        
        # Closing the ssh connection
        new_connection.close()

@app.route('/')
def getTopology():
  # Devices
  devices = [gateway]
  searchTopology( devices )
  # Generating the urls for every single interface in the topology
  urls = []
  for router in routers.keys():
      with app.test_request_context():
          urls.append( url_for('describeInterface', hostname=router) )
  return render_template('index.html', routers=routers, urls=urls)

@app.route('/interface/<hostname>')
def describeInterface(hostname):
    if  hostname == 'R4':
        print("Setting up the routing table for Router 4...")
        connection = SSHClient()
        connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        connection.connect( gateway, username=username, password=password, look_for_keys=False, allow_agent=False)
        new_connection = connection.invoke_shell()
        time.sleep(2)
        new_connection.send('terminal length 0\n')
        print(f'Obtaining the {hostname} router information\n')
        router_info = getNetworsRouter( hostname, routers)
        print(router_info)
        # Executing the commands for setting up the routing table
        new_connection.send('conf t\n')
        time.sleep(2)
        new_connection.send('router ospf 1\n')
        time.sleep(2)
        id_network_R3 = router_info['R3'][1]
        new_connection.send(f'network { id_network_R3 } 0.0.0.255 area 0\n')
        time.sleep(2)
        new_connection.send('redistribute rip metric 200 subnets\n')
        time.sleep(2)
        new_connection.send('redistribute static metric 200 subnets\n')
        time.sleep(2)
        new_connection.send('exit\n')
        time.sleep(2)
        new_connection.send('router rip\n')
        time.sleep(2)
        new_connection.send('version 2\n')
        time.sleep(2)
        new_connection.send('redistribute static\n')
        time.sleep(2)
        new_connection.send('redistribute ospf 1\n')
        time.sleep(2)
        new_connection.send('no auto-summary\n')
        time.sleep(2)
        id_network_R2 = router_info['R2'][1]
        new_connection.send(f'network {id_network_R2}\n')
        time.sleep(2)
        new_connection.send('exit\n')
        time.sleep(2)
        network_R1 = router_info['R1']
        new_connection.send(f'ip route 10.0.5.0 255.255.255.0 {network_R1[0]}\n')
        time.sleep(2)
        # Closing the ssh connection
        new_connection.close()

    return jsonify(Router=hostname, Devices_Directly_Connected=routers[hostname])

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

        
