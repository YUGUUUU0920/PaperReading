from __future__ import annotations

import unittest

from backend.app.core.utils import infer_link_kind, normalize_title_display


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


class ResourceLinkKindTests(unittest.TestCase):
    def test_ignores_non_resource_code_labels(self) -> None:
        self.assertEqual(infer_link_kind("https://neurips.cc/public/CodeOfConduct", "Code of Conduct"), "")
        self.assertEqual(infer_link_kind("https://github.com/mlresearch/v235", "Github Account"), "")
        self.assertEqual(
            infer_link_kind("https://raw.githubusercontent.com/mlresearch/v235/main/assets/paper.pdf", "Download PDF"),
            "",
        )


if __name__ == "__main__":
    unittest.main()
