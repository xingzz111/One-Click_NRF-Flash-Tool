# -*- coding: utf-8 -*-
import argparse
import cmd
import os
import traceback
import inspect
from functools import wraps
from mix.driver.smartgiant.sg2284pw01pca.module.sg2284pw01pca import SG2284PW01PCA
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


class SG2284PW01PCADebuger(cmd.Cmd):
    prompt = 'SG2284PW01PCA>'
    intro = 'Xavier SG2284PW01PCA debug tool, Type help or ? to list commands.\n'

    @handle_errors
    def do_module_init(self, line):
        '''module_init
        Need to call it once after module instance is created'''
        if '?' == line:
            print(get_function_doc(self))
            return None
        self.sg2284pw01pca.module_init()
        print("Done.")

    @handle_errors
    def do_power_control(self, line):
        '''power_control state
        control power on or off.
        state:  string, [on, off], state enable control.
        eg:           power_control 'on'
        '''
        if '?' == line:
            print(get_function_doc(self))
            return None
        # line = line.replace(' ', ',')
        self.sg2284pw01pca.power_control(eval(line))
        print("Done.")

    @handle_errors
    def do_power_voltage_output(self, line):
        '''power_voltage_output voltage
        power mode output voltage
        voltage:    int/float(500~7000).
        eg: power_voltage_output 1000.0' '''
        if '?' == line:
            print(get_function_doc(self))
            return None
        self.sg2284pw01pca.power_voltage_output(eval(line))
        print("Done.")

    @handle_errors
    def do_power_readback_voltage_calc(self, line):
        '''power_readback_voltage_calc voltage
        readback power voltage.
        voltage:    int/float(500~7000).
        eg: power_readback_voltage_calc 1000 '''
        if '?' == line:
            print(get_function_doc(self))
            return None
        result = self.sg2284pw01pca.power_readback_voltage_calc(eval(line))
        print("Result:")
        print(result)

    @handle_errors
    def do_power_readback_current_calc(self, line):
        '''power_readback_current_calc voltage
        readback power current.
        voltage:    float, ADC read back voltage, unit mV..
        eg: power_readback_current_calc 200.0
        '''
        if '?' == line:
            print(get_function_doc(self))
            return None
        result = self.sg2284pw01pca.power_readback_current_calc(eval(line))
        print("Result:")
        print(result)

    @handle_errors
    def do_eload_control(self, line):
        '''eload_control state
        control eload on or off.
        state:  string, [on, off], state enable control.
        eg: eload_control "off"
        '''
        if '?' == line:
            print(get_function_doc(self))
            return None
        result = self.sg2284pw01pca.eload_control(eval(line))
        print("Result:")
        print(result)

    @handle_errors
    def do_eload_output_current(self, line):
        '''eload_output_current current
        eload output current.
        current:    float, , unit mA, value of output current.
        eg: eload_output_current 2000'''
        if '?' == line:
            print(get_function_doc(self))
            return None
        self.sg2284pw01pca.eload_output_current(eval(line))
        print("Done.")

    @handle_errors
    def do_eload_readback_current_calc(self, line):
        '''eload_readback_current_calc voltage
        readback eload current.
        voltage:    float, unit mV, voltage value from ADC read back.
        eg: eload_readback_current_calc 100 '''
        if '?' == line:
            print(get_function_doc(self))
            return None
        result = self.sg2284pw01pca.eload_readback_current_calc(eval(line))
        print("Result:")
        print(result)

    @handle_errors
    def do_set_calibration_mode(self, line):
        '''set_calibration_mode
        enable calibration mode
        mode: str("raw", "cal")
        eg: set_calibration_mode "raw"'''
        if '?' == line:
            print(get_function_doc(self))
            return None
        self.sg2284pw01pca.set_calibration_mode(eval(line))
        print('Done.')

    @handle_errors
    def do_is_use_cal_data(self, line):
        '''is_use_cal_data
        query calibration mode if is enabled'''
        if '?' == line:
            print(get_function_doc(self))
            return None
        result = self.sg2284pw01pca.is_use_cal_data()
        print('Result:')
        print(result)

    @handle_errors
    def do_get_calibration_mode(self, line):
        '''get_calibration_mode
        get calibration mode
        eg: get_calibration_mode'''
        if '?' == line:
            print(get_function_doc(self))
            return None
        result = self.sg2284pw01pca.get_calibration_mode()
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


def create_sg2284pw01pca_dbg(i2c_bus_name):
    sg2284pw01pca_dbg = SG2284PW01PCADebuger()

    if i2c_bus_name == '':
        i2c_bus_name = None
    else:
        if utility.is_pl_device(eeprom_i2c_bus_name):
            axi4_bus = AXI4LiteBus(eeprom_i2c_bus_name, 256)
            i2c_bus_name = PLI2CBus(axi4_bus)
        else:
            i2c_bus_name = I2C(i2c_bus_name)

    sg2284pw01pca_dbg.sg2284pw01pca = SG2284PW01PCA(i2c_bus_name)
    return sg2284pw01pca_dbg


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
    sg2284pw01pca_dbg = create_sg2284pw01pca_dbg(args.i2c)

    sg2284pw01pca_dbg.cmdloop()
