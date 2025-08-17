import streamlit as st
import plotly.graph_objects as go

st.title("最简单的桑基图示例")

# 定义桑基图节点
label = ["A", "B", "C", "D"]

# 定义桑基图连接关系（source, target, value）
source = [0, 1, 0, 2]
target = [2, 3, 3, 3]
value = [8, 4, 2, 8]

fig = go.Figure(data=[go.Sankey(
    node=dict(
        pad=15,
        thickness=20,
        line=dict(color="black", width=0.5),
        label=label,
        color="blue"
    ),
    link=dict(
        source=source,
        target=target,
        value=value
    ))])

st.plotly_chart(fig)
