"""Regression checks for ExitPlan's fixed peach-pastel light/dark palette."""
from src.app.theme import PEACH_ACCENT, palette, theme_css


def test_dark_surfaces_are_warm_rose_not_navy():
    dark = palette("Tối")
    for field in ("bg", "surface", "sidebar", "plot", "border"):
        color = dark[field].lstrip("#")
        red, _, blue = (int(color[i:i + 2], 16) for i in (0, 2, 4))
        assert red > blue, f"{field} should stay in warm peach/plum hues"
    assert dark["accent"] == PEACH_ACCENT


def test_dark_theme_css_uses_warm_table_alert_and_sidebar_backgrounds():
    css = theme_css("Tối")
    assert "#261B23" in css
    assert "#2C1E29" in css
    assert "#533640" in css
    assert "#49313B" in css
    assert "__ALERTBG__" not in css


def test_light_theme_is_preserved():
    light = palette("Sáng")
    assert light["bg"] == "#FFF8F5"
    assert light["sidebar"] == "#FFF2EE"
    assert light["accent"] == PEACH_ACCENT
