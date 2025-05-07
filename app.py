import streamlit as st
import networkx as nx
import requests
import json
from streamlit_folium import st_folium
import folium
from folium import Marker, PolyLine

st.set_page_config(page_title="DryRoutes", layout="wide")
st.title("🌊 Rutas seguras ante riesgo de inundación")

# ---------------------- CARGA DEL GRAFO ----------------------
@st.cache_data
def cargar_grafo_fragmentado():
    G = nx.DiGraph()
    base_url = "https://raw.githubusercontent.com/dryroutes/app_2/main/"

    # Cargar nodos
    for i in range(1, 6):  # nodos_1.json a nodos_5.json
        url = base_url + f"nodos_{i}.json"
        response = requests.get(url)
        nodos = json.loads(response.content)
        for nodo in nodos:
            G.add_node(nodo["id"], x=nodo["x"], y=nodo["y"])

    # Cargar aristas
    for i in range(1, 16):  # aristas_1.json a aristas_15.json
        url = base_url + f"aristas_{i}.json"
        response = requests.get(url)
        aristas = json.loads(response.content)
        for arista in aristas:
            G.add_edge(arista["origen"], arista["destino"],
                       costo_total=arista["costo_total"],
                       tiempo=arista["tiempo"],
                       distancia=arista["distancia"])

    return G

G = cargar_grafo_fragmentado()
st.success(f"Grafo cargado con {G.number_of_nodes()} nodos y {G.number_of_edges()} aristas.")

# ---------------------- INTERFAZ ----------------------
nodos_disponibles = list(G.nodes())

origen = st.selectbox("📍 Nodo de origen", nodos_disponibles)
destino = st.selectbox("🏁 Nodo de destino", nodos_disponibles)
criterio = st.radio("¿Qué quieres minimizar?", ["costo_total", "tiempo"], index=0)

if st.button("Calcular ruta"):
    try:
        ruta = nx.shortest_path(G, source=origen, target=destino, weight=criterio)
        st.success("Ruta encontrada!")

        # Mostrar en mapa
        m = folium.Map(location=[G.nodes[ruta[0]]['y'], G.nodes[ruta[0]]['x']], zoom_start=14)
        puntos = []

        for nodo in ruta:
            x = G.nodes[nodo]['x']
            y = G.nodes[nodo]['y']
            puntos.append((y, x))
            Marker(location=(y, x), tooltip=f"Nodo {nodo}").add_to(m)

        PolyLine(locations=puntos, color="blue", weight=5).add_to(m)
        st_folium(m, width=700, height=500)

    except nx.NetworkXNoPath:
        st.error(f"No se pudo calcular la ruta: No hay camino entre {origen} y {destino}.")
