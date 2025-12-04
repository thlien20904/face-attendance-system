import sys
import subprocess
import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from utils import load_attendance_df, load_employees, delete_employee, update_employee, create_backups, restore_backup
from payroll import compute_payroll, export_payroll_to_excel_formatted
from face_engine import shutdown as face_engine_shutdown

try:
    import customtkinter as ctk
except ImportError:
    raise ImportError("customtkinter is required. Install with: pip install customtkinter")

# --- CTk setup ---
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("dark-blue")

# Departments and roles (mirrors main_register_employee.py choices)
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

# --- Root Window ---
root = ctk.CTk()
root.title("Admin Dashboard - FaceAttendance Pro")
root.state("zoomed")
# Apply scaling/font tweaks for better readability on high-DPI displays
try:
    import tkinter as _tk
    import tkinter.font as _tkfont
    _SCALE = 1.4
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
root.rowconfigure(0, weight=1)
root.columnconfigure(1, weight=1)

# --- Sidebar ---
sidebar = ctk.CTkFrame(root, fg_color="#1e293b", corner_radius=0)
sidebar.grid(row=0, column=0, sticky="nswe")
sidebar.grid_rowconfigure(0, weight=1)

ctk.CTkLabel(sidebar, text="FaceAttendance Pro", font=("Helvetica", 30, "bold"),
             text_color="#F3F6FB").pack(pady=(50,10), padx=20)
ctk.CTkLabel(sidebar, text="Admin Dashboard", font=("Helvetica", 18, "bold"),
             text_color="#B8D0F2").pack(pady=(0,20), padx=20)

# --- Main Content ---
main_frame = ctk.CTkFrame(root, fg_color="#f0f4f8")
main_frame.grid(row=0, column=1, sticky="nswe", padx=20, pady=20)
main_frame.rowconfigure(1, weight=1)
main_frame.columnconfigure(0, weight=1)

# --- Dynamic Content Frame ---
content_frame = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=15)
content_frame.grid(row=1, column=0, sticky="nsew")
content_frame.rowconfigure(0, weight=1)
content_frame.columnconfigure(0, weight=1)

# --- Functions ---
def clear_content():
    """Xóa toàn bộ nội dung hiện tại trong content_frame"""
    for widget in content_frame.winfo_children():
        widget.destroy()

def open_register():
    subprocess.Popen([sys.executable, "main_register_employee.py"], cwd=os.getcwd())

def logout():
    """Đóng Dashboard và mở lại main_menu.pyw"""
    root.withdraw()
    root.after(300, lambda: safe_destroy("main_menu.pyw"))


def safe_destroy(script_name=None):
    try:
        try:
            root.quit()
            root.update_idletasks()
        except Exception:
            pass
        root.destroy()
    except Exception:
        pass

    if script_name:
        try:
            subprocess.Popen([sys.executable, script_name], cwd=os.getcwd())
        except Exception:
            pass

def view_log():
    clear_content()
    df = load_attendance_df()
    if df.empty:
        ctk.CTkLabel(content_frame, text="No attendance data found.", font=("Arial", 16)).pack(pady=20)
        return

    # --- Title ---
    ctk.CTkLabel(content_frame, text="📋 Attendance Log", font=("Arial", 20, "bold")).pack(pady=(10,5))

    # --- Frame for Treeview ---
    table_frame = ctk.CTkFrame(content_frame)
    table_frame.pack(fill="both", expand=True, padx=20, pady=10)
    table_frame.rowconfigure(0, weight=1)
    table_frame.columnconfigure(0, weight=1)

    # Scrollbars
    vsb = ttk.Scrollbar(table_frame, orient="vertical")
    hsb = ttk.Scrollbar(table_frame, orient="horizontal")

    tree = ttk.Treeview(
        table_frame,
        columns=list(df.columns),
        show="headings",
        yscrollcommand=vsb.set,
        xscrollcommand=hsb.set,
        height=25
    )

    vsb.config(command=tree.yview)
    hsb.config(command=tree.xview)
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")
    tree.grid(row=0, column=0, sticky="nsew")

    # Setup columns and font larger
    style = ttk.Style()
    style.configure("Treeview.Heading", font=("Arial", 14, "bold"))
    style.configure("Treeview", font=("Arial", 12))
    style.map('Treeview', background=[('selected', '#0078d7')])

    for col in df.columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="center", width=160, minwidth=120)

    # Insert data
    for _, row in df.iterrows():
        tree.insert("", "end", values=list(row))

def show_dashboard():
    clear_content()
    df = load_attendance_df()
    employees = load_employees()

    total_emps = len(employees)
    total_logs = len(df)
    total_checkedout = len(df[df["checkout"] != ""] if not df.empty else [])
    avg_work_hours = 0

    try:
        df_valid = df[df["checkout"] != ""].copy()
        df_valid["checkin"] = pd.to_datetime(df_valid["checkin"])
        df_valid["checkout"] = pd.to_datetime(df_valid["checkout"])
        df_valid["hours"] = (df_valid["checkout"] - df_valid["checkin"]).dt.total_seconds() / 3600
        avg_work_hours = df_valid["hours"].mean()
    except Exception:
        pass

    # --- Cards Container ---
    cards_container = ctk.CTkFrame(content_frame, fg_color="#f0f4f8")
    cards_container.pack(fill="x", padx=20, pady=(10,10))
    cards_container.columnconfigure((0,1,2,3), weight=1)

    summary_texts = [
        f"Total Employees\n{total_emps}",
        f"Total Check-ins\n{total_logs}",
        f"Total Check-outs\n{total_checkedout}",
        f"Avg Work Hours\n{avg_work_hours:.2f}h"
    ]
    colors = ["#4CAF50", "#FF9800", "#607D8B", "#9C27B0"]

    for i, text in enumerate(summary_texts):
        card = ctk.CTkFrame(cards_container, fg_color=colors[i], corner_radius=15)
        card.grid(row=0, column=i, padx=10, sticky="nsew")
        ctk.CTkLabel(card, text=text, font=("Arial", 18, "bold"), text_color="white").pack(padx=20, pady=20)

    # --- Chart Container ---
    chart_container = ctk.CTkFrame(content_frame, fg_color="white")
    chart_container.pack(fill="both", expand=True, padx=20, pady=(0,20))

    if total_logs > 0:
        df["checkin_date"] = pd.to_datetime(df["checkin"], errors="coerce").dt.date
        checkin_counts = df["checkin_date"].value_counts().sort_index()

        fig, ax = plt.subplots(figsize=(10,5))
        ax.plot(checkin_counts.index, checkin_counts.values, marker='o', color="#3F51B5")
        ax.set_title("Check-ins by Date", fontsize=16)
        ax.set_xlabel("Date", fontsize=14)
        ax.set_ylabel("Count", fontsize=14)
        ax.grid(True)
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=chart_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
    else:
        ctk.CTkLabel(chart_container, text="No attendance data to visualize.", font=("Arial", 16)).pack(pady=20)


def show_payroll():
    """Hiển thị bảng lương cho tháng hiện tại và cho phép xuất Excel"""
    clear_content()
    # choose month/year (default: current month)
    today = datetime.now()
    year = today.year
    month = today.month

    # Controls: month and year selectors
    ctrl_frame = ctk.CTkFrame(content_frame, fg_color="white")
    ctrl_frame.pack(fill="x", padx=20, pady=(10,5))
    months = [str(i) for i in range(1, 13)]
    years = [str(y) for y in range(year - 3, year + 1)]
    month_var = ctk.StringVar(value=str(month))
    year_var = ctk.StringVar(value=str(year))
    ctk.CTkLabel(ctrl_frame, text="Tháng:").pack(side="left", padx=(0,8))
    month_menu = ctk.CTkOptionMenu(ctrl_frame, values=months, variable=month_var)
    month_menu.pack(side="left", padx=(0,16))
    ctk.CTkLabel(ctrl_frame, text="Năm:").pack(side="left", padx=(0,8))
    year_menu = ctk.CTkOptionMenu(ctrl_frame, values=years, variable=year_var)
    year_menu.pack(side="left", padx=(0,16))

    # Apply button
    def apply_filters():
        nonlocal month, year
        try:
            sel_m = int(month_var.get())
            sel_y = int(year_var.get())
        except Exception:
            return
        # refresh payroll table by recomputing
        refresh_table(sel_y, sel_m)

    ctk.CTkButton(ctrl_frame, text="Apply", command=apply_filters, fg_color="#3B82F6").pack(side="left", padx=8)

    try:
        df = compute_payroll(year, month)
    except Exception as e:
        ctk.CTkLabel(content_frame, text=f"Không thể tính bảng lương: {e}", font=("Arial", 16)).pack(pady=20)
        return

    if df.empty:
        ctk.CTkLabel(content_frame, text="No payroll data for selected month.", font=("Arial", 16)).pack(pady=20)
        return

    # Title and export button
    header_frame = ctk.CTkFrame(content_frame, fg_color="white")
    header_frame.pack(fill="x", padx=20, pady=(10,5))
    ctk.CTkLabel(header_frame, text=f"Bảng lương - {month}/{year}", font=("Arial", 18, "bold")).pack(side="left")

    def do_export():
        out = f"payroll_{year}_{month}.xlsx"
        try:
            export_payroll_to_excel_formatted(df, out)
            ctk.CTkLabel(header_frame, text=f"Exported: {out}", text_color="#10b981").pack(side="right", padx=10)
        except Exception as e:
            ctk.CTkLabel(header_frame, text=f"Export failed: {e}", text_color="#ef4444").pack(side="right", padx=10)

    ctk.CTkButton(header_frame, text="Export Excel", command=do_export, fg_color="#4CAF50").pack(side="right", padx=10)

    # Treeview table
    table_frame = ctk.CTkFrame(content_frame)
    table_frame.pack(fill="both", expand=True, padx=20, pady=10)

    cols = [
        'id','name','department','position','base_salary','worked_days','working_days','total_hours','regular_hours','overtime_hours','regular_pay','overtime_pay','total_pay'
    ]
    import tkinter.ttk as ttk
    vsb = ttk.Scrollbar(table_frame, orient="vertical")
    hsb = ttk.Scrollbar(table_frame, orient="horizontal")
    tree = ttk.Treeview(table_frame, columns=cols, show='headings', yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    vsb.config(command=tree.yview)
    hsb.config(command=tree.xview)
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")
    tree.grid(row=0, column=0, sticky="nsew")
    table_frame.rowconfigure(0, weight=1)
    table_frame.columnconfigure(0, weight=1)

    for c in cols:
        tree.heading(c, text=c)
        tree.column(c, width=120, anchor='center')

    def refresh_table(sel_year, sel_month):
        # recompute payroll for given month/year and repopulate tree
        try:
            new_df = compute_payroll(sel_year, sel_month)
        except Exception as e:
            clear_content()
            ctk.CTkLabel(content_frame, text=f"Không thể tính bảng lương: {e}", font=("Arial", 16)).pack(pady=20)
            return
        # clear tree
        for i in tree.get_children():
            tree.delete(i)
        if new_df is None or new_df.empty:
            return
        for _, r in new_df.iterrows():
            vals = [r[c] for c in cols]
            tree.insert('', 'end', values=vals)

    # initial populate
    refresh_table(year, month)

    # Charts container (below table)
    chart_frame = ctk.CTkFrame(content_frame, fg_color="white")
    chart_frame.pack(fill="both", expand=True, padx=20, pady=(10,20))

    def refresh_charts(new_df):
        # Clear previous charts
        for w in chart_frame.winfo_children():
            try:
                w.destroy()
            except Exception:
                pass

        if new_df is None or new_df.empty:
            return

        # Create two charts: dept total cost (bar) and top-10 earners (horizontal bar)
        try:
            fig, axes = plt.subplots(1, 2, figsize=(10, 4))

            # Dept total payroll
            dept_totals = new_df.groupby('department')['total_pay'].sum().sort_values(ascending=False)
            if not dept_totals.empty:
                axes[0].bar(dept_totals.index, dept_totals.values, color='#3F51B5')
                axes[0].set_title('Tổng chi phí lương theo phòng')
                axes[0].tick_params(axis='x', rotation=45)
            else:
                axes[0].text(0.5, 0.5, 'No data', ha='center')

            # Top 10 earners
            top10 = new_df.nlargest(10, 'total_pay')
            if not top10.empty:
                axes[1].barh(top10['name'][::-1], top10['total_pay'][::-1], color='#4CAF50')
                axes[1].set_title('Top 10 lương cao nhất')
            else:
                axes[1].text(0.5, 0.5, 'No data', ha='center')

            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, master=chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill='both', expand=True)
        except Exception as e:
            # if plotting fails, show simple message
            ctk.CTkLabel(chart_frame, text=f"Could not draw charts: {e}").pack(pady=10)

    # ensure charts updated after initial population
    try:
        refresh_charts(df)
    except Exception:
        pass


def show_employees():
    """Show a list of employees with option to delete selected."""
    clear_content()
    emps = load_employees()

    # search and filter controls
    ctrl_frame = ctk.CTkFrame(content_frame, fg_color='white')
    ctrl_frame.pack(fill='x', padx=20, pady=(10,5))
    search_var = ctk.StringVar(value='')
    ctk.CTkLabel(ctrl_frame, text='Tìm:').pack(side='left', padx=(0,8))
    search_entry = ctk.CTkEntry(ctrl_frame, textvariable=search_var, width=220)
    search_entry.pack(side='left', padx=(0,12))
    ctk.CTkLabel(ctrl_frame, text='Phòng ban:').pack(side='left', padx=(0,8))
    dept_vals = ['All'] + list(DEPARTMENTS.keys())
    dept_var = ctk.StringVar(value='All')
    dept_menu = ctk.CTkOptionMenu(ctrl_frame, values=dept_vals, variable=dept_var)
    dept_menu.pack(side='left')

    header = ctk.CTkLabel(content_frame, text="Manage Employees", font=("Arial", 20, "bold"))
    header.pack(padx=20, pady=(10,5), anchor="w")

    table_frame = ctk.CTkFrame(content_frame)
    table_frame.pack(fill="both", expand=True, padx=20, pady=10)

    cols = ['id', 'name', 'department', 'position']
    import tkinter.ttk as ttk
    # configure Treeview style for larger, more readable text and taller rows
    style = ttk.Style()
    try:
        style.configure("Treeview.Heading", font=("Arial", 16, "bold"))
        style.configure("Treeview", font=("Arial", 14), rowheight=30)
        style.map('Treeview', background=[('selected', '#0078d7')])
    except Exception:
        pass

    vsb = ttk.Scrollbar(table_frame, orient="vertical")
    hsb = ttk.Scrollbar(table_frame, orient="horizontal")
    # allow multi-select
    tree = ttk.Treeview(table_frame, columns=cols, show='headings', selectmode='extended', yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    vsb.config(command=tree.yview)
    hsb.config(command=tree.xview)
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")
    tree.grid(row=0, column=0, sticky="nsew")
    table_frame.rowconfigure(0, weight=1)
    table_frame.columnconfigure(0, weight=1)

    # set column widths and alignment for readability
    tree.heading('id', text='id')
    tree.column('id', width=80, anchor='center')
    tree.heading('name', text='name')
    tree.column('name', width=300, anchor='w')
    tree.heading('department', text='department')
    tree.column('department', width=260, anchor='w')
    tree.heading('position', text='position')
    tree.column('position', width=260, anchor='w')

    # helper to refresh based on search and dept filter
    emps_all = emps

    def refresh_tree():
        q = search_var.get().strip().lower()
        sel_dept = dept_var.get()
        for i in tree.get_children():
            tree.delete(i)
        for e in emps_all:
            if sel_dept != 'All' and e.get('department') != sel_dept:
                continue
            if q:
                if q not in str(e.get('id','')).lower() and q not in str(e.get('name','')).lower():
                    continue
            tree.insert('', 'end', values=(e.get('id'), e.get('name'), e.get('department'), e.get('position')))

    # bind search and dept change
    def on_search_change(var, idx, mode):
        refresh_tree()
    search_var.trace_add('write', on_search_change)
    try:
        dept_menu.configure(command=lambda choice: refresh_tree())
    except Exception:
        pass

    refresh_tree()

    # Delete and Edit buttons
    def delete_selected():
        sels = tree.selection()
        if not sels:
            return
        # collect names for confirmation
        items = [tree.item(it)['values'] for it in sels]
        emp_ids = [str(it[0]) for it in items]
        names = [str(it[1]) for it in items]
        from tkinter import messagebox
        if not messagebox.askyesno('Confirm', f'Xóa {len(emp_ids)} nhân viên đã chọn?'):
            return
        # create one backup before batch delete
        try:
            create_backups()
        except Exception:
            pass
        deleted = 0
        for eid in emp_ids:
            try:
                ok = delete_employee(eid)
                if ok:
                    deleted += 1
            except Exception:
                pass
        messagebox.showinfo('Deleted', f'Deleted {deleted} / {len(emp_ids)}')
        # reload and refresh
        show_employees()

    def edit_selected():
        sel = tree.selection()
        if not sel:
            from tkinter import messagebox
            messagebox.showwarning('Chỉnh sửa', 'Chưa chọn nhân viên nào.')
            return
        item = sel[0]
        vals = tree.item(item, 'values')
        emp_id = vals[0]
        # find employee
        emps = load_employees()
        emp = None
        for e in emps:
            if str(e.get('id')) == str(emp_id):
                emp = e
                break
        if emp is None:
            from tkinter import messagebox
            messagebox.showerror('Lỗi', 'Không tìm thấy nhân viên.')
            return

        # open edit dialog
        dlg = ctk.CTkToplevel(root)
        dlg.title('Chỉnh sửa nhân viên')
        # make dialog slightly taller so action buttons are visible
        dlg.geometry('480x300')
        dlg.resizable(False, False)
        dlg.transient(root)
        dlg.grab_set()

        lbl_name = ctk.CTkLabel(dlg, text='Họ và tên:')
        lbl_name.pack(padx=12, pady=(12, 4), anchor='w')
        ent_name = ctk.CTkEntry(dlg)
        ent_name.insert(0, emp.get('name', ''))
        ent_name.pack(fill='x', padx=12)

        lbl_dept = ctk.CTkLabel(dlg, text='Phòng ban:')
        lbl_dept.pack(padx=12, pady=(8, 4), anchor='w')
        dept_var = ctk.StringVar(value=emp.get('department', list(DEPARTMENTS.keys())[0] if DEPARTMENTS else ''))
        dept_menu = ctk.CTkOptionMenu(dlg, values=list(DEPARTMENTS.keys()), variable=dept_var)
        dept_menu.pack(fill='x', padx=12)

        lbl_pos = ctk.CTkLabel(dlg, text='Chức vụ:')
        lbl_pos.pack(padx=12, pady=(8, 4), anchor='w')
        # initialize roles based on selected department
        initial_roles = DEPARTMENTS.get(dept_var.get(), [])
        role_var = ctk.StringVar(value=emp.get('position', initial_roles[0] if initial_roles else ''))
        role_menu = ctk.CTkOptionMenu(dlg, values=initial_roles, variable=role_var)
        role_menu.pack(fill='x', padx=12)

        def _on_dept_change(choice):
            roles = DEPARTMENTS.get(choice, [])
            try:
                role_menu.configure(values=roles)
            except Exception:
                pass
            if roles:
                role_var.set(roles[0])

        # bind change
        try:
            dept_menu.configure(command=_on_dept_change)
        except Exception:
            # fallback: if command not supported, ignore
            pass

        def on_save():
            new_name = ent_name.get().strip()
            new_dept = dept_var.get().strip()
            new_pos = role_var.get().strip()
            from tkinter import messagebox
            if not new_name:
                messagebox.showwarning('Thiếu trường', 'Tên không được để trống.')
                return
            ok = update_employee(emp_id, name=new_name, department=new_dept, position=new_pos)
            if ok:
                # propagate changes to attendance CSV so historical logs reflect new name/department/position
                try:
                    from utils import update_attendance_records
                    updated_rows = update_attendance_records(emp_id, name=new_name, department=new_dept, position=new_pos)
                except Exception:
                    updated_rows = 0
                messagebox.showinfo('Lưu', f'Đã cập nhật nhân viên. Attendance rows updated: {updated_rows}')
                dlg.destroy()
                show_employees()
            else:
                messagebox.showerror('Lỗi', 'Không thể lưu thay đổi.')

        # place buttons in a fixed bottom frame so they are always visible
        btn_frame = ctk.CTkFrame(dlg)
        btn_frame.pack(side='bottom', fill='x', pady=12, padx=12)
        btn_cancel = ctk.CTkButton(btn_frame, text='Hủy', command=dlg.destroy)
        btn_cancel.pack(side='right', padx=(6, 0))
        btn_save = ctk.CTkButton(btn_frame, text='Lưu', command=on_save)
        btn_save.pack(side='right')

        # keyboard shortcuts: Enter to save, Esc to cancel
        dlg.bind('<Return>', lambda e: on_save())
        dlg.bind('<Escape>', lambda e: dlg.destroy())

    btn_frame = ctk.CTkFrame(content_frame, fg_color='white')
    btn_frame.pack(fill='x', padx=20, pady=(0,10))
    ctk.CTkButton(btn_frame, text='Delete Selected', fg_color='#E53935', command=delete_selected).pack(side='left', padx=(0,8))
    ctk.CTkButton(btn_frame, text='Edit Selected', fg_color='#F59E0B', command=edit_selected).pack(side='left', padx=(8,8))
    ctk.CTkButton(btn_frame, text='Restore Backup', fg_color='#6B7280', command=lambda: _restore_backup()).pack(side='left')

    def _restore_backup():
        from tkinter import messagebox
        if not messagebox.askyesno('Restore', 'Khôi phục từ bản sao lưu cuối cùng? (sẽ ghi đè dữ liệu hiện tại)'):
            return
        ok = restore_backup()
        if ok:
            messagebox.showinfo('Restore', 'Đã khôi phục từ bản sao lưu. Làm mới danh sách.')
            show_employees()
        else:
            messagebox.showerror('Restore', 'Không tìm thấy bản sao lưu hoặc khôi phục thất bại.')

# --- Sidebar Buttons ---
btn_cfg = {"height": 55, "corner_radius": 15, "font": ("Arial", 16, "bold")}
ctk.CTkButton(sidebar, text="➕ Register Employee", fg_color="#4CAF50", hover_color="#66bb6a",
              command=open_register, **btn_cfg).pack(fill="x", padx=20, pady=15)
ctk.CTkButton(sidebar, text="📋 View Attendance Log", fg_color="#FF9800", hover_color="#ffb74d",
              command=view_log, **btn_cfg).pack(fill="x", padx=20, pady=15)
ctk.CTkButton(sidebar, text="📊 Dashboard / Statistics", fg_color="#607D8B", hover_color="#78909C",
              command=show_dashboard, **btn_cfg).pack(fill="x", padx=20, pady=15)
ctk.CTkButton(sidebar, text="🧾 Bảng lương", fg_color="#3B82F6", hover_color="#60A5FA",
              command=show_payroll, **btn_cfg).pack(fill="x", padx=20, pady=15)
ctk.CTkButton(sidebar, text="👥 Manage Employees", fg_color="#10B981", hover_color="#34D399",
              command=lambda: show_employees(), **btn_cfg).pack(fill="x", padx=20, pady=15)
ctk.CTkButton(sidebar, text="🚪 Logout", fg_color="#E53935", hover_color="#F44336",
              command=logout, **btn_cfg).pack(fill="x", padx=20, pady=15)

# --- Footer ---
ctk.CTkLabel(root, text="FaceAttendance System © 2025", font=("Arial", 14, "italic"),
             text_color="#A0A0A0").grid(row=1, column=1, sticky="e", padx=30, pady=10)

# --- Close Handler ---
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
        # attempt to shutdown face engine to release TF resources
        try:
            face_engine_shutdown()
        except Exception:
            pass
        root.destroy()
    except tk.TclError:
        pass

root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()
