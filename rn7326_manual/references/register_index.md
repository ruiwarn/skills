# RN7326/RN202x 寄存器快速索引

> 自动生成自 manual.md，共 705 个寄存器定义
> 使用方法：找到寄存器行号后，用 `Read(offset=行号-10, limit=50)` 读取详细信息

---

## 📑 章节目录

| 章节 | 标题 | 行号 |
|------|------|------|
| 1 | 概述 24 | 28 |
| 5 | 三相计量单元 | 132 |
| 7 | 错误接线检测 | 243 |
| 8 | 误差温度补偿（新增） 248 | 247 |
| 11 | CRC (新增) 302 | 410 |
| 14 | 模拟外设 325 | 502 |
| 15 | RTC 334 | 522 |
| 23 | SPI、UART 通用 DMA 控制器 | 691 |
| 24 | UART 469 | 723 |
| 25 | SPI 1/3/4 (支持普通 DMA) | 751 |
| 26 | 高速SPIS（支持普通DMA） 485 | 775 |
| 27 | SPI0(支持专用DMA) 495 | 802 |
| 30 | LPUART (新增) | 878 |
| 31 | CAN (FLEX CAN) (新增) 539 | 920 |
| 32 | 安全密码加速器 SEA（新增） 585 | 982 |
| 33 | 编程支持 | 1011 |
| 34 | 选项字节 | 1028 |
| 1 | 概述 | 1042 |
| 2 | 电气特性 | 1515 |
| 3 | 系统控制 | 1529 |
| 4 | 处理器架构 | 1901 |
| 5 | 三相计量单元 | 2142 |
| 6 | 全失压测量 | 4840 |
| 7 | 错误接线检测 | 4995 |
| 8 | 误差温度补偿（新增） | 5009 |
| 9 | 闪变 | 5396 |
| 10 | DSP核 | 5504 |
| 11 | CRC（新增） | 6669 |
| 12 | 内存搬运单元（新增） | 7175 |
| 13 | 通用ADC | 7337 |

---

## 📋 寄存器索引（按模块）

### 1. 概述

| 地址 | 寄存器名 | 行号 |
|------|----------|------|
| 0X00 | WDT_EN | 554 |
| 0X04 | WDT_CTRL | 555 |
| 0X08 | WDT_PASS | 556 |
| 0X14 | WDT_HALT | 557 |
| 0X18 | WDT STBY | 558 |
| 0X00 | WDT_EN | 8157 |
| 0X04 | WDT_CTRL | 8163 |
| 0X08 | WDT_PASS | 8172 |
| 0X14 | WDT_HALT | 8179 |
| 0X18 | WDT_STBY | 8194 |

### 3. 系统控制 (SYS)

| 地址 | 寄存器名 | 行号 |
|------|----------|------|
| 0X00 | OSC_CTL1 | 80 |
| 0X04 | SYS_MODE | 81 |
| 0X08 | SYS PD | 82 |
| 0X0C | ADC CTL | 83 |
| 0X18 | SYS_RST1 | 84 |
| 0X1C | OSC_CTL2 | 85 |
| 0X20 | SYS_RST | 86 |
| 0X24 | SYS(MapCTL | 87 |
| 0X28 | MOD0_EN | 88 |
| 0X2C | MOD1 EN | 89 |
| 0X30 | INTC_EN | 90 |
| 0X34 | KBI_EN | 91 |
| 0X38 | CHIP_ID | 92 |
| 0X3C | SYS PS | 93 |
| 0X40 | IRFR_CTL | 94 |
| 0XA4 | TRIM_START | 96 |
| 0XBC | SYS CFG | 97 |
| 0XC0 | DMA_PR1 | 98 |
| 0XC4 | DMA RST | 99 |
| 0XC8 | FLKEN CTL | 100 |
| 0XCC | DMA PRI2 | 101 |
| 0XD0 | DMA_RST2 | 102 |
| 0X100 | CAN CFG | 103 |
| 0X114 | ADCIN CTL | 104 |
| 0X00 | OSC_CTL1 | 1693 |
| 0X04 | SYS_MODE | 1699 |
| 0X08 | SYS_PD | 1712 |
| 0X0C | ADC_CTL | 1724 |
| 0X18 | SYS_RST1 | 1730 |
| 0X1C | OSC_CTL2 | 1736 |
| 0X20 | SYS_RST | 1750 |
| 0X24 | SYS_MAPCTL | 1756 |
| 0X28 | MOD0_EN | 1764 |
| 0X2C | MOD1_EN | 1774 |
| 0X30 | INTC_EN | 1780 |
| 0X34 | KBI_EN | 1786 |
| 0X38 | CHIP_ID | 1792 |
| 0X3C | SYS_PS | 1799 |
| 0X40 | IRFR_CTL | 1805 |
| 0XA0 | TRIM_CFG1 | 1811 |
| 0XA4 | TRIM_START | 1817 |
| 0XBC | SYS_CFG | 1835 |
| 0XC0 | DMA_PRI | 1841 |
| 0XC4 | DMA_RST | 1859 |
| 0XC8 | FLKEN_CTL | 1865 |
| 0XCC | DMA_PRE12 | 1871 |
| 0XD0 | DMA_RST2 | 1877 |
| 0X100 | CAN_CFG | 1883 |
| 0X114 | ADCIN_CTL | 1889 |

### 5. 三相计量单元 (EMU)

| 地址 | 寄存器名 | 行号 |
|------|----------|------|
| 0X2FC | SPCMD | 168 |
| 0X434 | 相角 | 175 |
| 0X698 | HFCONST | 178 |
| 0X08 | Start | 179 |
| 0X10 | LostVoltage | 181 |
| 0X14 | ZXOT | 182 |
| 0X7B0 | ZXOT_Num | 183 |
| 0X18 | PRTHx | 184 |
| 0X28 | Iregion | 185 |
| 0X30 | PHSU/I | 186 |
| 0X4C | GSU/I | 187 |
| 0X68 | DCOSx | 188 |
| 0X164 | OVLVL | 195 |
| 0X168 | OILVL | 196 |
| 0X17C | MODSEL | 197 |
| 0X180 | CFCFG | 198 |
| 0X18C | EMUCON | 200 |
| 0X198 | PQSign | 202 |
| 0X19C | Noload | 203 |
| 0X1A0 | IRegionS | 204 |
| 0X1A4 | PHASES | 205 |
| 0X1AC | Rdata | 207 |
| 0X1B4 | ZXOTU | 209 |
| 0X1B8 | AUTODC_EN | 210 |
| 0X1BC | ZXOTCFG | 211 |
| 0X6B4 | 特殊计量单元配置 | 221 |
| 0X7AC | ECTCFG | 223 |
| 0X2FC | SPCMD | 3168 |
| 0X434 | 相角 | 3367 |
| 0X450 | 合相电压线频率 | 3381 |
| 0XC64 | 分相电压线频率UxFreq | 3393 |
| 0X574 | 半波有效值 | 3407 |
| 0X58C | 半波峰值 | 3423 |
| 0X698 | HFCONST | 3431 |
| 0X08 | Start | 3475 |
| 0X10 | LostVoltage | 3519 |
| 0X14 | ZXOT | 3535 |
| 0X7B0 | ZXOT_Num | 3551 |
| 0X18 | PRTHx | 3557 |
| 0X28 | Iregion | 3575 |
| 0X30 | PHSU/I | 3587 |
| 0X4C | GSU/I | 3651 |
| 0X68 | DCOSx | 3673 |
| 0X68C | HW_PNum | 3873 |
| 0X690 | HW_QNum | 3879 |
| 0X694 | HW_PQCFG | 3885 |
| 0X7EC | HWRMS_DCYC0 | 3891 |
| 0X7F0 | HWRMS_DCYC1 | 3897 |
| 0X7F4 | HWRMS_DCYC2 | 3903 |
| 0X7F8 | HWPQ_DCYC0 | 3909 |
| ... | （共 137 个寄存器） | ... |

### 6. 全失压测量

| 地址 | 寄存器名 | 行号 |
|------|----------|------|
| 0X00 | IE | 235 |
| 0X04 | IF | 236 |
| 0X08 | LS_CFG | 237 |
| 0X0C | LS_DCOS_Ix | 238 |
| 0X18 | LS_THOx | 239 |
| 0X24 | RMS_Lx | 240 |
| 0X3C | NVM_PSW | 241 |
| 0X00 | IE | 4919 |
| 0X04 | IF | 4925 |
| 0X08 | LS_CFG | 4931 |
| 0X0C | LS_DCOSIx | 4937 |
| 0X18 | LS_THOx | 4959 |
| 0X24 | RMS_Lx | 4965 |
| 0X3C | NVM_PSW | 4985 |

### 8. 误差温度补偿

| 地址 | 寄存器名 | 行号 |
|------|----------|------|
| 0X0 | WREN | 271 |
| 0X4 | CTRL | 272 |
| 0X8 | EN | 273 |
| 0XC | STATUS | 274 |
| 0X10 | IE | 275 |
| 0X14 | LT SET | 276 |
| 0X18 | HT_SET | 277 |
| 0X1C | TIMER_SET | 278 |
| 0X20 | PROT TEMP | 279 |
| 0X24 | PROT IxGAIN | 281 |
| 0X30 | PROT_UxGAIN | 282 |
| 0X40 | LT_KIx | 283 |
| 0X4C | LT_KUx | 284 |
| 0X5C | HT_KIx | 285 |
| 0X68 | HT KU | 286 |
| 0X7C | IxGAIN | 288 |
| 0X88 | UxGAIN | 289 |
| 0X0 | WREN | 5233 |
| 0X4 | CTRL | 5239 |
| 0X8 | EN | 5245 |
| 0XC | STATUS | 5251 |
| 0X10 | IE | 5257 |
| 0X14 | LT_SET | 5263 |
| 0X18 | HT_SET | 5269 |
| 0X1C | TIMER_SET | 5275 |
| 0X20 | PROT_TEMP | 5281 |
| 0X24 | PROT_IxGAIN | 5287 |
| 0X30 | PROT_UxGAIN | 5293 |
| 0X40 | LT_KIx | 5299 |
| 0X4C | LT_KUx | 5305 |
| 0X5C | HT_KlX | 5311 |
| 0X68 | HT_KU | 5317 |
| 0X78 | TEMP | 5323 |
| 0X7C | IxGAIN | 5331 |
| 0X88 | UxGAIN | 5339 |
| 0X98 | TEMP_UD | 5345 |

### 9. 闪变

| 地址 | 寄存器名 | 行号 |
|------|----------|------|
| 0X00 | FLK_EN | 307 |
| 0X04 | FLK_IE | 308 |
| 0X08 | FLK_IF | 309 |
| 0X0C | FLK_Ux | 310 |
| 0X18 | Ux_500Hz/400Hz | 311 |
| 0X24 | Ux_Sum | 312 |
| 0X3C | Sum_Cnt | 313 |
| 0X80 | Ux_Mean | 314 |
| 0X90 | Sum_Rst | 315 |
| 0X94 | FLK_PASS | 316 |
| 0X00 | FLK_EN | 5440 |
| 0X04 | FLK_IE | 5446 |
| 0X08 | FLK_IF | 5452 |
| 0X0C | FLK_Ux | 5460 |
| 0X18 | Ux_500Hz/400Hz | 5466 |
| 0X24 | Ux_Sum | 5472 |
| 0X3C | Sum_Cnt | 5480 |
| 0X80 | Ux_Mean | 5486 |
| 0X90 | Sum_Rst | 5492 |
| 0X94 | FLK_PASS | 5498 |

### 10. DSP加速器

| 地址 | 寄存器名 | 行号 |
|------|----------|------|
| 0X0 | MAC_CTL0 | 364 |
| 0X04 | MAC_CTL1 | 365 |
| 0X90 | MAC CTL2 | 366 |
| 0X08 | MAC_IN0 | 367 |
| 0X0C | MAC IN1 | 368 |
| 0X10 | MAC_IN2 | 369 |
| 0X14 | MAC_IN3 | 370 |
| 0X18 | MAC_IN4 | 371 |
| 0X1C | MAC IN5 | 372 |
| 0X20 | MAC_OUT0 | 373 |
| 0X24 | MAC OUT1 | 374 |
| 0X28 | MAC_OUT2 | 375 |
| 0X2C | MAC OUT3 | 376 |
| 0X30 | DIV_IN0 | 377 |
| 0X34 | DIV_IN1 | 378 |
| 0X38 | DIV_OUT | 379 |
| 0X3C | DMA SRBADR | 381 |
| 0X40 | DMA_SIBADR | 382 |
| 0X44 | DMA_PRBADR | 383 |
| 0X48 | DMA_PIBADR | 384 |
| 0X4C | DMA_TRBADR | 385 |
| 0X50 | DMA_TIBADR | 386 |
| 0X54 | DMA_LEN | 387 |
| 0X5C | DSP FLG | 389 |
| 0X60 | ALU_STA0 | 390 |
| 0X64 | ALU_sta1 | 391 |
| 0X68 | CRD_CTL | 392 |
| 0X6C | CRD_XIN | 393 |
| 0X70 | CRD_YIN | 394 |
| 0X74 | CRD_AMP | 395 |
| 0X78 | CRD PHASE | 396 |
| 0X7C | CRDAngle | 397 |
| 0X80 | CRD_COSINE | 398 |
| 0X84 | CRD_SINE | 399 |
| 0X88 | CRD IE | 400 |
| 0X8C | CRD_FLG | 401 |
| 0X94 | INTP LEN | 402 |
| 0X98 | INTP_LOC | 403 |
| 0X9C | INTP_STEP | 404 |
| 0X0 | MAC_CTL0 | 6372 |
| 0X04 | MAC_CTL1 | 6378 |
| 0X90 | MAC_CTL2 | 6386 |
| 0X08 | MAC_IN0 | 6396 |
| 0X0C | MAC_IN1 | 6402 |
| 0X10 | MAC_IN2 | 6408 |
| 0X14 | MAC_IN3 | 6417 |
| 0X18 | MAC_IN4 | 6423 |
| 0X1C | MAC_IN5 | 6429 |
| 0X24 | MAC_OUT1 | 6441 |
| 0X28 | MAC_OUT2 | 6447 |
| ... | （共 78 个寄存器） | ... |

### 11. CRC

| 地址 | 寄存器名 | 行号 |
|------|----------|------|
| 0X00 | CRC DR | 433 |
| 0X04 | CRC_STA | 434 |
| 0X08 | CRC CTRL | 435 |
| 0X0C | CRC INIT | 436 |
| 0X10 | CRC POL | 437 |
| 0X14 | CRC XOR | 438 |
| 0X18 | CRC DMA CTL | 439 |
| 0X1C | CRC_DMA_BADR | 440 |
| 0X20 | CRC_DMA_LEN | 441 |
| 0X24 | CRC_DMA_ADR | 442 |
| 0X28 | CRC_DMA_IE | 443 |
| 0X2C | CRC DMA FLG | 444 |
| 0X24 | CRC_DMA_ADR | 6873 |
| 0X2C | CRC_DMA_FLG | 6889 |

### 12. M2M DMA

| 地址 | 寄存器名 | 行号 |
|------|----------|------|
| 0X0 | M2M_MODE | 477 |
| 0X4 | M2M_CTL | 478 |
| 0X8 | M2M_DUMMY | 479 |
| 0XC | M2M SADDR | 480 |
| 0X10 | M2M_DADDR | 481 |
| 0X14 | M2M_ILEN | 482 |
| 0X18 | M2M IE | 483 |
| 0X1C | M2M_IF | 484 |
| 0X0 | M2M_MODE | 7273 |
| 0X4 | M2M_CTL | 7281 |
| 0X8 | M2M_DUMMY | 7289 |
| 0XC | M2M_SADDR | 7295 |
| 0X10 | M2M_DADDR | 7301 |
| 0X14 | M2MILEN | 7308 |
| 0X18 | M2M_IE | 7315 |
| 0X1C | M2M_IF | 7321 |

### 13. GPADC

| 地址 | 寄存器名 | 行号 |
|------|----------|------|
| 0X00 | GPADC_CTL0 | 494 |
| 0X04 | GPADC CTL1 | 495 |
| 0X08 | GPADC RATIO | 496 |
| 0X0C | GPADC_IE | 497 |
| 0X10 | GPADC_IF | 498 |
| 0X14 | GPADC_OUT | 499 |
| 0X18 | GPADC_R2RBUF_CTL | 500 |
| 0X00 | GPADC_CTL0 | 7364 |
| 0X04 | GPADC_CTL1 | 7370 |
| 0X08 | GPADC_RATIO | 7390 |
| 0X0C | GPADC_IE | 7396 |
| 0X10 | GPADC_IF | 7402 |
| 0X14 | GPADC_OUT | 7408 |
| 0X18 | GPADC_R2RBUF_CTL | 7414 |

### 14. 模拟外设 (SAR/LVD)

| 地址 | 寄存器名 | 行号 |
|------|----------|------|
| 0X00 | SAR_CTL | 509 |
| 0X04 | SAR_START | 510 |
| 0X08 | SAR_STATUS | 511 |
| 0X0C | SAR_DAT | 512 |
| 0X10 | LVD_CTL | 513 |
| 0X14 | LVD_STAT | 514 |
| 0X1C | SAR_DAT2 | 516 |
| 0X00 | SAR_CTL | 7465 |
| 0X04 | SAR_START | 7473 |
| 0X08 | SAR_STATUS | 7481 |
| 0X0C | SAR_DAT | 7489 |
| 0X10 | LVD_CTL | 7497 |
| 0X14 | LVD_STAT | 7507 |
| 0X1C | SAR_DAT2 | 7525 |

### 15. RTC

| 地址 | 寄存器名 | 行号 |
|------|----------|------|
| 0X00 | RTC_CTL | 7678 |
| 0X04 | RTC_SC | 7684 |
| 0X08 | RTC_MN | 7690 |
| 0X0C | RTC_HR | 7696 |
| 0X10 | RTC_DT | 7702 |
| 0X14 | RTC_MO | 7708 |
| 0X18 | RTC_YR | 7714 |
| 0X1C | RTC_DW | 7720 |
| 0X20 | RTC_CNT1 | 7727 |
| 0X24 | RTC_CNT2 | 7733 |
| 0X28 | RTC_SCA | 7739 |
| 0X2C | RTC_MNA | 7745 |
| 0X30 | RTC_HRA | 7751 |
| 0X34 | RTC_IE | 7761 |
| 0X38 | RTC_IF | 7767 |
| 0X3C | RTC_TEMP | 7773 |
| 0XF8 | RTC_TEMP2 | 7781 |
| 0XC4 | RTC_TEMPOS | 7787 |
| 0XC8 | RTC_TPSIN | 7795 |
| 0X150 | TPS_START | 7801 |
| 0X154 | TEMP_CAL | 7807 |
| 0XFC | VBAT_CLKSEL | 7814 |
| 0X6C | LOSC_CFG1 | 7824 |
| 0XFC | BAT_CLKSEL | 7835 |
| 0X40 | RTC_PS | 7843 |
| 0X44 | RTC_MODE | 7849 |
| 0X48 | RTC_DOTA0 | 7860 |
| 0X4C | RTC_ALPHAL | 7869 |
| 0X50 | RTC_ALPHAH | 7883 |
| 0X54 | RTC_XT0 | 7891 |
| 0X58 | RTC_TADJ | 7899 |
| 0X60 | RTC_ZT | 7905 |
| 0X130 | RTC_MODE1 | 7917 |
| 0X134 | RTC_XT1 | 7923 |
| 0X138 | RTC ALPHA | 7931 |
| 0X13C | RTC_BETA | 7937 |
| 0X140 | RTC_GAMMA | 7943 |
| 0X144 | RTC_ZETA | 7952 |
| 0XCC | RTC_CALPS | 7962 |
| 0XD0 | RTC_CAL_T0~T9 | 7968 |
| 0X64 | RTC[DOTAT | 7976 |
| 0X74 | RTC_FPTR | 7984 |
| 0X78 | RTC_FDTR1S | 7992 |
| 0X7C | RTC_FDTR30S | 7998 |
| 0X84 | RTC_FDTR120S | 8004 |
| 0X8C | RTC_IOMODE | 8012 |
| 0X180 | I2CMEEP_CTL | 8024 |
| 0X184 | I2CMEEP_CPASS | 8030 |
| 0X188 | I2CMEEP_CBYTE | 8038 |
| 0X18C | I2CMEEP_ABYTE | 8044 |

### 17. 定时器 (TC/PWM)

| 地址 | 寄存器名 | 行号 |
|------|----------|------|
| 0X00 | TC_CNT | 574 |
| 0X04 | TC_PS | 575 |
| 0X0C | TC_DN | 576 |
| 0X14 | TC_CCD0 | 577 |
| 0X18 | TC_CCD1 | 578 |
| 0X1C | TC_CCFG | 579 |
| 0X20 | TC_CR | 580 |
| 0X24 | TC_CM0 | 581 |
| 0X28 | TC_CM1 | 582 |
| 0X2C | TC_IE | 583 |
| 0X30 | TC STA | 584 |
| 0X34 | PWM_CFG | 596 |
| 0X38 | PWM_CTL | 597 |
| 0X3C | PWM STA | 598 |
| 0X4C | PWM_DMA_ADR | 603 |
| 0X00 | TC_CNT | 8357 |
| 0X04 | TC_PS | 8363 |
| 0X0C | TC_DN | 8369 |
| 0X14 | TC_CCD0 | 8375 |
| 0X18 | TC_CCD1 | 8384 |
| 0X1C | TC_CCFG | 8390 |
| 0X20 | TC_CR | 8398 |
| 0X24 | TC_CM0 | 8408 |
| 0X28 | TC_CM1 | 8414 |
| 0X2C | TC_IE | 8420 |
| 0X30 | TC_STA | 8426 |
| 0X34 | PWM_CFG | 8568 |
| 0X38 | PWM_CTL | 8576 |
| 0X3C | PWM_STA | 8582 |
| 0X40 | PWM CNT | 8588 |
| 0X44 | PWM_DMA_BADR | 8596 |
| 0X48 | PWM_DMA_LEN | 8602 |
| 0X4C | PWM_DMA_ADR | 8608 |

### 18. 简易定时器

| 地址 | 寄存器名 | 行号 |
|------|----------|------|
| 0X0 | CTRL | 617 |
| 0X4 | LOAD | 618 |
| 0X8 | VAL | 619 |
| 0X0 | CTRL | 8753 |
| 0X4 | LOAD | 8758 |
| 0X8 | VAL | 8762 |

### 19. GPIO

| 地址 | 寄存器名 | 行号 |
|------|----------|------|
| 0X00 | （输入或者输出）：PMA | 8887 |
| 0X04 | 0：PCA0 | 8898 |
| 0X08 | 1：PCA1 | 8904 |
| 0X28 | 2：PCA2 | 8912 |
| 0X0C | ：PUA | 8918 |
| 0X10 | PA口内部模式配置0：PIMA0 | 8926 |
| 0X14 | PA口内部模式配置1：PIMA1 | 8932 |
| 0X18 | PA口输入使能：PIEA | 8938 |
| 0X1C | ：PA | 8944 |
| 0X20 | ：PASET | 8951 |
| 0X24 | ：PACLR | 8959 |
| 0X2C | PB1 口内部模式配置 2: PIMB2 | 8970 |
| 0X30 | （输入或者输出）：PMB1 | 8976 |
| 0X34 | 0: PCB1 | 8985 |
| 0X38 | ：PUB1 | 8991 |
| 0X3C | PB1口内部模式配置：PIMB1 | 8999 |
| 0X40 | PB1口输入使能：PIEB1 | 9005 |
| 0X44 | ：PB1 | 9016 |
| 0X48 | ：PB1SET | 9022 |
| 0X4C | ：PB1CLR | 9030 |
| 0X50 | ：GPIO_PSW0 | 9043 |
| 0X054 | ：IOCNT | 9049 |
| 0X58 | 1: PCB3 | 9068 |
| 0X5C | （输入或者输出）：PMC | 9074 |
| 0X64 | ：PUC | 9083 |
| 0X68 | PC口内部模式配置0：PIMC0 | 9091 |
| 0X6C | PC口内部模式配置1：PIMC1 | 9097 |
| 0X70 | PC口输入使能：PIEC | 9103 |
| 0X74 | ：PC | 9109 |
| 0X78 | ：PCSET | 9115 |
| 0X7C | ：PCCLR | 9123 |
| 0X80 | ：IOCFG_UART_I2C | 9131 |
| 0X60 | ：PCC | 9167 |
| 0X84 | 0: IOCFG_KEY0 | 9173 |
| 0X88 | 1: IOCFG_KEY1 | 9187 |
| 0X8C | 0: IOCFG_INT0 | 9200 |
| 0X90 | 1: IOCFG_INT1 | 9210 |
| 0X94 | ：IOCFG IOCNT | 9219 |
| 0X98 | ：SPIDRV_CFG | 9225 |
| 0X9C | ：IODRV_CFG | 9231 |
| 0X100 | （输入或者输出）：PMB0 | 9241 |
| 0X104 | 0：PCB0 | 9251 |
| 0X108 | ：PUB0 | 9268 |
| 0X10C | PB0口内部模式配置0：PIMB0 | 9276 |
| 0X110 | PB0口输入使能：PIEB0 | 9282 |
| 0X114 | ：PB0 | 9288 |
| 0X118 | ：PBSET0 | 9294 |
| 0X11C | ：PBCLR0 | 9305 |
| 0X120 | ：GPIO_PSW1 | 9313 |
| 0X124 | ：PB0MASK | 9319 |
| ... | （共 51 个寄存器） | ... |

### 20. 外部中断 (INTC)

| 地址 | 寄存器名 | 行号 |
|------|----------|------|
| 0X00 | INTC_CTL | 644 |
| 0X00 | KBI_CTL | 645 |
| 0X04 | INTC_MODE | 646 |
| 0X08 | INTC_MASK | 647 |
| 0X0C | INTC_STA | 648 |
| 0X00 | INTC_CTL | 9375 |
| 0X00 | KBI_CTL | 9382 |
| 0X04 | INTC_MODE | 9389 |
| 0X08 | INTC_MASK | 9402 |
| 0X0C | INTC_STAT | 9411 |

### 21. 按键中断 (KBI)

| 地址 | 寄存器名 | 行号 |
|------|----------|------|
| 0X04 | KBI_CTL | 655 |
| 0X04 | KBI_SEL | 656 |
| 0X08 | KBI_DATA | 657 |
| 0X0C | KBI MASK | 659 |
| 0X04 | KBI_CTL | 9436 |
| 0X04 | KBI_SEL | 9443 |
| 0X08 | KBI_DATA | 9452 |
| 0X0C | KBI_MASK | 9461 |

### 22. 脉冲转发 (IOCNT)

| 地址 | 寄存器名 | 行号 |
|------|----------|------|
| 0X00 | IOCNT_CFG0~4 | 682 |
| 0X20 | IOCNT OUT0~4 | 683 |
| 0X40 | IOCNT CHNL | 684 |
| 0X48 | IOCNT_CTL | 685 |
| 0X4C | IOCNT CTL1 | 686 |
| 0X00 | IOCNT_CFG0~4 | 9745 |
| 0X20 | IOCNT_OUT0~4 | 9751 |
| 0X40 | IOCNT_CHNL | 9757 |
| 0X48 | IOCNT_CTL | 9763 |
| 0X4C | IOCNT_CTL1 | 9769 |

### 24. UART

| 地址 | 寄存器名 | 行号 |
|------|----------|------|
| 0X00 | UARTx_CTL | 732 |
| 0X08 | UARTx_STA | 734 |
| 0XC | UARTx_TXD | 735 |
| 0X10 | UARTx_RXD | 736 |
| 0X14 | UARTx_FDIV | 737 |
| 0X00 | UARTx_CTL | 9986 |
| 0X04 | UARTx_BAUD | 9992 |
| 0X08 | UARTx_STA | 10009 |
| 0XC | UARTx_TXD | 10018 |
| 0X10 | UARTx_RXD | 10022 |
| 0X14 | UARTx_FDIV | 10026 |

### 25. SPI1/3/4

| 地址 | 寄存器名 | 行号 |
|------|----------|------|
| 0X04 | SPI_STAT | 760 |
| 0X08 | SPI_TXDATA | 761 |
| 0X0C | SPI_RXDATA | 762 |
| 0X10 | SPI_TXDFLT | 763 |
| 0X14 | SPIX_DMA_CTL | 764 |
| 0X04 | SPI_STAT | 10177 |
| 0X08 | SPI_TXDATA | 10183 |
| 0X0C | SPI_RXDATA | 10189 |
| 0X10 | SPI_TXDFLT | 10195 |
| 0X14 | SPiX_DMA_CTL | 10201 |

### 26. 高速SPIS

| 地址 | 寄存器名 | 行号 |
|------|----------|------|
| 0X00 | SPIS_CTL | 783 |
| 0X04 | SPIS_STIF | 784 |
| 0X08 | SPIS_STIE | 785 |
| 0X0C | SPIS_STIFE | 786 |
| 0X10 | SPIS_RXDATA | 787 |
| 0X14 | SPIS_TXDATA | 788 |
| 0X18 | SPIS_TXDFLT | 789 |
| 0X24 | SPIS FFCLR | 791 |
| 0X28 | SPIS_DMA_CTL | 792 |
| 0X44 | SPIS_DMA_IE | 799 |
| 0X48 | SPIS_DMA_IF | 800 |
| 0X00 | SPIS_CTL | 10328 |
| 0X04 | SPIS_STIF | 10336 |
| 0X08 | SPIS_STIE | 10348 |
| 0X0C | SPIS_STIFE | 10356 |
| 0X10 | SPIS_RXDATA | 10366 |
| 0X14 | SPIS_TXDATA | 10374 |
| 0X18 | SPIS_TXDFLT | 10382 |
| 0X24 | SPIS_FFCLR | 10398 |
| 0X28 | SPIS_DMA_CTL | 10406 |
| 0X44 | SPIS_DMA_IO | 10448 |

### 27. SPI0

| 地址 | 寄存器名 | 行号 |
|------|----------|------|
| 0X04 | SPI_STAT | 822 |
| 0X08 | SPI_TXDATA | 823 |
| 0X0C | SPI_RXDATA | 824 |
| 0X10 | SPI_TXDFLT | 825 |
| 0X14 | SPI0_DMA_CTRL | 826 |
| 0X24 | SPI0_DMA_IF | 830 |
| 0X28 | SPI0_DMA_IO | 831 |
| 0X2C | SPI0_DMA_CRC_INIT | 832 |
| 0X30 | SPI0_DMA_CRC | 833 |
| 0X04 | SPI_STAT | 10713 |
| 0X08 | SPI_TXDATA | 10719 |
| 0X0C | SPI_RXDATA | 10725 |
| 0X10 | SPI_TXDFLT | 10731 |
| 0X14 | SPI0_DMA_CTRL | 10737 |
| 0X28 | SPI0_DMA_IO | 10771 |
| 0X2C | SPI0_DMA_CRC_INIT | 10777 |
| 0X30 | SPI0_DMA_CRC | 10783 |

### 28. I2C

| 地址 | 寄存器名 | 行号 |
|------|----------|------|
| 0X00 | $\mathrm{I}^2\mathrm{C}$ _CTL | 848 |
| 0X04 | $\mathrm{I}^2\mathrm{C}$ _CLK | 849 |
| 0X08 | $\mathrm{I}^2\mathrm{C}$ _STAT | 850 |
| 0X04 | $\mathbf{I}^2\mathbf{C}_{-}\mathbf{ | 10856 |

### 29. ISO7816

| 地址 | 寄存器名 | 行号 |
|------|----------|------|
| 0X00 | ISO7816 CTL0 | 864 |
| 0X04 | ISO7816 CTL1 | 865 |
| 0X08 | ISO7816_CLK | 866 |
| 0X0C | ISO7816_BDDIV0 | 867 |
| 0X10 | ISO7816 BDDIV1 | 868 |
| 0X14 | ISO7816_STAT0 | 869 |
| 0X18 | ISO7816_STAT1 | 870 |
| 0X1C | ISO7816 DAT0 | 871 |
| 0X20 | ISO7816_DAT1 | 873 |
| 0X00 | ISO7816_CTL0 | 10956 |
| 0X04 | ISO7816_CTL1 | 10964 |
| 0X08 | ISO7816_CLK | 10972 |
| 0X0C | ISO7816_BDDIV0 | 10980 |
| 0X10 | ISO7816_BDDIV1 | 10988 |
| 0X14 | ISO7816_STAT0 | 10996 |
| 0X18 | ISO7816_STAT1 | 11015 |
| 0X1C | ISO7816_DAT0 | 11023 |
| 0X20 | ISO7816_DAT1 | 11031 |

### 30. LPUART

| 地址 | 寄存器名 | 行号 |
|------|----------|------|
| 0X00 | LPUART_MODE | 905 |
| 0X04 | LPUART_IE | 906 |
| 0X08 | LPUART STA | 907 |
| 0XC | LPUART_BAUD | 908 |
| 0X10 | LPUART_TXD | 909 |
| 0X14 | LPUART_RXD | 910 |
| 0X18 | LPUART_DMR | 911 |
| 0X00 | LPUART MODE | 11245 |
| 0X04 | LPUART_IE | 11256 |
| 0X08 | LPUART_sta | 11264 |
| 0XC | LPUART_BAUD | 11276 |
| 0X10 | LPUART TXD | 11284 |
| 0X14 | LPUART RXD | 11292 |
| 0X18 | LPUART_DMR | 11300 |

### 31. CAN

| 地址 | 寄存器名 | 行号 |
|------|----------|------|
| 0X0000 | MCR | 12081 |
| 0X0004 | 1CTRL1 | 12092 |
| 0X0008 | TIMER | 12104 |
| 0X0010 | RXMGMASK | 12120 |
| 0X0014 | RX14MASK | 12134 |
| 0X0018 | RX15MASk | 12144 |
| 0X001C | ECR | 12154 |
| 0X0020 | 1ESR1 | 12174 |
| 0X0028 | IMASK1 | 12194 |
| 0X0030 | IFLAG1 | 12202 |
| 0X0034 | 2CTRL2 | 12218 |
| 0X0038 | 2 ESR2 | 12232 |
| 0X0044 | CRCR | 12238 |
| 0X0048 | RXFGMASK | 12246 |
| 0X004C | RXFIR | 12263 |
| 0X0050 | CBT | 12269 |
| 0X0080 | 邮箱 $\mathbf{x}$ MBx | 12283 |
| 0X00880 | 0~15 RXIMR0~15 | 12289 |
| 0X0B00 | 1PN_CTRL1 | 12295 |
| 0X0B04 | 2PN_CTRL2 | 12303 |
| 0X0B08 | PN_WUM | 12313 |
| 0X0B0C | PN_FLT_ID1 | 12321 |
| 0X0B10 | PN_FLT_DLC | 12329 |
| 0X0B14 | 1PN_PL1_LO | 12337 |
| 0X0B18 | 2PN_PL1_HI | 12349 |
| 0X0B1C | PN_FLT_ID2 | 12361 |
| 0X0B20 | 1PN_PL2_PLMASK_LO | 12369 |
| 0X0B24 | 2PN_PL2_PLMASK_HI | 12380 |
| 0X0B40 | PN_WMBx_SC | 12391 |
| 0X0B44 | PN_WMBx_ID | 12399 |
| 0X0B48 | 1PN_WMBx_DL1 | 12409 |
| 0X0B4C | 2PN_WMBx_DL2 | 12419 |
| 0X0BF0 | EPRS | 12429 |
| 0X3200 | DMA_RBADR | 12449 |
| 0X3204 | DMA_RLEN | 12455 |
| 0X3208 | DMA_RADR | 12461 |
| 0X320C | DMA_IE | 12467 |
| 0X3210 | DMA_IF | 12473 |
| 0X3214 | CAN_TMR_SEL | 12479 |
| 0X3218 | STOP_MD | 12485 |

---

## 🔍 地址快查表

常用寄存器地址快速定位：

| 地址 | 寄存器 | 模块 | 行号 |
|------|--------|------|------|
| 0X00 | OSC_CTL1 | 系统控制 (SYS) | 80 |
| 0X00 | IE | 全失压测量 | 235 |
| 0X0 | WREN | 误差温度补偿 | 271 |
| 0X00 | FLK_EN | 闪变 | 307 |
| 0X0 | MAC_CTL0 | DSP加速器 | 364 |
| 0X00 | CRC DR | CRC | 433 |
| 0X0 | M2M_MODE | M2M DMA | 477 |
| 0X00 | GPADC_CTL0 | GPADC | 494 |
| 0X00 | SAR_CTL | 模拟外设 (SAR/ | 509 |
| 0X00 | WDT_EN | 概述 | 554 |
| 0X00 | TC_CNT | 定时器 (TC/PW | 574 |
| 0X0 | CTRL | 简易定时器 | 617 |
| 0X00 | INTC_CTL | 外部中断 (INTC | 644 |
| 0X00 | KBI_CTL | 外部中断 (INTC | 645 |
| 0X00 | IOCNT_CFG0~4 | 脉冲转发 (IOCN | 682 |
| 0X00 | UARTx_CTL | UART | 732 |
| 0X00 | SPIS_CTL | 高速SPIS | 783 |
| 0X00 | $\mathrm{I}^2\mathrm | I2C | 848 |
| 0X00 | ISO7816 CTL0 | ISO7816 | 864 |
| 0X00 | LPUART_MODE | LPUART | 905 |
| 0X00 | OSC_CTL1 | 系统控制 (SYS) | 1693 |
| 0X00 | IE | 全失压测量 | 4919 |
| 0X0 | WREN | 误差温度补偿 | 5233 |
| 0X00 | FLK_EN | 闪变 | 5440 |
| 0X0 | MAC_CTL0 | DSP加速器 | 6372 |
| 0X0 | M2M_MODE | M2M DMA | 7273 |
| 0X00 | GPADC_CTL0 | GPADC | 7364 |
| 0X00 | SAR_CTL | 模拟外设 (SAR/ | 7465 |
| 0X00 | RTC_CTL | RTC | 7678 |
| 0X00 | WDT_EN | 概述 | 8157 |
| 0X00 | TC_CNT | 定时器 (TC/PW | 8357 |
| 0X0 | CTRL | 简易定时器 | 8753 |
| 0X00 | （输入或者输出）：PMA | GPIO | 8887 |
| 0X00 | INTC_CTL | 外部中断 (INTC | 9375 |
| 0X00 | KBI_CTL | 外部中断 (INTC | 9382 |
| 0X00 | IOCNT_CFG0~4 | 脉冲转发 (IOCN | 9745 |
| 0X00 | UARTx_CTL | UART | 9986 |
| 0X00 | SPIS_CTL | 高速SPIS | 10328 |
| 0X00 | ISO7816_CTL0 | ISO7816 | 10956 |
| 0X00 | LPUART MODE | LPUART | 11245 |
| 0X0000 | MCR | CAN | 12081 |
| 0X04 | SYS_MODE | 系统控制 (SYS) | 81 |
| 0X04 | IF | 全失压测量 | 236 |
| 0X4 | CTRL | 误差温度补偿 | 272 |
| 0X04 | FLK_IE | 闪变 | 308 |
| 0X04 | MAC_CTL1 | DSP加速器 | 365 |
| 0X04 | CRC_STA | CRC | 434 |
| 0X4 | M2M_CTL | M2M DMA | 478 |
| 0X04 | GPADC CTL1 | GPADC | 495 |
| 0X04 | SAR_START | 模拟外设 (SAR/ | 510 |
| 0X04 | WDT_CTRL | 概述 | 555 |
| 0X04 | TC_PS | 定时器 (TC/PW | 575 |
| 0X4 | LOAD | 简易定时器 | 618 |
| 0X04 | INTC_MODE | 外部中断 (INTC | 646 |
| 0X04 | KBI_CTL | 按键中断 (KBI) | 655 |
| 0X04 | KBI_SEL | 按键中断 (KBI) | 656 |
| 0X04 | SPI_STAT | SPI1/3/4 | 760 |
| 0X04 | SPIS_STIF | 高速SPIS | 784 |
| 0X04 | SPI_STAT | SPI0 | 822 |
| 0X04 | $\mathrm{I}^2\mathrm | I2C | 849 |
| 0X04 | ISO7816 CTL1 | ISO7816 | 865 |
| 0X04 | LPUART_IE | LPUART | 906 |
| 0X04 | SYS_MODE | 系统控制 (SYS) | 1699 |
| 0X04 | IF | 全失压测量 | 4925 |
| 0X4 | CTRL | 误差温度补偿 | 5239 |
| 0X04 | FLK_IE | 闪变 | 5446 |
| 0X04 | MAC_CTL1 | DSP加速器 | 6378 |
| 0X4 | M2M_CTL | M2M DMA | 7281 |
| 0X04 | GPADC_CTL1 | GPADC | 7370 |
| 0X04 | SAR_START | 模拟外设 (SAR/ | 7473 |
| 0X04 | RTC_SC | RTC | 7684 |
| 0X04 | WDT_CTRL | 概述 | 8163 |
| 0X04 | TC_PS | 定时器 (TC/PW | 8363 |
| 0X4 | LOAD | 简易定时器 | 8758 |
| 0X04 | 0：PCA0 | GPIO | 8898 |
| 0X04 | INTC_MODE | 外部中断 (INTC | 9389 |
| 0X04 | KBI_CTL | 按键中断 (KBI) | 9436 |
| 0X04 | KBI_SEL | 按键中断 (KBI) | 9443 |
| 0X04 | UARTx_BAUD | UART | 9992 |
| 0X04 | SPI_STAT | SPI1/3/4 | 10177 |
| 0X04 | SPIS_STIF | 高速SPIS | 10336 |
| 0X04 | SPI_STAT | SPI0 | 10713 |
| 0X04 | $\mathbf{I}^2\mathbf | I2C | 10856 |
| 0X04 | ISO7816_CTL1 | ISO7816 | 10964 |
| 0X04 | LPUART_IE | LPUART | 11256 |
| 0X0004 | 1CTRL1 | CAN | 12092 |
| 0X08 | SYS PD | 系统控制 (SYS) | 82 |
| 0X08 | Start | 三相计量单元 (EM | 179 |
| 0X08 | LS_CFG | 全失压测量 | 237 |
| 0X8 | EN | 误差温度补偿 | 273 |
| 0X08 | FLK_IF | 闪变 | 309 |
| 0X08 | MAC_IN0 | DSP加速器 | 367 |
| 0X08 | CRC CTRL | CRC | 435 |
| 0X8 | M2M_DUMMY | M2M DMA | 479 |
| 0X08 | GPADC RATIO | GPADC | 496 |
| 0X08 | SAR_STATUS | 模拟外设 (SAR/ | 511 |
| 0X08 | WDT_PASS | 概述 | 556 |
| 0X8 | VAL | 简易定时器 | 619 |
| 0X08 | INTC_MASK | 外部中断 (INTC | 647 |
| 0X08 | KBI_DATA | 按键中断 (KBI) | 657 |

> 完整列表共 705 个寄存器，可用 Grep 搜索具体地址