## 禅道链接
- Bug来源：{{ZENTAO_BUG_URL}}

---

## 1. Bug描述（问题现象）

### 1.1 环境信息
| 项目 | 内容 |
|------|------|
| 地区/项目 | {{AREA_OR_PROJECT}} |
| 软件版本 | {{SOFTWARE_VERSION}} |
| 硬件版本 | {{HARDWARE_VERSION}} |
| 测试环境 | {{TEST_ENV}} |

### 1.2 重现步骤
1. {{STEP_1}}
2. {{STEP_2}}
3. {{STEP_3}}

### 1.3 期望结果
{{EXPECTED_RESULT}}

### 1.4 实际结果
{{ACTUAL_RESULT}}

### 1.5 影响评估
- 影响范围：{{IMPACT_SCOPE}}
- 影响对象：{{IMPACT_TARGET}}
- 风险等级：{{RISK_LEVEL}}

### 1.6 相关日志/报文
```text
{{RAW_LOG_OR_FRAME}}
```

---

## 2. Bug原因分析（Root Cause）

### 2.1 根本原因
{{ROOT_CAUSE}}

### 2.2 直接原因
{{DIRECT_CAUSE}}

### 2.3 问题代码位置
- 文件：`{{FILE_PATH}}`
- 函数：`{{FUNCTION_NAME}}`
- 说明：{{CODE_LOCATION_NOTE}}

### 2.4 为什么之前没有发现
从以下角度明确检讨，不要空话：
- 需求/协议理解是否有偏差：{{MISSED_REASON_REQUIREMENT}}
- 设计阶段是否遗漏边界条件：{{MISSED_REASON_DESIGN}}
- 开发自测是否缺少异常/边界场景：{{MISSED_REASON_SELF_TEST}}
- 联调或测试阶段为什么未提前暴露：{{MISSED_REASON_INTEGRATION_TEST}}

### 2.5 责任检讨与经验教训
{{LESSON_LEARNED}}

---

## 3. 解决方案

### 3.1 修复思路
{{FIX_STRATEGY}}

### 3.2 代码修改点
1. {{CHANGE_POINT_1}}
2. {{CHANGE_POINT_2}}
3. {{CHANGE_POINT_3}}

### 3.3 为什么这样修
{{WHY_THIS_FIX}}

### 3.4 是否有副作用评估
- 兼容性：{{COMPATIBILITY_IMPACT}}
- 关联功能影响：{{RELATED_FEATURE_IMPACT}}
- 是否涉及协议行为变化：{{PROTOCOL_BEHAVIOR_IMPACT}}

### 3.5 已完成验证
- 静态检查：{{STATIC_CHECK_RESULT}}
- 构建结果：{{BUILD_RESULT}}
- 代码自测：{{SELF_TEST_RESULT}}

---

## 4. 给测试人员的黑盒测试建议

> 这里要站在测试人员视角写，不写代码内部实现，强调“怎么测、看什么、判定标准是什么”。

| 序号 | 测试目的 | 前置条件 | 操作步骤 | 预期结果 | 判定标准 |
|------|----------|----------|----------|----------|----------|
| 1 | 验证正常场景 | {{PRECONDITION_1}} | {{TEST_STEP_1}} | {{EXPECTED_1}} | {{PASS_CRITERIA_1}} |
| 2 | 验证边界场景 | {{PRECONDITION_2}} | {{TEST_STEP_2}} | {{EXPECTED_2}} | {{PASS_CRITERIA_2}} |
| 3 | 验证异常输入 | {{PRECONDITION_3}} | {{TEST_STEP_3}} | {{EXPECTED_3}} | {{PASS_CRITERIA_3}} |
| 4 | 验证回归影响 | {{PRECONDITION_4}} | {{TEST_STEP_4}} | {{EXPECTED_4}} | {{PASS_CRITERIA_4}} |

### 4.1 必测边界项
- 最小值：{{BOUNDARY_MIN}}
- 临界值：{{BOUNDARY_EDGE}}
- 越界值：{{BOUNDARY_OVERFLOW}}
- 回归项：{{REGRESSION_ITEMS}}

---

## 5. 后续改进与预防措施

### 5.1 代码层面
{{CODE_IMPROVEMENT}}

### 5.2 测试层面
{{TEST_IMPROVEMENT}}

### 5.3 流程层面
{{PROCESS_IMPROVEMENT}}

### 5.4 文档层面
{{DOC_IMPROVEMENT}}

---

## 6. 责任人与流转
| 角色 | 人员 |
|------|------|
| Bug提出人 | {{REPORTER}} |
| Bug定位人 | {{LOCATOR}} |
| 修复人 | {{FIXER}} |
| 验证人 | {{VERIFIER}} |
| 解决后转派给 | {{PROJECT_OWNER}} |
