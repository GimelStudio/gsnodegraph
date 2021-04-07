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

        self._nodes = {}
        
        self._selected_nodes = []
        self._active_node = None


        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)

    def OnDrawBackground(self, dc):
        dc.SetBackground(wx.Brush('#2E2E2E'))
        dc.Clear()
        dc.SetBrush(wx.Brush(wx.Colour('#282828'), wx.CROSS_HATCH))
        dc.DrawRectangle(0, 0, self.Size[0], self.Size[1])

    def OnDrawScene(self, dc):
        for node in self._nodes:
            self._nodes[node].Draw(dc)

        if self._tmp_wire != None:
            self._tmp_wire.Draw(dc)

        if self._bbox_start != None and self._bbox_rect != None:
            self.DrawSelectionBox(dc, self._bbox_rect)




    def OnDrawInterface(self, dc):
        pass

    def OnLeftDown(self, event):
        pnt = event.GetPosition()
        winpnt = self.CalcMouseCoords(pnt)
 

        self._src_node = self.HitTest(winpnt)
        if self._src_node is not None:
            self.HandleNodeSelection()

            # Handle sockets and wires
            self._src_socket = self._src_node.HitTest(winpnt)

            if self._src_socket is not None:

                pnt1 = self._src_node.pos + self._src_socket.pos

                self._tmp_wire = NodeWire(
                    self,
                    pnt1,
                    winpnt,
                    None,
                    None,
                    self._src_socket.direction
                )

        else:
            # Start the box select bbox
            self._bbox_start = winpnt

            self.DeselectNodes()
                

        self._last_pnt = winpnt

        self.UpdateDrawing()

    def OnLeftUp(self, event):
        pnt = event.GetPosition()
        winpnt = self.CalcMouseCoords(pnt)

        # Clear selection bbox and set nodes as selected
        if self._bbox_rect != None:
            self._selected_nodes = self.BoxSelectHitTest(self._bbox_rect)
            for node in self._selected_nodes:
                if node.IsSelected() != True and node.IsActive() != True:
                    node.SetSelected(True)

        # Reset all values
        self._src_node = None
        self._src_socket = None
        self._tmp_wire = None
        self._bbox_start = None
        self._bbox_rect = None

        # Refresh the nodegraph
        self.UpdateDrawing()


    def HandleNodeSelection(self):
        # Set the active node
        if self._active_node is None:
            self._active_node = self._src_node
            self._active_node.SetActive(True)

        else:
            # We check to make sure this is not just the same
            # node clicked again, then we switch the active states.
            #if self._srcNode.GetId() != self._activeNode.GetId():
            self._active_node.SetActive(False)
            self._active_node = self._src_node
            self._active_node.SetActive(True)

        # When a node is active, all the selected nodes
        # need to be set to the unselected state.
        if self._selected_nodes != []:
            for node in self._selected_nodes:
                node.SetSelected(False)

    def BoxSelectHitTest(self, bboxrect):
        """ Hit-test for box selection. """
        nodehits = []
        for node in self._nodes.values():
            if bboxrect.Intersects(node.GetRect()) == True:
                nodehits.append(node)

        if nodehits != []:
            return nodehits
        else:
            self.DeselectNodes()
            return []

    def DeselectNodes(self):
        """ Deselect everything that is selected or active. """
        for node in self._selected_nodes:
            node.SetSelected(False)

        self._selected_nodes = []

        if self._active_node != None:
            self._active_node.SetActive(False)
            self._active_node = None


    def HitTest(self, pnt):
        mouse_rect = wx.Rect(pnt[0], pnt[1], 2, 2)

        for node in self._nodes:
            if mouse_rect.Intersects(self._nodes[node].GetRect()):
                return self._nodes[node]

            # Refresh the nodegraph
            self.UpdateDrawing()

    def AddNode(self, idname, pos=(0, 0), location="POSITION"):
        node = Node(self)
        self._nodes[idname] = node
        node.pos = wx.Point(pos[0], pos[1])
        return node
        