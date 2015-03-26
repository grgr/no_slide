# NoSlide
Blender Addon to prevent e.g. sliding feet

## Description
This Addon integrates into the NLA-editor.
Its purpose is to prevent e.g. sliding feet.
The user does not need to set location or rotation keyframes
for an object which should move.
Distances are calculated according to the action an object 
is acting on in a NLA-Strip.

Therefore the addon calculates distances between e.g. an objects 
foot and the object center in the (user given) range of frames 
in which the foot should stay on the ground in the action of a 
NLA-Strip.
The object is than moved exactly the calculated distance.

Each foot, hand or whatever will rest in a position while the 
object moves is called a rest member. There can be as many 
members as needed.

A user defined framestep-parameter determines in which framesteps
the distances are calculated. There will be inserted a location
(and rotation) keyframe on every framestep.

It is also possible to add rotation on each member. So the object 
will rotate in its movement with the e.g. foot staying on the ground
in its position.

Another feature is to give a fixed distance. Like this objects can 
e.g. jump.


## Installation

* Put the no_slide.py file into your blender addon/scripts directory. 
* In blender click File > User Preferences > Addons.
* Search for NoSlide and check it.
* More info on blender addon installation, scripts directory etc. can be found [here](http://wiki.blender.org/index.php/Doc:2.6/Manual/Extensions/Python/Add-Ons).

## Usage

I will explain usage with a **walk** action as **example**.

* suppose you have a rigged character with a walk action and an NLA-strip with this action.

+ create a vertex-group on each foot (this will be used to calculate the distance to the characters center while walking).
+ select the walk NLA-strip in NLA-editor
+ select the rig in 3D-View
+ hit T in the NLA-editor to open settings
+ at the bottom you will see NoSlide

In NoSlide:
+ enter the rig-child (the character mesh).
+ enter the NLA-strip name
+ choose a frame step (smaller will be more precise but more heavy to calculate)
+ add a member for each foot and name it e.g. 'left foot' and 'right foot' 
+ for each member add the corresponding vertex-group
+ give some rotation values if you like to
+ insert the Rest Frames
+ hit calculate distances
