import streamlit as st
import plotly.graph_objects as go

st.set_page_config(page_title="带update_traces的桑基图", layout="wide")

st.title("桑基图（含update_traces用法）")

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
    title_text="使用update_traces修改节点样式",
    font=dict(
        family="SimHei, Heiti TC, 黑体",
        size=14
    ),
    width=1000,
    height=600
)

# 关键：正确使用update_traces修改节点样式（只使用支持的参数）
fig.update_traces(
    node=dict(
        # 节点颜色（支持）
        color=["#FF6347", "#4682B4", "#3CB371", "#FFD700", "#9370DB"],
        # 节点标签字体（支持）
        font=dict(
            family="SimHei",  # 黑体
            size=14,
            color="white",    # 白色文字（与节点颜色对比）
            weight="bold"     # 加粗（支持的参数）
        ),
        # 节点边框（支持）
        line=dict(
            color="black",
            width=1.5
        )
    ),
    # 可以同时修改连线样式
    link=dict(
        color="rgba(120, 120, 120, 0.6)"  # 半透明灰色连线
    )
)

# 显示图表
st.plotly_chart(fig, use_container_width=True)

st.info("已恢复update_traces：仅使用Plotly明确支持的参数（color、font、line等），避免错误")
