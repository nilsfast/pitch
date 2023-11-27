import logging
from abc import ABC, abstractmethod


def printlog(*args):
    logging.info(" ".join([str(arg) for arg in args]))


class Base(ABC):
    pass

    def __format__(self, format_spec):
        return self.__repr__()
