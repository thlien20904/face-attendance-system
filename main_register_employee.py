import cv2
import numpy as np
import customtkinter as ctk
import tkinter as tk
import tkinter.font as tkfont
from PIL import Image
from mtcnn import MTCNN
from utils import get_embedding, save_employee
from tkinter import messagebox
import subprocess
import sys
import os

# --- Configuration ---
MIN_FACE_SIZE = 80
MIN_CONFIDENCE = 0.95
REQUIRED_CAPTURES = 5

detector = MTCNN()
cap = None
detected_face = None
captured_faces = []
update_after_id = None

# --- Department -> Roles mapping (company IT example) ---
DEPARTMENTS = {
    "Engineering / Development": [
        "Backend Developer", "Frontend Developer", "Full-stack Developer",
        "Mobile Developer", "DevOps Engineer", "SRE", "Data Engineer",
        "AI/ML Engineer", "Game Developer"
    ],
    "Quality Assurance (QA)": [
        "QA Manual", "QA Automation", "Performance Tester", "Security Tester"
    ],
    "Product": ["Product Manager", "Product Owner", "Business Analyst"],
    "Design / UX / UI": ["UX Designer", "UI Designer", "UX Researcher"],
    "Infrastructure / IT Ops": ["System Administrator", "Network Engineer", "Cloud Engineer"],
    "Data / Analytics / Data Science": ["Data Analyst", "Data Scientist", "BI Engineer"],
    "DevSecOps / Security": ["Security Engineer", "Information Security Analyst"],
    "Project Management / PMO": ["Project Manager", "Scrum Master", "Technical Program Manager"],
    "Sales / Business Dev": ["Sales Engineer", "Account Manager", "Business Development"],
    "Human Resources (HR)": ["Recruiter", "L&D / Training", "C&B Specialist"],
    "Marketing": ["Product Marketing", "Digital Marketing", "Content / Growth"],
    "Customer Support / Technical Support": ["Support Engineer", "Customer Success"],
    "Finance / Legal / Operations": ["Finance / Accounting", "Legal", "Admin / Ops"]
}

# Flatten an initial default roles list (first department)
INITIAL_DEPTS = list(DEPARTMENTS.keys())
INITIAL_ROLES = DEPARTMENTS[INITIAL_DEPTS[0]] if INITIAL_DEPTS else []

# --- Quality Assessment ---
def assess_face_quality(face_img, detection_result):
    x, y, w, h = detection_result["box"]
    confidence = detection_result["confidence"]
    if w < MIN_FACE_SIZE or h < MIN_FACE_SIZE:
        return False, f"Face too small ({w}x{h}px, need ≥{MIN_FACE_SIZE}px)"
    if confidence < MIN_CONFIDENCE:
        return False, f"Low confidence ({confidence:.2f}, need ≥{MIN_CONFIDENCE:.2f})"
    return True, "Good quality"

# --- CTk setup ---
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

root = ctk.CTk()
root.title("Employee Registration")
root.geometry("1100x750")
root.resizable(False, False)
# scaling/font tweaks for high-DPI
try:
    _SCALE = 1.35
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

# --- Layout ---
main_frame = ctk.CTkFrame(root, corner_radius=10)
main_frame.pack(padx=15, pady=15, fill="both", expand=True)

# Header
header = ctk.CTkLabel(main_frame, text="📝 Employee Registration", font=ctk.CTkFont(size=26, weight="bold"))
header.pack(pady=10)

# Body frame: left=form, right=video+preview
body_frame = ctk.CTkFrame(main_frame, corner_radius=10)
body_frame.pack(fill="both", expand=True, padx=10, pady=10)

# Left: Form
form_frame = ctk.CTkFrame(body_frame, corner_radius=10)
form_frame.pack(side="left", fill="y", padx=10, pady=10)

# Form entries
lbl_id = ctk.CTkLabel(form_frame, text="Employee ID:", anchor="w")
lbl_id.pack(pady=5, padx=5, fill="x")
entry_id = ctk.CTkEntry(form_frame)
entry_id.pack(pady=5, padx=5, fill="x")

lbl_name = ctk.CTkLabel(form_frame, text="Full Name:", anchor="w")
lbl_name.pack(pady=5, padx=5, fill="x")
entry_name = ctk.CTkEntry(form_frame)
entry_name.pack(pady=5, padx=5, fill="x")

# Department selection
lbl_dept = ctk.CTkLabel(form_frame, text="Department:", anchor="w")
lbl_dept.pack(pady=(10,5), padx=5, fill="x")
dept_option = ctk.CTkOptionMenu(form_frame, values=INITIAL_DEPTS)
dept_option.set(INITIAL_DEPTS[0] if INITIAL_DEPTS else "")
dept_option.pack(pady=5, padx=5, fill="x")

# Role selection (will be updated when dept changes)
lbl_role = ctk.CTkLabel(form_frame, text="Role / Position:", anchor="w")
lbl_role.pack(pady=(10,5), padx=5, fill="x")
role_option = ctk.CTkOptionMenu(form_frame, values=INITIAL_ROLES)
if INITIAL_ROLES:
    role_option.set(INITIAL_ROLES[0])
role_option.pack(pady=5, padx=5, fill="x")

lbl_pos = ctk.CTkLabel(form_frame, text="Title (optional):", anchor="w")
lbl_pos.pack(pady=5, padx=5, fill="x")
entry_pos = ctk.CTkEntry(form_frame)
entry_pos.pack(pady=5, padx=5, fill="x")

# Progress
lbl_progress = ctk.CTkLabel(form_frame, text=f"Captured: 0/{REQUIRED_CAPTURES}", anchor="center")
lbl_progress.pack(pady=10)
progress = ctk.CTkProgressBar(form_frame, width=200)
progress.set(0)
progress.pack(pady=5)

# Status label
lbl_status = ctk.CTkLabel(form_frame, text="Position your face in frame")
lbl_status.pack(pady=5)

# Buttons
btn_capture = ctk.CTkButton(form_frame, text="📷 Capture Face", width=160, state="disabled")
btn_capture.pack(pady=5)
btn_reset = ctk.CTkButton(form_frame, text="🔄 Reset Captures", width=160)
btn_reset.pack(pady=5)
btn_save = ctk.CTkButton(form_frame, text="💾 Save Employee", width=160, state="disabled")
btn_save.pack(pady=5)

# Right: Video + preview
right_frame = ctk.CTkFrame(body_frame, corner_radius=10)
right_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

lbl_video = ctk.CTkLabel(right_frame, text="", width=640, height=480, fg_color="black")
lbl_video.pack(pady=10)

# Preview
preview_frame = ctk.CTkFrame(right_frame, corner_radius=10)
preview_frame.pack(pady=10, fill="x")
ctk.CTkLabel(preview_frame, text="Captured Images:").pack(pady=5)

preview_labels = []
inner_preview = ctk.CTkFrame(preview_frame)
inner_preview.pack(pady=5)

# Bo viền bằng CTkFrame
for i in range(REQUIRED_CAPTURES):
    frame_preview = ctk.CTkFrame(inner_preview, width=84, height=84, corner_radius=12, fg_color="#666")
    frame_preview.pack(side="left", padx=5)
    lbl = ctk.CTkLabel(frame_preview, width=80, height=80, fg_color="#444", corner_radius=10)
    lbl.pack(expand=True, fill="both", padx=2, pady=2)
    preview_labels.append(lbl)

# --- Functions ---
def on_dept_change(choice):
    """Update role_option values when department changes."""
    roles = DEPARTMENTS.get(choice, [])
    # update the option menu values and set first item if exists
    role_option.configure(values=roles)
    if roles:
        role_option.set(roles[0])
    else:
        role_option.set("")

# Bind department change
dept_option.configure(command=on_dept_change)

def update_status(text, color="#555"):
    lbl_status.configure(text=text, text_color=color)

def update_progress():
    count = len(captured_faces)
    progress.set(count / REQUIRED_CAPTURES)
    lbl_progress.configure(text=f"Captured: {count}/{REQUIRED_CAPTURES}")
    if count >= REQUIRED_CAPTURES:
        btn_save.configure(state="normal")
        btn_capture.configure(state="disabled")
        update_status("✓ Ready to save! Click 'Save Employee'", "#4CAF50")
    else:
        btn_save.configure(state="disabled")
        # ensure capture enabled/disabled depending on detection handled in update_frame

def update_frame():
    global detected_face
    global update_after_id
    ret, frm = cap.read()
    if not ret:
        update_after_id = root.after(10, update_frame)
        return

    rgb = cv2.cvtColor(frm, cv2.COLOR_BGR2RGB)
    results = detector.detect_faces(rgb)

    detected_face = None
    quality_ok = False
    quality_msg = "No face detected"

    if results:
        largest = max(results, key=lambda r: r["box"][2] * r["box"][3])
        x, y, w, h = largest["box"]
        x, y = max(0, x), max(0, y)
        face = rgb[y:y+h, x:x+w]

        quality_ok, quality_msg = assess_face_quality(face, largest)
        if quality_ok:
            # Validate crop before resize
            if face is None or getattr(face, 'size', 0) == 0:
                detected_face = None
            else:
                try:
                    detected_face = cv2.resize(face, (160, 160))
                except Exception:
                    detected_face = None
            btn_capture.configure(state="normal" if len(captured_faces) < REQUIRED_CAPTURES else "disabled")
        else:
            btn_capture.configure(state="disabled")

        cv2.rectangle(frm, (x, y), (x+w, y+h), (0,255,0) if quality_ok else (0,165,255), 2)
        cv2.putText(frm, quality_msg, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0) if quality_ok else (0,165,255), 2)
    else:
        btn_capture.configure(state="disabled")
        cv2.putText(frm, quality_msg, (30,40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)

    update_status("✓ Good quality - Press Capture" if quality_ok else f"⚠ {quality_msg}", "#4CAF50" if quality_ok else "#FF9800")

    img = Image.fromarray(cv2.cvtColor(frm, cv2.COLOR_BGR2RGB))
    try:
        ctk_img = ctk.CTkImage(light_image=img, size=(640, 480))
    except Exception:
        # fallback to using PIL image directly
        ctk_img = ctk.CTkImage(light_image=img, size=(640, 480))
    lbl_video.imgtk = ctk_img
    lbl_video.configure(image=ctk_img)

    update_after_id = root.after(10, update_frame)

def capture_face():
    global detected_face
    if detected_face is None:
        messagebox.showwarning("Warning", "No valid face detected!")
        return
    if len(captured_faces) >= REQUIRED_CAPTURES:
        messagebox.showinfo("Info", f"Already captured {REQUIRED_CAPTURES} faces.")
        return
    captured_faces.append(detected_face)
    idx = len(captured_faces) - 1
    face_pil = Image.fromarray(detected_face).resize((80,80))
    thumb = ctk.CTkImage(light_image=face_pil, size=(80,80))
    preview_labels[idx].imgtk = thumb
    preview_labels[idx].configure(image=thumb)
    update_progress()
    messagebox.showinfo("Success", f"Captured {len(captured_faces)}/{REQUIRED_CAPTURES} faces")

def reset_captures():
    global captured_faces
    if not captured_faces:
        messagebox.showinfo("Info", "No captures to reset")
        return
    if messagebox.askyesno("Confirm", "Reset all captured images?"):
        captured_faces.clear()
        for lbl in preview_labels:
            lbl.configure(image=None)
            lbl.imgtk = None
        update_progress()
        update_status("Position your face in frame", "#555")
        messagebox.showinfo("Info", "All captures cleared")

def save_user():
    emp_id = entry_id.get().strip()
    name = entry_name.get().strip()
    dept = dept_option.get().strip() if hasattr(dept_option, "get") else ""
    role = role_option.get().strip() if hasattr(role_option, "get") else ""
    title = entry_pos.get().strip()

    # if role is empty but title provided, allow
    if not emp_id:
        messagebox.showwarning("Warning", "Employee ID is required!")
        entry_id.focus()
        return
    if not name:
        messagebox.showwarning("Warning", "Name is required!")
        entry_name.focus()
        return
    if len(captured_faces) < REQUIRED_CAPTURES:
        messagebox.showwarning("Warning", f"Please capture {REQUIRED_CAPTURES} faces!")
        return

    try:
        update_status("Processing embeddings...", "#2196F3")
        root.update()
        embeddings = []
        for idx, face in enumerate(captured_faces):
            try:
                emb = get_embedding(face)
                embeddings.append(emb)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to compute embedding for capture #{idx+1}: {e}")
                update_status("Error computing embedding", "#f44336")
                return
        avg_emb = np.mean(embeddings, axis=0)
        # save_employee should accept dept and role/title as metadata; adapt if your utils.save_employee signature differs
        save_employee(emp_id, name, dept, role or title, avg_emb)
        messagebox.showinfo("Success", f"✓ Employee {name} registered successfully!\n\nID: {emp_id}\nDepartment: {dept}\nRole: {role or title}")
        root.withdraw()
        root.after(300, lambda: safe_destroy_and_spawn())
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save employee: {e}")
        update_status("Error occurred", "#f44336")

# --- Connect buttons ---
btn_capture.configure(command=capture_face)
btn_reset.configure(command=reset_captures)
btn_save.configure(command=save_user)

# --- Camera ---
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    messagebox.showerror("Error", "Cannot open camera!")
    root.withdraw()
    root.after(300, lambda: safe_destroy_and_spawn())
else:
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    update_frame()

def on_close():
    if cap:
        cap.release()
    # cancel scheduled update loop if any
    try:
        if update_after_id:
            root.after_cancel(update_after_id)
    except Exception:
        pass
    root.withdraw()
    # allow a short delay then spawn main menu
    root.after(300, lambda: safe_destroy_and_spawn())


def safe_destroy_and_spawn(script_name="main_menu.pyw"):
    try:
        root.destroy()
    except Exception:
        pass
    try:
        subprocess.Popen([sys.executable, script_name], cwd=os.getcwd())
    except Exception:
        pass

root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()
