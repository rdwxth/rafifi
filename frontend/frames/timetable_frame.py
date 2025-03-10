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
        
        self.week_label = ctk.CTkLabel(self.week_frame,
                                    text=f"Week of {monday.strftime('%B %d, %Y')}")
        self.week_label.pack()

        # Copy previous week option
        self.copy_frame = ctk.CTkFrame(self)
        self.copy_frame.pack(fill="x", padx=20, pady=10)
        
        self.copy_var = tk.BooleanVar(value=False)
        self.copy_check = ctk.CTkCheckBox(self.copy_frame,
                                       text="Copy targets from previous week",
                                       variable=self.copy_var,
                                       command=self.toggle_copy)
        self.copy_check.pack()

        # Days container
        self.days_container = ctk.CTkScrollableFrame(self)
        self.days_container.pack(expand=True, fill="both", padx=20, pady=10)
        
        # Create frames for each day
        self.day_frames = {}
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday',
                'Saturday', 'Sunday']
        
        for i, day in enumerate(days):
            frame = ctk.CTkFrame(self.days_container)
            frame.pack(fill="x", pady=5)
            
            label = ctk.CTkLabel(frame, text=day,
                              font=ctk.CTkFont(weight="bold"))
            label.pack(pady=5)
            
            targets_frame = ctk.CTkFrame(frame)
            targets_frame.pack(fill="x", padx=10, pady=5)
            
            add_btn = ctk.CTkButton(frame, text="Add Target",
                                 command=lambda d=i: self.add_target(d))
            add_btn.pack(pady=5)
            
            self.day_frames[i] = targets_frame

        # Save button
        self.save_button = ctk.CTkButton(self, text="Save Timetable",
                                      command=self.save_timetable)
        self.save_button.pack(pady=20)

        # Initialize with previous week's targets if requested
        if self.copy_var.get():
            self.load_previous_targets()

    def toggle_copy(self):
        if self.copy_var.get():
            self.load_previous_targets()
        else:
            # Clear all targets
            for frame in self.day_frames.values():
                for widget in frame.winfo_children():
                    widget.destroy()

    def load_previous_targets(self):
        try:
            headers = {'Authorization': f'Bearer {self.parent.controller.token}'}
            response = requests.get('http://localhost:5000/timetable/current',
                                 headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                targets_by_day = data['targets']
                
                for day, targets in targets_by_day.items():
                    day_idx = int(day)
                    frame = self.day_frames[day_idx]
                    
                    # Clear existing targets
                    for widget in frame.winfo_children():
                        widget.destroy()
                    
                    # Add previous targets
                    for target in targets:
                        self.add_target(day_idx, target['description'])
                        
        except requests.exceptions.RequestException:
            messagebox.showerror("Error", "Could not load previous timetable")

    def add_target(self, day, initial_text=""):
        frame = self.day_frames[day]
        max_targets = 5 if day in [5, 6] else 3
        
        if len(frame.winfo_children()) >= max_targets:
            messagebox.showwarning("Warning",
                                f"Maximum {max_targets} targets allowed for this day")
            return
            
        target_frame = ctk.CTkFrame(frame)
        target_frame.pack(fill="x", pady=2)
        
        entry = ctk.CTkEntry(target_frame)
        entry.pack(side="left", expand=True, fill="x", padx=5)
        entry.insert(0, initial_text)
        
        def remove_target():
            target_frame.destroy()
            
        remove_btn = ctk.CTkButton(target_frame, text="Remove",
                                width=60, command=remove_target)
        remove_btn.pack(side="right", padx=5)

    def save_timetable(self):
        targets = {}
        
        for day, frame in self.day_frames.items():
            day_targets = []
            for target_frame in frame.winfo_children():
                entry = target_frame.winfo_children()[0]
                text = entry.get().strip()
                if text:
                    day_targets.append(text)
            if day_targets:
                targets[day] = day_targets

        if not targets:
            messagebox.showwarning("Warning", "Please add at least one target")
            return

        try:
            headers = {'Authorization': f'Bearer {self.parent.controller.token}'}
            
            # Format data for API
            today = datetime.now()
            monday = today - timedelta(days=today.weekday())
            
            data = {
                'week_start': monday.strftime('%Y-%m-%d'),
                'targets': [
                    {'day': day, 'targets': targets}
                    for day, targets in targets.items()
                ]
            }
            
            response = requests.post('http://localhost:5000/timetable',
                                  headers=headers, json=data)
            
            if response.status_code == 201:
                messagebox.showinfo("Success", "Timetable created successfully")
                self.destroy()
            else:
                messagebox.showerror("Error", "Failed to create timetable")
                
        except requests.exceptions.RequestException:
            messagebox.showerror("Error", "Could not connect to server")
