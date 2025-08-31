from typing import Any


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

    def __eq__(self, other):
        if not isinstance(other, TreeNode):
            return False
        return self.val == other.val and self.left == other.left and self.right == other.right

"""
construct tree from array, in BFS order
"""
def array_to_tree(array):
  if len(array) == 0:
    return None

  level_node = []
  for e in array:
    n = TreeNode(e) if e is not None else None
    if len(level_node) > 0:
      p, d = level_node.pop(0)
      if d == 'l':
        p.left = n
      else:
        p.right = n
    else:
      root = n
    level_node += [(n, 'l'), (n, 'r')]

  return root

def array_to_binary_tree(array: list[Any]):
    l = len(array)
    if l == 0:
        return None

    nodes = [TreeNode(e) if e else None for e in array]
    for i, n in enumerate(filter(None, nodes), start = 1):
        n.left = nodes[2*i-1] if (2*i-1) < l else None
        n.right = nodes[2*i] if (2*i) < l else None

    return nodes[0]


if __name__ == '__main__':
    # test array_to_binary_tree
    actual1 = TreeNode(1, left=TreeNode(2), right=TreeNode(3))
    built1 = array_to_binary_tree([1,2,3])
    assert actual1 == built1, 'array_to_binary_tree incorrect'
