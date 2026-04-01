import customtkinter as ctk
import Exam_window
import pyrebase
from PIL import Image
import os
from auth_ui import AuthUI, LoginUI
from tkinter import messagebox as tmsg
import auth_manager as manager
import Dashboard_window
import auth_manager
from auth_manager import get_session
import secrets_config

# 1. Config ab secrets_config.py se aayega
config = secrets_config.FIREBASE_CONFIG

# 2. Connection initialize karo
firebase = pyrebase.initialize_app(config)
db = firebase.database()
auth = firebase.auth()

# Main Start Window
class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Sabse pehle db define karo
        
        self.title("BOSS - Benchmark Online Smart Suite")
        self.geometry("1200x800")
        self.wm_iconbitmap("BOSS-LOGO.ico")
        self.resizable(0,0)
        ctk.set_appearance_mode("dark")

        self.PRIMARY_BLUE = "#1a3a5f"
        self.ACCENT_GREEN = "#10b981"
        self.BG_WHITE = "#f8fafc"

        # --- UI SETUP ---
        self.left_panel = ctk.CTkFrame(self, width=500, fg_color=self.PRIMARY_BLUE, corner_radius=0)
        self.left_panel.pack(side="left", fill="both")
        self.left_panel.pack_propagate(False)
        self.setup_branding()

        self.right_panel = ctk.CTkFrame(self, fg_color=self.BG_WHITE, corner_radius=0)
        self.right_panel.pack(side="right", fill="both", expand=True)

        self.container = ctk.CTkFrame(self.right_panel, width=450, height=600, fg_color="white", corner_radius=25)
        self.container.place(relx=0.5, rely=0.5, anchor="center")
        self.container.pack_propagate(False)

        # --- AUTO-LOGIN LOGIC (Dhyan se dekho) ---
        saved_app = manager.get_session()
        token = manager.get_token()
        
        if saved_app:
            try:
                # 1. Firebase se data uthao (Dabba bharo)
                user_data = db.child("users").child(saved_app).get(token).val()
                self.questions = db.child("papers").get().val()
                
                if user_data:
                    # --- 🟢 YAHA PAR IMAGE LOGIC ---
                    temp_path = "temp_assets/current_user.jpg"
                    if not os.path.exists(temp_path):
                        photo_url = user_data.get('photo_link')
                        if photo_url and photo_url != "Pending":
                            # Manager ko bolo download kare
                            manager.download_temp_image(photo_url)
                    # -------------------------------

                    self.show_dashboard(user_data)
                else:
                    self.show_home()
            except Exception as e:
                print(f"Login Error: {e}")
                self.show_home()
        else:
            self.show_home()

    def setup_branding(self):
        ctk.CTkLabel(self.left_panel, text="BOSS", font=("Segoe UI", 90, "bold"), text_color="white").place(relx=0.1, rely=0.2)
        ctk.CTkLabel(self.left_panel, text="Benchmark Online Smart Suite", font=("Segoe UI", 22), text_color="#94a3b8").place(relx=0.1, rely=0.35)
        features = ["✓ Secure CBT Environment", "✓ Practice for JEE", "✓ Instant Result", "✓ Multi-device Sync"]
        for i, f in enumerate(features):
            ctk.CTkLabel(self.left_panel, text=f, font=("Segoe UI", 16), text_color="#cbd5e1").place(relx=0.1, rely=0.55 + (i*0.06))

    def clear_container(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def show_home(self):
        self.clear_container()
        ctk.CTkLabel(self.container, text="Welcome, Aspirant", font=("Segoe UI", 28, "bold"), text_color=self.PRIMARY_BLUE).pack(pady=(50, 10))
        self.create_big_button("LOGIN", "Access your portal", self.PRIMARY_BLUE, self.show_login)
        self.create_big_button("REGISTER", "Create new account", self.ACCENT_GREEN, self.show_register)

    def show_register(self):
        self.clear_container()
        # registration_frame load karo (db pass karo)
        reg_form = AuthUI(self.container, self, db, auth)
        reg_form.pack(fill="both", expand=True)

    def create_big_button(self, text, subtext, color, cmd):
        main_btn = ctk.CTkButton(self.container, text=f"{text}\n{subtext}", width=320, height=90, 
                                 corner_radius=15, fg_color=color, font=("Segoe UI", 18, "bold"), command=cmd)
        main_btn.pack(pady=15)

    def show_login(self):
        self.clear_container()
        login_form = LoginUI(self.container, self, db, firebase.auth())
        login_form.pack(fill="both", expand=True)

    def process_login_request(self):
        app_no = self.app_no_entry.get().strip()
        password = self.pass_entry.get().strip()
        if not app_no or not password:
            tmsg.showwarning("Empty", "Please fill all fields!")
            return
        
        success, user_data, is_new = manager.validate_dashboard_login(db, auth, app_no, password)
        if success:
                self.studentdashboard(user_data)
        else:
            tmsg.showerror("Login Failed", "Invalid App No. or Password!")

    def on_dashboard_close(self):
        """BOSS! Jab Dashboard ka 'X' dabbe, toh poora kissa khatam karo"""
        if hasattr(self, 'dash_window'):
            self.dash_window.destroy()
        
        # self.deiconify()  <-- Is line ko hata do (Ye login dikhati thi)
        self.quit()         # <-- Ye poore mainloop ko band kar dega
        self.destroy()      # <-- Ye window process khatam kar dega

    def handle_logout(self):
        print("Logging out...")
        manager.clear_session() 
    
        if hasattr(self, 'dash_window'):
            self.dash_window.destroy()
    # --- ENTRY RESET ---
    # Agar tere entries ke naam ye hain, toh inhe khali karo:
        try:
            self.app_no_entry.delete(0, 'end')
            self.pass_entry.delete(0, 'end')
        except:
            pass # Agar fields abhi exist nahi karte toh skip karo

        self.show_home() 
        self.deiconify()

    def show_dashboard(self, user_data):
        try:
            self.withdraw() 
            # Dhyan se dekh: dash_window ko humne 'self' (MainApp) pass kiya hai
            self.dash_window = Dashboard_window.StudentDashboard(self, user_data, db)
            
            # Agar user window 'X' se band kare toh on_dashboard_close chale
            self.dash_window.protocol("WM_DELETE_WINDOW", self.on_dashboard_close)
        
        except Exception as e:
            print(f"Dashboard Open Error: {e}")
            self.deiconify()

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()