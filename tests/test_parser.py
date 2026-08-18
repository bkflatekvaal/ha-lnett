from pathlib import Path
import importlib.util
import sys

MODULE = Path(__file__).parents[1] / "custom_components" / "lnett" / "parser.py"
spec = importlib.util.spec_from_file_location("lnett_parser", MODULE)
parser = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = parser
spec.loader.exec_module(parser)


def test_parse_2026_fixture():
    html = (Path(__file__).parent / "fixtures" / "lnett_2026.html").read_text(encoding="utf-8")
    data = parser.parse_tariffs(html)
    assert data.valid_from.isoformat() == "2026-01-01"
    assert data.energy_day == 32
    assert data.energy_night_weekend == 17
    assert data.consumption_tax == 8.91
    assert data.enova_fee == 1.25
    assert data.capacity["0-2"] == 150
    assert data.capacity["5-10"] == 400
    assert data.capacity["20-25"] == 1150
