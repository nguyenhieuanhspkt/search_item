import pandas as pd
import os

def process_and_audit(input_file):
    try:
        if not os.path.exists(input_file):
            print(f"❌ Không tìm thấy file: {input_file}")
            return

        # 1. Đọc dữ liệu
        df = pd.read_excel(input_file)
        all_cols = df.columns.tolist()
        col_b = all_cols[1]  # Tên cột B
        col_d = all_cols[3]  # Tên cột D (Sum)
        col_g = all_cols[6]  # Tên cột G (Sum)

        # 2. Làm sạch dữ liệu cột B để đảm bảo gộp chính xác
        # Xóa khoảng trắng thừa và chuyển về chữ hoa để tránh sai lệch do Unicodes
        df[col_b] = df[col_b].astype(str).str.strip()

        # 3. Tạo BẢNG KIỂM TRA (Audit Table)
        # Đếm xem mỗi giá trị ở cột B xuất hiện bao nhiêu lần trước khi gộp
        audit_df = df.groupby(col_b).size().reset_index(name='Số lần xuất hiện (Số dòng gốc)')
        # Chỉ lấy những cái tên nào có xuất hiện từ 2 lần trở lên để bạn dễ kiểm tra
        audit_df = audit_df[audit_df['Số lần xuất hiện (Số dòng gốc)'] > 1].sort_values(by='Số lần xuất hiện (Số dòng gốc)', ascending=False)

        # 4. Thực hiện GỘP DỮ LIỆU chính thức
        agg_dict = {col: 'first' for col in all_cols if col != col_b}
        agg_dict[col_d] = 'sum'
        agg_dict[col_g] = 'sum'
        
        df_result = df.groupby(col_b, as_index=False).agg(agg_dict)
        df_result = df_result[all_cols] # Giữ đúng thứ tự cột A, B, C...

        # 5. Xuất file
        summary_file = "Ket_Qua_Tong_Hop_Cuoi_Cung.xlsx"
        audit_file = "Bang_Kiem_Tra_Gop.xlsx"
        
        df_result.to_excel(summary_file, index=False)
        audit_df.to_excel(audit_file, index=False)

        print(f"--- BÁO CÁO HOÀN THÀNH ---")
        print(f"✅ File tổng hợp: {summary_file}")
        print(f"🔍 File kiểm tra: {audit_file}")
        print(f"📊 Tổng số nhóm (dòng duy nhất): {len(df_result)}")
        print(f"⚠️ Số mã hàng bị trùng đã được gộp: {len(audit_df)}")
        
        if len(audit_df) > 0:
            print("\nTop 5 mặt hàng được gộp nhiều nhất:")
            print(audit_df.head())
        else:
            print("\n💡 Không tìm thấy dòng nào trùng lặp ở cột B để gộp.")

    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    process_and_audit("Ket_Qua_Cuoi_Cung_Chuan.xlsx")