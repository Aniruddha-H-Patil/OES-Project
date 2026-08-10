import pyrebase
import json
import secrets_config
import getpass  # Password hide karne ke liye
import auth_manager as manager
import os

# 1. Config initialize
config = secrets_config.FIREBASE_CONFIG
firebase = pyrebase.initialize_app(config)
db = firebase.database()
auth = firebase.auth()

def admin_login():
    """Admin credentials se login karke token return karega"""
    print("\n" + "="*30)
    print("   ADMIN SECURE ACCESS")
    print("="*30)
    email = input("📧 Admin Email: ").strip()
    password = getpass.getpass("🔑 Admin Password: ") # Type karte waqt password nahi dikhega
    
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        print("✅ Identity Verified! Token granted.")
        return user['idToken'] 
    except Exception as e:
        print(f"❌ Access Denied: Galat Email ya Password! ({e})")
        return None

def update_available_tests(token):
    """Dashboard ke 'papers' node ko update karega"""
    print("\n--- Confirmation ---")
    confirm = input("Kya tu sach mein Dashboard ke TEST CARDS update karna chahta hai? (y/n): ")
    if confirm.lower() != 'y':
        print("❌ Action Cancelled.")
        return

    try:
        with open("Available_Tests.json", "r", encoding="utf-8") as file:
            tests_data = json.load(file)
            # Yahan token pass karna compulsory hai rules bypass karne ke liye
            db.child("papers").update(tests_data, token)
            print("✔ SUCCESS: Available Test Cards updated on Cloud!")
    except FileNotFoundError:
        print("❌ ERROR: 'Available_Tests.json' nahi mili!")
    except Exception as e:
        print(f"❌ ERROR: {e}")

def upload_question_paper(token):
    """Specific Paper ID ke questions 'questions' node mein upload karega"""
    paper_id = input("\nKaunse Paper ID mein questions dalne hain? (e.g. P001): ").strip()
    if not paper_id:
        print("❌ Paper ID zaroori hai!")
        return

    confirm = input(f"Confirm upload for '{paper_id}'? (y/n): ")
    if confirm.lower() != 'y':
        print("❌ Action Cancelled.")
        return

    try:
        with open("Question.json", "r", encoding="utf-8") as file:
            q_data = json.load(file)
            # .set() with token
            db.child("questions").child(paper_id).set(q_data, token)
            print(f"✔ SUCCESS: Paper '{paper_id}' sync ho gaya!")
    except FileNotFoundError:
        print("❌ ERROR: 'Question.json' nahi mili!")
    except Exception as e:
        print(f"❌ ERROR: {e}")

def upload_exam_logo(token):
    """Kisi specific paper ke liye logo upload karega aur Firebase node update karega"""
    paper_id = input("\nKaunse Paper ID ke liye logo upload karna hai? (e.g. P001): ").strip().upper()
    if not paper_id:
        print("❌ Paper ID zaroori hai!")
        return

    # Check karo ki kya wo paper database mein sach mein exist karta hai
    paper_check = db.child("papers").child(paper_id).get(token).val()
    if not paper_check:
        print(f"⚠️ Warning: Paper '{paper_id}' abhi database ke 'papers' node mein nahi hai!")
        confirm_anyway = input("Kya tu fir bhi is ID ke liye logo insert karna chahta hai? (y/n): ")
        if confirm_anyway.lower() != 'y':
            return

    image_path = input("📂 Local Image File Path dalo: ").strip()
    # Quotes remove karne ke liye agar terminal par drag-and-drop kiya ho
    image_path = image_path.replace('"', '').replace("'", "")

    # File name extract karo path se (e.g., 'images/jee_logo.png' -> 'jee_logo')
    file_name = os.path.splitext(os.path.basename(image_path))[0]

    # === 🔥 Yahan tera auth_manager ka function call ho raha hai ===
    print(f"🔄 Uploading {image_path} via auth_manager...")
    direct_logo_url = manager.upload_to_storage(image_path, file_name)
    print("uploaded succesfully to imgbb cloud")
    
    if not direct_logo_url:
        print("❌ Logo upload cancel ho gaya kyunki ImgBB upload fail hua.")
        return

    # Direct Firebase node update (papers -> PXYZ -> exam_logo)
    try:
        db.child("papers").child(paper_id).update({"exam_logo": direct_logo_url}, token)
        print(f"\n🎉 SUCCESS: Paper '{paper_id}' ka exam_logo update ho gaya cloud par!")
        print(f"🔗 URL: {direct_logo_url}")
    except Exception as e:
        print(f"❌ Database update fail ho gaya: {e}")

def main_menu():
    # Pehle login, phir kaam
    id_token = admin_login()
    
    if not id_token:
        print("Admin access ke bina script band ho rahi hai.")
        return

    while True:
        print("\n" + "="*30)
        print("   BOSS OES CLOUD UPDATER")
        print("="*30)
        print("1. Update Available Test Cards (papers node)")
        print("2. Upload/Update Question Paper (questions node)")
        print("3. Upload exam logo to imgbb")
        print("4. Exit")
        
        choice = input("\nSelect Task (1/2/3/4): ")
        
        if choice == '1':
            update_available_tests(id_token)
        elif choice == '2':
            upload_question_paper(id_token)
        elif choice == '3':
            upload_exam_logo(id_token)
        elif choice == '4':
            print("Chalo bye, mehnat kar!")
            break
        else:
            print("❌ Option galat hai, dhyan se dekh!")

if __name__ == "__main__":
    main_menu()