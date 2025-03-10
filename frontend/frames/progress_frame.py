import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
import requests
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class ProgressFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Configure grid
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header
        self.header = ctk.CTkFrame(self)
        self.header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20,0))
        
        self.title = ctk.CTkLabel(self.header, text="Progress Tracker",
                                font=ctk.CTkFont(size=24, weight="bold"))
        self.title.pack(side="left", padx=10)

        # Main content area
        self.content = ctk.CTkFrame(self)
        self.content.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        self.content.grid_columnconfigure((0, 1), weight=1)
        self.content.grid_rowconfigure((0, 1), weight=1)

        # XP Progress section
        self.xp_frame = ctk.CTkFrame(self.content)
        self.xp_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        self.xp_label = ctk.CTkLabel(self.xp_frame, text="XP Progress",
                                   font=ctk.CTkFont(size=18, weight="bold"))
        self.xp_label.pack(pady=10)
        
        self.xp_progress = ctk.CTkProgressBar(self.xp_frame)
        self.xp_progress.pack(fill="x", padx=20, pady=10)
        
        self.level_label = ctk.CTkLabel(self.xp_frame, text="Level 1")
        self.level_label.pack(pady=5)
        
        self.daily_xp_label = ctk.CTkLabel(self.xp_frame,
                                        text="Daily XP Goal: 0/100")
        self.daily_xp_label.pack(pady=5)

        # Titles section
        self.titles_frame = ctk.CTkFrame(self.content)
        self.titles_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        self.titles_label = ctk.CTkLabel(self.titles_frame, text="Your Titles",
                                      font=ctk.CTkFont(size=18, weight="bold"))
        self.titles_label.pack(pady=10)
        
        self.titles_list = ctk.CTkScrollableFrame(self.titles_frame)
        self.titles_list.pack(expand=True, fill="both", padx=10, pady=10)

        # Test Performance section
        self.tests_frame = ctk.CTkFrame(self.content)
        self.tests_frame.grid(row=1, column=0, columnspan=2,
                            sticky="nsew", padx=10, pady=10)
        
        self.tests_label = ctk.CTkLabel(self.tests_frame, text="Test Performance",
                                     font=ctk.CTkFont(size=18, weight="bold"))
        self.tests_label.pack(pady=10)
        
        # Create matplotlib figure for test performance graph
        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.tests_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

        # Stats section
        self.stats_frame = ctk.CTkFrame(self.tests_frame)
        self.stats_frame.pack(fill="x", padx=10, pady=10)
        
        # Create three columns for stats
        for i in range(3):
            self.stats_frame.grid_columnconfigure(i, weight=1)
            
        # Average Score
        self.avg_score_label = ctk.CTkLabel(self.stats_frame, text="Average Score")
        self.avg_score_label.grid(row=0, column=0, pady=5)
        
        self.avg_score_value = ctk.CTkLabel(self.stats_frame, text="0%")
        self.avg_score_value.grid(row=1, column=0, pady=5)
        
        # Tests Completed
        self.tests_count_label = ctk.CTkLabel(self.stats_frame,
                                           text="Tests Completed")
        self.tests_count_label.grid(row=0, column=1, pady=5)
        
        self.tests_count_value = ctk.CTkLabel(self.stats_frame, text="0")
        self.tests_count_value.grid(row=1, column=1, pady=5)
        
        # Recent Score
        self.recent_score_label = ctk.CTkLabel(self.stats_frame,
                                            text="Most Recent Score")
        self.recent_score_label.grid(row=0, column=2, pady=5)
        
        self.recent_score_value = ctk.CTkLabel(self.stats_frame, text="N/A")
        self.recent_score_value.grid(row=1, column=2, pady=5)

    def update_content(self):
        self.load_user_progress()
        self.load_titles()
        self.load_test_performance()

    def load_user_progress(self):
        try:
            headers = {'Authorization': f'Bearer {self.controller.token}'}
            response = requests.get('http://localhost:5000/user/profile',
                                 headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                xp = data['xp']
                
                # Calculate level and progress
                level = 1 + (xp // 1000)  # Level up every 1000 XP
                progress = (xp % 1000) / 1000  # Progress to next level
                
                self.xp_progress.set(progress)
                self.level_label.configure(text=f"Level {level}")
                
                # Update daily XP goal
                daily_xp = data.get('daily_xp', 0)
                self.daily_xp_label.configure(
                    text=f"Daily XP Goal: {daily_xp}/100"
                )
                
        except requests.exceptions.RequestException:
            messagebox.showerror("Error", "Could not load user progress")

    def load_titles(self):
        # Clear existing titles
        for widget in self.titles_list.winfo_children():
            widget.destroy()

        try:
            headers = {'Authorization': f'Bearer {self.controller.token}'}
            response = requests.get('http://localhost:5000/user/titles',
                                 headers=headers)
            
            if response.status_code == 200:
                titles = response.json()
                
                for title in titles:
                    frame = ctk.CTkFrame(self.titles_list)
                    frame.pack(fill="x", pady=2)
                    
                    title_label = ctk.CTkLabel(frame, text=title['title'])
                    title_label.pack(side="left", padx=10)
                    
                    unlocked_date = datetime.fromisoformat(title['unlocked_at'])
                    date_label = ctk.CTkLabel(
                        frame,
                        text=f"Unlocked: {unlocked_date.strftime('%b %d, %Y')}"
                    )
                    date_label.pack(side="right", padx=10)
                    
        except requests.exceptions.RequestException:
            messagebox.showerror("Error", "Could not load titles")

    def load_test_performance(self):
        try:
            headers = {'Authorization': f'Bearer {self.controller.token}'}
            response = requests.get('http://localhost:5000/user/tests',
                                 headers=headers)
            
            if response.status_code == 200:
                tests = response.json()
                
                if not tests:
                    return
                    
                # Calculate statistics
                scores = [test['score'] for test in tests]
                avg_score = sum(scores) / len(scores)
                recent_score = scores[-1]
                
                self.avg_score_value.configure(text=f"{avg_score:.1f}%")
                self.tests_count_value.configure(text=str(len(tests)))
                self.recent_score_value.configure(text=f"{recent_score:.1f}%")
                
                # Update graph
                self.ax.clear()
                
                # Get last 10 tests
                recent_tests = tests[-10:]
                dates = [datetime.fromisoformat(t['completed_at']).strftime('%m/%d')
                        for t in recent_tests]
                scores = [t['score'] for t in recent_tests]
                
                self.ax.plot(dates, scores, marker='o')
                self.ax.set_ylim(0, 100)
                self.ax.set_xlabel('Date')
                self.ax.set_ylabel('Score (%)')
                self.ax.grid(True)
                
                # Rotate x-axis labels for better readability
                plt.xticks(rotation=45)
                
                # Adjust layout to prevent label cutoff
                plt.tight_layout()
                
                self.canvas.draw()
                
        except requests.exceptions.RequestException:
            messagebox.showerror("Error", "Could not load test performance")
