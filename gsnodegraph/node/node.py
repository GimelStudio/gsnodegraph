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

import wx

from gsnodegraph.assets.bitmaps import ICON_IMAGE

from .socket import NodeSocket
from .utils import TruncateText
from ..constants import (NODE_DEFAULT_WIDTH, NODE_DEFAULT_HEIGHT,
                         NODE_HEADER_MUTED_COLOR,
                         SOCKET_INPUT, SOCKET_OUTPUT, NODE_THUMB_PADDING, NODE_Y_PADDING,
                         NODE_NORMAL_COLOR, NODE_MUTED_COLOR, NODE_THUMB_BORDER_COLOR,
                         NODE_BORDER_NORMAL_COLOR, NODE_BORDER_SELECTED_COLOR)
from ..assets import (ICON_BRUSH_CHECKERBOARD, ICON_IMAGE)


class NodeBase(object):
    def __init__(self, nodegraph, id):
        self.nodegraph = nodegraph
        self.id = id
        self.idname = None
        self.pos = wx.Point(0, 0)
        self.size = wx.Size(NODE_DEFAULT_WIDTH, NODE_DEFAULT_HEIGHT)
        self.header_color = wx.Colour("#242424")

        self.expanded = False
        self.selected = False
        self.active = False
        self.muted = False
        self.is_output = False

        self.sockets = []
        self.properties = {}
        self.outputs = {}

        self.label = ""
        self.category = None
        self.has_thumbnail = False

        self.thumbnail = self.CreateEmptyBitmap()
        self.expandicon_bmp = ICON_IMAGE.GetBitmap()
        self.checkerboard_bmp = ICON_BRUSH_CHECKERBOARD.GetBitmap()

    @property
    def NodeGraph(self):
        return self.nodegraph

    @property
    def NodeDatatypes(self):
        return self.nodegraph.node_datatypes

    @property
    def NodeCategories(self):
        return self.nodegraph.node_categories

    @property
    def NodeImageDatatype(self):
        return self.nodegraph.image_datatype

    def Init(self, idname) -> None:
        self.InitSockets()
        self.InitHeaderColor()
        self.InitSize()
        self.InitLabel()
        self.SetIdName(idname)

    def CreateEmptyBitmap(self) -> wx.Bitmap:
        img = wx.Image(120, 120)
        img.SetMaskColour(0,0,0)
        img.InitAlpha()
        return img.ConvertToBitmap()

    def AddSocket(self, label, color, direction) -> None:
        self.ArrangeSockets()

    def HitTest(self, pos: wx.Point) -> None:
        # Handle expanding the node to show thumbnail hittest
        if self.HasThumbnail() and wx.GetMouseState().LeftIsDown():
            icon_rect = self.expandicon_rect.Inflate(10, 10)
            mouse_rect = wx.Rect(pos[0], pos[1], 2, 2)
            if mouse_rect.Intersects(icon_rect):
                self.ToggleExpand()

        # Handle socket hittest
        for socket in self.sockets:
            if socket.HitTest(pos - self.pos):
                return socket

    def EditConnection(self, name, binding, socket):
        pass

    def InitHeaderColor(self) -> None:
        self.header_color = wx.Colour(self.NodeCategories[self.GetCategory()])

    def InitSockets(self) -> None:
        sockets = []
        ins = []
        outs = []

        # Create a list of input and output sockets with the format:
        # [(label, idname, datatype), ...]
        for prop_id in self.properties:
            prop = self.properties[prop_id]
            if prop.exposed and prop.can_be_exposed:
                ins.append((prop.label, prop.idname, prop.datatype))

        if self.IsOutputNode() is not True:
            for output_id in self.outputs:
                output = self.outputs[output_id]
                outs.append((output.label, output.idname, output.datatype))
                # If there is an image datatype then we know there 
                # should be a thumbnail for this node.
                if output.datatype == self.NodeImageDatatype:
                    self.has_thumbnail = True

        x, y, w, h = self.GetRect()
        x, y = self.pos
        w, h = self.size

        for i, p in enumerate(outs + ins):
            socket_type = SOCKET_INPUT  # Socket type IN
            x = 0  # socket margin
            if (p[0], p[1], p[2]) in outs:
                x = w - x - 1
                socket_type = SOCKET_OUTPUT  # Socket type OUT

            # We keep track of where the last socket is placed
            self.lastsocket_pos = 60 + 14 * i

            # Create the node sockets
            socket = NodeSocket(label=p[0], idname=p[1], datatype=p[2],
                                node=self, direction=socket_type)
            socket.pos = wx.Point(x, int(45 + (19 * i)))
            socket.SetColor(self.NodeDatatypes[socket.datatype])
            sockets.append(socket)

        self.sockets = sockets

    def InitSize(self) -> None:
        # Calculate the normal size of the node to fit
        # the amount of sockets the node has. The expanded size
        # is calculated to be the normal size plus the image thumbnail size.
        calc_height = self.lastsocket_pos + self.thumbnail.Height + NODE_THUMB_PADDING * 2
        self.expanded_size = wx.Size(NODE_DEFAULT_WIDTH, calc_height)

        self.normal_size = wx.Size(NODE_DEFAULT_WIDTH,
                                   self.lastsocket_pos+(NODE_Y_PADDING*2))

        # Set the initial node size
        if self.IsExpanded():
            self.SetSize(self.expanded_size)
        else:
            self.SetSize(self.normal_size)

    def InitLabel(self):
        # Number of chars to truncate from the label is based on 
        # whether there is a toggle icon taking up space on this node.
        if self.HasThumbnail() == True:
            chars = 15
        else:
            chars = 20
        self.label = TruncateText(self.GetLabel(), chars)

    def HasThumbnail(self) -> bool:
        return self.has_thumbnail

    def IsOutputNode(self) -> bool:
        """ Override method to set whether the node is the output or not. """
        return self.is_output

    def GetLabel(self) -> str:
        """ Get the node label. """
        return self.label

    def GetCategory(self) -> str:
        """ Override method to set the node category. """
        return self.category

    def GetIdname(self) -> str:
        return self.idname

    def SetIdName(self, idname) -> None:
        self.idname = idname

    def GetPosition(self) -> wx.Point:
        return self.pos

    def SetPosition(self, x: int, y: int) -> None:
        self.pos = wx.Point(x, y)

    def GetSize(self) -> wx.Size:
        return (self.size[0], self.size[1])

    def SetSize(self, size: wx.Size) -> None:
        self.size = size

    def GetRect(self) -> wx.Rect:
        return wx.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    def IsSelected(self) -> bool:
        return self.selected

    def SetSelected(self, selected=True) -> None:
        self.selected = selected

    def IsActive(self) -> bool:
        return self.active

    def SetActive(self, active=True) -> None:
        self.active = active

    def IsMuted(self) -> bool:
        return self.muted

    def SetMuted(self, muted=True) -> None:
        self.muted = muted
        self.SetExpanded(False)
        self.SetSize(self.normal_size)

    def IsExpanded(self) -> bool:
        return self.expanded

    def SetExpanded(self, expanded=True) -> None:
        self.expanded = expanded

    def ToggleExpand(self) -> None:
        if self.HasThumbnail():
            if self.IsExpanded() is True:
                self.SetExpanded(False)
                self.SetSize(self.normal_size)
            elif self.IsExpanded() is False:
                self.SetExpanded(True)
                self.SetSize(self.expanded_size)

    def GetSockets(self) -> list:
        return self.sockets

    def SetThumbnail(self, thumb) -> None:
        if self.HasThumbnail():
            self.thumbnail = thumb
            self.UpdateExpandSize()

    def UpdateExpandSize(self) -> None:
        calc_height = self.lastsocket_pos + self.thumbnail.Height + NODE_THUMB_PADDING * 2
        self.expanded_size = wx.Size(NODE_DEFAULT_WIDTH, calc_height)
        self.SetSize(self.expanded_size)

    def FindSocket(self, idname):
        """ Return the node socket with the given name.
        :param idname: the socket idname as a string
        :returns: Socket object
        """
        for socket in self.GetSockets():
            if socket.idname == idname:
                return socket

    def Draw(self, dc) -> None:
        x, y = self.GetPosition()
        w, h = self.GetSize()

        # Node body and border
        if self.IsSelected() or self.IsActive():
            border_color = NODE_BORDER_SELECTED_COLOR
        else:
            border_color = NODE_BORDER_NORMAL_COLOR
        if self.IsMuted():
            node_color = NODE_MUTED_COLOR
        else:
            node_color = NODE_NORMAL_COLOR
        dc.SetPen(wx.Pen(wx.Colour(border_color), 1))
        dc.SetBrush(wx.Brush(wx.Colour(node_color)))
        dc.DrawRoundedRectangle(x, y, w, h, 3)

        # Node header
        dc.SetPen(wx.Pen(wx.TRANSPARENT_PEN))
        if self.IsMuted():
            header_color = wx.Colour(NODE_HEADER_MUTED_COLOR)
            bottom_color = wx.Colour(NODE_HEADER_MUTED_COLOR).ChangeLightness(80)
        else:
            header_color = wx.Colour(self.header_color).ChangeLightness(70)
            bottom_color = wx.Colour(self.header_color).ChangeLightness(55)
        dc.SetBrush(wx.Brush(header_color))
        dc.DrawRoundedRectangle(x+1, y+1, w-2, 25, 3)

        # Bottom border of the node header (to cover up the rounded bottom)
        dc.SetBrush(wx.Brush(bottom_color))
        dc.DrawRectangle(x+1, y+24, w-2, 2)

        # Node name label
        if self.IsMuted():
            color = wx.Colour('#fff').ChangeLightness(60)
        else:
            color = wx.Colour('#fff').ChangeLightness(85)
        dc.SetTextForeground(color)
        dc.DrawText(self.GetLabel(), x+10, y+1)

        # Node sockets
        [socket.Draw(dc) for socket in self.sockets]

        # Expand node thumbnail icon
        if self.HasThumbnail() == True and self.IsMuted() != True:
            self.expandicon_rect = wx.Rect(x+NODE_DEFAULT_WIDTH-28, y+5, 16, 16)
            dc.DrawBitmap(self.expandicon_bmp, self.expandicon_rect[0],
                        self.expandicon_rect[1], True)

        # Thumbnail
        if self.IsExpanded() and self.HasThumbnail():
            # Calculate the coords for the placement of the thumbnail
            thumb_rect = wx.Rect(int(x+NODE_THUMB_PADDING/2),
                                 int(y+self.lastsocket_pos+(NODE_Y_PADDING*2)),
                                 NODE_DEFAULT_WIDTH-NODE_THUMB_PADDING,
                                 self.thumbnail.Height)

            # Draw thumbnail border and background
            dc.SetPen(wx.Pen(wx.Colour(NODE_THUMB_BORDER_COLOR), 1))
            dc.SetBrush(wx.Brush(self.checkerboard_bmp))
            dc.DrawRectangle(thumb_rect)

            # Draw the thumbnail
            dc.DrawBitmap(self.thumbnail, thumb_rect[0], thumb_rect[1], True)
