import gin
import nibabel as nib

from mlserver.utils import Path

@gin.configurable
class DicomSaver(object):
    def __call__(self, ds):
        ds.save_as(
            Path.dicom_path(ds.AccessionNumber, ds.SOPInstanceUID),
            write_like_original=False)