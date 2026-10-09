from pathlib import Path
import re
root=Path(__file__).resolve().parents[1]
out=root/'HARDWARE/HMI'; out.mkdir(parents=True,exist_ok=True)
def doc(name,desc,params,ret,note,author='吕朋聪'):
    return f'''/**
 * 功能：{desc}
 * 参数：{params}
 * 返回：{ret}
 * 注意：{note}
 * 作者/责任成员：{author}；版本/日期：V1.0 / 2026-10-09。
 * 修改历史：2026-10-09，V1.0，首次实现 {name}。
 */
'''
def write(name,text):
    (out/name).write_text(text,encoding='utf-8-sig')
key_funcs=[
('void Key_Init(void)','Key_Init','初始化按键 GPIO 并复位消抖状态','无','无','启动时调用；按下状态从下一次扫描开始计时'),
('void Key_Scan(uint32_t now_ms)','Key_Scan','非阻塞扫描三键，连续稳定20ms后更新状态','now_ms：单调递增毫秒节拍，允许32位回绕','无','每1~5ms调用；可在节拍中断调用；仅允许一个扫描调用者'),
('key_value_t Key_GetValue(void)','Key_GetValue','取出一个消抖后的按下键值','无','KEY_NONE或三个功能键值','主循环调用；同一键未消费的多次事件合并；同时按下按键号顺序返回')]
key_h='''/* 按键模块：提供三个独立按键初始化、非阻塞扫描、消抖和键值接口。 */
#ifndef HMI_KEY_H
#define HMI_KEY_H
#include <stdint.h>
typedef enum {
    KEY_NONE=0, KEY_TIMEBASE=1, KEY_MODE=2, KEY_HOLD=3
} key_value_t;
'''
for sig,n,d,p,r,c in key_funcs: key_h+=doc(n,d,p,r,c)+sig+';\n'
write('key.h',key_h+'#endif\n')
key_c='''/* 按键模块：实现PA5/PA6/PA7低有效按键扫描、20ms消抖与按下事件。 */
#include "key.h"
#include "hmi_port.h"
#define KEY_COUNT 3U
#define DEBOUNCE_MS 20U
static uint8_t candidate[KEY_COUNT], stable[KEY_COUNT];
static volatile uint8_t pending;
static uint32_t changed_at[KEY_COUNT];
'''
bodies=[
'''{
    uint8_t i;
    HMI_PortInit(); pending=0;
    for (i=0; i<KEY_COUNT; ++i) {
        candidate[i]=0; stable[i]=0; changed_at[i]=0;
    }
}
''',
'''{
    uint8_t i, raw=HMI_KeyRead();
    for (i=0; i<KEY_COUNT; ++i) {
        uint8_t pressed=(uint8_t)((raw>>i)&1U);
        if (pressed!=candidate[i]) {
            candidate[i]=pressed; changed_at[i]=now_ms;
        } else if (stable[i]!=pressed &&
                   (uint32_t)(now_ms-changed_at[i])>=DEBOUNCE_MS) {
            stable[i]=pressed;
            if (pressed) pending|=(uint8_t)(1U<<i);
        }
    }
}
''',
'''{
    uint8_t i; uint32_t mask=HMI_EnterCritical();
    for (i=0; i<KEY_COUNT; ++i) {
        if (pending&(1U<<i)) {
            pending&=(uint8_t)~(1U<<i);
            HMI_ExitCritical(mask);
            return (key_value_t)(i+1U);
        }
    }
    HMI_ExitCritical(mask); return KEY_NONE;
}
''']
for (sig,n,d,p,r,c),body in zip(key_funcs,bodies): key_c+=doc(n,d,p,r,c)+sig+'\n'+body
write('key.c',key_c)
# hmi_port.h/c are maintained directly; do not overwrite the hardware I2C1 driver.
oled_funcs=[
('oled_status_t OLED_Init(void)','OLED_Init','初始化SSD1306并清空屏幕','无','OLED_OK或OLED_IO_ERROR','调用前系统时钟已就绪；配置为128x64、0x3C、模块内置电荷泵'),
('oled_status_t OLED_Clear(void)','OLED_Clear','清空本地显示缓冲区','无','OLED_OK或OLED_NOT_READY','调用OLED_Refresh后实际屏幕才更新'),
('oled_status_t OLED_Refresh(void)','OLED_Refresh','将1024字节缓冲区按8页写入屏幕','无','OLED_OK/OLED_IO_ERROR/OLED_NOT_READY','阻塞通信，仅主循环调用；失败时可重试或重新初始化'),
('oled_status_t OLED_ShowChar(uint8_t x, uint8_t page, char ch)','OLED_ShowChar','在缓冲区显示一个5x7字符，含1列间距','x：0~122像素；page：0~7；ch：ASCII字符','OLED_OK/OLED_BAD_ARG/OLED_NOT_READY','只修改缓冲；不可显示字符替换为问号；再调用Refresh'),
('oled_status_t OLED_ShowString(uint8_t x, uint8_t page, const char *text)','OLED_ShowString','在缓冲区显示单行字符串','x：起始像素；page：页0~7；text：以零结束的字符串','OLED_OK/OLED_BAD_ARG/OLED_NOT_READY','超出本行返回错误且不写入；不自动换行；更新后Refresh'),
('oled_status_t OLED_ShowInt(uint8_t x, uint8_t page, int32_t value)','OLED_ShowInt','显示有符号32位十进制整数','x/page：坐标；value：整数，含INT32_MIN','OLED_OK/OLED_BAD_ARG/OLED_NOT_READY','不补前导零；覆盖旧数值前清屏或用空格填充；再Refresh'),
('oled_status_t OLED_ShowFloat(uint8_t x, uint8_t page, double value, uint8_t decimals)','OLED_ShowFloat','显示定点格式浮点数，四舍五入','x/page：坐标；value：数值；decimals：0~6小数位','OLED_OK/OLED_BAD_ARG/OLED_NOT_READY','拒绝NaN/无穷和放大后超出uint32范围的值；舍入半值远离零；再Refresh')]
oled_h='''/* OLED模块：提供SSD1306初始化、清屏、字符/字符串、整数和浮点显示接口。 */
#ifndef HMI_OLED_H
#define HMI_OLED_H
#include <stdint.h>
typedef enum {
    OLED_OK=0, OLED_BAD_ARG=-1, OLED_IO_ERROR=-2, OLED_NOT_READY=-3
} oled_status_t;
'''
for sig,n,d,p,r,c in oled_funcs: oled_h+=doc(n,d,p,r,c)+sig+';\n'
write('oled.h',oled_h+'#endif\n')
# Original 5x7 glyph designs, row bitmap to vertical SSD1306 bytes.
rows={
' ':['00000']*7,
'!':['00100','00100','00100','00100','00100','00000','00100'],
'"':['01010','01010','01010','00000','00000','00000','00000'],
'#':['01010','11111','01010','01010','11111','01010','00000'],
'$':['00100','01111','10100','01110','00101','11110','00100'],
'%':['11001','11010','00100','01000','10110','00110','00000'],
'&':['01100','10010','10100','01000','10101','10010','01101'],
"'":['00100','00100','01000','00000','00000','00000','00000'],
'(':['00010','00100','01000','01000','01000','00100','00010'],
')':['01000','00100','00010','00010','00010','00100','01000'],
'*':['00000','10101','01110','11111','01110','10101','00000'],
'+':['00000','00100','00100','11111','00100','00100','00000'],
',':['00000','00000','00000','00000','00100','00100','01000'],
'-':['00000','00000','00000','11111','00000','00000','00000'],
'.':['00000','00000','00000','00000','00000','00100','00100'],
'/':['00001','00010','00100','01000','10000','00000','00000'],
'0':['01110','10001','10011','10101','11001','10001','01110'],
'1':['00100','01100','00100','00100','00100','00100','01110'],
'2':['01110','10001','00001','00010','00100','01000','11111'],
'3':['11110','00001','00001','01110','00001','00001','11110'],
'4':['00010','00110','01010','10010','11111','00010','00010'],
'5':['11111','10000','10000','11110','00001','00001','11110'],
'6':['01110','10000','10000','11110','10001','10001','01110'],
'7':['11111','00001','00010','00100','01000','01000','01000'],
'8':['01110','10001','10001','01110','10001','10001','01110'],
'9':['01110','10001','10001','01111','00001','00001','01110'],
':':['00000','00100','00100','00000','00100','00100','00000'],
';':['00000','00100','00100','00000','00100','00100','01000'],
'<':['00010','00100','01000','10000','01000','00100','00010'],
'=':['00000','00000','11111','00000','11111','00000','00000'],
'>':['01000','00100','00010','00001','00010','00100','01000'],
'?':['01110','10001','00001','00010','00100','00000','00100'],
'@':['01110','10001','10111','10101','10111','10000','01110'],
'A':['01110','10001','10001','11111','10001','10001','10001'],
'B':['11110','10001','10001','11110','10001','10001','11110'],
'C':['01110','10001','10000','10000','10000','10001','01110'],
'D':['11110','10001','10001','10001','10001','10001','11110'],
'E':['11111','10000','10000','11110','10000','10000','11111'],
'F':['11111','10000','10000','11110','10000','10000','10000'],
'G':['01110','10001','10000','10111','10001','10001','01110'],
'H':['10001','10001','10001','11111','10001','10001','10001'],
'I':['01110','00100','00100','00100','00100','00100','01110'],
'J':['00111','00010','00010','00010','00010','10010','01100'],
'K':['10001','10010','10100','11000','10100','10010','10001'],
'L':['10000','10000','10000','10000','10000','10000','11111'],
'M':['10001','11011','10101','10101','10001','10001','10001'],
'N':['10001','11001','10101','10011','10001','10001','10001'],
'O':['01110','10001','10001','10001','10001','10001','01110'],
'P':['11110','10001','10001','11110','10000','10000','10000'],
'Q':['01110','10001','10001','10001','10101','10010','01101'],
'R':['11110','10001','10001','11110','10100','10010','10001'],
'S':['01111','10000','10000','01110','00001','00001','11110'],
'T':['11111','00100','00100','00100','00100','00100','00100'],
'U':['10001','10001','10001','10001','10001','10001','01110'],
'V':['10001','10001','10001','10001','10001','01010','00100'],
'W':['10001','10001','10001','10101','10101','10101','01010'],
'X':['10001','10001','01010','00100','01010','10001','10001'],
'Y':['10001','10001','01010','00100','00100','00100','00100'],
'Z':['11111','00001','00010','00100','01000','10000','11111'],
'[':['01110','01000','01000','01000','01000','01000','01110'],
'\\':['10000','01000','00100','00010','00001','00000','00000'],
']':['01110','00010','00010','00010','00010','00010','01110'],
'^':['00100','01010','10001','00000','00000','00000','00000'],
'_':['00000','00000','00000','00000','00000','00000','11111'],
'`':['01000','00100','00010','00000','00000','00000','00000'],
'a':['00000','00000','01110','00001','01111','10001','01111'],
'b':['10000','10000','11110','10001','10001','10001','11110'],
'c':['00000','00000','01110','10001','10000','10001','01110'],
'd':['00001','00001','01111','10001','10001','10001','01111'],
'e':['00000','00000','01110','10001','11111','10000','01110'],
'f':['00110','01001','01000','11100','01000','01000','01000'],
'g':['00000','01111','10001','10001','01111','00001','01110'],
'h':['10000','10000','11110','10001','10001','10001','10001'],
'i':['00100','00000','01100','00100','00100','00100','01110'],
'j':['00010','00000','00110','00010','00010','10010','01100'],
'k':['10000','10000','10010','10100','11000','10100','10010'],
'l':['01100','00100','00100','00100','00100','00100','01110'],
'm':['00000','00000','11010','10101','10101','10101','10101'],
'n':['00000','00000','11110','10001','10001','10001','10001'],
'o':['00000','00000','01110','10001','10001','10001','01110'],
'p':['00000','11110','10001','10001','11110','10000','10000'],
'q':['00000','01111','10001','10001','01111','00001','00001'],
'r':['00000','00000','10110','11001','10000','10000','10000'],
's':['00000','00000','01111','10000','01110','00001','11110'],
't':['01000','01000','11100','01000','01000','01001','00110'],
'u':['00000','00000','10001','10001','10001','10011','01101'],
'v':['00000','00000','10001','10001','10001','01010','00100'],
'w':['00000','00000','10001','10001','10101','10101','01010'],
'x':['00000','00000','10001','01010','00100','01010','10001'],
'y':['00000','10001','10001','10001','01111','00001','01110'],
'z':['00000','00000','11111','00010','00100','01000','11111'],
'{':['00010','00100','00100','01000','00100','00100','00010'],
'|':['00100','00100','00100','00100','00100','00100','00100'],
'}':['01000','00100','00100','00010','00100','00100','01000'],
'~':['00000','00000','01001','10110','00000','00000','00000']}
font=[]
for code in range(32,127):
    pattern=rows[chr(code)]
    cols=[sum((pattern[y][x]=='1')<<y for y in range(7)) for x in range(5)]
    font.append('    {'+','.join(f'0x{v:02X}' for v in cols)+'}, /* ASCII '+str(code)+' */')
oled_c='''/* OLED模块：实现SSD1306页缓冲、5x7 ASCII字库和数值格式化显示。 */
#include "oled.h"
#include "hmi_port.h"
#include <string.h>
static uint8_t framebuffer[8][128];
static uint8_t ready;
/* 原创5x7点阵；ASCII 32~126；每字符加1列间距。 */
static const uint8_t font5x7[95][5]={
'''+ '\n'.join(font)+'\n};\n'
oled_c+=doc('format_uint','将uint32转换为十进制字符','value：无符号值；text：至少11字节缓冲','字符数，不含结束零','内部使用，不调用printf')+'''static uint8_t format_uint(uint32_t value, char *text)
{
    char reverse[10]; uint8_t n=0,i;
    do { reverse[n++]=(char)('0'+value%10U); value/=10U; } while (value);
    for (i=0;i<n;++i) text[i]=reverse[n-1U-i];
    text[n]='\0'; return n;
}
'''.replace("'\0'","'\\0'")
oled_bodies=[
'''{
    static const uint8_t config[]={
        0xAE,0xD5,0x80,0xA8,0x3F,0xD3,0x00,0x40,
        0x8D,0x14,0x20,0x02,0xA1,0xC8,0xDA,0x12,
        0x81,0x7F,0xD9,0xF1,0xDB,0x40,0xA4,0xA6,0x2E
    };
    const uint8_t on=0xAF;
    ready=0; HMI_PortInit(); HMI_DelayMs(100);
    if (HMI_OLEDWrite(0x00,config,sizeof(config))!=0)
        return OLED_IO_ERROR;
    ready=1; (void)OLED_Clear();
    if (OLED_Refresh()!=OLED_OK || HMI_OLEDWrite(0x00,&on,1)!=0) {
        ready=0; return OLED_IO_ERROR;
    }
    return OLED_OK;
}
''',
'''{
    if (!ready) return OLED_NOT_READY;
    memset(framebuffer,0,sizeof(framebuffer)); return OLED_OK;
}
''',
'''{
    uint8_t p;
    if (!ready) return OLED_NOT_READY;
    for (p=0;p<8;++p) {
        uint8_t position[3]={(uint8_t)(0xB0U+p),0x00,0x10};
        if (HMI_OLEDWrite(0x00,position,3)!=0 ||
            HMI_OLEDWrite(0x40,framebuffer[p],128)!=0)
            return OLED_IO_ERROR;
    }
    return OLED_OK;
}
''',
'''{
    uint8_t code=(uint8_t)ch;
    if (!ready) return OLED_NOT_READY;
    if (x>122 || page>7) return OLED_BAD_ARG;
    if (code<32 || code>126) code='?';
    memcpy(&framebuffer[page][x],font5x7[code-32U],5);
    framebuffer[page][x+5U]=0; return OLED_OK;
}
''',
'''{
    uint8_t n=0,i,capacity;
    if (!ready) return OLED_NOT_READY;
    if (text==0 || page>7 || x>122) return OLED_BAD_ARG;
    capacity=(uint8_t)((128U-x)/6U);
    while (text[n]!=0) {
        if (n>=capacity) return OLED_BAD_ARG;
        ++n;
    }
    for (i=0;i<n;++i) (void)OLED_ShowChar((uint8_t)(x+i*6U),page,text[i]);
    return OLED_OK;
}
''',
'''{
    char text[12]; uint8_t offset=0; uint32_t magnitude;
    if (value<0) { text[offset++]='-'; magnitude=(uint32_t)(-(value+1))+1U; }
    else magnitude=(uint32_t)value;
    (void)format_uint(magnitude,text+offset);
    return OLED_ShowString(x,page,text);
}
''',
'''{
    char text[24]; uint32_t scale=1,rounded,fraction;
    uint8_t i,n=0; double magnitude=value;
    if (decimals>6 || value!=value) return OLED_BAD_ARG;
    if (value<0) magnitude=-value;
    for (i=0;i<decimals;++i) scale*=10U;
    magnitude*=scale;
    if (!(magnitude<=4294967294.0)) return OLED_BAD_ARG;
    rounded=(uint32_t)(magnitude+0.5);
    if (value<0 && rounded!=0) text[n++]='-';
    n+=format_uint(rounded/scale,text+n);
    if (decimals) {
        text[n++]='.'; fraction=rounded%scale;
        for (i=0;i<decimals;++i) {
            scale/=10U; text[n++]=(char)('0'+fraction/scale); fraction%=scale;
        }
    }
    text[n]=0; return OLED_ShowString(x,page,text);
}
''']
for (sig,n,d,p,r,c),body in zip(oled_funcs,oled_bodies): oled_c+=doc(n,d,p,r,c)+sig+'\n'+body
write('oled.c',oled_c)
demo='''/* 人机接口演示模块：提供1ms按键扫描、OLED基本显示与三个功能键交互。 */
#include "gd32f10x.h"
#include "key.h"
#include "oled.h"
static volatile uint32_t ticks;
/* 可在调试器观察；显示故障不阻止按键继续扫描。 */
volatile oled_status_t hmi_display_status;
'''
demo+=doc('SysTick_Handler','更新毫秒节拍并扫描按键','无','无','仅此中断调用Key_Scan，主循环只取事件','蒋观海')+'''void SysTick_Handler(void)
{
    ++ticks; Key_Scan(ticks);
}
'''
demo+=doc('render_page','绘制驱动演示页面','timebase：档0~2；mode：模式0~1；hold：保持状态','OLED状态码','演示数值不代表测量结果；统一刷新；坐标固定有效','何玉')+'''static oled_status_t render_page(uint8_t timebase, uint8_t mode, uint8_t hold)
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
'''
demo+=doc('main','启动人机接口演示并响应三个按键','无','嵌入式主程序不返回','按键先初始化再开启节拍；OLED失败每1秒重试；非测频程序','蒋观海')+'''int main(void)
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
'''
write('hmi_demo.c',demo)
# Create a separate Keil target; preserve the user's original example project.
project=(root.parent/'原始工程'/'2.uvprojx').read_text(encoding='utf-8')
project=project.replace('<TargetName>Target_1</TargetName>','<TargetName>HMI_Demo</TargetName>')
project=project.replace('<OutputDirectory>.\\Objects\\</OutputDirectory>','<OutputDirectory>.\\Objects_HMI\\</OutputDirectory>')
project=project.replace('<OutputName>2</OutputName>','<OutputName>HMI_Demo</OutputName>')
project=project.replace('<ListingPath>.\\Listings\\</ListingPath>','<ListingPath>.\\Listings_HMI\\</ListingPath>')
project=project.replace('.\\APP;.\\CMSIS;.\\Lib\\Include;.\\Lib\\Source',
                        '.\\APP;.\\CMSIS;.\\Lib\\Include;.\\Lib\\Source;.\\HARDWARE\\HMI')
files=''.join(f'<File><FileName>{f}</FileName><FileType>1</FileType><FilePath>.\\HARDWARE\\HMI\\{f}</FilePath></File>' for f in ['key.c','oled.c','hmi_port.c','hmi_demo.c'])
project=re.sub(r'<Group>\s*<GroupName>APP</GroupName>.*?</Group>',
               lambda m:'<Group><GroupName>HMI</GroupName><Files>'+files+'</Files></Group>',project,flags=re.S)
(root/'HMI.uvprojx').write_text(project,encoding='utf-8')
