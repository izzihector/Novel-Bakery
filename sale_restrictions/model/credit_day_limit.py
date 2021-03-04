from odoo import models,api,fields, _
import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning, UserError, ValidationError


class approval_sale(models.Model):
    _name = 'approval.lines'
    day_range = fields.One2many('day.limit','day_limit_id')
    credit_range = fields.One2many('credit.limit', 'credit_range_id')
    
    @api.model
    def create(self, vals):
        self.env.cr.execute("""
        select count(*) from approval_lines;
        """)
        records = self.env.cr.fetchall()
        if records[0][0] > 0:
            raise Warning(_('Please edit the settings, creation not allowed.'))
        return super(approval_sale, self).create(vals)
              
class limit(models.Model):
    _name = 'day.limit'
    day_limit_id = fields.Many2one('approval.lines', ondelete='cascade')
    days = fields.Integer(string="Days")
    group = fields.Many2one('res.groups', string="Allowed group")
    
class credit(models.Model):
    _name = 'credit.limit'
    credit_range_id = fields.Many2one('approval.lines', ondelete='cascade')
    amount_percent = fields.Float(string="% Over Credit Limit")
    group = fields.Many2one('res.groups', string="Allowed group")

class sale_order_inherit(models.Model):
    _inherit = 'sale.order'
    out_days = fields.Integer(compute = 'get_outstanding_days')
    amount_payable_percentage = fields.Float(compute='get_credit_amount')
    credit_limit_status = fields.Boolean(default=False)
    day_limit_status = fields.Boolean(default=False)
    allow_sale_min_price = fields.Boolean(default=False)
        
    # Return current user record
    def get_current_uid(self):
        return self.env['res.users'].search([('id','=', self.env.uid)])
    
    def get_total_amount_payable(self):
        return self.partner_id.credit + self.amount_total + self.get_confirm_so_amount()
    
    # To return approval group record
    def get_approval(self, table):
        return self.env[table].search([('group', 'in', self.get_current_uid().groups_id.ids)])
    
    def get_outstanding_days(self):
        
        # Fetching the earliest open invoice's due date of the selected partner
        invoice_rec = self.env['account.invoice'].search([('partner_id','=',self.partner_id.id),('state','=','open')],order='date_due asc',limit=1).date_due

        # If there is no opened invoice, then allow the user to confirm sale 
        if not invoice_rec:
            return False
        
        difference = relativedelta(datetime.datetime.today(), invoice_rec)
        
        days = str(difference.days)
        months = str(difference.months)
        years = str(difference.years)
        if days == False or days == None:
            days = 0
        if months == False or months == None:
            months = 0
        if years == False or years == None:
            years = 0
        self.out_days = ((int(years)*365)+(int(months)*30)+(int(days)))

        
    def get_credit_amount(self):
        
        # if the user has no credit limit set (to avoid division by zero)
        if self.partner_id.credit_limit > 0:
            self.amount_payable_percentage = (self.get_total_amount_payable() - self.partner_id.credit_limit)
        else:
            self.amount_payable_percentage = self.get_total_amount_payable()
    
    def get_confirm_so_amount(self):
        self.env.cr.execute("""
        select(
        (select sum(amount_total) as total from sale_order where state in ('sale','done') and partner_id= %s )-
        (select sum(amount_total) as total from account_invoice where state in ('open','paid') and partner_id= %s)
        ) as total
        """,(self.partner_id.id, self.partner_id.id))
        amount = self.env.cr.fetchall()
        if not amount[0][0]:
            return 0
        return amount[0][0]
    
    def check_day_limit(self):

        # if the user didn't reach his days limit
        if self.out_days < 0:
            self.state = 'sale'
            return False
        approval_rec = self.get_approval('day.limit')
        
        # If current user isn't in any approval group, don't allow
        if not approval_rec:
            raise Warning(_('You do not exist in any of the Approval Group'))
        if self.out_days <= max(approval_rec.mapped('days')):
            self.state = 'sale'
            return False
        else:
            return True
      
    def check_credit_limit(self):     
        # Check if the user is within his credit limit 
        if self.amount_payable_percentage < 0:
            self.state = 'sale'
            return False
        approval_rec = self.get_approval('credit.limit')
        
        # If current user isn't in any approval group, don't allow
        if not approval_rec:
            raise Warning(_('You do not exist in any of the Approval Group'))
        if self.amount_payable_percentage <= max(approval_rec.mapped('amount_percent')):
            self.state = 'sale'
            return False           
        else:
            return True
           
    def call_credit_day_func(self):
        credit_bool, day_bool = False, False
        if self.credit_limit_status and self.day_limit_status:
            self.state = 'sale'
            return
        if not self.credit_limit_status:
            credit_bool = self.check_credit_limit()
        if not self.day_limit_status:
            day_bool = self.check_day_limit()
        self.check_and_warn(credit_bool, day_bool)

    def check_and_warn(self, credit_bool, day_bool):
        if credit_bool and day_bool:
            raise Warning(_('Day & Credit Limit have been over, Approval Required'))
        elif day_bool:
            raise Warning(_('Day Limit has been over, Approval Required'))
        elif credit_bool:
            raise Warning(_('Credit Limit has been over, Approval Required'))

    def check_sale_price(self):
        if self.env.user.has_group('sale_restrictions.allow_sale_group'):
            return
        for rec in self.order_line:
            if rec.product_id.minimum_list_price > rec.price_unit:
                raise Warning(_('You do not allow to sale product %s below %s')%(rec.product_id.name, rec.product_id.minimum_list_price))

                             
    @api.multi
    def action_confirm(self):
        if self.company_id.id == 2:
            self.check_sale_price()
            self.call_credit_day_func()
        res = super(sale_order_inherit,self).action_confirm()
        return res

    @api.onchange('credit_limit_status','day_limit_status')        
    def approval_check(self):
        if self.partner_id:
            
            #check for credit days check
            app_day_rec = self.get_approval('day.limit')
            if self.out_days > max(app_day_rec.mapped('days')):
                self.day_limit_status = False
            elif self.out_days <= max(app_day_rec.mapped('days')):
                self.day_limit_status = True
          
            #check for credit limit check    
            app_credit_rec = self.get_approval('credit.limit')
            if self.amount_payable_percentage > max(app_credit_rec.mapped('amount_percent')):
                self.credit_limit_status = False
            elif self.amount_payable_percentage <= max(app_credit_rec.mapped('amount_percent')):
                self.credit_limit_status = True
