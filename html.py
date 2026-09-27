import re
import enum

class TokenType(enum.Enum):
    TAG_OPEN = 0
    TAG_CLOSE = 1
    TEXT = 2


class Token:
    def __init__(self, token_type, span):
        self.type = token_type
        self.span = span


class Node:
    def __init__(self, token):
        self.token = token
        self.child_nodes = []


def tokenize(html):
    MODE_TEXT = 0
    MODE_TAG_OPEN = 1
    MODE_TAG_CLOSE = 2
    MODE_ATTRIBUTE_KEY = 3
    MODE_ATTRIBUTE_VALUE = 4

    CHAR_LT = ord('<')
    CHAR_GT = ord('>')
    CHAR_EQ = ord('=')
    CHAR_SPACE = ord(' ')
    CHAR_SLASH = ord('/')

    tokens = []

    mode = MODE_TEXT
    l = 0
    r = 0
    html_len = len(html)
    while r < html_len:
        c = html[r]

        if mode == MODE_TEXT:
            if c == CHAR_LT:
                if r > l:
                    tokens += [Token(TokenType.TEXT, (l, r - 1))]
                    l = r
                mode = MODE_TAG_OPEN

        elif mode == MODE_TAG_OPEN:
            if r == l + 1 and c == CHAR_SLASH:
                mode = MODE_TAG_CLOSE
            elif r == l + 1 and not chr(c).isalpha(): # Special case for <!
                mode = MODE_TEXT
            elif c == CHAR_GT:
                if r > l + 1:
                    tokens += [Token(TokenType.TAG_OPEN, (l, r))]
                    l = r + 1
                mode = MODE_TEXT
            elif c == CHAR_SPACE:
                mode = MODE_ATTRIBUTE_KEY

        elif mode == MODE_ATTRIBUTE_KEY:
            if c == CHAR_EQ:
                mode = MODE_ATTRIBUTE_VALUE
            elif not chr(c).isalpha():
                mode = MODE_TEXT

        elif mode == MODE_ATTRIBUTE_VALUE:
            # FIXME: this is a quick and dirty way, but definitely not correct!
            if c == CHAR_GT:
                tokens += [Token(TokenType.TAG_OPEN, (l, r))]

                # Special case for script tag of which the entire content is text
                kv = html[l + 1:r].split()
                if kv and kv[0] == b'script' and kv[1] == b'language="JavaScript"':
                    index_close = html.index(b'</script>', r)
                    tokens += [Token(TokenType.TEXT, (r + 1, index_close - 1))]
                    txt = decode_text(html[tokens[-1].span[0]:tokens[-1].span[1]])
                    txt = re.sub(r'<!.', '', txt)
                    l = index_close
                    r = l
                    mode = MODE_TEXT
                    # print('-->', html[l:])
                    continue

                l = r + 1
                mode = MODE_TEXT

        elif mode == MODE_TAG_CLOSE:
            if c == CHAR_GT:
                if r > l + 2:
                    tokens += [Token(TokenType.TAG_CLOSE, (l, r))]
                    l = r + 1
                mode = MODE_TEXT

        r += 1
    return tokens

def parse_html(html):
    tokens = tokenize(html)

    def process_node(offset):
        token = tokens[offset]
        node = Node(token)
        if token.type != TokenType.TAG_OPEN:
            return offset, node

        i = offset + 1
        while i < len(tokens):
            child_token = tokens[i]

            if child_token.type == TokenType.TAG_CLOSE:
                tag_name = get_tag_name(html, node)
                child_tag_name = html[child_token.span[0]:child_token.span[1]][2:]
                if child_tag_name.decode('ascii', 'ignore') != tag_name:
                    # Workaround for missing closing tag
                    return i - 1, node
                return i, node

            new_i, child_node = process_node(i)
            node.child_nodes.append(child_node)
            i = new_i + 1
        return i, node
    return process_node(0)

def dump_node(html, node, depth=0):
    prefix = ''.join(['.'] * depth)
    result = ''
    node_text = decode_text(html[node.token.span[0]:node.token.span[1] + 1])
    result += prefix + node_text

    for child_node in node.child_nodes:
        result += '\n' + dump_node(html, child_node, depth + 1)

    if node.token.type == TokenType.TAG_OPEN:
        result += '\n' + prefix + '</' + node_text[1:node_text.find(' ')] + '>'
    return result

def find_element(html, node, tag_name, class_name=None):
    if node.token.type == TokenType.TAG_OPEN:
        node_tag_name = get_tag_name(html, node)
        if node_tag_name == tag_name:
            if class_name is None:
                return node
            class_names = get_class_names(html, node)
            if class_name in class_names:
                return node

        for child_node in node.child_nodes:
            elem = find_element(html, child_node, tag_name, class_name)
            if elem:
                return elem

def get_tag_name(html, node):
    sp_index = html.find(b' ', node.token.span[0], node.token.span[1])
    return html[node.token.span[0] + 1:sp_index if sp_index != -1 else node.token.span[1]].decode('ascii', 'ignore')

def get_class_names(html, node):
    node_text = html[node.token.span[0]:node.token.span[1]].decode('ascii', 'ignore')
    attributes = node_text.split()
    for attr in attributes:
        parts = attr.split('=')
        if parts[0] == 'class':
            return parts[1].strip('"').split()
    return []

def get_content_span(html, node):
    match node.token.type:
        case TokenType.TAG_OPEN:
            span = [node.token.span[1] + 1, node.token.span[1] + 1]
            for child_node in node.child_nodes:
                child_span = get_content_span(html, child_node)
                span = [span[0], child_span[1]]
            return span
        case TokenType.TEXT:
            return node.token.span

def get_text_content(html, node):
    match node.token.type:
        case TokenType.TAG_OPEN:
            txt = ''
            for child_node in node.child_nodes:
                txt += get_text_content(html, child_node)
            return txt
        case TokenType.TEXT:
            node_text = decode_text(html[node.token.span[0]:node.token.span[1] + 1])
            return node_text

def get_text_content_safe(html):
    tokens = tokenize(html)
    txt = ''
    for token in tokens:
        if token.type == TokenType.TEXT:
            txt += decode_text(html[token.span[0]:token.span[1] + 1])
    return txt

def find_child_nodes(html, node, tag_name):
    found = []
    if node.token.type == TokenType.TAG_OPEN:
        for child_node in node.child_nodes:
            if child_node.token.type == TokenType.TAG_OPEN:
                child_tag_name = get_tag_name(html, child_node)
                if child_tag_name == tag_name:
                    found += [child_node]
    return found

def decode_text(txt):
    return bytes(filter(lambda x: x >= 0x20, txt)).decode('cp1252', 'ignore')
