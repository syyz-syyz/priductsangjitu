import plotly.graph_objects as go
from plotly.offline import plot

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
fig.update_layout(title_text="带文字阴影的桑葚图")

# 3. 生成HTML并添加自定义CSS（设置text-shadow）
# 自定义CSS：为节点标签添加文字阴影，消除重影问题
css = """
<style>
    /* 定位桑葚图的节点标签元素 */
    .sankey-node text {
        text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.5) !important;
        /* 可选：若原阴影导致重影，可重置为none */
        /* text-shadow: none !important; */
    }
</style>
"""

# 生成包含自定义CSS的HTML
html = plot(fig, output_type='div', include_plotlyjs='cdn')
html_with_css = css + html

# 保存到本地HTML文件
with open('sankey_with_shadow.html', 'w', encoding='utf-8') as f:
    f.write(html_with_css)

print("图表已保存为 sankey_with_shadow.html")
