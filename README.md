Cách dùng
```bash
pip install
cd scripts
python docx2lawjsonl.py "Luật Giao thông đường bộ 2025.docx" traffic_law_2025.jsonl
```

Kiểm tra nhanh
```bash
head -n 1 traffic_law_2025.jsonl | python -m json.tool
```

Bạn sẽ thấy dạng:
JSON
```bash
{
  "id": "Điều 1",
  "text": "Điều 1. Phạm vi điều chỉnh... (đã được làm sạch)"
}
```
