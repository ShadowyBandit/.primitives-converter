''' ShadowHunterRUS 2015-2016 '''
''' + ShadowyBandit 2020 '''


#####################################################################
# imports

import os
from struct import pack
from ctypes import c_uint32
from xml.dom.minidom import getDOMImplementation
import xml.etree.ElementTree as ET
import bpy
from mathutils import Vector

#####################################################################
# packNormal

def packNormal(unpacked: Vector) -> int:
    unpacked.normalize()
    x = max( min( unpacked.x, 1.0 ), -1.0 )
    z = max( min( unpacked.y, 1.0 ), -1.0 )
    y = max( min( unpacked.z, 1.0 ), -1.0 )
    z = c_uint32( ( int( z * 511.0 ) & 0x3ff ) << 22).value
    y = c_uint32( ( int( y * 1023.0 ) & 0x7ff ) << 11).value
    x = c_uint32( ( int( x * 1023.0 ) & 0x7ff ) ).value
    return c_uint32(z^(y^x)).value

#####################################################################
# set_nodes

#Recursively add nodes to the visual document
def set_nodes(nodes:dict, elem, doc):
    for node_name, node in nodes.items():
        __node = doc.createElement('node')

        __identifier = doc.createElement('identifier')
        __identifier.appendChild(doc.createTextNode(node_name))
        __node.appendChild(__identifier)

        __transform = doc.createElement('transform')
        __row0 = doc.createElement('row0')
        __row1 = doc.createElement('row1')
        __row2 = doc.createElement('row2')
        __row3 = doc.createElement('row3')

        __row0.appendChild(doc.createTextNode('%f %f %f' % (node['scale'][0], 0.0, 0.0)))
        __row1.appendChild(doc.createTextNode('%f %f %f' % (0.0, node['scale'][1], 0.0)))
        __row2.appendChild(doc.createTextNode('%f %f %f' % (0.0, 0.0, node['scale'][2])))
        __row3.appendChild(doc.createTextNode('%f %f %f' % node['loc']))

        __transform.appendChild(__row0)
        __transform.appendChild(__row1)
        __transform.appendChild(__row2)
        __transform.appendChild(__row3)

        __node.appendChild(__transform)

        set_nodes(node['children'], __node, doc)

        elem.appendChild(__node)



#####################################################################
# BigWorldModelExporter

class BigWorldModelExporter(object):
    def get_vertices_and_indices(self, object_list: list, debug_mode):
        render_sets = [] #Array of render sets
        for object in object_list:
            if debug_mode: #Print divider
                    print('-'*48)
            render_set = { #Create a render set dictionary for each object
                'nodes'    : [],
                'geometry' : {
                    'vertices'              : '',
                    'primitive'             : '',
                    'primitiveGroups'       : None,
                    'indices_section_size'  : 0,
                    'vertices_section_size' : 0
                }
            }

            #Set indices and vertices names for object
            render_set['geometry']['vertices'] = '%s.vertices' % os.path.splitext(object.name)[0]
            render_set['geometry']['primitive'] = '%s.indices' % os.path.splitext(object.name)[0]
            if 'xyznuviiiwwtb' in object.data.materials[0].Vertex_Format:
                for vg in object.vertex_groups:
                    render_set['nodes'].append( vg.name )
            else:
                render_set['nodes'].append(object.name)

            #Dictionary of primitives groups and total stats, there should only be one primitive group
            primitives_group = {
                'groups'                : {},
                'nIndicesTotal'         : 0,
                'nVerticesTotal'        : 0,
                'nTriangleGroupsTotal'  : 0,
                'nPrimitivesTotal'      : 0,
            }

            primitives_group['groups'][0] = {
                'name'                         : os.path.splitext(object.data.materials[0].name)[0],
                'id'                           : 0,
                'format'                       : object.data.materials[0].Vertex_Format,
                'mfm'                          : object.data.materials[0].BigWorld_mfm_Path,
                'vertices'                     : [],
                'indices'                      : [],
                'startVertex'                  : 0,
                'startIndex'                   : 0,
                'nVertices'                    : 0,
                'nPrimitives'                  : 0
            }
            iv = 0 #Number of vertices
            ii = 0 #Number of indices i.e. edges
            uv_layer = object.data.uv_layers.active.data[:] #active uv map, should only be one

            #Recalculate normals vectors
            object.data.calc_normals()
            object.data.calc_tangents(uvmap='uv1')

            primitives_group['groups'][0]['startVertex'] = iv
            primitives_group['groups'][0]['startIndex'] = ii
            
            for poly in object.data.polygons:
                loop = poly.loop_indices
                for loopIndex, vertexIndex in enumerate(loop):
                    XYZNUVTB=None
                    if 'xyznuvtb' in primitives_group['groups'][0]['format']:
                        vert = object.data.vertices[poly.vertices[loopIndex]]
                        x, y, z = vert.co
                        n = object.data.loops[vertexIndex].normal.copy()
                        n = packNormal(n)
                        u, v = uv_layer[vertexIndex].uv
                        t = object.data.loops[vertexIndex].tangent.copy()
                        t = packNormal(t)
                        bn = object.data.loops[vertexIndex].bitangent.copy()
                        bn = packNormal(bn)
                        XYZNUVTB = (x, z, y, n, u, 1-v, t, bn)
                    elif 'xyznuvr' in primitives_group['groups'][0]['format']:
                        vert = object.data.vertices[poly.vertices[loopIndex]]
                        x, y, z = vert.co
                        n1, n2, n3 = object.data.loops[vertexIndex].normal.copy()
                        u, v = uv_layer[vertexIndex].uv
                        XYZNUVTB = (x, z, y, n1, n2, n3, u, 1-v, 0.002)
                    elif 'xyznuviiiwwtb' in primitives_group['groups'][0]['format']:
                        vert = object.data.vertices[poly.vertices[loopIndex]]
                        x, y, z = vert.co
                        y = -y
                        n = object.data.loops[vertexIndex].normal.copy()
                        n = packNormal(n)
                        u, v = uv_layer[vertexIndex].uv
                        t = object.data.loops[vertexIndex].tangent.copy()
                        t = packNormal(t)
                        bn = object.data.loops[vertexIndex].bitangent.copy()
                        bn = packNormal(bn)
                        XYZNUVTB = (x, z, y, n, u, 1-v)
                        TB = (t, bn)
                        if len(vert.groups) == 1:
                            index1 = vert.groups[0].group*3
                            index2 = 0
                            index3 = 0

                            weight1 = vert.groups[0].weight
                            weight2 = 0
                            weight3 = 0

                            sumWeights = weight1 + weight2 + weight3

                            weight1 = weight1/sumWeights
                            weight2 = weight2/sumWeights

                            weight1 = int(weight1*255)
                            weight2 = int(weight2*255)

                        elif len(vert.groups) == 2:
                            index1 = vert.groups[0].group*3
                            index2 = vert.groups[1].group*3
                            index3 = 0

                            weight1 = vert.groups[0].weight
                            weight2 = vert.groups[1].weight
                            weight3 = 0

                            sumWeights = weight1 + weight2 + weight3

                            weight1 = weight1/sumWeights
                            weight2 = weight2/sumWeights

                            weight1 = int(weight1*255)
                            weight2 = int(weight2*255)

                        elif len(vert.groups) == 3:
                            index1 = vert.groups[0].group*3
                            index2 = vert.groups[1].group*3
                            index3 = vert.groups[2].group*3

                            weight1 = vert.groups[0].weight
                            weight2 = vert.groups[1].weight
                            weight3 = vert.groups[2].weight

                            sumWeights = weight1 + weight2 + weight3

                            weight1 = weight1/sumWeights
                            weight2 = weight2/sumWeights

                            weight1 = int(weight1*255)
                            weight2 = int(weight2*255)

                        IIIWW = (index1, index2, index3, weight1, weight2)
                        XYZNUVTB += IIIWW
                        XYZNUVTB += TB
                    elif 'xyznuv' in primitives_group['groups'][0]['format']:
                        vert = object.data.vertices[poly.vertices[loopIndex]]
                        x, y, z = vert.co
                        n1, n2, n3 = object.data.loops[vertexIndex].normal.copy()
                        u, v = uv_layer[vertexIndex].uv
                        XYZNUVTB = (x, z, y, n1, n2, n3, u, 1-v)
                        
                    primitives_group['groups'][0]['vertices'].append( XYZNUVTB ) #Add to vertices array
                    iv += 1 #Add to vertices count

                if len(loop) == 3: #If is a triangle
                    primitives_group['groups'][0]['indices'].append( (loop[2], loop[1], loop[0]) ) #Add to triangle array
                    ii += 3 #Add to edges count

                else:
                    print('[Export Error] N-gon face detected')
                    raise Exception("Please triangulate faces") #Is an n-gon face

            #Number of vertices and triangles for the group
            primitives_group['groups'][0]['nVertices'] = iv - primitives_group['groups'][0]['startVertex']
            primitives_group['groups'][0]['nPrimitives'] = (ii - primitives_group['groups'][0]['startIndex'])//3
            if debug_mode: #Print number of vertices and faces
                print('   [Export Debug] Number of vertices of %s: %d' % (render_set['geometry']['vertices'], primitives_group['groups'][0]['nVertices']) )
                print('   [Export Debug] Number of faces of %s: %d' % (render_set['geometry']['primitive'], primitives_group['groups'][0]['nPrimitives']) )
            if debug_mode: #Print export type
                if 'xyznuvtb' in primitives_group['groups'][0]['format']:
                    print('   [Export Debug] Standard export')
                elif 'xyznuvr' in primitives_group['groups'][0]['format']:
                    print('   [Export Debug] Wire export')
                elif 'xyznuviiiwwtb' in primitives_group['groups'][0]['format']:
                    print('   [Export Debug] Weighted export')
                elif 'xyznuv' in primitives_group['groups'][0]['format']:
                    print('   [Export Debug] Alpha export')
            #Number of vertices, triangles, loops for all groups and number of groups
            primitives_group['nIndicesTotal'] = ii
            primitives_group['nPrimitivesTotal'] = ii//3
            primitives_group['nVerticesTotal'] = iv
            primitives_group['nTriangleGroupsTotal'] = len(primitives_group['groups'])
            object.data.free_tangents() #???
            
            render_set['geometry']['primitiveGroups'] = primitives_group #Set the primitive group for this renderset
            render_sets.append( render_set ) #Add this render set to array of render sets

        return render_sets


    def export(self, object_list: list, model_filepath: str, export_info: dict, debug_mode):
        render_sets = self.get_vertices_and_indices(object_list, debug_mode) #Make array of triangles, vertices for each object
        
        vertices_format = b'xyznuvtb' #Default format
        vertices_secsize = 32 #Default size
        vertices_pcformat = '<3fI2f2I' #Default struct format

        vertices_format = pack('64s', vertices_format) #Convert default format to 64 bytes of char

        primitives_filepath = '%s.primitives' % os.path.splitext(model_filepath)[0] #Primitives file name to save as
        with open(primitives_filepath, 'wb') as f: #Create the file
            #####################################################################
            # Primitives Header:
            f.write(pack('<l', 0x42a14e65)) #Write the primitives header B¡Ne


            #####################################################################
            # VERTICES

            for render_set in render_sets: #For each object/render set
                #If format is...
                if 'xyznuvtb' in render_set['geometry']['primitiveGroups']['groups'][0]['format']: 
                    vertices_format = b'xyznuvtb'
                    vertices_secsize = 32
                    vertices_pcformat = '<3fI2f2I'
                    vertices_format = pack('64s', vertices_format)
                elif 'xyznuvr' in render_set['geometry']['primitiveGroups']['groups'][0]['format']:
                    vertices_format = b'xyznuvr'
                    vertices_secsize = 36
                    vertices_pcformat = '<9f'
                    vertices_format = pack('64s', vertices_format)
                elif 'xyznuviiiwwtb' in render_set['geometry']['primitiveGroups']['groups'][0]['format']:
                    vertices_format = b'xyznuviiiwwtb'
                    vertices_secsize = 37
                    vertices_pcformat = '<3fI2f5B2I'
                    vertices_format = pack('64s', vertices_format)
                elif 'xyznuv' in render_set['geometry']['primitiveGroups']['groups'][0]['format']:
                    vertices_format = b'xyznuv'
                    vertices_secsize = 32
                    vertices_pcformat = '<8f'
                    vertices_format = pack('64s', vertices_format)
                f.write(vertices_format) #First 64 bytes for listing the format
                f.write(pack('<I', render_set['geometry']['primitiveGroups']['nVerticesTotal'])) #List total number of vertices
                for v in render_set['geometry']['primitiveGroups']['groups'][0]['vertices']:
                    f.write(pack(vertices_pcformat, *v)) #For each vertex, write into the file

                vertices_section_size = render_set['geometry']['primitiveGroups']['nVerticesTotal']*vertices_secsize + 68 #Length of vertex block for the end table
                if vertices_section_size%4>0: #Just add a buffer to make it a multiple of four
                    f.write(pack('%ds' % (4 - vertices_section_size%4), b''))
                    vertices_section_size += 4 - vertices_section_size%4

                render_set['geometry']['vertices_section_size'] = vertices_section_size #Update length of vertex block into the array of render sets


            #####################################################################
            # INDICES

            for render_set in render_sets: #For each object/render set
                if render_set['geometry']['primitiveGroups']['nVerticesTotal'] < 0xFFFF: #If smaller amount of vertices (less than 65535)
                    list_format = b'list' #Use list
                    list_pcformat = '<3H' #Use short for each index
                    list_secsize = 6 #Byte length is 6
                    list_format = pack('64s', list_format)

                else:
                    list_format = b'list32' #Use list32
                    list_pcformat = '<3I' #Use integer for each index
                    list_secsize = 12 #Byte length is 12
                    list_format = pack('64s', list_format)

                f.write(list_format) #First 64 bytes for listing the format
                f.write(pack('<I', render_set['geometry']['primitiveGroups']['nIndicesTotal'])) #Write total number of indices
                f.write(pack('<I', render_set['geometry']['primitiveGroups']['nTriangleGroupsTotal'])) #Write number of grousp, should be 0

                for face in render_set['geometry']['primitiveGroups']['groups'][0]['indices']: #For each triangle, 
                    f.write(pack(list_pcformat, face[0], face[1], face[2],)) #Write triangle to file

                #Add renderset info to the end
                f.write(pack('<I', render_set['geometry']['primitiveGroups']['groups'][0]['startIndex']))
                f.write(pack('<I', render_set['geometry']['primitiveGroups']['groups'][0]['nPrimitives']))
                f.write(pack('<I', render_set['geometry']['primitiveGroups']['groups'][0]['startVertex']))
                f.write(pack('<I', render_set['geometry']['primitiveGroups']['groups'][0]['nVertices']))

                #Same as vertices, save length of indices block to end table
                indices_section_size = render_set['geometry']['primitiveGroups']['nPrimitivesTotal']*list_secsize + 72 + 16*render_set['geometry']['primitiveGroups']['nTriangleGroupsTotal']
                if indices_section_size%4>0:
                    f.write(pack('%ds' % (4 - indices_section_size%4), b''))
                    indices_section_size += 4 - indices_section_size%4

                render_set['geometry']['indices_section_size'] = indices_section_size


            #####################################################################
            # PACKED INFORMATION

            #Add names, name lengths, and section length to the end table
            packed_groups_info = b''

            for render_set in render_sets:
                vertices_section_name_length = len(render_set['geometry']['vertices']) #Length of vertices name
                vertices_null_bytes = 0 
                if vertices_section_name_length%4>0:
                    vertices_null_bytes = 4-vertices_section_name_length%4

                pc_format = '<l16sI%ds' % (vertices_section_name_length + vertices_null_bytes)
                pc_vals = (
                    render_set['geometry']['vertices_section_size'],
                    b'',
                    vertices_section_name_length,
                    bytes(render_set['geometry']['vertices'], encoding='utf-8')
                )
                packed_groups_info += pack(pc_format, *pc_vals)


            for render_set in render_sets:
                indices_section_name_length = len(render_set['geometry']['primitive'])
                indices_null_bytes = 0
                if indices_section_name_length%4>0:
                    indices_null_bytes = 4-indices_section_name_length%4

                pc_format = '<l16sI%ds' % (indices_section_name_length + indices_null_bytes)
                pc_vals = (
                    render_set['geometry']['indices_section_size'],
                    b'',
                    indices_section_name_length,
                    bytes(render_set['geometry']['primitive'], encoding='utf-8')
                )
                packed_groups_info += pack(pc_format, *pc_vals)


            f.write(packed_groups_info)
            f.write(pack('<l', len(packed_groups_info)))


        #####################################################################
        # .visual

        #Creates new xml style document
        impl = getDOMImplementation()
        visual_document = impl.createDocument(None, 'root', None)
        visual_element = visual_document.documentElement


        #####################################################################
        # node

        #Add empty nodes
        set_nodes(export_info['nodes'], visual_element, visual_document)


        #####################################################################
        # renderSet

        for render_set in render_sets: #For each render set, 
            __renderSet = visual_document.createElement('renderSet') #Create unbound node RenderSet
            __treatAsWorldSpaceObject = visual_document.createElement('treatAsWorldSpaceObject') #Create unbound node treatAsWorldSpaceObject
            if 'xyznuviiiwwtb' in render_set['geometry']['primitiveGroups']['groups'][0]['format']: #If weighted, mark as true
                __treatAsWorldSpaceObject.appendChild(visual_document.createTextNode('true'))
            else: #Else, is false
                __treatAsWorldSpaceObject.appendChild(visual_document.createTextNode('false'))
            __renderSet.appendChild(__treatAsWorldSpaceObject) #Add treatAsWorldSpaceObject as child to the renderSet

            for node_name in render_set['nodes']: #Add nodes to the renderSet
                __node = visual_document.createElement('node')
                __node.appendChild(visual_document.createTextNode(node_name))
                __renderSet.appendChild(__node)


            #####################################################################
            # geometry

            __geometry = visual_document.createElement('geometry') #Create unbound node geometry

            __vertices = visual_document.createElement('vertices') #Create unbound node vertices
            __vertices.appendChild(visual_document.createTextNode(render_set['geometry']['vertices'])) #Add name of vertices
            __geometry.appendChild(__vertices) #Add geometry as child to geometry

            __primitive = visual_document.createElement('primitive') #Create unbound node primitive
            __primitive.appendChild(visual_document.createTextNode(render_set['geometry']['primitive'])) #Add name of indices
            __geometry.appendChild(__primitive) #Add primitive as child to geometry

            __primitiveGroup = visual_document.createElement('primitiveGroup')
            __primitiveGroup.appendChild(visual_document.createTextNode(str(0))) #Add index of primitive group


            #####################################################################
            # primitiveGroup -> material

            __material = visual_document.createElement('material') #Create unbound node material

            __identifier = visual_document.createElement('identifier') #Create unbound node identifier 
            __identifier.appendChild(visual_document.createTextNode(render_set['geometry']['primitiveGroups']['groups'][0]['name'])) #Add name of material
            __material.appendChild(__identifier) #Add identifier as child to material

            __mfm = visual_document.createElement('mfm') #Create unbound node mfm
            __mfm.appendChild(visual_document.createTextNode(render_set['geometry']['primitiveGroups']['groups'][0]['mfm'])) #Add mfm path
            __material.appendChild(__mfm) #Add mfm as child to material
            
            __primitiveGroup.appendChild(__material) #Add material as child to primitiveGroup
            __geometry.appendChild(__primitiveGroup) #Add primitiveGroup as child to geometry

            __renderSet.appendChild(__geometry) #Add geometry as child to renderSet
            visual_element.appendChild(__renderSet) #Add renderSet as child to root

        __boundingBox = visual_document.createElement('boundingBox') #Create unbound node boundingBox

        __min = visual_document.createElement('min') #Create unbound node min
        __min.appendChild(visual_document.createTextNode('%f %f %f' % export_info['bb_min'])) #Add the bounding box min
        __boundingBox.appendChild(__min) #Add min as child to boundingBox

        __max = visual_document.createElement('max') #Create unbound node max
        __max.appendChild(visual_document.createTextNode('%f %f %f' % export_info['bb_max'])) #Add the bounding box max
        __boundingBox.appendChild(__max) #Add max as child to boundingBox

        visual_element.appendChild(__boundingBox) #Add boundingBox as child to root


        #####################################################################
        # save .visual

        visual_filepath = '%s.visual' % os.path.splitext(model_filepath)[0]
        with open(visual_filepath, 'w') as f:
            f.write(visual_document.toprettyxml())
        
        tree = ET.parse(visual_filepath)
        root = tree.getroot()
        root.tag= os.path.basename(visual_filepath)
        tree.write(visual_filepath)

        #####################################################################
        # .temp_model

        model_document = impl.createDocument(None, 'root', None)
        model_element = model_document.documentElement

        __info_block = model_document.createComment('\n\tblender_version: %s\n\texporter_version: %s\n\t' % (bpy.app.version_string, export_info['exporter_version']))
        model_element.appendChild(__info_block)

        __nodefullVisual = model_document.createElement('nodefullVisual')
        __nodefullVisual.appendChild(model_document.createTextNode(os.path.splitext(visual_filepath)[0]))
        model_element.appendChild(__nodefullVisual)


        #####################################################################
        # save .temp_model

        with open(model_filepath, 'w') as f:
            f.write(model_document.toprettyxml())
