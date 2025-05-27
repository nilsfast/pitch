class NodeVisitor:
    def visit(self, node):
        """
        Recursively visit each node in the AST and perform operations.
        If the visit method returns a value, replace the node with the returned value.
        """
        method_name = f"visit_{type(node).__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        result = visitor(node)
        return result if result is not None else node

    def generic_visit(self, node):
        """
        Default visit method for nodes without a specific visitor method.
        If the node has children, recursively visit and replace them if needed.
        """
        if hasattr(node, "children"):
            new_children = []
            for child in node.children:
                new_child = self.visit(child)
                new_children.append(new_child)
            node.children = new_children
        return node
