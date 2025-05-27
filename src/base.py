class ASTObject:
    def repr(self):
        return repr(self)

    def inline_repr(self):
        return self.repr()

    def rich_repr(self):
        return self.repr().replace("[", "\\[")

    def all_attrs(self):
        return {}

    context = {}
    pre_c_hooks = []
    post_c_hooks = []
    location = None
