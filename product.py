import plotly.graph_objects as go
import streamlit as st


fig = go.Figure(go.Sankey(
    node=dict(
        label=["A", "B", "C"], 
        color="rgb(200,200,200)",
        pad=20,  # 增加节点间距
        thickness=30  # 增加节点厚度
    ),
    link=dict(
        source=[0], 
        target=[1], 
        value=[1], 
        color="rgba(150,150,150,1)",  # 显式设置完全不透明
        hoverinfo='none'
    ),
    arrangement="snap"
))

fig.update_layout(
    title_text="Minimal Test - Canvas Render",
    plot_bgcolor="white",
    paper_bgcolor="white",
    font=dict(family="Arial", size=14)
)

# 关键修改：强制使用Canvas渲染
config = {
    'toImageButtonOptions': {
        'format': 'png',
        'scale': 2
    },
    'displayModeBar': False,
    'plotlyServerURL': 'https://cdn.plot.ly'  # 使用CDN资源
}

st.plotly_chart(fig, use_container_width=True, config=config)
