import streamlit as st
import api_service as api
import docx_handler as docx
import pandas as pd
import time
import io

# --- CONFIG & STYLE ---
st.set_page_config(page_title="Hệ thống Thẩm định Vật tư", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    .stProgress .st-bo { background-color: #00ff00; }
    .status-card { border: 1px solid #ddd; padding: 10px; border-radius: 10px; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR & AUTH ---
with st.sidebar:
    st.title("🛡️ Thẩm định v2.6")
    status = api.get_system_status()
    
    if status.get("status") == "loading":
        st.warning(status["message"])
    elif status.get("status") == "ready":
        st.success(status["message"])
    else:
        st.error(status.get("message", "Lỗi Server"))

    st.write("---")
    menu = st.radio("Chức năng", ["🔍 Tìm kiếm đơn lẻ", "📑 Thẩm định File Word", "⚙️ Quản trị hệ thống"])
    
    st.write("---")
    is_admin = False
    pwd = st.text_input("Mật khẩu Admin", type="password")
    if pwd == "admin123":
        is_admin = True
        st.info("🔓 Đã mở khóa quyền Admin")

# --- CHỨC NĂNG 1: TÌM KIẾM ĐƠN LẺ ---
if menu == "🔍 Tìm kiếm đơn lẻ":
    st.header("🔍 Thẩm định vật tư đơn lẻ")
    q = st.text_area("Nhập tên/thông số kỹ thuật:", placeholder="VD: Bulong neo M24x600 thép mạ kẽm...", height=100)
    
    if st.button("🚀 Thẩm định") and q:
        results = api.search_query(q)
        if isinstance(results, list):
            for i, res in enumerate(results):
                with st.expander(f"Top {i+1}: {res['ten']} (Khớp: {res['final_score']}%)"):
                    c1, c2 = st.columns(2)
                    c1.write(f"**Mã ERP:** `{res['erp']}`")
                    c1.write(f"**Hãng SX:** {res['hang']}")
                    c2.write(f"**ĐVT:** {res['dvt']}")
                    c2.write(f"**Thông số:** {res['ts']}")
                    st.progress(min(res['final_score']/100, 1.0))
        else:
            st.error(results.get("error", "Không tìm thấy dữ liệu"))

# --- CHỨC NĂNG 2: THẨM ĐỊNH FILE WORD ---
elif menu == "📑 Thẩm định File Word":
    st.header("📑 Thẩm định danh mục từ file Word")
    uploaded_word = st.file_uploader("Tải file .docx có chứa bảng", type=["docx"])
    
    if uploaded_word and st.button("🚀 Bắt đầu thẩm định hàng loạt"):
        word_data = docx.extract_table_from_docx(uploaded_word)
        if not word_data:
            st.error("Không tìm thấy dữ liệu bảng trong file.")
        else:
            final_report = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, item in enumerate(word_data):
                query = f"{item['ten']} {item['ts']}"
                res = api.search_query(query)
                
                best_match = res[0] if (isinstance(res, list) and len(res) > 0) else {}
                
                final_report.append({
                    "STT": item['stt'],
                    "Tên hàng (Word)": item['ten'],
                    "Thông số (Word)": item['ts'],
                    "ĐVT (Word)": item['dvt_word'],
                    "Hệ thống khớp nhất": best_match.get('ten', '❌ Không tìm thấy'),
                    "Mã ERP": best_match.get('erp', ''),
                    "Độ tin cậy": f"{best_match.get('final_score', 0)}%"
                })
                progress_bar.progress((i + 1) / len(word_data))
                status_text.text(f"Đang thẩm định dòng {i+1}/{len(word_data)}...")

            df_report = pd.DataFrame(final_report)
            st.dataframe(df_report)
            
            # Xuất Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_report.to_excel(writer, index=False, sheet_name='BaoCao')
            st.download_button("📥 Tải báo cáo kết quả (.xlsx)", output.getvalue(), "Bao_cao_tham_dinh.xlsx")

# --- CHỨC NĂNG 3: QUẢN TRỊ ---
elif menu == "⚙️ Quản trị hệ thống":
    if not is_admin:
        st.warning("Vui lòng nhập mật khẩu admin ở thanh bên để truy cập.")
    else:
        st.header("⚙️ Cập nhật Cơ sở dữ liệu")
        excel_file = st.file_uploader("Nạp file Excel danh mục gốc", type=["xlsx"])
        
        if excel_file and st.button("🔥 Xác nhận cập nhật"):
            response = api.upload_database(excel_file.getvalue(), excel_file.name, pwd)
            
            if "message" in response:
                st.info("Đang xử lý Backend. Vui lòng không tắt trình duyệt.")
                prog_bar = st.progress(0)
                prog_text = st.empty()
                
                while True:
                    p = api.get_build_progress()
                    prog_bar.progress(p['percent'] / 100)
                    prog_text.markdown(f"**Nhiệm vụ:** {p['task']}")
                    
                    if p['percent'] >= 100:
                        st.success("✅ Cập nhật dữ liệu thành công!")
                        break
                    if "Lỗi" in p['task']:
                        st.error(p['task'])
                        break
                    time.sleep(2)
            else:
                st.error(response.get("error", "Lỗi không xác định"))