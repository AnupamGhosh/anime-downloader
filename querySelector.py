import logging
from html.parser import HTMLParser

class GetElements(object):
  '''
  Here we are searching for nodes that match a selector in a given html
  Think of querySelector in javascript, a string of matching nodes separated by space
  This thought can be transformed into finding longest common subsequence between
  the selector string and the html string
  '''
  def __init__(self, selector):
    rows = 1000
    self.N = len(selector)
    self.lcs = [[0 for _ in range(self.N + 1)] for _ in range(rows)]
    self.nodes = Search_Node.get_nodes(selector)
    self.row = 0
    self.elements = []

  def add_node(self, tag, attr):
    self.row += 1
    for c in range(1, self.N + 1):
      if self.nodes[c - 1].match(tag, attr):
        max_matched = self.lcs[self.row - 1][c - 1] + 1
        self.lcs[self.row][c] = max_matched
        if max_matched == self.N:
          self.elements.append(attr)
      else:
        self.lcs[self.row][c] = max(self.lcs[self.row - 1][c], self.lcs[self.row][c - 1])

  def remove_node(self):
    self.row -= 1

  def matched_elements(self):
    return self.elements

# Node that is searched in the DOM
class Search_Node(object):
  def __init__(self, tag, classes, attr):
    self.tag = tag
    self.classes = classes
    self.attr = attr
    assert 'class' not in self.attr

  def match(self, tag, attr):
    if self.tag != tag:
      return False
    class_names = attr['class'].split(' ') if 'class' in attr else []
    if not all(class_name in class_names for class_name in self.classes):
      return False
    for key in self.attr:
      if key not in attr or self.attr[key] != attr[key]:
        return False
    return True

  @staticmethod
  def get_nodes(search_nodes):
    nodes = []
    for item in search_nodes:
      classes = item['class'] if 'class' in item else []
      attr = item['attr'] if 'attr' in item else {}
      nodes.append(Search_Node(item['tag'], classes, attr))
    return nodes

class SearchNodeParser(HTMLParser):
  def __init__(self, dom): # dom is a subclass of GetElements
    HTMLParser.__init__(self)
    self.dom = dom

  def handle_starttag(self, tag, attrs):
    attr = SearchNodeParser.attrs2dict(attrs)
    self.dom.add_node(tag, attr)

  def handle_endtag(self, tag):
    self.dom.remove_node()

  @staticmethod
  def attrs2dict(attrs):
    return {name: value for name, value in attrs}
