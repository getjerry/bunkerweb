#!/usr/bin/env perl

use strict;
use warnings;
use autodie qw( :all );

use FindBin qw( $Bin );

use File::Path qw( mkpath );
use File::Slurp qw( edit_file read_file );
use File::Which qw( which );

sub main {
    my $target = shift || "$Bin/..";

    my @translators = qw ( lowdown pandoc );
    my $translator;
    foreach my $p (@translators) {
        if ( defined which($p) ) {
            $translator = $p;
            last;
        }
    }
    unless ( defined $translator ) {
        die "\n  You must install one of "
            . join( ', ', @translators )
            . " in order to generate the man pages.\n\n";
    }

    _make_man( $translator, $target, 'libmaxminddb', 3 );
    _make_lib_man_links($target);

    _make_man( $translator, $target, 'mmdblookup', 1 );
}

sub _make_man {
    my $translator = shift;
    my $target     = shift;
    my $name       = shift;
    my $section    = shift;

    my $input   = "$Bin/../doc/$name.md";
    my $man_dir = "$target/man/man$section";
    mkpath($man_dir);
    my $output = "$man_dir/$name.$section";

    if ( $translator eq 'pandoc' ) {
        system(
            'pandoc',
            '-s',
            '-f', 'markdown_mmd+backtick_code_blocks',
            '-t', 'man',
            '-M', "title:$name",
            '-M', "section:$section",
            $input,
            '-o', $output,
        );
        _pandoc_postprocess($output);
    }
    elsif ( $translator eq 'lowdown' ) {
        system(
            'lowdown',
            '-s',
            '--out-no-smarty',
            '-Tman',
            '-M', "title:$name",
            '-M', "section:$section",
            $input,
            '-o', $output,
        );
    }
}

sub _make_lib_man_links {
    my $target = shift;

    my $header = read_file("$Bin/../include/maxminddb.h");
    for my $proto ( $header =~ /^ *extern.+?(MMDB_\w+)\(/gsm ) {
        open my $fh, '>', "$target/man/man3/$proto.3";
        print {$fh} ".so man3/libmaxminddb.3\n";
        close $fh;
    }
}

# AFAICT there's no way to control the indentation depth for code blocks with
# Pandoc.
sub _pandoc_postprocess {
    my $file = shift;

    edit_file(
        sub {
            s/^\.IP\n\.nf/.IP "" 4\n.nf/gm;
            s/(Automatically generated by Pandoc)(.+)$/$1/m;
        },
        $file
    );
}

main(shift);
