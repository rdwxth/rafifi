import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
import requests
from datetime import datetime

class FlashcardFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Configure grid
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header
        self.header = ctk.CTkFrame(self)
        self.header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20,0))
        
        self.title = ctk.CTkLabel(self.header, text="Flashcards",
                                font=ctk.CTkFont(size=24, weight="bold"))
        self.title.pack(side="left", padx=10)
        
        self.create_set_button = ctk.CTkButton(self.header, text="Create New Set",
                                             command=self.show_create_set)
        self.create_set_button.pack(side="right", padx=10)

        # Main content area with sets list and flashcard view
        self.content = ctk.CTkFrame(self)
        self.content.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        self.content.grid_columnconfigure(1, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        # Sets list
        self.sets_frame = ctk.CTkFrame(self.content)
        self.sets_frame.grid(row=0, column=0, sticky="ns", padx=(0,20))
        
        self.sets_label = ctk.CTkLabel(self.sets_frame, text="Your Sets",
                                     font=ctk.CTkFont(weight="bold"))
        self.sets_label.pack(pady=10)
        
        self.sets_list = ctk.CTkScrollableFrame(self.sets_frame, width=200)
        self.sets_list.pack(expand=True, fill="both", padx=10, pady=10)

        # Flashcard view
        self.card_frame = ctk.CTkFrame(self.content)
        self.card_frame.grid(row=0, column=1, sticky="nsew")
        
        self.current_set = None
        self.current_cards = []
        self.current_card_index = 0
        self.showing_answer = False

        # Create flashcard display
        self.card_display = ctk.CTkFrame(self.card_frame, fg_color="gray20")
        self.card_display.pack(expand=True, fill="both", padx=20, pady=20)
        
        self.card_text = ctk.CTkLabel(self.card_display, text="Select a flashcard set",
                                    wraplength=400, font=ctk.CTkFont(size=18))
        self.card_text.pack(expand=True)

        # Navigation buttons
        self.nav_frame = ctk.CTkFrame(self.card_frame)
        self.nav_frame.pack(fill="x", padx=20, pady=10)
        
        self.prev_button = ctk.CTkButton(self.nav_frame, text="Previous",
                                       command=self.prev_card)
        self.prev_button.pack(side="left", padx=5)
        
        self.flip_button = ctk.CTkButton(self.nav_frame, text="Flip",
                                       command=self.flip_card)
        self.flip_button.pack(side="left", padx=5)
        
        self.next_button = ctk.CTkButton(self.nav_frame, text="Next",
                                       command=self.next_card)
        self.next_button.pack(side="left", padx=5)
        
        self.start_test_button = ctk.CTkButton(self.nav_frame, text="Start Test",
                                             command=self.start_test)
        self.start_test_button.pack(side="right", padx=5)

    def show_create_set(self):
        dialog = CreateSetDialog(self)
        self.wait_window(dialog)
        self.update_sets_list()

    def update_sets_list(self):
        # Clear existing sets
        for widget in self.sets_list.winfo_children():
            widget.destroy()

        try:
            headers = {'Authorization': f'Bearer {self.controller.token}'}
            response = requests.get('http://localhost:5000/flashcard/sets', headers=headers)
            
            if response.status_code == 200:
                sets = response.json()
                for set_data in sets:
                    btn = ctk.CTkButton(self.sets_list, text=set_data['name'],
                                     command=lambda s=set_data: self.load_set(s))
                    btn.pack(fill="x", pady=2)
        except requests.exceptions.RequestException:
            messagebox.showerror("Error", "Could not fetch flashcard sets")

    def load_set(self, set_data):
        try:
            headers = {'Authorization': f'Bearer {self.controller.token}'}
            response = requests.get(f'http://localhost:5000/flashcard/sets/{set_data["id"]}',
                                 headers=headers)
            
            if response.status_code == 200:
                self.current_set = set_data
                set_info = response.json()
                self.current_cards = set_info['flashcards']
                self.current_card_index = 0
                self.showing_answer = False
                self.update_card_display()
        except requests.exceptions.RequestException:
            messagebox.showerror("Error", "Could not load flashcard set")

    def update_card_display(self):
        if not self.current_cards:
            self.card_text.configure(text="No cards in this set")
            return
            
        card = self.current_cards[self.current_card_index]
        text = card['back'] if self.showing_answer else card['front']
        self.card_text.configure(text=text)

    def flip_card(self):
        if self.current_cards:
            self.showing_answer = not self.showing_answer
            self.update_card_display()

    def next_card(self):
        if self.current_cards and self.current_card_index < len(self.current_cards) - 1:
            self.current_card_index += 1
            self.showing_answer = False
            self.update_card_display()

    def prev_card(self):
        if self.current_cards and self.current_card_index > 0:
            self.current_card_index -= 1
            self.showing_answer = False
            self.update_card_display()

    def start_test(self):
        if not self.current_set:
            messagebox.showwarning("Warning", "Please select a flashcard set first")
            return
            
        test_window = TestWindow(self, self.current_set)
        self.wait_window(test_window)

    def update_content(self):
        self.update_sets_list()

class CreateSetDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        
        self.title("Create New Flashcard Set")
        self.geometry("600x400")

        # Set name
        self.name_frame = ctk.CTkFrame(self)
        self.name_frame.pack(fill="x", padx=20, pady=20)
        
        self.name_label = ctk.CTkLabel(self.name_frame, text="Set Name:")
        self.name_label.pack(side="left", padx=5)
        
        self.name_entry = ctk.CTkEntry(self.name_frame)
        self.name_entry.pack(side="left", expand=True, fill="x", padx=5)

        # Folder selection
        self.folder_frame = ctk.CTkFrame(self)
        self.folder_frame.pack(fill="x", padx=20, pady=10)
        
        self.folder_label = ctk.CTkLabel(self.folder_frame, text="Folder:")
        self.folder_label.pack(side="left", padx=5)
        
        self.folder_entry = ctk.CTkEntry(self.folder_frame)
        self.folder_entry.pack(side="left", expand=True, fill="x", padx=5)
        self.folder_entry.insert(0, "General")

        # Cards list
        self.cards_frame = ctk.CTkScrollableFrame(self)
        self.cards_frame.pack(expand=True, fill="both", padx=20, pady=10)
        
        self.add_card_button = ctk.CTkButton(self, text="Add Card",
                                          command=self.add_card_fields)
        self.add_card_button.pack(pady=10)
        
        self.save_button = ctk.CTkButton(self, text="Save Set",
                                      command=self.save_set)
        self.save_button.pack(pady=10)

        # Add first card
        self.cards = []
        self.add_card_fields()

    def add_card_fields(self):
        card_frame = ctk.CTkFrame(self.cards_frame)
        card_frame.pack(fill="x", pady=5)
        
        front_entry = ctk.CTkEntry(card_frame, placeholder_text="Front")
        front_entry.pack(fill="x", pady=2)
        
        back_entry = ctk.CTkEntry(card_frame, placeholder_text="Back")
        back_entry.pack(fill="x", pady=2)
        
        difficulty = ctk.CTkOptionMenu(card_frame,
                                    values=["easy", "medium", "hard"],
                                    variable=ctk.StringVar(value="medium"))
        difficulty.pack(pady=2)
        
        remove_button = ctk.CTkButton(card_frame, text="Remove",
                                   command=lambda: self.remove_card(card_frame))
        remove_button.pack(pady=2)
        
        self.cards.append((card_frame, front_entry, back_entry, difficulty))

    def remove_card(self, card_frame):
        card_frame.destroy()
        self.cards = [(f, q, a, d) for f, q, a, d in self.cards if f != card_frame]

    def save_set(self):
        name = self.name_entry.get().strip()
        folder = self.folder_entry.get().strip()
        
        if not name:
            messagebox.showwarning("Warning", "Please enter a set name")
            return
            
        if not self.cards:
            messagebox.showwarning("Warning", "Please add at least one card")
            return
            
        try:
            # Create set
            headers = {'Authorization': f'Bearer {self.parent.controller.token}'}
            response = requests.post('http://localhost:5000/flashcard/sets',
                                  headers=headers,
                                  json={'name': name, 'folder': folder})
            
            if response.status_code != 201:
                messagebox.showerror("Error", "Failed to create flashcard set")
                return
                
            set_data = response.json()
            
            # Add cards
            for _, front_entry, back_entry, difficulty in self.cards:
                front = front_entry.get().strip()
                back = back_entry.get().strip()
                
                if front and back:  # Only add cards with both front and back
                    response = requests.post(
                        f'http://localhost:5000/flashcard/sets/{set_data["id"]}/cards',
                        headers=headers,
                        json={
                            'front': front,
                            'back': back,
                            'difficulty': difficulty.get()
                        }
                    )
                    
                    if response.status_code != 201:
                        messagebox.showwarning("Warning", f"Failed to add card: {front}")
            
            self.destroy()
            
        except requests.exceptions.RequestException:
            messagebox.showerror("Error", "Could not connect to server")

class TestWindow(ctk.CTkToplevel):
    def __init__(self, parent, flashcard_set):
        super().__init__(parent)
        self.parent = parent
        self.flashcard_set = flashcard_set
        
        self.title("Test")
        self.geometry("800x600")

        self.current_card_index = 0
        self.start_time = datetime.now()
        self.scores = []
        self.cards = parent.current_cards
        self.setup_test_ui()

    def setup_test_ui(self):
        # Question display
        self.question_frame = ctk.CTkFrame(self)
        self.question_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        self.question_label = ctk.CTkLabel(self.question_frame,
                                        text=self.cards[0]['front'],
                                        wraplength=600,
                                        font=ctk.CTkFont(size=18))
        self.question_label.pack(expand=True)

        # Answer entry
        self.answer_frame = ctk.CTkFrame(self)
        self.answer_frame.pack(fill="x", padx=20, pady=10)
        
        self.answer_entry = ctk.CTkEntry(self.answer_frame,
                                      placeholder_text="Your answer")
        self.answer_entry.pack(fill="x", padx=10)
        
        self.submit_button = ctk.CTkButton(self.answer_frame,
                                        text="Submit Answer",
                                        command=self.check_answer)
        self.submit_button.pack(pady=10)

    def check_answer(self):
        answer = self.answer_entry.get().strip().lower()
        correct_answer = self.cards[self.current_card_index]['back'].lower()
        
        # Simple scoring: exact match = 1, close match = 0.5, no match = 0
        score = 1.0 if answer == correct_answer else 0.5 if answer in correct_answer or correct_answer in answer else 0.0
        self.scores.append(score)
        
        # Show feedback
        feedback = "Correct!" if score == 1.0 else "Partially Correct" if score == 0.5 else "Incorrect"
        messagebox.showinfo("Result", f"{feedback}\nCorrect answer: {correct_answer}")
        
        # Move to next question or finish test
        self.current_card_index += 1
        if self.current_card_index < len(self.cards):
            self.question_label.configure(text=self.cards[self.current_card_index]['front'])
            self.answer_entry.delete(0, 'end')
        else:
            self.submit_test()

    def submit_test(self):
        duration = int((datetime.now() - self.start_time).total_seconds())
        final_score = sum(self.scores) / len(self.scores) * 100
        
        try:
            headers = {'Authorization': f'Bearer {self.parent.controller.token}'}
            response = requests.post(
                f'http://localhost:5000/flashcard/sets/{self.flashcard_set["id"]}/test',
                headers=headers,
                json={'score': final_score, 'duration': duration}
            )
            
            if response.status_code == 201:
                result = response.json()
                messagebox.showinfo("Test Complete",
                                  f"Score: {final_score:.1f}%\n"
                                  f"Time: {duration} seconds\n"
                                  f"XP gained: {result['xp_gained']}")
            else:
                messagebox.showwarning("Warning", "Failed to submit test results")
                
        except requests.exceptions.RequestException:
            messagebox.showerror("Error", "Could not connect to server")
        
        self.destroy()
