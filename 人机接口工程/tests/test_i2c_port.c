#include "gd32f10x.h"
#include "hmi_port.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
mock_dwt_t mock_dwt;
mock_debug_t mock_debug;
uint32_t SystemCoreClock=1000000U;
static unsigned stage, fault, count, resets, stops, cleared;
static uint8_t sent[129];
void rcu_periph_clock_enable(uint32_t p) { (void)p; }
void gpio_init(uint32_t p,uint32_t mode,uint32_t speed,uint32_t pins)
{ (void)speed; (void)pins; if(p==GPIOB) assert(mode==GPIO_MODE_AF_OD); }
FlagStatus gpio_input_bit_get(uint32_t p,uint32_t pin)
{ (void)p; (void)pin; return SET; }
void i2c_deinit(uint32_t p) { assert(p==I2C1); ++resets; stage=0; }
void i2c_clock_config(uint32_t p,uint32_t speed,uint32_t duty)
{ assert(p==I2C1 && speed==100000U && duty==I2C_DTCY_2); }
void i2c_mode_addr_config(uint32_t p,uint32_t mode,uint32_t fmt,uint32_t addr)
{ (void)p; (void)mode; (void)fmt; (void)addr; }
void i2c_enable(uint32_t p) { (void)p; }
void i2c_ack_config(uint32_t p,uint32_t ack) { (void)p; (void)ack; }
void i2c_start_on_bus(uint32_t p) { (void)p; stage=1; cleared=0; }
void i2c_stop_on_bus(uint32_t p) { (void)p; ++stops; stage=fault==5?4:0; }
void i2c_master_addressing(uint32_t p,uint32_t addr,uint32_t mode)
{ assert(p==I2C1 && addr==0x78 && mode==I2C_TRANSMITTER); stage=2; }
void i2c_data_transmit(uint32_t p,uint8_t data)
{ assert(p==I2C1 && cleared); assert(count<129); sent[count++]=data; stage=3; }
void i2c_flag_clear(uint32_t p,i2c_flag_enum flag)
{ (void)p; if(flag==I2C_FLAG_ADDSEND) cleared=1; }
FlagStatus i2c_flag_get(uint32_t p,i2c_flag_enum flag)
{
    (void)p; mock_dwt.CYCCNT+=100;
    if(flag==I2C_FLAG_AERR) return ((fault==1 && stage==2)||(fault==2 && stage==3)||
                                 (fault==11 && stage==3 && count==3))?SET:RESET;
    if(flag==I2C_FLAG_LOSTARB) return fault==6 && stage==2?SET:RESET;
    if(flag==I2C_FLAG_BERR) return fault==7 && stage==2?SET:RESET;
    if(flag==I2C_FLAG_OUERR) return RESET;
    if(flag==I2C_FLAG_I2CBSY) return (stage || fault==4)?SET:RESET;
    if(flag==I2C_FLAG_MASTER) return stage && fault!=6?SET:RESET;
    if(flag==I2C_FLAG_SBSEND) return stage==1 && fault!=3?SET:RESET;
    if(flag==I2C_FLAG_ADDSEND) return stage==2 && fault!=8?SET:RESET;
    if(flag==I2C_FLAG_BTC) return stage==3 && fault!=9?SET:RESET;
    if(flag==I2C_FLAG_TBE) return fault==10?RESET:SET;
    return RESET;
}
uint32_t __get_PRIMASK(void) { return 0; }
void __disable_irq(void) {}
void __set_PRIMASK(uint32_t mask) { (void)mask; }
static void setup(unsigned f) { fault=f; count=0; stops=0; stage=0; cleared=0; }
int main(void)
{
    uint8_t data[128]; unsigned i,previous;
    memset(data,0xA5,sizeof(data));
    assert(HMI_OLEDWrite(0x40,data,1)==-1);
    HMI_PortInit();
    setup(0); assert(HMI_OLEDWrite(0x40,data,128)==0);
    assert(count==129 && sent[0]==0x40 && sent[128]==0xA5 && stops==1);
    setup(0); assert(HMI_OLEDWrite(0x00,data,3)==0);
    assert(count==4 && sent[0]==0x00);
    assert(HMI_OLEDWrite(0x01,data,1)==-1);
    assert(HMI_OLEDWrite(0x40,NULL,1)==-1);
    assert(HMI_OLEDWrite(0x40,data,0)==-1);
    assert(HMI_OLEDWrite(0x40,data,129)==-1);
    for(i=1;i<=11;++i) {
        setup(i); previous=resets; mock_dwt.CYCCNT=0xfffffff0U;
        assert(HMI_OLEDWrite(0x40,data,2)==-1);
        assert(resets>previous);
        if(i==6) assert(stops==0); /* lost arbitration: do not issue STOP */
        setup(0); assert(HMI_OLEDWrite(0x40,data,2)==0);
    }
    puts("PASS: I2C1 address/control/data/STOP, address/data NACK,");
    puts("BUSY/START/address/TBE/BTC/STOP timeout, arbitration loss,");
    puts("bus error, invalid args and successful transfer after recovery.");
    return 0;
}
