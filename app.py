import os
import streamlit as st

st.write("Archivos en directorio principal:")
st.write(os.listdir("."))

if os.path.exists("datos"):
    st.write("Contenido de datos:")
    st.write(os.listdir("datos"))


import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import folium

from folium.plugins import HeatMap
from streamlit_folium import st_folium


# ==================================================
# CONFIGURACIÓN GENERAL
# ==================================================

st.set_page_config(
    page_title="Accesibilidad a Parques Urbanos en Heredia",
    layout="wide"
)


# ==================================================
# CARGA DE DATOS
# ==================================================

@st.cache_data
def cargar_datos():

    parques = gpd.read_file(
        "datos/parques_urb.gpkg",
        engine="pyogrio"
)

    censo = gpd.read_file(
        "datos/censo.gpkg",
        enginge="pyogrio"
)

    limite = gpd.read_file(
        "datos/heredia_limite.gpkg",
        engine="pyogrio"
)

    return parques, censo, limite


parques, censo, limite = cargar_datos()


# ==================================================
# TÍTULO
# ==================================================

st.title("Accesibilidad a Parques Urbanos en la Ciudad de Heredia")


# ==================================================
# INTRODUCCIÓN
# ==================================================

st.header("Introducción")

st.markdown("""
Esta aplicación presenta un análisis exploratorio de la accesibilidad a parques urbanos
en la ciudad de Heredia utilizando información geoespacial de parques urbanos, población
censal y límites urbanos.

El objetivo es analizar la distribución espacial de las áreas verdes urbanas y su relación
con la población residente, utilizando herramientas de análisis geoespacial desarrolladas
en Python.

### Variables principales

- **NombreP:** nombre del parque urbano.
- **Area:** superficie del parque en metros cuadrados.
- **POBLACION:** cantidad de habitantes registrada por punto censal.

**Fuente de datos:** Marvin Alfaro Sánchez (2016). La amigabilidad de la ciudad de Heredia con los ancianos, 
            medida a partir de sus características físicas. Revista Geográfica de América Central, (57), 71–96.

Datos proporcionados por el autor durante el curso Aplicaciones en SIG en ordenamiento territorial de la 
            Maestría en SIG y Teledetección de la UNA/UCR.
""")


# ==================================================
# INDICADOR
# ==================================================

st.header("Indicador de accesibilidad")

area_total = parques["Area"].sum()

poblacion_total = censo["POBLACION"].sum()

m2_hab = area_total / poblacion_total

st.metric(
    "m² de parque por habitante",
    f"{m2_hab:.2f}"
)

st.info(
    f"La ciudad dispone aproximadamente de {m2_hab:.2f} m² de parque por habitante. "
    "La superficie total de parques urbanos alcanza aproximadamente 21 499 m² para una "
    "población cercana a 17 656 habitantes. Este resultado sugiere una disponibilidad "
    "limitada de áreas verdes urbanas para la población residente."
)


# ==================================================
# FILTRO
# ==================================================

st.sidebar.header("Filtro interactivo")

lista_parques = sorted(parques["NombreP"].unique())

parque = st.sidebar.selectbox(
    "Seleccione un parque",
    ["Todos"] + lista_parques
)

if parque == "Todos":
    parques_filtrados = parques.copy()
else:
    parques_filtrados = parques[
        parques["NombreP"] == parque
    ]


# ==================================================
# TABLA
# ==================================================

st.header("Tabla de parques urbanos")

tabla = (
    parques_filtrados[
        ["NombreP", "Area"]
    ]
    .sort_values(
        by="Area",
        ascending=False
    )
)

tabla["Porcentaje_Total"] = (
    tabla["Area"] /
    area_total
) * 100

st.dataframe(
    tabla,
    use_container_width=True,
    hide_index=True
)

st.info(
    "El parque Los Ángeles concentra la mayor superficie de área verde urbana, "
    "con 6 167.90 m², equivalentes al 28.69% del área total registrada. "
    "En contraste, el parque Fortín posee únicamente 700.50 m², representando "
    "el 3.26% del total. Esta diferencia evidencia una distribución desigual "
    "de la oferta de espacios verdes dentro de la ciudad."
)


# ==================================================
# GRÁFICO 1
# ==================================================

st.header("Gráfico 1. Área de parques urbanos")

fig1, ax1 = plt.subplots(figsize=(10, 5))

barras = ax1.bar(
    tabla["NombreP"],
    tabla["Area"]
)

ax1.set_title("Área de parques urbanos de Heredia")
ax1.set_xlabel("Parque")
ax1.set_ylabel("Área (m²)")

plt.xticks(rotation=45)

for barra in barras:

    altura = barra.get_height()

    ax1.annotate(
        f"{altura:,.0f}",
        xy=(barra.get_x() + barra.get_width() / 2, altura),
        ha="center",
        va="bottom"
    )

plt.tight_layout()

st.pyplot(fig1)

if parque == "Todos":

    st.info(
        "Los Ángeles es el parque de mayor tamaño con 6 167.90 m² "
        "(28.69% del área total), seguido por Central "
        "(2 656.80 m²) y Jardines de la Parroquia "
        "(2 595.86 m²). En el extremo opuesto se encuentra "
        "Fortín con 700.50 m². Los tres parques más grandes "
        "concentran más de la mitad del área verde urbana registrada."
    )

else:

    area = tabla.iloc[0]["Area"]

    porcentaje = tabla.iloc[0]["Porcentaje_Total"]

    st.info(
        f"El parque seleccionado posee un área aproximada de "
        f"{area:,.2f} m² y representa el "
        f"{porcentaje:.2f}% del área total de parques urbanos."
    )


# ==================================================
# GRÁFICO 2
# ==================================================

st.header("Gráfico 2. Distribución de población por punto censal")

fig2, ax2 = plt.subplots(figsize=(10, 5))

ax2.hist(
    censo["POBLACION"],
    bins=15
)

ax2.set_title(
    "Distribución de la población por punto censal"
)

ax2.set_xlabel("Habitantes")

ax2.set_ylabel("Frecuencia")

plt.tight_layout()

st.pyplot(fig2)

st.info(
    "La población promedio por punto censal es de 68 habitantes. "
    "El 50% de los puntos censales presenta 60 habitantes o menos, "
    "mientras que el 75% registra hasta 90 habitantes. "
    "El valor máximo alcanza 501 habitantes, lo que evidencia la existencia "
    "de sectores con una concentración poblacional significativamente superior al promedio."
)


# ==================================================
# MAPA
# ==================================================

st.header("Mapa interactivo de parques urbanos")

parques_wgs = parques_filtrados.to_crs(4326)

centro = parques.to_crs(4326).unary_union.centroid

mapa = folium.Map(
    location=[centro.y, centro.x],
    zoom_start=16,
    tiles="CartoDB positron"
)

folium.GeoJson(
    parques_wgs,
    style_function=lambda x: {
        "fillColor": "green",
        "color": "darkgreen",
        "weight": 2,
        "fillOpacity": 0.6
    },
    popup=folium.GeoJsonPopup(
        fields=["NombreP", "Area"],
        aliases=["Parque", "Área (m²)"]
    ),
    tooltip=folium.GeoJsonTooltip(
        fields=["NombreP"]
    )
).add_to(mapa)

folium.LayerControl().add_to(mapa)

st_folium(
    mapa,
    use_container_width=True,
    height=600
)

st.info(
    "La distribución espacial de los parques urbanos no es homogénea dentro de la ciudad de Heredia. "
    "Los Ángeles destaca no solo por ser el parque más grande, sino también por concentrar cerca del "
    "29% de toda el área verde registrada. En contraste, parques como Fortín y María Auxiliadora poseen "
    "superficies considerablemente menores, lo que podría limitar su capacidad para atender a la población "
    "residente en sus áreas de influencia."
)


# ==================================================
# CONCLUSIONES
# ==================================================

st.header("Conclusiones")

st.markdown("""
### Principales hallazgos

- La ciudad de Heredia dispone aproximadamente de **1.22 m² de parque por habitante**.
- El parque **Los Ángeles** concentra el **28.69%** de toda el área verde urbana registrada.
- Los parques presentan una distribución desigual tanto en tamaño como en localización.
- La mayoría de los puntos censales registran entre **30 y 90 habitantes**, aunque existen sectores que alcanzan hasta **501 habitantes**.
- La integración de Pandas, Matplotlib, Folium y Streamlit permitió desarrollar una aplicación interactiva para apoyar el análisis de accesibilidad a parques urbanos.
""")

# ==================================================
# MAPA 2
# ==================================================

st.header("Mapa de calor de concentración poblacional")

censo_wgs = censo.to_crs(4326)

heat_data = [
    [
        row.geometry.y,
        row.geometry.x,
        row.POBLACION
    ]
    for idx, row in censo_wgs.iterrows()
]

centro = censo_wgs.unary_union.centroid

mapa_calor = folium.Map(
    location=[centro.y, centro.x],
    zoom_start=16,
    tiles="CartoDB positron"
)

HeatMap(
    heat_data,
    radius=20,
    blur=15,
    name="Concentración poblacional"
).add_to(mapa_calor)

folium.GeoJson(
    parques_wgs,
    style_function=lambda x: {
        "fillColor": "green",
        "color": "darkgreen",
        "weight": 1,
        "fillOpacity": 0.5
    },
    name="Parques urbanos"
).add_to(mapa_calor)

folium.LayerControl().add_to(mapa_calor)

st_folium(
    mapa_calor,
    use_container_width=True,
    height=600
)

st.info(
    "El mapa de calor muestra la distribución espacial de la población dentro de la ciudad de Heredia. "
    "Las zonas de mayor intensidad representan sectores con una mayor concentración de habitantes y, por "
    "consiguiente, una mayor demanda potencial de espacios recreativos. La superposición de los parques "
    "urbanos permite identificar visualmente sectores donde la presión sobre las áreas verdes podría ser "
    "más elevada debido a la cercanía entre altas concentraciones poblacionales y una oferta limitada de parques."
)
