import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
import requests
from datetime import datetime, timedelta
import calendar

class TimetableFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Configure grid
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header
        self.header = ctk.CTkFrame(self)
        self.header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20,0))
        
        self.title = ctk.CTkLabel(self.header, text="Weekly Timetable",
                                font=ctk.CTkFont(size=24, weight="bold"))
        self.title.pack(side="left", padx=10)
        
        self.new_timetable_button = ctk.CTkButton(self.header, text="Create New Timetable",
                                                command=self.show_create_timetable)
        self.new_timetable_button.pack(side="right", padx=10)

        # Main content area
        self.content = ctk.CTkFrame(self)
        self.content.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        self.content.grid_columnconfigure(1, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        # Current timetable view
        self.timetable_frame = ctk.CTkFrame(self.content)
        self.timetable_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")
        
        # Days of week headers
        self.days_frame = ctk.CTkFrame(self.timetable_frame)
        self.days_frame.pack(fill="x", padx=10, pady=5)
        
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for i, day in enumerate(days):
            frame = ctk.CTkFrame(self.days_frame)
            frame.grid(row=0, column=i, sticky="ew", padx=2)
            frame.grid_columnconfigure(0, weight=1)
            
            label = ctk.CTkLabel(frame, text=day, font=ctk.CTkFont(weight="bold"))
            label.grid(sticky="ew", pady=5)
            
        self.days_frame.grid_columnconfigure(tuple(range(7)), weight=1)

        # Targets for each day
        self.targets_frame = ctk.CTkFrame(self.timetable_frame)
        self.targets_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        for i in range(7):
            frame = ctk.CTkFrame(self.targets_frame)
            frame.grid(row=0, column=i, sticky="nsew", padx=2)
            frame.grid_columnconfigure(0, weight=1)
            
        self.targets_frame.grid_columnconfigure(tuple(range(7)), weight=1)
        self.targets_frame.grid_rowconfigure(0, weight=1)

        # History section
        self.history_frame = ctk.CTkFrame(self)
        self.history_frame.grid(row=2, column=0, columnspan=2, sticky="ew",
                              padx=20, pady=(0,20))
        
        self.history_label = ctk.CTkLabel(self.history_frame, text="Previous Timetables",
                                       font=ctk.CTkFont(size=18, weight="bold"))
        self.history_label.pack(pady=10)
        
        self.history_list = ctk.CTkFrame(self.history_frame)
        self.history_list.pack(fill="x", padx=10, pady=5)

    def update_content(self):
        self.load_current_timetable()
        self.load_timetable_history()

    def load_current_timetable(self):
        try:
            headers = {'Authorization': f'Bearer {self.controller.token}'}
            response = requests.get('http://localhost:5000/timetable/current',
                                 headers=headers)
            
            # Clear existing targets
            for frame in self.targets_frame.winfo_children():
                for widget in frame.winfo_children():
                    widget.destroy()

            if response.status_code == 200:
                data = response.json()
                targets_by_day = data['targets']
                
                for day in range(7):
                    frame = self.targets_frame.winfo_children()[day]
                    day_targets = targets_by_day.get(str(day), [])
                    
                    for i, target in enumerate(day_targets):
                        target_frame = ctk.CTkFrame(frame)
                        target_frame.pack(fill="x", padx=5, pady=2)
                        
                        text = target['description']
                        if len(text) > 30:
                            text = text[:27] + "..."
                            
                        label = ctk.CTkLabel(target_frame, text=text,
                                          wraplength=150)
                        label.pack(side="left", padx=5)
                        
                        if not target['completed']:
                            complete_btn = ctk.CTkButton(
                                target_frame,
                                text="✓",
                                width=30,
                                command=lambda t=target: self.complete_target(t['id'])
                            )
                            complete_btn.pack(side="right", padx=5)
                        else:
                            complete_label = ctk.CTkLabel(target_frame, text="✓",
                                                       text_color="green")
                            complete_label.pack(side="right", padx=5)
                            
        except requests.exceptions.RequestException:
            messagebox.showerror("Error", "Could not load timetable")

    def load_timetable_history(self):
        try:
            headers = {'Authorization': f'Bearer {self.controller.token}'}
            response = requests.get('http://localhost:5000/timetable/history',
                                 headers=headers)
            
            # Clear existing history
            for widget in self.history_list.winfo_children():
                widget.destroy()

            if response.status_code == 200:
                timetables = response.json()
                
                for timetable in timetables:
                    frame = ctk.CTkFrame(self.history_list)
                    frame.pack(fill="x", pady=2)
                    
                    week_start = datetime.fromisoformat(timetable['week_start'])
                    week_end = week_start + timedelta(days=6)
                    
                    date_label = ctk.CTkLabel(
                        frame,
                        text=f"{week_start.strftime('%b %d')} - {week_end.strftime('%b %d')}"
                    )
                    date_label.pack(side="left", padx=10)
                    
                    completion = timetable['completion_rate'] * 100
                    stats_label = ctk.CTkLabel(
                        frame,
                        text=f"Completed: {completion:.1f}% ({timetable['completed_targets']}/{timetable['total_targets']})"
                    )
                    stats_label.pack(side="right", padx=10)
                    
        except requests.exceptions.RequestException:
            messagebox.showerror("Error", "Could not load timetable history")

    def complete_target(self, target_id):
        try:
            headers = {'Authorization': f'Bearer {self.controller.token}'}
            response = requests.post(f'http://localhost:5000/timetable/target/{target_id}/complete',
                                  headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                messagebox.showinfo("Success",
                                 f"Target completed! You earned {result['xp_gained']} XP")
                self.load_current_timetable()
            else:
                messagebox.showerror("Error", "Failed to complete target")
                
        except requests.exceptions.RequestException:
            messagebox.showerror("Error", "Could not connect to server")

    def show_create_timetable(self):
        dialog = CreateTimetableDialog(self)
        self.wait_window(dialog)
        self.update_content()

class CreateTimetableDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        
        self.title("Create New Timetable")
        self.geometry("800x600")

        # Week selection
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        
        self.week_frame = ctk.CTkFrame(self)
        self.week_frame.pack(fill="x", padx=20, pady=20)
        
        self.week_label = ctk.CTkLabel(self.week_frame, text="Week Starting:")
        self.week_label.pack(side="left", padx=5)
        
        self.week_start = monday
        self.week_display = ctk.CTkLabel(
            self.week_frame,
            text=monday.strftime("%B %d, %Y")
        )
        self.week_display.pack(side="left", padx=5)

        # Copy previous week option
        self.copy_frame = ctk.CTkFrame(self)
        self.copy_frame.pack(fill="x", padx=20, pady=10)
        
        self.copy_var = tk.BooleanVar(value=False)
        self.copy_check = ctk.CTkCheckBox(
            self.copy_frame,
            text="Copy goals from previous week",
            variable=self.copy_var,
            command=self.toggle_copy
        )
        self.copy_check.pack(side="left", padx=5)

        # Daily targets
        self.days_frame = ctk.CTkScrollableFrame(self)
        self.days_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.day_targets = {}  # Store targets for each day
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for i, day in enumerate(days):
            day_frame = ctk.CTkFrame(self.days_frame)
            day_frame.pack(fill="x", pady=5)
            
            day_label = ctk.CTkLabel(day_frame, text=day,
                                  font=ctk.CTkFont(weight="bold"))
            day_label.pack(pady=5)
            
            targets_frame = ctk.CTkFrame(day_frame)
            targets_frame.pack(fill="x", padx=10, pady=5)
            
            # Add target button
            max_targets = 5 if i >= 5 else 3  # 5 for weekends, 3 for weekdays
            add_btn = ctk.CTkButton(
                day_frame,
                text=f"Add Target (0/{max_targets})",
                command=lambda d=i: self.add_target(d)
            )
            add_btn.pack(pady=5)
            
            self.day_targets[i] = {
                'frame': targets_frame,
                'button': add_btn,
                'targets': [],
                'max_targets': max_targets
            }
        
        # Create button
        self.create_button = ctk.CTkButton(self, text="Create Timetable",
                                       command=self.create_timetable)
        self.create_button.pack(pady=20)

    def toggle_copy(self):
        if self.copy_var.get():
            try:
                headers = {'Authorization': f'Bearer {self.parent.controller.token}'}
                response = requests.get('http://localhost:5000/timetable/current',
                                    headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    # Clear existing targets
                    for day_data in self.day_targets.values():
                        for target in day_data['targets']:
                            target['frame'].destroy()
                        day_data['targets'] = []
                        self.update_add_button(day_data)
                    
                    # Add targets from previous week
                    for day, targets in data['targets'].items():
                        day = int(day)
                        for target in targets:
                            self.add_target(day, target['description'])
                else:
                    messagebox.showwarning("Warning", "No previous timetable to copy from")
                    self.copy_var.set(False)
                    
            except requests.exceptions.RequestException:
                messagebox.showerror("Error", "Could not fetch previous timetable")
                self.copy_var.set(False)

    def update_add_button(self, day_data):
        count = len(day_data['targets'])
        max_targets = day_data['max_targets']
        day_data['button'].configure(
            text=f"Add Target ({count}/{max_targets})",
            state="normal" if count < max_targets else "disabled"
        )

    def add_target(self, day, description=""):
        day_data = self.day_targets[day]
        
        if len(day_data['targets']) >= day_data['max_targets']:
            messagebox.showwarning(
                "Warning",
                f"Maximum {day_data['max_targets']} targets allowed for this day"
            )
            return
        
        target_frame = ctk.CTkFrame(day_data['frame'])
        target_frame.pack(fill="x", pady=2)
        
        entry = ctk.CTkEntry(target_frame)
        entry.pack(side="left", expand=True, fill="x", padx=5)
        entry.insert(0, description)
        
        delete_btn = ctk.CTkButton(target_frame, text="✕", width=30,
                                command=lambda: self.delete_target(day, target_frame))
        delete_btn.pack(side="right", padx=5)
        
        day_data['targets'].append({
            'frame': target_frame,
            'entry': entry
        })
        
        self.update_add_button(day_data)

    def delete_target(self, day, target_frame):
        day_data = self.day_targets[day]
        day_data['targets'] = [t for t in day_data['targets']
                             if t['frame'] != target_frame]
        target_frame.destroy()
        self.update_add_button(day_data)

    def create_timetable(self):
        # Validate targets
        targets_by_day = {}
        for day, day_data in self.day_targets.items():
            targets = []
            for target in day_data['targets']:
                description = target['entry'].get().strip()
                if description:
                    targets.append(description)
            if targets:
                targets_by_day[day] = targets
        
        if not targets_by_day:
            messagebox.showerror("Error", "Please add at least one target")
            return
        
        try:
            # Create timetable
            headers = {'Authorization': f'Bearer {self.parent.controller.token}'}
            response = requests.post(
                'http://localhost:5000/timetable/',
                json={
                    'week_start': self.week_start.isoformat(),
                    'targets': targets_by_day
                },
                headers=headers
            )
            
            if response.status_code == 201:
                messagebox.showinfo("Success", "Timetable created successfully")
                self.destroy()
            else:
                error_msg = response.json().get('message', 'Failed to create timetable')
                messagebox.showerror("Error", error_msg)
                
        except requests.exceptions.RequestException:
            messagebox.showerror("Error", "Could not connect to server")
