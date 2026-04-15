# -*- coding: utf-8 -*-
import argparse
import cmd
import os
import traceback
import inspect
from functools import wraps
from mix.driver.smartgiant.sg22055te01pca.module.sg22055te01pca import SG22055TE01PCA
from mix.driver.smartgiant.sg2284pw01pca.module.sg2284pw01pca import SG2284PW01PCA
from mix.driver.smartgiant.mimic.module.mimic import Mimic
from mix.driver.core.bus.axi4_lite_bus import AXI4LiteBus
from mix.driver.smartgiant.common.bus.pl_i2c_bus import PLI2CBus
from mix.driver.core.bus.i2c import I2C
from mix.driver.core.utility import utility

__author__ = 'Jiasheng.Xie@SmartGiant'
__version__ = '0.1'


def handle_errors(func):
    @wraps(func)
    def wrapper_func(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(e.message, os.linesep, traceback.format_exc())
    return wrapper_func


def get_function_doc(self=None):
    '''Get function.__doc__ '''
    func_name = inspect.stack()[1][3]
    if self is None:
        return eval('%s' % func_name).__doc__
    else:
        return getattr(self, func_name).__doc__


class SG22055TE01PCADebuger(cmd.Cmd):
    prompt = 'SG22055TE01PCA>'
    intro = 'Xavier SG22055TE01PCA debug tool, Type help or ? to list commands.\n'

    @handle_errors
    def do_module_init(self, line):
        '''module_init
        Need to call it once after module instance is created'''
        if '?' == line:
            print(get_function_doc(self))
            return None
        self.sg22055te01pca.module_init()
        print("Done.")

    @handle_errors
    def do_set_readback_path(self, line):
        '''set_readback_path range_name
        sg22055te01pca set readback path.
        range_name:     string, [POWER_VOLT, POWER_CURR, ELOAD_CURR, READBACK_RELEASE].
        eg:           set_readback_path 'POWER_VOLT'
        '''
        if '?' == line:
            print(get_function_doc(self))
            return None
        # line = line.replace(' ', ',')
        self.sg22055te01pca.set_readback_path(eval(line))
        print("Done.")

    @handle_errors
    def do_power_voltage_readback(self, line):
        '''power_voltage_readback
        sg22055te01pca readback voltage of power board.
        eg: power_voltage_readback'''
        if '?' == line:
            print(get_function_doc(self))
            return None
        result = self.sg22055te01pca.power_voltage_readback()
        print("Result:")
        print(result)

    @handle_errors
    def do_power_current_readback(self, line):
        '''power_current_readback
        readback power current.
        eg: power_current_readback '''
        if '?' == line:
            print(get_function_doc(self))
            return None
        result = self.sg22055te01pca.power_current_readback()
        print("Result:")
        print(result)

    @handle_errors
    def do_eload_current_readback(self, line):
        '''eload_current_readback.
        sg22055te01pca readback current of eload.
        eg: eload_current_readback '''
        if '?' == line:
            print(get_function_doc(self))
            return None
        result = self.sg22055te01pca.eload_current_readback()
        print("Result:")
        print(result)

    @handle_errors
    def do_quit(self, line):
        '''quit
        Exit'''
        if '?' == line:
            print(get_function_doc(self))
            return None
        return True

    @handle_errors
    def do_help(self, line):
        '''help
        Usage'''
        print('Usage:')
        for name, attr in inspect.getmembers(self):
            if 'do_' in name:
                print(attr.__doc__)


def create_sg22055te01pca_dbg(i2c_bus_name):
    sg22055te01pca_dbg = SG22055TE01PCADebuger()

    if i2c_bus_name == '':
        i2c_bus_name = None
    else:
        if utility.is_pl_device(eeprom_i2c_bus_name):
            axi4_bus = AXI4LiteBus(eeprom_i2c_bus_name, 256)
            i2c_bus_name = PLI2CBus(axi4_bus)
        else:
            i2c_bus_name = I2C(i2c_bus_name)

    sg22055te01pca_dbg.sg22055te01pca = SG22055TE01PCA(i2c_bus_name, None, None)
    return sg22055te01pca_dbg


if __name__ == '__main__':
    '''
    ***setup:
        module_init
    ***enable output power step:
        1.power_output 'batt' 1000
        2.power_enable 'batt'
    ***set the resistor limit step:
        1.resistor_set 'vddmain' 300
    ***when you control the power must be module init first.
    '''

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--i2c', help='i2c bus name',
                        default='')

    args = parser.parse_args()
    sg22055te01pca_dbg = create_sg22055te01pca_dbg(args.i2c)

    sg22055te01pca_dbg.cmdloop()
