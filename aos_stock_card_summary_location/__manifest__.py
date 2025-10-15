# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Stock Card Report Summary Location",
    "summary": "Add stock card report summary location on Inventory Reporting.",
    "version": "15.0.1.0.0",
    "category": "Warehouse",
    "website": "",
    "author": "Alphasoft",
    "license": "AGPL-3",
    "depends": ["base","stock", "report_xlsx_helper"], 
    "data": [
        "security/ir.model.access.csv",
        "data/paper_format.xml",
        "data/report_data.xml",
        "reports/stock_card_report_summary_location.xml",
        "wizard/stock_card_summary_wizard_location_view.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "aos_stock_card_summary_location/static/src/css/**/*",
            "aos_stock_card_summary_location/static/src/js/**/*",
        ]
    },
    'installable': True,
    'auto_install': False,
    'application': True,
}
