import streamlit as st
import pandas as pd
import numpy as np
import random
from pyecharts import options as opts
from pyecharts.charts import Sankey
from streamlit_echarts import st_pyecharts
import colorsys

# 定义需要校验的token
VALID_TOKEN = "mUo2TJ3PC3pqddAmQ3Wq2ZnxnEjAq1yd"
# 初始化session_state
if 'flow_df' not in st.session_state:
    st.session_state.flow_df = None
if 'source_nodes' not in st.session_state:
    st.session_state.source_nodes = []
if 'target_nodes' not in st.session_state:
    st.session_state.target_nodes = []
if 'selected_sources' not in st.session_state:
    st.session_state.selected_sources = []
if 'selected_targets' not in st.session_state:
    st.session_state.selected_targets = []
if 'start_period' not in st.session_state:
    st.session_state.start_period = None
if 'end_period' not in st.session_state:
    st.session_state.end_period = None
if 'highlight_keyword' not in st.session_state:
    st.session_state.highlight_keyword = "家乐"
if 'show_rank_value' not in st.session_state:
    st.session_state.show_rank_value = True

# 设置页面配置
st.set_page_config(
    page_title="品牌流量桑基图分析",
    page_icon="📊",
    layout="wide"
)


# 标题
st.title("品牌流量桑基图分析工具")

# 参数设置区域
st.subheader("分析参数设置")
param_col1, param_col2 = st.columns(2)

# 文件上传区域
with param_col1:
    uploaded_file = st.file_uploader("请上传Excel格式的数据文件（.xlsx）", type=["xlsx"])

# 如果上传了文件，则进行后续参数设置
if uploaded_file is not None:
    # 读取数据以获取Q的可能值
    df = pd.read_excel(uploaded_file)
    if 'Q' not in df.columns:
        st.error("上传的文件缺少必要的'Q'列")
        st.stop()
    
    # 获取Q的唯一值并排序
    q_values = sorted(df['Q'].unique().tolist())
    
    with param_col1:
        # 期初和期末选择
        col1, col2 = st.columns(2)
        with col1:
            start_period = st.selectbox("选择期初", q_values, index=0)
            st.session_state.start_period = start_period
        with col2:
            end_period = st.selectbox("选择期末", q_values, index=min(1, len(q_values)-1))
            st.session_state.end_period = end_period
        
        # 确保期初不等于期末
        if start_period == end_period:
            st.error("期初和期末不能选择相同的值，请重新选择")
            st.stop()
    
    with param_col2:
        # 其他参数设置
        highlight_keyword = st.text_input("节点高亮关键词", "家乐")
        st.session_state.highlight_keyword = highlight_keyword
        
        top_n_brands = st.slider("保留Top N品牌数量", 5, 20, 10)
        
        show_rank_value = st.checkbox("在节点标签中显示排名和数值", value=True)
        st.session_state.show_rank_value = show_rank_value
        
        # 生成桑基图按钮
        generate_chart = st.button("生成桑基图")
    
    # 当点击生成按钮时进行处理
    if generate_chart:
        with st.spinner("正在读取和处理数据..."):
            # 统一Value U列名
            if 'Value U' not in df.columns and 'Value' in df.columns:
                df = df.rename(columns={'Value': 'Value U'})
            
            # 检查必要的列是否存在
            required_columns = ['brand', 'Value U', 'Passport_id', 'Q']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                st.error(f"上传的文件缺少必要的列: {', '.join(missing_columns)}")
                st.stop()
            
            # 处理品牌列：聚合Value U并保留Top N品牌，统一品牌名称格式
            df['brand_clean'] = df['brand'].str.strip().str.lower()
            brand_values = df.groupby('brand_clean')['Value U'].sum().reset_index()
            brand_values_sorted = brand_values.sort_values('Value U', ascending=False)
            top_brands = brand_values_sorted.head(top_n_brands)['brand_clean'].tolist()
            df['brand_processed'] = df['brand_clean'].apply(lambda x: x if x in top_brands else '其他品牌')
            
            st.success(f"已处理品牌列，保留Top {top_n_brands}品牌，其余归为'其他品牌'")
        
        # 计算流向数据
        with st.spinner("正在计算流向数据..."):
            flow_results = []
            
            for passport_id, group in df.groupby('Passport_id'):
                has_start = start_period in group['Q'].values
                has_end = end_period in group['Q'].values
                
                # 场景1：只有期末
                if not has_start and has_end:
                    brand_data = group[group['Q'] == end_period].groupby('brand_processed')['Value U'].sum().reset_index()
                    for _, row in brand_data.iterrows():
                        flow_results.append({
                            '起始点': f"期初_新增门店",
                            '目标点': f"期末_{row['brand_processed']}",
                            '流量': row['Value U']
                        })
                    continue
                
                # 场景2：只有期初
                if has_start and not has_end:
                    brand_data = group[group['Q'] == start_period].groupby('brand_processed')['Value U'].sum().reset_index()
                    for _, row in brand_data.iterrows():
                        flow_results.append({
                            '起始点': f"期初_{row['brand_processed']}",
                            '目标点': f"期末_门店流失",
                            '流量': row['Value U']
                        })
                    continue
                
                # 场景3：既有期初又有期末
                if has_start and has_end:
                    start_data = group[group['Q'] == start_period].groupby('brand_processed')['Value U'].sum().reset_index()
                    end_data = group[group['Q'] == end_period].groupby('brand_processed')['Value U'].sum().reset_index()
                    
                    start_dict = dict(zip(start_data['brand_processed'], start_data['Value U']))
                    end_dict = dict(zip(end_data['brand_processed'], end_data['Value U']))
                    
                    # 1. 相同品牌优先匹配
                    common_brands = set(start_dict.keys()) & set(end_dict.keys())
                    remaining_start = start_dict.copy()
                    remaining_end = end_dict.copy()
                    
                    for brand in common_brands:
                        flow = min(start_dict[brand], end_dict[brand])
                        flow_results.append({
                            '起始点': f"期初_{brand}",
                            '目标点': f"期末_{brand}",
                            '流量': flow
                        })
                        remaining_start[brand] -= flow
                        remaining_end[brand] -= flow
                        if remaining_start[brand] == 0:
                            del remaining_start[brand]
                        if remaining_end[brand] == 0:
                            del remaining_end[brand]
                    
                    # 2. 不同品牌随机匹配剩余量
                    start_remaining = list(remaining_start.items())
                    end_remaining = list(remaining_end.items())
                    
                    while start_remaining and end_remaining:
                        brand1, val1 = start_remaining[0]
                        brand2, val2 = random.choice(end_remaining)
                        
                        flow = min(val1, val2)
                        flow_results.append({
                            '起始点': f"期初_{brand1}",
                            '目标点': f"期末_{brand2}",
                            '流量': flow
                        })
                        
                        if val1 == flow:
                            start_remaining.pop(0)
                        else:
                            start_remaining[0] = (brand1, val1 - flow)
                            
                        idx = end_remaining.index((brand2, val2))
                        if val2 == flow:
                            end_remaining.pop(idx)
                        else:
                            end_remaining[idx] = (brand2, val2 - flow)
                    
                    # 3. 处理最终余量
                    for brand, value in start_remaining:
                        flow_results.append({
                            '起始点': f"期初_{brand}",
                            '目标点': f"期末_品类流失",
                            '流量': value
                        })
                    
                    for brand, value in end_remaining:
                        flow_results.append({
                            '起始点': f"期初_新增品类",
                            '目标点': f"期末_{brand}",
                            '流量': value
                        })
            
            st.session_state.flow_df = pd.DataFrame(flow_results, columns=['起始点', '目标点', '流量'])
            st.success("流向数据计算完成")
            
            st.session_state.source_nodes = st.session_state.flow_df['起始点'].unique().tolist()
            st.session_state.target_nodes = st.session_state.flow_df['目标点'].unique().tolist()
            
            st.session_state.selected_sources = st.session_state.source_nodes
            st.session_state.selected_targets = st.session_state.target_nodes
    
    if st.session_state.flow_df is not None and not st.session_state.flow_df.empty:
        required_flow_columns = ['起始点', '目标点', '流量']
        missing_flow_cols = [col for col in required_flow_columns if col not in st.session_state.flow_df.columns]
        if missing_flow_cols:
            st.error(f"流向数据缺少必要的列: {', '.join(missing_flow_cols)}")
            st.stop()
        
        # 节点筛选区域
        st.subheader("节点筛选")
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            selected_sources = st.multiselect(
                "选择要显示的期初节点",
                st.session_state.source_nodes,
                default=st.session_state.selected_sources
            )
            st.session_state.selected_sources = selected_sources
        with filter_col2:
            selected_targets = st.multiselect(
                "选择要显示的期末节点",
                st.session_state.target_nodes,
                default=st.session_state.selected_targets
            )
            st.session_state.selected_targets = selected_targets
        
        filtered_flow_df = st.session_state.flow_df[
            st.session_state.flow_df['起始点'].isin(st.session_state.selected_sources) & 
            st.session_state.flow_df['目标点'].isin(st.session_state.selected_targets)
        ]
        
        if filtered_flow_df.empty:
            st.warning("筛选后没有数据，请调整筛选条件")
        else:
            with st.spinner("正在生成桑基图..."):
                aggregated_df = filtered_flow_df.groupby(['起始点', '目标点'], as_index=False)['流量'].sum()
                
                source_nodes_unique = aggregated_df['起始点'].unique().tolist()
                target_nodes_unique = aggregated_df['目标点'].unique().tolist()
                
                source_flow = aggregated_df.groupby('起始点')['流量'].sum().reset_index()
                source_flow.columns = ['节点', '总流量']
                source_flow_sorted = source_flow.sort_values('总流量', ascending=False).reset_index(drop=True)
                sorted_source_nodes = source_flow_sorted['节点'].tolist()
                
                target_flow = aggregated_df.groupby('目标点')['流量'].sum().reset_index()
                target_flow.columns = ['节点', '总流量']
                target_flow_sorted = target_flow.sort_values('总流量', ascending=False).reset_index(drop=True)
                sorted_target_nodes = target_flow_sorted['节点'].tolist()
                
                all_nodes = sorted_source_nodes + sorted_target_nodes
                node_indices = {node: idx for idx, node in enumerate(all_nodes)}
                
                # 生成节点颜色
                highlight_nodes = [node for node in all_nodes if st.session_state.highlight_keyword in str(node).lower()]
                
                def generate_clear_blue_variations(n):
                    clear_blues = []
                    for i in range(n):
                        hue = 0.58
                        saturation = 0.3 + (i % 3) * 0.1
                        value = 0.9 + (i % 5) * 0.03
                        r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
                        clear_blues.append(f"rgb({int(r*255)}, {int(g*255)}, {int(b*255)})")
                    return clear_blues
                
                highlight_colors = generate_clear_blue_variations(len(highlight_nodes))
                node_color_map = {node: color for node, color in zip(highlight_nodes, highlight_colors)}
                
                # 准备节点数据
                nodes = []
                node_colors = []
                for i, node in enumerate(all_nodes):
                    if "期初_" in node:
                        node_name = node.replace("期初_", "")
                        if st.session_state.show_rank_value:
                            rank = source_flow_sorted[source_flow_sorted['节点'] == node].index[0] + 1
                            flow = source_flow_sorted[source_flow_sorted['节点'] == node]['总流量'].values[0] / 10000
                            label = f"S{rank}. {node_name}\n({flow:.1f}万)"
                        else:
                            label = node_name
                    elif "期末_" in node:
                        node_name = node.replace("期末_", "")
                        if st.session_state.show_rank_value:
                            rank = target_flow_sorted[target_flow_sorted['节点'] == node].index[0] + 1
                            flow = target_flow_sorted[target_flow_sorted['节点'] == node]['总流量'].values[0] / 10000
                            label = f"T{rank}. {node_name}\n({flow:.1f}万)"
                        else:
                            label = node_name
                    else:
                        label = node
                    
                    # 设置节点颜色
                    color = node_color_map.get(node, "#dcebff")
                    nodes.append({"name": label})
                    node_colors.append(color)
                
                # 准备链接数据
                links = []
                for _, row in aggregated_df.iterrows():
                    source_idx = node_indices[row['起始点']]
                    target_idx = node_indices[row['目标点']]
                    value = row['流量']
                    links.append({"source": source_idx, "target": target_idx, "value": value})
                
                # 创建桑基图
                sankey = (
                    Sankey(init_opts=opts.InitOpts(width="1200px", height="800px"))
                    .add(
                        series_name="",
                        nodes=[{"name": node["name"], "itemStyle": {"color": color}} 
                              for node, color in zip(nodes, node_colors)],
                        links=links,
                        linestyle_opt=opts.LineStyleOpts(opacity=0.7, curve=0.5, color="source"),
                        label_opts=opts.LabelOpts(position="right", font_size=12),
                        node_gap=10,
                        node_width=20,
                    )
                    .set_global_opts(
                        title_opts=opts.TitleOpts(
                            title=f"品牌流量桑基图（{start_period} → {end_period}）- 筛选后",
                            pos_left="center",
                            title_textstyle_opts=opts.TextStyleOpts(font_size=16),
                        ),
                        tooltip_opts=opts.TooltipOpts(trigger="item", formatter="{b}: {c}"),
                    )
                )
                
                st.success("桑基图生成完成")
            
            try:
                st.subheader(f"品牌流量桑基图（{st.session_state.start_period} → {st.session_state.end_period}）")
                st_pyecharts(sankey, height="800px")
            except Exception as e:
                st.error(f"渲染桑基图时出错: {str(e)}")
                st.write("节点数量:", len(nodes))
                st.write("链接数量:", len(links))
                st.write("示例节点:", nodes[:3])
                st.write("示例链接:", links[:3])
            
            # 其余的数据分析和下载功能保持不变...
            # ...（此处省略流量占比计算和品牌分析部分代码）...

else:
    st.info("请上传数据文件以开始分析（支持Excel格式）")
