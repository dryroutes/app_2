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
