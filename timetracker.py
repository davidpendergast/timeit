import tkinter as tk
from tkinter import ttk
from tkinter import font
from ttkthemes import ThemedTk

import traceback


WINDOW_TITLE = "TimeTracker"
MAIN_THEME = 'breeze'

TITLE_FONT = None
MAIN_FONT = None


def init_style():
    global MAIN_FONT, TITLE_FONT

    main_font_fallbacks = [('DejaVu Sans Mono', 14), ("Courier", 14)]
    title_font_fallbacks = [("Purisa", 24), ("Ink Free", 24), ("Courier", 24)]

    available_fonts = set(f for f in font.families())

    MAIN_FONT = main_font_fallbacks[-1]
    for fname, fsize in main_font_fallbacks:
        if fname in available_fonts:
            MAIN_FONT = (fname, fsize)
            break

    TITLE_FONT = title_font_fallbacks[-1]
    for fname, fsize in title_font_fallbacks:
        if fname in available_fonts:
            TITLE_FONT = (fname, fsize)
            break

    s = ttk.Style()
    s.configure('.', font=MAIN_FONT)


def start():
    root = ThemedTk(theme=MAIN_THEME)
    root.title(WINDOW_TITLE)
    root.iconbitmap("icon/favicon.ico")

    init_style()

    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=1)

    mainframe = ttk.Frame(root, padding="4 4 4 4")
    mainframe.grid(column=0, row=0, sticky="nsew")
    mainframe.grid_columnconfigure(0, weight=1)

    titlelabel = ttk.Label(mainframe, text=f"{WINDOW_TITLE}", font=TITLE_FONT,
                           padding="0 0 0 4", anchor=tk.CENTER)
    titlelabel.grid(column=0, row=0, sticky="we")

    rowframe = ttk.Frame(mainframe)
    rowframe.grid(column=0, row=1, sticky="nsew")

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

    popup: tk.Toplevel = None

    def pop_edit_field(row_idx):
        nonlocal popup
        if popup is not None:
            close_popup()

        if row_idx in row_data:
            popup = tk.Toplevel(root)
            popup.transient(root)
            popup.title(row_data[row_idx].name_var.get())
            popup.resizable(False, False)

            popupframe = ttk.Frame(popup, padding="4 4 4 4")
            popupframe.grid(column=0, row=0, sticky="nsew")

            label = ttk.Label(popupframe, text="Add/Subtract Minutes", font=MAIN_FONT, anchor=tk.CENTER)
            label.grid(column=0, row=0, sticky="ew")

            edit_var = tk.StringVar()
            entry = ttk.Entry(popupframe, textvariable=edit_var, font=MAIN_FONT)
            entry.bind("<Return>", lambda evt: close_popup(row_idx, edit_var.get()))
            entry.grid(column=0, row=1, sticky="ew")
            entry.focus()

            button = ttk.Button(popupframe, text="Ok", width=4, command=lambda: close_popup(row_idx, edit_var.get()))
            button.grid(column=0, row=2)

    def close_popup(row_idx=-1, minute_str=""):
        nonlocal popup
        if popup is not None:
            popup.destroy()
        popup = None

        if row_idx in row_data:
            ms = 0
            try:
                ms = int(float(minute_str) * 60 * 1000)
            except (ValueError, OverflowError):
                traceback.print_exc()

            row_time_var = row_data[row_idx].time_var
            new_time = max(0, row_time_var.get() + ms)
            row_time_var.set(new_time)
            update_radio_button_label(row_idx)

    dragging_var = tk.IntVar(value=-1)

    def handle_mouse_event(i, evt: tk.Event):
        if evt.type == tk.EventType.Motion:
            if i == dragging_var.get():
                mx, my = (evt.x + evt.widget.winfo_rootx() - rowframe.winfo_rootx(),
                          evt.y + evt.widget.winfo_rooty() - rowframe.winfo_rooty())
                for row in range(len(row_order)):
                    bbx, bby, bbw, bbh = rowframe.grid_bbox(0, row, 100, row)
                    if bbx < mx < bbx + bbw and bby < my < bby + bbh:
                        set_row_order_index(i, row)
                        break
        elif evt.type == tk.EventType.ButtonPress:
            dragging_var.set(i)
        elif evt.type == tk.EventType.ButtonRelease:
            dragging_var.set(-1)

    def add_new_activity():
        nonlocal next_idx
        i = (next_idx := next_idx + 1) - 1

        radio_btn = ttk.Radiobutton(rowframe, text=f"0:00:00", padding="2 2 8 2", variable=active_row_var, value=i)

        name_var = tk.StringVar(value=f"Activity {i + 1}")
        time_var = tk.IntVar(value=0)

        name_label = ttk.Entry(rowframe, textvariable=name_var, font=MAIN_FONT)
        clear_btn = ttk.Button(rowframe, text="Clear", width=5, command=lambda _i=i: clear_time(_i))
        edit_btn = ttk.Button(rowframe, text="Edit", width=4, command=lambda _i=i: pop_edit_field(_i))
        delete_btn = ttk.Button(rowframe, text="✖", width=2, command=lambda _i=i: remove_activity(_i))

        hamburger_btn = ttk.Button(rowframe, text="☰", width=2)
        hamburger_btn.bind("<Motion>", lambda evt, _i=i: handle_mouse_event(i, evt))
        hamburger_btn.bind("<ButtonPress>", lambda evt, _i=i: handle_mouse_event(i, evt))
        hamburger_btn.bind("<ButtonRelease>", lambda evt, _i=i: handle_mouse_event(i, evt))

        row_order.append(i)
        row_data[i] = RowData(i, radio_btn, name_var, time_var,
                              (radio_btn, name_label, clear_btn, edit_btn, hamburger_btn, delete_btn))

        update_radio_button_label(i)
        update_widget_positions(i)

        for widget in row_data[i].widgets:
            add_global_keybinds(widget)

    def update_widget_positions(i):
        if i in row_data and i in row_order:
            y = row_order.index(i)
            for x, widget in enumerate(row_data[i].widgets):
                if isinstance(widget, (tk.Entry, ttk.Entry)):
                    widget.grid(column=x, row=y, sticky="ew")
                    rowframe.grid_columnconfigure(x, weight=1)
                else:
                    widget.grid(column=x, row=y)
                    rowframe.grid_columnconfigure(x, weight=0)
        elif i in row_data:
            for widget in row_data[i].widgets:
                widget.grid_remove()

    def set_row_order_index(i, new_idx):
        if i in row_data and i in row_order:
            old_idx = row_order.index(i)
            new_idx = max(0, min(new_idx, len(row_order) - 1))
            if old_idx != new_idx:
                row_order.pop(old_idx)
                row_order.insert(new_idx, i)

                for idx in range(min(old_idx, new_idx), len(row_order)):
                    update_widget_positions(row_order[idx])

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
        def change_active_row(dy):
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

        widget.bind("<Up>", lambda evt: change_active_row(-1))
        widget.bind("<Down>", lambda evt: change_active_row(1))

    for _ in range(5):
        add_new_activity()

    pause_btn = ttk.Radiobutton(mainframe, text=f"Paused", variable=active_row_var, value=-1)
    pause_btn.grid(column=0, row=2, sticky="w")
    set_active_row(-1)

    mainframe.grid_rowconfigure(3, weight=1)

    control_panel = ttk.Frame(mainframe)
    control_panel.grid(column=0, row=4, sticky="e")

    add_new_btn = ttk.Button(control_panel, text="Add Activity", command=lambda: add_new_activity())
    add_new_btn.grid(column=0, row=0)

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
