#
# test_skin.py – checks the skin and its packaging without Kodi (what CI can run).
#
# The skin's behaviour on screen is tested with the portable test Kodi instead (tools/navtest.py,
# tools/wraptest.py, tools/appearancetest.py; see the readme). Run: python -m unittest discover -s tests
#

import hashlib
import os
import sys
import tempfile
import unittest
import zipfile
from xml.etree import ElementTree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import build_repo  # noqa: E402
import build_zip  # noqa: E402
import nowrap  # noqa: E402
import skincheck  # noqa: E402


def sha256(path):
	with open(path, 'rb') as fh:
		return hashlib.sha256(fh.read()).hexdigest()


class Skin(unittest.TestCase):

	def test_skin_check_passes(self):
		# XML parses, textures exist with the right case, includes and colours are defined,
		# grouplists have no dead ends, no list wraps
		self.assertEqual(skincheck.check(), [])

	def test_no_list_wraps(self):
		for name in sorted(os.listdir(os.path.join(ROOT, 'skin.oakline', 'xml'))):
			if name in ('Includes_Folders.xml', 'Timers.xml', 'Font.xml'):
				continue
			with open(os.path.join(ROOT, 'skin.oakline', 'xml', name), encoding='utf-8') as fh:
				text = fh.read()
			for ctype, cid, _, direct in nowrap.containers(text):
				self.assertEqual(nowrap.missing(ctype, direct), [], '%s: %s %s wraps' % (name, ctype, cid))

	def test_addon_xml_holds_the_placeholder_version(self):
		# the version comes from the git tag; addon.xml must not pretend to be a release
		root = ElementTree.parse(os.path.join(ROOT, 'skin.oakline', 'addon.xml')).getroot()
		self.assertEqual(root.get('id'), 'skin.oakline')
		self.assertEqual(root.get('version'), '0.0.0')


class Versions(unittest.TestCase):

	def test_tags(self):
		self.assertEqual(build_zip.tag_to_version('v1.3.8'), '1.3.8')
		self.assertEqual(build_zip.tag_to_version('v1.4.0-rc.2'), '1.4.0~rc.2')
		with self.assertRaises(SystemExit):
			build_zip.tag_to_version('1.3.8')

	def test_describe(self):
		self.assertEqual(build_zip.describe_to_version('v1.3.8-0-gabc1234'), '1.3.8')
		self.assertEqual(build_zip.describe_to_version('v1.3.8-3-gabc1234'), '1.3.9~dev3')
		self.assertEqual(build_zip.describe_to_version(''), '0.0.0~dev')


class Packaging(unittest.TestCase):

	def build(self, out):
		skin, version = build_zip.build('skin.oakline', '1.3.8', out)
		repo, _ = build_zip.build('repository.oakline', None, out)
		return skin, repo

	def test_zip_layout(self):
		with tempfile.TemporaryDirectory() as out:
			skin, repo = self.build(out)
			self.assertEqual(os.path.basename(skin), 'skin.oakline-1.3.8.zip')
			with zipfile.ZipFile(skin) as zf:
				names = zf.namelist()
				self.assertEqual({n.split('/', 1)[0] for n in names}, {'skin.oakline'})
				for needed in ('addon.xml', 'icon.png', 'license.txt', 'xml/Home.xml', 'fonts/NotoSans-Regular.ttf', 'fonts/noto_license.txt'):
					self.assertIn('skin.oakline/' + needed, names)
				self.assertFalse([n for n in names if n.endswith('.pyc') or '/.' in n])
				version = ElementTree.fromstring(zf.read('skin.oakline/addon.xml')).get('version')
				self.assertEqual(version, '1.3.8')
			with zipfile.ZipFile(repo) as zf:
				self.assertIn('repository.oakline/addon.xml', zf.namelist())

	def test_zips_are_reproducible(self):
		sums = []
		for _ in range(2):
			with tempfile.TemporaryDirectory() as out:
				skin, repo = self.build(out)
				sums.append([sha256(p) for p in (skin, repo)])
		self.assertEqual(sums[0], sums[1])

	def test_update_site(self):
		with tempfile.TemporaryDirectory() as zips, tempfile.TemporaryDirectory() as site:
			self.build(zips)
			published = build_repo.build(zips, site)
			self.assertIn(('skin.oakline', '1.3.8'), published)
			self.assertTrue(os.path.exists(os.path.join(site, 'repo', 'addons.xml')))
			self.assertTrue(os.path.exists(os.path.join(site, 'repo', 'skin.oakline', 'skin.oakline-1.3.8.zip')))
			self.assertTrue(os.path.exists(os.path.join(site, 'index.html')))


if __name__ == '__main__':
	unittest.main()
