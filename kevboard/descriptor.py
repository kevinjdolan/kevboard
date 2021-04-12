INTERFACE_CLASS_HID = 0x03

def find_by_type(descriptors, name, first=True):
    matches = []
    for descriptor in descriptors: 
        if descriptor['bDescriptorTypeName'] == name:
            matches.append[descriptor]

class DescriptorSet(object):
    
    @classmethod
    def parse(cls, data):
        descriptors = []
        for subdata in cls._iter_descriptor_data(data):
            descriptor = Descriptor.parse(
                subdata, 
                descriptors,
            )
            descriptors.append(descriptor)
            
        return cls(descriptors)
    
    @classmethod
    def _iter_descriptor_data(cls, data):
        index = 0
        state = []
        while index < len(data):
            length = data[index]
            end = index + length
            subdata = data[index:end]
            yield subdata
            
            index = end
    
    def __init__(self, descriptors):
        self.descriptors = descriptors
        
    def __getitem__(self, name):
        matches = self.find(name)
        if matches:
            return matches[0]
        
    def find(self, name):
        out = []
        for descriptor in self.descriptors:
            if descriptor.name == name:
                out.append(descriptor)
        return out
    
    def pprint(self):
        return "\n".join(
            descriptor.pprint()
            for descriptor
            in self.descriptors
        )
        
class Descriptor(object):
    
    __abstract__ = True
    
    @classmethod
    def parse(cls, data, state):
        for subcls in DESCRIPTOR_TYPES:
            descriptor_type = data[1]
            parsed = subcls.parse(
                descriptor_type, 
                data[2:], 
                state,
            )
            if parsed is not None:
                return parsed
    
    @classmethod
    def _extract_attributes(cls, data, attrs):
        out = {}
        index = 0
        for attr in attrs:
            name = attr[0]
            length = attr[1]
            type = attr[2]
            subdata = data[index:index+length]
            value = cls._parse_value(subdata, type)
            out[name] = value
            index += length
        return out
            
    @classmethod
    def _parse_value(cls, data, type):
        if type == 'int':
            sum = 0
            for i, value in enumerate(data):
                sum += value << (8 * i)
            return sum
        if type == 'hex':
            sum = 0
            for i, value in enumerate(reversed(data)):
                sum += value << (8 * i)
            return sum
        if type == 'flags':
            flags = []
            for datum in data:
                for i in range(7, -1, -1):
                    flags.append(datum >> i & 1)
            return flags
        return data
        
    def __init__(
        self, 
        name, 
        descriptor_type,
        **attrs,
    ):
        self.name = name
        self.descriptor_type = descriptor_type
        self.attrs = attrs
        
    def __getitem__(self, name):
        return self.attrs[name]
    
    def pprint(self):
        header = f"{ self.name } ({ self.descriptor_type })"
        rows = [
            f"{ key }: { value }"
            for key, value
            in self.attrs.items()
        ]
        return "\n\t".join([
            header,
            *rows,
        ])
        
class BasicDescriptor(Descriptor):
    
    specs = {
        0x02: {
            'name': "CONFIGURATION",
            'attrs': [
                ('wTotalLength', 2, 'int'),
                ('bNumInterfaces', 1, 'int'),
                ('bConfigurationValue', 1, 'int'),
                ('iConfiguration', 1, 'int'),
                ('bmAttributes', 1, 'flags'),
                ('bMaxPower', 1, 'int'),
            ],
        },
        0x04: {
            'name': "INTERFACE",
            'attrs': [
                ('bInterfaceNumber', 1, 'int'),
                ('bAlternateSetting', 1, 'int'),
                ('bNumEndpoints', 1, 'int'),
                ('bInterfaceClass', 1, 'hex'),
                ('bInterfaceSubclass', 1, 'hex'),
                ('bInterfaceProtocol', 1, 'hex'),
                ('iInterface', 1, 'int'),
            ],
        },
        0x05: {
            'name': "ENDPOINT",
            'attrs': [
                ('bEndpointAddress', 1, 'hex'),
                ('bmAttributes', 1, 'flags'),
                ('wMaxPacketSize', 2, 'int'),
                ('bInterval', 1, 'int'),
            ],
        },
        0x0b: {
            'name': "INTERFACE ASSOCIATION",
            'attrs': [
                ('bFistAssociation', 1, 'int'),
                ('bInterfaceCount', 1, 'int'),
                ('bFunctionClass', 1, 'hex'),
                ('bFunctionSubclass', 1, 'hex'),
                ('bFunctionProtocol', 1, 'hex'),
                ('iFunction', 1, 'int'),
            ],
        },
    }
    
    @classmethod
    def parse(cls, descriptor_type, data, state):
        if descriptor_type not in cls.specs:
            return None
        spec = cls.specs[descriptor_type]
        attrs = cls._extract_attributes(data, spec['attrs'])
        return cls(
            name=spec['name'],
            descriptor_type=descriptor_type,
            **attrs,
        )

class InterfaceFunctionalDescriptor(Descriptor):
    
    specs = {
        (0xfe, 0x01): {
            'name': "DFU",
            'attrs': [
                ('capabilities', 1, 'flags'),
                ('wDetachTimeOut', 2, 'int'),
                ('wTransferSize', 2, 'int'),
                ('bcdDFUVersion', 2, 'hex'),
            ],
        },
        (0x03, 0x00): {
            'name': "HID",
            'attrs': [
                ('bcdHID', 2, 'hex'),
                ('bCountryCode', 1, 'hex'),
                ('bNumDescriptors', 1, 'int'),
                ('bDescriptorType2', 1, 'hex'),
                ('wDescriptorLength', 2, 'int'),
            ],
        },
    }
    
    @classmethod
    def parse(cls, descriptor_type, data, state):
        if descriptor_type != 0x21:
            return None

        last_descriptor = state[-1]
        iface = (
            last_descriptor['bInterfaceClass'],
            last_descriptor['bInterfaceSubclass'],        
        )
        if iface not in cls.specs:
            return cls(
                name="INTERFACE FUNCTIONAL: UNKNOWN",
                descriptor_type=descriptor_type,
                data=data,
            )
        
        spec = cls.specs[iface]
        attrs = cls._extract_attributes(data, spec['attrs'])
        return cls(
            name=f"INTERFACE FUNCTIONAL: { spec['name'] }",
            descriptor_type=descriptor_type,
            **attrs,
        )
            

class UnknownDescriptor(Descriptor):
    
    @classmethod
    def parse(cls, descriptor_type, data, state):
        return cls(
            name="Unknown",
            descriptor_type=descriptor_type,
            data=data,
        )

DESCRIPTOR_TYPES = [
    BasicDescriptor,
    InterfaceFunctionalDescriptor,
    UnknownDescriptor,
]