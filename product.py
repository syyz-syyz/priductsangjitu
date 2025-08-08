import plotly.graph_objects as go

fig = go.Figure(go.Sankey(
    node=dict(label=["A", "B", "C"], color="rgb(200,200,200)"),
    link=dict(source=[0], target=[1], value=[1], color="rgb(150,150,150)")
))
fig.update_layout(title_text="Minimal Test")
st.plotly_chart(fig)
