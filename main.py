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

import sys
import wx
import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(True)
except Exception:
    pass

from gsnodegraph import EVT_GSNODEGRAPH_ADDNODEBTN
from nodes import OutputNode, MixNode, ImageNode, BlurNode, BlendNode, ValueNode
from nodegraph import NodeGraph


# Install a custom displayhook to keep Python from setting the global
# _ (underscore) to the value of the last evaluated expression.
# If we don't do this, our mapping of _ to gettext can get overwritten.
# This is useful/needed in interactive debugging with PyShell.
def _displayHook(obj):
    """ Custom display hook to prevent Python stealing '_'. """

    if obj is not None:
        print(repr(obj))

# Add translation macro to builtin similar to what gettext does.
import builtins
builtins.__dict__['_'] = wx.GetTranslation


class MainApp(wx.App):

    def OnInit(self):

        # Work around for Python stealing "_".
        sys.displayhook = _displayHook

        return True


class MyFrame(wx.Frame):
    def __init__(self, parent, id=wx.ID_ANY, title=wx.EmptyString,
                 pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=wx.DEFAULT_FRAME_STYLE, name="frame"):
        wx.Frame.__init__(self, parent, id, title, pos, size, style, name)

        # Setup the node registry
        node_registry = {
            "image_nodeid": ImageNode,
            "mix_nodeid": MixNode,
            "blur_nodeid": BlurNode,
            "blend_nodeid": BlendNode,
            "value_nodeid": ValueNode,
            "output_nodeid": OutputNode
        }
        # Setup the config with datatypes and node categories
        config = {
            "image_datatype": "IMAGE",
            "node_datatypes": {
                "IMAGE": "#C6C62D",  # Yellow
                "INTEGER": "#A0A0A0",  # Grey
                "FLOAT": "#A0A0A0",  # Grey
                "VALUE": "#A0A0A0",  # Depreciated!
            },
            "input_nodes_categories": ["INPUT"],
            "node_categories": {
                "INPUT": "#E64555",  # Burgendy
                "DRAW": "#AF4467",  # Pink
                "MASK": "#084D4D",  # Blue-green
                "CONVERT": "#564B7C",  # Purple
                "FILTER": "#558333",  # Green
                "BLEND": "#498DB8",  # Light blue
                "COLOR": "#C2AF3A",  # Yellow
                "TRANSFORM": "#6B8B8B", # Blue-grey
                "OUTPUT": "#B33641"  # Red
            }
        }

        # Init the nodegraph
        ng = NodeGraph(self, registry=node_registry, config=config)

        # Add nodes to the node graph
        node1 = ng.AddNode("image_nodeid", pos=wx.Point(100, 10))
        node2 = ng.AddNode("image_nodeid", pos=wx.Point(450, 400))
        node3 = ng.AddNode("mix_nodeid", pos=wx.Point(400, 100))
        node4 = ng.AddNode("blur_nodeid", pos=wx.Point(700, 100))
        node5 = ng.AddNode("blend_nodeid", pos=wx.Point(720, 300))
        node6 = ng.AddNode("value_nodeid", pos=wx.Point(620, 430))
        node7 = ng.AddNode("output_nodeid", pos=wx.Point(1000, 290))

        # Maximize the window
        self.Maximize(True)

        # Bind events
        ng.Bind(EVT_GSNODEGRAPH_ADDNODEBTN, self.OnAddNodeMenuBtn)
        self.Bind(wx.EVT_CLOSE, self.OnDestroy)

    def OnAddNodeMenuBtn(self, event):
        print("Open add node menu")

    def OnDestroy(self, event):
        self.Destroy()


if __name__ == "__main__":
    app = MainApp()
    frame = MyFrame(None, size=(512, 512))
    frame.SetTitle("gsnodegraph demo")
    frame.Show()
    app.MainLoop()
