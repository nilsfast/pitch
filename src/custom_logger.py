class CustomLogger:

    def __init__(self, name: str):
        self.spans = []
        self.name = name

    def start_span(self, name: str):
        self.spans.append(name)
        print(f"[{self.name} START] {name}")

    def end_span(self):
        if self.spans:
            span = self.spans.pop()
            print(f"[{self.name} END] {span}")
        else:
            print(f"[{self.name} END] No spans to end")

    def log(self, message: str):
        indent = "  " * len(self.spans)
        print(f"{indent} {message}")

    def error(self, message: str):
        indent = "  " * len(self.spans)
        print(f"{indent}[ERROR] {message}")

    def info(self, message: str):
        indent = "  " * len(self.spans)
        print(f"{indent}[INFO] {message}")

    def debug(self, message: str):
        indent = "  " * len(self.spans)
        print(f"{indent}[DEBUG] {message}")
