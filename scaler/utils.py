import os
import re


def get_camera_id(camera_name):
    cam_num = None
    found_devices = {}

    if os.name == 'nt':
        raise OSError('Windows is not suported')
        # cam_num = find_cameras_windows()
    else:
        for file in os.listdir("/sys/class/video4linux"):
            real_file = os.path.realpath("/sys/class/video4linux/" + file + "/name")
            with open(real_file, "rt") as name_file:
                name = name_file.read().rstrip()

            if camera_name in name:
                cam_num = int(re.search("\d+$", file).group(0))
                print("{} -> {}".format(file, name))

            device = found_devices.get(name)
            if device is None:
                found_devices.setdefault(name, [cam_num])
            else:
                device.append(cam_num)

    return pick_proper_camera_id(found_devices)        # this will pick only ONE correct cam id per device


def pick_proper_camera_id(found_device: dict):
    """
    for some reason, we detect two cameras per one gelsight mini.
    i.e.
    video0 -> GelSight Mini R0B 28PV-K2T7: Ge
    video1 -> GelSight Mini R0B 28PV-K2T7: Ge
    But, we should use video 0 to get an image in this case
    """

    device_ids = {}
    for name, camera_ids in found_device.items():   # we assume that smaller cam id per device is the correct one
        cam_id = min(camera_ids)        # TODO: is picking smaller cam id is always correct?
        device_ids[name] = cam_id

    return device_ids
