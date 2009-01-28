<?php
# $Id$
# vim: ft=php
#
# Version: 0.2
# Author: Marcin ``MySZ`` Sztolcman <marcin@urzenia.net>
# Copyright: (r) 2008 - 2009
# Program: wwwshell.php - shell access via browser
# Date: 2009-01-28
# License: GPL v.2



# configuration
# your home directory
define ('HOME', '/home/mysz');
# how many commands store in history
define ('HISTORY_MAX', 30);
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
# putenv ('HOME='.HOME);

error_reporting (E_ALL | E_STRICT);
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
# clear output console
if (isset ($_GET['clear'])) {
	$_SESSION['results'] = $results;
}

# prepend console history
if (isset ($_SESSION['results'])) {
	$results .= $_SESSION['results'];
}

# commands history
if (!isset ($_SESSION['history']) || !is_array ($_SESSION['history'])) {
    $_SESSION['history'] = array ();
}

# set cwd
if (!isset ($_SESSION['cwd'])) {
	$_SESSION['cwd'] = getenv ('HOME') ? getenv ('HOME') : getcwd ();
}
# chdir to stored value
else {
	@chdir ($_SESSION['cwd']);
}

if (isset ($_GET['execute']) && isset ($_GET['command']) && $_GET['command']) {
	# magic_quotes_gpc :/
	if (get_magic_quotes_gpc ()) {
		$_GET['command'] = stripslashes ($_GET['command']);
	}
	# clean command
	$command = $_GET['command'];
	$command = str_replace (array ("\r", "\n"), array ('', ' '), $command);

	# default values
	$return	= array ('stdout' => '', 'stderr' => '');

	# we store few last commands
    $tmp_cmd = sprintf ('"%s"', addslashes ($command));
    if (count ($_SESSION['history']) && $_SESSION['history'][0] != $tmp_cmd) {
        array_unshift ($_SESSION['history'], $tmp_cmd);
    }
    $_SESSION['history'] = array_splice ($_SESSION['history'], 0, HISTORY_MAX);
    reset ($_SESSION['history']);

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
			<script type="text/javascript" src="http://code.jquery.com/jquery-1.2.6.pack.js"></script>
			<script type="text/javascript" src="http://dev.jquery.com/view/tags/plugins/autocomplete/1.0.2/jquery.autocomplete.pack.js"></script>
			<script type="text/javascript">
				function scrollResults () {
					e = $('#results');
					e.attr ('scrollTop', e.attr ('scrollHeight'));
				}
				function catchNaviFonts () {
					$ ('#fontDown').click (function () {
						fontSize ("-1");
					});
					$ ('#fontUp').click (function () {
						fontSize ("+1");
					});
					$ ('#fontStd').click (function () {
						fontSize ("12");
					});
				}
                var hist = new Array (<?php echo join (', ', $_SESSION['history']); ?>);
                $ (function () {
					scrollResults ();
					catchNaviFonts ();
					$('#command').focus ();
					$('#command').autocomplete (hist, {
                        'autoFill':     true,
                        'cacheLength':  <?php echo HISTORY_MAX; ?>,
                        'max':          <?php echo HISTORY_MAX; ?>,
                        'minChars':     0
                    });
                })
				function fontSize (offset) {
					var value = offset.match (/^(\+|-)?(\d+)$/);
					if (!value) return;

                    var e = $('#results');
                    var fs = e.css ('font-size').replace (/px$/, '');
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

					e.css ('font-size', fs);
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
            .ac_results {
	            padding: 0px;
	            border: 1px solid black;
	            background-color: white;
	            overflow: hidden;
	            z-index: 99999;
            }

            .ac_results ul {
	            width: 100%;
	            list-style-position: outside;
	            list-style: none;
	            padding: 0;
	            margin: 0;
            }

            .ac_results li {
	            margin: 0px;
	            padding: 2px 5px;
	            cursor: default;
	            display: block;
	            /*
	            if width will be 100% horizontal scrollbar will apear
	            when scroll mode will be used
	            */
	            /*width: 100%;*/
	            font: menu;
	            font-size: 12px;
	            /*
	            it is very important, if line-height not setted or setted
	            in relative units scroll will be broken in firefox
	            */
	            line-height: 16px;
	            overflow: hidden;
            }

            .ac_loading {
	            background: white url('indicator.gif') right center no-repeat;
            }

            .ac_odd {
	            background-color: #eee;
            }

            .ac_over {
	            background-color: #0A246A;
	            color: white;
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
			<input type="text" name="command" id="command" autocomplete="off" /><br />
			<input type="submit" name="execute" value="Wykonaj" />
			<input type="submit" name="clear" value="Wyczyść wyjście" />
		</form>
	</body>
</html>
