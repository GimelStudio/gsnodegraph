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


class Parameter(object):
    """ Example parameter base class. """
    def __init__(self, idname, label, default):
        self.idname = idname
        self.label = label
        self.default = default
        self.binding = None
        self.datatype = None


class ImageParam(Parameter):
    """ Example parameter. """
    def __init__(self, idname, label, default=Image()):
        Parameter.__init__(self, idname, label, default)
        self.value = default
        self.datatype = "IMAGE"

    def GetValue(self):
        return self.value

    def SetValue(self, value):
        self.value = value


class IntegerParam(Parameter):
    """ Example parameter. """
    def __init__(self, idname, label, default=1):
        Parameter.__init__(self, idname, label, default)
        self.value = default
        self.datatype = "VALUE"

    def GetValue(self):
        return self.value

    def SetValue(self, value):
        self.value = value


class OutputNode(NodeBase):
    """ Example output node. Only one of these should exist at a time.
    Use ``self._isoutput = True`` to set as the output node.  """
    def __init__(self, nodegraph, _id):
        NodeBase.__init__(self, nodegraph, _id)

        self.label = "Output"
        self.is_output = True
        self.category = "OUTPUT"
        self.parameters = {
            "image_socketid": ImageParam("image_socketid", "Image")
        }


class ImageNode(NodeBase):
    """ Example node showing an input node. """
    def __init__(self, nodegraph, _id):
        NodeBase.__init__(self, nodegraph, _id)

        self.label = "Image"
        self.category = "INPUT"
        self.parameters = {}


class MixNode(NodeBase):
    """ Example node showing a node with multiple inputs. """
    def __init__(self, nodegraph, _id):
        NodeBase.__init__(self, nodegraph, _id)

        self.label = "Mix"
        self.category = "BLEND"
        self.parameters = {
            "image1_socketid": ImageParam("image1_socketid", "Overlay"),
            "image2_socketid": ImageParam("image2_socketid", "Image")
        }


class BlurNode(NodeBase):
    """ Example node showing a node with multiple inputs
    and different datatypes. """
    def __init__(self, nodegraph, _id):
        NodeBase.__init__(self, nodegraph, _id)

        self.label = "Blur"
        self.category = "FILTER"
        self.parameters = {
            "image1_socketid": ImageParam("image1_socketid", "Image"),
            "int_socketid": IntegerParam("int_socketid", "Integer")
        }


class BlendNode(NodeBase):
    """ Example node showing a node with multiple inputs. """
    def __init__(self, nodegraph, _id):
        NodeBase.__init__(self, nodegraph, _id)

        self.label = "Brightness/Contrast"
        self.category = "BLEND"
        self.parameters = {
            "alphamask_socketid": ImageParam("alphamask_socketid", "Alpha"),
            "image1_socketid": ImageParam("image1_socketid", "Image"),
            "image2_socketid": ImageParam("image2_socketid", "Image")
        }


class ValueNode(NodeBase):
    """ Example node showing a node with a different datatype output. """
    def __init__(self, nodegraph, _id):
        NodeBase.__init__(self, nodegraph, _id)

        self.label = "Perspective Transform"
        self.category = "INPUT"

    def NodeOutputDatatype(self):
        return "VALUE"
