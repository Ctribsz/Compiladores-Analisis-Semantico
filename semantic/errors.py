from dataclasses import dataclass

@dataclass
class SemError:
    line: int
    col: int
    code: str
    msg: str

class ErrorCollector:
    def __init__(self):
        self.errors = []

    def report(self, line: int, col: int, code: str, msg: str):
        self.errors.append(SemError(line, col, code, msg))

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def pretty(self) -> str:
        return "\n".join([f"[{e.code}] ({e.line}:{e.col}) {e.msg}" for e in self.errors])
