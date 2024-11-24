cd src

python -m mpy_cross hdc1080.py
python -m mpy_cross ina226.py
python -m mpy_cross ssd1306.py
python -m mpy_cross veml7700.py

move hdc1080.mpy ../lib/hdc1080.mpy
move ina226.mpy ../lib/ina226.mpy
move ssd1306.mpy ../lib/ssd1306.mpy
move veml7700.mpy ../lib/veml7700.mpy

cd..
pause
