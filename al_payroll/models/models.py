# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo import time
import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, AccessError

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def _default_journal(self):
        return self.env['account.journal'].search([('name', '=', 'Payroll Expenses')], limit=1).id

    journal_id = fields.Many2one('account.journal', string='Journals', required=True, default=_default_journal)
    basic = fields.Monetary(string="Basic", digits=(16, 2), related='contract_id.wage', store=True)
    housing_allowance = fields.Monetary(string="Housing Allowance", compute='salary_computation_ag', store=True)
    food_allowance = fields.Monetary(string="Food Allowance", compute='salary_computation_ag', store=True)
    os_allowance = fields.Monetary(string="OS Allowance", compute='salary_computation_ag', store=True)
    transport_allowance = fields.Monetary(string="Transport Allowance", compute='salary_computation_ag', store=True)
    other_allowance = fields.Monetary(string="Other Allowance", compute='salary_computation_ag', store=True)
    os_other_allowance = fields.Monetary(string="OS Other Allowance", compute='salary_computation_ag', store=True)
    incentive_allowance = fields.Monetary(string="Incentive Allowance", compute='salary_computation_ag', store=True)
    os_incentive_allowance = fields.Monetary(string="OS Incentive", compute='salary_computation_ag', store=True)
    over_time = fields.Monetary(string="Overtime Allowance", compute='salary_computation_ag', store=True)
    os_over_time = fields.Monetary(string="OS Overtime", compute='salary_computation_ag', store=True)
    gosi_alloance = fields.Monetary(string="GOSI Allowance", compute='salary_computation_ag', store=True)
    currency_id = fields.Many2one(string="Currency", related='company_id.currency_id', readonly=True)
    total_salary = fields.Monetary(string="Total Salary", compute='salary_computation_ag', store=True)
    gross_tree = fields.Monetary(string="Gross", compute='salary_computation_ag', store=True)
    amount_gosi_ksa = fields.Monetary(string="GOSI Deduction", compute='salary_computation_ag', store=True)
    amount_comp_gosi_ksa = fields.Monetary(string="GOSI Company Share", compute='salary_computation_ag', store=True)
    penalty_tree = fields.Monetary(string="Penalty Deduction", compute='salary_computation_ag', store=True)
    other_tree = fields.Monetary(string="Other Deductions", compute='salary_computation_ag', store=True)
    absent = fields.Monetary(string="Absent Deduction", compute='salary_computation_ag', store=True)
    loan = fields.Monetary(string="Loan", compute='salary_computation_ag', store=True)
    total_ded = fields.Monetary(string="Total Deduction", compute='salary_computation_ag', store=True)
    net_salary = fields.Monetary(string="NET", compute='salary_computation_ag', store=True)
#    amount_vat = fields.Float(string="VAT", compute='salary_computation_ag')
#    net_salary_paid = fields.Float(string="NET Paid", compute='salary_computation_ag')
    agency_cost = fields.Monetary(string="Agency Cost", compute='salary_computation_ag', store=True)
    gosi_no = fields.Char(string='GOSI Reference', store=True)
    coach_id = fields.Many2one(string='Coach', related='employee_id.coach_id', store=True)
    nationality_id = fields.Char(string='National ID', related='employee_id.identification_id', store=True)
    department_id = fields.Many2one(string='Department', related='employee_id.department_id', store=True)
    bank_code_id = fields.Char(string='Bank Code', related='employee_id.bank_account_id.bank_code', store=True)
    iban_id = fields.Char(string='IBAN', related='employee_id.bank_account_id.acc_number', store=True)
    bank_other_allowance = fields.Float(string="Other Allowance", store=True)
    bank_payslip_allowance = fields.Monetary(string="Any Other Allowance", compute='salary_computation_ag', store=True)
    bank_hra = fields.Float(string="HRA", store=True)
    bank_days = fields.Float(string="Days", related='contract_id.bank_days', store=True)
    bank_total_salary = fields.Float(string="Total Salary", related='contract_id.bank_total_salary', store=True)
    late_in = fields.Monetary(string="Late In", compute='salary_computation_ag', store=True)
    difference_time = fields.Monetary(string="Difference Time", compute='salary_computation_ag', store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('hrapproval', 'HR Approved'),
        ('finance', 'Finance Approved'),
        ('verify', 'Waiting'),
        ('done', 'Done'),
        ('cancel', 'Rejected'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft',
        help="""* When the payslip is created the status is \'Draft\'
                \n* If the payslip is under verification, the status is \'Waiting\'.
                \n* If the payslip is confirmed then status is set to \'Done\'.
                \n* When user cancel payslip the status is \'Rejected\'.""")
    @api.onchange('bank_hra','housing_allowance','bank_anyother_allowance','food_allowance','transport_allowance','incentive_allowance','over_time','gosi_alloance','other_allowance','bank_payslip_allowance')
    def bank_allowances_calculation(self):
        self.bank_hra = self.housing_allowance
        self.bank_other_allowance = self.food_allowance + self.transport_allowance + self.incentive_allowance + self.over_time + self.other_allowance + self.gosi_alloance

    @api.onchange('contract_id')
    def _onchange_contract_id(self):
        for value in self:
            if value.contract_id:
                value.bank_other_allowance = value.contract_id.bank_other_allowance
                value.bank_total_salary = value.contract_id.bank_total_salary
                value.bank_days = value.contract_id.bank_days

    @api.multi
    def salary_computation_ag(self):
        for obj in self:
            for value in obj.line_ids:
                if value.name == 'Incentive Allowance':
                    amount_ia = value.total
                    obj.incentive_allowance = amount_ia
                if value.name == 'Transport Allowance':
                    amount_ta = value.total
                    obj.transport_allowance = amount_ia
                if value.name == 'Loan':
                    amount_lo = value.total
                    obj.loan = amount_ia
                if value.name == 'Agency Cost':
                    amount_ac = value.total
                    obj.agency_cost = amount_ia
                if value.name == 'Food Allowance':
                    amount_fa = value.total
                    obj.food_allowance = amount_ia
                if value.name == 'OS Incentive Allowance':
                    amount_osia = value.total
                    obj.os_incentive_allowance = amount_osia
                if value.name == 'OS Overtime Allowance':
                    amount_osot = value.total
                    obj.os_over_time = amount_osot
                if value.name == 'OS Other Allowance':
                    amount_osoa = value.total
                    obj.os_other_allowance = amount_osoa
                if value.name == 'Gross':
                    amount_gr = value.total
                    obj.gross_tree = amount_gr
                if value.name == 'Basic':
                    amount_basic = value.total
                    obj.basic = amount_basic
                if value.name == 'Housing Allowance':
                    amount_housing = value.total
                    obj.housing_allowance = amount_housing
                if value.name == 'GOSI Contribution For Saudi Employee':
                    amount_gosi_ksa = value.total
                    obj.amount_gosi_ksa = amount_gosi_ksa
                if value.name == 'GOSI Company Contribution For Saudi Employee':
                    amount_comp_gosi_ksa = value.total
                    obj.amount_comp_gosi_ksa = amount_comp_gosi_ksa
                if value.name == 'Penalty Deduction':
                    penalty_tree = value.total
                    obj.penalty_tree = penalty_tree
                if value.name == 'Other Deductions':
                    other_tree = value.total
                    obj.other_tree = other_tree
                if value.name == 'Net Salary':
                    net_salary = value.total
                    obj.net_salary = net_salary
#                if value.name == 'VAT':
#                    amount_vat = value.total
#                    obj.amount_vat = amount_vat
#                if value.name == 'Net Salary Paid':
#                    net_salary_paid = value.total
#                    obj.net_salary_paid = net_salary_paid
                if value.name == 'Absence':
                    absent = value.total
                    obj.absent = absent
                if value.name == 'Difference Time':
                    difference_time = value.total
                    obj.difference_time = difference_time
                if value.name == 'Late In':
                    late_in = value.total
                    obj.late_in = late_in
                if value.name == 'Overtime Allowance':
                    over_time = value.total
                    obj.over_time = over_time
                if value.name == 'Agency Cost':
                    agency_cost = value.total
                    obj.agency_cost = agency_cost
            obj.total_ded = obj.penalty_tree + obj.other_tree + obj.absent
            obj.os_allowance = obj.os_other_allowance + obj.os_incentive_allowance + obj.os_over_time
            obj.bank_payslip_allowance = ((obj.gross_tree - obj.basic) - obj.housing_allowance)

    @api.multi
    def action_payslip_hrapproval(self):
        return self.write({'state': 'hrapproval'})

    @api.multi
    def action_payslip_finance(self):
        return self.write({'state': 'finance'})

    @api.multi
    def action_payslip_draft(self):
        return self.write({'state': 'draft'})


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    def _default_journal(self):
        return self.env['account.journal'].search([('name', '=', 'Payroll Expenses')], limit=1).id

    journal_id = fields.Many2one('account.journal', string='Journals', required=True, default=_default_journal)
    total_basic_allowance = fields.Float(string="BASIC + ALW", default=0)
    total_ded = fields.Float(string="Total Deductions", default=0)
    total_net = fields.Float(string="Total NET", default=0)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('hrapproval', 'HR Approved'),
        ('close', 'Close'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft')

    @api.multi
    @api.depends('slip_ids.total_net_paid')
    def hrapproval_payslip_run(self):
        for record in self:
#            record.total_basic_allowance = record.total_ded = record.total_net = record.total_vat = record.total_net_paid = 0.0
            record.total_basic_allowance = record.total_ded = record.total_net = 0.0
            for value in record.slip_ids:
                self.total_basic_allowance += value.gross_tree
#                self.total_ded += (value.net_salary - value.gross_tree)
                self.total_ded += value.total_ded
                self.total_net += value.net_salary
#                self.total_vat += value.amount_vat
#                self.total_net_paid += value.net_salary_paid
                record.update({
                    'total_basic_allowance': record.total_basic_allowance,
                    'total_ded': record.total_ded,
                    'total_net': record.total_net,
#                    'total_vat': record.total_vat,
#                    'total_net_paid': record.total_net_paid,
                })

#        print (self.total_basic_allowance)
#        print ('total_basic_allowance')
#        print (self.total_ded)
#        print ('total_ded')
#        print (self.total_net)
#        print ('total_net')
#        print (self.total_vat)
#        print ('total_vat')
#        print (self.total_net_paid)
#        print ('total_net_paid')

        return self.write({'state': 'hrapproval'})


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    account_analytic_bool = fields.Boolean('Analytic Account in Contract')


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def mail_reminder(self):
        """Sending expiry date notification for ID and Passport"""

        now = datetime.now() + timedelta(days=1)
        date_now = now.date()
        match = self.search([])
        for i in match:
            if i.id_expiry_date:
                exp_date = fields.Date.from_string(i.id_expiry_date) - timedelta(days=14)
                if date_now >= exp_date:
                    mail_content = "  Hello  " + i.name + ",<br>Your ID " + i.identification_id + "is going to expire on " + \
                                   str(i.id_expiry_date) + ". Please renew it before expiry date"
                    main_content = {
                        'subject': _('ID-%s Expired On %s') % (i.identification_id, i.id_expiry_date),
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': i.work_email,
                    }
                    self.env['mail.mail'].sudo().create(main_content).send()
        match1 = self.search([])
        for i in match1:
            if i.passport_expiry_date:
                exp_date1 = fields.Date.from_string(i.passport_expiry_date) - timedelta(days=180)
                if date_now >= exp_date1:
                    mail_content = "  Hello  " + i.name + ",<br>Your Passport " + i.passport_id + "is going to expire on " + \
                                   str(i.passport_expiry_date) + ". Please renew it before expiry date"
                    main_content = {
                        'subject': _('Passport-%s Expired On %s') % (i.passport_id, i.passport_expiry_date),
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': i.work_email,
                    }
                    self.env['mail.mail'].sudo().create(main_content).send()

    personal_mobile = fields.Char(string='Mobile', related='address_home_id.mobile', store=True)
    emergency_contact = fields.Char(string='Emergency Contact', store=True)
    joining_date = fields.Date(string='Joining Date')
    id_expiry_date = fields.Date(string='ID Expiry Date', required=False, help='Expiry date of Identification ID')
    passport_expiry_date = fields.Date(string='Passport Expiry Date', help='Expiry date of Passport ID')
    id_attachment_id = fields.Many2many('ir.attachment', 'id_attachment_rel', 'id_ref', 'attach_ref',
                                        string="Attachment", help='You can attach the copy of your Id')
    passport_attachment_id = fields.Many2many('ir.attachment', 'passport_attachment_rel', 'passport_ref', 'attach_ref1',
                                              string="Attachment",
                                              help='You can attach the copy of Passport')
    fam_ids = fields.Many2one('hr.employee.family',  string='Family', help='Family Information')
    type = fields.Selection([('saudi', 'Saudi')], string='Type')
    gosi_number = fields.Char(string='GOSI Number')
    issue_date = fields.Date(string='Issued Date')
    age = fields.Float(string='Age', compute='get_age', copy=True, digits=None)
    limit = fields.Boolean(string='Eligible For GOSI')
    coach_id = fields.Many2one('hr.sponsors', string='Sponsor')
    staff_id = fields.Char(string='Staff ID', readonly=True, required=True, copy=False, default='New')
    joining_date = fields.Date(string='Joined Date', required=False)
    work_location = fields.Char('Work Location', required=False)
    mobile_phone = fields.Char('Work Mobile', required=False, default='Riyadh')
    department_id = fields.Many2one('hr.department', 'Department', required=False)
    job_id = fields.Many2one('hr.job', 'Job Position', required=False)
    parent_id = fields.Many2one('hr.employee', 'Manager', required=False)
    country_id = fields.Many2one('res.country', 'Nationality (Country)', groups="hr.group_hr_user", required=False)
    identification_id = fields.Char(string='Identification No', groups="hr.group_hr_user", required=False)
    health_certificate_number = fields.Char(string='Certificate #', required=False)
    health_issue_date = fields.Date(string='Issue Date', required=False)
    health_expiry_date = fields.Date(string='Expiry Date', required=False)
    employee_status = fields.Many2one('employee.status', string='Status', store=True)
    national_status = fields.Selection([
        ('saudi', 'Local'),
        ('foreigner', 'Foreigner')
    ], default="foreigner", required=False)
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], groups="hr.group_hr_user", default="male", required=False)
    marital = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('cohabitant', 'Legal Cohabitant'),
        ('widower', 'Widower'),
        ('divorced', 'Divorced')
    ], string='Marital Status', groups="hr.group_hr_user", default='single', required=False)
    birthday = fields.Date('Date of Birth', groups="hr.group_hr_user", required=False)
    place_of_birth = fields.Char('Place of Birth', groups="hr.group_hr_user", required=False)
    country_of_birth = fields.Many2one('res.country', string="Country of Birth", groups="hr.group_hr_user", required=False)
#    employee_contract_id = fields.Many2one('hr.contract', string='Employee Contract', required=False, domain="[('employee_id', '=', id)]")

    @api.model   
    def create(self, vals):
        if vals.get('staff_id', 'New') == 'New':
            vals['staff_id'] = self.env['ir.sequence'].next_by_code('staff.sequence') or 'New'       
#        if vals.get('staff_id', 'New') == 'New' and self.coach_id.name == 'Badon Company':
#            vals['staff_id'] = self.env['ir.sequence'].next_by_code('badon.company') or 'New'
#        if vals.get('staff_id', 'New') == 'New' and self.coach_id.name == 'INTL OS Co':
#            vals['staff_id'] = self.env['ir.sequence'].next_by_code('intl.company') or 'New'
#        if vals.get('staff_id', 'New') == 'New' and self.coach_id.name == 'Naas Company':
#            vals['staff_id'] = self.env['ir.sequence'].next_by_code('naas.company') or 'New'
        result = super(HrEmployee, self).create(vals)       
        return result


    @api.onchange('birthday')
    def get_age(self):
     res = {}
     if self.birthday:
         birthday = self.birthday
         age_calc = (datetime.date.today() - birthday).days/365
         age= str(age_calc)
         self.age = age

    def compute_age(self):
        for res in self:
            if int(res.age) <= 60 and int(res.age) >= 18:
                res.limit = True
            else:
                res.limit = False

class HrContract(models.Model):
    _inherit = 'hr.contract'

    def _default_journal(self):
        return self.env['account.journal'].search([('name', '=', 'Payroll Expenses')], limit=1).id

    housing_allowance = fields.Float(string="Housing Allowance", default=0)
    food_allowance = fields.Float(string="Food Allowance", default=0)
    transport_allowance = fields.Float(string="Transport Allowance", default=0)
    other_allowance = fields.Float(string="Other Allowance", default=0)
    gosi_alloance = fields.Float(string="GOSI Allowance", default=0)
#    total_salary = fields.Float(string="Total Salary", compute='total_salary_calculation')
    agency_cost = fields.Float(string="Agency Cost", default=0)
    total_salary = fields.Float(string="Total Salary", readonly=False)
    bank_other_allowance = fields.Float(string="Bank Other Allowance", default=0)
    bank_days = fields.Float(string="Days", default=30)
    bank_total_salary = fields.Float(string="Bank Total Salary", readonly=False)
    staff_id = fields.Char(related='employee_id.staff_id', string='Staff ID', store=True)
    journal_id = fields.Many2one('account.journal', 'Salary Journal', default=_default_journal, required=True)
    department_id = fields.Many2one('hr.department', string="Department", required=True)
    job_id = fields.Many2one('hr.job', string='Job Position', required=True)
    @api.onchange('total_salary','wage','housing_allowance','food_allowance','transport_allowance','other_allowance','gosi_alloance','agency_cost')
    def total_salary_calculation(self):
        self.bank_other_allowance = self.food_allowance + self.transport_allowance + self.other_allowance + self.gosi_alloance + self.agency_cost
        self.total_salary = self.wage + self.bank_other_allowance + self.housing_allowance


class HrPayslip(models.Model):
    _name = 'hr.bank.payslip'
    _description = 'Bank Pay Slip'

    name = fields.Char(string='Bank Payslip Name', readonly=True,
        states={'draft': [('readonly', False)]})
    number = fields.Char(string='Reference', readonly=True, copy=False,
        states={'draft': [('readonly', False)]})
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, readonly=True,
        states={'draft': [('readonly', False)]})
    date_from = fields.Date(string='Date From', readonly=True, required=True,
        default=lambda self: fields.Date.to_string(date.today().replace(day=1)), states={'draft': [('readonly', False)]})
    date_to = fields.Date(string='Date To', readonly=True, required=True,
        default=lambda self: fields.Date.to_string((datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()),
        states={'draft': [('readonly', False)]})
    # this is chaos: 4 states are defined, 3 are used ('verify' isn't) and 5 exist ('confirm' seems to have existed)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('verify', 'Waiting'),
        ('done', 'Done'),
        ('cancel', 'Rejected'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft',
        help="""* When the payslip is created the status is \'Draft\'
                \n* If the payslip is under verification, the status is \'Waiting\'.
                \n* If the payslip is confirmed then status is set to \'Done\'.
                \n* When user cancel payslip the status is \'Rejected\'.""")
    company_id = fields.Many2one('res.company', string='Company', readonly=True, copy=False,
        default=lambda self: self.env['res.company']._company_default_get(),
        states={'draft': [('readonly', False)]})
    worked_days_line_ids = fields.One2many('hr.payslip.worked_days', 'payslip_id',
        string='Payslip Worked Days', copy=True, readonly=True,
        states={'draft': [('readonly', False)]})
    note = fields.Text(string='Internal Note', readonly=True, states={'draft': [('readonly', False)]})
    contract_id = fields.Many2one('hr.contract', string='Contract', readonly=True,
        states={'draft': [('readonly', False)]})
    credit_note = fields.Boolean(string='Credit Note', readonly=True,
        states={'draft': [('readonly', False)]},
        help="Indicates this payslip has a refund of another")
    basic = fields.Monetary(string="Basic", digits=(16, 2), related='contract_id.wage')
    currency_id = fields.Many2one(string="Currency", related='company_id.currency_id', readonly=True)
    total_salary = fields.Float(string="Total Salary", compute='_onchange_contract_id')
    incentive_allowance = fields.Float(string="Incentive Allowance", compute='salary_computation_ag')
    absent = fields.Float(string="Absent Deduction", compute='salary_computation_ag')
    total_ded = fields.Float(string="Total Deduction", compute='salary_computation_ag')
    net_salary = fields.Float(string="NET", compute='salary_computation_ag')
    over_time = fields.Float(string="Overtime Allowance", compute='salary_computation_ag')
    coach_id = fields.Many2one(string='Coach', related='employee_id.coach_id', store=True)
    bank_other_allowance = fields.Float(string="Other Allowance", default=0)
    bank_days = fields.Float(string="Days", default=30)
    bank_total_salary = fields.Float(string="Total Salary", readonly=False)


class AccountJournal(models.Model):
    _inherit = 'res.partner.bank'

    bank_code = fields.Char(string=' Bank Code', store=True)


class EmployeeStatus(models.Model):
    _name = 'employee.status'

    s_no = fields.Integer(string='Serial No.', required=False)
    name = fields.Char(string='Status', required=True)


class HRSponosors(models.Model):
    _name = 'hr.sponsors'

    name = fields.Char(string='Name(s)', required=True)
    identification_no = fields.Char(string='Identification Number(s)', required=True)




