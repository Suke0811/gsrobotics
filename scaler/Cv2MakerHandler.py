from Cv2Handler import Cv2Handler
import cv2
import numpy as np
from Cv2Handler import DEFAULT_WINDOW_NAME

from demos.mini_marker_tracking import marker_detection as md

MASK = 'Mask'


class Cv2MakerHandler(Cv2Handler):
    def __init__(self):
        super().__init__()



    def show_mask(self, mask, name=DEFAULT_WINDOW_NAME):
        mask_img = np.asarray(mask) * 255
        self.show_image(mask_img, MASK + name, add_frame=False, multiplier=2)

    def show_flow(self, frame, flow, name=DEFAULT_WINDOW_NAME):
        md.draw_flow(frame, flow)   # inside cv2.arrowedLine is probably modify the frame in-place so no return necessary?
        self.show_image(frame, name, add_frame=True, multiplier=2)


    def show_image(self, frame, name=DEFAULT_WINDOW_NAME, add_frame=True, multiplier=2):    # TODO: not sure what multiplier is doing
        super().show_image(frame, name, add_frame, multiplier)

    def init_video_mask(self, file_path, frame, name=DEFAULT_WINDOW_NAME, fps=25):
        name = MASK + name  # TODO: should change hte filepath too
        super().init_video(file_path, frame, name, fps)
