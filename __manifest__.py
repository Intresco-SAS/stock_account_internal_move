# -*- coding: utf-8 -*-
# Copyright (C) 2023 by Intresco SAS
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl-3.0).
{
    "name": """Stock Account Internal Move""",
    "summary": """Allows tracking moves between internal locations via accounts
    Note: it only support standart cost
    This Module was migrated initially from OCA author from version 12 CE, due to was not migrate
    we decide to adapt to this version""",
    "category": "Warehouse",
    "version": "15.0.0.1",
    "author": "Intresco SAS",
    "website": "https://github.com/Intresco-SAS/stock_account_internal_move",
    "license": "AGPL-3",
    "depends": ["stock_account"],
    "data": ["views/stock_location.xml"],
    "development_status": "Alpha",
    "maintainers": [
        "NelsonV93",
    ],
}
