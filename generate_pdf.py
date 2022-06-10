#!/usr/bin/env python
"""
Code written with help of https://www.blog.pythonlibrary.org Reportlab tutorials

Code generates productivity calendars for a given month of current year. Pass the month number as first argument - like python generate.py 1 .
"""


import sys
import json
from copy import copy
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, portrait, inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

keeb_file = sys.argv[1]

with open(sys.argv[1], 'r') as f:
    keeb_data = json.load(f)

keeb_name = keeb_data.get("file_name", keeb_data.get("name", keeb_file.rsplit('/', 1)[-1].rsplit('.', 1)[0]))
if "lang" in keeb_data:
    keeb_name = keeb_name+'-'+keeb_data["lang"]

try:
    os.mkdir('datasheets/')
except FileExistsError:
    pass

print("Filename: datasheets/datasheet_{}.pdf".format(keeb_name.lower()))

doc = SimpleDocTemplate("datasheet/datasheet_{}.pdf".format(keeb_name.lower()), pagesize=portrait(A4),
                        rightMargin=72,leftMargin=72,
                        topMargin=40,bottomMargin=0)
elements = []

styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))

#Fun with Python and objects being duplicated
#data = 5*[7*[""]] #Sudden realisation
#data = 5*[7*copy([""])] #Naive attempt at fixing
#data = 5*[7*list([""])] #Same

columns = keeb_data['columns']
rows = keeb_data['rows']

#Well then.
data = [["" for x in range(len(rows)+1)] for x in range(len(columns)+1)]

data[0] = ["Columns"]+[str(x) for x in rows]

for x in range(1, len(columns)+1):
    data[x][0] = str(columns[x-1])

d = keeb_data['table']

for row, cols in d.items():
    for col, key in cols.items():
        data[columns.index(int(col))+1][rows.index(int(row))+1] = key.upper()

# heading

elements.append(Paragraph("<font size=20>Key table</font>", styles["Center"]))
elements.append(Spacer(1, 40))

elements.append(Paragraph("<font size=7>Rows</font>", styles["Center"]))
elements.append(Spacer(1, 7))

t=Table(data,(len(rows)+1)*[0.8*inch], (len(columns)+1)*[0.2*inch])

t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                       ('ALIGN',(0,0),(-1,-1),'CENTER'),
                       ('SIZE',(0,0),(-1,-1), 7),
                       #('BACKGROUND',(0, 1),(-1,-1),colors.cyan),
                       #('BACKGROUND',(0,4),(-1,-4),colors.pink),
                       #('BACKGROUND',(0, 8),(-1,-8),colors.white),
                       ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
                       ('BOX', (0,0), (-1,-1), 0.25, colors.black),
                        ]))
#                       ('TEXTCOLOR',(5,0),(-1,-1),colors.red)]))
elements.append(t)
# write the document to disk
doc.build(elements)
