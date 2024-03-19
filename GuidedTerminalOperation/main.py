import paramiko
from paramiko import SSHClient

import platform    # For getting the operating system name
import subprocess  # For executing a shell command

def ping(host):
    """
    Returns True if host (str) responds to a ping request.
    Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.
    """

    # Option for the number of packets as a function of
    param = '-n' if platform.system().lower()=='windows' else '-c'

    # Building the command. Ex: "ping -c 1 google.com"
    command = ['ping', param, '1', host]

    return subprocess.call(command) == 0


class SSHWrapper:
    def __init__(self, host_name):
        self.hostname = host_name
        self.client = SSHClient()
        self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        while True:
            try:
                self.client.connect(hostname=host_name, username="admin", password='', \
                                    look_for_keys=False, allow_agent=False)
                break
            except (Exception,):
                print("Cannot connect to the SSH client.")

        print("SSH Connected.")

    def __del__(self):
        self.client.close()

def terminal_operation(host_name):
    while True:
        print("=====Main Menu=====")
        print('Press 1 to ping robot controller module.')
        print('Press 2 to log in robot controller module.')
        print('Press 3 to exit program.')
        choice = input('=====Enter your choice: =====\n')
        if choice == '1':
            print('Pinging robot controller module')
            if ping(host_name):
                print('Robot controller module is online')
        elif choice == '2':
            print('Logging into robot controller module')
            robot_ssh_obj = SSHWrapper(host_name)
            while True:
                print("=====Robot SSH Menu=====")
                print('Press 1 to check SurgicalRobot process.')
                print('Press 2 to start SurgicalRobot process.')
                print('Press 3 to log out robot controller module.')
                choice = input('=====Enter your choice: =====\n')
                if choice == '1':
                    command = "top -n 1 | grep SurgicalRobot"
                    stdin, stdout, stderr = robot_ssh_obj.client.exec_command(command)
                    terminal_output = stdout.read().decode()
                    print(terminal_output)
                    if "SurgicalRobot" in terminal_output:
                        print("Detected SurgicalRobot process.")
                        process_num = terminal_output.split(" ")[1]
                        print(f"Process number is: {process_num}")
                        command = f"kill {process_num}"
                        stdin, stdout, stderr = robot_ssh_obj.client.exec_command(command)
                        print(f"Killed existing SurgicalRobot process.")
                    else:
                        print("No SurgicalRobot process is running.")
                elif choice == '2':
                    command = "./SurgicalRobot ProstateRobot"
                    stdin, stdout, stderr = robot_ssh_obj.client.exec_command(command)
                    print("Started SurgicalRobot process.")
                elif choice == '3':
                    print("Logged out.")
                    command = "exit"
                    stdin, stdout, stderr = robot_ssh_obj.client.exec_command(command)
                    break
        elif choice == '3':
            print("Program ended.")
            break


if __name__ == '__main__':
    print('Launching BRP Robot Guided Terminal Operation')

    host_name = "192.168.88.254"
    
    terminal_operation(host_name)

    

