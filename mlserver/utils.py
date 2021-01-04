import os
import time

from absl import flags
from absl import logging

import cv2
import numpy as np

flags.DEFINE_string('root_dir', '/mnt/data', 'Write received objects to directory.')
FLAGS = flags.FLAGS


def try_except(error_code, default_code=0x0000):
    def _try_except(f):
        def _f(*args, **kwargs):
            try:
                f(*args, **kwargs)
            except Exception as e:
                logging.exception(e)
                return error_code
            else:
                return default_code

        return _f

    return _try_except


def logged_method(f):
    def _f(self, *args, **kwargs):
        tag = f'{self.__class__.__name__}.{f.__name__}(*{args}, **{kwargs})'

        logging.info(f'{tag} -->')
        start = time.time()

        result = f(self, *args, **kwargs)

        interval = time.time() - start
        logging.info(f'[{interval:.3f} s] --> {tag}')
        return result

    return _f


def profiled_method(f):
    try:
        return profile(f)
    except:
        return f


#TODO: modify this to adjust for the cxr algorithms
class Path(object):
    @staticmethod
    def maybe_mkdir(dirpath):
        os.path.isdir(dirpath) or os.makedirs(dirpath)
        return dirpath

    @staticmethod
    def dicom_path(study_name=None, sop_instance_uid=None):
        dicom_root_dir = Path.maybe_mkdir(os.path.join(FLAGS.root_dir, 'dicom'))

        if study_name is None:
            return dicom_root_dir
        else:
            dicom_dir = Path.maybe_mkdir(os.path.join(dicom_root_dir, study_name))

        if sop_instance_uid is None:
            return dicom_dir
        else:
            return os.path.join(dicom_dir, f'{sop_instance_uid}.dcm')

    @staticmethod
    def nifti_path(study_name=None):
        nifti_dir = Path.maybe_mkdir(os.path.join(FLAGS.root_dir, 'nifti'))

        if study_name is None:
            return nifti_dir
        else:
            return os.path.join(nifti_dir, f'{study_name}.nii.gz')

    @staticmethod
    def mask_path(study_name=None):
        mask_dir = Path.maybe_mkdir(os.path.join(FLAGS.root_dir, 'mask'))

        if study_name is None:
            return mask_dir
        else:
            return os.path.join(mask_dir, f'{study_name}.nii.gz')

    @staticmethod
    def mask_json_path(study_name=None, organ=None):
        mask_json_dir = Path.maybe_mkdir(os.path.join(FLAGS.root_dir, 'mask_json'))

        if study_name is None or organ is None:
            return mask_json_dir
        else:
            return os.path.join(mask_json_dir, f'{study_name}-{organ.name.lower()}.json')

    @staticmethod
    def slice_path(study_name=None):
        slice_dir = Path.maybe_mkdir(os.path.join(FLAGS.root_dir, '2dslice'))

        if study_name is None:
            return slice_dir
        else:
            return os.path.join(slice_dir, f'{study_name}.png')


def dicom_to_png(ds, png_dir, png_name):
    img = ds.pixel_array
    img_max_value = ds.LargestImagePixelValue
    img = img.astype(np.double)
    img = img/img_max_value
    img = 65535*img
    img = img.astype(np.uint16)

    png_path = os.path.join(png_dir, png_name+'.png')
    cv2.imwrite(png_path, img)
    print(f"Saved png at {png_path}!")

    return
