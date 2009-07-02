# washer.cpl

output-pin
    pin-number
    on-is               high/low

input-pint
    pin-number
    use-pullup          True/False
    on-is               high/low

translate
    input (repeat)
        output

pwm
    type                fast/phase-correct
    pin-number
    on-is               high/low
    freq

multi-position-switch
    use-pullups         True/False
    selected-pin-is     high/low
    pin-number (repeat)
        value

translate 1 wash_temp: hot
translate 2 wash_temp: hot
translate 3 wash_temp: warm
translate 4 wash_temp: warm
translate 5 wash_temp: cold

translate 1 rinse_temp: warm
translate 2 rinse_temp: cold
translate 3 rinse_temp: warm
translate 4 rinse_temp: cold
translate 5 rinse_temp: cold

start water on temp:
    if temp is warm or cold: turn on cold_water
    if temp is hot or warm: turn on hot_water

stop water on temp:
    if temp is warm or cold: turn off cold_water
    if temp is hot or warm: turn off hot_water

to get wash_temp:
    return read temp_switch wash_temp

to get rinse_temp:
    return read temp_switch rinse_temp

to get water_level:
    return read water_level

task fill temp_label:
    set temp = get temp_label
    with water on temp:
        wait until water_level is get water_level

task agitate how_long:
    with clutch on agitate:
        with motor on get agitate_speed
            wait how_long

task spin how_long:
    with drain open:
        with clutch on neutral:
            with motor on medium:
                wait until water_level is empty 
            wait 3 sec  # for motor to stop
        with clutch on spin:
            with motor on medium:
                wait 10 sec
            with motor on high:
                wait how_long - 10 sec
            wait 5 sec  # for motor to stop

task buzz how_long:
    with buzzer on:
        wait how_long

task wash
    fill wash_temp
    agitate 10 min
    spin 3 min
    fill rinse_temp
    agitate 3 min
    spin 5 min
    buzz 3 sec
