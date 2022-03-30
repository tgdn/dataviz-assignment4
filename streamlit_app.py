import numpy as np
import pandas as pd
import altair as alt
import streamlit as st
from vega_datasets import data
from streamlit_vega_lite import altair_component

import config

st.set_page_config(
    page_title="Death and Assaults of Federal Officers in the USA",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "Data Viz Team"},
)


@st.cache
def read_data():
    states = alt.topo_feature(data.us_10m.url, feature="states")
    df = pd.read_csv("./data/state_weapon_assaults.csv", parse_dates=True)
    daf = pd.read_csv("./data/department_counts.csv")
    return states, df, daf


states, df, daf = read_data()

# Because of an incorrect mapping between geoshape id and state ids,
# we use the following map to convert.
stateid_map = {
    "1": 2,
    "11": 10,
    "12": 12,
    "13": 13,
    "14": 19,
    "15": 16,
    "16": 17,
    "17": 18,
    "18": 20,
    "19": 21,
    "2": 15,
    "20": 22,
    "21": 25,
    "22": 24,
    "23": 23,
    "24": 26,
    "25": 27,
    "26": 29,
    "27": 28,
    "28": 30,
    "29": 37,
    "30": 38,
    "31": 31,
    "32": 33,
    "33": 34,
    "34": 35,
    "35": 32,
    "36": 36,
    "37": 39,
    "38": 40,
    "39": 41,
    "4": 1,
    "40": 42,
    "41": 44,
    "42": 45,
    "43": 46,
    "44": 47,
    "45": 48,
    "46": 49,
    "47": 51,
    "48": 50,
    "49": 53,
    "5": 5,
    "50": 55,
    "51": 54,
    "52": 56,
    "6": 4,
    "7": 6,
    "8": 8,
    "9": 9,
}


@st.cache
def get_assault_count_by_state(selected_weapons):
    res = df.loc[df.weapon.isin(selected_weapons)]
    res = res[["id", "state", "count"]].groupby(["id", "state"]).sum()
    return res.reset_index()


@st.cache
def get_state_by_id(state_id: int, selected_weapons):
    # Fix geoshape id and state id.
    real_id = stateid_map.get(state_id)
    assault_count_by_state = get_assault_count_by_state(selected_weapons)
    d = assault_count_by_state.loc[assault_count_by_state["id"] == real_id]
    return d.to_dict("records")[0]


@st.cache
def get_total_count(selected_weapons, state_id=None):
    if state_id is None:
        return get_assault_count_by_state(selected_weapons)["count"].sum()
    return get_state_by_id(state_id, selected_weapons)["count"]


@st.cache
def groupby_weapon(state=None):
    # By default we select the overall sum of all states
    if state is None:
        return df[["weapon", "count"]].groupby("weapon").sum()
    # Otherwise we filter the selected state
    return (
        df.loc[df["state"] == state][["weapon", "count"]]
        .groupby("weapon")
        .sum()
    )


@st.cache(allow_output_mutation=True)
def build_weapon_pie(state=None):
    # filter our dataset
    total_by_weapon = groupby_weapon(state)

    source = pd.DataFrame(
        {"category": total_by_weapon.index, "values": total_by_weapon["count"]}
    )
    # base = alt.Chart(source).encode(
    #    theta=alt.Theta("values:Q", stack=True),
    #    color=alt.Color("category:N", legend=None),
    # )
    # pie = base.mark_arc(outerRadius=120)
    # text = base.mark_text(radius=140, size=10).encode(text="category:N")
    # return pie + text
    base = (
        alt.Chart(source)
        .encode(
            theta=alt.Theta("values:Q", stack=True),
            color=alt.Color(
                "category:N",
                scale=alt.Scale(reverse=False, scheme="tableau10"),
            ),
            radius=alt.Radius(
                "values", scale=alt.Scale(type="sqrt", zero=True, rangeMin=20)
            ),
            tooltip=["category", "values"],
        )
        .transform_filter(alt.datum.values > 0)
    )
    c1 = base.mark_arc(innerRadius=10, stroke="#fff")
    c2 = base.mark_text(radiusOffset=40).encode(text="category:N")
    return (c1 + c2).configure_view(strokeWidth=0)


@st.cache(allow_output_mutation=True)
def build_assault_map(selected_weapons):
    # df = get_assaults_by_weapon(selected_weapons)
    selection = alt.selection_single()
    color = alt.condition(
        selection,
        alt.Color(
            "count:Q",
            scale=alt.Scale(reverse=False, scheme="lightorange"),
            legend=alt.Legend(title="Count", orient="right"),
        ),
        alt.value("#ddd"),
    )

    return (
        alt.Chart(states)
        .mark_geoshape()
        .encode(color=color, tooltip=["state:N", "count:Q"])
        .transform_lookup(
            lookup="id",
            from_=alt.LookupData(
                get_assault_count_by_state(selected_weapons),
                "id",
                ["count", "state"],
            ),
        )
        .properties(width=500, projection={"type": "albersUsa"})
        .add_selection(selection)
        .configure_view(strokeWidth=0)
    )


def build_dpt_bars():
    return (
        alt.Chart(daf)
        .mark_bar(size=30)
        .encode(
            x=alt.X("count:Q", stack="zero"),
            y=alt.Y("department:N"),
            color=alt.Color("weapon:N"),
            tooltip=["weapon", "count"],
        )
        .properties(height=250, width=600)
    )


# Markup
st.title("Deaths & Assaults of Federal Officers in the USA")

selected_state = None

with st.container():

    col1, spacer, col2 = st.columns([5, 1, 6])
    with col1:
        st.markdown(
            """
    <p style="margin-top: 1rem; text-align: justify;">
    This tool allows to visualize data in three different ways and allows to make easier interpretations of deaths and assaults in the United States.
    It allows further insights by showing real world mapping of the data the use of a map.
    It is versatile and allows to show various data points onto the same vizualisation.
    </p>
        """,
            unsafe_allow_html=True,
        )

        with st.empty():
            st.metric(
                label="Selected State",
                value="All states" if not selected_state else selected_state,
            )

        container = st.container()
        select_all = st.checkbox("Select all", value=True)

        if select_all:
            selected_weapons = container.multiselect(
                "Weapons on map",
                pd.unique(df["weapon"]).tolist(),
                pd.unique(df["weapon"]).tolist(),
            )
        else:
            selected_weapons = container.multiselect(
                "Weapons on map",
                pd.unique(df["weapon"]).tolist(),
            )

    with col2:
        st.header("Deaths and assaults per state")
        state_selection = altair_component(build_assault_map(selected_weapons))
        # handle events
        if "_vgsid_" in state_selection:
            state_id = str(state_selection["_vgsid_"][0])
            selected_state = get_state_by_id(state_id, selected_weapons)
        else:
            selected_state = None

        if selected_state:
            st.write(
                f"{selected_state['state']}: {int(selected_state['count'])} assaults or deaths"
            )
        else:
            st.write(
                f"All states: {int(get_total_count(selected_weapons))} assaults or deaths"
            )

    dpt_bars = build_dpt_bars()
    pie = build_weapon_pie(selected_state["state"] if selected_state else None)

    st.subheader("Assaults outcome per department")
    st.altair_chart(dpt_bars, use_container_width=True)

    st.subheader("Assaults by weapon")
    st.altair_chart(pie, use_container_width=True)
