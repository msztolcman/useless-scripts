<?php
# Author: Marcin Sztolcman <http://urzenia.net/>
# Copyright: (c) 2008
# License: GPL v.2
# Version: 0.1
#
# $Id$
# vim: ft=php

# configuration
# your home directory
define ('HOME', '/home/mysz');

# your aliases
$aliases = array (
	'll'	=> 'ls -l',
	'la'	=> 'ls -la',
	'..'	=> 'cd ..',
	'...'	=> 'cd ../..',
	'pax'	=> 'ps awux',
	'paxg'	=> 'ps awux | grep',
	'g'		=> 'grep',
	'gi'	=> 'grep -i',
	'gr'	=> 'grep -ir',
);



# do not touch below this line - except you exactly now what are you doing...
putenv ('HOME='.HOME);

error_reporting (E_ALL|E_STRICT);
if (!session_id ()) {
	session_start ();
}

function str_entit ($str) {
	$pat = array (
		'<' => '&lt;',
		'>' => '&gt;',
		'"' => '&quot;',
		"\r" => '',
	);
	return strtr ($str, $pat);
}
function debug () {
	$args = func_get_args ();
	echo "<pre><strong>DEBUG:</strong>\n";

	$i = 0;
	foreach ($args as $arg) {
		printf ("%d. %s\n", ++$i, print_r ($arg, 1));
	}
	echo '</pre>';
}
function expand_alias ($command) {
	$length = strcspn ($command, " \t");
	$cmd = substr ($command, 0, $length);

	if (isset ($GLOBALS['aliases'][$cmd])) {
		return $GLOBALS['aliases'][$cmd] . substr ($command, $length);
	}
	return $command;
}

function execute ($command) {
	$output = array ();
	$res = proc_open ($command, array (
			1 => array('pipe', 'w'),
			2 => array('pipe', 'w')
		), $output);

	$return = array ('stderr' => '', 'stdout' => '');
    while (!feof($output[1])) {
        $return['stdout'] .= fgets($output[1]);
    }

    while (!feof($output[2])) {
        $return['stderr'] .= fgets($output[2]);
    }

    fclose($output[1]);
    fclose($output[2]);
    proc_close($res);

	return $return;
}

$results = '';
# cleat output console
if (isset ($_GET['clear'])) {
	$_SESSION['results'] = $results;
}

# prepend console history
if (isset ($_SESSION['results'])) {
	$results .= $_SESSION['results'];
}

# set cwd
if (!isset ($_SESSION['cwd'])) {
	$_SESSION['cwd'] = getenv ('HOME') ? getenv ('HOME') : getcwd ();
}
# chdir to stored value
else {
	@chdir ($_SESSION['cwd']);
}


if (isset ($_GET['command']) && $_GET['command']) {
	# magic_quotes_gpc :/
	if (get_magic_quotes_gpc ()) {
		$_GET['command'] = stripslashes ($_GET['command']);
	}
	# clean command
	$command = $_GET['command'];
	$command = str_replace (array ("\r", "\n"), array ('', ' '), $command);

	# default values
	$return	= array ('stdout' => '', 'stderr' => '');

	# aliases
	$command = expand_alias ($command);

	# cd - we change directory
	if (preg_match ('#^\s*cd(?:\s+(.*))?#', $command, $match)) {
		if (!isset ($match[1]) || trim ($match[1]) == '~') {
			$match[1] = getenv ('HOME');
		}

		$cwd = realpath (trim ($match[1]));
		if ($cwd && is_dir ($cwd) && is_executable ($cwd)) {
			if (@chdir ($cwd)) {
				$_SESSION['cwd'] = $cwd;
			}
			else {
				$return['stderr'] = sprintf ('Cannot change directory to "%s".', $cwd);
			}
		}
		else {
			$return['stderr'] = sprintf ('Cannot change directory to "%s".', $cwd);
		}
	}

	# other command
	else {
		$return = execute ($command);
		foreach (array ('stdout', 'stderr') as $io) {
			if (!isset ($return[$io])) {
				continue;
			}

			$return[$io] = str_entit ($return[$io]);
			$return[$io] = str_replace (array (' ', "\t", "\n"), array ('&nbsp;', '&nbsp;&nbsp;&nbsp;&nbsp;', "<br />\n"), $return[$io]);
		}
	}

	# prepare results
	$results	.= '<p class="output_command">'. $_SESSION['cwd'] .' $ '.str_entit ($_GET['command'])."</p>\n";
	if ($return['stdout']) {
		$results .= '<p class="output_correct">'. $return['stdout'] ."</p>\n";
	}
	if ($return['stderr']) {
		$results .= '<p class="output_error">'. $return['stderr'] ."</p>\n";
	}

	# store results in session
	$_SESSION['results'] = $results;
}

?><html>
	<head>
		<title>wwwShell (c)2008, Marcin Sztolcman</title>
			<script type="text/javascript">
				function scrollResults () {
					e = document.getElementById ('results');
					e.scrollTop=e.scrollHeight;
				}
				function catchNaviFonts () {
					document.getElementById ('fontDown').onclick = function () {
						fontSize ("-1");
					}
					document.getElementById ('fontUp').onclick = function () {
						fontSize ("+1");
					}
					document.getElementById ('fontStd').onclick = function () {
						fontSize ("12");
					}
				}
				window.onload = function () {
					scrollResults ();
					catchNaviFonts ();
					document.getElementById ('command').focus ();
				}
				function fontSize (offset) {
					var value = offset.match (/^(\+|-)?(\d+)$/);
					if (!value) return;

					var styles = window.getComputedStyle (document.getElementById ('results'), null);
					var fs = styles.fontSize.replace (/px$/, '');
					fs = parseInt (fs);
					if (value[1] == '-') {
						fs -= parseInt (value[2]);
					}
					else if (value[1] == '+') {
						fs += parseInt (value[2]);
					}
					else {
						fs = parseInt (value[2]);
					}

					e.style.fontSize = fs + 'px';
				}
		</script>
		<style type="text/css">
			body {
				font-family: "DejaVu Sans Mono", "Lucida Console", Courier, "Courier New", monospace;
				font-size: 12px;
			}
			#results {
				width: 90%;
				height: 300px;
				margin: 0 auto 10px auto;
				border: 1px solid black;
				padding: 10px;
				overflow: auto;
				font-size: 12px;
			}
			#command {
				width: 600px;
				height: 140px;
				margin: 0 auto;
			}
			.output_command {
				color: black;
				font-weight: bold;
			}
			.output_error {
				color: red;
				text-decoration: italic;
			}
			.output_correct {
				color: blue;
				text-decoration: none;
				font-weight: normal;
			}
			#navi {
				width: 90%;
				text-align: right;
			}
			.navi {
				cursor: pointer;
			}
		</style>
	</head>
	<body>
		<div id="navi">
			<span class="navi" id="fontDown" title="Shrink font size in results window">--A</span>
			<span class="navi" id="fontStd" title="Reset font size in results window">A</span>
			<span class="navi" id="fontUp" title="Enlarge font size in results window">A++</span></div>
		<div id="results"><?php echo $results; ?></div>
		<div id="cwd">&gt; <?php echo str_entit ($_SESSION['cwd']); ?></div>
		<form method="get" action="">
			<textarea name="command" id="command"></textarea><br />
			<input type="submit" name="execute" value="Wykonaj" />
			<input type="submit" name="clear" value="Wyczyść wyjście" />
		</form>
	</body>
</html>
