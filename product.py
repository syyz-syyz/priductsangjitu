import streamlit as st
import plotly.graph_objects as go

st.set_page_config(page_title="桑基图安全版本", layout="wide")

st.title("桑基图（安全参数版本）")

# 创建基础桑基图数据
def create_sankey_data():
    return go.Sankey(
        node=dict(
            label=["产品A", "产品B", "华东", "华南", "华北"],
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5)
        ),
        link=dict(
            source=[0, 0, 1, 1],
            target=[2, 3, 3, 4],
            value=[10, 20, 15, 5]
        )
    )

# 创建图表
fig = go.Figure(data=[create_sankey_data()])

# 全局布局设置
fig.update_layout(
    title_text="桑基图（安全参数配置）",
    font=dict(
        family="SimHei, Heiti TC, 黑体",  # 全局字体设置
        size=14,
        color="black"
    ),
    width=1000,
    height=600,
    margin=dict(l=50, r=50, t=80, b=50)
)

# 最简化的update_traces配置（只使用经过验证的参数）
fig.update_traces(
    node=dict(
        # 节点颜色（支持单颜色或颜色列表）
        color="lightblue",
        # 节点标签字体（仅保留最基础参数）
        font=dict(
            family="SimHei",
            size=14,
            color="black"
        )
    ),
    # 连线样式（使用基础参数）
    link=dict(
        color="gray"
    )
)

# 显示图表
st.plotly_chart(fig, use_container_width=True)

st.success("已使用最安全的参数配置：仅保留Plotly所有版本都支持的基础属性，避免参数冲突")
