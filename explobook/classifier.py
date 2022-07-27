# def detect_paragraph(section: Section) -> Section:
#     lines: List[Line] = [line for line in section.elements]
#     groups = list(itertools.groupby(lines, lambda el: el.words[0]['x0']))
#     normal_indent = min({group[0] for group in groups})
#     paragraphs: List[List[Line]] = []
#     for indent, grouped_elements in itertools.groupby(lines, lambda el: el.words[0]['x0']):
#         if indent != normal_indent or not paragraphs:
#             paragraphs.append(list(grouped_elements))
#         else:
#             paragraphs[-1].extend(list(grouped_elements))
#     return Section([Paragraph(lines=paragraph)
#                     for paragraph in paragraphs])
#
#
# def detect_elements(sections: List[Section]) -> List[Section]:
#     return [detect_paragraph(section) for section in sections]
import itertools
from typing import List, Optional, Union

from explobook.model import Page, Section, Line, Word, calculate_box


# items: List[Union[Section, TableText]] = []
# items.extend(page.sections)
# items.extend(page.tables)
# items.sort(key=lambda x: x.box()[-1])
def classify(page: Page):
    items = []
    for section in page.sections:
        items.extend(classify_item(section))
    return Document(items)


def classify_item(section: Section):
    lines = section.lines
    if header := try_header(lines):
        return header
    else:
        return section.lines


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


class Text:
    def __init__(self, style: str, text: str):
        self.style = style
        self.text = text

    def as_dict(self):
        return {'kind': 'text',
                'style': self.style,
                'text': self.text}


class Header:
    def __init__(self, level: str, text: List[Text], box):
        self.level = level
        self.text = text
        self.box = box

    def as_dict(self):
        return {'kind': 'header',
                'level': self.level,
                'text': [t.as_dict() for t in self.text],
                'box': self.box}


class Document:
    def __init__(self, elements):
        self.elements = elements

    def headers(self):
        return [el for el in self.elements if isinstance(el, Header)]

    def as_dict(self):
        return {'kind': 'document',
                'elements': [el.as_dict() for el in self.elements if el.as_dict]}


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


def try_header(lines: List[Line]) -> Optional[List[Header]]:
    if len(lines) > 2:
        return None
    first_word = lines[0].words[0]
    size = first_word['size']
    big = size >= 10 and (is_bold(first_word) or is_medium(first_word))
    if not big:
        return None

    def could_be_listing(lines):
        def begins_with_number(line):
            first_letter = line.words[0]['text'][0]
            return first_letter.isnumeric()

        if len(lines) == 1:
            return False
        return all([begins_with_number(line) for line in lines])

    if could_be_listing(lines):
        return None
    header = classify_header(lines[0])
    return [header] if len(lines) == 1 else [header, format_text(lines[1].words)]


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


def format_text(words: List[Word]):
    words_by_font = itertools.groupby(words, lambda w: w['fontname'])
    formatted_text = []
    for font, grouped_words in words_by_font:
        style = font_style(font)
        text = " ".join(word['text'] for word in grouped_words)
        formatted_text.append(Text(style, text))
    return formatted_text
