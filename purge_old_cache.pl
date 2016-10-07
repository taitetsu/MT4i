# Copyright (C) 太鉄 All rights reserved.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

use File::Find;
use Data::Dumper;
use FindBin qw($Bin);

# 外部ファイルの読み込み
eval {require $Bin.'/lib/mt4i/Config.pl'; 1} or die 'File not found: '.$Bin.'/lib/mt4i/Config.pl';

# 設定読み込み
our %cfg = Config::Read($Bin . '/mt4icfg.cgi');

unshift @INC, $cfg{MT_DIR} . 'lib';
unshift @INC, $cfg{MT_DIR} . 'extlib';

my $dir = $cfg{MT_DIR} . 'mt4i/cache/page';

# 設定の有無確認
die 'error: The parameter "PurgeCacheLimit" is not set.' if (!$cfg{PurgeCacheLimit});
die 'error: The parameter "PurgeCacheMailFrom" is not set.' if (!$cfg{PurgeCacheMailFrom});
die 'error: The parameter "PurgeCacheMailTo" is not set.' if (!$cfg{PurgeCacheMailTo});

my @files;
find(sub { push @files, $File::Find::name if -f }, $dir);

# 一日前の日付計算
$ENV{'TZ'} = "JST-9";   # タイムゾーンの設定
my $yesterdaytime = time - 1*$cfg{PurgeCacheLimit}*60*60;

my $body;

for my $file (@files) {
    my $updatetime = (stat $file)[9];
    if ($updatetime < $yesterdaytime) {
        unlink $file or die 'can\'t unlink '.$file;
        my ($sec, $min, $hour, $mday, $mon, $year, $wday, $yday, $isdst) = localtime($updatetime);
        my $formatdt = sprintf("%04d\/%02d\/%02d %02d:%02d:%02d", $year + 1900, $mon +1, $mday, $hour, $min, $sec);
        $file =~ s/$cfg{MT_DIR}//g;
        $body .= $formatdt.' '.$file."\n";
    }
}

# Mail Sending.
chdir $cfg{MT_DIR};
eval { require MT; };
die $@ if ($@);
my $app;
if (-e $cfg{MT_DIR} . 'mt-config.cgi') {
    $app = MT->new( Config => $cfg{MT_DIR} . 'mt-config.cgi', Directory => $cfg{MT_DIR} )
        or die MT->errstr;
} else {
    $app = MT->new( Config => $cfg{MT_DIR} . 'mt.cfg', Directory => $cfg{MT_DIR} )
        or die MT->errstr;
}
my %head = ( From => $cfg{PurgeCacheMailFrom},
             To => $cfg{PurgeCacheMailTo},
             Subject => "Automatic purge cache for MT4i");
my $charset = $app->config('MailEncoding') || $app->config('PublishCharset');
$head{'Content-Type'} = qq(text/plain; charset="$charset");
if (!$body) {
    $body = 'The target cache for the purge did not exist today.';
}
require MT::Mail;
MT::Mail->send(\%head, $body);
