import datetime
import gin
import json
import os
import pandas as pd
import sqlalchemy as sa
import sqlalchemy.ext.declarative as sa_ext_declarative
import sqlalchemy.inspection as sa_inspection
import urllib

from absl import logging

from mlserver.utils import Path

#TODO: modify this to adjust for the cxr algorithms/database
@gin.configurable
class Database(object):
    Base = sa_ext_declarative.declarative_base()

    class Patient(Base):
        __tablename__ = 'PatientData'

        MRN = sa.Column(sa.String(50), primary_key=True)
        PtName = sa.Column(sa.String(100))
        PtSex = sa.Column(sa.String(16))

        @classmethod
        def from_args(cls, ds):
            return cls(
                MRN=ds.PatientID,
                PtName=str(ds.PatientName),
                PtSex=ds.PatientSex)

    class Study(Base):
        __tablename__ = 'StudyData'

        ANum = sa.Column(sa.String(50), primary_key=True)
        MRN = sa.Column(sa.String(50), sa.ForeignKey('PatientData.MRN'))
        StudyDesc = sa.Column(sa.String(200))
        PtAge = sa.Column(sa.String(4))

        @classmethod
        def from_args(cls, ds):
            return cls(
                ANum=ds.AccessionNumber,
                MRN=ds.PatientID,
                StudyDesc=ds.StudyDescription,
                PtAge=getattr(ds, 'PatientAge'))

    class SegmentationVol(Base):
        __tablename__ = 'SegVolData'

        ANum = sa.Column(sa.String, primary_key=True)
        SpleenVolCC = sa.Column(sa.Numeric(4, 0))
        RightKidneyVolCC = sa.Column(sa.Numeric(4, 0))
        LeftKidneyVolCC = sa.Column(sa.Numeric(4, 0))
        LiverVolCC = sa.Column(sa.Numeric(4, 0))
        PancreasVolCC = sa.Column(sa.Numeric(4, 0))
        UpdateDtTm = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)

        @classmethod
        def from_args(cls, study_name):
            volumes_cc = {}
            for organ in Organ:
                if organ is Organ.BACKGROUND:
                    continue

                path = Path.mask_json_path(study_name, organ)
                if not os.path.isfile(path):
                    continue

                with open(path) as f:
                    json_obj = json.load(f)

                volumes_cc[organ] = int(json_obj['volume'] / 1000)

            return cls(
                ANum=study_name,
                SpleenVolCC=volumes_cc.get(Organ.SPLEEN),
                RightKidneyVolCC=volumes_cc.get(Organ.RIGHT_KIDNEY),
                LeftKidneyVolCC=volumes_cc.get(Organ.LEFT_KIDNEY),
                LiverVolCC=volumes_cc.get(Organ.LIVER),
                PancreasVolCC=volumes_cc.get(Organ.PANCREAS))

    def __init__(self, username, password, server, database, driver):
        params = urllib.parse.quote_plus(
            f'UID={username};'
            f'PWD={password};'
            f'SERVER={server};'
            f'DATABASE={database};'
            f'DRIVER={driver};')

        engine = sa.create_engine(f'mssql+pyodbc:///?odbc_connect={params}', echo=False)

        self.sess = sa.orm.sessionmaker(bind=engine)()

    def add(self, cls, force=True, *args, **kwargs):
        data = cls.from_args(*args, **kwargs)
        primary_keys = sa_inspection.inspect(cls).primary_key

        _data = (
            self.sess
            .query(cls)
            .filter(*[
                getattr(cls, key.name) == getattr(data, key.name)
                for key in primary_keys])
            .first())

        if _data is None:
            self.sess.add(data)
            logging.info(f'Adding to database {data.__dict__}')

        elif force:
            self.sess.merge(data)
            logging.info(f'Merging to database {data.__dict__}')

        self.sess.commit()
        return self

    def query(self, cls):
        query = self.sess.query(cls)
        df = pd.read_sql(query.statement, self.sess.bind)
        logging.info(df)

        return self