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

    def get_accumulated_stats(self):
        max_memory = self.max_memory
        cpu_time = self.cpu_time

        for child in self.children:
            child_stats = child.get_accumulated_stats()
            max_memory += child_stats["max_memory"]
            cpu_time += child_stats["cpu_time"]

        return dict(max_memory=max_memory, cpu_time=cpu_time)
