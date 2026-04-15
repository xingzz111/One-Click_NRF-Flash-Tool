# -*- coding: utf-8 -*-
import argparse
import cmd
import os
import traceback
from functools import wraps
from smu001002 import SMU001002
from mix.driver.smartgiant..ipcore.mix_smu001 import MIXSMU001
from ..bus.axi4_lite_bus import AXI4LiteBus
from ..bus.pl_i2c_bus import PLI2CBus
from ..bus.i2c import I2C
from ..utility import utility

__author__ = 'hongshen.wang@SmartGiant'
__version__ = '0.1'


def handle_errors(func):
    @wraps(func)
    def wrapper_func(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(e.message, os.linesep, traceback.format_exc())
    return wrapper_func


class SmuDebuger(cmd.Cmd):
    prompt = 'smu>'
    intro = 'Xavier smu001002 debug tool'

    @handle_errors
    def do_module_init(self, line):
        '''module_init'''
        self.smu.module_init()
        print("Done.")

    @handle_errors
    def do_output(self, line):
        '''output vset vrange iset irange # eg: output 1000 "20V" 1000000 "1mA"'''
        line = line.replace(' ', ',')
        self.smu.output(*list(eval(line)))
        # self.smu.output(eval(line))
        print("Done.")

    @handle_errors
    def do_voltage_readback(self, line):
        '''voltage_readback'''
        result = self.smu.voltage_readback()
        print("Result:")
        print((result))

    @handle_errors
    def do_current_readback(self, line):
        '''current_readback'''
        result = self.smu.current_readback()
        print("Result:")
        print((result))

    @handle_errors
    def do_set_sampling_rate(self, line):
        '''set_sampling_rate channel rate # eg: set_sampling_rate 0 100'''
        line = line.replace(' ', ',')
        self.smu.set_sampling_rate(*list(eval(line)))
        print("Done.")

    @handle_errors
    def do_ad7175_readback(self, line):
        '''ad7175_readback channel # eg: ad7175_readback 0'''
        result = self.smu.ad7175_readback(eval(line))
        print("Result:")
        print(result)

    @handle_errors
    def do_get_sampling_rate(self, line):
        '''get_sampling_rate channel # eg: get_sampling_rate 0'''
        result = self.smu.get_sampling_rate(eval(line))
        print("Result:")
        print(result)

    @handle_errors
    def do_quit(self, line):
        '''quit'''
        return True

    def do_help(self, line):
        '''help'''
        print('Usage:')
        print(self.do_module_init.__doc__)

        print(self.do_output.__doc__)
        print(self.do_voltage_readback.__doc__)
        print(self.do_current_readback.__doc__)
        print(self.do_ad7175_readback.__doc__)
        print(self.do_set_sampling_rate.__doc__)
        print(self.do_get_sampling_rate.__doc__)

        print(self.do_quit.__doc__)
        print(self.do_help.__doc__)


def create_smu_dbg(i2c_bus_name, ipcore_name):
    smu_dbg = SmuDebuger()

    if ipcore_name != '':
        axi4_bus = AXI4LiteBus(ipcore_name, 65535)
        ipcore = MIXSMU001(axi4_bus, "AD7175", ad717x_mvref=2048)

    if i2c_bus_name == '':
        i2c_bus = None
    else:
        if utility.is_pl_device(i2c_bus_name):
            axi4_bus = AXI4LiteBus(i2c_bus_name, 256)
            i2c_bus = PLI2CBus(axi4_bus)
        else:
            i2c_bus = I2C(i2c_bus_name)

    smu_dbg.smu = SMU001002(i2c_bus, ip=ipcore)
    smu_dbg.smu.module_init()
    return smu_dbg


if __name__ == '__main__':
    '''
    ***measure single voltage/current step:
        1.set_measure_path
        2.measure single voltage/current
    ***measure continue voltage/current step:
        1.set_measure_path
        2.enable_continuous_measure
        3.measure continue voltage/current
    ***when from continue mode to single mode,you have to stop_continuous_measure first.
(self, i2c, ad7175=None, vdac_spi=None, idac_spi=None, ip=None):
    '''
    parser = argparse.ArgumentParser()

    parser.add_argument('-i2c', '--i2c', help='cat9555 i2c bus name',
                        default='')

    parser.add_argument('-ip', '--ipcore', help='ipcore devcie name',
                        default='')

    args = parser.parse_args()
    smu_dbg = create_smu_dbg(args.i2c, args.ipcore)

    smu_dbg.cmdloop()
