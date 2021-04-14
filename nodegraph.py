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

from gsnodegraph import NodeGraphBase, NodeWire
from gsnodegraph.constants import *


class NodeGraph(NodeGraphBase):
    def __init__(self, parent, registry, **kwds):
        NodeGraphBase.__init__(self, parent, **kwds)

        self._noderegistry = registry


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

        for wire in self._wires:
            wire.Draw(dc)

    def OnDrawInterface(self, dc):
        pass

    def OnLeftDown(self, event):
        pnt = event.GetPosition()
        winpnt = self.CalcMouseCoords(pnt)
 
        # The node has been clicked
        self._src_node = self.HitTest(winpnt)
        if self._src_node is not None:
            self.HandleNodeSelection()

            # Handle sockets and wires
            self._src_socket = self._src_node.HitTest(winpnt)

            if self._src_socket is not None:

                # We do not allow connections from anything except
                # the output socket. If this is an Output socket,
                # we create the temp wire.
                if self._src_socket._direction == SOCKET_OUTPUT:
                    pnt1 = self._src_node.pos + self._src_socket.pos

                    self._tmp_wire = NodeWire(
                        self,
                        pnt1,
                        winpnt,
                        None,
                        None,
                        self._src_socket._direction
                    )

                # If this is an input socket, we disconnect any already-existing
                # sockets and connect the new wire. We do not allow disconnections
                # from the output socket
                elif self._src_socket._direction != SOCKET_OUTPUT:

                    for wire in self._wires:
                        if wire._dstsocket == self._src_socket:
                            dst = wire._dstsocket
                            self._src_socket = wire._srcsocket
                            self.DisconnectNodes(self._src_socket, dst)

                    # Refresh the nodegraph
                    self.UpdateDrawing()

                    # Don't allow a wire to be pulled out from an input node
                    if self._src_socket._direction == SOCKET_OUTPUT:

                        # Create the temp wire again
                        pnt = event.GetPosition()
                        winpnt = self.CalcMouseCoords(pnt)
                        pnt1 = self._src_socket._node._pos + self._src_socket._pos

                        # Draw the temp wire with the new values
                        self._tmp_wire = NodeWire(
                            self,
                            pnt1,
                            winpnt,
                            None,
                            None,
                            self._src_socket._direction,
                        )

                        # Important: we re-assign the source node variable
                        self._src_node = self._src_socket._node

        else:
            # Start the box select bbox
            self._bbox_start = winpnt

            self.DeselectNodes()
                

        self._last_pnt = winpnt

        # Refresh the nodegraph
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

        # Attempt to make a connection
        if self._src_node != None:
            dst_node = self.HitTest(winpnt)
            if dst_node is not None:
                dst_socket = dst_node.HitTest(winpnt)

                # Make sure not to allow the same datatype or
                # 'plug type' of sockets to be connected!
                if dst_socket is not None:
                    if self._src_socket._direction != dst_socket._direction \
                        and self._src_node != dst_node:

                        # Only allow a single wire to be connected to any one input.
                        if self.PlugHasWire(dst_socket) is not True:
                            self.ConnectNodes(self._src_socket, dst_socket)

                        # If there is already a connection,
                        # but a wire is "dropped" into the socket
                        # disconnect the last connection and
                        # connect the current wire.
                        else:
                            for wire in self._wires:
                                if wire._dstsocket == dst_socket:
                                    dst = wire._dstsocket
                                    src = wire._srcsocket
                                    self.DisconnectNodes(src, dst)

                            self.ConnectNodes(self._src_socket, dst_socket)

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
            if self._src_node != self._active_node:
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
            # Inflate the rect so that the node sockets are
            # highly sensitive to clicks for easier connections.
            node_rect = self._nodes[node].GetRect().Inflate(8, 8)
            if mouse_rect.Intersects(node_rect):
                return self._nodes[node]

            # Refresh the nodegraph
            self.UpdateDrawing()

    def AddNode(self, idname, pos=(0, 0), location="POSITION"):
        node = self._noderegistry[idname](self)
        node._Init()
        self._nodes[node._id] = node
        node.pos = wx.Point(pos[0], pos[1])
        return node

    def PlugHasWire(self, dst_socket):
        for wire in self._wires:
            if wire.dstsocket == dst_socket:
                return True
        return False

    def ConnectNodes(self, src_socket, dst_socket):
        pt1 = src_socket._node._pos + src_socket._pos
        pt2 = dst_socket._node._pos + dst_socket._pos
        _dir = src_socket._direction

        wire = NodeWire(src_socket, pt1, pt2, src_socket, dst_socket, _dir)
        wire.srcnode = src_socket._node
        wire.dstnode = dst_socket._node
        wire._srcsocket = src_socket
        wire._dstsocket = dst_socket

        self._wires.append(wire)

    def DisconnectNodes(self, src_socket, dst_socket):
        for wire in self._wires:
            if wire.srcsocket is src_socket and wire.dstsocket is dst_socket:
                self._wires.remove(wire)
