let allCities = [];

async function loadCities() {
    try {
        const response = await fetch("/api/cities");
        const data = await response.json();
        
        if (data.success) {
            allCities = data.cities;
            displayCities(allCities);
        }
    } catch (error) {
        console.error("加载城市列表失败：", error);
        document.getElementById("cities-grid").innerHTML = 
            '<p style="text-align:center; color:#6b7280;">加载失败，请刷新页面重试</p>';
    }
}

function displayCities(cities) {
    const grid = document.getElementById("cities-grid");
    
    if (cities.length === 0) {
        grid.innerHTML = '<p style="text-align:center; color:#6b7280;">未找到城市</p>';
        return;
    }
    
    grid.innerHTML = cities.map(city => `
        <div class="city-card" onclick="viewCityDetail('${city.id}')">
            <img src="${city.image}" alt="${city.name}" class="city-card-image">
            <div class="city-card-content">
                <h3>${city.name}</h3>
                <p class="city-province">${city.province}</p>
                <p class="city-description">${city.description}</p>
                <div class="city-highlights">
                    ${city.highlights.slice(0, 2).map(h => `<span>${h.name}</span>`).join('')}
                </div>
            </div>
        </div>
    `).join('');
}

function viewCityDetail(cityId) {
    window.location.href = `/city/${cityId}`;
}

async function searchCities() {
    const keyword = document.getElementById("search-input").value.trim();
    
    if (!keyword) {
        displayCities(allCities);
        return;
    }
    
    try {
        const response = await fetch(`/api/search-cities?keyword=${encodeURIComponent(keyword)}`);
        const data = await response.json();
        
        if (data.success) {
            displayCities(data.cities);
        }
    } catch (error) {
        console.error("搜索城市失败：", error);
    }
}

document.addEventListener("DOMContentLoaded", function() {
    loadCities();
});