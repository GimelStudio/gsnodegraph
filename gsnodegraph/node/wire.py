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


class NodeWire(object):
    """ Wire for showing a connection between two nodes. """
    def __init__(self, parent, pnt1, pnt2, srcsocket, dstsocket, direction):
        #self._id = wx.NewIdRef()
        self._parent = parent
        self._pnt1 = pnt1
        self._pnt2 = pnt2
        self._srcsocket = srcsocket
        self._dstsocket = dstsocket
        self._srcnode = None
        self._dstnode = None

        self.active = False
        self.curvature = 8
        self._direction = direction

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, parent):
        self._parent = parent

    @property
    def pnt1(self):
        return self._pnt1

    @pnt1.setter
    def pnt1(self, pnt1):
        self._pnt1 = pnt1

    @property
    def pnt2(self):
        return self._pnt2

    @pnt2.setter
    def pnt2(self, pnt2):
        self._pnt2 = pnt2

    @property
    def srcsocket(self):
        return self._srcsocket

    @srcsocket.setter
    def srcsocket(self, srcsocket):
        self._srcsocket = srcsocket

    @property
    def dstsocket(self):
        return self._dstsocket

    @dstsocket.setter
    def dstsocket(self, dstsocket):
        self._dstsocket = dstsocket

    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, active):
        self._active = active

    @property
    def curvature(self):
        return self._curvature

    @curvature.setter
    def curvature(self, curvature):
        self._curvature = curvature

    @property
    def direction(self):
        return self._direction

    @direction.setter
    def direction(self, direction):
        self._direction = direction

    def GetRect(self):
        min_x = min(self.pnt1[0], self.pnt2[0])
        min_y = min(self.pnt1[1], self.pnt2[1])
        size = self.pnt2 - self.pnt1
        rect = wx.Rect(min_x - 10, min_y, abs(size[0]) + 20, abs(size[1]))
        return rect.Inflate(2, 2)

    def Draw(self, dc):
        
        # Direction of wire
        sign = 1
        if self.direction == 0:
            sign = -1

        # Curvature of the wire
        curvature = int(self.curvature * 2)

        # If the wire has curvature, use a spline
        if self.curvature > 0:

            # Draw wire
            pnts = []
            pnts.append(self.pnt1)
            pnts.append(self.pnt1 + wx.Point(curvature * sign, 0))
            pnts.append(self.pnt2 - wx.Point(curvature * sign, 0))
            pnts.append(self.pnt2)

            if self.active is True:
                dc.SetPen(wx.Pen(wx.Colour("#ECECEC"), 3))
            else:
                dc.SetPen(wx.Pen(wx.Colour("#808080"), 3))
            dc.DrawSpline(pnts)

        else:
            # Otherwise, use a line
            if self.active is True:
                dc.SetPen(wx.Pen(wx.Colour("#ECECEC"), 3))
            else:
                dc.SetPen(wx.Pen(wx.Colour(wx.Colour("#808080")), 3))
            dc.DrawLine(self.pnt1[0], self.pnt1[1], self.pnt2[0], self.pnt2[1])
