import traceback
import typing

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

from kivymd.uix.behaviors import HoverBehavior

from kivy.clock import Clock
from kivy.config import Config
from kivy.core.window import Window
from kivy.core.text import LabelBase

import os
os.environ["SDL_MOUSE_FOCUS_CLICKTHROUGH"] = '1'

Config.set('input', 'mouse', 'mouse,multitouch_on_demand')  # red dots begone

REGULAR_FONT = 'DejaVuSansMono'
LabelBase.register(name=REGULAR_FONT,
                   fn_regular='fonts/dejavu-sans-mono/DejaVuSansMono.ttf',
                   fn_italic='fonts/dejavu-sans-mono/DejaVuSansMono-Oblique.ttf',
                   fn_bold='fonts/dejavu-sans-mono/DejaVuSansMono-Bold.ttf',
                   fn_bolditalic='fonts/dejavu-sans-mono/DejaVuSansMono-BoldOblique.ttf',)

WINDOW_TITLE = "TimeIt"

FG_COLOR = tuple(x/255. for x in (128, 222, 234))
FG_COLOR_DIM = tuple(x * 0.333 for x in FG_COLOR)
SECONDARY_COLOR = tuple(x/255. for x in (240, 240, 240))
BG_COLOR = tuple(x/255. for x in (0, 0, 0))
DISABLED_FG_COLOR = tuple(x/255. for x in (130, 130, 130))
ACCENT_COLOR = (1, 0, 0)

TITLE_FONT_SIZE = 64
REGULAR_FONT_SIZE = 20
SPACING = 4  # sp
ROW_HEIGHT = int(2 * REGULAR_FONT_SIZE)
ZERO_TIME = "0:00:00"


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
            points: self.pos[0], self.pos[1] + 1, \
                    self.pos[0] + self.size[0], self.pos[1] + 1, \
                    self.pos[0] + self.size[0], self.pos[1] + self.size[1], \
                    self.pos[0], self.pos[1] + self.size[1], \
                    self.pos[0] + 1, self.pos[1]
    
<MyTextInput>:
    padding_y: [self.height / 2.0 - (self.line_height / 2.0) * len(self._lines), 0]
    
    foreground_color: {SECONDARY_COLOR}  
    hint_text_color: {DISABLED_FG_COLOR}
    cursor_color: {SECONDARY_COLOR}
    
<Button>:
    font_name: '{REGULAR_FONT}'
    font_size: '{REGULAR_FONT_SIZE}sp'
    
<MyToggleButton>:
    canvas.after:
        Color:
            rgba: self.line_color
        Line:
            width: 1
            close: False
            points: self.pos[0] + 1, self.pos[1] + 1, \
                    self.pos[0] + self.size[0], self.pos[1] + 1, \
                    self.pos[0] + self.size[0], self.pos[1] + self.size[1], \
                    self.pos[0] + 1, self.pos[1] + self.size[1], \
                    self.pos[0] + 1, self.pos[1]
                    

<Boxes>:
    id: _parent
    scroller: _scroller
    boxes: _boxes 
    pause_btn: _pause_btn
    add_btn: _add_btn
    
    BoxLayout:
        orientation: 'vertical'
        padding: 8
            
        Image:
            source: 'logo.png'
            size_hint: (1, None)
            size: (self.texture_size[0], self.texture_size[1] * 1.25)
        
        MDScrollView:
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
                text: 'Add Activity'
                on_press: _parent.add_row()
                font_size: '{REGULAR_FONT_SIZE}sp'
                size_hint: (None, 1)
                width: '{ROW_HEIGHT * 4 + SPACING * 2}sp'
""")


class RowData:

    def __init__(self, row_widget, timer_btn, textbox):
        self.row_widget = row_widget
        self.timer_btn = timer_btn
        self.textbox = textbox
        self.elapsed_time = 0

    def add_time_ms(self, millis):
        self.elapsed_time += millis
        self.update_button_label()
        self.update_colors()

    def set_time_ms(self, millis):
        self.elapsed_time = millis
        self.update_button_label()
        self.update_colors()

    def get_time_ms(self):
        return self.elapsed_time

    def get_time_str(self):
        secs = self.elapsed_time // 1000
        mins = secs // 60
        hours = mins // 60
        return f"{hours}:{str(mins % 60).zfill(2)}:{str(secs % 60).zfill(2)}"

    def update_button_label(self):
        self.timer_btn.text = self.get_time_str()

    def update_colors(self):
        for widget in self.row_widget.children:  # TODO recurse
            if isinstance(widget, ColorUpdatable):
                widget.update_colors()


class ColorUpdatable:

    def __init__(self, *args, **kwargs):
        self.update_colors()

    def calc_text_color(self):
        return SECONDARY_COLOR

    def calc_line_color(self):
        return SECONDARY_COLOR

    def calc_fill_color(self):
        return BG_COLOR

    def update_colors(self):
        pass


class LineBorderWidget(Widget, ColorUpdatable):
    line_color = ColorProperty(DISABLED_FG_COLOR)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.background_normal = ''
        self.background_active = ''
        self.background_disabled_normal = ''
        self.background_disabled_down = ''

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
        self.background_normal = 'button_texture.png'
        self.background_active = 'button_texture.png'
        self.background_down = 'button_texture.png'
        self.background_disabled_normal = 'button_texture.png'
        self.background_disabled_down = 'button_texture.png'

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
            return BG_COLOR if self.state == 'down' else FG_COLOR
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

        self._cached_cursor_col = -1

        self.active_row_id = -1
        self.row_lookup: typing.Dict[int, RowData] = {}
        self.row_ordering = []
        for _ in range(5):
            self.add_row()

        self._build_pause_btn()
        self._build_add_btn()

        self.floating_row = -1
        self.floating_row_widget = None
        Window.bind(on_motion=lambda _, etype, me: self.handle_mouse_motion(etype, me))
        Window.bind(on_touch_up=lambda _, me: self.release_floating_row(me))

        self.timer = Clock.schedule_interval(self.inc_time, 0.5)

    def handle_mouse_motion(self, etype, me):
        if self.floating_row >= 0:
            Clock.schedule_once(lambda dt: self.update_floating_row(me.spos))

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
            self.reorder_rows(new_ordering)

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
            self.reorder_rows(new_ordering)
            self.floating_row = -1

    def get_row_order_idx_at(self, scr_xy, constrain=True):
        scr_xy_px = (int(scr_xy[0] * Window.size[0]), int(scr_xy[1] * Window.size[1]))
        box_xy = self.boxes.to_window(*self.boxes.pos)  # TODO check units on these
        box_size = self.boxes.size
        pos_rel_to_box = (scr_xy_px[0] - box_xy[0],
                          box_xy[1] + box_size[1] - scr_xy_px[1])
        row_order_idx = pos_rel_to_box[1] // (ROW_HEIGHT + SPACING)
        if constrain:
            row_order_idx = max(0, min(row_order_idx, len(self.row_ordering) - 1))

        # print(f"INFO: {scr_xy_px=}, {box_xy=}, {box_size=}, {pos_rel_to_box=}, {row_order_idx=}")
        return row_order_idx

    def reorder_rows(self, new_ordering):
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

        self._update_boxes_height()
        self.scroller.scroll_y = old_scroll_y

    def inc_time(self, dt):
        if self.active_row_id in self.row_lookup:
            row_data = self.row_lookup[self.active_row_id]
            row_data.add_time_ms(int(dt * 1000))
        self._update_window_caption()

    def _update_window_caption(self):
        if self.active_row_id in self.row_lookup:
            row_data = self.row_lookup[self.active_row_id]
            caption_msg = f"{row_data.textbox.text} ~ {row_data.get_time_str()}"
        else:
            caption_msg = "Paused"
        self._parent.title = f"{WINDOW_TITLE} [{caption_msg}]"

    def get_row_data(self, row_i=None) -> RowData:
        if row_i is None:
            row_i = self.active_row_id
        if row_i in self.row_lookup:
            return self.row_lookup[row_i]
        else:
            return None

    def _update_boxes_height(self):
        n = len(self.boxes.children)
        self.boxes.height = f"{ROW_HEIGHT * n + int(str(self.boxes.spacing)[:-2]) * (n - 1)}sp"

    def remove_row(self, i):
        if i in self.row_lookup:
            row_widget = self.row_lookup[i].row_widget
            self.boxes.remove_widget(row_widget)
            self._update_boxes_height()
            del self.row_lookup[i]
            self.row_ordering.remove(i)

            if self.active_row_id == i:
                self.update_row_colors(self.active_row_id)
                self.active_row_id = -1
                self._update_pause_btn(mode='pause', disabled=True)

    def clear_row_time(self, i):
        if i in self.row_lookup:
            self.row_lookup[i].set_time_ms(0)

            if i == self.active_row_id:
                self.row_lookup[i].timer_btn.state = "normal"
                self.row_lookup[i].timer_btn.update_colors()
                self.active_row_id = -1
                self._update_pause_btn(mode='pause', disabled=True)
            elif i == self.active_row_id_before_pause[0]:
                self.active_row_id_before_pause[0] = -1
                self._update_pause_btn(mode='pause', disabled=True)

            self.update_row_colors(i)

    def update_row_colors(self, i):
        if i in self.row_lookup:
            self.row_lookup[i].update_colors()

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

        def on_focus(instance, value):
            text_fld.update_colors()
        text_fld.bind(focus=on_focus)

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

    def add_row(self):
        i = self.activity_id_counter
        self.activity_id_counter += 1

        row_height = f'{ROW_HEIGHT}sp'
        row = BoxLayout(orientation='horizontal', height=row_height, size_hint=(1, None))
        row.spacing = self.boxes.spacing

        timer_toggle_btn = MyToggleButton(size=(f'{ROW_HEIGHT * 4}sp', row_height), size_hint=(None, None))
        timer_toggle_btn.group = self._btn_group
        timer_toggle_btn.text = ZERO_TIME

        def on_checkbox_active(btn):
            self.active_row_id_before_pause[0] = -1
            if btn.state == "down":
                self.update_row_colors(self.active_row_id)  # update old row
                self.active_row_id = i
                self._update_pause_btn(mode='pause', disabled=False)
            else:
                self.active_row_id = -1
                self._update_pause_btn(mode='pause', disabled=True)
            self.update_row_colors(i)

        timer_toggle_btn.bind(on_press=on_checkbox_active)

        def calc_timer_text_color():
            if timer_toggle_btn.disabled or timer_toggle_btn.state == "down":
                return BG_COLOR
            elif timer_toggle_btn.text in ('', ZERO_TIME):
                return DISABLED_FG_COLOR
            else:
                return FG_COLOR
        timer_toggle_btn.calc_text_color = calc_timer_text_color

        def calc_timer_bg_color():
            if timer_toggle_btn.state == "down":
                return FG_COLOR if not timer_toggle_btn.disabled else FG_COLOR_DIM
            elif self.active_row_id_before_pause[0] == i:
                return FG_COLOR_DIM
            else:
                return BG_COLOR
        timer_toggle_btn.calc_fill_color = calc_timer_bg_color

        row.add_widget(timer_toggle_btn)

        textinput = self._make_text_input(hint_text=f"Activity {i + 1}")

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

        row.add_widget(textinput)

        clear_btn = MyButton(size=(f"{ROW_HEIGHT * 2}sp", row_height), size_hint=(None, None))
        clear_btn.text = "Reset"
        clear_btn.font_size = f'{REGULAR_FONT_SIZE}sp'
        clear_btn.on_release = lambda: self.clear_row_time(i)

        def calc_clear_btn_text_color():
            if timer_toggle_btn.text in ('', ZERO_TIME) and \
                    i not in (self.active_row_id, self.active_row_id_before_pause[0]):
                return DISABLED_FG_COLOR
            elif clear_btn.hovering:
                return FG_COLOR
            else:
                return SECONDARY_COLOR
        clear_btn.calc_text_color = calc_clear_btn_text_color

        def calc_clear_btn_line_color():
            if timer_toggle_btn.text in ('', ZERO_TIME) and \
                    i not in (self.active_row_id, self.active_row_id_before_pause[0]):
                return DISABLED_FG_COLOR
            elif clear_btn.hovering:
                return FG_COLOR
            else:
                return DISABLED_FG_COLOR
        clear_btn.calc_line_color = calc_clear_btn_line_color

        row.add_widget(clear_btn)

        def create_popup(_):
            edit_field = self._make_text_input('+/- Minutes')
            ok_btn = MyButton(text='OK', font_size=f'{REGULAR_FONT_SIZE}sp')
            ok_btn.calc_text_color = lambda: FG_COLOR if ok_btn.hovering else SECONDARY_COLOR
            ok_btn.calc_line_color = lambda: FG_COLOR if ok_btn.hovering else DISABLED_FG_COLOR

            cancel_btn = MyButton(text='Cancel', font_size=f'{REGULAR_FONT_SIZE}sp')
            cancel_btn.calc_text_color = lambda: ACCENT_COLOR if cancel_btn.hovering else SECONDARY_COLOR
            cancel_btn.calc_line_color = lambda: ACCENT_COLOR if cancel_btn.hovering else DISABLED_FG_COLOR

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

            popup.title = f"Edit {textinput.text or 'Untitled Activity'}"
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
                    _row_data = self.get_row_data(i)
                    if _row_data is not None:
                        _row_data.set_time_ms(max(0, _row_data.get_time_ms() + ms_to_add))
                except Exception:
                    traceback.print_exc()
                finally:
                    popup.dismiss()

            # bind the on_press event of the button to the dismiss function
            ok_btn.bind(on_press=try_to_edit_time)
            cancel_btn.bind(on_press=popup.dismiss)

            edit_field.bind(on_text_validate=try_to_edit_time)
            edit_field.focus = True

            # open the popup
            popup.open()

        edit_btn = MyButton(size=(f"{ROW_HEIGHT * 2}sp", row_height), size_hint=(None, None))
        edit_btn.text = "Edit"
        edit_btn.font_size = f'{REGULAR_FONT_SIZE}sp'
        edit_btn.bind(on_release=create_popup)
        edit_btn.calc_line_color = lambda: FG_COLOR if edit_btn.hovering else DISABLED_FG_COLOR
        edit_btn.calc_text_color = lambda: FG_COLOR if edit_btn.hovering else SECONDARY_COLOR
        row.add_widget(edit_btn)

        drag_btn = MyButton(size=(row_height, row_height), size_hint=(None, None))
        drag_btn.text = "↕"
        drag_btn.font_size = f'{REGULAR_FONT_SIZE}sp'
        drag_btn.hover_cursor = 'size_ns'
        drag_btn.calc_line_color = lambda: FG_COLOR if drag_btn.hovering else DISABLED_FG_COLOR
        drag_btn.calc_text_color = lambda: FG_COLOR if drag_btn.hovering else SECONDARY_COLOR
        drag_btn.bind(on_touch_down=lambda btn, me: drag_btn.collide_point(*me.pos) and self.start_dragging_row(i, me))
        row.add_widget(drag_btn)

        remove_btn = MyButton(size=(row_height, row_height), size_hint=(None, None))
        remove_btn.text = "✖"
        remove_btn.font_size = f'{REGULAR_FONT_SIZE}sp'
        remove_btn.on_release = lambda: self.remove_row(i)
        remove_btn.calc_line_color = lambda: ACCENT_COLOR if remove_btn.hovering else DISABLED_FG_COLOR
        remove_btn.calc_text_color = lambda: ACCENT_COLOR if remove_btn.hovering else SECONDARY_COLOR

        row.add_widget(remove_btn)

        self.boxes.add_widget(row)
        self._update_boxes_height()

        row_data = RowData(row, timer_toggle_btn, textinput)
        self.row_lookup[i] = row_data
        self.row_ordering.append(i)

        self.update_row_colors(i)

    def _update_pause_btn(self, mode='pause', disabled=False):
        self.pause_btn.disabled = disabled
        self.pause_btn.text = "Pause" if mode == 'pause' else "Resume"
        self.pause_btn.update_colors()

    def _build_pause_btn(self):
        self.pause_btn.text = "Pause"
        self.pause_btn.group = self._btn_group

        def calc_pause_btn_color(for_text):
            if self.pause_btn.disabled:
                return DISABLED_FG_COLOR
            elif self.pause_btn.state == 'down':
                if self.pause_btn.hovering:
                    return BG_COLOR
                else:
                    return BG_COLOR if for_text else FG_COLOR
            elif self.pause_btn.hovering:
                return FG_COLOR
            else:
                return SECONDARY_COLOR if for_text else DISABLED_FG_COLOR

        self.pause_btn.calc_text_color = lambda: calc_pause_btn_color(True)
        self.pause_btn.calc_line_color = lambda: calc_pause_btn_color(False)

        def on_checkbox_active(btn):
            if btn.state == "down":
                self.active_row_id_before_pause[0] = self.active_row_id
                self.update_row_colors(self.active_row_id_before_pause[0])
                btn.text = "Resume"
                self.active_row_id = -1
            else:
                if self.active_row_id_before_pause[0] in self.row_lookup:
                    self.active_row_id = self.active_row_id_before_pause[0]
                    self.row_lookup[self.active_row_id_before_pause[0]].timer_btn.state = "down"
                    self.update_row_colors(self.active_row_id_before_pause[0])
                btn.text = "Pause"
                self.active_row_id_before_pause[0] = -1
            btn.update_colors()

        self.pause_btn.bind(on_press=on_checkbox_active)
        self._update_pause_btn(mode='pause', disabled=True)

    def _build_add_btn(self):
        self.add_btn.calc_text_color = lambda: FG_COLOR if self.add_btn.hovering else SECONDARY_COLOR
        self.add_btn.calc_line_color = lambda: FG_COLOR if self.add_btn.hovering else DISABLED_FG_COLOR


class TimeTrackerApp(App):

    def __init__(self):
        super().__init__()

    def build(self):
        self.title = WINDOW_TITLE
        self.icon = 'icon/icon64.png'
        return Boxes(self)


if __name__ == '__main__':
    TimeTrackerApp().run()
