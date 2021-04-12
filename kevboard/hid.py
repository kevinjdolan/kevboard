import usb.core

from kevboard import descriptor

B_REQUEST_GET_DESCRIPTOR = (0x80, 0x06)

DESCRIPTOR_TYPE_CONFIGURATION = 0x02

LANG_ID_UNSPECIFIED = 0x00

class HidDevice(object):
    
    def __init__(self, vendor_id, product_id):
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.device = usb.core.find(
            idVendor=vendor_id, 
            idProduct=product_id,
        )
        
    def get_descriptor(
        self,
        descriptor_type,
        descriptor_length,
        descriptor_index=0x00,
    ):
        w_value = descriptor_index | (descriptor_type << 8)
        data = self.send_ctrl(
            b_request=B_REQUEST_GET_DESCRIPTOR,
            w_value=w_value,
            w_index=descriptor_index,
            w_length=descriptor_length,
        )
        return descriptor.DescriptorSet.parse(data)
        
    def get_config_descriptor(self):
        truncated = self.get_descriptor(
            descriptor_type=DESCRIPTOR_TYPE_CONFIGURATION,
            descriptor_length=9,
        )
        full = self.get_descriptor(
            descriptor_type=DESCRIPTOR_TYPE_CONFIGURATION,
            descriptor_length=truncated['CONFIGURATION']['wTotalLength'],
        )
        return full
        
    def send_ctrl(
        self,
        b_request,
        w_value,
        w_index,
        w_length=None,
        data=None,
    ):
        return self.device.ctrl_transfer(
            bmRequestType=b_request[0],
            bRequest=b_request[1],
            wValue=w_value,
            wIndex=w_index,
            data_or_wLength=(data or w_length),
        )