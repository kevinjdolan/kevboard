import usb.core

from kevboard import descriptor

B_REQUEST_GET_DESCRIPTOR = (0x80, 0x06)
B_REQUEST_GET_HID_REPORT_DESCRIPTOR = (0x81, 0x06)
B_REQUEST_GET_IDLE = (0xa1, 0x02)
B_REQUEST_GET_REPORT = (0xa1, 0x01)
B_REQUEST_SET_IDLE = (0x21, 0x0a)
B_REQUEST_SET_REPORT = (0xa1, 0x09)

DESCRIPTOR_TYPE_CONFIGURATION = 0x02
DESCRIPTOR_TYPE_HID_REPORT = 0x22

REPORT_TYPE = {
    'input': 0x01,
    'output': 0x02,
    'feature': 0x03,
}

INTERFACE_CLASS_HID = 0x03

LANG_ID_UNSPECIFIED = 0x00

class HidDevice(object):
    
    def __init__(self, vendor_id, product_id):
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.device = usb.core.find(
            idVendor=vendor_id, 
            idProduct=product_id,
        )
        self.config = None
        self.hid_report_descriptor = None
        
    def detach_kernel_driver(self, interface):
        if self.device.is_kernel_driver_active(interface):
            self.device.detach_kernel_driver(interface)
        self.device.reset()
        
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
        data = descriptor.DescriptorSet.parse(data)
        return data
        
    def get_config(self):
        if self.config is None:
            truncated = self.get_descriptor(
                descriptor_type=DESCRIPTOR_TYPE_CONFIGURATION,
                descriptor_length=9,
            )
            self.config = self.get_descriptor(
                descriptor_type=DESCRIPTOR_TYPE_CONFIGURATION,
                descriptor_length=truncated['CONFIGURATION']['wTotalLength'],
            )
        return self.config
    
    def get_hid_functional_config(self, interface_number):
        config = self.get_config()
        functional_configs = config.find('INTERFACE FUNCTIONAL: HID')
        for functional_config in functional_configs:
            config_interface = functional_config['interface']['bInterfaceNumber']
            if config_interface == interface_number:
                return functional_config
            
    def get_hid_in_endpoint(self, interface_number=None):
        # TODO: implement me
        return 0x81
    
    def get_hid_interface(self, interface_number=None):
        hid_interfaces = self.get_hid_interfaces()
        if not hid_interfaces:
            return None
        
        if interface_number is None:
            return hid_interfaces[0]
        
        for interface in hid_interfaces:
            if interface['bInterfaceNumber'] == interface_number:
                return interface
            
    def get_hid_interface_number(self, interface_number=None):
        interface = self.get_hid_interface(interface_number)
        return interface['bInterfaceNumber']
        
    def get_hid_interfaces(self):
        hid_interfaces = []
        interfaces = self.get_interfaces()
        for interface in interfaces:
            if interface['bInterfaceClass'] == INTERFACE_CLASS_HID:
                hid_interfaces.append(interface)
        return hid_interfaces
    
    def get_report(
        self, 
        report_type, 
        report_id, 
        interface_number=None,
    ):
        interface_number = self.get_hid_interface_number(interface_number)
        descriptor = self.get_hid_report_descriptor()
        report_type_mask = REPORT_TYPE[report_type]
        w_value = report_id | (report_type_mask << 8)
        data = self.send_ctrl(
            b_request=B_REQUEST_GET_REPORT,
            w_value=w_value,
            w_index=interface_number,
            w_length=descriptor.get_report_packet_size(
                report_type, 
                report_id,
            ),
        ) 
        # TODO: parse report
        return data
    
    def get_feature_report(
        self, 
        report_id, 
        interface_number=None,
    ):
        return self.get_report(
            report_type='feature',
            report_id=report_id,
            interface_number=interface_number,
        )
        
    def get_input_report(
        self, 
        report_id, 
        interface_number=None,
    ):
        return self.get_report(
            report_type='input',
            report_id=report_id,
            interface_number=interface_number,
        )
        
    def get_interfaces(self):
        config = self.get_config()
        return config.find('INTERFACE')
    
    def get_hid_report_descriptor(self, interface_number=None):
        if self.hid_report_descriptor is None:
            interface_number = self.get_hid_interface_number(interface_number)
            config = self.get_hid_functional_config(interface_number)
            length = config['wDescriptorLength']
            w_value = 0x00 | (DESCRIPTOR_TYPE_HID_REPORT << 8)
            data = self.send_ctrl(
                b_request=B_REQUEST_GET_HID_REPORT_DESCRIPTOR,
                w_value=w_value,
                w_index=interface_number,
                w_length=length,
            )
            self.hid_report_descriptor = descriptor.HidReportDescriptor.parse(data)
        return self.hid_report_descriptor
    
    def get_idle(self, interface_number=None):
        interface_number = self.get_hid_interface_number(interface_number)
        result = self.send_ctrl(
            b_request=B_REQUEST_GET_IDLE,
            w_index=interface_number,
            w_length=1,
        )
        return result[0]
    
    def read_report(
        self, 
        timeout=None, 
        interface_number=None,
    ):
        descriptor = self.get_hid_report_descriptor()
        size = descriptor.get_input_packet_size()
        interface_number = self.get_hid_interface_number(interface_number)
        endpoint = self.get_hid_in_endpoint(interface_number)
        try:
            data = self.device.read(endpoint, size, timeout)
            #TODO: parse data
            #TODO: timeout
            return data
        except usb.core.USBTimeoutError:
            return None
        
    def read_reports(
        self, 
        interface_number=None,
        halt_on_timeout=True,
    ):
        while True:
            data = self.read_report(interface_number)
            if halt_on_timeout and (data is None):
                return

            yield data
        
    def send_ctrl(
        self,
        b_request,
        w_value=0,
        w_index=0,
        w_length=0,
        data=None,
    ):
        return self.device.ctrl_transfer(
            bmRequestType=b_request[0],
            bRequest=b_request[1],
            wValue=w_value,
            wIndex=w_index,
            data_or_wLength=(data or w_length),
        )
        
    def set_idle(
        self, 
        duration=0,
        report_id=0,
        interface_number=None,
    ):
        interface_number = self.get_hid_interface_number(interface_number)
        w_value = report_id | (duration << 8)
        result = self.send_ctrl(
            b_request=B_REQUEST_SET_IDLE,
            w_value=w_value,
            w_index=interface_number,
            w_length=0,
        )
        return result