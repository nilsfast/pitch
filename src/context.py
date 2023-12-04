from abc import ABC
from dataclasses import dataclass
import random
import string


class Context(object):
    def __init__(self):
        self.definitions = {}
        self.types = {}
        self.symbols = {}

    def add(self, name, value):
        self.definitions[name] = value

    def add_type(self, name, context):
        self.types[name] = context

    def find(self, name):
        return self.definitions.get(name)

    def symbol(self, name):
        return self.symbols.get(name)

    def register_symbol(self, name):
        if name in self.symbols:
            rand_str = "".join(random.choices(
                string.ascii_lowercase, k=5))
            return self.register_symbol(f"{name}_{rand_str}")
        self.symbols[name] = name
        return name

    def __repr__(self):
        return f"Context({self.definitions})"


class ContextVar(object):
    def __init__(self, liveness, scope):
        self.liveness = liveness
        self.scope = scope

    def __repr__(self):
        return f"ContextVar({self.liveness}, {self.scope})"
