/**
 * 芯片匹配工具函数
 */

/**
 * 解析芯片型号对应的 FastGPT appId
 * @param {string} chip - 芯片型号（不区分大小写）
 * @param {Object} config - 配置对象
 * @returns {string|null} 返回 appId 或 null
 */
function resolveChipAppId(chip, config) {
  if (!chip || !config) {
    return null;
  }

  // 不区分大小写匹配
  const normalizedChip = chip.trim().toLowerCase();
  const key = Object.keys(config).find(k => k.toLowerCase() === normalizedChip);

  return key ? config[key].appId : null;
}

/**
 * 从用户问题中提取芯片型号
 * @param {string} text - 用户输入的文本
 * @param {Object} config - 配置对象
 * @returns {string|null} 返回识别到的芯片型号或 null
 */
function extractChipFromText(text, config) {
  if (!text || !config) {
    return null;
  }

  const normalizedText = text.toLowerCase();

  // 遍历所有已配置的芯片型号
  for (const chipName of Object.keys(config)) {
    if (normalizedText.includes(chipName.toLowerCase())) {
      return chipName;
    }
  }

  return null;
}

/**
 * 验证芯片型号是否支持
 * @param {string} chip - 芯片型号
 * @param {Object} config - 配置对象
 * @returns {boolean} 是否支持该芯片
 */
function isChipSupported(chip, config) {
  return resolveChipAppId(chip, config) !== null;
}

/**
 * 获取所有支持的芯片列表
 * @param {Object} config - 配置对象
 * @returns {Array<Object>} 芯片列表
 */
function getSupportedChips(config) {
  return Object.entries(config).map(([name, info]) => ({
    name,
    appId: info.appId,
    description: info.description
  }));
}

/**
 * 格式化芯片信息为可读文本
 * @param {Object} config - 配置对象
 * @returns {string} 格式化的芯片列表
 */
function formatChipList(config) {
  const chips = getSupportedChips(config);
  return chips.map(chip => `- ${chip.name}: ${chip.description}`).join('\n');
}

module.exports = {
  resolveChipAppId,
  extractChipFromText,
  isChipSupported,
  getSupportedChips,
  formatChipList
};