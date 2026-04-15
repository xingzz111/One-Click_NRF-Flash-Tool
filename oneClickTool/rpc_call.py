from pathlib import Path
import subprocess
import time

from mix.lynx.rpc.rpc_client import RPCClientWrapper

END_POINT = {
    "receiver": "tcp://169.254.1.32:17801",
    "type": "rpc",
    "requester": "tcp://169.254.1.32:7801",
}

rpc = RPCClientWrapper(END_POINT)


##### cps doe
print(rpc.call("mixdevice.reset"))
print(rpc.call("mixdevice.relay", "LDO_TO_PP5V_AON_SW"))
print(rpc.call("mixdevice.relay", "PP5V_LDO_ENABLE"))
print(rpc.call("mixdevice.relay", "PP1V83_LDO_ENABLE"))
print(rpc.call("mixdevice.relay", "FIXTURE_TO_NRF_CPS_IIC_SEL_SW"))
time.sleep(3)

print(rpc.call("mixdevice.cps_program_auto", "/mix/addon/test_function/fw/CPS8200_3E_02_VDB3_CRC9A17.hex", timeout_ms=50000))
time.sleep(1)
print(rpc.call("mixdevice.reset"))
print(rpc.call("mixdevice.relay", "LDO_TO_PP5V_AON_SW"))
print(rpc.call("mixdevice.relay", "PP5V_LDO_ENABLE"))
print(rpc.call("mixdevice.relay", "PP1V83_LDO_ENABLE"))
print(rpc.call("mixdevice.relay", "FIXTURE_TO_NRF_CPS_IIC_SEL_SW"))
print(rpc.call("mixdevice.set_freq", "C", 1830))
print(rpc.call("mixdevice.set_freq", "D", 750))
time.sleep(3)
print(rpc.call("mixdevice.cps_send_word", 0xffffff00, 12))
time.sleep(1)
print(rpc.call("mixdevice.cps_send_word", 0x20000565, 1))
time.sleep(1)
print(rpc.call("mixdevice.cps_send_word", 0x200007c4, 0x01))
time.sleep(1)
print(rpc.call("mixdevice.cps_send_word", 0x2000058b, 0x10))
# print(rpc.call("mixdevice.cps_output", 2))
time.sleep(3)
print(rpc.call("mixdevice.measureFrequency", 0, 1000, "freq", "LP"))
# print(rpc.call("mixdevice.reset"))


###### tps doe
# print(rpc.call("mixdevice.reset"))

# print(rpc.call("mixdevice.relay", "LDO_TO_PP_PDC_LDO_3V3"))
# print(rpc.call("mixdevice.relay", "PP3V3_LDO_ENABLE"))
# print(rpc.call("mixdevice.relay", "FIXTURE_TO_PDC_IIC_SEL_SW"))
# time.sleep(3)
# src_bin = "/mix/addon/test_function/fw/tps.bin"
# readback_bin = "/mix/addon/test_function/fw/tps_readback.bin"
# print(rpc.call("mixdevice.tps_program_auto", src_bin, timeout_ms=50000))
# time.sleep(0.5)
# print(rpc.call("mixdevice.tps_readback_compare", src_bin, readback_bin, timeout_ms=50000))




###########check md5 done

# print(rpc.call("mixdevice.reset"))
# print(rpc.call("mixdevice.checkFWMD5", "/mix/addon/test_function/fw/tps.bin"))
# print(rpc.call("mixdevice.checkFWMD5", "/mix/addon/test_function/fw/cps.hex"))
