import usb.core
import usb.util 
import usb.control
import time
import re
import pprint

from kevboard import hid

dev = hid.HidDevice(0x1edb, 0xda0e)
config = dev.get_config_descriptor()
print(config.pprint())

# dev.set_configuration(1)

# if dev.is_kernel_driver_active(2):
#     print("detaching kernel driver")
#     dev.detach_kernel_driver(2)

# def send_ctrl(ctrl):
#     bmRequestType = int(ctrl[0:2], 16)
#     bRequest = int(ctrl[2:4], 16)
#     wValue = int(ctrl[6:8]+ctrl[4:6], 16)
#     wIndex = int(ctrl[10:12]+ctrl[8:10], 16)
#     wLength = int(ctrl[14:16]+ctrl[12:14], 16)
#     print(hex(bmRequestType), hex(bRequest), hex(wValue), hex(wIndex))
#     desc = dev.ctrl_transfer(
#         bmRequestType=bmRequestType,
#         bRequest=bRequest,
#         wValue=wValue,
#         wIndex=wIndex,
#         data_or_wLength=wLength,
#     )
#     return desc

# B_REQUESTS = {
#     'GET_DESCRIPTOR': (0x80, 0x02),
# }

# DESCRIPTORS = {
#     'CONFIGURATION': 0x02,
# }

# # configuration request
# print(send_ctrl("8006000200000900"))
# print(send_ctrl("8006000200004f00"))

# #set configuration
# print(send_ctrl("0009010000000000"))

# #set idle
# print(send_ctrl("210a000002000000"))