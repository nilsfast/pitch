class Context(object):
    def __init__(self):
        self.definitions = {}

    def add(self, name, value):
        self.definitions[name] = value

    def find(self, name):
        return self.definitions.get(name)

    def __repr__(self):
        return f"Context({self.definitions})"


class ContextVar(object):
    def __init__(self, liveness, scope):
        self.liveness = liveness
        self.scope = scope

    def __repr__(self):
        return f"ContextVar({self.liveness}, {self.scope})"
