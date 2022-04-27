
import pytest

import sys
for path in sys.path:
    print(path)

from solarwinds_observability.w3c_transformer import W3CTransformer

class TestW3CTransformer():
    def test_span_from_int(self):
        expected = "{:016x}".format(1111222233334444)
        assert W3CTransformer.span_id_from_int(1111222233334444) == expected
    
    def test_span_from_int_fails_with_str(self):
        with pytest.raises(ValueError):
            W3CTransformer.span_id_from_int("aaaabbbbbccccdddd")