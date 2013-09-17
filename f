#!/usr/bin/env perl

use 5.010;

sub DATA_SIZE() { 80 }

my ($fh);
if (scalar (@ARGV) < 1 || $ARGV[0] !~ /^\d+(\.\d+)?[kmgb]?$/) {
    die("Missing or incorrect file size.\n");
}
elsif (scalar(@ARGV) < 2 || !$ARGV[1]) {
    die("Missing file name.\n");
}
elsif (-f $ARGV[1]) {
    die("File already exists.\n");
}
elsif ($ARGV[1] eq '-') {
    $fh = *STDOUT;
}
elsif (!open($fh, '>', $ARGV[1])) {
    die("Cannot create file: $!\n");
}

my ($size, $data);
$size = (
    $ARGV[0] !~ s/([bkmg])$// || $1 eq 'm'  ?   $ARGV[0] * 1024 * 1024          :
    $1 eq 'k'                               ?   $ARGV[0] * 1024                 :
    $1 eq 'g'                               ?   $ARGV[0] * 1024 * 1024 * 1024   :
                                                $ARGV[0]
);

$data = 'abcdefghij' x (DATA_SIZE / 10);
$data = substr($data, 0, DATA_SIZE - 1);
while ($size > 0) {
    if ($size >= DATA_SIZE) {
        print $fh $data, "\n";
    }
    else {
        print $fh substr('abcdefghij' x $size, 0, $size);
    }
    $size -= DATA_SIZE;
}

close($fh)
    if ($ARGV[1] ne '-');

