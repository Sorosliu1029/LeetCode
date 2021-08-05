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