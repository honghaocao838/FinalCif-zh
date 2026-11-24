import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# The bundled Python runtime preloads a frozen FinalCif package through
# sitecustomize.py.  Drop it so the source tree under test is imported instead.
for _module_name in [name for name in sys.modules if name == 'finalcif' or name.startswith('finalcif.')]:
    del sys.modules[_module_name]

from finalcif.cif.core_dict import cif_core
from finalcif.cif.key_metadata import (
    KEY_ALIASES_FILENAME,
    KEY_REQUIRED_FILENAME,
    alias_index,
    load_key_aliases,
    load_key_required,
    mentioned_keys,
    required_note,
    user_config_path,
)

DATA_DIR = REPO_ROOT / 'finalcif' / 'datafiles'
ALIASES_PATH = DATA_DIR / KEY_ALIASES_FILENAME
REQUIRED_PATH = DATA_DIR / KEY_REQUIRED_FILENAME


def _write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')


class TestBundledData(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.alias_data = json.loads(ALIASES_PATH.read_text(encoding='utf-8'))
        cls.required_data = json.loads(REQUIRED_PATH.read_text(encoding='utf-8'))

    def test_json_files_contain_objects(self) -> None:
        self.assertIsInstance(self.alias_data, dict)
        self.assertIsInstance(self.required_data, dict)

    def test_alias_count(self) -> None:
        self.assertGreaterEqual(len(self.alias_data), 120)
        self.assertLessEqual(len(self.alias_data), 150)

    def test_required_count(self) -> None:
        entries = {key: value for key, value in self.required_data.items() if key != '_meta'}
        self.assertGreaterEqual(len(entries), 35)
        self.assertLessEqual(len(entries), 50)

    def test_alias_keys_exist_in_core_dict(self) -> None:
        missing = sorted(key for key in self.alias_data if key not in cif_core)
        self.assertEqual(missing, [])

    def test_required_keys_exist_in_core_dict(self) -> None:
        missing = sorted(key for key in self.required_data if key != '_meta' and key not in cif_core)
        self.assertEqual(missing, [])

    def test_alias_lists_are_clean(self) -> None:
        for key, values in self.alias_data.items():
            with self.subTest(key=key):
                self.assertIsInstance(values, list)
                self.assertGreaterEqual(len(values), 2)
                self.assertLessEqual(len(values), 4)
                self.assertEqual(len(values), len(set(values)))
                for alias in values:
                    self.assertIsInstance(alias, str)
                    self.assertTrue(alias.strip())

    def test_alias_keys_are_sorted(self) -> None:
        self.assertEqual(list(self.alias_data), sorted(self.alias_data))

    def test_required_entries_are_clean(self) -> None:
        for key, value in self.required_data.items():
            if key == '_meta':
                continue
            with self.subTest(key=key):
                self.assertIsInstance(value, dict)
                self.assertIn(value.get('level'), {'required', 'recommended'})
                self.assertIsInstance(value.get('note'), str)
                self.assertTrue(value['note'].strip())

    def test_required_meta(self) -> None:
        meta = self.required_data['_meta']
        self.assertEqual(meta['updated'], '2026-11-24')
        self.assertIn('IUCr', meta['basis'])
        self.assertIn('提示', meta['basis'])


class TestAliasIndex(unittest.TestCase):
    def test_alias_index_maps_aliases_to_keys(self) -> None:
        index = alias_index({'_cell_length_a': ['晶胞参数a', 'a轴'],
                             '_cell_length_b': ['晶胞参数b', 'a轴']})
        self.assertEqual(index['晶胞参数a'], {'_cell_length_a'})
        self.assertEqual(index['a轴'], {'_cell_length_a', '_cell_length_b'})

    def test_alias_index_is_case_insensitive_and_strips(self) -> None:
        index = alias_index({'_cell_volume': ['  Cell Volume  ']})
        self.assertEqual(index['cell volume'], {'_cell_volume'})

    def test_alias_index_skips_invalid_values(self) -> None:
        index = alias_index({'_cell_length_a': ['ok', '', '  ', 1, None],
                             'no_underscore': ['bad'],
                             '_bad_value': 'not-a-list'})
        self.assertEqual(index, {'ok': {'_cell_length_a'}})


class TestMentionedKeys(unittest.TestCase):
    def test_checkcif_sentence(self) -> None:
        text = ('PLAT041_ALERT 2 ALERT 1 C ... _cell_length_a is unusual; '
                'compare _cell_length_b and _diffrn_ambient_temperature. '
                'Check _refine_ls_R_factor_gt, then _a.')
        self.assertEqual(mentioned_keys(text),
                         {'_cell_length_a', '_cell_length_b',
                          '_diffrn_ambient_temperature', '_refine_ls_R_factor_gt'})

    def test_deduplicates(self) -> None:
        self.assertEqual(mentioned_keys('_cell_volume and _cell_volume'), {'_cell_volume'})

    def test_strips_surrounding_punctuation(self) -> None:
        text = 'See (_cell_volume), [_cell_length_c]; _cell_angle_alpha.'
        self.assertEqual(mentioned_keys(text),
                         {'_cell_volume', '_cell_length_c', '_cell_angle_alpha'})

    def test_ignores_embedded_and_short_names(self) -> None:
        self.assertEqual(mentioned_keys('foo_cell_length_a _a _ab'), set())


class TestFileFallbacks(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.bundled = self.tmp / 'bundled.json'
        self.user = self.tmp / 'user.json'
        self.missing = self.tmp / 'missing.json'
        self.corrupt = self.tmp / 'corrupt.json'
        self.corrupt.write_text('{not valid json', encoding='utf-8')

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_missing_files_return_empty(self) -> None:
        self.assertEqual(load_key_aliases(path=self.missing), {})
        self.assertEqual(load_key_required(path=self.missing), ({}, {}))

    def test_corrupt_files_return_empty(self) -> None:
        self.assertEqual(load_key_aliases(path=self.corrupt), {})
        self.assertEqual(load_key_required(path=self.corrupt), ({}, {}))

    def test_non_object_json_returns_empty(self) -> None:
        list_file = self.tmp / 'list.json'
        list_file.write_text('[]', encoding='utf-8')
        self.assertEqual(load_key_aliases(path=list_file), {})
        self.assertEqual(load_key_required(path=list_file), ({}, {}))

    def test_alias_user_override_priority(self) -> None:
        _write_json(self.bundled, {'_cell_length_a': ['bundled']})
        _write_json(self.user, {'_cell_volume': ['user']})
        self.assertEqual(load_key_aliases(path=self.bundled, user_path=self.user),
                         {'_cell_volume': ['user']})

    def test_alias_missing_user_falls_back_to_bundled(self) -> None:
        _write_json(self.bundled, {'_cell_length_a': ['bundled']})
        self.assertEqual(load_key_aliases(path=self.bundled, user_path=self.missing),
                         {'_cell_length_a': ['bundled']})

    def test_alias_corrupt_user_falls_back_to_bundled(self) -> None:
        _write_json(self.bundled, {'_cell_length_a': ['bundled']})
        self.assertEqual(load_key_aliases(path=self.bundled, user_path=self.corrupt),
                         {'_cell_length_a': ['bundled']})

    def test_alias_invalid_entries_are_filtered(self) -> None:
        _write_json(self.bundled, {'_cell_length_a': ['bundled']})
        _write_json(self.user, {'_cell_length_a': ['ok', '', 3],
                                'no_underscore': ['bad'],
                                '_cell_volume': 'not-a-list'})
        self.assertEqual(load_key_aliases(path=self.bundled, user_path=self.user),
                         {'_cell_length_a': ['ok']})

    def test_required_user_override_priority(self) -> None:
        _write_json(self.bundled, {'_meta': {'basis': 'bundled'},
                                   '_cell_length_a': {'level': 'required', 'note': '旧'}})
        _write_json(self.user, {'_meta': {'basis': 'user'},
                                '_cell_volume': {'level': 'recommended', 'note': '新'}})
        entries, meta = load_key_required(path=self.bundled, user_path=self.user)
        self.assertEqual(entries, {'_cell_volume': {'level': 'recommended', 'note': '新'}})
        self.assertEqual(meta, {'basis': 'user'})

    def test_required_corrupt_user_falls_back_to_bundled(self) -> None:
        _write_json(self.bundled, {'_cell_length_a': {'level': 'required', 'note': '内置'}})
        entries, meta = load_key_required(path=self.bundled, user_path=self.corrupt)
        self.assertEqual(entries, {'_cell_length_a': {'level': 'required', 'note': '内置'}})
        self.assertEqual(meta, {})

    def test_required_invalid_entries_are_filtered(self) -> None:
        _write_json(self.bundled, {'_cell_length_a': {'level': 'required', 'note': '内置'}})
        _write_json(self.user, {
            '_meta': {'basis': 'user'},
            '_cell_length_a': {'level': 'required', 'note': 'ok'},
            '_cell_length_b': {'level': 'optional', 'note': 'bad level'},
            '_cell_length_c': {'level': 'required', 'note': '   '},
            'no_underscore': {'level': 'required', 'note': 'bad key'},
            '_cell_volume': 'not-a-dict',
        })
        entries, meta = load_key_required(path=self.bundled, user_path=self.user)
        self.assertEqual(entries, {'_cell_length_a': {'level': 'required', 'note': 'ok'}})
        self.assertEqual(meta, {'basis': 'user'})


class TestConvenienceHelpers(unittest.TestCase):
    def test_default_loaders_return_bundled_data(self) -> None:
        self.assertGreaterEqual(len(load_key_aliases()), 120)
        entries, meta = load_key_required()
        self.assertGreaterEqual(len(entries), 35)
        self.assertEqual(meta['updated'], '2026-11-24')

    def test_required_note(self) -> None:
        self.assertEqual(required_note('_cell_length_a'), '晶胞参数 a')
        self.assertEqual(required_note('_not_a_cif_key'), '')

    def test_user_config_path(self) -> None:
        path = user_config_path(KEY_ALIASES_FILENAME)
        self.assertEqual(path.name, KEY_ALIASES_FILENAME)
        self.assertEqual(path.parent.name, 'FinalCif')


if __name__ == '__main__':
    unittest.main()
