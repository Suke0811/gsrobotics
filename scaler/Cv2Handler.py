import cv2
from gelsight import gs3drecon

DEFAULT_WINDOW_NAME = 'GelSight'    # this is to rip off the name args if the user is using just one sensor
class Cv2Handler:
    def __init__(self):
        self.video_writer = None
        self.vis3d = None

    def show_image(self, frame, name=DEFAULT_WINDOW_NAME, add_frame=True, multiplier=2):
        bigframe = cv2.resize(frame, (frame.shape[1] * multiplier, frame.shape[0] * multiplier))
        cv2.imshow(name, bigframe)      # opencv handle window based on names

        if add_frame:
            self.add_video_frame(frame, name)   # save the frame for video. if video is not init, then nothing happens

    def init_3d_visualizer(self,img_h, img_w, name=DEFAULT_WINDOW_NAME, file_path='', mmpp=0.0625):
        self.vis3d[name] = gs3drecon.Visualize3D(img_h, img_w, file_path, mmpp)    # it seems like mmpp is not used inside, (currently Gelsight mini value)

    def show_3d_image(self, depth_map, name=DEFAULT_WINDOW_NAME):
        self.vis3d[name].update(depth_map)

    def export_3d_video(self, name=None):
        if name is None and self.vis3d is not None:
            name = list(self.vis3d.keys())
        if isinstance(name, list):
            name = [name]

        for n in name:
            self.vis3d[n].save_pointcloud()
        self.vis3d = None   # once data is saved, reset


    def init_video(self, file_path, frame, name=DEFAULT_WINDOW_NAME, fps=25):
        # encoding
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        # set up writer. this is for avi, but it wouldn't work on Windows without proper encoder installation
        self.video_writer[name] = cv2.VideoWriter(file_path, fourcc, fps, (frame.shape[1], frame.shape[0]), isColor=True)

    def add_video_frame(self, frame, name=DEFAULT_WINDOW_NAME):
        if self.video_writer is not None:   # w/o init_video, it just ignore
            self.video_writer[name].write(frame)





    def __del__(self):
        if self.vis3d is not None:
            self.export_3d_video()
        cv2.destroyAllWindows()
