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
