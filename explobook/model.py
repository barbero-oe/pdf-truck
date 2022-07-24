from typing import TypedDict, List


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


def calculate_box(lines: List[Line]):
    x0 = min([first_word['x0'] for first_word in
              [line.words[0] for line in lines]])
    bottom = lines[-1].words[0]['bottom']
    x1 = max([last_word['x1'] for last_word in
              [line.words[-1] for line in lines]])
    top = lines[0].words[0]['top']
    return [x0, bottom, x1, top]
