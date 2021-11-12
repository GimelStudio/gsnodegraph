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
import uuid

from gsnodegraph.assets.bitmaps import ICON_IMAGE

from .socket import NodeSocket
from ..constants import (NODE_DEFAULT_WIDTH, NODE_DEFAULT_HEIGHT,
                         NODE_HEADER_MUTED_COLOR, NODE_HEADER_CATEGORY_COLORS,
                         SOCKET_INPUT, SOCKET_OUTPUT, NODE_THUMB_PADDING, NODE_Y_PADDING,
                         NODE_NORMAL_COLOR, NODE_MUTED_COLOR, NODE_THUMB_BORDER_COLOR,
                         NODE_BORDER_NORMAL_COLOR, NODE_BORDER_SELECTED_COLOR)
from ..assets import (ICON_BRUSH_CHECKERBOARD, ICON_IMAGE)


class NodeBase(object):
    def __init__(self, nodegraph, _id):
        self._nodegraph = nodegraph
        self._id = _id
        self._idname = None
        self._pos = wx.Point(0, 0)
        self._size = wx.Size(NODE_DEFAULT_WIDTH, NODE_DEFAULT_HEIGHT)

        self._expanded = False
        self._selected = False
        self._active = False
        self._muted = False

        self._sockets = []
        self._parameters = {}

        self._isoutput = False
        self._label = ""
        self._category = "DEFAULT"
        self._headercolor = wx.Colour(NODE_HEADER_CATEGORY_COLORS["DEFAULT"])

        self._thumbnail = self._CreateEmptyBitmap()
        self._expandicon_bmp = ICON_IMAGE.GetBitmap()
        self._checkerboard_bmp = ICON_BRUSH_CHECKERBOARD.GetBitmap()

    def _Init(self, idname) -> None:
        self.InitSockets()
        self.InitHeaderColor()
        self.InitSize()
        self.SetIdName(idname)

    def _CreateEmptyBitmap(self) -> wx.Bitmap:
        img = wx.Image(120, 120)
        img.SetMaskColour(0,0,0)
        img.InitAlpha()
        return img.ConvertToBitmap()

    @property
    def nodegraph(self):
        return self._nodegraph

    @nodegraph.setter
    def nodegraph(self, nodegraph):
        self._nodegraph = nodegraph

    @property
    def pos(self) -> wx.Point:
        return self._pos

    @pos.setter
    def pos(self, pos: wx.Point) -> None:
        self._pos = pos

    @property
    def size(self) -> wx.Size:
        return self._size

    @size.setter
    def size(self, size: wx.Size) -> None:
        self._size = size

    @property
    def selected(self) -> bool:
        return self._selected

    @selected.setter
    def selected(self, selected: bool) -> None:
        self._selected = selected

    @property
    def active(self) -> bool:
        return self._active

    @active.setter
    def active(self, active: bool) -> None:
        self._active = active

    @property
    def muted(self) -> bool:
        return self._muted

    @muted.setter
    def muted(self, muted: bool) -> None:
        self._muted = muted

    @property
    def expanded(self) -> bool:
        return self._expanded

    @expanded.setter
    def expanded(self, expanded: bool) -> None:
        self._expanded = expanded

    def NodeOutputDatatype(self) -> str:
        return "RGBAIMAGE"

    def AddSocket(self, label, color, direction) -> None:
        self.ArrangeSockets()

    def HitTest(self, pos: wx.Point) -> None:
        # Handle expanding the node to show thumbnail hittest
        if self.HasThumbnail():
            icon_rect = self._expandicon_rect.Inflate(8, 8)
            mouse_rect = wx.Rect(pos[0], pos[1], 2, 2)
            if mouse_rect.Intersects(icon_rect) and wx.GetMouseState().LeftIsDown():
                self.ToggleExpand()

        # Handle socket hittest
        for socket in self._sockets:
            if socket.HitTest(pos - self.pos):
                return socket

    def EditParameter(self, idname, value):
        pass

    def InitHeaderColor(self) -> None:
        self._headercolor = wx.Colour(NODE_HEADER_CATEGORY_COLORS[self.GetCategory()])

    def InitSockets(self) -> None:
        sockets = []
        ins = []
        outs = []

        # Create a list of input sockets with the format:
        # [(label, idname, datatype), ...]
        for param_id in self._parameters:
            param = self._parameters[param_id]
            ins.append((param.label, param.idname, param.datatype))

        if self.IsOutputNode() is not True:
            # TODO: eventually, we want to have the ability to edit the label
            data_type = self.NodeOutputDatatype()
            if data_type == "RGBAIMAGE":
                idname = "output_image"
                label = "Image"
            else:
                idname = "output_value"
                label = "Value"
            outs = [(label, idname, data_type)]

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
            self._lastsocketpos = 60 + 12 * i

            # Create the node sockets
            socket = NodeSocket(label=p[0], idname=p[1], datatype=p[2],
                                node=self, direction=socket_type)
            socket.pos = wx.Point(x, 40 + (19 * i))
            sockets.append(socket)

        self._sockets = sockets

    def InitSize(self) -> None:
        # Calculate the normal size of the node to fit
        # the amount of sockets the node has. The expanded size
        # is calculated to be the normal size plus the image thumbnail size.
        calc_height = self._lastsocketpos + self._thumbnail.Height + NODE_THUMB_PADDING * 2
        self._expandedsize = wx.Size(NODE_DEFAULT_WIDTH, calc_height)

        self._normalsize = wx.Size(NODE_DEFAULT_WIDTH,
                                   self._lastsocketpos+(NODE_Y_PADDING*2))

        # Set the initial node size
        if self.IsExpanded():
            self.SetSize(self._expandedsize)
        else:
            self.SetSize(self._normalsize)

    def HasThumbnail(self) -> bool:
        if self.NodeOutputDatatype() == "RGBAIMAGE":
            return True
        else:
            return False

    def IsOutputNode(self) -> bool:
        """ Override method to set whether the node is the output or not. """
        return self._isoutput

    def GetLabel(self) -> str:
        """ Override method to set the node label. """
        return self._label

    def GetCategory(self) -> str:
        """ Override method to set the node category. """
        return self._category

    def GetIdname(self) -> str:
        return self._idname

    def SetIdName(self, idname) -> None:
        self._idname = idname

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
        self.SetSize(self._normalsize)

    def IsExpanded(self) -> bool:
        return self.expanded

    def SetExpanded(self, expanded=True) -> None:
        self.expanded = expanded

    def ToggleExpand(self) -> None:
        if self.HasThumbnail():
            if self.IsExpanded() is True:
                self.SetExpanded(False)
                self.SetSize(self._normalsize)
            elif self.IsExpanded() is False:
                self.SetExpanded(True)
                self.SetSize(self._expandedsize)

    def GetSockets(self) -> list:
        return self._sockets

    def SetThumbnail(self, thumb) -> None:
        if self.HasThumbnail():
            self._thumbnail = thumb
            self.UpdateExpandSize()

    def UpdateExpandSize(self) -> None:
        calc_height = self._lastsocketpos + self._thumbnail.Height + NODE_THUMB_PADDING * 2
        self._expandedsize = wx.Size(NODE_DEFAULT_WIDTH, calc_height)
        self.SetSize(self._expandedsize)

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
            header_color = wx.Colour(self._headercolor).ChangeLightness(70)
            bottom_color = wx.Colour(self._headercolor).ChangeLightness(55)
        dc.SetBrush(wx.Brush(header_color))
        dc.DrawRoundedRectangle(x+1, y+1, w-2, 24, 3)

        # Bottom border of the node header (to cover up the rounded bottom)
        dc.SetBrush(wx.Brush(bottom_color))
        dc.DrawRectangle(x+1, y+23, w-2, 2)

        # Node name label
        if self.IsMuted():
            color = wx.Colour('#fff').ChangeLightness(60)
        else:
            color = wx.Colour('#fff').ChangeLightness(85)
        dc.SetTextForeground(color)
        dc.DrawText(self.GetLabel(), x+10, y+1)

        # Node sockets
        [socket.Draw(dc) for socket in self._sockets]

        # Expand node thumbnail icon
        if self.HasThumbnail() == True and self.IsMuted() != True:
            self._expandicon_rect = wx.Rect(x+NODE_DEFAULT_WIDTH-28, y+4, 16, 16)
            dc.DrawBitmap(self._expandicon_bmp, self._expandicon_rect[0],
                        self._expandicon_rect[1], True)

        # Thumbnail
        if self.IsExpanded() and self.HasThumbnail():
            # Calculate the coords for the placement of the thumbnail
            thumb_rect = wx.Rect((x+NODE_THUMB_PADDING/2),
                                  y+self._lastsocketpos+(NODE_Y_PADDING*2),
                                  NODE_DEFAULT_WIDTH-NODE_THUMB_PADDING,
                                  self._thumbnail.Height)

            # Draw thumbnail border and background
            dc.SetPen(wx.Pen(wx.Colour(NODE_THUMB_BORDER_COLOR), 1))
            dc.SetBrush(wx.Brush(self._checkerboard_bmp))
            dc.DrawRectangle(thumb_rect)

            # Draw the thumbnail
            dc.DrawBitmap(self._thumbnail, thumb_rect[0], thumb_rect[1], True)
