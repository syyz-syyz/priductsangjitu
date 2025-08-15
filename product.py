import streamlit as st
import plotly.graph_objects as go

# 设置页面配置
st.set_page_config(page_title="桑基图示例", layout="wide")

# 页面标题
st.title("Streamlit桑基图示例")
st.subheader("展示update_layout()与update_traces()的区别")

# 创建初始桑基图数据
def create_sankey_data():
    return go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=["产品A", "产品B", "华东", "华南", "华北"]  # 初始节点标签
        ),
        link=dict(
            source=[0, 0, 1, 1],  # 源节点索引
            target=[2, 3, 3, 4],  # 目标节点索引
            value=[10, 20, 15, 5] # 流量值
        )
    )

# 创建初始图表
fig = go.Figure(data=[create_sankey_data()])

# 使用update_layout()设置布局样式（非数据元素）
fig.update_layout(
    title_text="产品区域分布初始桑基图",
    font=dict(
        family="SimHei",  # 支持中文
        size=14,
        color="darkblue"
    ),
    width=1000,
    height=600,
    margin=dict(l=50, r=50, t=80, b=50),
    paper_bgcolor="lightgray",
    plot_bgcolor="white"
)

# 显示初始图表
st.subheader("1. 初始桑基图")
st.plotly_chart(fig, use_container_width=True)

# 使用update_traces()修改数据元素（节点标签和样式）
fig.update_traces(
    node=dict(
        label=["产品A（新版）", "产品B（新版）", "华东区", "华南区", "华北区"],  # 修改节点标签
        color=["#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#98D8C8"]  # 修改节点颜色
    ),
    link=dict(
        color=["rgba(255, 107, 107, 0.6)", 
               "rgba(255, 107, 107, 0.6)",
               "rgba(78, 205, 196, 0.6)",
               "rgba(78, 205, 196, 0.6)"]  # 修改连线颜色
    )
)

# 再次使用update_layout()修改布局（标题和字体）
fig.update_layout(
    title_text="修改后的桑基图（使用update_traces()和update_layout()）",
    font=dict(
        size=16,
        color="darkred"
    )
)

# 显示修改后的图表
st.subheader("2. 修改后的桑基图")
st.plotly_chart(fig, use_container_width=True)

# 说明文字
st.subheader("代码说明")
st.markdown("""
- **节点标签**：通过`update_traces(node=dict(label=[...]))`修改
- **节点颜色**：通过`update_traces(node=dict(color=[...]))`修改
- **连线颜色**：通过`update_traces(link=dict(color=[...]))`修改
- **标题、字体、背景**：通过`update_layout()`修改

可以看到，`update_traces()`用于修改与数据相关的元素（标签内容、节点和连线的颜色等），而`update_layout()`用于修改布局和全局样式。
""")
