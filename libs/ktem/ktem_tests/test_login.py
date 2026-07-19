import hashlib
from types import SimpleNamespace

import gradio as gr
from sqlmodel import Session, SQLModel, create_engine

from ktem.db.models import User
from ktem.pages import login as login_module
from ktem.pages.login import LoginPage, clear_legacy_credentials_js


def test_login_controls_are_visible_initially():
    app = SimpleNamespace(app_name="Knowledge Assistant")

    with gr.Blocks():
        page = LoginPage(app)

    assert page.usn.visible is True
    assert page.pwd.visible is True
    assert page.btn_login.visible is True


def test_legacy_browser_credentials_are_cleared_on_load():
    calls = []
    page = LoginPage.__new__(LoginPage)
    page._app = SimpleNamespace(
        app=SimpleNamespace(load=lambda **kwargs: calls.append(kwargs))
    )

    page._on_app_created()

    assert calls == [{"fn": None, "js": clear_legacy_credentials_js}]
    assert "localStorage.removeItem('username')" in clear_legacy_credentials_js
    assert "localStorage.removeItem('password')" in clear_legacy_credentials_js


def test_local_login(monkeypatch, tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'login.db'}")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        user = User(
            username="Admin",
            username_lower="admin",
            password=hashlib.sha256(b"admin").hexdigest(),
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        user_id = user.id

    monkeypatch.setattr(login_module, "engine", engine)
    monkeypatch.setattr(login_module.gr, "Warning", lambda *_: None)
    page = LoginPage.__new__(LoginPage)

    assert page.login("", "admin", None) == (None, "", "admin")
    assert page.login("admin", "wrong", None) == (None, "admin", "wrong")
    assert page.login("admin", "admin", None) == (user_id, "", "")
    assert page.login("  ADMIN  ", "admin", None) == (user_id, "", "")
