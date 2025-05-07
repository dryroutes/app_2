import streamlit as st
import networkx as nx
import requests
import json
from itertools import chain

# -------------------- CONFIG --------------------
BASE_URL = "https://raw.githubusercontent.com/dryroutes/app_2/main/"
NUM_NODOS = 4
NUM_ARISTAS = 14

# -------------------- CARGAR GRAFO --------------------
@st.cache_data
def cargar_grafo_fragmentado():
    nodos = []
    for i in range(1, NUM_NODOS + 1):
        url = f"{BASE_URL}nodos_{i}.json"
        res = requests.get(url)
        res.raise_for_status()
        nodos.extend(json.loads(res.content.decode("utf-8")))

    aristas = []
    for i in range(1, NUM_ARISTAS + 1):
        url = f"{BASE_URL}aristas_{i}.json"
        res = requests.get(url)
        res.raise_for_status()
        aristas.extend(json.loads(res.content.decode("utf-8")))

    G = nx.DiGraph()
    for nodo in nodos:
        G.add_node(nodo["id"], **{k: v for k, v in nodo.items() if k != "id"})

    for arista in aristas:
        G.add_edge(arista["origen"], arista["destino"], **{k: v for k, v in arista.items() if k not in ["origen", "destino"]})

    return G

# -------------------- APP --------------------
st.title("🌊 Rutas seguras ante riesgo de inundación")

G = cargar_grafo_fragmentado()
st.success(f"Grafo cargado con {len(G.nodes)} nodos y {len(G.edges)} aristas.")

# -------------------- CONECTIVIDAD --------------------
st.subheader("📊 Conectividad del grafo")

if nx.is_weakly_connected(G):
    st.info("🔗 El grafo es débilmente conexo.")
else:
    st.warning("⚠️ El grafo NO es débilmente conexo.")

num_componentes = nx.number_weakly_connected_components(G)
st.write(f"Componentes conexas encontradas: `{num_componentes}`")

if num_componentes > 1:
    componentes = sorted([len(c) for c in nx.weakly_connected_components(G)], reverse=True)
    st.write("Tamaño de las componentes (mayores primero):", componentes[:5])

# -------------------- CÁLCULO DE RUTAS --------------------
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

        puntos = [(G.nodes[n]["y"], G.nodes[n]["x"]) for n in ruta if "y" in G.nodes[n] and "x" in G.nodes[n]]

        if len(puntos) >= 2:
            import folium
            from streamlit_folium import st_folium
            from folium import Marker, PolyLine

            m = folium.Map(location=puntos[0], zoom_start=14)
            Marker(puntos[0], tooltip="Inicio", icon=folium.Icon(color="green")).add_to(m)
            Marker(puntos[-1], tooltip="Destino", icon=folium.Icon(color="red")).add_to(m)
            PolyLine(puntos, color="blue", weight=5).add_to(m)
            st_folium(m, width=800, height=500)

        elif len(puntos) == 1:
            st.warning("⚠️ Ruta con un solo nodo: no se puede pintar el mapa.")
        else:
            st.error("❌ No se pudo pintar el mapa: nodos sin coordenadas válidas.")

    except nx.NetworkXNoPath:
        st.error("❌ No se pudo calcular la ruta: no hay conexión entre los nodos seleccionados.")
    except Exception as e:
        st.exception(f"⛔ Error inesperado: {e}")
