# -*- coding: Utf-8 -*

import pygame

class Focusable:

    MODE_MOUSE = "mouse"
    MODE_KEY = "keyboard"
    MODE_JOY = "joystick"
    MODE = MODE_MOUSE
    ON_LEFT = "on_left"
    ON_RIGHT = "on_right"
    ON_TOP = "on_top"
    ON_BOTTOM = "on_bottom"

    def __init__(self, master, highlight_color=(0, 0, 255), highlight_thickness=2):
        self.__focus = False
        self.__side = dict.fromkeys((Focusable.ON_LEFT, Focusable.ON_RIGHT, Focusable.ON_TOP, Focusable.ON_BOTTOM))
        self.__take_focus = True
        self.__from_master = False
        self.__master = master
        self.highlight_color = highlight_color
        self.highlight_thickness = highlight_thickness

    @property
    def focus(self) -> bool:
        return self.__focus

    @focus.setter
    def focus(self, status: bool) -> None:
        status = bool(status)
        focus = self.__focus
        self.__focus = status
        if status is True:
            if not focus:
                self.on_focus_set()
        else:
            if focus:
                self.on_focus_leave()

    def get_obj_on_side(self, side: str):
        return self.__side.get(side, None)

    def set_obj_on_side(self, on_top=None, on_bottom=None, on_left=None, on_right=None) -> None:
        for side, obj in ((Focusable.ON_TOP, on_top), (Focusable.ON_BOTTOM, on_bottom), (Focusable.ON_LEFT, on_left), (Focusable.ON_RIGHT, on_right)):
            if side in self.__side and isinstance(obj, Focusable):
                self.__side[side] = obj

    def remove_obj_on_side(self, *sides: str):
        for side in sides:
            if side in self.__side:
                self.__side[side] = None

    def focus_drawing(self, surface: pygame.Surface):
        if not self.has_focus():
            return
        if hasattr(self, "rect"):
            outline = getattr(self, "outline", self.highlight_thickness)
            if outline <= 0:
                outline = self.highlight_thickness
            if outline > 0:
                pygame.draw.rect(surface, self.highlight_color, getattr(self, "rect"), width=outline)

    def has_focus(self) -> bool:
        return self.__focus

    def take_focus(self, status=None) -> bool:
        if status is not None:
            self.__take_focus = bool(status)
        shown = True
        if hasattr(self, "is_shown") and callable(self.is_shown) and not self.is_shown():
            shown = False
        return bool(self.__take_focus and shown)

    def focus_set(self) -> None:
        if not self.has_focus():
            self.__master.set_focus(self)

    def focus_leave(self) -> None:
        if self.has_focus():
            self.__master.set_focus(None)

    def focus_update(self):
        pass

    def on_focus_set(self):
        pass

    def on_focus_leave(self):
        pass