Pack 180 timer is Fast Track.  GE district is The Champ.

Generic serial hints:
dmesg | egrep --color 'serial|ttyS'
cu -l /dev/ttyS0 -s 9600
    tilde to exit
screen /dev/ttyS0 9600
screen /dev/ttySUSB0 19200,cs8

Fast Track protocol, in a nutshell:

    Q. I want to write my own software. What is the format of the timer's serial interface?
    A. The timer sends this string when all the cars have finished.

    A=1.234! B=2.345 C=3.456 D=4.567 E=0.000 F=0.000

    It puts an exclamation point after the winning time, with 2 spaces after every time (the exclamation point takes up a space). Also if you only have a 4 lane track the unused lanes (E and F in this example) will show 0.000
    Other characters:
    It sends an "@" sign whenever the reset switch is closed. Also it sends a <LF> and a <CR> (That is ASCII code 10 and 13) at the end of each string.
    The serial settings to view the timer results yourself are 9600 baud, 8 bits, no parity, 1 stop bit, no flow control. With these settings you should be able to see the results in hyperterminal.

    (derby2016env)robb@agrippa:~/derby2016env/local/derby/fast-track-docs > cat track-listen.sh
    #!/bin/sh
    screen /dev/ttyUSBO -s 9600

The Champ
    See champ_timer.pdf, pages 11-25, particularly Appendix A.  Results are similar to Fast Track.  Unit may require some intiial command setup to configure # lanes and set mode to send results after all lanes are tripped.

    "If the rg command is sent to the Champ Timer Finish Line, a result string will be returned after the race has been completed. The race is not completed until all cars have passed through the finish line or the force finish command is used."


    Commands to send to The Champ
        Command strings end with <cr>
        Command result strings received end with <cr><lf>
            ?<cr><lf> = invalid command
            <cr><lf> = result of setting a new value

    On connection (or init via shell for now, until we write code to send commands), read/log/set the following settings:
        r = reset

        od<cr> reads the # of decimals set
        od3<cr> sets the # of decimals to 3.  Max is 5.  This program should work with any value, but as of Jan 2017 on-screen rendering has not been tested with > 3.

        ol<cr> reads current lane char (represents lane)
        ol3<cr> sets lane char to uppercase letters

        om<cr> reads the # of lanes to be used
        Should never need to change this unless it is found to misreport the number of physical lanes (we want this to equal the # of physical lanes - see next note)
        om0 resets the track to the # of lanes available
            Note for races where lanes in use < # track lanes, we just ignore the unused lane results, so no need to ever change this value.

        on<cr> reads the # of lanes
        Should never need to change this unless it is found to misreport the number of physical lanes.
        on4<cr> to set the lane count to 6 (use Race.lane_ct)
            Note there exists code that prevents > 6 lanes, shouldn't be too hard to fix that.  Search for 'HACK'.  Robb - Jan 2017

        op3<cr> sets the place char to '!' - use this vs. anything else (0='a', 1='A', 2='1').
        If the exclamation point is used the placement values will be the following characters starting with the !: !”#$%&’(

        rg<cr> return results when race ends

----- begin -----
od3
ol3
om0
on
on4
op3
rg
----- end -----