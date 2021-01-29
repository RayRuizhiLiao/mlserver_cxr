#!/usr/bin/env python3

import functools
import gin
import itertools
import warnings
import cv2
import os

from absl import app
from absl import flags
from absl import logging

from pynetdicom import AE as _ApplicationEntity
from pynetdicom import evt
from pynetdicom import StoragePresentationContexts
from pynetdicom import VerificationPresentationContexts

from gradcam.grad_cam import save_gradcam_overlay

from mlserver import transfer_syntax
from mlserver.core import DicomSaver
from mlserver.model_cxr_edema import CXRModel, CXRModelGCam
from mlserver.utils import logged_method
from mlserver.utils import try_except
from mlserver.utils import dicom_to_png
from mlserver.utils import Path


flags.DEFINE_string('gin_file', 'config.gin', 'Gin configuration file to load.')
FLAGS = flags.FLAGS


@gin.configurable
class ApplicationEntity(_ApplicationEntity):
    def __init__(self, ae_title, host, port):
        super(ApplicationEntity, self).__init__(ae_title=ae_title)

        self._host = host
        self._port = port

        contexts = itertools.chain(
            StoragePresentationContexts,
            VerificationPresentationContexts)

        for context in contexts:
            self.add_supported_context(context.abstract_syntax, transfer_syntax)

    def start_server(self, *args, **kwargs):
        logging.info('Server started.')
        logging.info(f'Listening: ({self._host}, {self._port})...')
        print('Server started.')
        print('Listening: ({},{})...'.format(self._host, self._port))
        super(ApplicationEntity, self).start_server(
            (self._host, self._port),
            *args, **kwargs)


# TODO: need to customize this for our cxr algorithm
class Helper(object):
    def __init__(self):
        """Shared resources across all threads."""
        self._model = CXRModelGCam()

    @property
    def handlers(self):
        return [
            (evt.EVT_C_STORE, self.handle_c_store),
            (evt.EVT_C_ECHO, self.handle_c_echo)]

    def _create_uname(self, name: str):
        unique = False
        uid = 1
        while not unique:
            uname = f'{name}_{str(uid)}'
            f_path = Path.png_path(uname)
            if os.path.exists(f_path):
                uid+=1
            else:
                unique = True
        return uname

    @try_except(error_code=0xA700)
    @logged_method
    def handle_c_store(self, event):
        print('Triggered by EVT_C_STORE')
        ds = event.dataset
        ds.file_meta = event.file_meta

        if hasattr(ds, 'PatientID'):
            uname = f"p{ds.PatientID}_"
        else:
            uname = "p_"
        
        if hasattr(ds, 'AccessionNumber'):
            uname += ds.AccessionNumber
        elif hasattr(ds, 'StudyID'):
            uname += ds.StudyID

        uname = self._create_uname(uname)

        dicom_to_png(ds, uname)
        print(f'PNG image stored: {uname}.png')

        self._process_study(uname)

    @try_except(error_code=0xC2FF)
    @logged_method
    def _process_study(self, study_name):
        results_gcam, result_img = self._model(study_name)
        edema_severity, gcam_img, input_img = results_gcam
        print(f'Study {study_name} has edema severity of {edema_severity}')

        result_png_path = Path.png_path(f'{study_name}_{edema_severity}')
        cv2.imwrite(result_png_path, result_img)
        logging.info(f'Resulting PNG image saved at {result_png_path}')
        print(f'Resulting PNG image saved at {result_png_path}')

        gcam_png_path = Path.png_path(f'{study_name}_{edema_severity}_gcam')
        save_gradcam_overlay(gcam_png_path, gcam_img[0], input_img[0])
        logging.info(f'Grad-CAM PNG image saved at {gcam_png_path}')
        print(f'Grad-CAM PNG image saved at {gcam_png_path}')

    @try_except(error_code=0xA701)
    @logged_method
    def handle_c_echo(self, event):
        print('Triggered by EVT_C_ECHO')

        return 0x0000


def main(_):
    gin.parse_config_file(FLAGS.gin_file)
    # warnings.filterwarnings('ignore') #TODO: revisit if this is necessary
    logging.get_absl_handler().use_absl_log_file('mlserver_cxr')

    ae = ApplicationEntity()
    ae.start_server(evt_handlers=Helper().handlers)


if __name__ == '__main__':
    app.run(main)