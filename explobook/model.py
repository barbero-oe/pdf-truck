import itertools
from typing import TypedDict, List, Tuple, Union


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

    def __str__(self):
        return self.text()


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

    def to_html(self):
        lines = list(itertools.chain(*[section.lines for section in self.sections]))
        fix_word_breaks(lines)
        words = list(itertools.chain(*[line.words for line in lines]))
        formatted = [text.to_html() for text in format_text(words)]
        return wrap_tag('td', " ".join(formatted))


class Row:
    def __init__(self, cells: List[Cell]):
        self.cells = cells

    def text(self):
        return " | ".join([cell.text() for cell in self.cells])

    def as_dict(self):
        return {'kind': 'row',
                'text': self.text(),
                'cells': [cell.as_dict() for cell in self.cells]}

    def to_html(self):
        content = "\n".join([cell.to_html() for cell in self.cells])
        return wrap_tag('tr', content)


class TableText:
    def __init__(self, rows: List[Row], box: Tuple):
        self.rows = rows
        self.box = box

    def as_dict(self):
        return {'kind': 'table',
                'rows': [row.as_dict() for row in self.rows]}

    def to_html(self):
        content = "\n".join([row.to_html() for row in self.rows])
        return wrap_tag('table', content)


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
              [line.words[0] for line in lines if line.words]])
    bottom = lines[-1].words[0]['bottom']
    x1 = max([last_word['x1'] for last_word in
              [line.words[-1] for line in lines if line.words]])
    top = lines[0].words[0]['top']
    return [x0, bottom, x1, top]


def wrap_tag(tag: str, content: str):
    start = f'<{tag}>'
    end = f'</{tag}>'
    return f'{start}{content}{end}'


class FormattedText:
    def __init__(self, style: str, text: str):
        self.style = style
        self.text = text

    def as_dict(self):
        return {'kind': 'text',
                'style': self.style,
                'text': self.text}

    def __str__(self):
        return self.text

    def to_html(self):
        if self.style == 'italic':
            return wrap_tag('em', self.text)
        elif self.style == 'bold':
            return wrap_tag('strong', self.text)
        elif self.style == 'bold-italic':
            return wrap_tag('strong', wrap_tag('em', self.text))
        else:
            return self.text


class Paragraph:
    def __init__(self, text: List[FormattedText], box):
        self.text = text
        self.box = box

    def __str__(self):
        return " ".join([t.text for t in self.text])

    def to_html(self):
        return wrap_tag('p', " ".join([text.to_html() for text in self.text]))


class Listing:
    def __init__(self, kind: str, items: List[List[FormattedText]], box):
        self.kind = kind
        self._items = items
        self.box = box

    def items(self):
        return self._items

    def __str__(self):
        items = []
        for item in self._items:
            items.append(" ".join(text.text for text in item)[0:30] + "...")
        return str(items)

    def to_html(self):
        li = []
        for item in self.items():
            li.append(" ".join([line.to_html() for line in item]))
        type = 'ol' if self.kind == 'ordered' else 'ul'
        content = "\n".join([wrap_tag('li', item) for item in li])
        return wrap_tag(type, content)


class Header:
    def __init__(self, level: str, formatted_text: List[FormattedText], box):
        self.level = level
        self.formatted_text = formatted_text
        self.box = box

    def text(self):
        return " ".join(text.text for text in self.formatted_text)

    def as_dict(self):
        return {'kind': 'header',
                'level': self.level,
                'formatted_text': [t.as_dict() for t in self.formatted_text],
                'text': self.text(),
                'box': self.box}

    def __str__(self):
        return f"{self.level}: {self.text()}"

    def to_html(self):
        return wrap_tag(self.level, " ".join([text.text for text in self.formatted_text]))


class Document:
    def __init__(self, elements, tables):
        self.elements = elements
        self.tables = tables

    def all_elements(self):
        return sorted(list(itertools.chain(self.elements, self.tables)), key=lambda el: el.box[1])

    def headers(self):
        return [el for el in self.elements if isinstance(el, Header)]

    def as_dict(self):
        return {'kind': 'document',
                'elements': [el.as_dict() for el in self.elements if el.as_dict]}

    def ordered_lists(self):
        return [el for el in self.elements if isinstance(el, Listing) and el.kind == 'ordered']

    def lists(self):
        return [el for el in self.elements if isinstance(el, Listing) and el.kind == 'unordered']

    def paragraphs(self):
        return [el for el in self.elements if isinstance(el, Paragraph)]

    def to_html(self) -> str:
        serialized = []
        for element in self.all_elements():
            serialized.append(element.to_html())
        return "\n".join(serialized)


def fix_word_breaks(lines: List[Line]) -> List[Line]:
    for index in range(len(lines) - 2):
        if lines[index].words:
            last_word = lines[index].words[-1]
            next_line_word = lines[index + 1].words[0]
            if last_word['text'][-1] == '-':
                last_word['text'] = last_word['text'][0:-2] + next_line_word['text']
                lines[index + 1].words.remove(next_line_word)


def is_bold(word: Union[Word, str]):
    font = word if isinstance(word, str) else word['fontname']
    bold = "Black" in font or "Bold" in font
    return bold


def is_italic(word: Union[Word, str]):
    font = word if isinstance(word, str) else word['fontname']
    return "Italic" in font


def is_medium(word: Union[Word, str]):
    font = word if isinstance(word, str) else word['fontname']
    return "Medium" in font


def font_style(font_name: str):
    bold = is_bold(font_name) or is_medium(font_name)
    italic = is_italic(font_name)
    if bold and italic:
        return 'bold-italic'
    elif bold:
        return 'bold'
    elif italic:
        return 'italic'
    else:
        return 'normal'


def format_text(words: List[Word]) -> List[FormattedText]:
    words_by_font = itertools.groupby(words, lambda w: w['fontname'])
    formatted_text = []
    for font, grouped_words in words_by_font:
        style = font_style(font)
        text = " ".join(word['text'] for word in grouped_words)
        formatted_text.append(FormattedText(style, text))
    return formatted_text