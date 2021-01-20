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
            (evt.EVT_C_STORE, self.handle_c_store)]

    @try_except(error_code=0xA700)
    @logged_method
    def handle_c_store(self, event):
        print('Triggered by EVT_C_STORE')
        ds = event.dataset
        ds.file_meta = event.file_meta
        # ds.is_little_endian = ds.file_meta.TransferSyntaxUID.is_little_endian
        # ds.is_implicit_VR = ds.file_meta.TransferSyntaxUID.is_implicit_VR

        # DicomSaver()(ds)
        # Database().add(cls=Database.Patient, ds=ds).add(cls=Database.Study, ds=ds)

        # study_name = ds.AccessionNumber
        study_name = ds.StudyID
        dicom_to_png(ds, self._output_dir, study_name)
        self._executor.delayed_run(
            key=study_name,
            fn=functools.partial(self._process_study, study_name=study_name))

    @try_except(error_code=0xC2FF)
    @logged_method
    def _process_study(self, study_name):
        # NiftiConverter()(study_name)

        edema_severity, result_img = self._model(self._output_dir, study_name)

        result_png_path = os.path.join(self._output_dir, f"{study_name}_{edema_severity}.png")
        cv2.imwrite(result_png_path, result_img)

        # JsonConverter()(study_name, organs=self._model.organs)
        # SlicePlotter()(study_name)
        # Database().add(Database.SegmentationVol, study_name=study_name)
        print('Study {} has edema severity of {}'.format(study_name, edema_severity))
        print(f"Grad-CAM PNG image saved at {result_png_path}")


def main(_):
    gin.parse_config_file(FLAGS.gin_file)
    # warnings.filterwarnings('ignore') #TODO: revisit if this is necessary
    logging.get_absl_handler().use_absl_log_file('mlserver')

    ae = ApplicationEntity()
    ae.start_server(evt_handlers=Helper(output_dir=ae.output_dir).handlers)


if __name__ == '__main__':
    app.run(main)