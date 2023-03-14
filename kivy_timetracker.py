from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.textinput import TextInput
from kivy.clock import Clock

from kivy.config import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')  # red dots begone

Builder.load_string("""
<Boxes>:
    id: _parent
    boxes: _boxes 
    orientation: 'vertical'
    padding: 4
    spacing: 4
    
    Label:
        text: 'TimeTracker'
        font_size: '64sp'
        size_hint: (1, None)
        height: '128sp'
    
    ScrollView:
        effect_cls: 'ScrollEffect'
        do_scroll_x: False
        do_scroll_y: True
    
        BoxLayout: 
            id: _boxes
            orientation: 'vertical'
        
    #FloatLayout:
    #    size_hint: (1, 1)
        
    BoxLayout:
        orientation: 'horizontal'
        size_hint: (1, None)
        height: '32sp'
        FloatLayout:
            height: '32sp'
            size_hint: (1, None)
        Button:
            text: 'Add Activity'
            size: ('128sp', '32sp')
            size_hint: (None, None)
            on_press: _parent.add_row()
""")

class Boxes(BoxLayout):

    ROW_HEIGHT = 32

    def __init__(self, **kwargs):
        super(Boxes, self).__init__(**kwargs)
        self.boxes.size_hint = (1, None)
        self.activity_id_counter = 0
        self.row_lookup = {}
        for _ in range(5):
            self.add_row()

    def remove_row(self, i):
        if i in self.row_lookup:
            row_widget = self.row_lookup[i]
            self.boxes.remove_widget(row_widget)
            self.boxes.height = f"{Boxes.ROW_HEIGHT * len(self.boxes.children)}dp"  # seems like it shouldn't be needed
            del self.row_lookup[i]

    def add_row(self):
        i = self.activity_id_counter
        self.activity_id_counter += 1

        row_height = f'{Boxes.ROW_HEIGHT}dp'
        row = BoxLayout(orientation='horizontal', height=row_height, size_hint=(1, None))

        checkbox = ToggleButton(size=('80dp', row_height), size_hint=(None, None))
        checkbox.group = "gay"
        checkbox.text = "0:00:00"
        row.add_widget(checkbox)

        textinput = TextInput(text=f'Activity {i+1}',
                              height=row_height,
                              size_hint=(1, None),
                              multiline=False)

        def on_triple_tap():
            Clock.schedule_once(lambda dt: textinput.select_all())
            return True
        textinput.on_triple_tap = on_triple_tap
        row.add_widget(textinput)

        edit_btn = Button(size=(f"{Boxes.ROW_HEIGHT * 2}dp", row_height), size_hint=(None, None))
        edit_btn.text = "Edit"
        row.add_widget(edit_btn)

        drag_btn = Button(size=(row_height, row_height), size_hint=(None, None))
        drag_btn.text = "="
        row.add_widget(drag_btn)

        remove_btn = Button(size=(row_height, row_height), size_hint=(None, None))
        remove_btn.text = "X"
        row.add_widget(remove_btn)
        remove_btn.on_release = lambda: self.remove_row(i)

        self.boxes.add_widget(row)
        self.boxes.height = f"{Boxes.ROW_HEIGHT * len(self.boxes.children)}dp"  # seems like it shouldn't be needed
        self.row_lookup[i] = row


class TestApp(App):
    def build(self):
        return Boxes()

if __name__ == '__main__':
    TestApp().run()