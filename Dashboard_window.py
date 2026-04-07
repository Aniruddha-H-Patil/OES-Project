import customtkinter as ctk
from PIL import Image
import requests
from io import BytesIO
import threading
from tkinter import messagebox as tmsg
import os
import Exam_window
import Result_window
import auth_manager as manager

class StudentDashboard(ctk.CTkToplevel):
    def __init__(self, parent, user_data, db):
        super().__init__(parent)
        
        self.parent = parent
        self.user_data = user_data
        self.db = db
        self.test_on = False
        
        self.title(f"BOSS - Student Home | {user_data['name']}")
        self.geometry("1200x750")
        self.iconbitmap("BOSS-LOGO.ico")
        
        # Theme Colors (Modern UI)
        self.BG_COLOR = "#f0f2f5"
        self.SIDEBAR_COLOR = "#ffffff"
        self.PRIMARY_BLUE = "#1a73e8"
        self.TEXT_DARK = "#202124"

        self.configure(fg_color=self.BG_COLOR)
        self.setup_ui()

        self.protocol("WM_DELETE_WINDOW", self.parent.on_dashboard_close)

        # Photo loading in background
        threading.Thread(target=self.load_profile_photo, daemon=True).start()

    def setup_ui(self):
        # 1. LEFT SIDEBAR (Profile & Navigation)
        self.sidebar = ctk.CTkFrame(self, width=280, fg_color=self.SIDEBAR_COLOR, corner_radius=0)
        self.sidebar.pack(side="left", fill="y", padx=0, pady=0)
        self.sidebar.pack_propagate(False)

        # Profile Image Section
        self.profile_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.profile_frame.pack(pady=40)

        self.photo_label = ctk.CTkLabel(self.profile_frame, text="PHOTO", width=140, height=140, 
                                        fg_color="#e8f0fe", corner_radius=10) # Round feel
        self.photo_label.pack()

        ctk.CTkLabel(self.sidebar, text=self.user_data['name'].upper(), font=("Segoe UI", 20, "bold"), 
                     text_color=self.TEXT_DARK).pack(pady=(10, 0))
        ctk.CTkLabel(self.sidebar, text=f"Roll No: {self.user_data['roll_no']}", font=("Segoe UI", 14), 
                     text_color="#5f6368").pack()

        # Navigation Buttons
        self.nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.nav_frame.pack(fill="x", padx=20, pady=30)

        nav_btns = [("🏠 Home", self.home_click), ("📝 My Tests", self.tests_click), ("📊 Results", self.results_click)]
        for text, cmd in nav_btns:
            ctk.CTkButton(self.nav_frame, text=text, fg_color="transparent", text_color=self.TEXT_DARK,
                          hover_color="#f1f3f4", anchor="w", height=40, font=("Segoe UI", 15),
                          command=cmd).pack(fill="x", pady=2)

        # Logout Button
        # Dashboard_window.py ke andar
        self.logout_btn = ctk.CTkButton(self.sidebar, text="LOGOUT", command=self.parent.handle_logout) # <-- DHAYAN DE: self.parent use kar
        self.logout_btn.pack(side="bottom", pady=20, padx=20, fill="x")

        # 2. MAIN CONTENT AREA
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(side="right", fill="both", expand=True, padx=30, pady=20)

        # Header Stats
        self.header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=(0, 20))
        
        self.create_stat_card("Tests Available", "05", "#1a73e8", 0)
        self.create_stat_card("Completed", "02", "#10b981", 1)
        self.create_stat_card("Rank", "N/A", "#f59e0b", 2)

        # Dashboard Title
        ctk.CTkLabel(self.main_container, text="Welcome to Student Portal", font=("Segoe UI", 28, "bold"), 
                     text_color=self.TEXT_DARK).pack(anchor="w", pady=(20, 10))

        # Placeholder for Paper Selection
        ctk.CTkLabel(self.main_container, text="Available Examinations", font=("Segoe UI", 24, "bold"), 
                     text_color=self.TEXT_DARK).pack(anchor="w", pady=(20, 10))

        # 🟢 Khali card ki jagah ab ye scrollable area lega
        self.test_list_frame = ctk.CTkScrollableFrame(self.main_container, fg_color="transparent")
        self.test_list_frame.pack(fill="both", expand=True)

        # 🟢 Call the Fetcher
        self.load_available_tests()

    def create_stat_card(self, title, value, color, col):
        card = ctk.CTkFrame(self.header_frame, fg_color="white", width=250, height=100, corner_radius=12)
        card.grid(row=0, column=col, padx=(0, 20))
        card.grid_propagate(False)
        
        ctk.CTkLabel(card, text=title, font=("Segoe UI", 14), text_color="#5f6368").place(relx=0.1, rely=0.3)
        ctk.CTkLabel(card, text=value, font=("Segoe UI", 24, "bold"), text_color=color).place(relx=0.1, rely=0.6)

    def load_available_tests(self):
        try:
            token = manager.get_token()
            papers = self.db.child("papers").get(token).val()
            if not papers: return
            
            for widget in self.test_list_frame.winfo_children(): widget.destroy()

            for p_id, p_info in papers.items():
                # --- Card UI ---
                card = ctk.CTkFrame(self.test_list_frame, fg_color="white", height=100, corner_radius=12)
                card.pack(fill="x", pady=10, padx=5)
                card.pack_propagate(False)

                # Title (Tere DB mein 'TEST' key hai)
                ctk.CTkLabel(card, text=f"{p_id}: {p_info.get('TEST', 'Mock Test')}", 
                             font=("Segoe UI", 18, "bold"), text_color=self.PRIMARY_BLUE).place(relx=0.05, rely=0.25)

                ctk.CTkLabel(card, text=f"Subject: {p_info.get('subject', 'General')}", 
                             font=("Segoe UI", 13), text_color="#5f6368").place(relx=0.05, rely=0.6)

                # Start Button (Lambda zaroori hai ID pass karne ke liye)
                ctk.CTkButton(card, text="START TEST", width=120, height=35, corner_radius=8,
              command=lambda pid=p_id, pinfo=p_info: self.start_exam_logic(pid, pinfo)).place(relx=0.8, rely=0.35)
        except Exception as e:
            print(f"❌ Fetch Error: {e}")


    def create_paper_card(self, paper_id, info):
        card = ctk.CTkFrame(self.test_list_frame, fg_color="white", height=100, corner_radius=12)
        card.pack(fill="x", pady=10, padx=5)
        card.pack_propagate(False)

        # Title Section (Using '.get' to avoid crashes)
        title_text = info.get('TEST') or info.get('title') or "Mock Test"
        title_lbl = ctk.CTkLabel(card, text=f"{paper_id}: {title_text}", 
                                 font=("Segoe UI", 18, "bold"), text_color=self.PRIMARY_BLUE)
        title_lbl.place(relx=0.05, rely=0.25)

        sub_lbl = ctk.CTkLabel(card, text=f"Subject: {info.get('subject', 'N/A')} | Questions: {info.get('total_questions', 'N/A')}", 
                               font=("Segoe UI", 13), text_color="#5f6368")
        sub_lbl.place(relx=0.05, rely=0.6)

        # Time Info
        time_lbl = ctk.CTkLabel(card, text=f"⏱️ {info.get('duration', '0')} Mins", 
                                font=("Segoe UI", 14, "bold"), text_color=self.TEXT_DARK)
        time_lbl.place(relx=0.6, rely=0.45)

        # START BUTTON FIX: 
        # Variable 'info' use karo, 'p' nahi!
        btn = ctk.CTkButton(card, text="START TEST", width=120, height=35, corner_radius=8,
                            fg_color=self.PRIMARY_BLUE, font=("Segoe UI", 13, "bold"),
                            command=lambda pid=paper_id, pinfo=info: self.start_exam_logic(pid, pinfo))
        btn.place(relx=0.8, rely=0.45)

    def reset_after_exam(self):
        self.test_on = False
        self.deiconify() # Dashboard wapas lao# Dashboard wapas dikhao
        self.load_available_tests()

    def start_exam_logic(self, p_id, p_info):
        """
        Firebase se metadata aur questions dono fetch karke sync karta hai.
        """
        if self.test_on: return
        self.test_on = True

        try:
            # 1. Security Token lo
            token = manager.get_token()
            print(f"DEBUG: Fetching Full Data for Paper ID: {p_id}")

            # 2. PEHLA FETCH: Paper ki Details (Metadata) uthao
            # Path: papers -> P001 (Isme 'subject', 'duration', 'TEST' milega)
            paper_meta = self.db.child("papers").child(p_id).get(token).val()

            # 3. DOOSRA FETCH: Asli Questions uthao
            # Path: questions -> P001 (Isme Physics, Chemistry ke subjects milenge)
            paper_content = self.db.child("questions").child(p_id).get(token).val()

            if not paper_meta or not paper_content:
                print(f"ERROR: Database mein Paper ID '{p_id}' ka data incomplete hai!")
                tmsg.showerror("Fetch Error", f"Paper {p_id} ka data load nahi ho paya!")
                self.test_on = False
                return

            # 4. DATA SYNC: p_info ko update karo asli details se
            p_info.update(paper_meta) 
            p_info['all_questions'] = paper_content # Exam_window isi key ko dhoondta hai

            # 5. USER DATA SYNC: Login screen par Sahi Subject dikhane ke liye
            combined_data = self.user_data.copy()
            combined_data['current_paper_id'] = p_id
            
            # ✅ YAHAN HAI ASLI SYNC: 
            # 'subject' key mein JSON se 'subject' (e.g. B. Tech) uthao
            combined_data['subject'] = paper_meta.get('subject', 'General Paper')

            # 6. Dashboard ko hide karo
            self.withdraw()

            # 7. Naya Popup Window banao (Fresh Start)
            self.exam_popup = ctk.CTkToplevel(self) 
            self.exam_popup.title(f"BOSS Exam Portal - {p_id}")
            self.exam_popup.attributes("-fullscreen", True)
            
            # 8. Exam Session Start
            # Object ko 'self.exam_session' mein save karna zaroori hai (Crash fix)
            self.exam_session = Exam_window.ExamSession(
                window=self.exam_popup, 
                paper_id=p_id, 
                db=self.db, 
                user_data=combined_data, 
                paper_data=p_info, 
                on_close_callback=self.reset_after_exam 
            )
            
            print(f"🚀 Nayi window mein Exam start ho gaya! Subject: {combined_data['subject']}")

        except Exception as e:
            print(f"❌ Critical Sync Error: {e}")
            tmsg.showerror("System Error", f"Test start nahi hua: {e}")
            self.test_on = False
            self.deiconify() # Error pe Dashboard wapas dikhao
    
    def load_profile_photo(self):
    # Path yahan bhi define karna padega function ke andar
        temp_path = "temp_assets/current_user.jpg"
    
        if os.path.exists(temp_path):
            try:
                img = Image.open(temp_path)
                # Yahan self.ctk_img zaroori hai taaki image memory se na ude
                self.ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(140, 140))
                self.photo_label.configure(image=self.ctk_img, text="")
            except Exception as e:
                print(f"❌ Dashboard Load Error: {e}")
        else:
            print("⚠️ File mili hi nahi!")

    # Dummy commands
    def home_click(self): print("Home Clicked")

    def tests_click(self):
        self.load_available_tests() 
        print("Tests Clicked")
    
    def results_click(self):
        user_id = self.user_data['roll_no']
    
        # 1. Firebase se data uthao
        try:
            # 'user_results' node se current user ka data fetch karo
            all_results = self.db.child("user_results").child(user_id).get().val()
        
            if not all_results:
                tmsg.showinfo("No Records", "Bhai, abhi tak tune koi test nahi diya hai!")
                return

            # 2. Latest Result nikalna (Kyuki humne paper_id ke andar save kiya tha)
            # Hum filhaal latest wala dikha rahe hain, tu list bhi bana sakta hai
            latest_paper_id = list(all_results.keys())[-1] 
            result_data = all_results[latest_paper_id]['stats']
        
            # 3. Result Window ko call karo
            # Naya function jo sirf data lekar display kare
            Result_window.show_final_from_stats(result_data)

        except Exception as e:
            print(f"❌ Fetch Error: {e}")
            tmsg.showerror("Error", "Result fetch nahi ho paya!")

    def logout(self):
        self.destroy()
        self.parent.deiconify()