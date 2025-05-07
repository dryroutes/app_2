import streamlit as st
import networkx as nx
import requests
import zipfile
import json
from io import BytesIO
import folium
from folium import Marker, PolyLine
from streamlit_folium import st_folium

st.set_page_config(page_title="DryRoutes", layout="wide")
st.title("🌊 Rutas seguras ante riesgo de inundación")

# URL directa al .zip desde GitHub (raw)
ZIP_URL = "https://raw.githubusercontent.com/dryroutes/app2/main/grafo_tiny.zip"

@st.cache_data
def cargar_grafo_desde_zip(url_zip):
    G = nx.DiGraph()

    # Descargar el ZIP
    response = requests.get(url_zip)
    z = zipfile.ZipFile(BytesIO(response.content))

    # Leer todos los archivos de nodos
    nodos = []
    for filename in z.namelist():
        if filename.startswith("nodos_") and filename.endswith(".json"):
            with z.open(filename) as f:
                nodos.extend(json.load(f))

    # Leer todos los archivos de aristas
    aristas = []
    for filename in z.namelist():
        if filename.startswith("aristas_") and filename.endswith(".json"):
            with z.open(filename) as f:
                aristas.extend(json.load(f))

    # Crear nodos en el grafo
    for nodo in nodos:
        G.add_node(nodo["id"], x=nodo["x"], y=nodo["y"])

    # Crear aristas en el grafo
    for arista in aristas:
        G.add_edge(
            arista["origen"], arista["destino"],
            costo_total=arista["costo_total"],
            tiempo=arista["tiempo"],
            distancia=arista["distancia"]
        )

    return G

# ----------------- CARGA DEL GRAFO -----------------

with st.spinner("Cargando grafo desde GitHub..."):
    G = cargar_grafo_desde_zip(ZIP_URL)
    st.success(f"Grafo cargado con {G.number_of_nodes()} nodos y {G.number_of_edges()} aristas.")

# ----------------- INTERFAZ DE RUTAS -----------------

st.subheader("📍 Selección de ruta")

nodos_disponibles = list(G.nodes)
origen = st.selectbox("📍 Nodo de origen", nodos_disponibles)
destino = st.selectbox("🏁 Nodo de destino", nodos_disponibles)
criterio = st.radio("¿Qué quieres minimizar?", ["costo_total", "tiempo"])

if st.button("Calcular ruta"):
    try:
        ruta = nx.shortest_path(G, source=origen, target=destino, weight=criterio)
        st.success(f"Ruta calculada con {len(ruta)} nodos.")

        # Mostrar en mapa
        m = folium.Map(location=[G.nodes[origen]["y"], G.nodes[origen]["x"]], zoom_start=13)
        coords = [(G.nodes[n]["y"], G.nodes[n]["x"]) for n in ruta]
        PolyLine(coords, color="blue", weight=5).add_to(m)
        Marker(coords[0], tooltip="Inicio", icon=folium.Icon(color="green")).add_to(m)
        Marker(coords[-1], tooltip="Destino", icon=folium.Icon(color="red")).add_to(m)

        st_folium(m, height=500)

    except nx.NetworkXNoPath:
        st.error(f"No se pudo calcular la ruta: No path between {origen} and {destino}.")
