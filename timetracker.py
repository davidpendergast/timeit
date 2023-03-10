import tkinter as tk
from tkinter import ttk

from ttkthemes import ThemedTk


WINDOW_TITLE = "Time Tracker"


def start():
    root = ThemedTk(theme="breeze")
    root.title("Time Tracker")
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=1)

    mainframe = ttk.Frame(root, padding="4 4 4 4")
    mainframe.grid(column=0, row=0, sticky="nsew")
    mainframe.grid_columnconfigure(0, weight=1)

    rowframe = ttk.Frame(mainframe)
    rowframe.grid(column=0, row=0, sticky="nsew")

    active_row_var = tk.IntVar()

    row_btns = []
    row_names = []
    row_times = []
    row_widgets = []

    pause_btn = None

    def update_row_button_label(row_idx) -> str:
        if 0 <= row_idx < len(row_btns):
            btn = row_btns[row_idx]
            secs = row_times[row_idx].get() // 1000
            mins = secs // 60
            hours = mins // 60
            btn_text = f"{hours}:{str(mins % 60).zfill(2)}:{str(secs % 60).zfill(2)}"
            btn.configure(text=btn_text)
            return btn_text
        else:
            return "Paused"

    def clear_time(row_idx):
        if 0 <= row_idx < len(row_times):
            row_times[row_idx].set(0)
        update_row_button_label(row_idx)
        if active_row_var.get() == row_idx:
            set_active_row(-1)

    def set_active_row(row_idx):
        if 0 <= row_idx < len(row_btns):
            row_btns[row_idx].invoke()
        elif pause_btn is not None:
            pause_btn.invoke()

    popup = None

    def pop_edit_field(row_idx):
        nonlocal popup
        if popup is not None:
            close_popup()

        if 0 <= row_idx < len(row_btns):
            popup = tk.Toplevel(root)
            popup.title(row_names[row_idx].get())
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

        if 0 <= row_idx < len(row_btns):
            minutes = 0
            try:
                minutes = int(minute_str)
            except Exception:
                pass
            row_time_var = row_times[row_idx]
            new_time = max(0, row_time_var.get() + minutes * 60 * 1000)
            row_time_var.set(new_time)
            update_row_button_label(row_idx)

    def add_new_activity(i):
        x = -1
        playpause_btn = ttk.Radiobutton(rowframe, text=f"0:00:00", variable=active_row_var, value=i)
        playpause_btn.grid(column=(x := x + 1), row=i)

        name_var = tk.StringVar(value=f"Activity {i + 1}")

        row_btns.append(playpause_btn)
        row_times.append(tk.IntVar(value=0))
        row_names.append(name_var)

        update_row_button_label(i)

        name_label = ttk.Entry(rowframe, textvariable=name_var)
        name_label.grid(column=(x := x + 1), row=i, sticky="ew")
        rowframe.grid_columnconfigure(x, weight=1)

        clear_btn = ttk.Button(rowframe, text="Clear", command=lambda _i=i: clear_time(_i))
        clear_btn.grid(column=(x := x + 1), row=i)

        edit_btn = ttk.Button(rowframe, text="Edit", command=lambda _i=i: pop_edit_field(_i))
        edit_btn.grid(column=(x := x + 1), row=i)

        row_widgets.append((playpause_btn, name_label, clear_btn, edit_btn))

    def remove_activity(i=-1):
        if i == -1:
            i = len(row_btns) - 1
        else:
            raise NotImplemented("TODO")

        if 0 <= i < len(row_btns):
            for item in row_widgets[i]:
                item.grid_remove()
                item.destroy()
            row_btns.pop(i)  # XXX fragile code here
            row_names.pop(i)
            row_times.pop(i)
            row_widgets.pop(i)

            if i == active_row_var.get():
                set_active_row(-1)

    for idx in range(5):
        add_new_activity(idx)

    pause_btn = ttk.Radiobutton(mainframe, text=f"Paused", variable=active_row_var, value=-1)
    pause_btn.grid(column=0, row=1, sticky="w")
    set_active_row(-1)

    mainframe.grid_rowconfigure(2, weight=1)

    control_panel = ttk.Frame(mainframe)
    control_panel.grid(column=0, row=3, sticky="w")

    add_new_btn = ttk.Button(control_panel, text="Add Activity", command=lambda: add_new_activity(len(row_btns)))
    add_new_btn.grid(column=0, row=0)

    remove_act_btn = ttk.Button(control_panel, text="Delete Activity", command=lambda: remove_activity())
    remove_act_btn.grid(column=1, row=0)

    def time_loop(dt):
        row_idx = active_row_var.get()
        if 0 <= row_idx < len(row_btns):
            row_time = row_times[row_idx]
            row_time.set(row_time.get() + dt)
            label_text = f"{row_names[row_idx].get()} ~ {update_row_button_label(row_idx)}"
        else:
            label_text = update_row_button_label(row_idx)

        root.title(f"{WINDOW_TITLE} [{label_text}]")
        root.after(dt, time_loop, dt)

    root.after(1000, time_loop, 1000)

    root.mainloop()


if __name__ == "__main__":
    start()
