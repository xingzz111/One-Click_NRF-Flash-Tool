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
print(rpc.call("mixdevice.cps_program_auto", timeout_ms=50000))
time.sleep(1)
print(rpc.call("mixdevice.reset"))


###### tps doe
print(rpc.call("mixdevice.reset"))
print(rpc.call("mixdevice.relay", "LDO_TO_PP_PDC_LDO_3V3"))
print(rpc.call("mixdevice.relay", "PP3V3_LDO_ENABLE"))
print(rpc.call("mixdevice.relay", "FIXTURE_TO_PDC_IIC_SEL_SW"))
time.sleep(3)
print(rpc.call("mixdevice.tps_program_auto", timeout_ms=50000))

###### ulpod
print(rpc.call("mixdevice.reset"))
print(rpc.call("mixdevice.relay", "LDO_TO_PP1V83_AON"))
print(rpc.call("mixdevice.relay", "PP1V83_LDO_ENABLE"))
print(rpc.call("mixdevice.relay", "FIXTURE_TO_NRF_SWD_SEL_SW"))
time.sleep(3)




###########check md5 done

# print(rpc.call("mixdevice.reset"))
# print(rpc.call("mixdevice.checkFWMD5", "/mix/addon/test_function/fw/tps.bin"))
# print(rpc.call("mixdevice.checkFWMD5", "/mix/addon/test_function/fw/cps.hex"))



###### nrf program
print(rpc.call("mixdevice.reset"))
print(rpc.call("mixdevice.relay", "LDO_TO_PP_VSYS_SW"))
print(rpc.call("mixdevice.relay", "PP8V_LDO_ENABLE"))
print(rpc.call("mixdevice.relay", "TP_SYS_RST_PULLUP"))
print(rpc.call("mixdevice.relay", "PP1V83_LDO_ENABLE"))
time.sleep(0.5)
print(rpc.call("mixdevice.relay", "TP_SYS_RST_PULLDOWN"))
print(rpc.call("mixdevice.relay", "FIXTURE_TO_NRF_SWD_SEL_SW"))

#####data dfu power up
print(rpc.call("mixdevice.reset"))
print(rpc.call("mixdevice.relay", "LDO_TO_PP_VSYS_SW"))
print(rpc.call("mixdevice.relay", "PP8V_LDO_ENABLE"))
print(rpc.call("mixdevice.relay", "PP1V83_LDO_ENABLE"))
print(rpc.call("mixdevice.relay", "UART_SEL_SW"))
#####data dfu power off
print(rpc.call("mixdevice.reset"))




#####data fct power up
print(rpc.call("mixdevice.reset"))
print(rpc.call("mixdevice.relay", "DUT_USBUART_EN"))
print(rpc.call("mixdevice.relay", "DUT_PP_VSYS_TO_PSU_BATTERY_POS1"))
print(rpc.call("mixdevice.enable_battery_output", 8000, 5000))



#####data fct power off
print(rpc.call("mixdevice.reset"))
