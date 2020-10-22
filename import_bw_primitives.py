''' SkepticalFox 2015-2018 '''



#####################################################################
# imports

import os

from .common import *

from .loaddatamesh import LoadDataMesh

from .common.consts import visual_property_dict

import bpy

from bpy_extras.io_utils import unpack_list

from mathutils import Vector

#####################################################################
# Get empty nodes

def get_Empty_by_nodes(elem, empty_obj = None):
    if (elem.find('identifier') is None) or (elem.find('transform') is None):
        return None

    identifier = elem.find('identifier').text.strip()
    row0 = shr_AsVector(elem.find('transform').find('row0').text) #Scale (only the first in the tuple)
    row1 = shr_AsVector(elem.find('transform').find('row1').text) #Scale (only the second in the tuple)
    row2 = shr_AsVector(elem.find('transform').find('row2').text) #Scale (only the third in the tuple)
    row3 = shr_AsVector(elem.find('transform').find('row3').text) #Location (only the first three in the tuple)
    scale = Vector( (row0.x, row2.z, row1.y) )
    location = row3.xzy

    ob = bpy.data.objects.new(identifier, None) #Create new object

    ob.scale = scale
    ob.location = location
    if empty_obj is not None:
        ob.parent = empty_obj #empty_obj is the previous object

    bpy.context.scene.collection.objects.link(ob)
    ob.hide_set(False)
    
    for node in elem.findall('node'):
        get_Empty_by_nodes(node, ob) #for each child

    return ob

#####################################################################
# BigWorldModelLoader

class BigWorldModelLoader:

    root_empty_ob = None

    def load_from_file(self, model_filepath, import_empty, debug_mode):
        model_dir = os.path.dirname(model_filepath) #Directory of the file
        model_filename = os.path.basename(model_filepath) #Name of the file

        visual_filename = '%s.visual' % os.path.splitext(model_filename)[0] #Name of the visual file
        primitives_filename = '%s.primitives' % os.path.splitext(model_filename)[0] #Name of the primitives file
        
        visual_filepath = '' 
        primitives_filepath = '' 
        if os.path.exists(os.path.join(model_dir, visual_filename)):
            visual_filepath = os.path.join(model_dir, visual_filename) #Full name of the visual file
            primitives_filepath = os.path.join(model_dir, primitives_filename) #Full name of the primitives file

        if visual_filepath and primitives_filepath:
            with open(visual_filepath, 'rb') as f:
                visual = g_XmlUnpacker.read(f)

            if visual.find('renderSet') is not None: #Check if renderSet node(s) exist in the visual file
                for renderSet in visual.findall('renderSet'):
                    vres_name = renderSet.find('geometry/vertices').text.strip()
                    pres_name = renderSet.find('geometry/primitive').text.strip()
                    mesh_name = os.path.splitext(vres_name)[0]
                    bmesh = bpy.data.meshes.new(mesh_name)

                    dataMesh = LoadDataMesh(primitives_filepath, vres_name, pres_name, debug_mode)

                    bmesh.vertices.add(len(dataMesh.vertices))
                    bmesh.vertices.foreach_set('co', unpack_list(dataMesh.vertices)) #Add coordinates

                    # TODO:
                    # bmesh.vertices.foreach_set('normal', unpack_list(dataMesh.normal_list))

                    nbr_faces = len(dataMesh.indices) #Number of faces (dataMesh.indices is a list of tuples)
                    bmesh.polygons.add(nbr_faces) #Add face slots

                    #I believe polygon loops data is an overlay over the mesh loop data
                    bmesh.polygons.foreach_set('loop_start', range(0, nbr_faces*3, 3)) #Start of the loops of the face
                    bmesh.polygons.foreach_set('loop_total', (3,)*nbr_faces) #Number of loops per face(primitives are always triangles, so always 3) 

                    bmesh.loops.add(nbr_faces*3) #Loops are a vertex paired with a side for uv maps
                    bmesh.loops.foreach_set('vertex_index', unpack_list(dataMesh.indices)) #
                    #nbr_faces = len(bmesh.polygons) #Seems to be redundent

                    bmesh.polygons.foreach_set('use_smooth', [True]*nbr_faces) #Smooth shading

                    if dataMesh.uv_list:
                        uv_faces = bmesh.uv_layers.new() #Create new layer
                        uv_faces.name = 'uv1' #Rename
                        uv_faces.active = True #Make it the current map

                        uv_layer = bmesh.uv_layers['uv1'].data[:] #Allow editing of the uv map

                        for poly in bmesh.polygons:
                            for li in poly.loop_indices:
                                vi = bmesh.loops[li].vertex_index
                                uv_layer[li].uv = dataMesh.uv_list[vi] #Map the vertex with each index
                    else:
                        print('[Import Error] UV error')

                    for primitiveGroup in renderSet.findall('geometry/primitiveGroup'):
                        _identifier = primitiveGroup.find('material/identifier').text.strip() #Material identifier

                        material = bpy.data.materials.new(_identifier) #Create a new material
                        
                        material.Vertex_Format = dataMesh.vertices_type.strip() #Save the vertex format for export

                        bmesh.materials.append(material) #Apply the material to the mesh
                    
                    bmesh.validate()
                    bmesh.update() #Update mesh

                    ob = bpy.data.objects.new(mesh_name, bmesh) #Make it into an object

                    if 'true' in renderSet.find('treatAsWorldSpaceObject').text:
                        if dataMesh.bones_info:
                            bone_arr = []
                            for node in renderSet.findall('node'):
                                bone_name = node.text.strip() #???
                                group = ob.vertex_groups.new(name = bone_name) #Create new weight layer
                                bone_arr.append({'name': bone_name, 'group': group})
                            #Don't understand the next part, but is about weights
                            for vert_idx, iiiww in enumerate(dataMesh.bones_info):
                                bone_idx_vals = iiiww[0:3]
                                bone_wght_vals = iiiww[3:5]

                                index1 = bone_idx_vals[0]//3
                                index2 = bone_idx_vals[1]//3
                                index3 = bone_idx_vals[2]//3

                                weight1 = bone_wght_vals[0]/255.0
                                weight2 = bone_wght_vals[1]/255.0
                                weight3 = 1 - weight1 - weight2

                                # types:
                                # 'ADD', 'REPLACE', 'SUBTRACT'
                                bone_arr[index1]['group'].add([vert_idx], weight1, 'ADD')
                                bone_arr[index2]['group'].add([vert_idx], weight2, 'ADD')
                                bone_arr[index3]['group'].add([vert_idx], weight3, 'ADD')

                    ob.scale = Vector((1.0, 1.0, 1.0)) #Scale
                    ob.rotation_euler = Vector((0.0, 0.0, 0.0)) #Rotation
                    ob.location = Vector((0.0, 0.0, 0.0)) #Displacement
                    #Organizes the objects and empties
                    if import_empty: 
                        if self.root_empty_ob is None:
                            self.root_empty_ob = get_Empty_by_nodes(visual.findall('node')[0]) #Set the scene root
                        if self.root_empty_ob is not None:
                            ob.parent = self.root_empty_ob #Set the parent of the object as the scene root
                    #Adds to the scene collection 
                    bpy.context.scene.collection.objects.link(ob)
