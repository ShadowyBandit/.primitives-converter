''' SkepticalFox 2015-2018 '''
''' + ShadowyBandit 2020 '''

#####################################################################
# Addon Description

bl_info = {
    'name': 'BigWorld Model (.primitives)',
    'author': 'SkepticalFox+ShadowyBandit',
    'version': (1, 0, 1),
    'blender': (2, 80, 0),
    'location': 'File > Import-Export',
    'description': 'World of Warships BigWorld Model Import/Export plugin',
    'warning': 'In progress',
    'wiki_url': 'http://www.koreanrandom.com/forum/topic/28240-/',
    'category': 'Import-Export',
}

#####################################################################
# Imports and Registration

import os
import bpy
from mathutils import Vector
from bpy_extras.io_utils import ImportHelper, ExportHelper
from .import_bw_primitives import BigWorldModelLoader
import math

if __name__ == '__main__':
    register()
        
def register():
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import) #Importbar add option
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export) #Exportbar add option
    bpy.utils.register_class(Import_From_ModelFile) #Register import addon
    bpy.utils.register_class(Export_ModelFile) #Register export addon
    bpy.types.Material.Vertex_Format = bpy.props.StringProperty( #Save vertex type for export
        name = 'Format',
        default = '',
        description = 'Save vertex type for export'
    )
    bpy.types.Material.BigWorld_mfm_Path = bpy.props.StringProperty( #saves mfm path data, which contains extra rendering info
        name = 'mfm',
        default = '',
        description = '.mfm file path'
    )
    bpy.utils.register_class(BigWorld_Material_Panel) #Register material subpanel addon

def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import) #Importbar remove option
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export) #Exportbar remove option
    bpy.utils.unregister_class(BigWorld_Material_Panel) #Unregister material subpanel addon
    bpy.utils.unregister_class(Import_From_ModelFile) #Unregister import addon
    bpy.utils.unregister_class(Export_ModelFile) #Unregister export addon

#####################################################################
# Menu operators

def menu_func_import(self, context):
    self.layout.operator('import.model', text = 'World of Warships BigWorld Model (.primitives+.visual)')

def menu_func_export(self, context):
    self.layout.operator('export.model', text='World of Warships BigWorld Model (.primitives+.visual+.temp_model)')

#####################################################################
# BigWorld Material Panel

class BigWorld_Material_Panel(bpy.types.Panel):
    bl_label = 'BigWorld Material' #Name
    bl_idname = 'MATERIAL_PT_bigworld_material' #Id
    bl_space_type = 'PROPERTIES' #???
    bl_region_type = 'WINDOW' #???
    bl_options = {'DEFAULT_CLOSED'} #Normally closed
    bl_context = 'material' #Material tab

    def draw(self, context):
        mat = context.material #Material tab
        self.layout.prop(mat, 'Vertex_Format') #Add vertex type
        self.layout.prop(mat, 'BigWorld_mfm_Path') #mfm Path, just a placeholder

#####################################################################
# Import

class Import_From_ModelFile(bpy.types.Operator, ImportHelper):
    bl_idname = 'import.model' #Id
    bl_label = 'Import File' #Label
    bl_description = 'Import Ship Model' #Discription

    filename_ext = '.primitives' 
    filter_glob : bpy.props.StringProperty( #Filter file extension
        default = '*.primitives',
        options = {'HIDDEN'}
    )

    import_empty : bpy.props.BoolProperty( #Checkbox
        name = 'Import Empty',
        description = 'Import empty axes, required for modding',
        default = True
    )

    debug_mode : bpy.props.BoolProperty( #Checkbox
        name = 'Debug Mode',
        description = 'Will display extra info in the System Console',
        default = False
    )

    disp_x : bpy.props.FloatProperty( #Float box
        name = 'Position x',
        description = 'Do not change when modding, edit .visual instead',
        default = 0.0
    )

    disp_y : bpy.props.FloatProperty( #Float box
        name = 'Position y',
        description = 'Do not change when modding, edit .visual instead',
        default = 0.0
    )

    disp_z : bpy.props.FloatProperty( #Float box
        name = 'Position z',
        description = 'Do not change when modding, edit .visual instead',
        default = 0.0
    )

    rot_x : bpy.props.FloatProperty( #Float box
        name = 'Rotation x',
        description = 'Do not change when modding, edit .visual instead',
        default = 0.0,
        min = -180,
        max = 180
    )

    rot_y : bpy.props.FloatProperty( #Float box
        name = 'Rotation y',
        description = 'Do not change when modding, edit .visual instead',
        default = 0.0,
        min = -180,
        max = 180
    )

    rot_z : bpy.props.FloatProperty( #Float box
        name = 'Rotation z',
        description = 'Do not change when modding, edit .visual instead',
        default = 0.0,
        min = -180,
        max = 180
    )

    disp_z : bpy.props.FloatProperty( #Float box
        name = 'Position z',
        description = 'Do not change when modding, edit .visual instead',
        default = 0.0
    )

    scale_x : bpy.props.FloatProperty( #Float box
        name = 'Scale x',
        description = 'Do not change when modding, edit .visual instead',
        default = 1.0
    )

    scale_y : bpy.props.FloatProperty( #Float box
        name = 'Scale y',
        description = 'Do not change when modding, edit .visual instead',
        default = 1.0
    )

    scale_z : bpy.props.FloatProperty( #Float box
        name = 'Scale z',
        description = 'Do not change when modding, edit .visual instead',
        default = 1.0
    )

    def execute(self, context): #Main method
        print('='*48) #Divider
        print('[Import Info] Import %s' % os.path.basename(self.filepath)) #Filename info
        try:
            bw_model = BigWorldModelLoader()
            bw_model.load_from_file(self.filepath, self.import_empty, self.debug_mode,
                                    (self.disp_x, self.disp_y, self.disp_z),
                                    (self.rot_x*math.pi/180, self.rot_y*math.pi/180, self.rot_z*math.pi/180), #Convert from x radians to y radius
                                    (self.scale_x, self.scale_y, self.scale_z)) #Convert the file
        except:
            self.report({'ERROR'}, 'Error in import %s!' % os.path.basename(self.filepath))
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}
        return {'FINISHED'}

    def draw(self, context): #Edit the file import window
        layout = self.layout
        layout.prop(self, 'import_empty')
        layout.prop(self, 'debug_mode')
        layout.prop(self, 'disp_x')
        layout.prop(self, 'disp_y')
        layout.prop(self, 'disp_z')
        layout.prop(self, 'rot_x')
        layout.prop(self, 'rot_y')
        layout.prop(self, 'rot_z')
        layout.prop(self, 'scale_x')
        layout.prop(self, 'scale_y')
        layout.prop(self, 'scale_z')

#####################################################################
# Empty Axes from Blender

def get_nodes_by_empty(obj, export_info, is_root=True):
    #Set name
    if is_root:
        node_name = 'Scene Root'
    else:
        node_name = os.path.splitext(obj.name)[0]
    #Add empty to recursive dictionary
    export_info[node_name] = {
        'loc': obj.location.xzy.to_tuple(),
        'scale': obj.scale.xzy.to_tuple(),
        'children': {}
    }
    obj_models = [] #Children objects
    for child in obj.children:
        if (child.data is None) and isinstance(child, bpy.types.Object): #If is an empty object
            get_nodes_by_empty(child, export_info[node_name]['children'], False) #Add to dictionary
        elif isinstance(child.data, bpy.types.Mesh): #Else if a mesh object
            obj_models.append(child) #Add to array
    return obj_models #Return array for recursion

#####################################################################
# Export

class Export_ModelFile(bpy.types.Operator, ExportHelper):
    bl_idname = 'export.model'
    bl_label = 'Export Model'
    bl_description = 'Export BigWorld Model'

    filename_ext = '.temp_model'
    filter_glob : bpy.props.StringProperty( #Filter
        default = '*.temp_model',
        options = {'HIDDEN'}
    )

    debug_mode : bpy.props.BoolProperty( #Checkbox
        name = 'Debug Mode',
        description = 'Will display extra info in the System Console',
        default = False
    )

    @classmethod
    def poll(self, context): #Check if selected object is a parent and is empty, otherwise export option is greyed out
        sel_obj = context.selected_objects
        if len(sel_obj) == 1:
            return (sel_obj[0].data is None) and isinstance(sel_obj[0], bpy.types.Object) and sel_obj[0].children
        return False

    def execute(self, context):
        obj = context.selected_objects[0] #Selected object, should only be Scene Root
        export_info = { #Array of empty nodes
            'nodes' : {}
        }
        obj_models = get_nodes_by_empty(obj, export_info['nodes']) #Select entire hierarchy

        if len(obj_models): #If meshes even exist
            bb_min = Vector((10000.0, 10000.0, 10000.0)) #Bounding box min
            bb_max = Vector((-10000.0, -10000.0, -10000.0)) #Bounding box max

            export_info['exporter_version'] = '%s.%s.%s' % bl_info['version'] #For .temp_model, save version of blender primitives exporter
            
            for obj_model in obj_models:
                if not obj_model.data.uv_layers: #If model does not have a uv layer
                    self.report({'ERROR'}, 'mesh.uv_layers is None')
                    if self.debug_mode:
                        print('[Export Error] mesh.uv_layers is None')
                    return {'CANCELLED'}

                if not len(obj_model.data.materials): #If model does not have a material
                    self.report({'ERROR'}, 'mesh.materials is None')
                    if self.debug_mode: 
                        print('[Export Error] mesh.materials is None')
                    return {'CANCELLED'}
                #Get min and max bounding box
                bb_min.x = min(obj_model.location.x + obj_model.bound_box[0][0], bb_min.x)
                bb_min.z = min(obj_model.location.y + obj_model.bound_box[0][1], bb_min.z)
                bb_min.y = min(obj_model.location.z + obj_model.bound_box[0][2], bb_min.y)

                bb_max.x = max(obj_model.location.x + obj_model.bound_box[6][0], bb_max.x)
                bb_max.z = max(obj_model.location.y + obj_model.bound_box[6][1], bb_max.z)
                bb_max.y = max(obj_model.location.z + obj_model.bound_box[6][2], bb_max.y)
            #Save bounding box dimensions
            export_info['bb_min'] = bb_min.to_tuple()
            export_info['bb_max'] = bb_max.to_tuple()
                
            from .export_bw_primitives import BigWorldModelExporter
                
            try:
                bw_exporter = BigWorldModelExporter()
                bw_exporter.export(obj_models, self.filepath, export_info, self.debug_mode)
            except:
                self.report({'ERROR'}, 'Error in import %s!' % os.path.basename(self.filepath))
                import traceback
                traceback.print_exc()
                return {'CANCELLED'}
        print('='*48) #Divider
        print('[Export Info] Export %s' % os.path.basename(self.filepath)) #Filename info
        return {'FINISHED'}
 
    def draw(self, context): #Modify export window
        layout = self.layout
        layout.prop(self, 'debug_mode')
