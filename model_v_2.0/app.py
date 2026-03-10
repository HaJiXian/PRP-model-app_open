# -*- coding: utf-8 -*-
"""
心理弹性评估系统 - Flask后端主程序
"""

import os
import re
import json
import html as html_mod
import traceback
from flask import Flask, render_template, request, redirect, url_for, jsonify
import pandas as pd
import numpy as np
import joblib
from openai import OpenAI

app = Flask(__name__)

# ===== 获取当前脚本所在目录（确保相对路径正确） =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ===== 模型加载 =====
MODEL_PATH = os.path.join(BASE_DIR, 'RF-m1_slct_r0.pkl')
try:
    model = joblib.load(MODEL_PATH)
    print(f"模型加载成功: {MODEL_PATH}")
except Exception as e:
    print(f"模型加载失败: {e}")
    model = None

# ===== RAG知识库路径 =====
RAG_FILE = os.path.join(BASE_DIR, "RAG知识库实验用文档.txt")

# ===== LLM配置（LM Studio本地服务） =====
LLM_URL = "http://192.168.1.9:1234/v1"
LLM_KEY = "lm-studio"
LLM_MODEL = "deepseek-r1-distill-llama-8b@q8_0"

# ===== 常模数据（群体均值和标准差） =====
NORM_DATA = {
    # 三大维度
    'w1': {'mean': 3.515, 'std': 0.637, 'name': '亲和力'},
    'w2': {'mean': 3.494, 'std': 0.635, 'name': '生命力'},
    'w3': {'mean': 3.474, 'std': 0.663, 'name': '意志力'},
    # 亲和力子维度
    'w1-1': {'mean': 3.551, 'std': 0.932, 'name': '善良'},
    'w1-2': {'mean': 3.484, 'std': 0.985, 'name': '合作'},
    'w1-3': {'mean': 3.503, 'std': 0.96, 'name': '公平'},
    'w1-4': {'mean': 3.497, 'std': 0.969, 'name': '爱'},
    'w1-5': {'mean': 3.517, 'std': 0.958, 'name': '真诚'},
    'w1-6': {'mean': 3.525, 'std': 0.962, 'name': '领导力'},
    'w1-7': {'mean': 3.522, 'std': 0.953, 'name': '宽恕'},
    'w1-8': {'mean': 3.521, 'std': 0.956, 'name': '感恩'},
    # 生命力子维度
    'w2-1': {'mean': 3.509, 'std': 0.959, 'name': '幽默'},
    'w2-2': {'mean': 3.505, 'std': 0.963, 'name': '好奇心'},
    'w2-3': {'mean': 3.481, 'std': 0.991, 'name': '热情'},
    'w2-4': {'mean': 3.477, 'std': 0.975, 'name': '创造力'},
    'w2-5': {'mean': 3.471, 'std': 0.976, 'name': '洞察力'},
    'w2-6': {'mean': 3.487, 'std': 0.974, 'name': '希望'},
    'w2-7': {'mean': 3.462, 'std': 0.956, 'name': '社交'},
    'w2-8': {'mean': 3.512, 'std': 0.956, 'name': '美'},
    'w2-9': {'mean': 3.52, 'std': 0.936, 'name': '勇敢'},
    'w2-10': {'mean': 3.515, 'std': 0.93, 'name': '信仰'},
    # 意志力子维度
    'w3-1': {'mean': 3.46, 'std': 0.977, 'name': '判断力'},
    'w3-2': {'mean': 3.533, 'std': 0.955, 'name': '谨慎'},
    'w3-3': {'mean': 3.437, 'std': 0.982, 'name': '自我管理'},
    'w3-4': {'mean': 3.469, 'std': 0.969, 'name': '毅力'},
    'w3-5': {'mean': 3.466, 'std': 0.988, 'name': '好学'},
    'w3-6': {'mean': 3.478, 'std': 0.927, 'name': '谦虚'},
}


def get_level_by_norm(dim_code, score):
    """
    根据常模数据判断评分等级（三区间）

    参数:
        dim_code: 维度编码（如 'w1-1', 'w2', 'w3-2'）
        score: 个体得分

    返回:
        等级名称和评级代码
        - ('较差', -1): < μ - σ
        - ('一般', 0): μ - σ ~ μ + σ
        - ('优秀', 1): > μ + σ
    """
    if dim_code not in NORM_DATA:
        return ('未知', 0)

    norm = NORM_DATA[dim_code]
    mean = norm['mean']
    std = norm['std']

    lower_bound = mean - std  # 较差阈值
    upper_bound = mean + std  # 优秀阈值

    if score < lower_bound:
        return ('较差', -1)
    elif score > upper_bound:
        return ('优秀', 1)
    else:
        return ('一般', 0)


def get_dimension_name(dim_code):
    """获取维度的中文名称"""
    if dim_code in NORM_DATA:
        return NORM_DATA[dim_code]['name']
    return dim_code


# ===== 核心业务函数 =====

def calculate_features(form_data):
    # 定义features作为字典，存放28个特征的键值对
    # 定义feature_name作为列表，存放特征顺序
    features = {}
    # 根据问卷答案计算以下特征：
    # 'c1', 'c2', 'c5', 'c6', 'age group',
    # 'w1-1', 'w1-2', 'w1-3', 'w1-4', 'w1-5', 'w1-6', 'w1-7', 'w1-8',
    # 'w2-1', 'w2-2', 'w2-3', 'w2-4', 'w2-6', 'w2-7', 'w2-8', 'w2-9', 'w2-10',
    # 'w3-1', 'w3-2', 'w3-3', 'w3-4', 'w3-5', 'w3-6'

    # deal'c1'
    try:
        features['c1'] = float(form_data['q97'])
    except (KeyError, ValueError) as e:
        print(f"Error calculating c1: Missing key {e}")
        features['c1'] = 0.0

    # deal c2
    try:
        features['c2'] = float(form_data['q99'])
    except (KeyError, ValueError) as e:
        print(f"Error calculating c2: Missing key {e}")
        features['c2'] = 0.0

    # deal c5
    try:
        features['c5'] = float(form_data['q106'])
    except (KeyError, ValueError) as e:
        print(f"Error calculating c5: Missing key {e}")
        features['c5'] = 0.0

    # deal c6
    try:
        features['c6'] = float(form_data['q107'])
    except (KeyError, ValueError) as e:
        print(f"Error calculating c6: Missing key {e}")
        features['c6'] = 0.0

    # deal age group
    try:
        features['age group'] = float(form_data['q111'])
    except (KeyError, ValueError) as e:
        print(f"Error calculating age group: Missing key {e}")
        features['age group'] = 0.0

    # deal w1-1
    try:
        w1_1_scores = [
            float(form_data['q8']),
            float(form_data['q15']),
            float(form_data['q45']),
            float(form_data['q66'])
        ]
        features['w1-1'] = np.mean(w1_1_scores)
    except (KeyError, ValueError) as e:
        print(f"Error calculating w1-1: Missing key {e}")
        features['w1-1'] = 0.0

    # deal w1-2
    try:
        w1_2_scores = [
            float(form_data['q10']),
            float(form_data['q47']),
            float(form_data['q68']),
            float(form_data['q78'])
        ]
        features['w1-2'] = np.mean(w1_2_scores)
    except (KeyError, ValueError) as e:
        print(f"Error calculating w1-2: Missing key {e}")
        features['w1-2'] = 0.0

    # deal w1-3
    try:
        w1_3_scores = [
            float(form_data['q22']),
            float(form_data['q35']),
            float(form_data['q79']),
            float(form_data['q92'])
        ]
        features['w1-3'] = np.mean(w1_3_scores)
    except (KeyError, ValueError) as e:
        print(f"Error calculating w1-3: Missing key {e}")
        features['w1-3'] = 0.0

    # deal w1-4
    try:
        w1_4_scores = [
            float(form_data['q9']),
            float(form_data['q46']),
            float(form_data['q67']),
            float(form_data['q77'])
        ]
        features['w1-4'] = np.mean(w1_4_scores)
    except (KeyError, ValueError) as e:
        print(f"Error calculating w1-4: Missing key {e}")
        features['w1-4'] = 0.0

    # deal w1-5
    try:
        w1_5_scores = [
            float(form_data['q2']),
            float(form_data['q7']),
            float(form_data['q34']),
            float(form_data['q91'])
        ]
        features['w1-5'] = np.mean(w1_5_scores)
    except (KeyError, ValueError) as e:
        print(f"Error calculating w1-5: Missing key {e}")
        features['w1-5'] = 0.0

    # deal w1-6
    try:
        w1_6_scores = [
            float(form_data['q11']),
            float(form_data['q36']),
            float(form_data['q69']),
            float(form_data['q80'])
        ]
        features['w1-6'] = np.mean(w1_6_scores)
    except (KeyError, ValueError) as e:
        print(f"Error calculating w1-6: Missing key {e}")
        features['w1-6'] = 0.0

    # deal w1-7
    try:
        w1_7_scores = [
            float(form_data['q28']),
            float(form_data['q39']),
            float(form_data['q53']),
            float(form_data['q73'])
        ]
        features['w1-7'] = np.mean(w1_7_scores)
    except (KeyError, ValueError) as e:
        print(f"Error calculating w1-7: Missing key {e}")
        features['w1-7'] = 0.0

    # deal w1-8
    try:
        w1_8_scores = [
            float(form_data['q37']),
            float(form_data['q61']),
            float(form_data['q71']),
            float(form_data['q83'])
        ]
        features['w1-8'] = np.mean(w1_8_scores)
    except (KeyError, ValueError) as e:
        print(f"Error calculating w1-8: Missing key {e}")
        features['w1-8'] = 0.0

    # deal w2-1
    try:
        w2_1_scores = [
            float(form_data['q38']),
            float(form_data['q51']),
            float(form_data['q62']),
            float(form_data['q95'])
        ]
        features['w2-1'] = np.mean(w2_1_scores)
    except (KeyError, ValueError) as e:
        print(f"Error calculating w2-1: Missing key {e}")
        features['w2-1'] = 0.0

    # deal w2-2
    try:
        w2_2_scores = [
            float(form_data['q29']),
            float(form_data['q40']),
            float(form_data['q54']),
            float(form_data['q74'])
        ]
        features['w2-2'] = np.mean(w2_2_scores)
    except (KeyError, ValueError) as e:
        print(f"Error calculating w2-2: Missing key {e}")
        features['w2-2'] = 0.0

    # deal w2-3
    try:
        w2_3_scores = [
            float(form_data['q27']),
            float(form_data['q52']),
            float(form_data['q87']),
            float(form_data['q96'])
        ]
        features['w2-3'] = np.mean(w2_3_scores)
    except (KeyError, ValueError) as e:
        print(f"Error calculating w2-3: Missing key {e}")
        features['w2-3'] = 0.0

    # deal w2-4
    try:
        w2_4_scores = [
            float(form_data['q14']),
            float(form_data['q32']),
            float(form_data['q41']),
            float(form_data['q57'])
        ]
        features['w2-4'] = np.mean(w2_4_scores)
    except (KeyError, ValueError) as e:
        print(f"Error calculating w2-4: Missing key {e}")
        features['w2-4'] = 0.0

    # deal w2-5 (洞察力) - 新增：用于分析展示，不参与pkl模型预测
    try:
        w2_5_scores = [
            float(form_data['q42']),
            float(form_data['q58']),
            float(form_data['q64']),
            float(form_data['q89'])
        ]
        features['w2-5'] = np.mean(w2_5_scores)
    except (KeyError, ValueError) as e:
        print(f"Error calculating w2-5: Missing key {e}")
        features['w2-5'] = 0.0

    # deal w2-6
    try:
        w2_6_scores = [
            float(form_data['q3']),
            float(form_data['q13']),
            float(form_data['q18']),
            float(form_data['q84'])
        ]
        features['w2-6'] = np.mean(w2_6_scores)
    except (KeyError, ValueError) as e:
        print(f"Error calculating w2-6: Missing key {e}")
        features['w2-6'] = 0.0

    # deal w2-7
    try:
        w2_7_scores = [
            float(form_data['q5']),
            float(form_data['q20']),
            float(form_data['q33']),
            float(form_data['q76'])
        ]
        features['w2-7'] = np.mean(w2_7_scores)
    except (KeyError, ValueError) as e:
        print(f"Error calculating w2-7: Missing key {e}")
        features['w2-7'] = 0.0

    # deal w2-8
    try:
        w2_8_scores = [
            float(form_data['q24']),
            float(form_data['q49']),
            float(form_data['q60']),
            float(form_data['q82'])
        ]
        features['w2-8'] = np.mean(w2_8_scores)
    except (KeyError, ValueError) as e:
        print(f"Error calculating w2-8: Missing key {e}")
        features['w2-8'] = 0.0

    # deal w2-9
    try:
        w2_9_scores = [
            float(form_data['q43']),
            float(form_data['q59']),
            float(form_data['q65']),
            float(form_data['q90'])
        ]
        features['w2-9'] = np.mean(w2_9_scores)
    except (KeyError, ValueError) as e:
        print(f"Error calculating w2-9: Missing key {e}")
        features['w2-9'] = 0.0

    # deal w2-10
    try:
        w2_10_scores = [
            float(form_data['q19']),
            float(form_data['q25']),
            float(form_data['q50']),
            float(form_data['q85'])
        ]
        features['w2-10'] = np.mean(w2_10_scores)
    except (KeyError, ValueError) as e:
        print(f"Error calculating w2-10: Missing key {e}")
        features['w2-10'] = 0.0

    # deal w3-1
    try:
        w3_1_scores = [
            float(form_data['q4']),
            float(form_data['q31']),
            float(form_data['q56']),
            float(form_data['q63'])
        ]
        features['w3-1'] = np.mean(w3_1_scores)
    except (KeyError, ValueError) as e:
        print(f"Error calculating w3-1: Missing key {e}")
        features['w3-1'] = 0.0

    # deal w3-2
    try:
        w3_2_scores = [
            float(form_data['q17']),
            float(form_data['q48']),
            float(form_data['q70']),
            float(form_data['q81'])
        ]
        features['w3-2'] = np.mean(w3_2_scores)
    except (KeyError, ValueError) as e:
        print(f"Error calculating w3-2: Missing key {e}")
        features['w3-2'] = 0.0

    # deal w3-3
    try:
        w3_3_scores = [
            float(form_data['q12']),
            float(form_data['q16']),
            float(form_data['q23']),
            float(form_data['q93'])
        ]
        features['w3-3'] = np.mean(w3_3_scores)
    except (KeyError, ValueError) as e:
        print(f"Error calculating w3-3: Missing key {e}")
        features['w3-3'] = 0.0

    # deal w3-4
    try:
        w3_4_scores = [
            float(form_data['q1']),
            float(form_data['q6']),
            float(form_data['q21']),
            float(form_data['q44'])
        ]
        features['w3-4'] = np.mean(w3_4_scores)
    except (KeyError, ValueError) as e:
        print(f"Error calculating w3-4: Missing key {e}")
        features['w3-4'] = 0.0

    # deal w3-5
    try:
        w3_5_scores = [
            float(form_data['q30']),
            float(form_data['q55']),
            float(form_data['q75']),
            float(form_data['q88'])
        ]
        features['w3-5'] = np.mean(w3_5_scores)
    except (KeyError, ValueError) as e:
        print(f"Error calculating w3-5: Missing key {e}")
        features['w3-5'] = 0.0

    # deal w3-6
    try:
        w3_6_scores = [
            float(form_data['q26']),
            float(form_data['q72']),
            float(form_data['q86']),
            float(form_data['q94'])
        ]
        features['w3-6'] = np.mean(w3_6_scores)
    except (KeyError, ValueError) as e:
        print(f"Error calculating w3-6: Missing key {e}")
        features['w3-6'] = 0.0

    # 确保特征字典的键（特征名）和顺序与模型训练时完全一致
    # 使用模型所需的28个特征名的确切列表（不含w2-5，因为pkl模型不需要）
    feature_names_for_pkl = [
        'c1', 'c2', 'c5', 'c6', 'age group',
        'w1-1', 'w1-2', 'w1-3', 'w1-4', 'w1-5', 'w1-6', 'w1-7', 'w1-8',
        'w2-1', 'w2-2', 'w2-3', 'w2-4', 'w2-6', 'w2-7', 'w2-8', 'w2-9', 'w2-10',
        'w3-1', 'w3-2', 'w3-3', 'w3-4', 'w3-5', 'w3-6'
    ]

    # 确保每个特征都被计算过，避免KeyError
    for name in feature_names_for_pkl:
        if name not in features:
            features[name] = 0.0

    # 从字典中按feature_names的顺序提取值，组成一个二维数组
    feature_values = [features[name] for name in feature_names_for_pkl]

    # 创建DataFrame，列名必须与训练时一致
    final_dataframe = pd.DataFrame([feature_values], columns=feature_names_for_pkl)

    # 返回两个值：
    # 1. final_dataframe: 用于pkl模型预测（28个特征）
    # 2. features: 完整特征字典，用于分析展示（包含w2-5）
    return final_dataframe, features


# ===== RAG检索函数 =====
def rag_retrieve(features_dict):
    """
    RAG检索：基于常模的评分分级 + 单维度全搜

    1. 使用常模数据（均值±标准差）划分评分等级
    2. 只检索筛出的维度（优秀/较差）
    3. 个体变量不参与检索
    4. 协同关系已包含在单归因检索结果中，LLM负责解读
    """
    # 维度基础信息（只保留性格优势维度，个体变量不参与检索）
    dimension_info = {
        'w1-1': {'name': '善良', 'alt_names': [], 'category': '亲和力'},
        'w1-2': {'name': '合作', 'alt_names': ['团队合作'], 'category': '亲和力'},
        'w1-3': {'name': '公平', 'alt_names': [], 'category': '亲和力'},
        'w1-4': {'name': '爱', 'alt_names': [], 'category': '亲和力'},
        'w1-5': {'name': '真诚', 'alt_names': ['正直'], 'category': '亲和力'},
        'w1-6': {'name': '领导力', 'alt_names': [], 'category': '亲和力'},
        'w1-7': {'name': '宽恕', 'alt_names': ['仁慈','饶恕'], 'category': '亲和力'},
        'w1-8': {'name': '感恩', 'alt_names': [], 'category': '亲和力'},

        'w2-1': {'name': '幽默', 'alt_names': [], 'category': '生命力'},
        'w2-2': {'name': '好奇心', 'alt_names': [], 'category': '生命力'},
        'w2-3': {'name': '热情', 'alt_names': [], 'category': '生命力'},
        'w2-4': {'name': '创造力', 'alt_names': [], 'category': '生命力'},
        'w2-5': {'name': '洞察力', 'alt_names': [], 'category': '生命力'},
        'w2-6': {'name': '希望', 'alt_names': [], 'category': '生命力'},
        'w2-7': {'name': '社交', 'alt_names': ['社交智慧'], 'category': '生命力'},
        'w2-8': {'name': '美', 'alt_names': ['欣赏美', '审美'], 'category': '生命力'},
        'w2-9': {'name': '勇敢', 'alt_names': [], 'category': '生命力'},
        'w2-10': {'name': '信仰', 'alt_names': [], 'category': '生命力'},

        'w3-1': {'name': '判断力', 'alt_names': [], 'category': '意志力'},
        'w3-2': {'name': '谨慎', 'alt_names': [], 'category': '意志力'},
        'w3-3': {'name': '自我管理', 'alt_names': [], 'category': '意志力'},
        'w3-4': {'name': '毅力', 'alt_names': [], 'category': '意志力'},
        'w3-5': {'name': '好学', 'alt_names': ['爱学习'], 'category': '意志力'},
        'w3-6': {'name': '谦虚', 'alt_names': [], 'category': '意志力'},
    }

    # 读取知识库
    try:
        with open(RAG_FILE, 'r', encoding='utf-8') as f:
            knowledge_base = f.read()
    except Exception as e:
        print(f"知识库读取失败: {e}")
        knowledge_base = ""

    # === 细粒度切分知识库 ===
    paragraphs = knowledge_base.split('\n\n')
    chunks = []

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        lines = para.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 按句号、问号、感叹号、分号切分
            sentences = re.split(r'[。！？；; ,]', line)
            for sent in sentences:
                sent = sent.strip()
                if len(sent) > 3:  # 过滤太短的片段
                    chunks.append(sent)

    # === 使用常模数据对维度进行评级 ===
    excellent_dims = []  # 优秀维度（> μ + σ）
    poor_dims = []  # 较差维度（< μ - σ）
    normal_dims = []  # 一般维度（μ ± σ）
    all_dims = []  # 所有维度（用于计算大维度）

    for dim, score in features_dict.items():
        if dim not in dimension_info:
            continue  # 跳过个体变量（c1, c2, c5, c6, age group）

        info = dimension_info[dim]
        all_names = [info['name']] + info.get('alt_names', [])
        level_name, level_code = get_level_by_norm(dim, score)

        dim_data = {
            'dim': dim,
            'name': info['name'],
            'all_names': all_names,
            'score': score,
            'category': info['category'],
            'level_name': level_name,
            'level_code': level_code
        }

        all_dims.append(dim_data)

        if level_code == 1:  # 优秀
            excellent_dims.append(dim_data)
        elif level_code == -1:  # 较差
            poor_dims.append(dim_data)
        else:  # 一般
            normal_dims.append(dim_data)

    # === 单因归因检索（只检索优秀和较差的维度） ===
    single_cause_results = []
    filtered_dims = excellent_dims + poor_dims  # 只检索筛出的维度

    for dim in filtered_dims:
        matched_chunks = []

        for chunk in chunks:
            # 检查是否包含该维度的任何名称
            contains_dim = any(name in chunk for name in dim['all_names'])
            if contains_dim:
                # 计算相关性：维度名出现次数 + 大类出现次数
                keyword_count = sum(1 for name in dim['all_names'] if name in chunk)
                keyword_count += 1 if dim['category'] in chunk else 0

                matched_chunks.append({
                    'text': chunk,
                    'relevance': keyword_count
                })

        if matched_chunks:
            matched_chunks.sort(key=lambda x: x['relevance'], reverse=True)
            single_cause_results.append({
                'dim': dim['name'],
                'dim_code': dim['dim'],
                'level': dim['level_name'],
                'score': dim['score'],
                'category': dim['category'],
                'evidence': matched_chunks
            })

    # === 计算三大维度得分 ===
    big_dimensions = {'亲和力': [], '生命力': [], '意志力': []}

    for dim_data in all_dims:
        category = dim_data['category']
        if category in big_dimensions:
            big_dimensions[category].append(dim_data['score'])

    big_dim_scores = {}
    for big_cat, scores in big_dimensions.items():
        if scores:
            avg_score = sum(scores) / len(scores)
            # 使用常模判断大维度等级
            big_dim_code = {'亲和力': 'w1', '生命力': 'w2', '意志力': 'w3'}[big_cat]
            level_name, level_code = get_level_by_norm(big_dim_code, avg_score)
            big_dim_scores[big_cat] = {
                'score': avg_score,
                'count': len(scores),
                'level_name': level_name,
                'level_code': level_code
            }

    # === 组织输出（不输出具体分数，只输出等级） ===
    retrieved_text = []

    # 1. 维度状态总览（基于常模）- 不含分数
    retrieved_text.append("【维度状态总览（基于群体常模）】")
    retrieved_text.append("评级标准：优秀(高于大多数人)、一般(正常范围)、较差(低于大多数人)")

    if excellent_dims:
        retrieved_text.append(f"\n优秀维度({len(excellent_dims)}个): " +
                              ', '.join([d['name'] for d in excellent_dims]))
    if poor_dims:
        retrieved_text.append(f"较差维度({len(poor_dims)}个): " +
                              ', '.join([d['name'] for d in poor_dims]))
    if normal_dims:
        retrieved_text.append(f"一般维度({len(normal_dims)}个): " +
                              ', '.join([d['name'] for d in normal_dims]))

    # 2. 三大维度概览 - 不含分数
    retrieved_text.append("\n【三大维度概览】")
    for big_cat in ['亲和力', '生命力', '意志力']:
        if big_cat in big_dim_scores:
            info = big_dim_scores[big_cat]
            retrieved_text.append(f"  {big_cat}：{info['level_name']}")

    # 3. 单因归因检索结果 - 不含分数
    if single_cause_results:
        retrieved_text.append("\n【知识库检索结果】")
        retrieved_text.append("以下是与您优秀/较差维度相关的知识库内容：")

        for result in single_cause_results:
            level_marker = "★" if result['level'] == '优秀' else "▼"
            retrieved_text.append(
                f"\n{level_marker} {result['dim']}（{result['category']}，{result['level']}）")
            retrieved_text.append(f"  检索到{len(result['evidence'])}条相关描述：")
            # 只取前5条最相关的
            for i, evi in enumerate(result['evidence'][:5], 1):
                retrieved_text.append(f"    [{i}] {evi['text']}")

    return "\n".join(retrieved_text)


def preprocess_dimensions(dimensions_dict):
    """
    预处理维度数据，使用常模数据进行评级
    个体变量不参与分析，只展示性格优势维度
    注意：不输出具体分数，只输出等级，避免LLM照搬分数
    """

    # 格式化输出
    result = []

    # === 亲和力维度 ===
    result.append("【亲和力（人际交往能力）】")
    w1_scores = []
    w1_dims = ['w1-1', 'w1-2', 'w1-3', 'w1-4', 'w1-5', 'w1-6', 'w1-7', 'w1-8']

    for key in w1_dims:
        if key in dimensions_dict:
            score = dimensions_dict[key]
            w1_scores.append(score)
            name = get_dimension_name(key)
            level_name, _ = get_level_by_norm(key, score)
            result.append(f"  {name}：{level_name}")

    if w1_scores:
        avg = sum(w1_scores) / len(w1_scores)
        level_name, _ = get_level_by_norm('w1', avg)
        result.append(f"  → 亲和力整体：{level_name}")

    # === 生命力维度（包含w2-5洞察力）===
    result.append("\n【生命力（活力与积极性）】")
    w2_scores = []
    w2_dims = ['w2-1', 'w2-2', 'w2-3', 'w2-4', 'w2-5', 'w2-6', 'w2-7', 'w2-8', 'w2-9', 'w2-10']

    for key in w2_dims:
        if key in dimensions_dict:
            score = dimensions_dict[key]
            w2_scores.append(score)
            name = get_dimension_name(key)
            level_name, _ = get_level_by_norm(key, score)
            result.append(f"  {name}：{level_name}")

    if w2_scores:
        avg = sum(w2_scores) / len(w2_scores)
        level_name, _ = get_level_by_norm('w2', avg)
        result.append(f"  → 生命力整体：{level_name}")

    # === 意志力维度 ===
    result.append("\n【意志力（自我管理能力）】")
    w3_scores = []
    w3_dims = ['w3-1', 'w3-2', 'w3-3', 'w3-4', 'w3-5', 'w3-6']

    for key in w3_dims:
        if key in dimensions_dict:
            score = dimensions_dict[key]
            w3_scores.append(score)
            name = get_dimension_name(key)
            level_name, _ = get_level_by_norm(key, score)
            result.append(f"  {name}：{level_name}")

    if w3_scores:
        avg = sum(w3_scores) / len(w3_scores)
        level_name, _ = get_level_by_norm('w3', avg)
        result.append(f"  → 意志力整体：{level_name}")

    return "\n".join(result)


def calculate_chart_data(features_dict):
    """
    计算用于前端图表展示的数据
    包括：三大维度得分、评级、子维度详情
    """
    # 子维度配置
    w1_dims = ['w1-1', 'w1-2', 'w1-3', 'w1-4', 'w1-5', 'w1-6', 'w1-7', 'w1-8']
    w2_dims = ['w2-1', 'w2-2', 'w2-3', 'w2-4', 'w2-5', 'w2-6', 'w2-7', 'w2-8', 'w2-9', 'w2-10']
    w3_dims = ['w3-1', 'w3-2', 'w3-3', 'w3-4', 'w3-5', 'w3-6']

    # 计算三大维度得分
    def calc_avg(dim_list):
        scores = [features_dict.get(d, 0) for d in dim_list if d in features_dict]
        return round(sum(scores) / len(scores), 2) if scores else 0

    w1_avg = calc_avg(w1_dims)
    w2_avg = calc_avg(w2_dims)
    w3_avg = calc_avg(w3_dims)

    # 获取大维度评级和常模数据
    w1_level, w1_code = get_level_by_norm('w1', w1_avg)
    w2_level, w2_code = get_level_by_norm('w2', w2_avg)
    w3_level, w3_code = get_level_by_norm('w3', w3_avg)

    # 大维度数据
    big_dimensions = {
        'w1': {
            'name': '亲和力',
            'score': w1_avg,
            'level': w1_level,
            'mean': NORM_DATA['w1']['mean'],
            'std': NORM_DATA['w1']['std'],
            'lower': round(NORM_DATA['w1']['mean'] - NORM_DATA['w1']['std'], 2),
            'upper': round(NORM_DATA['w1']['mean'] + NORM_DATA['w1']['std'], 2)
        },
        'w2': {
            'name': '生命力',
            'score': w2_avg,
            'level': w2_level,
            'mean': NORM_DATA['w2']['mean'],
            'std': NORM_DATA['w2']['std'],
            'lower': round(NORM_DATA['w2']['mean'] - NORM_DATA['w2']['std'], 2),
            'upper': round(NORM_DATA['w2']['mean'] + NORM_DATA['w2']['std'], 2)
        },
        'w3': {
            'name': '意志力',
            'score': w3_avg,
            'level': w3_level,
            'mean': NORM_DATA['w3']['mean'],
            'std': NORM_DATA['w3']['std'],
            'lower': round(NORM_DATA['w3']['mean'] - NORM_DATA['w3']['std'], 2),
            'upper': round(NORM_DATA['w3']['mean'] + NORM_DATA['w3']['std'], 2)
        }
    }

    # 子维度数据（用于雷达图）
    def get_sub_dims(dim_list):
        result = []
        for d in dim_list:
            if d in features_dict and d in NORM_DATA:
                score = round(features_dict[d], 2)
                level, _ = get_level_by_norm(d, score)
                result.append({
                    'code': d,
                    'name': NORM_DATA[d]['name'],
                    'score': score,
                    'level': level,
                    'mean': NORM_DATA[d]['mean'],
                    'lower': round(NORM_DATA[d]['mean'] - NORM_DATA[d]['std'], 2),
                    'upper': round(NORM_DATA[d]['mean'] + NORM_DATA[d]['std'], 2)
                })
        return result

    sub_dimensions = {
        'w1': get_sub_dims(w1_dims),
        'w2': get_sub_dims(w2_dims),
        'w3': get_sub_dims(w3_dims)
    }

    return {
        'big_dimensions': big_dimensions,
        'sub_dimensions': sub_dimensions
    }


def llm_analyze(dimensions_dict, prediction_score, rag_result):
    """调用LLM生成心理弹性分析报告"""
    # 使用预处理函数格式化数据
    dimensions_str = preprocess_dimensions(dimensions_dict)

    # 确定等级描述（0-4分制，与前端保持一致）
    if prediction_score < 0:
        level_desc = "评分超出范围"
    elif 0 <= prediction_score < 1.8:
        level_desc = "较低水平"
    elif 1.8 <= prediction_score < 2.6:
        level_desc = "中等水平"
    elif 2.6 <= prediction_score < 3.4:
        level_desc = "良好水平"
    elif 3.4 <= prediction_score <= 4:
        level_desc = "优秀水平"
    else:
        level_desc = "未知水平"

    # ========== Prompt ==========
    prompt = f"""作为心理咨询师，请为这位大学生写一份心理弹性评估报告。

【来访者数据】
{dimensions_str}

心理弹性整体水平：{level_desc}

【知识库检索结果】
{rag_result}

【评级说明】
- 维度评级基于群体常模（均值±标准差）
- "优秀"：高于大多数人；"一般"：正常范围；"较差"：低于大多数人
- 特别注意：知识库中标注"负向影响"的维度，高分反而需要关注

【核心原则】
1. 一切分析和描述必须有据可依——只能基于上面提供的来访者数据和知识库检索结果进行分析，不得凭空编造任何结论
2. 对各个维度和子维度只描述等级水平（如"表现优秀""处于一般水平""相对薄弱"），不要提及具体的得分数字
3. 像一个真人咨询师在跟来访者面对面聊天一样说话，语气自然亲切，不要出现"根据数据显示""经分析""依据知识库"之类机械化的措辞

【报告格式要求】
请严格按以下格式输出，不要输出任何思考过程，禁止提及具体的分数数字（如3.52分、2.88分等），只描述等级：

一、三大维度表现分析
（禁止提及具体的分数数字（如3.52分、2.88分等），只描述等级）
分别分析亲和力、生命力、意志力三个大维度的整体表现：
（1）该大维度的整体评级如何
（2）哪些子维度表现优秀，对大维度有正向贡献
（3）哪些子维度表现较差，拖累了大维度
（4）综合来看，该大维度对心理弹性的影响
（每个分点100-200字）
格式：
1、亲和力：整体表现XX。其中XX、XX表现优秀，XX表现较差。这使得...
2、生命力：...
3、意志力：...

二、子维度之间的相互作用
（禁止没有知识库证据的判断，不能无中生有）
（优先针对表现优秀或者是较差的子维度分析，实在没有再分析一般的，且保证分析后输出的语句逻辑正确）
（如果某个部分确实没有内容可写（比如知识库中没有检索到相互作用关系），直接跳过该部分，不要硬编乱写）
根据知识库中的维度间关系，分析子维度之间的促进或对抗作用：
（1）哪些子维度之间存在相互促进关系
（2）哪些子维度之间存在对抗或制约关系
（3）这些相互作用如何影响大维度的表现和整体心理弹性
（每个分点20-50字）
格式：
1、XX与XX相互促进：...（描述具体表现和影响）
2、XX与XX存在对抗：...（描述具体表现和影响）

三、改善建议（必须输出）

针对表现较差或一般的维度，给出具体可行的建议：
（结合大学生实际场景：课程学习、社团活动、宿舍生活、考试备考、社交等）
（每个分点20-80字，至少给出2-3条建议）
格式：
1、提升XX：...（具体建议）
2、改善XX：...（具体建议）

（祝福语）
祝您在今后的学习生活中学有所成，劳有所得，生活更将幸福美满！（可以依次类型合理改动）


【重要说明】
- "子维度之间的相互作用"部分：如果知识库中没有检索到相关证据，直接跳过，不要硬编
- "改善建议"部分：必须输出，不能跳过，即使所有维度都表现优秀，也要给出保持或进一步提升的建议
- 大分点序号要根据实际输出的部分顺延编号（如跳过了"子维度相互作用"，则"改善建议"就是二而不是三）

【绝对禁止】
1. 禁止输出<think>标签或任何思考过程
2. 禁止使用w1-3、c1、c2等编码，只用中文名称
3. 禁止使用Markdown符号（#、*、-等）
4. 禁止没有知识库证据的判断，不能无中生有
5. 禁止提及具体的分数数字（如3.52分、2.88分等），只描述等级
6. 禁止出现"依据知识库""根据数据""经分析"等机械化AI措辞

【最终提醒】
你的输出必须包含"改善建议"部分，这是必须的。在写完前面的分析后，一定要继续写改善建议，不要提前结束。
"""

    # 调用LLM API
    try:
        client = OpenAI(base_url=LLM_URL, api_key=LLM_KEY)

        # 先获取可用模型列表
        try:
            models = client.models.list()
            available_model = models.data[0].id if models.data else LLM_MODEL
            print(f"使用模型: {available_model}")
        except Exception:
            available_model = LLM_MODEL
            print(f"无法获取模型列表，使用默认: {available_model}")

        # 构建system message
        system_msg = (
            "你是一位温暖、专业的心理咨询师，正在跟一位大学生面对面聊心理弹性的情况。"
            "请用自然亲切的口语化语言，像真人对话一样交流，避免使用可能伤及自尊心的措辞。"
            "绝对禁止输出<think>标签或任何思考过程，直接输出报告内容。"
            "禁止使用任何技术编码（如w1-3、c1等），全部使用中文名称。"
            "禁止提及具体得分数字，只用'表现优秀''处于一般水平''相对薄弱'等描述等级。"
            "描述影响时用'可能''也许'等词，避免绝对化表达。"
            "语句要自然通顺像说人话，不要说'依据知识库''根据分析结果'之类机械化的话。"
            "一二三部分只做分析描述，不给建议；建议只放在第三部分。"
            "所有分析必须基于给定数据和知识库内容，不能凭空编造。"
            "示例只是格式展示，实际关系要根据知识库检索和特征情况自行判断。"
            "不要乱用逻辑关联词，用语符合人类逻辑"
            "禁止提及具体的分数数字（如3.52分、2.88分等），只描述等级"
        )

        response = client.chat.completions.create(
            model=available_model,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,  # 稍微提高温度，让语言更自然
            max_tokens=4096  # 增加max_tokens确保完整输出
        )

        # 获取原始回复
        raw_analysis = response.choices[0].message.content

        # 过滤思考过程（DeepSeek R1模型特有）
        # 移除<think>...</think>标签及其内容
        analysis = re.sub(r'<think>.*?</think>', '', raw_analysis, flags=re.DOTALL)
        # 移除可能的其他思考标记
        analysis = re.sub(r'<thinking>.*?</thinking>', '', analysis, flags=re.DOTALL)

        # 移除可能残留的编码格式（如 w1-3、c1 等）
        analysis = re.sub(r'\(w\d+-\d+\)', '', analysis)
        analysis = re.sub(r'\(c\d+\)', '', analysis)
        analysis = re.sub(r'w\d+-\d+', '', analysis)
        analysis = re.sub(r'\bc\d+\b', '', analysis)

        # 移除类似 "运动习惯(c1): 3.00" 的格式
        analysis = re.sub(r'[\(（][^)）]*[\)）]\s*[:：]\s*\d+\.\d+', '', analysis)

        # 清理多余的空行
        analysis = re.sub(r'\n{3,}', '\n\n', analysis)
        analysis = analysis.strip()

        # 文本格式化为HTML友好格式
        # 先转义HTML特殊字符，防止XSS注入
        # 再将段落分隔转换为HTML段落标签
        paragraphs = analysis.split('\n\n')
        formatted_paragraphs = []
        for para in paragraphs:
            if para.strip():
                para_escaped = html_mod.escape(para)
                para_html = para_escaped.replace('\n', '<br>')
                formatted_paragraphs.append(f'<p>{para_html}</p>')

        analysis = ''.join(formatted_paragraphs)

        return analysis
    except Exception as e:
        print(f"LLM调用失败: {e}")
        traceback.print_exc()
        return "<p>心理咨询师分析报告暂时无法生成，请稍后重试。您仍可参考上方的维度得分和图表了解自己的心理弹性状况。</p>"


# ===== 路由接口 =====

@app.route('/')
def start():
    """首页"""
    if model is None:
        error_message = "模型未正确加载，无法进行预测，请联系管理员处理"
        return render_template('start.html', error=error_message)
    return render_template('start.html')


@app.route('/questionnaire')
def questionnaire():
    """问卷页"""
    if model is None:
        error_message = "模型未正确加载，无法进行预测，请联系管理员处理"
        return render_template('index.html', error=error_message)
    return render_template('index.html')


@app.route('/predict', methods=['POST'])
def predict():
    """接收表单，跳转等待页"""
    # 检查模型是否已加载
    if model is None:
        error_message = "模型未正确加载，无法进行预测"
        return render_template('index.html', error=error_message)

    # 获取表单数据并传递给等待页面
    form_data = request.form.to_dict()
    return render_template('wait.html', form_data=form_data)


@app.route('/predict_process', methods=['POST'])
def predict_process():
    """核心处理：特征计算 → 模型预测 → RAG检索 → LLM分析 → 结果页"""
    # 检查模型是否已加载
    if model is None:
        error_message = "模型未正确加载，无法进行预测"
        return render_template('index.html', error=error_message)

    # 1. 获取前端传来的114道题的答案
    answers = request.form

    # 1.5 基本验证：检查表单是否包含足够的问卷数据
    q_keys = [k for k in answers.keys() if k.startswith('q')]
    if len(q_keys) < 90:
        print(f"表单数据不完整: 仅收到{len(q_keys)}个问题的答案")
        return render_template('index.html',
                               error="提交的问卷数据不完整，请确保所有题目都已作答后重新提交")

    # 2. 调用函数，根据答案计算特征
    # 返回两个值：用于pkl预测的DataFrame和用于分析的完整特征字典
    try:
        input_features_df, full_features_dict = calculate_features(answers)
    except Exception as e:
        print(f"特征计算异常: {e}")
        traceback.print_exc()
        return render_template('index.html',
                               error="处理问卷答案时发生内部错误，请检查是否所有题目都已正确填写")

    # 3. 用计算好的特征进行预测（使用28个特征的DataFrame）
    try:
        prediction = model.predict(input_features_df)
        result = prediction[0]  # 获取单个预测结果
        if result > 4:
            result = 4.00  # 总分上限为4分
        if result < 0:
            result = 0.00  # 总分下限为0分
        result = round(result, 2)
    except Exception as e:
        print(f"模型预测异常: {e}")
        traceback.print_exc()
        return render_template('index.html',
                               error="模型预测时发生内部错误，请稍后重试")

    # 4. 计算三大维度得分和子维度数据（用于图表展示）
    try:
        chart_data = calculate_chart_data(full_features_dict)
    except Exception as e:
        print(f"图表数据计算异常: {e}")
        traceback.print_exc()
        return render_template('index.html',
                               error="评估结果生成失败，请稍后重试")

    # 5. RAG检索（使用完整特征字典，包含w2-5）
    try:
        rag_result = rag_retrieve(full_features_dict)
    except Exception as e:
        print(f"RAG检索失败: {e}")
        traceback.print_exc()
        rag_result = "知识库检索暂时不可用"

    # 6. LLM生成分析报告（使用完整特征字典）
    try:
        llm_analysis = llm_analyze(full_features_dict, result, rag_result)
    except Exception as e:
        print(f"LLM分析失败: {e}")
        traceback.print_exc()
        llm_analysis = None

    # 7. 跳转到结果页面，传递预测结果、图表数据和LLM分析
    return render_template('result.html',
                           prediction=result,
                           chart_data=chart_data,
                           analysis=llm_analysis)


@app.route('/new-assessment')
def new_assessment():
    """重新评估入口"""
    return redirect(url_for('questionnaire', new=True))


# ===== 全局错误处理 =====

@app.errorhandler(404)
def page_not_found(e):
    return render_template('start.html', error="您访问的页面不存在，请从首页重新开始"), 404


@app.errorhandler(500)
def internal_server_error(e):
    print(f"500错误: {e}")
    return render_template('start.html', error="服务器内部错误，请稍后重试"), 500


# ===== 启动入口 =====
if __name__ == '__main__':
    app.run(debug=True)