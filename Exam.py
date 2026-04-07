import customtkinter as ctk
import Exam_window
import pyrebase
from PIL import Image
import os
from auth_ui import AuthUI, LoginUI
from tkinter import messagebox as tmsg
import auth_manager as manager
import Dashboard_window
import secrets_config
import time

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
        self.token_refresh_job = None

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

        # --- AUTO-LOGIN LOGIC (Upgraded) ---
        # Isse window black nahi hogi aur background mein refresh chalega
        self.after(100, self.check_auto_login)

    def check_auto_login(self):
        """Manager ka use karke session refresh aur auto-login handle karega"""
        print("🔍 Checking for existing session...")
        
        # 1. Refresh logic call karo
        session_data = manager.refresh_session_on_startup(auth)
        
        if session_data:
            try:
                saved_app = session_data.get("app_no")
                token = session_data.get("idToken")
                
                # Global token update
                manager.current_id_token = token 
                
                # 2. Fresh data fetch from DB
                user_data = db.child("users").child(saved_app).get(token).val()
                
                if user_data:
                    db.child("users").child(saved_app).update({"is_active": True}, token)
                    print(f"🚀 Auto-login: {saved_app} marked Active.")
                    user_data['idToken'] = token 
                    
                    # Image download logic
                    temp_path = "temp_assets/current_user.jpg"
                    if not os.path.exists(temp_path):
                        photo_url = user_data.get('photo_link')
                        if photo_url and photo_url != "Pending":
                            manager.download_temp_image(photo_url)

                    print(f"✅ Welcome back, {user_data.get('name')}")
                    
                    # 3. Yahan Dashboard call ho raha hai, toh heartbeat wahan handle hogi
                    self.show_dashboard(user_data) 
                else:
                    self.show_home()
            except Exception as e:
                print(f"❌ Auto-login error: {e}")
                manager.clear_session()
                self.show_home()
        else:
            print("ℹ️ No session found, showing home screen.")
            self.show_home()

    def schedule_token_refresh(self):
        """Har 50 mins mein token refresh karega taaki session expire na ho"""
        print("🔄 Background: Refreshing ID Token...")
        new_data = manager.refresh_session_on_startup(auth)
        if new_data:
            manager.current_id_token = new_data.get("idToken")
            print("✅ Background: Token refreshed successfully.")
        
        # 50 minutes baad phir se refresh call hoga
        self.token_refresh_job = self.after(3000000, self.schedule_token_refresh)

            # --- NEW: HEARTBEAT SYSTEM ---
    def start_heartbeat(self):
        """DB update without constant file reading"""
        # Manager se directly memory wala token aur app_no uthao
        token = manager.current_id_token
        session = manager.get_session_data() # Sirf app_no ke liye
        
        if session and token:
            app_no = session.get("app_no")
            try:
                db.child("users").child(app_no).update({"last_seen": time.time()}, token)
                print("💓 Heartbeat sent...")
            except:
                print("⚠️ Heartbeat failed (Network issue?)")
        
        self.heart_job = self.after(30000, self.start_heartbeat)

    def mark_offline_in_db(self):
        session = manager.get_session_data()
        token = manager.current_id_token
        if session and token:
            app_no = session.get("app_no")
            try:
                db.child("users").child(app_no).update({"is_active": False, "last_seen": 0}, token)
                print("✅ Status set to Offline.")
            except:
                pass

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
        self.login_form = LoginUI(self.container, self, db, auth) 
        self.login_form.pack(fill="both", expand=True)

    def process_login_request(self, app_no, password):
        """Manual Login Request Handler with Token Syncing"""
        if not app_no or not password:
            tmsg.showwarning("Empty", "Please fill all fields!")
            return
        
        # 1. Firebase se login validate karwao
        success, result, is_new = manager.validate_dashboard_login(db, auth, app_no, password)
        
        if success:
            # 🔥 CRITICAL: Manual login ke baad naya token 'manager' mein save karna zaroori hai
            # Taaki heartbeat aur refresh timers ko sahi 'Ticket' (Token) mile
            if isinstance(result, dict) and 'idToken' in result:
                manager.current_id_token = result.get('idToken')
                print(f"🔑 Manual Login Success: Token synced for {app_no}")
            
            # 2. Dashboard open karo (Timers iske andar start honge)
            self.show_dashboard(result)
            
        elif result == "ALREADY_LOGGED_IN":
            tmsg.showerror("Security Alert", 
                           "This ID is already active on another device!\n"
                           "Please logout from there or wait 2 minutes for session timeout.")
        else:
            # Wrong Password ya User Not Found ka error
            tmsg.showerror("Login Failed", f"Invalid Credentials or Network Error: {result}")

    def on_dashboard_close(self):
        """Dashboard X pe band ho toh cleanup karo"""
        print("Closing Application and marking offline...")
        
        # 1. Heartbeat cancel karo
        if hasattr(self, 'heart_job'):
            self.after_cancel(self.heart_job)
        
        if hasattr(self, 'token_refresh_job') and self.token_refresh_job:
            self.after_cancel(self.token_refresh_job)
        
        # 2. DB mein offline mark karo (is_active: False isi mein hai)
        self.mark_offline_in_db()
        
        # 3. 800ms ka wait karo taaki Firebase request finish ho jaye
        # Phir app ko band karo
        self.after(800, self.final_cleanup)

    def final_cleanup(self):
        self.quit()
        self.destroy()

    def handle_logout(self):
        """Smooth animation + Real-time DB Status Cleanup"""
        print("Initiating smooth logout and clearing session...")
        
        # 1. Heartbeat turant band karo taaki status 'Active' na hota rahe
        if hasattr(self, 'heart_job'):
            self.after_cancel(self.heart_job)
            print("💓 Heartbeat stopped.")

        if hasattr(self, 'token_refresh_job') and self.token_refresh_job:
            self.after_cancel(self.token_refresh_job)

        # 2. Dashboard ko turant hide karo
        if hasattr(self, 'dash_window'):
            self.dash_window.withdraw()

        # 3. Ek Loading Overlay Window (Visual feedback)
        loading_screen = ctk.CTkToplevel()
        loading_screen.overrideredirect(True) 
        loading_screen.attributes("-topmost", True)
        loading_screen.configure(fg_color=self.PRIMARY_BLUE)
        
        # Window centering logic
        w, h = 400, 150
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        loading_screen.geometry(f"{w}x{h}+{x}+{y}")

        ctk.CTkLabel(loading_screen, text="Logging Out Safely...", 
                     font=("Segoe UI", 20, "bold"), text_color="white").pack(pady=(40, 5))
        ctk.CTkLabel(loading_screen, text="Cleaning up session data...", 
                     font=("Segoe UI", 12), text_color="#94a3b8").pack()

        def finalize_logout():
            # 4. Database mein status 'Inactive' mark karo
            # Ye sabse important step hai taaki doosra device login kar sake
            self.mark_offline_in_db() 
            
            # 5. Local Backend Cleanup
            manager.clear_session() 
            
            # 6. Dashboard Window fully destroy karo
            if hasattr(self, 'dash_window'):
                self.dash_window.destroy()
            
            # 7. UI Reset: Login entries khali karo
            try:
                # Agar login_form class attribute hai
                if hasattr(self, 'login_form'):
                    # Dhyan rakhna ki LoginUI mein entries ke yahi naam hon
                    self.login_form.app_entry.delete(0, 'end')
                    self.login_form.pass_entry.delete(0, 'end')
            except:
                pass

            # 8. Final Switch
            loading_screen.destroy()
            self.show_home() 
            self.deiconify() # MainApp wapas dikhao
            print("✅ BOSS: Logout completed and status set to Inactive.")

        # 1.2 Seconds ka delay (Thoda fast kar diya hai 1.5s se)
        self.after(1200, finalize_logout)

    def show_dashboard(self, user_data):
        """Dashboard kholne ka safe method + Heartbeat Initialization"""
        try:
            # 1. Login window ko hide karo
            self.withdraw() 
            
            # 2. Dashboard window initialize karo
            # Dhyan rakhna 'db' variable globally accessible ho ya self.db ho
            self.dash_window = Dashboard_window.StudentDashboard(self, user_data, db)
            
            # 3. Protocol set karo taaki 'X' dabane par mark_offline_in_db chale
            self.dash_window.protocol("WM_DELETE_WINDOW", self.on_dashboard_close)
            
            # 4. --- NAYA: HEARTBEAT START ---
            # Ye har 30s mein DB update karega taaki session 'Active' rahe
            self.start_heartbeat()

            if not self.token_refresh_job:
                self.schedule_token_refresh()
            print("🚀 Dashboard active: Heartbeat & Token Refresh ON.")
            
            # 5. Window focus management
            self.dash_window.lift()
            self.dash_window.focus_force()
            
        except Exception as e:
            print(f"❌ Dashboard Open Error: {e}")
            # Agar error aaye toh login screen wapas dikhao
            self.deiconify()
            tmsg.showerror("Error", f"Could not open Dashboard: {e}")

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()