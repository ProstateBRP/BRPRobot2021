from exsi_wrapper import ExSiWrapper
import time


HOST_NAME = "10.0.1.1"

# ----------------------- User-editable test values -----------------------

# 1) Load protocol test
PROTOCOL_PATH = "NeedleTracking/1"

# Optional task selection after loading/listing.
# Leave as None to skip SelectTask.
TASK_KEY = None

# 2) RX test
# Option A: classic setRxGeometry
RX_PLANE = "sagittal"  # <-- change this to your desired plane (e.g. "axial", "sagittal", "coronal")
RX_START_LOC = '10,20, 30'
RX_END_LOC = '20,30, 40'
RX_SLICES = None
RX_SPACING = None
RX_THICKNESS = None

# Option B: setRxGeometry3p
# Use this if you want to change only the "focus"/center location and keep
# everything else untouched on the scanner side, IF EXSI allows omitted params
# to remain unchanged for setRxGeometry3p.
USE_RX3P = False
RX3P_CENTERLOC = "1,2,3"   # <-- change this to your new focus / center location
RX3P_SPACING = None
RX3P_THICK = None
RX3P_COIL = None
RX3P_FOV = None
RX3P_FREQDIR = None

# 3) Image output test
#
# Your wrapper's generate/install image methods currently build commands like:
#   GenerateImageTypes all
#   GenerateImageTypes magnitude phase
#   installImageTypes all
#   installImageTypes magnitude phase
#
# So if EXSI really needs a numeric mode like "19", the wrapper does not
# currently enforce against it; it will simply send:
#   GenerateImageTypes 19
#   installImageTypes 19
#
# If that is what your scanner accepts, keep IMAGE_MODE = "19".
# Otherwise replace with tokens like:
#   "all"
#   "none"
#   []
IMAGE_MODE = "[magnitude] [phase]"

# Pause after each command block
STEP_PAUSE_SECONDS = 0.5


# ----------------------------- Test helpers ------------------------------

def wait_for_enter(msg="Press Enter to continue..."):
    input(msg)


def run_load_test(exsi_obj):
    print("\n=== LOAD TEST ===")
    print(f"[TEST] get_task_list()")
    exsi_obj.get_task_list()
    time.sleep(STEP_PAUSE_SECONDS)

    print(f"[TEST] load_protocal({PROTOCOL_PATH!r})")
    exsi_obj.load_protocal(PROTOCOL_PATH)
    time.sleep(STEP_PAUSE_SECONDS)

    print(f"[TEST] get_task_list() after load")
    exsi_obj.get_task_list()
    time.sleep(STEP_PAUSE_SECONDS)

    exsi_obj.select_task("15")
    print("[TEST] activate_task()")
    exsi_obj.activate_task("15")
    print("=== LOAD TEST DONE ===\n")


def run_rx_test(exsi_obj):
    print("\n=== RX TEST ===")

    if USE_RX3P:
        print("[TEST] set_rx_geometry3p(...)")
        print("This is the best match for 'change only focus/center location' with the current wrapper.")
        print("Sent values:")
        print(f"  centerloc={RX3P_CENTERLOC}")
        print(f"  spacing={RX3P_SPACING}")
        print(f"  thick={RX3P_THICK}")
        print(f"  taskKey={TASK_KEY}")
        print(f"  coil={RX3P_COIL}")
        print(f"  fov={RX3P_FOV}")
        print(f"  freqdir={RX3P_FREQDIR}")

        exsi_obj.set_rx_geometry3p(
            centerloc=RX3P_CENTERLOC,
            spacing=RX3P_SPACING,
            thick=RX3P_THICK,
            taskKey=TASK_KEY,
            coil=RX3P_COIL,
            fov=RX3P_FOV,
            freqdir=RX3P_FREQDIR,
        )
    else:
        print("[TEST] set_rx_geometry(...)")
        print("Sent values:")
        print(f"  plane={RX_PLANE}")
        print(f"  start_loc={RX_START_LOC}")
        print(f"  end_loc={RX_END_LOC}")
        print(f"  slices={RX_SLICES}")
        print(f"  spacing={RX_SPACING}")
        print(f"  thickness={RX_THICKNESS}")

        exsi_obj.set_rx_geometry(
            plane=RX_PLANE,
            start_loc=RX_START_LOC,
            end_loc=RX_END_LOC,
            slices=RX_SLICES,
            spacing=RX_SPACING,
            thickness=RX_THICKNESS,
        )

    time.sleep(STEP_PAUSE_SECONDS)

    print("[TEST] activate_task()")
    exsi_obj.activate_task()

    print("=== RX TEST DONE ===\n")


def run_image_output_test(exsi_obj):
    print("\n=== IMAGE OUTPUT TEST ===")
    print(f"[TEST] generate_image_types({IMAGE_MODE!r})")
    exsi_obj.generate_image_types(IMAGE_MODE)
    time.sleep(STEP_PAUSE_SECONDS)

    print(f"[TEST] install_image_types({IMAGE_MODE!r})")
    exsi_obj.install_image_types(IMAGE_MODE)

    print("=== IMAGE OUTPUT TEST DONE ===\n")


def run_pause_resume_test(exsi_obj):
    print("\n=== PAUSE/RESUME TEST ===")
    print("[TEST] pause_scan()")
    exsi_obj.pause_scan()
    time.sleep(STEP_PAUSE_SECONDS)

    print("[TEST] resume_scan()")
    exsi_obj.resume_scan()
    print("=== PAUSE/RESUME TEST DONE ===\n")


def print_menu():
    print("Choose a test:")
    print("  1 = load protocol / activate task test")
    print("  2 = RX test")
    print("  3 = image output test")
    print("  4 = pause/resume test")
    print("  s = get scanner state")
    print("  q = quit")


def main():
    exsi_obj = ExSiWrapper(HOST_NAME)

    try:
        while True:
            print_menu()
            choice = input("Input: ").strip().lower()

            if choice == "1":
                run_load_test(exsi_obj)
                wait_for_enter()
            elif choice == "2":
                run_rx_test(exsi_obj)
                wait_for_enter()
            elif choice == "3":
                run_image_output_test(exsi_obj)
                wait_for_enter()
            elif choice == "4":
                run_pause_resume_test(exsi_obj)
                wait_for_enter()
            elif choice == "s":
                print("\n=== SCANNER STATE ===")
                state = exsi_obj.get_scaner_state()
                print(f"Returned state code: {state}")
                print("=====================\n")
                wait_for_enter()
            elif choice == "q":
                print("Exiting.")
                break
            else:
                print("Unknown input. Please choose 1, 2, 3, 4, s, or q.\n")
    finally:
        del exsi_obj


if __name__ == "__main__":
    main()
