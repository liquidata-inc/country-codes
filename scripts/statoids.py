#!/usr/bin/env python
# -*- coding: utf-8 -*-
import collections
import urllib.request

from lxml import html

def capitalize_country_name(name):
    # replace all-caps name with capitalized country name
    cap_list = []
    always_lower = ['AND', 'THE', 'OF', 'PART', 'DA', 'DE', 'ET', 'DU', 'DES',
                    'LA']
    for w in name.split():
        if w == 'MCDONALD':
            cap_list.append('McDonald')
        if w.find('.') > 0:
            cap_list.append(w.upper())
            continue
        if w.find('\'') > 0:
            # d'Ivoire instead of D'ivoire
            s = w.split('\'')
            if len(s[0]) == 1:
                cap_list.append(s[0].lower() + '\'' + s[1].capitalize())
                continue
        if w.find('-') > 0:
            # Timor-Leste instead of Timor-leste
            cap_list.append('-'.join([b.capitalize() for b in w.split('-')]))
            continue

        if w.startswith('('):
            w = w.replace('(', '')
            if w in always_lower:
                w = w.lower()
            else:
                w = w.capitalize()
            cap_list.append('(' + w)
            continue

        if w[-1] == ')':
            w = w.replace(')', '')
            if w in always_lower:
                w = w.lower()
            else:
                w = w.capitalize()
            cap_list.append(w + ')')
            continue

        if w in always_lower:
            cap_list.append(w.lower())
            continue
        cap_list.append(w.capitalize())

    capitalized = " ".join(cap_list)
    return capitalized


def process_statoids_row(tr):
    row = []
    for td in tr.iterchildren():
        if len(td.getchildren()) == 0:
            row.append(td.text_content())
            continue
        if len(td.keys()) > 0:
            if td.get('colspan') is not None:
                # if a cell is taking up more than one column,
                # append the same number of blanks to the row
                assert td.get('colspan').isdigit()
                for col in xrange(int(td.get('colspan'))):
                    row.append('')
                continue
        if len(td.getchildren()) > 1:
            if td.find('.//br') is not None:
                if ((len(row) > 1) and (row[1] == "DO")):
                    # TIL dominican republic has three dialing codes
                    # td.text_content() is '1-8091-8291-849'
                    # so split into list of 5 chars each and join with commas
                    row.append(','.join(map(''.join,
                                            zip(*[iter(td.text_content())]*5))))
                    continue
        if ((len(row) > 1) and (row[1] in ["SH", "RS"])):
            # Saint Helena and Serbia dial cells have anchors to footnotes
            # so just append the number
            if td.text_content()[:3].isdigit():
                code = td.text_content().split(' ')[0]
                row.append(code)
                continue
        if len(td.getchildren()) == 1:
            if td.find('.//br') is not None:
                if len(td.getchildren()) == 1:
                    if td.getchildren()[0].tag == 'br':
                        td.text = td.text + "," + td.getchildren()[0].tail
                        row.append(td.text)
                        continue
            if td.find("code") is not None:
                # some cells contain more than one code,
                # so append a list also containing the code
                # that appears after the child element (<br>)
                if len(td.find("code").getchildren()) > 0:
                    if td.find('.//br') is not None:
                        row.append(td.find('code').text + ','
                                   + td.find('.//br').tail)
                        continue
                    if td.find('.//a') is not None:
                        anchor = td.find('.//a')
                        # UK has 4 FIFA codes
                        if row[1] == "GB":
                            assert anchor.text == "1"
                            row.append("ENG,NIR,SCO,WAL")
                            continue
                        # MARC treats United States Minor Outlying Islands
                        # as five countries
                        if row[1] == "UM":
                            assert anchor.text == "b"
                            row.append("ji,xf,wk,uc,up")
                            continue
                # some cells contain anchor to footnote,
                # so append only the content of the code element
                row.append(td.find("code").text)
                continue
            else:
                if td.find('.//a') is not None:
                    anchor = td.find('.//a')
                    # FIPS treats United States Minor Outlying Islands
                    # as nine countries
                    if len(row) > 1 and row[1] == "UM":
                        assert anchor.text == "a"
                        row.append("FQ,HQ,DQ,JQ,KQ,MQ,BQ,LQ,WQ")
                        continue
        row.append(td.text_content())
    return row


statoids_url = "http://www.statoids.com/wab.html"
print('Fetching other country codes...')
content = urllib.request.urlopen(statoids_url).read()
doc = html.fromstring(content)

# i dislike some of statoid's column names, so here i have renamed
# a few to be more descriptive
column_names = ["Entity", "ISO3166-1-Alpha-2", "ISO3166-1-Alpha-3",
                "ISO3166-1-numeric", "ITU", "FIPS", "IOC", "FIFA", "DS",
                "WMO", "GAUL", "MARC", "Dial", "is_independent"]
alpha2_key = "ISO3166-1-Alpha-2"

# comment out the preceding two lines and
# uncomment these lines to use statoids.com column names
"""
column_names = []
alpha2_key = 'A-2'
for tr in doc.find_class('hd'):
    for th in tr.iterchildren():
        column_names.append(th.text_content())
"""

# dict to hold dicts of all table rows
table_rows = {}

# the country code info is in a table where the trs have
# alternating classes of `e` and `o`
# so fetch half of the rows and zip each row together
# with the corresponding column name
for tr in doc.find_class('e'):
    row = process_statoids_row(tr)
    row_dict = collections.OrderedDict(zip(column_names, row))
    # statoids-assigned 'Entity' name is not really a standard
    row_dict.pop('Entity')
    row_dict.pop('ITU', None)
    row_dict.pop('FIPS', None)
    row_dict.pop('IOC', None)
    row_dict.pop('FIFA', None)
    row_dict.pop('DS', None)
    row_dict.pop('WMO', None)
    row_dict.pop('GAUL', None)
    row_dict.pop('MARC', None)
    row_dict.pop('Dial', None)
    row_dict.pop('is_independent', None)
    table_rows.update({row_dict[alpha2_key]: row_dict})
#    print(table_rows)


# and again for the other half
for tr in doc.find_class('o'):
    row = process_statoids_row(tr)
    row_dict = collections.OrderedDict(zip(column_names, row))
    # statoids-assigned 'Entity' name is not really a standard
    row_dict.pop('Entity')
    row_dict.pop('ITU', None)
    row_dict.pop('FIPS', None)
    row_dict.pop('IOC', None)
    row_dict.pop('FIFA', None)
    row_dict.pop('DS', None)
    row_dict.pop('WMO', None)
    row_dict.pop('GAUL', None)
    row_dict.pop('MARC', None)
    row_dict.pop('Dial', None)
    row_dict.pop('is_independent', None)
    table_rows.update({row_dict[alpha2_key]: row_dict})

output_filename = "data/statoids/iso_3166_1.csv"
f = open(output_filename, 'w')
# Write csv headers, should match schema of the iso_3166_1 table:
# https://www.dolthub.com/repositories/Liquidata/country-codes/data/master/iso_3166_1
f.write("alpha_2,alpha_3,numeric\n")

# iterate through all the table_rows
# TODO this assumes that statoids will have all of
# the items that are pulled from iso.org
for alpha2, info in table_rows.items():
    # ignore this crap that was parsed from other tables on the page
    if alpha2 in ['', 'Codes', 'Codes Codes', 'Codes Codes Codes']:
        continue
    row = []
    for key, val in info.items():
        row.append(val)

    row = ','.join(row)
    f.write(row[0:] + "\n")

