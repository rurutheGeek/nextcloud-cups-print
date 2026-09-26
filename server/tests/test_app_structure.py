"""Guard the cups_print Nextcloud app without a Nextcloud installation.

The app has no database and no PHP dependencies, so these structural checks
plus the bundle build in CI are the regression net before a real-instance
check against Nextcloud 33/35.
"""
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return (ROOT / path).read_text(encoding='utf-8')


class InfoXmlTests(unittest.TestCase):
    def setUp(self):
        self.info = read('appinfo/info.xml')
        self.xml = ET.fromstring(self.info)

    def test_the_id_and_namespace_match_the_php_namespace(self):
        self.assertEqual(self.xml.findtext('id'), 'cups_print')
        self.assertEqual(self.xml.findtext('namespace'), 'CupsPrint')
        self.assertIn('namespace OCA\\CupsPrint\\AppInfo;',
                      read('lib/AppInfo/Application.php'))

    def test_the_licence_is_spdx_agpl(self):
        self.assertEqual(self.xml.findtext('licence'), 'AGPL-3.0-or-later')
        self.assertTrue((ROOT / 'LICENSE').exists())

    def test_the_supported_versions_allow_the_current_releases(self):
        nextcloud = self.xml.find('dependencies/nextcloud')
        self.assertEqual(nextcloud.get('min-version'), '33')
        self.assertGreaterEqual(int(nextcloud.get('max-version')), 35)

    def test_the_store_metadata_is_complete(self):
        for tag in ('summary', 'description', 'bugs', 'repository'):
            self.assertTrue(self.xml.findtext(tag), tag)

    def test_the_admin_settings_are_declared(self):
        self.assertEqual(self.xml.findtext('settings/admin'),
                         'OCA\\CupsPrint\\Settings\\Admin')
        self.assertEqual(self.xml.findtext('settings/admin-section'),
                         'OCA\\CupsPrint\\Settings\\AdminSection')


class AppTests(unittest.TestCase):
    def test_the_files_script_is_registered_on_the_files_page(self):
        self.assertIn('LoadAdditionalScriptsEvent::class',
                      read('lib/AppInfo/Application.php'))
        self.assertIn("Util::addInitScript('cups_print', 'cups_print')",
                      read('lib/Listener/LoadAdditionalScripts.php'))

    def test_the_controller_forwards_with_a_token_to_the_relay(self):
        controller = read('lib/Controller/PrintController.php')
        self.assertIn("#[FrontpageRoute(verb: 'POST', url: '/print')]", controller)
        self.assertIn("getAppValue('cups_print', 'relay_url'", controller)
        self.assertIn("getAppValue('cups_print', 'relay_token'", controller)
        self.assertIn("'Bearer ' . $token", controller)
        self.assertIn("'allow_local_address' => true", controller)
        self.assertIn('isReadable()', controller)

    def test_the_print_options_reach_the_relay(self):
        controller = read('lib/Controller/PrintController.php')
        self.assertIn("'X-Print-Copies' =>", controller)
        self.assertIn("'X-Print-Color' =>", controller)
        self.assertIn("$headers['X-Print-Ranges'] = $ranges;", controller)
        self.assertIn('PAGE_RANGES_PATTERN', controller)
        self.assertIn("'md'", controller)

    def test_the_stream_size_and_relay_errors_are_handled(self):
        controller = read('lib/Controller/PrintController.php')
        # サイズ不明のストリームはchunkedになり、中継のContent-Length検査で弾かれる。
        self.assertIn("'Content-Length' => (string)$node->getSize()", controller)
        # 4xx/5xxでも中継のエラー本文を利用者へ返す。
        self.assertIn("'http_errors' => false", controller)
        self.assertIn("$result['error']", controller)
        # \s は改行も通してしまうので、ページ範囲は空白とハイフンだけ許可する。
        self.assertIn(r'/^[0-9,\- ]{1,64}$/', controller)

    def test_non_admins_may_use_the_print_route(self):
        controller = read('lib/Controller/PrintController.php')
        self.assertIn('use OCP\\AppFramework\\Http\\Attribute\\NoAdminRequired;', controller)
        self.assertEqual(controller.count('#[NoAdminRequired]'), 1)

    def test_only_administrators_may_change_the_settings(self):
        controller = read('lib/Controller/SettingsController.php')
        self.assertIn('AuthorizedAdminSetting(settings: Admin::class)', controller)
        self.assertIn("linkToRoute('cups_print.settings.save')", read('lib/Settings/Admin.php'))
        self.assertIn('IDelegatedSettings', read('lib/Settings/Admin.php'))
        self.assertIn('name="requesttoken"', read('templates/admin.php'))

    def test_the_action_uses_the_files_context_signature(self):
        source = read('src/print.js')
        self.assertIn('enabled: ({ nodes })', source)
        self.assertIn('exec: async ({ nodes })', source)
        self.assertIn("replace(/^\\./, '')", source)

    def test_the_action_offers_copies_color_and_page_range(self):
        source = read('src/print.js')
        self.assertIn('showPrintDialog', source)
        self.assertIn('pageRanges', source)
        self.assertIn("'md'", source)
        self.assertIn("t('cups_print', 'Copies')", source)
        self.assertIn("t('cups_print', 'Color mode')", source)


class BundleTests(unittest.TestCase):
    def test_the_bundle_registers_the_print_action(self):
        bundle = read('js/cups_print.js')
        self.assertIn('registerFileAction', bundle)
        self.assertIn('/apps/cups_print/print', bundle)
        self.assertIn('cups-print', bundle)
        # Register into the same @nextcloud/files v4 registry as the core.
        self.assertIn('_nc_files_scope', bundle)
        self.assertIn('register:action', bundle)

    def test_the_package_does_not_pull_the_dialog_vue_tree(self):
        package = json.loads(read('package.json'))
        self.assertNotIn('@nextcloud/dialogs', package['dependencies'])
        self.assertEqual(package['dependencies']['@nextcloud/files'], '^4.0.0')
        self.assertFalse((ROOT / 'js/cups_print.css').exists())


class TranslationTests(unittest.TestCase):
    def test_japanese_covers_the_visible_strings(self):
        translations = json.loads(read('l10n/ja.json'))['translations']
        for key in ('Print', 'Printed (job {job})', 'Printing failed',
                    'Relay URL', 'Relay token', 'Save'):
            self.assertIn(key, translations)
            self.assertTrue(translations[key])


if __name__ == '__main__':
    unittest.main()
