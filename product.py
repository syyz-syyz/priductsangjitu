import plotly.graph_objects as go
import streamlit as st

# 设置页面标题
st.title("桑葚图可视化")

# 1. 准备桑葚图数据
labels = ["A", "B", "C", "D", "E", "F"]
source = [0, 0, 1, 1, 2]
target = [3, 4, 4, 5, 5]
value = [10, 20, 15, 5, 25]

# 2. 创建桑葚图
sankey_data = go.Sankey(
    node=dict(
        pad=15,
        thickness=20,
        line=dict(color="black", width=0.5),
        label=labels,
        color=["blue", "green", "red", "purple", "orange", "pink"]
    ),
    link=dict(
        source=source,
        target=target,
        value=value
    )
)

fig = go.Figure(data=[sankey_data])
fig.update_layout(
    title_text="带文字阴影的桑葚图",
    font=dict(family="Arial, sans-serif")
)

# 3. 在Streamlit中显示图表
st.plotly_chart(fig, use_container_width=True)

# 添加说明文字
st.markdown("""
这是一个在Streamlit中展示的桑葚图(Sankey Diagram)，用于显示数据的流动和关系。
图中节点颜色分别为：A(蓝)、B(绿)、C(红)、D(紫)、E(橙)、F(粉)。
""")
