from .exsi_wrapper import ExSiWrapper

_exsi = None


def _require_exsi():
    if _exsi is None:
        raise RuntimeError("EXSI bridge not initialized. Call init(hostname) first.")
    return _exsi


def init(hostname="10.0.1.1", force_reconnect=False):
    global _exsi
    if _exsi is None or force_reconnect:
        if _exsi is not None:
            try:
                del _exsi
            except Exception:
                pass
        _exsi = ExSiWrapper(hostname)
    return True


def close():
    global _exsi
    if _exsi is not None:
        try:
            del _exsi
        except Exception:
            pass
        _exsi = None
    return True


def get_state():
    exsi = _require_exsi()
    return exsi.get_scaner_state()


def start_scan():
    exsi = _require_exsi()
    exsi.start_scan()
    return True


def get_task_list():
    exsi = _require_exsi()
    exsi.get_task_list()
    return True


def load_protocol(protocol_path: str, activate=True):
    exsi = _require_exsi()
    exsi.load_protocal(protocol_path)
    if activate:
        exsi.activate_task()
    return True


def select_task(task_key: str, activate=True):
    exsi = _require_exsi()
    exsi.select_task(task_key)
    if activate:
        exsi.activate_task()
    return True


def set_rx_focus_only(centerloc: str, task_key=None, activate=True):
    """
    Change only the center/focus location via setRxGeometry3p centerloc=...
    centerloc format example: "0,0,0"
    """
    exsi = _require_exsi()
    if task_key is not None:
        exsi.set_rx_geometry3p(centerloc=centerloc, taskKey=task_key)
    else:
        exsi.set_rx_geometry3p(centerloc=centerloc)
    if activate:
        exsi.activate_task()
    return True


def set_rx_geometry(plane: str, startloc: str, endloc: str,
                    slices=None, spacing=None, thickness=None, activate=True):
    exsi = _require_exsi()
    exsi.set_rx_geometry(
        plane=plane,
        start_loc=startloc,
        end_loc=endloc,
        slices=slices,
        spacing=spacing,
        thickness=thickness,
    )
    if activate:
        exsi.activate_task()
    return True


def set_image_output_mode(mode, install=True):
    """
    mode can be:
      - "19"
      - "all"
      - "none"
      - ["magnitude", "phase"]
    """
    exsi = _require_exsi()

    if isinstance(mode, (list, tuple)):
        exsi.generate_image_types(*mode)
        if install:
            exsi.install_image_types(*mode)
    else:
        exsi.generate_image_types(str(mode))
        if install:
            exsi.install_image_types(str(mode))
    return True


def pause_scan():
    exsi = _require_exsi()
    exsi.pause_scan()
    return True


def resume_scan():
    exsi = _require_exsi()
    exsi.resume_scan()
    return True


def run_brp(plane: str, startloc: str, endloc: str):
    """
    Original helper preserved.
    Run ONE plane at a time.
    plane: "Axial" | "Coronal" | "Sagittal"
    """
    init()
    _exsi.adjust_scan_plane(plane, startloc, endloc)
    if _exsi.get_scaner_state() == 0:
        _exsi.start_scan()
    return True


def run_simple_scan(protocol_path: str, centerloc: str = None, image_mode="19", task_key=None):
    """
    Straight-through convenience flow:
      1) load protocol
      2) optionally change focus-only RX center location
      3) set image output mode
      4) get scanner state
      5) start scan if idle
    """
    exsi = _require_exsi()

    exsi.load_protocal(protocol_path)
    exsi.activate_task()

    if centerloc is not None:
        if task_key is not None:
            exsi.set_rx_geometry3p(centerloc=centerloc, taskKey=task_key)
        else:
            exsi.set_rx_geometry3p(centerloc=centerloc)
        exsi.activate_task()

    exsi.generate_image_types(str(image_mode))
    exsi.install_image_types(str(image_mode))

    state = exsi.get_scaner_state()
    if state == 0:
        exsi.start_scan()

    return state
