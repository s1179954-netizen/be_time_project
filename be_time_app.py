# -*- coding: utf-8 -*-
# 本文件以 UTF-8 编码保存（含 BOM，方便 Windows 记事本/控制台正确识别中文，避免打开后乱码）
import os
import random
import base64
import json
from datetime import datetime, timedelta
from ics import Calendar, Event
import streamlit as st
import pandas as pd

# -------------------------- 本地持久化（保存在桌面项目目录，刷新 / 重启不丢） --------------------------
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "be_time_state.json")


def load_state():
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def save_state():
    try:
        data = {
            "finished_events": sorted(st.session_state.get("finished_events", set())),
            "starred_events": sorted(st.session_state.get("starred_events", set())),
            "personal_done": {t["id"]: t["done"] for t in st.session_state.get("personal_tasks", [])},
            "trip_plan": st.session_state.get("trip_plan", []),
            "fav_places": st.session_state.get("fav_places", []),
            "saved_articles": st.session_state.get("saved_articles", []),
            "place_seed": st.session_state.get("place_seed", 0),
            "free_hours": st.session_state.get("free_hours", 1.0),
            "user_profile": st.session_state.get("user_profile", {}),
            "dark_mode": st.session_state.get("dark_mode", False),
            "identity_mode": st.session_state.get("identity_mode", "student"),
            "selected_industry": st.session_state.get("selected_industry", "金融"),
            "goal_mode": st.session_state.get("goal_mode", "career"),
            "onboarding_done": st.session_state.get("onboarding_done", True),
            "timeline_view": st.session_state.get("timeline_view", "all"),
            "scores": st.session_state.get("scores", {}),
            "applications": st.session_state.get("applications", []),
            "alert_log": st.session_state.get("alert_log", []),
            "discussions": st.session_state.get("discussions", [])
        }
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
    except Exception:
        pass

# -------------------------- 全局环境设置 --------------------------
os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"

# 若控制台 / 编辑器仍出现中文乱码，通常是 Windows 代码页为 GBK（cp936）所致。
# 在启动命令前执行一次下面这句即可彻底避免（无需修改代码）：
#     set PYTHONUTF8=1 && streamlit run be_time_app.py

st.set_page_config(
    page_title="Be-Time｜八达通小组",
    layout="wide",
    page_icon="⏱️",
    initial_sidebar_state="collapsed"
)

# -------------------------- 主题配色定义（亮色 + 暗色） --------------------------
THEMES = {
    "study": {
        "name": "学业工作台",
        "primary": "#1f4e79",
        "secondary": "#4a7cad",
        "light": "#e8f0f8",
        "accent": "#72a6d8",
        "bg_grad": "linear-gradient(135deg, #f4f8fc, #e1ecf7)",
        "icon": "📚",
        "dark": {
            "primary": "#3b6b99",
            "secondary": "#5e8fbb",
            "light": "#182838",
            "accent": "#8ab8e0",
            "bg_grad": "linear-gradient(135deg, #101b28, #1c3044)"
        }
    },
    "job": {
        "name": "求职赛道",
        "primary": "#6b489e",
        "secondary": "#906fc9",
        "light": "#f1ecf8",
        "accent": "#b89ce0",
        "bg_grad": "linear-gradient(135deg, #f7f4fc, #e9dff7)",
        "icon": "💼",
        "dark": {
            "primary": "#8866bb",
            "secondary": "#a88bd8",
            "light": "#291f3d",
            "accent": "#c9b2e8",
            "bg_grad": "linear-gradient(135deg, #1c142b, #302248)"
        }
    },
    "local": {
        "name": "香港本地适配",
        "primary": "#239984",
        "secondary": "#47c4ab",
        "light": "#e7f7f4",
        "accent": "#77d8c5",
        "bg_grad": "linear-gradient(135deg, #f0fbf8, #dcf4ee)",
        "icon": "🗺️",
        "dark": {
            "primary": "#2eb89f",
            "secondary": "#58d4bb",
            "light": "#173530",
            "accent": "#8ee2d0",
            "bg_grad": "linear-gradient(135deg, #0f2723, #224941)"
        }
    },
    "resource": {
        "name": "经验资源库",
        "primary": "#d67722",
        "secondary": "#f09c4c",
        "light": "#fff3e8",
        "accent": "#f6b978",
        "bg_grad": "linear-gradient(135deg, #fff8f0, #ffe8d4)",
        "icon": "📖",
        "dark": {
            "primary": "#ec8b36",
            "secondary": "#f4ad66",
            "light": "#3b2818",
            "accent": "#f8c896",
            "bg_grad": "linear-gradient(135deg, #2b1c0f, #4d331c)"
        }
    },
    "assistant": {
        "name": "智能助手",
        "primary": "#c95f85",
        "secondary": "#e488a7",
        "light": "#fceef3",
        "accent": "#f7b6c9",
        "bg_grad": "linear-gradient(135deg, #fff2f6, #fce3eb)",
        "icon": "🤖",
        "dark": {
            "primary": "#d97295",
            "secondary": "#eb9fb8",
            "light": "#382029",
            "accent": "#f9c6d6",
            "bg_grad": "linear-gradient(135deg, #2c161f, #4b2837)"
        }
    }
}

NAV_MENU = [
    {
        "key": "study",
        "label": "学业工作台",
        "children": [
            {"key": "study_all", "label": "全景时间轴"},
            {"key": "study_week", "label": "本周课表"},
            {"key": "study_course", "label": "课程一览"},
            {"key": "study_team", "label": "个人看板"}
        ]
    },
    {
        "key": "job",
        "label": "求职赛道",
        "children": [
            {"key": "job_timeline", "label": "求职时间轴"},
            {"key": "job_recruit", "label": "招聘信息库"},
            {"key": "job_apps", "label": "网申进度"},
            {"key": "job_export", "label": "导出求职日历"}
        ]
    },
    {
        "key": "local",
        "label": "香港本地适配",
        "children": [
            {"key": "local_recommend", "label": "碎片行程推荐"},
            {"key": "local_plan", "label": "我的游玩计划"},
            {"key": "local_fav", "label": "我的收藏点位"}
        ]
    },
    {
        "key": "resource",
        "label": "经验资源库",
        "children": [
            {"key": "resource_list", "label": "经验贴广场"},
            {"key": "resource_saved", "label": "收藏经验贴"},
            {"key": "resource_discuss", "label": "讨论区"}
        ]
    },
    {
        "key": "assistant",
        "label": "智能助手",
        "children": [
            {"key": "assistant_chat", "label": "对话助手"},
            {"key": "assistant_plan", "label": "AI 任务拆解"}
        ]
    }
]

# -------------------------- 事件数据源（严格按截图日期） --------------------------
RAW_EVENTS = [
    {"date": "2026-09-22", "title": "基础挖掘代码作业", "type": "academic", "priority": "high", "note": "Python，聚类、关联规则实现"},
    {"date": "2026-10-20", "title": "数据集与预测思路 Presentation", "type": "academic", "priority": "high", "note": "选定数据集，模型选择说明"},
    {"date": "2026-11-17", "title": "完整挖掘项目 + 报告 Deadline", "type": "academic", "priority": "high", "note": "交付代码、可视化、项目报告"},
    {"date": "2026-11-26", "title": "Group Work Turnitin 提交", "type": "academic", "priority": "high", "note": "小组作业，提前合并文档"},
    {"date": "2026-11-27", "title": "PPT 提交", "type": "academic", "priority": "high", "note": "INT6140 课堂演示材料"},
    {"date": "2026-11-27", "title": "完整展示视频提交", "type": "academic", "priority": "high", "note": "INT6140 完整展示视频"},
    {"date": "2026-11-29", "title": "小组报告提交（Turnitin）", "type": "academic", "priority": "high", "note": "INT6140 小组报告"},
    {"date": "2026-11-30", "title": "课后报告 Reflective Report", "type": "academic", "priority": "mid", "note": "INT6140 反思报告"},
    {"date": "2026-12-01", "title": "小组报告提交（PPT + 報告）", "type": "academic", "priority": "high", "note": "INT6141 小组报告"},
    {"date": "2026-12-04", "title": "个人作品集提交", "type": "academic", "priority": "mid", "note": "INT6140 个人作品集"},
    {"date": "2026-12-06", "title": "（可选）小组贡献反馈", "type": "academic", "priority": "low", "note": "INT6140 可选反馈"},
    {"date": "2026-12-08", "title": "Individual Essay Submission（Turnitin）", "type": "academic", "priority": "high", "note": "INT6143 个人论文"},
    {"date": "2026-12-11", "title": "个人作品集提交", "type": "academic", "priority": "mid", "note": "INT6141 个人作品集"},
    {"date": "2026-12-14", "title": "小组项目", "type": "academic", "priority": "high", "note": "INT6136 小组项目"},
    {"date": "2026-12-14", "title": "个人项目（Turnitin）", "type": "academic", "priority": "high", "note": "INT6136 个人项目"},
    {"date": "2026-08-31", "title": "秋季开学", "type": "academic", "priority": "mid", "note": "新学期开始"},
    {"date": "2026-09-05", "title": "签证材料提交截止", "type": "academic", "priority": "mid", "note": "港校学生签证"},
    {"date": "2026-08-01", "title": "内地 / 香港秋招提前批启动", "type": "career", "priority": "normal", "note": "四大、银行 MT、能源提前批"},
    {"date": "2026-09-10", "title": "秋招主通道开启", "type": "career", "priority": "normal", "note": "大批企业开放网申"},
    {"date": "2026-11-08", "title": "简历中英文终版打磨", "type": "career", "priority": "normal", "note": "按 STAR 法则逐条核对，文件名规范为 姓名-学校-岗位-2026届"},
    {"date": "2026-11-15", "title": "国泰毕业培训生网申截止", "type": "career", "priority": "normal", "note": "2027 年 8 月入职批次，官网提交"},
    {"date": "2026-11-20", "title": "笔试 / OT 刷题冲刺", "type": "career", "priority": "normal", "note": "银行 SHL / 行测 + 四大逻辑题，每晚 1 小时"},
    {"date": "2026-12-01", "title": "秋招笔试高峰", "type": "career", "priority": "normal", "note": "集中线上笔试"},
    {"date": "2026-12-05", "title": "面试高频问题模拟", "type": "career", "priority": "normal", "note": "宝洁八大问 + 自我介绍英文版，录音复盘"},
    {"date": "2026-12-18", "title": "秋招复盘 + 寒假规划", "type": "career", "priority": "normal", "note": "梳理已投递公司进度，制定寒假实习 / 补投清单"},
    {"date": "2027-01-15", "title": "春招提前批启动", "type": "career", "priority": "normal", "note": "次年春招开启"},
    {"date": "2027-02-01", "title": "春招岗位清单整理", "type": "career", "priority": "normal", "note": "收集补录岗位，优先投递秋招有笔试记录的同一批公司"},
    {"date": "2027-03-01", "title": "春招主通道", "type": "career", "priority": "normal", "note": "大量补录岗位放出"},
    {"date": "2027-04-20", "title": "IANG 签证准备启动", "type": "career", "priority": "normal", "note": "留港签证规划"}
]

# -------------------------- 课程数据源（真实课表：2026-27 S1，来自用户课表截图 + e-SIS 时间） --------------------------
# 以用户所选课程为准：INT6143 / INT6140 / INT6141 / INT6136（周四下午未选课不收录）
COURSES = [
    {
        "code": "INT6143",
        "name": "数据挖掘：趋势分析与预测",
        "name_en": "DATA MINING FOR TRENDS ANALYSIS AND FORECASTING",
        "weekday": "周四",
        "time": "18:30 – 21:20",
        "room": "MP-16F-01B / 01A",
        "semester": "2026-27 S1",
        "tasks": [
            {"title": "基础挖掘代码作业", "due": "2026-09-22", "kind": "作业"},
            {"title": "数据集与预测思路 Presentation", "due": "2026-10-20", "kind": "演示"},
            {"title": "完整挖掘项目 + 报告", "due": "2026-11-17", "kind": "项目"},
            {"title": "Group Work Submission（Turnitin）", "due": "2026-11-26", "kind": "小组"},
            {"title": "Individual Essay Submission（Turnitin）", "due": "2026-12-08", "kind": "论文"}
        ],
        "note": "核心必修课，周四晚双班授课"
    },
    {
        "code": "INT6140",
        "name": "未来工作与劳动力趋势",
        "name_en": "FUTURE OF WORK AND WORKFORCE TRENDS",
        "weekday": "周五",
        "time": "14:30 – 17:20",
        "room": "N-G/F-08",
        "semester": "2026-27 S1",
        "tasks": [
            {"title": "PPT 提交", "due": "2026-11-27", "kind": "作业"},
            {"title": "完整展示视频提交", "due": "2026-11-27", "kind": "作业"},
            {"title": "小组报告提交（Turnitin）", "due": "2026-11-29", "kind": "小组"},
            {"title": "课后报告 Reflective Report", "due": "2026-11-30", "kind": "作业"},
            {"title": "个人作品集提交", "due": "2026-12-04", "kind": "作业"},
            {"title": "（可选）小组贡献反馈", "due": "2026-12-06", "kind": "可选"}
        ],
        "note": "周五下午班（官方课表确认：未来工作与劳动力趋势 = INT6140）"
    },
    {
        "code": "INT6141",
        "name": "新兴技术促进劳动力发展",
        "name_en": "EMERGING TECHNOLOGIES FOR WORKFORCE DEVELOPMENT",
        "weekday": "周五",
        "time": "18:30 – 21:20",
        "room": "待确认",
        "semester": "2026-27 S1",
        "tasks": [
            {"title": "小组报告提交（PPT + 報告）", "due": "2026-12-01", "kind": "小组"},
            {"title": "个人作品集提交", "due": "2026-12-11", "kind": "作业"}
        ],
        "note": "周五晚间班；教室待确认"
    },
    {
        "code": "INT6136",
        "name": "工作与居家场景的人工智能趋势",
        "name_en": "TRENDS IN ARTIFICIAL INTELLIGENCE AT WORKPLACE AND AT HOME",
        "weekday": "周三",
        "time": "18:30 – 21:20",
        "room": "待确认",
        "semester": "2026-27 S1",
        "tasks": [
            {"title": "小组项目", "due": "2026-12-14", "kind": "小组"},
            {"title": "个人项目（Turnitin）", "due": "2026-12-14", "kind": "项目"}
        ],
        "note": "周三晚间班；教室待确认"
    }
]

# -------------------------- 招聘数据源（2026 秋招，真实信息已标注来源） --------------------------
STUDENT_RECRUIT = [
    # ---- 银行（香港） ----
    {"name": "中国银行（香港）BOCHK", "type": "银行", "window": "MT 计划已开放（2026 Intake）", "note": "24 个月加速管培；另设大湾区培训生、东南亚启航实习计划", "src": "bochk.com 官网"},
    {"name": "汇丰 HSBC", "type": "银行", "window": "Graduate 9月3日开放 · 12月4日截止", "note": "环球市场销售与交易、零售银行与财富管理等多方向，2027年7月入职", "src": "hsbc.com 官网"},
    {"name": "恒生银行 Hang Seng", "type": "银行", "window": "MT 9月8日开放 · 11月30日截止", "note": "零售银行与财富管理管培；另有 12 个月毕业生全职计划（2026-27）", "src": "hangseng.com 官网"},
    {"name": "渣打银行 Standard Chartered", "type": "银行", "window": "Graduate 8–9月开放申请", "note": "24 个月毕业生计划，2027年7月入职，全专业可申", "src": "sc.com 官网"},
    {"name": "东亚银行 BEA", "type": "银行", "window": "秋招 9–12 月（以官网为准）", "note": "香港本地银行管培与 Graduate Programme", "src": "hk.bea.com"},
    # ---- 四大 ----
    {"name": "普华永道 PwC", "type": "四大", "window": "秋招 8–11 月", "note": "审计 / 咨询 MT，2026 秋招已开放", "src": "pwc.com 官网"},
    {"name": "德勤 Deloitte", "type": "四大", "window": "秋招 8–11 月", "note": "审计、风险咨询、数字化咨询岗", "src": "deloitte.com 官网"},
    {"name": "安永 EY", "type": "四大", "window": "秋招 8–11 月", "note": "审计、税务、交易咨询", "src": "ey.com 官网"},
    {"name": "毕马威 KPMG", "type": "四大", "window": "秋招 8–11 月", "note": "审计、管理咨询、香港毕业生计划", "src": "kpmg.com 官网"},
    # ---- 券商 / 投行（香港） ----
    {"name": "中银国际 BOCI", "type": "券商", "window": "秋招 9–12 月（以官网为准）", "note": "投行、研究、销售交易校招通道", "src": "bocigroup.com"},
    {"name": "华泰国际 Huatai", "type": "券商", "window": "秋招 9–12 月（以官网为准）", "note": "香港持牌券商校招与实习转正通道", "src": "huatai.com.hk"},
    {"name": "中金公司 CICC", "type": "券商", "window": "秋招 9–11 月（以官网为准）", "note": "投行、研究、资产管理香港岗位", "src": "cicc.com 官网"},
    # ---- 港资 / 跨国大企业 ----
    {"name": "国泰航空 Cathay", "type": "航空", "window": "毕业培训生 11月15日截止申请", "note": "2027 货运 / 数码及资讯科技 / 工程毕业培训生计划，2027年8月入职", "src": "careers.cathaypacific.com"},
    {"name": "港铁 MTR", "type": "交通", "window": "GT 9月15日–10月27日（本期已截止）", "note": "8 个方向毕业生培训计划（GT），7月入职；关注下一期", "src": "mtr.com.hk"},
    {"name": "太古 Swire", "type": "综合集团", "window": "管理培训生 9月11日–10月31日（本期已截止）", "note": "太古管理培训生计划 2027、太古财务领导力计划（SFP）", "src": "careers.swire.com"},
    {"name": "港灯 HK Electric", "type": "能源公用", "window": "见习工程师计划开放申请", "note": "2–3 年 Scheme A 培训，土木/电机/电子/机械/IT 专业应届生", "src": "hkelectric.com"},
    {"name": "中电 CLP", "type": "能源公用", "window": "秋招 9–11 月（以官网为准）", "note": "Graduate Trainee 计划，工程与商业方向", "src": "clp.com.hk"},
    # ---- 央企能源 ----
    {"name": "中石油校园招聘", "type": "能源", "window": "秋招 9–11 月", "note": "内地能源校招，研发 / 工程 / 市场岗", "src": "zhaopin.cnpc.com.cn"},
    {"name": "中石化校园招聘", "type": "能源", "window": "秋招 9–11 月", "note": "总部及分公司校招通道", "src": "job.sinopec.com"},
    # ---- 内地大厂（大湾区 / 远程） ----
    {"name": "腾讯 Tencent", "type": "互联网", "window": "校招已开放", "note": "技术研究（AI/基础架构）、算法-机器学习、产品、设计；深圳/北京/上海/广州", "src": "join.qq.com"},
    {"name": "美团 Meituan", "type": "互联网", "window": "校招已开放（574 个职位）", "note": "应届生校招 + 北斗计划（大模型、自动驾驶、无人机、具身智能）", "src": "zhaopin.meituan.com"},
    {"name": "字节跳动 ByteDance", "type": "互联网", "window": "校招已开放", "note": "国际化业务、算法、产品校招", "src": "jobs.bytedance.com"},
    {"name": "阿里巴巴 Alibaba", "type": "互联网", "window": "校招已开放", "note": "阿里国际、云计算、电商技术岗", "src": "campus.alibaba.com"},
    {"name": "华为 Huawei", "type": "科技", "window": "秋招 8–10 月（以官网为准）", "note": "研发、市场、财经应届生岗位", "src": "career.huawei.com"},
    {"name": "比亚迪 BYD", "type": "新能源车", "window": "秋招 8–11 月（以官网为准）", "note": "工程、研发、海外市场应届生招聘", "src": "job.byd.com"}
]

SOCIAL_RECRUIT = {
    "金融": [
        {"name": "摩根大通", "note": "资深分析师、风控岗持续放出"},
        {"name": "中金公司", "note": "投行、研究社招"},
        {"name": "恒生银行", "note": "香港本地金融社招"}
    ],
    "科技": [
        {"name": "腾讯香港", "note": "后端、算法、产品社招"},
        {"name": "阿里国际", "note": "跨境电商技术岗"},
        {"name": "字节跳动", "note": "国际化业务社招"}
    ],
    "能源": [
        {"name": "壳牌", "note": "能源交易、可持续发展岗"},
        {"name": "BP", "note": "亚太能源业务社招"}
    ],
    "咨询": [
        {"name": "麦肯锡", "note": "社会招聘资深顾问"},
        {"name": "波士顿 BCG", "note": "亚太咨询社招"}
    ],
    "快消": [
        {"name": "联合利华", "note": "品牌、市场社招"},
        {"name": "宝洁", "note": "供应链、市场岗"}
    ]
}

# -------------------------- 香港本地点位库 --------------------------
PLACE_POOL = [
    {
        "title": "香港大学美心食堂",
        "desc": "安静适合自习，平价简餐，人相对少",
        "tags": ["自习", "平价餐饮"],
        "trans": "港铁港岛线 HKU 站",
        "cost": 1,
        "img": "https://images.unsplash.com/photo-1541339907198-e08756dedf3f?w=600"
    },
    {
        "title": "西环码头",
        "desc": "看日落，短途散步放空，拍照很好看",
        "tags": ["拍照", "独处"],
        "trans": "港铁港岛线西营盘站步行 10 min",
        "cost": 1.5,
        "img": "https://images.unsplash.com/photo-1444723121867-7a241cacace9?w=600"
    },
    {
        "title": "K11 MUSEA",
        "desc": "文创空间，休息逛街，环境精致",
        "tags": ["逛街", "文创"],
        "trans": "港铁尖东站 / 尖沙咀站",
        "cost": 2,
        "img": "https://images.unsplash.com/photo-1578683010236-d716f9a3f461?w=600"
    },
    {
        "title": "香港中央图书馆",
        "desc": "超大安静自习区，座位充足",
        "tags": ["自习"],
        "trans": "港铁天后站步行",
        "cost": 2,
        "img": "https://images.unsplash.com/photo-1521587760476-6c12a4b040da?w=600"
    },
    {
        "title": "太平山山腰凉亭",
        "desc": "短途徒步，俯瞰维港，适合放松",
        "tags": ["独处", "拍照"],
        "trans": "太平山缆车 / 巴士上山",
        "cost": 3,
        "img": "https://images.unsplash.com/photo-1534430480872-3498386e7856?w=600"
    },
    {
        "title": "深水埗街头小吃",
        "desc": "鱼蛋、鸡蛋仔、肠粉一条街吃到饱，最有烟火气的港味",
        "tags": ["吃喝", "平价"],
        "trans": "港铁深水埗站步行",
        "cost": 1.5,
        "img": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=600"
    },
    {
        "title": "中环海滨长廊 + 摩天轮",
        "desc": "海风、天际线、20 港币坐摩天轮转 3 圈，傍晚去最舒服",
        "tags": ["拍照", "散步"],
        "trans": "港铁香港站 / 中环站步行",
        "cost": 1.5,
        "img": "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=600"
    },
    {
        "title": "星光大道 · 维港夜景",
        "desc": "明星手印打卡 + 8 点灯光秀，来港必看的夜景",
        "tags": ["拍照", "夜景"],
        "trans": "港铁尖沙咀站步行",
        "cost": 2,
        "img": "https://images.unsplash.com/photo-1508804185872-d7badad00f7d?w=600"
    },
    {
        "title": "大馆 Tai Kwun",
        "desc": "前中区警署改造的艺术文化地标，展览常换，免费入场",
        "tags": ["文化", "文艺"],
        "trans": "港铁中环站步行 10 min",
        "cost": 2.5,
        "img": "https://images.unsplash.com/photo-1544967082-d9d25d867d66?w=600"
    },
    {
        "title": "赤柱海滨小镇",
        "desc": "海边小镇 + 美利楼 + 市集，逛完还能在海边咖啡店发呆",
        "tags": ["独处", "放松"],
        "trans": "港铁香港站转巴士 6/6A/73",
        "cost": 3.5,
        "img": "https://images.unsplash.com/photo-1506973035872-a4ec16b8e8d9?w=600"
    },
    {
        "title": "麦理浩径一段",
        "desc": "万宜水库到浪茄湾，山海徒步经典路线，天气好时海水超蓝",
        "tags": ["徒步", "大自然"],
        "trans": "西贡巴士 94R / 小巴直达北潭涌",
        "cost": 4,
        "img": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=600"
    },
    {
        "title": "庙街夜市",
        "desc": "入夜后的地道港味：大排档、煲仔饭、算命摊，市井气息拉满",
        "tags": ["吃喝", "夜景"],
        "trans": "港铁佐敦站步行",
        "cost": 1.5,
        "img": "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?w=600"
    },
    {
        "title": "旺角女人街 / 波鞋街",
        "desc": "平价扫货一条街，逛累了顺便吃个糖水",
        "tags": ["逛街", "平价"],
        "trans": "港铁旺角站步行",
        "cost": 1.5,
        "img": "https://images.unsplash.com/photo-1449824913935-59a10b8d2000?w=600"
    },
    {
        "title": "铜锣湾时代广场",
        "desc": "中高端商场 + 街头艺人，傍晚的霓虹很出片",
        "tags": ["逛街", "拍照"],
        "trans": "港铁铜锣湾站步行",
        "cost": 1.5,
        "img": "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=600"
    },
    {
        "title": "香港艺术馆",
        "desc": "维港旁免费看展，常有中国书画与当代艺术特展",
        "tags": ["文化", "文艺"],
        "trans": "港铁尖沙咀站步行",
        "cost": 2,
        "img": "https://images.unsplash.com/photo-1518998053901-5348d3961a04?w=600"
    },
    {
        "title": "九龙公园",
        "desc": "闹市中的绿洲，有泳池、鸟湖和雕塑径，散步发呆都舒服",
        "tags": ["散步", "独处"],
        "trans": "港铁尖沙咀站步行",
        "cost": 2,
        "img": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=600"
    },
    {
        "title": "观塘海滨花园",
        "desc": "观塘码头海滨步道，傍晚看维港东岸日落",
        "tags": ["散步", "拍照"],
        "trans": "港铁观塘站步行 10 min",
        "cost": 2,
        "img": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=600"
    },
    {
        "title": "昂坪 360 缆车",
        "desc": "25 分钟缆车看大屿山全景，山顶有市集和天坛大佛",
        "tags": ["景点", "拍照"],
        "trans": "港铁东涌站转缆车站",
        "cost": 3,
        "img": "https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?w=600"
    },
    {
        "title": "南丫岛徒步",
        "desc": "榕树湾到索罟湾，海鲜大餐收尾，离岛一日游首选",
        "tags": ["徒步", "大自然"],
        "trans": "中环 4 号码头乘船",
        "cost": 3.5,
        "img": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=600"
    },
    {
        "title": "龙脊徒步径",
        "desc": "石澳龙脊，亚洲最佳徒步路线之一，俯瞰大浪湾",
        "tags": ["徒步", "拍照"],
        "trans": "筲箕湾站转 9 号巴士土地湾下",
        "cost": 3.5,
        "img": "https://images.unsplash.com/photo-1447752875215-b2761acb3c5d?w=600"
    },
    {
        "title": "长洲岛",
        "desc": "小岛慢生活：单车环岛、沙滩、芒果糯米糍，适合放空一整天",
        "tags": ["独处", "放松"],
        "trans": "中环 5 号码头乘船约 1 小时",
        "cost": 4,
        "img": "https://images.unsplash.com/photo-1502920514313-52581002a659?w=600"
    }
]

# -------------------------- 经验贴库 --------------------------
EXPERIENCE_LIST = [
    {
        "title": "港硕选课避坑｜如何拿到高 GPA",
        "tag": "选课",
        "content": """
# 港硕选课避坑｜如何拿到高 GPA

## 1. 课前调研
优先查看往届学长学姐流传出来的课程评分分布。部分课程老师压分严重，整体班级平均分只有B‑，尽量谨慎选择。
- 多在社群询问往届修课同学真实体验
- 小组作业占比高的课程，提前确认队友水平

## 2. 小组作业要点
小组作业是很多港硕课程的大头分数，占比经常40%‑60%。
1. **开课第一周锁定靠谱队友**，不要等到作业截止前临时组队
2. 明确分工，记录每个人交付时间节点
3. 定期开会同步进度，避免有人划水拖累全组

## 3. 考试与作业策略
- 平时作业不要简单复制网上内容，港校查重标准严格
- 重视课堂参与分，很多课程课堂发言会计入总分
> 总结：选课不看课程名字好不好听，要看给分松紧。
""",
        "img": "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=600",
        "comments": [
            {"user": "港仔阿明", "text": "亲测有效，压分课真的会心态崩！", "like": 312},
            {"user": "一只留学猫", "text": "感谢，已经把这篇转给室友了", "like": 187}
        ]
    },
    {
        "title": "香港租房完整流程 & 防骗指南",
        "tag": "租房",
        "content": """
# 香港租房完整流程 & 防骗指南

香港租房水很深，很多内地学生刚来很容易踩坑。

## 签约前必做检查
1. 一定要查看房东的**产权证明（屋契）**，核对身份证与产权人一致。
2. 如果是二房东转租，必须拿到原房东书面同意转租文件，否则合同无效。
3. 实地看房，检查空调、热水器、水管、电路是否正常。

## 费用问清楚
- 房租是否包含水电网、管理费
- 押金金额（一般两押一付）
- 退租条件，提前多久通知，扣押金的条款

## 签约提醒
所有口头承诺全部写到书面合同，不要相信口头保证。签约逐条细读每一项条款。
""",
        "img": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=600",
        "comments": [
            {"user": "新来的硕士", "text": "上个月差点被二房东坑，这个太及时了", "like": 422},
            {"user": "港岛打工人", "text": "签约条款一定要逐条细读", "like": 201}
        ]
    },
    {
        "title": "IANG 签证申请全流程",
        "tag": "IANG",
        "content": """
# IANG签证申请全流程

IANG是非本地毕业生留港最重要签证通道，毕业后不需要预先拿到工作就可以申请。

## 时间节点
- 拿到毕业证之后就可以递交，**不要拖到最后一个月**
- 处理排队时间不稳定，高峰期可达2‑3个月

## 需要准备材料
1. 港澳通行证及有效签注
2. 香港院校毕业证明、成绩单
3. 身份证，证件照片
4. 入境处申请表格

## 小提示
递交之后可以网上查询进度；拿到IANG之后，之后换工作不需要重新申请签证。
""",
        "img": "https://images.unsplash.com/photo-1580894894513-541e068a3e2b?w=600",
        "comments": [
            {"user": "留港选手", "text": "已经收藏，明年毕业要用！", "like": 513},
            {"user": "港漂学姐", "text": "建议毕业后尽快递交，排队时间不稳定", "like": 276}
        ]
    },
    {
        "title": "四大秋招面经｜群面技巧",
        "tag": "秋招",
        "content": """
# 四大秋招面经｜群面技巧

四大群面刷人比例很高，重点不是抢话多，而是逻辑和团队协作。

## 角色选择
你可以选下面其中一个定位，不要盲目抢leader：
1. **记录者**：记录大家观点，最后整理汇总
2. **协调者**：把控时间，拉回跑题话题
3. **方案输出者**：给出结构化分析框架

❌ 避雷：不要全程抢话、否定队友，会直接扣分。

## 准备建议
提前刷案例题库，练习商业分析框架；发言前简单组织语言，简短清晰表达观点。
""",
        "img": "https://images.unsplash.com/photo-1552664730-d307ca884978?w=600",
        "comments": [
            {"user": "冲刺四大", "text": "去年就是因为抢话挂了群面，记住教训", "like": 621},
            {"user": "求职小狗", "text": "准备案例库真的很重要", "like": 345}
        ]
    },
    {
        "title": "毕业论文时间规划｜不拖到最后",
        "tag": "论文",
        "content": """
# 毕业论文时间规划｜不要拖到最后一刻

很多同学容易踩坑：总觉得时间很多，最后熬夜爆肝。

## 时间拆分建议
1. **定题阶段**：尽早和导师开会，确认题目可行性
2. **文献阅读阶段**：边读边整理笔记，不要堆到后面
3. **实验 / 数据阶段**：预留容错时间，代码、数据很容易出bug
4. **初稿写作**：写完第一版，交给导师反馈
5. **修改、校对、格式排版**

> 忠告：千万不要相信自己一周写完毕业论文。
定期约导师meeting，不要消失等到截止日前才找老师。
""",
        "img": "https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?w=600",
        "comments": [
            {"user": "赶论文选手", "text": "正在痛苦写论文，哭了", "like": 288},
            {"user": "顺利毕业学长", "text": "不要相信自己可以一周写完论文", "like": 409}
        ]
    },
    {
        "title": "港硕一周时间管理｜作业不堆到最后",
        "tag": "学习",
        "content": """
# 港硕一周时间管理｜作业不堆到最后

一周 4 门课 3 个晚上在上课，作业还都是小组 + 个人混合，怎么排才不炸？

## 固定节奏法（亲测好用）
1. **周一 / 周二**：把本周所有 DDL 抄进日历，按"先小组后个人"排优先级
2. **周三**：上课前把前一周的笔记复盘完，避免越积越多
3. **周四 / 周五**：晚上上课，白天留 2-3 小时专攻本周最重的一项作业
4. **周末**：至少留一个半天给自己（这点很重要，不然会崩）

## 小组作业提醒
- 小组任务永远比个人任务早开始：队友的节奏不可控
- 每周固定一次 15 分钟对齐会，比临时抓人效率高很多

> 核心原则：**先完成，再完美**。港硕作业看的是按时交付，不是追求满分。
""",
        "img": "https://images.unsplash.com/photo-1523240795612-9a054b0db644?w=600",
        "comments": [
            {"user": "时间管理菜鸟", "text": "周末留半天给自己这个太真实了", "like": 356},
            {"user": "港硕二年级", "text": "小组任务永远先开始，血泪经验", "like": 518}
        ]
    },
    {
        "title": "香港生活攻略｜八达通 / 银行卡 / 手机卡一次办齐",
        "tag": "生活",
        "content": """
# 香港生活攻略｜八达通 / 银行卡 / 手机卡一次办齐

刚落地香港，这四件事建议第一周就办掉。

## 1. 八达通（最优先）
- 港铁站客服中心就能办，学生八达通半价乘港铁
- 办学生八达通需要学校发的在读证明，拿到学生证马上去办

## 2. 香港银行卡
- 常见选择：中银香港、汇丰、渣打；学校附近都有网点
- 带上：港澳通行证 + 学生签证 + 住址证明（租约/水电单）+ 内地身份证
- 中银香港和内地中行同名账户互转免费，很多同学选它

## 3. 手机卡
- 学生套餐：CMHK / 3HK / Smartone 都有学生优惠，校园网点可办
- 保留内地号码：办个「一卡两号」或保留内地号收验证码

## 4. 学生证 & 图书馆卡
- 学生证不仅是进校门用的，很多景点、电影、博物馆有学生价

> 小提示：银行开户高峰期排队很夸张，建议早上开门就去。
""",
        "img": "https://images.unsplash.com/photo-1516387938699-a93567ec168e?w=600",
        "comments": [
            {"user": "刚落地新人", "text": "学生八达通半价这个信息太有用了！", "like": 634},
            {"user": "港漂三年", "text": "开户真的要早去，下午经常没号", "like": 412}
        ]
    },
    {
        "title": "港硕边读书边秋招｜时间线安排",
        "tag": "秋招",
        "content": """
# 港硕边读书边秋招｜时间线安排

港硕一年制，秋招和学业是同期进行的，必须双线作战。

## 关键时间线
1. **8-9 月**：改简历、研究目标公司；银行和四大的秋招 8 月底到 9 月初陆续开
2. **9-11 月**：集中投递 + 笔试；**11 月是港校作业高峰，务必提前投完**
3. **12 月**：面试集中期；寒假前尽量拿到 1-2 个保底
4. **次年 1-3 月**：春招补录 + 秋招 Offer 定夺；毕业前把 IANG 材料备好

## 双线作战技巧
- 把投递当作"碎片任务"：课间、等车时完成一家公司的申请
- 每周固定一个晚上集中刷笔试，不要拖到 DDL 当天
- 作业截止和面试撞车时，**先保证作业交付**——面试可以改期，作业不行

> 记住：港硕一年过得飞快，秋招窗口就那几个月，越早投越主动。
""",
        "img": "https://images.unsplash.com/photo-1461749280684-dccba630e2f6?w=600",
        "comments": [
            {"user": "双线作战中", "text": "作业撞面试那条太真实了", "like": 745},
            {"user": "已上岸学姐", "text": "11月前投完真的关键，12月全是面试", "like": 388}
        ]
    },
    {
        "title": "小组作业英语 Presentation 实战技巧",
        "tag": "学习",
        "content": """
# 小组作业英语 Presentation 实战技巧

港硕小组展示大多是全英文，口语不自信也能做好。

## 开场 30 秒定胜负
- 第一句话不要说"I'm going to present..."，直接给结论："Our key finding is..."
- 开场讲清楚三件事：背景、目标、你们做了什么

## 分工与衔接
- 每人负责自己最熟的部分，按逻辑顺序排（背景→方法→结果→建议）
- 交接时说："Let me hand over to XX, who will walk you through the methodology."
- 提前排练 2 次以上，重点练衔接和结尾

## 应对提问
- 听不懂时用："Could you rephrase that for me?" 完全正常，不丢人
- 答不上来就说："That's a great point — we didn't test it, but I'd look into it next."

> 小技巧：把要点写成关键词卡片而不是逐字稿，讲的时候更自然。
""",
        "img": "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=600",
        "comments": [
            {"user": "口语恐惧症", "text": "开场直接给结论这个技巧立竿见影", "like": 502},
            {"user": "Presentation 苦手", "text": "排练两次真的比背稿有用", "like": 297}
        ]
    },
    {
        "title": "港硕期末复习冲刺攻略",
        "tag": "学习",
        "content": """
# 港硕期末复习冲刺攻略

期末和 Final 项目挤在一起，怎么安排复习最有效？

## 复习节奏（考前 3 周）
1. **第 1 周**：按课程把笔记整理成提纲，明确每门课的重点章节
2. **第 2 周**：刷 past paper 和往年真题，港校题型重复率高
3. **考前 3 天**：只复习提纲 + 错题，不再学新内容

## 学科差异
- 偏计算/代码的课（如数据挖掘）：**动手重跑一遍作业代码**，理解每一步
- 偏理论/论述的课：整理"观点 + 案例"卡片，考试直接套用

## 双线并行
- 期末前所有小组项目尽量提前交付，别把 Final 和 Project 挤在同一周
- 白天复习，晚上处理作业碎片，每天给自己留 30 分钟放空

> 核心：港硕考试考的是**理解 + 熟练度**，不是死记硬背。
""",
        "img": "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=600",
        "comments": [
            {"user": "期末焦虑中", "text": "刷 past paper 真的很有用", "like": 431},
            {"user": "高分学姐", "text": "考前只看提纲+错题，亲测高效", "like": 356}
        ]
    },
    {
        "title": "香港看病就医 & 保险指南",
        "tag": "生活",
        "content": """
# 香港看病就医 & 保险指南

在香港看病和内地差别很大，提前搞清楚省很多麻烦。

## 看病渠道
1. **普通感冒/小病**：找社区诊所（普通科门诊），价格便宜但要排队
2. **急症**：直接去公立医院急症室，按紧急程度分流（非紧急可能要等几小时）
3. **专科/私诊**：私立医院或私家诊所快但贵，看诊费几百到上千

## 保险必须买
- 港校一般强制学生买**团体医疗险**，先确认自己有没有
- 建议再买一份**意外险 + 门诊补充险**，覆盖团体险不报的部分
- 保险单号、联系方式存手机里，看病挂号要出示

## 常用小贴士
- 发烧感冒药可以在万宁/屈臣氏直接买，不用看医生
- 牙科、眼科一般不在普通医疗险里，提前问清楚
- 保留所有收据，后续理赔要用

> 重要：不要为了省钱不买保险，香港看一次私立急诊可能花掉半个月生活费。
""",
        "img": "https://images.unsplash.com/photo-1584036561566-baf8f5f1b144?w=600",
        "comments": [
            {"user": "健康第一", "text": "急症室排队真的会等到怀疑人生", "like": 289},
            {"user": "保险已买", "text": "牙科不报销这点深有体会", "like": 376}
        ]
    },
    {
        "title": "简历 STAR 法则｜港企投递细节",
        "tag": "秋招",
        "content": """
# 简历 STAR 法则｜港企投递细节

港企筛简历很快，平均 30 秒一份，怎么写才能过？

## STAR 法则写经历
每段经历都按四步写，不要写"负责了 XX"这种空话：
1. **S（情境）**：在什么背景下做这件事
2. **T（任务）**：你负责的目标是什么
3. **A（行动）**：你具体做了什么（动词开头，量化）
4. **R（结果）**：结果如何，最好有数字（提升 30%、节省 20 小时）

示例：
- ❌ "负责数据分析"
- ✅ "在课程项目中（S）为 5 万条客户数据建模（T），用 Python 完成清洗与聚类（A），预测准确率提升至 92%（R）"

## 港企投递细节
- 简历用**英文为主 + 中文对照**，港资/外企对英文要求高
- 文件名写成「姓名-学校-岗位-2026届」，HR 下载后一眼认得出
- 网申系统里的每个空都填满，很多系统用关键词自动筛人
- 附上成绩单（GPA 3.0+ 就放）和获奖证书 PDF

> 记住：简历不是人生经历全集，是**目标岗位的定制广告**。
""",
        "img": "https://images.unsplash.com/photo-1506784983877-45594efa4cbe?w=600",
        "comments": [
            {"user": "简历苦手", "text": "STAR 法则写完整个人都通透了", "like": 689},
            {"user": "HR 视角", "text": "文件名规范真的会加分，太多人乱命名", "like": 457}
        ]
    },
    {
        "title": "港硕学生优惠薅羊毛指南｜博物馆 / 交通 / 数码",
        "tag": "生活",
        "content": """
# 港硕学生优惠薅羊毛指南

香港对学生身份有大量隐藏优惠，办张学生证能省出一顿饭钱。

## 交通
- 学生八达通：港铁半价（13-25 岁全职学生），开学第一周就去办
- 港铁特惠站：拍卡再进闸每程省 2 港币，很多站都有

## 博物馆 / 文化
- 香港艺术馆、香港科学馆、M+ 等对全日制学生免费或半价
- 电影学生票通常省 20-30 港币

## 数码 / 生活
- Apple 教育优惠：每年开学季买 Mac / iPad 送 AirPods
- Adobe / Notion / Spotify 都有学生订阅价，港校邮箱即可认证
- 部分连锁餐厅、咖啡店出示学生证有 9 折

> 核心：**所有能出示学生证的地方都出示一下**，很多优惠不问就没有。
""",
        "img": "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=600",
        "comments": [
            {"user": "省钱小能手", "text": "M+ 学生免费这个太香了", "like": 356},
            {"user": "开学第一周", "text": "学生八达通半价是真的，快去办", "like": 412}
        ]
    },
    {
        "title": "秋招网申系统操作避坑指南",
        "tag": "秋招",
        "content": """
# 秋招网申系统操作避坑指南

港企和内地大厂的网申系统各不相同，操作失误直接错过申请窗口。

## 常见坑
1. **简历附件格式**：有的系统只要 PDF，有的要 Word 或特定文件名；提前读清楚再传
2. **网申页停留超时**：很多系统 20-30 分钟不操作会掉线，长表单先本地备好内容再粘贴
3. **推荐人邮箱**：部分系统要求填推荐人邮箱并发送确认邮件，提前和推荐人打招呼
4. **提交后无法修改**：多数系统提交即锁定，提交前逐页截图存档

## 时间管理
- 把每家公司的申请信息（账号、截止、状态）记进 Be-Time 的网申进度
- 提前 2-3 天提交，不要踩点——系统卡死/银行转账手续费等问题都可能踩坑

> 记住：网申不是终点，是开始——提交后定期查邮箱和垃圾箱。
""",
        "img": "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=600",
        "comments": [
            {"user": "踩坑选手", "text": "表单超时掉线真的会让人崩溃", "like": 287},
            {"user": "已投 20 家", "text": "每家公司一个表格记录状态，强烈建议", "like": 498}
        ]
    },
    {
        "title": "港硕小组合作避坑指南｜分工 / 沟通 / 冲突",
        "tag": "学习",
        "content": """
# 港硕小组合作避坑指南

港硕小组作业占比高，队友来自不同文化背景，合作方式是拿分关键。

## 组队第一周就做的事
1. 交换联系方式 + 各自擅长领域，明确分工（数据/代码/报告/PPT）
2. 定一个**固定例会时间**（如每周三晚 20:00 线上 15 分钟）
3. 建共享文档（Google Docs / Notion），所有进度可见

## 沟通原则
- 用英文沟通时写清楚，重要信息在群里同步（不要只私聊）
- 遇到分歧先对事不对人："We have two options, let's compare..."
- 有人掉线时，提前 48 小时发提醒，不要临场抓人

## 冲突处理
- 贡献不均：例会时摆出共享文档记录，让事实说话
- 实在无法合作：尽早和老师说明情况，不要拖到提交

> 核心：**把每个人做了什么记录下来**，这是保护自己最好的方式。
""",
        "img": "https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?w=600",
        "comments": [
            {"user": "组长本长", "text": "共享文档记录进度真的能避免 90% 扯皮", "like": 511},
            {"user": "跨文化组队", "text": "对事不对人这句话太重要了", "like": 344}
        ]
    }
]
# -------------------------- Session State 初始化 --------------------------
def init_state():
    defaults = {
        "launched": False,
        "current_page": "study_all",
        "theme_key": "study",
        "dark_mode": False,
        "user_profile": {
            "name": "",
            "entry_year": "2026",
            "target_career": "无"
        },
        "identity_mode": "student",
        "selected_industry": "金融",
        "goal_mode": "career",
        "onboarding_done": True,
        "timeline_view": "all",
        "starred_events": set(),
        "finished_events": set(),
        "fav_places": [],
        "trip_plan": [],
        "saved_articles": [],
        "notifications": [],
        "place_seed": random.randint(0, 9999),
        "free_hours": 1.0,
        "selected_post": None,
        "applications": [],
        "ddl_alert_handled": None,
        "alert_log": [],
        "discussions": []
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
    # 恢复上次保存的数据（本地持久化）
    saved = load_state()
    if saved:
        st.session_state["finished_events"] = set(saved.get("finished_events", []))
        st.session_state["starred_events"] = set(saved.get("starred_events", []))
        for k in ["trip_plan", "fav_places", "saved_articles", "user_profile", "applications", "alert_log", "discussions"]:
            if k in saved:
                st.session_state[k] = saved[k]
        for k in ["place_seed", "free_hours", "dark_mode", "identity_mode", "selected_industry", "timeline_view", "goal_mode", "onboarding_done"]:
            if k in saved:
                st.session_state[k] = saved[k]
    else:
        # 完全没有历史数据 = 新用户：先展示个性化引导页
        st.session_state["onboarding_done"] = False

init_state()

# -------------------------- 个人看板任务（按课程与学业事件生成，勾选状态保存在会话中） --------------------------
def build_personal_tasks():
    tasks = []
    seen = set()
    for c in COURSES:
        for t in c.get("tasks", []):
            key = (t["due"], t["title"])
            if key in seen:
                continue
            seen.add(key)
            tasks.append({
                "id": f"c_{c['code']}_{len(tasks)}",
                "title": t["title"],
                "course": c["code"],
                "due": t["due"],
                "kind": t["kind"],
                "done": False
            })
    # 时间轴里与课程作业重复的条目（保留在时间轴展示，但不再进个人看板）
    SKIP_TIMELINE_TITLES = {"完整挖掘项目 + 报告 Deadline", "Group Work Turnitin 提交"}
    for e in RAW_EVENTS:
        if e["type"] != "academic":
            continue
        if e["title"] in ("秋季开学",) or e["title"] in SKIP_TIMELINE_TITLES:
            continue
        key = (e["date"], e["title"])
        if key in seen:
            continue
        seen.add(key)
        tasks.append({
            "id": f"evt_{len(tasks)}",
            "title": e["title"],
            "course": "通用",
            "due": e["date"],
            "kind": "学业",
            "done": False
        })
    tasks.sort(key=lambda x: x["due"])
    return tasks


if "personal_tasks" not in st.session_state:
    st.session_state["personal_tasks"] = build_personal_tasks()
# 恢复上次的勾选完成状态（按任务 id 对应）
_done_map = load_state().get("personal_done", {})
for _t in st.session_state["personal_tasks"]:
    if _t["id"] in _done_map:
        _t["done"] = bool(_done_map[_t["id"]])

# -------------------------- 全局 CSS & 动画 --------------------------
def render_global_css():
    theme = THEMES[st.session_state["theme_key"]]
    if st.session_state["dark_mode"]:
        t = theme["dark"]
    else:
        t = theme
    css = f"""
    <style>
    * {{ box-sizing: border-box; }}
    html, body {{
        margin: 0;
        padding: 0;
        font-family: "Segoe UI", "Microsoft YaHei", "PingFang SC", "Segoe UI Emoji", "Apple Color Emoji", "Noto Color Emoji", Roboto, sans-serif;
        background: {t["bg_grad"]};
        transition: background 0.6s ease;
    }}
    .stApp {{
        background: transparent !important;
    }}
    .fade-in {{
        animation: fadeIn 0.7s ease forwards;
    }}
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(12px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    .pulse-soft {{
        animation: pulseSoft 2.2s infinite ease-in-out;
    }}
    @keyframes pulseSoft {{
        0%, 100% {{ transform: scale(1); opacity: 0.9; }}
        50% {{ transform: scale(1.03); opacity: 1; }}
    }}
    .float {{
        animation: floatAnim 3.5s infinite ease-in-out;
    }}
    @keyframes floatAnim {{
        0%, 100% {{ transform: translateY(0px); }}
        50% {{ transform: translateY(-8px); }}
    }}
    .cover-wrap {{
        position: fixed;
        inset: 0;
        z-index: 9999;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        background: linear-gradient(-45deg, #1f4e79, #6b489e, #239984, #d67722);
        background-size: 400% 400%;
        animation: bgShift 12s ease infinite;
        color: white;
    }}
    @keyframes bgShift {{
        0% {{ background-position: 0% 50%; }}
        50% {{ background-position: 100% 50%; }}
        100% {{ background-position: 0% 50%; }}
    }}
    .cover-title {{
        font-size: 4.2rem;
        font-weight: 800;
        margin-bottom: 12px;
        text-shadow: 0 4px 20px rgba(0,0,0,0.25);
    }}
    .cover-sub {{
        font-size: 1.3rem;
        opacity: 0.9;
        margin-bottom: 48px;
    }}
    .cover-btn {{
        padding: 16px 44px;
        border-radius: 999px;
        border: none;
        font-size: 1.2rem;
        font-weight: 600;
        background: rgba(255,255,255,0.95);
        color: #1f4e79;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 6px 24px rgba(0,0,0,0.18);
    }}
    .cover-btn:hover {{
        transform: translateY(-4px);
        box-shadow: 0 10px 32px rgba(0,0,0,0.25);
    }}
    .nav-bar {{
        position: sticky;
        top: 0;
        z-index: 1000;
        padding: 14px 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: rgba(255,255,255,0.72);
        backdrop-filter: blur(10px);
        border-radius: 0 0 16px 16px;
    }}
    .nav-desktop {{
        display: flex;
        gap: 10px;
        align-items: center;
    }}
    .nav-item {{
        position: relative;
    }}
    .nav-card {{
        padding: 10px 16px;
        border-radius: 12px;
        color: white;
        font-weight: 600;
        cursor: pointer;
        white-space: nowrap;
        transition: transform 0.25s ease, box-shadow 0.25s ease;
    }}
    .nav-card:hover {{
        transform: translateY(-3px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.14);
    }}
    .dropdown-menu {{
        position: absolute;
        top: 100%;
        left: 0;
        min-width: 160px;
        background: white;
        border-radius: 12px;
        box-shadow: 0 8px 28px rgba(0,0,0,0.16);
        padding: 8px;
        margin-top: 6px;
        display: none;
    }}
    .nav-item:hover .dropdown-menu {{
        display: block;
    }}
    .dropdown-item {{
        padding: 8px 12px;
        border-radius: 8px;
        color: #333;
        cursor: pointer;
        transition: background 0.2s;
    }}
    .dropdown-item:hover {{
        background: #f0f4f8;
    }}
    .hamburger {{
        display: none;
        font-size: 28px;
        cursor: pointer;
    }}
    .mobile-menu {{
        display: none;
        position: fixed;
        top: 72px;
        left: 12px;
        right: 12px;
        background: white;
        border-radius: 16px;
        padding: 16px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.18);
        z-index: 998;
    }}
    @media (max-width: 820px) {{
        .nav-desktop {{ display: none; }}
        .hamburger {{ display: block; }}
    }}
    .badge-notify {{
        position: absolute;
        top: -4px;
        right: -4px;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #e74c3c;
    }}
    .card {{
        border-radius: 16px;
        padding: 20px;
        background: rgba(255,255,255,0.74);
        backdrop-filter: blur(8px);
        box-shadow: 0 4px 18px rgba(0,0,0,0.08);
        margin-bottom: 16px;
    }}
    .course-card {{ transition: transform .2s ease, box-shadow .2s ease; }}
    .course-card:hover {{ transform: translateY(-3px); box-shadow: 0 8px 26px rgba(0,0,0,0.12); }}
    .finished {{ opacity: 0.5; text-decoration: line-through; }}
    .stButton > button {{ border-radius: 999px; font-weight: 600; }}
    .stDownloadButton > button {{ border-radius: 999px; }}
    .stProgress > div > div > div > div {{ border-radius: 999px; }}
    h1, h2, h3 {{ letter-spacing: 0.5px; }}
    .stCheckbox label {{ font-size: 0.95rem; }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# -------------------------- 封面页 --------------------------
def render_cover():
    if st.session_state["launched"]:
        return

    # 只输出封面样式，不再使用position:fixed全屏遮罩div！
    st.markdown("""
    <style>
    .cover-container {
        text-align:center;
        padding-top:120px;
        padding-bottom:80px;
        background: linear-gradient(-45deg, #1f4e79, #6b489e, #239984, #d67722);
        background-size:400% 400%;
        animation: bgShift 12s ease infinite;
        border-radius:16px;
        color:white;
        padding: 80px 20px;
    }
    .cover-title {
        font-size: 4.2rem;
        font-weight: 800;
        margin-bottom: 12px;
        text-shadow: 0 4px 20px rgba(0,0,0,0.25);
    }
    .cover-sub {
        font-size:1.3rem;
        opacity:0.9;
        margin-bottom:32px;
    }
    .float {
        animation: floatAnim 3.5s infinite ease-in-out;
    }
    @keyframes bgShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    @keyframes floatAnim {
        0%,100% { transform: translateY(0px); }
        50% { transform: translateY(-8px); }
    }
    </style>

    <div class="cover-container fade-in">
        <div class="cover-title">Be‑Time</div>
        <div class="cover-sub">八达通小组 · 港硕一站式规划平台</div>
        <div class="float">
            <svg width="110" height="110" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="42" fill="rgba(255,255,255,0.22)" />
                <circle cx="36" cy="42" r="6" fill="#fff" />
                <circle cx="64" cy="42" r="6" fill="#fff" />
                <path d="M 34 60 Q 50 74 66 60" stroke="#fff" stroke-width="4" fill="none" stroke-linecap="round" />
            </svg>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ✅原生Streamlit按钮，100%可以点击！没有任何层级遮挡
    col1, col2, col3 = st.columns([2,1,2])
    with col2:
        if st.button("🚀 开始使用", key="enter_app", use_container_width=True):
            st.session_state["launched"] = True
            st.rerun()

    st.stop()

# -------------------------- 新用户个性化引导页（可跳过） --------------------------
def render_onboarding():
    """新用户首次进入时：填昵称 / 目标方向 / 偏好行业，用于个性化推荐；可跳过。"""
    st.markdown("""
    <style>
    .ob-wrap { text-align:center; padding:56px 16px 24px 16px; }
    .ob-badge { font-size:3.2rem; }
    .ob-title { font-size:1.9rem; font-weight:800; color:#1f4e79; margin:6px 0 4px 0; }
    .ob-sub { color:#777; font-size:0.95rem; margin-bottom:20px; }
    .ob-card {
        background: linear-gradient(135deg, #eef6ff, #f3eeff);
        border:1px solid #e3e8f5;
        border-radius:18px;
        padding:26px 26px 10px 26px;
        margin:0 auto 18px auto;
        max-width:620px;
        text-align:left;
    }
    </style>
    """, unsafe_allow_html=True)
    st.markdown('<div class="ob-wrap"><div class="ob-badge">🎓</div>'
                '<div class="ob-title">欢迎来到 Be-Time</div>'
                '<div class="ob-sub">花 10 秒告诉我们你的方向，后面每个页面都会更懂你（也可以直接跳过）</div></div>',
                unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="ob-card">', unsafe_allow_html=True)
        name = st.text_input("👤 怎么称呼你？（可留空）", key="ob_name", placeholder="例如：阿豪")
        goal = st.radio("🎯 你更关注哪个方向？", ["求职就业", "学术深造"], horizontal=True, key="ob_goal")
        industry = st.selectbox("🏢 求职最想进的行业（校招推荐会优先展示）",
                                ["金融", "互联网", "科技", "新能源", "综合集团", "暂时没想好"],
                                key="ob_industry")
        st.markdown('</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns([2, 1, 2])
    with c2:
        if st.button("🚀 开始我的 Be-Time", key="ob_start", use_container_width=True):
            nm = (name or "").strip()
            if nm:
                st.session_state["user_profile"]["name"] = nm
            st.session_state["goal_mode"] = "academic" if goal == "学术深造" else "career"
            st.session_state["selected_industry"] = industry
            st.session_state["onboarding_done"] = True
            save_state()  # 立即持久化，防止 rerun 后从旧 JSON 恢复
            st.rerun()
    c4, c5, c6 = st.columns([2, 1, 2])
    with c5:
        if st.button("先跳过，随便逛逛", key="ob_skip", use_container_width=True):
            st.session_state["onboarding_done"] = True
            save_state()  # 立即持久化
            st.rerun()


# -------------------------- 顶部导航（可点击、真正生效的菜单栏） --------------------------
def render_navbar():
    # 说明：原版用自定义 HTML + parent.postMessage 做下拉，但 Streamlit 里没有任何 JS 监听该消息，
    # 点击下拉项不会跳转；下方那排“隐藏”按钮也并未隐藏，重复且乱。这里改为原生按钮菜单，稳定可点。
    cols = st.columns(len(NAV_MENU))
    for col, menu in zip(cols, NAV_MENU):
        t = THEMES[menu["key"]]
        with col:
            st.markdown(
                f"<div style='padding:10px 12px;border-radius:12px 12px 0 0;"
                f"background:{t['primary']};color:white;font-weight:700;text-align:center;"
                f"font-size:1.05rem;'>{t['icon']} {menu['label']}</div>",
                unsafe_allow_html=True,
            )
            for child in menu["children"]:
                active = child["key"] == st.session_state.get("current_page", "")
                if st.button(
                    child["label"],
                    key=f"navbtn_{child['key']}",
                    use_container_width=True,
                    type="primary" if active else "secondary",
                ):
                    st.session_state["current_page"] = child["key"]
                    st.session_state["theme_key"] = menu["key"]
                    st.rerun()
# -------------------------- 工具函数：事件处理、排序、过滤 --------------------------
def parse_event(evt):
    dt = datetime.strptime(evt["date"], "%Y-%m-%d")
    return {
        **evt,
        "datetime": dt,
        "is_academic": evt["type"] == "academic",
        "is_career": evt["type"] == "career"
    }

def get_all_events():
    evts = [parse_event(e) for e in RAW_EVENTS]
    evts.sort(key=lambda x: x["datetime"])
    return evts

def filter_events(events, view_mode):
    if view_mode == "all":
        return events
    elif view_mode == "academic":
        return [e for e in events if e["is_academic"]]
    elif view_mode == "career":
        return [e for e in events if e["is_career"]]
    return events

# -------------------------- 学业推送提醒（自动检测快到期的作业） --------------------------
def render_academic_alerts(evts=None):
    """学业工作台顶部推送：哪门课作业快到期，按紧急度配色提醒。"""
    if evts is None:
        evts = get_all_events()
    now = datetime.now()
    pending = [e for e in evts if e["is_academic"] and e["datetime"] >= now
               and e["date"] not in st.session_state["finished_events"]]
    pending = sorted(pending, key=lambda x: x["datetime"])
    theme = THEMES[st.session_state["theme_key"]]
    if not pending:
        st.success("✅ 学业推送：当前没有待交作业，可以放心安排其他事情。")
        return

    def chip(e):
        days = (e["datetime"] - now).days
        if days <= 3:
            color, tag = "#e74c3c", "🔴 紧急"
        elif days <= 7:
            color, tag = "#e67e22", "🟠 临近"
        else:
            color, tag = "#3498db", "🔵 待办"
        return f'<span style="background:{color};color:#fff;padding:2px 10px;border-radius:999px;font-size:0.75rem;font-weight:600;white-space:nowrap;">{tag} 剩 {days} 天</span>'

    top = pending[:3]
    rows = "".join(
        f'<div style="display:flex;justify-content:space-between;align-items:center;gap:10px;padding:9px 2px;border-bottom:1px dashed #e5e9f0;">'
        f'<div><b>{e["title"]}</b><br/>'
        f'<span style="color:#888;font-size:0.82rem;">📅 {e["date"]} · {e.get("tag","")}</span></div>{chip(e)}</div>'
        for e in top)
    st.markdown(f"""
    <div class="card fade-in" style="border-left:5px solid {theme['primary']};">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px;">
            <b>⏰ 学业推送 · 快交作业提醒</b>
            <span style="color:#888;font-size:0.82rem;">共 {len(pending)} 项待交</span>
        </div>
        {rows}
    </div>
    """, unsafe_allow_html=True)
    if len(pending) > 3:
        st.caption(f"另有 {len(pending) - 3} 项稍后截止（可到课程一览 / 全景时间轴查看全部）")


# -------------------------- 学期进度 + 最近截止倒计时 --------------------------
# -------------------------- 个性化欢迎横幅（昵称 + 按方向的下一件要紧事） --------------------------
def render_personal_banner(events):
    now = datetime.now()
    name = (st.session_state["user_profile"].get("name") or "").strip() or "同学"
    goal = st.session_state.get("goal_mode", "career")
    goal_label = "🎓 学术深造" if goal == "academic" else "💼 求职就业"
    # 按方向找下一件未完成的事
    is_career = goal == "career"
    pend = [e for e in events if e["is_career"] == is_career
            and e["datetime"] >= now and e["date"] not in st.session_state["finished_events"]]
    pend = sorted(pend, key=lambda x: x["datetime"])
    if pend:
        nxt = pend[0]
        days = (nxt["datetime"] - now).days
        zone_key = "job_timeline" if is_career else "study_all"
        zone_label = "求职时间轴" if is_career else "学业工作台"
        st.markdown(f"""
        <div class="card fade-in" style="background:linear-gradient(135deg,#eaf4ff,#f0ecff);border:1px solid #dfe6f8;">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;">
                <div>
                    <span style="font-size:1.05rem;">👋 下午好，<b>{name}</b></span>
                    <span style="margin-left:10px;background:#1f4e79;color:#fff;padding:2px 12px;border-radius:999px;font-size:0.78rem;">{goal_label}</span>
                </div>
                <div style="color:#555;font-size:0.9rem;">
                    🎯 你的下一件要紧事：<b>{nxt['title']}</b>
                    <span style="color:{'#e74c3c' if days <= 3 else '#e67e22' if days <= 7 else '#3498db'};font-weight:700;">（剩 {days} 天）</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        c_a, c_b, c_c = st.columns([2, 2, 4])
        with c_b:
            if st.button(f"去处理 → 打开{zone_label}", key="banner_go", use_container_width=True):
                st.session_state["current_page"] = zone_key
                st.rerun()
    else:
        st.markdown(f"""
        <div class="card fade-in" style="background:linear-gradient(135deg,#eaf4ff,#f0ecff);border:1px solid #dfe6f8;">
            👋 下午好，<b>{name}</b>　<span style="background:#1f4e79;color:#fff;padding:2px 12px;border-radius:999px;font-size:0.78rem;">{goal_label}</span>
            <span style="margin-left:12px;color:#888;">当前方向暂无待办，可以休息一下 🎉</span>
        </div>
        """, unsafe_allow_html=True)


def render_deadline_head(events):
    now = datetime.now()
    future = [e for e in events if e["datetime"] >= now]
    if not future:
        st.info("🎉 近期没有待办事件！")
        return
    next_evt = min(future, key=lambda x: x["datetime"])
    delta = (next_evt["datetime"] - now).days
    theme = THEMES[st.session_state["theme_key"]]
    st.markdown(f"""
    <div class="card fade-in">
        <h3 style="color:{theme['primary']};">⏳ 距离最近高优先级截止：{next_evt['title']}</h3>
        <p style="font-size:1.2rem; font-weight:bold;">剩余 {delta} 天</p>
        <p>备注：{next_evt.get('note','')}</p>
    </div>
    """, unsafe_allow_html=True)

    # 学期进度（假设学期起点：2026-08-31，终点：2026-12-20）
    term_start = datetime(2026, 8, 31)
    term_end = datetime(2026, 12, 20)
    if now < term_start:
        pct = 0
    elif now > term_end:
        pct = 100
    else:
        pct = ((now - term_start).total_seconds() / (term_end - term_start).total_seconds()) * 100
    st.markdown(f"""
    <div class="card">
        <h4>📊 本学期进度：{pct:.1f}%</h4>
        <div style="width:100%; height:14px; background:#ddd; border-radius:999px; overflow:hidden;">
            <div style="width:{pct}%; height:100%; background:{theme['secondary']};"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# -------------------------- HTML 渲染辅助（重要：修复"时间轴/热力图显示成原始 HTML"） --------------------------
# 说明：st.markdown(unsafe_allow_html=True) 对"单个元素"的 HTML 可正常渲染，
# 但对包含大量并列元素的大块 HTML（时间轴每行卡片、热力日历几十个格子）会被转义成纯文本显示。
# 改用 st.components.v1.html() 可稳定渲染任意 HTML，杜绝乱码。
def render_html(html, height=600, scrolling=True):
    import streamlit.components.v1 as components
    components.html(html, height=height, scrolling=scrolling)


# -------------------------- 上下错位箭头时间轴 --------------------------
def render_timeline(events):
    theme = THEMES[st.session_state["theme_key"]]
    st.subheader("📌 全景时间轴")
    view = st.radio("视图切换", ["全部事件", "仅学业", "仅求职"], horizontal=True)
    if view == "全部事件":
        st.session_state["timeline_view"] = "all"
    elif view == "仅学业":
        st.session_state["timeline_view"] = "academic"
    else:
        st.session_state["timeline_view"] = "career"

    evts = filter_events(events, st.session_state["timeline_view"])
    if not evts:
        st.warning("当前筛选下没有事件")
        return

    html = f"""
    <style>
    .ht-wrap {{ overflow-x: auto; overflow-y: hidden; padding: 30px 6px 18px; position: relative; }}
    .ht-line {{ position: absolute; top: 26px; left: 6px; right: 6px; height: 4px; border-radius: 2px; background: {theme['accent']}; }}
    .ht {{ display: flex; align-items: flex-start; gap: 14px; min-width: max-content; padding: 0 8px; }}
    .ht-item {{ width: 220px; flex-shrink: 0; }}
    .ht-dot {{ width: 18px; height: 18px; border-radius: 50%; background: {theme['primary']}; border: 3px solid #fff; box-shadow: 0 0 0 2px {theme['accent']}; margin: 0 auto; position: relative; z-index: 2; }}
    .ht-dot.pulse {{ animation: pulseSoft 2.2s infinite ease-in-out; }}
    .ht-card {{ margin-top: 14px; background: {theme['light']}; border-radius: 14px; padding: 12px 14px; box-shadow: 0 3px 12px rgba(0,0,0,0.08); }}
    .ht-card.academic {{ border-top: 4px solid {theme['primary']}; }}
    .ht-card.career {{ border-top: 4px solid {theme['secondary']}; }}
    .ht-card.finished {{ opacity: 0.45; text-decoration: line-through; }}
    .ht-title {{ font-weight: 700; font-size: 0.95rem; color: #26303d; }}
    .ht-date {{ font-size: 0.78rem; color: #889; margin-top: 4px; }}
    .ht-note {{ font-size: 0.8rem; color: #687890; margin-top: 6px; }}
    </style>
    <div class="ht-wrap">
      <div class="ht-line"></div>
      <div class="ht">
    """
    now = datetime.now()
    for e in sorted(evts, key=lambda x: x["datetime"]):
        is_fin = e["date"] in st.session_state["finished_events"]
        is_star = e["date"] in st.session_state["starred_events"]
        is_soon = 0 < (e["datetime"] - now).days <= 7
        cls = "academic" if e["is_academic"] else "career"
        pulse_cls = "pulse" if is_soon else ""
        fin_cls = "finished" if is_fin else ""
        html += f"""
        <div class="ht-item">
          <div class="ht-dot {pulse_cls}"></div>
          <div class="ht-card {cls} {fin_cls}">
            <div class="ht-title">{e['title']} {"⭐" if is_star else ""}</div>
            <div class="ht-date">📅 {e['date']}</div>
            <div class="ht-note">{e.get('note','')}</div>
          </div>
        </div>
        """
    html += "</div></div>"
    render_html(html, height=320, scrolling=True)

    # 勾选 / 星标操作（课程表式板块：前面勾选、后面任务，横向排布）
    st.markdown("#### ✏️ 任务操作")
    st.caption("课程表式排布：每行左侧勾选「完成 / 星标」，右侧显示任务；已完成置灰排后，星标任务带 ⭐")
    theme_ops = THEMES[st.session_state["theme_key"]]
    sorted_evts = sorted(evts, key=lambda e: (e["date"] in st.session_state["finished_events"], e["date"]))
    for idx, e in enumerate(sorted_evts):
        done = e["date"] in st.session_state["finished_events"]
        star = e["date"] in st.session_state["starred_events"]
        c1, c2, c3 = st.columns([0.72, 0.72, 5.6], vertical_alignment="center")
        with c1:
            if st.checkbox("完成", value=done, key=f"fin2_{e['date']}_{idx}"):
                st.session_state["finished_events"] = set(st.session_state["finished_events"]) | {e["date"]}
            elif e["date"] in st.session_state["finished_events"]:
                st.session_state["finished_events"] = set(st.session_state["finished_events"]) - {e["date"]}
        with c2:
            if st.checkbox("星标", value=star, key=f"star2_{e['date']}_{idx}"):
                st.session_state["starred_events"] = set(st.session_state["starred_events"]) | {e["date"]}
            elif e["date"] in st.session_state["starred_events"]:
                st.session_state["starred_events"] = set(st.session_state["starred_events"]) - {e["date"]}
        with c3:
            type_cn = "学业" if e["is_academic"] else "求职"
            line = "#5cb85c" if done else (theme_ops["primary"] if e.get("priority") == "high" else theme_ops["secondary"])
            bg = "#f3faf3" if done else "#ffffff"
            title_txt = ("<s style='color:#999;'>" + e["title"] + "</s>") if done else e["title"]
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:10px;background:{bg};border:1px solid #e5e9f0;'
                f'border-left:4px solid {line};border-radius:10px;padding:7px 12px;margin-bottom:4px;">'
                f'<span style="background:{theme_ops["primary"]};color:#fff;border-radius:8px;padding:3px 8px;'
                f'font-size:0.75rem;font-weight:700;min-width:72px;text-align:center;">{e["date"][5:]}</span>'
                f'<b style="flex:1;font-size:0.95rem;">{title_txt} {"⭐" if star else ""}</b>'
                f'<span style="background:{theme_ops["light"]};color:{theme_ops["primary"]};padding:2px 8px;'
                f'border-radius:999px;font-size:0.72rem;">{type_cn}</span>'
                f'<span style="color:#888;font-size:0.8rem;max-width:38%;white-space:nowrap;overflow:hidden;'
                f'text-overflow:ellipsis;">{e.get("note", "")}</span>'
                f'</div>', unsafe_allow_html=True)

# -------------------------- 任务负载热力日历 --------------------------
def render_heatmap(events):
    st.subheader("🔥 任务负载热力日历")
    from collections import defaultdict
    by_date = defaultdict(list)
    for e in events:
        by_date[e["date"]].append(e["title"])
    theme = THEMES[st.session_state["theme_key"]]

    def esc(s):
        return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")

    html = (
        "<style>"
        ".hm{display:grid;grid-template-columns:repeat(7,1fr);gap:6px;font-family:'Segoe UI','Microsoft YaHei',sans-serif;}"
        ".hm-head{text-align:center;font-weight:700;color:#7a8699;padding:4px 0;}"
        ".hm-month{grid-column:1/-1;font-weight:800;color:" + theme["primary"] + ";padding:14px 0 6px;margin-top:6px;border-bottom:2px solid " + theme["light"] + ";font-size:1.05rem;}"
        ".hm-cell{background:#eef3f8;border-radius:10px;padding:6px 5px;min-height:58px;text-align:center;}"
        ".hm-cell.today{outline:2px solid " + theme["primary"] + ";}"
        ".hm-day{font-weight:800;font-size:0.92rem;}"
        ".hm-item{font-size:0.62rem;line-height:1.3;background:rgba(255,255,255,0.30);border-radius:5px;margin-top:3px;padding:2px 3px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}"
        ".hm-more{font-size:0.6rem;color:rgba(255,255,255,0.85);margin-top:2px;}"
        "</style>"
        '<div class="hm">'
    )
    for d in ["一", "二", "三", "四", "五", "六", "日"]:
        html += f"<div class='hm-head'>{d}</div>"
    start = datetime(2026, 8, 31)
    term_end = datetime(2026, 12, 20)
    today = datetime.now()
    cur_month = None
    for offset in range((term_end - start).days + 1):
        day = start + timedelta(days=offset)
        month_key = day.strftime("%Y-%m")
        if month_key != cur_month:
            cur_month = month_key
            html += f"<div class='hm-month'>{day.strftime('%Y年%m月')}</div>"
        k = day.strftime("%Y-%m-%d")
        items = by_date.get(k, [])
        is_today = day.date() == today.date()
        if items:
            bg = theme["primary"] if len(items) > 1 else theme["secondary"]
            tip = esc(k + "：" + "；".join(items))
            item_html = "".join(
                f"<div class='hm-item' title='{esc(t)}'>{esc(t)}</div>" for t in items[:2]
            )
            extra = len(items) - 2
            if extra > 0:
                item_html += f"<div class='hm-more'>+{extra} 项</div>"
            cell = (f"<div class='hm-cell today' style='background:{bg};color:#fff;' title='{tip}'>"
                    f"<div class='hm-day'>{day.day}</div>{item_html}</div>")
        else:
            cell = (f"<div class='hm-cell{' today' if is_today else ''}' title='{k}：无安排'>"
                    f"<div class='hm-day'>{day.day}</div></div>")
        html += cell
    html += "</div>"
    legend = (
        "<div style='display:flex;gap:14px;justify-content:center;align-items:center;margin-top:10px;font-size:0.8rem;color:#667;'>"
        "<span><span style='display:inline-block;width:12px;height:12px;border-radius:3px;background:#eef3f8;vertical-align:-1px;'></span> 无安排</span>"
        f"<span><span style='display:inline-block;width:12px;height:12px;border-radius:3px;background:{theme['secondary']};vertical-align:-1px;'></span> 1 项</span>"
        f"<span><span style='display:inline-block;width:12px;height:12px;border-radius:3px;background:{theme['primary']};vertical-align:-1px;'></span> 2 项及以上</span>"
        "</div>"
    )
    render_html(html + legend, height=950, scrolling=True)

# -------------------------- ICS 日历导出 --------------------------
def export_ics(events, fname="betime_calendar.ics", label="📥 下载 ICS 日历文件"):
    c = Calendar()
    for e in events:
        ev = Event()
        ev.name = e["title"]
        ev.begin = e["datetime"]
        ev.description = e.get("note", "")
        c.events.add(ev)
    raw = str(c)
    b64 = base64.b64encode(raw.encode("utf-8")).decode()
    href = f'<a href="data:text/calendar;base64,{b64}" download="{fname}">{label}</a>'
    st.markdown(href, unsafe_allow_html=True)

# -------------------------- 星标待办独立面板 --------------------------
def render_star_panel(events):
    st.subheader("⭐ 我的重点待办")
    star_list = [e for e in events if e["date"] in st.session_state["starred_events"]]
    if not star_list:
        st.info("还没有星标事件，在时间轴里勾选星标！")
        return
    for s in star_list:
        st.markdown(f"- **{s['title']}**｜{s['date']}｜{s.get('note','')}")

# -------------------------- AI 自动任务拆解 --------------------------
def ai_split_task(title, note, target_dt):
    now = datetime.now()
    total_days = (target_dt - now).days
    if total_days <= 0:
        return ["截止日期已到"]
    seg = max(3, min(6, total_days // 4))
    steps = [
        "确定大纲 / 数据集",
        "完成初稿 / 基础代码",
        "自查 + 修改内容",
        "排版、可视化、校对",
        "最终版本提交"
    ]
    plan = []
    for i, step in enumerate(steps):
        d = now + timedelta(days=int(total_days * (i / len(steps))))
        plan.append(f"{d.strftime('%Y-%m-%d')}：{step}")
    return plan

def render_ai_planner(events):
    st.subheader("🧠 AI 任务拆解")
    opts = [e["title"] for e in events if e["datetime"] >= datetime.now()]
    if not opts:
        st.info("当前没有可拆解的未到期任务，先去时间轴添加任务吧！")
        return
    pick = st.selectbox("选择一项任务生成计划", opts)
    target = next(e for e in events if e["title"] == pick)
    if st.button("生成阶段性规划"):
        plan = ai_split_task(target["title"], target.get("note",""), target["datetime"])
        for p in plan:
            st.markdown(f"- {p}")
# -------------------------- 求职赛道模块 --------------------------
# 行业偏好 → 校招企业 type 映射（用于个性化筛选）
INDUSTRY_FILTER = {
    "金融": ["银行", "四大", "券商"],
    "互联网": ["互联网", "科技"],
    "新能源": ["新能源车", "能源"],
    "综合集团": ["综合集团", "交通", "航空", "能源公用"],
}


def render_job_recruit():
    st.subheader("💼 招聘信息库")
    mode = st.radio("身份选择", ["student", "social"], horizontal=True,
                    format_func=lambda x: "在校学生（校招）" if x == "student" else "在职（社招）")
    st.session_state["identity_mode"] = mode

    if mode == "student":
        st.markdown("#### 🎓 校招岗位（2026 秋招 · 银行 / 四大 / 券商 / 大企业）")
        st.caption("每张卡片一家公司，从左到右排布；点「💬 唤起助手」让它帮你准备面经和简历")
        # 按个性化行业偏好筛选（引导页填过就记住；也可随时手动切换）
        filter_opts = ["全部"] + list(INDUSTRY_FILTER.keys())
        default_f = st.session_state.get("selected_industry", "金融")
        if default_f not in filter_opts:
            default_f = "全部"
        pref = st.selectbox("🏢 按行业筛选", filter_opts, index=filter_opts.index(default_f), key="job_industry_filter")
        if pref == "全部":
            filtered = STUDENT_RECRUIT
        else:
            allowed = set(INDUSTRY_FILTER[pref])
            filtered = [x for x in STUDENT_RECRUIT if x["type"] in allowed]
        if not filtered:
            st.info("该行业暂无校招岗位，换个行业看看吧！")
            return
        type_colors = {
            "银行": "#1f4e79", "四大": "#2d6a4f", "券商": "#6b489e",
            "互联网": "#3498db", "科技": "#2c3e50", "能源": "#7d6608",
            "新能源车": "#16a085", "航空": "#c0392b", "交通": "#2980b9",
            "综合集团": "#8e44ad", "能源公用": "#27ae60"
        }
        for i in range(0, len(filtered), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j >= len(filtered):
                    break
                item = filtered[i + j]
                tc = type_colors.get(item["type"], "#666")
                with cols[j]:
                    st.markdown(
                        f'<div class="card" style="height:100%;display:flex;flex-direction:column;padding:14px;">'
                        f'<div style="display:flex;justify-content:space-between;align-items:center;gap:6px;flex-wrap:wrap;">'
                        f'<b style="font-size:1.02rem;line-height:1.3;">{item["name"]}</b>'
                        f'<span style="background:{tc};color:#fff;padding:2px 10px;border-radius:999px;font-size:0.72rem;flex-shrink:0;">{item["type"]}</span></div>'
                        f'<div style="color:#777;font-size:0.82rem;margin-top:7px;">⏰ {item["window"]}</div>'
                        f'<div style="color:#555;font-size:0.88rem;margin-top:6px;flex:1;">{item["note"]}</div>'
                        f'<div style="color:#aaa;font-size:0.75rem;margin-top:6px;">来源：{item.get("src", "")}</div>'
                        f'</div>', unsafe_allow_html=True)
                    if st.button("💬 唤起助手", key=f"job_chat_{item['name']}", use_container_width=True):
                        st.session_state["assistant_prompt"] = (
                            f"帮我准备 {item['name']} 的求职，给我面经、简历修改方向和常见面试题。"
                        )
                        st.session_state["current_page"] = "assistant_chat"
                        st.session_state["theme_key"] = "assistant"
                        st.rerun()
    else:
        industry = st.selectbox("选择行业", list(SOCIAL_RECRUIT.keys()))
        st.session_state["selected_industry"] = industry
        st.markdown(f"#### 🏢 {industry} 社招岗位")
        for item in SOCIAL_RECRUIT[industry]:
            with st.expander(f"{item['name']}"):
                st.markdown(f"- **备注：** {item['note']}")
                if st.button(f"唤起助手：查询面经｜{item['name']}",
                             key=f"social_chat_{item['name']}"):
                    st.session_state["assistant_prompt"] = (
                        f"帮我准备 {item['name']} 的社招面试，给出面试重点、简历优化建议。"
                    )
                    st.session_state["current_page"] = "assistant_chat"
                    st.session_state["theme_key"] = "assistant"
                    st.rerun()


def render_job_timeline(all_events):
    st.subheader("📅 求职专属时间轴")
    career_evts = [e for e in all_events if e["is_career"]]
    if not career_evts:
        st.info("暂无求职类事件")
        return
    theme = THEMES["job"]
    html = f"""
    <style>
    .career-timeline {{ position: relative; padding: 20px 0; }}
    .career-line {{
        position: absolute;
        left: 4px;
        top: 0;
        bottom: 0;
        width: 3px;
        background: {theme["accent"]};
    }}
    .career-item {{
        position: relative;
        margin-left: 24px;
        margin-bottom: 20px;
    }}
    .career-dot {{
        position: absolute;
        left: -22px;
        top: 6px;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: {theme["primary"]};
    }}
    .career-card {{
        background: {theme["light"]};
        padding: 14px 18px;
        border-radius: 14px;
    }}
    </style>
    <div class="career-timeline">
        <div class="career-line"></div>
    """
    for e in career_evts:
        html += f"""
        <div class="career-item">
            <div class="career-dot"></div>
            <div class="career-card">
                <div style="font-weight:700;">{e["title"]}</div>
                <div style="opacity:0.8; font-size:0.9rem;">{e["date"]}</div>
                <div style="font-size:0.85rem; margin-top:4px;">{e.get("note", "")}</div>
            </div>
        </div>
        """
    html += "</div>"
    render_html(html, height=max(320, len(career_evts) * 130 + 60), scrolling=True)


def render_job_export(all_events):
    st.subheader("📤 导出求职日历")
    career_evts = [e for e in all_events if e["is_career"]]
    if not career_evts:
        st.warning("没有求职事件可以导出")
        return
    export_ics(career_evts)
# -------------------------- 香港本地行程模块 --------------------------
def render_local_recommend():
    st.subheader("🗺️ 碎片行程推荐")
    st.caption("自动检测你的空闲时段，按空闲时长推送点位：点「想去」并选好日期加入游玩计划，不想去可直接跳过")
    theme = THEMES[st.session_state["theme_key"]]
    free_slots = detect_free_slots(7)
    # ---- 空闲时段自动检测面板（表格形式） ----
    if free_slots:
        slot_cn = {"morning": "上午 08:30–12:00", "afternoon": "下午 12:00–17:30", "evening": "晚上 17:30–21:30"}
        rows_html = ""
        for i, s in enumerate(free_slots[:8]):
            bg = "#f6f9fc" if i % 2 == 0 else "#ffffff"
            rows_html += (
                f'<tr style="background:{bg};">'
                f'<td style="padding:7px 10px;border:1px solid #e5e9f0;text-align:center;">{s["date"]}</td>'
                f'<td style="padding:7px 10px;border:1px solid #e5e9f0;text-align:center;">{s["weekday_cn"]}</td>'
                f'<td style="padding:7px 10px;border:1px solid #e5e9f0;text-align:center;">{slot_cn.get(s["slot"], s["slot"])}</td>'
                f'<td style="padding:7px 10px;border:1px solid #e5e9f0;text-align:center;color:{theme["primary"]};font-weight:700;">约 {s["hours"]} 小时</td>'
                f'</tr>'
            )
        more_row = ("<tr><td colspan=4 style=\"padding:6px;border:1px solid #e5e9f0;color:#aaa;text-align:center;\">…还有更多（下方滑块可按时长筛选）</td></tr>"
                    if len(free_slots) > 8 else "")
        table_html = (
            f'<div class="card" style="border-left:5px solid {theme["secondary"]};">'
            f'<b>🧭 已自动检测你的空闲时段</b>'
            f'<span style="color:#888;font-size:0.82rem;">（未来 7 天 · 结合课程表推算）</span>'
            f'<table style="border-collapse:collapse;width:100%;margin-top:10px;font-size:0.9rem;">'
            f'<tr style="background:{theme["light"]};">'
            f'<th style="padding:8px 10px;border:1px solid #e5e9f0;color:{theme["primary"]};">日期</th>'
            f'<th style="padding:8px 10px;border:1px solid #e5e9f0;color:{theme["primary"]};">星期</th>'
            f'<th style="padding:8px 10px;border:1px solid #e5e9f0;color:{theme["primary"]};">空闲时段</th>'
            f'<th style="padding:8px 10px;border:1px solid #e5e9f0;color:{theme["primary"]};">可用时长</th>'
            f'</tr>{rows_html}{more_row}'
            f'</table></div>'
        )
        st.markdown(table_html, unsafe_allow_html=True)
    else:
        st.info("未来 7 天暂时没有检测到整段空闲时段，可以先手动选日期安排。")

    hours = st.slider("可用空闲时长（小时）", min_value=0.5, max_value=4.0,
                      value=st.session_state["free_hours"], step=0.5)
    st.session_state["free_hours"] = hours
    # 推荐列表在会话内固定：只有点「换一批」才重新随机，避免每次刷新都换一批
    # （否则刚点的「想去」按钮会因列表变化而丢失点击，导致加不进计划）
    if "place_sample" not in st.session_state or st.session_state.get("place_refresh", False):
        rng = random.Random(st.session_state["place_seed"])
        # 换一批时排除上一批展示过的点位，保证每次都有新内容
        last_titles = st.session_state.get("last_places", [])
        pool_others = [p for p in PLACE_POOL if p["title"] not in last_titles]
        if len(pool_others) >= 3:
            sample = rng.sample(pool_others, k=3)
        else:
            sample = rng.sample(PLACE_POOL, k=min(3, len(PLACE_POOL)))
        st.session_state["place_sample"] = sample
        st.session_state["last_places"] = [p["title"] for p in sample]
        st.session_state["place_refresh"] = False
    else:
        sample = st.session_state["place_sample"]
    # 默认计划日：第一个空闲时段（无空闲则回退到下周六）
    if free_slots:
        default_date = datetime.strptime(free_slots[0]["date"], "%Y-%m-%d").date()
        default_slot_label = free_slots[0]["label"]
    else:
        today = datetime.now().date()
        days_to_sat = (5 - today.weekday()) % 7 or 7
        default_date = today + timedelta(days=days_to_sat)
        default_slot_label = "周六（手动）"

    def match_slot(cost):
        """找一个时长足够且最早的空闲时段。"""
        for s in free_slots:
            if s["hours"] >= cost:
                return s
        return None

    for idx, p in enumerate(sample):
        cost = float(p.get("cost", 0.5))
        hit = match_slot(cost)
        sug = f"🗓️ 建议塞进：{hit['label']}" if hit else "🗓️ 建议：周末或手动选日期"
        st.markdown(f"""
        <div class="card" style="padding:14px;">
            <div style="display:flex;gap:14px;flex-wrap:wrap;">
                <img src="{p['img']}" style="width:190px;height:140px;object-fit:cover;border-radius:12px;flex-shrink:0;"/>
                <div style="flex:1;min-width:220px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px;">
                        <b style="font-size:1.1rem;">{p['title']}</b>
                        <span style="background:{theme['secondary']};color:#fff;padding:2px 10px;border-radius:999px;font-size:0.75rem;">约 {cost} 小时</span>
                    </div>
                    <div style="margin-top:6px;color:#555;">{p['desc']}</div>
                    <div style="margin-top:8px;color:#888;font-size:0.88rem;">🚇 {p['trans']}</div>
                    <div style="margin-top:6px;color:{theme['primary']};font-size:0.88rem;font-weight:600;">{sug}</div>
                    <div style="margin-top:4px;">🏷️ {' / '.join(p['tags'])}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        col_a, col_b, col_c = st.columns([2.2, 1.3, 1.3])
        with col_a:
            plan_date = st.date_input("计划日期", value=default_date, key=f"plan_date_{p['title']}")
        with col_b:
            if st.button("✅ 想去，加入计划", key=f"plan_add_{p['title']}", use_container_width=True):
                item = {"title": p["title"], "desc": p["desc"], "trans": p["trans"],
                        "img": p["img"], "tags": p["tags"], "date": str(plan_date), "done": False}
                if not any(x["title"] == p["title"] and x["date"] == str(plan_date) for x in st.session_state["trip_plan"]):
                    st.session_state["trip_plan"].append(item)
                    st.success(f"已加入游玩计划：{p['title']}（{plan_date}）")
                else:
                    st.info("该点位该日期已在计划中")
        with col_c:
            if st.button("⭐ 收藏点位", key=f"fav_place_{p['title']}", use_container_width=True):
                if p not in st.session_state["fav_places"]:
                    st.session_state["fav_places"].append(p)
                st.success("已收藏！")
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("🎲 换一批推荐", key="refresh_places", use_container_width=True):
            st.session_state["place_seed"] = random.randint(0, 9999)
            st.session_state["place_refresh"] = True
            save_state()  # 立即持久化，防止 rerun 后从旧 JSON 恢复
            st.rerun()
    with c2:
        if st.button("🗓️ 查看我的游玩计划", use_container_width=True):
            st.session_state["current_page"] = "local_plan"
            st.rerun()


def render_local_plan():
    st.subheader("🗓️ 我的游玩计划")
    st.caption("从推荐里确认加入的点位都在这里；完成一项就勾一下，可随时移除")
    plan = st.session_state["trip_plan"]
    if not plan:
        st.info("计划还是空的，去「碎片行程推荐」里把想去的点位加入计划吧！")
        return
    done_count = sum(1 for x in plan if x["done"])
    st.markdown(f"#### 📊 计划进度：{done_count} / {len(plan)} 已打卡")
    ordered = sorted(plan, key=lambda x: (x["done"], x["date"]))
    for idx, item in enumerate(ordered):
        theme = THEMES[st.session_state["theme_key"]]
        done_cls = "finished" if item["done"] else ""
        st.markdown(f"""
        <div class="card {done_cls}" style="padding:12px 14px;margin-bottom:10px;">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                <div>
                    <b style="font-size:1.02rem;">{"✅ " if item['done'] else "📌 "}{item['title']}</b>
                    <div style="color:#888;font-size:0.85rem;margin-top:3px;">🗓️ {item['date']} ｜ 🚇 {item['trans']}</div>
                    <div style="color:#667;font-size:0.88rem;margin-top:3px;">{item['desc']}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        c1, c2 = st.columns([0.4, 1.2])
        with c1:
            checked = st.checkbox("完成", value=item["done"], key=f"plan_done_{idx}")
        if checked != item["done"]:
            item["done"] = checked
        with c2:
            if st.button("🚫 移除该项", key=f"plan_rm_{idx}"):
                st.session_state["trip_plan"] = [x for x in st.session_state["trip_plan"] if x is not item]
                st.rerun()


def render_local_fav():
    st.subheader("❤️ 我的收藏点位")
    if not st.session_state["fav_places"]:
        st.info("还没有收藏任何地点，去行程推荐页看看吧！")
        return
    for p in st.session_state["fav_places"]:
        st.markdown(f"- **{p['title']}**｜{p['trans']}")
        st.markdown(f"  {p['desc']}")


# -------------------------- 经验资源库 --------------------------
def render_resource_list():
    # 判断是否打开帖子详情
    if st.session_state["selected_post"] is not None:
        post = st.session_state["selected_post"]
        st.button("← 返回经验贴广场", on_click=lambda: st.session_state.update({"selected_post": None}))
        st.divider()
        st.image(post["img"], width=560)
        st.markdown(post["content"])
        st.divider()
        st.markdown(f"🏷️ 标签：{post['tag']}")
        st.markdown("### 💬 评论区")
        for com in post["comments"]:
            st.markdown(f"> *{com['user']}：* {com['text']} （👍 {com['like']}）")
        if st.button("收藏这篇", key=f"save_art_{post['title']}"):
            if post not in st.session_state["saved_articles"]:
                st.session_state["saved_articles"].append(post)
            st.success("收藏成功")
        return

    # -------- 列表广场模式（一行 3 张卡片） --------
    st.subheader("📖 经验贴广场")
    all_tags = list({art["tag"] for art in EXPERIENCE_LIST})
    selected_tag = st.selectbox("按标签筛选", ["全部"] + all_tags)
    arts = [art for art in EXPERIENCE_LIST
            if selected_tag == "全部" or art["tag"] == selected_tag]
    # 个性化：按用户方向把相关标签的经验贴排前面
    goal = st.session_state.get("goal_mode", "career")
    pref_tags = {"academic": ["学习", "论文", "选课"], "career": ["秋招"]}.get(goal, [])
    if pref_tags:
        arts = sorted(arts, key=lambda a: (0 if a["tag"] in pref_tags else 1, a["title"]))
    if not arts:
        st.info("该标签下暂无经验贴")
        return
    for r in range((len(arts) + 2) // 3):
        cols = st.columns(3)
        for c in range(3):
            i = r * 3 + c
            if i >= len(arts):
                break
            art = arts[i]
            with cols[c]:
                st.markdown(
                    f"<div style='border:1px solid #e5e9f0;border-radius:14px;padding:12px 12px 6px;'>"
                    f"<b style='font-size:1rem;'>📝 {art['title']}</b><br/>"
                    f"<span style='color:#888;font-size:0.82rem;'>标签：{art['tag']}</span></div>",
                    unsafe_allow_html=True)
                st.image(art["img"], width=300)
                if st.button("阅读全文", key=f"open_post_{art['title']}", use_container_width=True):
                    st.session_state["selected_post"] = art
                    st.rerun()



# -------------------------- 收藏经验贴（原代码缺失，导致进入即报 NameError） --------------------------
def render_resource_saved():
    st.subheader("💾 收藏经验贴")
    saved = st.session_state.get("saved_articles", [])
    if not saved:
        st.info("还没有收藏任何经验贴，去「经验贴广场」点『收藏这篇』吧！")
        return
    for art in saved:
        st.markdown(f"**📝 {art['title']}** ｜标签：`{art['tag']}`")
        st.image(art["img"], width=380)
        with st.expander("查看全文"):
            st.markdown(art["content"])
        st.markdown(f"🏷️ 标签：{art['tag']}")
        for com in art.get("comments", []):
            st.markdown(f"> *{com['user']}：* {com['text']} （👍 {com['like']}）")
        st.divider()


# -------------------------- 讨论区（供使用者交流，本地持久化） --------------------------
def render_discussion():
    st.subheader("💬 讨论区")
    st.caption("给一起使用 Be-Time 的港硕同学交流：问问题、分享信息、找队友都可以；发言会保存在本地")
    theme = THEMES[st.session_state["theme_key"]]
    posts = st.session_state.setdefault("discussions", [])

    with st.form("discussion_form", clear_on_submit=True):
        name = st.text_input("昵称", placeholder="例如：港硕新人", max_chars=20)
        topic = st.text_input("话题（可选）", placeholder="例如：求助 / 经验分享 / 组队", max_chars=30)
        msg = st.text_area("说点什么", placeholder="分享你的港硕经验、问问作业问题、找秋招搭子…", max_chars=500, height=100)
        submitted = st.form_submit_button("📮 发布", use_container_width=True)
    if submitted:
        if not (name.strip() and msg.strip()):
            st.warning("昵称和内容都要填哦～")
        else:
            posts.append({
                "name": name.strip(),
                "topic": topic.strip(),
                "text": msg.strip(),
                "at": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            st.session_state["discussions"] = posts
            st.success("已发布！")
            st.rerun()

    if not posts:
        st.info("还没有讨论，来发第一条吧～")
        return

    st.markdown("---")
    st.markdown(f"**共 {len(posts)} 条讨论**（新发布在前）")
    for i, post in enumerate(reversed(posts)):
        badge = f"<span style='background:{theme['light']};color:{theme['primary']};padding:2px 10px;border-radius:999px;font-size:0.72rem;margin-left:6px;'>{post.get('topic','闲聊')}</span>"
        st.markdown(
            f'<div style="background:#fafbfc;border:1px solid #e5e9f0;border-left:4px solid {theme["primary"]};'
            f'border-radius:10px;padding:10px 14px;margin-bottom:8px;">'
            f'<div style="display:flex;align-items:center;gap:8px;">'
            f'<b style="color:{theme["primary"]};">{post["name"]}</b>{badge}'
            f'<span style="color:#aaa;font-size:0.75rem;margin-left:auto;">{post["at"]}</span></div>'
            f'<div style="margin-top:6px;color:#444;">{post["text"]}</div>'
            f'</div>', unsafe_allow_html=True)



# -------------------------- 课程一览（真实课表展示） --------------------------
def render_course():
    st.subheader("📖 课程一览")
    st.caption("2026-27 第一学期 · 香港教育大学 EdUHK（课表来自你的课程表截图，待确认的课程名可直接替换）")
    # 一键导出全部学业截止到手机日历
    academic_evts = [e for e in get_all_events() if e["is_academic"]]
    export_ics(academic_evts, fname="betime_academic.ics",
               label="📤 导出学业日历（全部作业截止 → 手机日历 ICS）")
    now = datetime.now()
    theme = THEMES["study"]
    for c in COURSES:
        task_lines = []
        for t in c.get("tasks", []):
            try:
                d = datetime.strptime(t["due"], "%Y-%m-%d")
                left = (d - now).days
                suffix = f"剩 {left} 天" if left >= 0 else "已到期"
                color = "#e5484d" if left < 0 else ("#f08c00" if left <= 7 else "#2f9e44")
            except Exception:
                suffix = ""
                color = "#2f9e44"
            task_lines.append(
                f"<div style='display:flex;justify-content:space-between;padding:3px 0;'>"
                f"<span>· {t['title']} <span style='color:#999;font-size:0.78rem;'>（{t['kind']}）</span></span>"
                f"<span style='color:{color};font-weight:700;'>{t['due']} {suffix}</span></div>"
            )
        task_html = "".join(task_lines) if task_lines else (
            "<div style='color:#999;padding:4px 0;'>暂无已登记的作业安排</div>"
        )
        st.markdown(f"""
        <div class="card course-card">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px;">
                <div>
                    <span style="background:{theme['primary']};color:#fff;padding:3px 12px;border-radius:999px;font-size:0.82rem;font-weight:700;">{c['code']}</span>
                    <b style="font-size:1.15rem;margin-left:10px;">{c['name']}</b>
                </div>
                <span style="color:#999;font-size:0.85rem;">{c['semester']}</span>
            </div>
            <div style="color:#667;font-size:0.9rem;margin:8px 0 2px;">{c['name_en']}</div>
            <div style="margin-top:8px;display:flex;gap:18px;flex-wrap:wrap;color:#444;">
                <span>🗓️ {c['weekday']} {c['time']}</span>
                <span>📍 {c['room']}</span>
            </div>
            <div style="margin-top:12px;">
                <div style="font-weight:700;color:{theme['primary']};margin-bottom:4px;">📌 作业与任务</div>
                {task_html}
            </div>
            <div style="margin-top:8px;color:#999;font-size:0.85rem;">💡 {c.get('note', '')}</div>
        </div>
        """, unsafe_allow_html=True)


# -------------------------- 个人任务看板（个人作业完成情况） --------------------------
def render_personal_board():
    st.subheader("👤 个人任务看板")
    st.caption("勾选完成情况，进度实时更新；任务来自课程作业与学业事件，可在数据区自行增删")
    tasks = st.session_state.get("personal_tasks", [])
    if not tasks:
        st.info("暂无任务，先去「课程一览」添加作业吧！")
        return
    done = [t for t in tasks if t["done"]]
    pct = int(len(done) / len(tasks) * 100)
    theme = THEMES[st.session_state["theme_key"]]
    st.markdown(f"""
    <div class="card">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px;">
            <b style="font-size:1.15rem;">📊 整体完成进度</b>
            <span style="font-size:1.35rem;font-weight:800;color:{theme['primary']};">{len(done)} / {len(tasks)}（{pct}%）</span>
        </div>
        <div style="width:100%;height:16px;background:#e6edf3;border-radius:999px;overflow:hidden;margin-top:10px;">
            <div style="width:{pct}%;height:100%;background:linear-gradient(90deg,{theme['secondary']},{theme['primary']});transition:width .3s ease;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### ✅ 任务清单")
    ordered = sorted(tasks, key=lambda x: (x["done"], x["due"]))
    for t in ordered:
        c1, c2, c3, c4 = st.columns([0.4, 4.2, 1.6, 1.6])
        with c1:
            checked = st.checkbox("", value=t["done"], key=f"pt_{t['id']}")
        if checked != t["done"]:
            t["done"] = checked
        with c2:
            mark = "✅" if t["done"] else "⬜"
            st.markdown(f"{mark} **{t['title']}**")
        with c3:
            st.markdown(f"<span style='color:#888;font-size:0.85rem;'>{t['course']}</span>", unsafe_allow_html=True)
        with c4:
            st.markdown(f"<span style='color:#888;font-size:0.85rem;'>{t['due']} · {t['kind']}</span>", unsafe_allow_html=True)


# -------------------------- 本周课表（周历视图） --------------------------
WEEK_MAP = {"周一": 0, "周二": 1, "周三": 2, "周四": 3, "周五": 4, "周六": 5, "周日": 6}
WEEK_CN = ["一", "二", "三", "四", "五", "六", "日"]
SLOT_META = [
    ("上午", "08:30 – 12:00", "morning", 3.5),
    ("下午", "12:00 – 17:30", "afternoon", 5.5),
    ("晚上", "17:30 – 21:30", "evening", 4.0),
]


def slot_of(time_str):
    h = int(time_str.split(":")[0].strip())
    if h < 12:
        return "morning"
    if h < 17:
        return "afternoon"
    return "evening"


# -------------------------- 空闲时段自动检测（结合课表） --------------------------
def detect_free_slots(days_ahead=7):
    """按课程表自动推算未来 N 天内没有课的空闲时段（上午/下午/晚上）。"""
    now = datetime.now()
    free = []
    for d in range(days_ahead):
        day = now.date() + timedelta(days=d)
        weekday_cn = "周" + WEEK_CN[day.weekday()]
        for label, rng, slot, hours in SLOT_META:
            busy = any(WEEK_MAP.get(c["weekday"]) == day.weekday() and slot_of(c["time"]) == slot
                       for c in COURSES)
            if busy:
                continue
            if d == 0:  # 今天只保留还没过去的时段
                if slot == "morning" and now.hour >= 12:
                    continue
                if slot == "afternoon" and now.hour >= 17:
                    continue
                if slot == "evening" and now.hour >= 21:
                    continue
            free.append({"date": day.isoformat(), "weekday_cn": weekday_cn, "slot": slot,
                         "hours": hours,
                         "label": f"{weekday_cn} {day.month:02d}-{day.day:02d} {label}"})
    return free


def render_week_schedule():
    st.subheader("🗓️ 本周课表")
    st.caption("一周课程一目了然，今天的列会高亮；没课的时段可以安排自习 / 出游 / 网申")
    theme = THEMES[st.session_state["theme_key"]]
    today = datetime.now().weekday()

    rows = [("上午 08:30 – 12:00", "morning"), ("下午 12:00 – 17:30", "afternoon"), ("晚上 17:30 – 21:30", "evening")]
    cells = {}
    for c in COURSES:
        cells[(WEEK_MAP.get(c["weekday"], -1), slot_of(c["time"]))] = c

    html = '<table style="border-collapse:collapse;width:100%;text-align:center;font-size:0.92rem;">'
    html += '<tr><th style="padding:10px;background:#f2f5f9;">时段</th>' + "".join(
        f'<th style="padding:10px;background:{"transparent" if i!=today else theme["primary"]};color:{"#333" if i!=today else "#fff"};border-radius:10px 10px 0 0;">周{WEEK_CN[i]}{"（今天）" if i==today else ""}</th>'
        for i in range(7)) + '</tr>'
    for rlabel, rkey in rows:
        html += f'<tr><td style="padding:12px;font-weight:600;background:#fafbfc;border:1px solid #e5e9f0;">{rlabel}</td>'
        for i in range(7):
            c = cells.get((i, rkey))
            if c:
                td = (f'<div style="background:{theme["light"]};border-left:4px solid {theme["primary"]};'
                      f'border-radius:10px;padding:8px 6px;margin:3px;">'
                      f'<b>{c["code"]}</b><br/><span style="font-size:0.85rem;">{c["time"]}</span><br/>'
                      f'<span style="font-size:0.8rem;color:#777;">{c["room"]}</span></div>')
            else:
                td = '<span style="color:#d5dbe3;">·</span>'
            bg = 'background:' + ("#fff7fa" if i == today else "#fff")
            html += f'<td style="border:1px solid #e5e9f0;padding:6px;{bg}">{td}</td>'
        html += '</tr>'
    html += '</table>'
    render_html(html, height=280, scrolling=False)

    today_courses = [c for c in COURSES if WEEK_MAP.get(c["weekday"]) == today]
    if today_courses:
        st.markdown("**今天有课：** " + "；".join(f"{c['code']} {c['time']} {c['room']}" for c in today_courses))
    else:
        st.markdown("**今天没课**，可以安排自习 / 出游 / 网申。")
    st.markdown("💡 教室：INT6141 / INT6136 教室待确认，拿到课表后告诉我即可补上。")


# -------------------------- 网申进度跟踪（细化版） --------------------------
APP_STAGES = ["已投递", "笔试", "面试", "Offer", "已拒"]
APP_COLUMNS = ["company", "role", "location", "stage", "applied_date", "exam_date", "interview_date", "note"]


def render_job_apps():
    st.subheader("📋 网申进度跟踪")
    st.caption("细化版：记录地点、投递 / 笔试 / 面试日期与阶段；表格可直接编辑、增删行，数据本地保存")
    apps = st.session_state.setdefault("applications", [])
    if apps:
        from collections import Counter
        cnt = Counter(a.get("stage", "已投递") for a in apps if a.get("company"))
        summary = " ｜ ".join(f"{s}：{cnt.get(s, 0)}" for s in APP_STAGES)
        st.markdown(f"**进度一览：** {summary}")
    df = pd.DataFrame(apps) if apps else pd.DataFrame(columns=APP_COLUMNS)
    edited = st.data_editor(
        df,
        column_config={
            "company": st.column_config.TextColumn("公司", width="medium", required=True, help="必填项"),
            "role": st.column_config.TextColumn("岗位 / 方向", width="medium"),
            "location": st.column_config.SelectboxColumn("地点", options=["香港", "内地", "大湾区", "远程"], width="small"),
            "stage": st.column_config.SelectboxColumn("阶段", options=APP_STAGES, width="small"),
            "applied_date": st.column_config.TextColumn("投递日期", width="small"),
            "exam_date": st.column_config.TextColumn("笔试日期", width="small"),
            "interview_date": st.column_config.TextColumn("面试日期", width="small"),
            "note": st.column_config.TextColumn("链接 / 备注", width="large"),
        },
        num_rows="dynamic",
        hide_index=True,
        use_container_width=True,
        key="job_apps_editor2",
    )
    records = []
    for r in edited.to_dict("records"):
        if not (r.get("company") or "").strip():
            continue  # 空行不入库
        records.append({k: r.get(k, "") for k in APP_COLUMNS})
    st.session_state["applications"] = records
    st.caption("提示：新增行时先填「公司」，阶段默认「已投递」；配合招聘信息库的截止时间安排投递节奏")


# -------------------------- 助手对话页面 --------------------------
def render_assistant_chat():
    st.subheader("🤖 智能助手")
    if "assistant_prompt" not in st.session_state:
        st.session_state["assistant_prompt"] = ""
    now = datetime.now()
    evts = get_all_events()
    upcoming = [e for e in evts if e["datetime"] >= now and e["date"] not in st.session_state["finished_events"]]
    upcoming = sorted(upcoming, key=lambda x: x["datetime"])[:4]
    undone = sum(1 for t in st.session_state.get("personal_tasks", []) if not t["done"])
    plan_n = len(st.session_state.get("trip_plan", []))
    apps = st.session_state.get("applications", [])
    with st.expander("📌 我的数据快照（助手可见的上下文）"):
        st.markdown("**最近截止：** " + ("；".join(f"{e['title']}（{e['date']}）" for e in upcoming) if upcoming else "暂无"))
        st.markdown(f"**个人看板未完成：** {undone} 项")
        st.markdown(f"**游玩计划：** {plan_n} 项")
        st.markdown(f"**网申记录：** {len(apps)} 条")
    if st.button("🧠 基于我的数据生成建议"):
        ctx = (f"我本学期选了 {len(COURSES)} 门课，个人看板还有 {undone} 项作业未完成；"
               f"最近截止：{'；'.join(e['title'] + '(' + e['date'] + ')' for e in upcoming) if upcoming else '暂无'}。"
               f"游玩计划 {plan_n} 项，网申 {len(apps)} 条。"
               f"请基于这些数据，给我本周的时间优先级安排和求职投递节奏建议。")
        st.session_state["assistant_prompt"] = ctx
        st.rerun()
    user_input = st.text_area("输入你的问题", value=st.session_state["assistant_prompt"], height=140)
    if st.button("发送提问"):
        st.markdown("### 助手回复")
        st.markdown("> 这里可以对接大模型，当前为演示占位。你可以用来生成报告大纲、面试题、论文规划。")
    st.session_state["assistant_prompt"] = ""


# -------------------------- 右上角：资料、通知、明暗切换 --------------------------
def render_header_widgets(evts):
    with st.sidebar:
        st.subheader("👤 个人档案")
        st.session_state["user_profile"]["name"] = st.text_input("昵称", st.session_state["user_profile"]["name"])
        st.session_state["user_profile"]["entry_year"] = st.text_input("入学年份", st.session_state["user_profile"]["entry_year"])
        st.session_state["user_profile"]["target_career"] = st.text_input("求职目标", st.session_state["user_profile"]["target_career"])

        st.subheader("🔔 通知")
        now = datetime.now()
        pending = [e for e in evts if e["datetime"] >= now and e["date"] not in st.session_state["finished_events"]]
        pending = sorted(pending, key=lambda x: x["datetime"])
        top3 = pending[:3]
        if not top3:
            st.info("暂无新通知")
        else:
            for e in top3:
                days = (e["datetime"] - now).days
                if days <= 3:
                    color = "#e74c3c"
                elif days <= 7:
                    color = "#e67e22"
                else:
                    color = "#3498db"
                st.markdown(f"<span style='color:{color};font-weight:600;'>⏰ {e['date']} · {e['title']}（剩 {days} 天）</span>",
                            unsafe_allow_html=True)
            st.caption(f"另有 {len(pending) - len(top3)} 项未到期（已完成的自动消失）")

        st.subheader("🎨 显示设置")
        st.session_state["dark_mode"] = st.toggle("暗色模式", st.session_state["dark_mode"])


# -------------------------- 路由分发：根据 current_page 渲染页面 --------------------------
def route_page(all_events):
    p = st.session_state["current_page"]
    if p == "study_all":
        render_personal_banner(all_events)
        render_deadline_head(all_events)
        render_timeline(all_events)
        render_heatmap(all_events)
        render_star_panel(all_events)
    elif p == "study_week":
        render_academic_alerts(all_events)
        render_week_schedule()
    elif p == "study_course":
        render_academic_alerts(all_events)
        render_course()
    elif p == "study_team":
        render_academic_alerts(all_events)
        render_personal_board()
    elif p == "job_timeline":
        render_job_timeline(all_events)
    elif p == "job_recruit":
        render_job_recruit()
    elif p == "job_apps":
        render_job_apps()
    elif p == "job_export":
        render_job_export(all_events)
    elif p == "local_recommend":
        render_local_recommend()
    elif p == "local_plan":
        render_local_plan()
    elif p == "local_fav":
        render_local_fav()
    elif p == "resource_list":
        render_resource_list()
    elif p == "resource_saved":
        render_resource_saved()
    elif p == "resource_discuss":
        render_discussion()
    elif p == "assistant_chat":
        render_assistant_chat()
    elif p == "assistant_plan":
        render_ai_planner(all_events)
    else:
        st.warning("页面不存在")


# -------------------------- 赛道 DDL 预警弹窗（可交互，后台记录） --------------------------
ALERT_ZONES = {
    "学业": ["study_all", "study_week", "study_course", "study_team"],
    "求职": ["job_timeline", "job_recruit", "job_apps", "job_export"],
}


def _zone_of_page(page):
    for zone, pages in ALERT_ZONES.items():
        if page in pages:
            return zone
    return None


def _log_alert(target, action):
    """把弹窗确认结果写入本地记录（持久化到 be_time_state.json）。"""
    st.session_state.setdefault("alert_log", []).append({
        "title": target["title"],
        "date": target["date"],
        "action": action,
        "at": datetime.now().strftime("%Y-%m-%d %H:%M")
    })


@st.dialog("⏰ DDL 预警")
def ddl_alert_dialog(zone, pending, now):
    """弹窗：仅展示最近 3 个最紧急的截止，按紧急程度分板块（演示任务展示不同板块样式）。"""
    st.markdown(f"**{zone}赛道** · 最近 3 项最紧急的截止提醒（标【演示】的是示例任务，用于展示分级效果）")
    levels = [
        ("🔴 紧急 · 3 天内截止", "#e74c3c", lambda d: d <= 3),
        ("🟠 临近 · 7 天内截止", "#e67e22", lambda d: 3 < d <= 7),
        ("🔵 待办 · 7 天以上", "#3498db", lambda d: d > 7),
    ]
    shown = 0
    for label, color, pred in levels:
        items = [e for e in pending if pred((e["datetime"] - now).days)]
        if not items:
            continue
        shown += 1
        st.markdown(
            f"<div style='background:{color};color:#fff;padding:6px 12px;border-radius:10px;"
            f"font-weight:700;font-size:0.92rem;margin:8px 0 4px;'>{label}</div>",
            unsafe_allow_html=True)
        for e in items:
            days = (e["datetime"] - now).days
            c1, c2 = st.columns([3.2, 1], vertical_alignment="center")
            with c1:
                st.markdown(f"**{e['title']}**")
                note_txt = f" · {e['note']}" if e.get("note") else ""
                st.caption(f"{e['date']}（剩 {days} 天）{note_txt}")
            with c2:
                if st.button("✅ 完成", key=f"dlg_{zone}_{e['date']}_{e['title']}", use_container_width=True):
                    # 整体赋值（避免 set 原地 add 不被跟踪），标记完成并写入后台记录
                    st.session_state["finished_events"] = set(st.session_state["finished_events"]) | {e["date"]}
                    _log_alert(e, "已完成")
                    st.session_state["ddl_alert_handled"] = None  # 强制下一轮重新评估，自动推进到下一条
                    st.rerun()
    if shown == 0:
        st.success(f"🎉 {zone}赛道暂无待办截止，可以放心安排其他事情。")
    st.divider()
    if st.button("知道了（稍后再提醒）", use_container_width=True):
        st.session_state["ddl_alert_handled"] = f"{zone}:dismissed"
        st.rerun()
    st.caption("「✅ 完成」会写入本地记录并自动推进到下一条待办；「知道了」本次会话不再重复提醒")


def maybe_show_ddd_alert(evts):
    """只在「全景时间轴 / 求职时间轴」弹出对应赛道预警，展示最近 3 项 + 分级演示任务。"""
    now = datetime.now()
    page = st.session_state.get("current_page", "")
    # 只在两个时间轴页面弹出
    if page not in ("study_all", "job_timeline"):
        return
    zone = "学业" if page == "study_all" else "求职"
    is_acad = zone == "学业"
    pending = [e for e in evts
               if (e["is_academic"] if is_acad else e["is_career"])
               and e["datetime"] >= now
               and e["date"] not in st.session_state["finished_events"]]
    # 追加两个分级演示任务（动态日期），用于展示不同紧急程度的板块
    demo = [
        parse_event({"date": (now.date() + timedelta(days=3)).isoformat(),
                     "title": "【演示】模拟面试准备",
                     "type": "academic" if is_acad else "career",
                     "priority": "high",
                     "note": "演示数据 · 展示 3 天紧急提醒板块"}),
        parse_event({"date": (now.date() + timedelta(days=7)).isoformat(),
                     "title": "【演示】网申材料提交",
                     "type": "academic" if is_acad else "career",
                     "priority": "high",
                     "note": "演示数据 · 展示 7 天临近提醒板块"})
    ]
    pool = pending + demo
    pool = sorted(pool, key=lambda x: x["datetime"])[:3]
    if not pool:
        return
    first = pool[0]
    current_key = f"{zone}:{first['date']}|{first['title']}"
    if st.session_state.get("ddl_alert_handled") not in (current_key, f"{zone}:dismissed"):
        ddl_alert_dialog(zone, pool, now)


# -------------------------- 主入口 --------------------------
# -------------------------- 右下角智能人悬浮助手（可爱形象 + hover 问答） --------------------------
def render_buddy():
    """右下角固定悬浮的可爱智能人：鼠标滑过弹出面板，可回答简单问题（关键词规则问答）。"""
    import streamlit.components.v1 as components
    buddy_html = """
    <style>
      .bb-wrap { position: fixed; right: 18px; bottom: 18px; z-index: 99999; font-family: 'Segoe UI','Microsoft YaHei',sans-serif; }
      .bb-btn { width: 62px; height: 62px; border-radius: 50%;
                background: linear-gradient(135deg,#6b489e 0%,#239984 100%);
                cursor: pointer; box-shadow: 0 6px 22px rgba(0,0,0,.28);
                display: flex; align-items: center; justify-content: center; font-size: 32px;
                transition: transform .2s ease; border: 3px solid #fff; }
      .bb-btn:hover { transform: scale(1.1) rotate(-6deg); }
      .bb-panel { position: absolute; right: 0; bottom: 74px; width: 280px;
                  background: #fff; border-radius: 16px; box-shadow: 0 12px 40px rgba(0,0,0,.22);
                  padding: 14px; display: none; border: 1px solid #eee; }
      .bb-wrap:hover .bb-panel, .bb-wrap.open .bb-panel { display: block; }
      .bb-msgs { height: 128px; overflow-y: auto; font-size: .84rem; background: #f7f9fb;
                 border-radius: 10px; padding: 8px; }
      .bb-msgs::-webkit-scrollbar { width: 4px; }
      .bb-msgs::-webkit-scrollbar-thumb { background: #ccc; border-radius: 4px; }
      .bb-input { width: 100%; margin-top: 8px; padding: 6px 10px; border: 1px solid #e5e9f0;
                  border-radius: 10px; font-size: .84rem; outline: none; box-sizing: border-box; }
      .bb-input:focus { border-color: #6b489e; }
    </style>
    <div class="bb-wrap" id="bbWrap">
      <div class="bb-panel">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
          <span style="font-size:26px;">👾</span>
          <b>小贝助手</b>
          <span style="color:#aaa;font-size:.68rem;margin-left:auto;">滑过我 · 简单问答</span>
        </div>
        <div class="bb-msgs" id="bbMsgs">
          <div style="margin:6px 0;padding:6px 10px;background:#6b489e;color:#fff;border-radius:10px 10px 2px 10px;">
            你好呀！我是小贝～ 可以问我：作业截止 / 课表 / 秋招 / 香港推荐
          </div>
        </div>
        <input class="bb-input" id="bbInput" placeholder="输入问题，回车提问…" maxlength="60">
      </div>
      <div class="bb-btn" id="bbBtn">👾</div>
    </div>
    <script>
    (function(){
      function answer(q){
        q = q.toLowerCase();
        if (/你好|hi|hello|嗨|在吗/.test(q)) return "你好呀！我是小贝，随时帮你～";
        if (/作业|截止|ddl|deadline|考试/.test(q)) return "学业 DDL 都在📅全景时间轴，最近 3 项最紧急的会自动弹窗提醒～";
        if (/课表|上课|课程/.test(q)) return "本周课表在📚学业工作台 → 本周课表，一目了然～";
        if (/秋招|求职|面试|招聘|网申/.test(q)) return "求职节点看💼求职时间轴，具体岗位在「招聘信息库」横向卡片里～";
        if (/香港|玩|推荐|景点|行程/.test(q)) return "空闲时段推荐在🗺️碎片行程推荐，会自动检测你的空闲时间并排行程～";
        if (/成绩|gpa|绩点/.test(q)) return "目前没有成绩页啦，专注把作业按时交完最重要！";
        if (/讨论|交流/.test(q)) return "经验资源库里有💬讨论区，可以和大家交流～";
        if (/谢谢|感谢|bye|再见|拜拜/.test(q)) return "不客气～加油鸭！🦆";
        return "我还在学习中～可以试试问我：作业截止、课表、秋招、香港推荐";
      }
      function say(txt){
        var box = document.getElementById("bbMsgs");
        var d = document.createElement("div");
        d.style.cssText = "margin:6px 0;padding:6px 10px;background:#6b489e;color:#fff;border-radius:10px 10px 2px 10px;word-break:break-all;";
        d.textContent = txt;
        box.appendChild(d);
        box.scrollTop = box.scrollHeight;
      }
      var inp = document.getElementById("bbInput");
      inp.addEventListener("keydown", function(e){
        if (e.key === "Enter") {
          var v = this.value.trim();
          if (!v) return;
          var ud = document.createElement("div");
          ud.style.cssText = "margin:6px 0;text-align:right;padding:6px 10px;background:#e8f5ee;border-radius:10px 10px 10px 2px;color:#333;word-break:break-all;";
          ud.textContent = v;
          document.getElementById("bbMsgs").appendChild(ud);
          this.value = "";
          setTimeout(function(){ say(answer(v)); }, 250);
        }
      });
    })();
    </script>
    """
    components.html(buddy_html, height=420, scrolling=False)


def main():
    render_global_css()
    render_cover()
    # 新用户引导（可跳过）：只有全新会话且未完成引导时出现
    if st.session_state.get("launched") and not st.session_state.get("onboarding_done", False):
        render_onboarding()
        save_state()
        st.stop()
    evts = get_all_events()
    maybe_show_ddd_alert(evts)
    render_header_widgets(evts)
    render_navbar()
    route_page(evts)
    if st.session_state.get("launched"):
        render_buddy()
    save_state()  # 每次交互后自动持久化到本地 JSON


if __name__ == "__main__":
    main()
