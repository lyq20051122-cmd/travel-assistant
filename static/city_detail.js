async function loadCityDetail() {
    try {
        const response = await fetch(`/api/city/${cityId}`);
        const data = await response.json();
        
        if (data.success && data.city) {
            const city = data.city;
            
            document.getElementById("city-name").textContent = city.name;
            document.getElementById("city-province").textContent = city.province;
            document.getElementById("city-title").textContent = city.name;
            document.getElementById("city-description").textContent = city.description;
            document.getElementById("city-image").src = city.image;
            document.getElementById("city-image").alt = city.name;
            
            document.getElementById("best-time").textContent = city.best_time;
            document.getElementById("culture").textContent = city.culture;
            document.getElementById("transport").textContent = city.transport;
            
            // 生成景点列表（带点击链接）
            const highlightsList = document.getElementById("highlights-list");
            highlightsList.innerHTML = city.highlights.map(h => `
                <li style="cursor: pointer; padding: 8px 12px; border-radius: 8px; transition: background 0.3s;" 
                    onclick="showAttractionDetail('${h.id}')" 
                    onmouseenter="this.style.background='#f3f4f6'" 
                    onmouseleave="this.style.background='transparent'">
                    <span>${h.icon}</span> 
                    <strong>${h.name}</strong>
                    <span style="color: #6b7280; font-size: 14px;">- ${h.desc}</span>
                    <span style="float: right; color: #6366f1; font-size: 12px;">点击查看详情 →</span>
                </li>
            `).join('');
            
            const foodList = document.getElementById("food-list");
            foodList.innerHTML = city.food.map(f => `<li>${f}</li>`).join('');
            
            // 保存景点数据供弹窗使用
            window.cityAttractions = city.attractions || {};
            
        } else {
            document.getElementById("city-name").textContent = "城市不存在";
            document.getElementById("city-description").textContent = "未找到该城市的信息";
        }
    } catch (error) {
        console.error("加载城市详情失败：", error);
        document.getElementById("city-name").textContent = "加载失败";
    }
}

function showAttractionDetail(attractionId) {
    const attraction = window.cityAttractions[attractionId];
    if (!attraction) return;
    
    // 构建可选字段的HTML
    const optionalFields = [];
    if (attraction.best_time) {
        optionalFields.push(`
            <div class="info-item">
                <span class="info-icon">🌸</span>
                <span class="info-label">最佳时间：</span>
                <span>${attraction.best_time}</span>
            </div>
        `);
    }
    if (attraction.duration) {
        optionalFields.push(`
            <div class="info-item">
                <span class="info-icon">⏱️</span>
                <span class="info-label">游玩时长：</span>
                <span>${attraction.duration}</span>
            </div>
        `);
    }
    if (attraction.nearby && attraction.nearby.length > 0) {
        optionalFields.push(`
            <div class="info-item">
                <span class="info-icon">📍</span>
                <span class="info-label">周边景点：</span>
                <span>${attraction.nearby.join('、')}</span>
            </div>
        `);
    }
    if (attraction.suitable_for && attraction.suitable_for.length > 0) {
        optionalFields.push(`
            <div class="info-item">
                <span class="info-icon">👥</span>
                <span class="info-label">适合人群：</span>
                <span>${attraction.suitable_for.join('、')}</span>
            </div>
        `);
    }
    
    // 构建景点详情HTML
    const html = `
        <div class="attraction-detail">
            <h3>${attraction.name}</h3>
            <div class="attraction-rating">
                <span>⭐ ${attraction.rating}</span>
            </div>
            <p class="attraction-desc">${attraction.description}</p>
            <div class="attraction-info">
                <div class="info-item">
                    <span class="info-icon">📍</span>
                    <span class="info-label">地址：</span>
                    <span>${attraction.location}</span>
                </div>
                <div class="info-item">
                    <span class="info-icon">💰</span>
                    <span class="info-label">门票：</span>
                    <span>${attraction.price}</span>
                </div>
                <div class="info-item">
                    <span class="info-icon">⏰</span>
                    <span class="info-label">开放时间：</span>
                    <span>${attraction.opening_hours}</span>
                </div>
                <div class="info-item">
                    <span class="info-icon">🚇</span>
                    <span class="info-label">交通路线：</span>
                    <span>${attraction.route}</span>
                </div>
                ${optionalFields.join('')}
                <div class="info-item">
                    <span class="info-icon">💡</span>
                    <span class="info-label">游玩提示：</span>
                    <span>${attraction.tips}</span>
                </div>
            </div>
        </div>
    `;
    
    // 创建弹窗
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content">
            <button class="modal-close" onclick="closeModal()">×</button>
            ${html}
        </div>
    `;
    
    document.body.appendChild(modal);
    modal.style.display = 'block';
    
    // 点击遮罩关闭
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeModal();
        }
    });
}

function closeModal() {
    const modal = document.querySelector('.modal-overlay');
    if (modal) {
        modal.remove();
    }
}

function goBack() {
    window.location.href = "/cities";
}

document.addEventListener("DOMContentLoaded", function() {
    loadCityDetail();
});