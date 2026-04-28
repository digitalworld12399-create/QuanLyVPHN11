import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="Điều Hành VPHN11", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #fdfaf5; color: #000000; }
    h1, h2, h3, p, label { color: #000000 !important; font-weight: bold; }
    [data-testid="stDataEditor"] { border: 2px solid #d4a373; border-radius: 10px; }
    .stButton>button { background-color: #d4a373; color: black; font-weight: bold; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KẾT NỐI GOOGLE SHEETS (HỖ TRỢ GITHUB SECRETS) ---
def get_gspread_client():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # Kiểm tra xem đang chạy local hay trên Streamlit Cloud/Github
        if "GCP_SERVICE_ACCOUNT_JSON" in os.environ:
            # Lấy từ GitHub Secrets/Streamlit Cloud Secrets
            creds_info = json.loads(os.environ.get("GCP_SERVICE_ACCOUNT_JSON"))
        elif os.path.exists("credentials.json"):
            # Lấy từ tệp local nếu có
            with open("credentials.json") as f:
                creds_info = json.load(f)
        else:
            return None
            
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Lỗi cấu hình xác thực: {e}")
        return None

# --- 3. CƠ SỞ DỮ LIỆU & CẤU TRÚC LỊCH ---
SHEET_IDS = {
    "TỔNG HỢP VPHN11": "1TVpkHB2jcFmWuaBQF__IWhhd5z8UgmSdEn8X4YriyzY",
    "Nguyễn Văn Ánh": "1FGUNpLh2IGIjabg542-a6uMzHEL5KvopsurzzG_NzAs",
    "Nguyễn Văn Hiển": "1F4eaZAblHe39ewANHBkp5hIFZeE1VDVL9mnV1D6LguM",
    "Nguyễn Văn Quỳnh": "1J9wSztz6WmajEONksZu8ZmfVoCi1u9lGCrqrAadir1k",
    "Trần Ngọc Biên": "1K7LwuaCOAbvKutYpz-ixS74zssRQ903J7PLnrzrT36E",
    "Nguyễn Đoàn Quang Lực": "1i__Mh1IXmtjmGd3kWY1ZpDPpAGLq9bpZybmOxEYF8Fo"
}

# Hàm tạo DataFrame trống từ T2 - T7 nếu Sheet chưa có dữ liệu
def create_default_schedule():
    days = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7"]
    return pd.DataFrame({
        "Thứ": days,
        "Nội dung công việc": [""] * 6,
        "Cán bộ phụ trách": [""] * 6,
        "Kết quả": ["Chưa làm"] * 6,
        "Ghi chú": [""] * 6
    })

# --- 4. GIAO DIỆN CHÍNH ---
if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    st.title("🔐 Đăng nhập Quản lý VPHN11")
    user = st.text_input("Tài khoản")
    pwd = st.text_input("Mật khẩu", type="password")
    if st.button("Đăng nhập"):
        if user == "admin" and pwd == "123456":
            st.session_state['auth'] = True
            st.rerun()
        else:
            st.error("Sai tài khoản hoặc mật khẩu")
else:
    # Nút Kiểm tra cập nhật (Theo yêu cầu trước đó của bạn)
    st.sidebar.link_button("🔄 Kiểm tra cập nhật", "https://github.com/your-repo-link", use_container_width=True)
    
    st.sidebar.title("🛠 ĐIỀU HÀNH")
    menu = st.sidebar.radio("Chức năng", ["📅 Lịch Tuần (T2-T7)", "💰 Công Nợ", "📦 Sản Phẩm"])

    if menu == "📅 Lịch Tuần (T2-T7)":
        st.title("📅 QUẢN LÝ LỊCH CÔNG TÁC TUẦN")
        
        col1, col2 = st.columns(2)
        with col1:
            target_name = st.selectbox("👤 Chọn đối tượng:", list(SHEET_IDS.keys()))
            sheet_id = SHEET_IDS[target_name]
        with col2:
            week_no = st.number_input("📅 Tuần thứ:", 1, 53, 17)

        client = get_gspread_client()
        if client:
            try:
                sh = client.open_by_key(sheet_id)
                worksheet = sh.get_worksheet(0) 
                data = worksheet.get_all_records()
                
                if not data:
                    df = create_default_schedule()
                else:
                    df = pd.DataFrame(data)

                st.subheader(f"📝 Chỉnh sửa lịch: {target_name} (Tuần {week_no})")
                
                edited_df = st.data_editor(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    num_rows="dynamic",
                    column_config={
                        "Thứ": st.column_config.SelectboxColumn("📅 Thứ", options=["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"], width="small"),
                        "Nội dung công việc": st.column_config.TextColumn("📝 Nội dung", width="large"),
                        "Kết quả": st.column_config.SelectboxColumn("📌 Trạng thái", options=["Chưa làm", "Đang làm", "Hoàn thành"], width="small"),
                    }
                )

                if st.button("🚀 LƯU DỮ LIỆU LÊN HỆ THỐNG"):
                    with st.spinner("Đang đồng bộ..."):
                        # Cập nhật lại toàn bộ bảng
                        worksheet.clear()
                        worksheet.update([edited_df.columns.values.tolist()] + edited_df.fillna("").values.tolist())
                        st.success("✅ Đã cập nhật thành công!")
                        st.balloons()
            
            except Exception as e:
                st.error(f"Lỗi: {e}. Kiểm tra lại ID Sheet hoặc quyền truy cập của Service Account.")
        else:
            st.warning("⚠️ Hệ thống chưa được kết nối với Google API qua GitHub Secrets.")

# --- FOOTER ---
st.divider()
st.caption(f"Hệ thống VPHN11 v2026 - Kết nối trực tuyến GitHub & Google Sheet")
