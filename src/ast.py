class ASTNode:
    def __init__(self):
        self.children = []

    def add_child(self, child):
        self.children.append(child)


class LineNode(ASTNode):
    def __init__(self):
        super().__init__()


class ChordNode(ASTNode):
    def __init__(self, name):
        super().__init__()
        self.name = name

    def transpose(self, amount):
        self.name = transpose_chord(self.name, amount)


class TextNode(ASTNode):
    def __init__(self, text):
        super().__init__()
        self.text = text


class SpacerNode(ASTNode):
    def __init__(self, length):
        super().__init__()
        self.length = length


class SectionHeaderNode(ASTNode):
    def __init__(self, name):
        super().__init__()
        self.name = name


class CommentNode(ASTNode):
    def __init__(self, comment):
        super().__init__()
        self.comment = comment


def transpose_chord(chord, amount): ...
