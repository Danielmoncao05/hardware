"""Hospital equipment management: inventory, maintenance, occurrences, and reporting.

Technical equipment data only: no patient records, clinical data, or diagnosis.
"""

import reflex as rx

from .pages.catalog import CatalogState, catalog_page
from .pages.change_password import ChangePasswordState, change_password_page
from .pages.dashboard import DashboardState, dashboard_page
from .pages.equipment import (
    EquipmentDetailState,
    EquipmentFormState,
    EquipmentListState,
    equipment_detail_page,
    equipment_form_page,
    equipment_list_page,
)
from .pages.login import forgot_page, login_page, reset_page
from .pages.maintenance import MaintenanceState, maintenance_page
from .pages.no_access import no_access_page
from .pages.occurrences import OccurrenceState, occurrences_page
from .pages.reports import ReportsState, reports_page
from .pages.users import UsersState, users_page
from .state import AuthState

app = rx.App()

# Public: authentication and account recovery (no sign-up)
app.add_page(login_page, route="/login", title="Entrar")
app.add_page(forgot_page, route="/recuperar-senha", title="Recuperar senha")
app.add_page(reset_page, route="/reset-password", title="Definir nova senha")

# Authenticated: each on_load re-checks the session and the page's permission
app.add_page(dashboard_page, route="/", title="Painel", on_load=DashboardState.on_load)
app.add_page(equipment_detail_page, route="/equipamentos/[id]", title="Equipamento", on_load=EquipmentDetailState.on_load)
app.add_page(equipment_form_page, route="/equipamentos/[id]/editar", title="Editar equipamento", on_load=EquipmentFormState.on_load)
app.add_page(equipment_list_page, route="/equipamentos", title="Equipamentos", on_load=EquipmentListState.on_load)
app.add_page(equipment_form_page, route="/novo-equipamento", title="Novo equipamento", on_load=EquipmentFormState.on_load)
app.add_page(catalog_page, route="/catalogos", title="Catálogos e localizações", on_load=CatalogState.on_load)
app.add_page(maintenance_page, route="/manutencoes", title="Manutenções", on_load=MaintenanceState.on_load)
app.add_page(occurrences_page, route="/ocorrencias", title="Ocorrências", on_load=OccurrenceState.on_load)
app.add_page(reports_page, route="/relatorios", title="Relatórios", on_load=ReportsState.on_load)
app.add_page(users_page, route="/usuarios", title="Usuários e perfis", on_load=UsersState.on_load)
# Password change: required first step after an administrator-issued temporary password (session only)
app.add_page(change_password_page, route="/trocar-senha", title="Alterar senha", on_load=ChangePasswordState.on_load)
# Signed in but without the page's permission (requires only a session, so guards never loop)
app.add_page(no_access_page, route="/sem-acesso", title="Acesso não permitido", on_load=AuthState.require_login)
