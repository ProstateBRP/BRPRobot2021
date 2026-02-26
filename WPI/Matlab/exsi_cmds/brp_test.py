from exsi_wrapper import ExSiWrapper
import time

if __name__ == "__main__":
    host_name = "10.0.1.1"

    exsi_obj = ExSiWrapper(host_name)

    exsi_obj.adjust_scan_plane(plane="Axial", start_loc="0", end_loc="10")
    if exsi_obj.get_scaner_state() == 0:
        print("Start scanning")
        exsi_obj.start_scan()

    # start_loc = "30,35,40"
    # end_loc = "40,35,40"
    # step_size = 5
    # plane = "oblique"
    # exsi_obj.get_scaner_state()
    # exsi_obj.set_rx_geometry(plane, start_loc, end_loc)
    # exsi_obj.start_scan()

    # try:
    #     while True:
    #         print("Waiting robot to move.")
    #         time.sleep(5)
    #         if exsi_obj.get_scaner_state() == 0:
    #             print("Start scanning")
    #             exsi_obj.start_scan()
    #             exsi_obj.set_rx_geometry(plane, start_loc, end_loc)
    #             end_loc += step_size
    # except KeyboardInterrupt:
    #     print("Done.")
    #     pass

    del exsi_obj