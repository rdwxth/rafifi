import customtkinter as ctk
from frames.home_frame import HomeFrame
from frames.flashcard_frame import FlashcardFrame
from frames.timetable_frame import TimetableFrame
from frames.class_frame import ClassFrame
from frames.progress_frame import ProgressFrame
from frames.login_frame import LoginFrame, RegisterFrame

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title("Revision App")
        self.geometry("1200x800")
        
        # Initialize auth state
        self.token = None
        self.user_id = None
        self.username = None
        self.xp = 0
        
        # Configure grid layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)  # Column 1 is main content
        
        # Create sidebar
        self.sidebar = ctk.CTkFrame(self, width=200)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.sidebar.grid_propagate(False)  # Keep fixed width
        
        # Sidebar buttons
        self.sidebar_buttons = {}
        button_data = [
            ("Home", "HomeFrame"),
            ("Flashcards", "FlashcardFrame"),
            ("Timetable", "TimetableFrame"),
            ("Classes", "ClassFrame"),
            ("Progress", "ProgressFrame")
        ]
        
        for i, (text, frame) in enumerate(button_data):
            btn = ctk.CTkButton(
                self.sidebar,
                text=text,
                command=lambda f=frame: self.show_frame(f)
            )
            btn.pack(pady=5, padx=10, fill="x")
            self.sidebar_buttons[frame] = btn
        
        # Create main content area
        self.main_content = ctk.CTkFrame(self)
        self.main_content.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.main_content.grid_columnconfigure(0, weight=1)
        self.main_content.grid_rowconfigure(0, weight=1)
        
        # Create frames
        self.frames = {}
        for F in (LoginFrame, RegisterFrame, HomeFrame, FlashcardFrame, 
                 TimetableFrame, ClassFrame, ProgressFrame):
            frame = F(self.main_content, self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")
            
        # Show login frame initially
        self.show_frame('LoginFrame')
        self.sidebar.grid_remove()  # Hide sidebar until logged in
    
    def show_frame(self, frame_name):
        # Show/hide sidebar based on login state
        if frame_name in ('LoginFrame', 'RegisterFrame'):
            self.sidebar.grid_remove()
        else:
            self.sidebar.grid()
            
        # Update active button state
        for btn_frame, btn in self.sidebar_buttons.items():
            if btn_frame == frame_name:
                btn.configure(fg_color=("gray75", "gray25"))
            else:
                btn.configure(fg_color=("gray70", "gray30"))
        
        # Hide current frame
        for frame in self.frames.values():
            frame.grid_remove()
        
        # Show requested frame
        frame = self.frames.get(frame_name)
        if frame:
            frame.grid()
            if hasattr(frame, 'update_content'):
                frame.update_content()
        else:
            print(f"Frame {frame_name} not found")
    
    def logout(self):
        self.token = None
        self.user_id = None
        self.username = None
        self.xp = 0
        self.show_frame('LoginFrame')

if __name__ == "__main__":
    app = App()
    app.mainloop()
