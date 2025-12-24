from zoneinfo import available_timezones


timezones = {}

for zone in available_timezones():
    format = zone.split("/")
    if len(format) == 2:
        if format[0] not in timezones:
            timezones[format[0]] = [format[1]]
        else:
            timezones[format[0]].append(format[1])
