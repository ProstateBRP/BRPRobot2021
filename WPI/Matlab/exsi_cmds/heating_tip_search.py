import time

from exsi_wrapper import ExSiWrapper

def set_scan_plane_coronal(exsi_obj, plane, start_loc, end_loc, slices, spacing, thickness):
    exsi_obj.load_protocal("MRTI_V2/3")

    exsi_obj.set_rx_geometry(plane, start_loc, end_loc, slices, spacing, thickness)

    # Set the other two coordinates

    exsi_obj.activate_task()

    exsi_obj.set_control_variable(cv_name="rhrcctrl", value=29)


def set_scan_plane_oblique(exsi_obj, plane, start_loc, end_loc, slices, spacing, thickness):
    exsi_obj.load_protocal("MRTI_V2/6")

    exsi_obj.set_rx_geometry(plane, start_loc, end_loc, slices, spacing, thickness)

    exsi_obj.activate_task()

    # exsi_obj.set_control_variable(cv_name="rhrcctrl", value=29)

if __name__ == "__main__":
    host_name = "10.0.1.1"
    exsi_obj = ExSiWrapper(host_name)

    center = 79
    thickness = 2
    start_loc = center - 2 * thickness
    end_loc = center + 2 * thickness
    
    # set_scan_plane_coronal(exsi_obj, plane="coronal", start_loc=f"P{start_loc}", end_loc=f"P{end_loc}", slices=5, spacing=0, thickness=thickness)


    set_scan_plane_oblique(exsi_obj, plane="oblique", 
                           start_loc="l22,a11,s37", 
                           end_loc="l23,a18,s44", 
                           slices=5, 
                           spacing=0, 
                           thickness=thickness)

    del exsi_obj
