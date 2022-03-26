import numpy as np
import pandas as pd
import altair as alt
import streamlit as st
from vega_datasets import data
from streamlit_vega_lite import altair_component

st.set_page_config(
    page_title="My Title",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
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


@st.cache
def get_state_by_id(state_id: int):
    return assault_count_by_state.loc[assault_count_by_state["id"] == state_id]


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
pie = build_weapon_pie()

# Markup
st.title("Death & Assaults of Federal Officers in the USA")

st.header("Map of number of assaults in the USA")

# st.altair_chart(assault_map, use_container_width=True)
state_selection = altair_component(assault_map)

if "_vgsid_" in state_selection:
    state_id = state_selection["_vgsid_"][0]
    row = get_state_by_id(state_id)
    if row is None or row.empty:
        row = get_state_by_id(56)
    st.write(row)
else:
    st.write("All states")

st.write(assault_count_by_state)

# Two cols
col1, col2 = st.columns([4, 3])
with col1:
    st.subheader("Assaults outcome per department")
    st.altair_chart(cars, use_container_width=True)

with col2:
    st.subheader("Assaults by weapon")
    st.altair_chart(pie, use_container_width=True)
