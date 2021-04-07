# ----------------------------------------------------------------------------
# GS Nodegraph Copyright 2019-2021 by Noah Rahm and contributors
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

import wx

from gsnodegraph import NodeGraphBase, Node, NodeWire


class NodeGraph(NodeGraphBase):
    def __init__(self, *args, **kwds):
        NodeGraphBase.__init__(self, *args, **kwds)

        self.nodes = {}
        self.selectedNode = None

        self._tmp_wire = None
        self._srcNode = None

        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)

    def OnDrawBackground(self, dc):
        dc.SetBackground(wx.Brush('#2E2E2E'))
        dc.Clear()
        dc.SetBrush(wx.Brush(wx.Colour('#282828'), wx.CROSS_HATCH))
        dc.DrawRectangle(0, 0, self.Size[0], self.Size[1])

    def OnDrawScene(self, dc):
        for node in self.nodes:
            self.nodes[node].Draw(dc)

        if self._tmp_wire != None:
            self._tmp_wire.Draw(dc)

        if self._bbox_start != None and self._bbox_rect != None:
            dc.SetPen(wx.Pen(wx.Colour('#C2C2C2'), 2.5, wx.PENSTYLE_SHORT_DASH))
            dc.SetBrush(wx.Brush(wx.Colour(100, 100, 100, 56), wx.SOLID))
            dc.DrawRectangle(self._bbox_rect)


    def OnDrawInterface(self, dc):
        pass

    def OnLeftDown(self, event):
        pnt = event.GetPosition()
        winpnt = self.CalcMouseCoords(pnt)
 

        self._srcNode = self.HitTest(winpnt)
        if self._srcNode is not None:

            # Handle plugs and wires
            self._srcPlug = self._srcNode.HitTest(winpnt)

            self._srcNode.SetSelected(True)

            if self._srcPlug is not None:

                pnt1 = self._srcNode.pos + self._srcPlug.pos

                self._tmp_wire = NodeWire(
                    self,
                    pnt1,
                    winpnt,
                    None,
                    None,
                    self._srcPlug.direction
                )

        else:
            # Start the box select bbox
            self._bbox_start = winpnt
                

        self._last_pnt = winpnt

        self.UpdateDrawing()

    def OnLeftUp(self, event):
        self._srcNode = None
        self._srcPlug = None
        self._tmp_wire = None
        self._bbox_start = None
        self._bbox_rect = None

        self.UpdateDrawing()


    def HitTest(self, pnt):

        mouse_rect = wx.Rect(pnt[0], pnt[1], 2, 2)

        for node in self.nodes:

            # TODO: when a node is selected, bring it to the top of the stack
            if mouse_rect.Intersects(self.nodes[node].GetRect()):
                return self.nodes[node]
            else:
                self.nodes[node].SetSelected(False)
                #
                self.UpdateDrawing()


    def AddNode(self, idname, pos=(0, 0), location="POSITION"):
        node = Node(self)
        self.nodes[idname] = node
        node.pos = wx.Point(pos[0], pos[1])
        return node
        