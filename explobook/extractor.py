import functools
import itertools
import os.path
from typing import List, TypedDict, Optional, Union

import pdfplumber
import yaml
from pdfplumber.display import PageImage


class Word(TypedDict):
    text: str
    fontname: str
    size: float
    x0: float
    x1: float
    top: float
    bottom: float
    doctop: float
    direction: int
    upright: bool


class Line:
    def __init__(self, words: List[Word]):
        self.words = words

    def text(self):
        return " ".join([word['text'] for word in self.words])

    def as_dict(self):
        return {'kind': 'line',
                'text': self.text(),
                'words': [word for word in self.words]}


class Paragraph:
    def __init__(self, lines: List[Line]):
        self.lines = lines

    def text(self):
        return " ".join([line.text() for line in self.lines])

    def box(self):
        return calculate_box(self.lines)

    def as_dict(self):
        return {'kind': 'paragraph',
                'text': self.text(),
                'lines': [line.as_dict() for line in self.lines]}


class Section:
    def __init__(self, elements: List[Union[Paragraph | Line]]):
        self.elements = elements

    def boxes(self):
        return [el.box() for el in self.elements if el.box]

    def as_dict(self):
        return {'kind': 'section',
                'elements': [el.as_dict() for el in self.elements]}


def calculate_box(lines: List[Line]):
    x0 = min([first_word['x0'] for first_word in
              [line.words[0] for line in lines]])
    bottom = lines[-1].words[0]['bottom']
    x1 = max([last_word['x1'] for last_word in
              [line.words[-1] for line in lines]])
    top = lines[0].words[0]['top']
    return [x0, bottom, x1, top]


def crop(page):
    return page.crop((85, 132, 520, 645))


def extract_words(page):
    return page.extract_words(extra_attrs=['fontname', 'size'])


def normalize(words: List[Word]) -> List[Word]:
    return [Word(**{**word,
                    'x0': int(word['x0']),
                    'x1': int(word['x1']),
                    'bottom': int(word['bottom']),
                    'top': int(word['top'])})
            for word in words]


def detect_paragraph(section: Section) -> Section:
    lines: List[Line] = [line for line in section.elements]
    groups = list(itertools.groupby(lines, lambda el: el.words[0]['x0']))
    normal_indent = min({group[0] for group in groups})
    paragraphs: List[List[Line]] = []
    for indent, grouped_elements in itertools.groupby(lines, lambda el: el.words[0]['x0']):
        if indent != normal_indent or not paragraphs:
            paragraphs.append(list(grouped_elements))
        else:
            paragraphs[-1].extend(list(grouped_elements))
    return Section([Paragraph(lines=paragraph)
                    for paragraph in paragraphs])


def detect_elements(sections: List[Section]) -> List[Section]:
    return [detect_paragraph(section) for section in sections]


def extract(path: str, out: str, pages: Optional[int] = None):
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            cropped = crop(page)
            words = extract_words(cropped)
            normalized = normalize(words)
            lines = group_lines(normalized)
            sections = group_sections(lines)
            elements = detect_elements(sections)
            # joined = join_lines(sections)
            tables = extract_tables(cropped)
            page = {'page_number': page.page_number,
                    'sections': [s.as_dict() for s in elements],
                    'tables': tables}
            save_page(page, out)
            print_image(cropped, elements, out)
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


def save_page(page: dict, out: str):
    name = str(page['page_number']).rjust(3, "0") + ".yaml"
    filepath = os.path.join(out, name)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as file:
        yaml.dump(page, file)


def print_image(page, sections, out: str):
    name = str(page.page_number).rjust(3, "0") + ".jpeg"
    filepath = os.path.join(out, name)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as file:
        img: PageImage = page.to_image(resolution=150)
        for section in sections:
            img.draw_rects(section.boxes())
        img.draw_rects(page.lines, stroke="#0000FF", stroke_width=2)
        img.draw_rects(page.rects, stroke="#00FF00", stroke_width=2)
        img.save(file)
