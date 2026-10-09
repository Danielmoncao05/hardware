"""Gestão de equipamentos hospitalares: inventário, manutenção, ocorrências e relatórios.

Somente dados técnicos dos equipamentos: nada de registros de pacientes, dados clínicos ou diagnósticos.
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
from .pages.landing import landing_page
from .pages.login import forgot_page, login_page, reset_page
from .pages.maintenance import MaintenanceState, maintenance_page
from .pages.no_access import no_access_page
from .pages.occurrences import OccurrenceState, occurrences_page
from .pages.reports import ReportsState, reports_page
from .pages.tracking import TrackingState, tracking_page
from .pages.users import UsersState, users_page
from .components import BRAND
from .state import AuthState

# app.css: estilo das tabelas da área autenticada e animação de entrada do painel (classe hhm-enter)
app = rx.App(stylesheets=["/app.css"], head_components=[rx.script(src="/password.js")])

# Pública: página institucional da HospitalTech (estática, sem on_load nem chamadas à API)
app.add_page(
    landing_page,
    route="/",
    title="HospitalTech — Gestão de equipamentos hospitalares",
    description="HospitalTech: inventário, manutenções, ocorrências e relatórios de equipamentos hospitalares.",
)

# Públicas: autenticação e recuperação de conta (sem cadastro público)
app.add_page(login_page, route="/login", title=f"Entrar | {BRAND}")
app.add_page(forgot_page, route="/recuperar-senha", title=f"Recuperar senha | {BRAND}")
app.add_page(reset_page, route="/reset-password", title=f"Definir nova senha | {BRAND}")

# Autenticadas: cada on_load verifica de novo a sessão e a permissão da página
app.add_page(dashboard_page, route="/painel", title=f"Painel | {BRAND}", on_load=DashboardState.on_load)
app.add_page(tracking_page, route="/acompanhamento", title=f"Acompanhamento | {BRAND}", on_load=TrackingState.on_load)
app.add_page(equipment_detail_page, route="/equipamentos/[id]", title=f"Equipamento | {BRAND}", on_load=EquipmentDetailState.on_load)
app.add_page(equipment_form_page, route="/equipamentos/[id]/editar", title=f"Editar equipamento | {BRAND}", on_load=EquipmentFormState.on_load)
app.add_page(equipment_list_page, route="/equipamentos", title=f"Equipamentos | {BRAND}", on_load=EquipmentListState.on_load)
app.add_page(equipment_form_page, route="/novo-equipamento", title=f"Novo equipamento | {BRAND}", on_load=EquipmentFormState.on_load)
app.add_page(catalog_page, route="/catalogos", title=f"Catálogos e localizações | {BRAND}", on_load=CatalogState.on_load)
app.add_page(maintenance_page, route="/manutencoes", title=f"Manutenções | {BRAND}", on_load=MaintenanceState.on_load)
app.add_page(occurrences_page, route="/ocorrencias", title=f"Ocorrências | {BRAND}", on_load=OccurrenceState.on_load)
app.add_page(reports_page, route="/relatorios", title=f"Relatórios | {BRAND}", on_load=ReportsState.on_load)
app.add_page(users_page, route="/usuarios", title=f"Usuários e perfis | {BRAND}", on_load=UsersState.on_load)
# Troca de senha: primeiro passo obrigatório após uma senha temporária definida pelo administrador (só exige sessão)
app.add_page(change_password_page, route="/trocar-senha", title=f"Alterar senha | {BRAND}", on_load=ChangePasswordState.on_load)
# Logado, mas sem a permissão da página (só exige sessão, então os guards nunca entram em loop)
app.add_page(no_access_page, route="/sem-acesso", title=f"Acesso não permitido | {BRAND}", on_load=AuthState.require_login)
