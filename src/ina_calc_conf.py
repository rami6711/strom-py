# INA226 Config register calculator

# Lists of possible register settings
list_AVG = [['1', '0x0000'],['4', '0x0200'],['16', '0x0400'],['64', '0x0600'],['128', '0x0800'],['256', '0x0A00'],['512', '0x0C00'],['1024', '0x0E00'] ]

list_VBUSCT = [['140','0x0000'],['204','0x0040'],['332','0x0080'],['588','0x00C0'],['1100','0x0100'],['2116','0x0140'],['4156','0x0180'],['8244','0x01C0']]

list_VSHCT = [['140','0x0000'],['204','0x0008'],['332','0x0010'],['588','0x0018'],['1100','0x0020'],['2116','0x0028'],['4156','0x0030'],['8244','0x0038']]

list_MODE = [['Power off','0x0000'],['Vshunt, Triggered','0x0001'],['Vbus, Triggered','0x0002'],['Vshunt & Vbus, Triggered','0x0003'],['Power off','0x0004'],['Vshunt, Continuous','0x0005'],['Vbus, Continuous','0x0006'],['Vshunt & Vbus, Continuous','0x0007']]

constant_bits = 0x4000

# Structure of the config register
# constant_bits + AVG + VBUSCT + VSHCT + MODE

def get_config(choice, list_X):
    choice = int(choice)
    if choice < len(list_X):
        return list_X[choice][1]
    else:
        raise ValueError('Value out of range')

def get_value(choice, list_X):
    choice = int(choice)
    if choice < len(list_X):
        return list_X[choice][0]
    else:
        raise ValueError('Value out of range')

def list_view(list_X, prefix = '', suffix = ''):
    for index in range(len(list_X)):
        print('{}: {}{}{} ~ {}'.format(index, prefix, list_X[index][0], suffix, list_X[index][1]))

def config_reg():
    print('Averaging Mode:')
    list_view(list_AVG, 'N = ')
    select_avg_input = input('Please input sample number: ')
    select_avg = int(get_config(select_avg_input, list_AVG), 16)
    avg_value = int(get_value(select_avg_input, list_AVG))

    print('\nBus voltage conversion time:')
    list_view(list_VBUSCT, 'Tbus = ', 'us')
    select_VBUSCT_input = input('Please input VBUS conversion time: ')
    select_VBUSCT = int(get_config(select_VBUSCT_input, list_VBUSCT), 16)
    t_bus = int(get_value(select_VBUSCT_input, list_VBUSCT))

    print('\nShunt voltage conversion time:')
    list_view(list_VSHCT, 'Tshunt = ', 'us')
    select_VSHCT_input = input('Please input VSHUNT conversion time: ')
    select_VSHCT = int(get_config(select_VSHCT_input, list_VSHCT), 16)
    t_shunt = int(get_value(select_VSHCT_input, list_VSHCT))

    print('\nOperating mode:')
    list_view(list_MODE)
    select_MODE_input = input('Please input operating mode: ')
    select_MODE = int(get_config(select_MODE_input, list_MODE), 16)

    tb_ms = t_bus * avg_value / 1000
    ts_ms = t_shunt * avg_value / 1000
    print('Configuration result:')
    print('    Tbus = {} x {}us = {}ms'.format(avg_value, t_bus, tb_ms))
    print('    Tshunt = {} x {}us = {}ms'.format(avg_value, t_shunt, ts_ms))
    print('    Ttotal = {}ms'.format(tb_ms + ts_ms))

    # print('\n{} {} {} {} {}'.format(constant_bits, select_avg, select_VBUSCT, select_VSHCT, select_MODE))
    register = hex(constant_bits + select_avg + select_VBUSCT + select_VSHCT + select_MODE)
    register = '0x' + register[2:].upper()
    print('    Use "config" = ',register)
    return register

def round_up_125(value):
    preset = [1,2,5,10,20,50,100,200,500,1000,2000,5000,10000,20000,50000,100000]
    for x in preset:
        if value <= x:
            return x
    raise ValueError('The value exceeded the expected range.')

def calib_reg():
    max_expected_current = float(input('Please input maximum expected current in Amps: '))
    shunt_resistance = 0.001 * float(input('Please input shunt resistance in miliOhms: '))
    print('    Maximum allowed current = {:.2f}A'.format(0.08192/shunt_resistance))
    v_max = max_expected_current * shunt_resistance
    if v_max > 0.0819:
        raise ValueError('Shunt resistance too high: {:.3f}V'.format(v_max))
    current_lsb_uA = 1e6 * max_expected_current / 32768
    print('    Calculated Current_LSB: {} uA/bit'.format(current_lsb_uA))
    current_lsb_uA = round_up_125(current_lsb_uA)
    print('    Rounded Current_LSB: {} uA/bit'.format(current_lsb_uA))
    print('    Use "current_LSB" = {:f}'.format(1e-6 * current_lsb_uA))
    cal_register = 0.00512 / (shunt_resistance * current_lsb_uA / 1e6)
    print('    Use "calValue" = ',int(cal_register))
    print('    Shunt voltage Vmax = {:.3f}V'.format(v_max))
    return cal_register

status = True
print('Welcome to the INA226 configuration calculator.')
print('Results from this calculator can be used to configure the INA226 instance.')
while status:
    try:
        choice = input('Choice: (c)onfiguration or ca(l)ibration or (e)xit: ')
        if choice == 'c':
            print('\n')
            config_reg()
            print('\n')
        elif choice == 'l':
            print('\n')
            calib_reg()
            print('\n')
        elif choice == 'e':
            status = False
    except Exception as e:
        status = False
        print(e)

print('Goodbye!')
