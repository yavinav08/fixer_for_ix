from lib2to3 import fixer_base
from lib2to3.fixer_util import Name
from lib2to3.pytree import Node, Leaf
from lib2to3.pgen2 import token
from lib2to3.pygram import python_symbols as syms


def is_integer_like(self, node):
    if isinstance(node, Leaf):
        return node.type == token.NUMBER and node.value.isdigit()

    # List or slice check
    if isinstance(node, Node):

        if node.children[0].type == 9:
            return all(is_integer_like(self, child) for child in node.children[1:-1:2])

        if node.children[0].type == 11:  # got a slice

            if len(node.children) > 1:
                # a number or comma expected
                if node.children[1].type == token.NUMBER or node.children[1].type == 12:
                    if len(node.children) > 2:
                        return is_integer_like(self, node.children[2])
                    else:
                        return True
                else:
                    return False
            else:
                return True

        if node.children[0].type == 2:  # got a number
            if len(node.children) > 1:
                # comma or slice expected
                if node.children[1].type == 12 or node.children[1].type == 11:
                    if len(node.children) > 2:
                        return is_integer_like(self, node.children[2])
                    else:
                        return True
                else:
                    return False
            return True

        if node.children[0].type == 323:  # got a slice
            child = node.children[0]
            if child.children[0].type == token.NUMBER:
                if len(child.children) > 2:
                    if child.children[2].type == token.NUMBER:
                        if len(child.children) > 3:
                            return is_integer_like(self, child.children[3])
                        else:
                            return True
                else:
                    return True
            else:
                return False

    return False


class FixCustomFixers(fixer_base.BaseFix):
    BM_compatible = True

    PATTERN = """
              power< any+ trailer< '.' 'ix' > trailer< any* > >
              """

    def match(self, node):
        # Check if the node represents a method call
        if isinstance(node, Node) and node.children:
            # Look for a trailer node with '.' followed by 'ix'
            for child in node.children:
                if isinstance(child, Node) and child.type == self.syms.trailer:
                    if len(child.children) > 1 and isinstance(child.children[0], Leaf) and child.children[0].type == token.DOT and isinstance(child.children[1], Leaf) and child.children[1].value == 'ix':
                        return True
        return False

    def transform(self, node, results):
        # Call the transform method when a match is found
        ix_child = None
        for child in node.children:

            if isinstance(child, Node) and child.type == self.syms.trailer:
                dot_child = child.children[0]
                method_child = child.children[1]

                if ix_child is None and isinstance(dot_child, Leaf) and dot_child.type == token.DOT and isinstance(method_child,
                                                                                              Leaf) and method_child.value == 'ix':
                    ix_child = child
                elif ix_child is not None:
                    index_child = child
                    if is_integer_like(self, index_child.children[1]):
                        ix_child.children[1] = Leaf(token.NAME, 'iloc', prefix=ix_child.children[1].prefix)
                    else:
                        ix_child.children[1] = Leaf(token.NAME, 'loc', prefix=ix_child.children[1].prefix)
                    ix_child = None
        return node
