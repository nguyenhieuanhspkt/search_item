from huggingface_hub import snapshot_download
import os

def download_cross_encoder():
    # Model Cross-Encoder này cực kỳ quan trọng để xếp hạng vật tư chính xác
    model_id = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    
    # Đường dẫn tuyệt đối Hiếu yêu cầu
    save_path = r"D:\TaskApp_kiet\TaskApp\search_item2\search_item\back_end\AI_models\cross-encoder"
    
    if not os.path.exists(save_path):
        print(f"--- 📥 Đang khởi tạo tải Cross-Encoder về máy nhà... ---")
        try:
            snapshot_download(
                repo_id=model_id,
                local_dir=save_path,
                local_dir_use_symlinks=False
            )
            print(f"--- ✅ THÀNH CÔNG! Model đã nằm tại: {save_path} ---")
        except Exception as e:
            print(f"--- ❌ Lỗi khi tải: {e} ---")
    else:
        print(f"--- ✨ Model đã có sẵn tại: {save_path} ---")

if __name__ == "__main__":
    download_cross_encoder()