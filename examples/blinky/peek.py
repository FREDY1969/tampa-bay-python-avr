import sys
sys.stdin = open('flash.hex','r')
for line in sys.stdin:
    templine = line[0:3] + ' ' + line[3:7] +  ' ' + line[7:9] +' ' 
    j = 9
    while j < len(line)-4:
        templine = templine +  line[j+2:j+4] + line[j:j+2] + ' '
        j+=4
    print(templine)
