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

from .utils.z_matrix import ZMatrix


class NodeGraphBase(wx.ScrolledCanvas):
    def __init__(self, parent, *args, **kwds):
        self.matrix = ZMatrix()
        self.identity = ZMatrix()
        self.matrix.Reset()
        self.identity.Reset()
        self.previous_position = None
        self._buffer = None

        self._middle_pnt = None
        self._last_pnt = None

        self._bbox_rect = None
        self._bbox_start = None

        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.ScrolledCanvas.__init__(self, parent, *args, **kwds)

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda x: None)
        self.Bind(wx.EVT_SIZE, self.OnSize)
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

    def OnMotion(self, event):
        pnt = event.GetPosition()
        winpnt = self.CalcMouseCoords(pnt)


        # Draw box selection bbox
        if event.LeftIsDown() is True and self._src_node is None and self._bbox_start != None:

            self._bbox_rect = wx.Rect(
                topLeft=self._bbox_start,
                bottomRight=winpnt
            )
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
                dpnt = self._src_node.pos + winpnt - self._last_pnt
                self._src_node.pos = dpnt

                self._last_pnt = winpnt


            elif self._tmp_wire != None:
                # Set the wire to be active when it is being edited.
                self._tmp_wire.active = True

                if winpnt != None:
                    self._tmp_wire.pnt2 = winpnt

            self.UpdateDrawing()


    @staticmethod
    def DrawNodeWire(dc, wire, pnt1=None, pnt2=None):
        if pnt1 != None:
            wire.pnt1 = pnt1
        if pnt2 != None:
            wire.pnt2 = pnt2
        wire.Draw(dc)

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
        pass

    def OnDrawScene(self, dc):
        pass

    def OnDrawInterface(self, dc):
        pass

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
