# -*- coding: utf-8 -*-
import os
import logging
import ctypes
from ctypes import *

__author__ = 'wudan@SmartGiant'
__version__ = '0.1'


def load_lib():
    '''
    Load barcode library function
    :example:
            lib = load_lib()
    '''

    lib_file = os.environ.get('', '/usr/local/lib/') + 'libBarCode.so'

    if not os.access(lib_file, os.R_OK):
        logger = logging.getLogger(__name__)
        logger.error('Can not access BarCode library:' + lib_file)
        return None

    return ctypes.cdll.LoadLibrary(lib_file)


def to_c_pointer(value):
    '''
    convert python value type to C pointer
    '''
    # value_type: int(0-2),         Data type 0--bool 1--int 2--str
    value_type = 3
    if type(value) is bool:
        value_type = 0
        p_value = pointer(c_bool(value))
    if type(value) is int:
        value_type = 1
        p_value = pointer(c_int(value))
    if type(value) is str or type(value) is unicode:
        value_type = 2
        p_value = value.encode('utf-8')

    assert value_type >= 0 and value_type < 3

    return value_type, p_value


class Cyclops(object):

    rpc_public_api = ['decode', 'decode_local_image', 'transmit_img', 'write_config', 'write_item_config', 
	                  'add_reverse_item', 'read_reverse_item', 'write_reverse_item', 
                        'write_config_to_flash', 'read_config', 'read_item_config', 'read_cam_sn']

    def __init__(self, port_index):
        '''
        To create a Cyclops
        '''
        self._barcode_lib_inst = load_lib()
        if self._barcode_lib_inst is None:
            raise Exception('Load BarCode library failure!')
        # Get the path of local BarCodeConfig.json
        config_path = os.path.split(os.path.realpath(__file__))[0]
        self.cptr = self._barcode_lib_inst.Init(config_path, port_index)

    def decode(self, timeout):
        '''
        Cyclops capture a image and decode it

        :param:     timeout:   int(usually set 0-15000),  ms,
                               Usually used for debugging
        :example:
                    data = cyclops.decode(5000)
                    print(data)
        '''
        assert timeout >= 0
        result = ctypes.create_string_buffer(256)
        self._barcode_lib_inst.Decode(self.cptr, timeout, result)
        return result.raw.decode('utf-8')

    def decode_local_image(self, img_path):
        '''
        Cyclops read a local image and decode it

        :param:     img_path:   str, The full path of image
        :example:
                    cyclops.decode_local_image('/opt/seeing/log/test.jpg')
        '''
        result = ctypes.create_string_buffer(256)
        self._barcode_lib_inst.DecodeImg(self.cptr, img_path.encode('utf-8'), result)
        return result.raw.decode('utf-8')

    def transmit_img(self):
        '''
        Cyclops capture a image and return image path

        :example:
                    cyclops.transmit_img()
        '''
        img_path = ctypes.create_string_buffer(256)
        self._barcode_lib_inst.TransmitImg(self.cptr, img_path)
        return  img_path.raw.decode('utf-8')

    def _get_config_value_type(self, key_name):
        '''
        Cyclops get a json config value type: 0--bool 1--int 2--str

        :param:     key_name:   str,           Json key name
        :example:
                    type = cyclops._get_config_value_type('BlackBarCode')
        '''
        result = self._barcode_lib_inst.GetConfigValueType(self.cptr, key_name.encode('utf-8'))
        return result

    def _get_item_config_value_type(self, item_name, key_name):
        '''
        Cyclops get a json item config value type: 0--bool 1--int 2--str

        :param:     item_name:  str,           Json item name
        :param:     key_name:   str,           Json key name
        :example:
                    type = cyclops._get_item_config_value_type('ROI1', 'ExposureValue')
        '''
        result = self._barcode_lib_inst.GetItemConfigValueType(
            self.cptr, item_name.encode('utf-8'), key_name.encode('utf-8'))
        return result

    def _get_reverse_value_type(self, key_name):
        '''
        Cyclops get a reverse value type: 0--bool 1--int 2--str


        :param:     key_name:   str,           Json key name
        :example:
                    type = cyclops._get_reverse_value_type('Setting')
        '''
        result = self._barcode_lib_inst.GetReverseValueType(self.cptr, key_name.encode('utf-8'))
        return result

    def write_config(self, key_name, key_value):
        '''
        Cyclops write a json key value to config file

        :param:     key_name:   str,           Json key name
        :param:     key_value:  bool/int/str,  Json key value
        :example:
                    cyclops.write_config('BlackBarCode', True)
        '''
        config_type = self._get_config_value_type(key_name)
        value_type, p_key_value = to_c_pointer(key_value)
        assert config_type == value_type
        result = self._barcode_lib_inst.WriteConfig(
            self.cptr, key_name.encode('utf-8'), value_type, p_key_value)
        return result

    def write_item_config(self, item_name, key_name, key_value):
        '''
        Cyclops write a json item value to config file

        :param:     item_name:   str,          Json item name
        :param:     key_name:   str,           Json key name
        :param:     key_value:  bool/int/str,  Json key value
        :example:
                    cyclops.write_item_config('ROI1', 'ExposureValue', -1)
        '''
        config_type = self._get_item_config_value_type(item_name, key_name)
        value_type, p_key_value = to_c_pointer(key_value)
        assert config_type == value_type
        result = self._barcode_lib_inst.WriteItemConfig(self.cptr, item_name.encode('utf-8'),
            key_name.encode('utf-8'), value_type, p_key_value)
        return result

    def add_reverse_item(self, key_name, key_value):
        '''
        Cyclops write a json item value to config file

        :param:     key_name:   str,           Json key name
        :param:     key_value:  bool/int/str,  Json key value
        :example:
                    cyclops.add_reverse_item('Setting', 10)
        '''
        value_type, p_key_value = to_c_pointer(key_value)	
        result = self._barcode_lib_inst.AddReverseItem(self.cptr, 
            key_name.encode('utf-8'), value_type, p_key_value)
        return result

    def read_reverse_item(self, key_name):
        '''

        Cyclops read a json key value from config file

        :param:     key_name:   str,           Json key name
        :example:
                    key_value = cyclops.read_reverse_item('setting')
        '''
        config_type = self._get_reverse_value_type(key_name)
        assert config_type >= 0 and config_type < 3
        if config_type == 0:
            key_value = pointer(c_bool(True))
            self._barcode_lib_inst.ReadReverseItem(

                self.cptr, key_name.encode('utf-8'), config_type, key_value)
            return key_value.contents.value
        elif config_type == 1:
            key_value = pointer(c_int(1))
            self._barcode_lib_inst.ReadReverseItem(
                self.cptr, key_name.encode('utf-8'), config_type, key_value)
            return key_value.contents.value
        else:
            key_value = ctypes.create_string_buffer(40)
            self._barcode_lib_inst.ReadReverseItem(
                self.cptr, key_name.encode('utf-8'), config_type, key_value)
            return key_value.raw.decode('utf-8')

    def write_reverse_item(self, key_name, key_value):
        '''
        Cyclops write a json item value to config file

        :param:     key_name:   str,           Json key name
        :param:     key_value:  bool/int/str,  Json key value
        :example:
                    cyclops.write_reverse_item('Setting', 10)
        '''
        config_type = self._get_reverse_value_type(key_name)
        value_type, p_key_value = to_c_pointer(key_value)
        assert config_type == value_type	
        result = self._barcode_lib_inst.WriteReverseItem(self.cptr, 
            key_name.encode('utf-8'), value_type, p_key_value)
        return result

    def write_config_to_flash(self):
        '''
        Cyclops save config to flash

        :example:
                    cyclops.write_config_to_flash()
        '''
        result = self._barcode_lib_inst.WriteJsonToFlash(self.cptr)
        return result

    def read_config(self, key_name):
        '''
        Cyclops read a json key value from config file

        :param:     key_name:   str,           Json key name
        :example:
                    key_value = cyclops.read_config('BlackBarCode')
        '''
        config_type = self._get_config_value_type(key_name)
        assert config_type >= 0 and config_type < 3
        if config_type == 0:
            key_value = pointer(c_bool(True))
            self._barcode_lib_inst.ReadConfig(
                self.cptr, key_name.encode('utf-8'), config_type, key_value)
            return key_value.contents.value
        elif config_type == 1:
            key_value = pointer(c_int(1))
            self._barcode_lib_inst.ReadConfig(
                self.cptr, key_name.encode('utf-8'), config_type, key_value)
            return key_value.contents.value
        else:
            key_value = ctypes.create_string_buffer(40)
            self._barcode_lib_inst.ReadConfig(
                self.cptr, key_name.encode('utf-8'), config_type, key_value)
            return key_value.raw.decode('utf-8')

    def read_item_config(self, item_name, key_name):
        '''
        Cyclops read a json item value from config file

        :param:     item_name:   str,          Json item name
        :param:     key_name:    str,          Json key name
        :example:
                    key_value = cyclops.ReadItemConfig('NetPort', '6543')
        '''
        config_type = self._get_item_config_value_type(item_name, key_name)
        assert config_type >= 0 and config_type < 3
        if config_type == 0:
            key_value = pointer(c_bool(True))
            self._barcode_lib_inst.ReadItemConfig(self.cptr, item_name.encode('utf-8'),
                key_name.encode('utf-8'), config_type, key_value)
            return key_value.contents.value
        elif config_type == 1:
            key_value = pointer(c_int(1))
            self._barcode_lib_inst.ReadItemConfig(self.cptr, item_name.encode('utf-8'),
                key_name.encode('utf-8'), config_type, key_value)
            return key_value.contents.value
        else:
            key_value = ctypes.create_string_buffer(40)
            self._barcode_lib_inst.ReadItemConfig(self.cptr, item_name.encode('utf-8'),
                key_name.encode('utf-8'), config_type, key_value)
            return key_value.raw.decode('utf-8')

    def read_cam_sn(self):  
        '''
        Cyclops read camera sn

        :example:
                    cam_sn = cyclops.read_cam_sn()
        '''      
        result = self._barcode_lib_inst.ReadCamSN(self.cptr)
        return result
