import customtkinter as ctk

# --- THEME COLORS (Ek jagah change karo, har jagah badal jayega) ---
THEME = {
    "PRIMARY": "#1f538d",
    "WHITE": "#ffffff",
    "GREEN": "#2d8c3c",  # Answered
    "RED": "#e74c3c",    # Not Answered
    "PURPLE": "#8e44ad", # Marked for Review
    "GRAY": "#7f8c8d",   # Border
    "TEXT_DARK": "black",
    "TEXT_LIGHT": "white"
}

# --- REUSABLE COMPONENTS ---

class SubjectTab(ctk.CTkButton):
    def __init__(self, master, text, command, is_active=False, **kwargs):
        color = THEME["WHITE"] if is_active else THEME["PRIMARY"]
        text_col = THEME["TEXT_DARK"] if is_active else THEME["TEXT_LIGHT"]
        
        super().__init__(master, text=text, command=command, 
                         fg_color=color, text_color=text_col,
                         width=140, height=40, corner_radius=0, 
                         font=("Arial", 13, "bold"), **kwargs)

class QuestionPaletteBtn(ctk.CTkButton):
    def __init__(self, master, num, status, command, **kwargs):
        # Status logic
        bg_color = {
            "not_visited": THEME["WHITE"],
            "answered": THEME["GREEN"],
            "not_answered": THEME["RED"],
            "marked": THEME["PURPLE"],
            "answered_marked": THEME["PURPLE"],
        }.get(status, THEME["WHITE"])

        txt_col = THEME["TEXT_DARK"] if status == "not_visited" else THEME["TEXT_LIGHT"]

        super().__init__(master, text=str(num), width=45, height=45,
                         fg_color=bg_color, text_color=txt_col,
                         border_width=1, border_color=THEME["GRAY"],
                         corner_radius=5, command=command, **kwargs)

class ActionButton(ctk.CTkButton):
    def __init__(self, master, text, color, command, **kwargs):
        super().__init__(master, text=text, fg_color=color, 
                         command=command, font=("Arial", 13, "bold"), 
                         height=45, width=150, **kwargs)