class Node:
    def __init__(self, data):
        self.data = data
        self.next = None


class LinkedList:
    """
    Singly Linked list with push, pop, append, insert methods.
    """
    _length: int = 0

    def __init__(self):
        self.head = None

    def push(self, value):
        new_node = Node(value)
        if self.head:
            new_node.next = self.head
            self.head = new_node
        else:
            self.head = new_node
        self._length += 1

    def append(self, value):
        new_node = Node(value)
        if self.head:
            temp = self.head
            while temp.next:
                temp = temp.next
            else:
                temp.next = new_node
        else:
            self.head = new_node
        self._length += 1

    def insert(self, index, value):
        if index <= 0:
            self.push(value)
        elif index >= self._length - 1:
            self.append(value)
        else:
            temp = pre = self.head
            while index:
                pre = temp
                temp = temp.next
                index -= 1
            else:
                new_node = Node(value)
                new_node.next = temp
                pre.next = new_node

    def setter(self, lst):
        """
        This method will push a normal list values to a LinkedList Nodes.
        """
        self.head = None
        self._length = 0
        for value in lst[::-1]:
            self.push(value)

    @staticmethod
    def getter(head=None) -> list:
        """
        This method will return the current LinkedList or the CLinkedList to a normal list
        """
        temp = head
        if not temp:
            return []
        result: list = []
        while temp.next:
            result.append(temp.data)
            temp = temp.next
        else:
            result.append(temp.data)
        return result

    def pop(self, index=0):
        if self._length:
            if index <= 0:
                value = self.head.data
                self.head = self.head.next
            else:
                temp = pre = self.head
                while index and temp.next:
                    pre = temp
                    temp = temp.next
                    index -= 1
                else:
                    value = temp.data
                    pre.next = temp.next
            self._length -= 1
            return value
        else:
            return None

    @staticmethod
    def sorted_merges(head1,
                      head2,
                      condition_method=lambda head: isinstance(head.data, str)):
        """
        Merging two LinkedList which are sorted & also it can contains anything else instead integer
        condition_method is the specific data which helps to pass the sorting merge
        """
        if head1 is None:
            return head2
        if head2 is None:
            return head1

        # Recursive merging based on smaller value
        if condition_method(head1):
            head1.next = LinkedList.sorted_merges(head1.next, head2, condition_method)
            return head1
        elif condition_method(head2):
            head2.next = LinkedList.sorted_merges(head2.next, head1, condition_method)
            return head2
        elif head1.data <= head2.data:
            head1.next = LinkedList.sorted_merges(head1.next, head2, condition_method)
            return head1
        else:
            head2.next = LinkedList.sorted_merges(head1, head2.next, condition_method)
            return head2

    @staticmethod
    def print(head):
        if head:
            _str = ""
            temp = head
            while temp.next:
                _str += str(temp.data) + " -> "
                temp = temp.next
            else:
                _str += str(temp.data)
            return _str
        else:
            return "Warning: Linked-List Is Empty!"

    def __str__(self):
        if self.head:
            _str = ""
            temp = self.head
            while temp.next:
                _str += str(temp.data) + " -> "
                temp = temp.next
            else:
                _str += str(temp.data)
            return _str
        else:
            return "Warning: Linked-List Is Empty!"

    def __len__(self):
        return self._length


class Queue:
    """
    Simple algorithm for actions_queue ordering and sorting 
    """

    @staticmethod
    def merge_prev_current_queue(prev_queue_actions: list,
                                 scheduled_actions: list,
                                 condition=lambda action: not action.scheduledDate and not action.nextPeriod):
        """
        This method uses for merging two actions list on the queue by each data refreshing. for example:
        - We have already some scheduled actions, then user will add some actions to the queue manually. 
            -> scheduled_actions = [Action1, Action2, Action3]
            -> user add the selected action to the queue -> [Action1, "Action4(user added)", Action2, Action3]
        -If the data refresh happens or any of these action delete on the later the queue must be update automatically by the correct sorting.
            -> prev_queue = [Action1, "Action4(user added)", Action2, Action3]
            -> new_data_from_api = [Action2, Action3, Action5]
            -> the Queue view should be like this = ["Action4(user added)", Action2, Action3, Action5]
        """
        # Returns if one of the lists are empty!
        if not prev_queue_actions:
            return scheduled_actions
        if not scheduled_actions:
            return prev_queue_actions
        head_nodes = []
        tail_nodes = []
        # Appending until the head value is added by user
        while prev_queue_actions and condition(prev_queue_actions[0]):
            head_nodes.append(prev_queue_actions.pop(0))
        if not prev_queue_actions:
            return head_nodes + scheduled_actions
        # Inserting until the tail value is added by user
        while prev_queue_actions and condition(prev_queue_actions[-1]):
            tail_nodes.insert(0, prev_queue_actions.pop())
        if len(prev_queue_actions) < 3:
            return head_nodes + scheduled_actions + tail_nodes
        # A copy of the createdAt from the current actions
        scheduled_actions_ids = [val.createdAt for val in scheduled_actions]
        for i in range(1, len(prev_queue_actions) - 1):
            if not condition(prev_queue_actions[i]):
                continue
            for j in range(i + 1, len(prev_queue_actions)):
                if prev_queue_actions[j].createdAt in scheduled_actions_ids:
                    index = scheduled_actions_ids.index(prev_queue_actions[j].createdAt)
                    scheduled_actions_ids.insert(index, prev_queue_actions[i].createdAt)
                    scheduled_actions.insert(index, prev_queue_actions[i])
                    break
            else:
                tail_nodes.insert(0, prev_queue_actions[i])
        return head_nodes + scheduled_actions + tail_nodes


if __name__ == "__main__":
    # Examples...
    import json
    import random
    from newAgent.src.data.data_parser import Actions

    with open("../../test_data.txt", "rb") as file:
        actions = [Actions(action) for action in json.loads(file.read())['actions'] if action.get("title") != "test"]
    print(len(actions))
    publish_contents = [action for action in actions if action.type == "PUBLISH_CONTENT"]
    print(len(publish_contents))
    publish_contents_1, publish_contents_2 = publish_contents[:len(publish_contents) // 2], publish_contents[
                                                                                            len(publish_contents) // 2:]

    custom_actions = [action for action in actions if action.title in ["BOOOOMMMMMMMMM", "ParsaQueueTest"]]
    custom_actions = sorted(custom_actions, key=lambda action: action.scheduledLaunchDiff)
    for _ in range(5):
        custom_actions.insert(random.randint(0, len(custom_actions)), random.choice(actions))

    # custom_actions = []
    # for title in ["Linkedin action test running", "BOOOOMMMMMMMMM", "ParsaQueueTest", "Tech Savvy Freelancer", "BugTestParsa"]:
    #     for action in actions:
    #         if action.title == title and action.title not in [ctitle.title for ctitle in custom_actions]:
    #             custom_actions.append(action)

    sorted_action2 = sorted(publish_contents_1, key=lambda action: action.scheduledLaunchDiff)

    print("Actions Current: ", len(sorted_action2), sorted_action2)
    print("Prev Actions: ", len(custom_actions), custom_actions)

    res = Queue.merge_prev_current_queue(prev_queue_actions=custom_actions, scheduled_actions=sorted_action2)

    date_list = [r.scheduledDateCurrentZone.strftime("%B %d, %Y, %H:%M") if r.scheduledDate else "!NoTime!" for r in
                 res]

    print("Results: ", [(res_act, date) for date, res_act in zip(date_list, res)])
