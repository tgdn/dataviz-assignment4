import numpy as np
import pandas as pd
import altair as alt
import streamlit as st
from vega_datasets import data

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
assault_count_by_state = df[["state", "count"]].groupby("state").sum()
assault_count_by_state["id"] = range(1, len(assault_count_by_state) + 1)


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
        {"category": total_by_weapon.index, "value": total_by_weapon["count"]}
    )
    base = alt.Chart(source).encode(
        theta=alt.Theta("value:Q", stack=True),
        color=alt.Color("category:N", legend=None),
    )
    pie = base.mark_arc(outerRadius=120)
    text = base.mark_text(radius=140, size=10).encode(text="category:N")

    return pie + text


@st.cache(allow_output_mutation=True)
def build_assault_map():
    return (
        alt.Chart(states)
        .mark_geoshape()
        .encode(color=alt.Color("count:Q"))
        .transform_lookup(
            lookup="id",
            from_=alt.LookupData(assault_count_by_state, "id", ["count"]),
        )
        .project("albersUsa")
    )


# Markup
st.title("Death & Assaults of Federal Officers in the USA")

st.header("Map of number of killings and assaults in the USA")
assault_map = build_assault_map()
st.altair_chart(assault_map, use_container_width=True)

st.header("Assaults outcome per department")
cars = data.cars()
chart = (
    alt.Chart(cars)
    .mark_bar()
    .encode(
        x=alt.X("Miles_per_Gallon:Q", bin=alt.Bin(maxbins=30)),
        y="count()",
        color="Origin:N",
    )
)
st.altair_chart(chart, use_container_width=True)


st.header("Percentage of injuries caused by weapon types")
pie = build_weapon_pie()
st.altair_chart(pie, use_container_width=True)
