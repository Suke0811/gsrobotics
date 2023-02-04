

from gelsight import gsdevice
from gelsight import gs3drecon


DEVICE_PARAMS = dict(R1 = dict(res=0.0887, finger=gsdevice.Finger.R1, capture_stream=None, nn_name='nnr1.pt'),
                     local = dict(res=0.0887, finger=gsdevice.Finger.R15, capture_stream="http://" + 'R15' + ":8080/?action=stream", nn_name='nnr15.pt'),   # R15 was device variable
                     mini = dict(res=0.0625, finger=gsdevice.Finger.MINI, capture_stream=None, nn_name='nnmini.pt'))

THRESHOLD_PATCH_MASK = -0.01 # 0 flat, negative value -> pressed


class Patch3D:
    def __init__(self, gpu=False, model_path=None):
        self.gpu = gpu
        self.image = None
        self.mmpp = None
        if model_path is None:
            model_path = 'a'
        self.model_path = None

    def get_depthmap(self, frame):
        pass


    def get_patch_mask(self, depth_map, threshold=THRESHOLD_PATCH_MASK):



