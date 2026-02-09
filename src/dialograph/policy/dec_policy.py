# ============================================================
# 5. DECLARATIVE POLICY (WHAT HUMANS WRITE)
# ============================================================

@dataclass
class DeclarativePolicy:
    id: str
    when: Condition
    do: str
    rather_than: str
    because: str
    priority: int = 50
    confidence: float = 1.0

