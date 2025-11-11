# docx2lawjsonl.py
import re, json, sys
from docx import Document
from tqdm import tqdm

# 1. Đọc toàn bộ đoạn văn trong file .docx
def iter_block_items(parent):
    """Yield each paragraph/table in order."""
    from docx.document import Document as _Document
    from docx.table import _Cell, Table
    from docx.text.paragraph import Paragraph
    if isinstance(parent, _Document):
        parent_elm = parent.element.body
    elif isinstance(parent, _Cell):
        parent_elm = parent._tc
    else:
        raise ValueError
    for child in parent_elm.iterchildren():
        if child.tag.endswith('p'):
            yield Paragraph(child, parent)
        elif child.tag.endswith('tbl'):
            tbl = Table(child, parent)
            for row in tbl.rows:
                for cell in row.cells:
                    yield from iter_block_items(cell)

def docx_to_raw_text(path: str) -> str:
    doc = Document(path)
    pieces = []
    for block in iter_block_items(doc):
        if hasattr(block, 'text'):
            t = block.text.strip()
            if t:
                pieces.append(t)
    return '\n'.join(pieces)

# 2. Tách thành từng điều
RE_DIEU = re.compile(r'^\s*(Điều\s+\d+([a-zđ]*))\.?\s*(.+)', re.I | re.UNICODE)

def split_into_articles(raw: str):
    """Trả về list[(id, title+body)]"""
    lines = raw.splitlines()
    articles, cur_id, cur_buf = [], None, []
    for ln in lines:
        m = RE_DIEU.match(ln)
        if m:                                   # gặp điều mới
            if cur_id:                          # lưu điều cũ
                articles.append((cur_id, ' '.join(cur_buf)))
            cur_id = m.group(1).strip()
            cur_buf = [ln[m.end():].strip()]    # phần còn lại của dòng
        else:
            if cur_id:                          # đang trong 1 điều
                cur_buf.append(ln.strip())
    if cur_id:
        articles.append((cur_id, ' '.join(cur_buf)))
    return articles

# 3. Làm sạch nhẹ
def clean(text: str) -> str:
    # xóa dấu gạch đầu dòng thừa, space thừa
    text = re.sub(r'[\s–—-]+', ' ', text)
    return text.strip()

# 4. Chạy
if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python docx2lawjsonl.py input.docx output.jsonl')
        sys.exit(1)
    infile, outfile = sys.argv[1], sys.argv[2]

    print('Reading DOCX...')
    raw = docx_to_raw_text(infile)

    print('Splitting articles...')
    arts = split_into_articles(raw)

    print('Writing JSONL...')
    with open(outfile, 'w', encoding='utf-8') as f:
        for idx, (aid, body) in tqdm(enumerate(arts, 1), total=len(arts)):
            rec = {"id": aid, "text": clean(body)}
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')
    print(f'Done! {len(arts)} articles → {outfile}')
