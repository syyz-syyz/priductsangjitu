import streamlit as st
import plotly.graph_objects as go

# 设置页面配置
st.set_page_config(page_title="桑基图标签样式示例", layout="wide")

# 页面标题
st.title("桑基图节点标签样式调整")
st.subheader("黑体字体，无阴影和重影效果")

# 创建桑基图数据
def create_sankey_data():
    return go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=["产品A", "产品B", "华东", "华南", "华北"],
            # 初始字体设置（可被后续update_traces覆盖）
            font=dict(
                family="SimHei",  # 默认黑体
                size=14
            )
        ),
        link=dict(
            source=[0, 0, 1, 1],
            target=[2, 3, 3, 4],
            value=[10, 20, 15, 5]
        )
    )

# 创建初始图表
fig = go.Figure(data=[create_sankey_data()])

# 设置布局（确保全局无艺术字效果）
fig.update_layout(
    title_text="节点标签样式调整示例",
    # 全局字体设置（影响标题等非节点文本）
    font=dict(
        family="SimHei",  # 黑体
        size=16,
        color="black"     # 纯黑色，无阴影
    ),
    width=1000,
    height=600,
    margin=dict(l=50, r=50, t=80, b=50),
    paper_bgcolor="white",
    plot_bgcolor="white"
)

# 关键：修改节点标签样式（黑体，无阴影/重影）
fig.update_traces(
    node=dict(
        # 节点标签字体设置
        font=dict(
            family=["SimHei", "Heiti TC", "黑体"],  # 兼容不同系统的黑体字体
            size=14,
            color="black",                          # 纯黑色文字
            # 以下设置确保无艺术字效果
            shadow=False,                           # 关闭阴影
            weight="normal"                         # 正常字重（非加粗）
        )
    )
)

# 显示图表
st.plotly_chart(fig, use_container_width=True)

# 说明文字
st.subheader("标签样式说明")
st.markdown("""
- **字体**：节点标签使用黑体（`SimHei`/`Heiti TC`/`黑体`，兼容Windows、Mac和Linux系统）
- **无艺术效果**：通过设置 `shadow=False` 去除阴影，纯黑色文字（`color="black"`）避免重影
- **样式控制**：节点标签的字体样式通过 `update_traces(node=dict(font=...))` 实现，属于数据元素样式调整
- **兼容性**：多字体名称设置确保在不同操作系统上都能正确显示黑体
""")
