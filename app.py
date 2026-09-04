# -*- coding: utf-8 -*-
"""
紫微斗數 AI 排盤 —— Streamlit 網頁版
======================================
部署到 Streamlit Community Cloud 後即可得到一個永久網址。
本檔案只負責畫面／互動，核心排盤邏輯全部在 ziwei.py（已獨立驗證過）。
"""

import datetime
import streamlit as st
import streamlit.components.v1 as components

from ziwei import (
    ZiWeiChart, PALACE_ORDER, MAIN_STARS, event_hint,
    STAR_NATURE, star_sihua_hint, SIHUA_NAMES, ten_god, STEM_ELEMENT,
)

st.set_page_config(page_title="紫微斗數 AI 排盤", page_icon="🔮", layout="wide")

# ----------------------------------------------------------------------------
# 版面：輸入區（側邊欄）
# ----------------------------------------------------------------------------
st.sidebar.header("🔮 輸入生辰")
name = st.sidebar.text_input("姓名（選填）", value="")
gender_label = st.sidebar.radio("性別", ["男", "女"], horizontal=True)
gender = "M" if gender_label == "男" else "F"

birth_date = st.sidebar.date_input(
    "陽曆出生日期", value=None,
    min_value=datetime.date(1920, 1, 1), max_value=datetime.date(2036, 9, 4),
    format="YYYY-MM-DD",
)
col_h, col_m = st.sidebar.columns(2)
birth_hour = col_h.selectbox("小時（24小時制）", list(range(24)), index=2)
birth_minute = col_m.selectbox("分鐘", list(range(60)), index=0)

st.sidebar.caption("⏰ 時辰對照：23:00~00:59子、01:00~02:59丑、03:00~04:59寅…以此類推，每兩小時一個時辰。")
submitted = st.sidebar.button("開始排盤", type="primary", width="stretch")

st.sidebar.markdown("---")
st.sidebar.caption("本程式為傳統紫微斗數命理排盤工具，結果僅供參考娛樂，人生際遇仍取決於自身努力與選擇。")

# ----------------------------------------------------------------------------
# 標題
# ----------------------------------------------------------------------------
st.title("🔮 紫微斗數 AI 排盤")
st.caption("輸入陽曆生辰，立即取得完整十二宮命盤、十四主星／十四輔星、生年四化與宮干飛星分析。")

if not submitted:
    st.info("請在左側輸入生辰資料，按下「開始排盤」查看命盤。")
    st.stop()

if birth_date is None:
    st.error("請先選擇出生日期。")
    st.stop()

# ----------------------------------------------------------------------------
# 排盤
# ----------------------------------------------------------------------------
try:
    chart = ZiWeiChart(
        birth_date.year, birth_date.month, birth_date.day,
        birth_hour, birth_minute, gender,
    )
except Exception as e:
    st.error(f"排盤失敗，請確認日期時間是否正確（{e}）")
    st.stop()

display_name = name.strip() or "命主"

# ----------------------------------------------------------------------------
# 基本資訊卡
# ----------------------------------------------------------------------------
ec = chart.lunar.getEightChar()
c1, c2, c3, c4 = st.columns(4)
c1.metric("農曆生日", f"{chart.lunar_year}年{'閏' if chart.is_leap_month else ''}{chart.lunar_month}月{chart.lunar_day}日")
c2.metric("時辰", f"{chart.hour_branch}時")
c3.metric("命局", chart.ju_name)
c4.metric("納音", chart.ming_nayin)

c5, c6, c7 = st.columns(3)
c5.metric("八字", f"{ec.getYear()} {ec.getMonth()} {ec.getDay()} {ec.getTime()}")
c6.metric("命宮", f"{chart.palace_gz(chart.ming_idx)}（{chart.branch_of[chart.ming_idx]}宮）")
c7.metric("身宮", f"{chart.palace_gz(chart.shen_idx)}（{chart.palace_name(chart.shen_idx)}宮）")

st.markdown("---")

# ----------------------------------------------------------------------------
# 查詢日期（同時驅動命盤中央的紫微大限流年 與 八字大運流年）
# ----------------------------------------------------------------------------
today = datetime.date.today()
min_d = datetime.date(birth_date.year, 1, 1)
max_d = datetime.date(birth_date.year + 120, 12, 31)
default_d = today if min_d <= today <= max_d else min_d
target_date = st.date_input(
    "📅 查詢西元日期（決定命盤中央顯示的大限／流年／八字大運）",
    value=default_d, min_value=min_d, max_value=max_d, format="YYYY-MM-DD",
)
liu = chart.liuyue_analysis(target_date.year, target_date.month, target_date.day)
bazi_dayun = chart.bazi_dayun_by_year(target_date.year)
bazi_liunian_gz = chart.bazi_liunian_ganzhi(target_date.year)
if bazi_dayun is None or not bazi_dayun.getGanZhi():
    bazi_dayun_str = "尚未起運"
else:
    bazi_dayun_str = f"{bazi_dayun.getGanZhi()}（{bazi_dayun.getStartAge()}-{bazi_dayun.getEndAge()}歲）"

st.markdown("---")

# ----------------------------------------------------------------------------
# 命盤格局（傳統 4x4 排盤圖）
# ----------------------------------------------------------------------------
BRANCH_GRID_POS = {
    5: (1, 1), 6: (1, 2), 7: (1, 3), 8: (1, 4),
    4: (2, 1),                       9: (2, 4),
    3: (3, 1),                       10: (3, 4),
    2: (4, 1), 1: (4, 2), 0: (4, 3), 11: (4, 4),
}
SIHUA_COLOR = {"化祿": "#2e7d32", "化權": "#ef6c00", "化科": "#1565c0", "化忌": "#c62828"}


def render_chart_html(c: ZiWeiChart, title: str, liu: dict, bazi_dayun_str: str, bazi_liunian_gz: str) -> str:
    boxes = []
    for i in range(12):
        row, col = BRANCH_GRID_POS[i]
        stars = c.palace_stars[i]
        main = [s for s in stars if s in MAIN_STARS]
        minor = [s for s in stars if s not in MAIN_STARS]
        pname = c.palace_name(i) + "宮"
        a0, a1 = c.dayun_of[i]

        main_html = ""
        for s in main:
            tag = c.birth_sihua.get(s)
            if tag:
                color = SIHUA_COLOR[tag]
                main_html += (f'<span class="star main">{s}'
                              f'<span class="badge" style="background:{color}">{tag[-1]}</span></span>')
            else:
                main_html += f'<span class="star main">{s}</span>'
        if not main_html:
            main_html = '<span class="star empty">（空宮）</span>'

        minor_html = "".join(f'<span class="star minor">{s}</span>' for s in minor)

        marks = []
        if i == c.ming_idx:
            marks.append('<span class="mark ming">命宮</span>')
        if i == c.shen_idx:
            marks.append('<span class="mark shen">身宮</span>')

        boxes.append(f'''
        <div class="palace" style="grid-row:{row};grid-column:{col};">
          <div class="p-top">
            <span class="age">{a0}-{a1}</span>
            <span class="gz">{c.palace_gz(i)}</span>
          </div>
          <div class="p-main">{main_html}</div>
          <div class="p-minor">{minor_html}</div>
          <div class="p-bottom">{"".join(marks)}<span class="pname">{pname}</span></div>
        </div>''')

    bp = c.bazi_pillars
    if liu["dayun_idx"] is not None:
        a0, a1 = liu["dayun_range"]
        ziwei_dayun_str = f"{c.palace_name(liu['dayun_idx'])}宮（{a0}-{a1}歲）"
    else:
        ziwei_dayun_str = "尚未起運"

    center = f'''
        <div class="palace center" style="grid-row:2/4;grid-column:2/4;">
          <div class="center-title">{title}</div>
          <div class="center-line">生年干支：{c.year_gz}　性別：{"男" if c.gender=="M" else "女"}</div>
          <div class="center-line">農曆：{c.lunar_year}年{chr(9702)}{c.lunar_month}月{c.lunar_day}日 {c.hour_branch}時</div>
          <div class="center-line">命局：{c.ju_name}（{c.ming_nayin}）</div>
          <div class="center-line">命宮：{c.palace_gz(c.ming_idx)}　身宮：{c.palace_gz(c.shen_idx)}（{c.palace_name(c.shen_idx)}宮）</div>
          <div class="center-sep"></div>
          <div class="center-line">四柱八字：{bp['year']}　{bp['month']}　{bp['day']}　{bp['time']}</div>
          <div class="center-sep"></div>
          <div class="center-line">虛歲 {liu['age']}　｜　紫微大限：{ziwei_dayun_str}　流年：{liu['liu_stem']}{liu['liu_branch']}</div>
          <div class="center-line">八字大運：{bazi_dayun_str}　流年：{bazi_liunian_gz}</div>
        </div>'''

    html = f'''
    <html><head><meta charset="utf-8"><style>
      :root {{
        --bg:#fafaf7; --card:#ffffff; --border:#d8d2c4; --text:#2b2b2b;
        --sub:#7a7466; --accent:#8a2e2e;
      }}
      @media (prefers-color-scheme: dark) {{
        :root {{ --bg:#1e1c19; --card:#2a2724; --border:#4a453c; --text:#eae6dd; --sub:#b8b0a0; --accent:#e0a458; }}
      }}
      * {{ box-sizing:border-box; }}
      body {{ margin:0; background:var(--bg); font-family:"Microsoft JhengHei","PingFang TC",sans-serif; }}
      .grid {{
        display:grid; grid-template-columns:repeat(4,1fr); grid-template-rows:repeat(4,150px);
        gap:4px; padding:6px; background:var(--border);
      }}
      .palace {{
        background:var(--card); border:1px solid var(--border); padding:6px 8px;
        display:flex; flex-direction:column; justify-content:space-between; overflow:hidden;
      }}
      .p-top {{ display:flex; justify-content:space-between; font-size:11px; color:var(--sub); }}
      .p-main {{ line-height:1.5; }}
      .star.main {{ font-size:16px; font-weight:700; color:var(--text); margin-right:6px; position:relative; }}
      .star.empty {{ font-size:13px; color:var(--sub); }}
      .badge {{
        display:inline-block; color:#fff; font-size:10px; border-radius:3px;
        padding:0 3px; margin-left:2px; vertical-align:middle;
      }}
      .p-minor {{ font-size:11px; color:var(--sub); line-height:1.6; }}
      .star.minor {{ margin-right:5px; }}
      .p-bottom {{ display:flex; justify-content:space-between; align-items:center; font-size:12px; }}
      .pname {{ font-weight:600; color:var(--text); }}
      .mark {{ font-size:10px; border-radius:3px; padding:0 4px; margin-right:3px; color:#fff; }}
      .mark.ming {{ background:var(--accent); }}
      .mark.shen {{ background:#4a6fa5; }}
      .center {{ align-items:center; justify-content:center; text-align:center; background:var(--bg); border:none; }}
      .center-title {{ font-size:17px; font-weight:700; margin-bottom:4px; color:var(--accent); }}
      .center-line {{ font-size:11.5px; color:var(--text); margin:1px 0; }}
      .center-sep {{ width:60%; height:1px; background:var(--border); margin:4px auto; }}
    </style></head>
    <body><div class="grid">{"".join(boxes)}{center}</div></body></html>
    '''
    return html


components.html(
    render_chart_html(chart, display_name, liu, bazi_dayun_str, bazi_liunian_gz),
    height=650, scrolling=False,
)

st.caption("色塊：綠=化祿　橘=化權　藍=化科　紅=化忌（生年四化）")
st.caption(f"命盤中央依查詢日期 {target_date.isoformat()} 顯示紫微大限流年與八字大運流年，以利紫微／八字合參。")
st.markdown("---")

# ----------------------------------------------------------------------------
# 十二宮明細表
# ----------------------------------------------------------------------------
tab1, tab2, tab3, tab5, tab4 = st.tabs(
    ["📋 十二宮明細", "🌀 宮干四化飛星", "📅 大限流年流月應事", "🀄 八字十神／大運", "📝 紫微八字 AI 提示詞（可複製）"]
)

with tab1:
    rows = []
    for i in range(12):
        stars = chart.palace_stars[i]
        main = [s for s in stars if s in MAIN_STARS]
        minor = [s for s in stars if s not in MAIN_STARS]
        sihua_tags = [f"{s}{chart.birth_sihua[s]}" for s in stars if s in chart.birth_sihua]
        a0, a1 = chart.dayun_of[i]
        mark = "／".join(
            (["命宮"] if i == chart.ming_idx else []) + (["身宮"] if i == chart.shen_idx else [])
        )
        rows.append({
            "宮位": chart.palace_name(i) + "宮",
            "干支": chart.palace_gz(i),
            "大限": f"{a0}-{a1}",
            "標記": mark,
            "主星": "、".join(main) or "空宮",
            "輔星／煞星": "、".join(minor) or "無",
            "生年四化": "、".join(sihua_tags) or "",
        })
    st.dataframe(rows, width="stretch", hide_index=True)

with tab2:
    st.caption("將每個宮位的宮干代入十干四化表，飛入其化祿／化權／化科／化忌所在的星曜與宮位，並結合該星曜的星性推斷具體應事——這是紫微斗數「飛星派」核心技法。")
    for offset, pname in enumerate(PALACE_ORDER):
        p_idx = (chart.ming_idx - offset) % 12
        stem = chart.stem_of[p_idx]
        with st.expander(f"{pname}宮（{chart.palace_gz(p_idx)}）　宮干：{stem}"):
            for r in chart.flying_sihua(p_idx):
                self_note = "　🔁 自化（回本宮）" if r["is_self"] else ""
                nature = STAR_NATURE.get(r["star"], "")
                st.write(f"・{pname}宮{stem}干　飛入　**{r['target_name']}宮**　{r['star']}{r['tag']}{self_note}")
                if nature:
                    st.caption(f"　　{r['star']}星性：{nature}")
                if r["hint"]:
                    st.write(f"　　→ {r['hint']}")

with tab3:
    st.caption("將本命四化、大限（十年運）、流年（該年）、流月（該月）四層疊加，觀察同一宮位是否被多層同類四化「疊」中——這是判斷該年該月吉凶輕重的重要依據，尤其疊忌、疊祿最值得留意。")
    st.caption(f"目前查詢日期：{target_date.isoformat()}（可於命盤上方調整）")

    lc1, lc2, lc3, lc4 = st.columns(4)
    lc1.metric("虛歲", liu["age"])
    if liu["dayun_idx"] is not None:
        a0, a1 = liu["dayun_range"]
        lc2.metric("大限宮位", f"{chart.palace_name(liu['dayun_idx'])}宮（{a0}-{a1}歲）",
                   f"大限干支：{liu['dayun_stem']}{chart.branch_of[liu['dayun_idx']]}")
    else:
        lc2.metric("大限宮位", "尚未起運", "早運前參考命宮／福德宮")
    lc3.metric("流年宮位", f"{chart.palace_name(liu['liu_palace_idx'])}宮",
               f"流年干支：{liu['liu_stem']}{liu['liu_branch']}")
    leap_note = "（閏月）" if liu["is_leap_month"] else ""
    lc4.metric("流月宮位", f"{chart.palace_name(liu['yue_palace_idx'])}宮",
               f"農曆{liu['lunar_month']}月{leap_note}，流月干：{liu['yue_stem']}")
    st.caption(f"流年斗君（該年正月起點）落於 {chart.branch_of[liu['doujun_idx']]}宮")

    st.markdown("#### 八字大運流年（合參對照）")
    bc1, bc2 = st.columns(2)
    bc1.metric("八字大運", bazi_dayun_str)
    bc2.metric("八字流年", bazi_liunian_gz)

    st.markdown("#### 各宮四化疊加與應事提示（星曜星性 × 宮干四化）")

    def _render_palace_detail(i):
        pname = chart.palace_name(i)
        items = liu["layers"][i]
        for layer, star, tag in items:
            nature = STAR_NATURE.get(star, "")
            shint = star_sihua_hint(star, tag)
            st.write(f"**{layer}**｜{star}{tag}　{'（'+nature+'）' if nature else ''}")
            if shint:
                st.write(f"→ {shint}")
        seen_tags = [t for t in SIHUA_NAMES if t in {tg for _, _, tg in items}]
        theme_lines = [event_hint(pname, t) for t in seen_tags if event_hint(pname, t)]
        if theme_lines:
            st.caption(f"{pname}宮主題：" + "／".join(theme_lines))

    any_shown = False
    # 疊宮（同類四化出現 2 次以上）優先顯示
    hot_palaces = sorted(liu["overlaps"].keys())
    for i in hot_palaces:
        any_shown = True
        pname = chart.palace_name(i)
        hot = liu["overlaps"][i]
        hot_str = "、".join(f"{t}×{n}" for t, n in hot.items())
        with st.container(border=True):
            st.markdown(f"**⚠ {pname}宮　疊：{hot_str}**")
            _render_palace_detail(i)

    other_palaces = [i for i in range(12) if liu["layers"][i] and i not in liu["overlaps"]]
    for i in other_palaces:
        any_shown = True
        pname = chart.palace_name(i)
        tag_str = "、".join(f"{layer}{star}{tag}" for layer, star, tag in liu["layers"][i])
        with st.expander(f"{pname}宮　{tag_str}"):
            _render_palace_detail(i)

    if not any_shown:
        st.info("該年三層四化未落於任何主星／輔星所在宮位。")

with tab5:
    st.caption("依淵海子平十神生剋原理，將四柱天干、地支藏干換算成十神，並列出完整八字大運，供與紫微命盤合參使用。")

    PILLAR_LABEL = {'year': '年柱', 'month': '月柱', 'day': '日柱', 'time': '時柱'}
    pillar_rows = []
    for pos in ('year', 'month', 'day', 'time'):
        gz = chart.bazi_pillars[pos]
        hidden = "、".join(f"{gan}({tg})" for gan, tg, _ in chart.bazi_branch_hidden[pos])
        pillar_rows.append({
            "四柱": PILLAR_LABEL[pos],
            "干支": gz,
            "天干十神": chart.bazi_stem_ten_god[pos],
            "地支藏干十神": hidden,
        })
    st.dataframe(pillar_rows, width="stretch", hide_index=True)

    total = chart.bazi_support_score + chart.bazi_drain_score
    support_pct = chart.bazi_support_score / total * 100 if total else 0
    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("日主", f"{chart.bazi_day_master}（{'男' if gender=='M' else '女'}命）")
    sc2.metric("幫身（比劫／印）加權", chart.bazi_support_score)
    sc3.metric("耗身（食傷／財／官殺）加權", chart.bazi_drain_score)
    st.progress(min(max(support_pct / 100, 0.0), 1.0), text=f"幫身佔比約 {support_pct:.0f}%（僅供粗略參考，非精確子平旺衰演算，實際仍需結合月令、通根、季節旺相休囚死綜合判斷）")

    st.markdown("#### 八字大運")
    dayun_rows = []
    for dy in chart.bazi_dayun_list:
        if dy.getIndex() < 1:
            continue
        gz = dy.getGanZhi()
        dayun_rows.append({
            "大運": gz,
            "天干十神": ten_god(chart.bazi_day_master, gz[0]),
            "起訖年齡": f"{dy.getStartAge()}-{dy.getEndAge()}歲",
            "起訖西元年": f"{dy.getStartYear()}-{dy.getEndYear()}",
            "目前": "👈" if dy.getStartYear() <= target_date.year <= dy.getEndYear() else "",
        })
    st.dataframe(dayun_rows, width="stretch", hide_index=True)
    st.caption(f"查詢日期 {target_date.isoformat()} 對應八字大運：{bazi_dayun_str}　八字流年：{bazi_liunian_gz}"
               f"（流年干支十神：{ten_god(chart.bazi_day_master, bazi_liunian_gz[0])}）")

with tab4:
    lines = []
    lines.append(f"※以下為「{display_name}」紫微斗數命盤＋八字四柱十神資料（紫微八字合參版），可複製貼給 AI（ChatGPT／Claude／Grok…）進行深入解讀。")
    lines.append("")
    lines.append(f"性別：{'男' if gender=='M' else '女'}")
    lines.append(f"陽曆生日：{birth_date.year}年{birth_date.month}月{birth_date.day}日 {birth_hour}時{birth_minute}分")
    lines.append(f"農曆生日：{chart.lunar_year}年{'閏' if chart.is_leap_month else ''}{chart.lunar_month}月{chart.lunar_day}日 {chart.hour_branch}時")
    lines.append(f"八字：{ec.getYear()} {ec.getMonth()} {ec.getDay()} {ec.getTime()}")
    lines.append(f"命局：{chart.ju_name}（納音：{chart.ming_nayin}）")
    lines.append(f"命宮：{chart.palace_gz(chart.ming_idx)}（{chart.branch_of[chart.ming_idx]}宮）　身宮：{chart.palace_gz(chart.shen_idx)}（{chart.palace_name(chart.shen_idx)}宮）")
    lines.append("")

    lines.append("【八字四柱十神】")
    for pos, label in (('year', '年柱'), ('month', '月柱'), ('day', '日柱'), ('time', '時柱')):
        gz = chart.bazi_pillars[pos]
        hidden = "、".join(f"{gan}({tg})" for gan, tg, _ in chart.bazi_branch_hidden[pos])
        lines.append(f"{label}：{gz}　天干十神：{chart.bazi_stem_ten_god[pos]}　地支藏干：{hidden}")
    lines.append(f"日主：{chart.bazi_day_master}{STEM_ELEMENT[chart.bazi_day_master]}　幫身(比劫/印)加權：{chart.bazi_support_score}　"
                 f"耗身(食傷/財/官殺)加權：{chart.bazi_drain_score}（僅粗略參考，非精確子平旺衰演算）")
    lines.append("八字大運（依節氣精算起運，陽男陰女順排、陰男陽女逆排）：")
    for dy in chart.bazi_dayun_list:
        if dy.getIndex() < 1:
            continue
        gz = dy.getGanZhi()
        cur_note = "　←目前查詢日期落於此運" if dy.getStartYear() <= target_date.year <= dy.getEndYear() else ""
        lines.append(f"・{gz}（{ten_god(chart.bazi_day_master, gz[0])}）　{dy.getStartAge()}-{dy.getEndAge()}歲"
                     f"（{dy.getStartYear()}-{dy.getEndYear()}）{cur_note}")
    lines.append("")

    lines.append("【紫微十二宮】")
    for offset, pname in enumerate(PALACE_ORDER):
        p_idx = (chart.ming_idx - offset) % 12
        stars = chart.palace_stars[p_idx]
        main = [s for s in stars if s in MAIN_STARS]
        minor = [s for s in stars if s not in MAIN_STARS]
        a0, a1 = chart.dayun_of[p_idx]
        lines.append(f"【{pname}宮：宮位在{chart.palace_gz(p_idx)}，大限{a0}-{a1}歲】")
        lines.append(f"主星：{'、'.join(main) if main else '無（空宮，需借對宮星曜參看）'}")
        lines.append(f"輔星／煞星：{'、'.join(minor) if minor else '無'}")
        stem = chart.stem_of[p_idx]
        for r in chart.flying_sihua(p_idx):
            self_note = "（自化，化氣回本宮）" if r["is_self"] else ""
            lines.append(f"・{pname}宮{stem}干飛入{r['target_name']}宮{r['star']}{r['tag']}{self_note}")
        lines.append("")

    lines.append(f"【{target_date.isoformat()} 大限流年流月 × 八字大運流年（合參）】虛歲 {liu['age']}")
    if liu["dayun_idx"] is not None:
        a0, a1 = liu["dayun_range"]
        lines.append(f"紫微大限：{chart.palace_name(liu['dayun_idx'])}宮（{a0}-{a1}歲，大限干：{liu['dayun_stem']}）")
    else:
        lines.append("紫微大限：尚未起運")
    lines.append(f"紫微流年：{liu['liu_stem']}{liu['liu_branch']}年，流年命宮在 {chart.palace_name(liu['liu_palace_idx'])}宮")
    leap_note2 = "（閏月）" if liu["is_leap_month"] else ""
    lines.append(f"紫微流月：農曆{liu['lunar_month']}月{leap_note2}，流月落於 {chart.palace_name(liu['yue_palace_idx'])}宮（流月干：{liu['yue_stem']}）")
    lines.append(f"八字大運：{bazi_dayun_str}（十神：{ten_god(chart.bazi_day_master, bazi_dayun.getGanZhi()[0]) if bazi_dayun and bazi_dayun.getGanZhi() else '尚未起運'}）"
                 f"　八字流年：{bazi_liunian_gz}（十神：{ten_god(chart.bazi_day_master, bazi_liunian_gz[0])}）")
    for i in range(12):
        items = liu["layers"][i]
        if not items:
            continue
        pname_i = chart.palace_name(i)
        tag_str = "、".join(f"{layer}{star}{tag}" for layer, star, tag in items)
        hot = liu["overlaps"].get(i)
        hot_str = "（疊：" + "、".join(f"{t}x{n}" for t, n in hot.items()) + "）" if hot else ""
        lines.append(f"・{pname_i}宮：{tag_str}{hot_str}")
    ai_text = "\n".join(lines)
    st.text_area("複製以下內容給 AI 分析（紫微＋八字合參版）：", ai_text, height=400)
    st.download_button("⬇️ 下載為文字檔", ai_text, file_name=f"{display_name}_紫微斗數.txt")

st.markdown("---")
st.caption("© 紫微斗數 AI 排盤工具｜排盤邏輯依傳統紫微斗數安星訣（五虎遁、定紫微訣、十干四化等）計算，僅供命理研究與參考。")
