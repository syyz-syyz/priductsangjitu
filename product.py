import streamlit as st
import pandas as pd
import numpy as np
import random
from pyecharts import options as opts
from pyecharts.charts import Sankey
from streamlit_echarts import st_pyecharts
import colorsys

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
    layout="wide"  # 使用宽布局增加空间
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
            df['brand_clean'] = df['brand'].str.strip().str.lower()  # 清洗品牌名称
            brand_values = df.groupby('brand_clean')['Value U'].sum().reset_index()
            brand_values_sorted = brand_values.sort_values('Value U', ascending=False)
            top_brands = brand_values_sorted.head(top_n_brands)['brand_clean'].tolist()
            df['brand_processed'] = df['brand_clean'].apply(lambda x: x if x in top_brands else '其他品牌')
            
            st.success(f"已处理品牌列，保留Top {top_n_brands}品牌，其余归为'其他品牌'")
        
        # 计算流向数据
        with st.spinner("正在计算流向数据..."):
            flow_results = []
            
            # 按Passport_id分组处理
            for passport_id, group in df.groupby('Passport_id'):
                # 检查是否有期初和期末数据
                has_start = start_period in group['Q'].values
                has_end = end_period in group['Q'].values
                
                # 场景1：只有期末（期末有值，期初无值）
                if not has_start and has_end:
                    # 所有品牌都来自期初_新增门店
                    brand_data = group[group['Q'] == end_period].groupby('brand_processed')['Value U'].sum().reset_index()
                    for _, row in brand_data.iterrows():
                        flow_results.append({
                            '起始点': f"期初_新增门店",
                            '目标点': f"期末_{row['brand_processed']}",
                            '流量': row['Value U']
                        })
                    continue
                
                # 场景2：只有期初（期初有值，期末无值）
                if has_start and not has_end:
                    # 所有品牌流向期末_门店流失
                    brand_data = group[group['Q'] == start_period].groupby('brand_processed')['Value U'].sum().reset_index()
                    for _, row in brand_data.iterrows():
                        flow_results.append({
                            '起始点': f"期初_{row['brand_processed']}",
                            '目标点': f"期末_门店流失",
                            '流量': row['Value U']
                        })
                    continue
                
                # 场景3：既有期初又有期末（处理完整流向）
                if has_start and has_end:
                    # 按品牌聚合期初和期末的数据
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
                        # 更新剩余量
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
                        
                        # 更新剩余量
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
                    # 期初剩余量流向期末_品类流失
                    for brand, value in start_remaining:
                        flow_results.append({
                            '起始点': f"期初_{brand}",
                            '目标点': f"期末_品类流失",
                            '流量': value
                        })
                    
                    # 期末剩余量来自期初_新增品类
                    for brand, value in end_remaining:
                        flow_results.append({
                            '起始点': f"期初_新增品类",
                            '目标点': f"期末_{brand}",
                            '流量': value
                        })
            
            # 确保flow_df包含正确的列名
            st.session_state.flow_df = pd.DataFrame(flow_results, columns=['起始点', '目标点', '流量'])
            st.success("流向数据计算完成")
            
            # 保存节点信息
            st.session_state.source_nodes = st.session_state.flow_df['起始点'].unique().tolist()
            st.session_state.target_nodes = st.session_state.flow_df['目标点'].unique().tolist()
            
            # 初始化选择
            st.session_state.selected_sources = st.session_state.source_nodes
            st.session_state.selected_targets = st.session_state.target_nodes
    
    # 只有当有数据时才显示筛选和图表
    if st.session_state.flow_df is not None and not st.session_state.flow_df.empty:
        # 验证必要的列是否存在
        required_flow_columns = ['起始点', '目标点', '流量']
        missing_flow_cols = [col for col in required_flow_columns if col not in st.session_state.flow_df.columns]
        if missing_flow_cols:
            st.error(f"流向数据缺少必要的列: {', '.join(missing_flow_cols)}")
            st.stop()
        
        # 添加节点筛选区域
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
        
        # 应用筛选
        filtered_flow_df = st.session_state.flow_df[
            st.session_state.flow_df['起始点'].isin(st.session_state.selected_sources) & 
            st.session_state.flow_df['目标点'].isin(st.session_state.selected_targets)
        ]
        
        # 如果筛选后没有数据
        if filtered_flow_df.empty:
            st.warning("筛选后没有数据，请调整筛选条件")
        else:
            # 生成桑基图（基于筛选后的数据）
            with st.spinner("正在生成桑基图..."):
                # 确保聚合时使用正确的列名
                aggregated_df = filtered_flow_df.groupby(['起始点', '目标点'], as_index=False)['流量'].sum()
                
                # 分离源节点和目标节点
                source_nodes_unique = aggregated_df['起始点'].unique().tolist()
                target_nodes_unique = aggregated_df['目标点'].unique().tolist()
                
                # 分别按流量排序
                # 源节点按流出流量排序（降序）
                source_flow = aggregated_df.groupby('起始点')['流量'].sum().reset_index()
                source_flow.columns = ['节点', '总流量']
                source_flow_sorted = source_flow.sort_values('总流量', ascending=False).reset_index(drop=True)
                sorted_source_nodes = source_flow_sorted['节点'].tolist()
                
                # 目标节点按流入流量排序（降序）
                target_flow = aggregated_df.groupby('目标点')['流量'].sum().reset_index()
                target_flow.columns = ['节点', '总流量']
                target_flow_sorted = target_flow.sort_values('总流量', ascending=False).reset_index(drop=True)
                sorted_target_nodes = target_flow_sorted['节点'].tolist()
                
                # 合并节点列表（左侧源节点 + 右侧目标节点）
                all_nodes = sorted_source_nodes + sorted_target_nodes
                
                # 创建节点索引映射
                node_indices = {node: idx for idx, node in enumerate(all_nodes)}
                
                # 高亮指定关键词的节点
                highlight_nodes = [node for node in all_nodes if st.session_state.highlight_keyword in str(node).lower()]
                
                # 生成清晰的蓝色系颜色变化
                def generate_clear_blue_variations(n):
                    clear_blues = []
                    for i in range(n):
                        hue = 0.58  # 蓝色色相
                        saturation = 0.3 + (i % 3) * 0.1  # 适中饱和度
                        value = 0.9 + (i % 5) * 0.03  # 高明度
                        r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
                        clear_blues.append(f"rgba({int(r*255)}, {int(g*255)}, {int(b*255)}, 0.8)")  # 轻微透明
                    return clear_blues
                
                # 生成清晰的蓝色系颜色
                highlight_colors = generate_clear_blue_variations(len(highlight_nodes))
                node_color_map = {node: color for node, color in zip(highlight_nodes, highlight_colors)}
                
                # 准备节点数据
                nodes = []
                base_clear_blue = "rgba(220, 235, 255, 0.8)"  # 基础浅蓝色
                
                # 源节点
                for i, node in enumerate(sorted_source_nodes):
                    flow = source_flow_sorted[source_flow_sorted['节点'] == node]['总流量'].values[0] / 10000
                    node_name = node.replace("期初_", "")
                    if st.session_state.show_rank_value:
                        label = f"S{i+1}. {node_name} ({flow:.1f}万)"
                    else:
                        label = f"{node_name}"
                    
                    nodes.append({
                        "name": node,
                        "label": {"show": True, "formatter": label},
                        "itemStyle": {"color": node_color_map.get(node, base_clear_blue)}
                    })
                
                # 目标节点
                for i, node in enumerate(sorted_target_nodes):
                    flow = target_flow_sorted[target_flow_sorted['节点'] == node]['总流量'].values[0] / 10000
                    node_name = node.replace("期末_", "")
                    if st.session_state.show_rank_value:
                        label = f"T{i+1}. {node_name} ({flow:.1f}万)"
                    else:
                        label = f"{node_name}"
                    
                    nodes.append({
                        "name": node,
                        "label": {"show": True, "formatter": label},
                        "itemStyle": {"color": node_color_map.get(node, base_clear_blue)}
                    })
                
                # 准备链接数据
                links = []
                for _, row in aggregated_df.iterrows():
                    src = row['起始点']
                    tar = row['目标点']
                    value = row['流量']
                    
                    # 确定链接颜色
                    if src in node_color_map:
                        link_color = node_color_map[src]
                    elif tar in node_color_map:
                        link_color = node_color_map[tar]
                    else:
                        link_color = "rgba(220, 235, 255, 0.5)"  # 非高亮链接颜色
                    
                    links.append({
                        "source": src,
                        "target": tar,
                        "value": value,
                        "lineStyle": {"color": link_color, "opacity": 0.7}
                    })
                
                # 创建桑基图
                sankey = (
                    Sankey(init_opts=opts.InitOpts(width="1400px", height=f"{max(len(sorted_source_nodes), len(sorted_target_nodes)) * 50 + 200}px"))
                    .add(
                        series_name="",
                        nodes=nodes,
                        links=links,
                        pos_left="15%",
                        pos_right="15%",
                        focus_node_adjacency=True,
                        node_align="justify",
                        layout_iterations=0,  # 禁用自动布局
                        linestyle_opt=opts.LineStyleOpts(opacity=0.3, curve=0.5, color="source"),
                        label_opts=opts.LabelOpts(
                            position="right",
                            font_size=12,
                            font_family="Microsoft YaHei",
                            color="rgb(30, 30, 30)"
                        ),
                        tooltip_opts=opts.TooltipOpts(
                            trigger="item",
                            formatter="""
                            {b}<br/>
                            流量: {c} ({d}%)
                            """
                        ),
                    )
                    .set_global_opts(
                        title_opts=opts.TitleOpts(
                            title=f"品牌流量桑基图（{start_period} → {end_period}）- 筛选后",
                            pos_left="center",
                            title_textstyle_opts=opts.TextStyleOpts(
                                font_family="Microsoft YaHei",
                                font_size=16,
                                color="rgb(30, 30, 30)"
                            )
                        ),
                        tooltip_opts=opts.TooltipOpts(trigger="item"),
                    )
                )
                
                st.success("桑基图生成完成")
            
            # 显示桑基图
            st.subheader(f"品牌流量桑基图（{st.session_state.start_period} → {st.session_state.end_period}）")
            st_pyecharts(sankey, height=max(len(sorted_source_nodes), len(sorted_target_nodes)) * 50 + 200)
            
            # 计算并显示流量占比数据（基于筛选后的数据）
            with st.spinner("正在计算流量占比数据..."):
                # 创建字典用于快速查找每个源节点和目标节点的总流量
                source_total_flow = dict(zip(source_flow['节点'], source_flow['总流量']))
                target_total_flow = dict(zip(target_flow['节点'], target_flow['总流量']))
                
                # 按源节点分组，计算每个目标节点的流量占比
                result = []
                
                # 遍历每个源节点
                for source in sorted_source_nodes:
                    # 筛选出该源节点的所有流出数据
                    source_data = aggregated_df[aggregated_df['起始点'] == source]
                    
                    # 计算总流量
                    total_source = source_total_flow[source]
                    
                    # 存储该源节点的所有流向信息
                    flow_info = {
                        '源节点': source,
                        '源节点总流量': total_source / 10000,  # 转换为万单位
                        '流向分布': []
                    }
                    
                    # 遍历每个目标节点，计算占比
                    for _, row in source_data.iterrows():
                        # 确保使用正确的列名
                        target = row['目标点']
                        flow = row['流量']
                        total_target = target_total_flow[target]
                        
                        # 计算占比（保留两位小数）
                        pct_source = round((flow / total_source) * 100, 2)  # 占期初比
                        pct_target = round((flow / total_target) * 100, 2)  # 占期末比
                        
                        flow_info['流向分布'].append({
                            '目标节点': target,
                            '流量': flow / 10000,  # 转换为万单位
                            '占期初比(%)': pct_source,
                            '占期末比(%)': pct_target
                        })
                    
                    # 按占比降序排序
                    flow_info['流向分布'].sort(key=lambda x: x['占期初比(%)'], reverse=True)
                    result.append(flow_info)
                
                # 转换为DataFrame以便更好地查看
                rows = []
                for item in result:
                    for flow in item['流向分布']:
                        rows.append({
                            '源节点': item['源节点'],
                            '源节点总流量(万)': item['源节点总流量'],
                            '目标节点': flow['目标节点'],
                            '流量(万)': flow['流量'],
                            '占期初比(%)': flow['占期初比(%)'],
                            '占期末比(%)': flow['占期末比(%)']
                        })
                
                percentage_df = pd.DataFrame(rows)
                st.success("流量占比数据计算完成")
            
            # 显示流量占比数据（主要输出）
            st.subheader("流量占比详细数据（筛选后）")
            st.dataframe(percentage_df)
            
            # 生成品牌分析报告
            st.subheader("品牌流量分析报告")
            
            # 提取筛选后的品牌（仅包含选中的节点）
            filtered_brands = []
            
            # 从筛选的源节点中提取品牌
            for node in st.session_state.selected_sources:
                if "期初_" in node:
                    brand = node.split("_", 1)[1]
                    if brand not in ["新增门店", "新增品类", "门店流失", "品类流失", "其他品牌"]:
                        filtered_brands.append(brand)
            
            # 从筛选的目标节点中提取品牌
            for node in st.session_state.selected_targets:
                if "期末_" in node:
                    brand = node.split("_", 1)[1]
                    if brand not in ["新增门店", "新增品类", "门店流失", "品类流失", "其他品牌"] and brand not in filtered_brands:
                        filtered_brands.append(brand)
            
            # 确保按节点顺序排序（源节点顺序优先）
            sorted_brands = []
            # 首先添加源节点中的品牌（按源节点顺序）
            for node in sorted_source_nodes:
                if "期初_" in node:
                    brand = node.split("_", 1)[1]
                    if brand in filtered_brands and brand not in sorted_brands:
                        sorted_brands.append(brand)
            
            # 然后添加仅在目标节点中的品牌（按目标节点顺序）
            for node in sorted_target_nodes:
                if "期末_" in node:
                    brand = node.split("_", 1)[1]
                    if brand in filtered_brands and brand not in sorted_brands:
                        sorted_brands.append(brand)
            
            # 为每个筛选后的品牌生成分析报告（按排序后的顺序）
            for brand in sorted_brands:
                # 1. 品牌A的期初分析
                start_node = f"期初_{brand}"
                if start_node in source_total_flow and start_node in st.session_state.selected_sources:
                    start_total = source_total_flow[start_node] / 10000  # 转换为万单位
                    st.write(f"**{brand} 期初分析**")
                    
                    # 筛选该品牌的所有流向
                    brand_flows = percentage_df[percentage_df['源节点'] == start_node]
                    
                    # 保留的数据
                    retain_flow = 0
                    retain_pct = 0
                    # 转换到其他品牌的数据
                    convert_flows = []
                    # 流失数据（细分门店流失和品类流失）
                    store_loss_flow = 0  # 门店流失
                    store_loss_pct = 0
                    category_loss_flow = 0  # 品类流失
                    category_loss_pct = 0
                    
                    for _, row in brand_flows.iterrows():
                        target = row['目标节点']
                        if f"期末_{brand}" == target and target in st.session_state.selected_targets:
                            retain_flow = row['流量(万)']
                            retain_pct = row['占期初比(%)']
                        elif "期末_门店流失" == target and target in st.session_state.selected_targets:
                            store_loss_flow = row['流量(万)']
                            store_loss_pct = row['占期初比(%)']
                        elif "期末_品类流失" == target and target in st.session_state.selected_targets:
                            category_loss_flow = row['流量(万)']
                            category_loss_pct = row['占期初比(%)']
                        elif "期末_" in target and target in st.session_state.selected_targets:
                            target_brand = target.split("_", 1)[1]
                            if target_brand != brand:
                                convert_flows.append({
                                    'brand': target_brand,
                                    'flow': row['流量(万)'],
                                    'pct': row['占期初比(%)']
                                })
                    
                    # 生成期初分析文本
                    report_text = f"{brand}，期初金额{start_total:.1f}万，"
                    report_text += f"期末仍旧使用{brand}的金额{retain_flow:.1f}万，占比{retain_pct}%；"
                    
                    # 添加转换到其他品牌的信息
                    for cf in convert_flows[:3]:  # 只显示前3个主要转换
                        report_text += f"转换为{cf['brand']}的金额{cf['flow']:.1f}万，占比{cf['pct']}%；"
                    
                    # 明确区分门店流失和品类流失
                    report_text += f"门店流失金额{store_loss_flow:.1f}万，占比{store_loss_pct}%；"
                    report_text += f"品类流失金额{category_loss_flow:.1f}万，占比{category_loss_pct}%；"
                    
                    st.write(report_text)
                
                # 2. 品牌A的期末分析
                end_node = f"期末_{brand}"
                target_total = target_flow_sorted[target_flow_sorted['节点'] == end_node]['总流量'].values[0] / 10000 if (end_node in target_flow_sorted['节点'].values and end_node in st.session_state.selected_targets) else 0
                
                if target_total > 0:
                    st.write(f"**{brand} 期末分析**")
                    
                    # 筛选流向该品牌的所有来源
                    brand_inflows = percentage_df[percentage_df['目标节点'] == end_node]
                    
                    # 保留的数据（来自同一品牌）
                    retain_flow = 0
                    retain_pct = 0
                    # 从其他品牌转换来的数据
                    convert_flows = []
                    # 新增数据（细分新增门店和新增品类）
                    new_store_flow = 0  # 新增门店
                    new_store_pct = 0
                    new_category_flow = 0  # 新增品类
                    new_category_pct = 0
                    
                    # 计算总流入量
                    total_inflow = brand_inflows['流量(万)'].sum()
                    
                    for _, row in brand_inflows.iterrows():
                        source = row['源节点']
                        if f"期初_{brand}" == source and source in st.session_state.selected_sources:
                            retain_flow = row['流量(万)']
                            retain_pct = row['占期末比(%)']
                        elif "期初_新增门店" == source and source in st.session_state.selected_sources:
                            new_store_flow = row['流量(万)']
                            new_store_pct = row['占期末比(%)']
                        elif "期初_新增品类" == source and source in st.session_state.selected_sources:
                            new_category_flow = row['流量(万)']
                            new_category_pct = row['占期末比(%)']
                        elif "期初_" in source and source in st.session_state.selected_sources:
                            source_brand = source.split("_", 1)[1]
                            if source_brand != brand:
                                convert_flows.append({
                                    'brand': source_brand,
                                    'flow': row['流量(万)'],
                                    'pct': row['占期末比(%)']
                                })
                    
                    # 生成期末分析文本
                    report_text = f"{brand}，期末金额{target_total:.1f}万，"
                    report_text += f"来自期初{brand}的金额{retain_flow:.1f}万，占比{retain_pct:.2f}%；"
                    
                    # 添加从其他品牌转换来的信息
                    for cf in convert_flows[:3]:  # 只显示前3个主要来源
                        report_text += f"从{cf['brand']}转换来的金额{cf['flow']:.1f}万，占比{cf['pct']:.2f}%；"
                    
                    # 明确区分新增门店和新增品类
                    report_text += f"新增门店金额{new_store_flow:.1f}万，占比{new_store_pct:.2f}%；"
                    report_text += f"新增品类金额{new_category_flow:.1f}万，占比{new_category_pct:.2f}%；"
                    
                    st.write(report_text)
                
                st.write("---")  # 分隔线
            
            # 提供数据下载功能
            st.subheader("数据下载（筛选后）")
            download_col1, download_col2 = st.columns(2)
            
            with download_col1:
                # 流向数据下载（转换为万单位）
                flow_for_download = filtered_flow_df.copy()
                flow_for_download['流量'] = flow_for_download['流量'] / 10000
                flow_for_download = flow_for_download.rename(columns={'流量': '流量(万)'})
                flow_csv = flow_for_download.to_csv(index=False)
                st.download_button(
                    label="下载筛选后的流向数据",
                    data=flow_csv,
                    file_name=f"筛选后_桑基图流向数据_{st.session_state.start_period}_to_{st.session_state.end_period}.csv",
                    mime="text/csv",
                )
            
            with download_col2:
                # 流量占比数据下载
                percentage_csv = percentage_df.to_csv(index=False)
                st.download_button(
                    label="下载筛选后的流量占比数据",
                    data=percentage_csv,
                    file_name=f"筛选后_桑基图流量占比数据_{st.session_state.start_period}_to_{st.session_state.end_period}.csv",
                    mime="text/csv",
                )
else:
    st.info("请上传数据文件以开始分析（支持Excel格式）")
