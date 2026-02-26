from .exsi_wrapper import ExSiWrapper

_exsi = None

def init(hostname="10.0.1.1"):
    global _exsi
    if _exsi is None:
        _exsi = ExSiWrapper(hostname)
    return True


def run_brp(plane: str, startloc: str, endloc: str):
    """
    Run ONE plane at a time.
    plane: "Axial" | "Coronal" | "Sagittal"
    """
    init()

    _exsi.adjust_scan_plane(plane, startloc, endloc)

    if _exsi.get_scaner_state() == 0:
        _exsi.start_scan()

    return True
