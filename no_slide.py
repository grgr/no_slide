# Blender AddOn NoSlide (c) 2015 grgr
# 
# This Addon integrates into the NLA-editor.
# Its purpose is to prevent e.g. sliding feet.
# The user does not need to set location or rotation keyframes
# for an object which should move.
# Distances are calculated according to the action an object 
# is acting on in a NLA-Strip.
#
# Therefore the addon calculates distances between e.g. an objects 
# foot and the object center in the (user given) range of frames 
# in which the foot should stay on the ground in the action of a 
# NLA-Strip.
# The object is than moved exactly the calculated distance.
# 
# Each foot, hand or whatever will rest in a position while the 
# object moves is called a rest member. There can be as many 
# members as needed.
#
# A user defined framestep-parameter determines in which framesteps
# the distances are calculated. There will be inserted a location
# (and rotation) keyframe on every framestep.
#
# It is also possible to add rotation on each member. So the object 
# will rotate in its movement with the e.g. foot staying on the ground
# in its position.
#
# Another feature is to give a fixed distance. Like this objects can 
# e.g. jump.

# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####
# <pep8-80 compliant>

bl_info = {
    "name": "NoSlide",
    "author": "grgr",
    "version": (1,0),
    "blender": (2, 7, 1),
    "location": "NLA-Editor",
    "warning": "something is went wrong in NoSlide",
    "description": "Prevent sliding e.g. feet.",
    "wiki_url":"",
    "tracker_url": "",
    "category": "NLA"}

import bpy
from bpy.types import Menu, Panel, Header
from mathutils import Vector, Matrix
import math

class NoSlideAddMemberOperator(bpy.types.Operator):
    """Add NoSlide Member"""  
    bl_idname = "object.no_slide_add_member_operator"  
    bl_label = "Add NoSlide Member"  
    bl_description = "Add NoSlide Member"
    bl_options = {'REGISTER', 'UNDO'} 

    def invoke(self, context, event):
        rig = bpy.context.active_object 
        rig.no_slide.member_collection.add()
        return{'FINISHED'}

class NoSlideDelMemberOperator(bpy.types.Operator):
    """Delete NoSlide Member"""  
    bl_idname = "object.no_slide_del_member_operator"  
    bl_label = "Delete NoSlide Member"  
    bl_description = "Delete NoSlide Member"
    bl_options = {'REGISTER', 'UNDO'} 

    def invoke(self, context, event):
        rig = bpy.context.active_object 
        cnt = len(rig.no_slide.member_collection)
        if cnt > 0:
            rig.no_slide.member_collection.remove(cnt - 1)
        return{'FINISHED'}

class NoSlideDistance:
    def __init__(self, frame, distance, rotation):
        self.frame    = frame
        self.distance = distance 
        self.rotation = rotation

    def print(self):
        print("frame: " + str(self.frame) + ", distance: " + str(self.distance) + ", rotation: " + str(self.rotation))

class NoSlideMember(bpy.types.PropertyGroup):
    # properties which will be set through user-input:
    name               = bpy.props.StringProperty()
    vertex_group       = bpy.props.StringProperty()
    first_rest_frame   = bpy.props.IntProperty()
    last_rest_frame    = bpy.props.IntProperty()
    fixed_dist         = bpy.props.BoolProperty()
    #dist_vector        = bpy.props.FloatVectorProperty()
    dist_x             = bpy.props.FloatProperty()
    dist_y             = bpy.props.FloatProperty()
    dist_z             = bpy.props.FloatProperty()
    rot_x              = bpy.props.FloatProperty()
    rot_y              = bpy.props.FloatProperty()
    rot_z              = bpy.props.FloatProperty()
    interpolation_type = bpy.props.EnumProperty(
        name="Interpolation", 
        default = "BEZIER", 
        items = [
            ("CONSTANT", "CONSTANT", ""),
            ("LINEAR", "LINEAR", ""),
            ("BEZIER", "BEZIER", ""),
            ("SINE", "SINE", ""),
            ("QUAD", "QUAD", ""),
            ("CUBIC", "CUBIC", ""),
            ("QUART", "QUART", ""),
            ("QUINT", "QUINT", ""),
            ("EXPO", "EXPO", ""),
            ("CIRC", "CIRC", ""),
            ("BACK", "BACK", ""),
            ("BOUNCE", "BOUNCE", ""),
            ("ELASTIC", "ELASTIC", "")
        ]
    )

    # properties which will be set through instance-methods 
    # (ordinary python self. does not work well inside PropertyGroup):

    vertex_index       = bpy.props.IntProperty()
    rig_name           = bpy.props.StringProperty()

    def rig(self):
        return bpy.data.objects[self.rig_name]

    def rig_child(self):
        return bpy.data.objects[self.rig().no_slide.rig_child]

    def rotation(self):
        return Vector((math.radians(self.rot_x),
                       math.radians(self.rot_y),
                       math.radians(self.rot_z)))

    def setup(self, rig, parent_strip):
        self.rig_name = rig.name
        self.frame_start = parent_strip.frame_start
        self.get_vertex_index()

    def get_frame_steps_count(self):
        return math.ceil((self.last_rest_frame - self.first_rest_frame) /
                         self.rig().no_slide.frame_step)

    def get_stepped_rotation_radians(self):
        frame_steps = self.get_frame_steps_count()
        return self.rotation()/frame_steps

    def calculate_distances(self):
        distances  = []

        distances.append(
            NoSlideDistance(
                self.first_rest_frame, 
                Vector((0,0,0)),
                Vector((0,0,0)),
            )
        )
        distances[0].print()

        if self.fixed_dist:
            distances.append(
                NoSlideDistance(
                    self.last_rest_frame, 
                    Vector((self.dist_x, self.dist_y, self.dist_z)),
                    Vector((math.radians(self.rot_x), math.radians(self.rot_y), math.radians(self.rot_z))) 
                )
            )
        else:
            frame2     = self.first_rest_frame
            frame_step = self.rig().no_slide.frame_step
            rotation1  = Vector((0,0,0))
            rotation2  = self.get_stepped_rotation_radians()
            while frame2 < self.last_rest_frame - frame_step:
                frame1     = frame2
                frame2    += frame_step
                distances.append(
                    NoSlideDistance(
                        frame2, 
                        self.get_distance(frame1, frame2, rotation1, rotation2), 
                        self.get_stepped_rotation_radians()
                    )
                )
          
                rotation1 += self.get_stepped_rotation_radians()
                rotation2 += self.get_stepped_rotation_radians()
                distances[len(distances)-1].print()

            distances.append(
                NoSlideDistance(
                    self.last_rest_frame, 
                    self.get_distance(frame2, self.last_rest_frame, rotation1, rotation2), 
                    self.get_stepped_rotation_radians()
                )
            )
            distances[len(distances)-1].print()

        return distances

    def get_distance(self, frame1, frame2, rotation1, rotation2):
        old_vg_loc = self.get_vertex_position(frame1, rotation1)
        new_vg_loc = self.get_vertex_position(frame2, rotation2)
        print("old_vg_loc = " + str(old_vg_loc))
        print("new_vg_loc = " + str(new_vg_loc))
        return old_vg_loc - new_vg_loc

    def get_vertex_position(self, frame, rotation):
        self.apply_animation_and_rotate(frame, rotation)
        position = self.calculate_vertex_position_in_matrix_world()
        return position

    def apply_animation_and_rotate(self, frame, rotation):
        bpy.context.scene.frame_set(self.frame_start + frame)
        self.rig().rotation_mode = "XYZ"
        self.rig().rotation_euler = rotation
        bpy.context.scene.update()

    def calculate_vertex_position_in_matrix_world(self):
        mesh = self.rig_child().to_mesh(scene=bpy.context.scene, apply_modifiers=True, settings='PREVIEW')
        position = self.rig_child().matrix_world * mesh.vertices[self.vertex_index].co
        bpy.data.meshes.remove(mesh)
        return position

    def get_vertex_index(self):
        group_index = self.rig_child().vertex_groups[self.vertex_group].index
        for vertex in self.rig_child().data.vertices:
            for group in vertex.groups:
                if group.group == group_index:
                    self.vertex_index = vertex.index

class NoSlide:
    def __init__(self, rig, parent_strip):
        self.rig = rig
        self.parent_strip = parent_strip
        # get position and rotation on strip start:
        bpy.context.scene.frame_set(parent_strip.frame_start)
        self.rig_rotation = Vector(rig.rotation_euler)
        self.rig_location = Vector(rig.location.xyz)
        self.calculate_distances_for_members()
        self.distance_rotation = self.get_rotation_matrix(self.rig_rotation)
        self.create_no_slide_action()

    def calculate_distances_for_members(self):
        self.member_distances = {}
        for member in self.rig.no_slide.member_collection:
            member.setup(self.rig, self.parent_strip)
            self.member_distances[member.name] = member.calculate_distances()

    def print_member_distances(self):
        for member,distances in self.member_distances.items():
            for distance in distances:
                distance.print()

    def create_no_slide_action(self):
        self.rig.animation_data.action = bpy.data.actions.new(name="NoSlide " + self.parent_strip.action.name)

    def insert_keyframes(self):
        for repeat in range(0, int(round(self.parent_strip.repeat))):
            start_frame = self.parent_strip.frame_start + repeat * (self.parent_strip.action_frame_end - 1) - 1
            self.insert_keyframes_per_member_and_update_distance_rotation(start_frame)

    def insert_keyframes_per_member_and_update_distance_rotation(self, start_frame):
        for member in self.rig.no_slide.member_collection:
            for entry in self.member_distances[member.name]:

                frame = start_frame + entry.frame
                self.rig_location += self.distance_rotation * entry.distance 
                self.rig_rotation += entry.rotation

                self.insert_keyframes_per_frame_step(member, frame)

            self.update_distance_rotation()

    def update_distance_rotation(self):
        self.distance_rotation = self.get_rotation_matrix(self.rig_rotation)

    def get_rotation_matrix(self, rotation):
        rot_x = Matrix.Rotation(rotation.x, 3, 'X')
        rot_y = Matrix.Rotation(rotation.y, 3, 'Y')
        rot_z = Matrix.Rotation(rotation.z, 3, 'Z')
        rot_all = rot_x * rot_y * rot_z
        return rot_all

    def insert_keyframes_per_frame_step(self, member, frame):
        self.insert_keyframe_points('location', self.rig_location, frame, member.interpolation_type)
        self.insert_keyframe_points('rotation_euler', self.rig_rotation, frame, member.interpolation_type)

    def insert_keyframe_points(self, data_path, values, frame, interpolation_type):
        for index in range(len(values)):
            self.insert_keyframe_point(data_path, index, values, frame, interpolation_type)

    def insert_keyframe_point(self, data_path, index, values, frame, interpolation_type):
        fcurve = self.find_or_create_fcurve(data_path, index)
        keyframe = fcurve.keyframe_points.insert(frame = frame, value = values[index])
        keyframe.interpolation = interpolation_type

    def find_or_create_fcurve(self, data_path, index):
        for fcurve in self.rig.animation_data.action.fcurves:
            if fcurve.data_path == data_path and fcurve.array_index == index:
                return fcurve
        return self.rig.animation_data.action.fcurves.new(data_path, index = index)

    def action_to_strip(self):
        bpy.ops.nla.action_pushdown(channel_index=1)

        strip = self.rig.animation_data.nla_tracks.active.strips[0]

        strip.blend_in      = self.parent_strip.blend_in
        strip.blend_out     = self.parent_strip.blend_out
        strip.blend_type    = self.parent_strip.blend_type
        strip.extrapolation = self.parent_strip.extrapolation
        strip.influence     = self.parent_strip.influence

class NoSlidePanel(bpy.types.Panel):
    bl_space_type = 'NLA_EDITOR'
    bl_region_type = 'UI'
    bl_label = 'NoSlide'

    def draw(self, context):
        rig = bpy.context.active_object 
        if rig.type == "ARMATURE" and len(rig.children) > 0:
            layout = self.layout

            row = layout.row()
            row.label(text="Selected Rig: " + rig.name)

            if rig.animation_data.nla_tracks.active != None:
                row = layout.row()
                row.label(text="Selected NLA Track: " + rig.animation_data.nla_tracks.active.name)

            row = layout.row()
            # TODO: allow only rig children in the selection! (replace bpy.context.scene)
            row.prop_search(rig.no_slide, "rig_child", bpy.data, "objects", text="Rig Child with resting Vertex Group") 

            if rig.animation_data.nla_tracks.active != None:
                row = layout.row()
                row.prop_search(rig.no_slide, "parent_strip", rig.animation_data.nla_tracks.active, "strips", text="Strip") 

            row = layout.row()
            row.prop(rig.no_slide, "frame_step", text="Frame Step") 

            if rig.no_slide.rig_child != "" and bpy.data.objects[rig.no_slide.rig_child]:
                row = layout.row()
                col= row.column(align=True)
                for member in rig.no_slide.member_collection:
                    crow = col.row()
                    box = crow.box()
                    box.label("Member: " + member.name)
                    mrow = box.row()
                    mrow.prop(member, "name")

                    mrow = box.row()
                    mrow.prop(member, "fixed_dist", text = "Use Fixed Distance Vector (Frame Steps do not apply)")

                    if member.fixed_dist:
                        mrow = box.row()
                        mrow.label("Distance::")
                        mrow = box.row()
                        mrow.prop(member, "dist_x", text = "X")
                        mrow.prop(member, "dist_y", text = "Y")
                        mrow.prop(member, "dist_z", text = "Z")
                        #mrow = box.row()
                        #mrow.prop(member, "dist_vector", text = "dist")
                    else:
                        mrow = box.row()
                        mrow.prop_search(member, "vertex_group", bpy.data.objects[rig.no_slide.rig_child], "vertex_groups", text="Resting Vertex Group")

                    mrow = box.row()
                    mrow.label("Rotation:")
                    mrow = box.row()
                    mrow.prop(member, "rot_x", text = "X")
                    mrow.prop(member, "rot_y", text = "Y")
                    mrow.prop(member, "rot_z", text = "Z")

                    mrow = box.row()
                    mrow.label(text="Rest Frames:") 
                    mrow.prop(member, "first_rest_frame") 
                    mrow.prop(member, "last_rest_frame") 

                    mrow = box.row()
                    mrow.prop(member, "interpolation_type")

                    box.separator()

                col= row.column(align=True)
                col.operator("object.no_slide_add_member_operator", text="", icon="ZOOMIN")
                col.operator("object.no_slide_del_member_operator", text="", icon="ZOOMOUT")

            row = layout.row()
            row.operator("object.no_slide_operator")

class NoSlideOperator(bpy.types.Operator):
    """NoSlide Operator"""  
    bl_idname = "object.no_slide_operator"  
    bl_label = "Calculate Distance and Rotation"  
    bl_options = {'REGISTER', 'UNDO'} 

    @classmethod
    def poll(cls, context):
        rig = bpy.context.scene.objects.active
        return rig.no_slide.parent_strip is not ''

    def execute(self, context):
        rig = bpy.context.scene.objects.active
        no_slide_parent_strip = rig.animation_data.nla_tracks.active.strips[rig.no_slide.parent_strip]

        newtrack = "NoSlide " + rig.animation_data.nla_tracks.active.name
        if newtrack in rig.animation_data.nla_tracks:
            no_slide_nla_track = rig.animation_data.nla_tracks[newtrack]
        else:
            no_slide_nla_track = rig.animation_data.nla_tracks.new()
            no_slide_nla_track.name = newtrack  

        no_slide = NoSlide(rig, no_slide_parent_strip)
        #no_slide.print_member_distances()
        no_slide.insert_keyframes()
        no_slide.action_to_strip()
        
        self.report({'INFO'}, "NoSlide executed")
        return {'FINISHED'} 

class NoSlideProperties(bpy.types.PropertyGroup):
    rig_child          = bpy.props.StringProperty()
    parent_strip       = bpy.props.StringProperty()
    interpolation      = bpy.props.StringProperty()
    frame_step         = bpy.props.IntProperty(min=1)
    member_collection  = bpy.props.CollectionProperty(type=NoSlideMember)

def register():
    bpy.utils.register_module(__name__)
    bpy.types.Object.no_slide = bpy.props.PointerProperty(type=NoSlideProperties)
    bpy.types.Object.member_collection  = bpy.props.CollectionProperty(type=NoSlideMember)

def unregister():
    bpy.utils.unregister_module(__name__)
    del bpy.types.Object.no_slide
    del bpy.types.Object.member_collection

if __name__ == "__main__":
    register()

