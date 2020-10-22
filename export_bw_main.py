''' ShadowHunterRUS 2015-2016 '''
''' + ShadowyBandit 2020 '''


#####################################################################
# imports

import os

from struct import pack
from ctypes import c_uint32
from xml.dom.minidom import getDOMImplementation
from .common.consts import visual_property_dict

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
    def get_vertices_and_indices(self, object_list: list):
        render_sets = []
        for object in object_list:
            render_set = {
                'nodes'    : [],
                'geometry' : {
                    'vertices'              : 'vertices',
                    'primitive'             : 'indices',
                    'primitiveGroups'       : {},
                    'indices_section_size'  : 0,
                    'vertices_section_size' : 0
                }
            }

            render_set['geometry']['vertices'] = '%s.vertices' % os.path.splitext(object.name)[0]
            render_set['geometry']['primitive'] = '%s.indices' % os.path.splitext(object.name)[0]
            for vg in object.vertex_groups:
                render_set['nodes'].append( vg.name )

            primitives_group = {
                'groups'          : {},
                'nIndices'        : 0,
                'nVertices'       : 0,
                'nTriangleGroups' : 0,
                'nPrimitives'     : 0,
            }

            for mat_id, mat in enumerate(object.data.materials):
                primitives_group['groups'][mat_id] = {
                    'name'                         : os.path.splitext(mat.name)[0],
                    'id'                           : mat_id,
                    'format'                       : mat.Vertex_Format,
                    'vertices'                     : [],
                    'indices'                      : []
                }
            iv = 0
            ii = 0
            uv_layer = object.data.uv_layers.active.data[:]

            object.data.calc_normals()
            object.data.calc_tangents(uvmap='uv1')

            old2new = {}

            for mat_id, mat in primitives_group['groups'].items():
                mat['startVertex'] = iv
                mat['startIndex'] = ii

                for poly in object.data.polygons:
                    if poly.material_index == mat_id:
                        loop = poly.loop_indices
                        for vidx, i in enumerate(loop):
                            vert = object.data.vertices[poly.vertices[vidx]]
                            (x, y, z) = vert.co
                            y = -y
                            n = object.data.loops[i].normal.copy()
                            n = packNormal(n)
                            (u, v) = uv_layer[i].uv
                            t = object.data.loops[i].tangent.copy()
                            t = packNormal(t)
                            bn = object.data.loops[i].bitangent.copy()
                            bn = packNormal(bn)
                            XYZNUVIIIWWTB = (x, z, y, n, u, 1-v)
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

                            else:
                                print('Warn: len(vert.groups) == `%s`' % len(vert.groups))

                            IIIWW = (index1, index2, index3, weight1, weight2)
                            XYZNUVIIIWWTB += IIIWW

                            XYZNUVIIIWWTB += TB
                            mat['vertices'].append( XYZNUVIIIWWTB )

                            old2new[i] = iv
                            iv += 1

                        if len(loop) == 3:
                            mat['indices'].append( (old2new[loop[2]], old2new[loop[1]], old2new[loop[0]]) )
                            ii += 3

                        elif len(loop) == 4:
                            mat['indices'].append( (old2new[loop[2]], old2new[loop[1]], old2new[loop[0]]) )
                            mat['indices'].append( (old2new[loop[3]], old2new[loop[2]], old2new[loop[0]]) )
                            ii += 6

                mat['nVertices'] = iv - mat['startVertex']
                mat['nPrimitives'] = (ii - mat['startIndex'])//3

            primitives_group['nIndices'] = ii
            primitives_group['nPrimitives'] = ii//3
            primitives_group['nVertices'] = iv
            primitives_group['nTriangleGroups'] = len(primitives_group['groups'])
            object.data.free_tangents()

            render_set['geometry']['primitiveGroups'] = primitives_group

            render_sets.append( render_set )

        return render_sets


    def export(self, object_list: list, model_filepath: str, export_info: dict):
        render_sets = self.get_vertices_and_indices(object_list)

        vertices_format = b'xyznuviiiwwtb'
        vertices_secsize = 37
        vertices_pcformat = '<3fI2f5B2I'

        vertices_format = pack('64s', vertices_format)

        primitives_filepath = '%s.primitives' % os.path.splitext(model_filepath)[0]
        with open(primitives_filepath, 'wb') as f:
            #####################################################################
            # Primitives Header:
            f.write(pack('<l', 0x42a14e65))


            #####################################################################
            # VERTICES

            for render_set in render_sets:
                f.write(vertices_format)
                f.write(pack('<I', render_set['geometry']['primitiveGroups']['nVertices']))
                for pg in render_set['geometry']['primitiveGroups']['groups'].values():
                    for v in pg['vertices']:
                        f.write(pack(vertices_pcformat, *v))

                vertices_section_size = render_set['geometry']['primitiveGroups']['nVertices']*vertices_secsize + 68
                if vertices_section_size%4>0:
                    f.write(pack('%ds' % (4 - vertices_section_size%4), b''))
                    vertices_section_size += 4 - vertices_section_size%4

                render_set['geometry']['vertices_section_size'] = vertices_section_size


            #####################################################################
            # INDICES

            for render_set in render_sets:
                if render_set['geometry']['primitiveGroups']['nVertices'] < 0xFFFF:
                    list_format = b'list'
                    list_pcformat = '<3H'
                    list_secsize = 6
                    list_format = pack('64s', list_format)

                else:
                    list_format = b'list32'
                    list_pcformat = '<3I'
                    list_secsize = 12
                    list_format = pack('64s', list_format)

                f.write(list_format)
                f.write(pack('<I', render_set['geometry']['primitiveGroups']['nIndices']))
                f.write(pack('<I', render_set['geometry']['primitiveGroups']['nTriangleGroups']))

                for pg in render_set['geometry']['primitiveGroups']['groups'].values():
                    for face in pg['indices']:
                        f.write(pack(list_pcformat, face[0], face[1], face[2],))

                    f.write(pack('<I', pg['startIndex']))
                    f.write(pack('<I', pg['nPrimitives']))
                    f.write(pack('<I', pg['startVertex']))
                    f.write(pack('<I', pg['nVertices']))

                indices_section_size = render_set['geometry']['primitiveGroups']['nPrimitives']*list_secsize + 72 + 16*render_set['geometry']['primitiveGroups']['nTriangleGroups']
                if indices_section_size%4>0:
                    f.write(pack('%ds' % (4 - indices_section_size%4), b''))
                    indices_section_size += 4 - indices_section_size%4

                render_set['geometry']['indices_section_size'] = indices_section_size


            #####################################################################
            # PACKED INFORMATION

            packed_groups_info = b''

            for render_set in render_sets:
                vertices_section_name_length = len(render_set['geometry']['vertices'])
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

        impl = getDOMImplementation()
        visual_document = impl.createDocument(None, 'root', None)
        visual_element = visual_document.documentElement


        #####################################################################
        # node

        set_nodes(export_info['nodes'], visual_element, visual_document)


        #####################################################################
        # renderSet

        for render_set in render_sets:
            __renderSet = visual_document.createElement('renderSet')

            __treatAsWorldSpaceObject = visual_document.createElement('treatAsWorldSpaceObject')
            __treatAsWorldSpaceObject.appendChild(visual_document.createTextNode('true'))
            __renderSet.appendChild(__treatAsWorldSpaceObject)
            del __treatAsWorldSpaceObject

            for node_name in render_set['nodes']:
                __node = visual_document.createElement('node')
                __node.appendChild(visual_document.createTextNode(node_name))
                __renderSet.appendChild(__node)
                del __node


            #####################################################################
            # geometry

            __geometry = visual_document.createElement('geometry')

            __vertices = visual_document.createElement('vertices')
            __vertices.appendChild(visual_document.createTextNode(render_set['geometry']['vertices']))
            __geometry.appendChild(__vertices)

            __primitive = visual_document.createElement('primitive')
            __primitive.appendChild(visual_document.createTextNode(render_set['geometry']['primitive']))
            __geometry.appendChild(__primitive)

            for mat_id, mat in render_set['geometry']['primitiveGroups']['groups'].items():
                __primitiveGroup = visual_document.createElement('primitiveGroup')
                __primitiveGroup.appendChild(visual_document.createTextNode(str(mat_id)))


                #####################################################################
                # primitiveGroup -> material

                __material = visual_document.createElement('material')

                __identifier = visual_document.createElement('identifier')
                __identifier.appendChild(visual_document.createTextNode(mat['name']))
                __material.appendChild(__identifier)

                __collisionFlags = visual_document.createElement('collisionFlags')
                __collisionFlags.appendChild(visual_document.createTextNode('0'))
                __material.appendChild(__collisionFlags)

                __materialKind = visual_document.createElement('materialKind')
                __materialKind.appendChild(visual_document.createTextNode('0'))
                __material.appendChild(__materialKind)

                for prop_type, prop_names in visual_property_dict.items():
                    for prop_name in prop_names:
                        if mat.get(prop_name):
                            __property = visual_document.createElement('property')
                            __property.appendChild(visual_document.createTextNode(prop_name))
                            __property_value = visual_document.createElement(prop_type)
                            __property_value.appendChild(visual_document.createTextNode(mat[prop_name]))
                            __property.appendChild(__property_value)
                            __material.appendChild(__property)

                __primitiveGroup.appendChild(__material)

                if mat.get('groupOrigin'):
                    __groupOrigin = visual_document.createElement('groupOrigin')
                    __groupOrigin.appendChild(visual_document.createTextNode(mat['groupOrigin']))
                    __primitiveGroup.appendChild(__groupOrigin)

                __geometry.appendChild(__primitiveGroup)

            __renderSet.appendChild(__geometry)
            visual_element.appendChild(__renderSet)

        __boundingBox = visual_document.createElement('boundingBox')

        __min = visual_document.createElement('min')
        __min.appendChild(visual_document.createTextNode('%f %f %f' % export_info['bb_min']))
        __boundingBox.appendChild(__min)

        __max = visual_document.createElement('max')
        __max.appendChild(visual_document.createTextNode('%f %f %f' % export_info['bb_max']))
        __boundingBox.appendChild(__max)

        visual_element.appendChild(__boundingBox)


        #####################################################################
        # save .visual

        visual_filepath = '%s.visual' % os.path.splitext(model_filepath)[0]
        with open(visual_filepath, 'w') as f:
            f.write(visual_document.toprettyxml())


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
