''' SkepticalFox 2015-2018 '''
''' + ShadowyBandit 2020 '''

#####################################################################
# Addon Description

bl_info = {
    'name': 'BigWorld Model (.primitives)',
    'author': 'SkepticalFox+ShadowyBandit',
    'version': (0, 0, 17),
    'blender': (2, 80, 0),
    'location': 'File > Import-Export',
    'description': 'World of Warships BigWorld Model Import/Export plugin',
    'warning': 'Test version',
    'wiki_url': 'http://www.koreanrandom.com/forum/topic/28240-/',
    'category': 'Import-Export',
}

#####################################################################
# Imports and Registration

import os
import bpy
from mathutils import Vector
from bpy_extras.io_utils import ImportHelper, ExportHelper

from .common import *
from .import_bw_primitives import BigWorldModelLoader

if __name__ == '__main__':
    register()
        
def register():
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import) #Importbar add option
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export) #Exportbar add option
    bpy.utils.register_class(Import_From_ModelFile)
    bpy.utils.register_class(Export_ModelFile)
    bpy.types.Material.BigWorld_mfm_Path = bpy.props.StringProperty( #saves mfm path data, which contains extra rendering info
        name = 'mfm',
        default = '',
        description = '.mfm file path'
    )
    bpy.types.Material.Vertex_Format = bpy.props.StringProperty( #Save vertex type for export
        name = 'Format',
        default = '',
        description = 'Save vertex type for export'
    )
    bpy.utils.register_class(BigWorld_Material_Panel)

def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import) #Importbar remove option
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export) #Exportbar remove option
    bpy.utils.unregister_class(BigWorld_Material_Panel)
    bpy.utils.unregister_class(Import_From_ModelFile)
    bpy.utils.unregister_class(Export_ModelFile)

#####################################################################
# Menu operators

def menu_func_import(self, context):
    self.layout.operator('import.model', text = 'World of Warships BigWorld Model (.primitives+.visual)')

def menu_func_export(self, context):
    self.layout.operator('export.model', text='World of Warships BigWorld Model (.primitives)')

#####################################################################
# BigWorld Material Panel

class BigWorld_Material_Panel(bpy.types.Panel):
    bl_label = 'BigWorld Material'
    bl_idname = 'MATERIAL_PT_bigworld_material'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_options = {'DEFAULT_CLOSED'}
    bl_context = 'material'

    def draw(self, context):
        layout = self.layout
        mat = context.material
        layout.prop(mat, 'BigWorld_mfm_Path')
        layout.prop(mat, 'Vertex_Format')

#####################################################################
# Import

class Import_From_ModelFile(bpy.types.Operator, ImportHelper):
    bl_idname = 'import.model'
    bl_label = 'Import File'
    bl_description = 'Import Ship Model'
    bl_options = {'UNDO'}

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

    def execute(self, context): #Main method
        print('='*48) #Divider
        print('[Import Info] Import %s' % os.path.basename(self.filepath)) #Filename info
        try:
            bw_model = BigWorldModelLoader()
            bw_model.load_from_file(self.filepath, self.import_empty, self.debug_mode) #Convert the file
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

#####################################################################
# Empty Axes from Blender

def get_nodes_by_empty(obj, export_info, is_root=True):
    if is_root:
        node_name = 'Scene Root'
    else:
        node_name = os.path.splitext(obj.name)[0]
    export_info[node_name] = {
        'loc': obj.location.xzy.to_tuple(),
        'scale': obj.scale.xzy.to_tuple(),
        'children': {}
    }
    obj_models = []
    for child in obj.children:
        if (child.data is None) and isinstance(child, bpy.types.Object):
            get_nodes_by_empty(child, export_info[node_name]['children'], False)
        elif isinstance(child.data, bpy.types.Mesh):
            obj_models.append(child)
    return obj_models

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

    object_type : bpy.props.EnumProperty( #Dropdown
        name = 'Object type',
        description = '',
        items = (
            ('0', 'Main Armament','Gun Turrets'),
            ('1', 'Hull','Hull, Torpedo Tubes, and AA Guns')
        )
    )

    @classmethod
    def poll(self, context): #Check if selected object is a parent and is empty, otherwise export option is greyed out
        sel_obj = context.selected_objects
        if len(sel_obj) == 1:
            return (sel_obj[0].data is None) and isinstance(sel_obj[0], bpy.types.Object) and sel_obj[0].children
        return False

    def get_export_object(self, obj_models): #Gathers all selected objects
        bpy.ops.object.select_all(action='DESELECT')
        tmp_ctx = bpy.context.copy()
        obs = []
        for obj_model in obj_models:
            new_obj = obj_model.copy()
            new_obj.data = new_obj.data.copy()
            bpy.context.scene.objects.link(new_obj)
            obs.append(new_obj)
        tmp_ctx['selected_objects'] = obs
        tmp_ctx['active_object'] = tmp_ctx['selected_objects'][0]
        if len(tmp_ctx['selected_objects']) > 1:
            tmp_ctx['selected_editable_bases'] = [bpy.context.scene.object_bases[ob.name] for ob in obs]
            bpy.ops.object.join(tmp_ctx)
        return tmp_ctx['selected_objects'][0]

    def execute(self, context):
        obj = context.selected_objects[0]
        export_info = {
            'nodes' : {}
        }
        obj_models = get_nodes_by_empty(obj, export_info['nodes'])

        if len(obj_models):
            bb_min = Vector((10000.0, 10000.0, 10000.0))
            bb_max = Vector((-10000.0, -10000.0, -10000.0))

            export_info['exporter_version'] = '%s.%s.%s' % bl_info['version']
            
            if self.object_type == '0':
                for obj_model in obj_models:
                    if not obj_model.data.uv_layers:
                        self.report({'ERROR'}, 'mesh.uv_layers is None')
                        return {'CANCELLED'}

                    if not len(obj_model.data.materials):
                        # TODO:
                        # identifier = empty
                        # mfm = materials/template_mfms/lightonly.mfm
                        self.report({'ERROR'}, 'mesh.materials is None')
                        return {'CANCELLED'}

                    bb_min.x = min(obj_model.location.x + obj_model.bound_box[0][0], bb_min.x)
                    bb_min.z = min(obj_model.location.y + obj_model.bound_box[0][1], bb_min.z)
                    bb_min.y = min(obj_model.location.z + obj_model.bound_box[0][2], bb_min.y)

                    bb_max.x = max(obj_model.location.x + obj_model.bound_box[6][0], bb_max.x)
                    bb_max.z = max(obj_model.location.y + obj_model.bound_box[6][1], bb_max.z)
                    bb_max.y = max(obj_model.location.z + obj_model.bound_box[6][2], bb_max.y)

                from .export_bw_main import BigWorldModelExporter

                export_info['bb_min'] = bb_min.to_tuple()
                export_info['bb_max'] = bb_max.to_tuple()
                
                try:
                    bw_exporter = BigWorldModelExporter()
                    bw_exporter.export(obj_models, self.filepath, export_info)
                except UnboundLocalError:
                    self.report({'WARNING'}, '[Error] Wrong object type. Please export as a hull type.')
                    return {'CANCELLED'}

            elif self.object_type == '1':
                for obj_model in obj_models:
                    if not obj_model.data.uv_layers:
                        self.report({'ERROR'}, 'mesh.uv_layers is None')
                        #print('[Export Error] mesh.uv_layers is None')
                        return {'CANCELLED'}

                    if not len(obj_model.data.materials):
                        # TODO:
                        # identifier = empty
                        # mfm = materials/template_mfms/lightonly.mfm
                        self.report({'ERROR'}, 'mesh.materials is None')
                        #print('[Export Error] mesh.materials is None')
                        return {'CANCELLED'}

                    bb_min.x = min(obj_model.location.x + obj_model.bound_box[0][0], bb_min.x)
                    bb_min.z = min(obj_model.location.y + obj_model.bound_box[0][1], bb_min.z)
                    bb_min.y = min(obj_model.location.z + obj_model.bound_box[0][2], bb_min.y)

                    bb_max.x = max(obj_model.location.x + obj_model.bound_box[6][0], bb_max.x)
                    bb_max.z = max(obj_model.location.y + obj_model.bound_box[6][1], bb_max.z)
                    bb_max.y = max(obj_model.location.z + obj_model.bound_box[6][2], bb_max.y)

                from .export_bw_hull import BigWorldModelExporter

                export_info['bb_min'] = bb_min.to_tuple()
                export_info['bb_max'] = bb_max.to_tuple()

                bw_exporter = BigWorldModelExporter()
                bw_exporter.export(obj_models, self.filepath, export_info)
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'object_type')
