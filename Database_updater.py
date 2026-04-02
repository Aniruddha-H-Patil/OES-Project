import pyrebase
import json
import secrets_config

# 1. Config initialize
config = secrets_config.FIREBASE_CONFIG
firebase = pyrebase.initialize_app(config)
db = firebase.database()

def update_available_tests():
    """Dashboard ke test cards update karne ke liye"""
    print("\n--- Confirmation ---")
    confirm = input("Kya tu sach mein Dashboard ke TEST CARDS update karna chahta hai? (y/n): ")
    if confirm.lower() != 'y':
        print("❌ Action Cancelled.")
        return

    try:
        # Iske liye ek alag choti JSON file bana lena 'Available_Tests.json'
        with open("Available_Tests.json", "r", encoding="utf-8") as file:
            tests_data = json.load(file)
            # .update() use kiya hai taaki purane tests na udein
            db.child("papers").update(tests_data)
            print("✔ SUCCESS: Available Test Cards updated on Cloud!")
    except FileNotFoundError:
        print("❌ ERROR: 'Available_Tests.json' nahi mili!")
    except Exception as e:
        print(f"❌ ERROR: {e}")

def upload_question_paper():
    """Specific Paper ID ke questions upload karne ke liye"""
    paper_id = input("\nKaunse Paper ID mein questions dalne hain? (e.g. JEE_MAIN_01): ").strip()
    if not paper_id:
        print("❌ Paper ID bina kaam nahi chalega bhai!")
        return

    confirm = input(f"Kya tu sach mein '{paper_id}' ka QUESTION DATA badalna chahta hai? (y/n): ")
    if confirm.lower() != 'y':
        print("❌ Action Cancelled.")
        return

    try:
        with open("Question.json", "r", encoding="utf-8") as file:
            q_data = json.load(file)
            # .set() yahan chalega kyunki ek paper ka data refresh karna ho sakta hai
            db.child("questions").child(paper_id).set(q_data)
            print(f"✔ SUCCESS: Paper '{paper_id}' ke questions sync ho gaye!")
    except FileNotFoundError:
        print("❌ ERROR: 'Question.json' nahi mili!")
    except Exception as e:
        print(f"❌ ERROR: {e}")

def main_menu():
    while True:
        print("\n" + "="*30)
        print("   BOSS OES CLOUD UPDATER")
        print("="*30)
        print("1. Update Available Test Cards (Dashboard)")
        print("2. Upload/Update Question Paper (Specific Exam)")
        print("3. Exit")
        
        choice = input("\nSelect Task (1/2/3): ")
        
        if choice == '1':
            update_available_tests()
        elif choice == '2':
            upload_question_paper()
        elif choice == '3':
            print("Chalo bye, mehnat kar!")
            break
        else:
            print("❌ Galat button dabaya hai, dhyan se dekh!")

if __name__ == "__main__":
    main_menu()