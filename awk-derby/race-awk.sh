#!/usr/bin/awk -f
BEGIN { 
	FS="xxx" # Effectively disabling the Field Separator marker
	resultfile="./derby-results.current"
	lastresultfilebase="./derby-results."
	rc=system("test -f " lastresultfile)
	filect=1
	while (rc==0) {
		lastresultfile=lastresultfilebase filect
		print "Looking for " lastresultfile
		rc=system("test -f " lastresultfile)
		filect++;
	}
	print "lastresultfile=" lastresultfile
	system("mv -v " resultfile " " lastresultfile)	
	print "Races started at " strftime("%r", systime()) > resultfile
}

function getspeed(t) {
	if (0 == t) return 0
	mph = log((1 / (t+0.5)) * 10) * 150
	sub(/\..*/, "", mph)
	if(0 > mph) mph = 0
	return mph
}

{
	print "======================================="
	print "Raw=[" $0 "]"
	print "======================================="

	if (36 < length($0)) {
		# Remove unwanted chars.
		print "===>"
		print "Line=[" $line "]"
		line=sub("[@\r\n]", "", $line) # remove chars
		line=sub("[@\r\n]", "", $line) # remove chars
		line=sub("[@\r\n]", "", $line) # remove chars
		line=sub("[@\r\n]", "", $line) # remove chars
		line=sub("[@\r\n]", "", $line) # remove chars
		line=sub("[@\r\n]", "", $line) # remove chars
		line=sub("!"," ",$line)        # replace race winner ind with space
		line=sub("  $","",$line)       # remove trailing spaces
		gsub("  ","~",$line)           # convert 2 spaces to tilde

		# Now we have a string with two spaces delimiting each lane result
		print "Line=[" $line "]"
		print "<==="
		split($line,results,"~")

		print "Unsorted results:"
		for (i in results) {
			print i " = [" results[i] "]"
		}

		print "Move the lane letter to the end so we can sort on the times"
		for (i in results) {
			x=results[i]
			print "Old result " i " = [" results[i] "]"
			results[i]=substr(x,3) substr(x,1,1)
			print "New result " i " = [" results[i] "]"
		}

		asort(results)

		# Move the lane designator (A-F) back to the front and make it human-readable/friendly
		# Not being proficient with Awk, this is probably a horribly ineffient way of doing this...
		for (i in results) {
			x=results[i];
			results[i]=substr(x,6) substr(x,1,5)
			sub(/A/,"1\t",results[i])
			sub(/B/,"2\t",results[i])
			sub(/C/,"3\t",results[i])
			sub(/D/,"4\t",results[i])
			sub(/E/,"5\t",results[i])
			sub(/F/,"6\t",results[i])
		}

		print "\nRace #" ++iteration " at " strftime("%r", systime()) " results: "
		print "\nRace #" iteration " at " strftime("%r", systime()) " results: " >> resultfile 
		print "Raw=[" $0 "]" >> resultfile
		print "Place\tLane\tTime\tMPH"
		print "Place\tLane\tTime\tMPH" >> resultfile 
		for (i = 1; i < 7; i++) {
			print i "\t" results[i] "\t" getspeed(substr(results[i], 2)) " MPH"
			print i "\t" results[i] "\t" getspeed(substr(results[i], 2)) " MPH" >> resultfile
		}
		close(resultfile)
	}
}
