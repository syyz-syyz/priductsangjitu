import streamlit as st
import plotly.graph_objects as go

st.title("最简单的桑基图示例")

# 节点标签
label = ["A", "B", "C", "D"]

# 链接的起点、终点和数值
source = [0, 1, 0, 2]
target = [2, 3, 3, 3]
value = [8, 4, 2, 8]

fig = go.Figure(data=[go.Sankey(
    node=dict(
        pad=15,
        thickness=20,
        line=dict(color="black", width=0.5),
        label=label,
        color="blue",
        font=dict(size=14, color="black")  # 调整字体大小颜色
    ),
    link=dict(
        source=source,
        target=target,
        value=value
    ))])

st.plotly_chart(fig, use_container_width=True)
