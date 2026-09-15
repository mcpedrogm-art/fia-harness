"""Métrica de regresión del Parser Engine (F2): tasa de campos resueltos.

Corpus: 20 PRDs variados (idiomas, headings no estándar, sin headings, negritas,
tablas, prosa). Métrica medida al cerrar F2 (v3.0.0a2): **81% de campos resueltos**
(alta+media) y 70% con confianza alta. El umbral de este test es el suelo de
regresión: si baja, el parser empeoró y hay que justificarlo.
"""

import unittest
from pathlib import Path

from fia_harness.parser import prd

PRDS_DIR = Path(__file__).resolve().parent / "fixtures" / "prds"
FIELDS = ("title", "problem", "users", "features", "out_of_scope")
MIN_RESOLVED_RATE = 0.75


def _is_resolved(meta: dict, field: str) -> bool:
    return meta["confidence"][field]["level"] != "ninguna"


class CorpusMetricTests(unittest.TestCase):
    def test_el_corpus_tiene_al_menos_20_prds(self):
        self.assertGreaterEqual(len(list(PRDS_DIR.glob("*.md"))), 20)

    def test_tasa_de_campos_resueltos_no_baja_del_umbral(self):
        total = resolved = 0
        for path in sorted(PRDS_DIR.glob("*.md")):
            meta = prd.extract_prd_metadata(path)
            for field in FIELDS:
                total += 1
                resolved += 1 if _is_resolved(meta, field) else 0
        rate = resolved / total
        self.assertGreaterEqual(rate, MIN_RESOLVED_RATE,
                                f"tasa de campos resueltos: {resolved}/{total} = {rate:.0%}")

    def test_ningun_campo_resuelto_sin_nivel_de_confianza(self):
        for path in sorted(PRDS_DIR.glob("*.md")):
            meta = prd.extract_prd_metadata(path)
            for field in FIELDS:
                with self.subTest(prd=path.name, field=field):
                    conf = meta["confidence"].get(field)
                    self.assertIsNotNone(conf, "campo sin entrada de confianza")
                    self.assertIn(conf["level"], prd.CONFIDENCE_LEVELS)
                    self.assertTrue(conf["method"], "método vacío")
                    if field in ("features", "out_of_scope"):
                        has_value = bool(meta[field])
                    elif field in ("problem", "users"):
                        has_value = meta[field] != prd.DEFAULT_TEXT
                    else:
                        has_value = bool(meta["title"])
                    self.assertEqual(has_value, conf["level"] != "ninguna",
                                     f"{path.name}/{field}: valor={has_value} nivel={conf['level']}")

    def test_unresolved_es_exactamente_lo_que_tiene_confianza_ninguna(self):
        for path in sorted(PRDS_DIR.glob("*.md")):
            meta = prd.extract_prd_metadata(path)
            ninguna = [f for f in FIELDS if meta["confidence"][f]["level"] == "ninguna"]
            self.assertEqual(sorted(meta["unresolved"]), sorted(ninguna), path.name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
