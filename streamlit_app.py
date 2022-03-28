import numpy as np
import pandas as pd
import altair as alt
import streamlit as st
from vega_datasets import data
from streamlit_vega_lite import altair_component

st.set_page_config(
    page_title="Death and Assaults of Federal Officers in the USA",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={"About": "Data Viz Team"},
)

# data
states = alt.topo_feature(data.us_10m.url, feature="states")
df = pd.read_csv("./data/state_weapon_assaults.csv", parse_dates=True)
# Grouping
# group by state
assault_count_by_state = (
    df[["id", "state", "count"]].groupby(["id", "state"]).sum()
)
assault_count_by_state.reset_index(inplace=True)

# Incorrect mapping between geoshape id and state ids.
# We use the following map to convert.
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
def get_state_by_id(state_id: int):
    # Fix geoshape id and state id.
    real_id = stateid_map.get(state_id)
    print(real_id)
    d = assault_count_by_state.loc[assault_count_by_state["id"] == real_id]
    print(d)
    return d.to_dict("records")[0]


@st.cache
def get_total_count(state_id=None):
    if state_id is None:
        return assault_count_by_state["count"].sum()
    return get_state_by_id(state_id)["count"]


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
    base = alt.Chart(source).encode(
        theta=alt.Theta("values:Q", stack=True),
        color=alt.Color(
            "category:N",
            legend=None,
            scale=alt.Scale(reverse=False, scheme="tableau10"),
        ),
        radius=alt.Radius(
            "values", scale=alt.Scale(type="sqrt", zero=True, rangeMin=20)
        ),
    )
    c1 = base.mark_arc(innerRadius=10, stroke="#fff")
    c2 = base.mark_text(radiusOffset=40).encode(text="category:N")
    return c1 + c2


@st.cache(allow_output_mutation=True)
def build_assault_map():
    selection = alt.selection_single()
    color = alt.condition(
        selection,
        alt.Color(
            "count:Q", scale=alt.Scale(reverse=False, scheme="lightorange")
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
                assault_count_by_state, "id", ["count", "state"]
            ),
        )
        .properties(width=650, height=500, projection={"type": "albersUsa"})
        .add_selection(selection)
    )


def build_cars():
    cars = data.cars()
    return (
        alt.Chart(cars)
        .mark_bar()
        .encode(
            x=alt.X("Miles_per_Gallon:Q", bin=alt.Bin(maxbins=30)),
            y="count()",
            color="Origin:N",
        )
    )


# Build charts
assault_map = build_assault_map()
cars = build_cars()

# Markup
st.title("Death & Assaults of Federal Officers in the USA")

st.header("Map of number of assaults in the USA")

state_selection = altair_component(assault_map)
selected_state = None

if "_vgsid_" in state_selection:
    state_id = str(state_selection["_vgsid_"][0])
    selected_state = get_state_by_id(state_id)
else:
    selected_state = None

if selected_state:
    st.write(
        f"{selected_state['state']}: {int(selected_state['count'])} assaults or deaths"
    )
else:
    st.write(f"All states: {int(get_total_count())} assaults or deaths")

# selected_state["state"] if selected_state else None
pie = build_weapon_pie(selected_state["state"] if selected_state else None)

# Two cols
col1, col2 = st.columns([4, 3])
with col1:
    st.subheader("Assaults outcome per department")
    st.altair_chart(cars, use_container_width=True)

with col2:
    st.subheader("Assaults by weapon")
    st.altair_chart(pie, use_container_width=True)
