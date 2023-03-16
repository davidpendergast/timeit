import traceback
import typing

from kivymd.app import MDApp
from kivy.lang import Builder

from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRectangleFlatButton
from kivymd.uix.behaviors.toggle_behavior import MDToggleButton
from kivymd.uix.behaviors import HoverBehavior

from kivy.clock import Clock
from kivy.config import Config
from kivy.core.text import LabelBase

import os
os.environ["SDL_MOUSE_FOCUS_CLICKTHROUGH"] = '1'

Config.set('input', 'mouse', 'mouse,multitouch_on_demand')  # red dots begone
Config.set('kivy', 'window_icon', 'icon/icon64.png')

REGULAR_FONT = 'DejaVuSansMono'
LabelBase.register(name=REGULAR_FONT,
                   fn_regular='fonts/dejavu-sans-mono/DejaVuSansMono.ttf',
                   fn_italic='fonts/dejavu-sans-mono/DejaVuSansMono-Oblique.ttf',
                   fn_bold='fonts/dejavu-sans-mono/DejaVuSansMono-Bold.ttf',
                   fn_bolditalic='fonts/dejavu-sans-mono/DejaVuSansMono-BoldOblique.ttf',)

WINDOW_TITLE = "TimeIt"

TITLE_FONT_SIZE = 64
REGULAR_FONT_SIZE = 20
ROW_HEIGHT = int(2 * REGULAR_FONT_SIZE)
ZERO_TIME = "0:00:00"


Builder.load_string(f"""
<MDLabel>:
    font_name: '{REGULAR_FONT}'
    font_size: '{REGULAR_FONT_SIZE}sp'
    
<TextInput>:
    padding_y: [self.height / 2.0 - (self.line_height / 2.0) * len(self._lines), 0]
    background_normal: ''
    background_active: ''
    background_disabled_normal: ''
    background_disabled_down: ''
    line_anim: False
    
    canvas.after:
        Color:
            rgba: app.theme_cls.text_color if self.focus else app.theme_cls.disabled_primary_color
        Line:
            points: self.pos[0], self.pos[1], self.pos[0] + self.size[0], self.pos[1]
        Line:
            points: self.pos[0], self.pos[1] + self.size[1], self.pos[0] + self.size[0], self.pos[1] + self.size[1]
        Line:
            points: self.pos[0], self.pos[1], self.pos[0], self.pos[1] + self.size[1]
        Line:
            points: self.pos[0] + self.size[0], self.pos[1], self.pos[0] + self.size[0], self.pos[1] + self.size[1]
    
    background_color: app.theme_cls.bg_normal
    foreground_color: app.theme_cls.text_color
    
    hint_text_color: app.theme_cls.disabled_hint_text_color
    cursor_color: app.theme_cls.text_color

<MyToggleButton>:
    ripple_scale: 0
    font_size: '{REGULAR_FONT_SIZE}sp'
    text_color: app.theme_cls.bg_normal if (self.state == 'down') else \
            (app.theme_cls.disabled_hint_text_color if self.text == '{ZERO_TIME}' else app.theme_cls.primary_color)
    font_color_normal: app.theme_cls.disabled_hint_text_color if self.text == '{ZERO_TIME}' else app.theme_cls.primary_color
    font_color_down: app.theme_cls.bg_normal

<Boxes>:
    id: _parent
    boxes: _boxes 
    orientation: 'vertical'
    padding: 8
        
    Image:
        source: 'logo.png'
        size_hint: (1, None)
        size: (self.texture_size[0], self.texture_size[1] * 1.25)
    
    MDScrollView:
        effect_cls: 'ScrollEffect'
        do_scroll_x: False
        do_scroll_y: True
        
        scroll_type: ['bars']
        bar_width: 4
    
        MDBoxLayout: 
            id: _boxes
            orientation: 'vertical'
        
    MDBoxLayout:
        orientation: 'horizontal'
        size_hint: (1, None)
        height: '{ROW_HEIGHT}sp'
        FloatLayout:
            height: '{ROW_HEIGHT}sp'
            size_hint: (1, None)
        MyMDRectangleFlatButton:
            text: 'Add Activity'
            font_size: '{REGULAR_FONT_SIZE}sp'
            size: ('{ROW_HEIGHT * 4}sp', '{ROW_HEIGHT}sp')
            size_hint: (None, None)
            on_press: _parent.add_row()
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

    def set_time_ms(self, millis):
        self.elapsed_time = millis
        self.update_button_label()

    def get_time_ms(self):
        return self.elapsed_time

    def get_time_str(self):
        secs = self.elapsed_time // 1000
        mins = secs // 60
        hours = mins // 60
        return f"{hours}:{str(mins % 60).zfill(2)}:{str(secs % 60).zfill(2)}"

    def update_button_label(self):
        self.timer_btn.text = self.get_time_str()


class MyMDRectangleFlatButton(MDRectangleFlatButton, HoverBehavior):

    def on_enter(self, *args):
        self.line_color = self.theme_cls.text_color

    def on_leave(self, *args):
        self.line_color = self.theme_cls.primary_color


class MyToggleButton(MyMDRectangleFlatButton, MDToggleButton):

    def __init__(self, **kwargs):
        self.background_normal = [1, 1, 1, 1]  # bug?~
        super().__init__(**kwargs)
        self.background_normal = self.theme_cls.bg_normal
        self.background_down = self.theme_cls.primary_color


class Boxes(MDBoxLayout):

    def __init__(self, parent, **kwargs):
        super(Boxes, self).__init__(**kwargs)

        self._parent = parent
        self.boxes.size_hint = (1, None)
        self.boxes.spacing = '4sp'

        self.activity_id_counter = 0

        self._cached_cursor_col = -1

        self.active_row_id = -1
        self.row_lookup: typing.Dict[int, RowData] = {}
        self.row_ordering = []
        for _ in range(5):
            self.add_row()

        self.timer = Clock.schedule_interval(self.inc_time, 0.5)

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
        self.boxes.height = f"{(ROW_HEIGHT + int(str(self.boxes.spacing)[:-2])) * n}sp"

    def remove_row(self, i):
        if i in self.row_lookup:
            row_widget = self.row_lookup[i].row_widget
            self.boxes.remove_widget(row_widget)
            self._update_boxes_height()
            del self.row_lookup[i]
            self.row_ordering.remove(i)

            if self.active_row_id == i:
                self.active_row_id = -1

    def clear_row_time(self, i):
        if i in self.row_lookup:
            self.row_lookup[i].set_time_ms(0)

            if i == self.active_row_id:
                self.row_lookup[i].timer_btn.state = "normal"
                self.active_row_id = -1

    def _make_text_input(self, hint_text="") -> TextInput:
        return TextInput(
            text=f"",
            hint_text=hint_text,
            font_name=REGULAR_FONT,
            font_size=f'{REGULAR_FONT_SIZE}sp',
            height=f'{ROW_HEIGHT}sp',
            size_hint=(1, None),
            multiline=False,
            write_tab=False)

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
        row = MDBoxLayout(orientation='horizontal', height=row_height, size_hint=(1, None))
        row.spacing = self.boxes.spacing

        timer_toggle_btn = MyToggleButton(size=(f'{ROW_HEIGHT * 4}sp', row_height), size_hint=(None, None))
        timer_toggle_btn.group = "gey"
        timer_toggle_btn.text = ZERO_TIME

        def on_checkbox_active(btn):
            if btn.state == "down":
                self.active_row_id = i
            else:
                self.active_row_id = -1
        timer_toggle_btn.bind(on_press=on_checkbox_active)
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

        clear_btn = MyMDRectangleFlatButton(size=(f"{ROW_HEIGHT * 2}sp", row_height), size_hint=(None, None))
        clear_btn.text = "Clear"
        clear_btn.font_size = f'{REGULAR_FONT_SIZE}sp'
        clear_btn.on_release = lambda: self.clear_row_time(i)
        row.add_widget(clear_btn)

        def create_popup(_):
            edit_field = self._make_text_input('+/- Minutes')
            ok_btn = MyMDRectangleFlatButton(text='OK', font_size=f'{REGULAR_FONT_SIZE}sp')
            cancel_btn = MyMDRectangleFlatButton(text='Cancel', font_size=f'{REGULAR_FONT_SIZE}sp')

            content = MDBoxLayout(orientation='vertical')
            content.spacing = 4

            content.add_widget(Widget())
            content.add_widget(edit_field)
            content.add_widget(Widget())

            btn_row = MDBoxLayout(orientation='horizontal')
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

            popup.separator_color = self._parent.theme_cls.primary_color

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

        edit_btn = MyMDRectangleFlatButton(size=(f"{ROW_HEIGHT * 2}sp", row_height), size_hint=(None, None))
        edit_btn.text = "Edit"
        edit_btn.font_size = f'{REGULAR_FONT_SIZE}sp'
        edit_btn.bind(on_release=create_popup)
        row.add_widget(edit_btn)

        drag_btn = MyMDRectangleFlatButton(size=(row_height, row_height), size_hint=(None, None))
        drag_btn.text = "="
        drag_btn.font_size = f'{REGULAR_FONT_SIZE}sp'
        row.add_widget(drag_btn)

        remove_btn = MyMDRectangleFlatButton(size=(row_height, row_height), size_hint=(None, None))
        remove_btn.text = "✖"
        remove_btn.font_size = f'{REGULAR_FONT_SIZE}sp'
        row.add_widget(remove_btn)
        remove_btn.on_release = lambda: self.remove_row(i)

        self.boxes.add_widget(row)
        self._update_boxes_height()

        row_data = RowData(row, timer_toggle_btn, textinput)
        self.row_lookup[i] = row_data
        self.row_ordering.append(i)


class TimeTrackerApp(MDApp):

    def __init__(self):
        super().__init__()

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Cyan"
        self.theme_cls.primary_hue = "200"
        self.title = WINDOW_TITLE
        return Boxes(self)


if __name__ == '__main__':
    TimeTrackerApp().run()
