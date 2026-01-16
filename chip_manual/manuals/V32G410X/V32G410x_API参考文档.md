# V32G410x API 参考文档

基于 `./Inc` 目录下头文件接口定义生成的完整 API 参考文档。

## 概述

V32G410x 是一款基于 ARM Cortex-M 内核的 32 位微控制器，本文档提供所有外设模块的详细 API 接口说明，包括函数参数含义、使用方法和实际开发示例。文档严格按照头文件定义生成，确保信息的准确性和实用性，可直接用于嵌入式程序开发。

**使用说明：**
- 所有函数都需要先配置相应的外设时钟
- 使用前请先调用初始化函数进行配置
- 参数值需使用头文件中定义的常量枚举
- 返回值类型：void表示无返回值，其他类型表示具体的返回值

## 目录

- [配置模块 (lib_conf.h)](#配置模块-lib_confh)
- [USART/UART 串口模块 (lib_usart.h)](#usartuart-串口模块-lib_usarth)
- [看门狗模块 (lib_wwdg.h, lib_iwdg.h)](#看门狗模块-lib_wwdgh-lib_iwdgh)
- [中断和系统控制 (misc.h)](#中断和系统控制-misch)
- [定时器模块 (lib_tim.h)](#定时器模块-lib_timh)
- [实时时钟模块 (lib_rtc.h)](#实时时钟模块-lib_rtch)
- [SPI 通信模块 (lib_spi.h)](#spi-通信模块-lib_spih)
- [I2C 通信模块 (lib_i2c.h)](#i2c-通信模块-lib_i2ch)
- [外部中断模块 (lib_exti.h)](#外部中断模块-lib_extih)
- [DMA 模块 (lib_dma.h)](#dma-模块-lib_dmah)
- [CRC 校验模块 (lib_crc.h)](#crc-校验模块-lib_crch)
- [备份寄存器模块 (lib_bkp.h)](#备份寄存器模块-lib_bkph)
- [时钟控制模块 (lib_rcc.h)](#时钟控制模块-lib_rcch)
- [电源管理模块 (lib_pwr.h)](#电源管理模块-lib_pwrh)
- [调试模块 (lib_dbgmcu.h)](#调试模块-lib_dbgmcuh)
- [CAN 总线模块 (lib_can.h)](#can-总线模块-lib_canh)
- [ADC 模数转换模块 (lib_adc.h)](#adc-模数转换模块-lib_adch)
- [Flash 存储模块 (lib_flash.h)](#flash-存储模块-lib_flashh)
- [GPIO 通用输入输出模块 (lib_gpio.h)](#gpio-通用输入输出模块-lib_gpioh)

---

## 配置模块 (lib_conf.h)

### 模块说明
库配置文件，包含所有外设头文件的包含和断言配置。此模块是整个库的入口，包含了所有外设驱动的头文件引用，确保编译时包含所有必要的外设定义。

### 主要宏定义
- `ASSERT_ENABLED`: 断言功能启用开关（默认注释掉）。启用后会在关键函数调用时进行参数检查，便于调试。

### 包含的外设模块
- **通信接口**: ADC, BKP, CAN, CRC, DBGMCU, DMA, EXTI, FLASH
- **输入输出**: GPIO, I2C, IWDG, PWR, RCC, RTC, SPI, TIM
- **串口通信**: USART, WWDG, MISC (NVIC 和 SysTick 高级功能)

### 使用方法
在项目中直接包含此头文件即可使用所有外设功能：
```c
#include "lib_conf.h"
// 然后可以使用所有外设的API函数
```

---

## USART/UART 串口模块 (lib_usart.h)

### 模块说明
通用同步/异步收发器(USART)模块提供串行通信功能，支持同步、异步、LIN、智能卡等模式。包含8个USART/UART外设：USART1-3、USART6和UART4-5、UART7-8。

### 数据结构

#### USART_InitType
USART初始化结构体，配置串口的基本参数。
| 成员 | 类型 | 描述 | 示例值 |
|------|------|------|--------|
| USART_BaudRate | uint32_t | 通信波特率 | 9600, 115200 |
| USART_WordLength | uint16_t | 数据位长度 (8位/9位) | USART_WordLength_8b |
| USART_StopBits | uint16_t | 停止位数量 (1/0.5/2/1.5位) | USART_StopBits_1 |
| USART_Parity | uint16_t | 奇偶校验模式 | USART_Parity_None |
| USART_Mode | uint16_t | 发送/接收模式 | USART_Mode_Rx \| USART_Mode_Tx |
| USART_HardwareFlowControl | uint16_t | 硬件流控模式 | USART_HardwareFlowControl_None |

#### USART_ClockInitType
USART时钟初始化结构体，用于同步模式时钟配置。
| 成员 | 类型 | 描述 | 示例值 |
|------|------|------|--------|
| USART_Clock | uint16_t | 时钟使能状态 | DISABLE |
| USART_CPOL | uint16_t | 时钟极性 (高/低电平空闲) | USART_CPOL_Low |
| USART_CPHA | uint16_t | 时钟相位 (第一个/第二个边沿捕获) | USART_CPHA_1Edge |
| USART_LastBit | uint16_t | 最后位时钟输出 | DISABLE |

### 主要函数接口

#### 初始化和控制函数
| 函数名 | 参数说明 | 返回值 | 描述 | 使用示例 |
|--------|----------|--------|------|----------|
| USART_Reset() | **USARTx**: USART外设指针 (USART1/USART2等) | void | 复位指定USART到默认状态 | USART_Reset(USART1); |
| USART_Init() | **USARTx**: USART外设指针<br>**USART_InitStruct**: 初始化结构体指针 | void | 根据结构体参数初始化USART | USART_Init(USART1, &usartInit); |
| USART_StructInit() | **USART_InitStruct**: 初始化结构体指针 | void | 初始化结构体为默认值 (9600, 8N1) | USART_StructInit(&usartInit); |
| USART_ClockInit() | **USARTx**: USART外设指针<br>**USART_ClockInitStruct**: 时钟初始化结构体指针 | void | 配置同步模式时钟 | USART_ClockInit(USART1, &clockInit); |
| USART_Cmd() | **USARTx**: USART外设指针<br>**NewState**: 使能状态 (ENABLE/DISABLE) | void | 使能/禁用USART | USART_Cmd(USART1, ENABLE); |

#### 数据传输函数
| 函数名 | 参数说明 | 返回值 | 描述 | 使用示例 |
|--------|----------|--------|------|----------|
| USART_SendData() | **USARTx**: USART外设指针<br>**Data**: 要发送的数据 (0-0x1FF) | void | 发送一个数据字节 | USART_SendData(USART1, 0x55); |
| USART_ReceiveData() | **USARTx**: USART外设指针 | uint16_t | 接收一个数据字节 | uint16_t data = USART_ReceiveData(USART1); |
| USART_SendBreak() | **USARTx**: USART外设指针 | void | 发送中断信号 (LIN模式) | USART_SendBreak(USART1); |

#### 配置函数
| 函数名 | 参数说明 | 返回值 | 描述 | 使用示例 |
|--------|----------|--------|------|----------|
| USART_SetAddress() | **USARTx**: USART外设指针<br>**USART_Address**: USART地址 (0-15) | void | 设置USART的节点地址 | USART_SetAddress(USART1, 0x01); |
| USART_WakeUpConfig() | **USARTx**: USART外设指针<br>**USART_WakeUp**: 唤醒模式 (USART_WakeUp_IdleLine/USART_WakeUp_AddressMark) | void | 配置USART唤醒模式 | USART_WakeUpConfig(USART1, USART_WakeUp_IdleLine); |
| USART_LINBreakDetectLengthConfig() | **USARTx**: USART外设指针<br>**USART_LINBreakDetectLength**: LIN中断检测长度 (LIN_BreakDetectLength_10b/LIN_BreakDetectLength_11b) | void | 配置LIN中断检测长度 | USART_LINBreakDetectLengthConfig(USART1, LIN_BreakDetectLength_10b); |
| USART_SetGuardTime() | **USARTx**: USART外设指针<br>**USART_GuardTime**: 保护时间值 (0-255) | void | 设置智能卡模式保护时间 | USART_SetGuardTime(USART1, 0x10); |
| USART_SetPrescaler() | **USARTx**: USART外设指针<br>**USART_Prescaler**: 预分频器值 (0-255) | void | 设置智能卡模式预分频器 | USART_SetPrescaler(USART1, 0x01); |

#### 中断和DMA函数
| 函数名 | 参数说明 | 返回值 | 描述 | 使用示例 |
|--------|----------|--------|------|----------|
| USART_INTConfig() | **USARTx**: USART外设指针<br>**USART_INT**: 中断类型<br>**NewState**: 使能状态 | void | 配置USART中断 | USART_INTConfig(USART1, USART_INT_RXNE, ENABLE); |
| USART_DMACmd() | **USARTx**: USART外设指针<br>**USART_DMAReq**: DMA请求类型<br>**NewState**: 使能状态 | void | 配置DMA请求 | USART_DMACmd(USART1, USART_DMAReq_Tx, ENABLE); |

#### 状态查询函数
| 函数名 | 参数说明 | 返回值 | 描述 | 使用示例 |
|--------|----------|--------|------|----------|
| USART_GetFlagStatus() | **USARTx**: USART外设指针<br>**USART_FLAG**: 标志类型 | FlagStatus | 获取标志状态 (SET/RESET) | if(USART_GetFlagStatus(USART1, USART_FLAG_RXNE) == SET) |
| USART_ClearFlag() | **USARTx**: USART外设指针<br>**USART_FLAG**: 标志类型 | void | 清除指定标志 | USART_ClearFlag(USART1, USART_FLAG_RXNE); |
| USART_GetITStatus() | **USARTx**: USART外设指针<br>**USART_INT**: 中断类型 | ITStatus | 获取中断状态 (SET/RESET) | if(USART_GetITStatus(USART1, USART_INT_RXNE) == SET) |
| USART_ClearITPendingBit() | **USARTx**: USART外设指针<br>**USART_INT**: 中断类型 | void | 清除中断待处理位 | USART_ClearITPendingBit(USART1, USART_INT_RXNE); |

### 常量定义

#### 数据位长度
- `USART_WordLength_8b`: 8位数据长度 (标准)
- `USART_WordLength_9b`: 9位数据长度 (包含校验位)

#### 停止位
- `USART_StopBits_1`: 1个停止位 (标准)
- `USART_StopBits_0_5`: 0.5个停止位
- `USART_StopBits_2`: 2个停止位
- `USART_StopBits_1_5`: 1.5个停止位

#### 奇偶校验
- `USART_Parity_No`: 无校验 (常用)
- `USART_Parity_Even`: 偶校验
- `USART_Parity_Odd`: 奇校验

#### 模式 (可位或组合)
- `USART_Mode_Rx`: 接收模式
- `USART_Mode_Tx`: 发送模式
- 组合使用: `USART_Mode_Rx | USART_Mode_Tx`

#### 硬件流控
- `USART_HardwareFlowControl_None`: 无流控 (常用)
- `USART_HardwareFlowControl_RTS`: RTS流控
- `USART_HardwareFlowControl_CTS`: CTS流控
- `USART_HardwareFlowControl_RTS_CTS`: RTS+CTS流控

#### 常用中断类型
- `USART_INT_TXE`: 发送数据寄存器空中断
- `USART_INT_TC`: 发送完成中断
- `USART_INT_RXNE`: 接收数据寄存器非空中断
- `USART_INT_IDLE`: 空闲总线中断

#### 常用状态标志
- `USART_FLAG_TXE`: 发送数据寄存器空标志
- `USART_FLAG_TC`: 发送完成标志
- `USART_FLAG_RXNE`: 接收数据寄存器非空标志
- `USART_FLAG_IDLE`: 空闲总线标志
- `USART_FLAG_ORE`: 接收溢出错误标志

#### 支持的USART外设
- **USART**: USART1, USART2, USART3, USART6
- **UART**: UART4, UART5, UART7, UART8

### 使用示例
```c
// 基本串口通信配置示例
void USART1_Init_Example(void)
{
    USART_InitType USART_InitStructure;
    GPIO_InitType GPIO_InitStructure;

    // 1. 使能时钟
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_USART1, ENABLE);
    RCC_AHBPeriphClockCmd(RCC_AHBPeriph_GPIOA, ENABLE);

    // 2. 配置GPIO (PA9-TX, PA10-RX)
    GPIO_InitStructure.GPIO_Pins = GPIO_Pins_9;
    GPIO_InitStructure.GPIO_MaxSpeed = GPIO_MaxSpeed_50MHz;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP;
    GPIO_Init(GPIOA, &GPIO_InitStructure);

    GPIO_InitStructure.GPIO_Pins = GPIO_Pins_10;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN_FLOATING;
    GPIO_Init(GPIOA, &GPIO_InitStructure);

    // 3. 配置USART
    USART_InitStructure.USART_BaudRate = 115200;
    USART_InitStructure.USART_WordLength = USART_WordLength_8b;
    USART_InitStructure.USART_StopBits = USART_StopBits_1;
    USART_InitStructure.USART_Parity = USART_Parity_No;
    USART_InitStructure.USART_Mode = USART_Mode_Rx | USART_Mode_Tx;
    USART_InitStructure.USART_HardwareFlowControl = USART_HardwareFlowControl_None;
    USART_Init(USART1, &USART_InitStructure);

    // 4. 使能USART
    USART_Cmd(USART1, ENABLE);
}

// 发送字符串函数
void USART1_SendString(char* str)
{
    while(*str)
    {
        // 等待发送缓冲区空
        while(USART_GetFlagStatus(USART1, USART_FLAG_TXE) == RESET);
        USART_SendData(USART1, *str++);
    }
    // 等待发送完成
    while(USART_GetFlagStatus(USART1, USART_FLAG_TC) == RESET);
}
```

---

## 看门狗模块 (lib_wwdg.h, lib_iwdg.h)

### 模块说明
看门狗模块用于系统监控，包含两种类型的看门狗：
- **窗口看门狗 (WWDG)**: 需要在指定时间窗口内喂狗，过早或过晚喂狗都会触发复位
- **独立看门狗 (IWDG)**: 独立于主时钟，使用内部低速时钟LSI，只要在超时前喂狗即可

### 窗口看门狗 (WWDG)

窗口看门狗使用APB1时钟，具有可配置的时间窗口，必须在最小值和最大值之间喂狗。

#### 主要函数接口
| 函数名 | 参数说明 | 返回值 | 描述 | 使用示例 |
|--------|----------|--------|------|----------|
| WWDG_Reset() | 无 | void | 复位窗口看门狗到初始状态 | WWDG_Reset(); |
| WWDG_SetPrescaler() | **WWDG_Prescaler**: 预分频器值 (WWDG_Psc_1/2/4/8) | void | 设置预分频器，决定计数器时钟频率 | WWDG_SetPrescaler(WWDG_Psc_8); |
| WWDG_SetWindowCounter() | **WindowValue**: 窗口值 (0x40-0x7F) | void | 设置窗口计数器值，喂狗必须在大于此值时进行 | WWDG_SetWindowCounter(0x50); |
| WWDG_EnableINT() | 无 | void | 使能提前唤醒中断 (EWI) | WWDG_EnableINT(); |
| WWDG_SetCounter() | **Counter**: 计数器值 (0x40-0x7F) | void | 设置计数器值 (喂狗操作) | WWDG_SetCounter(0x7F); |
| WWDG_Enable() | **Counter**: 计数器值 (0x40-0x7F) | void | 使能看门狗并设置初始计数器值 | WWDG_Enable(0x7F); |
| WWDG_GetFlagStatus() | 无 | FlagStatus | 获取提前唤醒中断标志状态 | if(WWDG_GetFlagStatus() == SET) |
| WWDG_ClearFlag() | 无 | void | 清除提前唤醒中断标志 | WWDG_ClearFlag(); |

#### 预分频器常量
- `WWDG_Psc_1`: 1分频 (最快)
- `WWDG_Psc_2`: 2分频
- `WWDG_Psc_4`: 4分频
- `WWDG_Psc_8`: 8分频 (最慢)

#### 超时时间计算
超时时间 = (T_pclk1 × 4096 × 预分频器 × (计数器初始值 - 窗口值)) / 时钟频率

### 独立看门狗 (IWDG)

独立看门狗使用内部40kHz低速时钟LSI，不受主时钟影响，可靠性高。

#### 主要函数接口
| 函数名 | 参数说明 | 返回值 | 描述 | 使用示例 |
|--------|----------|--------|------|----------|
| IWDG_KeyRegWrite() | **IWDG_WriteAccess**: 写访问密钥 (IWDG_WriteAccess_Enable/Disable) | void | 写访问密钥寄存器，允许修改看门狗配置 | IWDG_KeyRegWrite(IWDG_WriteAccess_Enable); |
| IWDG_SetPrescaler() | **IWDG_Prescaler**: 预分频器 (IWDG_Psc_4到IWDG_Psc_256) | void | 设置预分频器，决定计数器递减频率 | IWDG_SetPrescaler(IWDG_Psc_32); |
| IWDG_SetReload() | **Reload**: 重载值 (0-0xFFF) | void | 设置重载值，计数器归零时重新加载的值 | IWDG_SetReload(0xFFF); |
| IWDG_ReloadCounter() | 无 | void | 重载计数器 (喂狗操作) | IWDG_ReloadCounter(); |
| IWDG_Enable() | 无 | void | 使能看门狗，一旦使能无法禁用 | IWDG_Enable(); |
| IWDG_GetFlagStatus() | **IWDG_FLAG**: 标志类型 (IWDG_FLAG_PVU/IWDG_FLAG_RVU) | FlagStatus | 获取预分频器更新或重载值更新标志 | if(IWDG_GetFlagStatus(IWDG_FLAG_PVU) == RESET) |

#### 预分频器常量
- `IWDG_Psc_4`: 4分频 (最快)
- `IWDG_Psc_8`: 8分频
- `IWDG_Psc_16`: 16分频
- `IWDG_Psc_32`: 32分频
- `IWDG_Psc_64`: 64分频
- `IWDG_Psc_128`: 128分频
- `IWDG_Psc_256`: 256分频 (最慢)

#### 超时时间计算
超时时间 = (LSI时钟周期 × 预分频器 × 重载值) ≈ (1/40000 × 预分频器 × 重载值) 秒

#### 写访问密钥常量
- `IWDG_WriteAccess_Enable`: 0x5555 - 允许修改寄存器
- `IWDG_WriteAccess_Disable`: 0x0000 - 禁止修改寄存器

#### 状态标志常量
- `IWDG_FLAG_PVU`: 预分频器更新标志
- `IWDG_FLAG_RVU`: 重载值更新标志

### 使用示例

#### 窗口看门狗示例
```c
// WWDG配置示例 - 超时约26ms (Pclk1=36MHz)
void WWDG_Config_Example(void)
{
    // 使能时钟
    RCC_APB1PeriphClockCmd(RCC_APB1Periph_WWDG, ENABLE);

    // 设置预分频器 (Pclk1/8/4096 = 1099Hz)
    WWDG_SetPrescaler(WWDG_Psc_8);

    // 设置窗口值 (计数器值必须大于0x50时才能喂狗)
    WWDG_SetWindowCounter(0x50);

    // 使能提前唤醒中断
    WWDG_EnableINT();

    // 使能看门狗，计数器从0x7F开始递减
    WWDG_Enable(0x7F);

    // 配置中断
    NVIC_EnableIRQ(WWDG_IRQn);
}

// 喂狗函数 (必须在计数器值 > 0x50时调用)
void WWDG_Feed_Dog(void)
{
    if(WWDG_GetCounter() > 0x50)  // 检查是否在时间窗口内
    {
        WWDG_SetCounter(0x7F);   // 喂狗
    }
}

// WWDG中断处理函数
void WWDG_IRQHandler(void)
{
    if(WWDG_GetFlagStatus() == SET)
    {
        WWDG_ClearFlag();  // 清除中断标志
        // 执行提前唤醒操作
        // 注意：这里不能喂狗，因为还未到窗口时间
    }
}
```

#### 独立看门狗示例
```c
// IWDG配置示例 - 超时约1秒 (LSI=40kHz)
void IWDG_Config_Example(void)
{
    // 1. 写入密钥允许修改寄存器
    IWDG_KeyRegWrite(IWDG_WriteAccess_Enable);

    // 2. 等待预分频器更新标志清零
    while(IWDG_GetFlagStatus(IWDG_FLAG_PVU) == SET);

    // 3. 设置预分频器为32 (40kHz/32 = 1250Hz)
    IWDG_SetPrescaler(IWDG_Psc_32);

    // 4. 等待预分频器更新标志清零
    while(IWDG_GetFlagStatus(IWDG_FLAG_PVU) == SET);

    // 5. 设置重载值为1250 (1250/1250Hz = 1秒)
    IWDG_SetReload(1250);

    // 6. 使能看门狗
    IWDG_Enable();

    // 7. 首次喂狗
    IWDG_ReloadCounter();
}

// 喂狗函数 - 在主循环中定期调用
void IWDG_Feed_Dog(void)
{
    IWDG_ReloadCounter();  // 重载计数器
}
```

### 使用建议
1. **独立看门狗**适用于大多数场景，时钟独立，可靠性高
2. **窗口看门狗**用于需要精确监控程序执行时间的场景
3. 喂狗操作应该在主循环或任务调度器的固定位置执行
4. IWDG一旦使能无法通过软件禁用，只能复位系统
5. WWDG的窗口时间设置要考虑程序的最快和最慢执行时间

---

## 中断和系统控制 (misc.h)

### 模块说明
中断和系统控制模块提供NVIC（嵌套向量中断控制器）和SysTick系统滴答定时器的配置功能。NVIC负责管理ARM Cortex-M内核的中断优先级、使能和禁用，SysTick提供系统时钟基准。

### 数据结构

#### NVIC_InitType
NVIC初始化结构体，配置单个中断通道的参数。
| 成员 | 类型 | 描述 | 示例值 |
|------|------|------|--------|
| NVIC_IRQChannel | uint8_t | IRQ通道号 (中断向量号) | USART1_IRQn (37) |
| NVIC_IRQChannelPreemptionPriority | uint8_t | 抢占优先级 (0-15) | 1 |
| NVIC_IRQChannelSubPriority | uint8_t | 子优先级 (0-15) | 0 |
| NVIC_IRQChannelCmd | FunctionalState | 使能/禁用 (ENABLE/DISABLE) | ENABLE |

### 主要函数接口
| 函数名 | 参数说明 | 返回值 | 描述 | 使用示例 |
|--------|----------|--------|------|----------|
| NVIC_PriorityGroupConfig() | **NVIC_PriorityGroup**: 优先级分组 (NVIC_PriorityGroup_0到_4) | void | 配置中断优先级分组 | NVIC_PriorityGroupConfig(NVIC_PriorityGroup_2); |
| NVIC_Init() | **NVIC_InitStruct**: NVIC初始化结构体指针 | void | 根据结构体参数初始化NVIC中断 | NVIC_Init(&nvicInit); |
| NVIC_SetVectorTable() | **NVIC_VectTab**: 向量表基址<br>**Offset**: 偏移量 | void | 设置中断向量表位置 | NVIC_SetVectorTable(NVIC_VectTab_FLASH, 0x0); |
| NVIC_SystemLPConfig() | **LowPowerMode**: 低功耗模式<br>**NewState**: 使能状态 | void | 系统低功耗配置 | NVIC_SystemLPConfig(SLEEPONEXIT, ENABLE); |
| SysTick_CLKSourceConfig() | **SysTick_CLKSource**: 时钟源选择 | void | SysTick时钟源配置 | SysTick_CLKSourceConfig(SysTick_CLKSource_HCLK); |

### 优先级分组详解
NVIC使用4位来表示中断优先级，分为抢占优先级和子优先级：

| 分组 | 抢占优先级位数 | 子优先级位数 | 描述 |
|------|----------------|--------------|------|
| NVIC_PriorityGroup_0 | 0位 | 4位 | 0级抢占，16级子优先级 |
| NVIC_PriorityGroup_1 | 1位 | 3位 | 2级抢占，8级子优先级 |
| NVIC_PriorityGroup_2 | 2位 | 2位 | 4级抢占，4级子优先级 |
| NVIC_PriorityGroup_3 | 3位 | 1位 | 8级抢占，2级子优先级 |
| NVIC_PriorityGroup_4 | 4位 | 0位 | 16级抢占，0级子优先级 |

**抢占优先级**：数值越小，优先级越高。高抢占优先级可以打断低抢占优先级的中断。
**子优先级**：当抢占优先级相同时，子优先级数值小的先执行，但不能互相打断。

### 向量表基址常量
- `NVIC_VectTab_RAM`: 向量表在RAM中 (0x20000000)
- `NVIC_VectTab_FLASH`: 向量表在Flash中 (0x08000000)

### 低功耗模式常量
- `SLEEPONEXIT`: 退出中断后进入睡眠模式
- `SLEEPDEEP`: 深度睡眠模式

### SysTick时钟源常量
- `SysTick_CLKSource_HCLK_Div8`: HCLK时钟8分频
- `SysTick_CLKSource_HCLK`: HCLK时钟

### 常用IRQ通道常量
系统中常见的中断通道号：
- `WWDG_IRQn`: 0 - 窗口看门狗中断
- `PVD_IRQn`: 1 - 电源电压检测中断
- `RTC_IRQn`: 2 - 实时时钟中断
- `FLASH_IRQn`: 3 - Flash操作中断
- `RCC_CRS_IRQn`: 4 - RCC和CRS中断
- `EXTI0_IRQn`: 6 - EXTI线0中断
- `EXTI1_IRQn`: 7 - EXTI线1中断
- ...
- `USART1_IRQn`: 37 - USART1全局中断
- `USART2_IRQn`: 38 - USART2全局中断
- `USART3_IRQn`: 39 - USART3全局中断
- ...

### 使用示例

#### 基本中断配置示例
```c
// USART1中断配置示例
void USART1_NVIC_Config(void)
{
    NVIC_InitType NVIC_InitStructure;

    // 1. 配置优先级分组 - 2位抢占，2位子优先级
    NVIC_PriorityGroupConfig(NVIC_PriorityGroup_2);

    // 2. 配置NVIC参数
    NVIC_InitStructure.NVIC_IRQChannel = USART1_IRQn;           // USART1中断通道
    NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 1;   // 抢占优先级为1
    NVIC_InitStructure.NVIC_IRQChannelSubPriority = 0;          // 子优先级为0
    NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;              // 使能中断

    // 3. 初始化NVIC
    NVIC_Init(&NVIC_InitStructure);
}

// 中断服务函数
void USART1_IRQHandler(void)
{
    if(USART_GetITStatus(USART1, USART_INT_RXNE) == SET)
    {
        // 处理接收中断
        uint8_t data = USART_ReceiveData(USART1);
        // ... 处理数据
        USART_ClearITPendingBit(USART1, USART_INT_RXNE);
    }

    if(USART_GetITStatus(USART1, USART_INT_TC) == SET)
    {
        // 处理发送完成中断
        USART_ClearITPendingBit(USART1, USART_INT_TC);
    }
}
```

#### SysTick配置示例
```c
// 1ms系统滴答定时器配置
static __IO uint32_t tick = 0;

void SysTick_Init(void)
{
    // 配置SysTick时钟源为HCLK
    SysTick_CLKSourceConfig(SysTick_CLKSource_HCLK);

    // 设置1ms定时 (假设系统时钟72MHz)
    if(SysTick_Config(SystemCoreClock / 1000))
    {
        // 配置失败
        while(1);
    }
}

// SysTick中断处理函数 (在stm32f10x_it.c中)
void SysTick_Handler(void)
{
    tick++;
}

// 获取系统时间
uint32_t Get_Tick(void)
{
    return tick;
}

// 毫秒延时函数
void Delay_ms(uint32_t ms)
{
    uint32_t start_tick = tick;
    while((tick - start_tick) < ms);
}
```

#### 多级中断优先级示例
```c
// 配置不同优先级的中断
void Multi_Level_Interrupt_Config(void)
{
    NVIC_InitType NVIC_InitStructure;

    // 设置优先级分组 - 4位抢占，0位子优先级
    NVIC_PriorityGroupConfig(NVIC_PriorityGroup_4);

    // 高优先级：紧急按键中断
    NVIC_InitStructure.NVIC_IRQChannel = EXTI0_IRQn;  // 假设紧急按键接PA0
    NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 0;  // 最高抢占优先级
    NVIC_InitStructure.NVIC_IRQChannelSubPriority = 0;
    NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;
    NVIC_Init(&NVIC_InitStructure);

    // 中优先级：串口通信中断
    NVIC_InitStructure.NVIC_IRQChannel = USART1_IRQn;
    NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 2;  // 中等抢占优先级
    NVIC_Init(&NVIC_InitStructure);

    // 低优先级：定时器中断
    NVIC_InitStructure.NVIC_IRQChannel = TMR3_IRQn;
    NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 5;  // 较低抢占优先级
    NVIC_Init(&NVIC_InitStructure);
}
```

### 使用建议
1. **优先级分组**应在系统初始化时统一设置，不要在程序运行中修改
2. **中断服务函数**应尽可能简短，复杂处理放在主循环中进行
3. **抢占优先级**用于区分不同功能模块的重要性，如安全相关中断应设为高优先级
4. **子优先级**用于同一模块内的不同中断源区分
5. **SysTick**通常用于系统时钟基准和RTOS心跳
6. 向量表通常放在Flash中，除非需要动态修改中断向量

### 注意事项
1. Cortex-M内核自动将某些异常设为固定优先级（如复位、NMI、硬故障）
2. 中断优先级数值越小，优先级越高
3. 只有在中断使能且优先级足够高时，中断才会被响应
4. 修改中断配置后，建议使用指令隔离栏确保配置生效

---

## 定时器模块 (lib_tim.h)

### 数据结构

#### TMR_TimerBaseInitType
| 成员 | 类型 | 描述 |
|------|------|------|
| TMR_DIV | uint16_t | 预分频器值 |
| TMR_CounterMode | uint32_t | 计数器模式 |
| TMR_Period | uint32_t | 周期值 |
| TMR_ClockDivision | uint16_t | 时钟分频 |
| TMR_RepetitionCounter | uint8_t | 重复计数器值 |

#### TMR_OCInitType
| 成员 | 类型 | 描述 |
|------|------|------|
| TMR_OCMode | uint16_t | 输出比较模式 |
| TMR_OutputState | uint16_t | 输出状态 |
| TMR_OutputNState | uint16_t | 互补输出状态 |
| TMR_Pulse | uint32_t | 脉冲值 |
| TMR_OCPolarity | uint16_t | 输出极性 |
| TMR_OCNPolarity | uint16_t | 互补输出极性 |
| TMR_OCIdleState | uint16_t | 空闲状态 |
| TMR_OCNIdleState | uint16_t | 互补空闲状态 |

#### TMR_ICInitType
| 成员 | 类型 | 描述 |
|------|------|------|
| TMR_Channel | uint16_t | 定时器通道 |
| TMR_ICPolarity | uint16_t | 输入捕获极性 |
| TMR_ICSelection | uint16_t | 输入选择 |
| TMR_ICDIV | uint16_t | 输入捕获分频 |
| TMR_ICFilter | uint16_t | 输入捕获滤波 |

#### TMR_BRKDTInitType
| 成员 | 类型 | 描述 |
|------|------|------|
| TMR_OSIMRState | uint16_t | 运行模式关闭状态选择 |
| TMR_OSIMIState | uint16_t | 空闲模式关闭状态选择 |
| TMR_LOCKgrade | uint16_t | 锁定级别 |
| TMR_DeadTime | uint16_t | 死区时间 |
| TMR_Break | uint16_t | 刹车输入 |
| TMR_BreakPolarity | uint16_t | 刹车极性 |
| TMR_AutomaticOutput | uint16_t | 自动输出 |

### 主要函数接口

#### 基础函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| TMR_Reset() | TMRx | void | 复位定时器 |
| TMR_TimeBaseInit() | TMRx, TMR_TimeBaseInitStruct | void | 时基初始化 |
| TMR_Cmd() | TMRx, NewState | void | 使能/禁用定时器 |
| TMR_SetCounter() | TMRx, Counter | void | 设置计数器值 |
| TMR_SetAutoreload() | TMRx, Autoreload | void | 设置自动重载值 |
| TMR_GetCounter() | TMRx | uint32_t | 获取计数器值 |

#### 输出比较函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| TMR_OC1Init() 到 TMR_OC4Init() | TMRx, TMR_OCInitStruct | void | 输出比较初始化 |
| TMR_SetCompare1() 到 TMR_SetCompare4() | TMRx, Compare1 | void | 设置比较值 |
| TMR_OC1PreloadConfig() 到 TMR_OC4PreloadConfig() | TMRx, TMR_OCPreload | void | 预装载配置 |

#### 输入捕获函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| TMR_ICInit() | TMRx, TMR_ICInitStruct | void | 输入捕获初始化 |
| TMR_PWMIConfig() | TMRx, TMR_ICInitStruct | void | PWM输入配置 |
| TMR_GetCapture1() 到 TMR_GetCapture4() | TMRx | uint32_t | 获取捕获值 |

#### 中断和DMA函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| TMR_INTConfig() | TMRx, TMR_INT, NewState | void | 中断配置 |
| TMR_DMACmd() | TMRx, TMR_DMASource, NewState | void | DMA请求配置 |

#### 状态查询函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| TMR_GetFlagStatus() | TMRx, TMR_FLAG | FlagStatus | 获取标志状态 |
| TMR_ClearFlag() | TMRx, TMR_FLAG | void | 清除标志 |
| TMR_GetINTStatus() | TMRx, TMR_INT | ITStatus | 获取中断状态 |
| TMR_ClearITPendingBit() | TMRx, TMR_INT | void | 清除中断待处理位 |

### 支持的定时器
- 基本定时器: TMR6, TMR7
- 通用定时器: TMR2, TMR3, TMR4, TMR5
- 高级定时器: TMR1, TMR8
- 其他定时器: TMR9, TMR10, TMR11, TMR12, TMR13, TMR14

---

## 实时时钟模块 (lib_rtc.h)

### 主要函数接口
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| RTC_INTConfig() | RTC_INT, NewState | void | 中断配置 |
| RTC_EnterConfigMode() | 无 | void | 进入配置模式 |
| RTC_ExitConfigMode() | 无 | void | 退出配置模式 |
| RTC_GetCounter() | 无 | uint32_t | 获取计数器值 |
| RTC_SetCounter() | CounterValue | void | 设置计数器值 |
| RTC_SetDIV() | PrescalerValue | void | 设置分频器 |
| RTC_SetAlarmValue() | AlarmValue | void | 设置闹钟值 |
| RTC_GetDivider() | 无 | uint32_t | 获取分频器值 |
| RTC_WaitForLastTask() | 无 | void | 等待上次任务完成 |
| RTC_WaitForSynchro() | 无 | void | 等待同步 |

### 状态查询函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| RTC_GetFlagStatus() | RTC_FLAG | FlagStatus | 获取标志状态 |
| RTC_ClearFlag() | RTC_FLAG | void | 清除标志 |
| RTC_GetINTStatus() | RTC_INT | ITStatus | 获取中断状态 |
| RTC_ClearINTPendingBit() | RTC_INT | void | 清除中断待处理位 |

### 中断定义
- `RTC_INT_OV`: 溢出中断
- `RTC_INT_ALA`: 闹钟中断
- `RTC_INT_PACE`: 秒中断

### 标志定义
- `RTC_FLAG_RTF`: RTC操作关闭标志
- `RTC_FLAG_RSYNF`: 寄存器同步标志
- `RTC_FLAG_OV`: 溢出标志
- `RTC_FLAG_ALA`: 闹钟标志
- `RTC_FLAG_PACE`: 秒标志

---

## SPI 通信模块 (lib_spi.h)

### 数据结构

#### SPI_InitType
| 成员 | 类型 | 描述 |
|------|------|------|
| SPI_TransMode | uint16_t | 传输模式 |
| SPI_Mode | uint16_t | 主从模式 |
| SPI_FrameSize | uint16_t | 帧大小 |
| SPI_CPOL | uint16_t | 时钟极性 |
| SPI_CPHA | uint16_t | 时钟相位 |
| SPI_NSSSEL | uint16_t | 片选管理 |
| SPI_MCLKP | uint16_t | 主时钟分频 |
| SPI_FirstBit | uint16_t | 首位传输 |

#### I2S_InitType
| 成员 | 类型 | 描述 |
|------|------|------|
| I2S_Mode | uint16_t | I2S模式 |
| I2s_AudioProtocol | uint16_t | 音频协议 |
| I2S_FrameFormat | uint16_t | 帧格式 |
| I2S_MCLKOE | uint16_t | MCLK输出使能 |
| I2S_AudioFreq | uint32_t | 音频频率 |
| I2S_CPOL | uint16_t | I2S时钟极性 |

### 主要函数接口

#### 基础函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| SPI_I2S_Reset() | SPIx | void | 复位SPI/I2S |
| SPI_Init() | SPIx, SPI_InitStruct | void | SPI初始化 |
| I2S_Init() | SPIx, I2S_InitStruct | void | I2S初始化 |
| SPI_Enable() | SPIx, NewState | void | SPI使能 |
| I2S_Enable() | SPIx, NewState | void | I2S使能 |

#### 数据传输函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| SPI_I2S_TxData() | SPIx, Data | void | 发送数据 |
| SPI_I2S_RxData() | SPIx | uint16_t | 接收数据 |

#### 配置函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| SPI_NSSInternalSoftwareConfig() | SPIx, SPI_NSSInternalSoft | void | 内部片选配置 |
| SPI_FrameSizeConfig() | SPIx, SPI_DataSize | void | 帧大小配置 |
| SPI_HalfDuplexTransModeConfig() | SPIx, SPI_Direction | void | 半双工模式配置 |

#### 中断和DMA函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| SPI_I2S_INTConfig() | SPIx, SPI_I2S_INT, NewState | void | 中断配置 |
| SPI_I2S_DMAEnable() | SPIx, SPI_I2S_DMAReq, NewState | void | DMA使能 |

#### 状态查询函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| SPI_I2S_GetFlagStatus() | SPIx, SPI_I2S_FLAG | FlagStatus | 获取标志状态 |
| SPI_I2S_GetITStatus() | SPIx, SPI_I2S_INT | ITStatus | 获取中断状态 |

### 常量定义

#### 传输模式
- `SPI_TRANSMODE_FULLDUPLEX`: 全双工
- `SPI_TRANSMODE_RXONLY`: 只接收
- `SPI_TRANSMODE_RX_HALFDUPLEX`: 半双工接收
- `SPI_TRANSMODE_TX_HALFDUPLEX`: 半双工发送

#### 主从模式
- `SPI_MODE_MASTER`: 主机模式
- `SPI_MODE_SLAVE`: 从机模式

#### 帧大小
- `SPI_FRAMESIZE_8BIT`: 8位
- `SPI_FRAMESIZE_16BIT`: 16位

#### 支持的SPI外设
- SPI1, SPI2, SPI3, SPI4

---

## I2C 通信模块 (lib_i2c.h)

### 数据结构

#### I2C_InitType
| 成员 | 类型 | 描述 |
|------|------|------|
| I2C_BitRate | uint32_t | 时钟频率 |
| I2C_Mode | uint16_t | I2C模式 |
| I2C_FmDutyCycle | uint16_t | 快速模式占空比 |
| I2C_OwnAddr1 | uint16_t | 自身地址1 |
| I2C_Ack | uint16_t | 应答使能 |
| I2C_AddrMode | uint16_t | 地址模式 |

### 主要函数接口

#### 基础函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| I2C_DeInit() | I2Cx | void | 复位I2C |
| I2C_Init() | I2Cx, I2C_InitStruct | void | I2C初始化 |
| I2C_Cmd() | I2Cx, NewState | void | 使能/禁用I2C |
| I2C_DMACmd() | I2Cx, NewState | void | DMA使能 |
| I2C_DMALastTransferCmd() | I2Cx, NewState | void | DMA最后传输 |

#### 通信控制函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| I2C_GenerateSTART() | I2Cx, NewState | void | 生成起始条件 |
| I2C_GenerateSTOP() | I2Cx, NewState | void | 生成停止条件 |
| I2C_AcknowledgeConfig() | I2Cx, NewState | void | 应答配置 |
| I2C_Send7bitAddress() | I2Cx, Address, I2C_Direction | void | 发送7位地址 |
| I2C_SendData() | I2Cx, Data | void | 发送数据 |
| I2C_ReceiveData() | I2Cx | uint8_t | 接收数据 |

#### 配置函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| I2C_OwnAddress2Config() | I2Cx, Address | void | 自身地址2配置 |
| I2C_DualAddressCmd() | I2Cx, NewState | void | 双地址使能 |
| I2C_GeneralCallCmd() | I2Cx, NewState | void | 广播使能 |
| I2C_NACKPositionConfig() | I2Cx, I2C_NACKPosition | void | NACK位置配置 |
| I2C_SMBusAlertConfig() | I2Cx, I2C_SMBusAlert | void | SMBus报警配置 |

#### 状态监控函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| I2C_CheckEvent() | I2Cx, I2C_EVENT | ErrorStatus | 检查事件 |
| I2C_GetLastEvent() | I2Cx | uint32_t | 获取最后事件 |
| I2C_GetFlagStatus() | I2Cx, I2C_FLAG | FlagStatus | 获取标志状态 |

#### 中断和状态函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| I2C_INTConfig() | I2Cx, I2C_INT, NewState | void | 中断配置 |
| I2C_ClearFlag() | I2Cx, I2C_FLAG | void | 清除标志 |
| I2C_GetINTStatus() | I2Cx, I2C_INT | ITStatus | 获取中断状态 |
| I2C_ClearITPendingBit() | I2Cx, I2C_INT | void | 清除中断待处理位 |

### 常量定义

#### I2C模式
- `I2C_Mode_I2CDevice`: I2C设备模式
- `I2C_Mode_SMBusDevice`: SMBus设备模式
- `I2C_Mode_SMBusHost`: SMBus主机模式

#### 传输方向
- `I2C_Direction_Transmit`: 发送
- `I2C_Direction_Receive`: 接收

#### 地址模式
- `I2C_AddrMode_7bit`: 7位地址
- `I2C_AddrMode_10bit`: 10位地址

#### 支持的I2C外设
- I2C1, I2C2, I2C3

---

## 外部中断模块 (lib_exti.h)

### 数据结构

#### EXTI_InitType
| 成员 | 类型 | 描述 |
|------|------|------|
| EXTI_Line | uint32_t | EXTI线 |
| EXTI_Mode | EXTIMode_Type | 模式 |
| EXTI_Trigger | EXTITrigger_Type | 触发方式 |
| EXTI_LineEnable | FunctionalState | 使能状态 |

#### 枚举类型

#### EXTIMode_Type
- `EXTI_Mode_Interrupt`: 中断模式
- `EXTI_Mode_Event`: 事件模式

#### EXTITrigger_Type
- `EXTI_Trigger_Rising`: 上升沿触发
- `EXTI_Trigger_Falling`: 下降沿触发
- `EXTI_Trigger_Rising_Falling`: 双边沿触发

### 主要函数接口
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| EXTI_Reset() | 无 | void | 复位EXTI |
| EXTI_Init() | EXTI_InitStruct | void | 初始化EXTI |
| EXTI_StructInit() | EXTI_InitStruct | void | 初始化结构体 |
| EXTI_GenerateSWInt() | EXTI_Line | void | 生成软件中断 |
| EXTI_GetFlagStatus() | EXTI_Line | FlagStatus | 获取标志状态 |
| EXTI_ClearFlag() | EXTI_Line | void | 清除标志 |
| EXTI_GetIntStatus() | EXTI_Line | ITStatus | 获取中断状态 |
| EXTI_ClearIntPendingBit() | EXTI_Line | void | 清除中断待处理位 |

### EXTI线定义
- `EXTI_Line0` 到 `EXTI_Line15`: 外部GPIO中断线
- `EXTI_Line16`: PVD输出中断线
- `EXTI_Line17`: RTC闹钟事件中断线

---

## DMA 模块 (lib_dma.h)

### 数据结构

#### DMA_InitType
| 成员 | 类型 | 描述 |
|------|------|------|
| DMA_PeripheralBaseAddr | uint32_t | 外设基地址 |
| DMA_MemoryBaseAddr | uint32_t | 内存基地址 |
| DMA_Direction | uint32_t | 传输方向 |
| DMA_BufferSize | uint32_t | 缓冲区大小 |
| DMA_PeripheralInc | uint32_t | 外设地址增量 |
| DMA_MemoryInc | uint32_t | 内存地址增量 |
| DMA_PeripheralDataWidth | uint32_t | 外设数据宽度 |
| DMA_MemoryDataWidth | uint32_t | 内存数据宽度 |
| DMA_Mode | uint32_t | 模式 |
| DMA_Priority | uint32_t | 优先级 |
| DMA_MTOM | uint32_t | 内存到内存传输 |

### 主要函数接口

#### 基础函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| DMA_Reset() | DMAy_Channelx | void | 复位DMA通道 |
| DMA_Init() | DMAy_Channelx, DMA_InitStruct | void | 初始化DMA |
| DMA_DefaultInitParaConfig() | DMA_InitStruct | void | 默认参数配置 |
| DMA_ChannelEnable() | DMAy_Channelx, NewState | void | 使能DMA通道 |

#### 配置函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| DMA_INTConfig() | DMAy_Channelx, DMA_INT, NewState | void | 中断配置 |
| DMA_SetCurrDataCounter() | DMAy_Channelx, DataNumber | void | 设置当前数据计数器 |
| DMA_GetCurrDataCounter() | DMAy_Channelx | uint16_t | 获取当前数据计数器 |

#### 灵活配置函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| DMA_Flexible_Config() | DMAx, Flex_Channelx, Hardware_ID | void | 灵活配置 |

#### 状态查询函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| DMA_GetFlagStatus() | DMAy_FLAG | FlagStatus | 获取标志状态 |
| DMA_ClearFlag() | DMAy_FLAG | void | 清除标志 |
| DMA_GetITStatus() | DMAy_INT | ITStatus | 获取中断状态 |
| DMA_ClearITPendingBit() | DMAy_INT | void | 清除中断待处理位 |

### 常量定义

#### 传输方向
- `DMA_DIR_PERIPHERALDST`: 外设作为目标
- `DMA_DIR_PERIPHERALSRC`: 外设作为源

#### 数据宽度
- `DMA_PERIPHERALDATAWIDTH_BYTE`: 字节
- `DMA_PERIPHERALDATAWIDTH_HALFWORD`: 半字
- `DMA_PERIPHERALDATAWIDTH_WORD`: 字

#### 模式
- `DMA_MODE_CIRCULAR`: 循环模式
- `DMA_MODE_NORMAL`: 正常模式

#### 优先级
- `DMA_PRIORITY_VERYHIGH`: 很高
- `DMA_PRIORITY_HIGH`: 高
- `DMA_PRIORITY_MEDIUM`: 中等
- `DMA_PRIORITY_LOW`: 低

#### 支持的DMA外设
- DMA1: Channel1-7
- DMA2: Channel1-7

---

## CRC 校验模块 (lib_crc.h)

### 主要函数接口
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| CRC_ResetDT() | 无 | void | 复位数据寄存器 |
| CRC_CalculateCRC() | Data | uint32_t | 计算CRC |
| CRC_CalculateBlkCRC() | pBuffer[], BufferLength | uint32_t | 计算块CRC |
| CRC_GetCRC() | 无 | uint32_t | 获取当前CRC |
| CRC_SetIDTReg() | IDValue | void | 设置独立数据寄存器 |
| CRC_GetIDTReg() | 无 | uint8_t | 获取独立数据寄存器 |

---

## 备份寄存器模块 (lib_bkp.h)

### 主要函数接口
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| BKP_Reset() | 无 | void | 复位备份寄存器 |
| BKP_TamperPinLvConfig() | BKP_TamperPinLevel | void | 篡改检测引脚电平配置 |
| BKP_TamperPinCmd() | NewState | void | 篡改检测引脚使能 |
| BKP_IntConfig() | NewState | void | 中断配置 |
| BKP_RTCOutputConfig() | BKP_RTCOutputSource | void | RTC输出配置 |
| BKP_SetRTCCalValue() | CalibrationValue | void | 设置RTC校准值 |
| BKP_WriteBackupReg() | BKP_DR, Data | void | 写入备份数据寄存器 |
| BKP_ReadBackupReg() | BKP_DR | uint16_t | 读取备份数据寄存器 |

#### 状态查询函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| BKP_GetFlagStatus() | 无 | FlagStatus | 获取标志状态 |
| BKP_ClearFlag() | 无 | void | 清除标志 |
| BKP_GetIntStatus() | 无 | ITStatus | 获取中断状态 |
| BKP_ClearIntPendingBit() | 无 | void | 清除中断待处理位 |

### 备份数据寄存器
- `BKP_DT1` 到 `BKP_DT64`: 64个备份数据寄存器

### 篡改检测引脚电平
- `BKP_TamperPinLv_H`: 高电平
- `BKP_TamperPinLv_L`: 低电平

### RTC输出选择
- `BKP_RTCOutput_None`: 无输出
- `BKP_RTCOutput_CalClk`: 校准时钟输出
- `BKP_RTCOutput_Alarm`: 闹钟输出
- `BKP_RTCOutput_Second`: 秒脉冲输出

---

## 时钟控制模块 (lib_rcc.h)

### 数据结构

#### RCC_ClockType
| 成员 | 类型 | 描述 |
|------|------|------|
| SYSCLK_Freq | uint32_t | 系统时钟频率 |
| AHBCLK_Freq | uint32_t | AHB时钟频率 |
| APB1CLK_Freq | uint32_t | APB1时钟频率 |
| APB2CLK_Freq | uint32_t | APB2时钟频率 |
| ADCCLK_Freq | uint32_t | ADC时钟频率 |

#### Autotrim_InitType
| 成员 | 类型 | 描述 |
|------|------|------|
| Autotrim_Select | uint32_t | 自动微调源选择 |
| Autotrim_UpperExpt | uint32_t | 上限期望值 |
| Autotrim_LowerExpt | uint32_t | 下限期望值 |

### 主要函数接口

#### 时钟配置函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| RCC_HSEConfig() | RCC_HSE | void | HSE配置 |
| RCC_PLLConfig() | RCC_PLLRefClk, RCC_PLLMult, RCC_PLLRange | void | PLL配置 |
| RCC_PLLCmd() | NewState | void | PLL使能 |
| RCC_SYSCLKConfig() | RCC_SYSCLKSelect | void | 系统时钟配置 |
| RCC_AHBCLKConfig() | RCC_SYSCLK_Div | void | AHB时钟配置 |
| RCC_APB1CLKConfig() | RCC_HCLK_Div | void | APB1时钟配置 |
| RCC_APB2CLKConfig() | RCC_HCLK_Div | void | APB2时钟配置 |

#### 外设时钟函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| RCC_AHBPeriphClockCmd() | RCC_AHBPeriph, NewState | void | AHB外设时钟使能 |
| RCC_APB2PeriphClockCmd() | RCC_APB2Periph, NewState | void | APB2外设时钟使能 |
| RCC_APB1PeriphClockCmd() | RCC_APB1Periph, NewState | void | APB1外设时钟使能 |

#### 时钟获取函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| RCC_GetClocksFreq() | RCC_Clocks | void | 获取时钟频率 |
| RCC_GetSYSCLKSelction() | 无 | uint8_t | 获取系统时钟选择 |

#### RTC时钟函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| RCC_LSEConfig() | RCC_LSE | void | LSE配置 |
| RCC_LSICmd() | NewState | void | LSI使能 |
| RCC_RTCCLKConfig() | RCC_RTCCLKSelect | void | RTC时钟配置 |
| RCC_RTCCLKCmd() | NewState | void | RTC时钟使能 |

#### USB时钟函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| RCC_USBCLKConfig() | RCC_USBCLKSelect | void | USB时钟配置 |

#### 其他函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| RCC_HSICmd() | NewState | void | HSI使能 |
| RCC_SetHSITweakValue() | HSITweakValue | void | 设置HSI微调值 |
| RCC_SetHSICalibValue() | HSICalibValue | void | 设置HSI校准值 |
| RCC_CLKOUTConfig() | RCC_CLKOUT, RCC_CLKOUTPRE | void | 时钟输出配置 |

### 常量定义

#### HSE配置
- `RCC_HSE_DISABLE`: 禁用HSE
- `RCC_HSE_ENABLE`: 使能HSE
- `RCC_HSE_BYPASS`: HSE旁路

#### PLL时钟源
- `RCC_PLLRefClk_HSI_Div2`: HSI/2作为PLL源
- `RCC_PLLRefClk_HSE_Div1`: HSE作为PLL源
- `RCC_PLLRefClk_HSE_Div2`: HSE/2作为PLL源

#### 系统时钟选择
- `RCC_SYSCLKSelction_HSI`: HSI作为系统时钟
- `RCC_SYSCLKSelction_HSE`: HSE作为系统时钟
- `RCC_SYSCLKSelction_PLL`: PLL作为系统时钟

#### AHB分频
- `RCC_SYSCLK_Div1`: 不分频
- `RCC_SYSCLK_Div2`: 2分频
- `RCC_SYSCLK_Div4`: 4分频
- `RCC_SYSCLK_Div8`: 8分频
- `RCC_SYSCLK_Div16`: 16分频
- `RCC_SYSCLK_Div64`: 64分频
- `RCC_SYSCLK_Div128`: 128分频
- `RCC_SYSCLK_Div256`: 256分频
- `RCC_SYSCLK_Div512`: 512分频

---

## 电源管理模块 (lib_pwr.h)

### 主要函数接口
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| PWR_Reset() | 无 | void | 复位电源管理 |
| PWR_BackupAccessCtrl() | NewState | void | 备份域访问控制 |
| PWR_PVDCtrl() | NewState | void | PVD控制 |
| PWR_PVDLevelConfig() | PWR_PVDLevel | void | PVD级别配置 |
| PWR_EnterSleepMode() | PWR_SLEEPEntry | void | 进入睡眠模式 |
| PWR_EnterSTOPMode() | PWR_Regulator, PWR_STOPEntry | void | 进入停止模式 |

#### 状态查询函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| PWR_GetFlagStatus() | PWR_FLAG | FlagStatus | 获取标志状态 |

### 常量定义

#### PVD检测级别
- `PWR_PVDS_2V2`: 2.2V
- `PWR_PVDS_2V3`: 2.3V
- `PWR_PVDS_2V4`: 2.4V
- `PWR_PVDS_2V5`: 2.5V
- `PWR_PVDS_2V6`: 2.6V
- `PWR_PVDS_2V7`: 2.7V
- `PWR_PVDS_2V8`: 2.8V
- `PWR_PVDS_2V9`: 2.9V

#### 睡眠模式入口
- `PWR_SLEEPEntry_WFI`: WFI指令进入
- `PWR_SLEEPEntry_WFE`: WFE指令进入

#### 停止模式入口
- `PWR_STOPEntry_WFI`: WFI指令进入
- `PWR_STOPEntry_WFE`: WFE指令进入

#### 调压器状态
- `PWR_Regulator_ON`: 调压器开启

#### 标志定义
- `PWR_FLAG_PVDO`: PVD输出标志

---

## 调试模块 (lib_dbgmcu.h)

### 主要函数接口
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| MCUDBG_GetRevID() | 无 | uint32_t | 获取版本ID |
| MCUDBG_GetDevID() | 无 | uint32_t | 获取设备ID |
| MCUDBG_PeriphDebugModeConfig() | DBGMCU_Periph, NewState | void | 外设调试模式配置 |

### 调试模式配置常量
- `MCUDBG_SLEEP`: 调试时睡眠模式停止
- `MCUDBG_STOP`: 调试时停止模式停止
- `MCUDBG_IWDG_STOP`: 调试时独立看门狗停止
- `MCUDBG_WWDG_STOP`: 调试时窗口看门狗停止
- `MCUDBG_TMR1_STOP` 到 `MCUDBG_TMR15_STOP`: 调试时定时器停止
- `MCUDBG_I2C1_SMBUS_TIMEOUT`: I2C1 SMBUS超时
- `MCUDBG_I2C2_SMBUS_TIMEOUT`: I2C2 SMBUS超时
- `MCUDBG_I2C3_SMBUS_TIMEOUT`: I2C3 SMBUS超时

---

## CAN 总线模块 (lib_can.h)

### 数据结构

#### CAN_InitType
| 成员 | 类型 | 描述 |
|------|------|------|
| CAN_Mode | uint8_t | CAN模式 |
| CAN_Prescaler | uint8_t | 预分频器 |
| CAN_SJW | uint8_t | 同步跳转宽度 |
| CAN_TSEG1 | uint8_t | 时间段1 |
| CAN_TSEG2 | uint8_t | 时间段2 |
| CAN_SAM | uint8_t | 采样次数 |
| CAN_EWLR | uint8_t | 错误警告限制 |

#### CAN_FilterInitType
| 成员 | 类型 | 描述 |
|------|------|------|
| CAN_FilterIDMode | uint8_t | 过滤器ID模式 |
| CAN_FilterAcceptMode | uint8_t | 过滤器接收模式 |
| CAN_FilterRTR | uint8_t | 过滤器RTR |
| CAN_FilterRTRMsk | uint8_t | 过滤器RTR掩码 |
| CAN_FilterStdID[2] | uint16_t | 标准ID |
| CAN_FilterStdIDMsk[2] | uint16_t | 标准ID掩码 |
| CAN_FilterData[2] | uint8_t | 过滤器数据 |
| CAN_FilterDataMsk[2] | uint8_t | 过滤器数据掩码 |
| CAN_FilterExtID[2] | uint32_t | 扩展ID |
| CAN_FilterExtIDMsk[2] | uint32_t | 扩展ID掩码 |

#### CanTxMsg / CanRxMsg
| 成员 | 类型 | 描述 |
|------|------|------|
| StdId | uint16_t | 标准ID |
| ExtId | uint32_t | 扩展ID |
| ID_Type | uint8_t | ID类型 |
| RTR | uint8_t | 远程传输请求 |
| DLC | uint8_t | 数据长度 |
| Data[8] | uint8_t | 数据 |

#### CAN_EccType
| 成员 | 类型 | 描述 |
|------|------|------|
| ErrorCode | uint8_t | 错误代码 |
| Direction | uint8_t | 方向 |
| SegmentCode | uint8_t | 段代码 |

### 主要函数接口

#### 初始化函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| CAN_DeInit() | CANx | void | 复位CAN |
| CAN_Init() | CANx, CAN_InitStruct | void | 初始化CAN |
| CAN_StructInit() | CAN_InitStruct | void | 初始化结构体 |
| CAN_FilterInit() | CANx, CAN_FilterInitStruct | void | 过滤器初始化 |
| CAN_FilterStructInit() | CAN_FilterInitStruct | void | 过滤器结构体初始化 |

#### 传输函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| CAN_Transmit() | CANx, TxMessage | uint8_t | 发送消息 |
| CAN_Receive() | CANx, RxMessage | void | 接收消息 |
| CAN_ReceiveFIFO() | CANx, RxMessage | void | 接收FIFO |
| CAN_TransmissionRequest() | CANx | void | 传输请求 |
| CAN_AbortTransmission() | CANx | void | 中止传输 |
| CAN_ReleaseReceiveBuffer() | CANx | void | 释放接收缓冲区 |
| CAN_ClearDataOverrun() | CANx | void | 清除数据溢出 |

#### 配置函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| CAN_SelfReceiveRequest() | CANx | void | 自接收请求 |
| CAN_SetReceiveBufferStartAddress() | CANx, Addr | void | 设置接收缓冲区起始地址 |
| CAN_GetReceiveBufferStartAddress() | CANx | uint8_t | 获取接收缓冲区起始地址 |

#### 低功耗函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| CAN_Sleep() | CANx | void | 进入睡眠模式 |
| CAN_WakeUp() | CANx | void | 唤醒 |

#### 状态查询函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| CAN_GetFlagStatus() | CANx, CAN_FLAG | FlagStatus | 获取标志状态 |
| CAN_GetINTStatus() | CANx, CAN_INT | ITStatus | 获取中断状态 |
| CAN_MessagePending() | CANx | uint8_t | 消息挂起 |

#### 错误处理函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| CAN_GetErrorCodeCapture() | CANx, CAN_EccStruct | uint8_t | 获取错误代码 |
| CAN_GetReceiveErrorCounter() | CANx | uint8_t | 获取接收错误计数 |
| CAN_GetTransmitErrorCounter() | CANx | uint8_t | 获取发送错误计数 |

### 常量定义

#### CAN模式
- `CAN_MODE_NORMAL`: 正常模式
- `CAN_MODE_LISTENONLY`: 只听模式
- `CAN_MODE_SELFTEST`: 自测试模式

#### ID类型
- `CAN_ID_STANDARD`: 标准ID
- `CAN_ID_EXTENDED`: 扩展ID

#### 远程传输请求
- `CAN_RTR_DATA`: 数据帧
- `CAN_RTR_REMOTE`: 远程帧

#### 数据长度
- `CAN_DLC_0` 到 `CAN_DLC_8`: 0-8字节

---

## ADC 模数转换模块 (lib_adc.h)

### 数据结构

#### ADC_InitType
| 成员 | 类型 | 描述 |
|------|------|------|
| ADC_Mode | uint32_t | ADC模式 |
| ADC_ScanMode | FunctionalState | 扫描模式 |
| ADC_ContinuousMode | FunctionalState | 连续模式 |
| ADC_ExternalTrig | uint32_t | 外部触发 |
| ADC_DataAlign | uint32_t | 数据对齐 |
| ADC_NumOfChannel | uint8_t | 通道数量 |

### 主要函数接口

#### 初始化和控制函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| ADC_Reset() | ADCx | void | 复位ADC |
| ADC_Init() | ADCx, ADC_InitStruct | void | 初始化ADC |
| ADC_StructInit() | ADC_InitStruct | void | 初始化结构体 |
| ADC_Ctrl() | ADCx, NewState | void | 使能/禁用ADC |
| ADC_DMACtrl() | ADCx, NewState | void | DMA控制 |

#### 校准函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| ADC_RstCalibration() | ADCx | void | 复位校准 |
| ADC_GetResetCalibrationStatus() | ADCx | FlagStatus | 获取复位校准状态 |
| ADC_StartCalibration() | ADCx | void | 开始校准 |
| ADC_GetCalibrationStatus() | ADCx | FlagStatus | 获取校准状态 |

#### 转换函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| ADC_SoftwareStartConvCtrl() | ADCx, NewState | void | 软件启动转换控制 |
| ADC_GetSoftwareStartConvStatus() | ADCx | FlagStatus | 获取软件启动转换状态 |
| ADC_GetConversionValue() | ADCx | uint16_t | 获取转换值 |
| ADC_GetDualModeConversionValue() | 无 | uint32_t | 获取双模式转换值 |

#### 规则通道函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| ADC_RegularChannelConfig() | ADCx, ADC_Channel, Rank, ADC_SampleTime | void | 规则通道配置 |
| ADC_ExternalTrigConvCtrl() | ADCx, NewState | void | 外部触发转换控制 |
| ADC_DiscModeChannelCountConfig() | ADCx, Number | void | 不连续模式通道数配置 |
| ADC_DiscModeCtrl() | ADCx, NewState | void | 不连续模式控制 |

#### 注入通道函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| ADC_AutoInjectedConvCtrl() | ADCx, NewState | void | 自动注入转换控制 |
| ADC_InjectedDiscModeCtrl() | ADCx, NewState | void | 注入不连续模式控制 |
| ADC_ExternalTrigInjectedConvConfig() | ADCx, ADC_ExternalTrigInjecConv | void | 外部触发注入转换配置 |
| ADC_ExternalTrigInjectedConvCtrl() | ADCx, NewState | void | 外部触发注入转换控制 |
| ADC_SoftwareStartInjectedConvCtrl() | ADCx, NewState | void | 软件启动注入转换控制 |
| ADC_GetSoftwareStartInjectedConvCtrlStatus() | ADCx | FlagStatus | 获取软件启动注入转换状态 |
| ADC_InjectedChannelConfig() | ADCx, ADC_Channel, Rank, ADC_SampleTime | void | 注入通道配置 |
| ADC_InjectedSequencerLengthConfig() | ADCx, Length | void | 注入序列长度配置 |
| ADC_SetInjectedOffset() | ADCx, ADC_InjectedChannel, Offset | void | 设置注入偏移 |
| ADC_GetInjectedConversionValue() | ADCx, ADC_InjectedChannel | uint16_t | 获取注入转换值 |

#### 模拟看门狗函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| ADC_AnalogWDGCtrl() | ADCx, ADC_AnalogWatchdog | void | 模拟看门狗控制 |
| ADC_AnalogWDGThresholdsConfig() | ADCx, HighThreshold, LowThreshold | void | 模拟看门狗阈值配置 |
| ADC_AnalogWDGSingleChannelConfig() | ADCx, ADC_Channel | void | 模拟看门狗单通道配置 |

#### 温度传感器函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| ADC_TempSensorVrefintCtrl() | NewState | void | 温度传感器和内部参考电压控制 |

#### 中断和状态函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| ADC_INTConfig() | ADCx, ADC_INT, NewState | void | 中断配置 |
| ADC_GetFlagStatus() | ADCx, ADC_FLAG | FlagStatus | 获取标志状态 |
| ADC_ClearFlag() | ADCx, ADC_FLAG | void | 清除标志 |
| ADC_GetINTStatus() | ADCx, ADC_INT | ITStatus | 获取中断状态 |
| ADC_ClearINTPendingBit() | ADCx, ADC_INT | void | 清除中断待处理位 |

### 常量定义

#### ADC模式
- `ADC_Mode_Independent`: 独立模式
- `ADC_Mode_RegInjecSimult`: 规则注入同时模式
- `ADC_Mode_RegSimult_AlterTrig`: 规则同时交替触发模式
- 其他多种双ADC模式

#### 数据对齐
- `ADC_DataAlign_Right`: 右对齐
- `ADC_DataAlign_Left`: 左对齐

#### ADC通道
- `ADC_Channel_0` 到 `ADC_Channel_15`: ADC通道0-15
- `ADC_Channel_16`: 温度传感器通道

#### 采样时间
- `ADC_SampleTime_4_5`: 4.5个周期
- `ADC_SampleTime_7_5`: 7.5个周期
- `ADC_SampleTime_13_5`: 13.5个周期
- `ADC_SampleTime_28_5`: 28.5个周期
- `ADC_SampleTime_41_5`: 41.5个周期
- `ADC_SampleTime_55_5`: 55.5个周期
- `ADC_SampleTime_71_5`: 71.5个周期
- `ADC_SampleTime_239_5`: 239.5个周期

#### 支持的ADC外设
- ADC1, ADC2

---

## Flash 存储模块 (lib_flash.h)

### 数据结构

#### FLASH_Status 枚举
- `FLASH_BSY`: 忙状态
- `FLASH_PGRM_FLR`: 编程错误
- `FLASH_WRPRT_FLR`: 写保护错误
- `FLASH_PRC_DONE`: 编程完成
- `FLASH_TIMEOUT`: 超时

#### T_BANK2_SEL 枚举
- `E_BANK2_SEL_ESMT_SP`: ESMT SP选择
- `E_BANK2_SEL_GENERAL_CFGQE`: 通用配置QE选择
- `E_BANK2_SEL_GENERAL`: 通用选择

#### FLASH_RdpLv 枚举
- `E_RDP_LV0`: 读保护级别0
- `E_RDP_LV1`: 读保护级别1
- `E_RDP_LV2`: 读保护级别2

### 主要函数接口

#### 基础操作函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| FLASH_Unlock() | 无 | void | 解锁Flash |
| FLASH_Lock() | 无 | void | 锁定Flash |
| FLASH_GetStatus() | 无 | FLASH_Status | 获取状态 |
| FLASH_WaitForProcess() | Timeout | FLASH_Status | 等待操作完成 |

#### 擦除函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| FLASH_ErasePage() | Page_Address | FLASH_Status | 擦除页 |
| FLASH_EraseAllPages() | 无 | FLASH_Status | 擦除所有页 |
| FLASH_EraseUserOptionBytes() | 无 | FLASH_Status | 擦除用户选项字节 |
| FLASH_AllEraseUserOption() | 无 | FLASH_Status | 全部擦除用户选项 |

#### 编程函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| FLASH_ProgramWord() | Address, Data | FLASH_Status | 编程字 |
| FLASH_ProgramHalfWord() | Address, Data | FLASH_Status | 编程半字 |
| FLASH_ProgramByte() | Address, Data | FLASH_Status | 编程字节 |
| FLASH_ProgramUserOptionByteData() | Address, Data | FLASH_Status | 编程用户选项字节 |

#### 写保护函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| FLASH_EnableWriteProtect() | FLASH_Pages | FLASH_Status | 使能写保护 |
| FLASH_ReadProtectConfig() | NewState | FLASH_Status | 读保护配置 |

#### 配置函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| FLASH_SampleDelayConfig() | SampleDelay | void | 采样延迟配置 |
| FLASH_CLKDIVConfig() | ClockDiv | void | 时钟分频配置 |
| FLASH_FastProgramConfig() | NewState | void | 快速编程配置 |
| FLASH_WaitConfig() | WAIT_Size | FLASH_Status | 等待配置 |
| FLASH_UserOptionByteConfig() | UOB_IWDG, UOB_STOP, UOB_STDBY | FLASH_Status | 用户选项字节配置 |

#### Bank2相关函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| FLASH_UnlockBank2() | 无 | void | 解锁Bank2 |
| FLASH_LockBank2() | 无 | void | 锁定Bank2 |
| FLASH_EraseBank2AllPages() | 无 | FLASH_Status | 擦除Bank2所有页 |
| FLASH_GetBank2Status() | 无 | FLASH_Status | 获取Bank2状态 |
| FLASH_WaitForBank2Process() | Timeout | FLASH_Status | 等待Bank2操作完成 |
| FLASH_Bank2EncEndAddrConfig() | EndAddress | void | Bank2加密结束地址配置 |

#### 状态查询函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| FLASH_GetUserOptionByte() | 无 | uint32_t | 获取用户选项字节 |
| FLASH_GetWriteProtectStatus() | 无 | uint32_t | 获取写保护状态 |
| FLASH_GetReadProtectStatus() | 无 | FlagStatus | 获取读保护状态 |
| FLASH_GetFlagStatus() | FLASH_FLAG | FlagStatus | 获取标志状态 |
| FLASH_ClearFlag() | FLASH_FLAG | void | 清除标志 |

#### 中断函数
| 函数名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| FLASH_INTConfig() | FLASH_INT, NewState | void | 中断配置 |

### 常量定义

#### 写保护页
- `FLASH_WRPRT_PAGE_0to1` 到 `FLASH_WRPRT_PAGE_62to1023`: 各页写保护定义
- `FLASH_WRPRT_AllPAGES`: 所有页写保护

#### 采样延迟
- `FLASH_SPDELY_NO`: 无延迟
- `FLASH_SPDELY_1`: 延迟1
- `FLASH_SPDELY_2`: 延迟2
- `FLASH_SPDELY_3`: 延迟3

#### 时钟分频
- `FLASH_CLOCKDIV_2`: 2分频
- `FLASH_CLOCKDIV_3`: 3分频

#### 等待大小
- `FLASH_WAIT_SIZE_0`: 无ZW
- `FLASH_WAIT_SIZE_128KB`: 128KB ZW
- `FLASH_WAIT_SIZE_384KB`: 384KB ZW
- `FLASH_WAIT_SIZE_512KB`: 512KB ZW
- `FLASH_WAIT_SIZE_640KB`: 640KB ZW

#### 用户选项字节
- `UOB_SW_IWDG`: 软件独立看门狗
- `UOB_HW_IWDG`: 硬件独立看门狗
- `UOB_NO_RST_STP`: 进入STOP时不复位
- `UOB_RST_STP`: 进入STOP时复位
- `UOB_NO_RST_STDBY`: 进入STANDBY时不复位
- `UOB_RST_STDBY`: 进入STANDBY时复位

---

## GPIO 通用输入输出模块 (lib_gpio.h)

### 模块说明
GPIO（General Purpose Input/Output）通用输入输出模块是微控制器最基本的外设，用于控制和读取芯片引脚的电平状态。V32G410x包含6个GPIO端口：GPIOA-GPIOF，每个端口有16个引脚。

GPIO支持多种工作模式：
- **输入模式**：模拟输入、浮空输入、下拉输入、上拉输入
- **输出模式**：推挽输出、开漏输出
- **复用功能模式**：复用推挽、复用开漏（用于USART、SPI、I2C等外设）
- **重映射功能**：通过AFIO实现引脚功能重映射

### 数据结构

#### GPIO_InitType
GPIO初始化结构体，配置引脚的工作模式。
| 成员 | 类型 | 描述 | 示例值 |
|------|------|------|--------|
| GPIO_Pins | uint16_t | 要配置的GPIO引脚 (可用位或组合) | GPIO_Pins_0 \| GPIO_Pins_1 |
| GPIO_MaxSpeed | GPIOMaxSpeed_Type | 最大输出速度 | GPIO_MaxSpeed_50MHz |
| GPIO_Mode | GPIOMode_Type | 工作模式 | GPIO_Mode_OUT_PP |

#### 枚举类型

#### GPIOMaxSpeed_Type
引脚最大输出速度，影响功耗和EMI。
- `GPIO_MaxSpeed_10MHz`: 10MHz - 低速，低功耗
- `GPIO_MaxSpeed_2MHz`: 2MHz - 最低速，最低功耗
- `GPIO_MaxSpeed_50MHz`: 50MHz - 高速，标准速度

#### GPIOMode_Type
引脚工作模式，决定了引脚的功能特性。
- `GPIO_Mode_IN_ANALOG`: 模拟输入 (用于ADC)
- `GPIO_Mode_IN_FLOATING`: 浮空输入 (高阻态，容易受干扰)
- `GPIO_Mode_IN_PD`: 下拉输入 (内部下拉电阻)
- `GPIO_Mode_OUT_PP`: 推挽输出 (强驱动，标准输出)
- `GPIO_Mode_OUT_OD`: 开漏输出 (只能拉低，需要外部上拉)
- `GPIO_Mode_AF_OD`: 复用功能开漏 (用于I2C等)
- `GPIO_Mode_AF_PP`: 复用功能推挽 (用于USART、SPI等)

#### BitState
位状态枚举，用于位操作。
- `Bit_RESET`: 复位状态 (0)
- `Bit_SET`: 置位状态 (1)

### 主要函数接口

#### 基础函数
| 函数名 | 参数说明 | 返回值 | 描述 | 使用示例 |
|--------|----------|--------|------|----------|
| GPIO_Reset() | **GPIOx**: GPIO外设指针 (GPIOA-GPIOF) | void | 复位指定GPIO端口到默认状态 | GPIO_Reset(GPIOA); |
| GPIO_AFIOReset() | 无 | void | 复位AFIO（复用功能IO）到默认状态 | GPIO_AFIOReset(); |
| GPIO_Init() | **GPIOx**: GPIO外设指针<br>**GPIO_InitStruct**: 初始化结构体指针 | void | 根据结构体参数初始化GPIO引脚 | GPIO_Init(GPIOA, &gpioInit); |
| GPIO_StructInit() | **GPIO_InitStruct**: 初始化结构体指针 | void | 初始化结构体为默认值 | GPIO_StructInit(&gpioInit); |

#### 数据读写函数
| 函数名 | 参数说明 | 返回值 | 描述 | 使用示例 |
|--------|----------|--------|------|----------|
| GPIO_ReadInputDataBit() | **GPIOx**: GPIO外设指针<br>**GPIO_Pin**: 引脚号 | uint8_t | 读取指定引脚的输入电平 (0/1) | uint8_t level = GPIO_ReadInputDataBit(GPIOA, GPIO_Pins_0); |
| GPIO_ReadInputData() | **GPIOx**: GPIO外设指针 | uint16_t | 读取整个端口的输入数据 (16位) | uint16_t portData = GPIO_ReadInputData(GPIOA); |
| GPIO_ReadOutputDataBit() | **GPIOx**: GPIO外设指针<br>**GPIO_Pin**: 引脚号 | uint8_t | 读取指定引脚的输出电平 | uint8_t outLevel = GPIO_ReadOutputDataBit(GPIOA, GPIO_Pins_0); |
| GPIO_ReadOutputData() | **GPIOx**: GPIO外设指针 | uint16_t | 读取整个端口的输出数据 | uint16_t outData = GPIO_ReadOutputData(GPIOA); |
| GPIO_SetBits() | **GPIOx**: GPIO外设指针<br>**GPIO_Pin**: 引脚号 | void | 设置指定引脚为高电平 | GPIO_SetBits(GPIOA, GPIO_Pins_0); |
| GPIO_ResetBits() | **GPIOx**: GPIO外设指针<br>**GPIO_Pin**: 引脚号 | void | 设置指定引脚为低电平 | GPIO_ResetBits(GPIOA, GPIO_Pins_0); |
| GPIO_WriteBit() | **GPIOx**: GPIO外设指针<br>**GPIO_Pin**: 引脚号<br>**BitVal**: 位值 (Bit_RESET/Bit_SET) | void | 写入单个引脚的状态 | GPIO_WriteBit(GPIOA, GPIO_Pins_0, Bit_SET); |
| GPIO_OD_WriteBit() | **GPIOx**: GPIO外设指针<br>**GPIO_PinSource**: 引脚源号<br>**BitVal**: 位值 | void | 开漏模式写入位 (原子操作) | GPIO_OD_WriteBit(GPIOA, GPIO_PinsSource0, Bit_SET); |
| GPIO_Write() | **GPIOx**: GPIO外设指针<br>**PortVal**: 端口值 | void | 写入整个端口的16位数据 | GPIO_Write(GPIOA, 0x1234); |

#### 配置函数
| 函数名 | 参数说明 | 返回值 | 描述 | 使用示例 |
|--------|----------|--------|------|----------|
| GPIO_PinsLockConfig() | **GPIOx**: GPIO外设指针<br>**GPIO_Pin**: 引脚号 | void | 锁定引脚配置，防止意外修改 | GPIO_PinsLockConfig(GPIOA, GPIO_Pins_0); |
| GPIO_EventOutputConfig() | **GPIO_PortSource**: 端口源<br>**GPIO_PinSource**: 引脚源 | void | 配置事件输出 | GPIO_EventOutputConfig(GPIO_PortSourceGPIOA, GPIO_PinsSource0); |
| GPIO_EventOutputCmd() | **NewState**: 使能状态 | void | 使能/禁用事件输出 | GPIO_EventOutputCmd(ENABLE); |
| GPIO_PinsRemapConfig() | **GPIO_Remap**: 重映射选择<br>**NewState**: 使能状态 | void | 配置引脚重映射 | GPIO_PinsRemapConfig(GPIO_Remap_USART1, ENABLE); |
| GPIO_EXTILineConfig() | **GPIO_PortSource**: 端口源<br>**GPIO_PinSource**: 引脚源 | void | 配置外部中断线 | GPIO_EXTILineConfig(GPIO_PortSourceGPIOA, GPIO_PinsSource0); |

### 常量定义

#### GPIO引脚定义 (可位或组合)
- `GPIO_Pins_0` 到 `GPIO_Pins_15`: 单个引脚定义
- `GPIO_Pins_All`: 所有16个引脚 (0xFFFF)
- 组合示例: `GPIO_Pins_0 | GPIO_Pins_1 | GPIO_Pins_2`

#### 重映射定义
重映射功能允许将外设功能映射到不同的引脚上。
- `GPIO_Remap01_SPI1`: SPI1重映射方式1
- `GPIO_Remap_I2C1`: I2C1重映射
- `GPIO_Remap_USART1`: USART1重映射 (PA9/PA10 → PB6/PB7)
- `GPIO_Remap_USART2`: USART2重映射 (PA2/PA3 → PD5/PD6)
- `GPIO_PartialRemap_USART3`: USART3部分重映射
- `GPIO_FullRemap_USART3`: USART3完全重映射
- `GPIO_PartialRemap_TMR1`: TMR1部分重映射
- `GPIO_FullRemap_TMR1`: TMR1完全重映射
- `GPIO_Remap_SWJ_NoJNTRST`: SWJ调试接口重映射 (禁用JNTRST)
- `GPIO_Remap_SWJ_JTAGDisable`: 禁用JTAG，保留SWD
- `GPIO_Remap_SWJ_AllDisable`: 完全禁用SWJ调试

#### 端口源定义
用于重映射和外部中断配置。
- `GPIO_PortSourceGPIOA` 到 `GPIO_PortSourceGPIOF`: GPIO端口源
- `GPIO_PinsSource0` 到 `GPIO_PinsSource15`: GPIO引脚源

#### 支持的GPIO外设
- **GPIOA**: 端口A，包含16个通用IO引脚
- **GPIOB**: 端口B，包含16个通用IO引脚
- **GPIOC**: 端口C，包含16个通用IO引脚
- **GPIOD**: 端口D，包含16个通用IO引脚
- **GPIOE**: 端口E，包含16个通用IO引脚
- **GPIOF**: 端口F，包含16个通用IO引脚

### 使用示例

#### 基本GPIO配置示例
```c
// LED控制示例 - 配置PA5为推挽输出
void LED_GPIO_Config(void)
{
    GPIO_InitType GPIO_InitStructure;

    // 1. 使能GPIOA时钟
    RCC_AHBPeriphClockCmd(RCC_AHBPeriph_GPIOA, ENABLE);

    // 2. 配置PA5为推挽输出，50MHz
    GPIO_InitStructure.GPIO_Pins = GPIO_Pins_5;
    GPIO_InitStructure.GPIO_MaxSpeed = GPIO_MaxSpeed_50MHz;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_OUT_PP;
    GPIO_Init(GPIOA, &GPIO_InitStructure);

    // 3. 初始状态设为低电平 (LED熄灭)
    GPIO_ResetBits(GPIOA, GPIO_Pins_5);
}

// LED控制函数
void LED_On(void)
{
    GPIO_SetBits(GPIOA, GPIO_Pins_5);  // 点亮LED
}

void LED_Off(void)
{
    GPIO_ResetBits(GPIOA, GPIO_Pins_5);  // 熄灭LED
}

void LED_Toggle(void)
{
    if(GPIO_ReadOutputDataBit(GPIOA, GPIO_Pins_5) == SET)
        GPIO_ResetBits(GPIOA, GPIO_Pins_5);
    else
        GPIO_SetBits(GPIOA, GPIO_Pins_5);
}
```

#### 按键输入示例
```c
// 按键配置示例 - 配置PA0为下拉输入
void Button_GPIO_Config(void)
{
    GPIO_InitType GPIO_InitStructure;

    // 1. 使能GPIOA时钟
    RCC_AHBPeriphClockCmd(RCC_AHBPeriph_GPIOA, ENABLE);

    // 2. 配置PA0为下拉输入
    GPIO_InitStructure.GPIO_Pins = GPIO_Pins_0;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN_PD;  // 下拉输入
    GPIO_Init(GPIOA, &GPIO_InitStructure);
}

// 按键检测函数
uint8_t Button_IsPressed(void)
{
    return (GPIO_ReadInputDataBit(GPIOA, GPIO_Pins_0) == SET);
}

// 带去抖动的按键检测
uint8_t Button_ReadWithDebounce(void)
{
    static uint8_t buttonState = 0;
    static uint32_t lastTime = 0;

    uint8_t currentState = GPIO_ReadInputDataBit(GPIOA, GPIO_Pins_0);
    uint32_t currentTime = Get_Tick();  // 假设有系统滴答函数

    if(currentState != buttonState)
    {
        if((currentTime - lastTime) > 20)  // 20ms去抖动
        {
            buttonState = currentState;
            lastTime = currentTime;
        }
    }

    return buttonState;
}
```

#### 外部中断配置示例
```c
// 配置PA0为外部中断输入
void EXTI_Config(void)
{
    GPIO_InitType GPIO_InitStructure;

    // 1. 使能时钟
    RCC_AHBPeriphClockCmd(RCC_AHBPeriph_GPIOA, ENABLE);
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_AFIO, ENABLE);

    // 2. 配置PA0为下拉输入
    GPIO_InitStructure.GPIO_Pins = GPIO_Pins_0;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN_PD;
    GPIO_Init(GPIOA, &GPIO_InitStructure);

    // 3. 配置EXTI线0连接到PA0
    GPIO_EXTILineConfig(GPIO_PortSourceGPIOA, GPIO_PinsSource0);

    // 4. 配置EXTI
    EXTI_InitType EXTI_InitStructure;
    EXTI_InitStructure.EXTI_Line = EXTI_Line0;
    EXTI_InitStructure.EXTI_Mode = EXTI_Mode_Interrupt;
    EXTI_InitStructure.EXTI_Trigger = EXTI_Trigger_Rising;
    EXTI_InitStructure.EXTI_LineEnable = ENABLE;
    EXTI_Init(&EXTI_InitStructure);

    // 5. 配置NVIC
    NVIC_InitType NVIC_InitStructure;
    NVIC_InitStructure.NVIC_IRQChannel = EXTI0_IRQn;
    NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 1;
    NVIC_InitStructure.NVIC_IRQChannelSubPriority = 1;
    NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;
    NVIC_Init(&NVIC_InitStructure);
}

// 外部中断处理函数
void EXTI0_IRQHandler(void)
{
    if(EXTI_GetITStatus(EXTI_Line0) == SET)
    {
        // 清除中断标志
        EXTI_ClearITPendingBit(EXTI_Line0);

        // 处理按键事件
        // ...
    }
}
```

#### 复用功能配置示例
```c
// USART1复用功能配置 (PA9-TX, PA10-RX)
void USART1_GPIO_Config(void)
{
    GPIO_InitType GPIO_InitStructure;

    // 1. 使能时钟
    RCC_AHBPeriphClockCmd(RCC_AHBPeriph_GPIOA, ENABLE);
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_USART1, ENABLE);

    // 2. 配置PA9为复用推挽输出 (TX)
    GPIO_InitStructure.GPIO_Pins = GPIO_Pins_9;
    GPIO_InitStructure.GPIO_MaxSpeed = GPIO_MaxSpeed_50MHz;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP;  // 复用推挽
    GPIO_Init(GPIOA, &GPIO_InitStructure);

    // 3. 配置PA10为浮空输入 (RX)
    GPIO_InitStructure.GPIO_Pins = GPIO_Pins_10;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN_FLOATING;  // 浮空输入
    GPIO_Init(GPIOA, &GPIO_InitStructure);
}
```

#### I2C开漏输出配置示例
```c
// I2C1复用功能配置 (PB6-SCL, PB7-SDA)
void I2C1_GPIO_Config(void)
{
    GPIO_InitType GPIO_InitStructure;

    // 1. 使能时钟
    RCC_AHBPeriphClockCmd(RCC_AHBPeriph_GPIOB, ENABLE);
    RCC_APB1PeriphClockCmd(RCC_APB1Periph_I2C1, ENABLE);

    // 2. 配置PB6和PB7为复用开漏输出
    GPIO_InitStructure.GPIO_Pins = GPIO_Pins_6 | GPIO_Pins_7;
    GPIO_InitStructure.GPIO_MaxSpeed = GPIO_MaxSpeed_50MHz;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_OD;  // 复用开漏
    GPIO_Init(GPIOB, &GPIO_InitStructure);
}
```

### 使用建议
1. **速度选择**：低速应用选择2MHz或10MHz以降低功耗，高速应用选择50MHz
2. **输入模式**：悬空的引脚使用下拉或上拉输入，避免浮空输入引入干扰
3. **输出驱动**：驱动LED等负载使用推挽输出，I2C总线使用开漏输出
4. **引脚锁定**：重要配置完成后可锁定引脚，防止意外修改
5. **时钟使能**：使用GPIO前必须先使能对应端口的AHB时钟
6. **复用功能**：外设使用前需要先配置GPIO为相应的复用功能模式

### 注意事项
1. **电源域**：不同GPIO端口可能属于不同的电源域
2. **5V容忍**：部分引脚支持5V容忍，使用前需查阅数据手册
3. **ESD保护**：所有GPIO引脚都有ESD保护电路
4. **复位状态**：复位后所有GPIO默认为浮空输入模式
5. **原子操作**：对开漏输出的位操作应使用GPIO_OD_WriteBit函数

---

## 总结

本文档提供了 V32G410x 微控制器所有外设模块的完整 API 参考信息，包含详细的参数说明、使用示例和开发建议。

### 文档特点
✅ **完整性** - 涵盖了所有 22 个主要功能模块
✅ **准确性** - 严格按照头文件中的接口定义生成
✅ **实用性** - 包含详细的参数说明和使用示例
✅ **结构化** - 按模块分类，层次清晰
✅ **开发友好** - 可直接用于嵌入式程序开发参考

### 包含的主要模块
1. **系统基础**: 配置模块、中断控制、时钟管理、电源管理
2. **通信接口**: USART/UART、SPI、I2C、CAN
3. **输入输出**: GPIO通用输入输出、外部中断
4. **定时控制**: 定时器模块、实时时钟、看门狗
5. **数据处理**: ADC模数转换、DMA直接存储器访问
6. **存储管理**: Flash存储、备份寄存器、CRC校验
7. **调试支持**: 调试模块

### 开发流程建议

#### 1. 系统初始化流程
```c
// 基本系统初始化顺序
void System_Init(void)
{
    // 1. 配置系统时钟
    RCC_SystemClock_Config();

    // 2. 配置中断优先级分组
    NVIC_PriorityGroupConfig(NVIC_PriorityGroup_2);

    // 3. 初始化GPIO（根据需求）
    GPIO_Basic_Config();

    // 4. 初始化外设（根据需求）
    USART_Config();
    Timer_Config();

    // 5. 使能系统滴答定时器
    SysTick_Init();
}
```

#### 2. 外设使用通用步骤
1. **使能时钟** - RCC_APBxPeriphClockCmd() 或 RCC_AHBPeriphClockCmd()
2. **配置GPIO** - GPIO_Init()（如需要）
3. **配置外设参数** - 对应的XXX_Init()函数
4. **使能外设** - XXX_Cmd()函数
5. **配置中断** - XXX_INTConfig() + NVIC_Init()（如需要）
6. **编写中断处理** - 中断服务函数

#### 3. 常用配置模板
- **串口通信**: USART → GPIO + NVIC配置
- **数字输入**: GPIO输入 → 外部中断配置
- **定时控制**: 定时器 → 中断配置
- **ADC采集**: ADC → DMA配置 → 中断配置

### 使用建议

#### 开发最佳实践
1. **时钟配置优先** - 先配置系统时钟，再初始化外设
2. **GPIO配置规范** - 根据功能选择合适的模式和速度
3. **中断管理规范** - 合理分配优先级，中断函数保持简短
4. **DMA使用建议** - 高速数据传输优先使用DMA
5. **看门狗配置** - 重要系统建议配置看门狗监控

#### 调试技巧
1. **断言使用** - 开发阶段启用断言检查参数
2. **状态标志** - 善用状态标志检查外设状态
3. **错误处理** - 检查函数返回值，处理错误情况
4. **日志输出** - 使用串口输出调试信息

#### 性能优化
1. **GPIO速度选择** - 根据需求选择合适速度，降低EMI
2. **时钟优化** - 关闭不使用的外设时钟
3. **中断优化** - 减少中断处理时间，避免嵌套过深
4. **DMA优化** - 合理配置DMA优先级和缓冲区大小

### 注意事项

#### 硬件相关
1. **引脚复用** - 注意引脚功能冲突，合理规划引脚使用
2. **电气特性** - 注意电压等级、驱动能力、ESD保护
3. **时钟约束** - 外设时钟不能超过最大工作频率
4. **电源管理** - 合理使用低功耗模式

#### 软件相关
1. **并发访问** - 注意中断和主程序的资源冲突
2. **状态同步** - 使用原子操作或临界区保护共享资源
3. **内存管理** - 合理使用栈空间和堆空间
4. **版本兼容** - 注意库版本和芯片型号的匹配

### 常见问题解决方案

#### 1. 外设不工作
- 检查时钟是否使能
- 检查GPIO配置是否正确
- 检查外设参数是否在有效范围内

#### 2. 中断不触发
- 检查中断是否使能
- 检查NVIC配置是否正确
- 检查中断标志是否需要手动清除

#### 3. 通信异常
- 检查波特率、时钟配置是否匹配
- 检查GPIO模式是否为复用功能
- 检查硬件连接是否正确

### 参考资源

#### 数据手册
- V32G410x 数据手册（硬件规格）
- V32G410x 参考手册（外设详细说明）

#### 开发工具
- IDE支持：Keil MDK, IAR EWARM
- 调试工具：J-Link, ST-Link
- 仿真工具：Proteus, Altium Designer

### 版本信息
- **库版本**: V1.0.0
- **文档版本**: 1.0
- **适用芯片**: V32G410x系列
- **最后更新**: 2022-08-17

---

**重要提示**: 本文档严格按照头文件定义生成，确保了信息的准确性。在实际开发中，如遇到特殊情况，请参考最新的芯片数据手册和官方技术文档。