/* 人机接口演示模块：提供1ms按键扫描、OLED基本显示与三个功能键交互。 */
#include "gd32f10x.h"
#include "key.h"
#include "oled.h"
static volatile uint32_t ticks;
/* 可在调试器观察；显示故障不阻止按键继续扫描。 */
volatile oled_status_t hmi_display_status;
/**
 * 功能：更新毫秒节拍并扫描按键
 * 参数：无
 * 返回：无
 * 注意：仅此中断调用Key_Scan，主循环只取事件
 * 作者/责任成员：蒋观海；版本/日期：V1.0 / 2026-10-09。
 * 修改历史：2026-10-09，V1.0，首次实现 SysTick_Handler。
 */
void SysTick_Handler(void)
{
    ++ticks; Key_Scan(ticks);
}
/**
 * 功能：绘制驱动演示页面
 * 参数：timebase：档0~2；mode：模式0~1；hold：保持状态
 * 返回：OLED状态码
 * 注意：演示数值不代表测量结果；统一刷新；坐标固定有效
 * 作者/责任成员：何玉；版本/日期：V1.0 / 2026-10-09。
 * 修改历史：2026-10-09，V1.0，首次实现 render_page。
 */
static oled_status_t render_page(uint8_t timebase, uint8_t mode, uint8_t hold)
{
    static const char *const bases[]={"10 MHz","1 MHz","100 kHz"};
    oled_status_t status=OLED_Clear();
    if (status!=OLED_OK) return status;
    (void)OLED_ShowString(0,0,"HMI DRIVER DEMO");
    (void)OLED_ShowString(0,1,"Demo Hz: ");
    (void)OLED_ShowFloat(54,1,1234.5678,4);
    (void)OLED_ShowString(0,2,"Base: ");
    (void)OLED_ShowString(36,2,bases[timebase]);
    (void)OLED_ShowString(0,3,mode?"Mode: MULTI":"Mode: SINGLE");
    (void)OLED_ShowString(0,4,hold?"State: HOLD":"State: RUN");
    (void)OLED_ShowString(0,5,"Int: ");
    (void)OLED_ShowInt(30,5,-2147483647-1);
    (void)OLED_ShowChar(0,6,'A');
    (void)OLED_ShowString(0,7,"SW1 Base 2 Mode 3 Run");
    return OLED_Refresh();
}
/**
 * 功能：启动人机接口演示并响应三个按键
 * 参数：无
 * 返回：嵌入式主程序不返回
 * 注意：按键先初始化再开启节拍；OLED失败每1秒重试；非测频程序
 * 作者/责任成员：蒋观海；版本/日期：V1.0 / 2026-10-09。
 * 修改历史：2026-10-09，V1.0，首次实现 main。
 */
int main(void)
{
    uint8_t base=0,mode=0,hold=0,dirty=1;
    uint32_t retry_at=0; key_value_t key;
    Key_Init();
    if (SysTick_Config(SystemCoreClock/1000U)!=0) while (1) {}
    hmi_display_status=OLED_Init();
    while (1) {
        while ((key=Key_GetValue())!=KEY_NONE) {
            if (key==KEY_TIMEBASE) base=(uint8_t)((base+1U)%3U);
            else if (key==KEY_MODE) mode^=1U;
            else if (key==KEY_HOLD) hold^=1U;
            dirty=1;
        }
        if (hmi_display_status!=OLED_OK &&
            (uint32_t)(ticks-retry_at)>=1000U) {
            retry_at=ticks; hmi_display_status=OLED_Init(); dirty=1;
        }
        if (dirty && hmi_display_status==OLED_OK) {
            hmi_display_status=render_page(base,mode,hold); dirty=0;
            retry_at=ticks;
        }
    }
}
