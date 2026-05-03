from typing import Callable, Dict

from ..core import review_decision


def build_review_chain() -> Callable[[Dict, Dict], Dict]:
    """
    Build a callable review chain. If LangChain is available, it can be swapped
    in later without changing the interface.
    """
    def _chain(compliance_result: Dict, quality_signal: Dict) -> Dict:
        return review_decision(compliance_result, quality_signal)

    return _chain
