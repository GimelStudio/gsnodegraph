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

import math
import wx

from ..constants import (SOCKET_INPUT, SOCKET_DATATYPES,
                         SOCKET_HIT_RADIUS, SOCKET_RADIUS)


class NodeSocket(object):
    """ Node socket showing the datatypes and flow of the node relative to
    the graph. Wires are dropped into the socket to connect nodes. """
    def __init__(self, label, idname, datatype, node, direction):
        self._label = label
        self._node = node
        self._pos = wx.Point(0, 0)
        self._color = "#fff"
        self._direction = direction
        self._datatype = datatype
        self._wires = []

        self._idname = idname

        self._InitSocket()

    def _InitSocket(self):
        """ Routine methods for initilizing the socket. """
        self.SetColorByDataType(self.datatype)
        self.SetTopLevelDC()

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, label):
        self._label = label

    @property
    def node(self):
        return self._node

    @node.setter
    def node(self, node):
        self._node = node

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, pos):
        self._pos = pos

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, color):
        self._color = color

    @property
    def direction(self):
        return self._direction

    @direction.setter
    def direction(self, direction):
        self._direction = direction

    @property
    def datatype(self):
        return self._datatype

    @datatype.setter
    def datatype(self, datatype):
        self._datatype = datatype

    def GetWires(self):
        return self._wires

    def CurrentSocketPos(self):
        """ Return the current coords of the node socket. """
        return self.pos + self.node.pos

    def SetColorByDataType(self, datatype):
        """ Set the color based on the datatype. """
        self.color = SOCKET_DATATYPES[datatype]

    def SetTopLevelDC(self):
        self.tdc = wx.WindowDC(wx.GetApp().GetTopWindow())

    def HitTest(self, pos):
        """ Returns True if the node socket was hit. """
        pnt = pos - self.pos
        distance = math.sqrt(math.pow(pnt.x, 2) + math.pow(pnt.y, 2))

        # socket hit radius
        if math.fabs(distance) < SOCKET_HIT_RADIUS:
            return True

    def Draw(self, dc):
        """ Draw the node socket. """
        final = self.CurrentSocketPos()

        # Set the socket color
        dc.SetPen(wx.Pen(wx.Colour("#2B2B2B"), 1))
        dc.SetBrush(wx.Brush(wx.Colour(self.color), wx.SOLID))

        # Draw the socket
        dc.DrawCircle(final.x, final.y, SOCKET_RADIUS)

        w, h = self.tdc.GetTextExtent(self.label)

        # Socket label margin
        if self.direction == SOCKET_INPUT:
            x = final.x + 12
        else:
            x = final.x - w - 12

        # Draw the label
        dc.DrawText(self.label, x, final.y - h / 2)
