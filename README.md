# 🎯 FaceAttendance - Hệ Thống Chấm Công Nhận Diện Khuôn Mặt

## 📋 Giới Thiệu

**FaceAttendance** là một hệ thống chấm công thông minh sử dụng công nghệ nhận diện khuôn mặt (Face Recognition) dựa trên Deep Learning. Hệ thống cho phép:

- ✅ Đăng ký nhân viên thông qua camera (thu thập 5 ảnh khuôn mặt)
- ✅ Check-in/Check-out tự động bằng khuôn mặt
- ✅ Quản lý nhân viên theo phòng ban và chức vụ
- ✅ Tính toán bảng lương tự động dựa trên giờ làm việc
- ✅ Xuất báo cáo chấm công và bảng lương ra Excel
- ✅ Giao diện đẹp mắt với CustomTkinter

---

## 🛠️ Công Nghệ Sử Dụng

### Ngôn ngữ & Framework

- **Python 3.8+** - Ngôn ngữ lập trình chính
- **CustomTkinter** - Giao diện người dùng hiện đại
- **OpenCV** - Xử lý hình ảnh và video
- **TensorFlow/Keras** - Deep Learning framework

### Thư viện AI/ML chính

- **MTCNN** - Phát hiện khuôn mặt (Face Detection)
- **FaceNet (keras-facenet)** - Trích xuất đặc trưng khuôn mặt (Face Embedding) 512 chiều
- **NumPy** - Tính toán Euclidean Distance để so khớp khuôn mặt

### Database & Storage

- **JSON** - Lưu trữ thông tin nhân viên và embedding
- **CSV** - Lưu trữ log chấm công
- **Pandas** - Xử lý và phân tích dữ liệu

### Visualization & Export

- **Matplotlib** - Biểu đồ thống kê
- **OpenPyXL** - Xuất báo cáo Excel

---

## 📁 Cấu Trúc Thư Mục

```
Machine/
│
├── main_menu.pyw                    # Màn hình chính (Entry point)
├── main_register_employee.py       # Module đăng ký nhân viên mới
├── main_login_employee.py          # Module đăng nhập admin
├── main_checkin_employee.py        # Module check-in
├── main_checkout_employee.py       # Module check-out
│
├── admin_panel.py                  # Dashboard quản lý admin
├── payroll.py                      # Module tính lương
├── utils.py                        # Các hàm tiện ích (embedding, attendance, auth)
├── face_engine.py                  # Khởi tạo MTCNN và FaceNet
│
├── requirements.txt                # Danh sách thư viện Python
├── admin.json                      # Thông tin đăng nhập admin (tự động tạo)
├── attendance_log.csv              # Log chấm công (tự động tạo)
│
├── embeddings/                     # Thư mục chứa dữ liệu nhân viên
│   └── employees.json              # Database nhân viên và face embeddings
│
├── assets/                         # Tài nguyên (logo, icon,...)
│   └── logo.jpg
│
└── __pycache__/                    # Python cache (tự động tạo)
```

### Giải thích các file chính:

| File                        | Chức năng                                                                   |
| --------------------------- | --------------------------------------------------------------------------- |
| `main_menu.pyw`             | Màn hình chính với 3 lựa chọn: Admin Login, Check-in, Check-out             |
| `main_register_employee.py` | Thu thập 5 ảnh khuôn mặt, tính embedding trung bình, lưu vào JSON           |
| `main_checkin_employee.py`  | Camera nhận diện khuôn mặt và ghi log check-in                              |
| `main_checkout_employee.py` | Camera nhận diện khuôn mặt và ghi log check-out                             |
| `admin_panel.py`            | Dashboard quản lý: xem log, thống kê, tính lương, quản lý nhân viên         |
| `utils.py`                  | Các hàm: get_embedding, recognize_face, mark_checkin/checkout, verify_admin |
| `face_engine.py`            | Singleton pattern để khởi tạo MTCNN detector và FaceNet embedder            |
| `payroll.py`                | Tính lương theo giờ làm việc, xử lý overtime, xuất Excel                    |

---

## 💻 Yêu Cầu Môi Trường

### Phần cứng

- **Camera/Webcam** (bắt buộc)
- **RAM**: Tối thiểu 4GB (khuyến nghị 8GB)
- **CPU**: Hỗ trợ AVX (Intel Core i3 trở lên)

### Phần mềm

- **Python**: 3.8 - 3.10 (khuyến nghị 3.9)
- **Windows 10/11**, macOS 10.15+, hoặc Ubuntu 20.04+

---

## 🚀 Hướng Dẫn Cài Đặt & Chạy

### Bước 1: Clone hoặc tải dự án

```bash
git clone <repository-url>
cd Machine
```

### Bước 2: Tạo môi trường ảo (khuyến nghị)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Bước 3: Cài đặt thư viện

```bash
pip install -r requirements.txt
```

**Lưu ý**:

- Nếu gặp lỗi với TensorFlow, cài đặt phiên bản cụ thể:
  ```bash
  pip install tensorflow==2.10.0
  ```
- Trên Windows, nếu lỗi OpenCV: `pip install opencv-python-headless`

### Bước 4: Chạy chương trình

```bash
# Windows
python main_menu.pyw

# macOS/Linux
python3 main_menu.pyw
```

### Bước 5: Đăng ký nhân viên mẫu

1. Từ màn hình chính, click **"Admin Login"**
2. Đăng nhập với tài khoản mặc định (xem phần dưới)
3. Click **"Register Employee"** để thêm nhân viên
4. Điền thông tin và chụp 5 ảnh khuôn mặt
5. Lưu nhân viên

### Bước 6: Thử check-in/check-out

1. Quay lại màn hình chính
2. Click **"Employee Check-in"** hoặc **"Employee Check-out"**
3. Đưa khuôn mặt vào camera
4. Hệ thống sẽ tự động nhận diện và ghi log

---

## 🔑 Tài Khoản Demo

### Admin (Quản lý hệ thống)

- **Username**: `admin`
- **Password**: `admin123`

**Quyền hạn**:

- ✅ Đăng ký nhân viên mới
- ✅ Xem/xuất log chấm công
- ✅ Quản lý danh sách nhân viên (sửa/xóa)
- ✅ Xem thống kê, biểu đồ
- ✅ Tính và xuất bảng lương

### Employee (Nhân viên)

- Không cần đăng nhập
- Sử dụng **khuôn mặt** để check-in/check-out
- Cần được admin đăng ký trước trong hệ thống

---

## 🎨 Kết Quả & Hình Ảnh Minh Họa

### 1. Màn hình chính (Main Menu)

![Main Menu](docs/screenshots/main_menu.png)

- Giao diện hiện đại với CustomTkinter
- 3 nút chính: Admin Login, Check-in, Check-out

### 2. Đăng ký nhân viên (Employee Registration)

![Employee Registration](docs/screenshots/registration.png)

- Form nhập thông tin: ID, Họ tên, Phòng ban, Chức vụ
- Camera hiển thị real-time với phát hiện khuôn mặt
- Yêu cầu thu thập 5 ảnh chất lượng cao (confidence > 0.95)
- Preview 5 ảnh đã chụp

### 3. Check-in/Check-out

![Check-in](docs/screenshots/checkin.png)

- Nhận diện khuôn mặt real-time
- Hiển thị tên, ID và độ tin cậy
- Chống spam: cooldown 10 giây giữa các lần check
- Yêu cầu 2 lần nhận diện liên tiếp để xác nhận

### 4. Admin Dashboard

![Admin Dashboard](docs/screenshots/admin_dashboard.png)

- **Cards tổng quan**: Tổng nhân viên, check-in, check-out, giờ làm trung bình
- **Biểu đồ**: Số lượng check-in theo ngày
- **Tabs**: Attendance Log, Payroll, Manage Employees

### 5. Bảng lương (Payroll)

![Payroll](docs/screenshots/payroll.png)

- Lọc theo tháng/năm
- Tính toán tự động:
  - Giờ regular (8h/ngày × số ngày làm việc)
  - Giờ overtime (× 1.5)
  - Lương theo phòng ban và chức vụ
- Xuất Excel với format đẹp (OpenPyXL)
- Biểu đồ: Top 10 lương cao nhất, tổng chi phí theo phòng ban

---

## 🧪 Cách Sử Dụng Chi Tiết

### Đăng ký nhân viên mới

1. Mở **Admin Panel** → Click **"Register Employee"**
2. Điền thông tin:
   - **Employee ID**: Mã nhân viên (duy nhất)
   - **Full Name**: Họ và tên
   - **Department**: Chọn phòng ban
   - **Role/Position**: Chọn chức vụ (tự động lọc theo phòng ban)
3. Đưa khuôn mặt vào camera:
   - Chờ khung màu xanh (chất lượng tốt)
   - Click **"Capture Face"** 5 lần
   - Thay đổi góc nhìn giữa các lần chụp (trái, phải, chính diện)
4. Click **"Save Employee"**

### Check-in

1. Màn hình chính → **"Employee Check-in"**
2. Đưa khuôn mặt vào camera
3. Chờ hệ thống nhận diện (2-3 giây)
4. Thông báo **"CHECKED IN"** màu xanh = thành công
5. Nếu đã check-in rồi: **"ALREADY CHECKED IN"** màu cam

### Check-out

1. Màn hình chính → **"Employee Check-out"**
2. Đưa khuôn mặt vào camera
3. Hệ thống kiểm tra đã check-in hôm nay chưa
4. Thông báo **"CHECKED OUT"** màu vàng = thành công
5. Nếu chưa check-in: **"NO CHECK-IN TODAY"** màu cam

### Xem log chấm công

1. **Admin Panel** → **"View Attendance Log"**
2. Bảng hiển thị: ID, Name, Department, Position, Check-in, Check-out
3. Có thể scroll xem toàn bộ lịch sử

### Tính bảng lương

1. **Admin Panel** → **"Bảng lương"**
2. Chọn tháng/năm → Click **"Apply"**
3. Hệ thống tự động:
   - Đếm số ngày làm việc (thứ 2 - thứ 6)
   - Tính tổng giờ làm từ log check-in/out
   - Tính overtime (> 8h/ngày × số ngày làm)
   - Nhân với mức lương theo chức vụ
4. Click **"Export Excel"** để xuất file `.xlsx`

### Quản lý nhân viên

1. **Admin Panel** → **"Manage Employees"**
2. Tìm kiếm theo tên/ID hoặc lọc theo phòng ban
3. Chọn nhân viên → Click:
   - **"Edit Selected"**: Sửa tên, phòng ban, chức vụ
   - **"Delete Selected"**: Xóa (có backup tự động)
4. **"Restore Backup"**: Khôi phục từ bản sao lưu cuối

---

## 🔬 Chi Tiết Kỹ Thuật

### Quy trình nhận diện khuôn mặt

```
1. Camera Frame (640×480)
       ↓
2. MTCNN Detector → Phát hiện khuôn mặt (bounding box)
       ↓
3. Kiểm tra chất lượng:
   - Kích thước ≥ 80×80 px
   - Confidence ≥ 0.95
       ↓
4. Crop & Resize → 160×160 px (chuẩn FaceNet)
       ↓
5. FaceNet Embedder → Vector 512 chiều
       ↓
6. So sánh Euclidean Distance với database
       ↓
7. Nếu distance < 0.7 → Nhận diện thành công
```

### Thuật toán so khớp khuôn mặt

```python
def recognize_face(embedding, users, threshold=0.7):
    min_dist = float('inf')
    matched_user = None

    for user in users:
        known_emb = np.array(user["embedding"])
        dist = np.linalg.norm(embedding - known_emb)  # Euclidean Distance

        if dist < min_dist:
            min_dist = dist
            matched_user = user

    if min_dist < threshold:
        return matched_user, min_dist
    return None, min_dist
```

### Cách tính lương

**Công thức**:

```
Lương cơ bản (theo chức vụ)
    ↓
Số giờ chuẩn = Số ngày làm việc trong tháng × 8h
    ↓
Tổng giờ làm thực tế (từ log check-in/out)
    ↓
- Giờ regular = min(Tổng giờ, Giờ chuẩn)
- Giờ overtime = max(0, Tổng giờ - Giờ chuẩn)
    ↓
Lương regular = (Giờ regular / Giờ chuẩn) × Lương cơ bản
Lương overtime = Giờ overtime × (Lương cơ bản / Giờ chuẩn) × 1.5
    ↓
Tổng lương = Lương regular + Lương overtime
```

**Ví dụ**:

- Lương cơ bản Backend Dev: 18,400,000 VND/tháng
- Tháng 12/2024: 22 ngày làm việc → 176 giờ chuẩn
- Nhân viên A làm: 20 ngày, tổng 168 giờ
  - Regular: 168h
  - Overtime: 0h
  - Lương = 18,400,000 × (168/176) ≈ 17,563,636 VND

---

## 📊 Dữ Liệu Mẫu

### File `embeddings/employees.json`:

```json
[
  {
    "id": "EMP001",
    "name": "Nguyễn Văn A",
    "department": "Engineering / Development",
    "position": "Backend Developer",
    "embedding": [0.123, -0.456, ..., 0.789],  // 512 số
    "registered_date": "2024-12-01 10:30:00"
  }
]
```

### File `attendance_log.csv`:

```csv
id,name,department,position,checkin,checkout
EMP001,Nguyễn Văn A,Engineering / Development,Backend Developer,2024-12-04 08:30:00,2024-12-04 17:45:00
```

---

## ⚙️ Cấu Hình & Tùy Chỉnh

### Thay đổi threshold nhận diện

File: `main_checkin_employee.py` và `main_checkout_employee.py`

```python
THRESHOLD = 0.7  # Giảm = dễ nhận diện hơn (có thể nhận nhầm)
                # Tăng = khắt khe hơn (khó nhận diện)
```

### Thay đổi mức lương

File: `payroll.py`

```python
ROLE_SALARY_REF = {
    "Backend Developer": 18400000,  # Sửa ở đây
    "Frontend Developer": 18400000,
    # ...
}
```

### Thay đổi mật khẩu admin

```python
# Chạy trong Python console:
from utils import change_admin_password
change_admin_password("admin123", "new_password_123")
```

---

## 🐛 Xử Lý Lỗi Thường Gặp

### 1. Lỗi: "Cannot open camera"

**Nguyên nhân**: Camera đang được sử dụng bởi ứng dụng khác
**Giải pháp**:

- Tắt Zoom, Teams, Skype
- Kiểm tra camera trong Device Manager (Windows)
- Thử `cap = cv2.VideoCapture(1)` nếu có nhiều camera

### 2. Lỗi: "Failed to load FaceNet model"

**Nguyên nhân**: Thiếu hoặc lỗi TensorFlow
**Giải pháp**:

```bash
pip uninstall tensorflow
pip install tensorflow==2.10.0
```

### 3. Lỗi: "Employee ID already exists"

**Nguyên nhân**: ID bị trùng
**Giải pháp**: Sử dụng ID khác hoặc xóa nhân viên cũ

### 4. Nhận diện sai người

**Nguyên nhân**:

- Ánh sáng kém
- Góc chụp không tốt
- Threshold quá thấp
  **Giải pháp**:
- Đăng ký lại với 5 ảnh chất lượng cao
- Tăng THRESHOLD lên 0.6 hoặc 0.65

### 5. Bảng lương sai

**Nguyên nhân**: Nhân viên quên check-out
**Giải pháp**: Admin sửa trực tiếp file `attendance_log.csv`

---

## 📦 Cấu Trúc Database

### employees.json (NoSQL)

```
{
  "id": string (unique),
  "name": string,
  "department": string,
  "position": string,
  "embedding": array[512] (float),
  "registered_date": string (ISO datetime)
}
```

### attendance_log.csv

| Cột          | Kiểu     | Mô tả                                    |
| ------------ | -------- | ---------------------------------------- |
| `id`         | string   | Mã nhân viên                             |
| `name`       | string   | Họ tên                                   |
| `department` | string   | Phòng ban                                |
| `position`   | string   | Chức vụ                                  |
| `checkin`    | datetime | Thời gian check-in (YYYY-MM-DD HH:MM:SS) |
| `checkout`   | datetime | Thời gian check-out (có thể rỗng)        |

---

## 🔐 Bảo Mật

### Các biện pháp đã triển khai:

- ✅ Mật khẩu admin được hash SHA-256 (không lưu plaintext)
- ✅ Backup tự động trước khi xóa/sửa
- ✅ Audit log ghi lại hành động admin
- ✅ Cooldown 10s chống spam check-in/out
- ✅ Yêu cầu 2 lần nhận diện liên tiếp để xác nhận

---

## 🤝 Đóng Góp & Phát Triển

### Các tính năng có thể mở rộng:

- [ ] Gửi email thông báo check-in muộn
- [ ] API REST để tích hợp với hệ thống khác
- [ ] Mobile app (Flutter/React Native)
- [ ] Nhận diện nhiều khuôn mặt đồng thời
- [ ] Anti-spoofing (chống ảnh/video giả mạo)
- [ ] Tích hợp với thiết bị kiểm soát cửa (access control)

## 📄 Giấy Phép (License)

Dự án này được phát triển cho mục đích học tập và nghiên cứu.

**Thư viện bên thứ ba**:

- MTCNN: [MIT License](https://github.com/ipazc/mtcnn)
- FaceNet: [MIT License](https://github.com/nyoki-mtl/keras-facenet)
- CustomTkinter: [MIT License](https://github.com/TomSchimansky/CustomTkinter)

---

## 📚 Tài Liệu Tham Khảo

1. **FaceNet Paper**: [Schroff et al., 2015 - FaceNet: A Unified Embedding for Face Recognition and Clustering](https://arxiv.org/abs/1503.03832)
2. **MTCNN Paper**: [Zhang et al., 2016 - Joint Face Detection and Alignment using Multi-task Cascaded Convolutional Networks](https://arxiv.org/abs/1604.02878)
3. **OpenCV Documentation**: [https://docs.opencv.org/](https://docs.opencv.org/)
4. **CustomTkinter Docs**: [https://customtkinter.tomschimansky.com/](https://customtkinter.tomschimansky.com/)
