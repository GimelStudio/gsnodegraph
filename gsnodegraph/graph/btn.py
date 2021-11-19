
import wx

from gsnodegraph.constants import (BTN_NORMAL_COLOR, BTN_CLICKED_COLOR, 
                                   BTN_FOCUSED_COLOR)
from gsnodegraph.assets import ICON_ADD_NODE


class AddNodeBtn(object):
    def __init__(self, parent):
        self.parent = parent
        self.bitmap = ICON_ADD_NODE.GetBitmap()
        self.rect = wx.Rect(0, 0, self.bitmap.Width, self.bitmap.Height)

        self.focused = False
        self.clicked = False

    def GetRect(self):
        return self.rect

    def SetRect(self, rect):
        self.rect = rect

    def GetHeight(self):
        return self.rect[3]

    def GetBitmap(self):
        return self.bitmap

    def IsFocused(self):
        return self.focused

    def SetFocused(self, focused):
        self.focused = focused

    def IsClicked(self):
        return self.clicked

    def SetClicked(self, clicked):
        self.clicked = clicked

    def Draw(self, dc, pnt):
        rect = wx.Rect(pnt[0], pnt[1], self.bitmap.Width, self.bitmap.Height)
        self.SetRect(rect)

        if self.IsClicked():
            btn_color = BTN_CLICKED_COLOR
        elif self.IsFocused():
            btn_color = BTN_FOCUSED_COLOR
        else:
            btn_color = BTN_NORMAL_COLOR

        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.SetBrush(wx.Brush(wx.Colour(btn_color)))
        dc.DrawRoundedRectangle(self.GetRect(), 4)
        dc.DrawBitmap(self.GetBitmap(), pnt[0], pnt[1], useMask=False)