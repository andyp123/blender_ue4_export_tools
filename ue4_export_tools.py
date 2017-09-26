#  ***** GPL LICENSE BLOCK *****
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#  All rights reserved.
#  ***** GPL LICENSE BLOCK *****

# TODO:
# + export scene (get this to actually work...)
#  - export all selected objects as one scene
#  - ask before overwrite option


# WISHLIST TODO:
# + set collider solid color
# + add UI for collider_layer (0-19)
# + add UI for collider_draw_type ('WIRE'/'SOLID')
# + UI: move certain options out from functions to general addon options:
#  - scale objects
#  - simple copy for colliders
#  - triangulate meshes
#  - user selectable collider_layer
# + remove support for *generating* colliders without a postfix number to simplify code and reduce possible errors?
# + add support for LODs
# + improve the way the files are exported (don't keep asking for the export folder)
# + export groups with different settings (see Andreas Esau's Godot exporter, which is awesome)
# + when adding colliders, more rigorously check the generated name does not collide with that of an existing object
# + look at other addons and figure out how to improve code
# + is it worth copying everything to a new layer for export if destructive options are used (triangulate etc.)?


import bpy, bmesh, os
from bpy.props import *
from mathutils import Vector


bl_info = {
  "name": "UE4 Export Tools",
  "author": "Andrew Palmer",
  "version": (0, 0, 1),
  "blender": (2, 78, 0),
  "location": "View3D > Tools > UE4",
  "description": "Tools to assist with a Blender to Unreal Engine 4 workflow.",
  "category": "Object"
}




##### GLOBAL CONSTANTS #####
collider_prefixes = ['UCX_', 'UBX_', 'USP_', 'UCP_']
non_collider_prefix = 'NC_'
collider_layer = 10
collider_draw_type = 'WIRE'




##### HELPER FUNCTIONS #####
def draw_split(layout, property_group, property_id, label, lcol_percentage=0.5):
  row = layout.row()
  split = row.split(percentage=lcol_percentage)
  col = split.column()
  col.label(label)
  split = split.split()
  col = split.column()
  col.prop(property_group, property_id, text="")

def move_to_layer(ob, layer_id):
  # needs to be on a layer first
  ob.layers[layer_id] = True

  # make sure only on single layer
  for i in range(20):
    ob.layers[i] = (i == layer_id)

# check to see if the object is a collider
def is_collider_name(name):
  for prefix in collider_prefixes:
    if name.startswith(prefix):
      return True
    return False

# check to see if an object has a collider
def has_collider(name):
  objs = bpy.data.objects
  for prefix in collider_prefixes:
    collider_name = prefix + name
    if objs.get(collider_name) is not None:
      return True
    if objs.get(collider_name + '_01') is not None:
      return True
  return False

def is_non_collider(name):
  return name.startswith(non_collider_prefix)

# get all valid colliders for the named object (based only on name)
def get_colliders(name):
  colliders = []
  objs = bpy.data.objects
  for prefix in collider_prefixes:
    collider_name = prefix + name
    collider_obj = objs.get(collider_name)
    if collider_obj is not None:
      colliders.append(collider_obj)
    else:
      num_colliders = 1
      while num_colliders < 100:
        collider_name = prefix + name + '_' + str(num_colliders).zfill(2)
        collider_obj = objs.get(collider_name)
        if collider_obj is not None:
          colliders.append(collider_obj)
          num_colliders += 1
        else:
          # whilst there *could* be a gap in the collider names, give up searching to avoid time wasting
          # could implement a simple if misses > max_misses: break style conditional here to catch some gaps
          break
  return colliders

def select_objects(objects, deselect_others=False):
  if deselect_others:
    bpy.ops.object.select_all(action='DESELECT')
  for ob in objects:
    ob.select = True

def get_path(base, filename):
  return bpy.path.abspath(base + filename)

def path_exists(path):
  return os.path.exists(bpy.path.abspath(path))

def make_collider(scn, ob, collider_name, use_object_copy=False):
  collider = ob.copy()
  collider.name = collider_name
  collider.data = ob.data.copy()
  collider.data.name = collider_name
  collider.data.materials.clear()
  collider.matrix_world = ob.matrix_world.copy()
  collider.draw_type = collider_draw_type

  # link colliders to scene
  scn.objects.link(collider)
  move_to_layer(collider, collider_layer)

  # generate convex hull using built-in function (requires edit mode with vertex selection)
  if not use_object_copy:
    collider.select = True
    scn.objects.active = collider
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(collider.data)
    for f in bm.faces: # for some reason, only selecting verts doesn't work correctly
      f.select = True
    for v in bm.verts:
      v.select = True
    bpy.ops.mesh.convex_hull(delete_unused = True)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.shade_flat()
    collider.select = False

  return collider

def scale_scene_objects(scn, scale_factor):
  selected_objects = list(ob for ob in scn.objects if ob.select)
  hidden_objects = list(ob for ob in scn.objects if ob.hide)
  visible_layers = scn.layers[:] # copy visible layers

  scn.layers = [True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True]

  for ob in scn.objects:
    ob.scale *= scale_factor
    ob.location *= scale_factor
    ob.select = True

  # apply scale to selected objects
  bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

  scn.layers = visible_layers
  select_objects(objects=selected_objects, deselect_others=True)
  for ob in hidden_objects:
    ob.hide = True

def approx_equal(a, b, tol=0.0001):
     return abs(a - b) < tol

# returns an array containing 
def get_collider_name(base_name, num=0):
  if num > 0:
    objs = bpy.data.objects
    while True:
      valid_name = 'UCX_{0}_{1}'.format(base_name, str(num).zfill(2))
      if objs.get(valid_name) is None:
        return (valid_name, num)
      num += 1
  else:
    return ('UCX_' + base_name, 0)


##### EXPOSED OPERATORS #####
class AWP_UE4ExportTools_FixObjectDataNames(bpy.types.Operator):
  """Rename data of selected objects to be the same as the object."""
  bl_idname = 'awp_ue4.fix_object_data_names'
  bl_label = 'UE4 Fix Object Data Names'
  bl_options = {'REGISTER', 'UNDO'}

  only_selected = bpy.props.BoolProperty(
    name = "only selected",
    default = False,
    description = "Only operate on selected objects."
    )

  def execute(self, context):
    scn = context.scene

    objects = None
    if self.only_selected:
      objects = (ob for ob in scn.objects if ob.type == 'MESH' and ob.select)
    else:
      objects = (ob for ob in scn.objects if ob.type == 'MESH')

    for ob in objects:
      ob.data.name = ob.name

    return {'FINISHED'}


class AWP_UE4ExportTools_OrganizeColliders(bpy.types.Operator):
  """Move existing colliders to the collider layer and set render mode to wire."""
  bl_idname = 'awp_ue4.organize_colliders'
  bl_label = 'UE4 Organize Colliders'
  bl_options = {'REGISTER', 'UNDO'}

  only_selected = bpy.props.BoolProperty(
    name = "only selected",
    default = False,
    description = "Only operate on selected objects."
    )

  def execute(self, context):
    scn = context.scene

    colliders = None
    if self.only_selected:
      colliders = (ob for ob in scn.objects if ob.select and is_collider_name(ob.name))
    else:
      colliders = (ob for ob in scn.objects if is_collider_name(ob.name))

    for ob in colliders:
      ob.data.name = ob.name
      ob.draw_type = collider_draw_type
      move_to_layer(ob, collider_layer)

    return {'FINISHED'}


class AWP_UE4ExportTools_SelectColliders(bpy.types.Operator):
  """Select the colliders of all the selected objects."""
  bl_idname = 'awp_ue4.select_colliders'
  bl_label = 'UE4 Select Colliders'
  bl_options = {'REGISTER', 'UNDO'}

  only_colliders = bpy.props.BoolProperty(
    name = "only colliders",
    default = False,
    description = "Select only the colliders and deselect non-colliders."
    )

  def execute(self, context):
    scn = context.scene

    # Make sure collider layer is visible
    scn.layers[collider_layer] = True

    selected_objects = (ob for ob in scn.objects if ob.select == True)
    colliders = []
   
    for ob in selected_objects:
      ob_name = ob.name
      if not is_non_collider(ob_name) and not is_collider_name(ob_name):
        colliders.extend(get_colliders(ob_name))

    select_objects(objects=colliders, deselect_others=self.only_colliders)

    return {'FINISHED'}


class AWP_UE4ExportTools_GenerateColliders(bpy.types.Operator):
  """Generate convex colliders for selected meshes"""
  bl_idname = 'awp_ue4.generate_colliders'
  bl_label = 'UE4 Generate Colliders'
  bl_options = {'REGISTER', 'UNDO'}

  use_object_copy = bpy.props.BoolProperty(
    name = "use object copy",
    default = False,
    description = "Instead of calculating a convex collider, the created collider is a simple copy of the object. This assumes the original object is already convex."
    )

  replace_existing = bpy.props.BoolProperty(
    name = "replace existing",
    default = False,
    description = "Replace any existing colliders with new ones. Will not replace if multiple colliders exist."
    )

  def execute(self, context):
    scn = context.scene

    # Make sure collider layer is visible
    scn.layers[collider_layer] = True

    colliders = []
    selected_objects = list(ob for ob in scn.objects if ob.type == 'MESH' and ob.select == True)

    objs = bpy.data.objects
    for ob in selected_objects:
      # fix data name
      ob_name = ob.name
      ob.data.name = ob_name
      # skip non-colliders and objects that are colliders
      if is_non_collider(ob_name) or is_collider_name(ob_name):
        continue

      # remove colliders existing for this object
      if self.replace_existing:
        existing_colliders = get_colliders(ob_name)
        num_colliders = len(existing_colliders)
        if num_colliders == 1: # replace single colliders only  
          for col in existing_colliders:
            objs.remove(objs[col.name], True)
        elif num_colliders > 1:
          continue

      # generate colliders for objects that don't already have them
      if not has_collider(ob_name):
        collider_name = get_collider_name(ob.name)
        collider = make_collider(scn, ob, collider_name[0], self.use_object_copy)
        colliders.append(collider)

    if len(colliders) > 0:
      select_objects(objects=colliders, deselect_others=True)
    else:
      select_objects(objects=selected_objects, deselect_others=True)

    message = '{0} new colliders created.'.format(len(colliders))
    self.report({'INFO'}, message)
    return {'FINISHED'}


class AWP_UE4ExportTools_ConvertSelectedToActiveColliders(bpy.types.Operator):
  """Convert the selected objects into colliders for the active object"""
  bl_idname = 'awp_ue4.convert_selected_to_active_colliders'
  bl_label = 'UE4 Convert Selected to Active Colliders'
  bl_options = {'REGISTER', 'UNDO'}

  use_object_copy = bpy.props.BoolProperty(
    name = "use object copy",
    default = False,
    description = "Instead of calculating a convex collider, the created collider is a simple copy of the object. This assumes the original object is already convex."
    )

  delete_converted = bpy.props.BoolProperty(
    name = "delete converted",
    default = True,
    description = "Delete objects from the selection that have been converted into colliders."
    )

  copy_active_transform = bpy.props.BoolProperty(
    name = "copy active transform",
    default = True,
    description = "Colliders will have the same transform as the active object.")

  def execute(self, context):
    scn = context.scene

    active_object = scn.objects.active
    selected_objects = list(ob for ob in scn.objects if ob.type == 'MESH' and ob.select == True and ob != active_object)
    colliders = []

    if active_object == None or len(selected_objects) < 1:
      self.report({'INFO'}, "Need one or more selected objects and an active object.")
      return {'FINISHED'}
    if is_collider_name(active_object.name) or is_non_collider(active_object.name):
      self.report({'INFO'}, "Active object should not be marked for no collision ('NC_' prefix) or a collider itself.")
      return {'FINISHED'}

    scn.layers[collider_layer] = True
    bpy.ops.object.select_all(action='DESELECT')

    # give selected objects temporary names to avoid collisions
    for i, ob in enumerate(selected_objects):
      temp_name = 'ue4tempname_' + str(i)
      ob.name = temp_name
      ob.data.name = temp_name

    # convert all selected objects into colliders for the active object
    num = 0
    if len(selected_objects) > 1:
      num += 1 # a value > 0 will cause make_collider to use the multi-collider naming scheme
    for ob in selected_objects:
      collider_name = get_collider_name(active_object.name, num)
      num = collider_name[1]
      collider = make_collider(scn, ob, collider_name[0], self.use_object_copy)
      colliders.append(collider)
      num += 1

    if self.delete_converted:
      objs = bpy.data.objects
      for ob in selected_objects:
        objs.remove(objs[ob.name], True)

    if self.copy_active_transform:
      # store current cursor position and snap it to the active object
      cursor_position = scn.cursor_location.copy()
      active_object.select = True
      bpy.ops.view3d.snap_cursor_to_selected()

      # set the origin of all the colliders to be that of the active object (at cursor)
      select_objects(colliders, True)
      bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

      # restore cursor position
      scn.cursor_location = cursor_position
    else:
      select_objects(colliders, True) # make sure the colliders are selected)

    active_object.select = True
    scn.objects.active = active_object

    return {'FINISHED'}


class AWP_UE4ExportTools_ExportObjects(bpy.types.Operator):
  """Export selected objects"""
  bl_idname = 'awp_ue4.export_objects'
  bl_label = 'UE4 Export object(s)'
  bl_options = {'REGISTER', 'UNDO'}

  export_path = bpy.props.StringProperty(subtype="FILE_PATH")
  check_existing = bpy.props.BoolProperty()

  def invoke(self, context, event):
    self.export_path = bpy.context.scene.export_settings.path
    self.check_existing = bpy.context.scene.export_settings.check_existing
    
    if path_exists(self.export_path):
      return self.execute(context)
    else:
      context.window_manager.fileselect_add(self)
      return {'RUNNING_MODAL'}
    
  def execute(self, context):
    scn = context.scene

    # enable colliders layer so we can find colliders
    collider_layer_visible = scn.layers[collider_layer]
    scn.layers[collider_layer] = True

    selected_objects = list(ob for ob in scn.objects if ob.select and not is_collider_name(ob.name))

    for ob in selected_objects:
      bpy.ops.object.select_all(action='DESELECT')

      ob.select = True
      object_location = ob.location.copy()
      ob.location = Vector((0.0, 0.0, 0.0))
      
      # select and move colliders and lods
      colliders = get_colliders(ob.name)
      for collider in colliders:
        collider.select = True
        collider.location -= object_location

      # lods = get_lods(ob.name)
      # for lod in lods:
      #   lod.select = True
      #   lod.location = object_location

      # export fbx using object name
      path = get_path(self.export_path, ob.name + '.fbx')
      bpy.ops.export_scene.fbx(filepath=path, check_existing=self.check_existing, use_selection=True)

      # revert object positions
      ob.location = object_location
      for collider in colliders:
        collider.location += object_location
      # for lod in lods:
      #   lod.location += object_location

    # reset selection and layer visibility
    select_objects(objects=selected_objects, deselect_others=True)
    scn.layers[collider_layer] = collider_layer_visible

    message = 'Exported {0} object(s).'.format(len(selected_objects))
    self.report({'INFO'}, message)
    return {'FINISHED'}


class AWP_UE4ExportTools_ExportScene(bpy.types.Operator):
  """Export entire scene"""
  bl_idname = 'awp_ue4.export_scene'
  bl_label = 'UE4 Export Scene'
  bl_options = {'REGISTER', 'UNDO'}

  # scale_scene = bpy.props.BoolProperty(
  #     name = "scale scene",
  #     default = False,
  #     subtype = 'NONE',
  #     description = "Scale the scene by 100"
  #     )

  export_path = bpy.props.StringProperty(subtype="FILE_PATH")
  check_existing = bpy.props.BoolProperty()

  def invoke(self, context, event):
    self.export_path = bpy.context.scene.export_settings.path
    self.check_existing = bpy.context.scene.export_settings.check_existing
    context.window_manager.fileselect_add(self)
    return {'RUNNING_MODAL'}

  def execute(self, context):
    scn = context.scene

    active_object = scn.objects.active
    selected_objects = list(ob for ob in scn.objects if ob.select)
    collider_layer_visible = scn.layers[collider_layer]

    scn.layers[collider_layer] = True
    bpy.ops.object.select_all(action='SELECT')

    # open fbx export dialogue
    path = get_path(self.export_path, 'scene_export.fbx')
    bpy.ops.export_scene.fbx(filepath=path, check_existing=self.check_existing, use_selection=True)

    # restore selection and layer visibility
    select_objects(objects=selected_objects, deselect_others=True)
    scn.objects.active = active_object
    scn.layers[collider_layer] = collider_layer_visible

    return {'FINISHED'}


class AWP_UE4ExportTools_SetUnrealSceneScale(bpy.types.Operator):
  """Set the scene scale to values that work best with Unreal"""
  bl_idname = 'awp_ue4.set_unreal_scale'
  bl_label = 'UE4 Set Unreal Scene Scale'
  bl_options = {'REGISTER', 'UNDO'}

  scale_objects = bpy.props.BoolProperty(
      name = "scale objects",
      default = True,
      subtype = 'NONE',
      description = "Scale objects in the scene."
      )

  def execute(self, context):
    scn = context.scene

    ignore_scale = (scn.unit_settings.system == 'METRIC' and approx_equal(scn.unit_settings.scale_length, 0.01))

    if not ignore_scale:
      scn.unit_settings.system = 'METRIC'
      scn.unit_settings.scale_length = 0.01

      if self.scale_objects:
        scale_scene_objects(scn, 100.0)

    return {'FINISHED'}


class AWP_UE4ExportTools_SetBlenderSceneScale(bpy.types.Operator):
  """Set the scene scale to default Blender values"""
  bl_idname = 'awp_ue4.set_blender_scale'
  bl_label = 'UE4 Set Blender Scene Scale'
  bl_options = {'REGISTER', 'UNDO'}

  scale_objects = bpy.props.BoolProperty(
      name = "scale objects",
      default = True,
      subtype = 'NONE',
      description = "Scale objects in the scene."
      )

  def execute(self, context):
    scn = context.scene

    ignore_scale = (scn.unit_settings.system == 'NONE' and approx_equal(scn.unit_settings.scale_length, 1.0))

    if not ignore_scale:
      scn.unit_settings.system = 'NONE'
      scn.unit_settings.scale_length = 1.0

      if self.scale_objects:
        scale_scene_objects(scn, 0.01)

    return {'FINISHED'}


# Required by the path selector in the UI
class AWP_ExportSettings(bpy.types.PropertyGroup):
    path = StringProperty(
        name="",
        description="Path to output directory",
        default="",
        maxlen=1024,
        subtype='DIR_PATH')
    check_existing = BoolProperty(
        name="",
        description="Check for existing files",
        default=False)


##### MAIN CLASS, UI AND REGISTRATION #####
class AWP_UE4ExportToolsPanel(bpy.types.Panel):
  """COMMENT"""
  bl_space_type = 'VIEW_3D'
  bl_region_type = 'TOOLS'
  bl_label = 'UE4 Tools'
  bl_category = 'UE4'
  bl_context = 'objectmode'

  # UI
  def draw(self, context):
    layout = self.layout

    col = layout.column(align=True)
    row = col.row(align=True)
    row.label("Misc:")
    row = col.row(align=True)
    row.operator('awp_ue4.fix_object_data_names',"Fix Data Names")

    col = layout.column(align=True)
    row = col.row(align=True)
    row.label("Scale:")
    row = col.row(align=True)
    row.operator('awp_ue4.set_unreal_scale',"UE4")
    row.operator('awp_ue4.set_blender_scale',"Blender")

    col = layout.column(align=True)
    row = col.row(align=True)
    row.label("Colliders:")
    row = col.row(align=True)
    row.operator('awp_ue4.generate_colliders',"Generate Colliders")
    row = col.row(align=True)
    row.operator('awp_ue4.convert_selected_to_active_colliders',"Convert to Colliders")
    row = col.row(align=True)
    row.operator('awp_ue4.select_colliders', "Select Colliders")
    row = col.row(align=True)
    row.operator('awp_ue4.organize_colliders', "Organize Colliders")

    col = layout.column(align=True)
    row = col.row(align=True)
    row.label("Exporting:")
    row = col.row(align=True)
    row.operator('awp_ue4.export_objects', "Export Object(s)")
    row = col.row(align=True)
    row.operator('awp_ue4.export_scene', "Export Scene")

    col = layout.column(align=True)
    row = col.row(align=True)
    col.prop(context.scene.export_settings, 'path', text="Output")
    # not working, so disable for now
    # row = col.row(align=True)
    # col.prop(context.scene.export_settings, 'check_existing', text="Check Existing")


##### OPERATOR REGISTRATION #####
def register():
  bpy.utils.register_class(AWP_UE4ExportToolsPanel)
  bpy.utils.register_class(AWP_UE4ExportTools_FixObjectDataNames)
  bpy.utils.register_class(AWP_UE4ExportTools_GenerateColliders)
  bpy.utils.register_class(AWP_UE4ExportTools_SelectColliders)
  bpy.utils.register_class(AWP_UE4ExportTools_OrganizeColliders)
  bpy.utils.register_class(AWP_UE4ExportTools_ExportObjects)
  bpy.utils.register_class(AWP_UE4ExportTools_ExportScene)
  bpy.utils.register_class(AWP_UE4ExportTools_ConvertSelectedToActiveColliders)
  bpy.utils.register_class(AWP_UE4ExportTools_SetUnrealSceneScale)
  bpy.utils.register_class(AWP_UE4ExportTools_SetBlenderSceneScale)

  bpy.utils.register_class(AWP_ExportSettings)
  bpy.types.Scene.export_settings = PointerProperty(type=AWP_ExportSettings)

def unregister():
  bpy.utils.unregister_class(AWP_UE4ExportToolsPanel)
  bpy.utils.unregister_class(AWP_UE4ExportTools_FixObjectDataNames)
  bpy.utils.unregister_class(AWP_UE4ExportTools_GenerateColliders)
  bpy.utils.unregister_class(AWP_UE4ExportTools_SelectColliders)
  bpy.utils.unregister_class(AWP_UE4ExportTools_OrganizeColliders)
  bpy.utils.unregister_class(AWP_UE4ExportTools_ExportObjects)
  bpy.utils.unregister_class(AWP_UE4ExportTools_ExportScene)
  bpy.utils.unregister_class(AWP_UE4ExportTools_ConvertSelectedToActiveColliders)
  bpy.utils.unregister_class(AWP_UE4ExportTools_SetUnrealSceneScale)
  bpy.utils.unregister_class(AWP_UE4ExportTools_SetBlenderSceneScale)

  bpy.utils.unregister_class(AWP_ExportSettings)
  del bpy.types.Scene.export_settings

# allows running addon from text editor
if __name__ == '__main__':
  register()
