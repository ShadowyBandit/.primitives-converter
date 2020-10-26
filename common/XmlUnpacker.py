from struct import unpack
import xml.etree.ElementTree as ET
import base64

class XmlUnpacker:
    PACKED_HEADER = 0x62a14e45
    stream = None
    dict = []

    def read(self, stream):
        self.stream = stream
        if self.isPacked():
            self.dict = self.readDictionary()
            root = ET.Element('root')
            self.readElement(root)
            self.stream = None
            return root
        else:
            stream.seek(0)
            tree = ET.fromstring(stream.read().decode('UTF-8'))
            return tree

    def readElement(self, _base):
        children_count = unpack('<H', self.stream.read(2))[0]
        descriptor = self.readDataDescriptor()
        children = self.readElementDescriptors(children_count)
        offset = self.readData(_base, 0, descriptor)
        for child in children:
            node = ET.SubElement(_base, self.dict[child['name_index']])
            offset = self.readData(node, offset, child['descriptor'])

    def readDataDescriptor(self):
        data = self.stream.read(4)
        if data:
            end_type = unpack('<L', data)[0]
            return {'type': (end_type >> 28) + 0, 'end': end_type & 268435455, 'address': self.stream.tell()}
        else:
            raise Exception('Failed to read data descriptor')

    def readElementDescriptors(self, count):
        descriptors = []
        for i in range(0, count):
            data = self.stream.read(2)
            if data:
                name_index = unpack('<H', data)[0]
                descriptor = self.readDataDescriptor()
                descriptors.append({'descriptor': descriptor, 'name_index': name_index})
                continue
            else:
                raise Exception('Failed to read element descriptors')
        return descriptors

    def readData(self, element, offset, descriptor):
        length = descriptor['end'] - offset
        if descriptor['type'] == 0:
            self.readElement(element)

        elif descriptor['type'] == 1:
            element.text = self.readString(length)

        elif descriptor['type'] == 2:
            element.text = str(self.readNumber(length))

        elif descriptor['type'] == 3:
            float_str = self.readFloat(length)
            strData = float_str.split(' ')
            if (len(strData) == 12):
                for i in [0, 3, 6, 9]:
                    row = ET.SubElement(element, 'row{}'.format(i//3))
                    row.text = '{} {} {}'.format( *strData[i:i+3] )
            else:
                element.text = float_str

        elif descriptor['type'] == 4:
            element.text = 'true' if self.readBoolean(length) else 'false'

        elif descriptor['type'] == 5:
            element.text = self.readBase64(length)

        else:
            raise Exception('Unknown element type: %s' % descriptor['type'])

        return descriptor['end']

    def readString(self, length):
        if length:
            return self.stream.read(length).decode('UTF-8')
        return ''

    def readNumber(self, length):
        if length == 0:
            return 0
        else:
            data = self.stream.read(length)
            if length == 1:
                return unpack('b', data)[0]
            elif length == 2:
                return unpack('<H', data)[0]
            elif length == 4:
                return unpack('<L', data)[0]
            elif length == 8:
                return unpack('<Q', data)[0]
            else:
                raise Exception('Uknown number length')

    def readFloat(self, length):
        n = length // 4
        res = ''
        for i in range(0, n):
            if i != 0:
                res += ' '
            res += str(unpack('f', self.stream.read(4))[0])
        return res

    def readBoolean(self, length):
        if length == 0:
            return False
        elif length == 1:
            b = unpack('B', self.stream.read(1))[0]
            if b == 1:
                return True
            return False
        else:
            raise Exception('Boolean with wrong length.')

    def readBase64(self, length):
        return base64.b64encode(self.stream.read(length)).decode('UTF-8')

    def readDictionary(self):
        self.stream.seek(5)
        dict = []
        entry = ''
        while True:
            entry = self.readASCIIZ()
            if not entry:
                break
            dict.append(entry)
        return dict

    def readASCIIZ(self):
        _str = ''
        while True:
            c = self.stream.read(1)
            if ord(c) == 0:
                break
            _str += c.decode('UTF-8', errors='ignore')
        return _str

    def isPacked(self):
        self.stream.seek(0)
        header = unpack('I', self.stream.read(4))[0]
        if header != self.PACKED_HEADER:
            return False
        return True
