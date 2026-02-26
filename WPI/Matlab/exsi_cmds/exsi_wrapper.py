import time

import paramiko
from paramiko import SSHClient


class ExSiWrapper:
    def __init__(self, host_name):
        self.hostname = host_name
        self.client = SSHClient()
        # client.load_system_host_keys()
        # client.load_host_keys('/home/practicepoint/.ssh/known_hosts')
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        while True:
            try:
                self.client.connect(hostname=host_name, username="sdc", password='508831MR1@wpi')
                break
            except (Exception,):
                print("Cannot connect to the SSH client.")
                time.sleep(1)

        print("SSH Connected.")

    def __del__(self):
        self.client.close()

    def start_scan(self):
        command = f"exsi -host {self.hostname} scan"
        stdin, stdout, stderr = self.client.exec_command(command)
        print(stdout.read().decode())

    def freeze_patient_table(self, switch):
        freeze_state = "on" if switch else "off"
        command = f"exsi -host {self.hostname} PatientTable freeze={freeze_state}"
        stdin, stdout, stderr = self.client.exec_command(command)
        print(stdout.read().decode())

    def set_rx_geometry(self, plane, start_loc, end_loc, slices, spacing, thickness):
        command = f"exsi -host {self.hostname} setRxGeometry plane={plane} startloc={start_loc} endloc={end_loc}"
        command += f" slices={slices} spacing={spacing} thick={thickness}"

        stdin, stdout, stderr = self.client.exec_command(command)
        print(stdout.read().decode())

    def get_control_variable(self, cv_name):
        command = f"exsi -host {self.hostname} getCVs {cv_name}"
        stdin, stdout, stderr = self.client.exec_command(command)
        print(stdout.read().decode())

    def set_control_variable(self, cv_name, value):
        command = f"exsi -host {self.hostname} setcvs {cv_name}={value}"
        stdin, stdout, stderr = self.client.exec_command(command)
        print(stdout.read().decode())

    def get_scaner_state(self):
        command = f"exsi -host {self.hostname} getscannerstate"
        stdin, stdout, stderr = self.client.exec_command(command)
        str_out = stdout.read().decode()
        print(str_out)
        if str_out == 'GetScannerState=ok  state=idle \n':
            return 0
        elif str_out == 'GetScannerState=ok  state=scanning \n':
            return 1
        elif str_out == 'GetScannerState=ok  state=prepped \n':
            return 2
        else:
            print("Unknown state!")
            return None

    def get_task_list(self):
        command = f"exsi -host {self.hostname} gettasklist"
        stdin, stdout, stderr = self.client.exec_command(command)
        print(stdout.read().decode())
    
    def load_protocal(self, protocal_name):
        command = f'exsi -host {self.hostname} loadprotocol site path="{protocal_name}"'
        stdin, stdout, stderr = self.client.exec_command(command)
        print(stdout.read().decode())
    
    def activate_task(self):
        command = f"exsi -host {self.hostname} activatetask"
        stdin, stdout, stderr = self.client.exec_command(command)
        print(stdout.read().decode())

    def adjust_scan_plane(self, plane, start_loc, end_loc):
        print("Changing scan plane to: ")
        self.load_protocal("ExSiTest/2")
        self.set_rx_geometry(plane, start_loc, end_loc)
        self.activate_task()
        print("Done with adjustment.")

    def setrealtimeoptions(self, controller):
        print(f"Set realtime option, controller={controller}")
        command = f"exsi -host {self.hostname} setrealtimeoptions controller={controller}"
        print(command)
        stdin, stdout, stderr = self.client.exec_command(command)
        print(stdout.read().decode())

    def beginrealtimeupdate(self):
        print("Begin realtime update.")
        command = f"exsi -host {self.hostname} beginrealtimeupdate"
        stdin, stdout, stderr = self.client.exec_command(command)
        print(stdout.read().decode())

    def endrealtimeupdate(self):
        print("End realtime update.")
        command = f"exsi -host {self.hostname} endrealtimeupdate commit"
        stdin, stdout, stderr = self.client.exec_command(command)
        print(stdout.read().decode())

    def setrealtimeparams(self, params):
        print("Set realtime params.")
        centerloc = ','.join(str(item) for item in params["centerloc"])
        rowvec = ','.join(str(item) for item in params["rowvec"])
        columnvec = ','.join(str(item) for item in params["columnvec"])

        command = f"exsi -host {self.hostname} setrealtimeparams centerloc={centerloc} rowvec={rowvec} columnvec={columnvec}"
        print(command)
        stdin, stdout, stderr = self.client.exec_command(command)
        print(stdout.read().decode())


if __name__ == "__main__":
    host_name = "10.0.1.1"

    exsi_obj = ExSiWrapper(host_name)

    exsi_obj.get_scaner_state()

    del exsi_obj
