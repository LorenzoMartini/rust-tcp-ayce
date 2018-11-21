import paramiko
import plotter
import time
import measurment

CONST_SERVER_ADDRESS = 'euler01'
CONST_CLIENT_ADDRESS = 'euler02'
CONST_PORT = '7878'
CONST_USERNAME = 'lmartini'
CONST_KEY_FILENAME = '/home/lorenzo/.ssh/euler0x-key'
CONST_SERVER_COMPILE = 'source $HOME/.cargo/env && cd rust-tcp-ayce/rust-tcp-ayce && cargo build --bin server --release'
CONST_CLIENT_COMPILE = 'source $HOME/.cargo/env && cd rust-tcp-ayce/rust-tcp-ayce && cargo build --bin client --release'
CONST_RUN_SERVER = './rust-tcp-ayce/rust-tcp-ayce/target/release/server'
CONST_RUN_CLIENT = './rust-tcp-ayce/rust-tcp-ayce/target/release/client'
CONST_PLOT = '0'
CONST_VERBOSE = '1'


def run_client_command(server_address):
    return CONST_RUN_CLIENT + ' -a ' + server_address


def print_and_collect_out(sout, server_id=''):
    # See output from server. Store out to analyze it and eventually plot it later
    out = []
    for line in sout:
        lstrip = line.rstrip('\n')
        if CONST_VERBOSE == '1':
            print('server' + server_id + ': ...' + lstrip)
        out.append(lstrip)
    return out


# Compiles given program and creates executable
def cargo_compile(ssh, compiling_command):
    print('Compiling executable...')
    _, stdout, stderr = ssh.exec_command(compiling_command)
    exit_status = stdout.channel.recv_exit_status()

    if exit_status == 0:
        print('Compilation successful, starting...')
        return 0

    print('Error while compiling:\n')
    for line in stderr:
        print(line.strip('\n'))
    return exit_status


# Compile the executables on server and client
def compile_source(server, client):
    if cargo_compile(server, CONST_SERVER_COMPILE) != 0 or cargo_compile(client, CONST_CLIENT_COMPILE):
        return -1
    return 0


# Connects client host to given server with name derived from command line args (or default) and given id
def setup_connection(machine_address):
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.connect(machine_address,
                username=CONST_USERNAME, key_filename=CONST_KEY_FILENAME)
    print('...Connected to ' + machine_address)
    return ssh


# Connect to remote machines to execute experiments
def connect_remote(server_address, client_address):
    # Connect to remote machines
    print('\nSetting up connection with servers...\n')
    server = setup_connection(server_address)
    client = setup_connection(client_address)
    print('\nConnected to all the machines!')
    return server, client


# Run server and client and returns stdout of server
def run_remote(server, client, server_address):
    _, sout, serr = server.exec_command(CONST_RUN_SERVER)
    time.sleep(5)
    _, cout, cerr = client.exec_command(run_client_command(server_address))

    # See output from client and make sure he's done
    for line in cout:
        print('client: ...' + line.rstrip('\n'))
    _ = cout.channel.recv_exit_status()
    print('client finished')

    # See output from server and make sure he's done. Store out to analyze it and eventually plot it later
    out = print_and_collect_out(sout)
    _ = sout.channel.recv_exit_status()
    print('server finished')

    # Print err
    for line in serr:
        print('Server ERR: ' + line)

    return out


def run(server_address, client_address):
    server, client = None, None
    output = None
    try:
        server, client = connect_remote(server_address, client_address)
        if compile_source(server, client) != 0:
            print("Compiling error")
            return
        output = run_remote(server, client, server_address)
    finally:
        if server:
            server.close()
        if client:
            client.close()

    if not output:
        print("No Output... Weird")
        return

    measurements = measurment.create_measurements_list(output)

    if CONST_PLOT == '1':
        plotter.plot_measurements(measurements)

    measurment.print_measurements_avg(measurements)


def main():
    run(CONST_SERVER_ADDRESS, CONST_CLIENT_ADDRESS)


if __name__ == "__main__":
    main()
