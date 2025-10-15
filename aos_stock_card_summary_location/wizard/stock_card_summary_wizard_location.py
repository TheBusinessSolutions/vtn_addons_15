import xlsxwriter
from io import StringIO
import io
import base64
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from datetime import date
from datetime import timedelta, timezone
import calendar
import pytz
from collections import defaultdict
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY
from odoo.tools.safe_eval import safe_eval


class StockCardSummaryWizardLocation(models.TransientModel):
    _name = "stock.card.summary.wizard.location"
    _description = "Stock Card Report Wizard Location"


    date_from = fields.Date(string="Start Date", required=True)
    date_to = fields.Date(string="End Date", required=True)
    generate_date = fields.Date(string="Generated Date", default=fields.Date.today(), readonly=True) 
    company_id = fields.Many2one('res.company', required=True, default = lambda self:self.env.user.company_id)
    # warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse", required=True)
    create_uid = fields.Many2one('res.users', string="Created by", default=lambda self: self.env.user, readonly=True)
    # location_id = fields.Many2one(
    #     comodel_name="stock.location", string="Location", required=True
    # )
    warehouse_ids = fields.Many2many(comodel_name="stock.warehouse", string="Warehouse", required=True)
    location_ids = fields.Many2many(comodel_name="stock.location", string="Location", required=True)
    filter_by = fields.Selection([('product','Product'),('category','Product Category')],string='Filter By', default='product')
    category_id = fields.Many2one('product.category',string='Category')
    product_ids = fields.Many2many(
        comodel_name="product.product", string="Products", required=False
    )
    valuation = fields.Boolean(string="Valuation")


    @api.onchange("warehouse_ids")
    def _onchange_warehouse_ids(self):
        if self.warehouse_ids:
           location_ids = self.warehouse_ids.mapped('lot_stock_id')
           self.location_ids = [(6, 0, location_ids.ids)]

    def button_export_html(self):
        self.ensure_one()
        action = self.env.ref("aos_stock_card_summary_location.action_report_stock_card_report_html_location")
        vals = action.sudo().read()[0]
        context = vals.get("context", {})
        if context:
            context = safe_eval(context)
        model = self.env["report.stock.card.summary.location"]
        report = model.create(self._prepare_stock_card_report())
        context["active_id"] = report.id
        context["active_ids"] = report.ids
        vals["context"] = context
        return vals

    def button_export_pdf(self):
        self.ensure_one()
        report_type = "qweb-pdf" 
        return self._export(report_type)

    # def button_export_xlsx(self):
    #     self.ensure_one()
    #     report_type = "xlsx"
    #     return self._export(report_type) 

    def _prepare_stock_card_report(self):
        self.ensure_one()
        return {
            "date_from": self.date_from,
            "date_to": self.date_to or fields.Date.context_today(self),
            "generate_date": self.generate_date,
            "generate_by":self.create_uid.id,
            "company_id": self.company_id.id,
            "product_ids": [(6, 0, self.product_ids.ids)],
            "location_ids": [(6, 0, self.location_ids.ids)],  
            "warehouse_ids": [(6, 0, self.warehouse_ids.ids)],
        }

    def _export(self, report_type):
        model = self.env["report.stock.card.summary.location"]
        report = model.create(self._prepare_stock_card_report())
        return report.print_report(report_type)

    # PRINT XLSX
    def print_report_xlsx(self):
        file_data = io.BytesIO()
        wb = xlsxwriter.Workbook(file_data)
        _p = self.env.user
        ws = wb.add_worksheet('Stock Card Report Summary Location')
        ws.fit_width_to_pages = 1
        row_count = 4
        header_style = wb.add_format({'bold': True, 'color': '#FF000000', 'size': 12, 'top':1, 'right':1, 'left':1,'bottom':1, 'border_color':'##000000'})
        body_style = wb.add_format({'align':'center','bold': False, 'color': 'FF000000','bottom':1, 'right':1, 'left':1,'border_color':'##000000', 'size': 10}) 
        title_style = wb.add_format({'text_wrap': True,'align':'center','size': 14})
        bot_style = wb.add_format({'bold': True, 'align':'vleft','size': 12})
        bold_title = wb.add_format({'align':'left','bold': True, 'color': 'FF000000','bottom':1, 'right':1, 'left':1,'border_color':'##000000', 'size': 10})
        product_style = wb.add_format({'align':'left','bold': False, 'color': 'FF000000','bottom':1, 'right':1, 'left':1,'border_color':'##000000', 'size': 10})
        uom_style = wb.add_format({'align':'right','bold': False, 'color': 'FF000000','bottom':1, 'right':1, 'left':1,'border_color':'##000000', 'size': 10})
        float_style = wb.add_format({'align':'right','bold': False, 'color': 'FF000000','bottom':1, 'right':1, 'left':1,'border_color':'##000000', 'size': 10, 'num_format': '#,##0.00' })
        header_style.set_align('center') 
        header_style.set_align('vcenter')
        header_style.set_bg_color('#CAC9D0')
        body_style.set_align('vcenter')
        ws.set_column('A:A', 35)
        ws.set_column('B:B', 50)
        ws.set_column('C:C', 23)
        ws.set_column('E:E', 20)
        ws.set_column('J:J', 20)
        ws.set_column('M:M', 30)
        ws.set_column('D:D', 23)
        ws.set_column('F:F', 16)
        ws.set_column('G:I', 17)
        ws.set_column('K:K', 20)
        ws.set_column('L:L', 20)
        ws.set_column('N:N', 20)
        ws.set_column('O:O', 20)
        ws.set_column('P:P', 20) 
        ws.set_default_row(20) 

        # <header_style>
        domain = [
            '|',
            ('location_id','in', self.location_ids.ids),  
            ('location_dest_id','in', self.location_ids.ids),
            ('date','>=',self.date_from), ('date','<=',self.date_to),
            ('state', '=', 'done'),
        ]

        if self.product_ids:
            domain.append(('product_id', 'in', self.product_ids.ids))

        stock_move = self.env['stock.move'].search(domain)
        # if not stock_move:
        #   raise UserError('%d records stock for %s %s' % (len(stock_move),self.date_from.strftime('%B'),self.date_to.year))


        #################### for beginning ####################
        domain_before_period = [
            '|','&',
            ('location_id', 'in', self.location_ids.ids),
            ('date', '<', self.date_from),
            '&',
            ('location_dest_id','in', self.location_ids.ids),
            ('date', '<', self.date_from),
            ('state', '=', 'done'), 
        ] 

        if self.product_ids:
            domain_before_period.append(('product_id','in',self.product_ids.ids))
        stock_move_before = self.env['stock.move'].search(domain_before_period)
    
        company = self.company_id
        ws.merge_range('A1:F1',"STOCK CARD SUMMARY REPORT LOCATION", title_style)
        
        # table first
        ws.write('A2', "Company", header_style)
        ws.write('B2', "Generated Date", header_style)
        ws.write('C2', "Date", header_style)
        ws.write('D2', "Generated By", header_style)
        # values
        ws.write('A3', company.name, body_style)
        ws.write('B3', self.generate_date.strftime('%Y-%m-%d'), body_style)
        ws.write('C3', f"{self.date_from or ''} To {self.date_to or ''}", body_style)
        ws.write('D3', self.create_uid.name, body_style)


        #table second
        ws.merge_range('A5:A6', "Product", header_style)
        ws.merge_range('B5:B6', "Location", header_style)
        ws.merge_range('C5:C6', "Beginning", header_style)
        ws.merge_range('D5:E5', "Sale", header_style)
        ws.write('D6', "Delivered (-)", header_style)
        ws.write('E6', "Returned (+)", header_style)
        ws.merge_range('F5:G5', "Purchase", header_style)
        ws.write('F6', "Received (+)", header_style)
        ws.write('G6', "Returned (-)", header_style)
        ws.merge_range('H5:I5', "W/H Transfer", header_style)
        ws.write('H6', "In (+)", header_style)
        ws.write('I6', "Out (-)", header_style)
        ws.merge_range('J5:K5', "Manufactured", header_style)
        ws.write('J6', "In (+)", header_style)
        ws.write('K6', "Out (-)", header_style)
        ws.merge_range('L5:M5', "Adjustment", header_style)
        ws.write('L6', "In (+)", header_style)
        ws.write('M6', "Out (-)", header_style)
        ws.merge_range('N5:N6', "Scrap (-)", header_style) 
        ws.merge_range('O5:O6', "Total", header_style)  


        # values
        grouped_data = {}
        valid_keys = set()

        for x in stock_move :
            location_key = (x.product_id.id, x.location_id.id if x.location_id.id in self.location_ids.ids else x.location_dest_id.id) 
            valid_keys.add(location_key)
            if location_key in valid_keys:
                if location_key not in grouped_data: 
                    grouped_data[location_key] = {
                    'product_name': x.product_id.display_name,
                    'location_name':x.location_id.display_name,  
                    'qty_sale_delivered': 0,
                    'qty_sale_returned': 0,
                    'qty_purchase_received': 0,
                    'qty_purchase_returned': 0,
                    'beginning_qty': 0,
                    'product_in_beginning': 0,
                    'product_out_beginning': 0, 
                    'product_in_qty': 0,
                    'product_out_qty': 0,
                    'manufactured_in_qty':0,
                    'manufactured_out_qty':0,
                    'adjustment_in_qty': 0,
                    'adjustment_out_qty': 0,
                    'scrap_out_qty': 0,
                    }
            
                # sale
                if x.location_dest_id.usage == 'customer':
                    grouped_data[location_key]['qty_sale_delivered'] += x.product_uom_qty
                elif x.location_id.usage == 'customer':
                    grouped_data[location_key]['qty_sale_returned'] += x.product_uom_qty
                
                # purchase
                elif x.location_id.usage == 'supplier': 
                    grouped_data[location_key]['qty_purchase_received'] += x.product_uom_qty
                elif x.location_dest_id.usage == 'supplier' : 
                    grouped_data[location_key]['qty_purchase_returned'] += x.product_uom_qty

                # internal transfer
                elif x.location_id.usage == 'internal' and x.location_dest_id.id in self.location_ids.ids : 
                    grouped_data[location_key]['product_in_qty'] += x.product_uom_qty
                elif x.location_dest_id.usage == 'internal' and x.location_id.id in self.location_ids.ids :
                    grouped_data[location_key]['product_out_qty'] += x.product_uom_qty 
                
                # manufactured
                elif x.location_id.usage == 'production' and x.location_dest_id.id in self.location_ids.ids :
                    grouped_data[location_key]['manufactured_in_qty'] += x.product_uom_qty
                elif x.location_dest_id.usage == 'production' :
                    grouped_data[location_key]['manufactured_out_qty'] += x.product_uom_qty
                
                # adjustment
                elif x.location_id.usage == 'inventory' and x.location_dest_id.id in self.location_ids.ids :
                    grouped_data[location_key]['adjustment_in_qty'] += x.product_uom_qty
                elif x.location_dest_id.usage == 'inventory' and not x.location_dest_id.scrap_location and x.location_id.id in self.location_ids.ids :
                    grouped_data[location_key]['adjustment_out_qty'] += x.product_uom_qty 
                

                # Scrap
                if x.location_dest_id.scrap_location and x.location_dest_id.usage == 'inventory': 
                    grouped_data[location_key]['scrap_out_qty'] += x.product_uom_qty
            


        ################ Start Values For beginning #######################
        for y in stock_move_before:
            key = (y.product_id.id, y.location_id.id)
            valid_keys.add(key)
            if y.location_dest_id.id in self.location_ids.ids:
                key = (y.product_id.id, y.location_dest_id.id if y.location_dest_id.id in self.location_ids.ids else y.location_id.id)
                if key in valid_keys:
                    if key not in grouped_data:
                        grouped_data[key] = {
                            'product_name': y.product_id.name,
                            'location_name':y.location_id.display_name if y.location_id.id in self.location_ids.ids else " ",
                            'qty_sale_delivered': 0,
                            'qty_sale_returned': 0,
                            'qty_purchase_received': 0,
                            'qty_purchase_returned': 0,
                            'beginning_qty': 0,
                            'product_in_beginning': 0,
                            'product_out_beginning': 0, 
                            'product_in_qty': 0,
                            'product_out_qty': 0,
                            'manufactured_in_qty':0,
                            'manufactured_out_qty':0,
                            'adjustment_in_qty': 0,
                            'adjustment_out_qty': 0,
                            'scrap_out_qty': 0,
     
                        }

                    grouped_data[key]['product_in_beginning'] += y.product_qty

            if y.location_id.id in self.location_ids.ids:
                key = (y.product_id.id, y.location_id.id if y.location_id.id in self.location_ids.ids else y.location_id.id)
                if key in valid_keys:
                    if key not in grouped_data:
                        grouped_data[key] = {
                            'product_name': y.product_id.name,
                            'location_name':y.location_id.display_name if y.location_id.id in self.location_ids.ids else " ",
                            'qty_sale_delivered': 0,
                            'qty_sale_returned': 0,
                            'qty_purchase_received': 0,
                            'qty_purchase_returned': 0,
                            'beginning_qty': 0,
                            'product_in_beginning': 0,
                            'product_out_beginning': 0, 
                            'product_in_qty': 0,
                            'product_out_qty': 0,
                            'manufactured_in_qty':0,
                            'manufactured_out_qty':0,
                            'adjustment_in_qty': 0,
                            'adjustment_out_qty': 0,
                            'scrap_out_qty': 0,
     
                        }
                    
                    grouped_data[key]['product_out_beginning'] += y.product_qty

            for key in grouped_data:
                grouped_data[key]['beginning_qty'] = grouped_data[key]['product_in_beginning'] - grouped_data[key]['product_out_beginning']
    ########################## End Values For Beginning #############################

            
        # tables
        row = 6
        for location_key, data in grouped_data.items():

            totals = (data['beginning_qty'] - data['qty_sale_delivered'] + data['qty_sale_returned'] +  
                       data['qty_purchase_received'] - data['qty_purchase_returned'] +
                       data['product_in_qty'] - data['product_out_qty'] +
                       data['manufactured_in_qty'] - data['manufactured_out_qty'] +
                      data['adjustment_in_qty'] - data['adjustment_out_qty'] -
                      data['scrap_out_qty']) 
            
            ws.write(row, 0, data['product_name'], product_style) 
            ws.write(row, 1, data['location_name'], product_style)
            ws.write(row, 2, data['beginning_qty'], float_style) 
            ws.write(row, 3, data['qty_sale_delivered'], float_style)
            ws.write(row, 4, data['qty_sale_returned'], float_style)
            ws.write(row, 5, data['qty_purchase_received'], float_style)
            ws.write(row, 6, data['qty_purchase_returned'], float_style)
            ws.write(row, 7, data['product_in_qty'], float_style)
            ws.write(row, 8, data['product_out_qty'], float_style)
            ws.write(row, 9, data['manufactured_in_qty'], float_style)
            ws.write(row, 10, data['manufactured_out_qty'], float_style) 
            ws.write(row, 11, data['adjustment_in_qty'], float_style)
            ws.write(row, 12, data['adjustment_out_qty'], float_style) 
            ws.write(row, 13, data['scrap_out_qty'], float_style)
            ws.write(row, 14, totals, float_style) 
            row +=1

        wb.close()
        file_data.seek(0) 
        generated_file = file_data.read()
        file_data.close()
        filename = "STOCK CARD SUMMARY REPORT LOCATION.xlsx"
        common_xlsx_out = self.env['common.xlsx.out'].sudo().create({
            'file': base64.b64encode(generated_file),
            'filename': filename
        }) 
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s/%s/file/%s?download=True' % (
            common_xlsx_out._name, common_xlsx_out.id, filename),
            'target': 'new', 
        }
    
    


        
        









