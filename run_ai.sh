#!/bin/bash
echo "--- Đang khởi động AI FaceID Server ---"
# Gọi trực tiếp Python trong venv để bỏ qua bước activate thủ công
./venv/bin/python3 ai_server.py
