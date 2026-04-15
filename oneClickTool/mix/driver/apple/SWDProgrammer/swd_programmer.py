import time
import sys
import os
import tempfile
import base64
import hashlib
from subprocess import PIPE, Popen
from threading import Timer
import struct

class SWDProgrammer():
    rpc_public_api = ['program_mcu', 'mass_erase', 'verify', 'protect', 'dump_bank', 'dump_chip_protection_status']

    rpc_public_api += ['program_kamet_otp', 'program_kamet_otp_blob']

    def __init__(self, slot_id, target_device=None):
        self.slot_id = slot_id
        self.target_device = target_device
        self.running_process = None

    def kill_process_on_timeout(self):
        if self.running_process:
            print("---------------------------------------------------------------------------------------")
            print("---------------------------- Process timed out. Killing it ----------------------------")
            print("---------------------------------------------------------------------------------------")
            self.running_process.kill()
            self.running_process = None
        else:
            print("Error. No process defined, cannot kill it")

    def cmdline(self, command, process_timeout=200):
        print (command)
        process = Popen( args=command, cwd=r'/mix/driver/apple/SWDProgrammer/',stdout=PIPE, stderr=PIPE, shell=True)
        self.running_process = process
        timer = Timer(process_timeout, self.kill_process_on_timeout)
        try:
            timer.start()    
            result = process.communicate()
        finally:
            timer.cancel()
        print(result[0])
        print(result[1])
        return result[0]+result[1]

    def executeOpenOCDSingleCommand(self, command, perform_reset_init=True, ccgx_flash_auto_erase_on=False, add_exit_commands=True):

        reset_init = " -c \"reset init\""
        use_host_interface = ""
        ccgx_flash_auto_erase_on_cmd = ""

        if (self.target_device[:3].lower() == "ccg"):
            reset_init = " -c \"reset_init_retry 10\""
            if (command.find("mass_erase") >= 0):
                use_host_interface = " -c \"ccgx_use_host_interface\""
            if (command.find("chip_protect_status") >= 0):
                use_host_interface = " -c \"ccgx_use_host_interface\""
            if ccgx_flash_auto_erase_on:
                ccgx_flash_auto_erase_on_cmd = "  -c \" ccgx flash_autoerase ccgx.flash on \" "


        cmd  = "./openocd "
        cmd += " -c \"interface zynqswd\""
        cmd += " -c \"zynq_dev_num " + str(self.slot_id) + "\""
        cmd += " -f /mix/driver/apple/SWDProgrammer/target/" + str(self.target_device) + ".cfg"
        cmd += use_host_interface
        cmd += reset_init if perform_reset_init else ""
        cmd += ccgx_flash_auto_erase_on_cmd
        cmd += " -c \"" + command + "\""
        if add_exit_commands:
            cmd += " -c \"reset; shutdown; exit\""

        return self.cmdline(cmd)

    def disable_lhotse_flash_protection(self):
        cmd = "disable_flash_protection"
        self.executeOpenOCDSingleCommand(cmd, perform_reset_init=False, add_exit_commands=False)

    def program_mcu(self, target_device, fw_binary, md5, offset, verify=True, ccgx_flash_auto_erase_on = False):
        """
        program the mcu using the apple SWD programmer.  

        :param target_device    str,    Device family for the chip
        :param fw_binary        str,    Firmware to download to the chip
        :param md5              str,    MD5 of the programming file.  If MD5 does not match, programming 
                                        will not proceed.
        :param offset           int,    Device address offset to place firmware
        :param verify           bool,   (Optional) whether to perform verify after programming.  Default=True.
        :param timeout_ms       int,    (Required if call through RPC).  Milliseconds for RPC to wait before 
                                        declaring call timeout.

        :return output          str,    The stdout of the programming process.
        :
        :example:   program_mcu("ccg2", "test_fw.bin", "d21127d234b5d22231d80e99b355248a", 0x00000000, timeout_ms=20000)
        More info: https://confluence.sd.apple.com/display/SMT/SWD+Programmer
        """
        self.target_device = target_device  # workaround until we change how people init this class.
        
        if target_device == "lhotse":
            self.disable_lhotse_flash_protection()
        
        if (not os.path.exists(fw_binary)):
            raise NameError('FW file not found')
        
        if (md5.lower().startswith("0x")):
            md5 = md5[2:]

        if (len(md5) != 32):
            raise NameError('Error in MD5 provided')

        file_md5 = "cccc"   # Just a random init value, in case hashlib.md5.hexdigest() return erronus value.
        with open(fw_binary, "rb") as f:            
            file_md5 = hashlib.md5(f.read()).hexdigest()

        if (file_md5.lower() != md5.lower()):
            raise NameError('Error, MD5 mismatched.  Programming aborted')

        cmd = "program " + fw_binary + " " + str(offset) + (" verify" if bool(verify) else "")

        reset_init = True if ccgx_flash_auto_erase_on else False
        return self.executeOpenOCDSingleCommand(cmd, reset_init, ccgx_flash_auto_erase_on)

    def verify(self, target_device, fw_binary, md5, offset):
        """
        Verify checksum or binary compare with a given image.  
        The image itself will be first md5 verified before verifying against the device.
        This will first attempt a comparison using a CRC checksum, if this fails it will try a binary compare.        
        
        :param target_device    str,    Device family for the chip
        :param fw_binary        str,    Firmware to download to the chip
        :param md5              str,    MD5 of the programming file.  If MD5 does not match, programming 
                                        will not proceed.
        :param offset           int,    Device address offset to start.
        :param timeout_ms       int,    (Required if call through RPC).  Milliseconds for RPC to wait before 
                                        declaring call timeout.

        :return output          str,    The stdout of the programming process.
        :
        :example:   verify("ccg2", "test_fw.bin", "d21127d234b5d22231d80e99b355248a", 0x00000000, timeout_ms=20000)
        """
        self.target_device = target_device  # workaround until we change how people init this class.
        
        if (not os.path.exists(fw_binary)):
            raise NameError('FW file not found')
        
        if (md5.lower().startswith("0x")):
            md5 = md5[2:]

        if (len(md5) != 32):
            raise NameError('Error in MD5 provided')

        file_md5 = "cccc"   # Just a random init value, in case hashlib.md5.hexdigest() return erronus value.
        with open(fw_binary) as f:            
            file_md5 = hashlib.md5(f.read()).hexdigest()
            f.close()

        if (file_md5.lower() != md5.lower()):
            raise NameError('Error, MD5 mismatched.  Programming aborted')

        cmd = "verify_image " + str(fw_binary) + " " + str(offset)
        return self.executeOpenOCDSingleCommand(cmd)


    def mass_erase(self, target_device, banks):
        """
        Perform mass erase to the given 'banks' list.
        :param target_device   str,        Device family for the chip
        :param banks           list[int],  Bank indexes to be mass-erased. 
    
        :example:   mass_erase("stm32f4x", [0,1])
        """
        self.target_device = target_device  # workaround until we change how people init this class.

        mass_erase_cmd = []
        for b in banks:
            mass_erase_cmd.append('%s mass_erase %d' % (target_device, b))
        cmd = ";".join(mass_erase_cmd)
        return self.executeOpenOCDSingleCommand(cmd)

    def protect(self, target_device, bank, first_block, last_block):
        """
        Perform mass erase to the given 'banks' list.
        :param target_device    str,        Device family for the chip
        :param bank             int,        Bank index to be configured.
        :param first_block      int,        first block index to be protected.
        :param last_block       int,        last block index to be protected.
    
        :example:   protect("ccg4", 0, 0, 511)
        """
        self.target_device = target_device  # workaround until we change how people init this class.

        cmd = ""

        # CCGX specific
        if first_block < 0:
            cmd = "ccgx chip_protect_only; "
            first_block = 0
            last_block = 0

        cmd += "flash protect %d %d %d on" % (bank, first_block, last_block)
        return self.executeOpenOCDSingleCommand(cmd)
        
    def dump_bank(self, target_device, bank, filename=None, offset=0, length=None, inline=False):
        """
        Dump the content of the device's given 'bank' into file.
        A random filename will be assigned if caller does not provide one.
        File will ALWAYS be saved in Xavier's /tmp folder.

        The stdout of the command will prompt "File saved as: /tmp/<filename>".  
        
        WARNING:  Unless 'inline=True', you are responsible for cleaning up the generated file!

        :param target_device    str,        Device family for the chip
        :param bank             int,        Bank index to be dumped.
        :param filename         str(opt),   User assigned file name in /tmp folder.
                                            If None provided, a random unique name will be assigned.
        :param offset           int(opt),   Bank offset to start the dump.
        :param length           int(opt),   The lenght to be dumped.
        :param inline           True/False, False by default.  Whether to dump the content directly back, 
                                            without saving to a file.  This is useful to get the content 
                                            directly to mac-mini client.
                                            Data is base64 encoded.

        :example:
            # Mac-Mini side example
            data_b64 = client.swdprog.dump_bank("stm32f4x.apple", 0, inline=True, timeout_ms=20000)
            import base64
            data_raw = base64.b64decode(data_b64)
            f = open('/tmp/xyz.bin', 'wb')
            f.write(data_raw)
            f.close()
        """
        self.target_device = target_device  # workaround until we change how people init this class.

        if (filename is None):
            fd = tempfile.mkstemp()
            filename = fd[1] + ".bin"
            os.close(fd[0])     # we just want the name.  close the file handle
            os.remove(fd[1])    # remove the temp file also

        filepath = os.path.join("/tmp", os.path.basename(filename))

        cmd = "flash read_bank %d %s %d" % (bank, filepath, offset)
        if length is not None:
            cmd += " " + str(length)

        output = self.executeOpenOCDSingleCommand(cmd)

        if inline:
            f = open(filepath, 'rb')
            output = f.read()
            output = base64.b64encode(output)
            os.remove(filepath)
        else:
            output += "\n\nFile saved as: " + filepath + "\n"

        return output

    def dump_chip_protection_status(self, target_device):
        """
        Execute command to dump the chip protection status.
        * Only CCG Family currently support this command.
        """
        
        # Only CCG family supports this
        assert target_device[:3] == "ccg"

        return self.executeOpenOCDSingleCommand("chip_protect_status")


    def kamet_otp_make_blob(self, BOOT_SERIALNUMBER, BOOT_HARDWARE_ID, BOOT_PRODUCT_ID,
                            IMON_GAIN, IMON_OFFSET, VMON_GAIN, VMON_OFFSET,
                            VBST_GAIN, VBST_OFFSET, ADC_GAIN, ADC_OFFSET,
                            TEMPERATURE_OFFSET, KAMET_VREF):

        assert len(BOOT_SERIALNUMBER) == 17

        MAGIC = 0x0B007CA1
        FMT_VER = 0x00000001

        blob = bytearray(80)

        struct.pack_into('<II', blob, 0, MAGIC, FMT_VER)

        for i in range(len(BOOT_SERIALNUMBER)):
            struct.pack_into('s', blob, 8 + i, BOOT_SERIALNUMBER[i].encode('utf-8'))

        struct.pack_into('<I', blob, 32, BOOT_HARDWARE_ID)
        struct.pack_into('<I', blob, 36, BOOT_PRODUCT_ID)

        struct.pack_into('<I', blob, 40, IMON_GAIN)
        struct.pack_into('<I', blob, 44, IMON_OFFSET)

        struct.pack_into('<I', blob, 48, VMON_GAIN)
        struct.pack_into('<I', blob, 52, VMON_OFFSET)

        struct.pack_into('<I', blob, 56, VBST_GAIN)
        struct.pack_into('<I', blob, 60, VBST_OFFSET)

        struct.pack_into('<I', blob, 64, ADC_GAIN)
        struct.pack_into('<I', blob, 68, ADC_OFFSET)

        struct.pack_into('<I', blob, 72, TEMPERATURE_OFFSET)
        struct.pack_into('<I', blob, 76, KAMET_VREF)

        return blob

    def program_kamet_otp_blob(self, blob, verify=True):
        """
        Special Device Support: Kamet OTP rdar://94266657

        blob should be an 80 bytes long for the calibration slot
        """
        assert len(blob) == 80

        tmpfile = tempfile.mktemp()
        f = open(tmpfile, 'wb')
        f.write(blob)
        f.close()

        self.target_device = "kamet_otp"
        cmd = "program_otp " + tmpfile + (" verify" if bool(verify) else "")

        rc = self.executeOpenOCDSingleCommand(cmd, False)

        if os.path.exists(tmpfile):
            os.remove(tmpfile)

        return rc

    def program_kamet_otp(self, boot_serialnumber, boot_hardware_id, boot_product_id,
                    imon_gain, imon_offset, vmon_gain, vmon_offset,
                    vbst_gain, vbst_offset, adc_gain, adc_offset,
                    temperature_offset, kmet_vref,
                    verify=True):
        """
        Special Device Support: Kamet OTP rdar://94266657
        """
        blob = self.kamet_otp_make_blob(boot_serialnumber, boot_hardware_id, boot_product_id,
                                    imon_gain, imon_offset, vmon_gain, vmon_offset,
                                    vbst_gain, vbst_offset, adc_gain, adc_offset,
                                    temperature_offset, kmet_vref)
        return self.program_kamet_otp_blob(blob, verify)
