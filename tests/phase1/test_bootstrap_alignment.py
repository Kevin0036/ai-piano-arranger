from __future__ import annotations

import unittest

import torch

from bootstrap_arranger.alignment import align_pooled_features, cosine_distance_matrix, dtw_alignment_path


class BootstrapAlignmentTest(unittest.TestCase):
    def test_cosine_distance_matrix_shape(self) -> None:
        source = torch.tensor([[1.0, 0.0], [0.0, 1.0]])
        target = torch.tensor([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
        distances = cosine_distance_matrix(source, target)
        self.assertEqual(tuple(distances.shape), (2, 3))

    def test_dtw_path_is_monotonic(self) -> None:
        cost = torch.tensor(
            [
                [0.0, 1.0, 2.0],
                [1.0, 0.0, 1.0],
                [2.0, 1.0, 0.0],
            ]
        )
        path = dtw_alignment_path(cost)
        self.assertEqual(path[0], (0, 0))
        self.assertEqual(path[-1], (2, 2))
        self.assertTrue(all(a0 <= a1 and b0 <= b1 for (a0, b0), (a1, b1) in zip(path, path[1:])))

    def test_align_pooled_features_returns_jsonable_path(self) -> None:
        source = torch.tensor([[1.0, 0.0], [0.0, 1.0]])
        target = torch.tensor([[1.0, 0.1], [0.1, 1.0]])
        alignment = align_pooled_features(source, target)
        self.assertIn("path", alignment)
        self.assertEqual(alignment["path"][0], [0, 0])


if __name__ == "__main__":
    unittest.main()
