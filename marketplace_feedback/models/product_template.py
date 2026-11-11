from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    marketplace_issue_ids = fields.One2many("marketplace.issue", "product_tmpl_id", "Marktplaatsfeedback")
    marketplace_issue_count = fields.Integer(
        "Meldingen", compute="_compute_marketplace_issue_count", store=True,
        help="Aantal meldingen van de marktplaatsen bij de laatste import.",
    )
    marketplace_amazon_type = fields.Char(
        "Amazon-producttype", compute="_compute_marketplace_issue_count", store=True,
        help="Producttype waarmee Channable dit artikel naar Amazon stuurde (laatste import).",
    )

    @api.depends("marketplace_issue_ids", "marketplace_issue_ids.amazon_product_type")
    def _compute_marketplace_issue_count(self):
        for tmpl in self:
            issues = tmpl.marketplace_issue_ids
            tmpl.marketplace_issue_count = len(issues)
            tmpl.marketplace_amazon_type = next(
                (i.amazon_product_type for i in issues if i.amazon_product_type), False)

    def action_marketplace_issues(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("marketplace_feedback.action_marketplace_issue")
        action["domain"] = [("product_tmpl_id", "=", self.id)]
        action["context"] = {}
        return action
