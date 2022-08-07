
class Writer():
    """
    Helper-class to write code to. Can code as string
    """
    out = []
    pre = []
    post = []

    def __init__(self) -> None:
        self.out = []

    def emit(self, depth, code):
        self.out.append('   ' * depth + code)

    def emit_post(self, elem):
        self.post.append(elem)

    def emit_pre(self, elem):
        self.pre.append(elem)
        

    def __str__(self):
        all = self.pre + self.out + self.post
        return "\n".join(all)


class MemWriter():
    """
    Helper-class to write code to.
    """
    out = []
    pre = []
    post = []

    def __init__(self) -> None:
        self.out = []

    def emit(self, depth, code):
        self.out.append(code)

    def emit_post(self, elem):
        self.post.append(elem)

    def emit_pre(self, elem):
        self.pre.append(elem)
        
    def get_all(self):
        return self.pre + self.out + self.post

