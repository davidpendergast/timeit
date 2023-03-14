from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.textinput import TextInput

from kivy.clock import Clock
from kivy.config import Config

import os
os.environ["SDL_MOUSE_FOCUS_CLICKTHROUGH"] = '1'


Config.set('input', 'mouse', 'mouse,multitouch_on_demand')  # red dots begone
Config.set('kivy', 'window_icon', 'icon/favicon-32x32.png')

WINDOW_TITLE = "TimeTracker"
TITLE_FONT_SIZE = 64
REGULAR_FONT_SIZE = 20
ROW_HEIGHT = int(2 * REGULAR_FONT_SIZE)


Builder.load_string(f"""
<Label>:
    font_name: 'DejaVuSansMono'
    font_size: '{REGULAR_FONT_SIZE}sp'
    
<TextInput>:
    padding_y: [self.height / 2.0 - (self.line_height / 2.0) * len(self._lines), 0]
    
<Boxes>:
    id: _parent
    boxes: _boxes 
    orientation: 'vertical'
    padding: 4
    spacing: 4
    
    Label:
        text: 'TimeTracker'
        font_size: '{TITLE_FONT_SIZE}sp'
        size_hint: (1, None)
        height: '{TITLE_FONT_SIZE*2}sp'
    
    ScrollView:
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
        height: '{ROW_HEIGHT}sp'
        FloatLayout:
            height: '{ROW_HEIGHT}sp'
            size_hint: (1, None)
        Button:
            text: 'Add Activity'
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

    def get_time_str(self):
        secs = self.elapsed_time // 1000
        mins = secs // 60
        hours = mins // 60
        return f"{hours}:{str(mins % 60).zfill(2)}:{str(secs % 60).zfill(2)}"

    def update_button_label(self):
        self.timer_btn.text = self.get_time_str()


class Boxes(BoxLayout):

    def __init__(self, parent, **kwargs):
        super(Boxes, self).__init__(**kwargs)

        self._parent = parent
        self.boxes.size_hint = (1, None)

        self.activity_id_counter = 0

        self.active_row_id = -1
        self.row_lookup = {}
        for _ in range(5):
            self.add_row()

        self.timer = Clock.schedule_interval(self.inc_time, 1)

    def inc_time(self, dt):
        if self.active_row_id in self.row_lookup:
            row_data = self.row_lookup[self.active_row_id]
            row_data.add_time_ms(int(dt * 1000))
            caption_msg = f"{row_data.textbox.text} ~ {row_data.get_time_str()}"
        else:
            caption_msg = "Paused"

        self._parent.title = f"{WINDOW_TITLE} [{caption_msg}]"

    def remove_row(self, i):
        if i in self.row_lookup:
            row_widget = self.row_lookup[i].row_widget
            self.boxes.remove_widget(row_widget)
            self.boxes.height = f"{ROW_HEIGHT * len(self.boxes.children)}sp"  # seems like it shouldn't be needed
            del self.row_lookup[i]

            if self.active_row_id == i:
                self.active_row_id = -1

    def clear_row_time(self, i):
        if i in self.row_lookup:
            self.row_lookup[i].set_time_ms(0)

            if i == self.active_row_id:
                self.row_lookup[i].timer_btn.state = "normal"
                self.active_row_id = -1

    def add_row(self):
        i = self.activity_id_counter
        self.activity_id_counter += 1

        row_height = f'{ROW_HEIGHT}sp'
        row = BoxLayout(orientation='horizontal', height=row_height, size_hint=(1, None))

        checkbox = ToggleButton(size=(f'{ROW_HEIGHT * 3}sp', row_height), size_hint=(None, None))
        checkbox.group = "gay"
        checkbox.text = "0:00:00"

        def on_checkbox_active(btn):
            if btn.state == "down":
                print(f"Activity {i+1} became active")
                self.active_row_id = i
            else:
                self.active_row_id = -1
        checkbox.bind(on_press=on_checkbox_active)

        row.add_widget(checkbox)

        textinput = TextInput(text=f'Activity {i+1}',
                              font_name="DejaVuSansMono",
                              font_size=f"{REGULAR_FONT_SIZE}sp",
                              height=row_height,
                              size_hint=(1, None),
                              multiline=False)

        def on_triple_tap():
            Clock.schedule_once(lambda dt: textinput.select_all())
            return True
        textinput.on_triple_tap = on_triple_tap
        row.add_widget(textinput)

        clear_btn = Button(size=(f"{ROW_HEIGHT * 2}sp", row_height), size_hint=(None, None))
        clear_btn.text = "Clear"
        clear_btn.on_release = lambda: self.clear_row_time(i)
        row.add_widget(clear_btn)

        edit_btn = Button(size=(f"{ROW_HEIGHT * 2}sp", row_height), size_hint=(None, None))
        edit_btn.text = "Edit"
        row.add_widget(edit_btn)

        drag_btn = Button(size=(row_height, row_height), size_hint=(None, None))
        drag_btn.text = "="
        row.add_widget(drag_btn)

        remove_btn = Button(size=(row_height, row_height), size_hint=(None, None))
        remove_btn.text = "✖"
        row.add_widget(remove_btn)
        remove_btn.on_release = lambda: self.remove_row(i)

        self.boxes.add_widget(row)
        self.boxes.height = f"{ROW_HEIGHT * len(self.boxes.children)}sp"  # seems like it shouldn't be needed

        row_data = RowData(row, checkbox, textinput)
        self.row_lookup[i] = row_data


class TimeTrackerApp(App):

    def __init__(self):
        super().__init__()

    def build(self):
        return Boxes(self)


if __name__ == '__main__':
    TimeTrackerApp().run()
