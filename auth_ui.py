import customtkinter as ctk
import cv2
import auth_manager as manager
from UI_composition import ActionButton, THEME
import os
from tkinter import messagebox as tmsg
from PIL import Image
from tkinter import filedialog
from auth_manager import process_registration # Tera manager function

class AuthUI(ctk.CTkFrame):
    def check_category(self, choice):
        if choice == "Others":
            self.other_cat_entry.pack(pady=5, after=self.category_combo)
        else:
            self.other_cat_entry.pack_forget()
            self.other_cat_entry.delete(0, 'end')

    def __init__(self, parent, controller, db, auth):
        super().__init__(parent, fg_color="white", corner_radius=25)
        self.controller = controller
        self.db = db # Ye zaroori hai error hatane ke liye
        self.auth = auth
        self.captured_image = None 

        # --- GRID CONFIG ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- BACK BUTTON (Professional Placement) ---
        self.back_btn = ctk.CTkButton(self, text="← Back", command=lambda: self.controller.show_home(),
                                      width=60, height=30, text_color="lightblue", hover_color="#1a3a5f")
        self.back_btn.place(x=10, y=10)

        # --- SCROLLABLE CONTAINER ---
        self.scroll_canvas = ctk.CTkScrollableFrame(self, fg_color="transparent", width=400, height=450)
        self.scroll_canvas.grid(row=0, column=0, padx=10, pady=(50, 10), sticky="nsew")
        self.scroll_canvas.grid_columnconfigure(0, weight=1)

        # --- FORM FIELDS ---
        ctk.CTkLabel(self.scroll_canvas, text="Create Account", font=("Segoe UI", 24, "bold"), text_color="#1a3a5f").grid(pady=(0, 20))
        
        self.name_entry = self.add_field("Full Name", "Name as per Document")
        self.mobile_entry = self.add_field("Mobile", "10-Digit Phone Number")
        
        # DOB Section
        ctk.CTkLabel(self.scroll_canvas, text="Date of Birth", text_color="#1a3a5f", font=("Segoe UI", 13)).grid(pady=(10,0))
        self.dob_frame = ctk.CTkFrame(self.scroll_canvas, fg_color="transparent")
        self.dob_frame.grid(pady=5)
        self.day = ctk.CTkComboBox(self.dob_frame, values=[str(i).zfill(2) for i in range(1, 32)], width=70)
        self.month = ctk.CTkComboBox(self.dob_frame, values=[str(i).zfill(2) for i in range(1, 13)], width=70)
        self.year = ctk.CTkComboBox(self.dob_frame, values=[str(i) for i in range(1990, 2015)], width=90)
        self.day.grid(row=0, column=0, padx=2)
        self.month.grid(row=0, column=1, padx=2)
        self.year.grid(row=0, column=2, padx=2)

        # --- GENDER SECTION ---
        ctk.CTkLabel(self.scroll_canvas, text="Gender", text_color="#1a3a5f", font=("Segoe UI", 13)).grid(pady=(10,0))
        self.gender_combo = ctk.CTkComboBox(self.scroll_canvas, values=["Male", "Female", "Other"], width=320)
        self.gender_combo.grid(pady=5)

        # --- CATEGORY SECTION ---
        ctk.CTkLabel(self.scroll_canvas, text="Category", text_color=["white","#1a3a5f"], font=("Segoe UI", 13)).grid(pady=(10,0))
        # Ek container frame banao jo category ki saari cheezein hold karega
        self.cat_container = ctk.CTkFrame(self.scroll_canvas, fg_color="transparent")
        self.cat_container.grid(pady=5)

        self.category_var = ctk.StringVar(value="SELECT CATEGORY")
        self.category_combo = ctk.CTkComboBox(
            self.cat_container, # Frame ke andar dalo
            values=["GENERAL", "GEN_PwD", "OBC", "OBC_PwD", "SC", "SC_PwD", "ST", "ST_PwD", "Others"], 
            variable=self.category_var, 
            command=self.check_category, 
            width=320
        )
        self.category_combo.pack(pady=2) # Pack use karo container ke andar
        # Hidden Entry (Ye bhi frame ke andar)
        self.other_cat_entry = ctk.CTkEntry(self.cat_container, placeholder_text="Specify Category", width=320)
        # Isse abhi pack nahi karenge

        # ---- Email ----
        self.email_entry = self.add_field("Email", "example@mail.com")
        
        # --- PASSWORD ---
        self.pass_entry = self.add_field("Private Password", "For dashboard login", show="*")

        # --- PHOTO SECTION ---
        self.photo_label = ctk.CTkLabel(self.scroll_canvas, text="No Photo Selected", 
                                        text_color="#1a3a5f", width=200, height=150, fg_color="#91949e", corner_radius=12)
        self.photo_label.grid(pady=20)

        self.btn_frame = ctk.CTkFrame(self.scroll_canvas, fg_color="transparent")
        self.btn_frame.grid(pady=5)

        self.cap_btn = ctk.CTkButton(self.btn_frame, text="📷 Live Capture", command=self.capture_photo, 
                                     fg_color="#1a3a5f", width=140)
        self.cap_btn.grid(row=0, column=0, padx=5)

        self.up_btn = ctk.CTkButton(self.btn_frame, text="📁 Upload", command=self.upload_photo, 
                                    fg_color="#10b981", width=140)
        self.up_btn.grid(row=0, column=1, padx=5)

        # --- SUBMIT ---
        self.reg_btn = ctk.CTkButton(self.scroll_canvas, text="Complete Registration", 
                                     command=self.submit_data, height=45, fg_color="#1a3a5f", font=("Segoe UI", 15, "bold"))
        self.reg_btn.grid(pady=30)


    def add_field(self, label, placeholder, show=""):
        ctk.CTkLabel(self.scroll_canvas, text=label, font=("Segoe UI", 13),
                      text_color=["#1a3a5f","#000000"]).grid(pady=(10,0), sticky="w", padx=40)
        
        entry = ctk.CTkEntry(self.scroll_canvas, placeholder_text=placeholder, width=320, height=35, show=show,
                                border_width=1, placeholder_text_color=["#64748b", "#94a3b8"],
                                fg_color=["#ffffff", "#2d3748"],
                                text_color=["#000000", "#ffffff"])
        entry.grid(pady=5)
        return entry

    def update_preview(self, cv2_img):
        self.captured_image = cv2_img
        rgb_img = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb_img)
        ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(200, 150))
        self.photo_label.configure(image=ctk_img, text="")

    def capture_photo(self):
        """BOSS! Camera window open karega aur SPACE dabate hi photo lega"""
        cap = cv2.VideoCapture(0)
        while True:
            ret, frame = cap.read()
            cv2.imshow("Capture Photo - Press or Press & hold SPACE to Capture / press & hold ESC to close", frame)
            if cv2.waitKey(1) & 0xFF == ord(' '): # Space key logic
                self.update_preview(frame)
                break
            if cv2.waitKey(1) & 0xFF == 27: # ESC to cancel
                break
        cap.release()
        cv2.destroyAllWindows()

    def upload_photo(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.png *.jpeg")])
        if path:
            img = cv2.imread(path)
            self.update_preview(img)

    def submit_data(self):
        # 1. Category Validation
        selected_cat = self.category_combo.get()
        if selected_cat == "Others":
            final_cat = self.other_cat_entry.get().strip() 
            if not final_cat:
                tmsg.showwarning("Warning", "Please specify your category!")
                return # <-- Ye sirf 'Other' khali hone par chalega
        else:
            final_cat = selected_cat
            
        user_data = {
            "name": self.name_entry.get().strip(),
            "mobile": self.mobile_entry.get().strip(),
            "email": self.email_entry.get().strip(),
            "day": self.day.get(),
            "month": self.month.get(),
            "year": self.year.get(),
            "gender": self.gender_combo.get(),
            "category": final_cat,
            "password": self.pass_entry.get()
        }

        # Check agar koi field khali hai
        if any(v == "" for v in user_data.values()):
            tmsg.showwarning("Incomplete Form", "Please fill all Required Fields!")
            return
        
        if self.captured_image is None:
            tmsg.showwarning("Photo Missing", "Bhai, pehle photo toh khich le!")
            return            

        # 2. REVIEW WINDOW & FINAL PROCESS
        from auth_manager import open_review_window, process_registration # <-- Dono import yahan honge
        
        def final_confirm():
            app_no = process_registration(self.db, self.auth, user_data, self.captured_image)
            if app_no:
                tmsg.showinfo("Registration Successful", f"YOUR APPLICATION NO.:\n{app_no}\n\nPlease save this number\nfor future refrence.")
                # Registration success hone par home/login par bhej do
                self.controller.show_home() # Ya show_home() jo tumne rakha hai

        # Review window kholo
        open_review_window(self.db, user_data, self.captured_image, final_confirm)

class LoginUI(ctk.CTkFrame):
    def __init__(self, parent, controller, db, auth):
        super().__init__(parent, fg_color="white", corner_radius=25)
        self.controller = controller
        self.db = db
        self.auth = auth

        # --- BACK BUTTON (Professional Placement) ---
        self.back_btn = ctk.CTkButton(self, text="← Back", command=lambda: self.controller.show_home(),
                                      width=60, height=30, text_color="lightblue", hover_color="#1a3a5f")
        self.back_btn.place(x=10, y=10)

        ctk.CTkLabel(self, text="STUDENT LOGIN", font=("Segoe UI", 24, "bold"), text_color="#1a3a5f").pack(pady=40)

        self.app_entry = ctk.CTkEntry(self, placeholder_text="Application Number", width=300, height=40)
        self.app_entry.pack(pady=10)

        self.pass_entry = ctk.CTkEntry(self, placeholder_text="Password", width=300, height=40, show="*")
        self.pass_entry.pack(pady=10)

        self.login_btn = ctk.CTkButton(self, text="LOGIN", command=self.handle_login, width=300, height=45, fg_color="#1a3a5f")
        self.login_btn.pack(pady=30)

        # Register button link
        ctk.CTkButton(self, text="New Student? Register Now", command=lambda: controller.show_register(), 
                      fg_color="transparent", hover_color="#91959e", text_color="#1a3a5f").pack()

    def handle_login(self):
        app_no = self.app_entry.get().strip()
        pwd = self.pass_entry.get().strip()

        if not app_no or not pwd:
            tmsg.showwarning("Warning", "Don't leave fields empty, Boss!")
            return

        # YAHAN ASLI MAGIC HOGA (Manager call)
        success, user_data, is_new = manager.validate_dashboard_login(self.db, self.auth, app_no, pwd)

        if success:
            if is_new:
               tmsg.showinfo("Success", f"Welcome {user_data['name']}!\nRoll No: {user_data['roll_no']}")
            # AB YAHAN SE DASHBOARD KHULEGA
            self.controller.show_dashboard(user_data)
        else:
            tmsg.showerror("Error", "Invalid Application Number or Password!")