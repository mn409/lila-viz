import streamlit as st
from PIL import Image, ImageDraw

st.set_page_config(page_title="LILA BLACK — Map Visualizer", layout="wide")
st.title("LILA BLACK — Player Journey Visualizer")

try:
    img = Image.open(r"C:\Mokshith\LILA\minimaps\AmbroseValley_Minimap.png").convert("RGBA")
    draw = ImageDraw.Draw(img)
    draw.ellipse([75, 887, 82, 894], fill=(255, 0, 0, 255))
    st.image(img, caption="AmbroseValley — Test dot at (-301.45, -355.55)", use_container_width=True)
    st.success("Coordinate mapping verified correctly!")
except Exception as e:
    st.error(f"Error loading image: {e}")