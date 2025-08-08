import plotly.graph_objects as go
import streamlit as st
fig = go.Figure(go.Sankey(
    node=dict(label=["A", "D", "C"], color="rgb(200,200,200)"),
    link=dict(source=[0], target=[1], value=[1], color="rgb(150,150,150)"),
    arrangement="snap"  # 禁用自动布局
))
fig.update_layout(
    title_text="Minimal Test",
    plot_bgcolor="white",  # 强制白色背景
    paper_bgcolor="white"
)

# 关键修改：强制使用SVG渲染
fig.update_traces(
    node=dict(line=dict(width=0)),  # 移除节点边框
    link=dict(hoverinfo='none'),     # 禁用悬停效果
    selector=dict(type='sankey')
)

# 显式指定渲染器
st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
