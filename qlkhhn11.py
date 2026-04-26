import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="Điều Hành VPHN11", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #fdfaf5; color: #000000; }
    h1, h2, h3, p, label { color: #000000 !important; font-weight: bold; }
    /* Tăng cường hiển thị cho bảng chỉnh sửa */
    [data-testid="stDataEditor"] { border: 2px solid #d4a373; border-radius: 10px; }
    .stButton>button { background-color: #d4a373; color: black; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KẾT NỐI GOOGLE SHEETS (QUYỀN GHI) ---
def get_gspread_client():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        # Đảm bảo bạn có file credentials.json trong cùng thư mục
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        return gspread.authorize(creds)
    except:
        return None

# --- 3. CƠ SỞ DỮ LIỆU ---
SHEET_IDS = {
    "TỔNG HỢP VPHN11": "1TVpkHB2jcFmWuaBQF__IWhhd5z8UgmSdEn8X4YriyzY",
    "Nguyễn Văn Ánh": "1FGUNpLh2IGIjabg542-a6uMzHEL5KvopsurzzG_NzAs",
    "Nguyễn Văn Hiển": "1F4eaZAblHe39ewANHBkp5hIFZeE1VDVL9mnV1D6LguM",
    "Nguyễn Văn Quỳnh": "1J9wSztz6WmajEONksZu8ZmfVoCi1u9lGCrqrAadir1k",
    "Trần Ngọc Biên": "1K7LwuaCOAbvKutYpz-ixS74zssRQ903J7PLnrzrT36E",
    "Nguyễn Đoàn Quang Lực": "1i__Mh1IXmtjmGd3kWY1ZpDPpAGLq9bpZybmOxEYF8Fo"
}

# --- 4. GIAO DIỆN CHÍNH ---
if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    st.title("🔐 Đăng nhập Quản lý VPHN11")
    if st.text_input("Tài khoản") == "admin" and st.text_input("Mật khẩu", type="password") == "123456":
        if st.button("Đăng nhập"):
            st.session_state['auth'] = True
            st.rerun()
else:
    st.sidebar.title("🛠 ĐIỀU HÀNH")
    menu = st.sidebar.radio("Chức năng", ["📅 Lịch Tuần (Chỉnh sửa trực tiếp)", "💰 Công Nợ", "📦 Sản Phẩm"])

    if menu == "📅 Lịch Tuần (Chỉnh sửa trực tiếp)":
        st.title("📅 QUẢN LÝ & CẬP NHẬT LỊCH")
        
        # Lựa chọn
        view_type = st.radio("Phạm vi:", ["Tổng hợp Đơn vị", "Chi tiết Cán bộ"], horizontal=True)
        col1, col2 = st.columns(2)
        
        with col1:
            target_name = st.selectbox("👤 Chọn đối tượng:", list(SHEET_IDS.keys()) if view_type == "Chi tiết Cán bộ" else ["TỔNG HỢP VPHN11"])
            sheet_id = SHEET_IDS[target_name]
        with col2:
            week_no = st.number_input("📅 Tuần (1-53):", 1, 53, 17)

        st.divider()

        # Kết nối và Tải dữ liệu
        client = get_gspread_client()
        if client:
            try:
                sh = client.open_by_key(sheet_id)
                # Tìm tab theo tên "Tuan X" hoặc chọn tab đầu tiên
                worksheet = sh.get_worksheet(0) 
                data = worksheet.get_all_records()
                df = pd.DataFrame(data)

                st.subheader(f"📝 Bảng chỉnh sửa dữ liệu - {target_name}")
                st.info("💡 Bạn có thể nhấn trực tiếp vào ô để sửa nội dung. Sau đó nhấn 'LƯU CẬP NHẬT'.")

                # --- CẤU HÌNH ĐỘ RỘNG CỘT PHÙ HỢP ---
                edited_df = st.data_editor(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    num_rows="dynamic", # Cho phép thêm dòng mới
                    column_config={
                        "Ngày": st.column_config.TextColumn("📅 Ngày", width="small"),
                        "Cán bộ": st.column_config.TextColumn("👤 Cán bộ", width="medium"),
                        "Nội dung": st.column_config.TextColumn("📝 Nội dung công việc", width="large"),
                        "Kết quả": st.column_config.SelectboxColumn("📌 Kết quả", options=["Chưa làm", "Đang làm", "Hoàn thành"], width="small"),
                        "Ghi chú": st.column_config.TextColumn("ℹ️ Ghi chú", width="medium")
                    }
                )

                if st.button("🚀 LƯU CẬP NHẬT LÊN GOOGLE SHEET"):
                    with st.spinner("Đang đồng bộ dữ liệu..."):
                        # Xóa dữ liệu cũ và ghi đè dữ liệu mới từ edited_df
                        worksheet.update([edited_df.columns.values.tolist()] + edited_df.values.tolist())
                        st.success("✅ Đã cập nhật thành công lên Google Sheet!")
                        st.balloons()
            
            except Exception as e:
                st.error(f"Lỗi truy cập: {e}. Vui lòng kiểm tra quyền chia sẻ cho Email Service Account.")
        else:
            st.warning("⚠️ Thiếu tệp 'credentials.json'. Vui lòng thiết lập Google Service Account để sử dụng tính năng chỉnh sửa.")

# --- FOOTER ---
st.divider()
st.caption(f"Hệ thống VPHN11 v2026 - Chế độ chỉnh sửa trực tiếp")