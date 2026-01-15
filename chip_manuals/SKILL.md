---
name: chip-manuals
description: Lookup MCU reference manual details (registers, peripherals, clocks, interrupts, DMA, GPIO, timers) for supported chips such as RN7326.
---

# Chip Manuals Query Skill

这个 Skill 允许 Claude 通过 FastGPT 知识库查询 MCU 芯片的技术手册信息。

## 支持的芯片型号

当前支持以下芯片：
- **RN7326** - 芯片参考手册


## 何时使用此 Skill

当用户询问以下内容时，自动使用此 Skill：
- 特定芯片的寄存器配置方法
- 外设模块（UART、SPI、I2C、ADC 等）的初始化流程
- 时钟树配置和频率计算
- 中断向量表和优先级设置
- DMA 配置和传输模式
- GPIO 引脚功能和复用配置
- 定时器工作模式和参数设置
- 任何需要查阅芯片技术手册的问题

## 使用方法

### 自动调用
当用户提问包含芯片型号和技术问题时，Claude 会自动识别并调用此 Skill。

**示例触发场景：**
```
用户: "RN7326 的 UART1 怎么配置？"
用户: "RN7326 的 ADC 采样率如何设置？"
用户: "RN7326 的时钟树配置流程是什么？"
用户: "RN7326 的串口API有哪些？"
```

### 执行流程

1. **识别芯片型号**：从用户问题中提取芯片型号
2. **匹配知识库**：根据 `config.json` 查找对应的 appId
3. **调用 FastGPT**：发送查询请求到 FastGPT API
4. **返回结果**：将技术手册中的相关内容返回给用户

### 调用函数

```javascript
// Claude 会自动调用此函数
const result = await queryChipManual({
  chip: "RN7326",    // 芯片型号
  query: "UART1配置"   // 查询问题
});
```


### 添加新芯片
在 `config.json` 中添加新的芯片映射：
```json
{
  "NEW_CHIP": {
    "appId": "chip_new_chip_manual",
    "description": "NEW_CHIP 芯片参考手册"
  }
}
```

## 执行脚本

此 Skill 使用 `request.cjs` 作为主执行脚本，包含：
- FastGPT API 调用逻辑
- 错误处理机制
- 芯片型号匹配算法

## 返回格式

返回的信息包括：
- ✅ 技术手册中的准确内容
- ✅ 寄存器地址和位域说明
- ✅ 配置步骤和示例代码
- ❌ 如果芯片型号不支持，会返回提示信息

## 最佳实践

### 提问技巧
- **具体明确**：指明芯片型号和具体问题
  - ✅ "RN7326 的 UART1 波特率寄存器如何配置？"
  - ❌ "UART 怎么用？"

- **包含上下文**：说明使用场景
  - ✅ "RN7326 配置 ADC 进行 DMA 连续采样"
  - ❌ "ADC 配置"

### Claude 处理流程
1. 检测到芯片型号关键词（RN7326、STM32F407）
2. 识别技术手册相关的查询意图
3. 自动调用 `request.cjs` 查询 FastGPT
4. 整合返回的技术文档内容
5. 用清晰的格式呈现给用户

## 故障排查

如果 Skill 未被调用：
- 确认芯片型号拼写正确
- 确认问题与技术手册相关
- 检查环境变量是否配置
- 查看 `config.json` 中是否有对应映射

## 注意事项

⚠️ **安全性**：
- 此 Skill 会调用外部 API，请确保 FastGPT 服务可信
- API Key 包含在配置中，请勿分享此 Skill 目录

⚠️ **准确性**：
- 返回内容基于 FastGPT 知识库的准确性
- 建议核对官方技术手册确认关键参数

⚠️ **网络依赖**：
- 需要能访问 FastGPT API 服务
- 网络故障时会返回错误提示

⚠️ **执行环境**：
- 运行时请使用非沙盒环境，并允许最大权限
