from pexpect import pxssh
from .models import Interfaces, Vlan
import re

def getVlanNUE( gateway ):
    ip_bytes     = gateway.split('.')
    vlan_number  = ip_bytes[2]
    ip_bytes[-1] = '0'
    vlan_network = '.'.join(ip_bytes)
    return vlan_number, vlan_network

def getVlanGateway( network ):
    ip_bytes     = network.split('.')
    ip_bytes[-1] = '1'
    gateway      = '.'.join(ip_bytes)
    return gateway


def vlanInformation( session ):
    print('The ssh session is working... ')
    vlan_command = 'show ip interface | include Internet address'
    
    # Getting all the vlan's ip
    session.sendline(vlan_command)
    session.expect('#')
    output_command = session.before.decode('utf-8')
    vlans = re.findall('is (\S+)', output_command)
    vlans_info = {}
    for vlan in vlans:
        vlan_gateway, mask = vlan.split('/')
        vlan_mask   = '255.255.255.0' if mask == '24' else 'Not Defined'
        vlan_number, vlan_network = getVlanNUE( vlan_gateway )
        # Getting all the interfaces bundled to a specific VLAN and their name
        vlan_interfaces_command = f'show vlan-switch id {vlan_number}'
        session.sendline(vlan_interfaces_command)
        session.expect('#')
        output_command = session.before.decode('utf-8')
        # print(output_command + '\n')
        vlan_name  = re.findall(f'{vlan_number}\s+(\w+)', output_command)[1]
        interfaces = [ interface.rstrip(',') for interface in re.findall(' (Fa\S+)', output_command) ]
        vlan_interfaces = list()
        if not interfaces:
            vlan_interfaces = 'Not assigned yet'
        else:
            for interface in interfaces:
                if int(interface.split('/')[-1]) >= 8:
                    vlan_interfaces.append(interface)
        
        vlans_info[vlan_number] = {
            'VLAN-name'      : vlan_name,
            'VLAN-gateway'   : vlan_gateway,
            'VLAN-mask'      : vlan_mask,
            'VLAN-number'    : vlan_number,
            'VLAN-network'   : vlan_network,
            'VLAN-interfaces': vlan_interfaces
        } 
    
    return vlans_info
    
def getDataVlan( session ):
    
    Interfaces.objects.all().delete()
    Vlan.objects.all().delete()
    
    vlan_info = vlanInformation( session )

    for vlan in vlan_info.keys():
        interfaces = vlan_info[vlan].get('VLAN-interfaces')
        if type(interfaces) is list:
            for interface in interfaces:
                # Creating the interfaces in the database
                Interfaces.objects.create(
                    name = interface
                )
    
    for vlan in vlan_info.keys():
        # Creating the Vlan instance in the database
        instance = Vlan.objects.create(
            name       = vlan_info[vlan].get('VLAN-name'),
            network    = vlan_info[vlan].get('VLAN-network'),
            mask       = vlan_info[vlan].get('VLAN-mask'), 
            gateway    = vlan_info[vlan].get('VLAN-gateway'),
            number     = vlan_info[vlan].get('VLAN-number')
        )
        interfaces = vlan_info[vlan].get('VLAN-interfaces')
        print(f'Vlan interfaces found: {interfaces}')
        
        if type(interfaces) is list:
            vlan_interfaces = Interfaces.objects.filter(
                # Getting all the interfaces that matches with the given list 'interfaces'
                name__in = interfaces
            )
            # Adding the corresponding interfaces for this instance
            instance.interfaces.add( *vlan_interfaces )
    return 1

def createVlanGNS3( session, vlan_number, vlan_name, vlan_gateway, vlan_mask ):
    # Creating the Vlan in the swith database 
    vlan_commands = [ 
        'vlan database', 
        f'vlan {vlan_number} name {vlan_name}', 
        'exit', 
        'conf t', # Setting up the interface for the vlan 
        f'int vlan {vlan_number}',
        f'ip add {vlan_gateway} {vlan_mask}',
        'no shutdown', 
        'end'
    ]

    for vlan_command in vlan_commands:
        session.sendline(vlan_command)
        session.expect('#')

def createSubInterfaz( session, vlan_number, vlan_gateway, vlan_mask ):
    # Creating the subinterfaz in the Router 
    router_commands = [ 
        'conf t', 
        f'interface Fa0/0.{vlan_number}', 
        f'encapsulation dot1Q {vlan_number}',
        f'ip add {vlan_gateway} {vlan_mask}', 
        'end'
    ]

    for router_command in router_commands:
        session.sendline(router_command)
        session.expect('#')

def deleteSubInterfaz( session, vlan_number ):
    # Creating the subinterfaz in the Router 
    router_commands = [ 
        'conf t', 
        f'no interface Fa0/0.{vlan_number}', 
        'end'
    ]

    for router_command in router_commands:
        session.sendline(router_command)
        session.expect('#')

def deleteVlanGNS3( session, vlan_number ):
    # Creating the Vlan in the swith database 
    vlan_commands = [ 
        'vlan database', 
        f'no vlan {vlan_number}', 
        'exit',
        'conf t',
        f'no interface vlan {vlan_number}',
        'exit'
    ]

    for vlan_command in vlan_commands:
        session.sendline(vlan_command)
        session.expect('#')


def assignInterfacesVlan( session, command_interfaces, vlan_number='1' ):
 
    for command_interface in command_interfaces:
        vlan_commands = [
            'conf t',
            command_interface,
            'switchport mode access',
            f'switchport access vlan {vlan_number}',
            'end'
        ]
        for vlan_command in vlan_commands:
            session.sendline(vlan_command)
            session.expect('#')
