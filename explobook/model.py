from typing import TypedDict, List, Tuple


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
    def __init__(self, lines: List[Line]):
        self.lines = lines

    def box(self):
        return calculate_box(self.lines)

    def text(self):
        return " ".join([line.text() for line in self.lines])

    def as_dict(self):
        return {'kind': 'section',
                'text': self.text(),
                'lines': [line.as_dict() for line in self.lines]}


class Cell:
    def __init__(self, sections: List[Section]):
        self.sections = sections

    def text(self):
        return " ".join([section.text() for section in self.sections])

    def as_dict(self):
        return {'kind': 'cell',
                'text': self.text(),
                'sections': [section.as_dict() for section in self.sections]}


class Row:
    def __init__(self, cells: List[Cell]):
        self.cells = cells

    def text(self):
        return " | ".join([cell.text() for cell in self.cells])

    def as_dict(self):
        return {'kind': 'row',
                'text': self.text(),
                'cells': [cell.as_dict() for cell in self.cells]}


class TableText:
    def __init__(self, rows: List[Row], box: Tuple):
        self.rows = rows
        self._box = box

    def box(self):
        return self._box

    def as_dict(self):
        return {'kind': 'table',
                'rows': [row.as_dict() for row in self.rows]}


class Page:
    def __init__(self, number, sections: List[Section], tables: List[TableText]):
        self.number = number
        self.sections = sections
        self.tables = tables

    def as_dict(self):
        return {'number': self.number,
                'sections': [s.as_dict() for s in self.sections],
                'tables': [t.as_dict() for t in self.tables]}


def calculate_box(lines: List[Line]):
    x0 = min([first_word['x0'] for first_word in
              [line.words[0] for line in lines]])
    bottom = lines[-1].words[0]['bottom']
    x1 = max([last_word['x1'] for last_word in
              [line.words[-1] for line in lines]])
    top = lines[0].words[0]['top']
    return [x0, bottom, x1, top]
