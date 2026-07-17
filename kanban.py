import streamlit as st
import pandas as pd
import os
import datetime
from streamlit_echarts import st_echarts



# 不在这里清空缓存，避免每次启动都重新加载
st.set_page_config(page_title="电量数据看板", layout="wide", initial_sidebar_state="expanded")

# -------------------------- 全局深色CSS（多选框高度加大，避免重叠） --------------------------
style_str = """
    <style>
        /* ---------- 全局深色基础 ---------- */
        .stApp {
            background-color: #0f1730 !important;
            color: #ffffff !important;
        }
        .main .block-container {
            background-color: #0f1730 !important;
            padding-top: 0.8rem !important;
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
            padding-bottom: 1rem !important;
        }
        header[data-testid="stHeader"] {
            background-color: #0f1730 !important;
        }
        section[data-testid="stSidebar"] {
            background-color: #0b1026 !important;
            border-right: 1px solid #242e52 !important;
        }
        section[data-testid="stSidebar"] * {
            color: #ffffff !important;
        }
        .stRadio label {
            color: #ffffff !important;
            font-weight: 700;
            padding: 10px 16px;
            border-radius: 8px;
        }
        .stRadio label:hover {
            background-color: #1a2347 !important;
        }
        h1, h2, h3, p, span {
            color: #ffffff !important;
            font-weight: 700;
        }
        h1 {
            margin-top: 0 !important;
        }

        /* ---------- 标签文字亮色 ---------- */
        .stMultiSelect label,
        .stSelectbox label,
        .stNumberInput label,
        .stSlider label {
            color: #ffffff !important;
            font-weight: 600;
            display:block;
        }

        /* ---------- 单选下拉框深色底+白字 ---------- */
        div[data-baseweb="select"] > div:first-child {
            background-color: #172040 !important;
            border: 1px solid #2c3860 !important;
            border-radius: 8px !important;
            min-height: 42px !important;
            color: #ffffff !important;
        }
        div[data-baseweb="select"] input {
            color: #ffffff !important;
        }
        div[data-baseweb="select"] input::placeholder {
            color: #ffffff !important;
            opacity: 0.85 !important;
        }
        div[data-baseweb="select"] ul {
            background-color: #172040 !important;
            border: 1px solid #2c3860 !important;
        }
        div[data-baseweb="select"] li {
            color: #ffffff !important;
        }
        div[data-baseweb="select"] li:hover {
            background-color: #242e52 !important;
            color: #ffffff !important;
        }

        /* ---------- 多选下拉框（高度加大，避免重叠，内部滚动，标签可见） ---------- */
        /* 外层容器固定高度，加下边距防止重叠 */
        div[data-testid="stMultiSelect"] {
            height: 68px !important;
            min-height: 68px !important;
            max-height: 68px !important;
            overflow: visible !important;
            margin-bottom: 8px !important;   /* 与下方元素保持距离 */
        }

        /* baseweb 组件容器填满高度 */
        div[data-testid="stMultiSelect"] > div[data-baseweb="multiselect"] {
            height: 100% !important;
        }

        /* 选择框主体（显示标签的区域） */
        div[data-testid="stMultiSelect"] > div[data-baseweb="multiselect"] > div:first-child {
            height: 100% !important;
            max-height: 100% !important;
            display: flex !important;
            flex-wrap: nowrap !important;
            align-items: center !important;
            background-color: #172040 !important;
            border: 1px solid #2c3860 !important;
            border-radius: 8px !important;
            padding: 0 8px !important;
            overflow: hidden !important;
        }

        /* 标签容器（包裹所有已选标签）—— 可滚动，高度适应 */
        div[data-testid="stMultiSelect"] > div[data-baseweb="multiselect"] > div:first-child > div:nth-child(2) {
            flex: 1 1 auto !important;
            max-height: 56px !important;     /* 比外层略小，留出上下边距 */
            overflow-y: auto !important;
            overflow-x: hidden !important;
            display: flex !important;
            flex-wrap: wrap !important;
            align-content: flex-start !important;
            gap: 4px !important;
            padding: 2px 0 !important;
        }

        /* 每个标签的样式（确保白色文字可见） */
        div[data-testid="stMultiSelect"] span[data-baseweb="tag"] {
            background-color: #2a3a6a !important;
            color: #ffffff !important;
            border-radius: 4px !important;
            padding: 0 8px !important;
            height: 24px !important;
            display: inline-flex !important;
            align-items: center !important;
            font-size: 13px !important;
            white-space: nowrap !important;
        }

        /* 标签中的文字 */
        div[data-testid="stMultiSelect"] span[data-baseweb="tag"] * {
            color: #ffffff !important;
        }

        /* 删除按钮（小叉）颜色，确保可见且可点击 */
        div[data-testid="stMultiSelect"] span[data-baseweb="tag"] svg {
            fill: #cccccc !important;
            color: #cccccc !important;
            pointer-events: auto !important;  /* 确保可点击 */
        }
        div[data-testid="stMultiSelect"] span[data-baseweb="tag"] button {
            background: transparent !important;
            border: none !important;
            padding: 0 2px !important;
            cursor: pointer !important;
        }

        /* 输入框占位文字颜色 */
        div[data-baseweb="multiselect"] input {
            color: #ffffff !important;
        }
        div[data-baseweb="multiselect"] input::placeholder {
            color: rgba(255,255,255,0.7) !important;
        }

        /* 下拉选项列表（弹出菜单）固定高度，可滚动 */
        div[data-baseweb="multiselect"] ul {
            max-height: 200px !important;
            overflow-y: auto !important;
            background-color: #172040 !important;
            border: 1px solid #2c3860 !important;
        }
        div[data-baseweb="multiselect"] li {
            color: #ffffff !important;
            padding: 6px 12px !important;
        }
        div[data-baseweb="multiselect"] li:hover {
            background-color: #242e52 !important;
        }

        /* 已选项标签上的小圆点删除按钮样式微调 */
        div[data-baseweb="multiselect"] span[role="button"] {
            background-color: transparent !important;
            color: #fff !important;
        }

        /* ---------- 数字输入框深色 ---------- */
        .stNumberInput input {
            background-color: #172040 !important;
            border: 1px solid #2c3860 !important;
            border-radius: 8px !important;
            min-height: 42px !important;
            max-height: 42px !important;
            color: #ffffff !important;
        }
        .stNumberInput input::placeholder {
            color: #ffffff !important;
            opacity: 0.85 !important;
        }
        .stNumberInput button {
            background-color: #242e52 !important;
            border: 1px solid #34456b !important;
            color: #ffffff !important;
        }
        .stNumberInput button:hover {
            background-color: #34456b !important;
        }

        /* ---------- 按钮/导出按钮深色 ---------- */
        .stButton button,
        .stDownloadButton button {
            background: linear-gradient(135deg, #204275, #3a6ebf) !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600;
        }
        .stButton button:hover,
        .stDownloadButton button:hover {
            background: linear-gradient(135deg, #2c5288, #4c7fcf) !important;
            color: #ffffff !important;
        }

        /* ---------- 指标卡片深色 ---------- */
        div[data-testid="stMetric"] {
            background: rgba(23, 32, 64, 0.88) !important;
            backdrop-filter: blur(10px);
            padding: 18px 20px;
            border-radius: 14px;
            border-left: 4px solid #5993ff;
            box-shadow: 0 4px 24px rgba(0,0,0,0.4) !important;
        }
        div[data-testid="stMetric"] div[data-testid="stMetricLabel"] {
            color: #ffffff !important;
            font-size: 14px;
            font-weight: 600;
        }
        div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
            color: #ffffff !important;
            font-size: 28px;
            font-weight: 700;
        }

        /* ---------- 警告提示深色 ---------- */
        .stWarning {
            background-color: #282640 !important;
            color: #ffffff !important;
        }
        .stWarning svg {
            color: #ffd54f !important;
            fill: #ffd54f !important;
        }

        /* ---------- 24时段表格紧凑深色 ---------- */
        .stDataFrame {
            background-color: #121a38 !important;
            border-radius: 10px !important;
            border: 1px solid #242e52 !important;
            overflow: hidden !important;
        }
        .stDataFrame table {
            border-collapse: collapse !important;
            width: 100% !important;
        }
        .stDataFrame thead tr th {
            background-color: #1c274d !important;
            color: #ffffff !important;
            font-weight: 700;
            font-size: 13px;
            padding: 8px 10px;
            border-right: 1px solid #242e52 !important;
            border-bottom: 1px solid #242e52 !important;
        }
        .stDataFrame tbody tr td {
            background-color: #121a38 !important;
            color: #e0e8ff !important;
            font-size: 12.5px;
            padding: 6px 10px;
            border-right: 1px solid #242e52 !important;
            border-bottom: 1px solid #242e52 !important;
        }
        .stDataFrame tbody tr:nth-child(even) td {
            background-color: #141d40 !important;
        }
        .stDataFrame tbody tr:hover td {
            background-color: #1a254a !important;
        }
        div[data-testid="stDataFrame-container"] {
            padding: 0 !important;
            margin: 0 !important;
        }

        /* ---------- 滑块轨道深色 ---------- */
        .stSlider > div[data-testid="stSliderTrack"] {
            background-color: #242e52 !important;
        }
        .stSlider > div[data-testid="stSliderThumb"] {
            background-color: #5993ff !important;
        }

        /* ---------- 折叠器深色样式 ---------- */
        .streamlit-expanderHeader {
            background-color: #172040 !important;
            color: #ffffff !important;
            border: 1px solid #2c3860;
            border-radius: 8px;
        }
        .streamlit-expanderContent {
            background-color: #0f1730 !important;
            color: #ffffff !important;
            border: 1px solid #2c3860;
            border-top: none;
            border-radius: 0 0 8px 8px;
        }

        /* ---------- 图标统一白色 ---------- */
        svg, svg * {
            color: #ffffff !important;
            fill: #ffffff !important;
            stroke: #ffffff !important;
        }

        hr {
            border-color: #242e52 !important;
        }
    </style>
"""
st.markdown(style_str, unsafe_allow_html=True)

st.markdown("""
<script>
document.addEventListener('DOMContentLoaded', function() {
    var monthNames = ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月'];
    var weekDayNames = ['日', '一', '二', '三', '四', '五', '六'];

    function translateDatePicker() {
        var dateInputs = document.querySelectorAll('[data-baseweb="datepicker"]');
        dateInputs.forEach(function(picker) {
            var elements = picker.querySelectorAll('div, span');
            elements.forEach(function(el) {
                monthNames.forEach(function(cn, idx) {
                    var en = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'][idx];
                    if (el.textContent && el.textContent.includes(en)) {
                        el.textContent = el.textContent.replace(en, cn);
                    }
                });
                weekDayNames.forEach(function(cn, idx) {
                    var en = ['S', 'M', 'T', 'W', 'T', 'F', 'S'][idx];
                    if (el.textContent && el.textContent === en) {
                        el.textContent = cn;
                    }
                });
            });
        });
    }

    translateDatePicker();

    var observer = new MutationObserver(function() {
        translateDatePicker();
    });
    observer.observe(document.body, { childList: true, subtree: true });
});
</script>
""", unsafe_allow_html=True)

# -------------------------- 文件路径配置 --------------------------
# 获取当前脚本所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

FILE_ELEC = os.path.join(DATA_DIR, "月电量.xlsx")
FILE_PRICE = os.path.join(DATA_DIR, "市场均价.xlsx")
FILE_GRID_PRICE = os.path.join(DATA_DIR, "国网代购.xlsx")
FILE_DAY_ELEC = os.path.join(DATA_DIR, "2026日用电量.xlsx")

# -------------------------- 缓存加载函数 --------------------------
@st.cache_data
def load_grid_price(file_path):
    price_data = {}
    sheet_map = {"陕西电网": "Sheet1", "榆林电网": "Sheet2"}
    for area_name, sheet_name in sheet_map.items():
        price_data[area_name] = {}
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        current_month = None
        current_type = None
        for _, row in df.iterrows():
            if pd.isna(row[0]) and pd.isna(row[2]):
                continue
            if isinstance(row[0], str) and "2026年" in str(row[0]):
                month_str = str(row[0]).split("2026年")[1].replace("月", "")
                current_month = int(month_str)
                price_data[area_name][current_month] = {}
            if not pd.isna(row[1]):
                current_type = str(row[1]).strip()
                price_data[area_name][current_month][current_type] = {}
            if not pd.isna(row[2]) and current_month and current_type:
                voltage = str(row[2]).strip()
                price_data[area_name][current_month][current_type][voltage] = {
                    "flat_total": float(row[3]),
                    "purchase_price": float(row[4]) if not pd.isna(row[4]) else 0,
                    "line_loss": float(row[5]) if not pd.isna(row[5]) else 0,
                    "trans_price": float(row[6]),
                    "system_fee": float(row[7]),
                    "gov_fee": float(row[8]),
                    "sharp_price": float(row[9]),
                    "peak_price": float(row[10]),
                    "flat_price": float(row[11]),
                    "valley_price": float(row[12]),
                    "cap_max": float(row[13]) if not pd.isna(row[13]) else 0,
                    "cap_trans": float(row[14]) if not pd.isna(row[14]) else 0
                }
    return price_data


@st.cache_data
def load_market_price(file_path):
    price_dict = {}
    if os.path.exists(file_path):
        price_df = pd.read_excel(file_path, sheet_name='Sheet1')
        period_col = price_df.columns[0]
        price_df.set_index(period_col, inplace=True)
        for col in price_df.columns:
            month_num = int(col.split('月')[0])
            price_dict[month_num] = [
                0.0 if pd.isna(x) else float(x) for x in price_df[col].tolist()
            ]
    return price_dict


@st.cache_data
def load_day_elec(file_path):
    if not os.path.exists(file_path):
        return None
    df = pd.read_excel(file_path, sheet_name='24点用电量')
    df['日期'] = pd.to_datetime(df['日期'])
    df['年月'] = df['日期'].dt.strftime('%Y-%m')
    df['月份'] = df['日期'].dt.month
    return df


@st.cache_data
def load_month_elec(file_path):
    if not os.path.exists(file_path):
        return None
    df = pd.read_excel(file_path, sheet_name='Sheet1')
    df['日期'] = pd.to_datetime(df['日期'].astype(str) + '-01')
    df['年月'] = df['日期'].dt.strftime('%Y-%m')
    df['月份'] = df['日期'].dt.month
    return df


@st.cache_data
def get_daily_total(day_df, start_date, end_date, user_tuple):
    mask_date = (day_df['日期'] >= pd.Timestamp(start_date)) & (day_df['日期'] <= pd.Timestamp(end_date))
    if user_tuple:
        mask_user = day_df['名称'].isin(user_tuple)
    else:
        mask_user = True
    filtered = day_df.loc[mask_date & mask_user]
    if filtered.empty:
        return pd.DataFrame(columns=['日期', '总用电量'])
    daily = filtered.groupby('日期')['总用电量'].sum().reset_index()
    return daily.sort_values('日期')


@st.cache_data
def sample_daily_data(daily_df, max_points=300):
    if len(daily_df) <= max_points:
        return daily_df
    step = len(daily_df) // max_points
    return daily_df.iloc[::step]


@st.cache_data
def filter_month_elec(df_elec, date_range, user_tuple):
    start_date, end_date = date_range
    start_month = f"{start_date.year}-{str(start_date.month).zfill(2)}"
    end_month = f"{end_date.year}-{str(end_date.month).zfill(2)}"
    mask_month = (df_elec['年月'] >= start_month) & (df_elec['年月'] <= end_month)
    filtered = df_elec[mask_month & (df_elec['名称'].isin(user_tuple))]
    hist_data = df_elec[mask_month]
    return filtered, hist_data


@st.cache_data
def filter_by_date_range(df_day, date_range, user_tuple):
    start_date, end_date = date_range
    mask_date = (df_day['日期'] >= pd.Timestamp(start_date)) & (df_day['日期'] <= pd.Timestamp(end_date))
    mask_user = df_day['名称'].isin(user_tuple)
    filtered_day = df_day[mask_date & mask_user]
    hist_day = df_day[mask_date]

    period_cols = [f"段{i}" for i in range(1, 25)]

    filtered = filtered_day.groupby(['名称', '户号', '年月'])[period_cols + ['总用电量']].sum().reset_index()
    filtered['月份'] = filtered['年月'].str.split('-').str[1].astype(int)

    hist_data = hist_day.groupby(['名称', '户号', '年月'])[period_cols + ['总用电量']].sum().reset_index()
    hist_data['月份'] = hist_data['年月'].str.split('-').str[1].astype(int)

    return filtered, hist_data


# 加载数据
grid_price = None
market_price_dict = {}
if os.path.exists(FILE_GRID_PRICE):
    grid_price = load_grid_price(FILE_GRID_PRICE)
else:
    st.error("❌ 未找到国网代购.xlsx，请检查D盘路径")

if os.path.exists(FILE_PRICE):
    market_price_dict = load_market_price(FILE_PRICE)

df_elec = load_month_elec(FILE_ELEC)
df_day = load_day_elec(FILE_DAY_ELEC)

# 电量模块用的价格字典（年月字符串key）
price_dict_str = {}
for m, vals in market_price_dict.items():
    price_dict_str[f"2026-{m:02d}"] = vals


# -------------------------- 24时段峰平谷划分工具函数 --------------------------
def get_period_type_map(month_sel):
    p_type = {}
    # 谷段 1-6、12-14
    for i in range(1, 7):
        p_type[i] = "谷段"
    for i in range(12, 15):
        p_type[i] = "谷段"
    # 平段7-11、15-16、24
    for i in range(7, 12):
        p_type[i] = "平段"
    for i in range(15, 17):
        p_type[i] = "平段"
    p_type[24] = "平段"
    # 高峰17-23
    for i in range(17, 24):
        p_type[i] = "高峰"
    # 尖峰覆盖
    if month_sel in [1, 12]:
        p_type[19] = "尖峰"
        p_type[20] = "尖峰"
    elif month_sel in [7, 8]:
        p_type[20] = "尖峰"
        p_type[21] = "尖峰"
    return p_type


# -------------------------- 侧边导航栏 --------------------------
with st.sidebar:
    st.markdown("### 📌 导航")
    menu = st.radio("", ["⚡ 电量数据模块", "💰 价格测算模块"], index=0, label_visibility="collapsed")
    st.markdown("---")
    st.caption("筛选参数在右侧主面板")

# ===================== 模块一：电量数据模块 =====================
if menu == "⚡ 电量数据模块":
    st.title("电量数据看板")
    if df_day is None:
        st.error("❌ 日用电量数据文件缺失，检查路径")
        st.stop()

    all_user = sorted(df_day['名称'].unique())
    min_date = df_day['日期'].min().date()
    max_date = df_day['日期'].max().date()

    if len(df_day) > 50000:
        st.warning(f"⚠️ 当前日用电量数据量较大({len(df_day):,}行)，建议缩短日期范围以提升性能")
    col_date1, col_date2, col_user = st.columns([1, 1, 1], gap="medium")
    with col_date1:
        filter_start_date = st.date_input("📅 起始日期", min_date, min_value=min_date, max_value=max_date,
                                          key="filter_start")
    with col_date2:
        filter_end_date = st.date_input("📅 结束日期", max_date, min_value=min_date, max_value=max_date,
                                        key="filter_end")
    with col_user:
        sel_user = st.multiselect("👤 选择用户", all_user, default=[], key="user_select")

    if filter_start_date > filter_end_date:
        st.error("起始日期不能晚于结束日期")
        st.stop()

    sel_user_final = sel_user if sel_user else all_user
    filtered, hist_data = filter_by_date_range(df_day, (filter_start_date, filter_end_date), tuple(sel_user_final))

    with st.expander("📋 筛选明细", expanded=False):
        if not filtered.empty:
            display_df = filtered[['名称', '户号', '年月', '总用电量']]
            max_rows = 500
            if len(display_df) > max_rows:
                st.warning(f"数据量较大({len(display_df):,}行)，仅显示前{max_rows}行")
                display_df = display_df.head(max_rows)
            st.dataframe(display_df, width="stretch")
        else:
            st.info("暂无匹配数据")

    st.markdown("---")
    total_all = hist_data['总用电量'].sum() if not hist_data.empty else 0
    total_sel = filtered['总用电量'].sum() if not filtered.empty else 0
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric("全部用户总电量", f"{total_all:,.2f} MWh")
    with col_m2:
        st.metric("选中用户总电量", f"{total_sel:,.2f} MWh")

    # 分时图表
    st.subheader("📈 分时用电量 & 市场均价")
    price_chart_type = st.radio("均价显示", ["柱状", "折线"], index=0, horizontal=True, key="price_chart_type",
                                label_visibility="collapsed")
    if not filtered.empty:
        period_cols = [f"段{i}" for i in range(1, 25)]
        group_month = filtered.groupby("年月")[period_cols].sum().reset_index()
        x_axis = [f"段{i}" for i in range(1, 25)]
        series = []
        legend = []
        color_e = ['#4fc3f7', '#81c784', '#4dd0e1', '#ba68c8', '#64b5f6']
        color_p = ['#ff8a65', '#ffb74d', '#f06292', '#aed581', '#ffd54f']
        for idx, row in group_month.iterrows():
            m = row['年月']
            series.append({
                "name": f"{m} 用电", "type": "line", "smooth": True, "symbol": "circle", "symbolSize": 6,
                "lineStyle": {"width": 3}, "data": row[period_cols].tolist(), "yAxisIndex": 0,
                "itemStyle": {"color": color_e[idx % len(color_e)]}
            })
            legend.append(f"{m} 用电")
            if m in price_dict_str:
                if price_chart_type == "柱状":
                    series.append({
                        "name": f"{m} 均价", "type": "bar", "barWidth": "40%",
                        "data": price_dict_str[m], "yAxisIndex": 1,
                        "itemStyle": {"color": color_p[idx % len(color_p)]}
                    })
                else:
                    series.append({
                        "name": f"{m} 均价", "type": "line", "smooth": True, "symbol": "circle", "symbolSize": 6,
                        "data": price_dict_str[m], "yAxisIndex": 1,
                        "itemStyle": {"color": color_p[idx % len(color_p)]},
                        "lineStyle": {"width": 2, "type": "dashed"}
                    })
                legend.append(f"{m} 均价")
        opt_main = {
            "backgroundColor": "#121a38",
            "tooltip": {"trigger": "axis", "textStyle": {"color": "#fff"}},
            "legend": {"data": legend, "textStyle": {"color": "#fff"}, "top": 0},
            "toolbox": {
                "left": "center",
                "bottom": 8,
                "textStyle": {"color": "#ffffff"},
                "feature": {
                    "dataZoom": {"yAxisIndex": "none"},
                    "restore": {"title": "重置"},
                    "saveAsImage": {"title": "下载图片"}
                }
            },
            "grid": {"left": "5%", "right": "6%", "bottom": "22%", "top": "20%", "containLabel": True},
            "xAxis": {"type": "category", "data": x_axis, "axisLabel": {"color": "#fff", "rotate": 30},
                      "axisLine": {"lineStyle": {"color": "#2c3860"}}, "splitLine": {"show": False}},
            "yAxis": [
                {"type": "value", "name": "用电量(MWh)", "nameTextStyle": {"color": "#fff"},
                 "axisLabel": {"color": "#fff"}, "splitLine": {"lineStyle": {"color": "#2c3860", "type": "dashed"}}},
                {"type": "value", "name": "均价(元/MWh)", "nameTextStyle": {"color": "#ff8a65"},
                 "axisLabel": {"color": "#ff8a65"}, "splitLine": {"show": False}, "position": "right"}
            ],
            "dataZoom": [{"type": "slider", "height": 16, "bottom": 10, "textStyle": {"color": "#fff"}}],
            "series": series
        }
        st_echarts(opt_main, height="480px")
    else:
        st.info("筛选无数据，无法展示曲线")

    st.caption("提示：底部工具栏可重置视图、下载图表")

    # ===================== 峰平谷环形图 & 用户条形图 =====================
    st.markdown("---")
    col_pie, col_bar = st.columns([1, 1], gap="large")
    if not hist_data.empty:
        user_sum = hist_data.groupby("名称")["总用电量"].sum().reset_index()
        chart_h = max(420, len(user_sum) * 35)
    else:
        chart_h = 420

    # ========= 峰平谷环形图 =========
    with col_pie:
        st.subheader("🥧 峰平谷用电量占比")
        st.caption("谷0-6/11-14 | 平6-11/14-16/23-24 | 高峰16-23")
        if not filtered.empty:
            p_cols = [f"段{i}" for i in range(1, 25)]
            total_p = filtered[p_cols].sum()
            m_list = filtered['月份'].unique()
            has_summer = any(x in [7, 8] for x in m_list)
            has_winter = any(x in [1, 12] for x in m_list)
            valley = total_p[["段1", "段2", "段3", "段4", "段5", "段6", "段12", "段13", "段14"]].sum()
            flat = total_p[["段7", "段8", "段9", "段10", "段11", "段15", "段16", "段24"]].sum()
            peak_all = total_p[["段17", "段18", "段19", "段20", "段21", "段22", "段23"]].sum()
            s_peak, w_peak, normal_peak = 0, 0, peak_all
            if has_summer:
                s_peak = total_p[["段20", "段21"]].sum()
                normal_peak -= s_peak
            if has_winter:
                w_peak = total_p[["段19", "段20"]].sum()
                normal_peak -= w_peak

            pie_data = []
            if valley > 0:
                pie_data.append({"name": "谷段", "value": round(valley, 2)})
            if flat > 0:
                pie_data.append({"name": "平段", "value": round(flat, 2)})
            if normal_peak > 0:
                pie_data.append({"name": "常规高峰", "value": round(normal_peak, 2)})
            if s_peak > 0:
                pie_data.append({"name": "夏季尖峰", "value": round(s_peak, 2)})
            if w_peak > 0:
                pie_data.append({"name": "冬季尖峰", "value": round(w_peak, 2)})

            pie_color = []
            for item in pie_data:
                if item["name"] == "谷段":
                    pie_color.append("#4fc3f7")
                elif item["name"] == "平段":
                    pie_color.append("#81c784")
                elif item["name"] == "常规高峰":
                    pie_color.append("#ffb74d")
                elif item["name"] == "夏季尖峰":
                    pie_color.append("#f06292")
                elif item["name"] == "冬季尖峰":
                    pie_color.append("#ba68c8")

            pie_opt = {
                "backgroundColor": "#121a38",
                "tooltip": {
                    "trigger": "item",
                    "textStyle": {"color": "#fff"},
                    "formatter": "{b}: {c} MWh ({d}%)"
                },
                "legend": {"textStyle": {"color": "#fff"}, "left": "left"},
                "series": [{
                    "type": "pie",
                    "radius": ["40%", "70%"],
                    "data": pie_data,
                    "color": pie_color,
                    "label": {
                        "color": "#fff",
                        "formatter": "{b}\n{c} MWh ({d}%)",
                        "show": True
                    }
                }]
            }
            st_echarts(pie_opt, height=f"{chart_h}px")
        else:
            st.info("无数据")

    # ========= 用户用电量横向条形图（最终修复：标签显示电量+百分比，tooltip简化） =========
    with col_bar:
        st.subheader("📊 当月全部用户用电量排名")
        if not hist_data.empty:
            user_total = hist_data.groupby("名称")["总用电量"].sum().reset_index().sort_values("总用电量",
                                                                                               ascending=True)
            total_sum = user_total["总用电量"].sum()
            bar_data = []
            for _, row in user_total.iterrows():
                val = round(row["总用电量"], 2)
                pct = (val / total_sum * 100) if total_sum > 0 else 0
                pct_round = round(pct, 1)
                bar_data.append({
                    "value": val,
                    "percent": pct_round,
                    "label": {
                        "show": True,
                        "position": "right",
                        "color": "#fff",
                        "formatter": f"{val} MWh ({pct_round}%)"
                    }
                })
            bar_opt = {
                "backgroundColor": "#121a38",
                "tooltip": {
                    "trigger": "axis",
                    "textStyle": {"color": "#fff"},
                    "formatter": "{b}<br/>电量: {c} MWh"  # 仅显示名称和电量，百分比已在标签中展示
                },
                "grid": {"left": "18%", "right": "18%", "bottom": "5%", "top": "5%", "containLabel": True},
                "xAxis": {"type": "value", "axisLabel": {"color": "#fff"}},
                "yAxis": {"type": "category", "data": user_total["名称"].tolist(), "axisLabel": {"color": "#fff"}},
                "series": [{
                    "type": "bar",
                    "data": bar_data,
                    "barWidth": "60%",
                    "itemStyle": {
                        "color": {
                            "type": "linear",
                            "x": 0, "y": 0, "x2": 1, "y2": 0,
                            "colorStops": [
                                {"offset": 0, "color": "#2a5caa"},
                                {"offset": 1, "color": "#5993ff"}
                            ]
                        },
                        "borderRadius": [0, 4, 4, 0]
                    }
                }]
            }
            st_echarts(bar_opt, height=f"{chart_h}px")
        else:
            st.info("当月无用户数据")

    # ===================== 每日总用电量趋势图（带独立筛选器，使用缓存） =====================
    st.markdown("---")
    st.subheader("📅 每日总用电量趋势")

    if df_day is not None and not df_day.empty:
        min_date = df_day['日期'].min().date()
        max_date = df_day['日期'].max().date()
        day_users = sorted(df_day['名称'].unique())

        col_f1, col_f2 = st.columns([1, 1])
        with col_f1:
            start_date = st.date_input("起始日期", min_date, min_value=min_date, max_value=max_date, key="day_start")
            end_date = st.date_input("结束日期", max_date, min_value=min_date, max_value=max_date, key="day_end")
            if start_date > end_date:
                st.error("起始日期不能晚于结束日期")
                st.stop()
        with col_f2:
            day_sel_users = st.multiselect("选择用户（日用电量）", day_users, default=[], key="day_users")

        daily_total = get_daily_total(df_day, start_date, end_date, tuple(day_sel_users) if day_sel_users else ())

        if not daily_total.empty:
            original_count = len(daily_total)
            sampled_total = sample_daily_data(daily_total, max_points=300)
            sampled_count = len(sampled_total)

            if sampled_count < original_count:
                st.warning(f"⚠️ 数据量较大({original_count}条)，已采样至{sampled_count}条以优化性能")

            weekday_map = {0: '周一', 1: '周二', 2: '周三', 3: '周四', 4: '周五', 5: '周六', 6: '周日'}
            x_axis = []
            for date_val in sampled_total['日期']:
                if isinstance(date_val, pd.Timestamp):
                    dt = date_val
                elif isinstance(date_val, (datetime.date, datetime.datetime)):
                    dt = pd.Timestamp(date_val)
                else:
                    dt = pd.Timestamp(str(date_val))
                x_axis.append(f"{dt.strftime('%m-%d')} {weekday_map[dt.weekday()]}")
            y_data = sampled_total['总用电量'].round(2).tolist()

            day_chart_opt = {
                "backgroundColor": "#121a38",
                "tooltip": {
                    "trigger": "axis",
                    "textStyle": {"color": "#fff"},
                    "formatter": "{b}<br/>总用电量: {c} MWh"
                },
                "grid": {"left": "5%", "right": "5%", "bottom": "12%", "top": "10%", "containLabel": True},
                "xAxis": {
                    "type": "category",
                    "data": x_axis,
                    "axisLabel": {"color": "#fff", "rotate": 30},
                    "axisLine": {"lineStyle": {"color": "#2c3860"}},
                    "splitLine": {"show": False}
                },
                "yAxis": {
                    "type": "value",
                    "name": "总电量 (MWh)",
                    "nameTextStyle": {"color": "#4fc3f7"},
                    "axisLabel": {"color": "#4fc3f7"},
                    "splitLine": {"lineStyle": {"color": "#242e52", "type": "dashed"}}
                },
                "series": [{
                    "name": "每日总电量",
                    "type": "line",
                    "smooth": True,
                    "symbol": "none",
                    "lineStyle": {"width": 3, "color": "#4fc3f7"},
                    "areaStyle": {"color": "rgba(79, 195, 247, 0.2)"},
                    "data": y_data,
                    "markLine": {
                        "data": [{"type": "average", "name": "日均电量"}],
                        "lineStyle": {"color": "#ffb74d", "type": "dashed"}
                    }
                }],
                "dataZoom": [{"type": "slider", "height": 16, "bottom": 5, "textStyle": {"color": "#fff"}}]
            }
            st_echarts(day_chart_opt, height="400px")
        else:
            st.info("当前筛选条件下无日用电量数据")
    else:
        st.warning("未找到日用电量数据文件，请检查路径")

# ===================== 模块二：国网代购电价格测算（保持不变） =====================
else:
    st.title("💰 国网代购电价测算工具")
    st.caption("常规：国网代购分时电价 | 市场化：市场均价 + 浮动参数 + 各项附加")

    if grid_price is None:
        st.stop()

    # 顶部左右布局
    col_left, col_right = st.columns([1, 1], gap="large")
    with col_left:
        st.subheader("📝 测算参数")
        c1, c2 = st.columns(2)
        with c1:
            area_sel = st.selectbox("地区电网", ["陕西电网", "榆林电网"])
        with c2:
            month_sel = st.selectbox("选择月份", sorted(grid_price[area_sel].keys()), format_func=lambda x: f"{x}月")
        c3, c4 = st.columns(2)
        with c3:
            type_sel = st.selectbox("用电类型", ["一般工商业用电", "大工业用电"])
        with c4:
            volt_list = list(grid_price[area_sel][month_sel][type_sel].keys())
            volt_sel = st.selectbox("电压等级", volt_list)

        price_info = grid_price[area_sel][month_sel][type_sel][volt_sel]

        float_param = st.number_input("市场化浮动参数(元/kWh，可正可负)", min_value=-9.9999, max_value=9.9999,
                                      value=0.0000, step=0.0001)
        total_kwh = st.number_input("总用电量 kWh", min_value=0.00, value=0.00, step=1000.00)

        cap_cost = 0.0
        if type_sel == "大工业用电":
            st.markdown("#### 容需量电费")
            cap_mode = st.selectbox("计费方式", ["不计容需量", "按最大容量", "按变压器容量"])
            if cap_mode == "按最大容量" and price_info["cap_max"] > 0:
                cap_kw = st.number_input("最大容量 kW", min_value=0.00, value=0.00, step=10.00)
                cap_cost = cap_kw * price_info["cap_max"]
            elif cap_mode == "按变压器容量" and price_info["cap_trans"] > 0:
                cap_kva = st.number_input("变压器容量 kVA", min_value=0.00, value=0.00, step=10.00)
                cap_cost = cap_kva * price_info["cap_trans"]

    with col_right:
        st.subheader("📊 峰平谷电量占比")
        has_jian = price_info["sharp_price"] > 0
        if has_jian:
            jian_pct = st.number_input("尖峰占比 %", min_value=0.00, max_value=100.00, value=0.00, step=0.01)
        else:
            jian_pct = 0.00
        col_p1, col_p2 = st.columns([1, 1])
        with col_p1:
            peak_pct = st.number_input("高峰占比 %", min_value=0.00, max_value=100.00, value=0.00, step=0.01)
        with col_p2:
            flat_pct = st.number_input("平段占比 %", min_value=0.00, max_value=100.00, value=0.00, step=0.01)
        valley_pct = st.number_input("谷段占比 %", min_value=0.00, max_value=100.00, value=0.00, step=0.01)
        sum_pct = round(jian_pct + peak_pct + flat_pct + valley_pct, 2)
        if not abs(sum_pct - 100.00) < 0.001:
            st.warning(f"⚠️ 当前占比总和 {sum_pct}%，请调整至 100.00%")

    # ---------- 24时段预计算 ----------
    period_type_map = get_period_type_map(month_sel)
    cnt_sharp = sum(1 for v in period_type_map.values() if v == "尖峰")
    cnt_peak = sum(1 for v in period_type_map.values() if v == "高峰")
    cnt_flat = sum(1 for v in period_type_map.values() if v == "平段")
    cnt_valley = sum(1 for v in period_type_map.values() if v == "谷段")

    total_sharp = total_kwh * jian_pct / 100
    total_peak = total_kwh * peak_pct / 100
    total_flat = total_kwh * flat_pct / 100
    total_valley = total_kwh * valley_pct / 100
    per_sharp = total_sharp / cnt_sharp if cnt_sharp > 0 else 0
    per_peak = total_peak / cnt_peak if cnt_peak > 0 else 0
    per_flat = total_flat / cnt_flat
    per_valley = total_valley / cnt_valley

    month_market_prices = []
    if month_sel in market_price_dict:
        month_market_prices = [p / 1000.0 for p in market_price_dict[month_sel]]

    # ---------- 常规测算结果 ----------
    st.markdown("---")
    st.subheader("🧮 常规测算结果")

    base_buy = price_info["purchase_price"]
    jian_buy, peak_buy, flat_buy, valley_buy = base_buy * 1.9, base_buy * 1.7, base_buy * 1.0, base_buy * 0.3
    jian_all, peak_all, flat_all, valley_all = price_info["sharp_price"], price_info["peak_price"], price_info[
        "flat_price"], price_info["valley_price"]

    avg_buy = jian_pct / 100 * jian_buy + peak_pct / 100 * peak_buy + flat_pct / 100 * flat_buy + valley_pct / 100 * valley_buy
    avg_all = jian_pct / 100 * jian_all + peak_pct / 100 * peak_all + flat_pct / 100 * flat_all + valley_pct / 100 * valley_all

    elec_total = total_kwh * avg_all
    all_total = elec_total + cap_cost
    naked_total_fee = total_kwh * avg_buy

    c_m1, c_m2, c_m3, c_m4 = st.columns(4)
    with c_m1:
        st.metric("⚡ 加权裸电单价", f"{avg_buy:.4f} 元/kWh")
    with c_m2:
        st.metric("💰 裸电总电费", f"{naked_total_fee:,.2f} 元")
    with c_m3:
        st.metric("🏠 加权到户单价", f"{avg_all:.4f} 元/kWh")
    with c_m4:
        st.metric("💸 月度总电费(全费用)", f"{all_total:,.2f} 元")

    if cap_cost > 0:
        extra_fee = elec_total - naked_total_fee
        st.caption(
            f"费用拆分：裸电购电成本 {naked_total_fee:,.2f} 元 | 输配电+基金附加 {extra_fee:,.2f} 元 | 容需量电费 {cap_cost:,.2f} 元")
    else:
        extra_fee = elec_total - naked_total_fee
        st.caption(f"费用拆分：裸电购电成本 {naked_total_fee:,.2f} 元 | 输配电+基金附加 {extra_fee:,.2f} 元")

    # ===================== 市场化电价测算 =====================
    st.markdown("---")
    st.subheader("📈 市场化电价测算结果")

    line_loss_price = price_info["line_loss"]
    trans_price = price_info["trans_price"]
    system_fee = price_info["system_fee"]
    gov_fee = price_info["gov_fee"]
    add_total_per_kwh = line_loss_price + trans_price + system_fee + gov_fee

    if total_kwh <= 0:
        mkt_avg_buy = 0.0
        mkt_naked_total = 0.0
        mkt_avg_all = 0.0
        mkt_total_fee = 0.0
    else:
        mkt_naked_total = 0.0
        for seg_idx in range(24):
            seg_num = seg_idx + 1
            p_t = period_type_map[seg_num]
            if p_t == "尖峰":
                elec = per_sharp
            elif p_t == "高峰":
                elec = per_peak
            elif p_t == "平段":
                elec = per_flat
            else:
                elec = per_valley
            mkt_price = month_market_prices[seg_idx] if seg_idx < len(month_market_prices) else 0
            mkt_naked_total += (mkt_price + float_param) * elec
        mkt_avg_buy = mkt_naked_total / total_kwh
        mkt_avg_all = mkt_avg_buy + add_total_per_kwh
        mkt_total_fee = total_kwh * mkt_avg_all

    mk1, mk2, mk3, mk4 = st.columns(4)
    with mk1:
        st.metric("⚡ 市场化加权裸电单价", f"{mkt_avg_buy:.4f} 元/kWh")
    with mk2:
        st.metric("💰 市场化裸电总电费", f"{mkt_naked_total:,.2f} 元")
    with mk3:
        st.metric("🏠 市场化加权到户单价", f"{mkt_avg_all:.4f} 元/kWh")
    with mk4:
        st.metric("💸 市场化月度总电费", f"{mkt_total_fee:,.2f} 元")

    st.caption(
        f"附加参数（取自国网代购表·{volt_sel}）："
        f"上网线损 {line_loss_price:.5f} | "
        f"输配电 {trans_price:.5f} | "
        f"系统运行费 {system_fee:.5f} | "
        f"政府基金 {gov_fee:.5f} 元/kWh | "
        f"浮动参数 {float_param:.4f} 元/kWh"
    )

    # ---------------------- 24时段对比图表 ----------------------
    st.markdown("---")
    st.subheader("📊 24时段电量、市场均价、国网代购裸电价对比")
    time_labels = [f"段{i}" for i in range(1, 25)]
    elec_data = []
    market_price_line = []
    grid_buy_price_line = []
    for seg_idx in range(24):
        seg_num = seg_idx + 1
        p_t = period_type_map[seg_num]
        if p_t == "尖峰":
            e = per_sharp
        elif p_t == "高峰":
            e = per_peak
        elif p_t == "平段":
            e = per_flat
        else:
            e = per_valley
        elec_data.append(round(e, 2))
        mp = month_market_prices[seg_idx] if seg_idx < len(month_market_prices) else 0
        market_price_line.append(round(mp, 4))
        if seg_num in [19, 20] and month_sel in [1, 12]:
            gp = jian_buy
        elif seg_num in [20, 21] and month_sel in [7, 8]:
            gp = jian_buy
        elif p_t == "高峰":
            gp = peak_buy
        elif p_t == "平段":
            gp = flat_buy
        else:
            gp = valley_buy
        grid_buy_price_line.append(round(gp, 4))

    chart_opt = {
        "backgroundColor": "#121a38",
        "tooltip": {"trigger": "axis", "textStyle": {"color": "#fff"}},
        "legend": {
            "data": ["分时电量", "市场分时均价", "国网代购裸电价"],
            "textStyle": {"color": "#fff"},
            "top": 0
        },
        "grid": {"left": "5%", "right": "6%", "bottom": "12%", "top": "15%", "containLabel": True},
        "xAxis": {
            "type": "category",
            "data": time_labels,
            "axisLabel": {"color": "#fff", "rotate": 30},
            "axisLine": {"lineStyle": {"color": "#2c3860"}},
            "splitLine": {"show": False}
        },
        "yAxis": [
            {
                "type": "value",
                "name": "分时电量(kWh)",
                "nameTextStyle": {"color": "#4fc3f7"},
                "axisLabel": {"color": "#4fc3f7"},
                "splitLine": {"lineStyle": {"color": "#242e52", "type": "dashed"}}
            },
            {
                "type": "value",
                "name": "电价(元/kWh)",
                "nameTextStyle": {"color": "#ffb74d"},
                "axisLabel": {"color": "#ffb74d"},
                "splitLine": {"show": False},
                "position": "right"
            }
        ],
        "series": [
            {
                "name": "分时电量",
                "type": "bar",
                "yAxisIndex": 0,
                "data": elec_data,
                "itemStyle": {"color": "#4fc3f780"}
            },
            {
                "name": "市场分时均价",
                "type": "line",
                "yAxisIndex": 1,
                "data": market_price_line,
                "lineStyle": {"width": 3},
                "itemStyle": {"color": "#ffb74d"}
            },
            {
                "name": "国网代购裸电价",
                "type": "line",
                "yAxisIndex": 1,
                "data": grid_buy_price_line,
                "lineStyle": {"width": 3, "type": "dashed"},
                "itemStyle": {"color": "#f06292"}
            }
        ]
    }
    st_echarts(chart_opt, height="400px")

    # ---------- 24时段分时电价明细 ----------
    st.markdown("---")
    with st.expander("📋 查看24时段分时电价明细", expanded=False):
        col_title, col_btn = st.columns([3, 1])
        with col_title:
            st.markdown("#### 24时段分时电价明细")
        with col_btn:
            def gen_24h_data():
                time_ranges = [f"{h:02d}:00-{h + 1:02d}:00" for h in range(24)]
                rows = []
                for seg_idx in range(24):
                    seg_num = seg_idx + 1
                    p_t = period_type_map[seg_num]
                    if p_t == "尖峰":
                        buy_p = jian_buy
                        all_p = jian_all
                        elec = per_sharp
                    elif p_t == "高峰":
                        buy_p = peak_buy
                        all_p = peak_all
                        elec = per_peak
                    elif p_t == "平段":
                        buy_p = flat_buy
                        all_p = flat_all
                        elec = per_flat
                    else:
                        buy_p = valley_buy
                        all_p = valley_all
                        elec = per_valley
                    mkt_price = month_market_prices[seg_idx] if seg_idx < len(month_market_prices) else 0
                    mkt_buy_p = mkt_price + float_param
                    mkt_all_p = mkt_buy_p + add_total_per_kwh
                    rows.append([
                        f"段{seg_num}", time_ranges[seg_idx], p_t,
                        round(buy_p, 4), round(mkt_buy_p, 4),
                        round(all_p, 4), round(mkt_all_p, 4),
                        round(elec, 2)
                    ])
                return pd.DataFrame(
                    rows,
                    columns=["时段编号", "时间范围", "时段类型", "常规裸电价", "市场化裸电价", "常规到户价",
                             "市场化到户价", "电量(kWh)"]
                )


            df_24h = gen_24h_data()
            csv_data = df_24h.to_csv(index=False, encoding="utf-8-sig")
            st.download_button("📥 导出CSV", data=csv_data, file_name=f"24时段分时电价_{area_sel}_{month_sel}月.csv",
                               mime="text/csv", use_container_width=True)
        st.dataframe(df_24h, hide_index=True, width="stretch", height=360)