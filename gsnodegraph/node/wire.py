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

from ..constants import WIRE_NORMAL_COLOR, WIRE_ACTIVE_COLOR


class NodeWire(object):
    """ Wire for showing a connection between two nodes. """
    def __init__(self, parent, pnt1, pnt2, srcsocket, dstsocket, direction, curvature):
        self.parent = parent
        self.pnt1 = pnt1
        self.pnt2 = pnt2
        self.srcsocket = srcsocket
        self.dstsocket = dstsocket
        self.curvature = curvature
        self.direction = direction

        self.srcnode = None
        self.dstnode = None
        self.active = False

    def SetCurvature(self, curvature) -> None:
        """ Set the curvature of the wire. """
        self.curvature = curvature

    def GetRect(self) -> wx.Rect:
        """ Get the bounding box rect of the wire. """
        min_x = min(self.pnt1[0], self.pnt2[0])
        min_y = min(self.pnt1[1], self.pnt2[1])
        size = self.pnt2 - self.pnt1
        rect = wx.Rect(min_x - 10, min_y, abs(size[0]) + 20, abs(size[1]))
        return rect.Inflate(2, 2)

    def Draw(self, dc) -> None:
        """ Draw the node wire. """
        # Direction of wire
        sign = 1
        if self.direction == 0:
            sign = -1

        # Curvature of the wire
        curvature = int(self.curvature * 2)

        # Wire color
        if self.active is True:
            color = WIRE_ACTIVE_COLOR
        else:
            color = WIRE_NORMAL_COLOR
        dc.SetPen(wx.Pen(wx.Colour(color), 3))

        # If the wire has curvature, use a spline
        if self.curvature > 0:
            pnts = []
            pnts.append(self.pnt1)
            pnts.append(self.pnt1 + wx.Point(curvature * sign, 0))
            pnts.append(self.pnt2 - wx.Point(curvature * sign, 0))
            pnts.append(self.pnt2)

            dc.DrawSpline(pnts)

        else:
            # Otherwise, use a line
            dc.DrawLine(self.pnt1[0], self.pnt1[1], self.pnt2[0], self.pnt2[1])
