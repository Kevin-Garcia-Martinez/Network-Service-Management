import paramiko, getpass, time, netifaces, re
from pexpect import pxssh
from orderedset import OrderedSet
from graphviz import Digraph

def findHostNames( routers ):
    router_interfaces = { }
    for router in routers:
        interfacesFA = routers[router].get('router_interfaces')
        router_interfaces[router] = [ interfacesFA[interfaceFA].get('ip') for interfaceFA in interfacesFA ]

    for device in routers:
        hostnames = []
        # Retrieving all the neighbours addresses for this device
        addresses = routers[device].get('neighbours_addresses')
        for address in addresses:
            for router, interfaces in router_interfaces.items():
                # If the router is different from the target device
                if device != router:
                    if address in interfaces:
                        hostnames.append(router)
                        break
        routers[device]['neighbours_hostname'] = hostnames

def searchTopology():
    # Retrieving the local gateway
    gateway = netifaces.gateways()['default'][2][0]
    # Credentials
    username = 'cisco'
    password = 'cisco'
    # Commands
    route_table       = 'show ip route'
    router_id         = 'show ip ospf interface | include Router ID'
    router_interfaces = 'show ip ospf interface brief'
    router_hostname   = 'sh running-config brief | include hostname'
    router_LAN        = 'sh ip route | include /24 is directly'
    # Variables
    routers         = dict()
    # neighbours      = dict()
    routers_information = dict()
    devices = [gateway]
    routers_interfaces_ip = []

    for device in devices:
        session = pxssh.pxssh()
        session.login(device, username, password, auto_prompt_reset=False)
        # Retrieving the hostname
        session.sendline(router_hostname)
        session.expect('#')
        # print(f'Comando anterior al prompt: {session.before}')
        hostname = session.before.decode('utf-8')
        router = re.findall('hostname (R[0-9])', hostname)[0]
        # If the router is already in the list of routers, close the ssh connection
        if router in routers:
            print(f'The router {router} is already visited')
            session.logout()
            continue
        print(f'Router hostname: {router}')
        # Retrieving the Router ID
        session.PROMPT = b'1' # Reiniciamos el prompt
        session.sendline(router_id)
        session.expect('#')
        #print(f'Comando anterior al prompt: {session.before}')
        _id = session.before.decode('utf-8')
        r_id =  re.findall( 'Router ID ([0-9.]+)', _id )[0]
        print(f'{router} ID: {r_id}')
        # Retrieving the Router Information
        session.PROMPT = b'1' # Reiniciamos el prompt
        session.sendline(router_interfaces)
        session.expect('#')
        print(f'Getting all the interfaces for the router: {router}')
        #print(f'Comando anterior al prompt: {session.before}')
        info_router_interfaces = session.before.decode('utf-8')
        interfaces      = re.findall( 'Fa(\S+)', info_router_interfaces )
        ip_interfaces   = re.findall( '([0-9.]+)/[2-9]+', info_router_interfaces )
        mask_interfaces = [ mask for mask in re.findall( '/([0-9]+)', info_router_interfaces) if int(mask)>=8 ]
        
        # Retreiving the routing table
        session.PROMPT = b'1' # Reiniciamos el prompt
        session.sendline(route_table)
        session.expect('#')
        print(f'Getting the route table for the router: {router}')
        #print(f'Comando anterior al prompt: {session.before}')
        table = session.before.decode('utf-8')
        addresses = list( OrderedSet( re.findall( 'via ([0-9.]+),', table ) ) )
        routers[router] = addresses
        # Retreiving the Router LAN
        session.PROMPT = b'1' # Reiniciamos el prompt
        session.sendline(router_LAN)
        session.expect('#')
        print(f'Getting the LAN for the router: {router}')
        #print(f'Comando anterior al prompt: {session.before}')
        command_lan = session.before.decode('utf-8')
        lan = re.findall('([0-9.]+)/24', command_lan)[0]
        # Adding new devices to search
        routers_interfaces_ip.extend( ip_interfaces )
        # Deleting duplicate and already visited addresses
        devices.extend( add for add in addresses if add not in routers_interfaces_ip )
        # Closing the ssh connection
        session.logout()

        # Gathering all the obtained data 
        data_interfaces = dict()

        for interface, address, mask in zip(interfaces, ip_interfaces, mask_interfaces):
            data_interfaces[ 'FastEthernet'+ interface ] = {
                'ip'   : address,
                'mask' : '255.255.255.0' if mask == '24' else '255.255.255.252' 
            }

        routers_information[router] = {
            'neighbours_addresses': routers[router],
            'router_id'           : r_id,
            'router_LAN'          : lan,
            'router_hostname'     : router,
            'router_interfaces'   : data_interfaces
        }

    print('Finding all the hostnames for every single Router')
    findHostNames( routers_information )
    return routers_information

routers = searchTopology()

def getNetworkID(address):
    network = address.split('.')
    last_byte =  int(network[-1])
    # Even
    if last_byte%2 == 0:
        network[-1] = str(last_byte-2)
    # Odd
    else:
        network[-1] = str(last_byte-1)
    
    return '.'.join(network)

def drawTopologyDiagram(routers):
    diagram = Digraph (comment='Network')
    for router in routers:
        diagram.attr('node', shape='doublecircle', fillcolor='blue:cyan', style='filled')        
        diagram.node(router)
        # Adding the LAN for this router
        lan = routers[router].get('router_LAN')
        diagram.attr('node', shape='box', fillcolor='red:pink', style='filled')
        # Creating the edge with the Router and their LAN
        diagram.edge( router, lan, label = 'LAN' )
        
        neighbours_addresses = routers[router].get('neighbours_addresses')
        neighbours_hostnames = routers[router].get('neighbours_hostname')
        # Obtaining all the interfaces
        interfaces_and_networks = []
        # Router interfaces
        dict_interfaces = routers[router].get('router_interfaces')
        # Looking in every single interface of the router
        for interface in dict_interfaces.keys():
            int_ip   = dict_interfaces[interface].get('ip') 
            int_mask = '24' if dict_interfaces[interface].get('mask') == '255.255.255.0' else '30'
            int_name = 'Fa'+ interface[-3] + interface[-2] + interface[-1] 
            # Looking in every single address of the router's neighbour a match with the network id
            for address, hostname in zip(neighbours_addresses,neighbours_hostnames):
                if getNetworkID(address) == getNetworkID(int_ip):
                    interfaces_and_networks.append( ( int_name, int_ip.split('.')[-1], int_mask, getNetworkID(address), hostname, router ) )                  
        
        for info in interfaces_and_networks:
            # Creating the node 
            diagram.attr('node', shape='box', fillcolor='red:yellow', style='filled')
            # Retrieveing the network id
            diagram.node( info[3] )
            # Creating the first edge
            diagram.edge( info[5], info[3] , label = info[0]+'\n'+'.'+info[1]+'/'+info[2] )
            # Creating the node for the neighbour
            diagram.attr('node', shape='doublecircle', fillcolor='blue:cyan', style='filled')        
            diagram.node( info[4] )
            # Creating the second edge
            diagram.edge( info[3], info[4] )

    diagram.render(filename='topology', format='png')


drawTopologyDiagram( routers )
