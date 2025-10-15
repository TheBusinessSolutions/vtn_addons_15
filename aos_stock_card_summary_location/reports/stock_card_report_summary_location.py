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
import pandas
from collections import defaultdict
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY
from odoo.tools.safe_eval import safe_eval


class StockCardSummaryViewLocation(models.TransientModel):
    _name = "stock.card.summary.view.location"
    _description = "Stock Card Summary View Location"
    _order = "date"

    product_ids = fields.Many2one(comodel_name="product.product")
    product_name = fields.Char()
    location_name = fields.Char()
    product_uom_qty = fields.Float()
    location_ids = fields.Many2many(comodel_name="stock.location")
    # location_dest_id = fields.Many2one(comodel_name="stock.location")
    product_in_qty = fields.Float()
    product_out_qty = fields.Float()
    qty_sale_delivered = fields.Float()
    qty_sale_returned = fields.Float()
    qty_purchase_received = fields.Float()
    qty_purchase_returned = fields.Float()
    manufactured_in_qty = fields.Float()
    manufactured_out_qty =  fields.Float()
    adjustment_in_qty = fields.Float()
    adjustment_out_qty = fields.Float()
    beginning_qty = fields.Float()
    scrap_out_qty = fields.Float()
    totals = fields.Float()



class StockCardReportSummaryLocation(models.TransientModel):
    _name = "report.stock.card.summary.location"
    _description = "Stock Card Report Summary Location"

    # Filters fields, used for data computation
    date_from = fields.Date()
    date_to = fields.Date()
    generate_date = fields.Date()
    generate_by = fields.Many2one(comodel_name="res.users")
    product_ids = fields.Many2many(comodel_name="product.product")
    location_ids = fields.Many2many(comodel_name="stock.location")
    company_id = fields.Many2one(comodel_name="res.company")
    warehouse_ids = fields.Many2many(comodel_name="stock.warehouse")

    # Data fields, used to browse report data
    results = fields.Many2many(
        comodel_name="stock.card.summary.view.location",
        compute="_compute_results",
        help="Use compute fields, so there is nothing store in database",
    )

    def _compute_results(self):
        self.ensure_one()
        domain = [
            '|',
            ('location_id','in', self.location_ids.ids),
            ('location_dest_id','in', self.location_ids.ids),
            ('date','>=',self.date_from), ('date','<=',self.date_to), 
            ('state', '=', 'done'),
        ]
        if self.product_ids:
            domain.append(('product_id', 'in', self.product_ids.ids)) 

        stock_moves = self.env['stock.move'].search(domain)
        # if not stock_moves:
        #     raise UserError('%d records stock for %s %s' % (len(stock_moves), self.date_from.strftime('%B'), self.date_to.year)) 

        #################### for beginning ####################
        domain_before_period = [
           '|', '&',
            ('location_id', 'in', self.location_ids.ids),
            ('date', '<', self.date_from),
            '&',
            ('location_dest_id', 'in', self.location_ids.ids),
            ('date', '<', self.date_from),
            ('state', '=', 'done'),
        ]

        if self.product_ids:
            domain_before_period.append(('product_id','in',self.product_ids.ids))
        stock_move_before = self.env['stock.move'].search(domain_before_period)
        
        report_lines = []
        grouped_data = {}
        valid_keys = set()
        for move in stock_moves:
            location_key = (move.product_id.id, move.location_id.id if move.location_id.id in self.location_ids.ids else move.location_dest_id.id) 
            valid_keys.add(location_key)
            if location_key in valid_keys:
                if location_key not in grouped_data:
                    grouped_data[location_key] = {
                        'product_name': move.product_id.name,
                        'location_name': move.location_id.display_name,
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
                        'qty_total': 0, 
                        }
                
            
            # sale
            if move.location_dest_id.usage == 'customer': 
                grouped_data[location_key]['qty_sale_delivered'] += move.product_uom_qty
            elif move.location_id.usage == 'customer':
                grouped_data[location_key]['qty_sale_returned'] += move.product_uom_qty
            
             # purchase
            elif move.location_id.usage == 'supplier': 
                grouped_data[location_key]['qty_purchase_received'] += move.product_uom_qty
            elif move.location_dest_id.usage == 'supplier' : 
                grouped_data[location_key]['qty_purchase_returned'] += move.product_uom_qty

             # internal transfer
            elif move.location_id.usage == 'internal' and move.location_dest_id.id in self.location_ids.ids : 
                grouped_data[location_key]['product_in_qty'] += move.product_uom_qty
            elif move.location_dest_id.usage == 'internal' and move.location_id.id in self.location_ids.ids :
                grouped_data[location_key]['product_out_qty'] += move.product_uom_qty 
            
            # manufactured
            elif move.location_id.usage == 'production' and move.location_dest_id.id in self.location_ids.ids :
                grouped_data[location_key]['manufactured_in_qty'] += move.product_uom_qty
            elif move.location_dest_id.usage == 'production' :
                grouped_data[location_key]['manufactured_out_qty'] += move.product_uom_qty
            
            # adjustment
            elif move.location_id.usage == 'inventory' and move.location_dest_id.id in self.location_ids.ids :
                grouped_data[location_key]['adjustment_in_qty'] += move.product_uom_qty
            elif move.location_dest_id.usage == 'inventory' and not move.location_dest_id.scrap_location and move.location_id.id in self.location_ids.ids :
                grouped_data[location_key]['adjustment_out_qty'] += move.product_uom_qty
            

            # Scrap
            if move.location_dest_id.scrap_location and move.location_dest_id.usage == 'inventory': 
                grouped_data[location_key]['scrap_out_qty'] += move.product_uom_qty
        
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
                            'qty_total': 0, 
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
                            'qty_total': 0, 
                        }
                    
                    grouped_data[key]['product_out_beginning'] += y.product_qty

            for key in grouped_data:
                grouped_data[key]['beginning_qty'] = grouped_data[key]['product_in_beginning'] - grouped_data[key]['product_out_beginning']  

        ########################## End Values For Beginning #############################

            
        for location_key, data in grouped_data.items(): 

            totals = (data['beginning_qty'] - data['qty_sale_delivered'] + data['qty_sale_returned'] +  
                       data['qty_purchase_received'] - data['qty_purchase_returned'] +
                       data['product_in_qty'] - data['product_out_qty'] +
                       data['manufactured_in_qty'] - data['manufactured_out_qty'] +
                      data['adjustment_in_qty'] - data['adjustment_out_qty'] -
                      data['scrap_out_qty']) 

            report_lines.append({
            'product_ids': self.product_ids.ids,
            'product_name': data['product_name'],
            'location_name':data['location_name'],
            'beginning_qty':data['beginning_qty'],
            'product_in_qty': data['product_in_qty'],
            'product_out_qty': data['product_out_qty'],
            'qty_sale_delivered': data['qty_sale_delivered'],
            'qty_sale_returned':  data['qty_sale_returned'],
            'qty_purchase_received': data['qty_purchase_received'],
            'qty_purchase_returned': data['qty_purchase_returned'],
            'manufactured_in_qty': data['manufactured_in_qty'],
            'manufactured_out_qty': data['manufactured_out_qty'],
            'adjustment_in_qty': data['adjustment_in_qty'],
            'adjustment_out_qty': data['adjustment_out_qty'],
            'scrap_out_qty': data['scrap_out_qty'],
            'totals': totals, 
        
            }) 

        ReportLine = self.env["stock.card.summary.view.location"]
        self.results = [ReportLine.new(line).id for line in report_lines]

    
    def print_report(self, action_type="qweb"):  
        self.ensure_one()
        action = (action_type == "xlsx"
                   and self.env.ref("aos_stock_card_summary_location.action_stock_card_report_xlsx_location")
                   or self.env.ref("aos_stock_card_summary_location.action_stock_card_report_pdf_location"))
        return action.report_action(self, config=False) 
    
    def _get_html(self):
        result = {}
        rcontext = {}
        report = self.browse(self._context.get("active_id"))
        if report:
            rcontext["o"] = report
            result["html"] = self.env.ref(
                "aos_stock_card_summary_location.report_stock_card_report_html"
            )._render(rcontext)
        return result

    @api.model
    def get_html(self, given_context=None):
        return self.with_context(**(given_context or {}))._get_html()
