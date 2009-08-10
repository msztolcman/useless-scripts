#!/usr/bin/env perl5.10
# $Id: killer.pl 51 2009-01-28 08:40:40Z urzenia $

# Version: 1.0.0
# Author: Marcin ``MySZ`` Sztolcman <marcin@urzenia.net>
# Copyright: (r) 2009
# Program: svnstat.pl - subversion repo statistics
# Date: 2009-08-10
# License: GPL v.2

use feature ':5.10';

use strict;
use warnings;
use Data::Dumper;
use POSIX;
use List::Util qw/min max first sum/;
use Getopt::Std qw/getopts/;

sub date2ts ($) {
    my ($date, ) = @_;

    my (@date, $ret, );
    @date = $date =~ /(\d{4})-(\d\d)-(\d\d) (\d\d):(\d\d):(\d\d) ([-+])(\d{4})/;
    return $date if (!scalar (@date));

    return mktime ($6, $5, $4, $3, $2-1, $1-1900);
}

sub my_cmp ($$) {
    my ($q1, $q2, ) = @_;
    if ($q1 =~ /^-?\d+(?:\.\d+)?$/ && $q2 =~ /^-?\d+(?:\.\d+)?$/) {
        return $q1 <=> $q2;
    }
    return $q1 cmp $q2;
}

my (%opts, %aliases, $line, $fh, %sort_columns, $sort_reverse, );
if (!getopts ('a:s:', \%opts, )) {
    exit (1);
}

if (scalar (@ARGV) < 1 || !-f $ARGV[0]) {
    print STDERR 'Give me some file!';
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

if ($opts{a} && -f $opts{a}) {
    if (!open ($fh, '<', $opts{a})) {
        print STDERR 'Canot open aliases file: ' . $!;
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


my ($rxp_statline, %log_data, $rev, $user, $date, $lines, );
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
    push (@{$log_data{$user}{date_ts}}, date2ts ($date));
    push (@{$log_data{$user}{lines}}, $lines);
}

my ($fmt_date, $date_min, $date_max, $revs, $data, );
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
}

print " User       Quant Date start - Date end   Fst rev - Lst rev Descr lines   \n";
print "--------------------------------------------------------------------------\n";
my @log_data = sort {
    my_cmp ($$a[$sort_columns{$opts{s}}], $$b[$sort_columns{$opts{s}}]) ||
    $$a[0] cmp $$b[0]
} values (%log_data);
@log_data = reverse (@log_data)
    if ($sort_reverse);
foreach $data (@log_data) {
    printf " %-10s % 5d %s - %s (% 6d - % 6d) % 6d (%.3f)\n", @$data;
}

