''' SkepticalFox 2015-2018 '''



#####################################################################
# imports

import os
from .common.XmlUnpacker import XmlUnpacker
from .loaddatamesh import LoadDataMesh
import bpy
from bpy_extras.io_utils import unpack_list
from mathutils import Vector

#####################################################################
# Get empty nodes

def get_Empty_by_nodes(elem, empty_obj = None):
    if (elem.find('identifier') is None) or (elem.find('transform') is None): #If not an node, skip
        return None

    identifier = elem.find('identifier').text.strip()
    row0 = asVector(elem.find('transform').find('row0').text) #Scale x(only the first in the tuple)
    row1 = asVector(elem.find('transform').find('row1').text) #Scale z(only the second in the tuple)
    row2 = asVector(elem.find('transform').find('row2').text) #Scale y(only the third in the tuple)
    row3 = asVector(elem.find('transform').find('row3').text) #Location (only the first three in the tuple)
    scale = Vector( (row0.x, row2.z, row1.y) ) #Form "tuple" of scale
    location = row3.xzy #Form "tuple" of location

    ob = bpy.data.objects.new(identifier, None) #Create new empty object

    ob.scale = scale #Set scale
    ob.location = location #Set location
    if empty_obj is not None: #If parent parameter exists
        ob.parent = empty_obj #Set parent

    bpy.context.scene.collection.objects.link(ob) #Put into the scene collection
    ob.hide_set(False) #Show empties
    
    for node in elem.findall('node'):
        get_Empty_by_nodes(node, ob) #For each child, recurse with this object as parent argument

    return ob #Return empty (used to mark root)

def asVector(string):
    return Vector(tuple(map(float, string.strip().split())))
#####################################################################
# BigWorldModelLoader

class BigWorldModelLoader:

    root_empty_ob = None #Main root

    def load_from_file(self, model_filepath, import_empty, debug_mode, displacement, rotation, scale):
        model_dir = os.path.dirname(model_filepath) #Directory of the file
        model_filename = os.path.basename(model_filepath) #Name of the file

        visual_filename = '%s.visual' % os.path.splitext(model_filename)[0] #Name of the visual file
        primitives_filename = '%s.primitives' % os.path.splitext(model_filename)[0] #Name of the primitives file
        
        visual_filepath = '' 
        primitives_filepath = '' 
        if os.path.exists(os.path.join(model_dir, visual_filename)): #If visual file exists
            visual_filepath = os.path.join(model_dir, visual_filename) #Full path of the visual file
            primitives_filepath = os.path.join(model_dir, primitives_filename) #Full path of the primitives file

        if visual_filepath and primitives_filepath: #If visual exists
            with open(visual_filepath, 'rb') as f: #Open visual file
                visual = XmlUnpacker().read(f) #Parse as XML

            if visual.find('renderSet') is not None: #Check if renderSet node(s) exist in the visual file
                for renderSet in visual.findall('renderSet'): #For each renderSet
                    vres_name = renderSet.find('geometry/vertices').text.strip() #Vertices group name
                    pres_name = renderSet.find('geometry/primitive').text.strip() #Indices group name
                    mesh_name = os.path.splitext(vres_name)[0] #Name of object
                    bmesh = bpy.data.meshes.new(mesh_name) #Create new blender object with name from visual

                    dataMesh = LoadDataMesh(primitives_filepath, vres_name, pres_name, debug_mode) #Compiles the vertices and indices into lists

                    bmesh.vertices.add(len(dataMesh.vertices)) #Add vertices slots to the mesh
                    bmesh.vertices.foreach_set('co', unpack_list(dataMesh.vertices)) #Add coordinates to each vertex
                    bmesh.vertices.foreach_set('normal', unpack_list(dataMesh.normal_list)) #Add normal values to each vertex

                    nbr_faces = len(dataMesh.indices) #Number of faces (dataMesh.indices is a list of triangles)
                    bmesh.polygons.add(nbr_faces) #Add face slots

                    #I believe polygon loops data is an overlay over the mesh loop data
                    bmesh.polygons.foreach_set('loop_start', range(0, nbr_faces*3, 3)) #Start of the loops of the face
                    bmesh.polygons.foreach_set('loop_total', (3,)*nbr_faces) #Number of loops per face(primitives are always triangles, so always 3) 

                    bmesh.loops.add(nbr_faces*3) #Loops are a vertex paired with a side for uv maps
                    bmesh.loops.foreach_set('vertex_index', unpack_list(dataMesh.indices)) #Set the vertex for each loop

                    bmesh.polygons.foreach_set('use_smooth', [True]*nbr_faces) #Smooth shading

                    uv_faces = bmesh.uv_layers.new() #Create new layer
                    uv_faces.name = 'uv1' #Rename
                    uv_faces.active = True #Make it the current map

                    uv_layer = bmesh.uv_layers['uv1'].data[:] #Allow editing of the uv layer

                    for poly in bmesh.polygons: #For each triangle
                        for li in poly.loop_indices: #For each loop,
                            vi = bmesh.loops[li].vertex_index #Get indices
                            uv_layer[li].uv = dataMesh.uv_list[vi] #Map the vertex with each index
                            
                    _identifier = renderSet.findall('geometry/primitiveGroup')[0].find('material/identifier').text.strip() #Material identifier
                    material = bpy.data.materials.new(_identifier) #Create a new material
                    material.Vertex_Format = dataMesh.vertices_type.strip() #Save the vertex format for export
                    if renderSet.findall('geometry/primitiveGroup')[0].find('material/mfm')!=None: #If mfm path exists
                        material.BigWorld_mfm_Path = renderSet.findall('geometry/primitiveGroup')[0].find('material/mfm').text.strip() #Save the mfm format for export
                    else:
                        material.BigWorld_mfm_Path = "Placeholder" #Else, just put in a placeholder
                    bmesh.materials.append(material) #Apply the material to the mesh
                    
                    bmesh.update() #Update mesh

                    ob = bpy.data.objects.new(mesh_name, bmesh) #Make it into an object

                    if 'true' in renderSet.find('treatAsWorldSpaceObject').text: #If has vector groups
                        if dataMesh.bones_info: #If bones exist
                            bone_arr = [] #Bone list
                            for node in renderSet.findall('node'):
                                bone_name = node.text.strip() #Set bone name from nodes
                                group = ob.vertex_groups.new(name = bone_name) #Create new weight layer
                                bone_arr.append({'name': bone_name, 'group': group})
                            #Don't understand the next part, but is about weights
                            for vert_idx, iiiww in enumerate(dataMesh.bones_info): #Example weight info is (0, 6, 0, 255, 0)
                                bone_idx_vals = iiiww[0:3]
                                bone_wght_vals = iiiww[3:5]

                                index1 = bone_idx_vals[0]//3
                                index2 = bone_idx_vals[1]//3
                                index3 = bone_idx_vals[2]//3
                                
                                weight1 = bone_wght_vals[0]/255.0
                                weight2 = bone_wght_vals[1]/255.0
                                weight3 = 1 - weight1 - weight2

                                bone_arr[index1]['group'].add([vert_idx], weight1, 'ADD')
                                bone_arr[index2]['group'].add([vert_idx], weight2, 'ADD')
                                bone_arr[index3]['group'].add([vert_idx], weight3, 'ADD')

                    ob.scale = Vector(scale) #Scale
                    ob.rotation_euler = Vector(rotation) #Rotation
                    ob.location = Vector(displacement) #Displacement
                    
                    if import_empty: #Organizes the objects and empties
                        if self.root_empty_ob is None:
                            self.root_empty_ob = get_Empty_by_nodes(visual.findall('node')[0]) #Set the scene root
                        if self.root_empty_ob is not None:
                            ob.parent = self.root_empty_ob #Set the parent of the object as the scene root
                    
                    bpy.context.scene.collection.objects.link(ob) #Adds to the scene collection 
