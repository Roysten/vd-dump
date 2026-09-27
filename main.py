#!/usr/bin/env python3

import argparse
import sys
import re
import json

import html
import validation

FIELD_ID = 0xCC

class ExtractError(Exception):

    def __init__(self, message, html_data, html_document):
        super().__init__(message)
        self.html_data = html_data
        self.html_document = html_document

def replace_refs(txt):
    ref_regex = r'<\+[F<](.*?)<\+(?:.EGWN).*<\+[@J]|<\+(.*?)<\+'
    return re.sub(ref_regex, lambda match: f'${(match.group(1) or match.group(2)).strip()}$', txt)

def process_word(data, span):
    left, right = span
    fields = data[left:right].split(b'<!')

    word_data = []
    for field in fields:
        if field and field[0] == FIELD_ID:
            word_data += [int(fields[1][1:].decode())]
            break

    description_start = data[left:right].find(b'<!\xC8')
    html_data = data[left + description_start + 7:right] 
    if b'writeContext' in html_data:
        html_data = expand_write_context(html_data)
    if b'writeBetekenis' in html_data:
        html_data = expand_write_betekenis(html_data)
    html_data = b'<html>' + html_data + b'</html>'
    document = html.parse_html(html_data)[1]
    # print(html.dump_node(html_data, html.parse_html(html_data)[1]))
    word_data += [extract_trefw(html_data, document)]
    word_data += [extract_fsn(html_data, document)]
    word_data += [extract_betekenis(html_data, document)]
    word_data += [extract_woordvormen(html_data, document)]
    return word_data

def extract_trefw(html_data, document):
    trefw = html.find_element(html_data, document, 'span', 'trefw')
    if trefw:
        return html.get_text_content(html_data, trefw)
    raise ExtractError('no trefw found', html_data, document)

def extract_fsn(html_data, document):
    fsn = html.find_element(html_data, document, 'div', 'fsn')
    if fsn:
        fsn_text = html.get_text_content(html_data, fsn)
        fsn_text = re.sub(r'<!.', '', fsn_text)
        return fsn_text
    raise ExtractError('no fsn found', html_data, document)

def extract_betekenis(html_data, document):
    definitions = []
    divs = html.find_child_nodes(html_data, document, 'div')

    for div in divs:
        table = html.find_element(html_data, div, 'table', 'lem')
        if not table:
            raise ExtractError('betekenis table not found', html_data, document)
        trs = html.find_child_nodes(html_data, table, 'tr')
        for tr in trs:
            tds = html.find_child_nodes(html_data, tr, 'td')
            if len(tds) == 5:
                if html.find_element(html_data, tds[2], 'span', 'betnr'):
                    token_span = html.get_content_span(html, tds[4])
                    raw_td_data = html_data[token_span[0]:token_span[1] + 1]
                    if b'<!\x7b' in raw_td_data:
                        definition_txt = re.search(rb'<!\x7b(.*?)<!', raw_td_data).group(1)
                        definition_txt = html.decode_text(definition_txt)
                    else:
                        text_node = next((c for c in tds[4].child_nodes if c.token.type == html.TokenType.TEXT), None)
                        definition_txt = html.get_text_content(html_data, tds[4])
                    definition_txt = re.sub(r'<!.', '', definition_txt)
                    definition_txt = replace_refs(definition_txt)
                    definition = {'d': definition_txt}

                    # Synonym processing
                    token_span = html.get_content_span(html, tds[4])
                    raw_td_data = html_data[token_span[0]:token_span[1] + 1]
                    synonym_match = re.search(rb'<!\xAD\x1B\x11\x01\x01(.*?\x1B\x11\x01\x01.*?)\x1B\x11\x01\x00', raw_td_data)
                    if synonym_match:
                        definition['s'] = html.get_text_content_safe(synonym_match.group(1))

                    # Antonym processing
                    token_span = html.get_content_span(html, tds[4])
                    raw_td_data = html_data[token_span[0]:token_span[1] + 1]
                    antonym_match = re.search(rb'<!\x6B\x1B\x11\x01\x01(.*?\x1B\x11\x01\x01.*?)\x1B\x11\x01\x00', raw_td_data)
                    if antonym_match:
                        definition['a'] = html.get_text_content_safe(antonym_match.group(1))

                    # Vorm variant processing
                    token_span = html.get_content_span(html, tds[4])
                    raw_td_data = html_data[token_span[0]:token_span[1] + 1]
                    vorm_variant_match = re.search(rb'<!\xC2\x1B\x11\x01\x01(.*?\x1B\x11\x01\x01.*?)\x1B\x11\x01\x00', raw_td_data)
                    if vorm_variant_match:
                        definition['vv'] = html.get_text_content_safe(vorm_variant_match.group(1))

                    definitions += [definition]
                else:
                    token_span = html.get_content_span(html, tds[4])
                    raw_td_data = html_data[token_span[0]:token_span[1] + 1]
                    if b'<!\x8c' in raw_td_data:
                        # print(raw_td_data)
                        # context_txt = re.search(rb'<!\x8c<!.(.*?)<!', raw_td_data).group(1)
                        # context_txt = html.decode_text(context_txt)
                        context_txt = html.get_text_content(html_data, tds[4])
                        context_txt = re.sub(r'<!\xC8 *', ' - ', context_txt)
                        context_txt = re.sub(r'<!.', '', context_txt)
                        context_txt = replace_refs(context_txt)
                        definitions[-1]['c'] = definitions[-1].get('c', []) + [context_txt]
                
    return definitions

def extract_woordvormen(html_data, document):
    divs = html.find_child_nodes(html_data, document, 'div')

    for div in divs:
        table = html.find_element(html_data, div, 'table', 'lem')
        if not table:
            raise ExtractError('betekenis table not found', html_data, document)
        trs = html.find_child_nodes(html_data, table, 'tr')
        for tr in trs:
            tds = html.find_child_nodes(html_data, tr, 'td')
            for td in tds:
                woordvormen_table = html.find_element(html_data, td, 'table', 'FLti')
                if woordvormen_table:
                    wvs = []
                    wv_trs = html.find_child_nodes(html_data, woordvormen_table, 'tr')
                    for wv_tr in wv_trs:
                        wv = []
                        wv_tds = html.find_child_nodes(html_data, wv_tr, 'td')
                        if len(wv_tds) >= 2:
                            wv += [html.get_text_content(html_data, wv_tds[0])]
                            wv += [html.get_text_content(html_data, wv_tds[1])]
                        if len(wv_tds) >= 4:
                            wv += [html.get_text_content(html_data, wv_tds[2])]
                            wv += [html.get_text_content(html_data, wv_tds[3])]
                        if wv[0] == '\xa0':
                            # Emtpy row
                            continue
                        wvs += [wv]
                    return wvs
    return []

def expand_write_betekenis(html_data):
    """Uitklapbaar blok in het bovenste deel"""
    new_html_data = html_data
    while True:
        m = re.search(b'<script language="JavaScript">(.*?writeBetekenis.*?)</script>', new_html_data)
        if not m:
            break

        if not b'writeBetekenis' in m.group(1):
            continue

        bet = re.search(b'bet="(.*?)";', m.group(1))
        context = re.search(b'context="(.*?)";', m.group(1))
        expanded = b'<tr class="bet"><td class="kol1"></td><td class="kol2"></td>' + bet.group(1).replace(b'\\"', b'"') + context.group(1).replace(b'\\"', b'"')

        new_html_data = new_html_data[:m.start()] + expanded + new_html_data[m.end():]
    return new_html_data

def expand_write_context(html_data):
    """Uitklapbaar blok in het onderste deel"""
    new_html_data = html_data
    it = 0
    while True:
        it += 1
        m = re.search(b'<script language="JavaScript">(.*?writeContext.*?)</script>', new_html_data)
        if not m:
            break

        if not b'writeContext' in m.group(1):
            continue

        bet = re.search(b'bet="(.*?)";', m.group(1))
        context = re.search(b'context="(.*?)";', m.group(1))
        expanded = b'<tr class="bet"><td class="kol1"></td><td class="kol2"></td>' + bet.group(1).replace(b'\\"', b'"') + context.group(1).replace(b'\\"', b'"')

        new_html_data = new_html_data[:m.start()] + expanded + new_html_data[m.end():]
    return new_html_data

def process(args):
    words = []
    with open(args.src, 'rb') as f:
        data = f.read()

    # BEGIN: 3C 21 CC
    # END: 1B 11 01 00
    offset = 0
    while offset < len(data):
        left = data.find(b'\x3C\x21\xCC', offset)
        if left == -1:
            break

        right = data.find(b'\x3C\x21\xCC', left + 1)
        if right == -1:
            span[1] = len(data) - 1

        span = [left, right]
        try:
            words += [process_word(data, span)]
        except ExtractError as e:
            print(e, file=sys.stderr)
            # print(html.dump_node(e.html_data, e.html_document), file=sys.stderr)
        except:
            print(span)
            print(data[span[0]:span[1] + 1])
            raise
        # print(words[-1]['word'], file=sys.stderr)
        # if len(words) >= 2000:
        #     break
        offset = span[1]
    print('[')
    sep = ''
    for word in words:
        if sep:
            print(sep)
        print(json.dumps(word, ensure_ascii=False, separators=(',', ':')), end='')
        sep = ','
    print(']')
    for i, word in enumerate(words):
        validation.validate(word, i)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("src")
    args = parser.parse_args()
    process(args)

if __name__ == "__main__":
    main()
