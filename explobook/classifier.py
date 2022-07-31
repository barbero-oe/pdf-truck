import functools
import itertools
from typing import List, Optional, Union, Callable

from explobook.model import Page, Line, Word, calculate_box, TableText

FONTS = [
    "Black",
    "Bold",
    "BoldItalic",
    "Book",
    "BookItalic"
    "Medium",
    "MediumItalic",
    "Normal",
    "NormalItalic",
]


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


class Paragraph:
    def __init__(self, text: List[FormattedText], box):
        self.text = text
        self.box = box

    def __str__(self):
        return " ".join([t.text for t in self.text])


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


class Document:
    def __init__(self, elements, tables):
        self.elements = elements
        self.tables = tables

    def all_elements(self):
        sorted(list(itertools.chain(self.elements, self.tables)), key=lambda el: el.box)

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


def classify(page: Page) -> Document:
    items = []
    for section in page.sections:
        items.extend(classify_lines(section.lines))
    return Document(items, page.tables)


def classify_tables(tables: List[TableText]):
    pass


def classify_lines(lines: List[Line]) -> List:
    if not lines:
        return lines
    if header := try_header(lines):
        return header
    elif ol := try_ol(lines):
        return ol
    elif ul := try_ul(lines):
        return ul
    else:
        return paragraph(lines)


def paragraph(lines: List[Line]):
    if not lines:
        return None
    min_indent = min(line.words[0]['x0'] for line in lines)
    if min_indent >= 120:
        return [create_paragraph(lines)]
    else:
        return grouped_paragraphs(min_indent, lines)


def create_paragraph(lines: List[Line]) -> Paragraph:
    box = calculate_box(lines)
    fix_word_breaks(lines)
    words = list(itertools.chain(*[line.words for line in lines]))
    return Paragraph(format_text(words), box)


def grouped_paragraphs(min_indent: float, lines: List[Line]) -> List[Paragraph]:
    def group(paragraphs: List[List[Line]], line: Line) -> List[List[Line]]:
        if not paragraphs:
            return [[line]]
        indent = line.words[0]['x0']
        if indent >= min_indent + 2:
            paragraphs.append([line])
        else:
            paragraphs[-1].append(line)
        return paragraphs

    paragraphs_grouped = functools.reduce(group, lines, [])
    return [create_paragraph(p_lines) for p_lines in paragraphs_grouped]


def is_unordered_list_item(line):
    first_word: str = line.words[0]['text']
    return first_word[0] in '-*#>•'


def is_ordered_list_item(line):
    first_word: str = line.words[0]['text']
    if len(first_word) == 1:
        return False
    return first_word[0].isnumeric() and not first_word[1].isalpha()


def try_ol(lines: List[Line]) -> List:
    return try_list(lines, is_ordered_list_item, 'ordered')


def try_ul(lines):
    return try_list(lines, is_unordered_list_item, 'unordered')


def try_list(lines: List[Line], starts_item: Callable[[Line], bool], kind: str) -> Optional[List]:
    ordered = [line for line in lines if starts_item(line)]
    if not ordered:
        return None
    ol = group_list_items(lines, ordered)

    items = list(itertools.chain(*ol))
    no_items = [line for line in lines if line not in items]

    list_items, box = tokenize_list(ol)
    listing = Listing(kind, list_items, box)
    return [*classify_lines(no_items), listing]


def fix_word_breaks(lines: List[Line]) -> List[Line]:
    for index in range(len(lines) - 2):
        if lines[index].words:
            last_word = lines[index].words[-1]
            next_line_word = lines[index + 1].words[0]
            if last_word['text'][-1] == '-':
                last_word['text'] = last_word['text'][0:-2] + next_line_word['text']
                lines[index + 1].words.remove(next_line_word)


def tokenize_list(ol: List[List[Line]]):
    items = []
    for item in ol:
        fix_word_breaks(item)
        words = list(itertools.chain(*[line.words for line in item]))
        items.append(format_text(words))
    box = calculate_box(list(itertools.chain(*ol)))
    return items, box


def group_list_items(lines: List[Line], list_item_start: List[Line]) -> List[List[Line]]:
    ol = []
    item = []
    for line in lines:
        if line in list_item_start:
            item = [line]
            ol.append(item)
        else:
            item.append(line)
    return ol


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


def header_level(line: Line) -> str:
    first_word = line.words[0]
    size = first_word['size']
    bold = is_bold(first_word)
    medium = is_medium(first_word)
    if bold and size > 20:
        return 'h1'
    elif medium and size > 10:
        return 'h2'
    else:
        return 'h3'


def classify_header(line: Line):
    level = header_level(line)
    text = format_text(line.words)
    box = calculate_box([line])
    return Header(level, text, box)


def is_all_caps(line: Line) -> bool:
    for word in line.words:
        for character in word['text']:
            if character.isalpha():
                if character.islower():
                    return False
    return True


def try_header(lines: List[Line]) -> Optional[List[Header]]:
    if not lines:
        return None
    first_line, rest = lines[0], lines[1:]
    first_word = first_line.words[0]
    size = first_word['size']
    medium = size == 10 and all([is_medium(word) or is_bold(word) for word in first_line.words])
    big = is_all_caps(first_line) and size >= 10 and (is_bold(first_word) or is_medium(first_word))
    if not big and not medium:
        return None
    header = classify_header(first_line)
    return [header, *classify_lines(rest)] if rest else [header]


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
