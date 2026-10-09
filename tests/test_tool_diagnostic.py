"""Labeled synthetic native/transport disagreement and truncation cases."""

import json
import unittest
from zenithsync.tool_diagnostic import parse_native_write, assess_write_response, QUOTE


class ToolDiagnosticTests(unittest.TestCase):
    def call(self, body):
        return '<|tool_call>call:write_file{' + body + '}<tool_call|>'

    def response(self, args, finish='tool_calls'):
        return {'choices':[{'finish_reason':finish,'message':{'tool_calls':[
            {'function':{'name':'write_file','arguments':json.dumps(args)}}]}}]}

    def test_literal_quotes_braces_unicode_and_argument_order(self):
        expected = {'filepath':'probe.py','content':'s = "🌍"\nprint(f"{s}, filepath:")\n'}
        raw = self.call(f'content:{QUOTE}{expected["content"]}{QUOTE},filepath:{QUOTE}probe.py{QUOTE}')
        self.assertEqual(parse_native_write(raw), expected)
        self.assertEqual(assess_write_response(self.response(expected),raw,expected)['classification'],'exact_match')

    def test_ordinary_quote_cannot_close_native_string(self):
        raw = self.call(f'content:{QUOTE}x = 1\n",filepath:{QUOTE}probe.py{QUOTE}')
        with self.assertRaises(ValueError):
            parse_native_write(raw)

    def test_duplicates_trailing_comma_and_missing_calls_rejected(self):
        for body in [f'filepath:{QUOTE}a{QUOTE},filepath:{QUOTE}b{QUOTE}',
                     f'filepath:{QUOTE}a{QUOTE},content:{QUOTE}b{QUOTE},']:
            with self.assertRaises(ValueError):
                parse_native_write(self.call(body))
        with self.assertRaises(ValueError):
            parse_native_write('No call.')

    def test_valid_native_with_damaged_transport_is_distinguished(self):
        expected={'filepath':'a','content':'b'}
        raw=self.call(f'filepath:{QUOTE}a{QUOTE},content:{QUOTE}b{QUOTE}')
        result=assess_write_response(self.response({'content':'b'}),raw,expected)
        self.assertEqual(result['classification'],'native_transport_disagreement')
        result=assess_write_response(self.response(expected,'length'),raw,expected)
        self.assertEqual(result['classification'],'output_budget_exhausted')


if __name__ == '__main__':
    unittest.main()
