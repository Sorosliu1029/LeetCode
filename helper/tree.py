class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

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
