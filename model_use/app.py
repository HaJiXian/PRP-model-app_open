from flask import Flask, render_template, request, redirect, url_for, jsonify
import pandas as pd
import numpy as np
import joblib

app = Flask(__name__)

try:
    model = joblib.load('RF-m1_slct_r0.pkl')
    print("模型加载成功")
except Exception as e:
    print(f"模型加载失败: {e}")
    model = None
    # exit(1)


def calculate_features(form_data):
    #定义features作为字典，存放28个特征的键值对
    #定义feature_name作为列表，存放特征顺序
    features = {}
    # 根据问卷答案计算以下特征：
    # 'c1', 'c2', 'c5', 'c6', 'age group',
    # 'w1-1', 'w1-2', 'w1-3', 'w1-4', 'w1-5', 'w1-6', 'w1-7', 'w1-8',
    # 'w2-1', 'w2-2', 'w2-3', 'w2-4', 'w2-6', 'w2-7', 'w2-8', 'w2-9', 'w2-10',
    # 'w3-1', 'w3-2', 'w3-3', 'w3-4', 'w3-5', 'w3-6'

    #deal‘c1’
    try:
        features['c1'] = float(form_data['q97'])
    except KeyError as e:
        print(f"Error calculating c1: Missing key {e}")
        features['c1'] = 0.0

    #deal c2
    try:
        features['c2'] = float(form_data['q99'])
    except KeyError as e:
        print(f"Error calculating c2: Missing key {e}")
        features['c2'] = 0.0

    #deal c5
    try:
        features['c5'] = float(form_data['q106'])
    except KeyError as e:
        print(f"Error calculating c5: Missing key {e}")
        features['c5'] = 0.0 

    #deal c6
    try:
        features['c6'] = float(form_data['q107'])
    except KeyError as e:
        print(f"Error calculating c6: Missing key {e}")
        features['c6'] = 0.0

    #deal age group
    try:
        features['age group'] = float(form_data['q111'])
    except KeyError as e:
        print(f"Error calculating age group: Missing key {e}")
        features['age group'] = 0.0

    #deal w1-1
    try:
        w1_1_scores = [
            float(form_data['q8']),
            float(form_data['q15']),
            float(form_data['q45']),
            float(form_data['q66'])
        ]
        features['w1-1'] = np.mean(w1_1_scores)
    except KeyError as e:
        print(f"Error calculating w1-1: Missing key {e}")
        features['w1-1'] = 0.0


    #deal w1-2
    try:
        w1_2_scores = [
            float(form_data['q10']),
            float(form_data['q47']),
            float(form_data['q68']),
            float(form_data['q78'])
        ]
        features['w1-2'] = np.mean(w1_2_scores)
    except KeyError as e:
        print(f"Error calculating w1-2: Missing key {e}")
        features['w1-2'] = 0.0

    #deal w1-3
    try:
        w1_3_scores = [
            float(form_data['q22']),
            float(form_data['q35']),
            float(form_data['q79']),
            float(form_data['q92'])
        ]
        features['w1-3'] = np.mean(w1_3_scores)
    except KeyError as e:
        print(f"Error calculating w1-3: Missing key {e}")
        features['w1-3'] = 0.0

    #deal w1-4
    try:
        w1_4_scores = [
            float(form_data['q9']),
            float(form_data['q46']),
            float(form_data['q67']),
            float(form_data['q77'])
        ]
        features['w1-4'] = np.mean(w1_4_scores)
    except KeyError as e:
        print(f"Error calculating w1-4: Missing key {e}")
        features['w1-4'] = 0.0

    #deal w1-5
    try:
        w1_5_scores = [
            float(form_data['q2']),
            float(form_data['q7']),
            float(form_data['q34']),
            float(form_data['q91'])
        ]
        features['w1-5'] = np.mean(w1_5_scores)
    except KeyError as e:
        print(f"Error calculating w1-5: Missing key {e}")
        features['w1-5'] = 0.0

    #deal w1-6
    try:
        w1_6_scores = [
            float(form_data['q11']),
            float(form_data['q36']),
            float(form_data['q69']),
            float(form_data['q80'])
        ]
        features['w1-6'] = np.mean(w1_6_scores)
    except KeyError as e:
        print(f"Error calculating w1-6: Missing key {e}")
        features['w1-6'] = 0.0

    #deal w1-7
    try:
        w1_7_scores = [
            float(form_data['q28']),
            float(form_data['q39']),
            float(form_data['q53']),
            float(form_data['q73'])
        ]
        features['w1-7'] = np.mean(w1_7_scores)
    except KeyError as e:
        print(f"Error calculating w1-7: Missing key {e}")
        features['w1-7'] = 0.0

    #deal w1-8
    try:
        w1_8_scores = [
            float(form_data['q37']),
            float(form_data['q61']),
            float(form_data['q71']),
            float(form_data['q83'])
        ]
        features['w1-8'] = np.mean(w1_8_scores)
    except KeyError as e:
        print(f"Error calculating w1-8: Missing key {e}")
        features['w1-8'] = 0.0

    #deal w2-1
    try:
        w2_1_scores = [
            float(form_data['q38']),
            float(form_data['q51']),
            float(form_data['q62']),
            float(form_data['q95'])
        ]
        features['w2-1'] = np.mean(w2_1_scores)
    except KeyError as e:
        print(f"Error calculating w2-1: Missing key {e}")
        features['w2-1'] = 0.0

    #deal w2-2
    try:
        w2_2_scores = [
            float(form_data['q29']),
            float(form_data['q40']),
            float(form_data['q54']),
            float(form_data['q74'])
        ]
        features['w2-2'] = np.mean(w2_2_scores)
    except KeyError as e:
        print(f"Error calculating w2-2: Missing key {e}")
        features['w2-2'] = 0.0

    #deal w2-3
    try:
        w2_3_scores = [
            float(form_data['q27']),
            float(form_data['q52']),
            float(form_data['q87']),
            float(form_data['q96'])
        ]
        features['w2-3'] = np.mean(w2_3_scores)
    except KeyError as e:
        print(f"Error calculating w2-3: Missing key {e}")
        features['w2-3'] = 0.0

    #deal w2-4
    try:
        w2_4_scores = [
            float(form_data['q14']),
            float(form_data['q32']),
            float(form_data['q41']),
            float(form_data['q57'])
        ]
        features['w2-4'] = np.mean(w2_4_scores)
    except KeyError as e:
        print(f"Error calculating w2-4: Missing key {e}")
        features['w2-4'] = 0.0

    #deal w2-6
    try:
        w2_6_scores = [
            float(form_data['q3']),
            float(form_data['q13']),
            float(form_data['q18']),
            float(form_data['q84'])
        ]
        features['w2-6'] = np.mean(w2_6_scores)
    except KeyError as e:
        print(f"Error calculating w2-6: Missing key {e}")
        features['w2-6'] = 0.0

    #deal w2-7
    try:
        w2_7_scores = [
            float(form_data['q5']),
            float(form_data['q20']),
            float(form_data['q33']),
            float(form_data['q76'])
        ]
        features['w2-7'] = np.mean(w2_7_scores)
    except KeyError as e:
        print(f"Error calculating w2-7: Missing key {e}")
        features['w2-7'] = 0.0

    #deal w2-8
    try:
        w2_8_scores = [
            float(form_data['q24']),
            float(form_data['q49']),
            float(form_data['q60']),
            float(form_data['q82'])
        ]
        features['w2-8'] = np.mean(w2_8_scores)
    except KeyError as e:
        print(f"Error calculating w2-8: Missing key {e}")
        features['w2-8'] = 0.0

    #deal w2-9
    try:
        w2_9_scores = [
            float(form_data['q43']),
            float(form_data['q59']),
            float(form_data['q65']),
            float(form_data['q90'])
        ]
        features['w2-9'] = np.mean(w2_9_scores)
    except KeyError as e:
        print(f"Error calculating w2-9: Missing key {e}")
        features['w2-9'] = 0.0

    #deal w2-10
    try:
        w2_10_scores = [
            float(form_data['q19']),
            float(form_data['q25']),
            float(form_data['q50']),
            float(form_data['q85'])
        ]
        features['w2-10'] = np.mean(w2_10_scores)
    except KeyError as e:
        print(f"Error calculating w2-10: Missing key {e}")
        features['w2-10'] = 0.0

    #deal w3-1
    try:
        w3_1_scores = [
            float(form_data['q4']),
            float(form_data['q31']),
            float(form_data['q56']),
            float(form_data['q63'])
        ]
        features['w3-1'] = np.mean(w3_1_scores)
    except KeyError as e:
        print(f"Error calculating w3-1: Missing key {e}")
        features['w3-1'] = 0.0

    #deal w3-2
    try:
        w3_2_scores = [
            float(form_data['q17']),
            float(form_data['q48']),
            float(form_data['q70']),
            float(form_data['q81'])
        ]
        features['w3-2'] = np.mean(w3_2_scores)
    except KeyError as e:
        print(f"Error calculating w3-2: Missing key {e}")
        features['w3-2'] = 0.0

    #deal w3-3
    try:
        w3_3_scores = [
            float(form_data['q12']),
            float(form_data['q16']),
            float(form_data['q23']),
            float(form_data['q93'])
        ]
        features['w3-3'] = np.mean(w3_3_scores)
    except KeyError as e:
        print(f"Error calculating w3-3: Missing key {e}")
        features['w3-3'] = 0.0

    #deal w3-4
    try:
        w3_4_scores = [
            float(form_data['q1']),
            float(form_data['q6']),
            float(form_data['q21']),
            float(form_data['q44'])
        ]
        features['w3-4'] = np.mean(w3_4_scores)
    except KeyError as e:
        print(f"Error calculating w3-4: Missing key {e}")
        features['w3-4'] = 0.0

    #deal w3-5
    try:
        w3_5_scores = [
            float(form_data['q30']),
            float(form_data['q55']),
            float(form_data['q75']),
            float(form_data['q88'])
        ]
        features['w3-5'] = np.mean(w3_5_scores)
    except KeyError as e:
        print(f"Error calculating w3-5: Missing key {e}")
        features['w3-5'] = 0.0

    #deal w3-6
    try:
        w3_6_scores = [
            float(form_data['q26']),
            float(form_data['q72']),
            float(form_data['q86']),
            float(form_data['q94'])
        ]
        features['w3-6'] = np.mean(w3_6_scores)
    except KeyError as e:
        print(f"Error calculating w3-6: Missing key {e}")
        features['w3-6'] = 0.0

    # 确保特征字典的键（特征名）和顺序与模型训练时完全一致
    # 使用模型所需的28个特征名的确切列表
    feature_names = [
        'c1', 'c2', 'c5', 'c6', 'age group',
        'w1-1', 'w1-2', 'w1-3', 'w1-4', 'w1-5', 'w1-6', 'w1-7', 'w1-8',
        'w2-1', 'w2-2', 'w2-3', 'w2-4', 'w2-6', 'w2-7', 'w2-8', 'w2-9', 'w2-10',
        'w3-1', 'w3-2', 'w3-3', 'w3-4', 'w3-5', 'w3-6'
    ]

    # 确保每个特征都被计算过，避免KeyError
    for name in feature_names:
        if name not in features:
            features[name] = 0.0

    # 从字典中按feature_names的顺序提取值，组成一个二维数组
    feature_values = [features[name] for name in feature_names]

    # 创建DataFrame，列名必须与训练时一致
    final_dataframe = pd.DataFrame([feature_values], columns=feature_names)

    return final_dataframe


@app.route('/')
def start():
    """网站首页：显示开始页面"""
    if model is None:
        error_message = "模型未正确加载，无法进行预测，请联系管理员处理"
        return render_template('start.html', error=error_message)
    return render_template('start.html')
  # 这里没有error参数，前端error变量不存在

# 2. 问卷页路由：显示问卷
@app.route('/questionnaire')
def questionnaire():
    """问卷页面：显示问卷内容"""
    if model is None:
        error_message = "模型未正确加载，无法进行预测，请联系管理员处理"
        return render_template('index.html', error=error_message)
    return render_template('index.html')


@app.route('/predict', methods=['POST'])
def predict():
    """处理表单提交，进行计算和预测"""
    # 检查模型是否已加载
    if model is None:
        error_message = "模型未正确加载，无法进行预测"
        return render_template('index.html', error=error_message)

    # 1. 获取前端传来的109道题的答案
    answers = request.form

    # 2. 调用函数，根据答案计算28个特征
    try:
        input_features_df = calculate_features(answers)
    except Exception as e:
        # 如果计算过程出错，跳回首页并显示错误
        error_message = f"处理问卷答案时发生错误: {str(e)}"
        return render_template('index.html', error=error_message)

    # 3. 用计算好的特征进行预测
    try:
        prediction = model.predict(input_features_df)
        result = prediction[0]  # 获取单个预测结果
        if result > 4 :
            result = 4.00
        # 根据您的需求格式化结果
        result = int(result * 100) / 100.0 # 保留2位小数
    except Exception as e:
        error_message = f"模型预测时发生错误: {str(e)}"
        return render_template('index.html', error=error_message)

    # 4. 跳转到结果页面，并传递预测结果
    return render_template('result.html', prediction=result)


@app.route('/new-assessment')
def new_assessment():
    """提供一个清空问卷的入口"""
    # 重定向到首页，由于是全新请求，表单是空的
    return redirect(url_for('questionnaire', new=True))



if __name__ == '__main__':
    app.run(debug=True)