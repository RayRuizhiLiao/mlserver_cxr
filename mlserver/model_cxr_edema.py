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


@gin.configurable
class PseudoModel(object):
    def __init__(self):

    	return

    @on_cpu
    @logged_method
    @profiled_method
    def __call__(self, study_name):
        
        return 1