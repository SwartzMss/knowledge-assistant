# Modified by SwartzMss in 2026 for Knowledge Assistant branding.

from pathlib import Path

import gradio as gr
from theflow.settings import settings


class HelpPage:
    def __init__(
        self,
        app,
        doc_dir: str = settings.KH_DOC_DIR,
        app_version: str | None = settings.KH_APP_VERSION,
    ):
        self._app = app
        self.doc_dir = Path(doc_dir)
        self.app_version = app_version

        about_md_dir = self.doc_dir / "about.md"
        if about_md_dir.exists():
            with (self.doc_dir / "about.md").open(encoding="utf-8") as fi:
                about_md = fi.read()
        else:
            about_md = ""
        if about_md:
            with gr.Accordion("About"):
                if self.app_version:
                    about_md = f"Version: {self.app_version}\n\n{about_md}"
                gr.Markdown(about_md)

        user_guide_md_dir = self.doc_dir / "usage.md"
        if user_guide_md_dir.exists():
            with (self.doc_dir / "usage.md").open(encoding="utf-8") as fi:
                user_guide_md = fi.read()
        else:
            user_guide_md = ""
        if user_guide_md:
            with gr.Accordion("User Guide", open=True):
                gr.Markdown(user_guide_md)
