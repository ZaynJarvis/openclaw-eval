import argparse
import asyncio
import importlib
import unittest
from unittest import mock


eval_module = importlib.import_module("eval")


def locomo_sample(sample_id: str) -> dict:
    return {
        "sample_id": sample_id,
        "conversation": {
            "speaker_a": "Alice",
            "speaker_b": "Bob",
            "session_1": [
                {"speaker": "Alice", "text": "hello"},
            ],
        },
        "qa": [
            {
                "question": "What did Alice say?",
                "answer": "hello",
                "category": 1,
                "evidence": ["D1:1"],
            }
        ],
    }


class EvalUserKeyTests(unittest.TestCase):
    def test_json_ingest_defaults_to_one_user_per_sample(self):
        args = argparse.Namespace(
            input="locomo.json",
            sample=None,
            sessions=None,
            tail="[]",
            user=None,
            viking=False,
            base_url="http://127.0.0.1:18789",
            token="token",
            output=None,
        )
        sent_users = []

        def fake_send_message(_base_url, _token, user, _message):
            sent_users.append(user)
            return "ok", {}

        with (
            mock.patch.object(
                eval_module,
                "load_locomo_data",
                return_value=[locomo_sample("conv-26"), locomo_sample("conv-30")],
            ),
            mock.patch.object(eval_module, "send_message", side_effect=fake_send_message),
            mock.patch.object(eval_module, "get_session_id", return_value=None),
            mock.patch.object(eval_module, "reset_session"),
        ):
            eval_module.run_ingest(args)

        self.assertEqual(sent_users, ["eval-conv-26", "eval-conv-30"])

    def test_qa_default_user_matches_ingest_default(self):
        args = argparse.Namespace(
            user=None,
            count=None,
            output=None,
            base_url="http://127.0.0.1:18789",
            token="token",
        )
        sent_users = []

        def fake_send_message_with_retry(_base_url, _token, user, _message):
            sent_users.append(user)
            return "hello", {}

        async def run_test():
            with (
                mock.patch.object(
                    eval_module,
                    "send_message_with_retry",
                    side_effect=fake_send_message_with_retry,
                ),
                mock.patch.object(eval_module, "get_session_id", return_value=None),
                mock.patch.object(eval_module, "reset_session"),
            ):
                await eval_module.run_sample_qa(
                    locomo_sample("conv-26"),
                    1,
                    args,
                    asyncio.Semaphore(1),
                )

        asyncio.run(run_test())

        self.assertEqual(sent_users, ["eval-conv-26"])
