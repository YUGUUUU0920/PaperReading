from __future__ import annotations

import unittest

from backend.app.core.utils import normalize_title_display


class NormalizeTitleDisplayTests(unittest.TestCase):
    def test_removes_latex_artifacts_from_titles(self) -> None:
        raw_title = r"$\bfΦ_\textrmFlow$: Differentiable Simulations for PyTorch, TensorFlow and Jax"
        self.assertEqual(
            normalize_title_display(raw_title),
            "ΦFlow: Differentiable Simulations for PyTorch, TensorFlow and Jax",
        )

    def test_preserves_meaningful_math_tokens(self) -> None:
        raw_title = r"$\rm E(3)$-Equivariant Actor-Critic Methods"
        self.assertEqual(normalize_title_display(raw_title), "E(3)-Equivariant Actor-Critic Methods")


if __name__ == "__main__":
    unittest.main()
