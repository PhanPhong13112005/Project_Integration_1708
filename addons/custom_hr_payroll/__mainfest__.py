{
    'name': 'Hệ thống Quản lý Chấm công và Tính lương Tự động',
    'version': '15.0.1.0.0',
    'summary': 'Kết nối hồ sơ nhân sự và dữ liệu công thực tế để tính lương, bảo hiểm tự động.',
    'description': """
        Mô tả chi tiết đề tài 2:
        - Quản lý hồ sơ nhân sự tập trung[cite: 7].
        - Tự động hóa tính lương dựa trên dữ liệu chấm công thực tế.
        - Tích hợp quy tắc tính lương, bảo hiểm và thuế.
    """,
    'author': 'Tên của bạn / Nhóm của bạn',
    'website': 'https://github.com/FIT-DNU/Business-Internship', # Link nguồn tham khảo 
    'category': 'Human Resources',
    'license': 'LGPL-3',
    
    # Các module bắt buộc phải cài đặt trước (Dependencies)
    'depends': [
        'base', 
        'hr',               # Module Quản lý nhân sự (bắt buộc kết hợp) 
        'hr_attendance',    # Module Chấm công 
        'hr_payroll',       # Module Tính lương 
        'hr_contract',      # Để lấy thông tin mức lương trong hợp đồng
    ],

    # Các file giao diện và cấu hình (Sẽ tạo ở các bước sau)
    'data': [
        'security/ir.model.access.csv',
        'views/hr_payroll_views.xml',
        'views/hr_attendance_views.xml',
        'data/salary_rule_data.xml', # Nơi định nghĩa công thức tính lương
    ],
    
    'installable': True,
    'application': True,
    'auto_install': False,
}