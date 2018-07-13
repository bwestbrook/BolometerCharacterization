from lab_code import lab_serial

motor_driver = lab_serial.lab_serial(port='/dev/ttyUSB0')
print motor_driver.write_read('RS')

print motor_driver.write_read('IP')

'''
Some useful commands you may want:
RS
CJ (probably not)
SJ (probably not)
FL
EP
DL
FP
FY
FS
IP
IS
MD
ME

'''
