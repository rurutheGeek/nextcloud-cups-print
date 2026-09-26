"""Guard the CUPS print relay API."""
import importlib.util
import os
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'print_api.py'

spec = importlib.util.spec_from_file_location('print_api', SOURCE)
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)


class AuthorizationTests(unittest.TestCase):
    def test_a_valid_token_from_the_allowed_client_passes(self):
        self.assertTrue(api.authorized('Bearer s3cret', '192.168.10.101',
                                       's3cret', {'192.168.10.101'}))

    def test_a_wrong_or_missing_token_is_refused(self):
        self.assertFalse(api.authorized('Bearer wrong', '192.168.10.101',
                                        's3cret', {'192.168.10.101'}))
        self.assertFalse(api.authorized(None, '192.168.10.101',
                                        's3cret', {'192.168.10.101'}))

    def test_another_client_is_refused_even_with_the_token(self):
        self.assertFalse(api.authorized('Bearer s3cret', '192.168.10.99',
                                        's3cret', {'192.168.10.101'}))

    def test_an_empty_allowlist_still_requires_the_token(self):
        self.assertTrue(api.authorized('Bearer s3cret', '192.0.2.9', 's3cret', set()))
        self.assertFalse(api.authorized('Bearer wrong', '192.0.2.9', 's3cret', set()))


class DocumentTests(unittest.TestCase):
    def test_only_printable_extensions_are_allowed(self):
        for extension in ('pdf', 'png', 'jpg', 'jpeg', 'txt', 'md'):
            self.assertIn(extension, api.ALLOWED_EXTENSIONS)
        for extension in ('exe', 'svg', 'zip'):
            self.assertNotIn(extension, api.ALLOWED_EXTENSIONS)

    def test_markdown_is_sent_to_the_text_filter(self):
        self.assertEqual(api.TEMP_SUFFIX.get('md'), 'txt')

    def test_the_filename_is_reduced_to_a_safe_title(self):
        # The Nextcloud app urlencodes the name, so decode before basename.
        self.assertEqual(api.printable_name('..%2F..%2Fetc%2Fpasswd.pdf'),
                         ('passwd.pdf', 'pdf'))
        self.assertEqual(api.printable_name(''), ('document', ''))
        self.assertEqual(api.printable_name('report%20final.PDF'),
                         ('report final.PDF', 'pdf'))

    def test_copies_are_bounded(self):
        self.assertEqual(api.bounded('200', 1, 99, 1), 99)
        self.assertEqual(api.bounded('0', 1, 99, 1), 1)
        self.assertEqual(api.bounded('x', 1, 99, 1), 1)
        self.assertEqual(api.bounded('3', 1, 99, 1), 3)

    def test_page_ranges_are_validated(self):
        self.assertEqual(api.parse_ranges('1-3,5'), '1-3,5')
        self.assertEqual(api.parse_ranges(' 2 '), '2')
        self.assertIsNone(api.parse_ranges(''))
        self.assertIsNone(api.parse_ranges('1-3; rm -rf /'))
        self.assertIsNone(api.parse_ranges('1-3 -o job-hold-until=indefinite'))
        self.assertIsNone(api.parse_ranges('1\n2'))
        self.assertIsNone(api.parse_ranges('x' * 65))


class LpTests(unittest.TestCase):
    def test_the_command_targets_the_queue_with_the_chosen_mode(self):
        command = api.lp_command('Printer', 'report.pdf', 2, 'monochrome', '/tmp/x.pdf')
        self.assertEqual(command[:5], ['lp', '-d', 'Printer', '-t', 'report.pdf'])
        self.assertIn('print-color-mode=monochrome', command)
        self.assertEqual(command[-1], '/tmp/x.pdf')

    def test_page_ranges_become_one_cups_option(self):
        command = api.lp_command('Printer', 'report.pdf', 1, 'color', '/tmp/x.pdf', '1-3,5')
        self.assertIn('page-ranges=1-3,5', command)
        without = api.lp_command('Printer', 'report.pdf', 1, 'color', '/tmp/x.pdf')
        self.assertNotIn('page-ranges=1-3,5', without)

    def test_the_job_id_is_read_from_the_lp_output(self):
        self.assertEqual(api.parse_job_id('request id is Printer-42 (1 file(s))'),
                         'Printer-42')
        self.assertIsNone(api.parse_job_id('lp: Error - unable to print'))


class ConfigurationTests(unittest.TestCase):
    def test_the_token_and_queue_must_be_set(self):
        os.environ.pop('CPS_TEST_VAR', None)
        with self.assertRaises(SystemExit):
            api.env_required('CPS_TEST_VAR')
        os.environ['CPS_TEST_VAR'] = '  value  '
        try:
            self.assertEqual(api.env_required('CPS_TEST_VAR'), 'value')
        finally:
            del os.environ['CPS_TEST_VAR']


if __name__ == '__main__':
    unittest.main()
