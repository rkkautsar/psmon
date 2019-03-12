class Watcher(object):
    watched_attrs = []

    def fallback(self, res):
        pass

    def register_root(self, pid):
        pass

    def update(self, processes_info):
        pass

    def get_stats(self, pid):
        pass

    def should_terminate(self, pid):
        return False

    def get_error(self, pid):
        return None, None
