# UE4 Export Tools for Blender
A script for Blender to assist with exporting objects and scenes to Unreal Engine 4.

## Installation
1. Download the script from GitHub by clicking [here](https://github.com/andyp123/blender_ue4_export_tools/archive/master.zip).
2. Open the downloaded .zip and extract the file 'ue4_export_tools.py' to a temporary place on your computer.
3. In Blender, open the User Preferences (ctrl+alt+p) and switch to the Add-ons tab.
4. Select 'Install Add-on from file...' and select the 'ue4_export_tools.py' file you extracted from the .zip.
5. Enable the add-on by searching for it (enter 'ue4' to quickly find it).
6. Save the user settings if you would like the script to always be enabled.

## Usage
This script is designed to make it easier to work with multiple objects in a Blender file and batch export them to different files that can be imported into Unreal. There is also a function to export the entire scene to be used with the 'File > Import Into Level...' importer in UE4. In addition to the export functions, there are tools to make it easier to quickly create and work with colliders that can be used in UE4.

#### Collider Naming Notes
UE4 handles several types of custom collider that can be included in the .fbx file of static meshes. The desired type of collider can be set by specifying a prefix in the collider object name, but UE4 Export Tools will automatically generate collier names so the user doesn't have to worry. For reference, the prefixes supported are listed below. More information about setting up colliders for static meshes can be found [here](https://docs.unrealengine.com/latest/INT/Engine/Content/FBX/StaticMeshes/).
+ __`UCX_` Convex Collider__ - Generic convex collider that can be automatically generated.
+ __`UBX_` Box Collider__ - Box collider (not generated)
+ __`USP_` Sphere Collider__ - Sphere Collider (not generated)
+ __`UCP_` Capsule Collider__ - Capsule Collider (not generated)
+ __`NC_` No Collider__ - No collider will be generated for objects with this prefix.
For collider types that are not generated, UE4 Export Tools will still detect them if they are manually created and named correctly.

#### Collider Layer
To better organizing the scene, this add-on puts colliders it generates or organizes into a designated layer. Currently this layer is set to layer _11_. If need be, it can be changed by modifying the ue4_export_tools.py file before installation and changing the number on the line that reads `collider_layer = _10_` to whatever you would like (0-19). I plan to make this easier in the future by adding the option directly in the add-on.

### Fix Data Names
This is a simple tool that will rename the data of any object to have the same name as the object itself. The reason for this is that when using the full scene importer in UE4, mesh data names are used instead of object names, which can be problematic.

_Options : _
+ __Only Selected__ (off) - Restrict the function to only selected objects instead of operating on the entire scene.

### UE4 / Blender Scale
Quickly scale the entire scene from Blender's default scene units where 1 Blender unit = 1m to that of UE4, where 100 Blender units = 1m and vice versa.

_Options : _
+ __Scale Objects__ (on) - Scale the objects in the scene. If disabled, only the scene units will be changed.

### Generate Colliders
Without colliders, there will be no collision on objects imported in Unreal, or Unreal will generate extremely poorly fitting colliders automatically, neither of which is desired. This function will create a copy of any selected object and then run Blender's built-in convex hull function on it to create a collider that can be used in UE4. The collider will automatically be named correctly after the object using the 'UCX_' prefix system.

_Options : _
+ __Use Object Copy__ (off) - Instead of generating a collider with the convex hull tool, a copy of the original object will be used. This is a little faster on large scenes where you need lots of colliders to be generated.
+ __Replace Existing__ (off) - If an object already has any colliders, they will be deleted and new colliders generated. Currently, this ignores objects with multiple colliders, which are usually made manually.

### Convert to Colliders
Not quite the same as the Generate Colliders function. Instead of creating colliders for all the selected objects, Convert to Colliders turns all the selected objects into colliders of the active (usually last selected) object. Selected objects will all be renamed to match the active object.

_Options : _
+ __Use Object Copy__ (off) - Instead of generating a collider with the convex hull tool, a copy of the original object will be used.
+ __Delete Converted__ (on) - Delete the original selected objects leaving only the active object and the created colliders.
+ __Copy Active Transform__ (on) - Copy the active object's transform to the selected objects so the active object and colliders are all in the same position.

### Select Colliders
Selects the colliders belonging to the selected object(s).

_Options : _
+ __Only Colliders__ (off) - Deselect everything except colliders belonging to the original selected object(s).

### Organise Colliders
Moves any objects with valid collider names to the collider layer and sets their render type to wireframe.

_Options : _
+ __Only Selected__ (off) - Restrict the function to only selected objects instead of operating on the entire scene.

### Export Object(s)
The Export Objects option will export all the selected objects and corresponding colliders (regardless of whether or not they are selected or hidden). Exported objects will automatically be centered to the origin and exported to individual .fbx files with the same name as the object, containing the object and its colliders.

### Export Scene
The Export Scene option is designed to be used with UE4's 'Import Into Level...', and will export everything in the scene to an .fbx file with the expection of objects hidden, or hidden from selection. Due to differences in the way that Unreal handles objects imported this way, the scene should be scaled by 100 and units should be set to Metric and scale to 0.01.

### Output
The output option allows selection of the default export folder to increase productivity by making it easieir to get to the desired output location in the file browser.
