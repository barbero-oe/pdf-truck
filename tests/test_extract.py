import os

from pytest import fixture, Config

from explobook.extractor import extract


@fixture
def rh_book(pytestconfig: Config) -> str:
    return os.path.join(pytestconfig.rootpath, "assets", "rastreadores-hogueras.pdf")


@fixture
def out_directory(pytestconfig: Config):
    # return os.path.join(pytestconfig.rootpath, "out", "rastreadores-hogueras")
    return os.path.join(pytestconfig.rootpath, "out", "test")


def test_extraction(rh_book: str, out_directory):
    extract(rh_book, out_directory, range(50))
    # extract(rh_book, out_directory)

# 7 table
# 16 weird titles
# 18 chapter
# 20 list, numbered list, activity <-- this one :P
# 23 god's word
# 34 verso
# 42 list