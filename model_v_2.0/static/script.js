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

    // ========== 自定义模态弹窗系统 ==========

    // 创建模态弹窗的DOM结构
    function createModalStructure() {
        // 检查是否已存在
        if (document.getElementById('incomplete-modal')) return;

        const modalHTML = `
            <div id="incomplete-modal" class="modal-overlay">
                <div class="modal-container">
                    <div class="modal-header">
                        <div class="modal-icon">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                                <line x1="12" y1="9" x2="12" y2="13"></line>
                                <line x1="12" y1="17" x2="12.01" y2="17"></line>
                            </svg>
                        </div>
                        <h2 class="modal-title">您还有问卷题目尚未完成</h2>
                    </div>
                    <div class="modal-body">
                        <p class="modal-subtitle">请先完成所有问题再提交，以下是未完成的题目：</p>
                        <div class="modal-list-container">
                            <ul id="incomplete-list" class="modal-list"></ul>
                        </div>
                        <p class="modal-hint">点击确认后将自动跳转到最前面一道未完成题目所在页面</p>
                    </div>
                    <div class="modal-footer">
                        <button id="modal-confirm-btn" class="modal-btn">确认</button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);

        // 绑定确认按钮事件
        document.getElementById('modal-confirm-btn').addEventListener('click', closeModalAndNavigate);

        // 点击遮罩层不关闭（强制用户点击确认）
        document.getElementById('incomplete-modal').addEventListener('click', function(e) {
            if (e.target === this) {
                // 轻微抖动提示用户需要点击确认
                const container = this.querySelector('.modal-container');
                container.classList.add('modal-shake');
                setTimeout(() => container.classList.remove('modal-shake'), 400);
            }
        });
    }

    // 存储第一个未完成页面（用于跳转）
    let firstIncompletePage = 1;

    // 显示模态弹窗
    function showIncompleteModal(incompleteQuestions, firstPage) {
        createModalStructure();
        firstIncompletePage = firstPage;

        const modal = document.getElementById('incomplete-modal');
        const list = document.getElementById('incomplete-list');

        // 清空列表
        list.innerHTML = '';

        // 填充未完成题目
        incompleteQuestions.forEach((item, index) => {
            const li = document.createElement('li');
            li.className = 'modal-list-item';

            let locationText = '';
            if (item.page === 9) {
                locationText = `位于第${item.page}页${item.sectionInfo}的第${item.sectionQuestionNum}题未完成`;
            } else {
                locationText = `位于第${item.page}页的第一部分的第${item.sectionQuestionNum}题未完成`;
            }

            li.innerHTML = `
                <span class="item-number">${index + 1}.</span>
                <span class="item-text">${locationText}</span>
            `;
            list.appendChild(li);
        });

        // 显示弹窗
        modal.classList.add('modal-visible');
        document.body.style.overflow = 'hidden'; // 禁止背景滚动

        // 添加入场动画
        setTimeout(() => {
            modal.querySelector('.modal-container').classList.add('modal-animate-in');
        }, 10);
    }

    // 关闭弹窗并跳转
    function closeModalAndNavigate() {
        const modal = document.getElementById('incomplete-modal');
        const container = modal.querySelector('.modal-container');

        // 退出动画
        container.classList.remove('modal-animate-in');
        container.classList.add('modal-animate-out');

        setTimeout(() => {
            modal.classList.remove('modal-visible');
            container.classList.remove('modal-animate-out');
            document.body.style.overflow = ''; // 恢复滚动

            // 跳转到第一个未完成页面
            goToPage(firstIncompletePage);
        }, 200);
    }

    // ========== 分页导航与数据持久化 ==========

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
        const isNewAssessment = window.location.search.includes('new=true');
        const isFromStartPage = document.referrer.includes('/start');

        if (isNewAssessment || isFromStartPage) {
            // 双重保险：再清空一次数据
            Object.keys(localStorage).forEach(key => {
                if (key.startsWith('q')) {
                    localStorage.removeItem(key);
                }
            });
            return;
        }

        // 只有非新评估，才加载保存的答案
        loadSavedAnswers();
    }

    // 更新导航按钮状态
    function updateNavigation() {
        currentPageSpan.textContent = currentPage;

        if (currentPage === 1) {
            prevBtn.classList.add('hidden');
        } else {
            prevBtn.classList.remove('hidden');
        }

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

        saveCurrentPageAnswers();

        pages.forEach(page => {
            page.classList.add('hidden');
        });

        const targetPage = document.getElementById(`page-${pageNumber}`);
        targetPage.classList.remove('hidden');

        currentPage = pageNumber;
        updateNavigation();
        loadSavedAnswers();

        // 智能滚动：检查目标页是否有未完成的题目
        setTimeout(() => {
            const firstUnanswered = findFirstUnansweredQuestion(pageNumber);
            if (firstUnanswered) {
                // 有未完成题目，滚动到该题目位置（留出一点上边距）
                const offset = firstUnanswered.getBoundingClientRect().top + window.pageYOffset - 100;
                window.scrollTo({ top: offset, behavior: 'smooth' });
            }
            // 如果该页全部完成，则不滚动，保持当前位置
        }, 50);
    }

    // 查找指定页面第一个未回答的题目元素
    function findFirstUnansweredQuestion(pageNumber) {
        const pageElement = document.getElementById(`page-${pageNumber}`);
        const questions = pageElement.querySelectorAll('.question');

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
                return question; // 返回第一个未回答的题目元素
            }
        }

        return null; // 该页全部完成
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

    // 清除localStorage中的问卷数据
    function clearAssessmentData() {
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
                    question: i + 1 + (currentPage - 1) * 12
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
                    const globalQuestionNum = j + 1 + (i - 1) * 12;
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
                        sectionInfo = '第一部分';
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
            return {
                complete: false,
                questions: incompleteQuestions,
                firstIncompletePage: incompleteQuestions[0].page
            };
        }

        return { complete: true };
    }

    // ========== 事件绑定 ==========

    // 上一页
    prevBtn.addEventListener('click', function() {
        goToPage(currentPage - 1);
    });

    // 下一页
    nextBtn.addEventListener('click', function() {
        goToPage(currentPage + 1);
    });

    // 提交表单：先检查是否全部完成
    form.addEventListener('submit', function(e) {
        const result = isAllPagesComplete();
        if (!result.complete) {
            e.preventDefault();

            // 使用自定义模态弹窗替代原生alert
            showIncompleteModal(result.questions, result.firstIncompletePage);
        } else {
            // 提交前保存所有答案
            for (let i = 1; i <= totalPages; i++) {
                const pageElement = document.getElementById(`page-${i}`);
                const inputs = pageElement.querySelectorAll('input[type="radio"]:checked');

                inputs.forEach(input => {
                    localStorage.setItem(input.name, input.value);
                });
            }
        }
    });

    // 初始化页面
    initializePages();
});