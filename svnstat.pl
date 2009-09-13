#!/usr/bin/env perl
# $Id: killer.pl 51 2009-01-28 08:40:40Z urzenia $
# Program: svnstat.pl - subversion repo statistics
# Version: 1.1.1
# Author: Marcin ``MySZ`` Sztolcman <marcin@urzenia.net>
# Copyright: (r) 2009
# Date: 2009-09-10
# License: GPL v.2

use feature ':5.10';

use strict;
use warnings;

use Data::Dumper;
use POSIX;
use List::Util qw/min max first sum/;
use Getopt::Std qw/getopts/;
use Time::Local qw/timelocal/;

our $VERSION = '1.1.1';
$Getopt::Std::STANDARD_HELP_VERSION = 1;

sub HELP_MESSAGE {
    $0 =~ /([^\/\\]+)$/;
    print {$_[0]}
        $1 .
        " [-a path/to/nick_aliases] [-s sort_column] [-f YYYY-MM[-DD]] [-l YYYY-MM[-DD]] [-m YYYY-MM] file\n" .
        "-a - nicknames aliases file. Format: nick = map_to_nick\n" .
        "-s - sort_column: user rev_quant date_start date_end rev_start rev_end lines lines_avg\n" .
        "-f - start date. If day is ommited, get first day of month (01)\n" .
        "-l - end date. If day is ommited, get last day of month (28, 29, 30 or 31)\n" .
        "-m - set -f and -l to given date\n" .
        "file - file with svn logs history\n"
    ;

    exit;
}

sub VERSION_MESSAGE {
    my ($fh, $line, );
    if (open ($fh, '<', $0)) {
        while (defined ($line = <$fh>)) {
            last if (!$line);
            next if ($line && $line !~ /^#\s*(\w.*)$/);

            print {$_[0]} $1, "\n";
        }
        print {$_[0]} "\n";
        close ($fh);
    }
}

sub date2ts ($) {
    my ($date, ) = @_;

    state $rxp_date = qr/(\d{4})-(\d\d)-(\d\d) (\d\d?):(\d\d?):(\d\d?)(?: ([-+])(\d{4}))?/;

    my (@date, $ret, );
    @date = $date =~ $rxp_date;
    return $date if (!scalar (@date));

    return mktime (int ($6 || 0), int ($5 || 0), int ($4 || 0), $3, $2-1, $1-1900);
}

sub my_cmp ($$) {
    my ($q1, $q2, ) = @_;
    if ($q1 =~ /^-?\d+(?:\.\d+)?$/ && $q2 =~ /^-?\d+(?:\.\d+)?$/) {
        return $q1 <=> $q2;
    }
    return $q1 cmp $q2;
}

my (%opts, %aliases, $line, $fh, %sort_columns, $sort_reverse, );
if (!getopts ('a:s:f:l:m:', \%opts, )) {
    exit (1);
}

if (scalar (@ARGV) < 1 || !-f $ARGV[0]) {
    print STDERR "Give me some file!\n";
    exit (2);
}

%sort_columns = (
    user        => 0,
    rev_quant   => 1,
    date_start  => 2,
    date_end    => 3,
    rev_start   => 4,
    rev_end     => 5,
    lines       => 6,
    lines_avg   => 7,
);

if (!$opts{s}) {
    $opts{s} = 'user';
}
elsif (
    !exists ($sort_columns{$opts{s}}) &&
    ($sort_reverse = $opts{s} =~ s/^!//) &&
    !exists ($sort_columns{$opts{s}})
) {
    print STDERR 'Known sort columns: ', join (', ', sort keys (%sort_columns)), " - your input: $opts{s}\n";
    exit (3);
}

if ($opts{m} && $opts{m} =~ /^\d{4}-\d\d$/) {
    $opts{f} = $opts{l} = $opts{m};
}

if ($opts{f} && $opts{f} =~ /^\d{4}-\d\d(-\d\d)?$/) {
    $opts{f} .= '-01'
        if (!$1);
    $opts{f} = date2ts ($opts{f} . ' 00:00:00');
}

delete ($opts{f})
    if (!$opts{f} || $opts{f} <= 0);

if ($opts{l} && $opts{l} =~ /^(\d{4})-(\d\d)(-\d\d)?$/) {
    if (!$3) {
        my $day = 31;
        while (1) {
            eval {
                timelocal (0, 0, 0, $day, $2-1, $1-1900);
            };
            last if (!$@);
            if ($day < 28) {
                print STDERR 'Error: cannot find last day of given date.';
                exit (2);
            }

            --$day;
        }
        $opts{l} .= "-$day";
    }

    $opts{l} = date2ts ($opts{l} . ' 23:59:59');
}

delete ($opts{l})
    if (!$opts{l} || $opts{l} <= 0);

if ($opts{a} && -f $opts{a}) {
    if (!open ($fh, '<', $opts{a})) {
        print STDERR 'Can\'t open aliases file: ' . $!;
        exit (4);
    }

    while (defined ($line = <$fh>)) {
        chomp ($line);
        next if ($line !~ /^\s*(\S+)\s*=\s*(\S+)/);
        $aliases{$1} = $2;
    }

    close ($fh);
}

if (!open ($fh, '<', $ARGV[0])) {
    print STDERR 'Canot open log file: ' . $!;
    exit (5);
}


my ($rxp_statline, %log_data, $rev, $user, $date, $date_ts, $lines, );
$rxp_statline = qr/
    ^
    \s*r
    (\d+)           # rewizja
    \s*\|\s*
    (\S+)           # nickname
    \s*\|\s*
    ([\d :+-]+)     # data
    \s+[^|]+\|\s*
    (\d+)           # ilosc linii loga
    \s*/x;

while (defined ($line = <$fh>)) {
    chomp ($line);
    next if ($line !~ $rxp_statline);
    ($rev, $user, $date, $lines, ) = ($1, $2, $3, $4, );

    $date_ts = date2ts ($date);
    next if (
        ($opts{f} && $opts{f} >= $date_ts)
        ||
        ($opts{l} && $opts{l} <= $date_ts)
    );

    $user = $aliases{$user}
        if (exists ($aliases{$user}));

    $log_data{$user} //= {
        rev     => [],
        user    => $user,
        date    => [],
        date_ts => [],
        lines   => [],
    };

    push (@{$log_data{$user}{rev}}, $rev);
    push (@{$log_data{$user}{date}}, $date);
    push (@{$log_data{$user}{date_ts}}, $date_ts);
    push (@{$log_data{$user}{lines}}, $lines);
}

my ($fmt_date, $date_min, $date_max, $revs, $data, %summary, );
$fmt_date = '%Y-%m-%d';
foreach $data (values (%log_data)) {
    $date_min   = min (@{$$data{date_ts}});
    $date_max   = max (@{$$data{date_ts}});
    $lines      = sum (@{$$data{lines}});
    $revs       = scalar (@{$$data{rev}});

    $data       = [
        $$data{user},
        $revs,
        strftime ($fmt_date, localtime ($date_min)),
        strftime ($fmt_date, localtime ($date_max)),
        min (@{$$data{rev}}),
        max (@{$$data{rev}}),
        $lines,
        ($lines / $revs),
    ];

    $summary{quant} += $revs;
    $summary{lines} += $lines;
}

print " User       Quant Date start - Date end   Fst rev - Lst rev Descr lines    \n";
print "---------------------------------------------------------------------------\n";
my @log_data = sort {
    my_cmp ($$a[$sort_columns{$opts{s}}], $$b[$sort_columns{$opts{s}}]) ||
    $$a[0] cmp $$b[0]
} values (%log_data);

@log_data = reverse (@log_data)
    if ($sort_reverse);

foreach $data (@log_data) {
    printf " %-10s % 5d %s - %s (% 6d - % 6d) % 6d (%.3f)\n", @$data;
}

print "---------------------------------------------------------------------------\n";
printf "Summary: %d revs, %d lines of comments (%.5f lines per commit)\n", $summary{quant}, $summary{lines}, $summary{lines} / $summary{quant};

