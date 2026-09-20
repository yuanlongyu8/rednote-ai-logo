"""Behavioral checks for manifest boundaries; does not claim visual acceptance."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_review import prepare


class ReviewTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        # Known 1x1 PNG fixture.
        import base64
        (self.root / 'a.png').write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aL1sAAAAASUVORK5CYII='))
        self.data = dict(schemaVersion=1, project='Example', revision='v1', concepts=[dict(
            id='a', title='A', version='v1', concept='Concept', changes='First', status='exploration',
            placement=dict(mode='contain'), palettes=[dict(id='a', label='Original', asset='a.png', kind='original')])])

    def run_data(self):
        path = self.root / 'review.json'
        path.write_text(json.dumps(self.data))
        return prepare(path)

    def test_hash_binds_content_and_default_padding(self):
        a = self.run_data()
        self.assertEqual(a['concepts'][0]['placement']['scale'], .8)
        self.data['concepts'][0]['concept'] = 'Different'
        self.assertNotEqual(a['snapshotBase'], self.run_data()['snapshotBase'])

    def test_duplicate_id(self):
        self.data['concepts'].append(copy.deepcopy(self.data['concepts'][0]))
        with self.assertRaises(AssertionError): self.run_data()

    def test_path_escape(self):
        self.data['concepts'][0]['palettes'][0]['asset'] = '../outside.png'
        with self.assertRaises(AssertionError): self.run_data()

    def test_monochrome_requires_confirmation(self):
        self.data['concepts'][0]['palettes'][0]['kind'] = 'monochrome-artwork'
        with self.assertRaises(AssertionError): self.run_data()

    def test_filter_preview(self):
        p = self.data['concepts'][0]['palettes'][0]
        p.update(kind='filter-preview', filter='hue-rotate(55deg)')
        self.run_data()
        p['filter'] = 'url(https://example.org)'
        with self.assertRaises(AssertionError): self.run_data()


if __name__ == '__main__': unittest.main()
