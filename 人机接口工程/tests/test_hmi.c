#include "key.h"
#include "oled.h"
#include <assert.h>
#include <string.h>
#include <stdio.h>
static uint8_t keys, fail;
static uint8_t screen[8][128];
static uint8_t page, col;
void HMI_PortInit(void) {}
uint32_t HMI_EnterCritical(void) { return 0; }
void HMI_ExitCritical(uint32_t mask) { (void)mask; }
uint8_t HMI_KeyRead(void) { return keys; }
void HMI_DelayMs(uint32_t ms) { (void)ms; }
int HMI_OLEDWrite(uint8_t control, const uint8_t *data, uint16_t len)
{
    uint16_t i;
    if (fail) return -1;
    if (!control && len == 3 && (data[0] & 0xf8) == 0xb0) {
        page = data[0] & 7;
        col = (data[1] & 15) | ((data[2] & 15) << 4);
    } else if (control == 0x40) {
        for (i=0; i<len; ++i) { assert(col < 128); screen[page][col++]=data[i]; }
    }
    return 0;
}
static void scan(uint32_t first, uint32_t last)
{
    uint32_t t;
    for (t=first; t<=last; ++t) Key_Scan(t);
}
int main(void)
{
    uint8_t glyph[6];
    Key_Init(); keys=1; scan(0,10); keys=0; scan(11,12);
    keys=1; scan(13,32); assert(Key_GetValue()==KEY_NONE);
    Key_Scan(33); assert(Key_GetValue()==KEY_TIMEBASE);
    scan(34,80); assert(Key_GetValue()==KEY_NONE);
    keys=0; scan(81,101); keys=7; scan(102,122);
    assert(Key_GetValue()==KEY_TIMEBASE);
    assert(Key_GetValue()==KEY_MODE); assert(Key_GetValue()==KEY_HOLD);
    assert(Key_GetValue()==KEY_NONE);
    Key_Init(); keys=0; Key_Scan(0xfffffff0u);
    keys=1; Key_Scan(0xfffffff1u); Key_Scan(5);
    assert(Key_GetValue()==KEY_TIMEBASE);
    assert(OLED_Init()==OLED_OK); assert(OLED_ShowChar(0,0,'A')==OLED_OK);
    assert(OLED_Refresh()==OLED_OK); memcpy(glyph,screen[0],6);
    assert(glyph[0] || glyph[1] || glyph[2]);
    assert(OLED_Clear()==OLED_OK); assert(OLED_Refresh()==OLED_OK);
    assert(screen[0][0]==0 && screen[0][1]==0);
    assert(OLED_ShowString(0,0,NULL)==OLED_BAD_ARG);
    assert(OLED_ShowChar(123,0,'A')==OLED_BAD_ARG);
    assert(OLED_ShowString(120,0,"AB")==OLED_BAD_ARG);
    assert(OLED_ShowInt(0,0,(-2147483647-1))==OLED_OK);
    assert(OLED_ShowFloat(0,1,-1.125,2)==OLED_OK);
    assert(OLED_ShowString(0,2,"-1.13")==OLED_OK);
    assert(OLED_Refresh()==OLED_OK);
    assert(memcmp(screen[1],screen[2],30)==0);
    assert(OLED_ShowFloat(0,0,1.0,7)==OLED_BAD_ARG);
    assert(OLED_ShowFloat(0,0,1e30,2)==OLED_BAD_ARG);
    assert(OLED_ShowFloat(0,0,0.0/0.0,2)==OLED_BAD_ARG);
    fail=1; assert(OLED_Refresh()==OLED_IO_ERROR);
    assert(OLED_Init()==OLED_IO_ERROR);
    assert(OLED_Refresh()==OLED_NOT_READY);
    puts("PASS: debounce, repeat suppression, simultaneous keys, tick wrap,");
    puts("framebuffer, bounds, INT32_MIN, rounding, invalid float and bus failure.");
    return 0;
}
