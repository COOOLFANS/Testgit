const form = document.getElementById('recommendation-form');
const weatherInput = document.getElementById('weather');
const temperatureInput = document.getElementById('temperature');
const windInput = document.getElementById('wind');
const submitButton = form.querySelector('.submit-button');

const placeholder = document.getElementById('result-placeholder');
const recommendationPanel = document.getElementById('recommendation');
const outfitEl = document.getElementById('outfit');
const accessoriesList = document.getElementById('accessories');
const accessoriesBlock = document.getElementById('accessories-block');
const tipsList = document.getElementById('tips');
const tipsBlock = document.getElementById('tips-block');
const summaryWeather = document.getElementById('summary-weather');
const summaryTemperature = document.getElementById('summary-temperature');
const summaryWind = document.getElementById('summary-wind');

const errorElements = new Map(
  Array.from(document.querySelectorAll('.error-message')).map((el) => [
    el.dataset.errorFor,
    el,
  ]),
);

const quickButtons = document.querySelectorAll('.quick-tags button');
quickButtons.forEach((button) => {
  button.addEventListener('click', () => {
    weatherInput.value = button.dataset.weather ?? '';
    weatherInput.focus();
  });
});

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  clearErrors();
  toggleLoading(true);

  const payload = {
    weather: weatherInput.value.trim(),
    temperature: temperatureInput.value.trim(),
    windSpeed: windInput.value.trim(),
  };

  if (!payload.temperature) {
    payload.temperature = null;
  }
  if (!payload.windSpeed) {
    payload.windSpeed = null;
  }

  try {
    const response = await fetch('/api/recommend', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    if (!response.ok || !data.success) {
      displayErrors(data.errors || { general: '请求失败，请稍后重试。' });
      showPlaceholder(
        data.errors?.general || data.errors?.weather || '请检查输入后再试一次。',
      );
      return;
    }

    renderRecommendation(data.data);
  } catch (error) {
    console.error(error);
    displayErrors({ general: '网络连接异常，请稍后重试。' });
    showPlaceholder('网络连接异常，请稍后重试。');
  } finally {
    toggleLoading(false);
  }
});

function renderRecommendation(data) {
  if (!data) {
    showPlaceholder('暂时无法获取建议，请稍后再试。');
    return;
  }

  placeholder.hidden = true;
  recommendationPanel.hidden = false;

  summaryWeather.textContent = weatherInput.value.trim() || '—';

  if (data.outfit) {
    outfitEl.textContent = data.outfit;
  } else {
    outfitEl.textContent = '暂无建议';
  }

  const temperatureValue = temperatureInput.value.trim();
  const windValue = windInput.value.trim();

  if (temperatureValue) {
    summaryTemperature.textContent = `${temperatureValue}°C`;
    summaryTemperature.hidden = false;
  } else {
    summaryTemperature.hidden = true;
  }

  if (windValue) {
    summaryWind.textContent = `${windValue} m/s`;
    summaryWind.hidden = false;
  } else {
    summaryWind.hidden = true;
  }

  renderList(accessoriesList, accessoriesBlock, data.accessories);
  renderList(tipsList, tipsBlock, data.tips);
}

function renderList(listEl, wrapperEl, items) {
  listEl.innerHTML = '';
  if (!items || items.length === 0) {
    wrapperEl.hidden = true;
    return;
  }

  items.forEach((item) => {
    const li = document.createElement('li');
    li.textContent = item;
    listEl.appendChild(li);
  });
  wrapperEl.hidden = false;
}

function showPlaceholder(message) {
  placeholder.hidden = false;
  recommendationPanel.hidden = true;
  placeholder.querySelector('p').textContent = message;
}

function displayErrors(errors) {
  if (!errors) return;

  Object.entries(errors).forEach(([key, message]) => {
    if (key === 'general') {
      placeholder.querySelector('p').textContent = message;
      return;
    }

    const errorEl = errorElements.get(key);
    if (errorEl) {
      errorEl.textContent = message;
    }
  });
}

function clearErrors() {
  errorElements.forEach((el) => {
    el.textContent = '';
  });
}

function toggleLoading(isLoading) {
  submitButton.disabled = isLoading;
  submitButton.textContent = isLoading ? '生成中…' : '生成穿搭';
}
