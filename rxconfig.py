import reflex as rx

config = rx.Config(
    app_name="hardware",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
        rx.plugins.RadixThemesPlugin(theme=rx.theme(accent_color="teal", radius="medium")),
    ]
)