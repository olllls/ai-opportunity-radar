// AI机会雷达 - 前端交互
(function() {
    'use strict';

    // 自动关闭提示消息
    document.querySelectorAll('.alert-auto-close').forEach(el => {
        setTimeout(() => {
            el.style.transition = 'opacity 0.5s';
            el.style.opacity = '0';
            setTimeout(() => el.remove(), 500);
        }, 5000);
    });

    // 表单提交禁用按钮（防止重复提交）
    document.querySelectorAll('form[data-disable-on-submit]').forEach(form => {
        form.addEventListener('submit', function() {
            const btn = this.querySelector('button[type="submit"]');
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = '处理中...';
            }
        });
    });

    // 确认对话框
    document.querySelectorAll('[data-confirm]').forEach(el => {
        el.addEventListener('click', function(e) {
            if (!confirm(this.dataset.confirm)) {
                e.preventDefault();
            }
        });
    });

    // 复制文本到剪贴板
    document.querySelectorAll('[data-copy]').forEach(el => {
        el.addEventListener('click', function() {
            const text = this.dataset.copy;
            navigator.clipboard.writeText(text).then(() => {
                const tip = this.querySelector('.copy-tip');
                if (tip) {
                    tip.textContent = '已复制!';
                    setTimeout(() => { tip.textContent = '复制'; }, 2000);
                }
            });
        });
    });

    // 自动刷新日志页面
    const logPage = document.getElementById('log-page');
    if (logPage) {
        const interval = parseInt(logPage.dataset.refreshInterval || '30');
        setTimeout(() => { window.location.reload(); }, interval * 1000);
    }

})();
