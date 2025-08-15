import streamlit as st
import plotly.graph_objects as go

# 设置页面配置
st.set_page_config(page_title="修复后的桑基图", layout="wide")

st.title("修复后的桑基图（无错误版本）")

# 创建桑基图数据（移除不支持的参数）
def create_sankey_data():
    return go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=["产品A", "产品B", "华东", "华南", "华北"],
            # 初始字体设置（仅保留Plotly支持的参数）
            font=dict(
                family="SimHei",  # 黑体
                size=14,
                color="black"     # 仅支持color、family、size等基础属性
            )
        ),
        link=dict(
            source=[0, 0, 1, 1],
            target=[2, 3, 3, 4],
            value=[10, 20, 15, 5]
        )
    )

# 创建图表
fig = go.Figure(data=[create_sankey_data()])

# 布局设置（全局字体）
fig.update_layout(
    title_text="节点标签样式调整（修复后）",
    font=dict(
        family="SimHei",
        size=16,
        color="black"
    ),
    width=1000,
    height=600,
    margin=dict(l=50, r=50, t=80, b=50),
    paper_bgcolor="white",
    plot_bgcolor="white"
)

# 修改节点标签样式（仅保留支持的参数）
fig.update_traces(
    node=dict(
        font=dict(
            family=["SimHei", "Heiti TC", "黑体"],  # 兼容多系统黑体
            size=14,
            color="black",
            weight="normal"  # 合法参数：normal/bold/light
            # 移除 shadow=False（Plotly不支持该参数）
        )
    )
)

# 显示图表
st.plotly_chart(fig, use_container_width=True)

st.info("错误已修复：移除了Plotly不支持的`shadow`参数，仅保留合法的字体属性（family/size/color/weight）")
