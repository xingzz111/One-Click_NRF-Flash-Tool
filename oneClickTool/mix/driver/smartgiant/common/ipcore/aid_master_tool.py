# -*- coding: utf-8 -*-
import argparse
import cmd
import os
import traceback
from functools import wraps
from mix.driver.smartgiant.common.aid_master import AIDMaster
from mix.driver.smartgiant.common.aid_master import AIDMasterDef
from mix.driver.core.bus.axi4_lite_bus import AXI4LiteBus


def handle_errors(func):
    @wraps(func)
    def wrapper_func(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(e.message, os.linesep, traceback.format_exc())
    return wrapper_func


class AIDMasterDebuger(cmd.Cmd):
    prompt = 'aid>'
    intro = 'Xavier aid slave debug tool'

    @handle_errors
    def do_open(self, line):
        '''open'''
        self.aid.open()
        print('Done.')

    @handle_errors
    def do_close(self, line):
        '''close'''
        self.aid.close()
        print('Done.')

    @handle_errors
    def do_switch_on(self, line):
        '''switch_on'''
        self.aid.switch_on()
        print('Done.')

    @handle_errors
    def do_switch_off(self, line):
        '''switch_off'''
        self.aid.switch_off()
        print('Done.')

    @handle_errors
    def do_detect_poll_on(self, line):
        '''detect_poll_on'''
        self.aid.detect_poll_on()
        print('Done.')

    @handle_errors
    def do_detect_poll_off(self, line):
        '''detect_poll_off'''
        self.aid.detect_poll_off()
        print('Done.')

    @handle_errors
    def do_send_commond(self, line):
        '''send_commond [cmd_req_data]'''
        ret = self.aid.send_commond(eval(line))
        print('result:%r' % ret)

    @handle_errors
    def do_quit(self, line):
        '''quit'''
        return True

    @handle_errors
    def do_help(self, line):
        '''help'''
        print('Usage:')
        print(self.do_open.__doc__)
        print(self.do_close.__doc__)
        print(self.do_switch_on.__doc__)
        print(self.do_switch_off.__doc__)
        print(self.do_detect_poll_on.__doc__)
        print(self.do_detect_poll_off.__doc__)
        print(self.do_send_commond.__doc__)
        print(self.do_quit.__doc__)
        print(self.do_help.__doc__)


def create_aid_dbg(dev_name):
    aid_dbg = AIDMasterDebuger()
    if dev_name == '':
        axi4_bus = None
    else:
        axi4_bus = AXI4LiteBus(dev_name, AIDMasterDef.REG_SIZE)
    aid_dbg.aid = AIDMaster(axi4_bus)
    return aid_dbg


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--device', help='device file name', default='')

    args = parser.parse_args()

    aid_dbg = create_aid_dbg(args.device)

    aid_dbg.cmdloop()
