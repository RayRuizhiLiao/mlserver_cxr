import functools
import gin
import itertools
import warnings

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
from mlserver.utils import logged_method
from mlserver.utils import try_except


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
        super(ApplicationEntity, self).start_server(
            (self._host, self._port),
            *args, **kwargs)
