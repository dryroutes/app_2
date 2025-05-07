import streamlit as st
import networkx as nx
import requests
import json
import os
from itertools import chain

# URL base de GitHub
BASE_URL = "https://raw.githubusercontent.com/dryroutes/app_2/main/"

# Archivos fragmentados
NUM_NODOS = 4
NUM_ARISTAS = 14

@st.cache_data
def cargar_grafo_fragmentado():
    # Descargar y cargar nodos
    nodos = []
    for i in range(1, NUM_NODOS + 1):
        url = f"{BASE_URL}nodos_{i}.json"
        res = requests.get(url)
        res.raise_for_status()
        nodos.extend(json.loads(res.content.decode("utf-8")))

    # Descargar y cargar aristas
    aristas = []
    for i in range(1, NUM_ARISTAS + 1):
        url = f"{BASE_URL}aristas_{i}.json"
        res = requests.get(url)
        res.raise_for_status()
        aristas.extend(json.loads(res.content.decode("utf-8")))

    # Construir el grafo
    G = nx.DiGraph()
    for nodo in nodos:
        G.add_node(nodo["id"], **{k: v for k, v in nodo.items() if k != "id"})

    for arista in aristas:
        G.add_edge(arista["origen"], arista["destino"], **{k: v for k, v in arista.items() if k not in ["origen", "destino"]})

    return G

# --- APP Streamlit ---
st.title("🌊 Rutas seguras ante riesgo de inundación")

# Cargar grafo
G = cargar_grafo_fragmentado()

st.success(f"Grafo cargado con {len(G.nodes)} nodos y {len(G.edges)} aristas.")


# --- VERIFICAR CONECTIVIDAD ---
st.subheader("📊 Conectividad del grafo")

if nx.is_weakly_connected(G):
    st.info("🔗 El grafo es débilmente conexo (todos los nodos están al menos conectados por alguna dirección).")
else:
    st.warning("⚠️ El grafo NO es débilmente conexo.")

num_componentes = nx.number_weakly_connected_components(G)
st.write(f"Componentes conexas encontradas: `{num_componentes}`")

# Mostrar tamaño de cada componente (solo si hay más de 1)
if num_componentes > 1:
    componentes = sorted([len(c) for c in nx.weakly_connected_components(G)], reverse=True)
    st.write("Tamaño de las componentes (mayores primero):", componentes[:5])

# --- CALCULAR RUTA MÁS SEGURA ---
st.subheader("🛣️ Calcular ruta segura entre nodos")

nodos_disponibles = list(G.nodes)
origen = st.selectbox("📍 Nodo de origen", nodos_disponibles)
destino = st.selectbox("🏁 Nodo de destino", nodos_disponibles)
criterio = st.radio("¿Qué quieres minimizar?", ["costo_total", "tiempo", "distancia"], index=0)

if st.button("Calcular ruta"):
    try:
        ruta = nx.shortest_path(G, source=origen, target=destino, weight=criterio)
        peso_total = nx.path_weight(G, ruta, weight=criterio)
        st.success(f"Ruta encontrada con {len(ruta)} nodos. {criterio} total: {peso_total:.2f}")

        # Mostrar mapa
        import folium
        from streamlit_folium import st_folium
        from folium import Marker, PolyLine

        m = folium.Map(location=[G.nodes[origen]["y"], G.nodes[origen]["x"]], zoom_start=14)
        puntos = [(G.nodes[n]["y"], G.nodes[n]["x"]) for n in ruta]
        Marker(puntos[0], tooltip="Inicio", icon=folium.Icon(color="green")).add_to(m)
        Marker(puntos[-1], tooltip="Destino", icon=folium.Icon(color="red")).add_to(m)
        PolyLine(puntos, color="blue", weight=5).add_to(m)
        st_folium(m, width=800, height=500)

    except nx.NetworkXNoPath:
        st.error("❌ No se pudo calcular la ruta: no hay conexión entre los nodos seleccionados.")

