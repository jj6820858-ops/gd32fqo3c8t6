/* OLED模块：提供SSD1306初始化、清屏、字符/字符串、整数和浮点显示接口。 */
#ifndef HMI_OLED_H
#define HMI_OLED_H
#include <stdint.h>
typedef enum {
    OLED_OK=0, OLED_BAD_ARG=-1, OLED_IO_ERROR=-2, OLED_NOT_READY=-3
} oled_status_t;
/**
 * 功能：初始化SSD1306并清空屏幕
 * 参数：无
 * 返回：OLED_OK或OLED_IO_ERROR
 * 注意：调用前系统时钟已就绪；配置为128x64、0x3C、模块内置电荷泵
 * 作者/责任成员：吕朋聪；版本/日期：V1.0 / 2026-10-09。
 * 修改历史：2026-10-09，V1.0，首次实现 OLED_Init。
 */
oled_status_t OLED_Init(void);
/**
 * 功能：清空本地显示缓冲区
 * 参数：无
 * 返回：OLED_OK或OLED_NOT_READY
 * 注意：调用OLED_Refresh后实际屏幕才更新
 * 作者/责任成员：吕朋聪；版本/日期：V1.0 / 2026-10-09。
 * 修改历史：2026-10-09，V1.0，首次实现 OLED_Clear。
 */
oled_status_t OLED_Clear(void);
/**
 * 功能：将1024字节缓冲区按8页写入屏幕
 * 参数：无
 * 返回：OLED_OK/OLED_IO_ERROR/OLED_NOT_READY
 * 注意：阻塞通信，仅主循环调用；失败时可重试或重新初始化
 * 作者/责任成员：吕朋聪；版本/日期：V1.0 / 2026-10-09。
 * 修改历史：2026-10-09，V1.0，首次实现 OLED_Refresh。
 */
oled_status_t OLED_Refresh(void);
/**
 * 功能：在缓冲区显示一个5x7字符，含1列间距
 * 参数：x：0~122像素；page：0~7；ch：ASCII字符
 * 返回：OLED_OK/OLED_BAD_ARG/OLED_NOT_READY
 * 注意：只修改缓冲；不可显示字符替换为问号；再调用Refresh
 * 作者/责任成员：吕朋聪；版本/日期：V1.0 / 2026-10-09。
 * 修改历史：2026-10-09，V1.0，首次实现 OLED_ShowChar。
 */
oled_status_t OLED_ShowChar(uint8_t x, uint8_t page, char ch);
/**
 * 功能：在缓冲区显示单行字符串
 * 参数：x：起始像素；page：页0~7；text：以零结束的字符串
 * 返回：OLED_OK/OLED_BAD_ARG/OLED_NOT_READY
 * 注意：超出本行返回错误且不写入；不自动换行；更新后Refresh
 * 作者/责任成员：吕朋聪；版本/日期：V1.0 / 2026-10-09。
 * 修改历史：2026-10-09，V1.0，首次实现 OLED_ShowString。
 */
oled_status_t OLED_ShowString(uint8_t x, uint8_t page, const char *text);
/**
 * 功能：显示有符号32位十进制整数
 * 参数：x/page：坐标；value：整数，含INT32_MIN
 * 返回：OLED_OK/OLED_BAD_ARG/OLED_NOT_READY
 * 注意：不补前导零；覆盖旧数值前清屏或用空格填充；再Refresh
 * 作者/责任成员：吕朋聪；版本/日期：V1.0 / 2026-10-09。
 * 修改历史：2026-10-09，V1.0，首次实现 OLED_ShowInt。
 */
oled_status_t OLED_ShowInt(uint8_t x, uint8_t page, int32_t value);
/**
 * 功能：显示定点格式浮点数，四舍五入
 * 参数：x/page：坐标；value：数值；decimals：0~6小数位
 * 返回：OLED_OK/OLED_BAD_ARG/OLED_NOT_READY
 * 注意：拒绝NaN/无穷和放大后超出uint32范围的值；舍入半值远离零；再Refresh
 * 作者/责任成员：吕朋聪；版本/日期：V1.0 / 2026-10-09。
 * 修改历史：2026-10-09，V1.0，首次实现 OLED_ShowFloat。
 */
oled_status_t OLED_ShowFloat(uint8_t x, uint8_t page, double value, uint8_t decimals);
#endif
