{
    "name": "Marktplaatsfeedback",
    "version": "18.0.1.0.0",
    "category": "Sales",
    "summary": "Feedback van Amazon (via Channable) inlezen en per artikel opvolgen",
    "description": """
Leest de Feedback-CSV van een marktplaatskanaal in Channable in (eerst Amazon).

* Algemeen niveau: per Amazon-veld één keer beslissen of het een property op het
  artikel is, een ander gegeven in Odoo, of iets dat in Channable opgelost wordt.
  Ontbrekende properties maak je met één knop aan.
* Artikelniveau: de feedback staat op de productfiche, en voor velden die een
  property zijn krijgt het artikel een (lege) property-rij met het vinkje
  'Voor Amazon'.
* Invullijst: alle ontbrekende property-waarden in één lijst, gegroepeerd per veld.

Vereist de Studio-modellen x_product_property_def en x_product_property_val
(x_value niet verplicht) en het veld x_studio_product_property_value_1.
""",
    "author": "Chameleonstars",
    "license": "LGPL-3",
    "depends": ["sale"],
    "data": [
        "security/ir.model.access.csv",
        "views/marketplace_field_views.xml",
        "views/marketplace_issue_views.xml",
        "views/marketplace_feedback_import_views.xml",
        "views/product_template_views.xml",
        "views/menus.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
}
