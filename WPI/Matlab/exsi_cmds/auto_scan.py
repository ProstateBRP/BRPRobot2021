import time

from exsi_wrapper import ExSiWrapper

if __name__ == "__main__":
    host_name = "10.0.1.1"

    exsi_obj = ExSiWrapper(host_name)

    try:
        while True:
            if exsi_obj.get_scaner_state() == 0:
                exsi_obj.start_scan()
            else:
                time.sleep(0.1)
    except KeyboardInterrupt:
        print("Done.")
        pass

    del exsi_obj

