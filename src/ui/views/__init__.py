from __future__ import annotations

from src.ui.views.backup_view import BackupView
from src.ui.views.cash_turn_view import CashTurnView
from src.ui.views.catalog_view import CatalogView
from src.ui.views.expense_view import ExpenseView
from src.ui.views.inventory_view import InventoryView
from src.ui.views.login_view import LoginView
from src.ui.views.loss_view import LossView
from src.ui.views.pos_view import POSView
from src.ui.views.reports_view import ReportsView
from src.ui.views.users_view import UsersView

__all__ = [
    "LoginView",
    "POSView",
    "CashTurnView",
    "CatalogView",
    "InventoryView",
    "ExpenseView",
    "LossView",
    "ReportsView",
    "UsersView",
    "BackupView",
]
