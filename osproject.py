# MIT License

# Copyright (c) 2020 Tirth Patel & Tirth Hihoriya

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Animation for the Round Robin scheduling algorithm
commonly used in distributed or clustered systems
like Google Colab and Amazon AWS to schedule the server
requests.
"""

import time
from threading import Thread
import re
import os
import math
import statistics
import tkinter as tk
import tkinter.messagebox as msg

# import numpy as np
# import matplotlib
# import matplotlib.pyplot as plt
# from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
# from matplotlib.figure import Figure
# matplotlib.use("TkAgg")

# We are subclassing Tkinkter's `Label` object
# to implement the less than (`<`) opertor which
# is a neccessary method to push/pop object of
# type `tk.Label` in a `heapq` heap.
class Label(tk.Label):
    def __init__(self, process_object, *args, **kwargs):
        self.process_object = process_object
        super().__init__(*args, **kwargs)

    def __lt__(self, other):
        # Get the text object of both labels and
        # split them using .split method. The last
        # element in the list is the arrival time
        # against which we want to compare
        fat = self.process_object.arrival_time
        sat = other.process_object.arrival_time
        return fat < sat


# Alias the subclassed object back to the tkinter's label
tk.Label = Label


class Process(object):
    """Initialize a process control block.

    Parameters
    ----------
    pid: int
        The process id

    burst_time: float
        The burst time of the process. If not known,
        pass `None` and the burst time will be inferred
        during runtime

    arrival_time: float
        The arrival time of the process.
    """

    def __init__(self, pid, burst_time, arrival_time):
        self.pid = pid
        self.burst_time = burst_time
        self.arrival_time = arrival_time

        # Attributes to do some book-keeping
        # during scheduling
        self.admitted_time = None
        self.last_preempted = None
        self.terminated_time = None
        self.waiting_time = None
        self.runtime = None

    def get_meta(self):
        msg = (
            f"Burst time:   \t{self.burst_time}\n"
            f"Total Runtime:\t{self.runtime}\n"
            # f"Waiting Time: \t{self.waiting_time:.1f}\n"
            f"Terminated:   \t{self.terminated_time}"
        )
        return msg

    def __repr__(self):
        # We return a message of the form
        # PID: <process.id>
        # Burst Time: <process.burst_time>
        # Arrival Time: <process.arrival_time>
        msg = f"PID:\t\t{self.pid}\n"
        msg += f"Burst Time:\t{self.burst_time:.1f}\n"
        msg += f"Arrival Time:\t{self.arrival_time:.1f}"
        if self.terminated_time is not None:
            msg += "\n"
            msg += self.get_meta()
        return msg

    def __str__(self):
        return self.__repr__()


class RoundRobin(tk.Tk):
    """The round robin algorithm used in
    Operating Systems to schedule processes.

    Parameters
    ----------
    tasks: optional, list
        A list of tasks to be inserted at runtime.
        The list must contain `tk.Label` objects with
        the text field of each label containing
        `Process` objects.
    """

    def __init__(self, filename="process_meta.csv", tasks=None):
        super().__init__()

        self.filename = filename

        # We create a seperate canvas to put all
        # our tasks related widgets in.
        self.tasks_canvas = tk.Canvas(self)

        # We now create a tasks frame to place all
        # our tasks label on and display them using the
        # `tasks_canvas` we made.
        self.tasks_frame = tk.Frame(self.tasks_canvas)

        # A seperate `text_frame` to take the user input
        self.text_frame = tk.Frame(self)

        # A scrollbar instance to place in our `tasks_canvas`.
        # We don't place it on the frame as we need to configure
        # it later and change the position of frames!
        self.scrollbar = tk.Scrollbar(
            self.tasks_canvas, orient="vertical", command=self.tasks_canvas.yview
        )

        # We set the scrollbar to the `tasks_canvas`
        self.tasks_canvas.configure(yscrollcommand=self.scrollbar.set)

        # We start of by first initializing the list
        # of tasks. Here, the list of tasks contain
        # instances of the labels we wnat to display.
        if not tasks:
            self.tasks = []
        else:
            self.tasks = tasks

        # This is the title of our app.
        self.title("Round Robin Algorithm")

        # This is the size of the canvas
        self.geometry("300x400")

        # `tk.Text` is a text box where the user can enter a string as input.
        # We place this text box at the bottom of the canvas and set the focus
        # of the keyboard at that text box. Notice that the text box goes in
        # `text_frame`
        self.task_create = tk.Text(self.text_frame, height=2, bg="white", fg="black")

        # We place the `tasks_canvas` and `scrollbar` on the root
        self.tasks_canvas.pack(side=tk.TOP, fill="both", expand=1)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # We create a new window to display the `tasks_canvas`.
        # We will not pack (place) the `tasks_frame` now as the
        # window already has put it for us. (see `window` parameter).
        self.canvas_frame = self.tasks_canvas.create_window(
            (0, 0), window=self.tasks_frame, anchor="n"
        )

        # We now pack rest of the widgets
        self.task_create.pack(side=tk.BOTTOM, fill=tk.X)
        self.text_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.task_create.focus_set()

        # Initialize the initial label that defines the
        # format of input.
        self.placeholder_text = tk.Label(
            None,
            self.tasks_frame,
            text="Add process here. The process must have the form:\n"
            "<pid (int)> ; <arrival time (float)> ; <burst time (float)> ; ...",
            bg="lightgrey",
            fg="black",
            pady=10,
            font=("Verdana", 12),
        )

        # We then bind the delete button with the placeholder and
        # pack it onto our canvas
        self.placeholder_text.bind("<Button-1>", self.remove_task)
        self.placeholder_text.pack(side=tk.TOP, fill=tk.X)

        # place each task at the top of our canvas
        for task in self.tasks:
            task.pack(side=tk.TOP, fill=tk.X)

        # This big block of bind does the following:
        #  - First, the `<Return>` command triggers the add_tasks method
        #  - the `<Configure>` command is triggered whenever the size.
        #    of the window is changed and it triggers `on_frame_configure`.
        #    and task_width methods that set the width of the `tasks_canvas`.
        #    and the frame width accordingly!
        #  - Button-1 is the left mouse click which triggers `remove_task`.
        #  - `Button-4`, `Button-5` and `MouseWheel` trigger `mouse_scroll` method.
        self.bind("<Return>", self.add_task)
        self.bind("<Configure>", self.on_frame_configure)
        self.bind_all("<MouseWheel>", self.mouse_scroll)
        self.bind_all("<Button-4>", self.mouse_scroll)
        self.bind_all("<Button-5>", self.mouse_scroll)
        self.tasks_canvas.bind("<Configure>", self.task_width)

        # The color schemes that we are going to use in the canvas.
        self.color_schemes = [
            {"bg": "lightgrey", "fg": "black"},
            {"bg": "grey", "fg": "white"},
        ]

        # We have interfaced the animation as follows. We create a stop_bit
        # which records if the user has interrupted using a `Stop` button.
        # Both start and stop button are represented by a
        # `self.start_animation` tk widget. This button widget triggers the
        # `self.manage_animation_thread` method that launches a thread for
        # animation. For further details, refer the method `self.manage_animation_thread`
        # Finally we pack the button onto our root.
        self.stop_bit = 0
        self.start_animation = tk.Button(
            self, text="Start", command=self.manage_animation_thread
        )
        self.start_animation.pack(side=tk.TOP)
        self.time_quantum_method = tk.StringVar(self)
        self.time_quantum_method.set("Arithmetic")
        methods = {"Arithmetic", "Geometric", "Harmonic"}
        self.methods_menu = tk.OptionMenu(self, self.time_quantum_method, *methods)
        self.methods_menu.pack(side=tk.TOP)

    def manage_animation_thread(self):
        """Manages the animation thread. It is triggers to start and stop
        the animation. It is done in the following way:
         - If the widget `text` contains `Start`, it creates and launches a
           thread that runs the method `self.run_animation`. Before we actually
           do that, we need to set stop_bit=0 to indicate that the animation
           hasn't been interruped yet. Then, we change the text of the widget
           from `Start` to `Stop`. Then, we need to finalize the tasks list
           by calling the method `self.finalize_tasks_list`. We then start the
           animation.
         - If the widget `text` contains `Stop`, it sets the stop_bit=1, waits for
           the thread to complete its task (by calling a `join()` on it) and finally
           we clean the `self.tasks_canvas` by removing all the tasks. Finally, the text
           of the widget is changed to `Start` so the user can restart the animation.
        """
        if self.start_animation["text"] == "Start":
            self.thread_for_animation = Thread(target=self.run_animation)
            self.stop_bit = 0
            self.start_animation.config(text="Stop")
            self.finalize_tasks_list()
            self.thread_for_animation.start()
        elif self.start_animation["text"] == "Stop":
            self.stop_bit = 1
            self.thread_for_animation.join()
            self.start_animation.config(text="Start")
            self.tasks = self.terminated_tasks
            self.save_results()
            self.display_results()
            self.calculate_metrics()
            self.new_tasks.clear()

    def calculate_metrics(self):
        """Calculates throughput, average turnaround time and average waiting time"""
        self.throughput = statistics.mean(
            [
                float(task.process_object.terminated_time)
                for task in self.terminated_tasks
            ]
        )
        self.avg_turnaround_time = statistics.mean(
            [
                float(
                    task.process_object.terminated_time
                    - task.process_object.admitted_time
                )
                for task in self.terminated_tasks
            ]
        )
        self.avg_waiting_time = statistics.mean(
            [float(task.process_object.waiting_time) for task in self.terminated_tasks]
        )
        self.placeholder_text.config(
            text=f"Throughput           :   {self.throughput:.4f}\n"
            f"Avg. TurnAround Time :   {self.avg_turnaround_time:.4f}\n"
            f"Avg. Waiting Time    :   {self.avg_waiting_time:.4f}\n"
            f"No latency assumed. So, time to context switch is 0."
        )

    def save_results(self):
        try:
            with open(self.filename, "w") as f:
                f.write(
                    "pid,burst_time,arrival_time,admitted_time,terminated_time,waiting_time,turnaround_time\n"
                )
                for task in self.terminated_tasks:
                    task_object = task.process_object
                    f.write(
                        f"{task_object.pid}"
                        f",{task_object.burst_time}"
                        f",{task_object.arrival_time}"
                        f",{task_object.admitted_time}"
                        f",{task_object.terminated_time}"
                        f",{task_object.waiting_time}"
                        f",{task_object.terminated_time-task_object.admitted_time}\n"
                    )
        except Exception as e:
            print(e.with_traceback())
            msg.showerror(
                title="Error during saving",
                message="Cannot save results! Make sure the directory entered exists",
            )
            raise e

    def display_results(self):
        for i, task in enumerate(self.terminated_tasks):
            task.bind("<Button-1>", self.remove_task)
            task.pack(side=tk.TOP, fill=tk.X)
            task.config(text=task.process_object.__repr__())
        self.recolor_tasks()

    def make_task(self, text):
        # Input is always in the form "PID; ARRIVAL_TIME; BURST_TIME"
        # We need to parse it so an `Process` object can be created
        try:
            re_ex = r" *; *"
            pattern = re.compile(re_ex)
            attr = pattern.split(text)
            task = Process(
                pid=int(attr[0]), arrival_time=int(attr[1]), burst_time=int(attr[2])
            )
            return task
        except Exception as e:
            msg.showerror(
                title="Invalid input",
                message="You have entered a invalid input. Please check and try again!",
            )
            raise e

    def add_task(self, event=None):
        # print("Event recorded: ", event)
        # We will first `get` the input that the user entered
        # in the `task_create` text box.
        task_text = self.task_create.get(1.0, tk.END).strip()

        if len(task_text) > 0:
            # Create a new task as a `Label` to be placed
            # at the top of the canvas
            # Parse the task just arrived and create a process
            arrived_task = self.make_task(task_text)
            new_task = tk.Label(
                arrived_task,
                self.tasks_frame,
                text=arrived_task,
                pady=10,
                font=("Verdana", 12),
            )

            self.set_task_color(len(self.tasks) + 1, new_task)

            # Place the new task onto the canvas.
            new_task.bind("<Button-1>", self.remove_task)
            new_task.pack(side=tk.TOP, fill=tk.X)

            # heapq.heappush(self.tasks, new_task)
            self.tasks.append(new_task)

        # Delete method of `tk.Text` deletes the text
        # from the first argument to the second argument.
        self.task_create.delete(1.0, tk.END)

    def remove_task(self, event):
        # print("Event recorded: ", event)
        task = event.widget
        message = "Are you sure you want to delete"
        if msg.askyesno("Confirm!", message + ' "' + task.cget("text") + '"?'):
            self.tasks.remove(event.widget)
            event.widget.destroy()
            self.recolor_tasks()

    def recolor_tasks(self):
        for index, task in enumerate(self.tasks):
            self.set_task_color(index + 1, task)

    def set_task_color(self, index, new_task):
        _, text_color_scheme = divmod(index, 2)

        my_color_choice = self.color_schemes[text_color_scheme]

        # Configure is used to change particular fields of the
        # object on the canvas. You can change the label text,
        # bg, fg, padx, pady, etc...
        new_task.configure(bg=my_color_choice["bg"])
        new_task.configure(fg=my_color_choice["fg"])

    def on_frame_configure(self, event=None):
        self.tasks_canvas.configure(scrollregion=self.tasks_canvas.bbox("all"))

    def task_width(self, event):
        # print("Event recorded: ", event)
        canvas_width = event.width
        self.tasks_canvas.itemconfig(self.canvas_frame, width=canvas_width)

    def mouse_scroll(self, event):
        # print("Event recorded: ", event)
        # print(f"MouseScroll Delta: {event.delta}, MouseScroll Num: {event.num}")
        if event.delta:
            self.tasks_canvas.yview_scroll(int(-1 * event.delta / 120), "units")
        else:
            if event.num == 5:
                move = 1
            else:
                move = -1
            self.tasks_canvas.yview_scroll(move, "units")

    def finalize_tasks_list(self):
        tmp_tasks = sorted(self.tasks)
        for task in self.tasks:
            task.pack_forget()
        self.tasks.clear()
        self.new_tasks = []
        self.terminated_tasks = []
        for task in tmp_tasks:
            self.new_tasks.append(task)

    def get_time_quantum(self):
        method = self.time_quantum_method.get()
        if method == "Arithmetic":
            tq = statistics.mean(
                [task.process_object.burst_time for task in self.tasks]
            )
        elif method == "Geometric":
            tq = math.sqrt(sum([task.process_object.burst_time for task in self.tasks]))
        elif method == "Harmonic":
            tq = 1.0 / statistics.mean(
                [1.0 / task.process_object.burst_time for task in self.tasks]
            )
        return round(tq, 1)

    def get_new_tasks(self, time_elapsed):
        while (
            self.new_tasks
            and self.new_tasks[0].process_object.arrival_time <= time_elapsed
        ):
            task = self.new_tasks.pop(0)
            task.process_object.last_preempted = time_elapsed
            task.process_object.waiting_time = (
                time_elapsed - task.process_object.arrival_time
            )
            task.process_object.admitted_time = time_elapsed
            task.process_object.runtime = 0.0
            self.set_task_color(len(self.tasks) + 1, task)
            task.pack(side=tk.TOP, fill=tk.X)
            self.tasks.append(task)

    def run_animation(self):
        """The core animation method. All the animation magic happens here.
        It is run by a thread `RoundRobinObject.thread_for_animation`
        You can operate on the thread if needed.

        ===========================================================
                                ALGORITHM
        ============================================================

        1. All the present processes are assigned to ready queue

        2. While (ready queue is not empty)

        3. Calculate quantum time (𝑞𝑡 ) using different means:

                𝑞𝑡 = 𝐴𝑟𝑖𝑡ℎ𝑚𝑒𝑡𝑖𝑐 𝑀𝑒𝑎𝑛 𝑜𝑓 𝐵𝑢𝑟𝑠𝑡 𝑇𝑖𝑚𝑒𝑠
                                or
                𝑞𝑡 = 𝐺𝑒𝑜𝑚𝑒𝑡𝑟𝑖𝑐 𝑀𝑒𝑎𝑛 𝑜𝑓 𝐵𝑢𝑟𝑠𝑡 𝑇𝑖𝑚𝑒𝑠
                                or
                𝑞𝑡 = 𝐻𝑎𝑟𝑚𝑜𝑛𝑖𝑐 𝑀𝑒𝑎𝑛 𝑜𝑓 𝐵𝑢𝑟𝑠𝑡 𝑇𝑖𝑚𝑒𝑠

        4. Assign 𝑞𝑡 to processes (P)
        𝑃𝑖 ← 𝑞𝑡
        𝑖 = 𝑖 + 1

        5. If (i<number of processes) then go to step 4

        6. If a new process is arrived:
        Update ready queue and go to step 3

        7. Calculate average turnaround time, average waiting
        time and context switches

        8. End

        ==============================================================
        """
        time_quantum = 1.0
        time_elapsed = 0.0
        while True:
            if self.stop_bit == 1:
                break
            self.get_new_tasks(time_elapsed)
            PREEMTED_OR_TERMINATED = 0
            if not self.tasks:
                self.placeholder_text.config(
                    text=f"Time Elapsed: {time_elapsed:.1f}\nCPU Idle"
                )
            elif self.tasks[0].process_object.arrival_time > time_elapsed:
                self.placeholder_text.config(
                    text=f"Time Elapsed: {time_elapsed:.1f}\nCPU Idle"
                )
            else:
                time_quantum = self.get_time_quantum()
                task = self.tasks.pop(0)
                task_object = task.process_object
                task_object.waiting_time += time_elapsed - task_object.last_preempted
                task.pack_forget()
                self.recolor_tasks()
                # if task_object.admitted_time is None:
                #     task_object.admitted_time = time_elapsed
                #     task_object.runtime = 0.
                runtime = 0.0
                while True:
                    if task_object.runtime == task_object.burst_time:
                        # time_elapsed -= task_object.runtime - task_object.burst_time
                        self.placeholder_text.config(
                            text=f"Time Elapsed: {time_elapsed:.1f}\n"
                            f"Process {task_object.pid} Terminated"
                        )
                        task_object.terminated_time = time_elapsed
                        task_object.last_preempted = time_elapsed
                        self.terminated_tasks.append(task)
                        task.pack_forget()
                        PREEMTED_OR_TERMINATED = 1
                        break
                    elif runtime == time_quantum:
                        task_object.last_preempted = time_elapsed
                        self.set_task_color(len(self.tasks) + 1, task)
                        task.pack(side=tk.TOP, fill=tk.X)
                        self.tasks.append(task)
                        self.placeholder_text.config(
                            text=f"Time Elapsed: {time_elapsed:.1f}\n"
                            f"Process {task_object.pid} Preempted"
                        )
                        PREEMTED_OR_TERMINATED = 1
                        break
                    self.placeholder_text.config(
                        text=f"Time Elapsed:\t{time_elapsed:.1f}\n"
                        f"Running Process\t{task_object.pid}\n"
                        f"Runtime in this cycle: {runtime:.1f}\n"
                        f"{task_object.get_meta()}"
                    )
                    runtime = round(runtime + 0.1, 1)
                    task_object.runtime = round(task_object.runtime + 0.1, 1)
                    self.get_new_tasks(time_elapsed)
                    time_elapsed = round(time_elapsed + 0.1, 1)
                    time.sleep(0.05)
            if not PREEMTED_OR_TERMINATED:
                self.get_new_tasks(time_elapsed)
                time_elapsed = round(time_elapsed + 0.1, 1)
            time.sleep(0.05)


if __name__ == "__main__":
    todo = RoundRobin()
    todo.mainloop()
