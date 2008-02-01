#!/usr/bin/env perl

# Author: Marcin Sztolcman <http://urzenia.net/email>
# Version: 1.0.1
# License: GPL v.2
# Copyright: @2007 Marcin Sztolcman
# SVN: $Id: killer.pl 3 2008-01-14 09:25:22Z mysz $

package Killer;
#use strict;
#use warnings;
{
	# deklaracja sygnałów
	my %signals = qw/
		SIGHUP		 1
		SIGINT		 2
		SIGQUIT		 3
		SIGILL		 4
		SIGTRAP		 5
		SIGABRT		 6
		SIGIOT		 6
		SIGBUS		 7
		SIGFPE		 8
		SIGKILL		 9
		SIGUSR1		10
		SIGSEGV		11
		SIGUSR2		12
		SIGPIPE		13
		SIGALRM		14
		SIGTERM		15
		SIGSTKFLT	16
		SIGCHLD		17
		SIGCONT		18
		SIGSTOP		19
		SIGTSTP		20
		SIGTTIN		21
		SIGTTOU		22
		SIGURG		23
		SIGXCPU		24
		SIGXFSZ		25
		SIGVTALRM	26
		SIGPROF		27
		SIGWINCH	28
		SIGIO		29
		SIGPOLL		29
		SIGPWR		30
		SIGSYS		31
		SIGUNUSED	31
		SIGRTMIN	32
	/;

	# szablon strony
	my $template = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="pl">
<head>
	<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
	<title>killer (&copy; 2007 Marcin Sztolcman)</title>
	<script type="text/javascript">
		function toggleChecks (parent) {
			var checks = parent.getElementsByTagName ("input");
			for (var i=0; i<checks.length; ++i) {
				if (checks[i].type == "checkbox") {
					checks[i].checked = !checks[i].checked;
				}
			}
		}
		function colorize () {
			var rows = document.getElementsByTagName ("tbody")[0].getElementsByTagName ("tr");
			for (var i =0; i<rows.length; ++i) {
				rows[i].onmouseover	= function (obj) {
					colorizeRow (obj.currentTarget, "trover");
				}
				rows[i].onmouseout	= function (obj) {
					decolorizeRow (obj.currentTarget, "trover");
				}
				makeClickable (rows[i]);
			}
		}

		function colorizeRow (row, class) {
			var cells = row.getElementsByTagName("td");
			for (var i=0; i<cells.length; ++i) {
				cells[i].className += " " + class;
			}
		}
		function decolorizeRow (row, class) {
			var cells = row.getElementsByTagName("td");
			var rxp = new RegExp ("\\\\s+"+class);
			for (var i=0; i<cells.length; ++i) {
				cells[i].className = cells[i].className.replace (rxp, "");
			}
		}
		function makeClickable (row) {
			var cells = row.getElementsByTagName("td");
			for (var i=0; i<cells.length; ++i) {
				cells[i].onclick = function () {
					var input = row.getElementsByTagName ("input")[0];
					if (input.checked) {
						input.checked = false;
						decolorizeRow (row, "selected");
					}
					else {
						input.checked = true;
						colorizeRow (row, "selected");
					}
				}
			}
			var input = row.getElementsByTagName ("input")[0];
			input.onclick = function () {
				this.checked = !this.checked;
			}
		}

		window.onload = function () {
			colorize ();
			if ({AUTO_REFRESH}) {
				setTimeout (function () { document.getElementById ("refresh").click () }, {AUTO_REFRESH} * 1000);
			}
		}
	</script>
	<style type="text/css">
		body {
			font-family: Tahoma, Arial, Helvetica, sans-serif;
		}
		table {
			width: 100%;
		}
		.r1 {
			background-color: #eee;
		}
		.r2 {
			background-color: #ccc;
		}
		th a {
			color: blue;
		}
		th a:hover {
			color: red;
			text-decoration: none;
		}
		.trover {
			background-color: #aaa;
		}
		.selected {
			background-color: #888;
		}
		#ps_options {
			width: 10em;
		}
		#auto_refresh {
			width: 3em;
			text-align: right;
		}
	</style>
</head>
<body>
	<form method="post" action="{ROOT}">
	<table>
		<thead>
			<tr>
				<td><input type="checkbox" onclick="toggleChecks (document.getElementsByTagName(\'tbody\')[0])" /></td>
				{TABLE_HEADERS}
			</tr>
		</thead>
		<tfoot>
			<tr>
				<td colspan="{COLUMNS_QUANT}" style="text-align: center">
					<input type="text" id="ps_options" name="ps_options" value="{PS_OPTIONS}" />
					<input type="text" id="auto_refresh" name="auto_refresh" value="{AUTO_REFRESH}" />
					<input type="submit" name="refresh" id="refresh" value="Odśwież" />
					<input type="submit" name="submit" value="KILL!" onclick="return confirm (\'Are you really sure?!\')" />
					<select name="signal">
						{SELECT_SIGNALS}
					</select>
					<input type="hidden" name="sort" value="{GET_SORT}" />
					<input type="hidden" name="sort_by" value="{GET_SORT_BY}" />
				</td>
			</tr>
		</tfoot>
		<tbody>
			{TABLE_BODY}
		</tbody>
	</table>
	</form>
</body>
</html>';


	sub new {
		my ($class, ) = @_;

		my $self = {
			get		=> scalar prepare_get_data (),
			post	=> scalar prepare_post_data (),
		};

		$$self{get}{signal} 	||= 15;
		$$self{get}{'sort'}		||= 'asc';
		$$self{get}{sort_by}	||= 'PID';
		$$self{get}{ps_options}	||= 'awwwux';

		$$self{request}	= {
			%{$$self{get}	|| {}},
			%{$$self{post}	|| {}},
		};

		$$self{root} = (
			exists ($ENV{DOCUMENT_URI})	? $ENV{DOCUMENT_URI}	:
			exists ($ENV{REQUEST_URI})	? $ENV{REQUEST_URI}		:
			'/'
		);

		return bless ($self, $class);
	}

	sub enumerate {
		my ($self, $arr) = @_;

		my ($lp, @ret);
		@ret = map { [$lp++, $_] } @$arr;

		return wantarray ? @ret : \@ret;
	}

	sub is_numeric {
		return ($_[1] =~ /^\d+(?:\.\d+)?$/);
	}

	sub is_equal {
		my ($self, $v1, $v2, $ignorecase) = @_;

		if ($self->is_numeric ($v1) && $self->is_numeric ($v2)) {
			return ($v1 == $v2);
		}
		elsif ($ignorecase) {
			return (lc ($v1) eq lc ($v2));
		}
		else {
			return ($v1 eq $v2);
		}
	}


	sub prepare_get_data {
		my ($self, $qs) = @_;

		$qs ||= $ENV{QUERY_STRING};
		return if (!$qs);

		# dwie pętle, ponieważ zakładam ze dana wartość może pojawić się wielokrotnie w querystringu
		my ($k, $v, $part, %ret, );
		foreach $part (split (/\&amp;|\&/, $qs)) {
			($k, $v) = split (/\=/, $part);
			push (@{$ret{$k}}, $v);
		}

		# wszystko co się pojawi wielokrotnie składamy łącząc je binarnym zerem
		foreach $k (keys %ret) {
			$ret{$k} = join ("\x{0}", @{$ret{$k}});
		}

		return wantarray ? %ret : \%ret;
	}

	sub prepare_post_data {
		my ($self) = @_;
		return () if (!exists ($ENV{REQUEST_METHOD}) || $ENV{REQUEST_METHOD} ne 'POST');

		my (%ret, $tmp, $part, $k, $v, );
		read (STDIN, $tmp, $ENV{CONTENT_LENGTH});

		# dwie pętle, ponieważ zakładam ze dana wartość może pojawić się wielokrotnie w querystringu
		foreach $part (split( /\&/, $tmp )) {
			($k, $v) = split( /\=/, $part, 2);
			$v =~ s/%23/\#/g;
			$v =~ s/%2F/\//g;
			push (@{$ret{$k}}, $v);
		}

		# wszystko co się pojawi wielokrotnie składamy łącząc je binarnym zerem
		foreach $k (keys %ret) {
			$ret{$k} = join ("\x{0}", @{$ret{$k}});
		}

		return wantarray ? %ret : \%ret;
	}

	sub set_headers {
		my ($self, $fields) = @_;

		my ($field, );
		foreach $field ($self->enumerate ($fields)) {
			$$self{fields}{$$field[1]} = $$field[0];
		}
		return 1;
	}

	sub get_process_list {
		my ($self, $options) = @_;

		$options ||= 'awwwux';

		my ($ps, $line, $head, @body, );

		$ps = `ps $options`;
		($head, @body) = split (/\n/, $ps);

		$head = [ split (' ', $head) ];
		foreach $line (@body) {
			$line = [ split (' ', $line, scalar (@$head)) ];
		}

		$self->set_headers ($head);

		return wantarray ? ($head, \@body) : [$head, \@body];
	}

	sub _sort_processes_list__asc {
		my ($self, $q) = @_;

		my (@ret, $v1, $v2);
		return sort {
			($v1, $v2) = ($$a[$$q{sort_by}], $$b[$$q{sort_by}]);
			($self->is_numeric ($v1) && $self->is_numeric ($v2)) ?
				$v1 <=> $v2
				:
				$v1 cmp $v2
		} @{$$q{ps}};
	}

	sub _sort_processes_list__desc {
		my ($self, $q) = @_;

		my (@ret, $v1, $v2);
		return sort {
			($v1, $v2) = ($$a[$$q{sort_by}], $$b[$$q{sort_by}]);
			($self->is_numeric ($v1) && $self->is_numeric ($v2)) ?
				$v2 <=> $v1
				:
				$v2 cmp $v1
		} @{$$q{ps}};
	}

	sub sort_processes_list {
		my ($self, $q) = @_;
		return if (!$$q{ps} || ref ($$q{ps}) ne 'ARRAY' || !$$self{fields});

		$$q{'sort'}		||= 'asc';
		$$q{sort_by}	||= 'PID';

		my $method = $self->can ('_sort_processes_list__'. lc ($$q{'sort'}));
		if (!$method || !exists ($$self{fields}{$$q{sort_by}})) {
			return wantarray ? $$q{ps} : @{$$q{ps}};
		}

		$$q{sort_by} = $$self{fields}{$$q{sort_by}};
		my @ret = &$method ($self, $q);
		return wantarray ? @ret : \@ret;
	}

	sub kill_processes {
		my ($self, $signal, @ps) = @_;

		my $ps = join (' ', grep { $_ != $$ } @ps);
		`kill $ps`;
		return 1;
	}

	sub kill_execute {
		my ($self, ) = @_;
		if (exists ($$self{post}{submit}) && exists ($$self{post}{pid})) {
			my @pid		= split (/\x{0}/, $$self{post}{pid});
			$self->kill_processes ($$self{post}{signal}, @pid);
			sleep (1); # bez tego ps w get_process_list () zwraca jeszcze stary stan procesów, przed killem
			return 1;
		}
		return 0;
	}

	sub _render__table_headers {
		my ($self, $root) = @_;

		my (@ret, $link, $fields, $sort, $field, );

		$fields = $$self{fields};
		foreach $field (sort { $$fields{$a} <=> $$fields{$b} } keys %$fields) {
			$sort = 'asc';
			$sort = 'desc' if ($field eq $$self{request}{sort_by} && $$self{request}{'sort'} eq 'asc');

			$link = sprintf ('<a href="%s?sort_by=%s&amp;sort=%s">%s</a>',
				$root,
				$field,
				$sort,
				$field
			);

			push (@ret, sprintf ('<th>%s</th>', $link));
		}

		return join ("\n", @ret);
	}

	sub _render__select_signals {
		my ($self) = @_;

		my @options = map {
			sprintf ('<option value="%s" %s>%s</option>',
				$signals{$_},
				(exists ($$self{request}{signal}) && $$self{request}{signal} == $signals{$_} ? 'selected="selected"' : ''),
				$_
			)
		} sort keys %signals;
		return join ("\n", @options);
	}

	sub _render__table_body {
		my ($self, $data) = @_;

		my ($fields, @ret, $line, $column, $class, );
		$column = $$self{fields}{PID};
		foreach $fields (@$data) {
			$class = !$class;
			$line = "<tr>\n"
				. sprintf (qq{<td class="%s"><input type="checkbox" name="pid" value="%s" /></td>\n}, ($class ? 'r1' : 'r2'), $$fields[$column])
				. join ("\n", map { sprintf ('<td class="%s">%s</td>', ($class ? 'r1' : 'r2'), $_) } @$fields)
				. "\n</tr>";

			push (@ret, $line);
		}
		return join ("\n", @ret);
	}

	sub render {
		my ($self, $data) = @_;

		my $arefresh = int ($$self{request}{auto_refresh});
		my %data = (
			ROOT				=> $$self{root},
			TABLE_HEADERS		=> $self->_render__table_headers ($$self{root}),
			COLUMNS_QUANT		=> scalar (keys %{$$self{fields}}) + 1,
			SELECT_SIGNALS		=> $self->_render__select_signals (),
			GET_SORT			=> $$self{request}{'sort'},
			GET_SORT_BY			=> $$self{request}{sort_by},
			TABLE_BODY			=> $self->_render__table_body ($data),
			PS_OPTIONS			=> $$self{request}{ps_options},
			AUTO_REFRESH		=> $arefresh,
		);

		my $ret = $template;
		foreach (keys %data) {
			$ret =~ s/\{$_\}/$data{$_}/g;
		}
		return $ret;
	}

	sub display {
		my ($self, $q) = @_;

		$$q{ps_options} ||= $$self{request}{ps_options};
		$$q{'sort'}		||= $$self{request}{'sort'};
		$$q{sort_by}	||= $$self{request}{sort_by};

		my $ps = $self->get_process_list ($$q{ps_options});
		$ps = $self->sort_processes_list ({
			ps		=> $$ps[1],
			'sort'	=> $$q{'sort'},
			sort_by	=> $$q{sort_by},
		});

		my $ret = $self->render ($ps);
		return $ret if ($$q{'return'});

		print $ret;
		return 1;
	}

}

package main;
sub main {
	print 'Content-type: text/html;charset=UTF-8', "\n\n";
	my $K = new Killer;
	$K->kill_execute ();
	$K->display ();
}
main ();

# vim: ft=perl
