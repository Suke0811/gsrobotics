from os import listdir
from os.path import isfile, join
import scipy, scipy.fftpack
import torch
import torch.nn as nn
import torch.nn.functional as F
import open3d
import numpy as np
import math
import enum
import os
import cv2
from scipy.interpolate import griddata


# creating enumerations using class
class Finger(enum.Enum):
    R1 = 1
    R15 = 2
    DIGIT = 3
    MINI = 4

def find_marker(gray):
    mask = cv2.inRange(gray, 0, 70)
    # kernel = np.ones((2, 2), np.uint8)
    # dilation = cv2.dilate(mask, kernel, iterations=1)
    return mask

def dilate(img, ksize=5, iter=1):
    kernel = np.ones((ksize, ksize), np.uint8)
    return cv2.dilate(img, kernel, iterations=iter)

def erode(img, ksize=5):
    kernel = np.ones((ksize, ksize), np.uint8)
    return cv2.erode(img, kernel, iterations=1)

def matching_rows(A,B):
    ### https://stackoverflow.com/questions/8317022/get-intersecting-rows-across-two-2d-numpy-arrays
    matches=[i for i in range(B.shape[0]) if np.any(np.all(A==B[i],axis=1))]
    if len(matches)==0:
        return B[matches]
    return np.unique(B[matches],axis=0)

def interpolate_gradients(gx, gy, img, cm, markermask):
    ''' interpolate gradients at marker location '''

    # if np.where(cm)[0].shape[0] != 0:
    cmcm = np.zeros(img.shape[:2])
    ind1 = np.vstack(np.where(cm)).T
    ind2 = np.vstack(np.where(markermask)).T
    ind2not = np.vstack(np.where(~markermask)).T
    ind3 = matching_rows(ind1, ind2)
    cmcm[(ind3[:, 0], ind3[:, 1])] = 1.
    ind4 = ind1[np.all(np.any((ind1 - ind3[:, None]), axis=2), axis=0)]
    x = np.linspace(0, 240, 240)
    y = np.linspace(0,320, 320)
    X, Y = np.meshgrid(x, y)

    '''interpolate at the intersection of cm and markermask '''
    # gx_interpol = griddata(ind4, gx[(ind4[:, 0], ind4[:, 1])], ind3, method='nearest')
    # gx[(ind3[:, 0], ind3[:, 1])] = gx_interpol
    # gy_interpol = griddata(ind4, gy[(ind4[:, 0], ind4[:, 1])], ind3, method='nearest')
    # gy[(ind3[:, 0], ind3[:, 1])] = gy_interpol

    ''' interpolate at the entire markermask '''
    gx_interpol = griddata(ind2, gx[(ind2[:, 0], ind2[:, 1])], gx[(ind2not[:, 0], ind2not[:, 1])], method='nearest')
    gx[(ind2not[:, 0], ind2not[:, 1])] = gx_interpol
    gy_interpol = griddata(ind2, gy[(ind2[:, 0], ind2[:, 1])], gy[(ind2not[:, 0], ind2not[:, 1])], method='nearest')
    gy[(ind2not[:, 0], ind2not[:, 1])] = gy_interpol
    #print (gy_interpol.shape, gx_interpol.shape, gx.shape, gy.shape)

    ''' interpolate using samples in the vicinity of marker '''


    ''' method #3 '''
    # ind1 = np.vstack(np.where(markermask)).T
    # gx_interpol = scipy.ndimage.map_coordinates(gx, [ind1[:, 0], ind1[:, 1]], order=1, mode='constant')
    # gx[(ind1[:, 0], ind1[:, 1])] = gx_interpol
    # gy_interpol = scipy.ndimage.map_coordinates(gy, [ind1[:, 0], ind1[:, 1]], order=1, mode='constant')
    # gx[(ind1[:, 0], ind1[:, 1])] = gy_interpol

    ''' method #4 '''
    # x = np.arange(0, img.shape[0])
    # y = np.arange(0, img.shape[1])
    # fgx = scipy.interpolate.RectBivariateSpline(x, y, gx, kx=2, ky=2, s=0)
    # gx_interpol = fgx.ev(ind2[:,0],ind2[:,1])
    # gx[(ind2[:, 0], ind2[:, 1])] = gx_interpol
    # fgy = scipy.interpolate.RectBivariateSpline(x, y, gy, kx=2, ky=2, s=0)
    # gy_interpol = fgy.ev(ind2[:, 0], ind2[:, 1])
    # gy[(ind2[:, 0], ind2[:, 1])] = gy_interpol

    return gx_interpol, gy_interpol


def interpolate_grad(img, mask):
    # mask = (soft_mask > 0.5).astype(np.uint8) * 255
    # pixel around markers
    mask_around = (dilate(mask, ksize=3, iter=2) > 0) & ~(mask != 0)
    # mask_around = mask == 0
    mask_around = mask_around.astype(np.uint8)
    # cv2.imshow("mask_around", mask_around*1.)

    x, y = np.arange(img.shape[0]), np.arange(img.shape[1])
    yy, xx = np.meshgrid(y, x)

    # mask_zero = mask == 0
    mask_zero = mask_around == 1
    # cv2.imshow("mask_zero", mask_zero*1.)

    # if np.where(mask_zero)[0].shape[0] != 0:
    #     print ('interpolating')
    mask_x = xx[mask_around == 1]
    mask_y = yy[mask_around == 1]
    points = np.vstack([mask_x, mask_y]).T
    values = img[mask_x, mask_y]
    markers_points = np.vstack([xx[mask != 0], yy[mask != 0]]).T
    method = "nearest"
    # method = "linear"
    # method = "cubic"
    x_interp = griddata(points, values, markers_points, method=method)
    x_interp[x_interp != x_interp] = 0.0
    ret = img.copy()
    ret[mask != 0] = x_interp
    # else:
    #     ret = img
    return ret

def demark(gx, gy, markermask):
    # mask = find_marker(img)
    gx_interp = interpolate_grad(gx.copy(), markermask)
    gy_interp = interpolate_grad(gy.copy(), markermask)
    return gx_interp, gy_interp

#@njit(parallel=True)
def get_features(img,pixels,features,imgw,imgh):
    features[:,3], features[:,4]  = pixels[:,0] / imgh, pixels[:,1] / imgw
    for k in range(len(pixels)):
        i,j = pixels[k]
        rgb = img[i, j] / 255.
        features[k,:3] = rgb

#
# 2D integration via Poisson solver
#
def poisson_reconstruct(gradx, grady, boundarysrc):
    # Laplacian
    gyy = grady[1:,:-1] - grady[:-1,:-1]
    gxx = gradx[:-1,1:] - gradx[:-1,:-1]
    f = np.zeros(boundarysrc.shape)
    f[:-1,1:] += gxx
    f[1:,:-1] += gyy
    # Boundary image
    boundary = boundarysrc.copy()
    boundary[1:-1,1:-1] = 0;

    # Subtract boundary contribution
    f_bp = -4*boundary[1:-1,1:-1] + boundary[1:-1,2:] + boundary[1:-1,0:-2] + boundary[2:,1:-1] + boundary[0:-2,1:-1]
    f = f[1:-1,1:-1] - f_bp

    # Discrete Sine Transform
    #tt = np.zeros(boundarysrc.shape)
    #fsin = np.zeros(boundarysrc.shape)
    #cv2.dft(f, tt)
    #cv2.dft(tt.T, fsin)
    #cv2.namedWindow('dft')
    #cv2.imshow('dft',fsin)
    #cv2.waitKey()
    tt = scipy.fftpack.dst(f, norm='ortho')
    fsin = scipy.fftpack.dst(tt.T, norm='ortho').T
    # Eigenvalues
    (x,y) = np.meshgrid(range(1,f.shape[1]+1), range(1,f.shape[0]+1), copy=True)
    denom = (2*np.cos(math.pi*x/(f.shape[1]+2))-2) + (2*np.cos(math.pi*y/(f.shape[0]+2)) - 2)
    f = fsin/denom
    # Inverse Discrete Sine Transform
    #img_tt = np.zeros(f.shape)
    #cv2.idft(f, tt)
    #cv2.idft(tt.T, img_tt)
    tt = scipy.fftpack.idst(f, norm='ortho')
    img_tt = scipy.fftpack.idst(tt.T, norm='ortho').T
    print('tt shape = ', tt.shape)
    # New center + old boundary
    result = boundary
    result[1:-1,1:-1] = img_tt
    return result





class RGB2NormNetR1(nn.Module):
    def __init__(self):
        super(RGB2NormNetR1, self).__init__()
        input_size = 5
        self.fc1 = nn.Linear(input_size, 16)
        self.fc2 = nn.Linear(16, 32)
        self.fc3 = nn.Linear(32, 64)
        self.fc4 = nn.Linear(64, 32)
        self.fc5 = nn.Linear(32, 16)
        self.fc6 = nn.Linear(16, 8)
        self.fc7 = nn.Linear(8, 2)
        self.drop_layer = nn.Dropout(p=0.1)

    def forward(self, x):
        x = F.tanh(self.fc1(x))
        x = self.drop_layer(x)
        x = F.tanh(self.fc2(x))
        x = self.drop_layer(x)
        x = F.tanh(self.fc3(x))
        x = self.drop_layer(x)
        x = F.tanh(self.fc4(x))
        x = self.drop_layer(x)
        x = F.tanh(self.fc5(x))
        x = F.tanh(self.fc6(x))
        x = self.fc7(x)
        return x


''' nn architecture for r1.5 and mini '''
class RGB2NormNetR15(nn.Module):
    def __init__(self):
        super(RGB2NormNetR15, self).__init__()
        input_size = 5
        self.fc1 = nn.Linear(input_size, 64)
        self.fc2 = nn.Linear(64,64)
        self.fc3 = nn.Linear(64,64)
        self.fc4 = nn.Linear(64,2)
        self.drop_layer = nn.Dropout(p=0.05)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = self.drop_layer(x)
        x = F.relu(self.fc2(x))
        x = self.drop_layer(x)
        x = F.relu(self.fc3(x))
        x = self.drop_layer(x)
        x = self.fc4(x)
        return x

class Reconstruction3D:
    def __init__(self, finger, dev):
        self.finger = finger
        self.cpuorgpu = "cpu"
        self.dm_zero_counter = 0
        self.dm_zero = np.zeros((dev.imgw, dev.imgh))
        pass

    def load_nn(self, net_path, cpuorgpu):

        self.cpuorgpu = cpuorgpu
        device = torch.device(cpuorgpu)

        if not os.path.isfile(net_path):
            print('Error opening ', net_path, ' does not exist')
            return

        print('self.finger = ', self.finger)
        if self.finger == Finger.R1:
            print('calling nn R1...')
            net = RGB2NormNetR1().float().to(device)
        elif self.finger == Finger.R15:
            print('calling nn R15...')
            net = RGB2NormNetR15().float().to(device)
        else:
            net = RGB2NormNetR15().float().to(device)

        if cpuorgpu=="cuda":
            ### load weights on gpu
            # net.load_state_dict(torch.load(net_path))
            checkpoint = torch.load(net_path, map_location=lambda storage, loc: storage.cuda(0))
            net.load_state_dict(checkpoint['state_dict'])
        else:
            ### load weights on cpu which were actually trained on gpu
            checkpoint = torch.load(net_path, map_location=lambda storage, loc: storage)
            net.load_state_dict(checkpoint['state_dict'])

        self.net = net

        return self.net

    def get_depthmap(self, frame, mask_markers, cm=None):
        MARKER_INTERPOLATE_FLAG = mask_markers

        ''' find contact region '''
        # cm, cmindx = find_contact_mask(f1, f0)
        ###################################################################
        ### check these sizes
        ##################################################################
        if (cm is None):
            cm, cmindx = np.ones(frame.shape[:2]), np.where(np.ones(frame.shape[:2]))
        imgh = frame.shape[:2][0]
        imgw = frame.shape[:2][1]

        if MARKER_INTERPOLATE_FLAG:
            ''' find marker mask '''
            markermask = find_marker(cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY))
            cm = ~markermask
            '''intersection of cm and markermask '''
            # cmmm = np.zeros(img.shape[:2])
            # ind1 = np.vstack(np.where(cm)).T
            # ind2 = np.vstack(np.where(markermask)).T
            # ind2not = np.vstack(np.where(~markermask)).T
            # ind3 = matching_rows(ind1, ind2)
            # cmmm[(ind3[:, 0], ind3[:, 1])] = 1.
            cmandmm = (np.logical_and(cm, markermask)).astype('uint8')
            cmandnotmm = (np.logical_and(cm, ~markermask)).astype('uint8')

        ''' Get depth image with NN '''
        nx = np.zeros(frame.shape[:2])
        ny = np.zeros(frame.shape[:2])
        dm = np.zeros(frame.shape[:2])

        ''' ENTIRE CONTACT MASK THRU NN '''
        # if np.where(cm)[0].shape[0] != 0:
        rgb = frame[np.where(cm)] / 255
        # rgb = diffimg[np.where(cm)]
        pxpos = np.vstack(np.where(cm)).T
        # pxpos[:, [1, 0]] = pxpos[:, [0, 1]] # swapping
        pxpos[:, 0], pxpos[:, 1] = pxpos[:, 0] / imgh, pxpos[:, 1] / imgw
        # the neural net was trained using height=320, width=240
        # pxpos[:, 0] = pxpos[:, 0] / ((320 / imgh) * imgh)
        # pxpos[:, 1] = pxpos[:, 1] / ((240 / imgw) * imgw)

        features = np.column_stack((rgb, pxpos))
        features = torch.from_numpy(features).float().to(self.cpuorgpu)
        with torch.no_grad():
            self.net.eval()
            out = self.net(features)

        nx[np.where(cm)] = out[:, 0].cpu().detach().numpy()
        ny[np.where(cm)] = out[:, 1].cpu().detach().numpy()
        # print(nx.min(), nx.max(), ny.min(), ny.max())
        # nx = 2 * ((nx - nx.min()) / (nx.max() - nx.min())) -1
        # ny = 2 * ((ny - ny.min()) / (ny.max() - ny.min())) -1
        # print(nx.min(), nx.max(), ny.min(), ny.max())

        '''OPTION#1 normalize gradient between [a,b]'''
        # a = -5
        # b = 5
        # gx = (b-a) * ((gx - gx.min()) / (gx.max() - gx.min())) + a
        # gy = (b-a) * ((gy - gy.min()) / (gy.max() - gy.min())) + a
        '''OPTION#2 calculate gx, gy from nx, ny. '''
        # nz = np.sqrt(1 - nx ** 2 - ny ** 2)
        # if np.isnan(nz).any():
        #     print ('nan found')
        # nz[np.where(np.isnan(nz))] = 0
        # gx = nx / nz
        # gy = ny / nz
        gx = nx / 0.73
        gy = ny / 0.73

        if MARKER_INTERPOLATE_FLAG:
            # gx, gy = interpolate_gradients(gx, gy, img, cm, cmmm)
            dilated_mm = dilate(markermask, ksize=3, iter=2)
            gx_interp, gy_interp = demark(gx, gy, dilated_mm)
        else:
            gx_interp, gy_interp = gx, gy

        # print (gx.min(), gx.max(), gy.min(), gy.max())
        # nz = np.sqrt(1 - nx ** 2 - ny ** 2) ### normalize normals to get gradients for poisson
        #print(gy_interp.shape)
        boundary = np.zeros((imgh, imgw))

        dm = poisson_reconstruct(gx_interp, gy_interp, boundary)
        dm = np.reshape(dm, (imgh, imgw))
        #print(dm.shape)
        # cv2.imshow('dm',dm)

        ''' remove initial zero depth '''
        if self.dm_zero_counter < 50:
            self.dm_zero += dm
            print ('zeroing depth. do not touch the gel!')
            if self.dm_zero_counter == 49:
                self.dm_zero /= self.dm_zero_counter
        else:
            print ('touch me!')
        self.dm_zero_counter += 1
        dm = dm - self.dm_zero
        # print(dm.min(), dm.max())

        ''' ENTIRE MASK. GPU OPTIMIZED VARIABLES. '''
        # if np.where(cm)[0].shape[0] != 0:
        ### Run things through NN. FAST!!??
        # pxpos = np.vstack(np.where(cm)).T
        # features = np.zeros((len(pxpos), 5))
        # get_features(img, pxpos, features, imgw, imgh)
        # features = torch.from_numpy(features).float().to(device)
        # with torch.no_grad():
        #     net.eval()
        #     out = net(features)
        # # Create gradient images and do reconstuction
        # gradx = torch.from_numpy(np.zeros_like(cm, dtype=np.float32)).to(device)
        # grady = torch.from_numpy(np.zeros_like(cm, dtype=np.float32)).to(device)
        # grady[pxpos[:, 0], pxpos[:, 1]] = out[:, 0]
        # gradx[pxpos[:, 0], pxpos[:, 1]] = out[:, 1]
        # # dm = poisson_reconstruct_gpu(grady, gradx, denom).cpu().numpy()
        # dm = cv2.resize(poisson_reconstruct(grady, gradx, denom).cpu().numpy(), (640, 480))
        # dm = cv2.resize(dm, (imgw, imgh))
        # # dm = np.clip(dm / img.max(), 0, 1)
        # # dm = 255 * dm
        # # dm = dm.astype(np.uint8)

        ''' normalize gradients for plotting purpose '''
        #print(gx.min(), gx.max(), gy.min(), gy.max())
        gx = (gx - gx.min()) / (gx.max() - gx.min())
        gy = (gy - gy.min()) / (gy.max() - gy.min())
        gx_interp = (gx_interp - gx_interp.min()) / (gx_interp.max() - gx_interp.min())
        gy_interp = (gy_interp - gy_interp.min()) / (gy_interp.max() - gy_interp.min())

        return dm


class Visualize3D:
    def __init__(self, n, m, save_path, mmpp):
        self.n, self.m = n, m
        self.init_open3D()
        self.cnt = 212
        self.save_path = save_path
        pass

    def init_open3D(self):
        x = np.arange(self.n)# * mmpp
        y = np.arange(self.m)# * mmpp
        self.X, self.Y = np.meshgrid(x,y)
        Z = np.sin(self.X)

        self.points = np.zeros([self.n * self.m, 3])
        self.points[:, 0] = np.ndarray.flatten(self.X) #/ self.m
        self.points[:, 1] = np.ndarray.flatten(self.Y) #/ self.n

        self.depth2points(Z)

        self.pcd = open3d.geometry.PointCloud()
        self.pcd.points = open3d.utility.Vector3dVector(self.points)
        # self.pcd.colors = Vector3dVector(np.zeros([self.n, self.m, 3]))
        self.vis = open3d.visualization.Visualizer()
        self.vis.create_window(width=640, height=480)
        self.vis.add_geometry(self.pcd)

    def depth2points(self, Z):
        self.points[:, 2] = np.ndarray.flatten(Z)

    def update(self, Z):
        self.depth2points(Z)
        dx, dy = np.gradient(Z)
        dx, dy = dx * 0.5, dy * 0.5

        np_colors = dx + 0.5
        np_colors[np_colors < 0] = 0
        np_colors[np_colors > 1] = 1
        np_colors = np.ndarray.flatten(np_colors)
        colors = np.zeros([self.points.shape[0], 3])
        for _ in range(3): colors[:,_]  = np_colors

        self.pcd.points = open3d.utility.Vector3dVector(self.points)
        self.pcd.colors = open3d.utility.Vector3dVector(colors)

        self.vis.update_geometry(self.pcd)
        self.vis.poll_events()
        self.vis.update_renderer()

        #### SAVE POINT CLOUD TO A FILE
        if self.save_path != '':
            open3d.io.write_point_cloud(self.save_path + "pc_{}.pcd".format(self.cnt), self.pcd)

        self.cnt += 1

    def save_pointcloud(self):
        open3d.io.write_point_cloud(self.save_path + "pc_{}.pcd".format(self.cnt), self.pcd)





