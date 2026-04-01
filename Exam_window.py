import customtkinter as ctk
import UI_composition as ui
from PIL import Image
import os
import random
import auth_manager as manager


class ExamSession:
    def __init__(self, window, paper_id, db, user_data, paper_data, on_close_callback):
        print("RAW DATA KEYS:", paper_data.keys())
        self.exam_win = window
        self.db = db
        self.paper_id = paper_id
        self.user_data = user_data
        self.paper_data = paper_data
        self.on_close_callback = on_close_callback
        
        all_q_data = self.paper_data.get('all_questions', {})

        # Subjects nikal lo (Chemistry, Physics, etc.)
        self.available_subjects = [k for k, v in all_q_data.items() if isinstance(v, list)]
        
        print(f"DEBUG: Final Subjects List: {self.available_subjects}")

        if self.available_subjects:
            self.current_subject = self.available_subjects[0]
            self.subject_questions = all_q_data.get(self.current_subject, [])
        else:
            self.current_subject = None
            self.subject_questions = []
            print("ERROR: Dashboard se questions nahi mile!")

        self.current_question_index = 0
        self.answers = {}
        self.question_status = {}
        # Timer logic (Jo Dashboard se duration aayi hai)
        raw_duration = str(self.paper_data.get('duration', '180'))
        self.time_left = int(raw_duration.split()[0]) * 60

        self.setup_ui()

        # === DEFINE ===
    def get_user_photo(self):
        photo_path = self.user_data.get("photo_path", "temp_assets/current_user.jpg")
        
        if not os.path.exists(photo_path):
            return None 
            
        # Ye line 'if' ke bahar honi chahiye (lekin function ke andar)
        return ctk.CTkImage(light_image=Image.open(photo_path),
                            dark_image=Image.open(photo_path),
                                size=(150, 150))
    
    def check_pass_input(self, event=None):
        if len(self.pass_entry.get()) > 0:
            self.signin_btn.configure(cursor="hand2", state="normal")
        else:
            self.signin_btn.configure(cursor="no", state="disabled")

    def create_tooltip(self, widget, text):
        tooltip=None
        def show_tooltip(event):
            nonlocal tooltip
            tooltip = ctk.CTkToplevel(self.exam_win)
            tooltip.wm_overrideredirect(True)
            tooltip.geometry(f"+{event.x_root + 15}+{event.y_root + 10}")
            lable = ctk.CTkLabel(tooltip, text=text, fg_color="#ffffca", text_color="black",
                                  font=("Segoe UI", 11, "bold"),corner_radius=5, padx=5,pady=2)
            lable.pack()

        def hide_tooltip(event):
                nonlocal tooltip
                if tooltip:
                    tooltip.destroy()
                    tooltip = None

        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)

    def handle_login(self):
        entered_pass = self.pass_entry.get()
        roll_no = self.user_data.get('roll_no')

        if not entered_pass:
            self.show_error_feedback("⚠️ Please Enter Password")
            return
        self.signin_btn.configure(state="disabled", text="Login...")
        self.error_frame.pack_forget()
        self.login_progress.pack(pady=10)
        self.login_progress.start()

        self.exam_win.update_idletasks()

        success, full_data = manager.validate_exam_login(self.db, roll_no, entered_pass)

        self.login_progress.stop()
        self.login_progress.pack_forget()

        if success:
            self.user_data = full_data
            self.details_frame.pack_forget()
            self.login_area.destroy()
            self.show_instructions()
        else:
            self.error_frame.pack(pady=(5,10), padx=40, fill="x")
            self.show_error_feedback("❌ Invalid Password! Please try again.")
            self.signin_btn.configure(state="normal", text="SIGN IN")
        
    def show_error_feedback(self, message):
            self.error_frame.configure(border_width=1, border_color="#D32F2F", fg_color="#FFEBEE")
            self.error_lbl.configure(text=message)

            def clear_error():
                if self.error_frame.winfo_exists():
                    self.error_frame.configure(border_width=0, fg_color="transparent")
                    self.error_lbl.configure(text="")
                
            self.exam_win.after(3000, clear_error)

    def setup_ui(self):
        # ---- WINDOW SECTION ----
        self.exam_win.title("Exam Session")
        self.exam_win.iconbitmap("BOSS-LOGO.ico")
        self.exam_win.attributes("-fullscreen", True)
        self.exam_win.configure(fg_color="white", cursor="arrow")

        # === UI ===
        # === HEADER SECTION ===
        self.header_frame = ctk.CTkFrame(self.exam_win, height=40, fg_color="#003366", corner_radius=0)
        self.header_frame.pack(side="top", fill="x")
        # TODO: software logo and title

        # === DETAILS SECTION ===

        Candidate_name = self.user_data.get('name', "N/A").upper()
        ROLL = self.user_data.get('roll_no', "N/A").upper()
        Subject = self.user_data.get('subject', "General Paper").upper()

        
        self.details_frame = ctk.CTkFrame(self.exam_win, height=250, fg_color="#14141b", corner_radius=0)
        self.details_frame.pack(side="top", fill="x")
        self.details_frame.pack_propagate(False)

        sys_rand_no = f"{random.randint(1, 999):03}" # :03 ka matlab 3 digits (e.g., 007)
        display_sys_name = f"C{sys_rand_no}"
        
        self.sys_lbl = ctk.CTkLabel(self.details_frame, text="System:", font=("Segoe UI", 40, "italic"), text_color="gray")
        self.sys_lbl.pack(side="left", padx=20, pady=(60,60))
        self.sys_no = ctk.CTkLabel(self.details_frame, text=display_sys_name, font=("Segoe UI", 40, "italic"), text_color="white")
        self.sys_no.pack(side="left", padx=20, pady=(60,60))

        # === PHOTO AND INFO ===
        self.R_panel = ctk.CTkFrame(self.details_frame, fg_color="transparent")
        self.R_panel.pack(side="right", padx=20, fill="y")

        # 1. DETAILS GRID (Left of Photo)
        # Is frame ke andar hum grid use karenge
        self.info_grid = ctk.CTkFrame(self.R_panel, fg_color="transparent")
        self.info_grid.pack(side="left", padx=20, pady=10)

        # Row 0: Name
        ctk.CTkLabel(self.info_grid, text="Candidate Name:", font=("Segoe UI", 20, "italic"), text_color="gray").grid(row=0, column=0, sticky="e", pady=2)
        ctk.CTkLabel(self.info_grid, text=f"{Candidate_name}", font=("Segoe UI", 30, "italic"), text_color="white").grid(row=1, column=0, sticky="e", pady=2)

        # Row 1: Roll No
        ctk.CTkLabel(self.info_grid, text="Roll No:", font=("Segoe UI", 20, "italic"), text_color="gray").grid(row=2, column=0, sticky="e", pady=2)
        ctk.CTkLabel(self.info_grid, text=f"{ROLL}", font=("Segoe UI", 30, "italic"), text_color="white").grid(row=3, column=0, sticky="e", pady=2)

        # Row 2: Subject
        ctk.CTkLabel(self.info_grid, text="Subject:", font=("Segoe UI", 20, "italic"), text_color="gray").grid(row=4, column=0, sticky="e", pady=2)
        ctk.CTkLabel(self.info_grid, text=f"{Subject}", font=("Segoe UI", 30, "italic"), text_color="white").grid(row=5, column=0, sticky="e", pady=2)

        # === PHOTO BOX ===
        self.photo_box = ctk.CTkFrame(self.R_panel, width=130, height=150, 
                                      fg_color="#333333", border_width=2, border_color="gray")
        self.photo_box.pack(side="left", padx=10)
        self.photo_box.pack_propagate(False)

        # Ab apne banaye huye function ko call karo
        user_img = self.get_user_photo()

        if user_img:
            self.photo_label = ctk.CTkLabel(self.photo_box, image=user_img, text="")
            self.photo_label.pack(fill="both", expand=True)
        else:
            ctk.CTkLabel(self.photo_box, text="NO PHOTO", text_color="white").place(relx=0.5, rely=0.5, anchor="center")
        
        # === LOGIN SECTION ===

        self.login_area = ctk.CTkFrame(self.exam_win, fg_color="#e9e9e9", corner_radius=0)
        self.login_area.pack(fill="both", expand=True)
        
        self.login_box = ctk.CTkFrame(self.login_area, width=400, height=420, fg_color="white", border_width=1, border_color="#cccccc")
        self.login_box.place(relx=0.5, rely=0.4, anchor="center")
        self.login_box.pack_propagate(False)

        self.login_title = ctk.CTkFrame(self.login_box, height=60, fg_color="#A6AAAC", corner_radius=0)
        self.login_title.pack(fill="x", padx=5, pady=5)

        self.log_title = ctk.CTkLabel(self.login_title, text="Login", font=("AgencyFB", 22, "bold"), text_color="black")
        self.log_title.pack(padx=5, pady=10, anchor="w")

        self.log_title = ctk.CTkLabel(self.login_box, text="ROLL NO.", font=("AgencyFB", 22, "bold"), text_color="lightblue")
        self.log_title.pack(padx=30,pady=10, anchor="w")

        self.roll_entry = ctk.CTkEntry(self.login_box, width=330, height=40, text_color="gray", font=("Segoe UI", 15, "bold"), corner_radius=5,)
        self.roll_entry.insert(0, ROLL)
        self.roll_entry.configure(state="disabled", fg_color="lightgray", cursor="no")
        self.roll_entry.pack(pady=2)

        self.pass_title = ctk.CTkLabel(self.login_box, text="PASSWORD", font=("AgencyFB", 22, "bold"), text_color="lightblue")
        self.pass_title.pack(padx=30, pady=10, anchor="w")

        self.pass_entry = ctk.CTkEntry(self.login_box, width=330, height=40, text_color="gray", font=("Segoe UI", 15, "bold"),
                                        fg_color="lightgray", corner_radius=5,)
        self.pass_entry.pack(pady=2)
        self.pass_entry.focus_set()
        self.pass_entry.bind("<KeyRelease>", self.check_pass_input)
        self.create_tooltip(self.pass_entry, "Enter you Date Of Birth (DOB) as Password (e.g., DDMMYYYY)")
        
        # === ERROR FRAME ===
        self.error_frame = ctk.CTkFrame(self.login_box, fg_color="transparent", border_width=0)
        self.error_frame.pack(pady=(5,10), padx=40, fill="x")
        self.error_lbl = ctk.CTkLabel(self.error_frame, text="",text_color="#D32F2F",
                                      font=("Segoe UI",12, "bold"))
        self.error_lbl.pack(pady=5)

        # === PROGRESSBAR SECTION ===
        self.login_progress = ctk.CTkProgressBar(self.login_box, width=320, mode="indeterminate",
                                                  indeterminate_speed=1.5, fg_color="#f2f2f2",
                                                  progress_color="#003366")

        # === SIGN IN SECTION ===
        self.signin_btn = ctk.CTkButton(self.login_box, text="SIGN IN", cursor="no", font=("AgencyFB", 15, "bold"),
                                         width=330, height=45, hover_color="#0bbd46", 
                                         state="disabled", command=self.handle_login)
        self.signin_btn.pack(pady=40)

    # === INSTRUCTION SECTION ===
    def show_instructions(self):
        # === INSTRUCTION CONTAINER ===
        self.inst_cont = ctk.CTkFrame(self.exam_win, fg_color="white")
        self.inst_cont.pack(fill="both", expand=True)

        # === TOP TITLE BAR ===
        title_bar = ctk.CTkFrame(self.inst_cont, height=40, fg_color="#D16E1D", corner_radius=0)
        title_bar.pack(fill="x")
        ctk.CTkLabel(title_bar, text="Please read the instructions carefully",
                      font=("AgencyFB", 16, "bold"), text_color="white").pack(pady=5, anchor="center")
        
        # === MIDDLE CONTENT AREA ===
        cont_frame = ctk.CTkFrame(self.inst_cont, fg_color="transparent")
        cont_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # === LEFT: SCROLLABLE RULES (70% WIDTH)
        self.rules_scroll = ctk.CTkScrollableFrame(cont_frame, fg_color="#fcfcfc", border_width=1, border_color="#cccccc")
        self.rules_scroll.pack(side="left", fill="both", expand=True, padx=(0,15))

        # === SECTION 1: TEXT RULES ===
        TEST = self.paper_data.get('TEST', "General Paper").upper()
        DURATION = self.paper_data.get('duration', "N/A").upper()

        ctk.CTkLabel(self.rules_scroll, text="General Instruction:", font=("AgencyFB", 20, "bold", "underline"), text_color="black").pack(anchor="w")
        
        # --- SECTION 1: TEXT RULES ---
        self.add_rule_text(f"Total duration of {TEST} is {DURATION} mins." \
        "\nThe clock will be set at the server." \
        " The countdown timer in the top right corner of" \
        " screen will display the remaining time" \
        " available for you to complete the examination.")
        
        # --- SECTION 2: SYMBOLS LEGEND ---
        self.add_rule_text("\nQuestion Palette Symbols:", font=("Segoe UI", 20, "bold"))
        symbol_data = [
                    ("#ffffff", "You have not visited the question yet."),
                    ("#ff0000", "You have not answered the question."),
                    ("#00ff00", "You have answered the question."),
                    ("#7030a0", "You have NOT answered the question, but marked for review.")
                ]
        for color, desc in symbol_data:
                    row = ctk.CTkFrame(self.rules_scroll, fg_color="#ffffca", border_width=1, border_color="gray")
                    row.pack(fill="x", pady=2, padx=10)
                    ctk.CTkLabel(row, text="", width=20, height=20, fg_color=color, text_color="gray").pack(side="left", padx=10, pady=10)
                    ctk.CTkLabel(row, text=desc, font=("Segoe UI", 15, "bold"), text_color="black").pack(side="left", padx=10)
        
        # --- SECTION 3: MARKING SCHEME TABLE ---
        self.add_rule_text("\nExamination Structure & Marking Scheme:", font=("Segoe UI", 20, "bold"))
        self.create_instruction_table(self.rules_scroll)
        
        # --- SECTION 4: FINAL PROCEDURES ---
        self.add_rule_text("\nNavigating to a Question:", font=("Segoe UI", 20, "bold"))
        self.add_rule_text("- Click on 'Save & Next' to save your answer." \
        "\n- Click on 'Mark for Review & Next' to save and review later." \
        "\n- To change an answer, click 'Clear Response'.")

        self.add_rule_text("\nTerms & Conditions:", font=("Segoe UI", 20, "bold"))
        footer = ctk.CTkFrame(self.rules_scroll, height=100, fg_color="#eeeeee", corner_radius=2, border_width=1)
        footer.pack(pady=5, side="bottom", fill="x")

        self.agree_var = ctk.BooleanVar(value=False)
        agreement = "I have read and understood the instructions." \
        "I declare that I am not in possession of any prohibited gadgets." \
        "\nI agree that in case of not adhering to the instruction," \
        "I shall be liable for disciplinary action"
        
        self.agree_var = ctk.CTkCheckBox(footer, text=agreement, variable=self.agree_var, font=("Segoe UI", 16),
                                         command=self.toggle_proceed, text_color="black")
        self.agree_var.pack(padx=10, pady=15, fill="x", anchor="w")
        self.proceed_btn = ctk.CTkButton(footer, text="START", text_color="white", width=300, height=45,
                                         fg_color="#003366", state="disabled", command=self.start_exam)
        self.proceed_btn.pack(pady=10)

    def add_rule_text(self, text, font=("Segoe UI", 20)):
        lbl = ctk.CTkLabel(self.rules_scroll, text=text, font=font, text_color="black", justify="left", wraplength=800)
        lbl.pack(anchor="w", pady=5, padx=10)

    def create_instruction_table(self, parent):
        table_frame = ctk.CTkFrame(parent, fg_color="transparent")
        table_frame.pack(pady=10, padx=10, fill="x")
        headers = ["Section", "Questions", "Correct", "Negative"]
        data = [["Physics", "25", "+4", "-1"], ["Chemistry", "25", "+4", "-1"], ["Maths", "25", "+4", "-1"]]
        
        for col, h in enumerate(headers):
            cell = ctk.CTkFrame(table_frame, fg_color="#003366", corner_radius=0, border_width=1, border_color="white")
            cell.grid(row=0, column=col, sticky="nsew")
            ctk.CTkLabel(cell, text=h, font=("Segoe UI", 15, "bold"), text_color="white").pack(padx=10, pady=5)

        for r_idx, r_data in enumerate(data, 1):
            for c_idx, val in enumerate(r_data):
                cell = ctk.CTkFrame(table_frame, fg_color="white", corner_radius=0, border_width=1, border_color="#cccccc")
                cell.grid(row=r_idx, column=c_idx, sticky="nsew")
                ctk.CTkLabel(cell, text=val, font=("Segoe UI", 15, "bold"), text_color="black").pack(padx=10, pady=5)
        for i in range(4): table_frame.grid_columnconfigure(i, weight=1)

    def toggle_proceed(self):
        state = "normal" if self.agree_var.get() else "disabled"
        self.proceed_btn.configure(state=state, cursor="hand2" if state=="normal" else "no")

    def start_exam(self):
        print(f"Starting Exam... {self.paper_id}")
        self.inst_cont.destroy()
        self.details_frame.pack(side="top", fill="x")
        self.Setup_exam_interface()
        # Yahan hum load_exam_interface() call karenge jo hum agle step mein banayenge

    def render_question_area(self):
        """Sawal dikhane ke liye dhancha taiyar karna"""
        # 1. Question Number Label
        self.q_num_lbl = ctk.CTkLabel(self.left_panel, text="", 
                                      font=("Segoe UI", 18, "bold"), text_color="#003366")
        self.q_num_lbl.pack(anchor="w", padx=20, pady=(10, 0))

        # 2. Actual Question Text (Yeh wo hai jo missing tha)
        self.q_text_lbl = ctk.CTkLabel(self.left_panel, text="Loading...", 
                                       font=("Segoe UI", 20), wraplength=800, 
                                       justify="left", text_color="black")
        self.q_text_lbl.pack(anchor="w", padx=30, pady=20)

        # 3. Options Container
        self.opt_var = ctk.StringVar(value="") 
        self.options_container = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        self.options_container.pack(fill="both", expand=True, padx=40, pady=20)
        
        self.opt_btns = [] # Empty list for radio buttons

    def load_question(self):
        # 1. Purane buttons uda do
        for btn in self.opt_btns:
            btn.destroy()
        self.opt_btns = []

        questions = self.subject_questions 
        if not questions or self.current_question_index >= len(questions):
            self.q_text_lbl.configure(text="Sawal khatam ho gaye!")
            return

        q_data = questions[self.current_question_index]
        
        # UI Update
        self.q_num_lbl.configure(text=f"Question No. {self.current_question_index + 1}")
        self.q_text_lbl.configure(text=q_data.get('q', 'No Question Found'))

        # 2. Options Render logic (ASLI FIX YAHAN HAI)
        opts_dict = q_data.get('options', {})
        
        for key in ['A', 'B', 'C', 'D']:
            if key in opts_dict:
                opt_text = opts_dict[key]
                
                # FIX: text mein humne f"{key}:" hata diya hai
                rb = ctk.CTkRadioButton(
                    self.options_container, 
                    text=f"{opt_text}", # <--- Sirf option ka text dikhega
                    variable=self.opt_var,
                    value=key,          # <--- Lekin backend mein 'A' hi save hoga
                    font=("Segoe UI", 25),
                    hover_color="#1a73e8",
                    text_color="black"
                )
                rb.pack(anchor="w", pady=12)
                self.opt_btns.append(rb)

        # Saved answer restore
        saved_ans = self.answers.get(f"{self.current_subject}_{self.current_question_index}", "")
        self.opt_var.set(saved_ans)

    def switch_subject(self, new_subject):
        """Manual click aur Next/Prev looping dono ke liye ek hi function"""
        print(f"DEBUG: Switching UI for {new_subject}")
        
        # 1. Data Update
        self.current_subject = new_subject
        all_q_data = self.paper_data.get('all_questions', {})
        self.subject_questions = all_q_data.get(new_subject, [])
        self.current_question_index = 0
        
        # 2. Visual: Question Text & Options update karo
        self.load_question()
        
        # 3. Visual: Question Palette ko naye subject ke hisaab se redraw karo
        self.refresh_palette()
        
        # 4. Visual: Subject Tabs ka color (Active/Inactive) update karo
        self.update_tab_colors()

    def render_palette_area(self):
        # 1. Pehle frame ko saaf karo
        for widget in self.right_panel.winfo_children():
            widget.destroy()

        # 2. Section Title
        ctk.CTkLabel(self.right_panel, text="QUESTION PALETTE", 
                     font=("Segoe UI", 16, "bold"), fg_color="#123fff", text_color="#FFFFFF", corner_radius=5).pack(padx=5, pady=5, fill="x")

        # 4. Asli Palette Scrollable Frame
        # IMPORTANT: fg_color ko thoda alag rakho taaki dikhe ki frame kahan hai
        self.palette_scroll = ctk.CTkScrollableFrame(self.right_panel, fg_color="#f0f0f0", 
                                                     width=280, height=400)
        self.palette_scroll.pack(fill="both", expand=True, padx=10, pady=5)

        # 5. Buttons ko load karo
        self.refresh_palette()

    def update_current_status(self):
        """Sawal badalne se pehle uska status check karo"""
        current_key = f"{self.current_subject}_{self.current_question_index}"
        
        # Agar is sawal ka pehle se koi status nahi hai (matlab abhi visit kiya hai)
        # Ya agar status 'not_visited' hai, toh usse 'not_answered' (Red) kar do
        if self.question_status.get(current_key) in ["not_visited", None]:
            self.question_status[current_key] = "not_answered"

    def refresh_palette(self):
        # Frame ke andar ka purana kachra saaf karo
        for widget in self.palette_scroll.winfo_children():
            widget.destroy()

        num_q = len(self.subject_questions)
        print(f"DEBUG: Refreshing palette with {num_q} questions")

        if not self.subject_questions:
            print("DEBUG: No questions to show in palette")
            return

        # Grid settings
        cols = 4
        for i in range(len(self.subject_questions)):
            q_num = i + 1
            # Status check
            status_key = f"{self.current_subject}_{i}"
            status = self.question_status.get(status_key, "not_visited")

            if status == "answered_marked":
                btn = ui.QuestionPaletteBtn(
                    self.palette_scroll, 
                    num=q_num, 
                    status=status,
                    command=lambda idx=i: self.jump_to_question(idx)
                )
                btn.grid(row=i // cols, column=i % cols, padx=8, pady=8)
                btn.configure(border_width=3, border_color=ui.THEME["GREEN"]) 
            else:
                btn = ui.QuestionPaletteBtn(
                    self.palette_scroll, 
                    num=q_num, 
                    status=status,
                    command=lambda idx=i: self.jump_to_question(idx)
                )
                btn.grid(row=i // cols, column=i % cols, padx=8, pady=8)

    def jump_to_question(self, index):
        current_key = f"{self.current_subject}_{self.current_question_index}"
        if current_key not in self.question_status:
            self.question_status[current_key] = "not_answered"

        self.current_question_index = index
        self.load_question()
        self.refresh_palette()


    def render_nav_buttons(self):
        # ERROR FIX: Ensure navigation frame is in main_frame and NO GRID is used in main_frame
        # Agar tune main_frame mein grid use kiya hai, toh yahan bhi .grid() use karna padega
        
        self.nav_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.nav_frame.pack(side="bottom", fill="x", padx=40, pady=20)

        # === Previous Button ===
        self.prev_btn = ui.ActionButton(self.nav_frame, text="← PREVIOUS",
                                        color=ui.THEME["PRIMARY"],
                                        command=self.prev_question)
        self.prev_btn.pack(side="left", padx=10)

        self.next_btn = ui.ActionButton(self.nav_frame, text="NEXT →", 
                                               color=ui.THEME["PRIMARY"], 
                                               command=self.next_question,)
        self.next_btn.pack(side="left", padx=10)

        # 1. Mark for Review
        self.mark_btn = ui.ActionButton(
            self.nav_frame, text="MARK FOR REVIEW", 
            color=ui.THEME["PURPLE"],
            command=self.mark_for_review_only
        )
        self.mark_btn.pack(side="left", padx=10)

        # 2. Clear Response
        self.clear_btn = ui.ActionButton(
            self.nav_frame, text="CLEAR RESPONSE", 
            color=ui.THEME["WHITE"], text_color=ui.THEME["TEXT_DARK"],
            command=self.clear_response,
            border_width=1, border_color=ui.THEME["GRAY"]
        )
        self.clear_btn.pack(side="left", padx=10) # Nav_frame ke andar pack allowed hai

        # 3. Save & Next
        self.save_btn = ui.ActionButton(
            self.nav_frame, text="SAVE & NEXT", 
            color=ui.THEME["PRIMARY"],
            command=self.save_and_next
        )
        self.save_btn.pack(side="right", padx=10)


        # 4. Save and Mark for Review
        self.save_mark_btn = ui.ActionButton(self.tabs_frame, text="SAVE & MARK FOR REVIEW", 
                                             color="#2c3e50",
                                             command=self.save_and_mark_review)
        self.save_mark_btn.pack(side="right", padx=10)

        # === SUBMIT BUTTON ===

    def clear_response(self):
        """Bhai, ye selection hatane ke liye hai"""
        print("DEBUG: Clearing Response...")
        self.opt_var.set("") # Radio button selection reset
        
        current_key = f"{self.current_subject}_{self.current_question_index}"
        
        # Agar pehle se answer saved tha, toh delete karo
        if current_key in self.answers:
            del self.answers[current_key]
        
        # Status 'not_answered' (Red) kar do kyunki ab koi option selected nahi hai
        self.question_status[current_key] = "not_answered"
        self.refresh_palette()

    def mark_for_review_only(self):
        """SIRF MARK: Option select nahi kiya, bas purple karna hai"""
        current_key = f"{self.current_subject}_{self.current_question_index}"
        
        # Agar galti se option select tha, toh use answer list se hata do
        if current_key in self.answers:
            del self.answers[current_key]
            
        self.question_status[current_key] = "marked" # Purple
        self.next_question()

    def save_and_mark_review(self):
        """SAVE + MARK: Answer bhi chahiye aur review bhi"""
        current_key = f"{self.current_subject}_{self.current_question_index}"
        val = self.opt_var.get()
        
        if val:
            self.answers[current_key] = val
            self.question_status[current_key] = "answered_marked" # Special Status
            self.next_question()
        else:
            # Agar option select nahi kiya aur ye button dabaya, toh warning do ya normal mark kar do
            print("WARNING: Please select an option to 'Save' & Mark")

    def save_and_next(self):
        """Save and Next logic (Green color)"""
        current_key = f"{self.current_subject}_{self.current_question_index}"
        val = self.opt_var.get()
        
        if val:
            self.answers[current_key] = val
            self.question_status[current_key] = "answered"
            self.next_question()
        else:
            # Agar bina select kiye Save dabaya, toh Red kar do status
            self.question_status[current_key] = "not_answered"
            self.next_question()

    def next_question(self):
        """Agle sawal pe le jane wala engine"""
        if self.current_question_index < len(self.subject_questions) - 1:
            self.current_question_index += 1
            self.load_question()
            self.refresh_palette()
        else:
            print("INFO: Last question of this subject reached.")

    def next_question(self):
        # 1. Jo sawal abhi screen pe hai, usse 'not_answered' mark karo agar answer nahi diya
        self.update_current_status()

        subjects = self.available_subjects
        if self.current_question_index < len(self.subject_questions) - 1:
            self.current_question_index += 1
            self.load_question()
            self.refresh_palette() # Palette update hoga aur pichla wala Red dikhega
        else:
            # Subject Loop
            next_idx = (subjects.index(self.current_subject) + 1) % len(subjects)
            self.switch_subject(subjects[next_idx])

    def prev_question(self):
        # 1. Current sawal ko 'not_answered' mark karo
        self.update_current_status()

        subjects = self.available_subjects
        if self.current_question_index > 0:
            self.current_question_index -= 1
        else:
            # Prev Subject Loop
            prev_idx = (subjects.index(self.current_subject) - 1) % len(subjects)
            self.current_subject = subjects[prev_idx]
            self.subject_questions = self.paper_data.get('all_questions', {}).get(self.current_subject, [])
            self.current_question_index = len(self.subject_questions) - 1
            self.update_tab_colors()

        self.load_question()
        self.refresh_palette()
    
    def update_tab_colors(self):
        """Subject tabs ka background color change karne ke liye"""
        if hasattr(self, 'sub_btns'):
            for sub_name, btn_obj in self.sub_btns.items():
                if sub_name == self.current_subject:
                    # Jo select hua hai: Blue background, White text
                    btn_obj.configure(
                        fg_color=ui.THEME["PRIMARY"], 
                        text_color=ui.THEME["TEXT_LIGHT"]
                    )
                else:
                    # Jo select nahi hai: No background, Black text
                    btn_obj.configure(
                        fg_color="transparent", 
                        text_color=ui.THEME["TEXT_DARK"]
                    )

    def Setup_exam_interface(self):
        """Poora Exam Layout set karna"""
        if hasattr(self, 'main_frame'): self.main_frame.destroy()

        if not hasattr(self, 'current_subject') or not self.current_subject:
            if self.available_subjects:
                self.current_subject = self.available_subjects[0]

        self.main_frame = ctk.CTkFrame(self.exam_win, fg_color="white")
        self.main_frame.pack(fill="both", expand=True)

        self.sub_btns = {} 

        # Tabs logic...
        self.tabs_frame = ctk.CTkFrame(self.main_frame, height=45, fg_color="#f2f2f2", corner_radius=0)
        self.tabs_frame.pack(side="top", fill="x")

        for sub in self.available_subjects:
            is_active = (sub == self.current_subject)
            btn = ui.SubjectTab(
                self.tabs_frame, text=sub.upper(), 
                command=lambda s=sub: self.switch_subject(s),
                is_active=is_active
            )
            btn.pack(side="left", padx=2, pady=5)
            
            # ASLI FIX: Button ko save karo taaki baad mein color change kar sakein
            self.sub_btns[sub] = btn

        # Main Panels
        self.content_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.content_container.pack(fill="both", expand=True)

        self.left_panel = ctk.CTkFrame(self.content_container, fg_color="white", corner_radius=0)
        self.left_panel.pack(side="left", fill="both", expand=True)

        # SEQUENCE FIX: Pehle render (dhancha), phir load (data)
        self.render_question_area() # <--- Pehle labels banao
        
        self.right_panel = ctk.CTkFrame(self.content_container, width=320, fg_color="#f5f5f5", border_width=1)
        self.right_panel.pack(side="right", fill="y")
        self.right_panel.pack_propagate(False)

        self.render_palette_area()
        self.load_question() # <--- Ab data load karo, error nahi aayega
        self.render_nav_buttons()

# TESTING CODE (Isse run karke dekh)
def open_exam(root, paper_id, db, user_data, paper_data, on_close):
    exam_win = ctk.CTkToplevel(root)
    # Ye line class ka object banati hai aur window usse pakda deti hai
    ExamSession(exam_win, paper_id, db, user_data, paper_data, on_close)