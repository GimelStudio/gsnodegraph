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

import uuid
import wx
from wx.lib.newevent import NewCommandEvent

from gsnodegraph.node import NodeWire
from gsnodegraph.constants import *

from .utils.z_matrix import ZMatrix


gsnodegraph_nodeselect_cmd_event, EVT_GSNODEGRAPH_NODESELECT = NewCommandEvent()
gsnodegraph_nodeconnect_cmd_event, EVT_GSNODEGRAPH_NODECONNECT = NewCommandEvent()
gsnodegraph_nodedisconnect_cmd_event, EVT_GSNODEGRAPH_NODEDISCONNECT = NewCommandEvent()


class NodeGraph(wx.ScrolledCanvas):
    def __init__(self, parent, registry, *args, **kwds):
        self.parent = parent
        self.matrix = ZMatrix()
        self.identity = ZMatrix()
        self.matrix.Reset()
        self.identity.Reset()
        self.previous_position = None
        self._buffer = None

        self._noderegistry = registry

        self._wires = []
        self._nodes = {}
        
        self._selected_nodes = []
        self._active_node = None

        self._middle_pnt = None
        self._last_pnt = None

        self._tmp_wire = None
        self._src_node = None
        self._src_socket = None
        
        self._bbox_rect = None
        self._bbox_start = None

        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.ScrolledCanvas.__init__(self, parent, *args, **kwds)

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda x: None)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_MOUSEWHEEL, self.OnMousewheel)
        self.Bind(wx.EVT_MIDDLE_DOWN, self.OnMiddleDown)
        self.Bind(wx.EVT_MIDDLE_UP, self.OnMiddleUp)
        
    def OnPaint(self, event):
        wx.BufferedPaintDC(self, self._buffer)

    def OnSize(self, event):
        Size = self.ClientSize
        self._buffer = wx.Bitmap(*Size)
        self.UpdateDrawing()

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

        # Update the properties panel
        self.SendNodeSelectEvent()

        # Refresh the nodegraph
        self.UpdateDrawing()

    def OnMotion(self, event):
        pnt = event.GetPosition()
        winpnt = self.CalcMouseCoords(pnt)

        # Draw box selection bbox
        if event.LeftIsDown() is True:
            if self._src_node is None and self._bbox_start != None:
                rect = wx.Rect(topLeft=self._bbox_start, bottomRight=winpnt)
                self._bbox_rect = rect
                self.UpdateDrawing()

        # If the MMB is down, calculate the scrolling of the graph
        if event.MiddleIsDown() is True and event.Dragging():
            dx = (winpnt[0] - self._middle_pnt[0])
            dy  =(winpnt[1] - self._middle_pnt[1])
            self.ScrollNodeGraph(dx, dy)
            self.ScenePostPan(dx, dy)
            self.UpdateDrawing()

        if event.LeftIsDown() and self._src_node != None and event.Dragging():
            if self._src_socket is None:
                
                # Traslating the selected nodes
                if self._selected_nodes != []:
                    for node in self._selected_nodes:
                        dpnt = node._pos + winpnt - self._last_pnt
                        node._pos = dpnt
                else:
                    # Traslating the active node
                    dpnt = self._src_node._pos + winpnt - self._last_pnt
                    self._src_node._pos = dpnt

                self._last_pnt = winpnt

                # Redraw the wires
                for wire in self._wires:
                    wire.pnt1 = wire.srcnode._pos + wire.srcsocket._pos
                    wire.pnt2 = wire.dstnode._pos + wire.dstsocket._pos

            elif self._tmp_wire != None:

                # Set the wire to be active when it is being edited.
                self._tmp_wire.active = True

                if winpnt != None:
                    self._tmp_wire.pnt2 = winpnt

            self.UpdateDrawing()

    def DrawSelectionBox(self, dc, rect):
        dc.SetPen(wx.Pen(wx.Colour('#C2C2C2'), 2.5, wx.PENSTYLE_SHORT_DASH))
        dc.SetBrush(wx.Brush(wx.Colour(100, 100, 100, 56), wx.SOLID))
        dc.DrawRectangle(rect)

    def OnMousewheel(self, event):
        rotation = event.GetWheelRotation()
        mouse = event.GetPosition()
        if rotation > 1:
            self.ScenePostScale(1.1, 1.1, mouse[0], mouse[1])
        elif rotation < -1:
            self.ScenePostScale(0.9, 0.9, mouse[0], mouse[1])
        self.UpdateDrawing()

    def OnMiddleDown(self, event):
        """ Event that updates the mouse cursor. """
        pnt = event.GetPosition()
        winpnt = self.CalcMouseCoords(pnt)

        self._middle_pnt = winpnt

        self.SetCursor(wx.Cursor(wx.CURSOR_SIZING))

    def OnMiddleUp(self, event):
        """ Event that resets the mouse cursor. """
        self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))

    def ScrollNodeGraph(self, pos_x, pos_y):
        """ Scrolls the scrollbars to the specified position. """
        scrollpos_x = self.GetScrollPos(wx.HORIZONTAL)
        scrollpos_y = self.GetScrollPos(wx.VERTICAL)

        self.Scroll(scrollpos_x - pos_x,
                    scrollpos_y - pos_y)

    def CalcMouseCoords(self, pnt):
        """ Calculate the mouse coordinates, taking into account 
        the current scroll position and zoom level. """
        pnt = self.ConvertWindowToScene(self.ConvertCoords(pnt))
        return wx.Point(pnt[0], pnt[1])

    def ConvertCoords(self, pnt):
        """ Convert coords to account for scrolling.

        :param pnt: the given wx.Point coord to convert
        :returns: wx.Point
        """
        xv, yv = self.GetViewStart()
        xd, yd = self.GetScrollPixelsPerUnit()
        return wx.Point(pnt[0] + (xv * xd), pnt[1] + (yv * yd))

    def GetViewableWindowRegion(self):
        """ Get the shown scrolled region of the window based on
        the current scrolling.

        :returns: wx.Rect
        """
        xv, yv = self.GetViewStart()
        xd, yd = self.GetScrollPixelsPerUnit()
        x, y = (xv * xd, yv * yd)
        rgn = self.GetUpdateRegion()
        rgn.Offset(x, y)
        return rgn.GetBox()

    def UpdateDrawing(self):
        dc = wx.MemoryDC()
        dc.SelectObject(self._buffer)
        dc = wx.GCDC(dc)
        self.OnDrawBackground(dc)
        dc.SetTransformMatrix(self.matrix)
        self.OnDrawScene(dc)
        dc.SetTransformMatrix(self.identity)
        self.OnDrawInterface(dc)
        del dc  # need to get rid of the MemoryDC before Update() is called.
        self.Refresh()
        self.Update()

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
        node = self._noderegistry[idname](self, uuid.uuid4())
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

        dst_socket.node.EditParameter(dst_socket._label, self._nodes[src_socket.node._id])
        self.SendNodeConnectEvent()

    def DisconnectNodes(self, src_socket, dst_socket):
        for wire in self._wires:
            if wire.srcsocket is src_socket and wire.dstsocket is dst_socket:
                self._wires.remove(wire)

                wire._dstsocket.node.EditParameter(wire._dstsocket._label, None)

        self.SendNodeDisconnectEvent()

    def SendNodeSelectEvent(self):
        wx.PostEvent(self, 
                     gsnodegraph_nodeselect_cmd_event(id=self.GetId(), 
                     value=self._active_node))

    def SendNodeConnectEvent(self):
        wx.PostEvent(self, 
                     gsnodegraph_nodeconnect_cmd_event(id=self.GetId(), 
                     value=self._active_node))

    def SendNodeDisconnectEvent(self):
        wx.PostEvent(self, 
                     gsnodegraph_nodedisconnect_cmd_event(id=self.GetId(), 
                     value=self._active_node))


    def SceneMatrixReset(self):
        self.matrix.Reset()

    def ScenePostScale(self, sx, sy=None, ax=0, ay=0):
        self.matrix.PostScale(sx, sy, ax, ay)

    def ScenePostPan(self, px, py):
        self.matrix.PostTranslate(px, py)

    def ScenePostRotate(self, angle, rx=0, ry=0):
        self.matrix.PostRotate(angle, rx, ry)

    def ScenePreScale(self, sx, sy=None, ax=0, ay=0):
        self.matrix.PreScale(sx, sy, ax, ay)

    def ScenePrePan(self, px, py):
        self.matrix.PreTranslate(px, py)

    def ScenePreRotate(self, angle, rx=0, ry=0):
        self.matrix.PreRotate(angle, rx, ry)

    def GetScaleX(self):
        return self.matrix.GetScaleX()

    def GetScaleY(self):
        return self.matrix.GetScaleY()

    def GetSkewX(self):
        return self.matrix.GetSkewX()

    def GetSkewY(self):
        return self.matrix.GetSkewY()

    def GetTranslateX(self):
        return self.matrix.GetTranslateX()

    def GetTranslateY(self):
        return self.matrix.GetTranslateY()

    def FocusPositionScene(self, scene_point):
        window_width, window_height = self.ClientSize
        scale_x = self.GetScaleX()
        scale_y = self.GetScaleY()
        self.SceneMatrixReset()
        self.ScenePostPan(-scene_point[0], -scene_point[1])
        self.ScenePostScale(scale_x, scale_y)
        self.ScenePostPan(window_width / 2.0, window_height / 2.0)

    def FocusViewportScene(self, new_scene_viewport, buffer=0, lock=True):
        window_width, window_height = self.ClientSize
        left = new_scene_viewport[0]
        top = new_scene_viewport[1]
        right = new_scene_viewport[2]
        bottom = new_scene_viewport[3]
        viewport_width = right - left
        viewport_height = bottom - top

        left -= viewport_width * buffer
        right += viewport_width * buffer
        top -= viewport_height * buffer
        bottom += viewport_height * buffer

        if right == left:
            scale_x = 100
        else:
            scale_x = window_width / float(right - left)
        if bottom == top:
            scale_y = 100
        else:
            scale_y = window_height / float(bottom - top)

        cx = ((right + left) / 2)
        cy = ((top + bottom) / 2)
        self.matrix.Reset()
        self.matrix.PostTranslate(-cx, -cy)
        if lock:
            scale = min(scale_x, scale_y)
            if scale != 0:
                self.matrix.PostScale(scale)
        else:
            if scale_x != 0 and scale_y != 0:
                self.matrix.PostScale(scale_x, scale_y)
        self.matrix.PostTranslate(window_width / 2.0, window_height / 2.0)

    def ConvertSceneToWindow(self, position):
        return self.matrix.TransformPoint([position[0], position[1]])

    def ConvertWindowToScene(self, position):
        return self.matrix.InverseTransformPoint([position[0], position[1]])
