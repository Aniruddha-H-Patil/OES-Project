import pyrebase
import json
import secrets_config
import getpass  # Password hide karne ke liye

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
        print("3. Exit")
        
        choice = input("\nSelect Task (1/2/3): ")
        
        if choice == '1':
            update_available_tests(id_token)
        elif choice == '2':
            upload_question_paper(id_token)
        elif choice == '3':
            print("Chalo bye, mehnat kar!")
            break
        else:
            print("❌ Option galat hai, dhyan se dekh!")

if __name__ == "__main__":
    main_menu()