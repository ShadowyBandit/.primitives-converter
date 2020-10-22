''' ShadowHunterRUS 2015-2016 '''
''' +ShadowyBandit 2020 '''


#####################################################################
# imports
from .common import *

from struct import unpack
from mathutils import Vector

#####################################################################
# LoadDataMesh

class LoadDataMesh:
    PrimitiveGroups = None
    uv_list = None
    normal_list = None
    tangent_list = None
    binormal_list = None
    bones_info = None
    vertices = None
    indices = None
    vertices_section_name = None
    indices_section_name = None
    vertices_format = None
    __PackedGroups = None
    __pfile = None
    __debug = False
    def __init__(self, filepath, vertices_name, primitive_name, extra_info):
        self.__debug = extra_info
        self.__pfile = open(filepath, 'rb')
        self.indices_section_name = primitive_name
        self.vertices_section_name = vertices_name
        header = unpack('<I', self.__pfile.read(4))[0]
        assert(header == 0x42a14e65) #Check if it is a real .primitives file
        self.__load_packed_section() #Read the table section of the .primitives file
##        print(self.__PackedGroups)
        self.__load_XYZNUV(
            self.__PackedGroups[primitive_name]['position'],
            self.__PackedGroups[vertices_name]['position']
            ) #loads the vertex and triangle data from the locations
        self.__pfile.close()


    def __load_packed_section(self):
        self.__pfile.seek(-4, 2) #Go to 4th to last byte
        table_len = unpack('<l', self.__pfile.read(4))[0] #Length of the table
        self.__pfile.seek(-4-table_len, 2) #Go to the beginning of the table section
        position = 4 #Current byte position (file position, not table)
        self.__PackedGroups = {} #Dictionary(key:  name, value: dictionary(key: 'position'/'length, value: position/length))
        while True:
            data = self.__pfile.read(4) #byte size of the section
##            if data == None or len(data) != 4:
##                break
            section_byte_size = unpack('<I', data)[0]
            self.__pfile.read(16) #Skip 16 bytes of buffer?
            data = self.__pfile.read(4) #Read byte size of the name e.g. 26 bytes for MidBack_wireShape.vertices
            if data == None or len(data) != 4:
                break
            section_name_length = unpack('<I', data)[0]
            section_name = self.__pfile.read(section_name_length).decode('utf-8') #Name of section e.g MidBack_wireShape.vertices
            for item in ('vertices', 'indices'): #If the section is a vertices or indices section, add to __PackedGroups
                #TODO:
                #'armor' data
                if item in section_name:
                    self.__PackedGroups[section_name] = {
                        'position' : position,
                        'length'   : section_byte_size
                    }
                    break
            position += section_byte_size
            if section_byte_size%4 > 0: #Skip bytes to next multiple of 4
                position += 4-section_byte_size%4
            if section_name_length%4 > 0:
                self.__pfile.read(4-section_name_length%4)
            
    def __load_XYZNUV(self, iposition, vposition):
        if self.__debug:
                print('-'*48)
        self.__pfile.seek(iposition) #Index position
        if self.__debug:
            print('   [Import Debug] Index position of %s: %d' % (self.indices_section_name, iposition) )
        indexFormat = self.__pfile.read(64).split(b'\x00')[0].decode('utf-8') #IndexFormat (either 'list' or 'list32')
        nIndices = unpack('<I', self.__pfile.read(4))[0] #Number of indices
        nTriangleGroups = unpack('<I', self.__pfile.read(4))[0] #Number of groups
        self.PrimitiveGroups = []
        if 'list32' in indexFormat:
            UINT_LEN = 4
        else:
            UINT_LEN = 2
            
        try:
            offset = nIndices*UINT_LEN+72 #Skip past the indices block to the group block
        except:
            print('     [Import Error] Index Format not found')
            
        self.__pfile.seek(iposition+offset) #Goto the group block
        
        for i in range(nTriangleGroups):
            startIndex = unpack('<I', self.__pfile.read(4))[0] #Offset of the index group, normally 0 b/c there is only 1 group
            nPrimitives = unpack('<I', self.__pfile.read(4))[0] #Number of triangles, same as the metadata in the indices group divided by three
            startVertex = unpack('<I', self.__pfile.read(4))[0] #Offset of the vertex group, normally 0 b/c there is only 1 group
            nVertices = unpack('<I', self.__pfile.read(4))[0] #Number of vertices, same as the metadata in the vertices group
            
            self.PrimitiveGroups.append({
                'startIndex'  : startIndex,
                'nPrimitives' : nPrimitives,
                'startVertex' : startVertex,
                'nVertices'   : nVertices
            })

##        print(self.PrimitiveGroups)
        
        if self.__debug:
                print('   [Import Debug] Vertex position of %s: %d' % (self.vertices_section_name, vposition) )
        self.__pfile.seek(vposition) #Goto the vertices block
        
        vertices_type = self.__pfile.read(64).split(b'\x00')[0].decode('utf-8') #Vertices format
        verticesCount = unpack('<l', self.__pfile.read(4))[0] #Number of vertices
        
        pos = self.__pfile.tell()

        byte_size = 0 #Byte size of each vertex
        is_skinned = False #Is weighted
        is_alpha = False
        is_wire = False
        
        if 'xyznuvtb' in vertices_type:
            if self.__debug:
                print('   [Import Debug] Standard import')
            byte_size = 32
            unpack_format = '<3fI2f2I'
            self.vertices_type='xyznuvtb'

        elif 'xyznuviiiwwtb' in vertices_type:
            if self.__debug:
                print('   [Import Debug] Gun import')
            byte_size = 37
            unpack_format = '<3fI2f5B2I'
            is_skinned = True
            self.vertices_type='xyznuviiiwwtb'

        elif 'xyznuvr' in vertices_type:
            if self.__debug:
                print('   [Import Debug] Wire import')
            byte_size = 36
            unpack_format = '<9f'
            is_wire = True
            self.vertices_type='xyznuvr'
            
        elif 'xyznuv' in vertices_type:
            if self.__debug:
                print('   [Import Debug] Alpha import')
            byte_size = 32
            unpack_format = '<8f'
            is_alpha = True
            self.vertices_type='xyznuv'
        else:
            print('   [Import Error] Format=%s' % self.vertices_type)

        vert_list = []
        pointer = 0

        for i in range(verticesCount):
            self.__pfile.seek(pos) #Goto new vertex position

            t, bn = None, None #Tangent, binormal

            if is_skinned:
                if byte_size == 37:
                    (x, z, y, n, u, v, index_1, index_2, index_3, weight_1, weight_2, t, bn) = unpack(unpack_format, self.__pfile.read(byte_size))

                    IIIWW = (index_1, index_2, index_3, weight_1, weight_2)

                y = -y #??? Weighted may be flipped

            else:
                if byte_size == 36:
                    (x, z, y, n1, n2, n3, u, v, r) = unpack(unpack_format, self.__pfile.read(byte_size))
                elif byte_size == 32 and not is_alpha:
                    (x, z, y, n, u, v, t, bn) = unpack(unpack_format, self.__pfile.read(byte_size))
                elif byte_size == 32 and is_alpha:
                    (x, z, y, n1, n2, n3, u, v) = unpack(unpack_format, self.__pfile.read(byte_size))
                    

            XYZ = Vector((x, y, z))
            XYZ.freeze()
            if not is_wire and not is_alpha:
                N = shr_UnpackNormal(n)
            else:
                N = Vector((n1,n2,n3))
                
            if t and bn:
                T = shr_UnpackNormal(t)
                BN = shr_UnpackNormal(bn)
            else:
                T = Vector((0.0, 0.0, 0.0))
                BN = Vector((0.0, 0.0, 0.0))

            N.freeze()
            T.freeze()
            BN.freeze()

            UV = Vector((u, 1-v))
            UV.freeze()

            XYZNUV2TB = (XYZ, N, UV, T, BN)
            if is_skinned:
                XYZNUV2TB += ( IIIWW, )
                
            #Removes duplicates
            vert_list.append(XYZNUV2TB)
            pointer += 1
            pos += byte_size #Move position up

##        print(vert_list_map)
##        print(vert_list
            
##        vert_list = list(vert_list.keys()) #Only take vertex tuples

        if not is_skinned:
            (self.vertices, self.normal_list, self.uv_list, self.tangent_list, self.binormal_list) = zip(*vert_list)
        else:
            (self.vertices, self.normal_list, self.uv_list, self.tangent_list, self.binormal_list, self.bones_info) = zip(*vert_list)

        self.indices = [] #Array of triangle faces
        for group in self.PrimitiveGroups:
            self.__pfile.seek(iposition + group['startIndex']*UINT_LEN+72) #Goto indices
            temp=group['nPrimitives']
            for cnt in range(group['nPrimitives']):
                if UINT_LEN == 2:
                    v1 = unpack('<H', self.__pfile.read(2))[0]
                    v2 = unpack('<H', self.__pfile.read(2))[0]
                    v3 = unpack('<H', self.__pfile.read(2))[0]
                elif UINT_LEN == 4:
                    v1 = unpack('<I', self.__pfile.read(4))[0]
                    v2 = unpack('<I', self.__pfile.read(4))[0]
                    v3 = unpack('<I', self.__pfile.read(4))[0]
                TRIANGLE = (v1, v2, v3)
                self.indices.append( TRIANGLE )
        
