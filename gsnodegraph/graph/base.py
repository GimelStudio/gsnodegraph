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

import uuid
import wx
import wx.lib.agw.flatmenu as flatmenu
from wx.lib.newevent import NewCommandEvent

from gsnodegraph.node import NodeWire
from gsnodegraph.constants import (GRAPH_BACKGROUND_COLOR, SOCKET_OUTPUT,
                                   SELECTION_BOX_COLOR, SELECTION_BOX_BORDER_COLOR,
                                   DEFAULT_WIRE_CURVATURE)
from gsnodegraph.assets import ICON_ADD_NODE
from .utils.z_matrix import ZMatrix
from .btn import AddNodeBtn

gsnodegraph_nodeselect_cmd_event, EVT_GSNODEGRAPH_NODESELECT = NewCommandEvent()
gsnodegraph_nodeconnect_cmd_event, EVT_GSNODEGRAPH_NODECONNECT = NewCommandEvent()
gsnodegraph_nodedisconnect_cmd_event, EVT_GSNODEGRAPH_NODEDISCONNECT = NewCommandEvent()
gsnodegraph_mousezoom_cmd_event, EVT_GSNODEGRAPH_MOUSEZOOM = NewCommandEvent()
gsnodegraph_addnodebtn_cmd_event, EVT_GSNODEGRAPH_ADDNODEBTN = NewCommandEvent()

ID_CONTEXTMENU_DELETENODE = wx.NewIdRef()
ID_CONTEXTMENU_MUTENODE = wx.NewIdRef()
ID_CONTEXTMENU_UNMUTENODE = wx.NewIdRef()
ID_CONTEXTMENU_DELETENODES = wx.NewIdRef()
ID_CONTEXTMENU_DUPLICATENODE = wx.NewIdRef()
ID_CONTEXTMENU_DESELECTALLNODES = wx.NewIdRef()
ID_CONTEXTMENU_SELECTALLNODES = wx.NewIdRef()


class NodeGraphBase(wx.ScrolledCanvas):
    def __init__(self, parent, registry, config, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.ScrolledCanvas.__init__(self, parent, *args, **kwds)
        
        self.parent = parent
        self.node_registry = registry
        self.node_datatypes = config["node_datatypes"]
        self.node_categories = config["node_categories"]
        self.image_datatype = config["image_datatype"]
        self.input_nodes_categories = config["input_nodes_categories"]

        self.matrix = ZMatrix()
        self.identity = ZMatrix()
        self.matrix.Reset()
        self.identity.Reset()

        self.buffer = None
        self.bg_img = None
        self.zoom = 100

        self.wires = []
        self.nodes = {}

        self.sel_nodes = []
        self.active_node = None
        self.last_active_node = None

        self.middle_pnt = None
        self.last_pnt = None

        self.tmp_wire = None
        self.src_node = None
        self.src_socket = None

        self.bbox_rect = None
        self.bbox_start = None

        self.wire_curvature = DEFAULT_WIRE_CURVATURE

        # Init the add node button
        self.addnode_btn = AddNodeBtn(self)

        # Event bindings
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda x: None)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_MOUSEWHEEL, self.OnMousewheel)
        self.Bind(wx.EVT_MIDDLE_DOWN, self.OnMiddleDown)
        self.Bind(wx.EVT_MIDDLE_UP, self.OnMiddleUp)

        # Context menu bindings
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        self.Bind(wx.EVT_MENU, self.OnDeleteNode,
                          id=ID_CONTEXTMENU_DELETENODE)
        self.Bind(wx.EVT_MENU, self.OnMuteNode,
                          id=ID_CONTEXTMENU_MUTENODE)
        self.Bind(wx.EVT_MENU, self.OnUnmuteNode,
                          id=ID_CONTEXTMENU_UNMUTENODE)
        self.Bind(wx.EVT_MENU, self.OnDeleteNodes,
                          id=ID_CONTEXTMENU_DELETENODES)
        self.Bind(wx.EVT_MENU, self.OnSelectAllNodes,
                          id=ID_CONTEXTMENU_SELECTALLNODES)
        self.Bind(wx.EVT_MENU, self.OnDeselectAllNodes,
                          id=ID_CONTEXTMENU_DESELECTALLNODES)
        self.Bind(wx.EVT_MENU, self.OnDuplicateNode,
                          id=ID_CONTEXTMENU_DUPLICATENODE)

        # Keyboard shortcut bindings
        self.accel_tbl = wx.AcceleratorTable([(wx.ACCEL_SHIFT, ord('D'),
                                               ID_CONTEXTMENU_DUPLICATENODE),
                                              (wx.ACCEL_SHIFT, ord('M'),
                                               ID_CONTEXTMENU_MUTENODE),
                                              (wx.ACCEL_NORMAL, wx.WXK_DELETE,
                                               ID_CONTEXTMENU_DELETENODES),
                                              ])
        self.parent.SetAcceleratorTable(self.accel_tbl)

    def OnPaint(self, event):
        dc = wx.BufferedPaintDC(self, self.buffer)

    def OnSize(self, event):
        Size = self.ClientSize
        self.buffer = wx.Bitmap(*Size)
        self.UpdateNodeGraph()

    def OnLeftDown(self, event):
        pnt = event.GetPosition()
        winpnt = self.CalcMouseCoords(pnt)

        # The node has been clicked
        self.src_node = self.HitTest(winpnt)
        if self.src_node is not None:
            self.HandleNodeSelection()

            # If the user CTRL+Clicks a node, connect it to the
            # output node in place of any other connections.
            if wx.GetKeyState(wx.WXK_CONTROL) == True:
                self.SetNodeAsPreview(self.src_node)

            # Handle sockets and wires
            self.src_socket = self.src_node.HitTest(winpnt)

            if self.src_socket is not None:

                # We do not allow connections from anything except
                # the output socket. If this is an Output socket,
                # we create the temp wire.
                if self.src_socket.direction == SOCKET_OUTPUT:
                    pnt1 = self.src_node.pos + self.src_socket.pos

                    self.tmp_wire = NodeWire(self, pnt1, winpnt, None, None,
                                              self.src_socket.direction,
                                              self.wire_curvature)

                # If this is an input socket, we disconnect any already-existing
                # sockets and connect the new wire. We do not allow disconnections
                # from the output socket
                elif self.src_socket.direction != SOCKET_OUTPUT:

                    for wire in self.wires:
                        if wire.dstsocket == self.src_socket:
                            dst = wire.dstsocket
                            self.src_socket = wire.srcsocket
                            self.DisconnectNodes(self.src_socket, dst)

                    # Refresh the nodegraph
                    self.UpdateNodeGraph()

                    # Don't allow a wire to be pulled out from an input node
                    # AKA: backwards
                    if self.src_socket.direction == SOCKET_OUTPUT:

                        # Create the temp wire again
                        pnt = event.GetPosition()
                        winpnt = self.CalcMouseCoords(pnt)
                        pnt1 = self.src_socket.node.pos + self.src_socket.pos

                        # Draw the temp wire with the new values
                        self.tmp_wire = NodeWire(self, pnt1, winpnt, None, None,
                                                  self.src_socket.direction,
                                                  self.wire_curvature)

                        # Important: we re-assign the source node variable
                        self.src_node = self.src_socket.node

        else:
            # Start the box select bbox
            self.bbox_start = winpnt

            self.DeselectNodes()

            # Update add node button
            pnt = event.GetPosition()
            if self.MouseInAddNodeBtn(pnt) is True:
                self.addnode_btn.SetClicked(True)

        self.last_pnt = winpnt

        # Refresh the nodegraph
        self.UpdateNodeGraph()

    def OnLeftUp(self, event):
        pnt = event.GetPosition()
        winpnt = self.CalcMouseCoords(pnt)

        # Clear selection bbox and set nodes as selected
        if self.bbox_rect != None:
            self.sel_nodes = self.BoxSelectHitTest(self.bbox_rect)
            for node in self.sel_nodes:
                if node.IsSelected() != True and node.IsActive() != True:
                    node.SetSelected(True)

        # Attempt to make a connection
        if self.src_node != None:
            dst_node = self.HitTest(winpnt)
            
            if dst_node is not None:
                dst_socket = dst_node.HitTest(winpnt)

                # Make sure not to allow different datatypes or
                # the same 'socket type' to be connected!
                if dst_socket is not None:
                    if (self.src_socket.direction != dst_socket.direction
                        and self.src_socket.datatype == dst_socket.datatype
                        and self.src_node != dst_node):

                        # Only allow a single wire to be connected to any one input.
                        if self.SocketHasWire(dst_socket) is not True:
                            self.ConnectNodes(self.src_socket, dst_socket)

                        # If there is already a connection,
                        # but a wire is "dropped" into the socket
                        # disconnect the last connection and
                        # connect the current wire.
                        else:
                            for wire in self.wires:
                                if wire.dstsocket == dst_socket:
                                    dst = wire.dstsocket
                                    src = wire.srcsocket
                                    self.DisconnectNodes(src, dst)

                            self.ConnectNodes(self.src_socket, dst_socket)

            # Send event to update the properties panel
            if self.last_active_node is None:
                self.SendNodeSelectEvent()
            if self.last_active_node is not self.src_node:
                self.SendNodeSelectEvent()
            self.last_active_node = self.src_node


        # Reset all values
        self.src_node = None
        self.src_socket = None
        self.tmp_wire = None
        self.bbox_start = None
        self.bbox_rect = None

        # Update add node button and send button event if it was clicked
        pnt = event.GetPosition()
        if self.MouseInAddNodeBtn(pnt) is True:
            self.addnode_btn.SetClicked(False)
            self.SendAddNodeBtnEvent()

        # Refresh the nodegraph
        self.UpdateNodeGraph()

    def OnMotion(self, event):
        pnt = event.GetPosition()
        winpnt = self.CalcMouseCoords(pnt)

        # Draw box selection bbox
        if event.LeftIsDown() is True:
            if self.src_node is None and self.bbox_start != None:
                rect = wx.Rect(topLeft=self.bbox_start, bottomRight=winpnt)
                self.bbox_rect = rect
                self.UpdateNodeGraph()

        # If the MMB is down, calculate the scrolling of the graph
        if event.MiddleIsDown() is True and event.Dragging():
            dx = int(winpnt[0] - self.middle_pnt[0])
            dy = int(winpnt[1] - self.middle_pnt[1])
            self.ScrollNodeGraph(dx, dy)
            self.ScenePostPan(dx, dy)
            self.UpdateNodeGraph()

        if event.LeftIsDown() and self.src_node != None and event.Dragging():
            if self.src_socket is None:

                # Traslating the selected nodes
                if self.sel_nodes != []:
                    for node in self.sel_nodes:
                        dpnt = node.pos + winpnt - self.last_pnt
                        node.pos = dpnt
                else:
                    # Traslating the active node
                    dpnt = self.src_node.pos + winpnt - self.last_pnt
                    self.src_node.pos = dpnt

                self.last_pnt = winpnt

                # Redraw the wires
                for wire in self.wires:
                    wire.pnt1 = wire.srcnode.pos + wire.srcsocket.pos
                    wire.pnt2 = wire.dstnode.pos + wire.dstsocket.pos

            elif self.tmp_wire != None:

                # Set the wire to be active when it is being edited.
                self.tmp_wire.active = True

                if winpnt != None:
                    self.tmp_wire.pnt2 = winpnt

            self.UpdateNodeGraph()

        else:
            pnt = event.GetPosition()
            if self.addnode_btn.IsClicked() is not True:
                if self.MouseInAddNodeBtn(pnt) is True:
                    self.addnode_btn.SetFocused(True)
                else:
                    self.addnode_btn.SetFocused(False)
            self.UpdateNodeGraph()

    def OnDeleteNodes(self, event):
        self.DeleteNodes()

    def OnDeleteNode(self, event):
        if (self.active_node != None and
            self.active_node.IsOutputNode() != True):
            self.DeleteNode(self.active_node)
            self.active_node = None

        # Update the properties panel so that the deleted
        # nodes' properties are not still shown!
        self.SendNodeSelectEvent()

        self.UpdateNodeGraph()

    def OnMuteNode(self, event):
        self.active_node.SetMuted(True)
        self.UpdateNodeGraph()

    def OnUnmuteNode(self, event):
        self.active_node.SetMuted(False)
        self.UpdateNodeGraph()

    def OnSelectAllNodes(self, event):
        """ Event that selects all the nodes in the Node Graph. """
        for node_id in self.nodes:
            node = self.nodes[node_id]
            if node.IsActive() is True:
                node.SetActive(False)
            node.SetSelected(True)
            self.sel_nodes.append(node)
        self.UpdateNodeGraph()

    def OnDeselectAllNodes(self, event):
        """ Event that deselects all the currently selected nodes. """
        self.DeselectNodes()
        self.UpdateNodeGraph()

    def OnDuplicateNode(self, event):
        """ Event that duplicates the currently selected node. """
        self.DuplicateNode(self.active_node)

    def OnContextMenu(self, event):
        # Create the popup menu
        self.CreateContextMenu()

        # Position it at the mouse cursor
        pnt = event.GetPosition()
        self.context_menu.Popup(wx.Point(pnt.x, pnt.y), self)

    def CreateContextMenu(self):
        self.context_menu = flatmenu.FlatMenu()

        # If there is an active node, then we know
        # that there shouldn't be any other nodes
        # selected, thus we handle the active node first.
        if self.active_node != None:

            # Do not allow the output node to be
            # deleted or duplicated at all.
            if self.active_node.IsOutputNode() != True:
                duplicate_menuitem = flatmenu.FlatMenuItem(self.context_menu,
                                                           ID_CONTEXTMENU_DUPLICATENODE,
                                                           "{0}{1}".format(_("Duplicate"), "\tShift+D"), "",
                                                           wx.ITEM_NORMAL)
                self.context_menu.AppendItem(duplicate_menuitem)
                delete_menuitem = flatmenu.FlatMenuItem(self.context_menu,
                                                        ID_CONTEXTMENU_DELETENODE,
                                                        "{0}{1}".format(_("Delete"), "\tDel"), "",
                                                        wx.ITEM_NORMAL)
                self.context_menu.AppendItem(delete_menuitem)

                if self.IsInputNode(self.active_node) is not True:
                    if self.active_node.IsMuted() is not True:
                        mute_menuitem = flatmenu.FlatMenuItem(self.context_menu,
                                                                ID_CONTEXTMENU_MUTENODE,
                                                                "{0}{1}".format(_("Mute"), "\tShift+M"), "",
                                                                wx.ITEM_NORMAL)
                        self.context_menu.AppendItem(mute_menuitem)
                    else:
                        unmute_menuitem = flatmenu.FlatMenuItem(self.context_menu,
                                                                ID_CONTEXTMENU_UNMUTENODE,
                                                                _("Unmute"), "",
                                                                wx.ITEM_NORMAL)
                        self.context_menu.AppendItem(unmute_menuitem)

        else:
            if self.sel_nodes != []:
                deletenodes_menuitem = flatmenu.FlatMenuItem(self.context_menu,
                                                             ID_CONTEXTMENU_DELETENODES,
                                                             "{0}{1}".format(_("Delete Selected"), "\tDel"), "",
                                                             wx.ITEM_NORMAL)
                self.context_menu.AppendItem(deletenodes_menuitem)

        selectallnodes_menuitem = flatmenu.FlatMenuItem(self.context_menu,
                                                        ID_CONTEXTMENU_SELECTALLNODES,
                                                        "Select All", "",
                                                        wx.ITEM_NORMAL)
        self.context_menu.AppendItem(selectallnodes_menuitem)

        deselectallnodes_menuitem = flatmenu.FlatMenuItem(self.context_menu,
                                                          ID_CONTEXTMENU_DESELECTALLNODES,
                                                          "Deselect All", "",
                                                          wx.ITEM_NORMAL)
        self.context_menu.AppendItem(deselectallnodes_menuitem)

    def DrawSelectionBox(self, dc, rect):
        dc.SetPen(wx.Pen(wx.Colour(SELECTION_BOX_BORDER_COLOR), 2,
                  wx.PENSTYLE_SHORT_DASH))
        dc.SetBrush(wx.Brush(wx.Colour(SELECTION_BOX_COLOR)))
        dc.DrawRectangle(rect)

    def SetZoomLevel(self, zoom, x=0, y=0):
        if x == 0:
            x = int(self.Size[0]/2)
            y = int(self.Size[1]/2)
        self.ScenePostScale(zoom, zoom, x, y)
        self.UpdateZoomValue()
        self.UpdateNodeGraph()

    def OnMousewheel(self, event):
        rotation = event.GetWheelRotation()
        mouse = event.GetPosition()

        if rotation > 1 and self.zoom < 310:
            self.ScenePostScale(1.1, 1.1, mouse[0], mouse[1])

        elif rotation < -1 and self.zoom > 60:
            self.ScenePostScale(0.9, 0.9, mouse[0], mouse[1])

        self.UpdateZoomValue()
        self.SendMouseZoomEvent()
        self.UpdateNodeGraph()

    def OnMiddleDown(self, event):
        """ Event that updates the mouse cursor. """
        pnt = event.GetPosition()
        winpnt = self.CalcMouseCoords(pnt)

        self.middle_pnt = winpnt

        self.SetCursor(wx.Cursor(wx.CURSOR_SIZING))

    def OnMiddleUp(self, event):
        """ Event that resets the mouse cursor. """
        self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))

    def GetNodes(self):
        return self.nodes

    def UpdateZoomValue(self):
        self.zoom = round(self.GetScaleX() * 100)

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
        return wx.Point(int(pnt[0]), int(pnt[1]))

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

    def UpdateNodeGraph(self):
        dc = wx.MemoryDC()
        dc.SelectObject(self.buffer)
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
        dc.SetBackground(wx.Brush(wx.Colour(GRAPH_BACKGROUND_COLOR)))
        dc.Clear()

    def OnDrawScene(self, dc):
        # Draw background
        if self.bg_img != None:
            image = self.bg_img

            x = int(self.GetSize()[0]/2.0 - image.Width/2.0)
            y = int(self.GetSize()[1]/2.0 - image.Height/2.0)
            pnt = self.ConvertCoords(wx.Point(x, y))
            dc.DrawBitmap(image, pnt[0], pnt[1], useMask=False)

        # Draw nodes
        for node_id in self.nodes:
            self.nodes[node_id].Draw(dc)

        # Draw temporary wires
        if self.tmp_wire != None:
            self.tmp_wire.Draw(dc)

        # Draw wires
        for wire in self.wires:
            wire.Draw(dc)

        # Draw selection box
        if self.bbox_start != None and self.bbox_rect != None:
            self.DrawSelectionBox(dc, self.bbox_rect)

    def OnDrawInterface(self, dc):
        # Calculate the position and draw the add node button
        padding = 10
        x = (padding)
        y = int((self.GetSize()[1] - self.addnode_btn.GetHeight()) - padding)
        pnt = self.ConvertCoords(wx.Point(x, y))
        self.addnode_btn.Draw(dc, pnt)

    def SetNodeWireCurvature(self, curvature):
        self.wire_curvature = curvature

        # Change existing wires
        for wire in self.wires:
            wire.SetCurvature(curvature)

    def SetBackgroundImage(self, image):
        self.bg_img = image

    def HandleNodeSelection(self):
        # Set the active node
        if self.active_node is None:
            self.active_node = self.src_node
            self.active_node.SetActive(True)

        else:
            # We check to make sure this is not just the same
            # node clicked again, then we switch the active states.
            if self.src_node != self.active_node:
                self.active_node.SetActive(False)
                self.active_node = self.src_node
                self.active_node.SetActive(True)

        # When a node is active, all the selected nodes
        # need to be set to the unselected state.
        if self.sel_nodes != []:
            [node.SetSelected(False) for node in self.sel_nodes]

    def BoxSelectHitTest(self, bboxrect):
        """ Hit-test for box selection. """
        nodehits = []
        for node in self.nodes.values():
            if bboxrect.Intersects(node.GetRect()) == True:
                nodehits.append(node)

        if nodehits != []:
            return nodehits
        else:
            self.DeselectNodes()
            return []

    def DeselectNodes(self):
        """ Deselect everything that is selected or active. """
        [node.SetSelected(False) for node in self.sel_nodes]

        self.sel_nodes = []

        if self.active_node != None:
            self.active_node.SetActive(False)
            self.active_node = None

    def HitTest(self, pnt):
        mouse_rect = wx.Rect(pnt[0], pnt[1], 2, 2)

        for node in self.nodes:
            # Inflate the rect so that the node sockets are
            # highly sensitive to clicks for easier connections.
            node_rect = self.nodes[node].GetRect().Inflate(7, 7)
            if mouse_rect.Intersects(node_rect):
                return self.nodes[node]

        # Refresh the nodegraph
        self.UpdateNodeGraph()

    def MouseInAddNodeBtn(self, pnt):
        mouse_rect = wx.Rect(pnt[0], pnt[1], 1, 1)
        
        addnodebtn_rect = self.addnode_btn.GetRect()
        if mouse_rect.Intersects(addnodebtn_rect):
            return True
        else:
            return False

    def DeleteNodes(self):
        """ Delete the currently selected nodes. This will refuse
        to delete the Output Composite node though, for obvious reasons.
        """
        for node in self.sel_nodes:
            if node.IsOutputNode() != True:
                self.DeleteNode(node)
            else:
                # In the case that this is an output node, we
                # want to deselect it, not delete it. :)
                node.SetSelected(False)
        self.sel_nodes = []

        if (self.active_node != None and
            self.active_node.IsOutputNode() != True):
            self.DeleteNode(self.active_node)
            self.active_node = None

        # Update the properties panel so that the deleted
        # nodes' properties are not still shown!
        self.SendNodeSelectEvent()

        self.UpdateNodeGraph()

    def DuplicateNode(self, node):
        """ Duplicates the given ``Node`` object with its properties.
        :param node: the ``Node`` object to duplicate
        :returns: the duplicate ``Node`` object
        """
        if node.IsOutputNode() is not True:
            duplicate_node = self.AddNode(node.GetIdname(), location="CURSOR")

            # TODO: Assign the same properties to the duplicate node object

            self.UpdateNodeGraph()
            return duplicate_node

    def AddNode(self, idname, nodeid=None, pos=(0, 0), location="POSITION"):
        if nodeid is None:
            node_id = uuid.uuid4().hex
        else:
            node_id = nodeid
        node = self.node_registry[idname](self, node_id)
        node.Init(idname)
        self.nodes[node.id] = node

        if location == "CURSOR":
            node.pos = self.CalcMouseCoords(self.ScreenToClient(wx.GetMousePosition()))
        else:
            node.pos = wx.Point(pos[0], pos[1])
        return node

    def IsInputNode(self, node) -> bool:
        if node.GetCategory() in self.input_nodes_categories:
            return True
        else:
            return False

    def SocketHasWire(self, dst_socket):
        for wire in self.wires:
            if wire.dstsocket == dst_socket:
                return True
        return False

    def SetNodeAsPreview(self, current_node):
        """ Connect the given node to the the output node in place
        of any other connections.
        :param current_node: NodeBase subclass object
        """
        output_node = self.GetOutputNode()

        # We assume there is only one input (for now)
        output_node_socket = output_node.GetSockets()[0]

        # Disconnect any previous connections
        wires = output_node_socket.GetWires()
        for wire in wires:
            if wire.dstsocket == output_node_socket:
                dst = wire.dstsocket
                src = wire.srcsocket
                self.DisconnectNodes(src, dst)

        # Connect the newly selected node to the output
        for socket in current_node.GetSockets():
            if socket.direction == SOCKET_OUTPUT:
                src_socket = socket

        self.ConnectNodes(src_socket, output_node_socket)

    def GetOutputNode(self):
        """ Return the output node object. """
        for node_id in self.nodes:
            node = self.nodes[node_id]
            if node.IsOutputNode():
                return node

    def GetNodeByTypeId(self, type_id):
        """ Return a node object based on the node type identifier.
        :param type_id: node type identifier
        :returns: NodeBase subclass object
        """
        for node_id in self.GetNodes():
            if self.nodes[node_id].idname == type_id:
                return self.nodes[node_id]

    def ConnectNodes(self, src_socket, dst_socket):
        pt1 = src_socket.node.pos + src_socket.pos
        pt2 = dst_socket.node.pos + dst_socket.pos
        direction = src_socket.direction

        wire = NodeWire(src_socket, pt1, pt2, src_socket, dst_socket,
                        direction, self.wire_curvature)
        wire.srcnode = src_socket.node
        wire.dstnode = dst_socket.node
        wire._srcsocket = src_socket
        wire._dstsocket = dst_socket

        self.wires.append(wire)

        src_socket.wires.append(wire)
        dst_socket.wires.append(wire)

        dst_socket.node.EditConnection(dst_socket.idname, self.nodes[src_socket.node.id], src_socket.idname)
        self.SendNodeConnectEvent()

    def DisconnectNodes(self, src_socket, dst_socket):
        for wire in self.wires:
            if wire.srcsocket is src_socket and wire.dstsocket is dst_socket:
                self.wires.remove(wire)
                wire.dstsocket.node.EditConnection(wire.dstsocket.idname, None, None)

        self.SendNodeDisconnectEvent()

    def DeleteNode(self, node):
        for socket in node.GetSockets():
            for wire in socket.GetWires():
                # Clean up any wires that are
                # connected to this node.
                self.DisconnectNodes(wire.srcsocket, wire.dstsocket)
        del self.nodes[node.id]
        self.UpdateNodeGraph()

    def SendNodeSelectEvent(self):
        wx.PostEvent(self,
                     gsnodegraph_nodeselect_cmd_event(id=self.GetId(),
                     value=self.active_node))

    def SendNodeConnectEvent(self):
        wx.PostEvent(self,
                     gsnodegraph_nodeconnect_cmd_event(id=self.GetId(),
                     value=self.active_node))

    def SendNodeDisconnectEvent(self):
        wx.PostEvent(self,
                     gsnodegraph_nodedisconnect_cmd_event(id=self.GetId(),
                     value=self.active_node))

    def SendMouseZoomEvent(self):
        wx.PostEvent(self,
                     gsnodegraph_mousezoom_cmd_event(id=self.GetId(),
                     value=self.zoom))

    def SendAddNodeBtnEvent(self):
        wx.PostEvent(self,
                     gsnodegraph_addnodebtn_cmd_event(id=self.GetId(),
                     value=self.active_node))

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

        cx = int((right + left) / 2)
        cy = int((top + bottom) / 2)
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
