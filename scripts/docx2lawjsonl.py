# docx2clausejsonl.py
import re, json, sys, os
from docx import Document
from tqdm import tqdm

# ---------- 1. đọc DOCX ----------
def iter_block_items(parent):
    from docx.document import Document as _Document
    from docx.table import _Cell, Table
    from docx.text.paragraph import Paragraph
    parent_elm = parent.element.body if isinstance(parent, _Document) else parent._tc
    for child in parent_elm.iterchildren():
        if child.tag.endswith('p'):
            yield Paragraph(child, parent)
        elif child.tag.endswith('tbl'):
            from docx.table import Table
            tbl = Table(child, parent)
            for row in tbl.rows:
                for cell in row.cells:
                    yield from iter_block_items(cell)

def docx_to_raw_text(path: str) -> str:
    doc = Document(path)
    pieces = [p.text.strip() for p in iter_block_items(doc) if p.text.strip()]
    return '\n'.join(pieces)

# ---------- 2. tách Điều ----------
RE_DIEU = re.compile(r'^\s*(Điều\s+\d+[a-zđ]*)\.?', re.I | re.UNICODE)

def split_articles(raw: str):
    lines = raw.splitlines()
    arts, cur_id, buf = [], None, []
    for ln in lines:
        m = RE_DIEU.match(ln)
        if m:
            if cur_id:
                arts.append((cur_id, ' '.join(buf)))
            cur_id, buf = m.group(1), [ln[m.end():].strip()]
        else:
            if cur_id:
                buf.append(ln.strip())
    if cur_id:
        arts.append((cur_id, ' '.join(buf)))
    return arts

# ---------- 3. tách Khoản ----------
# mẫu 1., 2., 3. ... hoặc a), b), c) ...
RE_KHOAN_NUM = re.compile(r'\s(\d+)\.\s')
RE_KHOAN_ABC  = re.compile(r'\s([a-zđ])\)\s')

def split_clauses(article_id: str, text: str):
    """Trả về list[(clause_id, clause_text)]"""
    # thử chia theo dạng số trước
    segs = RE_KHOAN_NUM.split(text)
    if len(segs) > 1:   # có chia được
        clauses = []
        for i in range(1, len(segs), 2):
            clauses.append((segs[i], segs[i+1].strip()))
        return clauses
    # nếu không chia theo chữ cái
    segs = RE_KHOAN_ABC.split(text)
    if len(segs) > 1:
        clauses = []
        for i in range(1, len(segs), 2):
            clauses.append((segs[i] + ')', segs[i+1].strip()))
        return clauses
    # không chia được → trả toàn bộ là khoản duy nhất
    return [('full', text)]

# ---------- 4. clean ----------
def clean(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()

# ---------- 5. main ----------
if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python docx2clausejsonl.py input.docx output.jsonl')
        sys.exit(1)
    infile = os.path.expanduser(sys.argv[1])
    outfile = sys.argv[2]

    raw = docx_to_raw_text(infile)
    articles = split_articles(raw)

    total = 0
    with open(outfile, 'w', encoding='utf-8') as f:
        for art_id, body in articles:
            clauses = split_clauses(art_id, body)
            for clause_num, clause_txt in clauses:
                rec = {
                    "id": f"{art_id.replace(' ', '_')}_k{clause_num}",
                    "article": art_id,
                    "clause": clause_num,
                    "text": clean(clause_txt)
                }
                f.write(json.dumps(rec, ensure_ascii=False) + '\n')
                total += 1
    print(f'Done! {total} clauses → {outfile}')
