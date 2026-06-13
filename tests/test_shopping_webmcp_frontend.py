from __future__ import annotations

from pathlib import Path
from typing import Final

ROOT: Final = Path(__file__).resolve().parents[1]
APP_JS: Final = ROOT / "webmcp-shopping-lab" / "app.js"
LAB_JS: Final = ROOT / "webmcp-shopping-lab" / "lab.js"
WIDGET_JS: Final = ROOT / "webmcp-shopping-lab" / "third-party-widget.js"
INDEX_HTML: Final = ROOT / "webmcp-shopping-lab" / "index.html"
LAB_HTML: Final = ROOT / "webmcp-shopping-lab" / "lab.html"


def test_browser_poison_button_mutates_clean_surface_client_side() -> None:
    app = APP_JS.read_text(encoding="utf-8")
    lab = LAB_JS.read_text(encoding="utf-8")
    widget = WIDGET_JS.read_text(encoding="utf-8")
    storefront_html = INDEX_HTML.read_text(encoding="utf-8")
    lab_html = LAB_HTML.read_text(encoding="utf-8")

    assert "/api/tool-surface?mode=normal" in lab
    assert "poisonEverydayMartTools" in lab
    assert "third-party-widget.js" in widget
    assert "simulateAgent" not in app
    assert "Mutated by" in lab
    assert "third-party-widget.js" not in storefront_html
    assert "third-party-widget.js" in lab_html
