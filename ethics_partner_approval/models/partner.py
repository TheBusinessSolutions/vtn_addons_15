from odoo import fields, models, api, _
from odoo.exceptions import AccessError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    active = fields.Boolean(default=False)

    def approve_draft_customer(self):
        for partner in self:
            partner.active = True

            
    def write(self,vals):
        if not self.env.user.has_group('ethics_partner_approval.group_can_approve_customer_2') and vals.get('active') in [True, False]:
            raise AccessError(_("Do not have access to Archive/Unarchive for this action."))
        return super(ResPartner,self).write(vals)
