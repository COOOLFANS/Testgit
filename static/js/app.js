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

const forecastStatus = document.getElementById('forecast-status');
const forecastList = document.getElementById('forecast-list');
const refreshForecastButton = document.getElementById('refresh-forecast');

if (refreshForecastButton) {
  refreshForecastButton.addEventListener('click', () => {
    requestAutoForecast(true);
  });
}

initAutoForecast();

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

function initAutoForecast() {
  if (!forecastStatus || !forecastList) {
    return;
  }

  if (!('geolocation' in navigator)) {
    updateForecastStatus('当前浏览器不支持定位功能，请使用表单获取建议。', true);
    if (refreshForecastButton) {
      refreshForecastButton.disabled = true;
    }
    return;
  }

  requestAutoForecast(false);
}

function requestAutoForecast(isRetry = false) {
  if (!forecastStatus || !forecastList || !('geolocation' in navigator)) {
    return;
  }

  forecastList.hidden = true;
  updateForecastStatus(isRetry ? '重新定位中…' : '正在定位…');

  if (refreshForecastButton) {
    refreshForecastButton.disabled = true;
  }

  navigator.geolocation.getCurrentPosition(
    (position) => {
      fetchAutoForecast(position.coords.latitude, position.coords.longitude);
    },
    (error) => {
      console.error(error);
      let message = '定位失败，请稍后再试。';
      if (error.code === error.PERMISSION_DENIED) {
        message = '定位被拒绝，无法自动获取天气。';
      }
      updateForecastStatus(message, true);
      if (refreshForecastButton) {
        refreshForecastButton.disabled = false;
      }
    },
    {
      enableHighAccuracy: false,
      timeout: 10000,
      maximumAge: 30 * 60 * 1000,
    },
  );
}

async function fetchAutoForecast(latitude, longitude) {
  if (!forecastStatus || !forecastList) {
    return;
  }

  updateForecastStatus('正在获取 7 天天气与穿搭建议…');

  try {
    const response = await fetch('/api/auto-forecast', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ latitude, longitude }),
    });

    const payload = await response.json();

    if (!response.ok || !payload.success) {
      const message =
        payload?.errors?.general || '天气服务暂时不可用，请稍后再试。';
      updateForecastStatus(message, true);
      return;
    }

    renderForecastDays(payload.data);
  } catch (error) {
    console.error(error);
    updateForecastStatus('获取天气数据失败，请稍后重试。', true);
  } finally {
    if (refreshForecastButton) {
      refreshForecastButton.disabled = false;
    }
  }
}

function renderForecastDays(data) {
  if (!forecastList) {
    return;
  }

  forecastList.innerHTML = '';

  if (!data || !Array.isArray(data.days) || data.days.length === 0) {
    updateForecastStatus('暂无可用的预报信息。', true);
    forecastList.hidden = true;
    return;
  }

  data.days.forEach((day) => {
    forecastList.appendChild(createForecastItem(day));
  });

  forecastList.hidden = false;

  const timezone = data.location?.timezone;
  if (timezone) {
    updateForecastStatus(`已基于你的位置（${timezone}）生成未来 7 天的穿搭建议。`);
  } else {
    updateForecastStatus('已基于你的位置生成未来 7 天的穿搭建议。');
  }
}

function createForecastItem(day) {
  const item = document.createElement('li');
  item.className = 'forecast-item';

  const header = document.createElement('div');
  header.className = 'forecast-item-header';

  const dateGroup = document.createElement('div');
  dateGroup.className = 'forecast-date-group';

  const dateText = document.createElement('p');
  dateText.className = 'forecast-date';
  dateText.textContent = formatDate(day?.date);
  dateGroup.appendChild(dateText);

  const weatherLine = document.createElement('p');
  weatherLine.className = 'forecast-weather';
  const weatherParts = [];
  if (day?.weather_text) {
    weatherParts.push(day.weather_text);
  }
  const rangeText = formatTemperatureRange(day?.temperature_min, day?.temperature_max);
  if (rangeText) {
    weatherParts.push(rangeText);
  }
  weatherLine.textContent = weatherParts.join(' · ');
  dateGroup.appendChild(weatherLine);

  header.appendChild(dateGroup);

  const windText = formatWind(day?.wind_speed);
  if (windText) {
    const wind = document.createElement('span');
    wind.className = 'forecast-wind';
    wind.textContent = windText;
    header.appendChild(wind);
  }

  item.appendChild(header);

  const recommendation = day?.recommendation || {};

  const outfit = document.createElement('p');
  outfit.className = 'forecast-outfit';
  outfit.textContent =
    recommendation.outfit || '暂无穿搭建议，请稍后再试。';
  item.appendChild(outfit);

  const accessoriesText = formatList(recommendation.accessories, '、');
  if (accessoriesText) {
    const accessories = document.createElement('p');
    accessories.className = 'forecast-extra';
    accessories.innerHTML = `<span class="forecast-extra-label">搭配：</span>${accessoriesText}`;
    item.appendChild(accessories);
  }

  const tipsText = formatList(recommendation.tips, '；');
  if (tipsText) {
    const tips = document.createElement('p');
    tips.className = 'forecast-extra';
    tips.innerHTML = `<span class="forecast-extra-label">提示：</span>${tipsText}`;
    item.appendChild(tips);
  }

  return item;
}

function updateForecastStatus(message, isError = false) {
  if (!forecastStatus) {
    return;
  }

  forecastStatus.textContent = message;
  forecastStatus.classList.toggle('is-error', Boolean(isError));
}

function formatDate(value) {
  if (!value) {
    return '日期待定';
  }

  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  try {
    return new Intl.DateTimeFormat('zh-CN', {
      month: 'numeric',
      day: 'numeric',
      weekday: 'short',
    }).format(date);
  } catch (error) {
    console.error(error);
    return value;
  }
}

function formatTemperatureRange(min, max) {
  const minText = formatTemperature(min);
  const maxText = formatTemperature(max);

  if (minText && maxText) {
    return `${maxText} / ${minText}`;
  }
  return maxText || minText || '';
}

function formatTemperature(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return '';
  }
  return `${Math.round(number)}°C`;
}

function formatWind(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return '';
  }
  return `最大风速 ${Math.round(number)} m/s`;
}

function formatList(items, separator) {
  if (!Array.isArray(items) || items.length === 0) {
    return '';
  }
  return items.join(separator);
}
