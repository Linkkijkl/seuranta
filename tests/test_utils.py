import string
import src.utils as utils


def test_sanitise_name_trim_leading_whitespace():
    result = utils.sanitise_name(" alex")
    assert result == "alex"

def test_sanitise_name_trim_trailing_whitespace():
    result = utils.sanitise_name("alex ")
    assert result == "alex"

def test_sanitise_name_remove_bounded_whitespace():
    result = utils.sanitise_name("al ex")
    assert result == "alex"

def test_sanitise_name_cut_long_name():
    result = utils.sanitise_name("XXXXXEEEEEXXXXXEEEEEz")
    assert result == "XXXXXEEEEEXXXXXEEEEE"

def test_sanitise_name_valid_name():
    result = utils.sanitise_name("AlexIs45spoons")
    assert result == "AlexIs45spoons"

def test_sanitise_name_remove_punctuation_characters():
    for char in string.punctuation:
        result = utils.sanitise_name(f"al{char}ex")
        assert result == "alex"