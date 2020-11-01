# -*- coding:Utf-8 -*

import random
import socket
from math import sin, cos
from typing import Tuple, Sequence, Dict, Any
import pygame
from constants import RESOURCES, NB_LINES_BOXES, NB_COLUMNS_BOXES, BOX_SIZE
from my_pygame import Window
from my_pygame import Image, ImageButton, Button, RectangleShape, Text
from my_pygame import DrawableListHorizontal, DrawableListVertical
from my_pygame import GREEN, GREEN_DARK, GREEN_LIGHT, WHITE, YELLOW, RED, TRANSPARENT
from my_pygame import CountDown
from my_pygame.vector import Vector2
from player import Player
from game import Gameplay

class BoxSetup(Button):
    def __init__(self, master, size: Tuple[int, int], pos: Tuple[int, int]):
        params = {
            "size": size,
            "bg": TRANSPARENT,
            "hover_bg": GREEN,
            "disabled_bg": TRANSPARENT,
            "disabled_hover_bg": RED,
            "outline_color": WHITE,
            "highlight_color": WHITE,
        }
        Button.__init__(self, master=master, **params)
        self.disable_key_joy()
        self.disable_mouse()
        self.pos = pos
        self.ship = None

class ShipSetup(Image):

    VERTICAL = "vertical"
    HORIZONTAL = "horizontal"

    def __init__(self, master, ship_name: str, ship_size: int):
        Image.__init__(self, RESOURCES.IMG[ship_name])
        self.name = ship_name
        self.__orient = ShipSetup.VERTICAL
        self.master = master
        self.ship_size = ship_size
        self.orient = ShipSetup.HORIZONTAL
        self.set_width(self.ship_size * BOX_SIZE[0])
        self.clicked = False
        self.on_move = False
        self.mouse_offset = (0, 0)
        self.default_center = (0, 0)
        self.center_before_click = (0, 0)
        self.__boxes_covered = list()
        self.master.bind_event(pygame.MOUSEBUTTONDOWN, self.select_event)
        self.master.bind_event(pygame.MOUSEBUTTONUP, self.unselect_event)
        self.master.bind_event(pygame.MOUSEMOTION, self.move_event)

    @property
    def orient(self) -> str:
        return self.__orient

    @orient.setter
    def orient(self, orient: str) -> None:
        if orient in (ShipSetup.VERTICAL, ShipSetup.HORIZONTAL) and orient != self.__orient:
            if orient == ShipSetup.HORIZONTAL:
                self.rotate(90)
            else:
                self.rotate(-90)
            self.__orient = orient

    @property
    def on_map(self) -> bool:
        return bool(len(self.boxes_covered))

    @property
    def boxes_covered(self) -> Sequence[BoxSetup]:
        return self.__boxes_covered

    @boxes_covered.setter
    def boxes_covered(self, boxes: Sequence[BoxSetup]) -> None:
        self.clear()
        self.__boxes_covered = boxes
        for box in self.__boxes_covered:
            box.ship = self

    def clear(self) -> None:
        for box in self.boxes_covered:
            box.ship = None
        self.boxes_covered.clear()

    def select_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.clicked = True
            self.center_before_click = self.center
            self.pos_offset = (event.pos[0] - self.left, event.pos[1] - self.top)
            self.move_ip(0, -3)

    def unselect_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONUP and self.clicked:
            if (self.on_move and not self.place_ship_on_map()) or (not self.on_move and not self.rotate_ship()):
                self.animate_move(self.master, 1, center=self.center_before_click)
            self.clicked = self.on_move = False
            self.master.remove_boxes_highlight()

    def move_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEMOTION and self.clicked:
            self.on_move = True
            topleft = list(event.pos)
            for i in range(2):
                topleft[i] -= self.pos_offset[i]
            self.move(topleft=tuple(topleft))
            self.master.highlight_boxes(self)

    def place_ship_on_map(self, boxes=None) -> bool:
        if boxes is None:
            boxes = self.master.get_valid_highlighted_boxes()
        if not boxes:
            return False
        self.__place_ship(boxes)
        return True

    def rotate_ship(self) -> bool:
        if not self.on_map:
            return False
        first_box = self.boxes_covered[0]
        line, column = first_box.pos
        new_cases = list()
        new_orient = ShipSetup.HORIZONTAL if self.orient == ShipSetup.VERTICAL else ShipSetup.VERTICAL
        for i in range(1, self.ship_size):
            box = self.master.get_box(
                line + i if new_orient == ShipSetup.VERTICAL else line,
                column + i if new_orient == ShipSetup.HORIZONTAL else column
            )
            if box is None or (box.ship is not None and box.ship != self):
                return False
            new_cases.append(box)
        self.orient = new_orient
        self.__place_ship([first_box] + new_cases)
        return True

    def __place_ship(self, boxes: Sequence[BoxSetup]):
        left = min(boxes, key=lambda box: box.left).left
        top = min(boxes, key=lambda box: box.top).top
        right = max(boxes, key=lambda box: box.right).right
        bottom = max(boxes, key=lambda box: box.bottom).bottom
        width = right - left
        height = bottom - top
        rect = pygame.Rect(left, top, width, height)
        self.center = rect.center
        self.boxes_covered = boxes

class EnemyQuitGame(Window):
    def __init__(self, master):
        Window.__init__(self, master=master, bg_music=master.bg_music)
        self.bg = RectangleShape(self.width, self.height, (0, 0, 0, 170))
        self.frame = RectangleShape(0.5 * self.width, 0.5 * self.height, GREEN_DARK, outline=2)
        self.text_finish = Text("The enemy has left\nthe game", font=(None, 70))
        params_for_all_buttons = {
            "font": (None, 40),
            "bg": GREEN,
            "hover_bg": GREEN_LIGHT,
            "active_bg": GREEN_DARK,
            "highlight_color": YELLOW
        }
        self.button_return_to_menu = Button(self, "Return to menu", callback=self.stop, **params_for_all_buttons)
        self.bind_key(pygame.K_ESCAPE, lambda event: self.stop())

    def place_objects(self):
        self.frame.center = self.center
        self.text_finish.center = self.frame.center
        self.button_return_to_menu.move(bottom=self.frame.bottom - 20, centerx=self.frame.centerx)

class WaitEnemy(Window):
    def __init__(self, master):
        Window.__init__(self, master=master, bg_music=master.bg_music)
        self.master = master
        self.bg = RectangleShape(self.width, self.height, (0, 0, 0, 170))
        self.frame = RectangleShape(0.5 * self.width, 0.5 * self.height, GREEN_DARK, outline=2)
        self.text = Text("Waiting for enemy", font=(None, 70))

    def update(self):
        if self.master.player.recv("ready"):
            self.stop()
        elif self.master.player.recv("quit"):
            self.stop()
            EnemyQuitGame(self.master).mainloop()
            self.master.stop()

    def place_objects(self):
        self.frame.center = self.center
        self.text.center = self.frame.center

class NavySetup(Window):
    def __init__(self, player_socket: socket.socket, player_id: int):
        Window.__init__(self, bg_color=(0, 200, 255), bg_music=RESOURCES.MUSIC["setup"])
        self.player = Player(player_socket, player_id)
        self.count_down = CountDown(self, 60, "Time left: {seconds}", font=(None, 70), color=WHITE)
        self.start_count_down = lambda: self.count_down.start(at_end=self.timeout) if self.player.connected() else None
        self.start_count_down()
        params_for_all_buttons = {
            "bg": GREEN,
            "hover_bg": GREEN_LIGHT,
            "active_bg": GREEN_DARK,
            "highlight_color": YELLOW
        }
        self.button_back = ImageButton(self, RESOURCES.IMG["arrow_blue"], **params_for_all_buttons, rotate=180, size=50, callback=self.stop)
        self.navy_grid = DrawableListVertical(offset=0, bg_color=(0, 157, 255))
        for i in range(NB_LINES_BOXES):
            box_line = DrawableListHorizontal(offset=0)
            for j in range(NB_COLUMNS_BOXES):
                box_line.add(BoxSetup(self, size=BOX_SIZE, pos=(i, j)))
            self.navy_grid.add(box_line)
        self.ships_list = DrawableListVertical(offset=70, justify="left")
        ships = {
            "carrier":      {"size": 4, "nb": 1, "offset": 0},
            "battleship":   {"size": 3, "nb": 2, "offset": 30},
            "destroyer":    {"size": 2, "nb": 3, "offset": 30},
            "patroal_boat": {"size": 1, "nb": 4, "offset": 70}
        }
        for ship_name, ship_infos in ships.items():
            ship_line = DrawableListHorizontal(offset=ship_infos["offset"])
            for _ in range(ship_infos["nb"]):
                ship_line.add(ShipSetup(self, ship_name, ship_infos["size"]))
            self.ships_list.add(ship_line)
        option_size = 50
        self.button_restart = ImageButton(self, RESOURCES.IMG["reload_blue"], size=option_size, show_bg=True, callback=self.reinit_all_ships, **params_for_all_buttons)
        self.button_random = ImageButton(self, RESOURCES.IMG["random"], size=option_size, show_bg=True, callback=self.shuffle, **params_for_all_buttons)
        self.button_play = Button(self, "Play", font=(None, 40), callback=self.play, state=Button.DISABLED, **params_for_all_buttons)

    @property
    def ships(self) -> Sequence[ShipSetup]:
        return self.ships_list.drawable

    @property
    def boxes(self) -> Sequence[BoxSetup]:
        return self.navy_grid.drawable

    def on_start_loop(self):
        self.player.start()

    def on_quit(self):
        self.player.stop()

    def place_objects(self) -> None:
        self.button_back.move(x=20, y=20)
        self.count_down.move(top=20, right=self.right - 20)
        self.navy_grid.move(x=20, centery=self.centery)
        self.ships_list.move(left=self.navy_grid.right + 100, top=self.navy_grid.top + 30)
        self.button_restart.move(left=self.navy_grid.right + 20, bottom=self.navy_grid.bottom)
        self.button_random.move(left=self.button_restart.right + 20, bottom=self.navy_grid.bottom)
        self.button_play.move(right=self.right - 20, bottom=self.bottom - 20)
        for ship in self.ships:
            ship.default_center = ship.center

    def update(self):
        self.button_play.state = Button.NORMAL if all(ship.on_map for ship in self.ships) else Button.DISABLED
        if self.player.recv("quit"):
            self.count_down.stop()
            EnemyQuitGame(self).mainloop()
            self.stop()

    def create_setup(self) -> Sequence[Dict[str, Dict[str, Any]]]:
        setup = list()
        for ship in self.ships:
            setup.append({
                "name": ship.name,
                "orient": ship.orient,
                "boxes": [box.pos for box in ship.boxes_covered]
            })
        return setup

    def timeout(self):
        if any(not ship.on_map for ship in self.ships):
            self.shuffle()
        self.play()

    def play(self):
        if not all(ship.on_map for ship in self.ships):
            return
        if not self.player.connected():
            ai_navy_setup = NavySetup(None, 2)
            ai_navy_setup.shuffle()
            ai_setup = ai_navy_setup.create_setup()
        else:
            ai_setup = None
            self.count_down.stop()
            self.player.send("ready")
            WaitEnemy(self).mainloop()
            if not self.loop:
                return
        gameplay = Gameplay(self.player, self.create_setup(), ai_setup=ai_setup)
        gameplay.mainloop()
        if gameplay.restart:
            self.reinit_all_ships()
            self.start_count_down()
        else:
            self.stop()

    def reinit_all_ships(self):
        for ship in self.ships:
            ship.center = ship.default_center
            ship.orient = ShipSetup.HORIZONTAL
            ship.clear()

    def get_box(self, line: int, column: float) -> BoxSetup:
        return {box.pos: box for box in self.boxes}.get((line, column))

    def remove_boxes_highlight(self):
        for box in self.boxes:
            box.hover = False
            box.state = Button.NORMAL

    def get_valid_highlighted_boxes(self) -> Sequence[BoxSetup]:
        return list(filter(lambda box: box.hover and box.state == Button.NORMAL, self.boxes))

    def highlight_boxes(self, ship: ShipSetup) -> None:
        boxes = list()
        for box in self.boxes:
            self.highlight_one_box(ship, box, len(boxes))
            if box.hover is True:
                boxes.append(box)
        if len(boxes) != ship.ship_size or any(not self.valid_box(ship, box) for box in boxes):
            for box in boxes:
                box.state = Button.DISABLED

    def highlight_one_box(self, ship: ShipSetup, box: BoxSetup, nb_boxes_covered: int) -> None:
        box.hover = False
        box.state = Button.NORMAL
        if nb_boxes_covered == ship.ship_size:
            return
        if ship.orient == ShipSetup.HORIZONTAL:
            if (box.top <= ship.centery <= box.bottom) is False:
                return
            if ship.left > box.centerx or ship.right < box.centerx:
                return
        else:
            if (box.left <= ship.centerx <= box.right) is False:
                return
            if ship.top > box.centery or ship.bottom < box.centery:
                return
        box.hover = True

    def valid_box(self, ship: ShipSetup, box: BoxSetup) -> bool:
        line, column = box.pos
        offsets = [
            (-1, -1),
            (0, -1),
            (1, -1),
            (-1, 0),
            (0, 0),
            (1, 0),
            (-1, 1),
            (0, 1),
            (1, 1)
        ]
        for u, v in offsets:
            box = self.get_box(line + u, column + v)
            if box is None:
                continue
            if box.ship is not None and box.ship != ship:
                return False
        return True

    def shuffle(self) -> None:
        self.reinit_all_ships()
        for ship in self.ships:
            self.set_random_position_for_ship(ship)

    def set_random_position_for_ship(self, ship: ShipSetup) -> None:
        ship.orient = random.choice([ShipSetup.HORIZONTAL, ShipSetup.VERTICAL])
        first_box = random.choice(self.get_available_boxes(ship))
        boxes = [first_box]
        for i in range(1, ship.ship_size):
            u = first_box.pos[0] + i if ship.orient == ShipSetup.VERTICAL else first_box.pos[0]
            v = first_box.pos[1] + i if ship.orient == ShipSetup.HORIZONTAL else first_box.pos[1]
            boxes.append(self.get_box(u, v))
        ship.place_ship_on_map(boxes)

    def get_available_boxes(self, ship: ShipSetup):
        available_boxes = list()
        for box in self.boxes:
            if not self.valid_box(ship, box):
                continue
            line, column = box.pos
            valid = True
            for i in range(1, ship.ship_size):
                u = line + i if ship.orient == ShipSetup.VERTICAL else line
                v = column + i if ship.orient == ShipSetup.HORIZONTAL else column
                b = self.get_box(u, v)
                if b is None or (not self.valid_box(ship, b)):
                    valid = False
                    break
            if valid:
                available_boxes.append(box)
        return available_boxes