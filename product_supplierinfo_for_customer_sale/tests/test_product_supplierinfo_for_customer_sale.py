# Copyright 2017 ForgeFlow S.L.
#   (http://www.forgeflow.com)
# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestProductSupplierinfoForCustomerSale(TransactionCase):
    def setUp(self):
        super().setUp()
        self.supplierinfo_model = self.env["product.supplierinfo"]
        self.customerinfo_model = self.env["product.customerinfo"]
        self.pricelist_item_model = self.env["product.pricelist.item"]
        self.pricelist_model = self.env["product.pricelist"]
        self.customer = self._create_customer("customer1")
        self.product = self.env.ref("product.product_product_4")
        self.product_variant_1 = self.env.ref("product.product_product_4b")
        self.product_variant_2 = self.env.ref("product.product_product_4c")
        self.customerinfo = self._create_partnerinfo(
            "customer", self.customer, self.product
        )
        self.pricelist = self._create_pricelist("Test Pricelist", self.product)
        self.pricelist_item = self._create_pricelist_item(
            "Test Pricelist Item", self.pricelist, self.product
        )
        self.company = self.env.ref("base.main_company")
        self._create_partnerinfo("customer", self.customer, self.product_variant_1)
        self._create_partnerinfo(
            "customer", self.customer, self.product_variant_2, empty_variant=True
        )
        self.product_template = self.env["product.template"].create(
            {"name": "product wo variants"}
        )
        self._create_partnerinfo(
            "customer",
            self.customer,
            self.product_template.product_variant_ids[:1],
            empty_variant=True,
        )
        self.pricelist_template = self._create_pricelist(
            "Test Pricelist Template", self.product_template.product_variant_ids[:1]
        )

    def _create_customer(self, name):
        return self.env["res.partner"].create(
            {"name": name, "email": "example@yourcompany.com", "phone": 123456}
        )

    def _create_partnerinfo(
        self, supplierinfo_type, partner, product, empty_variant=False
    ):
        vals = {
            "name": partner.id,
            "product_id": product.id,
            "product_name": "product4",
            "product_code": "00001",
            "price": 100.0,
            "min_qty": 15.0,
        }
        if empty_variant:
            vals.pop("product_id", None)
            vals["product_tmpl_id"] = product.product_tmpl_id.id
        return self.env["product." + supplierinfo_type + "info"].create(vals)

    def _create_pricelist(self, name, product):
        return self.pricelist_model.create(
            {"name": name, "currency_id": self.env.ref("base.USD").id}
        )

    def _create_pricelist_item(self, name, pricelist, product):
        return self.pricelist_item_model.create(
            {
                "name": name,
                "pricelist_id": pricelist.id,
                "applied_on": "0_product_variant",
                "product_id": product.id,
                "compute_price": "formula",
                "base": "partner",
            }
        )

    def test_product_supplierinfo_for_customer_sale(self):
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.customer
        order_form.pricelist_id = self.pricelist
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product
        order = order_form.save()
        line = order.order_line
        self.assertIn("00001", order.order_line.name)
        self.assertEqual(
            line.product_customer_code,
            self.customerinfo.product_code,
            "Error: Customer product code was not passed to sale order line",
        )
        self.assertEqual(
            line.product_uom_qty,
            self.customerinfo.min_qty,
            "Error: Min qty was not passed to the sale order line",
        )

    def test_product_supplierinfo_for_customer_sale_variant(self):
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.customer
        order_form.pricelist_id = self.pricelist
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product_variant_1
        order = order_form.save()
        line = order.order_line
        self.assertEqual(
            line.product_customer_code,
            self.customerinfo.product_code,
            "Error: Customer product code was not passed to sale order line",
        )

    def test_product_supplierinfo_for_customer_sale_template(self):
        customerinfo = self._create_partnerinfo(
            "customer", self.customer, self.product_variant_2
        )
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.customer
        order_form.pricelist_id = self.pricelist
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product_variant_2
        order = order_form.save()
        line = order.order_line
        self.assertEqual(
            line.product_customer_code,
            customerinfo.product_code,
            "Error: Customer product code was not passed to sale order line",
        )
        # Test with product without variants
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.customer
        order_form.pricelist_id = self.pricelist_template
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product_template.product_variant_ids[0]
        order2 = order_form.save()
        line2 = order2.order_line
        self.assertEqual(
            line2.product_customer_code,
            customerinfo.product_code,
            "Error: Customer product code was not passed to sale order line",
        )

    def test_product_supplierinfo_for_customer_sale_variant_wo_template(self):
        customerinfo = self._create_partnerinfo(
            "customer", self.customer, self.product_variant_2, empty_variant=True
        )
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.customer
        order_form.pricelist_id = self.pricelist
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product_variant_2
        order = order_form.save()
        line = order.order_line
        self.assertEqual(
            line.product_customer_code,
            customerinfo.product_code,
            "Error: Customer product code was not passed to sale order line",
        )
