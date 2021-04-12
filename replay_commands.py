import json 
import usb.core
import usb.util
import time
import re

# find our device
dev = usb.core.find(idVendor=0x1edb, idProduct=0xda0e)
print(dev)

if dev.is_kernel_driver_active(2):
    print("detaching kernel driver")
    dev.detach_kernel_driver(2)

def get_requests():
    with open('usbdump.json') as f: 
        data = json.load(f)
        
    for line in data:
        frame = line['_source']['layers']['frame']
        time = float(frame['frame.time_relative'])
        if time > 48:
            continue

        usb = line['_source']['layers']['usb']
        if usb['usb.src'] != 'host':
            continue
        
        protocols = frame['frame.protocols']
        if protocols != "usb:usbhid": 
            continue
        
        setup = line['_source']['layers']['Setup Data']
        if 'usbhid.setup.bRequest' not in setup:
            continue
        
        data = setup.get('usb.data_fragment')
        if data:
            data = [
                int(x, 16)
                for x 
                in data.split(':')
            ]
            
        
        yield {
            'frame': frame['frame.number'],
            'bmRequestType': int(setup['usb.bmRequestType'], 16),
            'bRequest': int(setup['usbhid.setup.bRequest'], 16),
            'wValue': int(setup['usbhid.setup.wValue'], 16),
            'wIndex': int(setup['usbhid.setup.wIndex']),
            'wLength': int(setup['usbhid.setup.wLength']),
            'data': data,
        }

def send_ctrl(ctrl):
    bmRequestType = int(ctrl[0:2], 16)
    bRequest = int(ctrl[2:4], 16)
    wValue = int(ctrl[6:8]+ctrl[4:6], 16)
    wIndex = int(ctrl[10:12]+ctrl[8:10], 16)
    wLength = int(ctrl[14:16]+ctrl[12:14], 16)
    desc = dev.ctrl_transfer(
        bmRequestType=bmRequestType,
        bRequest=bRequest,
        wValue=wValue,
        wIndex=wIndex,
        data_or_wLength=wLength,
    )
    return desc

# configuration request
print(send_ctrl("8006000200000900"))
print(send_ctrl("8006000200004f00"))

#set configuration
print(send_ctrl("0009010000000000"))

for request in get_requests():
    print(request)
    desc = dev.ctrl_transfer(
        bmRequestType=request['bmRequestType'],
        bRequest=request['bRequest'],
        wValue=request['wValue'],
        wIndex=request['wIndex'],
        data_or_wLength=request['data'] or request['wLength'],
    )
    print(desc)
    
ep = dev[0][(2,0)][0]
data = ep.read(13, 10000)
print(data)

ep = dev[0][(2,0)][0]
data = ep.read(13, 10000)
print(data)

ep = dev[0][(2,0)][0]
data = ep.read(13, 10000)
print(data)

ep = dev[0][(2,0)][0]
data = ep.read(13, 10000)
print(data)

ep = dev[0][(2,0)][0]
data = ep.read(13, 10000)
print(data)