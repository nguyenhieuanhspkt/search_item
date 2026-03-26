import gc
import ctypes

def clean_ram():
    print("Đang tiến hành dọn dẹp RAM...")
    
    # 1. Thu gom rác (Garbage Collector)
    # Giải phóng các đối tượng không còn tham chiếu trong Python
    collected = gc.collect()
    print(f"Đã dọn dẹp {collected} vật thể dư thừa.")

    # 2. Giải phóng bộ nhớ đệm thư viện C (Dành cho Windows)
    try:
        ctypes.windll.psapi.EmptyWorkingSet(ctypes.windll.kernel32.GetCurrentProcess())
        print("Đã tối ưu hóa Working Set của ứng dụng.")
    except Exception as e:
        print(f"Không thể tối ưu hóa bộ nhớ hệ thống: {e}")

if __name__ == "__main__":
    clean_ram()