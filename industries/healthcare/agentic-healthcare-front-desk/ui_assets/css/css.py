import os

import gradio as gr

bot_title = os.getenv("BOT_TITLE", "NVIDIA Inference Microservice")

header = f"""
<span style="color:#76B900;font-weight:600;font-size:28px">
{bot_title}
</span>
"""

with open("ui_assets/css/style.css", "r") as file:
    css = file.read()

theme = gr.themes.Monochrome(primary_hue="emerald", secondary_hue="green", font=["nvidia-sans", "sans-serif"]).set(
    button_primary_background_fill="#76B900",
    button_primary_background_fill_dark="#76B900",
    button_primary_background_fill_hover="#569700",
    button_primary_background_fill_hover_dark="#569700",
    button_primary_text_color="#000000",
    button_primary_text_color_dark="#ffffff",
    button_secondary_background_fill="#76B900",
    button_secondary_background_fill_dark="#76B900",
    button_secondary_background_fill_hover="#569700",
    button_secondary_background_fill_hover_dark="#569700",
    button_secondary_text_color="#000000",
    button_secondary_text_color_dark="#ffffff",
    slider_color="#76B900",
    color_accent="#76B900",
    color_accent_soft="#76B900",
    body_text_color="#000000",
    body_text_color_dark="#ffffff",
    color_accent_soft_dark="#76B900",
    border_color_accent="#ededed",
    border_color_accent_dark="#3d3c3d",
    block_title_text_color="#000000",
    block_title_text_color_dark="#ffffff",
)
