import collections
import enum
import gin
import json
import nibabel as nib
import numpy as np
import os
import pandas as pd

from absl import flags
from absl import logging

from mlserver.utils import logged_method
from mlserver.utils import profiled_method
from mlserver.utils import try_except
from mlserver.utils import Path

from resnet_chestxray.model import resnet7_2_1
from resnet_chestxray.model_utils import load_image
from resnet_chestxray.model_utils import CenterCrop
from resnet_chestxray import main_utils

import torch
import torchvision
from torch.utils.data import DataLoader


def run_inference(image_path, model_architecture='resnet7_2_1', 
				  checkpoint_path='/opt/mlmodel/data/pytorch_model_epoch300.bin'):
	device = 'cpu'

	'''
	Create an instance of a resnet model and load a checkpoint
	'''
	output_channels = 4
	if model_architecture == 'resnet7_2_1':
		resnet_model = resnet7_2_1(pretrained=True, 
								   pretrained_model_path=checkpoint_path,
								   output_channels=output_channels)
	resnet_model = resnet_model.to(device)

	'''
	Load the input image
	'''
	image = load_image(image_path)

	'''
	Run model inference on the image
	'''
	pred = main_utils.inference(resnet_model, image)
	pred = pred[0]
	severity = sum([i*pred[i] for i in range(len(pred))])

	return severity

@gin.configurable
class CXRModel(object):
    def __init__(self):

    	return

    #@on_cpu
    @logged_method
    @profiled_method
    def __call__(self, study_name):
        
        png_path = Path.png_path(study_name)

        image = load_image(png_path)
        xray_transform = CenterCrop(2048)
        image = xray_transform(image)
        image = 65535*image
        image = image.astype(np.uint16)

        return run_inference(png_path), image