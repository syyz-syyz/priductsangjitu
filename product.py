import plotly.graph_objects as go
import streamlit as st

# 注入自定义CSS，为桑葚图节点添加文字阴影
st.markdown("""
<style>
    /* 定位Plotly桑葚图的节点标签元素 */
    .stPlotlyChart div svg g:nth-child(3) g g text {
        text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.5) !important;
        font-weight: 500 !important;
    }
</style>
""", unsafe_allow_html=True)

# 设置页面标题
st.title("带文字阴影的桑葚图")

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
    title_text="桑葚图节点文字阴影效果",
    font=dict(family="Arial, sans-serif")
)

# 3. 在Streamlit中显示图表
st.plotly_chart(fig, use_container_width=True)

# 添加说明文字
st.markdown("""
图表中的节点文字已添加阴影效果，使文字在彩色背景上更清晰易读。
这种方法通过Streamlit的自定义CSS实现了与原HTML版本相同的视觉效果。
""")
    
