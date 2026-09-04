# -*- coding: utf-8 -*-
"""
紫微斗數排盤與飛星四化分析程式
================================
輸入：陽曆出生日期時間、性別
輸出：
  1. 十二宮完整排盤（宮位干支、十四主星、十四輔星、生年四化）
  2. 十二宮「宮干四化飛星」分析（命宮、財帛、官祿…宮干四化飛入何宮何星）
  3. 文字版命盤 + 簡易論斷重點

依賴：lunar_python（農曆/干支換算，已安裝）
用法：
    python ziwei.py                      # 使用內建範例（吳明森 1961-03-15 02:59 男）
    python ziwei.py 1990-08-23 14:20 M    # 自訂：陽曆日期 時:分 M/F
"""

import sys
import io
from lunar_python import Solar

if sys.platform.startswith("win"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# ----------------------------------------------------------------------------
# 基礎資料
# ----------------------------------------------------------------------------
STEMS = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
BRANCHES = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

# ----------------------------------------------------------------------------
# 八字（子平）十神與地支藏干
# ----------------------------------------------------------------------------
STEM_ELEMENT = {
    '甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
    '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水',
}
STEM_YANG = {s: (i % 2 == 0) for i, s in enumerate(STEMS)}  # 甲丙戊庚壬為陽
ELEMENT_GENERATES = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
ELEMENT_CONTROLS = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}

# 地支藏干：(天干, 權重)，權重僅用於粗略的日主旺衰參考，非精確子平算法
ZHI_HIDE_GAN = {
    '子': [('癸', 1.0)],
    '丑': [('己', 0.6), ('癸', 0.3), ('辛', 0.1)],
    '寅': [('甲', 0.6), ('丙', 0.3), ('戊', 0.1)],
    '卯': [('乙', 1.0)],
    '辰': [('戊', 0.6), ('乙', 0.3), ('癸', 0.1)],
    '巳': [('丙', 0.6), ('庚', 0.3), ('戊', 0.1)],
    '午': [('丁', 0.7), ('己', 0.3)],
    '未': [('己', 0.6), ('丁', 0.3), ('乙', 0.1)],
    '申': [('庚', 0.6), ('壬', 0.3), ('戊', 0.1)],
    '酉': [('辛', 1.0)],
    '戌': [('戊', 0.6), ('辛', 0.3), ('丁', 0.1)],
    '亥': [('壬', 0.7), ('甲', 0.3)],
}

TEN_GOD_SUPPORT = {'比肩', '劫財', '正印', '偏印'}   # 幫身（比劫、印綬）
TEN_GOD_DRAIN = {'食神', '傷官', '正財', '偏財', '正官', '七殺'}  # 耗身（食傷、財、官殺）


def ten_god(day_stem, other_stem):
    """回傳 other_stem 相對於 day_stem（日主）的十神名稱。"""
    if other_stem == day_stem:
        return '比肩'
    de, oe = STEM_ELEMENT[day_stem], STEM_ELEMENT[other_stem]
    same_yy = STEM_YANG[day_stem] == STEM_YANG[other_stem]
    if oe == de:
        return '比肩' if same_yy else '劫財'
    if ELEMENT_GENERATES[de] == oe:      # 我生
        return '食神' if same_yy else '傷官'
    if ELEMENT_CONTROLS[de] == oe:       # 我剋
        return '偏財' if same_yy else '正財'
    if ELEMENT_CONTROLS[oe] == de:       # 剋我
        return '七殺' if same_yy else '正官'
    return '偏印' if same_yy else '正印'  # 生我

# 十二宮名稱（由命宮起算，方向＝地支索引遞減）；顯示時一律加「宮」字
PALACE_ORDER = ['命', '兄弟', '夫妻', '子女', '財帛', '疾厄',
                '遷移', '僕役', '官祿', '田宅', '福德', '父母']

# 六十甲子納音（用於命宮定五行局）
NAYIN = {}
_nayin_table = [
    ("甲子乙丑", "海中金"), ("丙寅丁卯", "爐中火"), ("戊辰己巳", "大林木"),
    ("庚午辛未", "路旁土"), ("壬申癸酉", "劍鋒金"), ("甲戌乙亥", "山頭火"),
    ("丙子丁丑", "澗下水"), ("戊寅己卯", "城頭土"), ("庚辰辛巳", "白蠟金"),
    ("壬午癸未", "楊柳木"), ("甲申乙酉", "泉中水"), ("丙戌丁亥", "屋上土"),
    ("戊子己丑", "霹靂火"), ("庚寅辛卯", "松柏木"), ("壬辰癸巳", "長流水"),
    ("甲午乙未", "沙中金"), ("丙申丁酉", "山下火"), ("戊戌己亥", "平地木"),
    ("庚子辛丑", "壁上土"), ("壬寅癸卯", "金箔金"), ("甲辰乙巳", "覆燈火"),
    ("丙午丁未", "天河水"), ("戊申己酉", "大驛土"), ("庚戌辛亥", "釵釧金"),
    ("壬子癸丑", "桑柘木"), ("甲寅乙卯", "大溪水"), ("丙辰丁巳", "沙中土"),
    ("戊午己未", "天上火"), ("庚申辛酉", "石榴木"), ("壬戌癸亥", "大海水"),
]
for pair, name in _nayin_table:
    gz1, gz2 = pair[:2], pair[2:]
    NAYIN[gz1] = name
    NAYIN[gz2] = name

ELEMENT_JU = {"水": 2, "木": 3, "金": 4, "土": 5, "火": 6}
JU_NAME = {2: "水二局", 3: "木三局", 4: "金四局", 5: "土五局", 6: "火六局"}

# 十干四化表：(化祿, 化權, 化科, 化忌)
SIHUA_TABLE = {
    '甲': ('廉貞', '破軍', '武曲', '太陽'),
    '乙': ('天機', '天梁', '紫微', '太陰'),
    '丙': ('天同', '天機', '文昌', '廉貞'),
    '丁': ('太陰', '天同', '天機', '巨門'),
    '戊': ('貪狼', '太陰', '右弼', '天機'),
    '己': ('武曲', '貪狼', '天梁', '文曲'),
    '庚': ('太陽', '武曲', '太陰', '天同'),
    '辛': ('巨門', '太陽', '文曲', '文昌'),
    '壬': ('天梁', '紫微', '左輔', '武曲'),
    '癸': ('破軍', '巨門', '太陰', '貪狼'),
}
SIHUA_NAMES = ['化祿', '化權', '化科', '化忌']

# 十二宮 × 四化 應事提示（傳統命理公共判斷原則的通俗白話整理，非特定書籍原文）
EVENT_HINTS = {
    ('命', '化祿'): '心情愉快、機運轉佳，容易逢凶化吉、諸事較順心。',
    ('命', '化權'): '企圖心與主導慾增強，做事積極但也易獨斷，宜多聽取他人意見。',
    ('命', '化科'): '名譽形象提升，貴人扶持，適合展現自己、參加考試或面試。',
    ('命', '化忌'): '情緒起伏大、諸多不順或猶豫不決，凡事宜謹慎保守、避免衝動決定。',
    ('兄弟', '化祿'): '手足或同儕情誼佳，合作或合夥有助力。',
    ('兄弟', '化權'): '在朋友或手足間居主導地位，但也可能意見較強勢。',
    ('兄弟', '化科'): '與手足、夥伴關係和睦，溝通順暢。',
    ('兄弟', '化忌'): '與手足或合夥人易有金錢或意見上的糾紛，合作宜留書面憑證。',
    ('夫妻', '化祿'): '感情甜蜜、桃花運旺，單身者有機會遇到心儀對象。',
    ('夫妻', '化權'): '另一半較強勢或主導感情發展，相處宜互相尊重。',
    ('夫妻', '化科'): '感情穩定，適合訂婚、結婚或公開關係。',
    ('夫妻', '化忌'): '感情或婚姻易生波折、爭執增多，宜多溝通、避免猜忌。',
    ('子女', '化祿'): '與子女緣分佳，可能有懷孕喜訊或親子關係融洽。',
    ('子女', '化權'): '子女表現突出、有主見，但管教上宜軟性溝通。',
    ('子女', '化科'): '子女學業或才藝表現亮眼，親子溝通順暢。',
    ('子女', '化忌'): '子女教養較費心，或與子女緣分／溝通上有波折。',
    ('財帛', '化祿'): '財運亨通，正財偏財皆有進帳機會。',
    ('財帛', '化權'): '理財能力增強、敢於投資，但也易衝動操作，宜控管風險。',
    ('財帛', '化科'): '財務狀況穩健，收支規劃得宜。',
    ('財帛', '化忌'): '財務吃緊或破財機率增加，簽約、借貸、投資都要格外謹慎。',
    ('疾厄', '化祿'): '身心愉快、精神狀況良好。',
    ('疾厄', '化權'): '體力旺盛、活動力強，但也容易過度操勞，宜量力而為。',
    ('疾厄', '化科'): '健康狀況穩定，就醫或調養容易獲得改善。',
    ('疾厄', '化忌'): '健康亮紅燈，容易生病或舊疾復發，宜安排健康檢查、避免過勞。',
    ('遷移', '化祿'): '外出機運佳，出差、旅行、搬遷或異地發展皆順利。',
    ('遷移', '化權'): '在外具影響力、易受矚目，適合拓展人脈或對外交涉。',
    ('遷移', '化科'): '外出貴人多，形象與口碑俱佳。',
    ('遷移', '化忌'): '外出諸事不順，宜小心交通意外與人際糾紛，出遠門前多留意行程規劃。',
    ('僕役', '化祿'): '人緣佳、朋友或部屬多有助力。',
    ('僕役', '化權'): '在朋友圈或團隊中居領導地位。',
    ('僕役', '化科'): '透過朋友、人脈獲得貴人相助或合作機會。',
    ('僕役', '化忌'): '易被朋友連累或與部屬生糾紛，交友、合夥宜謹慎篩選。',
    ('官祿', '化祿'): '事業運暢旺，工作順利、可能有升遷或加薪機會。',
    ('官祿', '化權'): '職權擴大、責任加重，是掌權或創業的好時機，但壓力也隨之增加。',
    ('官祿', '化科'): '工作上獲得肯定，考試、升等、證照運佳。',
    ('官祿', '化忌'): '工作壓力大、易有職場變動或人事糾紛，決策宜三思而後行。',
    ('田宅', '化祿'): '適合購置不動產，居家生活和樂、財庫穩固。',
    ('田宅', '化權'): '在家中或不動產事務上握有主導權，房產可能增值。',
    ('田宅', '化科'): '居家環境改善，或家中添購喜訊。',
    ('田宅', '化忌'): '搬遷、裝修或房產交易易生波折，簽約前務必詳閱合約。',
    ('福德', '化祿'): '心情愉悅、福分佳，容易感到知足快樂。',
    ('福德', '化權'): '想法主觀、操心事多，閒不下來，宜學習放鬆。',
    ('福德', '化科'): '心境平和，興趣嗜好上有所收穫。',
    ('福德', '化忌'): '容易鑽牛角尖、精神壓力大，宜找出口紓壓、避免胡思亂想。',
    ('父母', '化祿'): '與長輩、上司關係融洽，容易獲得提攜。',
    ('父母', '化權'): '長輩管教或要求較嚴格，職場上上司要求也較多。',
    ('父母', '化科'): '文書、證件、考試、公家事務進行順利。',
    ('父母', '化忌'): '與長輩或上司意見相左，文書合約、證件事務宜多留意細節。',
}


def event_hint(palace_base_name, tag):
    return EVENT_HINTS.get((palace_base_name, tag), "")


# 十四主星星性簡述（傳統命理公共知識的通俗整理，非特定書籍原文）
STAR_NATURE = {
    '紫微': '帝王星，尊貴自負、重面子，天生具領導氣質，需輔星相助才不致孤高。',
    '天機': '智多星，機靈善謀、思慮周密，長於策劃分析，但情緒也易多疑善變。',
    '太陽': '光明博愛、奔波勞碌，代表事業、名譽與男性長輩／夫星，重付出。',
    '武曲': '財星，剛毅果決、重義氣，行事講求效率，個性較硬、不善甜言蜜語。',
    '天同': '福星，溫和隨性、重享受知足，抗壓性看似柔弱但韌性強，易流於安逸被動。',
    '廉貞': '次桃花／囚星，精明幹練、原則性強，重紀律但也容易招惹是非官非。',
    '天府': '財庫星，穩重厚道、包容力強，善於守成理財，但也可能流於保守。',
    '太陰': '財星，柔美細膩、重感情內斂，代表女性長輩、母親、妻子，藏富不外顯。',
    '貪狼': '慾望星，多才多藝、交際應酬手腕強，主偏財與桃花，也易貪多嚼不爛。',
    '巨門': '暗星，口才犀利、善分析但多疑，重言語表達，容易因言招惹是非。',
    '天相': '印星，忠誠謹慎、重原則，善於輔佐協調，個性隨和但也較無主見。',
    '天梁': '蔭星，老成持重、清高自負，具貴人／長輩／醫藥緣，重名譽與原則。',
    '七殺': '肅殺星，果決剛強、衝勁十足，敢衝敢拚但性急，變動與挑戰皆多。',
    '破軍': '耗星，破舊立新、勇於開創，變動性大、消耗也大，先破後立。',
}

# （星曜, 四化）→ 應事提示：結合星性＋四化能量的具體判斷語句
# 僅列出十干四化表中實際會出現的組合（武曲/天機/太陰四化皆全，其餘依表列情況而定）
STAR_SIHUA_HINTS = {
    ('廉貞', '化祿'): '人際手腕圓融、異性緣佳，社交或感情場合中容易左右逢源、有所斬獲。',
    ('廉貞', '化忌'): '容易招惹是非官非、意氣用事，人際或感情糾紛需格外謹慎，避免衝動行事。',
    ('破軍', '化祿'): '勇於開創新局，變動中反而帶來機運，是白手起家、開拓新版圖的好時機。',
    ('破軍', '化權'): '破舊立新的魄力增強，敢於大刀闊斧改革，但也容易耗損過大，需量力而為。',
    ('武曲', '化祿'): '正財運旺，靠實力、專業或投資獲利，理財態度務實穩健。',
    ('武曲', '化權'): '財務決策力強、敢於投資或掌控資金調度，行事果斷但也容易獨斷。',
    ('武曲', '化科'): '財務規劃有條理，理財觀念或專業技能獲得肯定。',
    ('武曲', '化忌'): '財務週轉易生問題，投資、借貸、金錢往來要格外謹慎，也易因財與人起衝突。',
    ('太陽', '化祿'): '貴人運佳（尤其男性長輩或上司），事業與名譽同步提升，付出有回報。',
    ('太陽', '化權'): '企圖心與領導慾增強，掌權掌勢、事業版圖擴大，但也容易操勞過度。',
    ('太陽', '化忌'): '奔波辛勞卻不易被肯定，與男性長輩、上司或另一半易有摩擦，眼睛、心血管需留意。',
    ('天機', '化祿'): '腦筋靈活帶來機運，企劃、策略、資訊相關的事務特別順利。',
    ('天機', '化權'): '善於運籌帷幄、掌握關鍵決策，但思慮過多也容易多疑猶豫。',
    ('天機', '化科'): '智慧才華受肯定，考試、企劃、學習方面表現亮眼。',
    ('天機', '化忌'): '想太多反而自尋煩惱，計畫容易生變、決策搖擺不定，宜避免鑽牛角尖。',
    ('天梁', '化祿'): '貴人相助明顯、逢凶化吉，長輩蔭庇或名譽帶來實質好處。',
    ('天梁', '化權'): '說話具份量、受人敬重，適合擔任顧問或監督性角色，但也易倚老賣老。',
    ('天梁', '化科'): '名譽清譽俱佳，考試、證照、醫療或法律相關事務進行順利。',
    ('紫微', '化權'): '地位與掌控力提升，領導魄力增強、更有主見，但也易剛愎自用、聽不進勸。',
    ('紫微', '化科'): '氣度與名望受人推崇，形象出眾，適合公開場合展現自己。',
    ('太陰', '化祿'): '財運細水長流、家庭生活和樂，女性貴人（母親、妻子）帶來助力。',
    ('太陰', '化權'): '理財謹慎精明，對家庭或財務事務的主導性增強。',
    ('太陰', '化科'): '情感細膩、人緣溫和，居家或感情生活穩定美滿。',
    ('太陰', '化忌'): '情緒敏感易鑽牛角尖，與女性長輩或另一半易生嫌隙，財務也宜謹慎防暗損。',
    ('天同', '化祿'): '心情愉快、福分自然來，生活安逸，容易逢凶化吉。',
    ('天同', '化權'): '原本隨和的個性變得較有主張，願意主動爭取自己想要的生活品質。',
    ('天同', '化忌'): '容易流於懶散被動、遇事逃避，情緒偏消極憂鬱，宜積極面對而非閃躲。',
    ('文昌', '化科'): '文書、考試、證照、名譽方面特別順利，適合進修或發表。',
    ('文昌', '化忌'): '文書契約易生糾紛或疏失，簽約、考試、證件務必仔細核對，避免粗心出錯。',
    ('巨門', '化祿'): '因言語、專業知識或口才獲利，適合教學、業務、傳播、顧問等以口為業的工作。',
    ('巨門', '化權'): '言語具說服力、辯才無礙，在需要溝通談判的場合特別吃香。',
    ('巨門', '化忌'): '口舌是非增多，容易因言語誤會或猜疑心重而與人產生摩擦，宜謹言慎行。',
    ('貪狼', '化祿'): '人緣桃花旺、交際手腕圓融，偏財機運佳，才藝或應酬場合特別吃得開。',
    ('貪狼', '化權'): '企圖心與慾望增強，善於掌握機會、開拓人脈，但也容易貪多嚼不爛。',
    ('貪狼', '化忌'): '慾望難以滿足反生煩惱，應酬或桃花容易招惹麻煩，宜節制、避免貪念過重。',
    ('右弼', '化科'): '貴人（尤其女性）暗中相助，人際協調圓融，合作事務進行順利。',
    ('左輔', '化科'): '貴人（尤其男性）暗中相助，做事有人分憂解勞，合作進行順利。',
    ('文曲', '化科'): '才藝、文采、考試運俱佳，適合發表、進修或參加甄選。',
    ('文曲', '化忌'): '容易言多必失，或因文書、才藝表現不如預期而受挫，宜謙虛謹慎，避免逞口舌之能。',
}


def star_sihua_hint(star, tag):
    return STAR_SIHUA_HINTS.get((star, tag), "")

# 天魁、天鉞（依年干）
KUI_YUE = {
    '甲': ('丑', '未'), '戊': ('丑', '未'), '庚': ('丑', '未'),
    '乙': ('子', '申'), '己': ('子', '申'),
    '丙': ('亥', '酉'), '丁': ('亥', '酉'),
    '壬': ('卯', '巳'), '癸': ('卯', '巳'),
    '辛': ('午', '寅'),
}

# 祿存（依年干）
LUCUN = {'甲': '寅', '乙': '卯', '丙': '巳', '丁': '午', '戊': '巳',
         '己': '午', '庚': '申', '辛': '酉', '壬': '亥', '癸': '子'}

# 天馬（依年支三合組）
TIANMA = {}
for grp in [(2, 6, 10, 8), (8, 0, 4, 2), (5, 9, 1, 11), (11, 3, 7, 5)]:
    for b in grp[:3]:
        TIANMA[b] = grp[3]

# 火星／鈴星起點（依年支三合組，之後順數生時）
HUOXING_START = {}
LINGXING_START = {}
for members, hs, ls in [((2, 6, 10), 1, 3), ((8, 0, 4), 2, 10),
                         ((5, 9, 1), 3, 10), ((11, 3, 7), 9, 10)]:
    for b in members:
        HUOXING_START[b] = hs
        LINGXING_START[b] = ls

# 紫微星系（相對紫微的順時針位移）／天府星系（相對天府的順時針位移）
ZIWEI_SERIES_OFFSET = {0: '紫微', 11: '天機', 9: '太陽', 8: '武曲', 7: '天同', 4: '廉貞'}
TIANFU_SERIES_OFFSET = {0: '天府', 1: '太陰', 2: '貪狼', 3: '巨門',
                         4: '天相', 5: '天梁', 6: '七殺', 10: '破軍'}

MAIN_STARS = set(list(ZIWEI_SERIES_OFFSET.values()) + list(TIANFU_SERIES_OFFSET.values()))


def idx(branch):
    return BRANCHES.index(branch)


def stem_idx(stem):
    return STEMS.index(stem)


# ----------------------------------------------------------------------------
# 排盤核心
# ----------------------------------------------------------------------------
class ZiWeiChart:
    def __init__(self, solar_year, solar_month, solar_day, hour, minute, gender):
        self.solar = Solar.fromYmdHms(solar_year, solar_month, solar_day, hour, minute, 0)
        self.lunar = self.solar.getLunar()
        self.gender = gender  # 'M' or 'F'

        self.lunar_year = self.lunar.getYear()
        self.lunar_month = abs(self.lunar.getMonth())
        self.lunar_day = self.lunar.getDay()
        self.is_leap_month = self.lunar.getMonth() < 0

        self.year_gz = self.lunar.getYearInGanZhi()
        self.year_stem = self.year_gz[0]
        self.year_branch = self.year_gz[1]

        self.hour_branch = self.lunar.getTimeZhi()
        self.hour_idx = idx(self.hour_branch)

        self._build_palace_branches()
        self._build_palace_stems()
        self._build_ming_shen()
        self._build_ju()
        self._build_main_stars()
        self._build_minor_stars()
        self._build_birth_sihua()
        self._build_dayun()
        self._build_bazi_yun()

    # -- 十二宮地支（固定：子=0 ... 亥=11） -----------------------------------
    def _build_palace_branches(self):
        self.branch_of = {i: BRANCHES[i] for i in range(12)}

    # -- 十二宮天干（五虎遁年起月訣，寅宮起） ----------------------------------
    @staticmethod
    def _stems_from_seed(seed_stem):
        """依五虎遁公式，用任一天干（生年干／流年干皆可）起出對應的十二宮天干。"""
        base_map = [2, 4, 6, 8, 0]  # 甲己丙/乙庚戊/丙辛庚/丁壬壬/戊癸甲 -> 寅宮天干索引
        yin_stem_idx = base_map[stem_idx(seed_stem) % 5]
        stems = {}
        for i in range(12):
            s = (yin_stem_idx + ((i - 2) % 12)) % 10
            stems[i] = STEMS[s]
        return stems

    def _build_palace_stems(self):
        self.stem_of = self._stems_from_seed(self.year_stem)

    # -- 命宮／身宮 -----------------------------------------------------------
    def _build_ming_shen(self):
        month_palace = (2 + (self.lunar_month - 1)) % 12  # 寅起正月，順數至生月
        self.ming_idx = (month_palace - self.hour_idx) % 12   # 逆數至生時 -> 命宮
        self.shen_idx = (month_palace + self.hour_idx) % 12   # 順數至生時 -> 身宮

    # -- 五行局 ---------------------------------------------------------------
    def _build_ju(self):
        gz = self.stem_of[self.ming_idx] + self.branch_of[self.ming_idx]
        self.ming_nayin = NAYIN[gz]
        element = self.ming_nayin[-1]
        self.ju = ELEMENT_JU[element]
        self.ju_name = JU_NAME[self.ju]

    # -- 十四主星 ---------------------------------------------------------------
    def _locate_ziwei(self):
        """安紫微星訣：找出「出生日＋補數」恰能被局數整除的最小補數（offset），
        商數（除以12取餘）減一為基準宮位，補數為偶則順行補數宮、為奇則逆行補數宮，
        最後從寅宮起算。此為經查證與 iztro 開源實作一致的標準演算法。"""
        d, ju = self.lunar_day, self.ju
        offset = 0
        while (d + offset) % ju != 0:
            offset += 1
        quotient = (d + offset) // ju
        steps = (quotient % 12) - 1
        if offset % 2 == 0:
            steps += offset
        else:
            steps -= offset
        return (2 + steps) % 12

    def _build_main_stars(self):
        self.star_palace = {}   # 星名 -> 宮位索引
        self.palace_stars = {i: [] for i in range(12)}  # 宮位索引 -> [星名,...]

        ziwei_idx = self._locate_ziwei()
        self.ziwei_idx = ziwei_idx
        tianfu_idx = (4 - ziwei_idx) % 12
        self.tianfu_idx = tianfu_idx

        for off, name in ZIWEI_SERIES_OFFSET.items():
            p = (ziwei_idx + off) % 12
            self.star_palace[name] = p
            self.palace_stars[p].append(name)

        for off, name in TIANFU_SERIES_OFFSET.items():
            p = (tianfu_idx + off) % 12
            self.star_palace[name] = p
            self.palace_stars[p].append(name)

    # -- 十四輔星（六吉六煞＋祿存天馬） -----------------------------------------
    def _build_minor_stars(self):
        h = self.hour_idx
        m = self.lunar_month
        y_stem, y_branch_idx = self.year_stem, idx(self.year_branch)

        placements = {
            '文昌': (10 - h) % 12,
            '文曲': (4 + h) % 12,
            '左輔': (4 + (m - 1)) % 12,
            '右弼': (10 - (m - 1)) % 12,
            '天魁': idx(KUI_YUE[y_stem][0]),
            '天鉞': idx(KUI_YUE[y_stem][1]),
            '祿存': idx(LUCUN[y_stem]),
            '天馬': TIANMA[y_branch_idx],
            '地空': (11 - h) % 12,
            '地劫': (11 + h) % 12,
            '火星': (HUOXING_START[y_branch_idx] + h) % 12,
            '鈴星': (LINGXING_START[y_branch_idx] + h) % 12,
        }
        lucun_idx = placements['祿存']
        placements['擎羊'] = (lucun_idx + 1) % 12
        placements['陀羅'] = (lucun_idx - 1) % 12

        for name, p in placements.items():
            self.star_palace[name] = p
            self.palace_stars[p].append(name)

    # -- 大限（十年一運，起運歲數＝五行局數；陽男陰女順行、陰男陽女逆行） -------------
    def _build_dayun(self):
        is_yang_stem = stem_idx(self.year_stem) % 2 == 0
        # 順行＝沿地支順序前進（命→父母→福德…，offset 遞減）
        # 逆行＝沿十二宮人事序前進（命→兄弟→夫妻…，offset 遞增，即 PALACE_ORDER 順序）
        forward = (self.gender == 'M' and is_yang_stem) or (self.gender == 'F' and not is_yang_stem)
        self.dayun_forward = forward
        self.dayun_of = {}  # 宮位索引 -> (起歲, 迄歲)
        start = self.ju
        for k in range(12):
            offset = (-k) % 12 if forward else k
            p_idx = (self.ming_idx - offset) % 12
            self.dayun_of[p_idx] = (start + 10 * k, start + 10 * k + 9)

    # -- 四柱八字與八字大運（供與紫微命盤合參） ---------------------------------
    def _build_bazi_yun(self):
        self.eight_char = self.lunar.getEightChar()
        self.bazi_pillars = {
            'year': self.eight_char.getYear(),
            'month': self.eight_char.getMonth(),
            'day': self.eight_char.getDay(),
            'time': self.eight_char.getTime(),
        }
        gender_num = 1 if self.gender == 'M' else 0
        self.bazi_yun = self.eight_char.getYun(gender_num)
        self.bazi_dayun_list = self.bazi_yun.getDaYun(13)  # 13輪覆蓋約130歲

        self.bazi_day_master = self.bazi_pillars['day'][0]  # 日主天干
        dm = self.bazi_day_master

        # 四柱天干十神（日柱本身標記為「日主」）
        self.bazi_stem_ten_god = {}
        for pos in ('year', 'month', 'day', 'time'):
            stem = self.bazi_pillars[pos][0]
            self.bazi_stem_ten_god[pos] = '日主' if pos == 'day' else ten_god(dm, stem)

        # 四柱地支藏干十神（僅日柱藏干不含日主本身的比肩重複標註問題，直接照算）
        self.bazi_branch_hidden = {}
        for pos in ('year', 'month', 'day', 'time'):
            branch = self.bazi_pillars[pos][1]
            self.bazi_branch_hidden[pos] = [
                (gan, ten_god(dm, gan), weight) for gan, weight in ZHI_HIDE_GAN[branch]
            ]

        # 幫身／耗身簡易加權統計（僅供參考，非精確子平旺衰演算）
        support, drain = 0.0, 0.0
        for pos in ('year', 'month', 'time'):  # 日主本身不計入
            tg = self.bazi_stem_ten_god[pos]
            if tg in TEN_GOD_SUPPORT:
                support += 1.0
            elif tg in TEN_GOD_DRAIN:
                drain += 1.0
        for pos in ('year', 'month', 'day', 'time'):
            for gan, tg, weight in self.bazi_branch_hidden[pos]:
                if tg in TEN_GOD_SUPPORT:
                    support += weight
                elif tg in TEN_GOD_DRAIN:
                    drain += weight
        self.bazi_support_score = round(support, 2)
        self.bazi_drain_score = round(drain, 2)

    def bazi_dayun_by_year(self, solar_year):
        """回傳指定西元年所落的八字大運（DaYun 物件）；查無對應區間則回傳 None。"""
        for dy in self.bazi_dayun_list:
            if dy.getStartYear() <= solar_year <= dy.getEndYear():
                return dy
        return None

    def bazi_liunian_ganzhi(self, solar_year):
        """回傳指定西元年八字流年干支（依節氣定年柱界線，7/1為基準時刻避開節氣交界誤判）。"""
        ref = Solar.fromYmdHms(solar_year, 7, 1, 12, 0, 0)
        return ref.getLunar().getEightChar().getYear()

    # -- 生年四化（命主一生四化，標註於主星輔星上） -----------------------------
    def _build_birth_sihua(self):
        stars = SIHUA_TABLE[self.year_stem]
        self.birth_sihua = {}  # 星名 -> '化祿'/'化權'/'化科'/'化忌'
        for star, tag in zip(stars, SIHUA_NAMES):
            self.birth_sihua[star] = tag

    # -- 通用：某天干四化，飛入哪些宮位 -----------------------------------------
    def _sihua_targets(self, stem):
        """回傳 list of (star, tag, target_palace_idx)"""
        results = []
        for star, tag in zip(SIHUA_TABLE[stem], SIHUA_NAMES):
            target_p = self.star_palace.get(star)
            if target_p is not None:
                results.append((star, tag, target_p))
        return results

    # -- 宮干四化飛星：某宮宮干四化飛入哪一宮、作用在哪顆星 ----------------------
    def flying_sihua(self, palace_idx):
        """回傳 list of dict：{tag, star, target_palace_idx, target_palace_name, is_self}"""
        stem = self.stem_of[palace_idx]
        results = []
        for star, tag, target_p in self._sihua_targets(stem):
            results.append({
                'tag': tag,
                'star': star,
                'target_idx': target_p,
                'target_name': self.palace_name(target_p),
                'is_self': target_p == palace_idx,
                'hint': star_sihua_hint(star, tag),
            })
        return results

    # -- 大限：依歲數找出對應大限宮位 -------------------------------------------
    def dayun_palace_by_age(self, age):
        """傳入虛歲，回傳落在哪個大限宮位索引；早於起運歲數則回傳 None。"""
        for p_idx, (a0, a1) in self.dayun_of.items():
            if a0 <= age <= a1:
                return p_idx
        return None

    # -- 流年：依西元年取得流年干支、流年虛歲、流年宮位 --------------------------
    def liunian_ganzhi(self, solar_year):
        """用當年 7/1 當基準日換算該西元年的農曆干支（避開農曆新年交界的誤判）。"""
        ref = Solar.fromYmdHms(solar_year, 7, 1, 12, 0, 0)
        gz = ref.getLunar().getYearInGanZhi()
        return gz[0], gz[1]

    def liunian_age(self, solar_year):
        """虛歲＝流年農曆年 − 出生農曆年 + 1"""
        ref = Solar.fromYmdHms(solar_year, 7, 1, 12, 0, 0)
        liu_lunar_year = ref.getLunar().getYear()
        return liu_lunar_year - self.lunar_year + 1

    # -- 通用：多層四化疊加（本命固定為底層，其餘依傳入層級疊上去） -----------------
    def _sihua_layers(self, layer_stems):
        """layer_stems: [(層級名稱, 天干或 None), ...]。回傳 (layers, overlaps)。"""
        layers = {i: [] for i in range(12)}  # 宮位 -> [(層級, 星, 四化), ...]
        for star, tag in self.birth_sihua.items():
            p = self.star_palace.get(star)
            if p is not None:
                layers[p].append(('本命', star, tag))
        for layer_name, stem in layer_stems:
            if stem is None:
                continue
            for star, tag, p in self._sihua_targets(stem):
                layers[p].append((layer_name, star, tag))

        overlaps = {}  # 宮位 -> {'化祿': n, ...}（僅記錄 >=2 層重疊的四化）
        for p, items in layers.items():
            counts = {}
            for _, _, tag in items:
                counts[tag] = counts.get(tag, 0) + 1
            hot = {tag: n for tag, n in counts.items() if n >= 2}
            if hot:
                overlaps[p] = hot
        return layers, overlaps

    def liunian_analysis(self, solar_year):
        """回傳指定西元年的本命／大限／流年三層四化與疊宮應事分析（結構化資料）。"""
        age = self.liunian_age(solar_year)
        liu_stem, liu_branch = self.liunian_ganzhi(solar_year)
        liu_palace_idx = idx(liu_branch)
        dayun_idx = self.dayun_palace_by_age(age)
        dayun_stem = self.stem_of[dayun_idx] if dayun_idx is not None else None

        layers, overlaps = self._sihua_layers([('大限', dayun_stem), ('流年', liu_stem)])

        return {
            'age': age,
            'dayun_idx': dayun_idx,
            'dayun_stem': dayun_stem,
            'dayun_range': self.dayun_of.get(dayun_idx) if dayun_idx is not None else None,
            'liu_stem': liu_stem,
            'liu_branch': liu_branch,
            'liu_palace_idx': liu_palace_idx,
            'layers': layers,
            'overlaps': overlaps,
        }

    # -- 流月：安流年斗君（流年支宮逆數生月、順數生時），再順數至目標農曆月 -----------
    def liuyue_doujun(self, liu_palace_idx):
        """流年斗君＝該流年正月所在宮位。公式：流年支宮逆數生月、順數生時。
        已用範例命盤驗證：1961/1/29 丑時生，2026（丙午）年斗君落於未宮，與實際命盤相符。"""
        return (liu_palace_idx - (self.lunar_month - 1) + self.hour_idx) % 12

    def liuyue_analysis(self, solar_year, solar_month, solar_day):
        """回傳指定西元日期所屬農曆月的本命／大限／流年／流月四層四化與疊宮應事分析。"""
        ref = Solar.fromYmdHms(solar_year, solar_month, solar_day, 12, 0, 0)
        ref_lunar = ref.getLunar()
        gz = ref_lunar.getYearInGanZhi()
        liu_stem, liu_branch = gz[0], gz[1]
        liu_palace_idx = idx(liu_branch)
        ref_lunar_year = ref_lunar.getYear()
        ref_lunar_month = abs(ref_lunar.getMonth())
        is_leap = ref_lunar.getMonth() < 0

        age = ref_lunar_year - self.lunar_year + 1
        dayun_idx = self.dayun_palace_by_age(age)
        dayun_stem = self.stem_of[dayun_idx] if dayun_idx is not None else None

        doujun_idx = self.liuyue_doujun(liu_palace_idx)
        yue_palace_idx = (doujun_idx + (ref_lunar_month - 1)) % 12
        yue_stem = self._stems_from_seed(liu_stem)[yue_palace_idx]

        layers, overlaps = self._sihua_layers([
            ('大限', dayun_stem), ('流年', liu_stem), ('流月', yue_stem),
        ])

        return {
            'age': age,
            'dayun_idx': dayun_idx,
            'dayun_stem': dayun_stem,
            'dayun_range': self.dayun_of.get(dayun_idx) if dayun_idx is not None else None,
            'liu_stem': liu_stem,
            'liu_branch': liu_branch,
            'liu_palace_idx': liu_palace_idx,
            'lunar_month': ref_lunar_month,
            'is_leap_month': is_leap,
            'doujun_idx': doujun_idx,
            'yue_palace_idx': yue_palace_idx,
            'yue_stem': yue_stem,
            'layers': layers,
            'overlaps': overlaps,
        }

    # -- 工具 -----------------------------------------------------------------
    def palace_name(self, branch_idx):
        """回傳宮位基礎名稱（不含「宮」字），例如 命／兄弟／官祿"""
        offset = (self.ming_idx - branch_idx) % 12
        return PALACE_ORDER[offset]

    def palace_gz(self, branch_idx):
        return self.stem_of[branch_idx] + self.branch_of[branch_idx]


# ----------------------------------------------------------------------------
# 輸出格式化
# ----------------------------------------------------------------------------
def print_chart(c: ZiWeiChart, name="", note=""):
    print("=" * 72)
    print(f"紫微斗數命盤{'：' + name if name else ''}")
    print("=" * 72)
    g = "男" if c.gender == 'M' else "女"
    print(f"陽曆：{c.solar.getYear()}年{c.solar.getMonth()}月{c.solar.getDay()}日 "
          f"{c.solar.getHour():02d}:{c.solar.getMinute():02d}　性別：{g}")
    print(f"農曆：{c.lunar_year}年{'閏' if c.is_leap_month else ''}{c.lunar_month}月{c.lunar_day}日　"
          f"時辰：{c.hour_branch}時")
    ec = c.lunar.getEightChar()
    print(f"八字：{ec.getYear()} {ec.getMonth()} {ec.getDay()} {ec.getTime()}")
    print(f"生年干：{c.year_stem}　命宮：{c.palace_gz(c.ming_idx)}（{c.branch_of[c.ming_idx]}宮）　"
          f"身宮：{c.palace_gz(c.shen_idx)}（{c.branch_of[c.shen_idx]}宮 / {c.palace_name(c.shen_idx)}宮）")
    print(f"命局：{c.ju_name}（納音：{c.ming_nayin}）　命主/身主查表略")
    print("-" * 72)

    for i in range(12):
        gz = c.palace_gz(i)
        pname = c.palace_name(i) + "宮"
        stars = c.palace_stars[i]
        main = [s for s in stars if s in MAIN_STARS]
        minor = [s for s in stars if s not in MAIN_STARS]
        tags = []
        for s in stars:
            if s in c.birth_sihua:
                tags.append(f"{s}({c.birth_sihua[s]})")
        mark = []
        if i == c.ming_idx:
            mark.append("命宮")
        if i == c.shen_idx:
            mark.append("身宮")
        mark_s = "★" + "/".join(mark) if mark else ""
        a0, a1 = c.dayun_of[i]
        print(f"[{gz}] {pname:<4}大限{a0:>3}-{a1:<3}{mark_s:<8} "
              f"主星：{','.join(main) if main else '（空宮）':<12} "
              f"輔煞：{','.join(minor) if minor else '無'}")
        if tags:
            print(f"        生年四化：{'、'.join(tags)}")
    print("=" * 72)


def print_flying_sihua(c: ZiWeiChart):
    print("\n【十二宮宮干四化飛星分析】")
    print("-" * 72)
    for offset, pname in enumerate(PALACE_ORDER):
        p_idx = (c.ming_idx - offset) % 12
        stem = c.stem_of[p_idx]
        print(f"\n{pname}宮（{c.palace_gz(p_idx)}）：")
        for r in results_or_empty(c.flying_sihua(p_idx)):
            self_tag = "（自化／回本宮）" if r['is_self'] else ""
            print(f"  ・{pname}宮{stem}干　飛入　{r['target_name']}宮　{r['star']}{r['tag']}{self_tag}")


def results_or_empty(res):
    return res


def _print_layers_block(c: ZiWeiChart, r: dict):
    for i in range(12):
        items = r['layers'][i]
        if not items:
            continue
        pname = c.palace_name(i)
        tag_str = "、".join(f"{layer}{star}{tag}" for layer, star, tag in items)
        hot = r['overlaps'].get(i)
        hot_str = ""
        if hot:
            hot_str = "　⚠ 疊：" + "、".join(f"{t}x{n}" for t, n in hot.items())
        print(f"[{pname}宮] {tag_str}{hot_str}")
        for layer, star, tag in items:
            shint = star_sihua_hint(star, tag)
            print(f"    ・{layer}｜{star}{tag}：{shint or '（無對應提示）'}")
        seen_tags = {tag for _, _, tag in items}
        for tag in SIHUA_NAMES:
            if tag in seen_tags:
                phint = event_hint(pname, tag)
                if phint:
                    print(f"    · {pname}宮主題（{tag}）：{phint}")


def print_liunian(c: ZiWeiChart, solar_year: int):
    r = c.liunian_analysis(solar_year)
    print(f"\n【{solar_year} 年　大限流年分析】")
    print("-" * 72)
    print(f"虛歲：{r['age']}")
    if r['dayun_idx'] is not None:
        a0, a1 = r['dayun_range']
        print(f"大限：{c.palace_gz(r['dayun_idx'])}宮"
              f"（{c.palace_name(r['dayun_idx'])}宮，{a0}-{a1}歲，大限干：{r['dayun_stem']}）")
    else:
        print("大限：尚未起運（早運前參考命宮／福德宮）")
    print(f"流年：{r['liu_stem']}{r['liu_branch']}　流年命宮在 {c.branch_of[r['liu_palace_idx']]}宮"
          f"（{c.palace_name(r['liu_palace_idx'])}宮）")
    print()
    _print_layers_block(c, r)


def print_liuyue(c: ZiWeiChart, solar_year: int, solar_month: int, solar_day: int):
    r = c.liuyue_analysis(solar_year, solar_month, solar_day)
    print(f"\n【{solar_year}-{solar_month:02d}-{solar_day:02d}　大限流年流月分析】")
    print("-" * 72)
    print(f"虛歲：{r['age']}")
    if r['dayun_idx'] is not None:
        a0, a1 = r['dayun_range']
        print(f"大限：{c.palace_gz(r['dayun_idx'])}宮"
              f"（{c.palace_name(r['dayun_idx'])}宮，{a0}-{a1}歲，大限干：{r['dayun_stem']}）")
    else:
        print("大限：尚未起運（早運前參考命宮／福德宮）")
    print(f"流年：{r['liu_stem']}{r['liu_branch']}　流年命宮在 {c.branch_of[r['liu_palace_idx']]}宮"
          f"（{c.palace_name(r['liu_palace_idx'])}宮）")
    leap_note = "（閏月）" if r['is_leap_month'] else ""
    print(f"流月：農曆{r['lunar_month']}月{leap_note}　流年斗君在 {c.branch_of[r['doujun_idx']]}宮　"
          f"流月落於 {c.branch_of[r['yue_palace_idx']]}宮（{c.palace_name(r['yue_palace_idx'])}宮，流月干：{r['yue_stem']}）")
    print()
    _print_layers_block(c, r)


# ----------------------------------------------------------------------------
# 主程式
# ----------------------------------------------------------------------------
def main():
    if len(sys.argv) >= 4:
        d = sys.argv[1]
        t = sys.argv[2]
        gender = sys.argv[3].upper()
        y, mo, da = [int(x) for x in d.split('-')]
        hh, mm = [int(x) for x in t.split(':')]
        name = sys.argv[4] if len(sys.argv) > 4 else ""
    else:
        # 內建範例：吳明森 1961-03-15 02:59 男（民國50年，農曆50年1月29日丑時）
        y, mo, da, hh, mm = 1961, 3, 15, 2, 59
        gender = 'M'
        name = "吳明森（範例）"

    chart = ZiWeiChart(y, mo, da, hh, mm, gender)
    print_chart(chart, name=name)
    print_flying_sihua(chart)

    target_year = int(sys.argv[5]) if len(sys.argv) > 5 else 2026
    print_liunian(chart, target_year)

    if len(sys.argv) > 7:
        target_month, target_day = int(sys.argv[6]), int(sys.argv[7])
        print_liuyue(chart, target_year, target_month, target_day)


if __name__ == "__main__":
    main()
