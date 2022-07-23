import itertools
import json
import os.path
from typing import List, TypedDict, Dict, Any, Optional

import pdfplumber
from pdfplumber.display import PageImage


class PageInfo(TypedDict):
    page_number: int
    words: List[Dict[str, Any]]


def crop(page):
    return page.crop((85, 132, 520, 645))


def extract_words(page):
    return page.extract_words(extra_attrs=['fontname', 'size'])


def extract(path: str, out: str, pages: Optional[int] = None):
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            cropped = crop(page)
            words = extract_words(cropped)
            lines = group_lines(words)
            tables = extract_tables(cropped)
            page = {'page_number': page.page_number,
                    'lines': lines,
                    'tables': tables}
            save_page(page, out)
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
    return [list(w) for (_, w) in lines]


def save_page(page: dict, out: str):
    name = str(page['page_number']).rjust(3, "0") + ".yaml"
    filepath = os.path.join(out, name)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as file:
        json.dump(page, file, indent=2)


def print_image(page, out: str):
    name = str(page.page_number).rjust(3, "0") + ".jpeg"
    filepath = os.path.join(out, name)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as file:
        img: PageImage = page.to_image()
        img.save(file)
