import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os

# --- 1. CẤU HÌNH HỆ THỐNG & GIAO DIỆN ---
st.set_page_config(page_title="Điều Hành VPHN11", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #fdfaf5; color: #000000; }
    h1, h2, h3, p, label { color: #000000 !important; font-weight: bold; }
    [data-testid="stDataEditor"] { border: 2px solid #d4a373; border-radius: 10px; background-color: white; }
    .stButton>button { 
        background-color: #d4a373; 
        color: black; 
        font-weight: bold; 
        border-radius: 8px;
        width: 100%;
        border: none;
        padding: 10px;
    }
    .stButton>button:hover { border: 1px solid black; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HÀM KẾT NỐI GOOGLE API (ƯU TIÊN GITHUB SECRETS) ---
def get_gspread_client():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # Thử lấy cấu hình từ GitHub Secrets / Streamlit Cloud Secrets
        creds_json = os.environ.get("GCP_SERVICE_ACCOUNT_JSON")
        
        if creds_json:
            # Nếu chạy trên Server (GitHub/Streamlit Cloud)
            creds_info = json.loads(creds_json)
        elif os.path.exists("credentials.json"):
            # Nếu chạy local trên máy tính
            with open("credentials.json") as f:
                creds_info = json.load(f)
        else:
            return None
            
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Lỗi hệ thống kết nối: {e}")
        return None

# --- 3. DANH SÁCH SHEET ID ---
SHEET_IDS = {
    "TỔNG HỢP VPHN11": "1TVpkHB2jcFmWuaBQF__IWhhd5z8UgmSdEn8X4YriyzY",
    "Nguyễn Văn Ánh": "1FGUNpLh2IGIjabg542-a6uMzHEL5KvopsurzzG_NzAs",
    "Nguyễn Văn Hiển": "1F4eaZAblHe39ewANHBkp5hIFZeE1VDVL9mnV1D6LguM",
    "Nguyễn Văn Quỳnh": "1J9wSztz6WmajEONksZu8ZmfVoCi1u9lGCrqrAadir1k",
    "Trần Ngọc Biên": "1K7LwuaCOAbvKutYpz-ixS74zssRQ903J7PLnrzrT36E",
    "Nguyễn Đoàn Quang Lực": "1i__Mh1IXmtjmGd3kWY1ZpDPpAGLq9bpZybmOxEYF8Fo"
}

# Hàm tạo khung lịch mặc định
def create_default_df():
    return pd.DataFrame({
        "Thứ": ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7"],
        "Nội dung công việc": [""] * 6,
        "Kết quả": ["Chưa làm"] * 6,
        "Ghi chú": [""] * 6
    })

# --- 4. XỬ LÝ GIAO DIỆN ---
if 'auth' not in st.session_state:
    st.session_state['auth'] = False

if not st.session_state['auth']:
    # Màn hình đăng nhập
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        st.title("🔐 ĐĂNG NHẬP HỆ THỐNG")
        user = st.text_input("Tài khoản admin")
        pwd = st.text_input("Mật khẩu", type="password")
        if st.button("Đăng nhập"):
            if user == "admin" and pwd == "123456":
                st.session_state['auth'] = True
                st.rerun()
            else:
                st.error("Thông tin đăng nhập không chính xác!")
else:
    # Sidebar điều hướng
    st.sidebar.title("🛠 ĐIỀU HÀNH")
    
    # NÚT KIỂM TRA CẬP NHẬT (Theo yêu cầu)
    st.sidebar.link_button("🚀 Kiểm tra cập nhật", "https://github.com/your-username/your-repo", use_container_width=True)
    
    menu = st.sidebar.radio("Chức năng chính", ["📅 Lịch Tuần (T2-T7)", "💰 Công Nợ", "📦 Sản Phẩm"])
    
    if st.sidebar.button("Đăng xuất"):
        st.session_state['auth'] = False
        st.rerun()

    if menu == "📅 Lịch Tuần (T2-T7)":
        st.title("📅 QUẢN LÝ LỊCH CÔNG TÁC")
        
        # Bộ lọc
        c1, c2 = st.columns(2)
        with c1:
            target = st.selectbox("👤 Chọn Cán bộ/Đơn vị:", list(SHEET_IDS.keys()))
        with c2:
            week = st.number_input("📅 Tuần thứ (1-53):", 1, 53, 17)
            
        st.divider()

        client = get_gspread_client()
        if client:
            try:
                # Mở Sheet
                sh = client.open_by_key(SHEET_IDS[target])
                worksheet = sh.get_worksheet(0)
                data = worksheet.get_all_records()
                
                # Chuyển đổi dữ liệu
                if not data:
                    df = create_default_df()
                else:
                    df = pd.DataFrame(data)

                st.subheader(f"📝 Bảng chỉnh sửa: {target}")
                st.info("Nhấp đúp vào ô để sửa. Dữ liệu từ Thứ 2 đến Thứ 7.")

                # Trình chỉnh sửa dữ liệu
                edited_df = st.data_editor(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    num_rows="dynamic",
                    column_config={
                        "Thứ": st.column_config.SelectboxColumn("Thứ", options=["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"], width="small"),
                        "Nội dung công việc": st.column_config.TextColumn("Nội dung công việc", width="large"),
                        "Kết quả": st.column_config.SelectboxColumn("Kết quả", options=["Chưa làm", "Đang làm", "Hoàn thành"], width="medium"),
                        "Ghi chú": st.column_config.TextColumn("Ghi chú", width="medium")
                    }
                )

                # Nút lưu
                if st.button("💾 LƯU CẬP NHẬT LÊN GOOGLE SHEETS"):
                    with st.spinner("Đang đồng bộ dữ liệu..."):
                        # Xóa và ghi lại toàn bộ để đảm bảo đồng bộ
                        worksheet.clear()
                        # Ghi tiêu đề và nội dung
                        worksheet.update([edited_df.columns.values.tolist()] + edited_df.fillna("").values.tolist())
                        st.success(f"✅ Đã cập nhật thành công lịch của {target}!")
                        st.balloons()

            except Exception as e:
                st.error(f"❌ Không thể kết nối tới Google Sheet. Hãy kiểm tra ID Sheet hoặc quyền chia sẻ Editor cho Service Account. Chi tiết: {e}")
        else:
            st.warning("⚠️ Hệ thống chưa được kết nối với Google API qua GitHub Secrets (GCP_SERVICE_ACCOUNT_JSON).")

# --- 5. FOOTER ---
st.divider()
st.caption(f"Hệ thống VPHN11 v2026 - Kết nối trực tuyến GitHub & Google Sheet")
