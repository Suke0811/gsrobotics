
import copy


from demos.mini_marker_tracking import find_marker
import numpy as np
import cv2
import time
from demos.mini_marker_tracking import marker_detection
import sys
from demos.mini_marker_tracking import setting
import Gelsight

INIT_LOOP = 50


def resize_crop_mini(img, imgw, imgh):
    # resize, crop and resize back
    img = cv2.resize(img, (895, 672))  # size suggested by janos to maintain aspect ratio
    border_size_x, border_size_y = int(img.shape[0] * (1 / 7)), int(np.floor(img.shape[1] * (1 / 7)))  # remove 1/7th of border from each size
    img = img[border_size_x:img.shape[0] - border_size_x, border_size_y:img.shape[1] - border_size_y]
    img = img[:, :-1]  # remove last column to get a popular image resolution
    img = cv2.resize(img, (imgw, imgh))  # final resize for 3d
    return img

def compute_tracker_gel_stats(thresh):
    numcircles = 9 * 7;
    mmpp = .0625;
    true_radius_mm = .5;
    true_radius_pixels = true_radius_mm / mmpp;
    circles = np.where(thresh)[0].shape[0]
    circlearea = circles / numcircles;
    radius = np.sqrt(circlearea / np.pi);
    radius_in_mm = radius * mmpp;
    percent_coverage = circlearea / (np.pi * (true_radius_pixels) ** 2);
    return radius_in_mm, percent_coverage*100.



class GelsightMarker(Gelsight):
    def __init__(self):
        self.RESCALE = setting.RESCALE

    def init_marker(self, gelsight):
        for n in range(INIT_LOOP):
            frame = gelsight.
            print('flush black imgs')

            if n == 48:
                ret, frame = cap.read()
                ##########################
                frame = resize_crop_mini(frame, imgw, imgh)
                ### find marker masks
                mask = marker_detection.find_marker(frame)
                ### find marker centers
                mc = marker_detection.marker_center(mask, frame)
                break


        mccopy = mc
        mc_sorted1 = mc[mc[:, 0].argsort()]
        mc1 = mc_sorted1[:setting.N_]
        mc1 = mc1[mc1[:, 1].argsort()]

        mc_sorted2 = mc[mc[:, 1].argsort()]
        mc2 = mc_sorted2[:setting.M_]
        mc2 = mc2[mc2[:, 0].argsort()]

