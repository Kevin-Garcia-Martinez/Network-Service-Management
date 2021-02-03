from pexpect import pxssh

def ssh_login( address, username, password, time=10 ):
    try:
        session = pxssh.pxssh() 
        session.login( address, username, password, auto_prompt_reset=False, login_timeout=time )
        return session
    
    except pxssh.ExceptionPxssh as e:
        print("pxssh failed on login.")
        print(e)
    

def make_ssh_conexion( address, ssh_user, ssh_pass ):
    time = 10
    session = ssh_login( address, ssh_user, ssh_pass )
    while session == None:
        time+=2
        print('Trying again ...')
        session = ssh_login( address, ssh_user, ssh_pass, time )
    print('ssh conexion stablished successfully')
    return session