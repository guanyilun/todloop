import moby2
import numpy as np

from .base import Routine


class TODLoader(Routine):
    def __init__(self, output_key="tod_data", abspath=False, load_opts={}):
        """
        A routine that loads the TOD and save it to a key
        :param output_key: string - key used to save the tod_data
        :param abspath: bool - if the input name is absolute path or just name
        :param load_opts: dict - dictionary with load options
        """
        Routine.__init__(self)
        self._output_key = output_key
        self._fb = None
        self._abspath = abspath
        self._load_opts = load_opts

    def execute(self, store):
        tod_filename = self.get_filename()
        self.logger.info('Loading TOD: %s ...' % tod_filename)

        # define load options
        load_opts = {
            'filename': tod_filename,
            'repair_pointing': True
        }
        load_opts.update(self._load_opts)
        tod_data = moby2.scripting.get_tod(load_opts)
        self.logger.info('TOD loaded')
        store.set(self._output_key, tod_data)  # save tod_data in memory for routines to process


class TODSelector(Routine):
    def __init__(self, tod_list):
        """A routine that takes a list of TOD names and run the TODLoop on 
        the given TOD list based on a base list
        :param: 
            tod_list: a list of tods names to run over"""
        Routine.__init__(self)
        self._tod_list = tod_list 
            
    def execute(self):
        """Scripts that run for each TOD"""
        tod_name = self.get_name()
        if tod_name not in self._tod_list:
            self.veto()  # halt subsequent routines


class FixOpticalSign(Routine):
    """A routine that corrects for optical sign"""
    def __init__(self, input_key="tod_data", output_key="tod_data"):
        Routine.__init__(self)
        self._input_key = input_key
        self._output_key = output_key

    def execute(self, store):
        tod_data = store.get(self._input_key)  # retrieve TOD
        optical_signs = tod_data.info.array_data['optical_sign']
        tod_data.data = tod_data.data*optical_signs[:, np.newaxis]
        store.set(self._output_key, tod_data)


class CalibrateTOD(Routine):
    """A routine that calibrates from DAQ to W"""
    def __init__(self, input_key="tod_data", output_key="tod_data"):
        Routine.__init__(self)
        self._input_key = input_key
        self._output_key = output_key

    def execute(self, store):
        tod = store.get(self._input_key)
        cal = moby2.scripting.get_calibration({'type': 'iv', 'source': 'data'}, tod=tod)
        cal_mask, cal_val = cal.get_property('cal', det_uid=tod.det_uid)
        tod.data *= cal_val[:,None]
        store.set(self._output_key, tod)

