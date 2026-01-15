const fs = require("fs");
const path = require("path");
const { resolveChipAppId } = require("./utils.cjs");

// 获取当前文件所在目录
const currentFile = process.argv[1];
const currentDir = path.dirname(currentFile);

// 读取配置文件
const configPath = path.join(currentDir, "config.json");
const config = JSON.parse(fs.readFileSync(configPath, "utf-8"));

/**
 * 查询芯片技术手册
 * @param {Object} params - 查询参数
 * @param {string} params.chip - 芯片型号（如 V32G410x）
 * @param {string} params.query - 查询问题
 * @returns {Promise<Object>} 返回查询结果
 */
module.exports = async function queryChipManual({ chip, query }) {
  // 验证参数
  if (!chip || !query) {
    return {
      success: false,
      answer: "❌ 参数错误：需要提供芯片型号 (chip) 和查询问题 (query)"
    };
  }

  // 解析芯片对应的 appId
  const chipConfig = config[chip];
  if (!chipConfig) {
    const availableChips = Object.keys(config).join(", ");
    return {
      success: false,
      answer: `❌ 未找到芯片 ${chip} 对应的知识库。\n\n当前支持的芯片型号：${availableChips}\n\n请检查芯片型号拼写或在 config.json 中添加新的芯片配置。`
    };
  }

  // 从芯片配置中获取 API 配置
  const baseUrl = chipConfig.apiBase;
  const apiKey = chipConfig.apiKey;
  const appId = chipConfig.appId;

  if (!baseUrl || !apiKey || !appId) {
    return {
      success: false,
      answer: `❌ 配置错误：芯片 ${chip} 的配置中缺少 apiBase、apiKey 或 appId`
    };
  }

  console.log(`🔍 正在查询 ${chip} 手册：${query}`);

  try {
    // 构建 FastGPT 请求
    const url = `${baseUrl}/v1/chat/completions`;
    const body = {
      chatId: `claude_query_${chip}_${Date.now()}`,
      appId,
      stream: false, // 禁用流式输出
      messages: [
        { 
          role: "system", 
          content: "你是一名专业的 MCU 技术手册助手。请基于技术手册提供准确、详细的答案。" 
        },
        { 
          role: "user", 
          content: `芯片型号：${chip}\n查询问题：${query}` 
        }
      ]
    };

    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${apiKey}`
      },
      body: JSON.stringify(body),
      timeout: 300000 // 300秒超时
    });

    if (!response.ok) {
      const errorText = await response.text();
      return { 
        success: false,
        answer: `❌ FastGPT API 请求失败：\n状态码：${response.status} ${response.statusText}\n详情：${errorText}` 
      };
    }

    // 解析响应
    const data = await response.json();
    
    // 提取答案文本
    let answer = data.data?.text || data.text || JSON.stringify(data, null, 2);
    
    // 添加来源标识
    const chipInfo = config[Object.keys(config).find(k => k.toLowerCase() === chip.toLowerCase())];
    const footer = `\n\n---\n📖 数据来源：${chipInfo?.description || chip + ' 技术手册'}`;
    
    console.log(`✅ 查询成功`);
    
    return { 
      success: true,
      answer: answer + footer,
      metadata: {
        chip,
        appId,
        timestamp: new Date().toISOString()
      }
    };

  } catch (error) {
    console.error(`❌ 查询失败:`, error);
    return { 
      success: false,
      answer: `❌ 查询过程中发生错误：${error.message}\n\n请检查：\n1. FastGPT 服务是否正常运行\n2. 网络连接是否正常\n3. API 配置是否正确` 
    };
  }
}

// 如果直接运行此文件（用于测试）
if (require.main === module) {
  const testChip = process.argv[2] || "V32G410x";
  const testQuery = process.argv[3] || "UART1 配置寄存器说明";

  console.log(`🧪 测试模式：查询 ${testChip} - ${testQuery}`);
  const queryChipManual = module.exports;
  queryChipManual({ chip: testChip, query: testQuery })
    .then(result => console.log(JSON.stringify(result, null, 2)))
    .catch(err => console.error(err));
}