# -*- coding: utf-8 -*-

import argparse
import cmd
import os
import traceback
from functools import wraps

from mix.driver.core.bus.axi4_lite_bus import AXI4LiteBus
from mix.driver.smartgiant.common.ipcore.mix_ad7124_sg import *

__author__ = 'shunreng.he@SmartGiant'
__version__ = '0.1'


def handle_errors(func):
    @wraps(func)
    def wrapper_func(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(e.message, os.linesep, traceback.format_exc())
    return wrapper_func


class MIXAd712XSGDebuger(cmd.Cmd):
    prompt = 'ad7124>'
    intro = 'Xavier ad7124 debug tool'

    @handle_errors
    def do_read_register(self, line):
        '''read_register reg_addr '''
        line = line.replace(' ', ',')
        data = self.ad7124.read_register(eval(line))
        print('Result:')
        print(data)
        return

    @handle_errors
    def do_write_register(self, line):
        '''write_register register_address data'''
        line = line.replace(' ', ',')
        self.ad7124.write_register(*list(eval(line)))
        print('Done')
        return

    @handle_errors
    def do_set_filter_register(self, line):
        '''set_sinc channel sinc '''
        line = line.replace(' ', ',')
        self.ad7124.set_sinc(*list(eval(line)))
        print('Done')
        return

    @handle_errors
    def do_set_sampling_rate(self, line):
        '''set_sampling_rate channel sampling_rate '''
        line = line.replace(' ', ',')
        self.ad7124.set_sampling_rate(*list(eval(line)))
        print('Done')
        return

    @handle_errors
    def do_get_sampling_rate(self, line):
        '''get_sampling_rate channel'''
        result = self.ad7124.get_sampling_rate(eval(line))
        print('Result:')
        print(result)
        return

    @handle_errors
    def do_read_volt(self, line):
        '''read_volt channel'''
        result = self.ad7124.read_volt(eval(line))
        print('Result:')
        print(result)
        return

    @handle_errors
    def do_is_communication_ok(self, line):
        '''is_communication_ok'''
        self.ad7124.is_communication_ok()
        print('Done')
        return

    @handle_errors
    def do_enable_continuous_sampling(self, line):
        '''enable_continuous_sampling channel sampling_rate '''
        line = line.replace(' ', ',')
        self.ad7124.enable_continuous_sampling(*list(eval(line)))
        print('Done')
        return

    @handle_errors
    def do_disable_continuous_sampling(self, line):
        '''disable_continuous_sampling'''
        self.ad7124.disable_continuous_sampling()
        print('Done')
        return

    @handle_errors
    def do_channel_init(self, line):
        '''channel_init'''
        result = self.ad7124.channel_init()
        print('Result:')
        print(result)
        return

    @handle_errors
    def do_read_multi_channel_volt(self, line):
        '''read_multi_channel_volt channel_num'''
        line = line.replace(' ', ',')
        result = self.ad7124.read_multi_channel_volt((eval(line)))
        print('Result:')
        print(result)
        return

    @handle_errors
    def do_quit(self, line):
        '''quit'''
        return True

    @handle_errors
    def do_help(self, line):
        print("Usage:")
        print(self.do_read_register.__doc__)
        print(self.do_write_register.__doc__)
        print(self.do_set_filter_register.__doc__)
        print(self.do_set_sampling_rate.__doc__)
        print(self.do_get_sampling_rate.__doc__)
        print(self.do_read_volt.__doc__)
        print(self.do_is_communication_ok.__doc__)
        print(self.do_enable_continuous_sampling.__doc__)
        print(self.do_disable_continuous_sampling.__doc__)
        print(self.do_read_multi_channel_volt.__doc__)
        print(self.do_quit.__doc__)


def create_ad7124_dbg(dev_name, vref):
    ad7124_dbg = MIXAd712XSGDebuger()
    vref = int(vref)
    if dev_name == '':
        axi4_bus = None
    else:
        axi4_bus = AXI4LiteBus(dev_name, 8192)
    ad7124_dbg.ad7124 = MIXAd7124SG(axi4_bus, vref)
    return ad7124_dbg


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--device', help='device file name', default='/dev/MIX_AD712X_SG_0')
    parser.add_argument('-v', '--vref', help='device reference voltage', default=2500)
    args = parser.parse_args()

    ad7124_dbg = create_ad7124_dbg(args.device, args.vref)

    ad7124_dbg.cmdloop()
