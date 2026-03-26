import os
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime

# ============================================================
# 1. THIẾT LẬP ĐƯỜNG DẪN (PATH SETUP)
# ============================================================
current_file = Path(__file__).resolve()

# AI_SYSTEM_DIR: folder 'ai_audit_system' (chứa pipeline.py)
AI_SYSTEM_DIR = current_file.parent 
# PROJECT_ROOT: lùi 4 tầng về 'TaskApp' (Dựa trên cấu trúc folder của Hiếu)
PROJECT_ROOT = current_file.parent 
print(f"📍 Root dự án: {AI_SYSTEM_DIR}")