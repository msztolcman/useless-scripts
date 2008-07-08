#!/usr/bin/env perl

# $Id$
my $__version__   = 'version 0.2'
my $__author__    = 'Marcin ``MySZ`` Sztolcman <marcin@urzenia.net>'
my $__copyright__ = '(r) 2008'
my $__program__   = 'sat.pl - simple static analysis tool'
my $__date__      = '2008-07-08'
my $__license__   = 'GPL v.2'

use strict;
use warnings;

use Data::Dumper;

# funkcje pomocnicze
sub SEEK_SET { 0 }
sub SEEK_CUR { 1 }
sub SEEK_END { 2 }

# funkcje wyjścia
sub display_html {
	my ($subs) = @_;

	my ($sub, $data, $fname, );

	foreach $sub (sort keys (%$subs)) {
		printf ("Plik: %s<br />\nFunkcja: %s<br />\n", $$subs{$sub}[0], $sub);

		if (%{$$subs{$sub}[1]}) {
			print "Wywoływana w:<br />\n";
			foreach $fname (sort keys %{$$subs{$sub}[1]}) {
				foreach $data (sort keys %{$$subs{$sub}[1]{$fname}}) {
					printf ("&nbsp;&nbsp;&nbsp;&nbsp;%s::%s - linie: %s<br />\n", $fname, $data, join (', ', @{$$subs{$sub}[1]{$fname}{$data}}));
				}
			}
		}

		print "<br />\n";
	}

	return;
}

sub display_console {
	my ($subs) = @_;

	my ($sub, $data, $fname, );

	foreach $sub (sort keys (%$subs)) {
		printf ("Plik: %s\nFunkcja: %s\n", $$subs{$sub}[0], $sub);

		if (%{$$subs{$sub}[1]}) {
			print "Wywoływana w:\n";
			foreach $fname (sort keys %{$$subs{$sub}[1]}) {
				foreach $data (sort keys %{$$subs{$sub}[1]{$fname}}) {
					printf ("\t%s::%s - linie: %s\n", $fname, $data, join (', ', @{$$subs{$sub}[1]{$fname}{$data}}));
				}
			}
		}

		print "\n";
	}

	return;
}

sub display_raw {
	my ($subs, ) = @_;

	print Dumper ($subs);
	return;
}


# parsowanie plików
sub parse_files {

	my (%fh, $fh, $line, $subs, $sub, $curr_sub, $lineno, $fname, $lsub, );
	foreach $fname (@_) {
		open ($fh, '<', $fname) or die (sprintf ('Nie powiodło się otworzenie pliku "%s".', $fname));

		# wyszukujemy wszystkie zdefiniowane funkcje
		while ($line = <$fh>) {
			next if ($line !~ /^\s*sub\s+(\w+)\s*\{/);
			next if ($1 eq 'main');
			$$subs{$1} = [$fname, {}];
		}

		# wracamy na początek pliku
		seek ($fh, 0, SEEK_SET);

		$fh{$fname} = $fh;
		undef ($fh);
	}

	foreach $fname (sort keys %fh) {
		$fh = $fh{$fname};

		# wyszukujemy wystapienia wszystkich znalezionych funkcji
		$curr_sub = '_';
		while ($line = <$fh>) {
			++$lineno;
			next if ($line =~ /\s*#/);

			# sprawdzamy i zapamiętujemy curr_sub
			if ($line =~ /^\s*sub\s+(\w+)\s*\{/) {
				$curr_sub = $1;
				next;
			}

			# szukamy w bieżącej linii wystąpienia dowolnej z naszych metod
			foreach $sub (keys %$subs) {
				if ($line =~ /[^\$\%\@\w]$sub\b/) {
					push (@{ $$subs{$sub}[1]{$fname}{$curr_sub} ||= [] }, $lineno);
				}
			}
		}

		# zamykamy plika
		close ($fh);

		# zerujemy licznik linii
		$lineno = 0;
	}

	return wantarray ? %$subs : $subs;
}

# parsowanie argumentów
my ($display, @files, $ret, );
if (@ARGV >= 3 && $ARGV[0] =~ /^(?:-f|--format)$/) {
	$display = $ARGV[1];
	@files = @ARGV[2 .. $#ARGV];
}
else {
	$display = 'console';
	@files = @ARGV;
}

if (!@files) {
	print STDERR "Nie podałeś plików do parsowania.\n";
	exit 1;
}

if (!defined (&{'display_'.$display})) {
	print STDERR "Nieznany format wyjścia.\n";
	exit 2;
}
$display = \&{'display_'.$display};

# wyświetlenie wyników
eval {
	$ret = parse_files (@files);
};
if ($@) {
	print STDERR 'Wystapił błąd podczas parsowania pliku: '. $@;
	exit 3;
}

&$display ($ret);

