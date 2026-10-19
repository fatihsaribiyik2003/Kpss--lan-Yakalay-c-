import calendar
import datetime as dt
import tkinter as tk
from tkinter import ttk

from .core import today


class ScanCalendar(ttk.Frame):
    MONTHS = ('', 'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
              'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık')

    def __init__(self, parent):
        super().__init__(parent, padding=(12, 12))
        current = today()
        self.year, self.month = current.year, current.month
        self.days = set()
        self.current_day = current
        ttk.Label(self, text='Tarama takvimi', font=('Segoe UI', 11, 'bold')).pack(anchor='w', pady=(0, 10))
        nav = ttk.Frame(self)
        nav.pack(fill='x')
        ttk.Button(nav, text='‹', width=2, command=lambda: self.move(-1)).pack(side='left')
        self.heading = ttk.Label(nav, anchor='center', width=17, font=('Segoe UI', 10, 'bold'))
        self.heading.pack(side='left', expand=True, fill='x')
        ttk.Button(nav, text='›', width=2, command=lambda: self.move(1)).pack(side='right')
        self.canvas = tk.Canvas(self, width=238, height=238, bg='white', highlightthickness=0)
        self.canvas.pack(pady=(10, 8))
        legend = ttk.Frame(self)
        legend.pack(anchor='w')
        dot = tk.Canvas(legend, width=14, height=18, bg='#f4f6fa', highlightthickness=0)
        dot.create_oval(4, 7, 10, 13, fill='#2785e8', outline='')
        dot.pack(side='left')
        ttk.Label(legend, text='Taranan gün', style='Muted.TLabel').pack(side='left', padx=3)
        ttk.Button(self, text='Bu ay', command=self.show_today).pack(anchor='e', pady=(8, 0))
        self.draw()

    def update_days(self, days):
        current = today()
        if days != self.days or current != self.current_day:
            self.days = set(days)
            self.current_day = current
            self.draw()

    def move(self, delta):
        value = self.year * 12 + self.month - 1 + delta
        year, month = divmod(value, 12)
        if 1 <= year <= 9999:
            self.year, self.month = year, month + 1
            self.draw()

    def show_today(self):
        self.year, self.month = today().year, today().month
        self.draw()

    def draw(self):
        self.heading.configure(text=f'{self.MONTHS[self.month]} {self.year}')
        canvas = self.canvas
        canvas.delete('all')
        cell = 34
        for col, name in enumerate(('Pt', 'Sa', 'Ça', 'Pe', 'Cu', 'Ct', 'Pa')):
            canvas.create_text(col*cell+17, 17, text=name, fill='#7b879b', font=('Segoe UI', 9))
        for row, week in enumerate(calendar.Calendar(firstweekday=0).monthdayscalendar(self.year, self.month)):
            for col, number in enumerate(week):
                if not number:
                    continue
                x, y = col*cell+17, row*cell+49
                date = dt.date(self.year, self.month, number)
                if date == self.current_day:
                    canvas.create_oval(x-12, y-12, x+12, y+12, fill='#e8f2fe', outline='')
                canvas.create_text(x, y, text=str(number), fill='#18243c', font=('Segoe UI', 10))
                if date.isoformat() in self.days:
                    canvas.create_oval(x-2.7, y+11, x+2.7, y+16.4, fill='#2785e8', outline='')
