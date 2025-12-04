import os
import json
import numpy as np
import pandas as pd
from datetime import datetime, date
import hashlib
from face_engine import get_embedder

# --- Paths ---
EMP_PATH = os.path.join("embeddings", "employees.json")
ATT_CSV = "attendance_log.csv"
ADMIN_FILE = "admin.json"

os.makedirs("embeddings", exist_ok=True)

# --- Embedding ---
def get_embedding(face_img):
    """Extract 512-dim face embedding using FaceNet"""
    embedder = get_embedder()
    if embedder is None:
        raise RuntimeError("Failed to load FaceNet model")
    # Validate input
    if face_img is None:
        raise ValueError("Empty face image provided to get_embedding")

    # Normalize PIL Image -> numpy array
    try:
        from PIL import Image
        if isinstance(face_img, Image.Image):
            face_arr = np.array(face_img.convert('RGB'))
        else:
            face_arr = np.array(face_img)
    except Exception:
        face_arr = np.array(face_img)

    # Now validate shape: expect (..., H, W, C) where H>0 and W>0 and C in {1,3}
    if face_arr.size == 0:
        raise ValueError("Empty face image provided to get_embedding (zero size array)")

    # If batch of images
    if getattr(face_arr, 'ndim', 0) == 4:
        # ensure none of batch items are empty
        if any((a.size == 0) for a in face_arr):
            raise ValueError("One or more images in batch are empty")
        try:
            emb = embedder.embeddings(face_arr)
            return emb[0]
        except Exception as e:
            raise RuntimeError(f"Failed to compute embedding for batch: {e}")

    # Single image
    if getattr(face_arr, 'ndim', 0) != 3:
        raise ValueError(f"Expected image with 3 dimensions (H,W,C), got shape={getattr(face_arr, 'shape', None)}")
    h, w, c = face_arr.shape
    if h == 0 or w == 0:
        raise ValueError("Face image has zero height or width")
    if c not in (1, 3):
        # try to reshape if grayscale
        if c == 0:
            raise ValueError("Face image has invalid channel count")
        # allow but convert to RGB
    # run embedding
    try:
        emb = embedder.embeddings([face_arr])
        return emb[0]
    except Exception as e:
        raise RuntimeError(f"Failed to compute embedding: {e}")

# --- Employees ---
def load_employees():
    """Load all registered employees from JSON"""
    if not os.path.exists(EMP_PATH):
        return []
    try:
        with open(EMP_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("[ERROR] Corrupted employees.json file")
        return []

def save_employee(emp_id, name, dept, pos, embedding):
    """
    Save new employee with duplicate ID check
    Raises ValueError if ID already exists
    """
    employees = load_employees()
    
    # Check duplicate ID
    if any(e["id"] == emp_id for e in employees):
        raise ValueError(f"Employee ID {emp_id} already exists!")
    
    # Validate embedding
    if not isinstance(embedding, np.ndarray) or embedding.shape[0] != 512:
        raise ValueError("Invalid embedding format")

    employees.append({
        "id": emp_id,
        "name": name,
        "department": dept,
        "position": pos,
        "embedding": embedding.tolist(),
        "registered_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    # Write atomically: write to temp file then replace
    tmp_path = EMP_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(employees, f, indent=4, ensure_ascii=False)
    try:
        os.replace(tmp_path, EMP_PATH)
    except Exception:
        # Fallback to non-atomic write if replace fails
        with open(EMP_PATH, "w", encoding="utf-8") as f:
            json.dump(employees, f, indent=4, ensure_ascii=False)


def delete_employee(emp_id):
    """Remove an employee by id from employees.json (atomic). Returns True if deleted."""
    emp_id_str = str(emp_id)
    employees = load_employees()
    if not employees:
        return False
    new_emps = [e for e in employees if str(e.get('id')) != emp_id_str]
    if len(new_emps) == len(employees):
        # not found
        return False

    # backup before delete
    try:
        create_backups()
    except Exception:
        pass

    tmp_path = EMP_PATH + ".tmp"
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(new_emps, f, indent=4, ensure_ascii=False)
    try:
        os.replace(tmp_path, EMP_PATH)
    except Exception:
        with open(EMP_PATH, 'w', encoding='utf-8') as f:
            json.dump(new_emps, f, indent=4, ensure_ascii=False)

    try:
        write_audit_log(actor='admin', emp_id=emp_id, action='delete', details=None)
    except Exception:
        pass

    return True


def _audit_log_path():
    return os.path.join('embeddings', 'employee_changes.log')


def write_audit_log(actor, emp_id, action, details=None):
    """Append an audit log entry. details can be a dict or string."""
    entry = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'actor': actor or 'admin',
        'emp_id': str(emp_id) if emp_id is not None else None,
        'action': action,
        'details': details
    }
    try:
        with open(_audit_log_path(), 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    except Exception:
        pass


def create_backups():
    """Create .bak copies of employees.json and attendance_log.csv (overwrite existing backups)."""
    try:
        if os.path.exists(EMP_PATH):
            os.replace(EMP_PATH, EMP_PATH + '.bak') if False else None
    except Exception:
        # fallback to copy
        try:
            import shutil
            if os.path.exists(EMP_PATH):
                shutil.copy2(EMP_PATH, EMP_PATH + '.bak')
        except Exception:
            pass
    try:
        import shutil
        if os.path.exists(EMP_PATH):
            shutil.copy2(EMP_PATH, EMP_PATH + '.bak')
        if os.path.exists(ATT_CSV):
            shutil.copy2(ATT_CSV, ATT_CSV + '.bak')
    except Exception:
        pass


def restore_backup():
    """Restore employees.json and attendance_log.csv from .bak files. Returns True if restored."""
    restored = False
    try:
        import shutil
        if os.path.exists(EMP_PATH + '.bak'):
            shutil.copy2(EMP_PATH + '.bak', EMP_PATH)
            restored = True
        if os.path.exists(ATT_CSV + '.bak'):
            shutil.copy2(ATT_CSV + '.bak', ATT_CSV)
            restored = True
    except Exception:
        restored = False
    return restored

# --- Recognition ---
def recognize_face(embedding, users, threshold=0.7):
    """
    Match face embedding with registered users using Euclidean distance
    Returns: (matched_user, distance) or (None, min_distance)
    """
    if not users:
        return None, 999
    
    min_dist = float('inf')
    matched_user = None
    
    for user in users:
        known_emb = np.array(user["embedding"])
        dist = np.linalg.norm(embedding - known_emb)
        
        if dist < min_dist:
            min_dist = dist
            matched_user = user
    
    if min_dist < threshold:
        return matched_user, min_dist
    return None, min_dist

# --- Attendance CSV ---
def ensure_attendance_csv():
    """Create attendance CSV if not exists"""
    if not os.path.exists(ATT_CSV):
        df = pd.DataFrame(columns=["id", "name", "department", "position", "checkin", "checkout"])
        df.to_csv(ATT_CSV, index=False)

def load_attendance_df():
    """Load attendance dataframe with error handling"""
    ensure_attendance_csv()
    try:
        # Read CSV and fill NaN in checkout column with empty string
        df = pd.read_csv(ATT_CSV)
        df['checkout'] = df['checkout'].fillna('')
        return df
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=["id", "name", "department", "position", "checkin", "checkout"])

def save_attendance_df(df):
    """Save attendance dataframe to CSV"""
    df.to_csv(ATT_CSV, index=False)

def mark_checkin(emp):
    """
    Record employee check-in
    Check if already checked in today
    """
    df = load_attendance_df()
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")  # Only date part
    
    # Check if already checked in today
    if not df.empty:
        # Parse checkin column and extract date
        df['checkin_parsed'] = pd.to_datetime(df['checkin'], errors='coerce')
        df['checkin_date_str'] = df['checkin_parsed'].dt.strftime('%Y-%m-%d')
        
        # Convert ID to string for comparison
        emp_id_str = str(emp['id'])
        already_checkin = df[(df['id'].astype(str) == emp_id_str) & (df['checkin_date_str'] == today_str)]
        
        # Clean up temporary columns
        df = df.drop(['checkin_parsed', 'checkin_date_str'], axis=1)
        
        if not already_checkin.empty:
            print(f"[INFO] {emp['name']} already checked in today")
            return False
    
    # Record new check-in
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    new_row = pd.DataFrame([{
        "id": emp["id"],
        "name": emp["name"],
        "department": emp["department"],
        "position": emp["position"],
        "checkin": now_str,
        "checkout": ""
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    
    save_attendance_df(df)
    print(f"[SUCCESS] {emp['name']} checked in at {now_str}")
    return True

def mark_checkout(emp):
    """
    Record employee check-out
    Find today's unchecked-out record only
    """
    df = load_attendance_df()
    
    if df.empty:
        print(f"[ERROR] No check-in record found for {emp['name']}")
        return False
    
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")  # Only date part
    
    print(f"[DEBUG] Looking for checkout for {emp['name']} on {today_str}")
    print(f"[DEBUG] Total records in CSV: {len(df)}")
    
    # Parse checkin column properly
    df['checkin_parsed'] = pd.to_datetime(df['checkin'], errors='coerce')
    df['checkin_date_str'] = df['checkin_parsed'].dt.strftime('%Y-%m-%d')
    
    # Convert ID to string for comparison (CSV stores as string)
    emp_id_str = str(emp['id'])
    
    # Debug: Print all records for this employee
    emp_records = df[df['id'].astype(str) == emp_id_str]
    print(f"[DEBUG] Records for {emp['name']} (ID: {emp_id_str}):")
    for idx, row in emp_records.iterrows():
        print(f"  - Index {idx}: id={row['id']}, checkin={row['checkin']}, date={row['checkin_date_str']}, checkout='{row['checkout']}'")
    
    # Find today's check-in without checkout
    # Note: Empty checkout can be either empty string "" or NaN
    matching_records = df[
        (df['id'].astype(str) == emp_id_str) & 
        (df['checkout'].isna() | (df['checkout'] == "")) & 
        (df['checkin_date_str'] == today_str)
    ]
    
    print(f"[DEBUG] Matching records: {len(matching_records)}")
    
    if not matching_records.empty:
        # Get the first matching record
        idx = matching_records.index[0]
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")
        
        # Update checkout time
        df.at[idx, 'checkout'] = now_str
        
        # Remove temporary columns before saving
        df = df.drop(['checkin_parsed', 'checkin_date_str'], axis=1)
        save_attendance_df(df)
        
        print(f"[SUCCESS] {emp['name']} checked out at {now_str}")
        return True
    else:
        print(f"[ERROR] No valid check-in found for {emp['name']} today")
        print(f"[DEBUG] Today is: {today_str}")
        return False

# --- Admin credentials ---
def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def ensure_admin_account():
    """
    Create default admin account if not exists
    Password is hashed
    Default credentials: admin / admin123
    """
    if not os.path.exists(ADMIN_FILE):
        admin = {
            "username": "admin",
            "password": hash_password("admin123")
        }
        with open(ADMIN_FILE, "w", encoding="utf-8") as f:
            json.dump(admin, f, indent=4)
        print("[INFO] Default admin account created (username: admin, password: admin123)")

def verify_admin(username, password):
    """
    Verify admin credentials
    Compare hashed passwords
    """
    ensure_admin_account()
    try:
        with open(ADMIN_FILE, "r", encoding="utf-8") as f:
            admin = json.load(f)
        
        # Hash input password and compare
        hashed_input = hash_password(password)
        return username == admin["username"] and hashed_input == admin["password"]
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        print("[ERROR] Admin file corrupted")
        return False

def change_admin_password(old_password, new_password):
    """
    Change admin password
    """
    if not verify_admin("admin", old_password):
        raise ValueError("Current password is incorrect")
    
    if len(new_password) < 6:
        raise ValueError("New password must be at least 6 characters")
    
    admin = {
        "username": "admin",
        "password": hash_password(new_password)
    }
    
    with open(ADMIN_FILE, "w", encoding="utf-8") as f:
        json.dump(admin, f, indent=4)
    
    print("[SUCCESS] Admin password changed successfully")

# --- Export Reports ---
def export_attendance_to_excel(start_date=None, end_date=None, output_file="attendance_report.xlsx"):
    """
    Export attendance to Excel with filtering
    """
    df = load_attendance_df()
    
    if df.empty:
        print("[WARN] No attendance records to export")
        return False
    
    # Filter by date range if provided
    if start_date or end_date:
        df['checkin_date'] = pd.to_datetime(df['checkin'], errors='coerce').dt.date
        if start_date:
            df = df[df['checkin_date'] >= start_date]
        if end_date:
            df = df[df['checkin_date'] <= end_date]
        df = df.drop('checkin_date', axis=1)
    
    # Calculate working hours
    df_copy = df.copy()
    df_copy['checkin_dt'] = pd.to_datetime(df_copy['checkin'], errors='coerce')
    df_copy['checkout_dt'] = pd.to_datetime(df_copy['checkout'], errors='coerce')
    df_copy['working_hours'] = (df_copy['checkout_dt'] - df_copy['checkin_dt']).dt.total_seconds() / 3600
    df_copy['working_hours'] = df_copy['working_hours'].apply(lambda x: f"{x:.2f}h" if pd.notna(x) else "")
    
    # Select columns for export
    export_df = df_copy[['id', 'name', 'department', 'position', 'checkin', 'checkout', 'working_hours']]
    
    # Export to Excel
    export_df.to_excel(output_file, index=False, sheet_name='Attendance')
    print(f"[SUCCESS] Exported {len(export_df)} records to {output_file}")
    return True


def update_employee(emp_id, **fields):
    """Update fields of an employee identified by emp_id. Returns True if updated."""
    emp_id_str = str(emp_id)
    employees = load_employees()
    if not employees:
        return False

    updated = False
    for e in employees:
        if str(e.get('id')) == emp_id_str:
            # update allowed fields: name, department, position, embedding
            for k, v in fields.items():
                if k in ('name', 'department', 'position', 'embedding'):
                    e[k] = v
            updated = True
            break

    if not updated:
        return False

    # create backups before applying change
    try:
        create_backups()
    except Exception:
        pass

    tmp_path = EMP_PATH + ".tmp"
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(employees, f, indent=4, ensure_ascii=False)
    try:
        os.replace(tmp_path, EMP_PATH)
    except Exception:
        with open(EMP_PATH, 'w', encoding='utf-8') as f:
            json.dump(employees, f, indent=4, ensure_ascii=False)

    # audit log
    try:
        write_audit_log(actor='admin', emp_id=emp_id, action='update', details=fields)
    except Exception:
        pass

    return True


def update_attendance_records(emp_id, **fields):
    """Update attendance_log.csv rows for the given emp_id with provided fields.
    Allowed fields: name, department, position. Returns number of rows updated.
    """
    allowed = {'name', 'department', 'position'}
    to_update = {k: v for k, v in fields.items() if k in allowed}
    if not to_update:
        return 0

    df = load_attendance_df()
    if df.empty:
        return 0

    emp_id_str = str(emp_id)
    mask = df['id'].astype(str) == emp_id_str
    if not mask.any():
        return 0

    # Update allowed columns
    for k, v in to_update.items():
        if k in df.columns:
            df.loc[mask, k] = v

    # Save back
    save_attendance_df(df)
    return int(mask.sum())