{
    "name": "Marketplace Product Feed",
    "version": "1.0.0",
    "category": "Sales",
    "summary": "SQL-based product feed for marketplaces",
    "description": "Provides a read-only SQL view exposing products for marketplace feeds",
    "author": "Your Company",
    "depends": [
        "product",
        "stock",
        "website_sale",  # nodig voor description_ecommerce
    ],
    "data": [
        "data/model.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
    "application": False,
}
