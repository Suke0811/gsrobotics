from gelsight import gsdevice
from gelsight import gs3drecon
from utils import get_camera_id
from Cv2Handler import Cv2Handler
import cv2
import numpy as np

FINGER = 'finger'

THRESHOLD_PATCH_MASK = -0.01 # 0 flat, negative value -> pressed


class GelSightDevice:
    MINI = 'GelSight Mini'
    R1 = 'R1'
    R15 = 'R15'
    ALL_DEVICE = [R1, MINI, R15]
    PARAMS = {
        R1: dict(res=0.0887, finger=gsdevice.Finger.R1, capture_stream=None, nn_name='nnr1.pt'),
        R15: dict(res=0.0887, finger=gsdevice.Finger.R15,
                              capture_stream="http://" + 'R15' + ":8080/?action=stream", nn_name='nnr15.pt'),
        # R15 was device variable
        MINI: dict(res=0.0625, finger=gsdevice.Finger.MINI, capture_stream=None, nn_name='nnmini.pt')
    }

    @classmethod
    def get_finger(cls, name):
        return cls.get_param(FINGER, name)

    @classmethod
    def get_param(cls, param_name, name):
        param = None
        for dev_name in cls.ALL_DEVICE:
            if dev_name in name:
                param = cls.PARAMS[dev_name][param_name]
        return param



DEFAULT_DEVICE = [GelSightDevice.MINI]



class GelSight:

    def __init__(self, device_list=None):
        if device_list is None:
            device_list = DEFAULT_DEVICE
        if not isinstance(device_list, list):
            device_list = [device_list]
        self.device_list = device_list

        self.cameras = []
        self.devices = {}
        self.devices_roi = {}

    def connect_all(self):
        for device in self.device_list:
            self._connect_to(device)

    def _connect_to(self, device_name):
        # get dev and store in dict
        devices = {}
        camera_devices = get_camera_id(device_name)
        for name, cam_id in camera_devices.items():
            finger = GelSightDevice.get_finger(name)
            dev = gsdevice.Camera(finger, cam_id)
            dev.connect()
            roi = self._get_ROI(dev)
            self.devices[name] = dev
            self.devices_roi[name] = roi


    def _get_ROI(self, dev, FIND_ROI=False):
        FIND_ROI = False     # TODO: this is from the sdk, not sure what FIND_ROI  case would do so now always false
        f0 = dev.get_raw_image()
        if FIND_ROI:
            roi = cv2.selectROI(f0)
            roi_cropped = f0[int(roi[1]):int(roi[1] + roi[3]), int(roi[0]):int(roi[0] + roi[2])]
            cv2.imshow('ROI', roi_cropped)
            print('Press q in ROI image to continue')
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        elif f0.shape == (640, 480, 3):
            roi = (60, 100, 375, 380)
        elif f0.shape == (320, 240, 3):
            roi = (30, 50, 186, 190)
        elif f0.shape == (240, 320, 3):
            ''' cropping is hard coded in resize_crop_mini() function in gsdevice.py file '''
            border_size = 0  # default values set for mini to get 3d
            roi = (border_size, border_size, 320 - 2 * border_size,
                   240 - 2 * border_size)  # default values set for mini to get 3d
        else:
            roi = (0, 0, f0.shape[1], f0.shape[0])

        return roi


    def get_image(self, device_name, raw=False):
        img = None
        dev = self.devices[device_name]
        roi = self.devices_roi[device_name]
        if raw:
            img = dev.get_raw_image()
        else:
            img = dev.get_image(roi)
        return img


    def get_all_images(self, device_names:list=None, raw=False):
        ret_image = {}
        if device_names is None:
            device_names = list(self.devices.keys())
        for name in device_names:
            img = self.get_image(name, raw)
            ret_image[name] = img

        return ret_image

    def get_image_shape(self, device_name):
        """
        return: device image (width, height)
        """
        dev = self.devices[device_name]
        return dev.imgw, dev.imgh

    def get_3d_image(self, device_name):
        pass

    def get_all_3d_images(self):
        return dict()

    def get_patch_mask(self, depth_map, threshold=THRESHOLD_PATCH_MASK):
        # return masking for pixel with a negative depth (pressed)
        return np.where(depth_map < THRESHOLD_PATCH_MASK, True, False)

    def stream(self, teminate =False):
        screen = Cv2Handler()

        # screen.init_video()
        # screen.init_3d_visualizer()

        try:
            while not teminate:
                # things to do in the loop
                self._streem_loop(screen)

                # Termination condittions
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        except KeyboardInterrupt:
            print('Interrupted!')   # just in case?

        # close the deivces (also attempts in __del__)
        self.close_devices()


    def _streem_loop(self, screen):
        images = self.get_all_images()
        images_3d = self.get_all_3d_images()

        for name, img, img_3d in zip(images.items(), images_3d.values()):
            screen.show_image(img, name)
            screen.show_3d_image(img_3d, name)

    def close_devices(self):
        for dev in self.devices.values():
            dev.stop_video()



    def __del__(self):
        if self.devices is not None:    # if devices are not set None, we need to try disabling them
              self.close_devices()



if __name__ == '__main__':
    pass


