#!/usr/bin/env perl5.10.0
# $Id$
# Program: r2j.pl - extracting jpegs embedded in raws
# Version: 0.2
# Author: Marcin ``MySZ`` Sztolcman <marcin@urzenia.net>
# Copyright: (r) 2009
# Date: 2009-09-13
# License: GPL v.2

use feature ':5.10';

use strict;
use warnings;

use Getopt::Std qw/getopts/;

use Image::ExifTool;

our $VERSION = '0.2';
$Getopt::Std::STANDARD_HELP_VERSION = 1;

sub HELP_MESSAGE {
    $0 =~ /([^\/\\]+)$/;
    print {$_[0]}
        $1 .
        " [-t extract|preview] [-d dest/dir] [-e file_ext] [-p file_prefix] [-s file_suffix] [-f] [-n] file1 file 2 dir1 file3\n" .
        "-t - extract embedded image, or get preview (defaults to 'extract')\n" .
        "-d - destination directory (defaults to source file directory)\n" .
        "-e - destination file extension (defaults to jpg)\n" .
        "-p - destination file prefix (for example: -p 'file_' a.nef -> file_a.jpg)\n" .
        "-s - destination file suffix (for example: -s '_new' a.nef -> a_new.jpg)\n" .
        "-f - force write file, even if already exists\n" .
        "-n - don't copy exif from source file\n"
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

sub path_join {
    my (@ret, ) = @_;
    return join ('/', map {s/[\/\\]+/\//; $_} @ret);
}

sub main {
    my (%opts, %types, );
    if (!getopts ('t:d:e:p:s:fnc:', \%opts, )) {
        exit (1);
    }

    ## dostepne typy wyciaganych obrazkow
    %types = (
        extract => 'JpgFromRaw',
        preview => 'PreviewImage',
    );

    ## domyslnie extract
    $opts{t} //= 'extract';
    if (!$types{$opts{t}}) {
        print STDERR "Incorrect type: $opts{t}.\n";
        exit (1);
    }

    ## sciezka docelowa
    if ($opts{d} && !-d $opts{d}) {
        print STDERR "Incorrect destination directory: $opts{d}.\n";
        exit (2);
    }

    ## czy mozemy tam zapisac
    if ($opts{d} && !-x _) {
        print STDERR "Cannot write in destination directory: $opts{d}.\n";
        exit (3);
    }

    ## wyszukujemy pliki w podanych argumentach
    my ($item, @files, );
    foreach $item (@ARGV) {
        if (-f $item) {
            push (@files, $item);
        }
        elsif (-d _) {
            push (@files, grep { -f $_ } glob ($item . '/*'));
        }
        else {
            next;
        }
    }

    ## czy mamy co zapisywac?
    if (!scalar (@files)) {
        print STDERR "Give me something to process, please...\n";
        exit (4);
    }

    if (!defined ($opts{c}) || $opts{c} !~ /^\d+$/) {
        $opts{c} = 30;
    }

    ## OK, do dziela
    my ($et, $info, $fh, $path, $counter, $counter_max, );
    $et = Image::ExifTool->new ();
    $et->Options (Binary => 1, Replace => 1, );

    $counter_max = scalar (@files);

    printf "Found: %d files\n", $counter_max;
    foreach $item (@files) {
        ++$counter;

        $info = $et->ImageInfo ($item);
        if (!$info) {
            print STDERR "Cannot read file: $item.\n";
            next;
        }
        if (!$$info{$types{$opts{t}}} || ref ($$info{$types{$opts{t}}}) ne 'SCALAR') {
            print STDERR "Cannot find embedded image in $item.\n";
            next;
        }

        printf "  Processing: %d, left: %d\n", $counter, $counter_max - $counter
            if ($opts{c} > 0 && !($counter % $opts{c}));

        ## pobieramy nazwe pliku
        $item =~ /(.*?)([^\/\\]+)$/;
        ## sciezka docelowa: katalog docelowy lub zrodlowy, prefix, nazwa pliku
        $path = path_join (($opts{d} // $1 || '.'), ($opts{p} // '') . $2);
        ## wycinamy rozszerzenie docelowego pliku (pobrane z pliku zrodlowego)
        if ($path !~ s/\.tar\.(?:bz2?|gz)$//i) {
            $path =~ s/\.[^.]+$//;
        }
        ## doklejamy suffix
        $path .= $opts{s}
            if ($opts{s});
        ## doklejamy podane przez usera, lub standardowo jpg
        $path .= '.' . ($opts{e} // 'jpg');

        ## jesli nie kazano nam nadpisywac pliku, to wyrzucamy blad jesli takowy juz istnieje
        if (!$opts{f} && -f $path) {
            print STDERR "File $path exists.\n";
            next;
        }

        ## proba otworzenia do zapisu
        if (!open ($fh, '>', $path)) {
            print STDERR "Cannot open to write \"$path\": $!\n";
            next;
        }

        ## zapis
        print {$fh} ${delete ($$info{$types{$opts{t}}})};
        close ($fh);

        if (!$opts{n}) {
            $et->ImageInfo ($path);
            $et->SetNewValuesFromFile ($item);
            $et->WriteInfo ($path);
        }

        print "$path writed.\n";
    }
}

main ();

