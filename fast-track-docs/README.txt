Q. I want to write my own software. What is the format of the timer's serial interface?
A. The timer sends this string when all the cars have finished.

A=1.234! B=2.345 C=3.456 D=4.567 E=0.000 F=0.000

It puts an exclamation point after the winning time, with 2 spaces after every time (the exclamation point takes up a space). Also if you only have a 4 lane track the unused lanes (E and F in this example) will show 0.000
Other characters:
It sends an "@" sign whenever the reset switch is closed. Also it sends a <LF> and a <CR> (That is ASCII code 10 and 13) at the end of each string.
The serial settings to view the timer results yourself are 9600 baud, 8 bits, no parity, 1 stop bit, no flow control. With these settings you should be able to see the results in hyperterminal.
