import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import requests
import re
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LoginFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Configure grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Main container
        self.container = ctk.CTkFrame(self)
        self.container.grid(row=0, column=0, padx=20, pady=20)
        
        # Title
        self.title = ctk.CTkLabel(self.container, text="Welcome to Revision App",
                               font=ctk.CTkFont(size=24, weight="bold"))
        self.title.pack(pady=20)
        
        # Login form
        self.username_label = ctk.CTkLabel(self.container, text="Username:")
        self.username_label.pack(pady=(10,0))
        
        self.username_entry = ctk.CTkEntry(self.container)
        self.username_entry.pack(pady=5)
        
        self.password_label = ctk.CTkLabel(self.container, text="Password:")
        self.password_label.pack(pady=(10,0))
        
        self.password_entry = ctk.CTkEntry(self.container, show="*")
        self.password_entry.pack(pady=5)
        
        self.login_button = ctk.CTkButton(self.container, text="Login",
                                      command=self.login)
        self.login_button.pack(pady=20)
        
        # Register link
        self.register_link = ctk.CTkButton(self.container, text="Create Account",
                                       command=self.show_register,
                                       fg_color="transparent")
        self.register_link.pack()
        
        # Bind Enter key to login
        self.username_entry.bind('<Return>', lambda e: self.login())
        self.password_entry.bind('<Return>', lambda e: self.login())

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        # Validate inputs
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
            
        try:
            logger.info(f"Attempting login for user: {username}")
            response = requests.post('http://localhost:5000/auth/login',
                                 json={'username': username, 'password': password})
            
            logger.info(f"Login response status: {response.status_code}")
            logger.info(f"Login response content: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                self.controller.token = data['token']
                self.controller.user_id = data['user_id']
                self.controller.username = data['username']
                self.controller.show_frame('HomeFrame')
            else:
                messagebox.showerror("Error", response.json().get('message', 'Login failed'))
        except requests.exceptions.RequestException:
            logger.error("Failed to connect to server", exc_info=True)
            messagebox.showerror("Error", "Could not connect to server")
        except Exception as e:
            logger.error("Unexpected error during login", exc_info=True)
            messagebox.showerror("Error", str(e))

    def show_register(self):
        self.controller.show_frame('RegisterFrame')

class RegisterFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Configure grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Main container
        self.container = ctk.CTkFrame(self)
        self.container.grid(row=0, column=0, padx=20, pady=20)
        
        # Title
        self.title = ctk.CTkLabel(self.container, text="Create Account",
                               font=ctk.CTkFont(size=24, weight="bold"))
        self.title.pack(pady=20)
        
        # Registration form
        fields = [
            ('username', "Username"),
            ('email', "Email"),
            ('recovery_email', "Recovery Email (Optional)"),
            ('password', "Password"),
            ('confirm_password', "Confirm Password")
        ]
        
        self.entries = {}
        for field, label in fields:
            label_widget = ctk.CTkLabel(self.container, text=label)
            label_widget.pack(pady=(10,0))
            
            show = "*" if "password" in field else ""
            entry = ctk.CTkEntry(self.container, show=show)
            entry.pack(pady=5)
            
            self.entries[field] = entry
        
        # Password requirements
        self.req_label = ctk.CTkLabel(self.container, 
                                   text="Password must contain:\n" +
                                        "- At least 8 characters\n" +
                                        "- One uppercase letter\n" +
                                        "- One lowercase letter\n" +
                                        "- One number\n" +
                                        "- One special character",
                                   justify="left")
        self.req_label.pack(pady=10)
        
        # Register button
        self.register_button = ctk.CTkButton(self.container, text="Register",
                                         command=self.register)
        self.register_button.pack(pady=20)
        
        # Login link
        self.login_link = ctk.CTkButton(self.container, text="Back to Login",
                                    command=self.show_login,
                                    fg_color="transparent")
        self.login_link.pack()

    def validate_password(self, password):
        """Validate password strength"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter"
        if not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter"
        if not re.search(r"\d", password):
            return False, "Password must contain at least one number"
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            return False, "Password must contain at least one special character"
        return True, None

    def register(self):
        data = {field: entry.get().strip() 
                for field, entry in self.entries.items()}
        
        # Basic validation
        if not all(data[f] for f in ['username', 'email', 'password', 'confirm_password']):
            messagebox.showerror("Error", "Please fill in all required fields")
            return
            
        if data['password'] != data['confirm_password']:
            messagebox.showerror("Error", "Passwords do not match")
            return
            
        # Password validation
        is_valid, error_msg = self.validate_password(data['password'])
        if not is_valid:
            messagebox.showerror("Error", error_msg)
            return
            
        # Email validation
        if not re.match(r"[^@]+@[^@]+\.[^@]+", data['email']):
            messagebox.showerror("Error", "Invalid email format")
            return
            
        if data['recovery_email'] and not re.match(r"[^@]+@[^@]+\.[^@]+", data['recovery_email']):
            messagebox.showerror("Error", "Invalid recovery email format")
            return
            
        # Remove confirm_password from data
        del data['confirm_password']
        
        try:
            logger.info(f"Attempting registration for user: {data['username']}")
            response = requests.post('http://localhost:5000/auth/register',
                                 json=data)
            
            logger.info(f"Registration response status: {response.status_code}")
            logger.info(f"Registration response content: {response.text}")
            
            if response.status_code == 201:
                messagebox.showinfo("Success", "Account created successfully!")
                self.show_login()
            else:
                error_msg = response.json().get('message', 'Registration failed')
                messagebox.showerror("Error", error_msg)
        except requests.exceptions.RequestException:
            logger.error("Failed to connect to server", exc_info=True)
            messagebox.showerror("Error", "Could not connect to server")
        except Exception as e:
            logger.error("Unexpected error during registration", exc_info=True)
            messagebox.showerror("Error", str(e))

    def show_login(self):
        self.controller.show_frame('LoginFrame')
