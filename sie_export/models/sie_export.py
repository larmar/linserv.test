# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import odoo
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import base64

from odoo.exceptions import UserError

from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class AccountSIEExport(models.TransientModel):
    _name = "account.sie.export"

    name = fields.Char(default="SIE Export")
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)
    period = fields.Selection(
        [(str(num), str(num)) for num in range((datetime.now().year - 3),
                                               (datetime.now().year + 2))],
        string='Period', required=True, default=str(datetime.now().year - 1))

    date_from = fields.Date(string="Date From")
    date_to = fields.Date(string="Date To")

    sie_file = fields.Binary('SIE File')

    def export_sie(self):

        if self.date_from > self.date_to:
            raise UserError(_("Date To can not be earlier than Date From!"))

        SIE4 = ""

        konto = {}
        res = {}
        context = {}
        balance = {}
        ver_trans = ''

        context['company_ids'] = self.company_id.id

        SIE4 += '#FLAGGA 0\r\n'
        SIE4 += '#PROGRAM "ODOO" %s\r\n' % (odoo.service.common.exp_version()['server_serie'])
        SIE4 += '#FORMAT PC8\r\n'
        SIE4 += '#GEN ' + str(date.today().strftime('%Y%m%d')) + ' "' + self.env.user.name + '"\r\n'
        SIE4 += '#ORGNR %s\r\n' % self.company_id.company_registry
        SIE4 += '#SIETYP 4\r\n'
        SIE4 += '#FNAMN "%s"\r\n' % self.company_id.name

        # 0 -> -1
        rar_0_date_from_year = ''
        rar_0_date_to_year = ''
        rar_0_date_from_day = ''
        rar_0_date_to_day = ''
        rar_0_date_from_month = ''
        rar_0_date_to_month = ''

        # we take last and before last year data
        for i in range(0, -2, -1):
            res[i] = {}
            balance[i] = {}

            date_from = self.date_from + relativedelta(years=i)
            date_to = self.date_to + relativedelta(years=i)

            cur_year = date.today().year
            company = self.company_id

            account_move = self.env['account.move'].search(
                [('date', '>=', date_from),
                 ('date', '<=', date_to),
                 ('company_id', '=', company.id),
                 ('state', '=', 'posted')])

            if i == 0 and not account_move:
                raise UserError(_("There are no journal entries for this period!"))
            elif not account_move:
                continue
            else:
                if i == 0:

                    # VER & TRANS

                    for move in account_move.sorted(key=lambda a: (a.name, a.journal_id.type)):
                        ver_trans += '#VER %s %s %s "%s"\r\n{\r\n' % (
                            move.journal_id.code, move.name, move.date.strftime('%Y%m%d'), self.if_empty(move.ref))
                        for move_line in move.line_ids:
                            ver_trans += '#TRANS %s {} %s %s "%s" 0\r\n' % (
                                move_line.account_id.code, "%.2f" % (move_line.debit - move_line.credit),
                                move.date.strftime('%Y%m%d'), self.if_empty(move_line.name).replace('\n',
                                                                                                    ' '))  # added replace function to format description into one line
                            konto[move_line.account_id.code] = move_line.account_id.name

                        ver_trans += '}\r\n'

                move_lines = self.env['account.move.line'].search(
                    [('date', '>=', date_from),
                     ('date', '<=', date_to),
                     ('company_id', '=', company.id)])

                # Profit & Loss Balances

                for move in move_lines:
                    if not move.account_id.user_type_id.include_initial_balance:
                        if move.account_id.code not in res[i]:
                            res[i][move.account_id.code] = -move.balance if move.balance > 0 else abs(move.balance)
                        else:
                            res[i][move.account_id.code] += -move.balance if move.balance > 0 else abs(move.balance)
                    konto[move.account_id.code] = move.account_id.name

                # Opening & Closing Balances

                report = self.env['account.general.ledger']

                report.filter_date = {
                    'date_from': date_from.strftime(DEFAULT_SERVER_DATE_FORMAT),
                    'date_to': date_to.strftime(DEFAULT_SERVER_DATE_FORMAT),
                    'filter': 'custom',
                    'mode': report.filter_date.get('mode', 'range'),
                }

                options = report._get_options(None)
                options['unfold_all'] = True
                options_list = report._get_options_periods_list(options)

                accounts_results, taxes_results = \
                    self.with_context(date_from_aml=str(date_from), date_to=date_to, company_ids=[self.company_id.id],
                                      state='posted', date_from=date_from).env[
                        'account.general.ledger']._do_query(options_list, None)

                balance[i] = accounts_results

                if i == 0:
                    year = date_from.year
                    if cur_year == year and company.fiscalyear_last_month == 12 and company.fiscalyear_last_day == 31:
                        SIE4 += '#RAR %s %s %s1231 \r\n' % (i, date_from.strftime('%Y%m%d'), year)
                        rar_0_date_from_year = year
                        rar_0_date_from_month = date_from.month
                        rar_0_date_from_day = date_from.day
                        rar_0_date_to_year = year
                        rar_0_date_to_month = '12'
                        rar_0_date_to_day = '31'
                    elif (cur_year - 1) == year and company.fiscalyear_last_month == 4 and \
                            company.fiscalyear_last_day == 30:
                        SIE4 += '#RAR %s %s %s0430 \r\n' % (i, date_from.strftime('%Y%m%d'), cur_year)
                        rar_0_date_from_year = year
                        rar_0_date_from_month = date_from.month
                        rar_0_date_from_day = date_from.day
                        rar_0_date_to_year = cur_year
                        rar_0_date_to_month = '04'
                        rar_0_date_to_day = '30'
                    else:
                        SIE4 += '#RAR %s %s %s \r\n' % (i, date_from.strftime('%Y%m%d'), date_to.strftime('%Y%m%d'))
                        rar_0_date_from_year = year
                        rar_0_date_from_month = date_from.month
                        rar_0_date_from_day = date_from.day
                        rar_0_date_to_year = date_to.year
                        rar_0_date_to_month = date_to.month
                        rar_0_date_to_day = date_to.day
                else:
                    year_from = str(rar_0_date_from_year - 1)
                    year_to = str(rar_0_date_to_year - 1)
                    if len(str(rar_0_date_from_month)) == 1:
                        rar_0_date_from_month = '0' + str(rar_0_date_from_month)
                    if len(str(rar_0_date_from_day)) == 1:
                        rar_0_date_from_day = '0' + str(rar_0_date_from_day)
                    if len(str(rar_0_date_to_month)) == 1:
                        rar_0_date_to_month = '0' + str(rar_0_date_to_month)
                    if len(str(rar_0_date_to_day)) == 1:
                        rar_0_date_to_day = '0' + str(rar_0_date_to_day)
                    SIE4 += '#RAR %s %s %s \r\n' % (i,
                                                    (str(year_from) + str(rar_0_date_from_month) + str(
                                                        rar_0_date_from_day)),
                                                    (str(year_to) + str(rar_0_date_to_month) + str(rar_0_date_to_day)))

        for konto_line in konto:
            SIE4 += '#KONTO %s "%s"\r\n' % (konto_line, konto[konto_line])

        # IB & UB

        IB = ''
        UB = ''

        for year_no, data_list in balance.items():
            for account in data_list:

                if account[0].user_type_id.include_initial_balance:
                    # todo what to do with lines which dont have initial_balance value?
                    if 'sum' in account[1][0] and 'initial_balance' in account[1][0]:
                        IB += "#IB %s %s %s 0\r\n" % (
                            year_no, account[0].code, "%.2f" % account[1][0]['initial_balance']['balance'])
                        UB += "#UB %s %s %s 0\r\n" % (
                            year_no, account[0].code, "%.2f" % account[1][0]['sum']['balance'])

        SIE4 += IB
        SIE4 += UB

        # RES

        for year_no, dict in res.items():
            for account in dict:
                SIE4 += '#RES %s %s %s 0\r\n' % (year_no, account, "%.2f" % -dict[account])

        SIE4 += ver_trans
        self.update({'sie_file': base64.b64encode(SIE4.encode('cp437', 'xmlcharrefreplace'))})
        sql_query = "select id from account_sie_export order by id desc limit 1"
        self.env.cr.execute(sql_query)
        last_record = self.env.cr.fetchone()

        file_name = "SIE_%s.SE" % (self.company_id.name)

        url = "web/content/?model=account.sie.export&id=%s&field=sie_file&download=true&filename=" + file_name

        return {
            'type': 'ir.actions.act_url',
            'url': url % (last_record),
            'target': 'new',
        }

    def if_empty(self, string):
        '''

        Check if string empty return quotes else string

        :param string:
        :return:
        '''
        return string if string else ""
