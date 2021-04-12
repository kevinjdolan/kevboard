import usb.core
import usb.util 
import usb.control
import time
import re
import pprint

from kevboard import hid

dev = hid.HidDevice(0x1edb, 0xda0e)
dev.detach_kernel_driver(2)

print("Getting USB config...")
config = dev.get_config()
print(config.pprint())

print("Getting HID Config...")
hid_config = dev.get_hid_report_descriptor()
print(hid_config.pprint())

print(dev.set_idle(duration=0))
print(dev.get_idle())

for report in dev.read_reports():
    print(report) 
    
print(dev.get_input_report(3))
print(dev.get_input_report(4))
print(dev.get_input_report(7))

print(dev.get_feature_report(1))
print(dev.get_feature_report(5))
print(dev.get_feature_report(6))
print(dev.get_feature_report(8))