var RACE_UPDATE_PROTOCOL = "json";
var CURRENT_CLASS = 'run_current'; /* DO NOT CHANGE - value referenced in html */
var CURRENT_ID = 'run_current';
var isReversed = false;

function reverseLaneDisplay() {
	console.log('OLD isReversed=' + isReversed);
	isReversed = !isReversed;
	console.log('NEW isReversed=' + isReversed);
}

function getDate() {
	var now = new Date();
	var hour = 60*60*1000;
	var min = 60*1000;
	return new Date(now.getTime() + (now.getTimezoneOffset() * min));
}

function slugify(value) {
	// 1) convert to lowercase
	// 2) remove dashes and pluses
	// 3) replace spaces with dashes
	// 4) remove everything but alphanumeric characters and dashes
	return value.toLowerCase().replace(/-+/g, '').replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
}

function speed(t, dnf) {
	if (typeof(dnf) === 'undefined') dnf = false;
    if (null == t || 0 == t || dnf) return "-";
    var mph = ((Math.log((1 / Math.max(1.1, (t-1.0))) * 15) * 200)-75).toFixed(0);
    if (0 >= mph) mph = "-";
    return mph + ' MPH';
}

function testSpeed() {
	console.log('Entered testSpeed');
	var m = '';
	var s = 0.001;
	m+='' + s + '\t'+speed(s, 0) + "\n";
	for (s=0; s<=10; s+=.3333) {
		m+='' + s + '\t'+speed(s, 0) + "\n";
	}
	s = 9.99;
	m+='' + s + '\t'+speed(s, 0) + "\n";
	alert(m);
}

function getRun(data, run_seq) {
	var run = data.runs[run_seq-1]; // we can do this b/c runs is sorted on run_seq in the model
	return run;
}

function prettyDate(x) {
	/* Converts a date like:
	 *
	 * 2013-11-24T22:08:05.034439
	 *
	 * to
	 *
	 * 2013-11-24 22:08:05
	 */
	if (null != x && undefined != x) {
		if (x.length == 26) {
			result = x.substr(0, 10) + ' ' + x.substr(11,8);
		} else {
			return x;
		}
	}
	else result = "";
	return result;
}

function updateLastRefreshUI(now) {
	$('#last_refresh').text(prettyDate(now));
}

function myToFixed(x) {
	if (x == null) return '-';
	return x.toFixed(3);
}

function scrollToRun(event, run_seq) {
	console.log("ENTER scrollToRun");
	if (null != event) event.stopPropagation();
	if (null != run_seq && run_seq > 0) {
		console.log("scrollToRun(event, " + run_seq + ")...");
		var offset = $('#run_table_'+run_seq).offset();
		offset.left -= 20;
		/*offset.top -= 20;*/
		$('html, body').animate({
		    scrollTop: offset.top,
		    scrollLeft: offset.left
		});
	} else {
		console.log("scrollToRun(event, null) => hmmm, nothing to do!");
	}
	console.log("EXIT scrollToRun");
}

function scrollToCurrentRun(event) {
	if (null != event) event.stopPropagation();
	var offset = $('table.run_current').offset();
	offset.left -= 20;
	$('html, body').animate({
	    scrollTop: offset.top,
	    scrollLeft: offset.left
	});
}

function renderRun(data, run_seq, reversed, detailed) {
	console.log('BEGIN renderRun');
	var run = getRun(data, run_seq);

	if (null == run) {
		console.log('Could not find a run for run_seq=' + run_seq);
		return '';
	}
	var cls = '';
	var cid = 'run_table_' + run_seq; /* do not change this prefix - is referenced elsewhere */
	var isCurrentRun = false;
	if (run.run_id == data.current_run_id) {
		console.log("===== current found =====" + run.run_id + "/" + run.run_seq);
		cls = CURRENT_CLASS;
		isCurrentRun = true;
	}
	var colct = data.lane_ct + 1;
	var table = "<table id='" + cid + "' class='run-table " + cls + "'>";
	var table_body = "";
	var run_stamp = "";
	if (run.run_completed) {
		run_stamp = ' [' + prettyDate(String(run.run_stamp)) + ']';
	}
	var imgrow = '';
	if (detailed) imgrow = '<tr class="thin-hborder"><td/>';

	var prev_run_seq = parseInt(run_seq-1);
	var prev_nav_snip = "<button id='nav_prev_run_seq_"+prev_run_seq+"' class='ui-button' onclick='scrollToRun(event,"+prev_run_seq+")'>PREV</button>";
	var next_run_seq = parseInt(run_seq+1);
	var next_nav_snip = "<button id='nav_next_run_seq_"+next_run_seq+"' class='ui-button' onclick='scrollToRun(event,"+next_run_seq+")'>NEXT</button>";
	var curr_nav_snip = "<button id='nav_curr_run' class='ui-button' onclick='scrollToCurrentRun(event)'>CURRENT</button>";

	var row = ['<tr class="thin-hborder divider status-heading '+ cls +'"><td colspan="'+ parseInt(data.lane_ct-1) +
	           			'" width="90%" class="big-text">Run '+ run.run_seq +' of '+ data.runs.length +
	           			run_stamp +'</td><td colspan="2" class="center">'+prev_nav_snip + '&nbsp;&nbsp;&nbsp;' + ((true == isCurrentRun) ? '&nbsp;&nbsp;&nbsp;' : curr_nav_snip) + '&nbsp;&nbsp;&nbsp;' + next_nav_snip+'</td>',
				'<tr class="thin-hborder"><td width="10%" class="big-text">Lane</td>',
				imgrow,
	            '<tr class="thin-hborder"><td class="big-text">Car name</td>',
	            '<tr class="thin-hborder"><td class="big-text">Driver</td>',
				'<tr class="thin-hborder"><td class="big-text">Time</td>',
				'<tr><td class="big-text">Speed</td>'];

	colwidth = 90 / data.lane_ct;
	var loop_init = 0;
	var loop_inc = 1;
	var loop_end = data.lane_ct;
	if (true == reversed) {
		loop_init = data.lane_ct - 1;
		loop_inc = -1;
		loop_end = -1;
	}
	for (l = loop_init; l != loop_end; l+=loop_inc) {
		rp = run.runplaces[l];
		var c = 1; // skipping row[0], which is already complete
		row[c++] += "<td width='"+colwidth+"%' class='lane-label'>" + rp.lane + "</td>";
		if (detailed) {
			if (isCurrentRun) {
				tdid = "id='lane_"+rp.lane+"' racer_id='"+rp.racer_id+"' run_seq='"+run.run_seq+"' ";
			} else {
				tdid = '';
			}
			row[c++] += "<td "+tdid+
				"class='center'><img class='racer_pic' src='"+rp.racer_img+"' alt='("+rp.racer_img+")'/></td>";
		} else {
			c++;
		}
		row[c++] += "<td class='big-text'>#" + rp.racer_id + " " + rp.racer_name + "</td>";
		row[c++] += "<td class='big-text'>" + rp.person_name + "</td>";
		var seconds = '';
		var dnfClass = '';
		if (rp.dnf) {
			dnfClass = ' dnf';
			seconds = '* DNF *'
		} else if (null != rp.seconds) {
			seconds = Number(rp.seconds).toFixed(3) + ' sec.';
		} else {
			seconds = '-';
		}
		row[c++] += "<td class='big-text" + dnfClass + "'>" + seconds + "</td>";
		row[c++] += "<td class='big-text'>" + speed(rp.seconds, rp.dnf) + "</td>";
	}
	for (x = 0; x < row.length; x++) {
		if ('' != row) {
			table_body += row[x] + "</tr>";
		}
	}

	table_body += "</tr></table>";
	console.log('END renderRun');
	return table+table_body;
}
