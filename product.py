import streamlit as st
import plotly.graph_objects as go

# 页面配置
st.set_page_config(page_title="无冲突桑基图", layout="wide")
st.title("桑基图（零冲突版本）")

# 最简单的桑基图数据（仅保留必需参数）
data = go.Sankey(
    node=dict(
        label=["A", "B", "C", "D", "E"],  # 节点标签
        pad=20,                           # 节点间距
        thickness=30                      # 节点厚度
    ),
    link=dict(
        source=[0, 0, 1, 1, 2],           # 源节点索引
        target=[2, 3, 3, 4, 4],           # 目标节点索引
        value=[10, 20, 15, 5, 25]         # 流量值
    )
)

# 创建图表（不使用update_traces，避免参数冲突）
fig = go.Figure(data=[data])

# 仅设置必要的布局（避免复杂配置）
fig.update_layout(
    title_text="基础桑基图（确保运行）",
    width=800,
    height=500,
    margin=dict(l=50, r=50, t=50, b=50)
)

# 显示图表
st.plotly_chart(fig, use_container_width=True)

st.info("已移除所有可能引起冲突的配置：\n1. 不使用update_traces()\n2. 仅保留Sankey图必需的基础参数\n3. 布局设置极简")
