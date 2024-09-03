# -*- coding: utf-8 -*-
from .common import TestAccountReportsCommon

from odoo import fields
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestFinancialReport(TestAccountReportsCommon):

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)

        # ==== Partners ====

        cls.partner_a = cls.env['res.partner'].create({'name': 'partner_a', 'company_id': False})
        cls.partner_b = cls.env['res.partner'].create({'name': 'partner_b', 'company_id': False})
        cls.partner_c = cls.env['res.partner'].create({'name': 'partner_c', 'company_id': False})

        # ==== Accounts ====

        # Cleanup existing "Current year earnings" accounts since we can only have one by company.
        cls.env['account.account'].search([
            ('company_id', 'in', (cls.company_data['company'] + cls.company_data_2['company']).ids),
            ('user_type_id', '=', cls.env.ref('account.data_unaffected_earnings').id),
        ]).unlink()

        account_type_data = [
            (cls.env.ref('account.data_account_type_receivable'),           {'reconcile': True}),
            (cls.env.ref('account.data_account_type_payable'),              {'reconcile': True}),
            (cls.env.ref('account.data_account_type_liquidity'),            {}),
            (cls.env.ref('account.data_account_type_current_assets'),       {}),
            (cls.env.ref('account.data_account_type_prepayments'),          {}),
            (cls.env.ref('account.data_account_type_fixed_assets'),         {}),
            (cls.env.ref('account.data_account_type_non_current_assets'),   {}),
            (cls.env.ref('account.data_account_type_equity'),               {}),
            (cls.env.ref('account.data_unaffected_earnings'),               {}),
            (cls.env.ref('account.data_account_type_revenue'),              {}),
        ]

        accounts = cls.env['account.account'].create([{
            **data[1],
            'name': 'account%s' % i,
            'code': 'code%s' % i,
            'user_type_id': data[0].id,
            'company_id': cls.company_data['company'].id,
        } for i, data in enumerate(account_type_data)])

        accounts_2 = cls.env['account.account'].create([{
            **data[1],
            'name': 'account%s' % (i + 100),
            'code': 'code%s' % (i + 100),
            'user_type_id': data[0].id,
            'company_id': cls.company_data_2['company'].id,
        } for i, data in enumerate(account_type_data)])

        # ==== Custom filters ====

        cls.filter = cls.env['ir.filters'].create({
            'name': 'filter',
            'model_id': 'account.move.line',
            'context': str({'group_by': ['date', 'partner_id']}),
            'domain': str([('partner_id.name', '=', 'partner_a')]),
        })

        # ==== Journal entries ====

        cls.move_2019 = cls.env['account.move'].create({
            'move_type': 'entry',
            'date': fields.Date.from_string('2019-01-01'),
            'line_ids': [
                (0, 0, {'debit': 25.0,      'credit': 0.0,      'account_id': accounts[0].id,   'partner_id': cls.partner_a.id}),
                (0, 0, {'debit': 25.0,      'credit': 0.0,      'account_id': accounts[0].id,   'partner_id': cls.partner_b.id}),
                (0, 0, {'debit': 25.0,      'credit': 0.0,      'account_id': accounts[0].id,   'partner_id': cls.partner_c.id}),
                (0, 0, {'debit': 25.0,      'credit': 0.0,      'account_id': accounts[0].id,   'partner_id': cls.partner_a.id}),
                (0, 0, {'debit': 200.0,     'credit': 0.0,      'account_id': accounts[1].id,   'partner_id': cls.partner_b.id}),
                (0, 0, {'debit': 0.0,       'credit': 300.0,    'account_id': accounts[2].id,   'partner_id': cls.partner_c.id}),
                (0, 0, {'debit': 400.0,     'credit': 0.0,      'account_id': accounts[3].id,   'partner_id': cls.partner_a.id}),
                (0, 0, {'debit': 0.0,       'credit': 1100.0,   'account_id': accounts[4].id,   'partner_id': cls.partner_b.id}),
                (0, 0, {'debit': 700.0,     'credit': 0.0,      'account_id': accounts[6].id,   'partner_id': cls.partner_a.id}),
                (0, 0, {'debit': 0.0,       'credit': 800.0,    'account_id': accounts[7].id,   'partner_id': cls.partner_b.id}),
                (0, 0, {'debit': 800.0,     'credit': 0.0,      'account_id': accounts[8].id,   'partner_id': cls.partner_c.id}),
            ],
        })
        cls.move_2019.action_post()

        cls.move_2018 = cls.env['account.move'].create({
            'move_type': 'entry',
            'date': fields.Date.from_string('2018-01-01'),
            'line_ids': [
                (0, 0, {'debit': 1000.0,    'credit': 0.0,      'account_id': accounts[0].id,   'partner_id': cls.partner_a.id}),
                (0, 0, {'debit': 0.0,       'credit': 1000.0,   'account_id': accounts[2].id,   'partner_id': cls.partner_b.id}),
                (0, 0, {'debit': 250.0,     'credit': 0.0,      'account_id': accounts[0].id,   'partner_id': cls.partner_a.id}),
                (0, 0, {'debit': 0.0,       'credit': 250.0,    'account_id': accounts[9].id,   'partner_id': cls.partner_a.id}),
            ],
        })
        cls.move_2018.action_post()

        cls.move_2017 = cls.env['account.move'].with_company(cls.company_data_2['company']).create({
            'move_type': 'entry',
            'date': fields.Date.from_string('2017-01-01'),
            'line_ids': [
                (0, 0, {'debit': 2000.0,    'credit': 0.0,      'account_id': accounts_2[0].id, 'partner_id': cls.partner_a.id}),
                (0, 0, {'debit': 0.0,       'credit': 4000.0,   'account_id': accounts_2[2].id, 'partner_id': cls.partner_b.id}),
                (0, 0, {'debit': 0.0,       'credit': 5000.0,   'account_id': accounts_2[4].id, 'partner_id': cls.partner_c.id}),
                (0, 0, {'debit': 7000.0,    'credit': 0.0,      'account_id': accounts_2[6].id, 'partner_id': cls.partner_a.id}),
            ],
        })
        cls.move_2017.action_post()

        cls.report = cls.env.ref('account_reports.account_financial_report_balancesheet0')
        cls.report.applicable_filters_ids |= cls.filter

    def test_financial_report_single_company(self):
        line_id = self.env.ref('account_reports.account_financial_report_bank_view0').id
        options = self._init_options(self.report, fields.Date.from_string('2019-01-01'), fields.Date.from_string('2019-12-31'))
        options['unfolded_lines'] = [line_id]
        options.pop('multi_company', None)

        headers, lines = self.report._get_table(options)
        self.assertLinesValues(
            lines,
            #   Name                                            Balance
            [   0,                                              1],
            [
                ('ASSETS',                                      50.0),
                ('Current Assets',                              -650.0),
                ('Bank and Cash Accounts',                      -1300.0),
                ('code2 account2',                              -1300.0),
                ('Total Bank and Cash Accounts',                -1300.0),
                ('Receivables',                                 1350.0),
                ('Current Assets',                              400.0),
                ('Prepayments',                                 -1100.0),
                ('Total Current Assets',                        -650.0),
                ('Plus Fixed Assets',                           0.0),
                ('Plus Non-current Assets',                     700.0),
                ('Total ASSETS',                                50.0),

                ('LIABILITIES',                                 -200.0),
                ('Current Liabilities',                         -200.0),
                ('Current Liabilities',                         0.0),
                ('Payables',                                    -200.0),
                ('Total Current Liabilities',                   -200.0),
                ('Plus Non-current Liabilities',                0.0),
                ('Total LIABILITIES',                           -200.0),

                ('EQUITY',                                      250.0),
                ('Unallocated Earnings',                        -550.0),
                ('Current Year Unallocated Earnings',           -800.0),
                ('Current Year Earnings',                       0.0),
                ('Current Year Allocated Earnings',             -800.0),
                ('Total Current Year Unallocated Earnings',     -800.0),
                ('Previous Years Unallocated Earnings',         250.0),
                ('Total Unallocated Earnings',                  -550.0),
                ('Retained Earnings',                           800.0),
                ('Total EQUITY',                                250.0),

                ('LIABILITIES + EQUITY',                        50.0),
            ],
        )

        self.assertLinesValues(
            self.report._get_lines(options, line_id=line_id),
            #   Name                                            Balance
            [   0,                                              1],
            [
                ('Bank and Cash Accounts',                      -1300.0),
                ('code2 account2',                              -1300.0),
                ('Total Bank and Cash Accounts',                -1300.0),
            ],
        )

    def test_financial_report_multi_company_currency(self):
        line_id = self.env.ref('account_reports.account_financial_report_bank_view0').id
        options = self._init_options(self.report, fields.Date.from_string('2019-01-01'), fields.Date.from_string('2019-12-31'))
        options['unfolded_lines'] = [line_id]

        headers, lines = self.report._get_table(options)
        self.assertLinesValues(
            lines,
            #   Name                                            Balance
            [   0,                                              1],
            [
                ('ASSETS',                                      50.0),
                ('Current Assets',                              -4150.0),
                ('Bank and Cash Accounts',                      -3300.0),
                ('code102 account102',                          -2000.0),
                ('code2 account2',                              -1300.0),
                ('Total Bank and Cash Accounts',                -3300.0),
                ('Receivables',                                 2350.0),
                ('Current Assets',                              400.0),
                ('Prepayments',                                 -3600.0),
                ('Total Current Assets',                        -4150.0),
                ('Plus Fixed Assets',                           0.0),
                ('Plus Non-current Assets',                     4200.0),
                ('Total ASSETS',                                50.0),

                ('LIABILITIES',                                 -200.0),
                ('Current Liabilities',                         -200.0),
                ('Current Liabilities',                         0.0),
                ('Payables',                                    -200.0),
                ('Total Current Liabilities',                   -200.0),
                ('Plus Non-current Liabilities',                0.0),
                ('Total LIABILITIES',                           -200.0),

                ('EQUITY',                                      250.0),
                ('Unallocated Earnings',                        -550.0),
                ('Current Year Unallocated Earnings',           -800.0),
                ('Current Year Earnings',                       0.0),
                ('Current Year Allocated Earnings',             -800.0),
                ('Total Current Year Unallocated Earnings',     -800.0),
                ('Previous Years Unallocated Earnings',         250.0),
                ('Total Unallocated Earnings',                  -550.0),
                ('Retained Earnings',                           800.0),
                ('Total EQUITY',                                250.0),

                ('LIABILITIES + EQUITY',                        50.0),
            ],
        )

        self.assertLinesValues(
            self.report._get_lines(options, line_id=line_id),
            #   Name                                            Balance
            [   0,                                              1],
            [
                ('Bank and Cash Accounts',                      -3300.0),
                ('code102 account102',                          -2000.0),
                ('code2 account2',                              -1300.0),
                ('Total Bank and Cash Accounts',                -3300.0),
            ],
        )

    def test_financial_report_comparison(self):
        line_id = self.env.ref('account_reports.account_financial_report_bank_view0').id
        options = self._init_options(self.report, fields.Date.from_string('2019-01-01'), fields.Date.from_string('2019-12-31'))
        options = self._update_comparison_filter(options, self.report, 'custom', 1, date_to=fields.Date.from_string('2018-12-31'))
        options['unfolded_lines'] = [line_id]

        headers, lines = self.report._get_table(options)
        self.assertLinesValues(
            lines,
            #   Name                                            Balance     Comparison  %
            [   0,                                              1,          2,          3],
            [
                ('ASSETS',                                      50.0,       250.0,      '-80.0%'),
                ('Current Assets',                              -4150.0,    -3250.0,    '27.7%'),
                ('Bank and Cash Accounts',                      -3300.0,    -3000.0,    '10.0%'),
                ('code102 account102',                          -2000.0,    -2000.0,    '0.0%'),
                ('code2 account2',                              -1300.0,    -1000.0,    '30.0%'),
                ('Total Bank and Cash Accounts',                -3300.0,    -3000.0,    '10.0%'),
                ('Receivables',                                 2350.0,     2250.0,     '4.4%'),
                ('Current Assets',                              400.0,      0.0,        'n/a'),
                ('Prepayments',                                 -3600.0,    -2500.0,    '44.0%'),
                ('Total Current Assets',                        -4150.0,    -3250.0,    '27.7%'),
                ('Plus Fixed Assets',                           0.0,        0.0,        'n/a'),
                ('Plus Non-current Assets',                     4200.0,     3500.0,     '20.0%'),
                ('Total ASSETS',                                50.0,       250.0,      '-80.0%'),

                ('LIABILITIES',                                 -200.0,     0.0,        'n/a'),
                ('Current Liabilities',                         -200.0,     0.0,        'n/a'),
                ('Current Liabilities',                         0.0,        0.0,        'n/a'),
                ('Payables',                                    -200.0,     0.0,        'n/a'),
                ('Total Current Liabilities',                   -200.0,     0.0,        'n/a'),
                ('Plus Non-current Liabilities',                0.0,        0.0,        'n/a'),
                ('Total LIABILITIES',                           -200.0,     0.0,        'n/a'),

                ('EQUITY',                                      250.0,      250.0,      '0.0%'),
                ('Unallocated Earnings',                        -550.0,     250.0,      '-320.0%'),
                ('Current Year Unallocated Earnings',           -800.0,     250.0,      '-420.0%'),
                ('Current Year Earnings',                       0.0,        250.0,      '-100.0%'),
                ('Current Year Allocated Earnings',             -800.0,     0.0,        'n/a'),
                ('Total Current Year Unallocated Earnings',     -800.0,     250.0,      '-420.0%'),
                ('Previous Years Unallocated Earnings',         250.0,      0.0,        'n/a'),
                ('Total Unallocated Earnings',                  -550.0,     250.0,      '-320.0%'),
                ('Retained Earnings',                           800.0,      0.0,        'n/a'),
                ('Total EQUITY',                                250.0,      250.0,      '0.0%'),

                ('LIABILITIES + EQUITY',                        50.0,       250.0,      '-80.0%'),
            ],
        )

        self.assertLinesValues(
            self.report._get_lines(options, line_id=line_id),
            #   Name                                            Balance     Comparison  %
            [   0,                                              1,          2,          3],
            [
                ('Bank and Cash Accounts',                      -3300.0,    -3000.0,    '10.0%'),
                ('code102 account102',                          -2000.0,    -2000.0,    '0.0%'),
                ('code2 account2',                              -1300.0,    -1000.0,    '30.0%'),
                ('Total Bank and Cash Accounts',                -3300.0,    -3000.0,    '10.0%'),
            ],
        )

    def test_financial_report_custom_filters(self):
        line_id = self.env.ref('account_reports.account_financial_report_receivable0').id
        options = self._init_options(self.report, fields.Date.from_string('2019-01-01'), fields.Date.from_string('2019-12-31'))
        options = self._update_comparison_filter(options, self.report, 'custom', 1, date_to=fields.Date.from_string('2018-12-31'))
        options = self._update_multi_selector_filter(options, 'ir_filters', self.filter.ids)
        options['unfolded_lines'] = [line_id]

        headers, lines = self.report._get_table(options)
        self.assertHeadersValues(headers, [
            [   ('', 1),                                                ('As of 12/31/2019',  3),                                   ('As of 12/31/2018', 3)],
            [   ('', 1),                                    ('2017-01-01', 1),  ('2018-01-01', 1),  ('2019-01-01', 1),  ('2017-01-01', 1),  ('2018-01-01', 1),  ('2019-01-01', 1)],
            [   ('', 1),                                    ('partner_a', 1),   ('partner_a', 1),   ('partner_a', 1),   ('partner_a', 1),   ('partner_a', 1),   ('partner_a', 1)],
        ])
        self.assertLinesValues(
            lines,
            [   0,                                          1,                  2,                  3,                  4,                  5,                  6],
            [
                ('ASSETS',                                  4500.0,             1250.0,             1150.0,             4500.0,             1250.0,             0.0),
                ('Current Assets',                          1000.0,             1250.0,             450.0,              1000.0,             1250.0,             0.0),
                ('Bank and Cash Accounts',                  0.0,                0.0,                0.0,                0.0,                0.0,                0.0),
                ('Receivables',                             1000.0,             1250.0,             50.0,               1000.0,             1250.0,             0.0),
                ('code0 account0',                          0.0,                1250.0,             50.0,               0.0,                1250.0,             0.0),
                ('code100 account100',                      1000.0,             0.0,                0.0,                1000.0,             0.0,                0.0),
                ('Total Receivables',                       1000.0,             1250.0,             50.0,               1000.0,             1250.0,             0.0),
                ('Current Assets',                          0.0,                0.0,                400.0,              0.0,                0.0,                0.0),
                ('Prepayments',                             0.0,                0.0,                0.0,                0.0,                0.0,                0.0),
                ('Total Current Assets',                    1000.0,             1250.0,             450.0,              1000.0,             1250.0,             0.0),
                ('Plus Fixed Assets',                       0.0,                0.0,                0.0,                0.0,                0.0,                0.0),
                ('Plus Non-current Assets',                 3500.0,             0.0,                700.0,              3500.0,             0.0,                0.0),
                ('Total ASSETS',                            4500.0,             1250.0,             1150.0,             4500.0,             1250.0,             0.0),

                ('LIABILITIES',                             0.0,                0.0,                0.0,                0.0,                0.0,                0.0),
                ('Current Liabilities',                     0.0,                0.0,                0.0,                0.0,                0.0,                0.0),
                ('Current Liabilities',                     0.0,                0.0,                0.0,                0.0,                0.0,                0.0),
                ('Payables',                                0.0,                0.0,                0.0,                0.0,                0.0,                0.0),
                ('Total Current Liabilities',               0.0,                0.0,                0.0,                0.0,                0.0,                0.0),
                ('Plus Non-current Liabilities',            0.0,                0.0,                0.0,                0.0,                0.0,                0.0),
                ('Total LIABILITIES',                       0.0,                0.0,                0.0,                0.0,                0.0,                0.0),

                ('EQUITY',                                  0.0,                250.0,              0.0,                0.0,                250.0,              0.0),
                ('Unallocated Earnings',                    0.0,                250.0,              0.0,                0.0,                250.0,              0.0),
                ('Current Year Unallocated Earnings',       0.0,                0.0,                0.0,                0.0,                250.0,              0.0),
                ('Current Year Earnings',                   0.0,                0.0,                0.0,                0.0,                250.0,              0.0),
                ('Current Year Allocated Earnings',         0.0,                0.0,                0.0,                0.0,                0.0,                0.0),
                ('Total Current Year Unallocated Earnings', 0.0,                0.0,                0.0,                0.0,                250.0,              0.0),
                ('Previous Years Unallocated Earnings',     0.0,                250.0,              0.0,                0.0,                0.0,                0.0),
                ('Total Unallocated Earnings',              0.0,                250.0,              0.0,                0.0,                250.0,              0.0),
                ('Retained Earnings',                       0.0,                0.0,                0.0,                0.0,                0.0,                0.0),
                ('Total EQUITY',                            0.0,                250.0,              0.0,                0.0,                250.0,              0.0),

                ('LIABILITIES + EQUITY',                    0.0,                250.0,              0.0,                0.0,                250.0,              0.0),
            ],
        )

        self.assertLinesValues(
            self.report._get_lines(options, line_id=line_id),
            [   0,                                          1,                  2,                  3,                  4,                  5,                  6],
            [
                ('Receivables',                             1000.0,             1250.0,             50.0,               1000.0,             1250.0,             0.0),
                ('code0 account0',                          0.0,                1250.0,             50.0,               0.0,                1250.0,             0.0),
                ('code100 account100',                      1000.0,             0.0,                0.0,                1000.0,             0.0,                0.0),
                ('Total Receivables',                       1000.0,             1250.0,             50.0,               1000.0,             1250.0,             0.0),
            ],
        )
