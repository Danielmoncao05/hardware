import reflex as rx

config = rx.Config(
    app_name="hardware",
    # Tema claro até o usuário escolher outro no botão do layout (a escolha fica salva no navegador)
    default_color_mode="light",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
        rx.plugins.RadixThemesPlugin(theme=rx.theme(accent_color="teal", radius="medium")),
    ]
)