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

current_id_token = None

def get_tracking_info():
    try:
        ip = requests.get('https://api.ipify.org', timeout=3).text
    except:
        ip = "Unknown/Offline"
    
    device = socket.gethostname()
    time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # --- MAC Address nikalne ka logic ---
    # Isse "00:1A:2B:3C:4D:5E" format mein address milega
    mac_num = hex(uuid.getnode()).replace('0x', '').upper()
    mac = ':'.join(mac_num[i:i+2] for i in range(0, len(mac_num), 2))
    # ------------------------------------

    return ip, device, time, mac


# --- 2. ID GENERATOR (Pure Integers) ---
def generate_app_no(db):
    app_no = int(f"2026{random.randint(100000, 999999)}")
    check = db.child("users").child(str(app_no)).get().val()
    if check: return generate_app_no(db)
    return app_no

def assign_roll_no(db, app_no):
    """Ye function tab chalega jab Dashboard pe pehli baar login hoga"""
    new_roll = int(f"99{random.randint(100000, 999999)}")
    
    # Update in Database
    db.child("users").child(app_no).update({"roll_no": str(new_roll)})
    return new_roll

# --- 1. IMGBB STORAGE SETUP ---
def upload_to_storage(file_path, file_name):
    """BOSS! Ye code photo ImgBB par bhejega aur permanent link dega."""
    # APNI API KEY YAHAN DALO
    API_KEY = secrets_config.IMGBB_API_KEY
    
    try:
        if not os.path.exists(file_path):
            print(f"Error: File {file_path} nahi mili!")
            return None

        with open(file_path, "rb") as file:
            url = "https://api.imgbb.com/1/upload"
            payload = {
                "key": API_KEY,
                "image": base64.b64encode(file.read()),
                "name": file_name
                # Expiration parameter nahi hai, isliye Manual deletion hoga
            }
            
            response = requests.post(url, payload)
            result = response.json()
            
            if result['success']:
                photo_url = result['data']['url']
                print(f"Success: Photo uploaded to ImgBB -> {photo_url}")
                return photo_url
            else:
                print(f"ImgBB Error: {result['error']['message']}")
                return None
                
    except Exception as e:
        print(f"Critical Error in Upload: {e}")
        return None

# --- 3. REGISTRATION PROCESS ---
def process_registration(db, auth, user_data, photo_frame):
    """BOSS! Ye code tabhi upload karega jab sab kuch perfect hoga."""
    temp_path = None    
    try:
        # 1. Pehle IDs generate karo
        app_no = generate_app_no(db)

        # ---- SHADOW EMAIL LOGIC ----
        # student apna app_no hi use karega, par piche yeh email banega
        shadow_email = f"{app_no}@exam.com"
        password = user_data['password']

        # 2. Firebase Auth mein account banao (Sabse pehle)
        # Isse humein 'idToken' milega jo "Entry Pass" ka kaam karega
        auth_user = auth.create_user_with_email_and_password(shadow_email, password)
        user_token = auth_user['idToken'] # <--- YE HAI WOH CHABI (TOKEN)!
        
        print(f"✅ Auth Account Created: {app_no}")
        
        # 2. Local save karo (sirf temporary)
        temp_path = f"temp_{app_no}.jpg"
        cv2.imwrite(temp_path, photo_frame)
        
        # 4. AB IMAGE UPLOAD KARO (Internet check)
        photo_link = upload_to_storage(temp_path, f"STUDENT_{app_no}")
        
        if not photo_link:
            raise Exception("Upload Error", "Photo upload Failed.\nPlease check Internet connection!")
        
        # 5. SAB KUCH SAHI HAI? TOH AB DATABASE MEIN ENTRY KARO
        student_profile = {
            "app_no": str(app_no),
            "roll_no": "Pending",
            "name": user_data['name'],
            "mobile": user_data['mobile'],
            "personal_email": user_data['email'],
            "gender": user_data['gender'],
            "category": user_data['category'],
            "dob": f"{user_data['day']}-{user_data['month']}-{user_data['year']}",
            "exam_password": f"{user_data['day']}{user_data['month']}{user_data['year']}",
            "password": user_data['password'],
            "photo_link": photo_link,
            "exam_status": "Pending",
            "score": 0
        }

        # FINAL STEP: Database Entry
        db.child("users").child(app_no).set(student_profile, user_token)

        # Cleanup
        if os.path.exists(temp_path): os.remove(temp_path)
        return app_no

    except Exception as e:
        # AGAR KAHIN BHI ERROR AAYA:
        print(f"ROLLBACK: Registration failed due to: {e}")
        
        # Cleanup local files agar registration fail hui
        if temp_path and os.path.exists(temp_path): os.remove(temp_path)
        
        tmsg.showerror("Registration Error", f"Registration Failed! No data was uploaded.\nPlease check your Internet Connection!\nError: {e}")
        return None, None
    
def validate_dashboard_login(db, auth, app_no, password):
    global current_id_token
    try:
        # STEP 1: Shadow Email reconstruct karo (Student ko pata bhi nahi chalega)
        shadow_email = f"{app_no}@exam.com"

        # STEP 2: Firebase Auth login (Auth Token milega)
        auth_user = auth.sign_in_with_email_and_password(shadow_email, password)
        current_id_token = auth_user['idToken'] 
        print(f"✅ Auth Success! Token generated.")

        # STEP 3: Database se data uthao (Token use karke)
        user_node = db.child("users").child(app_no).get(current_id_token).val()
        
        if not user_node:
            return False, None, False

        # STEP 4: Tracking & Roll No Logic (Update with Token)
        is_new = False 
        update_data = {}

        if user_node.get('roll_no') == "Pending":
            new_roll = f"2{random.randint(100000, 999999)}"
            update_data["roll_no"] = new_roll
            user_node['roll_no'] = new_roll
            is_new = True 

        ip, device, time, mac = get_tracking_info()
        update_data.update({
            "last_login_ip": ip,
            "last_login_device": device,
            "last_login_time": time,
            "MAC Address": mac
        })
        
        # Database update with security token
        db.child("users").child(app_no).update(update_data, current_id_token)
        user_node.update(update_data)

        # Photo Download
        photo_url = user_node.get('photo_link') 
        if photo_url and photo_url != "Pending":
            download_temp_image(photo_url)

        save_session(user_node)
        return True, user_node, is_new 
        
    except Exception as e:
        print(f"❌ Login Manager Error: {e}")
        return False, None, False

def get_token():
    global current_id_token
    return current_id_token
    
def download_temp_image(url):    
    # 1. Folder check karo
    folder = "temp_assets"
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"DEBUG: Folder '{folder}' created.")

    # 2. Exact Path define karo
    temp_path = os.path.join(folder, "current_user.jpg")
    print(f"DEBUG: Trying to save at: {os.path.abspath(temp_path)}")

    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            with open(temp_path, "wb") as f:
                f.write(r.content)
            print(f"✅ SUCCESS: File downloaded and saved!")
            return True
        else:
            print(f"❌ FAILED: URL returned status {r.status_code}")
    except Exception as e:
        print(f"❌ ERROR in download_temp_image: {e}")
    return False

    
def validate_exam_login(db, roll_no, dob_input):
    try:
        users = db.child("users").get().val()
        for app_id, data in users.items():
            if str(data.get('roll_no')) == str(roll_no) and str(data.get('exam_password')) == str(dob_input):
                return True, data
        return False, None
    except:
        return False, None
    
# --- 5. PAWWORD RESET LOGIC ---
# TODO: Implement

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
    
SESSION_FILE = "user_session.json"

def save_session(user_data): # Pehle yahan sirf app_no tha
    """Login success hone par poora tracking data save karo"""
    try:
        with open(SESSION_FILE, "w") as f:
            # Hum poora user_data dabba hi save kar rahe hain
            json.dump(user_data, f, indent=4) 
        print("DEBUG: Full Session with Tracking saved locally.")
    except Exception as e:
        print(f"DEBUG: Session save error: {e}")

def get_session():
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r") as f:
                data = json.load(f)
                # Yeh abhi bhi sirf app_no return karega taaki purana code na phate
                return data.get("app_no") 
        except:
            return None
    return None

def clear_session():
    import os, shutil
    file_name = "user_session.json"
    temp_folder = "temp_assets"
    
    try:
        # 1. Session file udao
        if os.path.exists(file_name):
            os.remove(file_name)
            print("✅ BOSS: Session file deleted.")
        
        # 2. Poora folder udao (Andar ki files ke saath)
        if os.path.exists(temp_folder):
            # shutil.rmtree folder ko jadd se mita deta hai
            shutil.rmtree(temp_folder)
            print("✅ BOSS: Temp folder and all images cleared.")
        else:
            print("ℹ️ BOSS: Folder pehle se hi nahi hai.")
            
        return True
    except Exception as e:
        # Agar error aaye "Access Denied", iska matlab image abhi bhi UI pe open hai
        print(f"❌ ERROR: Cleanup fail: {e}")
        return False
