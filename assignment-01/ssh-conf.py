import pexpect

devices = {
    'iosv-1': {'prompt': 'iosv-1#', 'ip': '192.168.122.65'},
    'iosv-2': {'prompt': 'iosv-2#', 'ip': '192.168.122.130'},
    'iosv-3': {'prompt': 'iosv-3#', 'ip': '192.168.122.138'},
    'iosv-4': {'prompt': 'iosv-4#', 'ip': '192.168.122.134'},
}

with open('commands.txt', 'r') as f:
    commands = [command for command in f.readlines()]

username = 'admin'
password = 'admin01'

for device in devices.keys():
    # Retrieving the ip for every single Router
    ip = devices[device]['ip']
    # Establishing remote connection with telnet 
    child = pexpect.spawn(f'telnet {ip}')
    child.expect('Username:')
    child.sendline(username)
    child.expect('Password:')
    child.sendline(password)

    # SSH Configuration
    print(f'Setting up ssh for device {device}@{ip}')
    for command in commands:
        child.expect('#')
        child.sendline(command)
    print('SSH configured correctly...')


