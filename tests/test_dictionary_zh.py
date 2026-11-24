"""Validation tests for the Chinese CIF help dictionary (cif_dict_zh.json)."""

import json
import re
from pathlib import Path

from finalcif.cif.all_cif_dicts import (
    _load_zh_help,
    additional_keywords,
    cif_all_dict,
    cif_all_dict_zh_keys,
    has_chinese_help,
    keyword_help_title,
)
from finalcif.cif.core_dict import cif_core
from finalcif.cif.modulation_dict import modulation_dict
from finalcif.cif.powder_dict import powder_dict
from finalcif.cif.restraints_dict import restraints_dict
from finalcif.cif.twin_dict import twinning_dict

DATA_FILE = (Path(__file__).resolve().parent.parent
             / 'finalcif' / 'datafiles' / 'cif_dict_zh.json')

EXPECTED_ENTRIES = 1429
CJK_RE = re.compile(r'[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]')

# The English original of this keyword has no <h2> header either, so the
# Chinese translation correctly mirrors that structure.
NO_H2_IN_ENGLISH = '_olex2_diffrn_ambient_temperature_device'


def _english_dict() -> dict[str, str]:
    """Return the combined English dictionary as it exists before the override."""
    english: dict[str, str] = {}
    english.update(cif_core)
    english.update(twinning_dict)
    english.update(modulation_dict)
    english.update(powder_dict)
    english.update(restraints_dict)
    english.update(additional_keywords)
    return english


ENGLISH = _english_dict()
ZH = json.loads(DATA_FILE.read_text(encoding='utf-8'))


def test_entry_count_matches_english_dictionary():
    assert len(ZH) == EXPECTED_ENTRIES
    assert len(ENGLISH) == EXPECTED_ENTRIES


def test_all_chinese_keys_exist_in_english_dictionary():
    assert set(ZH) - set(ENGLISH) == set()
    assert set(ENGLISH) - set(ZH) == set()


def test_every_value_has_h2_header_with_its_key():
    missing = [
        key for key, value in ZH.items()
        if key != NO_H2_IN_ENGLISH and f'<h2>{key}</h2>' not in value
    ]
    assert missing == []
    # The single exception mirrors the English original, which has no <h2> either.
    assert f'<h2>{NO_H2_IN_ENGLISH}</h2>' not in ENGLISH[NO_H2_IN_ENGLISH]


def test_every_value_has_balanced_pre_h2_h4_tags():
    broken = {}
    for key, value in ZH.items():
        for tag in ('pre', 'h2', 'h4'):
            opens = value.count(f'<{tag}>')
            closes = value.count(f'</{tag}>')
            if opens != closes:
                broken[key] = (tag, opens, closes)
    assert broken == {}


def test_every_value_is_non_empty_and_contains_cjk():
    assert [key for key, value in ZH.items() if not value.strip()] == []
    assert [key for key, value in ZH.items() if not CJK_RE.search(value)] == []


def test_chinese_keys_set_matches_loaded_file():
    assert cif_all_dict_zh_keys == set(ZH)
    assert cif_all_dict_zh_keys <= set(ENGLISH)


def test_load_zh_help_missing_file_returns_empty_dict(tmp_path):
    assert _load_zh_help(tmp_path / 'does_not_exist.json') == {}


def test_load_zh_help_corrupt_file_returns_empty_dict(tmp_path):
    corrupt = tmp_path / 'corrupt.json'
    corrupt.write_text('{"broken": ', encoding='utf-8')
    assert _load_zh_help(corrupt) == {}


def test_load_zh_help_filters_non_string_entries(tmp_path):
    mixed = tmp_path / 'mixed.json'
    mixed.write_text(json.dumps({'valid': '文本', 'number': 1, 'none': None}),
                     encoding='utf-8')
    assert _load_zh_help(mixed) == {'valid': '文本'}

    not_an_object = tmp_path / 'list.json'
    not_an_object.write_text('["not", "a", "dict"]', encoding='utf-8')
    assert _load_zh_help(not_an_object) == {}


def test_translated_key_has_chinese_help_and_plain_title():
    key = '_cell_length_a'
    assert key in cif_all_dict_zh_keys
    assert has_chinese_help(key) is True
    assert keyword_help_title(key) == key


def test_untranslated_key_is_annotated():
    key = '_this_key_does_not_exist_anywhere'
    assert key not in cif_all_dict_zh_keys
    assert has_chinese_help(key) is False
    assert keyword_help_title(key) == f'{key}（暂无中文）'


def test_cif_all_dict_contains_chinese_but_english_original_is_untouched():
    key = '_cell_length_a'
    assert key in cif_all_dict
    assert CJK_RE.search(cif_all_dict[key])
    assert cif_all_dict[key] != cif_core[key]
    assert not CJK_RE.search(cif_core[key])
