import customtkinter as ctk
import requests
from frames.home_frame import HomeFrame
from frames.flashcard_frame import FlashcardFrame
from frames.timetable_frame import TimetableFrame
from frames.class_frame import ClassFrame
from frames.progress_frame import ProgressFrame

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
        
        # Configure grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Create main frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Initialize frames dictionary
        self.frames = {}
        
        # Show login frame
        self.show_login()
    
    def show_frame(self, frame_name):
        # Hide current frame
        for frame in self.frames.values():
            frame.grid_remove()
        
        # Show requested frame
        if frame_name in self.frames:
            self.frames[frame_name].grid(row=0, column=0, sticky="nsew")
        else:
            print(f"Frame {frame_name} not found")
    
    def show_login(self):
        # Clear main frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # Create login frame
        login_frame = ctk.CTkFrame(self.main_frame)
        login_frame.pack(pady=20, padx=20, expand=True)
        
        # Title
        title = ctk.CTkLabel(
            login_frame,
            text="Welcome to Revision App",
            font=("Helvetica", 24, "bold")
        )
        title.pack(pady=20)
        
        # Username
        username_entry = ctk.CTkEntry(
            login_frame,
            placeholder_text="Username",
            width=300
        )
        username_entry.pack(pady=10)
        
        # Password
        password_entry = ctk.CTkEntry(
            login_frame,
            placeholder_text="Password",
            show="*",
            width=300
        )
        password_entry.pack(pady=10)
        
        # Error message
        error_label = ctk.CTkLabel(
            login_frame,
            text="",
            text_color="red"
        )
        error_label.pack(pady=5)
        
        # Login button
        login_button = ctk.CTkButton(
            login_frame,
            text="Login",
            width=200,
            command=lambda: self.login(
                username_entry.get(),
                password_entry.get(),
                error_label
            )
        )
        login_button.pack(pady=10)
        
        # Register link
        register_button = ctk.CTkButton(
            login_frame,
            text="Create Account",
            width=200,
            command=self.show_register
        )
        register_button.pack(pady=10)
    
    def show_register(self):
        # Clear main frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # Create register frame
        register_frame = ctk.CTkFrame(self.main_frame)
        register_frame.pack(pady=20, padx=20, expand=True)
        
        # Title
        title = ctk.CTkLabel(
            register_frame,
            text="Create Account",
            font=("Helvetica", 24, "bold")
        )
        title.pack(pady=20)
        
        # Username
        username_entry = ctk.CTkEntry(
            register_frame,
            placeholder_text="Username",
            width=300
        )
        username_entry.pack(pady=10)
        
        # Email
        email_entry = ctk.CTkEntry(
            register_frame,
            placeholder_text="Email",
            width=300
        )
        email_entry.pack(pady=10)
        
        # Password
        password_entry = ctk.CTkEntry(
            register_frame,
            placeholder_text="Password",
            show="*",
            width=300
        )
        password_entry.pack(pady=10)
        
        # Confirm Password
        confirm_password_entry = ctk.CTkEntry(
            register_frame,
            placeholder_text="Confirm Password",
            show="*",
            width=300
        )
        confirm_password_entry.pack(pady=10)
        
        # Error message
        error_label = ctk.CTkLabel(
            register_frame,
            text="",
            text_color="red"
        )
        error_label.pack(pady=5)
        
        # Register button
        register_button = ctk.CTkButton(
            register_frame,
            text="Register",
            width=200,
            command=lambda: self.register(
                username_entry.get(),
                email_entry.get(),
                password_entry.get(),
                confirm_password_entry.get(),
                error_label
            )
        )
        register_button.pack(pady=10)
        
        # Back to login link
        back_button = ctk.CTkButton(
            register_frame,
            text="Back to Login",
            width=200,
            command=self.show_login
        )
        back_button.pack(pady=10)
    
    def login(self, username, password, error_label):
        if not username or not password:
            error_label.configure(text="Please fill in all fields")
            return
        
        try:
            response = requests.post(
                'http://localhost:5000/login',
                json={
                    'username': username,
                    'password': password
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data['token']
                self.user_id = data['user_id']
                self.username = data['username']
                self.show_home()
            else:
                error_label.configure(text="Invalid username or password")
        except requests.exceptions.RequestException:
            error_label.configure(text="Connection error")
    
    def register(self, username, email, password, confirm_password, error_label):
        if not all([username, email, password, confirm_password]):
            error_label.configure(text="Please fill in all fields")
            return
        
        if password != confirm_password:
            error_label.configure(text="Passwords do not match")
            return
        
        if len(password) < 8:
            error_label.configure(text="Password must be at least 8 characters")
            return
        
        try:
            response = requests.post(
                'http://localhost:5000/register',
                json={
                    'username': username,
                    'email': email,
                    'password': password
                }
            )
            
            if response.status_code == 201:
                self.show_login()
            else:
                error_label.configure(text=response.json().get('message', 'Registration failed'))
        except requests.exceptions.RequestException:
            error_label.configure(text="Connection error")
    
    def show_home(self):
        # Clear main frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # Configure main frame grid
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)
        
        # Create sidebar
        sidebar = ctk.CTkFrame(
            self.main_frame,
            width=200,
            corner_radius=0
        )
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(7, weight=1)
        
        # App logo/name
        logo_label = ctk.CTkLabel(
            sidebar,
            text="Revision App",
            font=("Helvetica", 20, "bold")
        )
        logo_label.grid(row=0, column=0, padx=20, pady=20)
        
        # Navigation buttons
        self.create_nav_button(sidebar, "Home", lambda: self.show_frame("home"), 1)
        self.create_nav_button(sidebar, "Flashcards", lambda: self.show_frame("flashcards"), 2)
        self.create_nav_button(sidebar, "Tests", lambda: self.show_frame("tests"), 3)
        self.create_nav_button(sidebar, "Timetable", lambda: self.show_frame("timetable"), 4)
        self.create_nav_button(sidebar, "Classes", lambda: self.show_frame("classes"), 5)
        self.create_nav_button(sidebar, "Progress", lambda: self.show_frame("progress"), 6)
        
        # Logout button
        logout_button = ctk.CTkButton(
            sidebar,
            text="Logout",
            command=self.logout
        )
        logout_button.grid(row=8, column=0, padx=20, pady=20, sticky="s")
        
        # Create content frame
        content_frame = ctk.CTkFrame(self.main_frame)
        content_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        # Configure content frame grid
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)
        
        # Initialize frames
        self.frames = {
            'home': HomeFrame(content_frame, self),
            'flashcards': FlashcardFrame(content_frame, self),
            'timetable': TimetableFrame(content_frame, self),
            'classes': ClassFrame(content_frame, self),
            'progress': ProgressFrame(content_frame, self)
        }
        
        # Show home frame
        self.show_frame("home")
    
    def create_nav_button(self, parent, text, command, row):
        button = ctk.CTkButton(
            parent,
            text=text,
            command=command,
            anchor="w"
        )
        button.grid(row=row, column=0, padx=20, pady=10, sticky="ew")
    
    def logout(self):
        self.token = None
        self.user_id = None
        self.username = None
        self.xp = 0
        self.frames = {}
        self.show_login()

if __name__ == "__main__":
    app = App()
    app.mainloop()
