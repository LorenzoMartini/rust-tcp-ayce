import paramiko
import plotter
import time
import measurment

CONST_SERVER_ADDRESS = "euler01"
CONST_CLIENT_ADDRESS = "euler02"
CONST_PORT = "7878"
CONST_USERNAME = "lmartini"
CONST_KEY_FILENAME = "/home/lorenzo/.ssh/euler0x-key"
CONST_SERVER_COMPILE = "source $HOME/.cargo/env && cd rust-tcp-ayce/rust-tcp-ayce && cargo build --bin server --release"
CONST_CLIENT_COMPILE = "source $HOME/.cargo/env && cd rust-tcp-ayce/rust-tcp-ayce && cargo build --bin client --release"
CONST_RUN_SERVER = "./rust-tcp-ayce/rust-tcp-ayce/target/release/server -k 100000"
CONST_RUN_CLIENT = "./rust-tcp-ayce/rust-tcp-ayce/target/release/client -a euler01 -k 100000"


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


# Run server and client and returns somthing TODO{@lmartini}
def run_remote(server, client):
    _, sout, serr = server.exec_command(CONST_RUN_SERVER)
    _, cout, cerr = client.exec_command(CONST_RUN_CLIENT)
    _ = sout.channel.recv_exit_status()
    _ = cout.channel.recv_exit_status()
    for line in serr:
        print(line)
    return sout


def run(server_address, client_address):
    server, client = None, None
    output = None
    try:
        server, client = connect_remote(server_address, client_address)
        # if compile_source(server, client) != 0:
        #     print("Compiling error")
        #     return
        time.sleep(2)
        output = run_remote(server, client)
    finally:
        if server:
            server.close()
        if client:
            client.close()

    if not output:
        print("No Output... Weird")
        return

    measurements = measurment.create_measurements_list(output)

    plotter.plot_measurements(measurements)

    measurment.print_measurements_avg(measurements)


def main():
    run(CONST_SERVER_ADDRESS, CONST_CLIENT_ADDRESS)


if __name__ == "__main__":
    main()
