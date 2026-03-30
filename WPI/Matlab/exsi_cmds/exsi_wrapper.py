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

    # Updated to allow old usage (adjust_scan_plane calls with only 3 args)
    # slices/spacing/thickness default to None (do not append if None)
    def set_rx_geometry(self, plane, start_loc, end_loc, slices=None, spacing=None, thickness=None):
        command = f"exsi -host {self.hostname} setRxGeometry plane={plane} startloc={start_loc} endloc={end_loc}"

        if slices is not None:
            command += f" slices={slices}"
        if spacing is not None:
            command += f" spacing={spacing}"
        if thickness is not None:
            command += f" thick={thickness}"

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
    
    def load_protocal(self, protocal_name, dir_name="Pelvis"):
        command = f'exsi -host {self.hostname} loadprotocol site dir="PracticePoint" path="{protocal_name}"'
        stdin, stdout, stderr = self.client.exec_command(command)
        print(stdout.read().decode())
    
    def activate_task(self, task_key=None):
        command = f"exsi -host {self.hostname} activatetask taskKey={task_key}"
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
    # ------------------------ New methods ------------------------

    # 1) Select task by taskKey
    # Spec: SelectTask params: taskKey=string :contentReference[oaicite:3]{index=3}
    def select_task(self, task_key):
        command = f"exsi -host {self.hostname} SelectTask taskKey={task_key}"
        stdin, stdout, stderr = self.client.exec_command(command)
        print(stdout.read().decode())

    # 2) setRxGeometry3p
    # Spec: setRxGeometry3p params include: [taskKey] [coil] [centerloc=r,a,s] [spacing=r,a,s] [thick] [fov] [freqdir] :contentReference[oaicite:4]{index=4}
    # NOTE: We keep the same “append params if provided” pattern used elsewhere.
    def set_rx_geometry3p(self, centerloc=None, spacing=None, thick=None, taskKey=None, coil=None, fov=None, freqdir=None):
        command = f"exsi -host {self.hostname} setRxGeometry3p"

        if taskKey is not None:
            command += f" taskKey={taskKey}"
        if coil is not None:
            command += f" coil={coil}"
        if centerloc is not None:
            command += f" centerloc={centerloc}"
        if spacing is not None:
            command += f" spacing={spacing}"
        if thick is not None:
            command += f" thick={thick}"
        if fov is not None:
            command += f" fov={fov}"
        if freqdir is not None:
            command += f" freqdir={freqdir}"

        stdin, stdout, stderr = self.client.exec_command(command)
        print(stdout.read().decode())

    # 3) Pause / Resume scan (realtime)
    # Spec: PauseScan / ResumeScan :contentReference[oaicite:5]{index=5}
    def pause_scan(self):
        command = f"exsi -host {self.hostname} PauseScan"
        stdin, stdout, stderr = self.client.exec_command(command)
        print(stdout.read().decode())

    def resume_scan(self):
        command = f"exsi -host {self.hostname} ResumeScan"
        stdin, stdout, stderr = self.client.exec_command(command)
        print(stdout.read().decode())

    # Helper: build image type args exactly like the EXSI command expects:
    # - either "all"/"none" OR a combination of magnitude/phase/real/imaginary
    def _img_types_args(self, *types):
        if len(types) == 0:
            return "all"
        # allow caller to pass a single list/tuple
        if len(types) == 1 and isinstance(types[0], (list, tuple)):
            types = tuple(types[0])
        return " ".join(str(t) for t in types)

    # 4) GenerateImageTypes
    # Spec: GenerateImageTypes all | [magnitude] [phase] [real] [imaginary] :contentReference[oaicite:6]{index=6}
    def generate_image_types(self, *types):
        args = self._img_types_args(*types)
        command = f"exsi -host {self.hostname} GenerateImageTypes {args}"
        stdin, stdout, stderr = self.client.exec_command(command)
        print(stdout.read().decode())

    # 5) installImageTypes
    # Spec: installImageTypes all | none | [magnitude] [phase] [real] [imaginary] :contentReference[oaicite:7]{index=7}
    def install_image_types(self, *types):
        args = self._img_types_args(*types)
        command = f"exsi -host {self.hostname} installImageTypes {args}"
        stdin, stdout, stderr = self.client.exec_command(command)
        print(stdout.read().decode())

if __name__ == "__main__":
    host_name = "10.0.1.1"

    exsi_obj = ExSiWrapper(host_name)

    exsi_obj.get_scaner_state()

    del exsi_obj
