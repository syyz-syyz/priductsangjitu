import streamlit as st
import pandas as pd
import numpy as np
import os
from io import BytesIO, StringIO
import plotly.graph_objects as go
from plotly.io import from_json, to_json
from datetime import datetime
import pickle


# 初始化session状态
essential_states = {
    'flow_df': None,
    'brand_mapping': None,
    'original_df': None,
    'marked_data': None,
    'split_flow_data': None,
    'sorted_split_data': None,
    'split_flow_data_start': None,
    'sorted_split_data_start': None,
    'sankey_fig_start': None,
    'split_flow_data_end': None,
    'sorted_split_data_end': None,
    'sankey_fig_end': None,
    'selected_product': None,
    'sankey_fig': None,
    'top_products': None,
    'history_snapshots': [],
    'current_snapshot_id': None,
    'uploaded_file_processed': False,
    'start_period': None,
    'end_period': None
}

for key, value in essential_states.items():
    if key not in st.session_state:
        st.session_state[key] = value

# 历史记录快照配置
SNAPSHOT_FILE = "analysis_snapshots.pkl"

# 定义中间层标签配置
MIDDLE_LAYER_CONFIG = [
    {"label": "期初_新增", "color": "rgba(153, 102, 255, 0.8)"},
    {"label": "期初_不同品牌不同产品", "color": "rgba(54, 162, 235, 0.8)"},
    {"label": "期初_同品牌不同产品", "color": "rgba(153, 153, 255, 0.8)"},
    {"label": "同品牌同产品", "color": "rgba(102, 204, 102, 0.8)"},
    {"label": "期末_同品牌不同产品", "color": "rgba(102, 255, 255, 0.8)"},
    {"label": "期末_不同品牌不同产品", "color": "rgba(75, 192, 192, 0.8)"},
    {"label": "期末_流失", "color": "rgba(255, 99, 132, 0.8)"}
]

MIDDLE_LAYER_ORDER = [item["label"] for item in MIDDLE_LAYER_CONFIG]
LABEL_COLOR_MAP = {item["label"]: item["color"] for item in MIDDLE_LAYER_CONFIG}
LABEL_ORDER = MIDDLE_LAYER_ORDER
label_sort_mapping = {label: idx for idx, label in enumerate(LABEL_ORDER)}

# 页面配置
st.set_page_config(
    page_title="产品品牌流量分析工具",
    page_icon="📊",
    layout="wide"
)

# Token校验函数（实际使用时可启用）
def check_token():
    token = st.sidebar.text_input("请输入访问令牌", type="password")
    if token != VALID_TOKEN:
        st.error("令牌无效，请重新输入")
        st.stop()
    st.sidebar.success("令牌验证通过")

# 加载历史快照
def load_snapshots_from_file():
    try:
        if os.path.exists(SNAPSHOT_FILE):
            with open(SNAPSHOT_FILE, 'rb') as f:
                return pickle.load(f)
        return []
    except Exception as e:
        st.error(f"加载快照文件失败: {str(e)}")
        return []

# 保存历史快照
def save_snapshots_to_file(snapshots):
    try:
        with open(SNAPSHOT_FILE, 'wb') as f:
            pickle.dump(snapshots, f)
        return True
    except Exception as e:
        st.error(f"保存快照失败: {str(e)}")
        return False

# 初始化时加载历史快照
if not st.session_state.history_snapshots:
    loaded_snapshots = load_snapshots_from_file()
    st.session_state.history_snapshots = loaded_snapshots

# 保存快照
def save_snapshot(start_period, end_period, product):
    if st.session_state.sorted_split_data is None or st.session_state.sankey_fig is None:
        st.warning("没有可保存的分析结果")
        return False
        
    snapshot_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
    try:
        snapshot = {
            "id": snapshot_id,
            "timestamp": datetime.now(),
            "metadata": {
                "start_period": start_period,
                "end_period": end_period,
                "product": product
            },
            "data": {
                "split_flow_csv": st.session_state.sorted_split_data.to_csv(index=False),
                "sankey_fig_json": to_json(st.session_state.sankey_fig),
                "split_flow_start_csv": st.session_state.sorted_split_data_start.to_csv(index=False) if st.session_state.sorted_split_data_start is not None else None,
                "sankey_fig_start_json": to_json(st.session_state.sankey_fig_start) if st.session_state.sankey_fig_start is not None else None,
                "split_flow_end_csv": st.session_state.sorted_split_data_end.to_csv(index=False) if st.session_state.sorted_split_data_end is not None else None,
                "sankey_fig_end_json": to_json(st.session_state.sankey_fig_end) if st.session_state.sankey_fig_end is not None else None,
                "marked_data_csv": st.session_state.marked_data.to_csv(index=False) if st.session_state.marked_data is not None else None
            }
        }
        
        st.session_state.history_snapshots.append(snapshot)
        st.session_state.current_snapshot_id = snapshot_id
        save_snapshots_to_file(st.session_state.history_snapshots)
        return True
    except Exception as e:
        st.error(f"创建快照时出错: {str(e)}")
        return False

# 从快照加载数据
def load_from_snapshot(snapshot_id):
    try:
        for snapshot in st.session_state.history_snapshots:
            if snapshot["id"] == snapshot_id:
                required_keys = ["split_flow_csv", "sankey_fig_json", 
                                "split_flow_start_csv", "sankey_fig_start_json",
                                "split_flow_end_csv", "sankey_fig_end_json",
                                "marked_data_csv"]
                if not all(key in snapshot["data"] for key in required_keys):
                    st.error("快照数据不完整，无法加载")
                    return False

                # 加载核心数据
                st.session_state.sorted_split_data = pd.read_csv(
                    StringIO(snapshot["data"]["split_flow_csv"])
                )
                
                st.session_state.sankey_fig = from_json(
                    snapshot["data"]["sankey_fig_json"]
                )
                
                # 加载新增视图数据
                if snapshot["data"]["split_flow_start_csv"]:
                    st.session_state.sorted_split_data_start = pd.read_csv(
                        StringIO(snapshot["data"]["split_flow_start_csv"])
                    )
                    st.session_state.sankey_fig_start = from_json(
                        snapshot["data"]["sankey_fig_start_json"]
                    )
                
                if snapshot["data"]["split_flow_end_csv"]:
                    st.session_state.sorted_split_data_end = pd.read_csv(
                        StringIO(snapshot["data"]["split_flow_end_csv"])
                    )
                    st.session_state.sankey_fig_end = from_json(
                        snapshot["data"]["sankey_fig_end_json"]
                    )
                
                # 加载标记数据
                if snapshot["data"]["marked_data_csv"]:
                    st.session_state.marked_data = pd.read_csv(
                        StringIO(snapshot["data"]["marked_data_csv"])
                    )
                
                # 加载元数据
                st.session_state.selected_product = snapshot["metadata"]["product"]
                st.session_state.start_period = snapshot["metadata"]["start_period"]
                st.session_state.end_period = snapshot["metadata"]["end_period"]
                st.session_state.current_snapshot_id = snapshot_id
                
                return True
        
        st.error(f"未找到ID为 {snapshot_id} 的快照")
        return False
    except Exception as e:
        st.error(f"加载快照时出错: {str(e)}")
        return False

# 删除快照
def delete_snapshot(snapshot_id):
    try:
        st.session_state.history_snapshots = [
            s for s in st.session_state.history_snapshots 
            if s["id"] != snapshot_id
        ]
        if st.session_state.current_snapshot_id == snapshot_id:
            st.session_state.current_snapshot_id = None
        save_snapshots_to_file(st.session_state.history_snapshots)
        return True
    except Exception as e:
        st.error(f"删除快照时出错: {str(e)}")
        return False

# 生成桑基图函数（优化标签重影问题）
def generate_sorted_sankey(split_flow_data, top_products=None, use_full_products=False):
    def aggregate_node(node, top_products, use_full_products):
        if use_full_products or not top_products:
            return node
            
        special_tags = ["新增门店", "门店流失", "产品流失", "新增产品", "其他产品"]
        if node in special_tags or node in MIDDLE_LAYER_ORDER:
            return node
            
        if node.startswith("期初_"):
            base_node = node[3:]
            if base_node not in top_products and base_node not in special_tags:
                return "期初_其他产品"
            return node
            
        if node.startswith("期末_"):
            base_node = node[3:]
            if base_node not in top_products and base_node not in special_tags:
                return "期末_其他产品"
            return node
            
        return node
    
    def process_source_node(node):
        if "期初" in node or "新增" in node or node in MIDDLE_LAYER_ORDER:
            return node
        return f"期初_{node}"
    
    def process_target_node(node):
        if "期末" in node or "流失" in node or node in MIDDLE_LAYER_ORDER:
            return node
        return f"期末_{node}"
    
    processed_data = split_flow_data.copy()
    processed_data['源节点'] = processed_data['源节点'].apply(process_source_node)
    processed_data['目标节点'] = processed_data['目标节点'].apply(process_target_node)
    
    if not use_full_products and top_products is not None:
        processed_data['源节点'] = processed_data['源节点'].apply(
            lambda x: aggregate_node(x, top_products, use_full_products)
        )
        processed_data['目标节点'] = processed_data['目标节点'].apply(
            lambda x: aggregate_node(x, top_products, use_full_products)
        )
        processed_data = processed_data.groupby(
            ['源节点', '目标节点', '流向类型', '标签类别'], 
            as_index=False
        )['流量'].sum()
    
    # 提取各层节点（去重处理）
    layer1_nodes = []
    for _, row in processed_data.iterrows():
        if row['流向类型'] == '期初到标签':
            node = row['源节点']
            if node not in layer1_nodes and (node.startswith("期初_") or node in ["新增门店", "新增产品"]):
                layer1_nodes.append(node)
    
    layer2_nodes = [node for node in MIDDLE_LAYER_ORDER if node in processed_data['源节点'].values or node in processed_data['目标节点'].values]
    
    layer3_nodes = []
    for _, row in processed_data.iterrows():
        if row['流向类型'] == '标签到期末':
            node = row['目标节点']
            if node not in layer3_nodes and (node.startswith("期末_") or node in ["门店流失", "产品流失"]):
                layer3_nodes.append(node)
    
    # 关键修复1：节点去重（避免重复标签）
    all_nodes = layer1_nodes + layer2_nodes + layer3_nodes
    unique_nodes = list(dict.fromkeys(all_nodes))  # 去重并保留顺序
    
    # 计算中间层百分比
    middle_layer_inflows = {}
    total_middle_inflow = 0
    for node in layer2_nodes:
        inflow = processed_data[
            (processed_data['目标节点'] == node) & 
            (processed_data['流向类型'] == '期初到标签')
        ]['流量'].sum()
        middle_layer_inflows[node] = inflow
        total_middle_inflow += inflow
    
    layer2_labels_with_percent = []
    for node in layer2_nodes:
        # 优化标签长度，避免过长导致重叠
        short_label = node.replace("不同品牌不同产品", "跨品牌").replace("同品牌不同产品", "同品牌跨产品")
        if total_middle_inflow > 0:
            percentage = (middle_layer_inflows[node] / total_middle_inflow) * 100
            layer2_labels_with_percent.append(f"{short_label}\n{round(percentage)}%")
        else:
            layer2_labels_with_percent.append(short_label)
    
    # 关键修复2：标签与去重节点一一对应
    labels = []
    for node in unique_nodes:
        if node in layer1_nodes:
            # 简化期初节点标签
            simplified = node.replace("期初_", "")
            labels.append(simplified)
        elif node in layer2_nodes:
            idx = layer2_nodes.index(node)
            labels.append(layer2_labels_with_percent[idx])
        elif node in layer3_nodes:
            # 简化期末节点标签
            simplified = node.replace("期末_", "")
            labels.append(simplified)
    
    node_indices = {node: idx for idx, node in enumerate(unique_nodes)}
    
    # 连接配置
    links_source = [node_indices[row['源节点']] for _, row in processed_data.iterrows()]
    links_target = [node_indices[row['目标节点']] for _, row in processed_data.iterrows()]
    links_value = processed_data['流量'].tolist()
    
    # 颜色配置
    def get_node_color(node):
        if node in LABEL_COLOR_MAP:
            return LABEL_COLOR_MAP[node]
        elif node.startswith("期初_") or node in ["新增门店", "新增产品"]:
            connected_labels = processed_data[processed_data['源节点'] == node]['标签类别'].unique()
            if len(connected_labels) > 0:
                label_color = LABEL_COLOR_MAP.get(connected_labels[0], "rgba(200, 200, 200, 0.8)")
                return label_color.replace("0.8", "0.4").replace("0.6", "0.3")
            return "rgba(200, 200, 200, 0.4)"
        elif node.startswith("期末_") or node in ["门店流失", "产品流失"]:
            connected_labels = processed_data[processed_data['目标节点'] == node]['标签类别'].unique()
            if len(connected_labels) > 0:
                label_color = LABEL_COLOR_MAP.get(connected_labels[0], "rgba(200, 200, 200, 0.8)")
                return label_color.replace("0.8", "0.4").replace("0.6", "0.3")
            return "rgba(200, 200, 200, 0.4)"
        else:
            return "rgba(200, 200, 200, 0.8)"
    
    node_colors = [get_node_color(node) for node in unique_nodes]
    
    link_colors = []
    for _, row in processed_data.iterrows():
        label_color = LABEL_COLOR_MAP.get(row['标签类别'], "rgba(200, 200, 200, 0.8)")
        link_color = label_color.replace("0.8", "0.3").replace("0.6", "0.2")
        link_colors.append(link_color)
    
    # 关键修复3：优化节点位置计算（避免重叠）
    node_x, node_y = [], []
    vertical_padding = 0.1  # 上下边距
    vertical_range = 1.0 - 2 * vertical_padding  # 可用垂直空间
    
    # 第一层节点位置（x固定0.15，增加水平间距）
    level_count = len(layer1_nodes)
    for i in range(level_count):
        node_x.append(0.15)  # 增加x值，远离左侧边缘
        if level_count == 1:
            node_y.append(0.5)  # 单个节点居中
        else:
            # 更均匀的垂直分布
            node_y.append(vertical_padding + (vertical_range / (level_count - 1)) * i)
    
    # 第二层节点位置（x固定0.5，中间位置）
    level_count = len(layer2_nodes)
    for i in range(level_count):
        node_x.append(0.5)
        if level_count == 1:
            node_y.append(0.5)
        else:
            node_y.append(vertical_padding + (vertical_range / (level_count - 1)) * i)
    
    # 第三层节点位置（x固定0.85，增加水平间距）
    level_count = len(layer3_nodes)
    for i in range(level_count):
        node_x.append(0.85)  # 减小x值，远离右侧边缘
        if level_count == 1:
            node_y.append(0.5)
        else:
            node_y.append(vertical_padding + (vertical_range / (level_count - 1)) * i)
    
    # 创建桑基图（关键修复4：增强渲染配置）
    fig = go.Figure(data=[go.Sankey(
        arrangement="none",  # 禁用自动排列，使用手动坐标
        node=dict(
            pad=20,  # 增大节点间距，减少重叠
            thickness=25,  # 增加节点厚度
            line=dict(color="black", width=1),  # 更清晰的节点边框
            label=labels,
            color=node_colors,
            x=node_x,
            y=node_y,
            # 优化字体配置，解决云环境字体问题
            textfont=dict(
                family="SimHei, Microsoft YaHei, Heiti TC, Arial, sans-serif",
                size=11,
                color="rgb(30, 30, 30)"
            )
        ),
        link=dict(
            source=links_source,
            target=links_target,
            value=links_value,
            color=link_colors,
            line=dict(width=0.5)  # 链接线优化
        )
    )])
    
    # 添加图例（优化布局）
    legend_items = []
    for item in MIDDLE_LAYER_CONFIG:
        try:
            rgba_str = item["color"].replace("rgba", "").replace("(", "").replace(")", "")
            r, g, b = map(lambda x: int(float(x.strip())), rgba_str.split(",")[:3])
            short_label = item["label"].replace("不同品牌不同产品", "跨品牌").replace("同品牌不同产品", "同品牌跨产品")
            legend_items.append(f'<span style="color:rgb({r},{g},{b})">●</span> {short_label}')
        except:
            legend_items.append(f'<span style="color:gray">●</span> {item["label"]}')
    
    # 图例分行显示，避免水平溢出
    legend_chunk_size = 3
    legend_rows = []
    for i in range(0, len(legend_items), legend_chunk_size):
        legend_rows.append(" ".join(legend_items[i:i+legend_chunk_size]))
    
    for i, row in enumerate(legend_rows):
        fig.add_annotation(
            text=row,
            x=0.5, y=1.05 + (i * 0.05),  # 垂直排列图例
            xref="paper", yref="paper",
            showarrow=False, 
            font=dict(
                family="SimHei, Microsoft YaHei, Arial",
                size=10
            ),
            align="center"
        )
    
    # 图表尺寸和布局优化
    max_level_count = max(len(layer1_nodes), len(layer2_nodes), len(layer3_nodes))
    height = max_level_count * 60 + 250  # 基于节点数量动态调整高度
    height = min(max(height, 600), 1000)  # 限制最大最小高度
    
    # 关键修复5：增强字体兼容性和布局稳定性
    fig.update_layout(
        title_text="产品流量三层桑基图分析",
        font=dict(
            family="SimHei, Microsoft YaHei, Heiti TC, Arial, sans-serif",
            size=12,
            color="rgb(30, 30, 30)"
        ),
        width=1000,  # 增加宽度，提供更多空间
        height=height,
        margin=dict(l=100, r=100, t=120 + (len(legend_rows)*30), b=80),  # 根据图例行数调整顶部边距
        paper_bgcolor="rgba(255, 255, 255, 1)",  # 白色背景，增强对比度
        plot_bgcolor="rgba(255, 255, 255, 1)"
    )
    
    # 禁用自动缩放，保持布局一致性
    fig.update_xaxes(autorange=False)
    fig.update_yaxes(autorange=False)
    
    return fig

# 生成期末分析报告
def generate_end_report(marked_data, product):
    if marked_data is None or marked_data.empty:
        return "无可用数据生成期末分析报告。"
    
    relevant_data = marked_data[marked_data['标签类别'] != "不涉及目标产品"]
    if relevant_data.empty:
        return f"无涉及产品 {product} 的相关数据，无法生成期末分析报告。"
    
    start_total = relevant_data[relevant_data['期初产品'] == product]['流量'].sum() / 10000
    
    if start_total == 0:
        return f"产品 {product} 期初金额为0，无法生成有效期末分析报告。"
    
    same_product = relevant_data[
        (relevant_data['标签类别'] == "同品牌同产品") & 
        (relevant_data['期初产品'] == product)
    ]['流量'].sum() / 10000
    
    same_brand_other = relevant_data[
        (relevant_data['标签类别'] == "期末_同品牌不同产品") & 
        (relevant_data['期初产品'] == product)
    ]['流量'].sum() / 10000
    
    other_brand = relevant_data[
        (relevant_data['标签类别'] == "期末_不同品牌不同产品") & 
        (relevant_data['期初产品'] == product)
    ]['流量'].sum() / 10000
    
    store_loss = relevant_data[
        (relevant_data['标签类别'] == "期末_流失") & 
        (relevant_data['期初产品'] == product) &
        (relevant_data['期末产品'] == "门店流失")
    ]['流量'].sum() / 10000
    
    product_loss = relevant_data[
        (relevant_data['标签类别'] == "期末_流失") & 
        (relevant_data['期初产品'] == product) &
        (relevant_data['期末产品'] == "产品流失")
    ]['流量'].sum() / 10000
    
    same_brand_details = relevant_data[
        (relevant_data['标签类别'] == "期末_同品牌不同产品") & 
        (relevant_data['期初产品'] == product)
    ].groupby('期末产品')['流量'].sum().reset_index()
    same_brand_details = same_brand_details.sort_values('流量', ascending=False).head(2)
    same_brand_details['流量'] = same_brand_details['流量'] / 10000
    
    other_brand_details = relevant_data[
        (relevant_data['标签类别'] == "期末_不同品牌不同产品") & 
        (relevant_data['期初产品'] == product)
    ].groupby('期末产品')['流量'].sum().reset_index()
    other_brand_details = other_brand_details.sort_values('流量', ascending=False).head(2)
    other_brand_details['流量'] = other_brand_details['流量'] / 10000
    
    report = f"期初分析报告：{product}\n\n"
    report += f"产品期初金额为{start_total:.2f}万。"
    report += f"期末仍旧使用本品的金额为{same_product:.2f}万，占比{same_product/start_total*100:.2f}%；"
    report += f"转换为同品牌的其它产品的金额为{same_brand_other:.2f}万，占比{same_brand_other/start_total*100:.2f}%，"
    
    if not same_brand_details.empty:
        details = []
        for i, row in same_brand_details.iterrows():
            details.append(f"主要为{row['期末产品']}（金额{row['流量']:.2f}万，占比{row['流量']/start_total*100:.2f}%）")
        report += "、".join(details) + "；"
    else:
        report += "无主要转换产品；"
    
    report += f"转换为其它品牌产品的金额为{other_brand:.2f}万，占比{other_brand/start_total*100:.2f}%，"
    
    if not other_brand_details.empty:
        details = []
        for i, row in other_brand_details.iterrows():
            details.append(f"主要为{row['期末产品']}（金额{row['流量']:.2f}万，占比{row['流量']/start_total*100:.2f}%）")
        report += "、".join(details) + "；"
    else:
        report += "无主要转换产品；"
    
    report += f"门店流失金额为{store_loss:.2f}万，占比{store_loss/start_total*100:.2f}%；"
    report += f"产品流失金额为{product_loss:.2f}万，占比{product_loss/start_total*100:.2f}%。\n\n"
    
    return report

# 生成期初分析报告
def generate_start_report(marked_data, product):
    if marked_data is None or marked_data.empty:
        return "无可用数据生成期初分析报告。"
    
    relevant_data = marked_data[marked_data['标签类别'] != "不涉及目标产品"]
    if relevant_data.empty:
        return f"无涉及产品 {product} 的相关数据，无法生成期初分析报告。"
    
    end_total = relevant_data[relevant_data['期末产品'] == product]['流量'].sum() / 10000
    
    if end_total == 0:
        return f"产品 {product} 期末金额为0，无法生成有效期初分析报告。"
    
    same_product = relevant_data[
        (relevant_data['标签类别'] == "同品牌同产品") & 
        (relevant_data['期末产品'] == product)
    ]['流量'].sum() / 10000
    
    new_stores = relevant_data[
        (relevant_data['标签类别'] == "期初_新增") & 
        (relevant_data['期末产品'] == product) &
        (relevant_data['期初产品'] == "新增门店")
    ]['流量'].sum() / 10000
    
    new_users = relevant_data[
        (relevant_data['标签类别'] == "期初_新增") & 
        (relevant_data['期末产品'] == product) &
        (relevant_data['期初产品'] == "新增产品")
    ]['流量'].sum() / 10000
    
    same_brand_other = relevant_data[
        (relevant_data['标签类别'] == "期初_同品牌不同产品") & 
        (relevant_data['期末产品'] == product)
    ]['流量'].sum() / 10000
    
    other_brand = relevant_data[
        (relevant_data['标签类别'] == "期初_不同品牌不同产品") & 
        (relevant_data['期末产品'] == product)
    ]['流量'].sum() / 10000
    
    same_brand_details = relevant_data[
        (relevant_data['标签类别'] == "期初_同品牌不同产品") & 
        (relevant_data['期末产品'] == product)
    ].groupby('期初产品')['流量'].sum().reset_index()
    same_brand_details = same_brand_details.sort_values('流量', ascending=False).head(2)
    same_brand_details['流量'] = same_brand_details['流量'] / 10000
    
    other_brand_details = relevant_data[
        (relevant_data['标签类别'] == "期初_不同品牌不同产品") & 
        (relevant_data['期末产品'] == product)
    ].groupby('期初产品')['流量'].sum().reset_index()
    other_brand_details = other_brand_details.sort_values('流量', ascending=False).head(2)
    other_brand_details['流量'] = other_brand_details['流量'] / 10000
    
    report = f"期末分析报告：{product}\n\n"
    report += f"产品期末总金额为{end_total:.2f}万。"
    report += f"期初已使用本品并持续使用的金额为{same_product:.2f}万，占比{same_product/end_total*100:.2f}%；"
    report += f"从同品牌其他产品转换而来的总金额为{same_brand_other:.2f}万，占比{same_brand_other/end_total*100:.2f}%，"
    
    if not same_brand_details.empty:
        details = []
        for i, row in same_brand_details.iterrows():
            details.append(f"主要来源为{row['期初产品']}（金额{row['流量']:.2f}万，占比{row['流量']/end_total*100:.2f}%）")
        report += "、".join(details) + "；"
    else:
        report += "无主要来源产品；"
    
    report += f"从其他品牌产品转换而来的总金额为{other_brand:.2f}万，占比{other_brand/end_total*100:.2f}%，"
    
    if not other_brand_details.empty:
        details = []
        for i, row in other_brand_details.iterrows():
            details.append(f"主要来源为{row['期初产品']}（金额{row['流量']:.2f}万，占比{row['流量']/end_total*100:.2f}%）")
        report += "、".join(details) + "；"
    else:
        report += "无主要来源产品；"
    
    report += f"新增门店带来的金额为{new_stores:.2f}万，占比{new_stores/end_total*100:.2f}%；"
    report += f"新增用户带来的金额为{new_users:.2f}万，占比{new_users/end_total*100:.2f}%。\n\n"    
    return report

# 生成标签汇总报告
def generate_label_summary(marked_data):
    if marked_data is None or marked_data.empty:
        return "无可用数据生成标签汇总报告。"
    
    relevant_data = marked_data[marked_data['标签类别'] != "不涉及目标产品"]
    if relevant_data.empty:
        return "无有效数据生成标签汇总报告。"
    
    total_flow = relevant_data['流量'].sum() / 10000
    
    if total_flow == 0:
        return "总流量为0，无法生成标签汇总报告。"
    
    label_summary = relevant_data.groupby('标签类别')['流量'].sum().reset_index()
    label_summary = label_summary.sort_values(
        by='标签类别', 
        key=lambda x: x.map(label_sort_mapping)
    )
    label_summary['流量'] = label_summary['流量'] / 10000
    label_summary['占比'] = (label_summary['流量'] / total_flow) * 100
    
    gain_labels = ["期初_新增", "期初_不同品牌不同产品", "期初_同品牌不同产品"]
    lost_labels = ["期末_同品牌不同产品", "期末_不同品牌不同产品", "期末_流失"]
    remain_label = "同品牌同产品"
    
    gain_value = label_summary[label_summary['标签类别'].isin(gain_labels)]['占比'].sum()
    lost_value = label_summary[label_summary['标签类别'].isin(lost_labels)]['占比'].sum()
    remain_value = label_summary[label_summary['标签类别'] == remain_label]['占比'].sum() if remain_label in label_summary['标签类别'].values else 0
    
    lost_ratio_base_start = lost_value / (lost_value + remain_value) * 100 if (lost_value + remain_value) > 0 else 0
    gain_ratio_base_end = gain_value / (gain_value + remain_value) * 100 if (gain_value + remain_value) > 0 else 0
    start_end_comparison = (gain_value + remain_value) / (lost_value + remain_value) if (lost_value + remain_value) > 0 else 0
    
    report = "标签流量汇总分析\n\n"
    report += f"总流量为{total_flow:.2f}万。"
    
    label_details = []
    for _, row in label_summary.iterrows():
        label = row['标签类别']
        flow = row['流量']
        percentage = row['占比']
        label_details.append(f"{label}的金额为{flow:.2f}万，占比{percentage:.2f}%")
    
    report += "、".join(label_details) + "。\n\n"
    
    report += "核心指标分析：\n"
    report += f"- Gain值（新增（新增+流入）：{gain_value:.2f}%\n"
    report += f"- Lost值（流出+流失）：{lost_value:.2f}%\n"
    report += f"- Remain值（留存）：{remain_value:.2f}%\n"
    report += f"- 以期初为基准的Lost占比：{lost_ratio_base_start:.2f}%\n"
    report += f"- 以期末为基准的Gain占比：{gain_ratio_base_end:.2f}%\n"
    report += f"- 期初期末对比值：{start_end_comparison:.2f}倍"
    
    return report

# 标题
st.title("产品品牌流量分析工具（报告版）")

# 历史快照管理
with st.expander("历史分析快照", expanded=True):
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("快照包含分析结果和可视化图表，关闭浏览器后不会丢失")
    with col2:
        if st.button("清空所有快照"):
            if st.session_state.history_snapshots:
                st.session_state.history_snapshots = []
                save_snapshots_to_file([])
                st.success("已清空所有历史快照")
                st.rerun()
            else:
                st.info("没有快照可清空")
    
    # 显示快照列表
    if not st.session_state.history_snapshots:
        st.info("暂无分析快照，请先进行分析并生成结果")
    else:
        for idx, snapshot in enumerate(reversed(st.session_state.history_snapshots)):
            meta = snapshot["metadata"]
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{snapshot['timestamp'].strftime('%Y-%m-%d %H:%M')}** - {meta['start_period']}至{meta['end_period']} - {meta['product']}")
            with col2:
                if st.button("查看", key=f"view_{idx}_{snapshot['id']}", help=f"查看快照 {snapshot['id'][-6:]}"):
                    with st.spinner(f"正在加载快照 {snapshot['id'][-6:]}..."):
                        load_success = load_from_snapshot(snapshot['id'])
                        if load_success:
                            st.success(f"已加载快照 {snapshot['id'][-6:]}")
                            st.rerun()
                        else:
                            st.error(f"加载快照 {snapshot['id'][-6:]} 失败")
            with col3:
                if st.button("删除", key=f"del_{idx}_{snapshot['id']}", help=f"删除快照 {snapshot['id'][-6:]}"):
                    delete_success = delete_snapshot(snapshot['id'])
                    if delete_success:
                        st.success(f"已删除快照 {snapshot['id'][-6:]}")
                        st.rerun()
                    else:
                        st.error(f"删除快照 {snapshot['id'][-6:]} 失败")

# 文件上传
uploaded_file = st.file_uploader("上传Excel数据文件", type=["xlsx", "xls"])

if uploaded_file is not None:
    st.session_state.uploaded_file_processed = True
    
    df = pd.read_excel(uploaded_file)
    st.session_state.original_df = df.copy()
    
    # 检查必要列
    required_columns = ['Q', 'Passport_id', 'Value', 'product_st_new', 'brand']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        st.error(f"缺少必要的列: {', '.join(missing_columns)}")
        st.stop()
    
    q_values = sorted(df['Q'].unique().tolist())
    
    # 产品-品牌映射
    brand_mapping = df[['product_st_new', 'brand']].drop_duplicates().rename(
        columns={'product_st_new': '产品', 'brand': '品牌'}
    )
    st.session_state.brand_mapping = brand_mapping
    
    # 检查未匹配品牌的产品
    missing_brand_products = brand_mapping[brand_mapping['品牌'].isna() | (brand_mapping['品牌'] == '')]
    if not missing_brand_products.empty:
        st.warning(f"发现 {len(missing_brand_products)} 个产品未匹配到品牌信息")
    
    # 可用产品列表
    special_tags = ["新增门店", "门店流失", "产品流失", "新增产品", "其他产品"]
    available_products = [p for p in brand_mapping['产品'].unique() 
                         if p not in special_tags and pd.notna(p)]
    
    # 参数设置
    st.subheader("分析参数设置")
    col1, col2, col3 = st.columns(3)
    with col1:
        start_period = st.selectbox("选择期初", q_values, index=0)
        end_period = st.selectbox("选择期末", q_values, index=min(1, len(q_values)-1))
        st.session_state.start_period = start_period
        st.session_state.end_period = end_period
        
        if start_period == end_period:
            st.error("期初和期末不能相同，请重新选择")
            st.stop()
    
    with col2:
        if available_products:
            st.session_state.selected_product = st.selectbox(
                "选择要分析的产品", 
                available_products,
                index=0 if len(available_products) > 0 else None
            )
            
            product_brand = brand_mapping[
                brand_mapping['产品'] == st.session_state.selected_product
            ]['品牌'].values[0] if st.session_state.selected_product in brand_mapping['产品'].values else "未知品牌"
            
            st.info(f"对应品牌: {product_brand}")
        else:
            st.warning("未找到可用产品数据")
    
    with col3:
        use_full_products = st.checkbox("全量输出所有产品", value=False)
        if not use_full_products:
            top_n = st.slider("展示的Top N产品数量", 5, 20, 10)
        else:
            st.slider("展示的Top N产品数量（全量模式禁用）", 5, 20, 10, disabled=True)
        
        generate_data = st.button("生成流量数据并分析")
    
    if generate_data and st.session_state.selected_product:
        with st.spinner("正在处理数据..."):
            # 数据处理逻辑
            if 'Value U' not in df.columns:
                df = df.rename(columns={'Value': 'Value U'})
            df['product_processed'] = df['product_st_new']
            
            # 计算流向数据
            flow_results = []
            for passport_id, group in df.groupby('Passport_id'):
                has_start = start_period in group['Q'].values
                has_end = end_period in group['Q'].values
                
                # 新增用户
                if not has_start and has_end:
                    product_data = group[group['Q'] == end_period].groupby('product_processed')['Value U'].sum().reset_index()
                    for _, row in product_data.iterrows():
                        flow_results.append({
                            '期初产品': "新增门店",
                            '期末产品': row['product_processed'],
                            '流量': row['Value U']
                        })
                    continue
                
                # 流失用户
                if has_start and not has_end:
                    product_data = group[group['Q'] == start_period].groupby('product_processed')['Value U'].sum().reset_index()
                    for _, row in product_data.iterrows():
                        flow_results.append({
                            '期初产品': row['product_processed'],
                            '期末产品': "门店流失",
                            '流量': row['Value U']
                        })
                    continue
                
                # 既有期初又有期末
                if has_start and has_end:
                    start_data = group[group['Q'] == start_period].copy()
                    end_data = group[group['Q'] == end_period].copy()
                    
                    start_agg = start_data.groupby('product_processed')['Value U'].sum().reset_index()
                    end_agg = end_data.groupby('product_processed')['Value U'].sum().reset_index()
                    
                    start_dict = {row['product_processed']: row['Value U'] for _, row in start_agg.iterrows()}
                    end_dict = {row['product_processed']: row['Value U'] for _, row in end_agg.iterrows()}
                    
                    # 相同产品留存
                    same_products = set(start_dict.keys()) & set(end_dict.keys())
                    for product in same_products:
                        flow = min(start_dict[product], end_dict[product])
                        flow_results.append({
                            '期初产品': product,
                            '期末产品': product,
                            '流量': flow
                        })
                        start_dict[product] -= flow
                        end_dict[product] -= flow
                        if start_dict[product] == 0: del start_dict[product]
                        if end_dict[product] == 0: del end_dict[product]
                    
                    # 不同产品转换
                    remaining_start = list(start_dict.items())
                    remaining_end = list(end_dict.items())
                    
                    while remaining_start and remaining_end:
                        (s_product, s_val) = remaining_start[0]
                        (e_product, e_val) = remaining_end[0]
                        
                        flow = min(s_val, e_val)
                        flow_results.append({
                            '期初产品': s_product,
                            '期末产品': e_product,
                            '流量': flow
                        })
                        
                        if s_val == flow:
                            remaining_start.pop(0)
                        else:
                            remaining_start[0] = (s_product, s_val - flow)
                        
                        if e_val == flow:
                            remaining_end.pop(0)
                        else:
                            remaining_end[0] = (e_product, e_val - flow)
                    
                    # 剩余流失
                    for (s_product, s_val) in remaining_start:
                        flow_results.append({
                            '期初产品': s_product,
                            '期末产品': "产品流失",
                            '流量': s_val
                        })
                    
                    # 剩余新增
                    for (e_product, e_val) in remaining_end:
                        flow_results.append({
                            '期初产品': "新增产品",
                            '期末产品': e_product,
                            '流量': e_val
                        })
            
            # 合并流量数据
            flow_df = pd.DataFrame(flow_results, columns=['期初产品', '期末产品', '流量'])
            flow_df = flow_df.groupby(['期初产品', '期末产品'], as_index=False)['流量'].sum()
            st.session_state.flow_df = flow_df
            
            # 打标分析
            with st.spinner("正在打标分析..."):
                brand_dict = dict(zip(brand_mapping['产品'], brand_mapping['品牌']))
                marked_df = flow_df.copy()
                
                marked_df['期初品牌'] = marked_df['期初产品'].apply(
                    lambda x: brand_dict.get(x, x) if x not in special_tags else x
                )
                marked_df['期末品牌'] = marked_df['期末产品'].apply(
                    lambda x: brand_dict.get(x, x) if x not in special_tags else x
                )
                
                product_brand = brand_mapping[
                    brand_mapping['产品'] == st.session_state.selected_product
                ]['品牌'].values[0] if st.session_state.selected_product in brand_mapping['产品'].values else "未知品牌"
                
                # 打标函数
                def create_labels(row):
                    if row['期末产品'] == st.session_state.selected_product:
                        if row['期初产品'] in ["新增门店", "新增产品"]:
                            return "期初_新增"
                        
                        start_product = row['期初产品']
                        start_brand = row['期初品牌']
                        
                        if start_product == st.session_state.selected_product and start_brand == product_brand:
                            return "同品牌同产品"
                        elif start_brand == product_brand:
                            return "期初_同品牌不同产品"
                        else:
                            return "期初_不同品牌不同产品"
                    
                    elif row['期初产品'] == st.session_state.selected_product:
                        if row['期末产品'] in ["门店流失", "产品流失"]:
                            return "期末_流失"
                        
                        end_product = row['期末产品']
                        end_brand = row['期末品牌']
                        
                        if end_product == st.session_state.selected_product and end_brand == product_brand:
                            return "同品牌同产品"
                        elif end_brand == product_brand:
                            return "期末_同品牌不同产品"
                        else:
                            return "期末_不同品牌不同产品"
                    
                    else:
                        return "不涉及目标产品"
                
                marked_df['标签类别'] = marked_df.apply(create_labels, axis=1)
                st.session_state.marked_data = marked_df.drop(['期初品牌', '期末品牌'], axis=1)
                
                # 拆分流向 - 完整数据集
                split_flow = []
                for _, row in marked_df.iterrows():
                    if row['标签类别'] != "不涉及目标产品":
                        split_flow.append({
                            '源节点': row['期初产品'],
                            '目标节点': row['标签类别'],
                            '流量': row['流量'],
                            '流向类型': '期初到标签',
                            '标签类别': row['标签类别']
                        })
                        split_flow.append({
                            '源节点': row['标签类别'],
                            '目标节点': row['期末产品'],
                            '流量': row['流量'],
                            '流向类型': '标签到期末',
                            '标签类别': row['标签类别']
                        })
                
                split_flow_df = pd.DataFrame(split_flow)
                if not split_flow_df.empty:
                    split_flow_df = split_flow_df.groupby(
                        ['源节点', '目标节点', '流向类型', '标签类别'], 
                        as_index=False
                    )['流量'].sum()
                    
                    # 排序
                    split_flow_df['sort_key'] = split_flow_df['标签类别'].apply(
                        lambda x: label_sort_mapping.get(x, len(LABEL_ORDER))
                    )
                    sorted_split_df = split_flow_df.sort_values(
                        by=['sort_key', '流量'], 
                        ascending=[True, False]
                    ).drop(columns=['sort_key'])
                    
                    st.session_state.split_flow_data = split_flow_df
                    st.session_state.sorted_split_data = sorted_split_df
                else:
                    st.warning("没有找到涉及目标产品的流量数据")
            
            # 处理期初产品筛选数据
            with st.spinner("正在处理期初产品筛选数据..."):
                if st.session_state.marked_data is not None:
                    start_filtered_data = st.session_state.marked_data[
                        st.session_state.marked_data['期初产品'] == st.session_state.selected_product
                    ]
                    
                    if not start_filtered_data.empty:
                        split_flow_start = []
                        for _, row in start_filtered_data.iterrows():
                            if row['标签类别'] != "不涉及目标产品":
                                split_flow_start.append({
                                    '源节点': row['期初产品'],
                                    '目标节点': row['标签类别'],
                                    '流量': row['流量'],
                                    '流向类型': '期初到标签',
                                    '标签类别': row['标签类别']
                                })
                                split_flow_start.append({
                                    '源节点': row['标签类别'],
                                    '目标节点': row['期末产品'],
                                    '流量': row['流量'],
                                    '流向类型': '标签到期末',
                                    '标签类别': row['标签类别']
                                })
                        
                        split_flow_start_df = pd.DataFrame(split_flow_start)
                        if not split_flow_start_df.empty:
                            split_flow_start_df = split_flow_start_df.groupby(
                                ['源节点', '目标节点', '流向类型', '标签类别'], 
                                as_index=False
                            )['流量'].sum()
                            
                            split_flow_start_df['sort_key'] = split_flow_start_df['标签类别'].apply(
                                lambda x: label_sort_mapping.get(x, len(LABEL_ORDER))
                            )
                            sorted_split_start_df = split_flow_start_df.sort_values(
                                by=['sort_key', '流量'], 
                                ascending=[True, False]
                            ).drop(columns=['sort_key'])
                            
                            st.session_state.split_flow_data_start = split_flow_start_df
                            st.session_state.sorted_split_data_start = sorted_split_start_df
            
            # 处理期末产品筛选数据
            with st.spinner("正在处理期末产品筛选数据..."):
                if st.session_state.marked_data is not None:
                    end_filtered_data = st.session_state.marked_data[
                        st.session_state.marked_data['期末产品'] == st.session_state.selected_product
                    ]
                    
                    if not end_filtered_data.empty:
                        split_flow_end = []
                        for _, row in end_filtered_data.iterrows():
                            if row['标签类别'] != "不涉及目标产品":
                                split_flow_end.append({
                                    '源节点': row['期初产品'],
                                    '目标节点': row['标签类别'],
                                    '流量': row['流量'],
                                    '流向类型': '期初到标签',
                                    '标签类别': row['标签类别']
                                })
                                split_flow_end.append({
                                    '源节点': row['标签类别'],
                                    '目标节点': row['期末产品'],
                                    '流量': row['流量'],
                                    '流向类型': '标签到期末',
                                    '标签类别': row['标签类别']
                                })
                        
                        split_flow_end_df = pd.DataFrame(split_flow_end)
                        if not split_flow_end_df.empty:
                            split_flow_end_df = split_flow_end_df.groupby(
                                ['源节点', '目标节点', '流向类型', '标签类别'], 
                                as_index=False
                            )['流量'].sum()
                            
                            split_flow_end_df['sort_key'] = split_flow_end_df['标签类别'].apply(
                                lambda x: label_sort_mapping.get(x, len(LABEL_ORDER))
                            )
                            sorted_split_end_df = split_flow_end_df.sort_values(
                                by=['sort_key', '流量'], 
                                ascending=[True, False]
                            ).drop(columns=['sort_key'])
                            
                            st.session_state.split_flow_data_end = split_flow_end_df
                            st.session_state.sorted_split_data_end = sorted_split_end_df
            
            # 生成桑基图
            with st.spinner("正在生成可视化图表..."):
                # 计算TopN产品
                all_products = pd.unique(st.session_state.sorted_split_data[['源节点', '目标节点']].values.ravel('K')) if st.session_state.sorted_split_data is not None else []
                product_traffic = {}
                
                for product in all_products:
                    if product not in special_tags and product not in MIDDLE_LAYER_ORDER:
                        source_flow = st.session_state.sorted_split_data[
                            st.session_state.sorted_split_data['源节点'] == product
                        ]['流量'].sum() if st.session_state.sorted_split_data is not None else 0
                        target_flow = st.session_state.sorted_split_data[
                            st.session_state.sorted_split_data['目标节点'] == product
                        ]['流量'].sum() if st.session_state.sorted_split_data is not None else 0
                        product_traffic[product] = source_flow + target_flow
                
                # 选择TopN产品
                if product_traffic and not use_full_products:
                    sorted_products = sorted(product_traffic.items(), key=lambda x: x[1], reverse=True)
                    st.session_state.top_products = [p[0] for p in sorted_products[:top_n]]
                    st.info(f"已选择流量最高的Top {top_n} 产品")
                else:
                    st.session_state.top_products = None
                
                # 生成完整图表
                if st.session_state.sorted_split_data is not None and not st.session_state.sorted_split_data.empty:
                    st.session_state.sankey_fig = generate_sorted_sankey(
                        st.session_state.sorted_split_data,
                        top_products=st.session_state.top_products,
                        use_full_products=use_full_products
                    )
                
                # 生成期初产品筛选图表
                if st.session_state.sorted_split_data_start is not None and not st.session_state.sorted_split_data_start.empty:
                    st.session_state.sankey_fig_start = generate_sorted_sankey(
                        st.session_state.sorted_split_data_start,
                        top_products=st.session_state.top_products,
                        use_full_products=use_full_products
                    )
                
                # 生成期末产品筛选图表
                if st.session_state.sorted_split_data_end is not None and not st.session_state.sorted_split_data_end.empty:
                    st.session_state.sankey_fig_end = generate_sorted_sankey(
                        st.session_state.sorted_split_data_end,
                        top_products=st.session_state.top_products,
                        use_full_products=use_full_products
                    )
            
            # 保存快照
            save_success = save_snapshot(start_period, end_period, st.session_state.selected_product)
            if save_success:
                st.success("分析完成并已保存快照")
            else:
                st.success("分析完成")
    
    # 显示分析结果
    if st.session_state.sorted_split_data is not None and not st.session_state.sorted_split_data.empty:
        # 显示桑基图
        st.subheader("📊 流量可视化图表")
        
        # 完整桑基图
        st.subheader("完整产品流量桑基图")
        if st.session_state.sankey_fig is not None:
            st.plotly_chart(st.session_state.sankey_fig, use_container_width=True, config={'displayModeBar': True})
        else:
            st.warning("无法生成完整桑基图")
        
        # 期初产品筛选桑基图
        if st.session_state.sorted_split_data_start is not None and not st.session_state.sorted_split_data_start.empty:
            st.subheader(f"期初产品 = {st.session_state.selected_product} 的流量桑基图")
            if st.session_state.sankey_fig_start is not None:
                st.plotly_chart(st.session_state.sankey_fig_start, use_container_width=True, config={'displayModeBar': True})
        
        # 期末产品筛选桑基图
        if st.session_state.sorted_split_data_end is not None and not st.session_state.sorted_split_data_end.empty:
            st.subheader(f"期末产品 = {st.session_state.selected_product} 的流量桑基图")
            if st.session_state.sankey_fig_end is not None:
                st.plotly_chart(st.session_state.sankey_fig_end, use_container_width=True, config={'displayModeBar': True})
        
        # 显示报告
        st.subheader("📋 分析报告")
        
        # 生成并显示期末分析报告
        end_report = generate_end_report(st.session_state.marked_data, st.session_state.selected_product)
        st.markdown(end_report)
        
        # 生成并显示期初分析报告
        start_report = generate_start_report(st.session_state.marked_data, st.session_state.selected_product)
        st.markdown(start_report)
        
        # 生成并显示标签汇总报告
        label_report = generate_label_summary(st.session_state.marked_data)
        st.markdown(label_report)
        
        # 下载结果
        st.subheader("💾 下载分析结果")
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            if st.session_state.marked_data is not None:
                st.session_state.marked_data.to_excel(writer, index=False, sheet_name='原始打标数据')
            
            st.session_state.sorted_split_data.drop(columns=['标签类别']).to_excel(
                writer, index=False, sheet_name='完整拆分流向数据'
            )
            
            if st.session_state.sorted_split_data_start is not None and not st.session_state.sorted_split_data_start.empty:
                st.session_state.sorted_split_data_start.drop(columns=['标签类别']).to_excel(
                    writer, index=False, sheet_name='期初产品筛选数据'
                )
            
            if st.session_state.sorted_split_data_end is not None and not st.session_state.sorted_split_data_end.empty:
                st.session_state.sorted_split_data_end.drop(columns=['标签类别']).to_excel(
                    writer, index=False, sheet_name='期末产品筛选数据'
                )
            
            if st.session_state.top_products:
                pd.DataFrame({'TopN产品': st.session_state.top_products}).to_excel(
                    writer, index=False, sheet_name='TopN产品列表'
                )
        
        output.seek(0)
        if st.session_state.selected_product and st.session_state.start_period and st.session_state.end_period:
            st.download_button(
                "下载完整结果（Excel）",
                data=output,
                file_name=f"{st.session_state.start_period}_to_{st.session_state.end_period}_{st.session_state.selected_product}_结果.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        # 当前快照信息
        if st.session_state.current_snapshot_id:
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"当前分析已保存为快照 (ID: {st.session_state.current_snapshot_id[-6:]})")
            with col2:
                if st.button("重新保存快照") and st.session_state.start_period and st.session_state.selected_product:
                    save_success = save_snapshot(st.session_state.start_period, st.session_state.end_period, st.session_state.selected_product)
                    if save_success:
                        st.success("已重新保存快照")
elif uploaded_file is None:
    # 如果有加载的快照，显示结果
    if st.session_state.sorted_split_data is not None and not st.session_state.sorted_split_data.empty:
        st.info("显示已加载的快照数据")
        
        # 显示桑基图
        st.subheader("📊 流量可视化图表")
        
        # 完整桑基图
        st.subheader("完整产品流量桑基图")
        if st.session_state.sankey_fig is not None:
            st.plotly_chart(st.session_state.sankey_fig, use_container_width=True, config={'displayModeBar': True})
        
        # 期初产品筛选桑基图
        if st.session_state.sorted_split_data_start is not None and not st.session_state.sorted_split_data_start.empty:
            st.subheader(f"期初产品 = {st.session_state.selected_product} 的流量桑基图")
            if st.session_state.sankey_fig_start is not None:
                st.plotly_chart(st.session_state.sankey_fig_start, use_container_width=True, config={'displayModeBar': True})
        
        # 期末产品筛选桑基图
        if st.session_state.sorted_split_data_end is not None and not st.session_state.sorted_split_data_end.empty:
            st.subheader(f"期末产品 = {st.session_state.selected_product} 的流量桑基图")
            if st.session_state.sankey_fig_end is not None:
                st.plotly_chart(st.session_state.sankey_fig_end, use_container_width=True, config={'displayModeBar': True})
        
        # 显示报告
        st.subheader("📋 分析报告")
        
        # 生成并显示期末分析报告
        end_report = generate_end_report(st.session_state.marked_data, st.session_state.selected_product)
        st.markdown(end_report)
        
        # 生成并显示期初分析报告
        start_report = generate_start_report(st.session_state.marked_data, st.session_state.selected_product)
        st.markdown(start_report)
        
        # 生成并显示标签汇总报告
        label_report = generate_label_summary(st.session_state.marked_data)
        st.markdown(label_report)
    
    else:
        st.info("请上传包含以下列的数据文件：Passport_id, Value, Q, product_st_new, brand")
