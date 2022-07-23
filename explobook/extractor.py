import itertools
import os.path
from typing import List, TypedDict, Dict, Any, Optional

import pdfplumber
import yaml
from pdfplumber.display import PageImage


class Line(TypedDict):
    kind: str
    words: List[dict[str, Any]]


class Paragraph(TypedDict):
    kind: str
    lines: List[Line]


class PageInfo(TypedDict):
    page_number: int
    words: List[Dict[str, Any]]


def crop(page):
    return page.crop((85, 132, 520, 645))


def extract_words(page):
    return page.extract_words(extra_attrs=['fontname', 'size'])


def join_lines(paragraphs: List[Paragraph]):
    p = []
    for paragraph in paragraphs:
        lines = paragraph['lines']
        x0 = lines[0]['words'][0]['x0']
        bottom = lines[-1]['words'][0]['bottom']
        x1 = max([last_word['x1'] for last_word in
                  [line['words'][-1] for line in lines]])
        top = lines[0]['words'][0]['top']
        box = [x0, bottom, x1, top]
        joined_words = []
        for line in lines:
            words = line['words']
            joined_words.append(" ".join([w["text"] for w in words]))
        p.append({'kind': 'paragraph',
                  'text': " ".join(joined_words),
                  'box': box})
    return p


def normalize(words: List[dict]):
    return [{**word,
             'x0': int(word['x0']),
             'x1': int(word['x1']),
             'bottom': int(word['bottom']),
             'top': int(word['top']),
             } for word in words]


def extract(path: str, out: str, pages: Optional[int] = None):
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            cropped = crop(page)
            words = extract_words(cropped)
            normalized = normalize(words)
            lines = group_lines(normalized)
            paragraphs = group_paragraphs(lines)
            joined = join_lines(paragraphs)
            tables = extract_tables(cropped)
            page = {'page_number': page.page_number,
                    'paragraphs': joined,
                    'tables': tables}
            save_page(page, out)
            print_image(cropped, [el['box'] for el in joined], out)
            if pages == cropped.page_number:
                break


def extract_tables(page):
    tables = page.find_tables()
    page_tables = []
    for table in tables:
        rows = []
        for row in table.rows:
            rows.append(row.cells)
        page_tables.append(rows)
    return page_tables


def group_lines(words):
    lines = itertools.groupby(words, lambda w: w['bottom'])
    return [{'kind': 'line',
             'words': list(w)}
            for (_, w) in lines]


def group_paragraphs(lines):
    paragraphs = itertools.groupby(lines, lambda line: line['words'][0]['x0'])
    return [{'kind': 'paragraph',
             'lines': list(lines)}
            for (_, lines) in paragraphs]


def save_page(page: dict, out: str):
    name = str(page['page_number']).rjust(3, "0") + ".yaml"
    filepath = os.path.join(out, name)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as file:
        yaml.dump(page, file)


def print_image(page, boxes, out: str):
    name = str(page.page_number).rjust(3, "0") + ".jpeg"
    filepath = os.path.join(out, name)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as file:
        img: PageImage = page.to_image()
        img.draw_rects(boxes)
        img.save(file)
