import customtkinter as ctk
import os
import cv2
import random
import requests
from io import BytesIO
from tkinter import messagebox as tmsg
import base64
from tkinter import Toplevel, Label, Button, Frame
from PIL import Image, ImageTk
import json
import socket
import datetime
import uuid
import secrets_config
import time

# --- GLOBAL CONFIG ---
current_id_token = None  # Yeh main token hai jo poore app mein chalega
SESSION_FILE = "user_session.json"

# --- 1. TRACKING & SYSTEM INFO ---
def get_tracking_info():
    try:
        # Timeout 3s rakha hai taaki agar internet slow ho toh app hang na ho
        ip = requests.get('https://api.ipify.org', timeout=3).text
    except:
        ip = "Unknown/Offline"
    
    device = socket.gethostname()
    curr_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Unique MAC Address logic
    mac_num = hex(uuid.getnode()).replace('0x', '').upper()
    mac = ':'.join(mac_num[i:i+2] for i in range(0, len(mac_num), 2))

    return ip, device, curr_time, mac

# --- 2. ID GENERATORS (UNIQUE) ---
def generate_app_no(db):
    """UNIQUE Application Number starting with 2026"""
    while True:
        app_no = str(f"2026{random.randint(100000, 999999)}")
        try:
            # FIX: Try-except add kiya taaki unauthorized error se app crash na ho
            check = db.child("users").child(app_no).get().val()
            if not check:
                return app_no
        except:
            # Agar permission error aaye, toh assume karo ki ID available hai ya loop continue karo
            return app_no

def assign_roll_no(db, token=None):
    """UNIQUE 8-digit Roll Number generate karta hai (With Token support)"""
    attempts = 0
    while attempts < 20:
        new_roll = str(f"99{random.randint(100000, 999999)}")
        try:
            # Agar token hai toh login user ki tarah check karega (Rules bypass honge)
            # Agar token nahi hai (pehle ki tarah), toh guest ki tarah check karega
            query = db.child("users").order_by_child("roll_no").equal_to(new_roll)
            check = query.get(token).val() if token else query.get().val()
            
            if not check:
                return new_roll
            print(f"⚠️ Collision: {new_roll} exists. Retrying...")
        except Exception as e:
            # Agar fir bhi rules block karein, toh fallback 
            print(f"⚠️ Roll Check Warning: {e}")
            return new_roll
        attempts += 1
    return str(f"99{random.randint(111111, 999999)}")

# --- 3. STORAGE (IMGBB) ---
def upload_to_storage(file_path, file_name):
    API_KEY = secrets_config.IMGBB_API_KEY
    try:
        if not os.path.exists(file_path):
            return None

        with open(file_path, "rb") as file:
            url = "https://api.imgbb.com/1/upload"
            payload = {
                "key": API_KEY,
                "image": base64.b64encode(file.read()),
                "name": file_name
            }
            response = requests.post(url, payload)
            result = response.json()
            
            if result.get('success'):
                return result['data']['url']
            return None
    except Exception as e:
        print(f"Critical Error in Upload: {e}")
        return None

# --- 4. AUTH & REGISTRATION ---
def process_registration(db, auth, user_data, photo_frame):
    temp_path = None    
    try:
        # 1. App No generate karo (Isme read ki zaroorat nahi kyunki ye key hai)
        app_no = generate_app_no(db)
        
        shadow_email = f"{app_no}@exam.com"
        password = user_data['password']

        # 2. Pehle Auth Account banao
        auth.create_user_with_email_and_password(shadow_email, password)
        
        # 3. Turant Login karke TOKEN lo
        login_session = auth.sign_in_with_email_and_password(shadow_email, password)
        user_token = login_session['idToken'] 

        # 4. AB ROLL NUMBER CHECK KARO (Token ke saath)
        # Ab Firebase mana nahi karega kyunki banda logged in hai
        new_roll = assign_roll_no(db, token=user_token)
        
        # 5. Tracking info fetch karo
        ip, device, _, current_mac = get_tracking_info()
        
        # 6. Photo Processing & Upload
        temp_path = f"temp_reg_{app_no}.jpg"
        cv2.imwrite(temp_path, photo_frame)
        photo_link = upload_to_storage(temp_path, f"STUDENT_{app_no}")
        
        if not photo_link:
            raise Exception("Photo upload Failed! Check Internet.")
        
        # 7. Profile Data Object
        student_profile = {
            "app_no": app_no,
            "roll_no": new_roll,
            "name": user_data['name'].strip().upper(),
            "mobile": user_data['mobile'],
            "personal_email": user_data['email'],
            "gender": user_data['gender'],
            "category": user_data['category'],
            "dob": f"{user_data['day']}-{user_data['month']}-{user_data['year']}",
            "exam_password": f"{user_data['day']}{user_data['month']}{user_data['year']}",
            "password": password,
            "photo_link": photo_link,
            "exam_status": "Pending",
            "score": 0,
            "is_active": False,
            "last_seen": 0,
            "MAC Address": current_mac,
            "reg_ip": ip,
            "reg_device": device
        }

        # 8. Database mein save karo (Token ke saath)
        db.child("users").child(app_no).set(student_profile, user_token)
        
        print(f"✅ Full Registration Success! App No: {app_no}, Roll No: {new_roll}")
        return app_no 

    except Exception as e:
        print(f"❌ REGISTRATION FAILED: {e}")
        tmsg.showerror("Error", f"Registration Failed: {e}")
        return None
        
    finally:
        if temp_path and os.path.exists(temp_path): 
            try: os.remove(temp_path)
            except: pass

def validate_dashboard_login(db, auth, app_no, password):
    global current_id_token
    try:
        shadow_email = f"{app_no}@exam.com"
        auth_user = auth.sign_in_with_email_and_password(shadow_email, password)
        current_id_token = auth_user['idToken']
        refresh_token = auth_user['refreshToken']

        # Token pass karna zaroori hai
        user_node = db.child("users").child(app_no).get(current_id_token).val()
        
        if not user_node:
            return False, "User data missing!", False

        ip, device, _, current_mac = get_tracking_info()
        current_time = time.time()
        
        last_seen = user_node.get("last_seen", 0)
        is_active = user_node.get("is_active", False)
        saved_mac = user_node.get("MAC Address", "Pending")

        # Session Lock Logic
        if is_active and (current_time - last_seen) < 120:
            if saved_mac != "Pending" and saved_mac != current_mac:
                return False, "ALREADY_LOGGED_IN", False

        update_data = {
            "last_login_ip": ip,
            "last_login_device": device,
            "MAC Address": current_mac,
            "is_active": True,
            "last_seen": current_time
        }

        db.child("users").child(app_no).update(update_data, current_id_token)
        user_node.update(update_data)
        user_node['idToken'] = current_id_token # Sync local data
        user_node['refreshToken'] = refresh_token

        if user_node.get('photo_link'):
            download_temp_image(user_node['photo_link'])

        save_session(user_node)
        return True, user_node, False 
        
    except Exception as e:
        err = str(e)
        if "INVALID_PASSWORD" in err:
            return False, "Galat password hai!", False
        return False, f"Login Error: {err}", False

# --- 5. SESSION MANAGEMENT ---
def refresh_session_on_startup(auth):
    """Startup par check karega aur token refresh karega taaki 1 ghante wali limit reset ho jaye"""
    session_data = get_session_data()
    if not session_data:
        return None

    try:
        # Firebase refresh token use karke naya idToken mangwao
        # 'refreshToken' login ke waqt milta hai
        refreshed = auth.refresh(session_data['refreshToken'])
        
        # Naye tokens update karo
        session_data['idToken'] = refreshed['idToken']
        session_data['refreshToken'] = refreshed['refreshToken']
        
        # Global variable update karo
        global current_id_token
        current_id_token = refreshed['idToken']
        
        # Wapas save karo file mein
        save_session(session_data)
        print("🔄 Session Refreshed Successfully on Startup!")
        return session_data
    except Exception as e:
        print(f"⚠️ Session Refresh Failed (Login expired): {e}")
        clear_session() # Agar refresh fail hua toh purana session uda do
        return None

def save_session(user_data):
    try:
        with open(SESSION_FILE, "w") as f:
            json.dump(user_data, f, indent=4) 
        print("✅ Session saved locally.")
    except Exception as e:
        print(f"❌ Session save error: {e}")

def get_session_data():
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r") as f:
                return json.load(f)
        except:
            return None
    return None

def get_token():
    global current_id_token
    if current_id_token:
        return current_id_token
    data = get_session_data()
    return data.get("idToken") if data else None

def get_session():
    """Backwards compatibility: Returns only app_no"""
    data = get_session_data()
    return data.get("app_no") if data else None

def download_temp_image(url):    
    folder = "temp_assets"
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    temp_path = os.path.join(folder, "current_user.jpg")
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            with open(temp_path, "wb") as f:
                f.write(r.content)
            print(f"✅ Image Downloaded")
            return True
    except Exception as e:
        print(f"❌ Download Error: {e}")
    return False

def validate_exam_login(db, roll_no, dob_input):
    try:
        # Important: Token pass karo agar rules strict hain
        token = get_token()
        user_query = db.child("users").order_by_child("roll_no").equal_to(str(roll_no)).get(token)
        user_dict = user_query.val()

        if not user_dict: return False, None

        for app_id, data in user_dict.items():
            if str(data.get('exam_password')) == str(dob_input):
                return True, data
        return False, None
    except Exception as e:
        print(f"❌ Exam Auth Error: {e}")
        return False, None

def clear_session():
    import os, shutil, gc
    temp_folder = "temp_assets"
    
    try:
        # 1. Session file delete karo
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
            print("✅ BOSS: Session file deleted.")
        
        # 2. Memory release karo taaki files "Access Denied" na dein
        gc.collect() 
        
        # 3. Poora folder udao
        if os.path.exists(temp_folder):
            # Thoda wait (0.1s) taaki OS file handles release kar de
            time.sleep(0.1) 
            shutil.rmtree(temp_folder)
            print("✅ BOSS: Temp assets cleared.")
        else:
            print("ℹ️ BOSS: No temp folder found.")
            
        return True
    except Exception as e:
        # Agar fir bhi fail ho, toh users ko bata do manual cleanup ya restart chahiye
        print(f"❌ Cleanup Error: {e}")
        return False
    
# Password Reset
# TODO: Implements
    
# --- 5. REVIEW WINDOW (UI Feature) ---
def open_review_window(db, user_data, photo_frame, on_confirm_callback):
    review_win = ctk.CTkToplevel()
    review_win.title("REVIEW WINDOW")
    review_win.iconbitmap("BOSS-LOGO.ico")
    
    # --- 1. FIXED SIZE & NON-RESIZABLE ---
    window_width = 800
    window_height = 600
    review_win.geometry(f"{window_width}x{window_height}")
    review_win.resizable(False, False) # User resize nahi kar payega
    review_win.attributes("-topmost", True)
    review_win.grab_set()
    
    # Header Section (Blue Strip)
    header = ctk.CTkFrame(review_win, fg_color="#1a3a5f", height=50, corner_radius=0)
    header.pack(fill="x", side="top")
    ctk.CTkLabel(header, text="CANDIDATE DATA VERIFICATION", 
                 font=("Segoe UI", 20, "bold"), text_color="white").pack(pady=12)

    # Main Body Container
    body = ctk.CTkFrame(review_win, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=25, pady=15)

    # --- LEFT SECTION: Data Grid ---
    left_panel = ctk.CTkFrame(body, fg_color=["#f8fafc", "#1e293b"], corner_radius=12, border_width=1)
    left_panel.pack(side="left", fill="both", expand=True, padx=(0, 15))

    info_map = [
        ("CANDIDATE NAME", user_data['name'].upper()),
        ("MOBILE / PHONE", user_data['mobile']),
        ("EMAIL ADDRESS", user_data['email']),
        ("DATE OF BIRTH", f"{user_data['day']}-{user_data['month']}-{user_data['year']}"),
        ("GENDER", user_data['gender']),
        ("CATEGORY", user_data['category'])
    ]

    for i, (label, val) in enumerate(info_map):
        # Label
        ctk.CTkLabel(left_panel, text=label, font=("Segoe UI", 15, "bold"), 
                     text_color="#64748b").grid(row=i*2, column=0, sticky="w", padx=20, pady=(10, 0))
        # Value (Bold but No semibold)
        ctk.CTkLabel(left_panel, text=val, font=("Segoe UI", 20, "bold"), 
                     text_color=["#1e293b", "#f1f5f9"]).grid(row=i*2+1, column=0, sticky="w", padx=20, pady=(0, 5))

    # --- RIGHT SECTION: Photo Card ---
    right_panel = ctk.CTkFrame(body, width=300, fg_color="transparent")
    right_panel.pack(side="right", fill="y")

    # Photo Container with border
    img_border = ctk.CTkFrame(right_panel, fg_color=["#e2e8f0", "#334155"], corner_radius=8, border_width=2)
    img_border.pack(pady=(5, 10))

    ctk.CTkLabel(right_panel, text="LIVE CAPTURE", font=("Segoe UI", 15, "bold"), text_color="gray").pack()
    rgb_image = cv2.cvtColor(photo_frame, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb_image)
    ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(160, 190))
    
    ctk.CTkLabel(img_border, image=ctk_img, text="").pack()

    # --- BOTTOM SECTION: Buttons ---
    footer = ctk.CTkFrame(review_win, fg_color="transparent")
    footer.pack(fill="x", side="bottom", pady=20, padx=25)

    def on_confirm():
        review_win.destroy()
        on_confirm_callback()

    # Buttons Placement (Symmetry)
    ctk.CTkButton(footer, text="BACK TO EDIT", fg_color="#94a3b8", hover_color="#64748b",
                 text_color="white", width=150, height=38, font=("Segoe UI", 12, "bold"),
                 command=review_win.destroy).pack(side="left")

    ctk.CTkButton(footer, text="CONFIRM & FINAL SUBMIT", fg_color="#059669", hover_color="#047857",
                 text_color="white", width=250, height=38, font=("Segoe UI", 12, "bold"),
                 command=on_confirm).pack(side="right")
