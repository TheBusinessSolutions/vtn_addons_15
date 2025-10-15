from odoo import models, fields

class CommonXlsxOut(models.TransientModel):
    _name = "common.xlsx.out"
    _description = "Common Xlsx Out"
    
    file = fields.Binary(readonly=True)
    filename = fields.Char(string="Filename", size=64, readonly=True)
