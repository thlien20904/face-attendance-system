import sys
import subprocess
import os
import matplotlib.pyplot as plt
from utils import verify_admin, ensure_admin_account

try:
    import customtkinter as ctk
except ImportError:
    raise ImportError("customtkinter is required. Install with: pip install customtkinter")

# --- Ensure admin account exists ---
ensure_admin_account()

# --- CustomTkinter theme ---
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("dark-blue")

# --- Main window ---
root = ctk.CTk()
root.title("Admin Login - FaceAttendance")
root.state('zoomed')  # Fullscreen
root.rowconfigure(0, weight=1)
root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=2)

# --- Left branding panel ---
LEFT_BG_GRADIENT = "#1e293b"
left_frame = ctk.CTkFrame(root, corner_radius=0, fg_color=LEFT_BG_GRADIENT)
left_frame.grid(row=0, column=0, sticky="nswe", padx=0, pady=0)
left_frame.grid_rowconfigure(0, weight=1)
left_frame.grid_columnconfigure(0, weight=1)

left_inner = ctk.CTkFrame(left_frame, fg_color="transparent")
left_inner.grid(row=0, column=0, sticky="nsew", padx=20)
left_inner.grid_rowconfigure(0, weight=1)
left_inner.grid_rowconfigure(1, weight=1)
left_inner.grid_rowconfigure(2, weight=1)
left_inner.grid_rowconfigure(3, weight=1)

# Branding text
ctk.CTkLabel(left_inner, text="FaceAttendance", font=("Helvetica", 42, "bold"),
             text_color="#F3F6FB").grid(row=0, column=0, pady=(40,10), sticky="n")
ctk.CTkLabel(left_inner, text="Fast • Secure • Reliable", font=("Helvetica", 20, "italic"),
             text_color="#B8D0F2").grid(row=1, column=0, pady=(0,10), sticky="n")
ctk.CTkLabel(left_inner, text="Admin Login Portal", font=("Helvetica", 28, "bold"),
             text_color="#F3F6FB").grid(row=2, column=0, pady=(0,20), sticky="n")

# --- Right login panel ---
right_frame = ctk.CTkFrame(root, corner_radius=12, fg_color="#f0f4f8")
right_frame.grid(row=0, column=1, sticky="nswe", padx=50, pady=50)
right_frame.rowconfigure(0, weight=1)
right_frame.columnconfigure(0, weight=1)

# Login card
login_card = ctk.CTkFrame(right_frame, corner_radius=20, fg_color="white", border_width=2, border_color="#cbd5e1")
login_card.grid(row=0, column=0, sticky="nsew", padx=40, pady=40)
login_card.columnconfigure(0, weight=1)

# --- Back button ---
def go_back():
    root.withdraw()
    root.after(300, lambda: safe_destroy("main_menu.pyw"))

back_btn = ctk.CTkButton(login_card, text="← Back", command=go_back,
                         height=35, width=100, fg_color="#e5e7eb",
                         hover_color="#d1d5db", text_color="#111827",
                         font=("Arial", 14, "bold"))
back_btn.grid(row=0, column=0, sticky="w", padx=20, pady=(15,5))

# Title
ctk.CTkLabel(login_card, text="Welcome Back!", font=("Helvetica", 28, "bold")).grid(row=1, column=0, sticky="w", padx=30, pady=(10,5))
ctk.CTkLabel(login_card, text="Sign in to your admin account", font=("Arial", 14),
             text_color="#6b7280").grid(row=2, column=0, sticky="w", padx=30, pady=(0,20))

# --- Input fields ---
username_var = ctk.StringVar()
password_var = ctk.StringVar()

def create_input(frame, emoji, placeholder, variable, show=None):
    container = ctk.CTkFrame(frame, fg_color="transparent")
    container.grid(sticky="ew", padx=30, pady=10)
    container.columnconfigure(1, weight=1)
    ctk.CTkLabel(container, text=emoji, font=("Arial", 18)).grid(row=0, column=0, padx=(0,10))
    entry = ctk.CTkEntry(container, placeholder_text=placeholder, height=45, textvariable=variable, show=show, corner_radius=12)
    entry.grid(row=0, column=1, sticky="ew")
    return entry

username_entry = create_input(login_card, "✉", "Username", username_var)
password_entry = create_input(login_card, "🔒", "Password", password_var, show="*")

# Status
status_label = ctk.CTkLabel(login_card, text="", font=("Arial", 11), text_color="#ef4444")
status_label.grid(row=5, column=0, sticky="w", padx=30, pady=5)

# --- Login function ---
def on_login():
    user = username_var.get().strip()
    pwd = password_var.get().strip()
    if not user or not pwd:
        status_label.configure(text="Please enter username and password")
        return
    if verify_admin(user, pwd):
        status_label.configure(text="Login successful", text_color="#10b981")
        root.withdraw()
        root.after(300, lambda: safe_destroy("admin_panel.py"))
    else:
        status_label.configure(text="Invalid credentials. Try again.", text_color="#ef4444")

# Gradient-like Login button
login_btn = ctk.CTkButton(login_card, text="Login", command=on_login,
                          height=50, fg_color="#6366f1", hover_color="#818cf8",
                          text_color="white", font=("Arial", 16, "bold"))
login_btn.grid(row=6, column=0, sticky="ew", padx=30, pady=(20,30))

root.bind('<Return>', lambda e: on_login())

# scaling/font tweaks for high-DPI
try:
    import tkinter as _tk
    import tkinter.font as _tkfont
    _SCALE = 1.35
    try:
        root.tk.call('tk', 'scaling', _SCALE)
    except Exception:
        pass
    for _name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont"):
        try:
            f = _tkfont.nametofont(_name)
            f.configure(size=int(max(8, f.cget('size') * _SCALE)))
        except Exception:
            pass
except Exception:
    pass


def safe_destroy(script_name=None):
    try:
        root.destroy()
    except Exception:
        pass

    if script_name:
        try:
            subprocess.Popen([sys.executable, script_name], cwd=os.getcwd())
        except Exception:
            pass


def on_close():
    try:
        plt.close("all")
    except Exception:
        pass
    try:
        root.quit()
    except Exception:
        pass
    try:
        root.destroy()
    except Exception:
        pass


root.protocol("WM_DELETE_WINDOW", on_close)

# --- Footer ---
ctk.CTkLabel(root, text="© 2025 FaceAttendance System", font=("Arial", 10, "italic"),
             text_color="#9ca3af").grid(row=1, column=1, sticky="e", padx=30, pady=10)

root.mainloop()
