import os.path
from typing import List

from explobook.model import Document


def group_chapters(documents: List[Document]) -> List[List[Document]]:
    chapters = []
    for document in documents:
        if not document.all_elements():
            continue
        has_title = any(header for header in document.headers() if header.level == 'h1')
        if has_title or not chapters:
            chapters.append([document])
        else:
            chapters[-1].append(document)
    return chapters


def chapter_title(chapter: List[Document]):
    return chapter[0].headers()[0].text()


def export(out: str, documents: List[Document]):
    chapters = group_chapters(documents)
    for index, chapter in enumerate(chapters):
        to_html(out, chapter, index)


def to_html(out: str, chapter: List[Document], index):
    index_name = str(index).rjust(2, '0')
    title = chapter_title(chapter).replace(' ', '-').lower()
    file_name = f'{index_name}-{title}.html'
    print(f'Processing chapter {file_name}')
    file_path = os.path.join(out, file_name)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as html:
        html.writelines([
            '<!doctype html>'
            '<html lang="es">'
            '<head>'
            '<meta charset="UTF-8">'
            '</head>'
            '<body>'])
        for doc in chapter:
            html.write(doc.to_html())
        html.write('</body>')
        html.write('</html>')
