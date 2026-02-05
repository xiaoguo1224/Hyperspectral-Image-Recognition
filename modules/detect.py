import argparse
import warnings
from tkinter import Image

import torch
import torch.nn as nn
import os

from jedi.api.file_name import complete_file_name
from scipy.constants import blob
from torch.utils.data import DataLoader
import torch.optim as optim
from torchvision import utils
import glob
import sys

from assistant.dataloader import HL_SC
from models.evaluate_function import evaluate

sys.path.append("..")
from models.DSST import ACEN

pre_net = '../outputs/DMSSN_double_epoch_100.pth'
dir_output = '../outputs/pic/'
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

warnings.filterwarnings("ignore")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = ACEN()


def init_model():
    global model
    print("[INFO] loading model...")
    model.to(device)
    checkpoint = torch.load(pre_net)
    model.load_state_dict(checkpoint, strict=False)
    print("[INFO] model loaded")


def data_process(picList, fileList, batchsize=6):
    '''
    :param pic: 图片
    :param file: 高光谱文件
    :return:
    '''
    test_dataset = HL_SC(img_list=picList, file_list=fileList)
    test_dataloader = DataLoader(test_dataset, batch_size=batchsize, num_workers=0, drop_last=False)
    return test_dataloader


def save_image_tensor(input_tensor: torch.Tensor, filename):
    input_tensor = input_tensor.clone().detach()
    input_tensor = input_tensor.to(torch.device('cpu'))
    utils.save_image(input_tensor, filename)


def test(model, test_loader, batchsize=6):
    model.eval()
    mini_batch = batchsize
    complete_file_list = []
    error_list = []
    with torch.no_grad():
        for i, data in enumerate(test_loader):
            inputs, name = data['image'], data['id']
            inputs_v = inputs.to(device)
            _, _, _, _, out = model(inputs_v)
            for j in range(mini_batch):
                try:
                    draw, id = out[j, :, :, :], name[j]
                    draw = (draw - torch.min(draw)) / (torch.max(draw) - torch.min(draw))
                    draw = torch.swapaxes(draw, 2, 1)
                    save_image_tensor(draw, os.path.join(dir_output, id + ".jpg"))
                    complete_file_list.append(os.path.join(dir_output, id + ".jpg"))
                except:
                    error_list.append(id)
                finally:
                    pass
    return error_list, complete_file_list


def main(picList, fileList):
    test_dataloader = data_process(picList, fileList)
    if not os.path.exists(dir_output):
        os.makedirs(dir_output)
    test_error_list, test_complete_file_list = test(model, test_dataloader, batchsize=6)
    return test_error_list, test_complete_file_list


if __name__ == "__main__":
    init_model()
    picList = glob.glob("../data/pic/*.jpg")
    fileList = glob.glob("../data/mat/*.mat")
    main(picList, fileList)
