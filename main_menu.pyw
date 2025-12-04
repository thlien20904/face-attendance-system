import sys
import subprocess
import os
from utils import ensure_admin_account
import tkinter as tk
import tkinter.font as tkfont
import matplotlib.pyplot as plt

try:
    import customtkinter as ctk
except ImportError:
    raise ImportError("customtkinter is required. Install with: pip install customtkinter")

# --- Ensure necessary files exist ---
os.makedirs("embeddings", exist_ok=True)
ensure_admin_account()

# --- CustomTkinter theme ---
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("dark-blue")

# --- Main window ---
root = ctk.CTk()
root.title("FaceAttendance - Main Menu")
root.state("zoomed")
# Try to increase scaling/font sizes for high-DPI displays so text is readable
try:
    _SCALE = 1.4
    try:
        root.tk.call('tk', 'scaling', _SCALE)
    except Exception:
        pass
    for _name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont"):
        try:
            f = tkfont.nametofont(_name)
            f.configure(size=int(max(8, f.cget('size') * _SCALE)))
        except Exception:
            pass
except Exception:
    pass
root.rowconfigure(0, weight=1)
root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=2)

# --- Function to open a script without blocking ---
def open_and_close(script_name):
    # Hide main menu first to avoid destroying widgets too quickly
    root.withdraw()
    # Delay full destroy so customtkinter widgets have time to release images
    root.after(300, lambda: safe_destroy(script_name))


def safe_destroy(script_name):
    try:
        try:
            root.quit()
            root.update_idletasks()
        except Exception:
            pass
        root.destroy()
    except Exception:
        pass

    subprocess.Popen([sys.executable, script_name], cwd=os.getcwd())

# --- Left Branding Panel ---
LEFT_BG = "#1e293b"
left_frame = ctk.CTkFrame(root, corner_radius=0, fg_color=LEFT_BG)
left_frame.grid(row=0, column=0, sticky="nswe")
left_frame.grid_rowconfigure(0, weight=1)
left_frame.grid_columnconfigure(0, weight=1)

# Inner left frame for content
left_inner = ctk.CTkFrame(left_frame, fg_color="transparent")
left_inner.grid(row=0, column=0, sticky="nsew", padx=50, pady=50)
left_inner.grid_rowconfigure(0, weight=1)
left_inner.grid_rowconfigure(1, weight=1)
left_inner.grid_rowconfigure(2, weight=1)
left_inner.grid_rowconfigure(3, weight=1)

# Branding Text
ctk.CTkLabel(left_inner, text="FaceAttendance", font=("Helvetica", 48, "bold"),
             text_color="#F3F6FB", anchor="w").grid(row=0, column=0, sticky="w", pady=(0,10))
ctk.CTkLabel(left_inner, text="Fast • Secure • Reliable", font=("Helvetica", 22),
             text_color="#B8D0F2", anchor="w").grid(row=1, column=0, sticky="w", pady=(0,10))
ctk.CTkLabel(left_inner, text="Main Menu", font=("Helvetica", 28, "bold"),
             text_color="#F3F6FB", anchor="w").grid(row=2, column=0, sticky="w", pady=(0,20))
desc = ("Select your role or action:\n\n"
        "• Admin Login\n"
        "• Employee Check-in\n"
        "• Employee Check-out")
ctk.CTkLabel(left_inner, text=desc, font=("Arial", 16),
             text_color="#D7E6FB", wraplength=400, justify="left").grid(row=3, column=0, sticky="w")

# --- Right Panel ---
right_frame = ctk.CTkFrame(root, corner_radius=20, fg_color="#f0f4f8")
right_frame.grid(row=0, column=1, sticky="nswe", padx=50, pady=50)
right_frame.rowconfigure(0, weight=1)
right_frame.columnconfigure(0, weight=1)

# --- Action Card ---
card = ctk.CTkFrame(right_frame, corner_radius=20, fg_color="white", border_width=2, border_color="#cbd5e1")
card.grid(row=0, column=0, sticky="nsew", padx=40, pady=40)
card.columnconfigure(0, weight=1)

ctk.CTkLabel(card, text="Welcome!", font=("Helvetica", 28, "bold")).grid(row=0, column=0, sticky="w", padx=30, pady=(30,5))
ctk.CTkLabel(card, text="Select your role or action", font=("Arial", 14),
             text_color="#6b7280").grid(row=1, column=0, sticky="w", padx=30, pady=(0,20))

# --- Buttons with gradient-like colors ---
btn_cfg = {"height": 55, "corner_radius": 12, "font": ("Arial", 18, "bold")}

ctk.CTkButton(card, text="👨‍💼 Admin Login", fg_color="#6366f1", hover_color="#818cf8",
              text_color="white",
              command=lambda: open_and_close("main_login_employee.py"),
              **btn_cfg).grid(row=2, column=0, sticky="ew", padx=30, pady=15)

ctk.CTkButton(card, text="👷 Employee Check-in", fg_color="#10b981", hover_color="#34d399",
              text_color="white",
              command=lambda: open_and_close("main_checkin_employee.py"),
              **btn_cfg).grid(row=3, column=0, sticky="ew", padx=30, pady=15)

ctk.CTkButton(card, text="👷 Employee Check-out", fg_color="#8b5cf6", hover_color="#a78bfa",
              text_color="white",
              command=lambda: open_and_close("main_checkout_employee.py"),
              **btn_cfg).grid(row=4, column=0, sticky="ew", padx=30, pady=15)

# --- Footer ---
ctk.CTkLabel(root, text="© 2025 FaceAttendance System", font=("Arial", 12, "italic"),
             text_color="#A0A0A0").grid(row=1, column=1, sticky="e", padx=30, pady=10)

# --- Proper Close Handler ---
def on_close():
    try:
        try:
            plt.close("all")
        except Exception:
            pass
        root.quit()
    except Exception:
        pass
    try:
        try:
            root.quit()
            root.update_idletasks()
        except Exception:
            pass
        root.destroy()
    except Exception:
        pass

root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()
