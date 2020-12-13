import pydicom.uid as uid

transfer_syntax = [
    uid.ExplicitVRLittleEndian,
    uid.ImplicitVRLittleEndian,
    uid.ExplicitVRBigEndian,
    uid.DeflatedExplicitVRLittleEndian,
    uid.JPEGBaseline,
    uid.JPEGExtended,
    uid.JPEGLosslessP14,
    uid.JPEGLossless,
    uid.JPEGLSLossless,
    uid.JPEGLSLossy,
    uid.JPEG2000Lossless,
    uid.JPEG2000,
    uid.JPEG2000MultiComponentLossless,
    uid.JPEG2000MultiComponent,
    uid.RLELossless]