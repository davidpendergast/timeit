import tkinter as tk
from tkinter import ttk

from ttkthemes import ThemedTk


WINDOW_TITLE = "Time Tracker"


def start():
    root = ThemedTk(theme="breeze")
    root.title(WINDOW_TITLE)
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=1)

    mainframe = ttk.Frame(root, padding="4 4 4 4")
    mainframe.grid(column=0, row=0, sticky="nsew")
    mainframe.grid_columnconfigure(0, weight=1)

    rowframe = ttk.Frame(mainframe)
    rowframe.grid(column=0, row=0, sticky="nsew")

    next_idx = 0
    active_row_var = tk.IntVar()

    row_data = {}
    row_order = []

    class RowData:
        def __init__(self, idx, btn, name_var, time_var, widgets):
            self.idx = idx
            self.btn = btn
            self.name_var = name_var
            self.time_var = time_var
            self.widgets = widgets

    pause_btn = None

    def update_radio_button_label(row_idx) -> str:
        if row_idx in row_data:
            btn = row_data[row_idx].btn
            secs = row_data[row_idx].time_var.get() // 1000
            mins = secs // 60
            hours = mins // 60
            btn_text = f"{hours}:{str(mins % 60).zfill(2)}:{str(secs % 60).zfill(2)}"
            btn.configure(text=btn_text)
            return btn_text
        else:
            return "Paused"

    def clear_time(row_idx):
        if row_idx in row_data:
            row_data[row_idx].time_var.set(0)
        update_radio_button_label(row_idx)
        if active_row_var.get() == row_idx:
            set_active_row(-1)

    def set_active_row(row_idx):
        if row_idx in row_data:
            row_data[row_idx].btn.invoke()
        elif pause_btn is not None:
            pause_btn.invoke()

    popup = None

    def pop_edit_field(row_idx):
        nonlocal popup
        if popup is not None:
            close_popup()

        if row_idx in row_data:
            popup = tk.Toplevel(root)
            popup.title(row_data[row_idx].name_var.get())
            popupframe = ttk.Frame(popup, padding="4 4 4 4")
            popupframe.grid(column=0, row=0, sticky="nsew")

            edit_var = tk.StringVar()

            # Create an Entry Widget in the Toplevel window
            label = ttk.Label(popupframe, text="Add/Subtract Minutes: ")
            label.pack()

            entry = ttk.Entry(popupframe, textvariable=edit_var, width=48)
            entry.bind("<Return>", lambda evt: close_popup(row_idx, edit_var.get()))
            entry.pack()
            entry.focus()

            # Create a Button Widget in the Toplevel Window
            button = ttk.Button(popupframe, text="Ok", command=lambda: close_popup(row_idx, edit_var.get()))
            button.pack(pady=5, side=tk.TOP)

    def close_popup(row_idx=-1, minute_str=""):
        nonlocal popup
        if popup is not None:
            popup.destroy()
        popup = None

        if row_idx in row_data:
            minutes = 0
            try:
                minutes = int(minute_str)
            except Exception:
                pass
            row_time_var = row_data[row_idx].time_var
            new_time = max(0, row_time_var.get() + minutes * 60 * 1000)
            row_time_var.set(new_time)
            update_radio_button_label(row_idx)

    def add_new_activity():
        nonlocal next_idx
        i = (next_idx := next_idx + 1) - 1

        x = -1
        y = len(row_order)

        radio_btn = ttk.Radiobutton(rowframe, text=f"0:00:00", variable=active_row_var, value=i)

        name_var = tk.StringVar(value=f"Activity {i + 1}")
        time_var = tk.IntVar(value=0)

        name_label = ttk.Entry(rowframe, textvariable=name_var)
        clear_btn = ttk.Button(rowframe, text="Reset", command=lambda _i=i: clear_time(_i))
        edit_btn = ttk.Button(rowframe, text="Edit", command=lambda _i=i: pop_edit_field(_i))
        delete_btn = ttk.Button(rowframe, text="Delete", command=lambda _i=i: remove_activity(_i))

        row_order.append(i)
        row_data[i] = RowData(i, radio_btn, name_var, time_var,
                              (radio_btn, name_label, clear_btn, edit_btn, delete_btn))

        update_radio_button_label(i)
        update_widget_positions(i)

        for widget in row_data[i].widgets:
            add_global_keybinds(widget)

    def update_widget_positions(i):
        if i in row_data and i in row_order:
            y = row_order.index(i)
            for x, widget in enumerate(row_data[i].widgets):
                if isinstance(widget, ttk.Entry):
                    widget.grid(column=x, row=y, sticky="ew")
                    rowframe.grid_columnconfigure(x, weight=1)
                else:
                    widget.grid(column=x, row=y)
                    rowframe.grid_columnconfigure(x, weight=0)
        elif i in row_data:
            for widget in row_data[i].widgets:
                widget.grid_remove()

    def remove_activity(i):
        if i in row_data:
            for item in row_data[i].widgets:
                item.grid_remove()
                item.destroy()

            del row_data[i]

            if i == active_row_var.get():
                set_active_row(-1)

            if i in row_order:
                order_idx = row_order.index(i)
                row_order.pop(order_idx)
                for idx in range(order_idx, len(row_order)):
                    update_widget_positions(row_order[idx])

    def add_global_keybinds(widget):

        def move_active(dy):
            cur_active = active_row_var.get()
            if len(row_order) == 0 or len(row_data) == 0:
                new_active = -1
            elif cur_active == -1:
                new_active = -1
                if dy < 0:
                    new_active = row_order[-1]
                elif dy > 0:
                    new_active = row_order[0]
            elif dy < 0 and cur_active == row_order[0]:
                new_active = -1
            elif dy > 0 and cur_active == row_order[-1]:
                new_active = -1
            elif cur_active in row_order and cur_active in row_data:
                cur_active_order_idx = row_order.index(cur_active)
                new_active = row_order[cur_active_order_idx + dy]
            else:
                new_active = -1

            if new_active >= 0:
                row_data[new_active].btn.invoke()
            else:
                pause_btn.invoke()
            return "break"
        
        widget.bind("<Up>", lambda evt: move_active(-1))
        widget.bind("<Down>", lambda evt: move_active(1))

    for _ in range(5):
        add_new_activity()

    pause_btn = ttk.Radiobutton(mainframe, text=f"Paused", variable=active_row_var, value=-1)
    pause_btn.grid(column=0, row=1, sticky="w")
    set_active_row(-1)

    mainframe.grid_rowconfigure(2, weight=1)

    control_panel = ttk.Frame(mainframe)
    control_panel.grid(column=0, row=3, sticky="e")

    add_new_btn = ttk.Button(control_panel, text="Add Activity", command=lambda: add_new_activity())
    add_new_btn.grid(column=0, row=0)

    # remove_act_btn = ttk.Button(control_panel, text="Delete Activity", command=lambda: remove_activity())
    # remove_act_btn.grid(column=1, row=0)

    def time_loop(dt):
        row_idx = active_row_var.get()
        if row_idx in row_data:
            row_time = row_data[row_idx].time_var
            row_time.set(row_time.get() + dt)
            label_text = f"{row_data[row_idx].name_var.get()} ~ {update_radio_button_label(row_idx)}"
        else:
            label_text = update_radio_button_label(row_idx)

        root.title(f"{WINDOW_TITLE} [{label_text}]")
        root.after(dt, time_loop, dt)

    add_global_keybinds(root)
    root.after(1000, time_loop, 1000)

    root.mainloop()


if __name__ == "__main__":
    start()
