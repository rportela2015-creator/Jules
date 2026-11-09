import json
import os
import tempfile
from decimal import Decimal
from typing import Any, Dict, List, Optional
from src.utils.math import dec

class TaxPersistentStore:
    """Guarda as alíquotas de REFERÊNCIA (ex.: CBS 8,8 / IBS 17,7). A alíquota efetiva do ano vem do calendário."""

    def __init__(self, path: str = "tax_state_config.json"):
        self.path = path
        self._s = self._load()

    def _load(self) -> Dict[str, Optional[str]]:
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as fh:
                d = json.load(fh)
            return {"aliquota_cbs_padrao": d.get("aliquota_cbs_padrao"), "aliquota_ibs_padrao": d.get("aliquota_ibs_padrao")}
        return {"aliquota_cbs_padrao": None, "aliquota_ibs_padrao": None}

    def _save(self) -> None:
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(self.path)), suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(self._s, fh, indent=4, ensure_ascii=False)
        os.replace(tmp, self.path)  # escrita atômica

    def set_persistent_rates(self, cbs_pct: Any = None, ibs_pct: Any = None, user_override: bool = False) -> List[str]:
        """Retorna a lista de campos IGNORADOS (já preenchidos e sem override) — nada é silencioso."""
        ignored, changed = [], False
        for key, val in (("aliquota_cbs_padrao", cbs_pct), ("aliquota_ibs_padrao", ibs_pct)):
            if val is None:
                continue
            if self._s.get(key) is None or user_override:
                self._s[key] = str(dec(val))
                changed = True
            else:
                ignored.append(key)
        if changed:
            self._save()
        return ignored

    def _get(self, key: str, label: str) -> Decimal:
        v = self._s.get(key)
        if v is None:
            raise ValueError(f"Alíquota de referência {label} ainda não definida.")
        return dec(v)

    @property
    def cbs_pct(self) -> Decimal:
        return self._get("aliquota_cbs_padrao", "CBS")

    @property
    def ibs_pct(self) -> Decimal:
        return self._get("aliquota_ibs_padrao", "IBS")
