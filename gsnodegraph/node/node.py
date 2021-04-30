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

from .socket import NodeSocket
from ..constants import *


class NodeBase(object):
    def __init__(self, nodegraph, _id):
        self._nodegraph = nodegraph
        self._id = _id
        self._pos = wx.Point(0, 0)
        self._size = wx.Size(NODE_DEFAULT_WIDTH, NODE_DEFAULT_HEIGHT)
        self._selected = False
        self._active = False

        self._sockets = []
        self._parameters = {}

        self._isoutput = False
        self._label = ""
        self._category = "INPUT"
        self._headercolor = "#fff"

    def _Init(self):
        self.InitSockets()
        self.InitHeaderColor()
        
    @property
    def nodegraph(self):
        return self._nodegraph

    @nodegraph.setter
    def nodegraph(self, nodegraph):
        self._nodegraph = nodegraph

    @property
    def pos(self):
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

    def AddSocket(self, label, color, direction):
        self.ArrangeSockets()

    def HitTest(self, pos):
        # Handle socket hittest
        for socket in self._sockets:
            if socket.HitTest(pos - self.pos):
                return socket

    def IsOutputNode(self):
        return self._isoutput

    def InitHeaderColor(self):
        self._headercolor = NODE_CATEGORY_COLORS[self._category]

    def InitSockets(self):
        x, y, w, h = self.GetRect()

        _id = wx.NewIdRef()

        sockets = []

        ins = []
        outs = []

        for param in self._parameters:
            ins.append((param, "RENDERIMAGE"))

        if self.IsOutputNode() != True:
            outs = [('Output', "RENDERIMAGE")]

        x, y = self.pos
        w, h = self.size
        for i, p in enumerate(outs + ins):
            socket_type = SOCKET_INPUT  # Socket type IN
            x = 0  # socket margin
            if (p[0], p[1]) in outs:
                x = w - x + 1
                socket_type = SOCKET_OUTPUT  # Socket type OUT

            # We keep track of where the last socket is placed
            lastcoord = 60 + 30 * i

            socket = NodeSocket(p[0], p[1], self)
            socket.direction = socket_type
            socket.pos = wx.Point(x, 40 + (19 * i))
            sockets.append(socket)

        self._sockets = sockets

        # Adjust the size of the node to fit 
        # the amount of sockets the node has.
        self.size[1] = lastcoord


    def GetPosition(self):
        return self.pos

    def SetPosition(self, x, y):
        self.pos = wx.Point(x, y)

    def GetSize(self):
        return (self.size[0], self.size[1])

    def GetRect(self):
        return wx.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    def IsSelected(self):
        return self.selected

    def SetSelected(self, selected=True):
        self.selected = selected

    def IsActive(self):
        return self.active

    def SetActive(self, active=True):
        self.active = active

    def Draw(self, dc):
        x, y = self.GetPosition()
        w, h = self.GetSize()

        # Node body and border
        if self.IsSelected() or self.IsActive():
            dc.SetPen(wx.Pen(wx.Colour(255, 255, 255, 255), 2))
        else:
            dc.SetPen(wx.Pen(wx.Colour(31, 31, 31, 255), 2))
        dc.SetBrush(wx.Brush(wx.Colour(65, 65, 65, 255)))
        dc.DrawRoundedRectangle(x, y, w, h, 4)

        # Node header and title
        dc.SetPen(wx.Pen(wx.TRANSPARENT_PEN))
        dc.SetBrush(wx.Brush(wx.Colour(self._headercolor)))
        dc.DrawRoundedRectangle(x+1, y+1, w-3, 20, 3)
        dc.DrawRectangle(x+1, y+10, w-3, 12)

        fnt = self.nodegraph.GetFont()
        dc.SetFont(fnt)
        dc.SetTextForeground(wx.Colour('#fff'))
        dc.DrawText(self._label, x+10, y+1)

        for socket in self._sockets:
            socket.Draw(dc)
