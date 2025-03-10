import customtkinter as ctk
from PIL import Image, ImageTk
import os

class HomeFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.setup_ui()

    def setup_ui(self):
        # Welcome message
        welcome_label = ctk.CTkLabel(
            self,
            text=f"Welcome back, {self.controller.username}!",
            font=("Helvetica", 24, "bold")
        )
        welcome_label.pack(pady=20)

        # Create grid for feature buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(pady=20, padx=20, fill="both", expand=True)

        # Configure grid
        button_frame.grid_columnconfigure((0, 1), weight=1)
        button_frame.grid_rowconfigure((0, 1, 2), weight=1)

        # Feature buttons
        self.create_feature_button(
            button_frame,
            "Flashcards",
            "Study and create flashcard sets",
            lambda: self.controller.show_frame("FlashcardFrame"),  
            0, 0
        )

        self.create_feature_button(
            button_frame,
            "Tests",
            "Take tests based on your flashcards",
            lambda: self.controller.show_frame("TestFrame"),
            0, 1
        )

        self.create_feature_button(
            button_frame,
            "Timetable",
            "Plan your weekly study schedule",
            lambda: self.controller.show_frame("TimetableFrame"),
            1, 0
        )

        self.create_feature_button(
            button_frame,
            "Classes",
            "Join study groups and compete",
            lambda: self.controller.show_frame("ClassFrame"),
            1, 1
        )

        self.create_feature_button(
            button_frame,
            "Progress",
            "Track your learning journey",
            lambda: self.controller.show_frame("ProgressFrame"),
            2, 0
        )

        self.create_feature_button(
            button_frame,
            "Settings",
            "Customize your experience",
            lambda: self.controller.show_frame("SettingsFrame"),
            2, 1
        )

        # Stats summary
        stats_frame = ctk.CTkFrame(self)
        stats_frame.pack(pady=10, padx=20, fill="x")

        # XP Level
        level_label = ctk.CTkLabel(
            stats_frame,
            text=f"Level {self.controller.xp // 1000}",
            font=("Helvetica", 16)
        )
        level_label.pack(side="left", padx=20)

        # Streak
        streak_label = ctk.CTkLabel(
            stats_frame,
            text=" 7 Day Streak",
            font=("Helvetica", 16)
        )
        streak_label.pack(side="right", padx=20)

    def create_feature_button(self, parent, title, description, command, row, col):
        # Create a frame for each feature button
        frame = ctk.CTkFrame(parent)
        frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

        # Title
        title_label = ctk.CTkLabel(
            frame,
            text=title,
            font=("Helvetica", 18, "bold")
        )
        title_label.pack(pady=(10, 5))

        # Description
        desc_label = ctk.CTkLabel(
            frame,
            text=description,
            font=("Helvetica", 12)
        )
        desc_label.pack(pady=(0, 10))

        # Button
        button = ctk.CTkButton(
            frame,
            text="Open",
            command=command,
            width=120
        )
        button.pack(pady=(0, 10))
