from typing import Any


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

    def __eq__(self, other):
        if not isinstance(other, TreeNode):
            return False
        return (
            self.val == other.val
            and self.left == other.left
            and self.right == other.right
        )


"""
construct tree from array, in BFS order
"""


def array_to_tree(array):
    return array_to_binary_tree(array)


def array_to_binary_tree(array: list[Any]):
    l = len(array)
    if l == 0:
        return None

    nodes = [TreeNode(e) if e else None for e in array]
    for i, n in enumerate(filter(None, nodes), start=1):
        n.left = nodes[2 * i - 1] if (2 * i - 1) < l else None
        n.right = nodes[2 * i] if (2 * i) < l else None

    return nodes[0]


if __name__ == "__main__":
    import unittest

    class TestCase(unittest.TestCase):
        def test_array_to_binary_tree_simple(self):
            actual = TreeNode(1, left=TreeNode(2), right=TreeNode(3))
            built = array_to_binary_tree([1, 2, 3])
            self.assertEqual(actual, built, "array_to_binary_tree incorrect")

        def test_array_to_binary_tree_simple2(self):
            actual = TreeNode(1, left=TreeNode(3), right=TreeNode(2))
            built = array_to_binary_tree([1, 3, 2])
            self.assertEqual(actual, built, "array_to_binary_tree incorrect")

        def test_array_to_binary_tree_complex(self):
            actual = TreeNode(
                3,
                left=TreeNode(
                    5,
                    left=TreeNode(6),
                    right=TreeNode(2, left=TreeNode(7), right=TreeNode(4)),
                ),
                right=TreeNode(1, left=TreeNode(9), right=TreeNode(8)),
            )
            built = array_to_binary_tree([3, 5, 1, 6, 2, 9, 8, None, None, 7, 4])
            self.assertEqual(actual, built, "array_to_binary_tree incorrect")

        def test_array_to_binary_tree_complex2(self):
            actual = TreeNode(
                3,
                left=TreeNode(
                    5,
                    left=TreeNode(6),
                    right=TreeNode(7),
                ),
                right=TreeNode(
                    1,
                    left=TreeNode(4),
                    right=TreeNode(2, left=TreeNode(9), right=TreeNode(8)),
                ),
            )
            built = array_to_binary_tree(
                [3, 5, 1, 6, 7, 4, 2, None, None, None, None, None, None, 9, 8]
            )
            self.assertEqual(actual, built, "array_to_binary_tree incorrect")

    unittest.main()
