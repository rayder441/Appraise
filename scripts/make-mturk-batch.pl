#!/usr/bin/perl

use strict;
use warnings;

if (@ARGV != 5) {
  print "Usage: make-mturk-batch.sh BATCHNO SOURCE TARGET DATADIR FILEPREFIX\n";
  exit;
}
my ($batchno,$source,$target,$plaindir,$fileprefix) = @ARGV;

my $pair="$source-$target";
mkdir($pair) unless -d $pair;

my $outfile = "$pair/$pair-batch$batchno.txt";
die "Cowardly refusing to create batch $outfile (already exists)" if -e $outfile;

my %langs = (
	en => 'eng',
	ru => 'rus',
	cs => 'cze',
	fr => 'fre',
	de => 'deu',
	es => 'spa' );

my $cmd = "python $ENV{APPRAISE}/scripts/wmt_ranking_task.py $plaindir/sources/$fileprefix-src.$source $plaindir/references/$fileprefix-ref.$target $plaindir/systems/$fileprefix.$pair.* -source $langs{$source} -target $langs{$target} -no-sequential -redundancy 0 -maxlen 200 > $outfile";

#print "$cmd\n";
system($cmd);
