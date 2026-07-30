from __future__ import annotations

import unittest

import torch

from bootstrap_arranger.decoder_io import build_picogen_decoder_batch
from bootstrap_arranger.model import BootstrapConditionAdapter


class BootstrapModelTest(unittest.TestCase):
    def test_adapter_outputs_picogen_shape(self) -> None:
        model = BootstrapConditionAdapter(input_dim=8, d_model=16, hidden_dim=32, dropout=0.0)
        source_features = torch.randn(2, 5, 8)
        output = model.encode_source(source_features)
        picogen_tensor = output.to_picogen_tensor()
        self.assertEqual(tuple(picogen_tensor.shape), (2, 5, 2, 16))

    def test_decoder_batch_builder_shapes(self) -> None:
        condition_embeddings = torch.randn(4, 2, 16)
        token_ids = torch.tensor([5, 6, 7], dtype=torch.long)
        batch = build_picogen_decoder_batch(
            condition_embeddings=condition_embeddings,
            target_token_ids=token_ids,
            max_seq_len=16,
            bos_token_id=1,
        )
        self.assertEqual(tuple(batch["input_ids"].shape), (1, 16))
        self.assertEqual(tuple(batch["input_cond_embs"].shape), (1, 16, 2, 16))


if __name__ == "__main__":
    unittest.main()
