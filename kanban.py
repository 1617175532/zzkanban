import streamlit as st
import pandas as pd
import os
import datetime
import io
import matplotlib.pyplot as plt
from streamlit_echarts import st_echarts

# -------------------------- 报告生成函数 --------------------------
def generate_report_data(area, month, type_, volt, total_kwh, contract_capacity,
                         price_info, period_map,
                         jian_pct, peak_pct, flat_pct, valley_pct,
                         avg_buy, avg_all, all_total, cap_cost,
                         mkt_avg_buy, mkt_avg_all, mkt_total_fee, mkt_naked_total,
                         naked_total_fee, elec_total, add_total_per_kwh,
                         float_param, per_sharp, per_peak, per_flat, per_valley,
                         market_price_dict):
    """生成报告数据（统一数据源）"""
    
    total_sharp = total_kwh * jian_pct / 100
    total_peak = total_kwh * peak_pct / 100
    total_flat = total_kwh * flat_pct / 100
    total_valley = total_kwh * valley_pct / 100
    
    saving = all_total - (mkt_total_fee + cap_cost)
    saving_rate = (saving / all_total * 100) if all_total > 0 else 0
    
    trans_plus_gov = price_info["trans_price"] + price_info["gov_fee"]
    system_total = total_kwh * price_info["system_fee"]
    trans_gov_total = total_kwh * trans_plus_gov
    
    avg_kwh_per_kva = total_kwh / contract_capacity if contract_capacity > 0 else 0
    discount_status = "✅ 已享受九折优惠" if avg_kwh_per_kva >= 260 else "⚠️ 未达到九折标准"
    
    peak_valley_ratio = peak_pct / valley_pct if valley_pct > 0 else float('inf')
    
    base_buy = price_info["base_buy"] if "base_buy" in price_info else naked_total_fee / total_kwh if total_kwh > 0 else 0
    jian_buy_val = base_buy * 1.9
    peak_buy_val = base_buy * 1.7
    flat_buy_val = base_buy * 1.0
    valley_buy_val = base_buy * 0.3
    
    time_labels = [f"段{i}" for i in range(1, 25)]
    period_names = [period_map[i] for i in range(1, 25)]
    elec_data = []
    market_prices = []
    grid_buy_prices = []
    
    for i in range(1, 25):
        p_t = period_map[i]
        if p_t == "尖峰":
            elec_data.append(per_sharp)
        elif p_t == "高峰":
            elec_data.append(per_peak)
        elif p_t == "平段":
            elec_data.append(per_flat)
        else:
            elec_data.append(per_valley)
        
        if month in market_price_dict and (i-1) < len(market_price_dict[month]):
            market_prices.append(market_price_dict[month][i-1] / 1000.0)
        else:
            market_prices.append(0)
        
        if i in [19, 20] and month in [1, 12]:
            grid_buy_prices.append(jian_buy_val)
        elif i in [20, 21] and month in [7, 8]:
            grid_buy_prices.append(jian_buy_val)
        elif p_t == "高峰":
            grid_buy_prices.append(peak_buy_val)
        elif p_t == "平段":
            grid_buy_prices.append(flat_buy_val)
        else:
            grid_buy_prices.append(valley_buy_val)
    
    report_data = {
        "basic_info": {
            "area": area, "month": month, "type": type_, "volt": volt,
            "total_kwh": total_kwh, "contract_capacity": contract_capacity,
            "report_date": datetime.date.today().strftime("%Y-%m-%d"),
            "avg_kwh_per_kva": avg_kwh_per_kva, "discount_status": discount_status
        },
        "elec_structure": {
            "jian_pct": jian_pct, "peak_pct": peak_pct, "flat_pct": flat_pct, "valley_pct": valley_pct,
            "total_sharp": total_sharp, "total_peak": total_peak,
            "total_flat": total_flat, "total_valley": total_valley,
            "peak_valley_ratio": peak_valley_ratio
        },
        "cost_data": {
            "avg_buy": avg_buy, "avg_all": avg_all, "all_total": all_total, "cap_cost": cap_cost,
            "naked_total_fee": naked_total_fee, "elec_total": elec_total,
            "trans_gov_total": trans_gov_total, "system_total": system_total,
            "mkt_avg_buy": mkt_avg_buy, "mkt_avg_all": mkt_avg_all,
            "mkt_total_fee": mkt_total_fee, "mkt_naked_total": mkt_naked_total,
            "saving": saving, "saving_rate": saving_rate,
            "float_param": float_param, "add_total_per_kwh": add_total_per_kwh,
            "price_info": price_info
        },
        "hourly_data": {
            "time_labels": time_labels, "period_names": period_names,
            "elec_data": elec_data, "market_prices": market_prices,
            "grid_buy_prices": grid_buy_prices
        },
        "analysis": {
            "jian_desc": "本月无尖峰时段（非1、7、8、12月）" if jian_pct == 0 else f"尖峰用电 {total_sharp:,.0f} kWh，占比 {jian_pct:.1f}%",
            "peak_desc": f"高峰用电集中，占比 {peak_pct:.1f}%，建议关注削峰",
            "flat_desc": f"平段用电稳定，占比 {flat_pct:.1f}%",
            "valley_desc": f"谷段用电占比 {valley_pct:.1f}%，{'存在较大优化空间' if valley_pct < 20 else '利用正常'}",
            "peak_valley_desc": f"峰谷差较大（峰/谷比约 {peak_valley_ratio:.1f}），{'建议调整' if peak_valley_ratio > 1.5 else '较为合理'}",
            "saving_desc": f"市场化方案预计节省 {saving:,.0f} 元（降幅 {saving_rate:.1f}%），经济效益{'显著' if saving_rate > 10 else '一般'}"
        }
    }
    return report_data


def generate_html_report(report_data):
    """生成美观的HTML报告预览"""
    bi = report_data["basic_info"]
    es = report_data["elec_structure"]
    cd = report_data["cost_data"]
    hd = report_data["hourly_data"]
    analysis = report_data["analysis"]
    
    elec_data = hd['elec_data']
    market_prices = hd['market_prices']
    grid_buy_prices = hd['grid_buy_prices']
    
    max_elec = max(elec_data) if elec_data else 1
    max_price = max(max(market_prices), max(grid_buy_prices), 0.1)
    
    elec_scale = 180 / max_elec
    price_scale = 180 / max_price
    
    bar_width = 28
    gap = 4
    start_x = 40
    start_y = 200
    
    bars_svg = ''
    for i in range(24):
        x = start_x + i * (bar_width + gap)
        height = elec_data[i] * elec_scale
        bars_svg += f'<rect x="{x}" y="{start_y - height}" width="{bar_width}" height="{height}" fill="rgba(79, 195, 247, 0.5)" stroke="rgba(79, 195, 247, 0.8)" stroke-width="1" rx="3"/>'
    
    market_line = ''
    for i in range(24):
        x = start_x + i * (bar_width + gap) + bar_width / 2
        y = start_y - market_prices[i] * price_scale
        if i == 0:
            market_line += f'M {x} {y}'
        else:
            market_line += f' L {x} {y}'
    
    grid_line = ''
    for i in range(24):
        x = start_x + i * (bar_width + gap) + bar_width / 2
        y = start_y - grid_buy_prices[i] * price_scale
        if i == 0:
            grid_line += f'M {x} {y}'
        else:
            grid_line += f' L {x} {y}'
    
    html = f"""
    <div style="font-family: 'Microsoft YaHei', sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); min-height: 100vh;">
        <div style="background: white; border-radius: 16px; box-shadow: 0 10px 40px rgba(0,0,0,0.1); overflow: hidden;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                <h1 style="color: white; font-size: 28px; margin: 0; font-weight: 700;">⚡ 电费成本分析报告</h1>
                <p style="color: rgba(255,255,255,0.8); margin-top: 8px; font-size: 14px;">专业 · 精准 · 高效</p>
            </div>
            
            <div style="padding: 25px;">
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-bottom: 25px;">
                    <div style="background: linear-gradient(135deg, #e0f7fa 0%, #b2ebf2 100%); padding: 20px; border-radius: 12px;">
                        <div style="color: #006064; font-size: 13px; font-weight: 600;">用户名称</div>
                        <div style="color: #00838f; font-size: 20px; font-weight: 700; margin-top: 5px;">{bi['type']}</div>
                    </div>
                    <div style="background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%); padding: 20px; border-radius: 12px;">
                        <div style="color: #4a148c; font-size: 13px; font-weight: 600;">电压等级</div>
                        <div style="color: #6a1b9a; font-size: 20px; font-weight: 700; margin-top: 5px;">{bi['volt']}</div>
                    </div>
                    <div style="background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%); padding: 20px; border-radius: 12px;">
                        <div style="color: #bf360c; font-size: 13px; font-weight: 600;">报告月份</div>
                        <div style="color: #e65100; font-size: 20px; font-weight: 700; margin-top: 5px;">2026年{bi['month']}月</div>
                    </div>
                    <div style="background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); padding: 20px; border-radius: 12px;">
                        <div style="color: #1b5e20; font-size: 13px; font-weight: 600;">总用电量</div>
                        <div style="color: #2e7d32; font-size: 20px; font-weight: 700; margin-top: 5px;">{bi['total_kwh']:,.0f} kWh</div>
                    </div>
                </div>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 12px; margin-bottom: 25px;">
                    <h2 style="color: #333; font-size: 18px; margin: 0 0 15px 0; font-weight: 700;">📊 核心指标对比</h2>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr style="background: #667eea; color: white;">
                            <th style="padding: 10px; text-align: left; font-weight: 600;">指标</th>
                            <th style="padding: 10px; text-align: center; font-weight: 600;">国网代购</th>
                            <th style="padding: 10px; text-align: center; font-weight: 600;">市场化交易</th>
                            <th style="padding: 10px; text-align: center; font-weight: 600;">差异</th>
                        </tr>
                        <tr style="border-bottom: 1px solid #ddd;">
                            <td style="padding: 10px; color: #555;">加权裸电单价</td>
                            <td style="padding: 10px; text-align: center; font-weight: 600;">{cd['avg_buy']:.4f} 元/kWh</td>
                            <td style="padding: 10px; text-align: center; font-weight: 600;">{cd['mkt_avg_buy']:.4f} 元/kWh</td>
                            <td style="padding: 10px; text-align: center; font-weight: 700; color: {'green' if (cd['mkt_avg_buy'] - cd['avg_buy']) < 0 else 'red'};">
                                {(cd['mkt_avg_buy'] - cd['avg_buy']):+.4f} 元/kWh
                            </td>
                        </tr>
                        <tr style="border-bottom: 1px solid #ddd;">
                            <td style="padding: 10px; color: #555;">裸电费用</td>
                            <td style="padding: 10px; text-align: center; font-weight: 600;">¥{cd['naked_total_fee']:,.2f}</td>
                            <td style="padding: 10px; text-align: center; font-weight: 600;">¥{cd['mkt_naked_total']:,.2f}</td>
                            <td style="padding: 10px; text-align: center; font-weight: 700; color: {'green' if (cd['mkt_naked_total'] - cd['naked_total_fee']) < 0 else 'red'};">
                                ¥{(cd['mkt_naked_total'] - cd['naked_total_fee']):+,.2f}
                            </td>
                        </tr>
                        <tr style="border-bottom: 1px solid #ddd;">
                            <td style="padding: 10px; color: #555;">总电费</td>
                            <td style="padding: 10px; text-align: center; font-weight: 600;">¥{cd['all_total']:,.2f}</td>
                            <td style="padding: 10px; text-align: center; font-weight: 600;">¥{(cd['mkt_total_fee'] + cd['cap_cost']):,.2f}</td>
                            <td style="padding: 10px; text-align: center; font-weight: 700; color: {'green' if ((cd['mkt_total_fee'] + cd['cap_cost']) - cd['all_total']) < 0 else 'red'};">
                                ¥{((cd['mkt_total_fee'] + cd['cap_cost']) - cd['all_total']):+,.2f}
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; color: #555;">平均电价</td>
                            <td style="padding: 10px; text-align: center; font-weight: 600;">{cd['avg_all']:.4f} 元/kWh</td>
                            <td style="padding: 10px; text-align: center; font-weight: 600;">{cd['mkt_avg_all']:.4f} 元/kWh</td>
                            <td style="padding: 10px; text-align: center; font-weight: 700; color: {'green' if (cd['mkt_avg_all'] - cd['avg_all']) < 0 else 'red'};">
                                {(cd['mkt_avg_all'] - cd['avg_all']):+.4f} 元/kWh
                            </td>
                        </tr>
                    </table>
                </div>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 12px; margin-bottom: 25px;">
                    <h2 style="color: #333; font-size: 18px; margin: 0 0 15px 0; font-weight: 700;">⚡ 用电结构分析</h2>
                    <div style="display: flex; justify-content: space-around; margin-bottom: 15px;">
                        <div style="text-align: center;">
                            <div style="width: 80px; height: 80px; border-radius: 50%; background: #ff4c4c; display: flex; align-items: center; justify-content: center; margin: 0 auto 8px; color: white; font-weight: 700; font-size: 14px;">{es['jian_pct']:.1f}%</div>
                            <div style="font-size: 12px; color: #666;">尖峰</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="width: 80px; height: 80px; border-radius: 50%; background: #ffa500; display: flex; align-items: center; justify-content: center; margin: 0 auto 8px; color: white; font-weight: 700; font-size: 14px;">{es['peak_pct']:.1f}%</div>
                            <div style="font-size: 12px; color: #666;">高峰</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="width: 80px; height: 80px; border-radius: 50%; background: #4caf50; display: flex; align-items: center; justify-content: center; margin: 0 auto 8px; color: white; font-weight: 700; font-size: 14px;">{es['flat_pct']:.1f}%</div>
                            <div style="font-size: 12px; color: #666;">平段</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="width: 80px; height: 80px; border-radius: 50%; background: #2196f3; display: flex; align-items: center; justify-content: center; margin: 0 auto 8px; color: white; font-weight: 700; font-size: 14px;">{es['valley_pct']:.1f}%</div>
                            <div style="font-size: 12px; color: #666;">谷段</div>
                        </div>
                    </div>
                    <div style="background: white; padding: 15px; border-radius: 8px;">
                        <p style="margin: 5px 0; font-size: 14px; color: #555;">📌 {analysis['jian_desc']}</p>
                        <p style="margin: 5px 0; font-size: 14px; color: #555;">📌 {analysis['peak_desc']}</p>
                        <p style="margin: 5px 0; font-size: 14px; color: #555;">📌 {analysis['flat_desc']}</p>
                        <p style="margin: 5px 0; font-size: 14px; color: #555;">📌 {analysis['valley_desc']}</p>
                        <p style="margin: 5px 0; font-size: 14px; color: #555;">📌 {analysis['peak_valley_desc']}</p>
                    </div>
                </div>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 12px; margin-bottom: 25px;">
                    <h2 style="color: #333; font-size: 18px; margin: 0 0 15px 0; font-weight: 700;">📈 24时段电量、市场均价、国网代购裸电价对比</h2>
                    <svg width="100%" height="320" viewBox="0 0 850 320" preserveAspectRatio="xMidYMid meet">
                        <line x1="40" y1="20" x2="40" y2="200" stroke="#ddd" stroke-width="1"/>
                        <line x1="40" y1="200" x2="810" y2="200" stroke="#ddd" stroke-width="1"/>
                        {''.join([f'<text x="{40 + i * 32 + 14}" y="220" font-size="8" fill="#666" text-anchor="middle">{i+1}:00</text>' for i in range(24)])}
                        <text x="15" y="110" font-size="9" fill="#666" text-anchor="middle" transform="rotate(-90, 15, 110)">电量(kWh)</text>
                        <text x="405" y="250" font-size="11" fill="#666" text-anchor="middle">时段</text>
                        <line x1="810" y1="20" x2="810" y2="200" stroke="#ddd" stroke-width="1"/>
                        <text x="830" y="110" font-size="9" fill="#ff8a65" text-anchor="middle" transform="rotate(-90, 830, 110)">电价(元)</text>
                        {bars_svg}
                        <path d="{market_line}" fill="none" stroke="#ffb74d" stroke-width="3"/>
                        {''.join([f'<circle cx="{40 + i * 32 + 14}" cy="{200 - market_prices[i] * price_scale}" r="4" fill="#ffb74d"/>' for i in range(24)])}
                        <path d="{grid_line}" fill="none" stroke="#f06292" stroke-width="3" stroke-dasharray="5,3"/>
                        {''.join([f'<circle cx="{40 + i * 32 + 14}" cy="{200 - grid_buy_prices[i] * price_scale}" r="4" fill="#f06292"/>' for i in range(24)])}
                        <g transform="translate(325, 260)">
                            <rect x="0" y="0" width="200" height="35" fill="white" rx="6" stroke="#eee"/>
                            <rect x="10" y="12" width="15" height="10" fill="rgba(79, 195, 247, 0.5)" rx="2"/>
                            <text x="32" y="20" font-size="10" fill="#333">分时电量</text>
                            <circle cx="82" cy="17" r="4" fill="#ffb74d"/>
                            <line x1="72" y1="17" x2="92" y2="17" stroke="#ffb74d" stroke-width="2"/>
                            <text x="98" y="21" font-size="10" fill="#333">市场均价</text>
                            <circle cx="158" cy="17" r="4" fill="#f06292"/>
                            <line x1="148" y1="17" x2="168" y2="17" stroke="#f06292" stroke-width="2" stroke-dasharray="3,2"/>
                            <text x="174" y="21" font-size="10" fill="#333">国网代购</text>
                        </g>
                    </svg>
                </div>
                
                <div style="background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); padding: 20px; border-radius: 12px; margin-bottom: 25px;">
                    <h2 style="color: #1b5e20; font-size: 18px; margin: 0 0 15px 0; font-weight: 700;">💡 推荐建议</h2>
                    <div style="background: white; padding: 15px; border-radius: 8px;">
                        <div style="font-size: 16px; font-weight: 700; margin-bottom: 10px; color: {'green' if cd['saving'] > 0 else 'orange'};">
                            {'✅ 推荐：市场化交易' if cd['saving'] > 0 else '⚠️ 推荐：国网代购'}
                        </div>
                        <p style="margin: 5px 0; font-size: 14px; color: #555;">{analysis['saving_desc']}</p>
                    </div>
                </div>
                
                <div style="text-align: center; margin-top: 25px; padding-top: 20px; border-top: 1px solid #eee;">
                    <p style="color: #999; font-size: 12px;">报告生成日期：{bi['report_date']}</p>
                    <p style="color: #999; font-size: 12px; margin-top: 5px;">本报告仅供参考，请以实际结算为准</p>
                </div>
            </div>
        </div>
    </div>
    """
    return html


def generate_excel_report(report_data):
    """生成美观的 Excel 报告"""
    try:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            bi = report_data["basic_info"]
            es = report_data["elec_structure"]
            cd = report_data["cost_data"]
            hd = report_data["hourly_data"]
            analysis = report_data["analysis"]
            
            header_format = workbook.add_format({
                'bold': True, 'font_color': 'white', 'bg_color': '#5B8FF9',
                'align': 'center', 'valign': 'vcenter', 'border': 1, 'font_size': 11
            })
            title_format = workbook.add_format({
                'bold': True, 'font_size': 16, 'align': 'center', 'valign': 'vcenter', 'font_color': '#1E3A8A'
            })
            currency_format = workbook.add_format({
                'num_format': '#,##0.00', 'align': 'right', 'border': 1
            })
            percent_format = workbook.add_format({
                'num_format': '0.00%', 'align': 'center', 'border': 1
            })
            normal_format = workbook.add_format({
                'align': 'center', 'valign': 'vcenter', 'border': 1
            })
            highlight_green = workbook.add_format({
                'bold': True, 'font_color': '#16A34A', 'align': 'center', 'border': 1
            })
            highlight_red = workbook.add_format({
                'bold': True, 'font_color': '#DC2626', 'align': 'center', 'border': 1
            })
            card_format = workbook.add_format({
                'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter', 'font_color': '#1E3A8A'
            })
            
            ws1 = writer.book.add_worksheet("报告摘要")
            ws1.set_column('A:A', 22)
            ws1.set_column('B:B', 22)
            ws1.set_column('C:C', 22)
            ws1.set_column('D:D', 22)
            
            ws1.merge_range('A1:D1', '⚡ 电费成本分析报告', title_format)
            ws1.write('A3', '用户名称', header_format)
            ws1.write('B3', bi["type"], card_format)
            ws1.write('C3', '电压等级', header_format)
            ws1.write('D3', bi["volt"], card_format)
            ws1.write('A4', '报告月份', header_format)
            ws1.write('B4', f"2026年{bi['month']}月", normal_format)
            ws1.write('C4', '生成日期', header_format)
            ws1.write('D4', bi["report_date"], normal_format)
            ws1.write('A5', '总用电量', header_format)
            ws1.write('B5', f"{bi['total_kwh']:,.0f} kWh", card_format)
            ws1.write('C5', '合同容量', header_format)
            ws1.write('D5', f"{bi['contract_capacity']:,.0f} kVA", card_format)
            ws1.write('A6', '九折状态', header_format)
            ws1.write('B6', bi["discount_status"], highlight_green if "已享受" in bi["discount_status"] else highlight_red)
            
            ws1.merge_range('A8:D8', '📊 核心指标对比', title_format)
            ws1.write('A9', '指标', header_format)
            ws1.write('B9', '国网代购', header_format)
            ws1.write('C9', '市场化交易', header_format)
            ws1.write('D9', '差异', header_format)
            ws1.write('A10', '加权裸电单价(元/kWh)', normal_format)
            ws1.write('B10', round(cd["avg_buy"], 4), currency_format)
            ws1.write('C10', round(cd["mkt_avg_buy"], 4), currency_format)
            ws1.write('D10', round(cd["mkt_avg_buy"] - cd["avg_buy"], 4), highlight_green if cd["mkt_avg_buy"] < cd["avg_buy"] else highlight_red)
            ws1.write('A11', '总电费(元)', normal_format)
            ws1.write('B11', round(cd["all_total"], 2), currency_format)
            ws1.write('C11', round(cd["mkt_total_fee"] + cd["cap_cost"], 2), currency_format)
            ws1.write('D11', round(cd["saving"], 2), highlight_green if cd["saving"] > 0 else highlight_red)
            ws1.write('A12', '平均电价(元/kWh)', normal_format)
            ws1.write('B12', round(cd["avg_all"], 4), currency_format)
            ws1.write('C12', round(cd["mkt_avg_all"], 4), currency_format)
            ws1.write('D12', f"{cd['saving_rate']:+.1f}%", highlight_green if cd["saving_rate"] > 0 else highlight_red)
            
            ws2 = writer.book.add_worksheet("用电结构")
            ws2.set_column('A:A', 12)
            ws2.set_column('B:B', 18)
            ws2.set_column('C:C', 12)
            ws2.set_column('D:D', 35)
            ws2.merge_range('A1:D1', '⚡ 用电结构分析', title_format)
            ws2.write('A3', '时段', header_format)
            ws2.write('B3', '电量(kWh)', header_format)
            ws2.write('C3', '占比(%)', header_format)
            ws2.write('D3', '分析说明', header_format)
            
            periods = [
                ("尖峰", es["total_sharp"], es["jian_pct"], analysis["jian_desc"]),
                ("高峰", es["total_peak"], es["peak_pct"], analysis["peak_desc"]),
                ("平段", es["total_flat"], es["flat_pct"], analysis["flat_desc"]),
                ("谷段", es["total_valley"], es["valley_pct"], analysis["valley_desc"]),
                ("合计", bi["total_kwh"], 100, "—")
            ]
            for i, (name, qty, pct, desc) in enumerate(periods):
                row = i + 4
                ws2.write(f'A{row}', name, normal_format)
                ws2.write(f'B{row}', round(qty, 2), currency_format)
                ws2.write(f'C{row}', pct, percent_format)
                ws2.write(f'D{row}', desc, normal_format)
            
            ws2.write('A10', '峰谷比', header_format)
            ws2.write('B10', f"{es['peak_valley_ratio']:.1f}", normal_format)
            ws2.write('C10', '分析', header_format)
            ws2.write('D10', analysis["peak_valley_desc"], normal_format)
            
            ws3 = writer.book.add_worksheet("成本明细")
            ws3.set_column('A:A', 22)
            ws3.set_column('B:C', 18)
            ws3.set_column('D:D', 25)
            ws3.merge_range('A1:D1', '💰 成本明细对比', title_format)
            ws3.write('A3', '费用项目', header_format)
            ws3.write('B3', '国网代购(元)', header_format)
            ws3.write('C3', '市场化(元)', header_format)
            ws3.write('D3', '计算方式', header_format)
            
            cost_items = [
                ("裸电总电费", cd["naked_total_fee"], cd["mkt_naked_total"], "总用电量 × 加权裸电价"),
                ("输配电+基金附加", cd["trans_gov_total"], cd["trans_gov_total"], f"总用电量 × ({cd['price_info']['trans_price']:.4f}+{cd['price_info']['gov_fee']:.5f})"),
                ("系统运行费", cd["system_total"], cd["system_total"], f"总用电量 × {cd['price_info']['system_fee']:.4f}"),
                ("基本电费(容需量)", cd["cap_cost"], cd["cap_cost"], "合同容量/需量 × 对应电价"),
                ("合计总电费", cd["all_total"], cd["mkt_total_fee"] + cd["cap_cost"], "以上各项之和")
            ]
            for i, (item, grid_val, mkt_val, calc) in enumerate(cost_items):
                row = i + 4
                ws3.write(f'A{row}', item, normal_format)
                ws3.write(f'B{row}', round(grid_val, 2), currency_format)
                ws3.write(f'C{row}', round(mkt_val, 2), currency_format)
                ws3.write(f'D{row}', calc, normal_format)
            
            ws4 = writer.book.add_worksheet("24小时数据")
            ws4.set_column('A:A', 10)
            ws4.set_column('B:B', 14)
            ws4.set_column('C:C', 10)
            ws4.set_column('D:D', 16)
            ws4.set_column('E:E', 18)
            ws4.write('A1', '时段编号', header_format)
            ws4.write('B1', '时间范围', header_format)
            ws4.write('C1', '时段类型', header_format)
            ws4.write('D1', '电量(kWh)', header_format)
            ws4.write('E1', '市场均价(元/kWh)', header_format)
            
            time_ranges = [f"{h:02d}:00-{h + 1:02d}:00" for h in range(24)]
            for i in range(24):
                ws4.write(f'A{i+2}', f"段{i+1}", normal_format)
                ws4.write(f'B{i+2}', time_ranges[i], normal_format)
                ws4.write(f'C{i+2}', hd["period_names"][i], normal_format)
                ws4.write(f'D{i+2}', round(hd["elec_curve"][i], 2), currency_format)
                ws4.write(f'E{i+2}', round(hd["market_prices"][i], 4), currency_format)
            
            ws5 = writer.book.add_worksheet("优化建议")
            ws5.set_column('A:A', 12)
            ws5.set_column('B:B', 28)
            ws5.set_column('C:C', 35)
            ws5.merge_range('A1:C1', '💡 优化建议与措施', title_format)
            ws5.write('A3', '序号', header_format)
            ws5.write('B3', '优化方向', header_format)
            ws5.write('C3', '具体措施与预期收益', header_format)
            
            suggestions = [
                ("推荐方案", f"{'✅ 市场化交易' if cd['saving'] > 0 else '⚠️ 国网代购'}", analysis["saving_desc"]),
                ("削峰填谷", "降低高峰用电占比", "将9:00-11:00负荷转移至谷段，预计节省5%"),
                ("储能配置", "配置储能系统", "建议配置500kWh储能，谷充峰放，年省约3万"),
                ("功率因数", "提高功率因数", "加装无功补偿至0.95以上，减免力调电费约1%"),
                ("错峰生产", "调整生产班次", "高耗电工序安排在平/谷段")
            ]
            for i, (idx, title, desc) in enumerate(suggestions):
                row = i + 4
                ws5.write(f'A{row}', idx, normal_format)
                ws5.write(f'B{row}', title, normal_format)
                ws5.write(f'C{row}', desc, normal_format)
        
        return output.getvalue(), None
    except Exception as e:
        return None, str(e)


# -------------------------- Streamlit 页面配置 --------------------------
st.set_page_config(page_title="电量数据看板", layout="wide", initial_sidebar_state="expanded")

# -------------------------- 相对路径配置 --------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

FILE_ELEC = os.path.join(DATA_DIR, "月电量.xlsx")
FILE_PRICE = os.path.join(DATA_DIR, "市场均价.xlsx")
FILE_GRID_PRICE = os.path.join(DATA_DIR, "国网代购.xlsx")
FILE_DAY_ELEC = os.path.join(DATA_DIR, "2026日用电量.xlsx")

# ---------- 日期选择器汉化 ----------
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
        last_purchase_price = 0.0

        for _, row in df.iterrows():
            if pd.isna(row[0]) and pd.isna(row[2]):
                continue

            if isinstance(row[0], str) and "2026年" in str(row[0]):
                month_str = str(row[0]).split("2026年")[1].replace("月", "")
                current_month = int(month_str)
                price_data[area_name][current_month] = {}
                last_purchase_price = 0.0

            if not pd.isna(row[1]):
                current_type = str(row[1]).strip()
                price_data[area_name][current_month][current_type] = {}
                if not pd.isna(row[4]):
                    last_purchase_price = float(row[4])

            if not pd.isna(row[2]) and current_month and current_type:
                voltage = str(row[2]).strip()
                if not pd.isna(row[4]):
                    last_purchase_price = float(row[4])

                price_data[area_name][current_month][current_type][voltage] = {
                    "flat_total": float(row[3]),
                    "purchase_price": last_purchase_price,
                    "line_loss": float(row[5]) if not pd.isna(row[5]) else 0,
                    "trans_price": float(row[6]) if not pd.isna(row[6]) else 0,
                    "system_fee": float(row[7]) if not pd.isna(row[7]) else 0,
                    "gov_fee": float(row[8]) if not pd.isna(row[8]) else 0,
                    "sharp_price": float(row[9]) if not pd.isna(row[9]) else 0,
                    "peak_price": float(row[10]) if not pd.isna(row[10]) else 0,
                    "flat_price": float(row[11]) if not pd.isna(row[11]) else 0,
                    "valley_price": float(row[12]) if not pd.isna(row[12]) else 0,
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
            values = price_df[col].tolist()[:24]  # 只取前24个
            price_dict[month_num] = [
                0.0 if pd.isna(x) else float(x) for x in values
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


# -------------------------- 加载数据 --------------------------
grid_price = None
market_price_dict = {}
if os.path.exists(FILE_GRID_PRICE):
    grid_price = load_grid_price(FILE_GRID_PRICE)
else:
    st.error("❌ 未找到国网代购.xlsx，请检查路径")

if os.path.exists(FILE_PRICE):
    market_price_dict = load_market_price(FILE_PRICE)

df_elec = load_month_elec(FILE_ELEC)
df_day = load_day_elec(FILE_DAY_ELEC)

if df_day is None:
    st.error("❌ 日用电量数据文件缺失，检查路径")

# 构建价格字典（年月字符串key）
price_dict_str = {}
for m, vals in market_price_dict.items():
    price_dict_str[f"2026-{m:02d}"] = vals


# -------------------------- 24时段峰平谷划分工具函数 --------------------------
def get_period_type_map(month_sel):
    p_type = {}
    for i in range(1, 7):
        p_type[i] = "谷段"
    for i in range(12, 15):
        p_type[i] = "谷段"
    for i in range(7, 12):
        p_type[i] = "平段"
    for i in range(15, 17):
        p_type[i] = "平段"
    p_type[24] = "平段"
    for i in range(17, 24):
        p_type[i] = "高峰"
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
        filter_start_date = st.date_input("📅 起始日期", min_date, min_value=min_date, max_value=max_date, key="filter_start")
    with col_date2:
        filter_end_date = st.date_input("📅 结束日期", max_date, min_value=min_date, max_value=max_date, key="filter_end")
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

    # 分时图表（浅色主题）
    st.subheader("📈 分时用电量 & 市场均价")
    price_chart_type = st.radio("均价显示", ["柱状", "折线"], index=0, horizontal=True, key="price_chart_type", label_visibility="collapsed")
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
            "tooltip": {"trigger": "axis", "textStyle": {"color": "#333"}},
            "legend": {"data": legend, "textStyle": {"color": "#333"}, "top": 0},
            "toolbox": {
                "left": "center",
                "bottom": 8,
                "textStyle": {"color": "#333"},
                "feature": {
                    "dataZoom": {"yAxisIndex": "none"},
                    "restore": {"title": "重置"},
                    "saveAsImage": {"title": "下载图片"}
                }
            },
            "grid": {"left": "5%", "right": "6%", "bottom": "22%", "top": "20%", "containLabel": True},
            "xAxis": {"type": "category", "data": x_axis, "axisLabel": {"color": "#333", "rotate": 30},
                      "axisLine": {"lineStyle": {"color": "#ccc"}}, "splitLine": {"show": False}},
            "yAxis": [
                {"type": "value", "name": "用电量(MWh)", "nameTextStyle": {"color": "#333"},
                 "axisLabel": {"color": "#333"}, "splitLine": {"lineStyle": {"color": "#eee", "type": "dashed"}}},
                {"type": "value", "name": "均价(元/MWh)", "nameTextStyle": {"color": "#ff8a65"},
                 "axisLabel": {"color": "#ff8a65"}, "splitLine": {"show": False}, "position": "right"}
            ],
            "dataZoom": [{"type": "slider", "height": 16, "bottom": 10, "textStyle": {"color": "#333"}}],
            "series": series
        }
        st_echarts(opt_main, height="480px")
    else:
        st.info("筛选无数据，无法展示曲线")
    st.caption("提示：底部工具栏可重置视图、下载图表")

    # 峰平谷环形图 & 用户条形图
    st.markdown("---")
    col_pie, col_bar = st.columns([1, 1], gap="large")
    if not hist_data.empty:
        user_sum = hist_data.groupby("名称")["总用电量"].sum().reset_index()
        chart_h = max(420, len(user_sum) * 35)
    else:
        chart_h = 420
    # 峰平谷环形图
    with col_pie:
        st.subheader("🥧 峰平谷用电量占比")
        st.caption("谷0-6/11-14 | 平6-11/14-16/23-24 | 高峰16-23")
        if not filtered.empty:
            p_cols = [f"段{i}" for i in range(1, 25)]
            total_p = filtered[p_cols].sum()
            m_list = filtered['月份'].unique()
            has_summer = any(x in [7, 8] for x in m_list)
            has_winter = any(x in [1, 12] for x in m_list)
            valley = total_p[["段1","段2","段3","段4","段5","段6","段12","段13","段14"]].sum()
            flat = total_p[["段7","段8","段9","段10","段11","段15","段16","段24"]].sum()
            peak_all = total_p[["段17","段18","段19","段20","段21","段22","段23"]].sum()
            s_peak, w_peak, normal_peak = 0, 0, peak_all
            if has_summer:
                s_peak = total_p[["段20","段21"]].sum()
                normal_peak -= s_peak
            if has_winter:
                w_peak = total_p[["段19","段20"]].sum()
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
                "tooltip": {"trigger": "item", "textStyle": {"color": "#333"}, "formatter": "{b}: {c} MWh ({d}%)"},
                "legend": {"textStyle": {"color": "#333"}, "left": "left"},
                "series": [{
                    "type": "pie",
                    "radius": ["40%", "70%"],
                    "data": pie_data,
                    "color": pie_color,
                    "label": {"color": "#333", "formatter": "{b}\n{c} MWh ({d}%)", "show": True}
                }]
            }
            st_echarts(pie_opt, height=f"{chart_h}px")
        else:
            st.info("无数据")
    # 用户用电量横向条形图
    with col_bar:
        st.subheader("📊 当月全部用户用电量排名")
        if not hist_data.empty:
            user_total = hist_data.groupby("名称")["总用电量"].sum().reset_index().sort_values("总用电量", ascending=True)
            total_sum = user_total["总用电量"].sum()
            bar_data = []
            for _, row in user_total.iterrows():
                val = round(row["总用电量"], 2)
                pct = (val / total_sum * 100) if total_sum > 0 else 0
                pct_round = round(pct, 1)
                bar_data.append({
                    "value": val,
                    "percent": pct_round,
                    "label": {"show": True, "position": "right", "color": "#333", "formatter": f"{val} MWh ({pct_round}%)"}
                })
            bar_opt = {
                "tooltip": {"trigger": "axis", "textStyle": {"color": "#333"}, "formatter": "{b}<br/>电量: {c} MWh"},
                "grid": {"left": "18%", "right": "18%", "bottom": "5%", "top": "5%", "containLabel": True},
                "xAxis": {"type": "value", "axisLabel": {"color": "#333"}},
                "yAxis": {"type": "category", "data": user_total["名称"].tolist(), "axisLabel": {"color": "#333"}},
                "series": [{
                    "type": "bar",
                    "data": bar_data,
                    "barWidth": "60%",
                    "itemStyle": {
                        "color": {"type": "linear", "x": 0, "y": 0, "x2": 1, "y2": 0,
                                  "colorStops": [{"offset": 0, "color": "#2a5caa"}, {"offset": 1, "color": "#5993ff"}]},
                        "borderRadius": [0, 4, 4, 0]
                    }
                }]
            }
            st_echarts(bar_opt, height=f"{chart_h}px")
        else:
            st.info("当月无用户数据")
    # 每日总用电量趋势图
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
                "tooltip": {"trigger": "axis", "textStyle": {"color": "#333"}, "formatter": "{b}<br/>总用电量: {c} MWh"},
                "grid": {"left": "5%", "right": "5%", "bottom": "12%", "top": "10%", "containLabel": True},
                "xAxis": {
                    "type": "category",
                    "data": x_axis,
                    "axisLabel": {"color": "#333", "rotate": 30},
                    "axisLine": {"lineStyle": {"color": "#ccc"}},
                    "splitLine": {"show": False}
                },
                "yAxis": {
                    "type": "value",
                    "name": "总电量 (MWh)",
                    "nameTextStyle": {"color": "#333"},
                    "axisLabel": {"color": "#333"},
                    "splitLine": {"lineStyle": {"color": "#eee", "type": "dashed"}}
                },
                "series": [{
                    "name": "每日总电量",
                    "type": "line",
                    "smooth": True,
                    "symbol": "none",
                    "lineStyle": {"width": 3, "color": "#4fc3f7"},
                    "areaStyle": {"color": "rgba(79, 195, 247, 0.2)"},
                    "data": y_data,
                    "markLine": {"data": [{"type": "average", "name": "日均电量"}],
                                 "lineStyle": {"color": "#ffb74d", "type": "dashed"}}
                }],
                "dataZoom": [{"type": "slider", "height": 16, "bottom": 5, "textStyle": {"color": "#333"}}]
            }
            st_echarts(day_chart_opt, height="400px")
        else:
            st.info("当前筛选条件下无日用电量数据")
    else:
        st.warning("未找到日用电量数据文件，请检查路径")


# ===================== 模块二：价格测算 + 报告导出 =====================
else:
    st.title("💰 电价测算工具")
    st.write("📂 代码版本：2026-07-20 v5")  # 可确认代码更新

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

        # 使用 text_input 避免浮点数舍入
        float_input = st.text_input(
            "市场化浮动参数(元/kWh，可正可负)",
            value="0.000",
            help="请输入数字，如 0.006 或 -0.006"
        )
        try:
            float_param = float(float_input)
        except ValueError:
            st.error("❌ 请输入有效的数字（如 0.006 或 -0.006）")
            float_param = 0.0

        total_kwh = st.number_input("总用电量 kWh", min_value=0.00, value=0.00, step=1000.00)

        # ---------- 容需量电费（修正逻辑） ----------
        cap_cost = 0.0
        total_capacity = 0.0
        if type_sel == "大工业用电":
            st.markdown("#### 容需量电费")
            cap_mode = st.selectbox("计费方式", ["不计容需量", "按容量电价", "按需量电价"])

            if cap_mode == "按容量电价" and price_info["cap_trans"] > 0:
                contract_capacity = st.number_input("合同变压器容量 kVA", min_value=0.00, value=0.00, step=10.00)
                cap_cost = contract_capacity * price_info["cap_trans"]
                total_capacity = contract_capacity

            elif cap_mode == "按需量电价" and price_info["cap_max"] > 0:
                actual_max_demand = st.number_input("当月实际最大需量 kW", min_value=0.00, value=0.00, step=10.00)
                cap_cost = actual_max_demand * price_info["cap_max"]
                total_capacity = st.number_input("合同变压器总容量 kVA（用于九折判断）", min_value=0.0, value=0.0, step=10.0)

            # 九折判断
            if cap_mode != "不计容需量" and total_capacity > 0 and total_kwh > 0:
                avg_kwh_per_kva = total_kwh / total_capacity
                if avg_kwh_per_kva >= 260:
                    cap_cost *= 0.9
                    st.success(f"✅ 月均单台容量用电量 {avg_kwh_per_kva:.1f} kWh/kVA ≥ 260，基本电费已打九折")
                else:
                    st.info(f"ℹ️ 月均单台容量用电量 {avg_kwh_per_kva:.1f} kWh/kVA，未达到九折标准（需 ≥ 260）")
            elif cap_mode != "不计容需量" and total_capacity == 0:
                st.warning("⚠️ 合同变压器总容量为 0，无法判断九折条件，请填写正确的合同容量")

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
    per_flat = total_flat / cnt_flat if cnt_flat > 0 else 0
    per_valley = total_valley / cnt_valley if cnt_valley > 0 else 0

    month_market_prices = []
    if month_sel in market_price_dict:
        month_market_prices = [p / 1000.0 for p in market_price_dict[month_sel]]

    # ---------- 国网代购测算结果 ----------
    st.markdown("---")
    st.subheader("🧮 国网代购测算结果")

    base_buy = price_info["purchase_price"]
    jian_buy, peak_buy, flat_buy, valley_buy = base_buy * 1.9, base_buy * 1.7, base_buy * 1.0, base_buy * 0.3
    jian_all, peak_all, flat_all, valley_all = price_info["sharp_price"], price_info["peak_price"], price_info["flat_price"], price_info["valley_price"]

    avg_buy = jian_pct / 100 * jian_buy + peak_pct / 100 * peak_buy + flat_pct / 100 * flat_buy + valley_pct / 100 * valley_buy
    avg_all = jian_pct / 100 * jian_all + peak_pct / 100 * peak_all + flat_pct / 100 * flat_all + valley_pct / 100 * valley_all

    elec_total = total_kwh * avg_all
    all_total = elec_total + cap_cost
    naked_total_fee = total_kwh * avg_buy

    col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
    with col_m1:
        st.metric("⚡ 加权裸电单价", f"{avg_buy:.4f} 元/kWh")
    with col_m2:
        st.metric("💰 裸电总电费", f"{naked_total_fee:,.2f} 元")
    with col_m3:
        st.metric("⚙️ 基本电费(容需量)", f"{cap_cost:,.2f} 元")
    with col_m4:
        st.metric("🏠 加权到户单价", f"{avg_all:.4f} 元/kWh")
    with col_m5:
        st.metric("💸 月度总电费(全费用)", f"{all_total:,.2f} 元")

    if cap_cost > 0:
        extra_fee = elec_total - naked_total_fee
        st.caption(f"费用拆分：裸电购电成本 {naked_total_fee:,.2f} 元 | 输配电+基金附加 {extra_fee:,.2f} 元 | 容需量电费 {cap_cost:,.2f} 元")
    else:
        extra_fee = elec_total - naked_total_fee
        st.caption(f"费用拆分：裸电购电成本 {naked_total_fee:,.2f} 元 | 输配电+基金附加 {extra_fee:,.2f} 元")

    # ---------- 市场化电价测算 ----------
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
        mkt_total_fee = total_kwh * mkt_avg_all + cap_cost

    col_mk1, col_mk2, col_mk3, col_mk4, col_mk5 = st.columns(5)
    with col_mk1:
        st.metric("⚡ 市场化加权裸电单价", f"{mkt_avg_buy:.4f} 元/kWh")
    with col_mk2:
        st.metric("💰 市场化裸电总电费", f"{mkt_naked_total:,.2f} 元")
    with col_mk3:
        st.metric("⚙️ 基本电费(容需量)", f"{cap_cost:,.2f} 元")
    with col_mk4:
        st.metric("🏠 市场化加权到户单价", f"{mkt_avg_all:.4f} 元/kWh")
    with col_mk5:
        st.metric("💸 市场化月度总电费(含容需量)", f"{mkt_total_fee:,.2f} 元")

    st.caption(
        f"附加参数（取自国网代购表·{volt_sel}）："
        f"上网线损 {line_loss_price:.5f} | "
        f"输配电 {trans_price:.5f} | "
        f"系统运行费 {system_fee:.5f} | "
        f"政府基金 {gov_fee:.5f} 元/kWh | "
        f"浮动参数 {float_param:.4f} 元/kWh"
    )

    # ---------- 24时段对比图表 ----------
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
        "tooltip": {"trigger": "axis", "textStyle": {"color": "#333"}},
        "legend": {
            "data": ["分时电量", "市场分时均价", "国网代购裸电价"],
            "textStyle": {"color": "#333"},
            "top": 0
        },
        "grid": {"left": "5%", "right": "6%", "bottom": "12%", "top": "15%", "containLabel": True},
        "xAxis": {
            "type": "category",
            "data": time_labels,
            "axisLabel": {"color": "#333", "rotate": 30},
            "axisLine": {"lineStyle": {"color": "#ccc"}},
            "splitLine": {"show": False}
        },
        "yAxis": [
            {
                "type": "value",
                "name": "分时电量(kWh)",
                "nameTextStyle": {"color": "#333"},
                "axisLabel": {"color": "#333"},
                "splitLine": {"lineStyle": {"color": "#eee", "type": "dashed"}}
            },
            {
                "type": "value",
                "name": "电价(元/kWh)",
                "nameTextStyle": {"color": "#ff8a65"},
                "axisLabel": {"color": "#ff8a65"},
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
                    columns=["时段编号", "时间范围", "时段类型", "常规裸电价", "市场化裸电价",
                             "常规到户价", "市场化到户价", "电量(kWh)"]
                )

            df_24h = gen_24h_data()
            csv_data = df_24h.to_csv(index=False, encoding="utf-8-sig")
            st.download_button("📥 导出CSV", data=csv_data,
                               file_name=f"24时段分时电价_{area_sel}_{month_sel}月.csv",
                               mime="text/csv", use_container_width=True)
        st.dataframe(df_24h, hide_index=True, width="stretch", height=360)

    # ---------- 导出报告 ----------
    st.markdown("---")
    with st.expander("📊 生成电费成本分析报告", expanded=False):
        st.markdown("点击下方按钮生成并预览完整报告（含用电结构、成本对比、优化建议）")
        
        contract_capacity_report = total_capacity
        
        if total_kwh > 0:
            report_data = generate_report_data(
                area_sel, month_sel, type_sel, volt_sel,
                total_kwh, contract_capacity_report,
                price_info, period_type_map,
                jian_pct, peak_pct, flat_pct, valley_pct,
                avg_buy, avg_all, all_total, cap_cost,
                mkt_avg_buy, mkt_avg_all, mkt_total_fee, mkt_naked_total,
                naked_total_fee, elec_total, add_total_per_kwh,
                float_param, per_sharp, per_peak, per_flat, per_valley,
                market_price_dict
            )
            
            col_preview, col_export = st.columns([1, 1])
            
            with col_preview:
                st.markdown("#### 📄 报告预览")
                html_report = generate_html_report(report_data)
                st.components.v1.html(html_report, height=800, scrolling=True)
            
            with col_export:
                st.markdown("#### � 导出报告")
                
                excel_data, excel_error = generate_excel_report(report_data)
                if excel_data is not None:
                    st.download_button(
                        label="📥 导出 Excel 报告",
                        data=excel_data,
                        file_name=f"电费成本分析报告_{area_sel}_{month_sel}月.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        key="download_excel"
                    )
                else:
                    st.error(f"❌ Excel导出失败：{excel_error}")
                
                html_bytes = html_report.encode('utf-8')
                st.download_button(
                    label="🌐 导出 HTML 报告",
                    data=html_bytes,
                    file_name=f"电费成本分析报告_{area_sel}_{month_sel}月.html",
                    mime="text/html",
                    use_container_width=True,
                    key="download_html"
                )
        else:
            st.warning("⚠️ 请先输入总用电量，才能生成报告")