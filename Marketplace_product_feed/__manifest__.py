{
    "name": "Marketplace Product Feed",
    "version": "1.0.14",
    "category": "Sales",
    "summary": "SQL-based product feed for marketplaces",
    "description": "Provides a read-only SQL view exposing products for marketplace feeds",
    "author": "Your Company",
    "depends": [
        "product",
        "stock",
        "website_sale",  # nodig voor description_ecommerce
        "stock_delivery",  # hs_code en country_of_origin
    ],
    "data": [
        "security/ir.model.access.csv",
    ],
    "installable": True,
    "application": False,
}
