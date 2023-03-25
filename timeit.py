import traceback
import typing
import time

from kivy.app import App
from kivy.lang import Builder

from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.properties import ColorProperty

from kivy.clock import Clock
from kivy.config import Config
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.resources import resource_add_path

import os
import sys

os.environ["SDL_MOUSE_FOCUS_CLICKTHROUGH"] = '1'

# pyinstaller stuff
if hasattr(sys, '_MEIPASS'):
    resource_add_path(os.path.join(sys._MEIPASS))

Config.set('input', 'mouse', 'mouse,multitouch_on_demand')  # red dots begone
Window.size = (800, 480)

REGULAR_FONT = 'DejaVuSansMono'

FONT_DIR = 'resources/fonts/dejavu-sans-mono'
LabelBase.register(name=REGULAR_FONT,
                   fn_regular=f'{FONT_DIR}/DejaVuSansMono.ttf',
                   fn_italic=f'{FONT_DIR}/DejaVuSansMono-Oblique.ttf',
                   fn_bold=f'{FONT_DIR}/DejaVuSansMono-Bold.ttf',
                   fn_bolditalic=f'{FONT_DIR}/DejaVuSansMono-BoldOblique.ttf',)
TRANSPARENT_PNG = 'resources/imgs/transparent.png'

WINDOW_TITLE = "TimeIt"

OK_TEXT = "Ok"
CANCEL_TEXT = "Cancel"

RESET_TEXT = "Reset"
EDIT_TEXT = "Edit"
EDIT_DRAG_FROM_TEXT = "From"
EDIT_DRAG_TO_TEXT = "[ To ]"
EDIT_DRAG_TARGET_TEXT = "[    ]"

DRAG_SYMBOL_TEXT = "↕"
REMOVE_SYMBOL_TEXT = "✖"

PAUSE_TEXT = "Pause"
PAUSED_TEXT = "Paused"
RESUME_TEXT = "Resume"

ADD_ACTIVITY_TEXT = "Add Activity"
NEW_ACTIVITY_TEXT = "Activity {0}"

EDIT_ACTIVITY_TEXT = "Edit {0}"
TRANSFER_TIME_TEXT = "Transfer to {0}"
UNTITLED_ACTIVITY_TEXT = "Untitled Activity"
PLUS_MINUS_MINUTES_TEXT = "+/- Minutes"

ZERO_TIME = "0:00:00"


FG_COLOR = tuple(x/255. for x in (128, 222, 234))
FG_COLOR_DIM = tuple(x * 0.333 for x in FG_COLOR)

def set_fg_color(rgb):
    global FG_COLOR, FG_COLOR_DIM
    FG_COLOR = rgb
    FG_COLOR_DIM = tuple(x * 0.333 for x in FG_COLOR)


SECONDARY_COLOR = tuple(x/255. for x in (240, 240, 240))
BG_COLOR = tuple(x/255. for x in (0, 0, 0))
DISABLED_FG_COLOR = tuple(x/255. for x in (130, 130, 130))
ACCENT_COLOR = tuple(x/255. for x in (245, 245, 66))
CANCEL_COLOR = (1, 0, 0)


# 0=Red, 30=Orange, 60=Yellow, 90=Yellow-Green, 120=Green
# 150=Sea Foam, 180=Cyan, 210=Light Blue, 240=Dark Blue,
# 270=Purple, 300=Magenta, 330=Pink, 360=Red
RAINBOW_HUE_OFFSET = 0  # color at 12am

RAINBOW_PERIOD_HOURS = 12  # 12 hour cycle

TITLE_FONT_SIZE = 64
REGULAR_FONT_SIZE = 20
SPACING = 4  # sp
ROW_HEIGHT = int(2 * REGULAR_FONT_SIZE)

global_popup_var = []
last_mouse_pos = (0, 0)


Builder.load_string(f"""
<Label>:
    font_name: '{REGULAR_FONT}'
    font_size: '{REGULAR_FONT_SIZE}sp'
    
<LineBorderWidget>:
    background_color: {BG_COLOR}

    canvas.after:
        Color:
            rgba: self.line_color
        Line:
            width: 1
            close: False
            points: self.pos[0],                    self.pos[1] + 1, \
                    self.pos[0] + self.size[0] - 1, self.pos[1] + 1, \
                    self.pos[0] + self.size[0] - 1, self.pos[1] + self.size[1] - 1, \
                    self.pos[0],                    self.pos[1] + self.size[1] - 1, \
                    self.pos[0],                    self.pos[1]
    
<MyTextInput>:
    padding_y: [self.height / 2.0 - (self.line_height / 2.0) * len(self._lines), 0]
    foreground_color: {SECONDARY_COLOR}  
    hint_text_color: {DISABLED_FG_COLOR}
    cursor_color: {SECONDARY_COLOR}
    
<Button>:
    font_name: '{REGULAR_FONT}'
    font_size: '{REGULAR_FONT_SIZE}sp'
    
<MyToggleButton>:
    canvas.before:
        Color:
            rgba: self.background_color
        Rectangle:
            pos: self.pos[0] + 1, self.pos[1] + 1
            size: self.size[0] - 2, self.size[1] - 2
    canvas.after:
        Color:
            rgba: self.line_color
        Line:
            width: 1
            close: True
            cap: 'square'
            joint: 'miter'
            points: self.pos[0] + 1,                self.pos[1] + 1, \
                    self.pos[0] + self.size[0] - 1, self.pos[1] + 1, \
                    self.pos[0] + self.size[0] - 1, self.pos[1] + self.size[1] - 1, \
                    self.pos[0] + 1,                self.pos[1] + self.size[1] - 1
                    
<Boxes>:
    id: _parent
    scroller: _scroller
    boxes: _boxes 
    title_img: _title_img
    pause_btn: _pause_btn
    add_btn: _add_btn
    
    BoxLayout:
        orientation: 'vertical'
        padding: 8
            
        Image:
            id: _title_img
            source: 'resources/imgs/logo.png'
            size_hint: (1, None)
            size: (self.texture_size[0], self.texture_size[1] * 1.25)
        
        ScrollView:
            id: _scroller
            effect_cls: 'ScrollEffect'
            do_scroll_x: False
            do_scroll_y: True
            scroll_type: ['bars']
            bar_width: 4
        
            BoxLayout: 
                id: _boxes
                orientation: 'vertical'
            
        BoxLayout:
            orientation: 'horizontal'
            size_hint: (1, None)
            height: '{ROW_HEIGHT + SPACING}sp'
            padding: (0, '{SPACING}sp', 0, 0)
            MyToggleButton:
                id: _pause_btn
                font_size: '{REGULAR_FONT_SIZE}sp'
                size_hint: (None, 1)
                width: '{ROW_HEIGHT * 4}sp'
            FloatLayout:
            MyButton:
                id: _add_btn
                text: '{ADD_ACTIVITY_TEXT}'
                on_press: _parent.add_row()
                font_size: '{REGULAR_FONT_SIZE}sp'
                size_hint: (None, 1)
                width: '{ROW_HEIGHT * 4 + SPACING * 2}sp'
""")


class RowData:

    def __init__(self, row_widget, timer_btn, textbox, edit_btn, remove_btn):
        self.row_widget = row_widget
        self.timer_btn = timer_btn
        self.textbox = textbox
        self.edit_btn = edit_btn
        self.remove_btn = remove_btn
        self.elapsed_time = 0

    def add_time_ms(self, millis):
        self.set_time_ms(self.elapsed_time + millis)

    def set_time_ms(self, millis):
        self.elapsed_time = max(0, millis)
        self.update_timer_btn_label()
        self.update_colors()

    def get_time_ms(self):
        return self.elapsed_time

    def get_time_str(self):
        secs = self.elapsed_time // 1000
        mins = secs // 60
        hours = mins // 60
        return f"{hours}:{str(mins % 60).zfill(2)}:{str(secs % 60).zfill(2)}"

    def update_timer_btn_label(self):
        self.timer_btn.text = self.get_time_str()

    def update_colors(self):
        for widget in self.row_widget.children:
            if isinstance(widget, ColorUpdatable):
                widget.update_colors()

class ColorUpdatable:

    def calc_text_color(self):
        return SECONDARY_COLOR

    def calc_line_color(self):
        return SECONDARY_COLOR

    def calc_fill_color(self):
        return BG_COLOR

    def update_colors(self):
        pass


class HoverBehavior(Widget):

    def __init__(self, *args, in_popup=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.in_popup = in_popup
        self.hovering = False
        Window.bind(mouse_pos=self._handle_mouse_move)

    def _handle_mouse_move(self, window, pos):
        global last_mouse_pos
        last_mouse_pos = pos

        in_widget = False
        if self.get_root_window() is None:
            in_widget = False
        elif self.collide_point(*self.to_widget(*pos)):
            in_widget = True

        popup_active = len(global_popup_var) > 0
        if self.in_popup ^ popup_active:
            in_widget = False

        if in_widget != self.hovering:
            self.hovering = in_widget
            self.on_enter(pos) if self.hovering else self.on_leave(pos)

    def on_enter(self, pos):
        pass

    def on_leave(self, pos):
        pass


class LineBorderWidget(Widget, ColorUpdatable):
    line_color = ColorProperty(DISABLED_FG_COLOR)

    def calc_line_color(self):
        return DISABLED_FG_COLOR

    def update_colors(self):
        self.line_color = self.calc_line_color()


class MyButton(Button, HoverBehavior, LineBorderWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hover_cursor = None

    def on_enter(self, *args):
        if self.hover_cursor is not None:
            Window.set_system_cursor(self.hover_cursor)
        self.update_colors()

    def on_leave(self, *args):
        if self.hover_cursor is not None:
            Window.set_system_cursor('arrow')
        self.update_colors()

    def calc_line_color(self):
        if self.disabled or not self.hovering:
            return DISABLED_FG_COLOR
        else:
            return FG_COLOR

    def update_colors(self):
        super().update_colors()
        self.color = self.calc_text_color()
        self.background_color = self.calc_fill_color()


class MyTextInput(TextInput, HoverBehavior, LineBorderWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_enter(self, *args):
        Window.set_system_cursor('ibeam')
        self.update_colors()

    def on_leave(self, *args):
        Window.set_system_cursor('arrow')
        self.update_colors()

    def calc_line_color(self):
        if self.focused:
            return SECONDARY_COLOR
        else:
            return DISABLED_FG_COLOR


class MyToggleButton(ToggleButton, HoverBehavior, ColorUpdatable):

    line_color = ColorProperty(DISABLED_FG_COLOR)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = TRANSPARENT_PNG
        self.background_active = TRANSPARENT_PNG
        self.background_down = TRANSPARENT_PNG
        self.background_disabled_normal = TRANSPARENT_PNG
        self.background_disabled_down = TRANSPARENT_PNG

        self.update_colors()

    def on_enter(self, *args):
        self.update_colors()

    def on_leave(self, *args):
        self.update_colors()

    def calc_text_color(self):
        if self.disabled:
            return DISABLED_FG_COLOR
        elif self.state == "down":
            return BG_COLOR
        else:
            return SECONDARY_COLOR

    def calc_fill_color(self):
        if self.disabled or self.state != "down":
            return BG_COLOR
        else:
            return FG_COLOR

    def calc_line_color(self):
        if self.hovering and not self.disabled:
            return FG_COLOR_DIM if self.state == 'down' else FG_COLOR
        else:
            return FG_COLOR if self.state == 'down' else DISABLED_FG_COLOR

    def update_colors(self):
        self.line_color = self.calc_line_color()
        self.color = self.calc_text_color()
        self.background_color = self.calc_fill_color()


class Boxes(FloatLayout):

    def __init__(self, parent, **kwargs):
        super(Boxes, self).__init__(**kwargs)
        self._parent = parent
        self._btn_group = 'group0'
        self.boxes.size_hint = (1, None)
        self.boxes.spacing = f'{SPACING}sp'

        self.activity_id_counter = 0
        self.active_row_id_before_pause = [-1]

        self.floating_row = -1
        self.floating_row_widget = None
        self.dragging_edit_btn_row = -1

        self._cached_cursor_col = -1

        self.active_row_id = -1
        self.row_lookup: typing.Dict[int, RowData] = {}
        self.row_ordering = []
        for _ in range(5):
            self.add_row()

        self._build_pause_btn()
        self._build_add_btn()

        Window.bind(on_motion=lambda _, etype, me: self.handle_mouse_motion(etype, me))
        Window.bind(on_touch_up=lambda _, me: self.handle_mouse_release(me))

        self.last_time_seen_ms = int(time.time() * 1000)
        self.timer = Clock.schedule_interval(self.inc_time, 0.5)

    def handle_mouse_motion(self, etype, me):
        if self.floating_row >= 0:
            Clock.schedule_once(lambda dt: self.update_floating_row(me.spos))
        if self.dragging_edit_btn_row >= 0:
            self.update_all_edit_buttons()

    def handle_mouse_release(self, me):
        if self.floating_row >= 0:
            self.release_floating_row(me)
        if self.dragging_edit_btn_row >= 0:
            self.release_edit_button(me)

    def start_dragging_row(self, i, me):
        self.floating_row = i
        Clock.schedule_once(lambda dt: self.update_floating_row(me.spos))

    def update_floating_row(self, mouse_sxy):
        if self.floating_row >= 0:
            hover_order_idx = self.get_row_order_idx_at(mouse_sxy, constrain=True)

            new_ordering = []
            for row_id in self.row_ordering:
                if len(new_ordering) == hover_order_idx:
                    new_ordering.append(-2)
                if row_id >= 0 and row_id != self.floating_row:
                    new_ordering.append(row_id)
            if len(new_ordering) == hover_order_idx:
                new_ordering.append(-2)
            self.reorder_rows(new_ordering, update_hints=False)

            if self.floating_row_widget is None:
                self.floating_row_widget = BoxLayout(size_hint=(None, None),
                                                     size=(self.size[0] - SPACING * 2, ROW_HEIGHT))
                self.floating_row_widget.add_widget(self.row_lookup[self.floating_row].row_widget)
                self.add_widget(self.floating_row_widget)

            self.floating_row_widget.pos = (SPACING, Window.size[1] * mouse_sxy[1] - ROW_HEIGHT / 2)

    def release_floating_row(self, me):
        if self.floating_row >= 0:
            if self.floating_row_widget is not None:
                for child in list(self.floating_row_widget.children):
                    self.floating_row_widget.remove_widget(child)
                self.remove_widget(self.floating_row_widget)
                self.floating_row_widget = None

            new_ordering = [(row_id if row_id >= 0 else self.floating_row) for row_id in self.row_ordering]
            self.reorder_rows(new_ordering, update_hints=True)
            self.floating_row = -1

    def start_dragging_edit_button(self, i):
        self.dragging_edit_btn_row = i

    def update_all_edit_buttons(self):
        for row_id in self.row_lookup.keys():
            row = self.row_lookup[row_id]
            row.edit_btn.update_colors()

            if self.dragging_edit_btn_row < 0:
                row.edit_btn.text = EDIT_TEXT
            elif row.edit_btn.hovering:
                if row_id == self.dragging_edit_btn_row:
                    row.edit_btn.text = EDIT_TEXT  # No xfer happening
                else:
                    row.edit_btn.text = EDIT_DRAG_TO_TEXT
            else:
                if row_id == self.dragging_edit_btn_row:
                    row.edit_btn.text = EDIT_DRAG_FROM_TEXT
                else:
                    row.edit_btn.text = EDIT_DRAG_TARGET_TEXT  # Drag Target

    def release_edit_button(self, me):
        if self.dragging_edit_btn_row >= 0:
            mouse_xy = (int(Window.size[0] * me.spos[0]),
                        int(Window.size[1] * me.spos[1]))
            for row_id in self.row_lookup.keys():
                row = self.row_lookup[row_id]
                if row.edit_btn.collide_point(*row.edit_btn.to_widget(*mouse_xy)):
                    if row_id != self.dragging_edit_btn_row:
                        Clock.schedule_once(lambda dt, _dest_id=row_id, _src_id=self.dragging_edit_btn_row:
                                            self.create_edit_popup(_dest_id, _src_id))
                    break
            self.dragging_edit_btn_row = -1
            self.update_all_edit_buttons()

    def get_row_order_idx_at(self, scr_xy, constrain=True):
        scr_xy_px = (int(scr_xy[0] * Window.size[0]), int(scr_xy[1] * Window.size[1]))
        box_xy = self.boxes.to_window(*self.boxes.pos)  # TODO check units on these
        box_size = self.boxes.size
        pos_rel_to_box = (scr_xy_px[0] - box_xy[0],
                          box_xy[1] + box_size[1] - scr_xy_px[1])
        row_order_idx = pos_rel_to_box[1] // (ROW_HEIGHT + SPACING)
        if constrain:
            row_order_idx = max(0, min(row_order_idx, len(self.row_ordering) - 1))

        return row_order_idx

    def reorder_rows(self, new_ordering, update_hints=True):
        old_scroll_y = self.scroller.scroll_y
        old_widgets = list(self.boxes.children)
        for widget in old_widgets:
            self.boxes.remove_widget(widget)

        self.row_ordering = new_ordering
        for i in self.row_ordering:
            if i in self.row_lookup:
                self.boxes.add_widget(self.row_lookup[i].row_widget)
            else:
                self.boxes.add_widget(Widget(size_hint=(1, None), height=f'{ROW_HEIGHT}sp'))

        if update_hints:
            self._update_row_hint_texts()

        self._update_boxes_height()
        self.scroller.scroll_y = old_scroll_y

    def _update_row_hint_texts(self):
        hint_text_cnt = 1
        for i in self.row_ordering:
            if i in self.row_lookup:
                self.row_lookup[i].textbox.hint_text = NEW_ACTIVITY_TEXT.format(hint_text_cnt)
            hint_text_cnt += 1

    def inc_time(self, _):
        cur_time_ms = int(time.time() * 1000)
        dt = cur_time_ms - self.last_time_seen_ms
        self.last_time_seen_ms = cur_time_ms

        if self.active_row_id in self.row_lookup:
            row_data = self.row_lookup[self.active_row_id]
            row_data.add_time_ms(dt)

        self._update_foreground_color()
        self._update_window_caption()

    def _update_window_caption(self):
        if self.active_row_id in self.row_lookup:
            row_data = self.row_lookup[self.active_row_id]
            caption_msg = f"{row_data.textbox.text or UNTITLED_ACTIVITY_TEXT} ~ {row_data.get_time_str()}"
        else:
            caption_msg = PAUSED_TEXT
        self._parent.title = f"{WINDOW_TITLE} [{caption_msg}]"

    def _update_foreground_color(self):
        set_fg_color(get_color_for_time())
        self.update_all_colors()

    def get_row_data(self, row_i=None) -> typing.Optional[RowData]:
        if row_i is None:
            row_i = self.active_row_id
        if row_i in self.row_lookup:
            return self.row_lookup[row_i]
        else:
            return None

    def _update_boxes_height(self):
        n = len(self.boxes.children)
        self.boxes.height = f"{ROW_HEIGHT * n + int(str(self.boxes.spacing)[:-2]) * (n - 1)}sp"

        # XXX otherwise the rows will float in the middle of the scrollpane until you jibble them
        if self.scroller.height > self.boxes.height:
            self.scroller.scroll_y = 1

    def simulate_mouse_hover_after_layout_change(self, widgets):
        if last_mouse_pos is not None:
            for widget in widgets:
                if isinstance(widget, HoverBehavior):
                    if widget.collide_point(*widget.to_widget(*last_mouse_pos)):
                        widget.hovering = True
                        widget.on_enter(last_mouse_pos)
                        if isinstance(widget, ColorUpdatable):
                            widget.update_colors()
                        break

    def remove_row(self, i, simulate_hover_evt=False):
        if i in self.row_lookup:
            old_boxes_height = self.boxes.height
            old_scroll_y = self.scroller.scroll_y

            row_widget = self.row_lookup[i].row_widget
            self.boxes.remove_widget(row_widget)
            self._update_boxes_height()

            old_idx = self.row_ordering.index(i)

            del self.row_lookup[i]
            self.row_ordering.remove(i)

            if self.active_row_id_before_pause[0] == i:
                self.active_row_id_before_pause[0] = -1
                self.update_pause_btn(mode='pause', disabled=True)

            if self.active_row_id == i:
                self.active_row_id = -1
                self.update_row_colors(self.active_row_id)
                self.update_pause_btn(mode='pause', disabled=True)

            new_boxes_height = self.boxes.height
            if 0 < self.scroller.scroll_y < 1:
                # if possible, adjust the scroll_y to keep remaining items' onscreen positions the same
                view_h = self.scroller.height
                new_scroll_y = 1 - (old_boxes_height - view_h) / (new_boxes_height - view_h) * (1 - old_scroll_y)
                self.scroller.scroll_y = min(1, max(0, new_scroll_y))

            if simulate_hover_evt:
                # highlight the new button that ends up underneath the mouse
                all_rm_btns = [data.remove_btn for data in self.row_lookup.values()]
                Clock.schedule_once(lambda _: self.simulate_mouse_hover_after_layout_change(all_rm_btns))

            self.update_title_img_color()
            self._update_row_hint_texts()

    def clear_row_time(self, i):
        if i in self.row_lookup:
            self.row_lookup[i].set_time_ms(0)

            if i == self.active_row_id:
                self.row_lookup[i].timer_btn.state = "normal"
                self.active_row_id = -1
                self.update_pause_btn(mode='pause', disabled=True)
            elif i == self.active_row_id_before_pause[0]:
                self.active_row_id_before_pause[0] = -1
                self.update_pause_btn(mode='pause', disabled=True)

            self.update_row_colors(i)

    def update_row_colors(self, i):
        if i in self.row_lookup:
            self.row_lookup[i].update_colors()

    def update_title_img_color(self):
        self.title_img.color = FG_COLOR if self.active_row_id >= 0 else FG_COLOR_DIM

    def update_all_colors(self):
        self.update_title_img_color()
        for i in self.row_lookup:
            self.row_lookup[i].update_colors()
        self.pause_btn.update_colors()
        self.add_btn.update_colors()

    def _make_text_input(self, hint_text="") -> MyTextInput:
        text_fld = MyTextInput(
            text=f"",
            hint_text=hint_text,
            font_name=REGULAR_FONT,
            font_size=f'{REGULAR_FONT_SIZE}sp',
            height=f'{ROW_HEIGHT}sp',
            size_hint=(1, None),
            multiline=False,
            write_tab=False)

        text_fld.bind(focus=lambda *_: text_fld.update_colors())

        return text_fld

    def select_text_field(self, i, cursor_col=0):
        if i in self.row_lookup:
            row_to_focus = self.row_lookup[i]
            row_to_focus.textbox.focus = True
            row_to_focus.textbox.cursor = (cursor_col, 0)

    def move_focused_text_field(self, cur_i, dy, cursor_col=0):
        if cur_i in self.row_lookup and len(self.row_lookup) > 1:
            order_idx = self.row_ordering.index(cur_i)
            next_i = self.row_ordering[(order_idx + dy) % len(self.row_ordering)]
            self.select_text_field(next_i, cursor_col=cursor_col)

    def _cache_cursor_pos(self, i):
        if i in self.row_lookup:
            row = self.row_lookup[i]
            self._cached_cursor_col = row.textbox.cursor_col

    def stop_active_timer(self):
        if self.active_row_id >= 0:
            row_id = self.active_row_id
            if self.active_row_id in self.row_lookup:
                self.row_lookup[self.active_row_id].timer_btn.state = 'normal'
            self.active_row_id = -1
            self.update_row_colors(row_id)
            self.update_title_img_color()
            self.update_pause_btn(mode='pause', disabled=True)

    def add_row(self):
        i = self.activity_id_counter
        self.activity_id_counter += 1

        row_height = f'{ROW_HEIGHT}sp'
        row = BoxLayout(orientation='horizontal', height=row_height, size_hint=(1, None))
        row.spacing = self.boxes.spacing

        timer_btn = MyToggleButton(size=(f'{ROW_HEIGHT * 4}sp', row_height), size_hint=(None, None))
        timer_btn.group = self._btn_group
        timer_btn.text = ZERO_TIME

        def on_timer_btn_press(btn):
            rows_to_update = set()
            if self.active_row_id_before_pause[0] >= 0:
                rows_to_update.add(self.active_row_id_before_pause[0])
                self.active_row_id_before_pause[0] = -1

            if btn.state == "down":
                rows_to_update.add(self.active_row_id)
                self.active_row_id = i
                self.update_pause_btn(mode='pause', disabled=False)
            else:
                self.active_row_id = -1
                self.update_pause_btn(mode='pause', disabled=True)

            rows_to_update.add(i)

            for row_id in rows_to_update:
                self.update_row_colors(row_id)
            self.update_title_img_color()

        timer_btn.bind(on_press=on_timer_btn_press)

        def calc_timer_text_color():
            if timer_btn.disabled:
                return DISABLED_FG_COLOR
            elif timer_btn.state == 'down':
                return BG_COLOR
            elif timer_btn.text in ('', ZERO_TIME):
                return DISABLED_FG_COLOR
            else:
                return FG_COLOR
        timer_btn.calc_text_color = calc_timer_text_color

        def calc_timer_bg_color():
            if timer_btn.state == 'down':
                return FG_COLOR if not timer_btn.disabled else FG_COLOR_DIM
            elif self.active_row_id_before_pause[0] == i:
                return FG_COLOR_DIM
            else:
                return BG_COLOR
        timer_btn.calc_fill_color = calc_timer_bg_color

        row.add_widget(timer_btn)

        textinput = self._make_text_input()
        textinput.hint_text = NEW_ACTIVITY_TEXT.format(f'{len(self.row_ordering) + 1}')

        def on_triple_tap(txt_fld):
            Clock.schedule_once(lambda dt: txt_fld.select_all())
            return True
        textinput.bind(on_triple_tap=on_triple_tap)

        old_kb_on_key_down = textinput.keyboard_on_key_down

        def kb_on_key_down(window, keycode, text, modifiers):
            if keycode is not None and keycode[1] in ('up', 'down'):
                cursor_col = textinput.cursor_col
                self.move_focused_text_field(i, (1 if keycode[1] == 'down' else -1), max(cursor_col, self._cached_cursor_col))
                return True
            elif keycode is not None and keycode[1] in ('left', 'right', 'home', 'end', 'pageup', 'pagedown'):
                Clock.schedule_once(lambda dt: self._cache_cursor_pos(i))
            return old_kb_on_key_down(window, keycode, text, modifiers)

        textinput.keyboard_on_key_down = kb_on_key_down

        def store_cursor_pos_later(*_):
            Clock.schedule_once(lambda dt: self._cache_cursor_pos(i))
        textinput.bind(text=store_cursor_pos_later)

        def store_cursor_col_later_wrapper(func):
            def wrapper(*args, **kwargs):
                Clock.schedule_once(lambda dt: self._cache_cursor_pos(i))
                func(*args, **kwargs)
            return wrapper

        textinput.on_touch_down = store_cursor_col_later_wrapper(textinput.on_touch_down)
        textinput.on_touch_up = store_cursor_col_later_wrapper(textinput.on_touch_up)

        def calc_border_color():
            if textinput.focused:
                return SECONDARY_COLOR
            elif i == self.active_row_id:
                return FG_COLOR
            elif i == self.active_row_id_before_pause[0]:
                return FG_COLOR_DIM
            else:
                return DISABLED_FG_COLOR
        textinput.calc_line_color = calc_border_color

        row.add_widget(textinput)

        reset_btn = MyButton(size=(f"{ROW_HEIGHT * 2}sp", row_height), size_hint=(None, None))
        reset_btn.text = RESET_TEXT
        reset_btn.font_size = f'{REGULAR_FONT_SIZE}sp'
        reset_btn.on_release = lambda: self.clear_row_time(i)

        def calc_reset_btn_color(for_text):
            base_line_color = FG_COLOR if self.active_row_id == i else \
                (FG_COLOR_DIM if self.active_row_id_before_pause[0] == i else DISABLED_FG_COLOR)
            if timer_btn.text in ('', ZERO_TIME) and \
                    i not in (self.active_row_id, self.active_row_id_before_pause[0]):
                return DISABLED_FG_COLOR if for_text else base_line_color
            elif reset_btn.hovering:
                return FG_COLOR
            else:
                return SECONDARY_COLOR if for_text else base_line_color
        reset_btn.calc_text_color = lambda: calc_reset_btn_color(True)
        reset_btn.calc_line_color = lambda: calc_reset_btn_color(False)

        row.add_widget(reset_btn)

        edit_btn = MyButton(size=(f"{ROW_HEIGHT * 2}sp", row_height), size_hint=(None, None))
        edit_btn.text = EDIT_TEXT
        edit_btn.font_size = f'{REGULAR_FONT_SIZE}sp'
        edit_btn.bind(on_release=lambda _: self.create_edit_popup(i))
        edit_btn.bind(on_press=lambda _: self.start_dragging_edit_button(i))

        def calc_edit_btn_colors(for_text):
            base_line_color = FG_COLOR if self.active_row_id == i else \
                (FG_COLOR_DIM if self.active_row_id_before_pause[0] == i else DISABLED_FG_COLOR)
            if self.dragging_edit_btn_row < 0:
                if for_text:
                    return FG_COLOR if edit_btn.hovering else SECONDARY_COLOR
                else:
                    return FG_COLOR if edit_btn.hovering else base_line_color
            elif i == self.dragging_edit_btn_row:
                return FG_COLOR if edit_btn.hovering else ACCENT_COLOR
            elif not edit_btn.hovering:
                return SECONDARY_COLOR if for_text else base_line_color
            else:
                return ACCENT_COLOR

        edit_btn.calc_line_color = lambda: calc_edit_btn_colors(False)
        edit_btn.calc_text_color = lambda: calc_edit_btn_colors(True)
        row.add_widget(edit_btn)

        def get_basic_btn_color(btn, for_text, hover_color=None):
            if for_text:
                return (hover_color or FG_COLOR) if btn.hovering else SECONDARY_COLOR
            else:
                base_line_color = FG_COLOR if self.active_row_id == i else \
                    (FG_COLOR_DIM if self.active_row_id_before_pause[0] == i else DISABLED_FG_COLOR)
                return (hover_color or FG_COLOR) if btn.hovering else base_line_color

        drag_btn = MyButton(size=(row_height, row_height), size_hint=(None, None))
        drag_btn.text = DRAG_SYMBOL_TEXT
        drag_btn.font_size = f'{REGULAR_FONT_SIZE}sp'
        drag_btn.hover_cursor = 'size_ns'
        drag_btn.calc_line_color = lambda: get_basic_btn_color(drag_btn, False)
        drag_btn.calc_text_color = lambda: get_basic_btn_color(drag_btn, True)
        drag_btn.bind(on_touch_down=lambda btn, me: drag_btn.collide_point(*me.pos) and self.start_dragging_row(i, me))
        row.add_widget(drag_btn)

        remove_btn = MyButton(size=(row_height, row_height), size_hint=(None, None))
        remove_btn.text = REMOVE_SYMBOL_TEXT
        remove_btn.font_size = f'{REGULAR_FONT_SIZE}sp'
        remove_btn.on_release = lambda: self.remove_row(i, simulate_hover_evt=True)
        remove_btn.calc_line_color = lambda: get_basic_btn_color(remove_btn, False, hover_color=CANCEL_COLOR)
        remove_btn.calc_text_color = lambda: get_basic_btn_color(remove_btn, True, hover_color=CANCEL_COLOR)

        row.add_widget(remove_btn)

        self.boxes.add_widget(row)
        self._update_boxes_height()

        row_data = RowData(row, timer_btn, textinput, edit_btn, remove_btn)
        self.row_lookup[i] = row_data
        self.row_ordering.append(i)

        self.update_row_colors(i)

    def create_edit_popup(self, i, from_row_id=None):
        if i not in self.row_lookup:
            return
        dest_row = self.row_lookup[i]

        if from_row_id is not None and from_row_id in self.row_lookup:
            from_row = self.row_lookup[from_row_id]
        else:
            from_row = None

        edit_field = self._make_text_input(PLUS_MINUS_MINUTES_TEXT)
        ok_btn = MyButton(text=OK_TEXT, font_size=f'{REGULAR_FONT_SIZE}sp')
        ok_btn.calc_text_color = lambda: FG_COLOR if ok_btn.hovering else SECONDARY_COLOR
        ok_btn.calc_line_color = lambda: FG_COLOR if ok_btn.hovering else DISABLED_FG_COLOR

        cancel_btn = MyButton(text=CANCEL_TEXT, font_size=f'{REGULAR_FONT_SIZE}sp')
        cancel_btn.calc_text_color = lambda: CANCEL_COLOR if cancel_btn.hovering else SECONDARY_COLOR
        cancel_btn.calc_line_color = lambda: CANCEL_COLOR if cancel_btn.hovering else DISABLED_FG_COLOR

        content = BoxLayout(orientation='vertical')
        content.spacing = 4

        content.add_widget(Widget())
        content.add_widget(edit_field)
        content.add_widget(Widget())

        btn_row = BoxLayout(orientation='horizontal')
        btn_row.size_hint = (1, None)
        btn_row.height = f'{ROW_HEIGHT}sp'
        btn_row.add_widget(Widget())
        btn_row.add_widget(ok_btn)
        btn_row.add_widget(cancel_btn)
        btn_row.add_widget(Widget())
        btn_row.spacing = 4
        content.add_widget(btn_row)

        popup = Popup(content=content, auto_dismiss=True)

        global_popup_var.append(popup)

        if from_row is None:
            title_text = EDIT_ACTIVITY_TEXT.format(f"{dest_row.textbox.text or UNTITLED_ACTIVITY_TEXT}")
        else:
            title_text = TRANSFER_TIME_TEXT.format(f"{dest_row.textbox.text or UNTITLED_ACTIVITY_TEXT}")

        if len(title_text) > 30:
            title_text = title_text[:27] + "..."

        popup.title = title_text
        popup.title_align = 'center'
        popup.title_font = REGULAR_FONT
        popup.title_size = REGULAR_FONT_SIZE

        popup.separator_color = FG_COLOR

        popup.size_hint = (None, None)
        popup.size = ('400sp', '168sp')

        def try_to_edit_time(_):
            cur_text = edit_field.text
            try:
                ms_to_add = int(1000 * 60 * float(cur_text))
                if from_row is not None:
                    new_from_time = max(0, from_row.get_time_ms() - ms_to_add)
                    from_row.set_time_ms(new_from_time)
                    if new_from_time == 0 and from_row_id == self.active_row_id:
                        self.stop_active_timer()

                new_dest_time = max(0, dest_row.get_time_ms() + ms_to_add)
                dest_row.set_time_ms(new_dest_time)
                if new_dest_time == 0 and i == self.active_row_id:
                    self.stop_active_timer()

            except Exception:
                traceback.print_exc()
            finally:
                popup.dismiss()

        ok_btn.bind(on_press=try_to_edit_time)
        ok_btn.in_popup = True

        cancel_btn.bind(on_press=popup.dismiss)
        cancel_btn.in_popup = True

        edit_field.bind(on_text_validate=try_to_edit_time)
        edit_field.focus = True
        edit_field.in_popup = True

        popup.bind(on_dismiss=lambda _: global_popup_var.clear())

        popup.open()

    def update_pause_btn(self, mode='pause', disabled=False):
        self.pause_btn.disabled = disabled
        self.pause_btn.text = PAUSE_TEXT if mode == 'pause' else RESUME_TEXT
        self.pause_btn.update_colors()

    def _build_pause_btn(self):
        self.pause_btn.text = PAUSE_TEXT
        self.pause_btn.group = self._btn_group

        def calc_pause_btn_color(for_text):
            if self.pause_btn.disabled:
                return DISABLED_FG_COLOR
            elif self.pause_btn.state == 'down':
                if self.pause_btn.hovering:
                    return BG_COLOR if for_text else FG_COLOR_DIM
                else:
                    return BG_COLOR if for_text else FG_COLOR
            elif self.pause_btn.hovering:
                return FG_COLOR
            else:
                return SECONDARY_COLOR if for_text else DISABLED_FG_COLOR

        self.pause_btn.calc_text_color = lambda: calc_pause_btn_color(True)
        self.pause_btn.calc_line_color = lambda: calc_pause_btn_color(False)

        def on_btn_press(btn):
            rows_to_update = []
            if btn.state == "down":
                self.active_row_id_before_pause[0] = self.active_row_id
                btn.text = RESUME_TEXT
                self.active_row_id = -1
                rows_to_update.append(self.active_row_id_before_pause[0])
            else:
                if self.active_row_id_before_pause[0] in self.row_lookup:
                    self.active_row_id = self.active_row_id_before_pause[0]
                    self.row_lookup[self.active_row_id_before_pause[0]].timer_btn.state = "down"
                    rows_to_update.append(self.active_row_id_before_pause[0])
                btn.text = PAUSE_TEXT
                self.active_row_id_before_pause[0] = -1

            btn.update_colors()
            for row_id in rows_to_update:
                self.update_row_colors(row_id)
            self.update_title_img_color()

        self.pause_btn.bind(on_press=on_btn_press)
        self.update_pause_btn(mode='pause', disabled=True)

    def _build_add_btn(self):
        self.add_btn.calc_text_color = lambda: FG_COLOR if self.add_btn.hovering else SECONDARY_COLOR
        self.add_btn.calc_line_color = lambda: FG_COLOR if self.add_btn.hovering else DISABLED_FG_COLOR


class TimeTrackerApp(App):

    def __init__(self):
        super().__init__()

    def build(self):
        self.title = WINDOW_TITLE
        self.icon = 'resources/icon/icon64.png'
        return Boxes(self)


def hsv_to_rgb(h, s, v):
    # from https://stackoverflow.com/a/26856771
    h /= 360
    if s == 0.0:
        return (v, v, v)
    i = int(h * 6.)
    f = (h * 6.) - i
    p, q, t = v * (1. - s), v * (1. - s * f), v * (1. - s * (1. - f))
    i %= 6
    if i == 0: return (v, t, p)
    if i == 1: return (q, v, p)
    if i == 2: return (p, v, t)
    if i == 3: return (p, q, v)
    if i == 4: return (t, p, v)
    if i == 5: return (v, p, q)


def get_color_for_time(t_ms=None):
    if RAINBOW_PERIOD_HOURS <= 0:
        h = RAINBOW_HUE_OFFSET
    else:
        if t_ms is None:
            t_ms = int(time.time() * 1000)
        time_of_day = t_ms % (24 * 60 * 60 * 1000)
        ms_per_period = RAINBOW_PERIOD_HOURS * 60 * 60 * 1000
        h = 360 * (time_of_day % ms_per_period) / ms_per_period + RAINBOW_HUE_OFFSET
    hsv = (h, 0.666, 1)
    rgb = hsv_to_rgb(*hsv)
    return rgb


if __name__ == '__main__':
    set_fg_color(get_color_for_time())
    TimeTrackerApp().run()
