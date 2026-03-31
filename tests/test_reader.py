import io
import pytest

from engine.sample_creator import create_sample_workbook
from engine.reader import EBAExcelReader


def test_eba_excel_reader_reads_generated_template():
    buf = create_sample_workbook(currencies=["EUR", "USD"], entity_lei="TESTLEI", ref_date="2025-12-31")
    reader = EBAExcelReader()
    data = reader.read(io.BytesIO(buf.getvalue()))

    # Expect at least the EUR and USD C72 template sheets to be read
    assert any(k.startswith("C 72.00") for k in data)
    assert any(v["currency"] == "EUR" for v in data.values())
    assert any(v["currency"] == "USD" for v in data.values())
    assert all("template_code" in v for v in data.values())


if __name__ == "__main__":
    pytest.main(["-q"])
