# -*- coding: utf-8 -*-

from mix.driver.core.tracer.recorder import *

__author__ = 'yuanle@SmartGiant'
__version__ = '0.1'


class AIDMasterEmulator(object):
    def __init__(self, dev_name):
        self.dev_name = dev_name
        self._recorder = Recorder()
        add_recorder(self._recorder)

    def open(self):
        self._recorder.record('{} open'.format(self.dev_name))

    def close(self):
        self._recorder.record('{} close'.format(self.dev_name))

    def switch_on(self):
        self._recorder.record("switch on")

    def switch_off(self):
        self._recorder.record("switch off")

    def detect_poll_on(self):
        self._recorder.record(" detect poll on")

    def detect_poll_off(self):
        self._recorder.record("detect poll off")

    def send_commond(self, cmd_req_data):
        record_data = "["
        for i in range(len(cmd_req_data)):
            record_data += "0x%02x" % (cmd_req_data[i])
            if i != len(cmd_req_data) - 1:
                record_data += ", "
        record_data += "]"
        self._recorder.record("send command " + record_data)
        return [0x75, 0x1A, 0x2b, 0x3c, 0x4d, 0x5e, 0x6f, 0xf4]

    def set_parameter(self, T_IBT, T_CYC, T_CYCRD, T_JUDGE, T_BR, T_B, T_W1, T_W0):
        self._recorder.record("set parameter:T_IBT=(%d)" % T_IBT)
