/* 按键模块：提供三个独立按键初始化、非阻塞扫描、消抖和键值接口。 */
#ifndef HMI_KEY_H
#define HMI_KEY_H
#include <stdint.h>
typedef enum {
    KEY_NONE=0, KEY_TIMEBASE=1, KEY_MODE=2, KEY_HOLD=3
} key_value_t;
/**
 * 功能：初始化按键 GPIO 并复位消抖状态
 * 参数：无
 * 返回：无
 * 注意：启动时调用；按下状态从下一次扫描开始计时
 * 作者/责任成员：吕朋聪；版本/日期：V1.0 / 2026-10-09。
 * 修改历史：2026-10-09，V1.0，首次实现 Key_Init。
 */
void Key_Init(void);
/**
 * 功能：非阻塞扫描三键，连续稳定20ms后更新状态
 * 参数：now_ms：单调递增毫秒节拍，允许32位回绕
 * 返回：无
 * 注意：每1~5ms调用；可在节拍中断调用；仅允许一个扫描调用者
 * 作者/责任成员：吕朋聪；版本/日期：V1.0 / 2026-10-09。
 * 修改历史：2026-10-09，V1.0，首次实现 Key_Scan。
 */
void Key_Scan(uint32_t now_ms);
/**
 * 功能：取出一个消抖后的按下键值
 * 参数：无
 * 返回：KEY_NONE或三个功能键值
 * 注意：主循环调用；同一键未消费的多次事件合并；同时按下按键号顺序返回
 * 作者/责任成员：吕朋聪；版本/日期：V1.0 / 2026-10-09。
 * 修改历史：2026-10-09，V1.0，首次实现 Key_GetValue。
 */
key_value_t Key_GetValue(void);
#endif
