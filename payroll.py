import calendar
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import os
from utils import load_employees, load_attendance_df

# Salary reference (VND / month) - reasonable defaults for VN IT market
# These are mid/typical values; you can tweak per-company
ROLE_SALARY_REF = {
    # Software
    "Backend Developer": 18400000,
    "Frontend Developer": 18400000,
    "Full-stack Developer": 22000000,
    "Mobile Developer": 20000000,
    "DevOps Engineer": 28000000,
    "SRE": 30000000,
    "Data Engineer": 30000000,
    "AI/ML Engineer": 35000000,
    "Game Developer": 20000000,
    # QA
    "QA Manual": 14000000,
    "QA Automation": 18000000,
    "Performance Tester": 16000000,
    # Product / PM
    "Product Manager": 40000000,
    "Product Owner": 38000000,
    "Business Analyst": 25000000,
    # Design
    "UX Designer": 18000000,
    "UI Designer": 17000000,
    "UX Researcher": 17000000,
    # Infra
    "System Administrator": 16000000,
    "Network Engineer": 18000000,
    "Cloud Engineer": 30000000,
    # Security
    "Security Engineer": 22000000,
    # PMO
    "Project Manager": 45000000,
    "Scrum Master": 35000000,
    # Sales / HR / Others
    "Sales Engineer": 20000000,
    "Recruiter": 15000000,
    "Finance / Accounting": 15000000,
    "Admin / Ops": 12000000,
}

# Default base by department if role unknown
DEPT_DEFAULT = {
    "Engineering / Development": 20000000,
    "Quality Assurance (QA)": 15000000,
    "Product": 35000000,
    "Design / UX / UI": 17000000,
    "Infrastructure / IT Ops": 18000000,
    "Data / Analytics / Data Science": 30000000,
    "DevSecOps / Security": 22000000,
    "Project Management / PMO": 40000000,
    "Sales / Business Dev": 18000000,
    "Human Resources (HR)": 14000000,
    "Marketing": 14000000,
    "Customer Support / Technical Support": 12000000,
    "Finance / Legal / Operations": 14000000,
}

# Payroll rules
STANDARD_HOURS_PER_DAY = 8
OVERTIME_RATE = 1.5  # 1.5x per hour


def working_days_in_month(year: int, month: int):
    """Return number of weekday working days in a month (Mon-Fri)."""
    c = calendar.Calendar()
    wd = [d for d in c.itermonthdates(year, month) if d.month == month and d.weekday() < 5]
    return len(wd)


def parse_attendance_for_month(df: pd.DataFrame, year: int, month: int):
    """Aggregate attendance into per-employee worked days and total hours in given month."""
    if df is None or df.empty:
        return pd.DataFrame()

    df_copy = df.copy()
    # parse datetimes safely
    df_copy['checkin_dt'] = pd.to_datetime(df_copy['checkin'], errors='coerce')
    df_copy['checkout_dt'] = pd.to_datetime(df_copy['checkout'], errors='coerce')

    # keep only records in given month
    df_copy['date'] = df_copy['checkin_dt'].dt.date
    df_copy = df_copy[df_copy['checkin_dt'].dt.year == year]
    df_copy = df_copy[df_copy['checkin_dt'].dt.month == month]

    if df_copy.empty:
        return pd.DataFrame()

    # compute duration per row (in hours)
    def duration_hours(row):
        ci = row['checkin_dt']
        co = row['checkout_dt']
        if pd.isna(ci) or pd.isna(co):
            return 0.0
        delta = co - ci
        hours = max(delta.total_seconds() / 3600.0, 0.0)
        return hours

    df_copy['hours'] = df_copy.apply(duration_hours, axis=1)

    # aggregate per id
    agg = df_copy.groupby(df_copy['id'].astype(str)).agg(
        worked_days=pd.NamedAgg(column='date', aggfunc=lambda x: x.nunique()),
        total_hours=pd.NamedAgg(column='hours', aggfunc='sum')
    ).reset_index()

    return agg


def get_base_salary_for_employee(emp: dict):
    """Return base monthly salary (VND) for employee dictionary from employees.json"""
    role = emp.get('position') or emp.get('role') or ''
    dept = emp.get('department') or ''
    if role in ROLE_SALARY_REF:
        return ROLE_SALARY_REF[role]
    # try fuzzy match by keywords
    for k, v in ROLE_SALARY_REF.items():
        if k.lower() in role.lower():
            return v
    # fallback to department default
    if dept in DEPT_DEFAULT:
        return DEPT_DEFAULT[dept]
    return 18000000  # generic default


def compute_payroll(year: int, month: int):
    """Compute payroll for the specified month/year.

    Returns a DataFrame with columns:
    id, name, department, position, base_salary, worked_days, working_days, total_hours,
    overtime_hours, overtime_pay, pro_rated_pay, total_pay
    """
    employees = load_employees()
    att = load_attendance_df()

    working_days = working_days_in_month(year, month)
    if working_days == 0:
        working_days = calendar.monthrange(year, month)[1]

    att_agg = parse_attendance_for_month(att, year, month)

    rows = []
    for emp in employees:
        emp_id = str(emp.get('id'))
        name = emp.get('name')
        dept = emp.get('department', '')
        pos = emp.get('position', '')
        base = get_base_salary_for_employee(emp)

        # find attendance
        rec = att_agg[att_agg['id'] == emp_id]
        if not rec.empty:
            worked_days = int(rec.iloc[0]['worked_days'])
            total_hours = float(rec.iloc[0]['total_hours'])
        else:
            worked_days = 0
            total_hours = 0.0

        # compute expected monthly hours (working days * standard hours)
        expected_hours = working_days * STANDARD_HOURS_PER_DAY
        # compute hourly rate
        hourly_rate = base / expected_hours if expected_hours > 0 else 0

        # Use hourly-based salary: regular pay = base * (regular_hours / expected_hours)
        # regular_hours = min(total_hours, expected_hours)
        regular_hours = min(total_hours, expected_hours)
        overtime_hours = max(0.0, total_hours - expected_hours)

        regular_pay = hourly_rate * regular_hours
        overtime_pay = overtime_hours * hourly_rate * OVERTIME_RATE

        total_pay = regular_pay + overtime_pay

        rows.append({
            'id': emp_id,
            'name': name,
            'department': dept,
            'position': pos,
            'base_salary': base,
            'worked_days': worked_days,
            'working_days': working_days,
            'total_hours': round(total_hours, 2),
            'regular_hours': round(regular_hours, 2),
            'overtime_hours': round(overtime_hours, 2),
            'regular_pay': int(round(regular_pay)),
            'overtime_pay': int(round(overtime_pay)),
            'total_pay': int(round(total_pay))
        })

    df = pd.DataFrame(rows)
    # sort by total_pay desc
    if not df.empty:
        df = df.sort_values('total_pay', ascending=False).reset_index(drop=True)
    return df


def export_payroll_to_excel(df: pd.DataFrame, output_file: str):
    """Export payroll DataFrame to Excel file."""
    if df is None or df.empty:
        raise ValueError('Empty payroll data')
    # basic export using pandas (kept for backward compatibility)
    df.to_excel(output_file, index=False, sheet_name='Payroll')
    return output_file


def export_payroll_to_excel_formatted(df: pd.DataFrame, output_file: str):
    """Export payroll to an Excel file with formatting (requires openpyxl).

    Adds a Summary sheet (total per department) and applies currency formatting
    and a totals row on the Payroll sheet.
    """
    if df is None or df.empty:
        raise ValueError('Empty payroll data')

    try:
        import openpyxl
        from openpyxl.utils import get_column_letter
        from openpyxl.styles import Font, Alignment, numbers
    except Exception as e:
        raise RuntimeError('openpyxl is required for formatted export: pip install openpyxl') from e

    # write dataframe to Excel
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Payroll')
        wb = writer.book
        ws = writer.sheets['Payroll']

        # header formatting
        header_font = Font(bold=True)
        for col_idx, col in enumerate(df.columns, 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center')
            # auto width attempt
            max_len = max(
                [len(str(col))] + [len(str(x)) for x in df[col].astype(str).values[:100]])
            ws.column_dimensions[get_column_letter(col_idx)].width = min(max_len + 4, 50)

        # number formatting for currency-like columns
        currency_cols = [c for c in ['base_salary', 'regular_pay', 'overtime_pay', 'total_pay'] if c in df.columns]
        col_index = {c: i + 1 for i, c in enumerate(df.columns)}
        for c in currency_cols:
            idx = col_index[c]
            for r in range(2, 2 + len(df)):
                cell = ws.cell(row=r, column=idx)
                try:
                    cell.value = int(cell.value)
                except Exception:
                    pass
                cell.number_format = '#,##0'

        # totals row
        total_row = 2 + len(df)
        ws.cell(row=total_row, column=1).value = 'Total'
        ws.cell(row=total_row, column=1).font = Font(bold=True)
        for c in currency_cols:
            idx = col_index[c]
            col_letter = get_column_letter(idx)
            sum_range = f"{col_letter}2:{col_letter}{1+len(df)}"
            ws.cell(row=total_row, column=idx).value = f"=SUM({sum_range})"
            ws.cell(row=total_row, column=idx).number_format = '#,##0'

        # Summary sheet: totals per department
        try:
            summary = df.groupby('department')['total_pay'].sum().reset_index()
            summary_sheet = wb.create_sheet('Summary')
            summary_sheet.append(['department', 'total_pay'])
            summary_sheet['A1'].font = Font(bold=True)
            summary_sheet['B1'].font = Font(bold=True)
            for _, row in summary.iterrows():
                summary_sheet.append([row['department'], int(row['total_pay'])])
            # format totals column
            for r in range(2, 2 + len(summary)):
                summary_sheet.cell(row=r, column=2).number_format = '#,##0'
            # overall total
            overall_row = 2 + len(summary)
            summary_sheet.cell(row=overall_row, column=1).value = 'Company Total'
            summary_sheet.cell(row=overall_row, column=1).font = Font(bold=True)
            summary_sheet.cell(row=overall_row, column=2).value = f"=SUM(B2:B{1+len(summary)})"
            summary_sheet.cell(row=overall_row, column=2).number_format = '#,##0'
        except Exception:
            # if grouping fails, skip summary
            pass

    return output_file


if __name__ == '__main__':
    # quick demo for current month
    today = date.today()
    df = compute_payroll(today.year, today.month)
    print(df.head())
