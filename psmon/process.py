class ProcessNode:
    def __init__(self, pid):
        self.pid = pid
        self.parent = None
        self.children = []
        self.max_memory = 0
        self.cpu_time = 0
        self.finished = False

    def add_child(self, child):
        self.children.append(child)
        child.parent = self

    def update(self, cpu_time, memory):
        self.max_memory = max(self.max_memory, memory)
        self.cpu_time = cpu_time

        if self.parent:
            self.parent.update(
                self.parent.cpu_time + cpu_time,
                self.parent.max_memory + self.max_memory,
            )
