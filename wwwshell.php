<?php
# Author: Marcin Sztolcman <http://urzenia.net/>
# Copyright: (c) 2008
# License: GPL v.2
# Version: 0.1
#
# $Id$
# vim: ft=php

define ('HOME', '/home/mysz');



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
		"\n" => "<br />\n",
	);
	return strtr ($str, $pat);
}
function debug () {
	$args = func_get_args ();
	echo "<pre><strong>DEBUG:</strong>\n";

	$i = 0;
	foreach ($args as $arg) {
		echo ++$i .'. ';
		print_r ($arg);
		echo "\n";
	}
	echo '</pre>';
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
	$_SESSION['cwd'] = getcwd ();
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
	$return	= '';
	$code	= 0;

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
				$return	= sprintf ('Cannot change directory to "%s".', $cwd);
				$code	= 1;
			}
		}
		else {
			$return	= sprintf ('Cannot change directory to "%s".', $cwd);
			$code	= 1;
		}
	}

	# other command
	else {
		exec ($command.' 2>&1', $return, $code);

		$return		= join ("\n", $return);
		$return		= str_replace (array (' ', "\t", "\n"), array ('&nbsp;', '&nbsp;&nbsp;&nbsp;&nbsp;', "<br />\n"), $return);
	}


	# prepare results
	$results	.= '<p class="output_command">'. $_SESSION['cwd'] .' % '.str_entit ($_GET['command'])."</p>\n";
	if ($code > 0) {
		$results .= '<p class="output_error">'. $return ."</p>\n";
	}
	else {
		$results .= '<p class="output_correct">'. $return ."</p>\n";
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
					else {
						fs += parseInt (value[2]);
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
				max-height: 300px;
				min-height: 100px;
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
		<div id="navi"><span class="navi" id="fontDown">A--</span> <span class="navi" id="fontUp">A++</span></div>
		<div id="results"><?php echo $results; ?></div>
		<div id="cwd">&gt; <?php echo str_entit ($_SESSION['cwd']); ?></div>
		<form method="get" action="">
			<textarea name="command" id="command"></textarea><br />
			<input type="submit" name="execute" value="Wykonaj" />
			<input type="submit" name="clear" value="Wyczyść wyjście" />
		</form>
	</body>
</html>
