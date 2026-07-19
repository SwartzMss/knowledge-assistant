import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).parents[3]
sys.path.insert(0, str(REPO_ROOT))

import ktem.pages.chat as chat_module
import ktem.pages.chat.control as control_module
from ktem.db.models import Conversation
from ktem.pages.chat import ChatPage
from ktem.pages.chat.common import STATE
from ktem.pages.chat.control import ConversationControl
from sqlmodel import Session, SQLModel, create_engine, select

import flowsettings
from kotaemon.indices.ingests.files import KH_DEFAULT_FILE_EXTRACTORS


def test_minimal_product_registration():
    assert flowsettings.KH_REASONINGS == ["ktem.reasoning.simple.FullQAPipeline"]
    assert flowsettings.KH_INDEX_TYPES == ["ktem.index.file.FileIndex"]
    assert len(flowsettings.KH_INDICES) == 1
    assert set(KH_DEFAULT_FILE_EXTRACTORS) == {".pdf", ".md", ".txt"}


def test_app_make_with_empty_model_configuration(tmp_path):
    env = os.environ.copy()
    env["KH_APP_DATA_DIR"] = str(tmp_path / "app-data")
    for key in tuple(env):
        if key.endswith("_API_KEY") or key in {"LOCAL_MODEL", "LOCAL_MODEL_EMBEDDINGS"}:
            env[key] = ""
    for key in (
        "OPENAI_API_KEY",
        "AZURE_OPENAI_API_KEY",
        "GOOGLE_API_KEY",
        "ANTHROPIC_API_KEY",
        "GROQ_API_KEY",
        "COHERE_API_KEY",
        "MISTRAL_API_KEY",
        "VOYAGE_API_KEY",
        "LOCAL_MODEL",
        "LOCAL_MODEL_EMBEDDINGS",
    ):
        env[key] = ""

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from ktem.main import App; App().make(); print('app-make-ok')",
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert "app-make-ok" in result.stdout


def test_conversation_lifecycle_and_data_source_restore(tmp_path, monkeypatch):
    database = tmp_path / "conversations.db"
    engine = create_engine(f"sqlite:///{database}")
    SQLModel.metadata.create_all(engine)
    monkeypatch.setattr(control_module, "engine", engine)
    monkeypatch.setattr(chat_module, "engine", engine)

    app = SimpleNamespace(index_manager=SimpleNamespace(indices=[]))
    control = ConversationControl.__new__(ConversationControl)
    control._app = app

    conversation_id, _ = control.new_conv("local-user")
    control.rename_conv(conversation_id, "Baseline session", True, "local-user")

    chat_page = ChatPage.__new__(ChatPage)
    chat_page._app = app
    state = deepcopy(STATE)
    messages = [["question", "answer"]]
    retrieval = "<p>evidence</p>"
    plot = {"data": [], "layout": {}}
    chat_page.persist_data_source(
        conversation_id,
        "local-user",
        retrieval,
        plot,
        [],
        [],
        messages,
        state,
    )

    restored = control.select_conv(conversation_id, "local-user")
    assert restored[2] == "Baseline session"
    assert restored[3] == messages
    assert restored[4] == retrieval
    assert restored[6] == [retrieval]
    assert restored[7] == [plot]

    control.delete_conv(conversation_id, "local-user")
    with Session(engine) as session:
        assert (
            session.exec(
                select(Conversation).where(Conversation.id == conversation_id)
            ).one_or_none()
            is None
        )
