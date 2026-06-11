async function sendMessage(){

    let input = document.getElementById("user-input")

    let message = input.value

    if(message.trim() === ""){
        return
    }

    let chatBox = document.getElementById("chat-box")

    // 用户消息
    chatBox.innerHTML += `

    <div class="message user-message">

        <div class="bubble user-bubble">
            ${message}
        </div>

        <div class="avatar user-avatar">我</div>

    </div>

    `

    try{

        const response = await fetch("/chat",{

            method:"POST",

            headers:{
                "Content-Type":"application/json"
            },

            body:JSON.stringify({
                message:message
            })
        })

        const data = await response.json()

        // AI消息
        chatBox.innerHTML += `

        <div class="message ai-message">

            <div class="avatar ai-avatar">AI</div>

            <div class="bubble ai-bubble">
                ${data.reply}
            </div>

        </div>

        `

        // 更新历史会话列表
        loadRecentConversations()

    }catch(error){

        chatBox.innerHTML += `

        <div class="message ai-message">

            <div class="avatar ai-avatar">AI</div>

            <div class="bubble ai-bubble">
                系统连接失败
            </div>

        </div>

        `
    }

    input.value = ""

    chatBox.scrollTop = chatBox.scrollHeight
}

// 页面加载时恢复对话历史
async function loadConversationHistory() {
    try {
        const response = await fetch("/conversation-history", {
            method: "GET"
        });
        const data = await response.json();
        
        if (data.history && data.history.length > 0) {
            let chatBox = document.getElementById("chat-box");
            chatBox.innerHTML = "";
            
            data.history.forEach(item => {
                if (item.role === "user") {
                    chatBox.innerHTML += `
                    <div class="message user-message">
                        <div class="bubble user-bubble">
                            ${item.content}
                        </div>
                        <div class="avatar user-avatar">我</div>
                    </div>
                    `;
                } else {
                    chatBox.innerHTML += `
                    <div class="message ai-message">
                        <div class="avatar ai-avatar">AI</div>
                        <div class="bubble ai-bubble">
                            ${item.content}
                        </div>
                    </div>
                    `;
                }
            });
            
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    } catch (error) {
        console.error("加载对话历史失败:", error);
    }
}

// 加载最近会话列表
async function loadRecentConversations() {
    try {
        const response = await fetch("/recent-conversations", {
            method: "GET"
        });
        const data = await response.json();
        
        let historyList = document.getElementById("history-list");
        
        if (data.conversations && data.conversations.length > 0) {
            historyList.innerHTML = "";
            
            data.conversations.forEach(item => {
                let historyItem = document.createElement("div");
                historyItem.className = "history-item";
                historyItem.setAttribute("data-date", item.date);
                historyItem.onclick = function() {
                    loadConversationByDate(item.date);
                };
                
                // 格式化日期显示
                let dateStr = formatDate(item.date);
                
                historyItem.innerHTML = `
                    <div class="history-date">${dateStr}</div>
                    <div class="history-preview">${item.preview}</div>
                    <div class="history-count">${item.message_count} 条消息</div>
                `;
                
                historyList.appendChild(historyItem);
            });
        } else {
            historyList.innerHTML = '<div style="color:#6b7280; text-align:center; padding:10px;">暂无历史对话</div>';
        }
    } catch (error) {
        console.error("加载最近会话失败:", error);
    }
}

// 按日期加载会话
async function loadConversationByDate(dateStr) {
    try {
        const response = await fetch(`/conversation-by-date?date=${dateStr}`, {
            method: "GET"
        });
        const data = await response.json();
        
        let chatBox = document.getElementById("chat-box");
        
        if (data.history && data.history.length > 0) {
            chatBox.innerHTML = "";
            
            data.history.forEach(item => {
                if (item.role === "user") {
                    chatBox.innerHTML += `
                    <div class="message user-message">
                        <div class="bubble user-bubble">
                            ${item.content}
                        </div>
                        <div class="avatar user-avatar">我</div>
                    </div>
                    `;
                } else {
                    chatBox.innerHTML += `
                    <div class="message ai-message">
                        <div class="avatar ai-avatar">AI</div>
                        <div class="bubble ai-bubble">
                            ${item.content}
                        </div>
                    </div>
                    `;
                }
            });
            
            chatBox.scrollTop = chatBox.scrollHeight;
            
            // 更新选中状态
            document.querySelectorAll('.history-item').forEach(item => {
                item.classList.remove('active');
            });
            document.querySelector(`[data-date="${dateStr}"]`).classList.add('active');
        }
    } catch (error) {
        console.error("加载指定日期会话失败:", error);
    }
}

// 格式化日期
function formatDate(dateStr) {
    const date = new Date(dateStr);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    
    if (dateStr === today.toISOString().split('T')[0]) {
        return '今天';
    } else if (dateStr === yesterday.toISOString().split('T')[0]) {
        return '昨天';
    } else {
        const month = date.getMonth() + 1;
        const day = date.getDate();
        return `${month}月${day}日`;
    }
}

// 清空对话历史
async function clearConversation() {
    if (confirm("确定要清空所有对话历史吗？")) {
        try {
            const response = await fetch("/clear-conversation", {
                method: "POST"
            });
            const data = await response.json();
            
            if (data.success) {
                let chatBox = document.getElementById("chat-box");
                chatBox.innerHTML = `
                <div class="message ai-message">
                    <div class="avatar ai-avatar">AI</div>
                    <div class="bubble ai-bubble">
                        你好，我是旅游计划生成助手，可以帮你规划旅游路线、查询天气以及记录旅游偏好。
                    </div>
                </div>
                `;
                
                // 更新历史会话列表
                loadRecentConversations();
            }
        } catch (error) {
            console.error("清空对话历史失败:", error);
        }
    }
}

// 键盘事件监听
document.getElementById("user-input").addEventListener("keyup", function(event) {
    if (event.key === "Enter") {
        sendMessage();
    }
});

// 页面加载完成后自动加载对话历史和会话列表
document.addEventListener("DOMContentLoaded", function() {
    loadConversationHistory();
    loadRecentConversations();
});