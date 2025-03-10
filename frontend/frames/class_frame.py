import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
import requests
from datetime import datetime, timedelta

class ClassFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Configure grid
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header
        self.header = ctk.CTkFrame(self)
        self.header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20,0))
        
        self.title = ctk.CTkLabel(self.header, text="Classes",
                                font=ctk.CTkFont(size=24, weight="bold"))
        self.title.pack(side="left", padx=10)
        
        self.create_class_button = ctk.CTkButton(self.header, text="Create Class",
                                               command=self.show_create_class)
        self.create_class_button.pack(side="right", padx=5)
        
        self.join_class_button = ctk.CTkButton(self.header, text="Join Class",
                                            command=self.show_join_class)
        self.join_class_button.pack(side="right", padx=5)

        # Main content area
        self.content = ctk.CTkFrame(self)
        self.content.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        self.content.grid_columnconfigure(1, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        # Classes list
        self.classes_frame = ctk.CTkFrame(self.content)
        self.classes_frame.grid(row=0, column=0, sticky="ns", padx=(0,20))
        
        self.classes_label = ctk.CTkLabel(self.classes_frame, text="Your Classes",
                                       font=ctk.CTkFont(weight="bold"))
        self.classes_label.pack(pady=10)
        
        self.classes_list = ctk.CTkScrollableFrame(self.classes_frame, width=200)
        self.classes_list.pack(expand=True, fill="both", padx=10, pady=10)

        # Class view
        self.class_view = ctk.CTkFrame(self.content)
        self.class_view.grid(row=0, column=1, sticky="nsew")
        
        self.current_class = None

    def show_create_class(self):
        dialog = CreateClassDialog(self)
        self.wait_window(dialog)
        self.update_content()

    def show_join_class(self):
        dialog = JoinClassDialog(self)
        self.wait_window(dialog)
        self.update_content()

    def update_content(self):
        self.load_classes()
        if self.current_class:
            self.load_class_details(self.current_class)

    def load_classes(self):
        # Clear existing classes
        for widget in self.classes_list.winfo_children():
            widget.destroy()

        try:
            headers = {'Authorization': f'Bearer {self.controller.token}'}
            response = requests.get('http://localhost:5000/class/list',
                                 headers=headers)
            
            if response.status_code == 200:
                classes = response.json()
                for class_data in classes:
                    btn = ctk.CTkButton(
                        self.classes_list,
                        text=class_data['name'],
                        command=lambda c=class_data: self.load_class_details(c)
                    )
                    btn.pack(fill="x", pady=2)
        except requests.exceptions.RequestException:
            messagebox.showerror("Error", "Could not fetch classes")

    def load_class_details(self, class_data):
        self.current_class = class_data
        
        # Clear existing view
        for widget in self.class_view.winfo_children():
            widget.destroy()

        try:
            headers = {'Authorization': f'Bearer {self.controller.token}'}
            
            # Get class members
            response = requests.get(
                f'http://localhost:5000/class/{class_data["id"]}/members',
                headers=headers
            )
            
            if response.status_code != 200:
                messagebox.showerror("Error", "Could not load class details")
                return
                
            members = response.json()
            
            # Class header
            header = ctk.CTkFrame(self.class_view)
            header.pack(fill="x", padx=20, pady=10)
            
            title = ctk.CTkLabel(header, text=class_data['name'],
                              font=ctk.CTkFont(size=20, weight="bold"))
            title.pack(side="left")
            
            if class_data.get('leader_id') == self.controller.user_id:
                code_label = ctk.CTkLabel(header,
                                      text=f"Class Code: {class_data['code']}")
                code_label.pack(side="right")

            # Members section
            members_frame = ctk.CTkFrame(self.class_view)
            members_frame.pack(fill="x", padx=20, pady=10)
            
            members_label = ctk.CTkLabel(members_frame, text="Members",
                                      font=ctk.CTkFont(weight="bold"))
            members_label.pack(pady=5)
            
            for member in members:
                member_frame = ctk.CTkFrame(members_frame)
                member_frame.pack(fill="x", pady=2)
                
                name_label = ctk.CTkLabel(member_frame, text=member['username'])
                name_label.pack(side="left", padx=10)
                
                xp_label = ctk.CTkLabel(member_frame, text=f"XP: {member['xp']}")
                xp_label.pack(side="right", padx=10)
                
                if (class_data.get('leader_id') == self.controller.user_id and
                    member['id'] != self.controller.user_id):
                    kick_btn = ctk.CTkButton(
                        member_frame,
                        text="Kick",
                        width=60,
                        command=lambda m=member: self.kick_member(m['id'])
                    )
                    kick_btn.pack(side="right", padx=5)

            # Leaderboard section
            leaderboard_frame = ctk.CTkFrame(self.class_view)
            leaderboard_frame.pack(fill="x", padx=20, pady=10)
            
            leaderboard_header = ctk.CTkFrame(leaderboard_frame)
            leaderboard_header.pack(fill="x", pady=5)
            
            leaderboard_label = ctk.CTkLabel(leaderboard_header,
                                          text="Leaderboard",
                                          font=ctk.CTkFont(weight="bold"))
            leaderboard_label.pack(side="left")
            
            if class_data.get('leader_id') == self.controller.user_id:
                create_board_btn = ctk.CTkButton(
                    leaderboard_header,
                    text="Create Leaderboard",
                    command=lambda: self.show_create_leaderboard(class_data['id'])
                )
                create_board_btn.pack(side="right")

            # Get current leaderboard
            response = requests.get(
                f'http://localhost:5000/class/{class_data["id"]}/leaderboard/current',
                headers=headers
            )
            
            if response.status_code == 200:
                leaderboard = response.json()
                
                end_date = datetime.fromisoformat(leaderboard['end_date'])
                time_left = end_date - datetime.utcnow()
                
                if time_left.total_seconds() > 0:
                    time_label = ctk.CTkLabel(
                        leaderboard_frame,
                        text=f"Time remaining: {time_left.days} days"
                    )
                    time_label.pack(pady=5)
                    
                    for rank in leaderboard['rankings']:
                        rank_frame = ctk.CTkFrame(leaderboard_frame)
                        rank_frame.pack(fill="x", pady=2)
                        
                        pos_label = ctk.CTkLabel(rank_frame,
                                              text=f"#{rank['rank']}")
                        pos_label.pack(side="left", padx=10)
                        
                        name_label = ctk.CTkLabel(rank_frame,
                                               text=rank['username'])
                        name_label.pack(side="left", padx=10)
                        
                        xp_label = ctk.CTkLabel(rank_frame,
                                             text=f"XP: {rank['xp']}")
                        xp_label.pack(side="right", padx=10)
                        
        except requests.exceptions.RequestException:
            messagebox.showerror("Error", "Could not load class details")

    def kick_member(self, member_id):
        if not self.current_class:
            return
            
        if not messagebox.askyesno("Confirm",
                                 "Are you sure you want to kick this member?"):
            return
            
        try:
            headers = {'Authorization': f'Bearer {self.controller.token}'}
            response = requests.post(
                f'http://localhost:5000/class/{self.current_class["id"]}/kick/{member_id}',
                headers=headers
            )
            
            if response.status_code == 200:
                messagebox.showinfo("Success", "Member removed from class")
                self.load_class_details(self.current_class)
            else:
                messagebox.showerror("Error", "Failed to remove member")
                
        except requests.exceptions.RequestException:
            messagebox.showerror("Error", "Could not connect to server")

    def show_create_leaderboard(self, class_id):
        dialog = CreateLeaderboardDialog(self, class_id)
        self.wait_window(dialog)
        if self.current_class:
            self.load_class_details(self.current_class)

class CreateClassDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        
        self.title("Create New Class")
        self.geometry("400x200")

        self.grid_rowconfigure((0, 1, 2), weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Class name
        self.name_label = ctk.CTkLabel(self, text="Class Name:")
        self.name_label.grid(row=0, column=0, padx=20, pady=(20,0))
        
        self.name_entry = ctk.CTkEntry(self)
        self.name_entry.grid(row=1, column=0, padx=20, pady=(0,20), sticky="ew")

        # Create button
        self.create_button = ctk.CTkButton(self, text="Create Class",
                                        command=self.create_class)
        self.create_button.grid(row=2, column=0, padx=20, pady=20)

    def create_class(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Warning", "Please enter a class name")
            return

        try:
            headers = {'Authorization': f'Bearer {self.parent.controller.token}'}
            response = requests.post('http://localhost:5000/class',
                                  headers=headers,
                                  json={'name': name})
            
            if response.status_code == 201:
                result = response.json()
                messagebox.showinfo("Success",
                                 f"Class created! Class code: {result['code']}")
                self.destroy()
            else:
                messagebox.showerror("Error", "Failed to create class")
                
        except requests.exceptions.RequestException:
            messagebox.showerror("Error", "Could not connect to server")

class JoinClassDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        
        self.title("Join Class")
        self.geometry("400x200")

        self.grid_rowconfigure((0, 1, 2), weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Class code
        self.code_label = ctk.CTkLabel(self, text="Enter Class Code:")
        self.code_label.grid(row=0, column=0, padx=20, pady=(20,0))
        
        self.code_entry = ctk.CTkEntry(self)
        self.code_entry.grid(row=1, column=0, padx=20, pady=(0,20), sticky="ew")

        # Join button
        self.join_button = ctk.CTkButton(self, text="Join Class",
                                      command=self.join_class)
        self.join_button.grid(row=2, column=0, padx=20, pady=20)

    def join_class(self):
        code = self.code_entry.get().strip()
        if not code:
            messagebox.showwarning("Warning", "Please enter a class code")
            return

        try:
            headers = {'Authorization': f'Bearer {self.parent.controller.token}'}
            response = requests.post('http://localhost:5000/class/join',
                                  headers=headers,
                                  json={'code': code})
            
            if response.status_code == 200:
                messagebox.showinfo("Success", "Successfully joined class!")
                self.destroy()
            else:
                messagebox.showerror("Error", "Failed to join class")
                
        except requests.exceptions.RequestException:
            messagebox.showerror("Error", "Could not connect to server")

class CreateLeaderboardDialog(ctk.CTkToplevel):
    def __init__(self, parent, class_id):
        super().__init__(parent)
        self.parent = parent
        self.class_id = class_id
        
        self.title("Create Leaderboard")
        self.geometry("400x200")

        self.grid_rowconfigure((0, 1, 2), weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Duration
        self.duration_label = ctk.CTkLabel(self, text="Duration (days):")
        self.duration_label.grid(row=0, column=0, padx=20, pady=(20,0))
        
        self.duration_var = tk.StringVar(value="7")
        self.duration_menu = ctk.CTkOptionMenu(
            self,
            values=["7", "14", "30"],
            variable=self.duration_var
        )
        self.duration_menu.grid(row=1, column=0, padx=20, pady=(0,20))

        # Create button
        self.create_button = ctk.CTkButton(self, text="Create Leaderboard",
                                        command=self.create_leaderboard)
        self.create_button.grid(row=2, column=0, padx=20, pady=20)

    def create_leaderboard(self):
        try:
            headers = {'Authorization': f'Bearer {self.parent.controller.token}'}
            response = requests.post(
                f'http://localhost:5000/class/{self.class_id}/leaderboard',
                headers=headers,
                json={'duration_days': int(self.duration_var.get())}
            )
            
            if response.status_code == 201:
                messagebox.showinfo("Success", "Leaderboard created successfully!")
                self.destroy()
            else:
                messagebox.showerror("Error", "Failed to create leaderboard")
                
        except requests.exceptions.RequestException:
            messagebox.showerror("Error", "Could not connect to server")
