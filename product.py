
import streamlit as st

from pyecharts import options as opts
from pyecharts.charts import Sankey
from streamlit_echarts import st_pyecharts

# 定义节点和连接
nodes = [
    {"name": "A"}, 
    {"name": "B"}, 
    {"name": "C"}
]
links = [
    {"source": "A", "target": "B", "value": 100},
    {"source": "B", "target": "C", "value": 50}
]

# 创建桑基图
c = (
    Sankey()
    .add(
        series_name="",
        nodes=nodes,
        links=links,
        linestyle_opt=opts.LineStyleOpts(opacity=1, curve=0.5, color="source"),  # 禁用透明度
        label_opts=opts.LabelOpts(position="right"),  # 标签位置
        node_gap=10  # 节点间距
    )
    .set_global_opts(title_opts=opts.TitleOpts(title="Pyecharts桑基图"))
)

# 在Streamlit中渲染
st_pyecharts(c, height="500px")
