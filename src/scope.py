import logging
from src.pitchtypes import TypeBase


class ScopeEntry():
    def __init__(self, name: str, type: str):
        self.name = name
        self.type = type

    def __repr__(self):
        return f'({self.name}: {self.type})'


class Scope():
    def __init__(self, identifier, parent=None, inject=None):
        self.identifier = identifier
        self.parent = parent
        self.entries: list[ScopeEntry] = []
        if inject:
            for entry in inject:
                self.add(entry.name, entry.type)

    def add(self, name: str, type: TypeBase):
        logging.info(f"Adding {name} to scope {self.identifier}")
        self.entries.append(ScopeEntry(name, type))

    def find(self, name: str):
        for entry in self.entries:
            if entry.name == name:
                return entry

        if self.parent:
            return self.parent.find(name)

        return None

    def __setitem__(self, name: str, type: str):
        self.add(name, type)

    def __getitem__(self, name: str):
        for entry in self.entries:
            if entry.name == name:
                return entry

        return None

    def __repr__(self):
        return f'Scope({self.entries})'
