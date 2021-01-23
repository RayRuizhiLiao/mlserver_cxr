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

from mlserver import transfer_syntax
from mlserver.core import DicomSaver
from mlserver.database import Database
from mlserver.executor import DelayedExecutor
from mlserver.model_cxr_edema import CXRModel
from mlserver.utils import logged_method
from mlserver.utils import try_except
from mlserver.utils import dicom_to_png


flags.DEFINE_string('gin_file', 'config.gin', 'Gin configuration file to load.')
FLAGS = flags.FLAGS


@gin.configurable
class ApplicationEntity(_ApplicationEntity):
    def __init__(self, ae_title, host, port, output_dir='./'):
        super(ApplicationEntity, self).__init__(ae_title=ae_title)

        self._host = host
        self._port = port
        self.output_dir = output_dir

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
    def __init__(self, output_dir):
        """Shared resources across all threads."""
        self._model = CXRModel()
        self._executor = DelayedExecutor()
        self._executor.start()
        self._output_dir = output_dir

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
            f_path = os.path.join(self._output_dir, f'{uname}.png')
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

        if hasattr(ds, 'AccessionNumber'):
            uname = self._create_uname(ds.AccessionNumber)
        elif hasattr(ds, 'StudyID'):
            uname = self._create_uname(ds.StudyID)
        else:
            uname = self._create_uname('_')
            logging.warning(f'Neither AccessionNumber nor StudyID exists, so {uname} is used!')

        dicom_to_png(ds, self._output_dir, uname)
        print(f'PNG image stored: {uname}.png')

        self._process_study(uname)
        # TODO: investigate if it's necessary to delay model inference
        # self._executor.delayed_run(
        #     key=study_name,
        #     fn=functools.partial(self._process_study, study_name=study_name))

    @try_except(error_code=0xC2FF)
    @logged_method
    def _process_study(self, study_name):
        edema_severity, result_img = self._model(self._output_dir, study_name)
        print(f'Study {study_name} has edema severity of {edema_severity}')

        result_png_path = os.path.join(self._output_dir, f"{study_name}_{edema_severity}.png")
        cv2.imwrite(result_png_path, result_img)
        logging.info(f'Grad-CAM PNG image saved at {result_png_path}')
        print(f'Grad-CAM PNG image saved at {result_png_path}')

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
    ae.start_server(evt_handlers=Helper(output_dir=ae.output_dir).handlers)


if __name__ == '__main__':
    app.run(main)