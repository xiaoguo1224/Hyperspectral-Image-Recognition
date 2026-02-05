import os

from torch.utils.data import Dataset
from skimage import io, transform
import numpy as np
import scipy.io as scio
import sys
from assistant.sc_norm import *
from assistant.data_aug import *


def normalize_sc(data):
    for i in range(data.shape[0]):
        data[i, :, :] = (data[i, :, :] - mean_sc[i]) / std_sc[i]
    data = (data - np.min(data)) / (np.max(data) - np.min(data))
    return data


class HL_SC(Dataset):
    def __init__(self, img_list, file_list):
        self.image_list = img_list
        self.file_list = file_list
        self.fileMap = {}
        for idx, img in enumerate(self.image_list):
            name = os.path.basename(img)
            id = os.path.splitext(name)[0]
            self.fileMap[id] = file_list[idx]

    def __len__(self):
        return len(self.image_list)

    def __getitem__(self, idx):
        name = os.path.basename(self.image_list[idx])
        id = os.path.splitext(name)[0]
        image_mat = scio.loadmat(self.fileMap[id])
        image = image_mat['data']
        image = image.astype(np.float32)
        image_norm = normalize_sc(image)

        img = image_norm.astype(np.float32)

        sample = {'image': img.copy(), 'id': id}

        return sample
