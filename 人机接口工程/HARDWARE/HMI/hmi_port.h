/* 硬件适配模块：封装PA5~PA7按键读取、PB10/PB11硬件I2C1和短延时。 */
#ifndef HMI_PORT_H
#define HMI_PORT_H
#include <stdint.h>
#define HMI_OLED_ADDRESS 0x3CU /* 7位地址 */
/**
 * 功能：初始化按键输入与OLED硬件I2C1（100kHz）及DWT计时
 * 参数：无
 * 返回：无
 * 注意：幂等；先完成系统时钟初始化；保留PA0/PA1及SWD
 * 作者/责任成员：吕朋聪；版本/日期：V1.1 / 2026-10-09。
 * 修改历史：2026-10-09，V1.0，首次实现 HMI_PortInit；V1.1，改用硬件I2C1。
 */
void HMI_PortInit(void);
/**
 * 功能：读取三个功能键的瞬时按下状态
 * 参数：无
 * 返回：bit0~2对应SW1~SW3；1表示按下
 * 注意：内部上拉，未消抖；SW4为硬件复位不参与扫描
 * 作者/责任成员：吕朋聪；版本/日期：V1.0 / 2026-10-09。
 * 修改历史：2026-10-09，V1.0，首次实现 HMI_KeyRead。
 */
uint8_t HMI_KeyRead(void);
/**
 * 功能：按毫秒执行短时阻塞延时
 * 参数：ms：延时毫秒数
 * 返回：无
 * 注意：仅OLED启动使用；需先初始化DWT；不关闭中断
 * 作者/责任成员：吕朋聪；版本/日期：V1.0 / 2026-10-09。
 * 修改历史：2026-10-09，V1.0，首次实现 HMI_DelayMs。
 */
void HMI_DelayMs(uint32_t ms);
/**
 * 功能：硬件I2C1写SSD1306，检查NACK、总线错误和5ms阶段超时
 * 参数：control：0x00命令/0x40数据；data：数据；len：1~128字节
 * 返回：0成功；-1总线超时/NACK/非法参数
 * 注意：仅主循环；PB10/PB11开漏，需外部3.3V上拉；失败复位外设，不重试
 * 作者/责任成员：吕朋聪；版本/日期：V1.1 / 2026-10-09。
 * 修改历史：2026-10-09，V1.0，首次实现 HMI_OLEDWrite；V1.1，改用硬件I2C1。
 */
int HMI_OLEDWrite(uint8_t control, const uint8_t *data, uint16_t len);
/**
 * 功能：保存中断屏蔽状态并进入短临界区
 * 参数：无
 * 返回：原PRIMASK值
 * 注意：仅保护取键值，不在临界区进行OLED传输
 * 作者/责任成员：吕朋聪；版本/日期：V1.0 / 2026-10-09。
 * 修改历史：2026-10-09，V1.0，首次实现 HMI_EnterCritical。
 */
uint32_t HMI_EnterCritical(void);
/**
 * 功能：恢复进入临界区前的中断状态
 * 参数：mask：EnterCritical返回值
 * 返回：无
 * 注意：必须与EnterCritical成对使用
 * 作者/责任成员：吕朋聪；版本/日期：V1.0 / 2026-10-09。
 * 修改历史：2026-10-09，V1.0，首次实现 HMI_ExitCritical。
 */
void HMI_ExitCritical(uint32_t mask);
#endif
