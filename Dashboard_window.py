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
import time

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
        self.TEXT_DARK = "#202124"
        self.PRIMARY_BLUE = "#1a73e8"
        self.BG_COLOR = "#f8f9fa"       # Light background
        self.SIDEBAR_COLOR = "#ffffff"  # Pure white sidebar
        self.ACCENT_COLOR = "#6366f1"   # Modern Indigo (Image 2 style)
        self.CARD_BG = "#ffffff"
        self.TEXT_MAIN = "#1f2937"      # Darker grey for text

        self.configure(fg_color=self.BG_COLOR)
        self.setup_ui()
        self.update_dashboard_stats()

        self.protocol("WM_DELETE_WINDOW", self.parent.on_dashboard_close)

        # Photo loading in background
        threading.Thread(target=self.load_profile_photo, daemon=True).start()

    def setup_ui(self):
        # 1. LEFT SIDEBAR (Refined & Modern)
        self.sidebar = ctk.CTkFrame(self, width=260, fg_color=self.SIDEBAR_COLOR, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
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

        # Navigation Buttons (Using helper for consistency)
        self.nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.nav_frame.pack(fill="x", padx=15, pady=30)

        self.home_btn = self.create_nav_item("🏠  Home", self.home_click)
        self.test_btn = self.create_nav_item("📝  My Exams", self.tests_click)
        self.res_btn = self.create_nav_item("📊  Performace", self.results_click)
        self.settings = self.create_nav_item("⚙  Settings", self.settings_click)

        # Logout Button (Bottom aligned)
        self.logout_btn = ctk.CTkButton(self.sidebar, text="Sign Out", height=40,
                                        fg_color="#fee2e2", text_color="#ef4444", 
                                        hover_color="#fecaca", font=("Segoe UI", 13, "bold"),
                                        command=self.parent.handle_logout)
        self.logout_btn.pack(side="bottom", pady=30, padx=20, fill="x")

        # 2. MAIN CONTENT AREA
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(side="right", fill="both", expand=True, padx=40, pady=25)

        # Header Section (Greeting + Clock)
        self.header = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.header.pack(fill="x", pady=(0, 25))
        
        self.greeting_lbl = ctk.CTkLabel(self.header, text="", font=("Segoe UI", 26, "bold"), text_color=self.TEXT_MAIN)
        self.greeting_lbl.pack(side="left")

        self.time_lbl = ctk.CTkLabel(self.header, text="", font=("Segoe UI", 14), text_color="#6b7280")
        self.time_lbl.pack(side="right")
        self.update_clock()

        # Stats Grid (Image 2 top row)
        self.header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=(0, 25))
        
        self.stat_labels = {}
        self.stat_labels['available'] = self.create_stat_card("Active Tests", "--", self.ACCENT_COLOR, 0)
        self.stat_labels['completed'] = self.create_stat_card("Completed", "--", "#10b981", 1)
        self.stat_labels['rank'] = self.create_stat_card("Your Rank", "N/A", "#f59e0b", 2)

        # Content Title (Ye badlega jab button click hoga)

        self.content_title = ctk.CTkLabel(self.main_container,
                                        font=("Segoe UI", 28, "bold"), text_color=self.PRIMARY_BLUE)
        self.content_title.pack(anchor="w", pady=(10, 10))

        # Ye ab normal frame hai (Space occupy nahi karega)
        self.content_wrapper = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.content_wrapper.pack(fill="both", expand=True)

        # Starting mein Home dikhao
        self.home_click()

    def update_dashboard_stats(self):
        def fetch():
            try:
                # 1. Firebase se data mangwao
                token = manager.get_token()
                roll_no = self.user_data['roll_no']

                # Papers count (Available Tests)
                papers = self.db.child("papers").get(token).val()
                avail_count = len(papers) if papers else 0
                
                # Results count (Completed Tests)
                results = self.db.child("user_results").child(roll_no).get(token).val()
                comp_count = len(results) if results else 0

                # 2. UI Update (self.after zaroori hai crash se bachne ke liye)
                self.after(0, lambda: self.stat_labels['available'].configure(text=f"{avail_count:02d}"))
                self.after(0, lambda: self.stat_labels['completed'].configure(text=f"{comp_count:02d}"))
                self.after(0, lambda: self.stat_labels['rank'].configure(text="--"))

            except Exception as e:
                print(f"❌ Stats Update Error: {e}")

        # 3. Background thread mein chalao taaki app hang na ho
        threading.Thread(target=fetch, daemon=True).start()

    def create_stat_card(self, title, value, color, col):
        card = ctk.CTkFrame(self.header_frame, fg_color="white", width=250, height=100, corner_radius=12)
        card.grid(row=0, column=col, padx=(0, 20))
        card.grid_propagate(False)
        
        ctk.CTkLabel(card, text=title, font=("Segoe UI", 14), text_color="#5f6368").place(relx=0.1, rely=0.3)

        # Is label ko variable mein lo taaki return kar sakein
        val_lbl = ctk.CTkLabel(card, text=value, font=("Segoe UI", 24, "bold"), text_color=color)
        val_lbl.place(relx=0.1, rely=0.6)
        
        return val_lbl  # Yeh line add karni hai

    def get_dynamic_container(self, item_count, threshold=4):
        """
        item_count: Kitne cards ya items hain.
        threshold: Kitne items ke baad scrollbar chahiye (Default 4).
        """
        # Purana content saaf karo
        for widget in self.content_wrapper.winfo_children():
            widget.destroy()

        # Decision Logic
        if item_count > threshold:
            container = ctk.CTkScrollableFrame(self.content_wrapper, fg_color="transparent")
        else:
            container = ctk.CTkFrame(self.content_wrapper, fg_color="transparent")
        
        container.pack(fill="both", expand=True)
        return container

    def load_available_tests(self):
        try:
            # 1. Clear previous content
            for widget in self.content_wrapper.winfo_children():
                widget.destroy()

            # 2. Reset grid weights (Home click ne weights set kiye honge)
            self.content_wrapper.columnconfigure(0, weight=1)
            self.content_wrapper.columnconfigure(1, weight=0)

            # 3. Data fetch
            token = manager.get_token()
            papers_data = self.db.child("papers").get(token).val()
            
            if not papers_data:
                ctk.CTkLabel(self.content_wrapper, text="No tests available right now.", 
                             font=("Segoe UI", 16), text_color="#6b7280").pack(pady=100)
                return

            papers_list = list(papers_data.items())
            container = self.get_dynamic_container(len(papers_list), threshold=4)

            # 4. Modern Cards Loop
            for p_id, p_info in papers_list:
                card = ctk.CTkFrame(container, fg_color="white", height=120, corner_radius=15)
                card.pack(fill="x", pady=8, padx=5)
                card.pack_propagate(False)

                # Left side: Exam Info
                title = p_info.get('TEST', 'Mock Test')
                ctk.CTkLabel(card, text=title, font=("Segoe UI", 18, "bold"), 
                             text_color=self.TEXT_MAIN).place(relx=0.03, rely=0.25)
                
                detail_str = f"Subject: {p_info.get('subject', 'General')}  |  Questions: {p_info.get('total_questions', '--')}"
                ctk.CTkLabel(card, text=detail_str, font=("Segoe UI", 13), 
                             text_color="#6b7280").place(relx=0.03, rely=0.6)

                # Center side: Duration Tag
                dur_box = ctk.CTkFrame(card, fg_color="#eef2ff", corner_radius=8)
                dur_box.place(relx=0.6, rely=0.5, anchor="center")
                ctk.CTkLabel(dur_box, text=f"⏱ {p_info.get('duration', '0')} Mins", 
                             font=("Segoe UI", 12, "bold"), text_color=self.ACCENT_COLOR).pack(padx=10, pady=5)

                # Right side: Action Button
                ctk.CTkButton(card, text="START TEST", width=140, height=40, corner_radius=10,
                             fg_color=self.ACCENT_COLOR, hover_color="#4f46e5",
                             font=("Segoe UI", 13, "bold"),
                             command=lambda pid=p_id, pinfo=p_info: self.start_exam_logic(pid, pinfo)).place(relx=0.97, rely=0.5, anchor="e")

        except Exception as e:
            print(f"❌ Fetch Error: {e}")
            tmsg.showerror("Fetch Error", f"Bhai database se connect nahi ho pa raha: {e}")


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
        self.update_dashboard_stats()

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
        # 1. Identifier se roll_no hataya
        photo_url = self.user_data.get("photo_link", "")
        student_filename = "current_user.jpg"
        temp_path = os.path.join("temp_assets", student_filename)
        
        # 2. Logic ko unify kiya
        photo_loaded = False
        if not os.path.exists(temp_path) and photo_url and photo_url.startswith("http"):
            downloaded_file = manager.download_temp_image(photo_url, student_filename)
            if downloaded_file and os.path.exists(temp_path):
                photo_loaded = True
        elif os.path.exists(temp_path):
            photo_loaded = True
    
        # 3. GUI Layout
        if photo_loaded:
            try:
                img = Image.open(temp_path)
                self.ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(140, 140))
                self.photo_label.configure(image=self.ctk_img, text="")
                self.user_data["photo_path"] = temp_path
            except Exception as e:
                print(f"❌ Dashboard Load Error: {e}")
        else:
            print("⚠️ Student Profile File local par nahi hai aur download bhi fail ho gaya!")

    def update_nav_style(self, active_btn):
        # Sabko normal karo
        for btn in [self.home_btn, self.test_btn, self.res_btn]:
            btn.configure(fg_color="transparent", text_color=self.TEXT_DARK)
        # Active ko highlight karo
        active_btn.configure(fg_color="#e8f0fe", text_color=self.PRIMARY_BLUE)

    def create_nav_item(self, text, cmd):
        btn = ctk.CTkButton(self.nav_frame, text=text, fg_color="transparent", 
                            text_color="#4b5563", hover_color="#f3f4f6", 
                            anchor="w", height=45, font=("Segoe UI", 14),
                            command=cmd)
        btn.pack(fill="x", pady=4)
        return btn

    def home_click(self):
        self.update_nav_style(self.home_btn)
        self.content_title.configure(text="Home")

        for widget in self.content_wrapper.winfo_children():
            widget.destroy()

        # 70/30 Split logic
        self.content_wrapper.columnconfigure(0, weight=7)
        self.content_wrapper.columnconfigure(1, weight=3)
        self.content_wrapper.rowconfigure(0, weight=1)

        left_area = ctk.CTkFrame(self.content_wrapper, fg_color="transparent")
        left_area.grid(row=0, column=0, sticky="nsew", padx=(0, 20))

        right_area = ctk.CTkFrame(self.content_wrapper, fg_color="white", corner_radius=15)
        right_area.grid(row=0, column=1, sticky="nsew")

        # --- Left Area: Banner ---
        banner = ctk.CTkFrame(left_area, fg_color=self.ACCENT_COLOR, height=100, corner_radius=20)
        banner.pack(fill="x", pady=(0, 20))
        banner.pack_propagate(False)

        ctk.CTkLabel(banner, text=f"Welcome back, {self.user_data['name'].split()[0]}!", 
                     font=("Segoe UI", 22, "bold"), text_color="white").place(relx=0.05, rely=0.3)
        
        # --- Right Area: Firebase Tasks ---
        ctk.CTkLabel(right_area, text="Tasks", font=("Segoe UI", 16, "bold"), 
                     text_color=self.TEXT_MAIN).pack(pady=(20, 10), padx=20, anchor="w")
        
        # 1. Task Input
        self.task_entry = ctk.CTkEntry(right_area, placeholder_text="What's your goal?", height=35, 
                                       fg_color="#f3f4f6", text_color=self.TEXT_MAIN, border_width=0)
        self.task_entry.pack(fill="x", padx=15, pady=5)
        
        # 2. Add Button
        ctk.CTkButton(right_area, text="+ Add Task", height=30, fg_color=self.ACCENT_COLOR,
                      font=("Segoe UI", 12, "bold"),
                      command=self.add_task_to_firebase).pack(fill="x", padx=15, pady=5)

        # 3. Task List Container (Ye ab dynamic container banega)
        self.task_list_container = ctk.CTkFrame(right_area, fg_color="transparent")
        self.task_list_container.pack(fill="both", expand=True, padx=5, pady=10)
        
        # 4. Tasks Load Karo
        self.load_tasks_from_firebase()
        
    def tests_click(self):
        self.update_nav_style(self.test_btn)
        self.content_title.configure(text="Available Examinations")
        self.load_available_tests()
    
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

    def settings_click(self):
        pass

    def logout(self):
        self.destroy()
        self.parent.deiconify()

    def update_clock(self):
        # 1. Time nikalo
        curr_time = time.strftime("%I:%M %p | %d %b")
        self.time_lbl.configure(text=curr_time)
        # 2. Greeting logic yahan shift kar do (setup_ui se hata kar)
        h = int(time.strftime("%H"))
        greeting = "Good Morning" if h < 12 else "Good Afternoon" if h < 17 else "Good Evening"
        # Label update karo
        first_name = self.user_data['name'].split()[0]
        self.greeting_lbl.configure(text=f"{greeting}, {first_name}! 👋")
        # Har 1 second mein loop
        self.after(1000, self.update_clock)
    
    def add_task_to_firebase(self):
        task_text = self.task_entry.get().strip()
        if not task_text: return

        def run():
            try:
                token = manager.get_token()
                roll_no = self.user_data['roll_no']
                data = {"task": task_text, "timestamp": time.time()}
                # Firebase mein 'user_tasks/roll_no' ke andar push karo
                self.db.child("user_tasks").child(roll_no).push(data, token)

                self.task_entry.delete(0, 'end')
                self.load_tasks_from_firebase() # Refresh list
            except Exception as e:
                print(f"❌ Task Add Error: {e}")

        threading.Thread(target=run, daemon=True).start()
    
    def load_tasks_from_firebase(self):
        # 🛠️ CHANGES HERE: Direct destroy karne ke bajaye pehle screen se un-map karo
        # Taaki Tkinter ka draw engine crash na kare
        for widget in self.task_list_container.winfo_children():
            widget.pack_forget()
            widget.grid_forget()
            self.after(10, widget.destroy)  # 10ms ka safe gap memory clean karne ke liye

        def fetch():
            try:
                token = manager.get_token()
                roll_no = self.user_data['roll_no']
                tasks = self.db.child("user_tasks").child(roll_no).get(token).val()
                
                # UI Update Main Thread mein
                def update_ui():
                    try:  # 🛠️ CHANGES HERE: Pure UI rendering ko try-except block mein wrap kiya
                        if not tasks:
                            # Empty state logic
                            ctk.CTkLabel(self.task_list_container, text="No tasks yet! 🌟", 
                                         font=("Segoe UI", 13), text_color="#9ca3af").pack(pady=40)
                            return

                        task_items = list(tasks.items())
                        count = len(task_items)

                        # Dynamic Decision: 5 se zyada tasks toh scrollbar, warna normal frame
                        if count > 5:
                            self.active_task_frame = ctk.CTkScrollableFrame(self.task_list_container, 
                                                                           fg_color="transparent", height=380)
                        else:
                            self.active_task_frame = ctk.CTkFrame(self.task_list_container, fg_color="transparent")
                        
                        self.active_task_frame.pack(fill="both", expand=True)

                        # Tasks ko render karo (Reverse takki naya task top pe dikhe)
                        for t_id, t_data in reversed(task_items):
                            t_text = t_data.get('task', '')
                            is_done = t_data.get('status', 'pending') == 'completed'
                            self.render_task_item(t_text, t_id, is_completed=is_done)
                            
                    except Exception as render_error:
                        # Agar Tkinter background mein draw karte waqt race condition hit karega toh yahan handle ho jayega
                        print(f"⚠️ Tkinter caught rendering race condition: {render_error}")

                self.after(0, update_ui)

            except Exception as e:
                print(f"❌ Firebase Load Error: {e}")

        threading.Thread(target=fetch, daemon=True).start()

    def render_task_item(self, text, task_id, is_completed=False):
        t_box = ctk.CTkFrame(self.active_task_frame, fg_color="#f9fafb", corner_radius=8)
        t_box.pack(fill="x", pady=3, padx=5)

        # Agar task complete ho chuka hai, toh text thoda light dikhao
        if is_completed:
            display_text = f"✓ {text} (Done)"
            text_color = "#9ca3af"  # Light grey color for completed tasks
        else:
            display_text = f"• {text}"
            text_color = self.TEXT_MAIN

        task_lbl = ctk.CTkLabel(t_box, text=display_text, font=("Segoe UI", 12), 
                                text_color=text_color, wraplength=180, justify="left")
        task_lbl.pack(side="left", padx=10, pady=10, anchor="w")

        btn_frame = ctk.CTkFrame(t_box, fg_color="transparent")
        btn_frame.pack(side="right", padx=5)

        # 1. DELETE BUTTON
        delete_btn = ctk.CTkButton(btn_frame, text="✕", width=25, height=25, 
                                   fg_color="#fee2e2", text_color="#ef4444", 
                                   hover_color="#fecaca", font=("Arial", 10, "bold"),
                                   command=lambda: self.confirm_and_delete_task(task_id, text))
        delete_btn.pack(side="right", padx=2)

        # 2. DONE BUTTON
        if not is_completed:
            done_btn = ctk.CTkButton(btn_frame, text="✓", width=25, height=25, 
                                     fg_color="#d1fae5", text_color="#10b981", 
                                     hover_color="#a7f3d0", font=("Arial", 10, "bold"),
                                     command=lambda: self.mark_task_as_done(task_id))
            done_btn.pack(side="right", padx=2)

    def confirm_and_delete_task(self, task_id, task_text):
        response = tmsg.askyesno("Delete Task?", f"Bhai, kya sach mein is task ko delete karna hai?\n\n'{task_text}'")
        if response:
            def run():
                try:
                    token = manager.get_token()
                    roll_no = self.user_data['roll_no']
                    self.db.child("user_tasks").child(roll_no).child(task_id).remove(token)
                    self.after(0, self.load_tasks_from_firebase)
                except Exception as e:
                    print(f"❌ Delete Error: {e}")
            threading.Thread(target=run, daemon=True).start()

    def mark_task_as_done(self, task_id):
        def run():
            try:
                token = manager.get_token()
                roll_no = self.user_data['roll_no']
                self.db.child("user_tasks").child(roll_no).child(task_id).update({"status": "completed"}, token)
                self.after(0, self.load_tasks_from_firebase)
            except Exception as e:
                print(f"❌ Status Update Error: {e}")
        threading.Thread(target=run, daemon=True).start()