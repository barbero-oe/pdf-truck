import os

import pdfplumber
from pytest import fixture, Config

from explobook.extractor import parse_page


@fixture
def rh_book(pytestconfig: Config) -> str:
    return os.path.join(pytestconfig.rootpath, "assets", "rastreadores-hogueras.pdf")


@fixture
def out_directory(pytestconfig: Config):
    # return os.path.join(pytestconfig.rootpath, "out", "rastreadores-hogueras")
    return os.path.join(pytestconfig.rootpath, "out", "test")


@fixture
def page_19(rh_book):
    structure = [
        h2('ENTENDIENDOLOS'),
        p('En general, los'),
        h2('OBJETIVOS CUMPLIDOS'),
        ul('-Los Rastreadores', '- Actuaron con'),
        h2('ACTIVIDADES CENTRALES'),
        ol('1-Construcciones', '2-Mu'),
        h3('ACTIVIDAD 1: CONSTRUCCIONES CRUZADAS'),
        p('- Orientaci'),
        p('- Actividad'),
        ol('1. Cada', '2. Explica', '3. Intervenir', '4. En alg')
    ]

    with pdfplumber.open(rh_book) as pdf:
        yield pdf.pages[19], structure


def test_validate_titles(page_19):
    page, structure = page_19
    actual = parse_page(page)

    expected_headers = [el for el in structure if el['kind'] == 'title']
    values = zip(expected_headers, actual.headers())

    assert len(actual.headers()) == len(expected_headers)
    for expected, actual in values:
        assert expected['level'] == actual.level
        assert expected['text'] in actual.text()


# def test_extraction(rh_book: str, out_directory):
#     extract(rh_book, out_directory, [19])
# extract(rh_book, out_directory)


def title(level: str, text: str):
    return {'kind': 'title', 'level': level, 'text': text}


def h1(text: str):
    return title('h1', text)


def h2(text: str):
    return title('h2', text)


def h3(text: str):
    return title('h3', text)


def p(text: str):
    return {'kind': 'paragraph', 'text': text}


def ul(*items: str):
    return {'kind': 'ul', 'items': items}


def ol(*items: str):
    return {'kind': 'ol', 'items': items}

# 6 table
# 15 weird titles
# 17 chapter
# 19 list, numbered list, activity <-- this one :P
# 22 god's word
# 33 verso
# 41 list
