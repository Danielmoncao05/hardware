"""Página inicial institucional da HospitalTech (pública, estática, sem chamadas à API).

A paleta azul/branco/cinza vale só aqui: o tema aninhado troca o accent para azul (indigo) sem mexer no tema global
(teal) das telas internas e do login. Sem `appearance`, para continuar seguindo o claro/escuro escolhido.
"""

import reflex as rx

from ..components import current_year, theme_toggle

COMPANY = "HospitalTech"
LOGIN_HREF = "/login"
CONTENT_WIDTH = "72rem"

# (ícone, título, descrição): os mesmos ícones do menu interno, para manter a coerência com o sistema
FEATURES = [
    ("monitor", "Inventário de equipamentos", "Cadastro completo de cada equipamento, com patrimônio, fabricante, modelo, setor e componentes."),
    ("wrench", "Manutenções preventivas e corretivas", "Planejamento das preventivas e registro das corretivas, com histórico por equipamento."),
    ("circle_alert", "Ocorrências", "Registro de falhas e problemas por gravidade, do aviso inicial até a resolução."),
    ("activity", "Acompanhamento", "Visão em tempo real dos equipamentos que precisam de atenção em cada setor."),
    ("file_chart_column", "Relatórios", "Indicadores e relatórios para apoiar decisões de compra, manutenção e descarte."),
]


def _access_button(size: str = "3", compact: bool = False, **props) -> rx.Component:
    """Link para o login com aparência de botão (o foco fica só no link). `compact` mostra "Entrar" em telas
    estreitas, para o botão do cabeçalho não quebrar linha no celular."""
    label = (
        [rx.text.span("Entrar", display=["inline", "none"]), rx.text.span("Acessar o sistema", display=["none", "inline"])]
        if compact
        else ["Acessar o sistema"]
    )
    return rx.link(
        rx.button(*label, rx.icon("log_in", size=18, aria_hidden="true"), size=size, tab_index=-1, white_space="nowrap"),
        href=LOGIN_HREF,
        underline="none",
        flex_shrink="0",
        aria_label="Acessar o sistema",
        **props,
    )


def _section(*children, background: str | None = None, **props) -> rx.Component:
    return rx.el.section(
        rx.box(*children, max_width=CONTENT_WIDTH, margin_x="auto", padding_x="1rem", padding_y=["3rem", "3rem", "4rem"]),
        background=background or "transparent",
        width="100%",
        **props,
    )


def _image(src: str, alt: str, lazy: bool = True, **props) -> rx.Component:
    return rx.image(
        src=src,
        alt=alt,
        loading="lazy" if lazy else "eager",
        width="100%",
        object_fit="cover",
        border_radius="var(--radius-4)",
        box_shadow="var(--shadow-4)",
        **props,
    )


def _brand() -> rx.Component:
    return rx.hstack(
        rx.center(
            rx.icon("heart_pulse", size=22, color="white", aria_hidden="true"),
            background=rx.color("accent", 9),
            border_radius="var(--radius-3)",
            width="2.25rem",
            height="2.25rem",
        ),
        rx.text(COMPANY, size="5", weight="bold", color=rx.color("accent", 11)),
        spacing="2",
        align="center",
    )


def _header() -> rx.Component:
    return rx.el.header(
        rx.hstack(
            _brand(),
            rx.spacer(),
            theme_toggle(),
            _access_button(size="2", compact=True),
            max_width=CONTENT_WIDTH,
            margin_x="auto",
            padding_x="1rem",
            padding_y="0.75rem",
            spacing="3",
            align="center",
        ),
        position="sticky",
        top="0",
        z_index="10",
        background=rx.color("gray", 1),
        border_bottom=f"1px solid {rx.color('gray', 5)}",
        width="100%",
    )


def _hero() -> rx.Component:
    return _section(
        rx.grid(
            rx.vstack(
                rx.badge("Engenharia clínica e gestão hospitalar", size="2", variant="soft"),
                rx.heading(
                    "Equipamentos hospitalares sempre prontos para cuidar de quem precisa",
                    as_="h1",
                    size=rx.breakpoints(initial="7", md="8"),
                    color=rx.color("accent", 12),
                ),
                rx.text(
                    f"A {COMPANY} ajuda hospitais e clínicas a controlar o inventário, as manutenções e as ocorrências "
                    "dos seus equipamentos em um só lugar, com segurança e rastreabilidade.",
                    size="4",
                    color_scheme="gray",
                ),
                rx.hstack(
                    _access_button(),
                    rx.link("Conheça os recursos", href="#recursos", size="3", weight="medium"),
                    spacing="5",
                    align="center",
                    wrap="wrap",
                ),
                spacing="5",
                align="start",
                justify="center",
            ),
            _image(
                "/landing/hero.webp",
                "Sala cirúrgica vazia com foco cirúrgico, mesa de operação e equipamentos médicos",
                lazy=False,
                height=["16rem", "20rem", "24rem"],
            ),
            columns=rx.breakpoints(initial="1", md="2"),
            gap="2.5rem",
            align="center",
        ),
        background=f"linear-gradient(180deg, {rx.color('accent', 2)} 0%, {rx.color('gray', 1)} 100%)",
    )


def _feature_card(icon: str, title: str, text: str) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.center(
                rx.icon(icon, size=22, aria_hidden="true"),
                background=rx.color("accent", 3),
                color=rx.color("accent", 11),
                border_radius="var(--radius-3)",
                width="2.75rem",
                height="2.75rem",
            ),
            rx.heading(title, as_="h3", size="4"),
            rx.text(text, size="2", color_scheme="gray"),
            spacing="3",
            align="start",
        ),
        size="3",
    )


def _features() -> rx.Component:
    return _section(
        rx.vstack(
            rx.heading("Tudo o que a engenharia clínica precisa", as_="h2", size="7", color=rx.color("accent", 12)),
            rx.text(
                "Do cadastro ao descarte, cada etapa da vida do equipamento fica registrada e fácil de consultar.",
                size="3",
                color_scheme="gray",
            ),
            rx.grid(
                *[_feature_card(*f) for f in FEATURES],
                rx.box(
                    _image(
                        "/landing/manutencao.webp",
                        "Técnico abrindo um equipamento médico para testar e consertar a placa eletrônica",
                        height="100%",
                        min_height="12rem",
                    ),
                ),
                columns=rx.breakpoints(initial="1", sm="2", md="3"),
                gap="1.25rem",
                width="100%",
            ),
            spacing="4",
            width="100%",
        ),
        id="recursos",
        background=rx.color("gray", 2),
    )


def _about() -> rx.Component:
    return _section(
        rx.grid(
            _image(
                "/landing/sobre.webp",
                "Corredor de hospital iluminado e limpo",
                height=["16rem", "20rem", "24rem"],
            ),
            rx.vstack(
                rx.heading(f"Sobre a {COMPANY}", as_="h2", size="7", color=rx.color("accent", 12)),
                rx.text(
                    f"A {COMPANY} nasceu da parceria entre profissionais de engenharia clínica e de tecnologia "
                    "para resolver um problema comum nos hospitais: saber, a qualquer momento, onde está cada "
                    "equipamento, em que estado ele se encontra e quando precisa de manutenção.",
                    size="3",
                    color_scheme="gray",
                ),
                rx.text(
                    "Nosso sistema trata apenas de dados técnicos dos equipamentos. Nenhuma informação de pacientes, "
                    "dados clínicos ou diagnósticos é armazenada.",
                    size="3",
                    color_scheme="gray",
                ),
                rx.hstack(
                    *[
                        rx.hstack(rx.icon(i, size=18, color=rx.color("accent", 11), aria_hidden="true"), rx.text(t, size="2", weight="medium"), spacing="2", align="center")
                        for i, t in [("shield_check", "Acesso por perfis"), ("history", "Histórico rastreável"), ("bell_ring", "Alertas de atenção")]
                    ],
                    spacing="5",
                    wrap="wrap",
                ),
                _access_button(),
                spacing="4",
                align="start",
            ),
            columns=rx.breakpoints(initial="1", md="2"),
            gap="2.5rem",
            align="center",
        ),
        id="sobre",
    )


def _footer() -> rx.Component:
    return rx.el.footer(
        rx.flex(
            _brand(),
            rx.text(
                "© ",
                current_year(),
                f" {COMPANY}. Gestão de equipamentos hospitalares.",
                size="2",
                color_scheme="gray",
            ),
            direction=rx.breakpoints(initial="column", sm="row"),
            justify="between",
            align=rx.breakpoints(initial="start", sm="center"),
            gap="3",
            max_width=CONTENT_WIDTH,
            margin_x="auto",
            padding_x="1rem",
            padding_y="2rem",
        ),
        border_top=f"1px solid {rx.color('gray', 5)}",
        background=rx.color("gray", 2),
        width="100%",
    )


def landing_page() -> rx.Component:
    return rx.theme(
        rx.box(
            _header(),
            rx.el.main(_hero(), _features(), _about(), id="conteudo"),
            _footer(),
            min_height="100vh",
            overflow_x="hidden",
        ),
        # indigo: o azul do Radix com contraste AA para texto branco nos botões (o "blue" puro fica em ~3,2:1)
        accent_color="indigo",
        gray_color="slate",
        has_background=True,
    )
