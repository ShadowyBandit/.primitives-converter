''' ShadowHunterRUS 2015-2016 '''
''' +ShadowyBandit 2020 '''


#####################################################################
# imports
from ctypes import c_long
from struct import unpack
from mathutils import Vector

#####################################################################
# Unpack normal from 4-byte int
def UnpackNormal(packed):
    pky = (packed>>22)&0x1FF
    pkz = (packed>>11)&0x3FF
    pkx = packed&0x3FF
    x = pkx/1023.0
    if pkx & (1<<10):
        x = -x
    y = pky/511.0
    if pky & (1<<9):
        y = -y
    z = pkz/1023.0
    if pkz & (1<<10):
        z = -z
    return Vector((x, z, y))

#####################################################################
# LoadDataMesh

class LoadDataMesh:
    PrimitiveGroups = None #List of groups for each set
    uv_list = None #UV sublist
    normal_list = None #Normal sublist
    tangent_list = None #Tangent sublist
    binormal_list = None #Binormal sublist
    bones_info = None #Bones sublist
    vertices = None #Vertices sublist
    indices = None #Indices sublist
    vertices_section_name = None #Name of the set + .vertices
    indices_section_name = None #Name of the set + .indices
    vertices_format = None #Format of this set
    __PackedGroups = None #Lists some redundant info
    __pfile = None #Primitive file
    __debug = False
    def __init__(self, filepath, vertices_name, primitive_name, extra_info):
        self.__debug = extra_info #Debug mode?
        self.__pfile = open(filepath, 'rb') #Open .primitives file
        self.indices_section_name = primitive_name #Indices group name
        self.vertices_section_name = vertices_name #Vertices group name
        header = unpack('<I', self.__pfile.read(4))[0] #First 4 bytes of the file
        assert(header == 0x42a14e65) #Check if it is a real .primitives file i.e. first four bytes are B¡Ne
        self.__load_packed_section() #Read the table section of the .primitives file and lists length+position of all sections
        self.__load_XYZNUV(
            self.__PackedGroups[primitive_name]['position'],
            self.__PackedGroups[vertices_name]['position']
            ) #loads the vertex and triangle data from the locations
        self.__pfile.close() #Close .primitives file


    def __load_packed_section(self):
        self.__pfile.seek(-4, 2) #Go to 4th to last byte
        table_len = unpack('<l', self.__pfile.read(4))[0] #Length of the table
        self.__pfile.seek(-4-table_len, 2) #Go to the beginning of the table section
        position = 4 #Current byte position in file
        self.__PackedGroups = {} #Dictionary(name: dictionary('position':position, 'length': length))
        while True:
            data = self.__pfile.read(4) #byte size of the section
            section_byte_size = unpack('<I', data)[0] #Interpret section byte size
            self.__pfile.read(16) #Skip 16 bytes of buffer?
            data = self.__pfile.read(4) #Read byte size of the name e.g. 26 bytes for MidBack_wireShape.vertices
            if data == None or len(data) != 4:
                break
            section_name_length = unpack('<I', data)[0] #Interpret section name byte size
            section_name = self.__pfile.read(section_name_length).decode('utf-8') #Name of section e.g MidBack_wireShape.vertices
            for item in ('vertices', 'indices'): #If the section is a vertices or indices section, add to __PackedGroups
                #TODO:
                #'armor' data
                if item in section_name: #If section is a vertices or indices type
                    self.__PackedGroups[section_name] = {
                        'position' : position,
                        'length'   : section_byte_size
                    }#Save position and length
                    break
            if 'armor' in section_name: #If section is a vertices or indices type
                print(position)
                print(section_byte_size)
            position += section_byte_size #Move position up to start of next section
            if section_byte_size%4 > 0: #Skip section bytes to next multiple of 4
                position += 4-section_byte_size%4
            if section_name_length%4 > 0: #Skip table position to next multiple of 4
                self.__pfile.read(4-section_name_length%4)
            
    def __load_XYZNUV(self, iposition, vposition):
        if self.__debug: #Print divider
                print('-'*48)
        self.__pfile.seek(iposition) #Go to index position
        if self.__debug: #Print location of linked sections
            print('   [Import Debug] Vertex position of %s: %d' % (self.vertices_section_name, vposition) )
            print('   [Import Debug] Index position of %s: %d' % (self.indices_section_name, iposition) )
        indexFormat = self.__pfile.read(64).split(b'\x00')[0].decode('utf-8') #IndexFormat (either 'list' or 'list32')
        nIndices = unpack('<I', self.__pfile.read(4))[0] #Number of indices
        nTriangleGroups = unpack('<I', self.__pfile.read(4))[0] #Number of groups, should be 1
        if nTriangleGroups != 1:
            raise Exception("More than one primitives group")
        self.PrimitiveGroups = [] #List the TriangleGroups, should only have one element
        if 'list32' in indexFormat: #Index format
            UINT_LEN = 4
        else:
            UINT_LEN = 2
            
        try:
            offset = nIndices*UINT_LEN+72 #Skip past the metadata and indices to the packed information
        except:
            print('   [Import Error] Index Format not found')
            raise Exception("Can't recognize index format")
            
        self.__pfile.seek(iposition+offset) #Goto the group block
        
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
        if self.__debug: #Print number of vertices and faces
            print('   [Import Debug] Number of vertices of %s: %d' % (self.vertices_section_name, nVertices) )
            print('   [Import Debug] Number of faces of %s: %d' % (self.indices_section_name, nPrimitives) )
            
        self.__pfile.seek(vposition) #Goto the vertices block
        
        vertices_type = self.__pfile.read(64).split(b'\x00')[0].decode('utf-8') #Vertices format
        verticesCount = unpack('<l', self.__pfile.read(4))[0] #Number of vertices
        
        pos = self.__pfile.tell() #Just vposition+68

        byte_size = 0 #Byte size of each vertex
        is_skinned = False #Is weighted type, used for main armament
        is_alpha = False #Is alpha type, used for nets and glass
        is_wire = False #Is wire type, used for railings and wires
        
        if 'xyznuvtb' in vertices_type: #If standard type
            if self.__debug:
                print('   [Import Debug] Standard import')
            byte_size = 32
            unpack_format = '<3fI2f2I'
            self.vertices_type='xyznuvtb'

        elif 'xyznuviiiwwtb' in vertices_type: #If weighted type
            if self.__debug:
                print('   [Import Debug] Gun import')
            byte_size = 37
            unpack_format = '<3fI2f5B2I'
            is_skinned = True
            self.vertices_type='xyznuviiiwwtb'

        elif 'xyznuvr' in vertices_type: #If wire type
            if self.__debug:
                print('   [Import Debug] Wire import')
            byte_size = 36
            unpack_format = '<9f'
            is_wire = True
            self.vertices_type='xyznuvr'
            
        elif 'xyznuv' in vertices_type: #If alpha type
            if self.__debug:
                print('   [Import Debug] Alpha import')
            byte_size = 32
            unpack_format = '<8f'
            is_alpha = True
            self.vertices_type='xyznuv'
        else:
            print('   [Import Error] Format=%s' % self.vertices_type)
            raise Exception("Unrecognized vertex format")

        vert_list = [] #List of vertices

        for i in range(verticesCount):
            self.__pfile.seek(pos) #Goto vertex data position

            t, bn = None, None #Tangent, binormal

            if is_skinned:
                if byte_size == 37:
                    (x, z, y, n, u, v, index_1, index_2, index_3, weight_1, weight_2, t, bn) = unpack(unpack_format, self.__pfile.read(byte_size))
                    y=-y #Skinned is flipped?
                    IIIWW = (index_1, index_2, index_3, weight_1, weight_2)

            else:
                if byte_size == 36:
                    (x, z, y, n1, n2, n3, u, v, r) = unpack(unpack_format, self.__pfile.read(byte_size))
                elif byte_size == 32 and not is_alpha:
                    (x, z, y, n, u, v, t, bn) = unpack(unpack_format, self.__pfile.read(byte_size))
                elif byte_size == 32 and is_alpha:
                    (x, z, y, n1, n2, n3, u, v) = unpack(unpack_format, self.__pfile.read(byte_size))
                    

            XYZ = Vector((x, y, z))
            XYZ.freeze()
            if not is_wire and not is_alpha: #If not wire or alpha types
                N = UnpackNormal(n)
            else: #If wire or alpha type
                N = Vector((n1,n2,n3))
                
            if t and bn: #If standard model
                T = UnpackNormal(t)
                BN = UnpackNormal(bn)
            else: #Else, empty vectors
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
            
            #Add to vertices list
            vert_list.append(XYZNUV2TB)
            pos += byte_size #Shift to next vertice

        if not is_skinned: #Set sublists
            (self.vertices, self.normal_list, self.uv_list, self.tangent_list, self.binormal_list) = zip(*vert_list)
        else: #Set sublists
            (self.vertices, self.normal_list, self.uv_list, self.tangent_list, self.binormal_list, self.bones_info) = zip(*vert_list)

        self.indices = [] #Array of triangles
        self.__pfile.seek(iposition + self.PrimitiveGroups[0]['startIndex']*UINT_LEN+72) #Goto indices for the group
        for cnt in range(self.PrimitiveGroups[0]['nPrimitives']):
            if UINT_LEN == 2: #If smaller vertices number (<32768)
                v1 = unpack('<H', self.__pfile.read(2))[0]
                v2 = unpack('<H', self.__pfile.read(2))[0]
                v3 = unpack('<H', self.__pfile.read(2))[0]
            elif UINT_LEN == 4: #If larger vertices number (>32767)
                v1 = unpack('<I', self.__pfile.read(4))[0]
                v2 = unpack('<I', self.__pfile.read(4))[0]
                v3 = unpack('<I', self.__pfile.read(4))[0]
            TRIANGLE = (v1, v2, v3)
            self.indices.append( TRIANGLE ) #Add the tuple of indices of vertices
        
