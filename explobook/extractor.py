import functools
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
        x0 = min([first_word['x0'] for first_word in
                  [line['words'][0] for line in lines]])
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


def get_fonts(line):
    fonts = itertools.groupby(line['words'], lambda word: word['fontname'])
    return [font[0] for font in fonts]


def line_separation(top_line, bottom_line):
    bottom = top_line['words'][0]['bottom']
    top = bottom_line['words'][0]['top']
    return top - bottom


def group_sections(group: List, line: Line):
    if not group:
        group.append([line])
        return group
    paragraph = group[-1]
    last_line = paragraph[-1]
    if line_separation(last_line, line) <= 2:
        paragraph.append(line)
    else:
        group.append([line])
    return group


def group_paragraphs(lines):
    sections = functools.reduce(group_sections, lines, [])
    return [{'kind': 'paragraph',
             'lines': p} for p in sections]

    # paragraphs = itertools.groupby(lines, lambda line: line['words'][0]['x0'])
    # return [{'kind': 'paragraph',
    #          'lines': list(lines)}
    #         for (_, lines) in paragraphs]


# line_fonts = get_fonts(line)
# next_line_fonts = get_fonts(next_line)
# intersection = [value for value in line_fonts if value in next_line_fonts]


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
