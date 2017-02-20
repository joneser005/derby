Pack 180 timer is Fast Track.  GE district is The Champ.

Generic serial hints:
dmesg | egrep --color 'serial|ttyS'
cu -l /dev/ttyS0 -s 9600
    tilde to exit
screen /dev/ttyUSB0 9600
    <ctrl>-a then ? for help, \ to exit

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

        TODO: Test their track results with and without rl command.
        First test (program) was not getting any results.  We may have to send
        'rg' (return results when race ends) once or as soon as we start listening (ever time)


????? Does the Champ send anything on reset?  IOW can we learn of a reset event without polling with the read reset sw cmd ('rr')


----- begin read current settings (save results) -----
v  "eTekGadget SmartLine Timer v20.09 (B0010)"

rr  read reset sw 1=active
rs  read start sw 1=active
rl  read finish line 1=active for each lane
on  # lanes
ol  lane char
op  place char
om  lane mask
od  num decimals (3-5)
or  reset delay secs
of  photo finish trigger delay ms (0-255)
ow  photo finish trigger length ms (0-255)
ox  DTX000 mode
ov  1=reverse lanes
----- end read current settings -----

----- begin set desired settings -----
r
v
on4
ol3
op3
om0
od3
or0
ov0
----- end desired settings -----
rg   (return results at end of race)



----- Set to original settings (based on prior interrogation - did not pull all vars) -----
od4
ol1
om  (no response - no mask)
on4
opa (note it reported 'a' vs. '0')
----- end set to original settings -----


    On connection (or init via shell for now, until we write code to send commands), read/log/set the following settings:
        r = reset

        od<cr> reads the # of decimals set
        od3<cr> sets the # of decimals to 3.  Max is 5.  This program should work with any value, but as of Jan 2017 on-screen rendering has not been tested with > 3.

        ol<cr> reads current lane char (represents lane)
        ol3<cr> sets lane char to uppercase letters

        om<cr> Lane mask
        Should never need to change this - we don't mask lanes
        om0 resets the track to the # of lanes available

        on<cr> reads the # of lanes
        Should never need to change this unless it is found to misreport the number of physical lanes.
        on4<cr> to set the lane count to 6 (use Race.lane_ct)
            Note there exists code that prevents > 6 lanes, shouldn't be too hard to fix that.  Search for 'HACK'.  Robb - Jan 2017

        op3<cr> sets the place char to '!' - use this vs. anything else (0='a', 1='A', 2='1').
        If the exclamation point is used the placement values will be the following characters starting with the !: !”#$%&’(

        rg<cr> return results when race ends


        3.1.1 Race Result Commands
            ra  Force end of race, return results, then reset
            rg  Return results when race ends
            rp  Return results from previous race

        3.1.4 Read Switches
            rr  Read reset switch
                0(inactive) or 1(active) returned
            rs  Read Start Switch
                0(inactive) or 1(active) returned
            rl  Read finish line
                0(inactive) or 1(active) returned for each lane

        3.1.5 Set or Read Variables

        on
        Set/Read number of lanes
        The total physical number of lanes on your track.
        on<cr>
        Reads the current setting.
        on4<cr>
        Set to 4 lane track

        ol
        Set/Read lane character
        Indicates lane 1 in the response to the ra, rg and rp commands.
        ol<cr>
        Reads the current setting.
        ol0<cr>
        Set to ‘A’
        ol1<cr>
        Set to ‘1’
        ol2<cr>
        Set to ‘a’
        ol3<cr>
        Set to ‘A’ (Refer to details for reasoning of this.)

        op
        Set/Read place character
        Indicates place in the response to the ra, rg and rp commands.
        op<cr>
        Reads current setting of placement character.
        op0<cr>
        Set to ‘a’
        op1<cr>
        Set to ‘A’
        op2<cr>
        Set to ‘1’
        op3<cr>
        Set to ‘!’

        om
        Set/Read lane mask
        Mask off the lane specified until reset with om0,on or power cycle.
        om<cr>
        Reads the current setting.
        om3<cr>
        Mask lane 3
        om0<cr>
        Resets mask to use all lanes

        od
        Set/Read number of decimal places in the result values.

        od<cr>
        Reads current number of decimals

        od3<cr>
        Set to 3 decimals

        od4<cr>
        Set to 4 decimals

        od5<cr>
        Set to 5 decimals

        or
        Set/Read automatic reset delay
        Set the delay up to 255 seconds.
        or<cr>
        Reads current setting of reset delay in seconds
        or10<cr>
        Set to 10 seconds
        or30<cr>
        Set to 30 seconds
        or0<cr>
        Auto reset off
        Manualslib.com manuals search engine
        12

        of
        Set./Read photo finish trigger delay
        Set the delay up to 255 milliseconds.

        ow
        Set/Read photo finish trigger length
        Set the trigger length up to 255 milliseconds.
        ox
        Set the finish line to DTX000 mode
        This changes the Champ Timer finish line to use the DTX000 format.
        ox1<cr>
        Go into DTX000 mode
        ox0<cr>
        Return to Champ Timer lower and upper case
        mode

        ov
        Set/Read reverse lane numbering
        ov<cr>
        Reads value of 0 or 1 for normal or reverse.
        ov0<cr>
        normal, Lanes displayed left to right [1 2 3 4]
        ov1<cr>
        reverse, Lanes displayed right to left [4 3 2 1]
        (Refer to details for more complete information).
