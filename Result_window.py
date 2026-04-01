import customtkinter as ctk
import Result  # Result.py ko import kiya

def show_final_from_stats(stats):
    # 'stats' wahi dictionary hai jo tune Firebase mein save ki thi
    res_win = ctk.CTkToplevel() 
    res_win.title("Your Performance")
    res_win.geometry("450x500")
    res_win.attributes("-topmost", True) # Dashboard ke upar hi rahegi
    
    total = stats.get("Total", {"score": 0, "correct": 0, "wrong": 0})

    ctk.CTkLabel(res_win, text="TEST REPORT", font=("Segoe UI", 24, "bold")).pack(pady=20)
    
    # Simple Stats Display
    box = ctk.CTkFrame(res_win, fg_color="#f8f9fa", corner_radius=10)
    box.pack(pady=10, padx=30, fill="both", expand=True)

    ctk.CTkLabel(box, text=f"Total Score: {total['score']}", font=("Arial", 30, "bold"), text_color="#1a73e8").pack(pady=20)
    ctk.CTkLabel(box, text=f"✅ Correct: {total['correct']}", font=("Arial", 16)).pack(pady=5)
    ctk.CTkLabel(box, text=f"❌ Wrong: {total['wrong']}", font=("Arial", 16)).pack(pady=5)

    ctk.CTkButton(res_win, text="CLOSE", command=res_win.destroy).pack(pady=20)

    res_win.mainloop()