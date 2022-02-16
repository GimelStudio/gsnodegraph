# ----------------------------------------------------------------------------
# gsnodegraph Copyright 2019-2022 by Noah Rahm and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ----------------------------------------------------------------------------

from gsnodegraph import NodeBase


class Image(object):
    """ An example datatype. """
    # Create your datatype. For this example, we do nothing.
    pass


class Property(object):
    """ Example property base class. """
    def __init__(self, idname, default, label, exposed=True, 
                 can_be_exposed=True, visible=False):
        self.idname = idname
        self.label = label
        self.default = default
        self.exposed = exposed
        self.can_be_exposed = can_be_exposed
        self.visible = visible
        self.binding = None
        self.datatype = None
        

class ImageProp(Property):
    """ Example property. """
    def __init__(self, idname, default=Image(), label="Image", exposed=True, 
                 can_be_exposed=True, visible=True):
        Property.__init__(self, idname, default, label, exposed, 
                          can_be_exposed, visible)
        self.value = default
        self.datatype = "IMAGE"

    def GetValue(self):
        return self.value

    def SetValue(self, value):
        self.value = value


class IntegerProp(Property):
    """ Example property. """
    def __init__(self, idname, default=1, label="Integer", exposed=True, 
                 can_be_exposed=True, visible=True):
        Property.__init__(self, idname, default, label, exposed, 
                          can_be_exposed, visible)
        self.value = default
        self.datatype = "INTEGER"

    def GetValue(self):
        return self.value

    def SetValue(self, value):
        self.value = value


class Output(object):
    def __init__(self, idname, datatype, label, visible=True):
        self.idname = idname
        self.datatype = datatype
        self.label = label 
        self.visible = visible


class OutputNode(NodeBase):
    """ Example output node. Only one of these should exist at a time.
    Use ``self._isoutput = True`` to set as the output node.  """
    def __init__(self, nodegraph, _id):
        NodeBase.__init__(self, nodegraph, _id)

        self.label = "Output"
        self.is_output = True
        self.category = "OUTPUT"
        self.properties = {
            "image_socketid": ImageProp("image_socketid", label="Image")
        }


class ImageNode(NodeBase):
    """ Example node showing an input node. """
    def __init__(self, nodegraph, _id):
        NodeBase.__init__(self, nodegraph, _id)

        self.label = "Image"
        self.category = "INPUT"
        self.outputs = {
            "image": Output(idname="image", datatype="IMAGE", label="Image")
        }
        self.properties = {}


class MixNode(NodeBase):
    """ Example node showing a node with multiple inputs. """
    def __init__(self, nodegraph, _id):
        NodeBase.__init__(self, nodegraph, _id)

        self.label = "Mix"
        self.category = "BLEND"
        self.outputs = {
            "image": Output(idname="image", datatype="IMAGE", label="Image"),
            "alpha": Output(idname="alpha", datatype="INTEGER", label="Alpha")
        }
        self.properties = {
            "image1_socketid": ImageProp("image1_socketid", label="Overlay"),
            "image2_socketid": ImageProp("image2_socketid", label="Image")
        }


class BlurNode(NodeBase):
    """ Example node showing a node with multiple inputs
    and different datatypes. """
    def __init__(self, nodegraph, _id):
        NodeBase.__init__(self, nodegraph, _id)

        self.label = "Blur"
        self.category = "FILTER"
        self.outputs = {
            "image": Output(idname="image", datatype="IMAGE", label="Image")
        }
        self.properties = {
            "image1_socketid": ImageProp("image1_socketid", label="Image"),
            "int_socketid": IntegerProp("int_socketid", label="Integer")
        }


class BlendNode(NodeBase):
    """ Example node showing a node with multiple inputs. """
    def __init__(self, nodegraph, _id):
        NodeBase.__init__(self, nodegraph, _id)

        self.label = "Brightness/Contrast"
        self.category = "BLEND"

        self.outputs = {
            "image": Output(idname="image", datatype="IMAGE", label="Image")
        }
        self.properties = {
            "alphamask_socketid": ImageProp("alphamask_socketid", label="Alpha"),
            "image1_socketid": ImageProp("image1_socketid", label="Image"),
            "image2_socketid": ImageProp("image2_socketid", label="Image")
        }


class ValueNode(NodeBase):
    """ Example node showing a node with a different datatype output. """
    def __init__(self, nodegraph, _id):
        NodeBase.__init__(self, nodegraph, _id)

        self.label = "Value"
        self.category = "INPUT"
        self.outputs = {
            "value": Output(idname="value", datatype="INTEGER", label="Value")
        }

