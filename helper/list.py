class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def array_to_list(array):
    dummy = ListNode()
    p = dummy
    for i in array:
        p.next = ListNode(i)
        p = p.next

    return dummy.next


def print_list(l):
    print("[", end="")
    while l:
        print(l.val, ", ", end="", sep="")
        l = l.next
    print("]")


if __name__ == "__main__":
    import unittest

    class TestCase(unittest.TestCase):

        def test_array_to_list(self):
            actual = ListNode(1, next=ListNode(2, next=ListNode(3)))
            built = array_to_list([1, 2, 3])
            p1, p2 = actual, built
            while p1 and p2:
                self.assertEqual(p1.val, p2.val, "array_to_list incorrect")
                p1 = p1.next
                p2 = p2.next

            self.assertIsNone(p1, "array_to_list incorrect")
            self.assertIsNone(p2, "array_to_list incorrect")

        def test_print_list(self):
            import io
            from unittest import mock
            with mock.patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
                print_list(array_to_list([1, 2, 3]))
                self.assertEqual(mock_stdout.getvalue(), "[1, 2, 3, ]\n", "print_list incorrect")

    unittest.main()

