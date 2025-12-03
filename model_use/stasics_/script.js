document.addEventListener('DOMContentLoaded', function() {
    // 页面元素
    const form = document.getElementById('questionnaire-form');
    const pages = document.querySelectorAll('.page');
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const submitBtn = document.getElementById('submit-btn');
    const currentPageSpan = document.getElementById('current-page');

    let currentPage = 1;
    const totalPages = pages.length;

    // 初始化：显示第一页，隐藏其他页
    function initializePages() {
        pages.forEach((page, index) => {
            if (index === 0) {
                page.classList.remove('hidden');
            } else {
                page.classList.add('hidden');
            }
        });
        updateNavigation();
        // 只有当不是从重新开始按钮进入时才加载保存的答案
        // 可以通过URL参数判断是否是新评估
        // 关键修改：如果是新评估，先清空数据，再强制不加载答案
        const isNewAssessment = window.location.search.includes('new=true');
        const isFromStartPage = document.referrer.includes('/start');

        if (isNewAssessment || isFromStartPage) {
            // 双重保险：再清空一次数据（防止结果页清空失败）
            Object.keys(localStorage).forEach(key => {
                if (key.startsWith('q')) {
                    localStorage.removeItem(key);
                }
            });
            // 不加载任何答案（即使有残留也不读）
            return;
        }

        // 只有非新评估，才加载保存的答案
        loadSavedAnswers();


    }

    // 更新导航按钮状态
    function updateNavigation() {
        // 更新页码显示
        currentPageSpan.textContent = currentPage;

        // 显示/隐藏上一页按钮
        if (currentPage === 1) {
            prevBtn.classList.add('hidden');
        } else {
            prevBtn.classList.remove('hidden');
        }

        // 显示/隐藏下一页和提交按钮
        if (currentPage === totalPages) {
            nextBtn.classList.add('hidden');
            submitBtn.classList.remove('hidden');
        } else {
            nextBtn.classList.remove('hidden');
            submitBtn.classList.add('hidden');
        }
    }

    // 切换到指定页面
    function goToPage(pageNumber) {
        if (pageNumber < 1 || pageNumber > totalPages) return;

        // 保存当前页面的答案
        saveCurrentPageAnswers();

        // 隐藏所有页面
        pages.forEach(page => {
            page.classList.add('hidden');
        });

        // 显示目标页面
        const targetPage = document.getElementById(`page-${pageNumber}`);
        targetPage.classList.remove('hidden');

        // 更新当前页码
        currentPage = pageNumber;
        updateNavigation();

        // 加载目标页面的保存答案
        loadSavedAnswers();
    }

    // 保存当前页面的答案到localStorage
    function saveCurrentPageAnswers() {
        const currentPageElement = document.getElementById(`page-${currentPage}`);
        const inputs = currentPageElement.querySelectorAll('input[type="radio"]:checked');

        inputs.forEach(input => {
            localStorage.setItem(input.name, input.value);
        });
    }

    // 从localStorage加载保存的答案
    function loadSavedAnswers() {
        const currentPageElement = document.getElementById(`page-${currentPage}`);
        const inputs = currentPageElement.querySelectorAll('input[type="radio"]');

        inputs.forEach(input => {
            const savedValue = localStorage.getItem(input.name);
            if (savedValue && input.value === savedValue) {
                input.checked = true;
            }
        });
    }

    function clearAssessmentData() {
        // 清除localStorage中保存的所有问卷答案
        Object.keys(localStorage).forEach(key => {
            if (key.startsWith('q')) {
                localStorage.removeItem(key);
            }
        });
    }


    // 检查当前页面所有问题是否已回答
    function isCurrentPageComplete() {
        const currentPageElement = document.getElementById(`page-${currentPage}`);
        const questions = currentPageElement.querySelectorAll('.question');

        for (let i = 0; i < questions.length; i++) {
            const question = questions[i];
            const inputs = question.querySelectorAll('input[type="radio"]');
            let answered = false;

            for (let j = 0; j < inputs.length; j++) {
                if (inputs[j].checked) {
                    answered = true;
                    break;
                }
            }

            if (!answered) {
                return {
                    complete: false,
                    question: i + 1 + (currentPage - 1) * 12 // 计算全局题号
                };
            }
        }

        return { complete: true };
    }

    // 检查所有页面是否完成
    function isAllPagesComplete() {

        const incompleteQuestions = [];

        for (let i = 1; i <= totalPages; i++) {
            const pageElement = document.getElementById(`page-${i}`);
            const questions = pageElement.querySelectorAll('.question');

            for (let j = 0; j < questions.length; j++) {
                const question = questions[j];
                const inputs = question.querySelectorAll('input[type="radio"]');
                let answered = false;

                for (let k = 0; k < inputs.length; k++) {
                    if (inputs[k].checked) {
                        answered = true;
                        break;
                    }
                }

                if (!answered) {
                // 计算全局题号
                    const globalQuestionNum = j + 1 + (i - 1) * 12;
                    // 确定题目所在部分（根据你的分段逻辑）
                let sectionInfo = '';
                let sectionQuestionNum = 0;

                // 处理第9页的特殊分段
                if (i === 9) {
                    if (globalQuestionNum < 97) {
                        sectionInfo = '第一部分';
                        sectionQuestionNum = globalQuestionNum - (9-1)*12;
                    } else if (globalQuestionNum >= 97 && globalQuestionNum < 99) {
                        sectionInfo = '第二部分';
                        sectionQuestionNum = globalQuestionNum - 96;
                    } else if (globalQuestionNum >= 99 && globalQuestionNum < 104) {
                        sectionInfo = '第三部分';
                        sectionQuestionNum = globalQuestionNum - 98;
                    } else if (globalQuestionNum >= 104 && globalQuestionNum < 108) {
                        sectionInfo = '第四部分';
                        sectionQuestionNum = globalQuestionNum - 103;
                    } else if (globalQuestionNum >= 108 && globalQuestionNum < 110) {
                        sectionInfo = '第五部分';
                        sectionQuestionNum = globalQuestionNum - 107;
                    } else if (globalQuestionNum >= 110) {
                        sectionInfo = '第六部分';
                        sectionQuestionNum = globalQuestionNum - 109;
                    }
                } else {
                    // 非第9页，直接使用页面内题号
                    sectionInfo = '第一部分'; // 其他页默认第一部分
                    sectionQuestionNum = j + 1;
                }
                    incompleteQuestions.push({
                        page: i,
                        globalQuestionNum: globalQuestionNum,
                        sectionInfo: sectionInfo,
                        sectionQuestionNum: sectionQuestionNum
                    });
                }
            }
        }

        if (incompleteQuestions.length > 0) {
        // 返回所有未完成的题目
            return {
                complete: false,
                questions: incompleteQuestions,
                firstIncompletePage: incompleteQuestions[0].page // 第一个未完成题目的页面
            };
        }

        return { complete: true };
    }

    // 事件监听器
    //本人觉得不完成不让翻页有点离谱，所以不启用该功能。
    prevBtn.addEventListener('click', function() {
//        const result = isCurrentPageComplete();
//        if (result.complete) {
            goToPage(currentPage - 1);
//        } else {
//            alert(`请先完成第${result.question}题再继续。`);
//        }
    });

    nextBtn.addEventListener('click', function() {
//        const result = isCurrentPageComplete();
//        if (result.complete) {
            goToPage(currentPage + 1);
//        } else {
//            alert(`请先完成第${result.question}题再继续。`);
//        }
    });

    form.addEventListener('submit', function(e) {
        const result = isAllPagesComplete();
        if (!result.complete) {
            e.preventDefault();

            // 构建未完成题目提示信息
            let alertMessage = "当前有以下题目尚未完成，请先完成所有问题再提交：\n";


            // 遍历所有未完成题目，添加到提示信息中
            result.questions.forEach((item, index) => {
                if (item.page === 9) {
                    // 第9页的特殊格式
                    alertMessage += `${index + 1}. 位于第${item.page}页${item.sectionInfo}的第${item.sectionQuestionNum}题未完成。\n`;
                } else {
                    // 其他页的格式
                    alertMessage += `${index + 1}. 位于第${item.page}页的第一部分的第${item.sectionQuestionNum}题未完成。\n`;
                }
            });

            alertMessage += "将自动为您跳转到最前面一道未完成题目所在页面。\n"

            // 显示所有未完成题目
            alert(alertMessage);


            goToPage(result.firstIncompletePage);

        } else {
            // 提交前保存所有答案
            for (let i = 1; i <= totalPages; i++) {
                const pageElement = document.getElementById(`page-${i}`);
                const inputs = pageElement.querySelectorAll('input[type="radio"]:checked');

                inputs.forEach(input => {
                    localStorage.setItem(input.name, input.value);
                });
            }
            // 可以在这里添加表单提交前的其他处理
        }
    });

    // 初始化页面
    initializePages();
});