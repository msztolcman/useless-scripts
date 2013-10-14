#!/usr/bin/env perl

use strict;
use warnings FATAL => 'all';
use 5.010;

# Version: 0.1
# Author: Marcin ``MySZ`` Sztolcman <marcin@urzenia.net>
# Copyright: (r) 2012
# Program: commands.pl - simple shell history stats
# Date: 2012-07-13
# License: GPL v.2

use File::Basename;
use Getopt::Std;

use Data::Dumper;
$Data::Dumper::Sortkeys = 1;
$Data::Dumper::Terse = 1;
$Data::Dumper::Indent = 1;
$Data::Dumper::Quotekeys = 1;
sub cgi_dump { say &Dumper; };

my (%CMD_PARSERS, %FILE_PARSERS, %SHELL_FILE, );

%CMD_PARSERS = (
    git => \&_cmd_parser_git,
    svn => \&_cmd_parser_git,
    sudo => \&_cmd_parser_git,
);

%FILE_PARSERS = (
    zsh     => {
        parser      => \&_file_parser__default,
        prepare     => \&_file_parser_zsh__prepare,
        fetch_line  => \&_file_parser_zsh__fetch_line,
    },
    bash    => {
        parser      => \&_file_parser__default,
    },
);

%SHELL_FILE = (
    zsh     => $ENV{HOME} . '/.zsh_history',
    bash    => $ENV{HOME} . '/.bash_history',
);

sub _file_parser_zsh__prepare {
    my ($content, ) = @_;

    $content =~ s{\\\n(?!:)}{}g;

    return $content;
}

sub _file_parser_zsh__fetch_line {
    my ($line, ) = @_;

    $line =~ /^:\s*\d+:\d+;(.*)/m;

    return $1;
}

sub _file_parser__default {
    my ($f, $callbacks, )  = @_;

    my ($content, $fh, );
    open ($fh, '<', $f) or die (qq/Can't open file "$f": $!/);
    sysread ($fh, $content, -s $f) or die (qq/Can't read file "$f": $!/);
    close ($fh);

    $content = &{$$callbacks{prepare}} ($content)
        if (defined ($$callbacks{prepare}));

    $content = [ split (/\n/, $content), ];

    my ($cmd, $line, %ret, $subcmd, );
    foreach $line (@$content) {
        next if (!length ($line));

        $line = &{$$callbacks{fetch_line}} ($line)
            if (defined ($$callbacks{fetch_line}));
        next if (!length ($line));

        $cmd = [ split (/\s+/, $line, 2), ];

        $ret{$$cmd[0]} //= { quant => 0, sub => {}, };
        ++$ret{$$cmd[0]}{quant};

        if (exists ($CMD_PARSERS{$$cmd[0]})) {
            $subcmd = &{$CMD_PARSERS{$$cmd[0]}} ($cmd);
            next if (!defined ($subcmd));

            $ret{$$cmd[0]}{sub}{$subcmd} //= 0;
            ++$ret{$$cmd[0]}{sub}{$subcmd};
        }
    }

    return wantarray ? %ret : \%ret;
}

sub _cmd_parser_git {
    my ($cmd, ) = @_;

    return if (scalar (@$cmd) < 2);

    my ($subcmd, ) = split (/\s+/, $$cmd[1], 2);

    return $$cmd[0] if (!length ($$cmd[1]));
    return "$$cmd[0] $subcmd";
}

sub usage {
    say basename ($0) . ' - simple shell history stats
-s SHELL [opt] - shell type to parse. If not defined use $SHELL environment variable
-f FILE [opt] - history file (defaults to ~/.zsh_history for ZSH, ~/.bash_history for BASH)
-c QUANTITY [opt] - max QUANTITY results (defaults to 10)
-b QUANTITY [opt] - max QUANTITY results for every subcommand (defaults to -c)'
}

sub main {
    my (%opts, );

    getopt ('s:f:c:b:h', \%opts);

    if (exists ($opts{h})) {
        usage ();
        exit;
    }

    $opts{c} //= 10;
    $opts{b} //= $opts{c};
    $opts{s} //= $ENV{SHELL};
    $opts{s} = basename ($opts{s});
    $opts{f} //= $SHELL_FILE{$opts{s}};

    my (%quants, @sorted, );
    %quants = &{$FILE_PARSERS{$opts{s}}{parser}} ($opts{f}, $FILE_PARSERS{$opts{s}});
    @sorted = map {
        [$quants{$_}, $_, ]
    } sort {
        $quants{$b}{quant}<=> $quants{$a}{quant}
    } keys (%quants);

    splice (@sorted, $opts{c})
        if ($opts{c} < scalar (@sorted));

    my ($cmd, $fmt_cmd, $fmt_subcmd, $subcmd, @sub_sorted, );
    $fmt_cmd = '% ' . (length ($sorted[0][0]{quant}) + 1) . "d: %s\n";
    foreach $cmd (@sorted) {
        printf $fmt_cmd, $$cmd[0]{quant}, $$cmd[1];

        if (%{$$cmd[0]{sub}}) {
            @sub_sorted = map {
                [$$cmd[0]{sub}{$_}, $_, ]
            } sort {
                $$cmd[0]{sub}{$b} <=> $$cmd[0]{sub}{$a}
            } keys (%{$$cmd[0]{sub}});

            splice (@sub_sorted, $opts{b})
                if ($opts{b} < scalar (@sub_sorted));

            $fmt_subcmd = "\t% " . (length ($sub_sorted[0][0]) + 1) . "d: %s\n";
            foreach $subcmd (@sub_sorted) {
                printf $fmt_subcmd, $$subcmd[0], $$subcmd[1];
            }
        }
    }
}

main ();
