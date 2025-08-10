from typing import Dict, List, Optional
from .symbols import Symbol

class ScopeStack:
    def __init__(self):
        self.stack: List[Dict[str, Symbol]] = [ {} ]  # global

    def push(self):
        self.stack.append({})

    def pop(self):
        self.stack.pop()

    def define(self, sym: Symbol) -> bool:
        if sym.name in self.symbols:
            return False
        self.symbols[sym.name] = sym
        return True

    def resolve(self, name: str) -> Optional[Symbol]:
        cur = self
        while cur:
            if name in cur.symbols:
                return cur.symbols[name]
            cur = cur.parent
        return None
