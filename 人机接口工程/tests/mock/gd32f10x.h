#ifndef MOCK_GD32_H
#define MOCK_GD32_H
#include <stdint.h>
typedef enum { RESET=0, SET=1 } FlagStatus;
typedef enum {
 I2C_FLAG_SBSEND,I2C_FLAG_ADDSEND,I2C_FLAG_BTC,I2C_FLAG_TBE,
 I2C_FLAG_BERR,I2C_FLAG_LOSTARB,I2C_FLAG_AERR,I2C_FLAG_OUERR,
 I2C_FLAG_MASTER,I2C_FLAG_I2CBSY
} i2c_flag_enum;
typedef struct { volatile uint32_t CTRL, CYCCNT; } mock_dwt_t;
typedef struct { volatile uint32_t DEMCR; } mock_debug_t;
extern mock_dwt_t mock_dwt;
extern mock_debug_t mock_debug;
extern uint32_t SystemCoreClock;
#define DWT (&mock_dwt)
#define CoreDebug (&mock_debug)
#define CoreDebug_DEMCR_TRCENA_Msk 1U
#define DWT_CTRL_CYCCNTENA_Msk 1U
#define GPIOA 0U
#define GPIOB 1U
#define GPIO_PIN_5 (1U<<5)
#define GPIO_PIN_6 (1U<<6)
#define GPIO_PIN_7 (1U<<7)
#define GPIO_PIN_10 (1U<<10)
#define GPIO_PIN_11 (1U<<11)
#define GPIO_MODE_IPU 1U
#define GPIO_MODE_AF_OD 2U
#define GPIO_OSPEED_2MHZ 2U
#define GPIO_OSPEED_50MHZ 50U
#define RCU_GPIOA 0U
#define RCU_GPIOB 1U
#define RCU_AF 2U
#define RCU_I2C1 3U
#define I2C1 1U
#define I2C_DTCY_2 0U
#define I2C_I2CMODE_ENABLE 0U
#define I2C_ADDFORMAT_7BITS 0U
#define I2C_ACK_ENABLE 1U
#define I2C_TRANSMITTER 0U
void rcu_periph_clock_enable(uint32_t p);
void gpio_init(uint32_t p,uint32_t mode,uint32_t speed,uint32_t pins);
FlagStatus gpio_input_bit_get(uint32_t p,uint32_t pin);
void i2c_deinit(uint32_t p);
void i2c_clock_config(uint32_t p,uint32_t speed,uint32_t duty);
void i2c_mode_addr_config(uint32_t p,uint32_t mode,uint32_t fmt,uint32_t addr);
void i2c_enable(uint32_t p);
void i2c_ack_config(uint32_t p,uint32_t ack);
void i2c_start_on_bus(uint32_t p);
void i2c_stop_on_bus(uint32_t p);
void i2c_master_addressing(uint32_t p,uint32_t addr,uint32_t mode);
void i2c_data_transmit(uint32_t p,uint8_t data);
FlagStatus i2c_flag_get(uint32_t p,i2c_flag_enum flag);
void i2c_flag_clear(uint32_t p,i2c_flag_enum flag);
uint32_t __get_PRIMASK(void);
void __disable_irq(void);
void __set_PRIMASK(uint32_t mask);
#endif
