import functools
import itertools
import os.path
from typing import List, Optional, Tuple

import pdfplumber
import yaml
from pdfplumber.display import PageImage
from pdfplumber.page import Page
from pdfplumber.table import Table

from explobook import model
from explobook.model import Word, Line, Section, TableText, Cell, Row


def crop(page: Page):
    return page.crop((85, 132, 520, 645))


def extract_words(page: Page) -> List[Word]:
    return normalize(page.extract_words(extra_attrs=['fontname', 'size']))


def normalize(words: List[Word]) -> List[Word]:
    return [Word(**{**word,
                    'x0': int(word['x0']),
                    'x1': int(word['x1']),
                    'bottom': int(word['bottom']),
                    'top': int(word['top'])})
            for word in words]


def extract(path: str, out: str, pages: Optional[int] = None):
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            cropped = crop(page)
            (tables, sections) = extract_text(cropped)
            p = model.Page(page.page_number, sections, tables)
            save_page(p, out)
            print_image(cropped, p, out)
            if pages == cropped.page_number:
                break


def parse_table(page: Page, table: Table) -> TableText:
    rows = []
    for row in table.rows:
        table_row = []
        for cell in row.cells:
            if not cell:
                continue
            cell_boundaries = page.within_bbox(cell)
            words = extract_words(cell_boundaries)
            lines = group_lines(words)
            sections = group_sections(lines)
            table_row.append(Cell(sections))
        rows.append(Row(table_row))
    return TableText(rows, table.bbox)


def extract_tables(page: Page) -> List[TableText]:
    return [parse_table(page, table)
            for table in page.find_tables()]


def remove_tables(page: Page) -> List[Word]:
    words = extract_words(page)
    tables = page.find_tables()
    for table in tables:
        table_words = extract_words(page.within_bbox(table.bbox))
        for word in table_words:
            words.remove(word)
    return words


def extract_text(page: Page) -> Tuple[List[TableText], List[Section]]:
    tables = extract_tables(page)
    words = remove_tables(page)
    lines = group_lines(words)
    sections = group_sections(lines)
    return tables, sections


def group_lines(words: List[Word]) -> List[Line]:
    lines = itertools.groupby(words, lambda w: w['bottom'])
    return [Line(list(w))
            for (_, w) in lines]


def get_fonts(line):
    fonts = itertools.groupby(line.words, lambda word: word['fontname'])
    return [font[0] for font in fonts]


def line_separation(top_line: Line, bottom_line: Line) -> float:
    bottom = top_line.words[0]['bottom']
    top = bottom_line.words[0]['top']
    return top - bottom


def detect_sections(group: List[List[Line]], line: Line) -> List[List[Line]]:
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


def group_sections(lines: List[Line]) -> List[Section]:
    sections: List[List[Line]] = functools.reduce(detect_sections, lines, [])
    return [Section(section) for section in sections]


def save_page(page: model.Page, out: str):
    name = str(page.number).rjust(3, "0") + ".yaml"
    filepath = os.path.join(out, name)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as file:
        yaml.dump(page.as_dict(), file)


GREEN = (0, 255, 0, 50)
RED = (255, 0, 0, 50)


def print_image(page, model_page: model.Page, out: str):
    name = str(model_page.number).rjust(3, "0") + ".jpeg"
    filepath = os.path.join(out, name)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as file:
        img: PageImage = page.to_image(resolution=150)
        img.draw_rects([section.box() for section in model_page.sections])
        img.draw_rects([table.box for table in model_page.tables], fill=GREEN)
        img.save(file)
