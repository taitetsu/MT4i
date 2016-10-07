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
package MT4i::Log;

##################################################
# Sub WriteLog
##################################################
sub writelog {
    my ($logstr) = @_;
    $logstr = getlogheader().' '.$logstr."\n" or die "$!";
    my $log_file = $::Bin.'/mt4i.log';
    if (!-e $log_file) {
        open(OUT,"> $log_file") or die "Can't open ".$log_file." : $!";
        flock(OUT, 2) or die "Can't flock  : $!";
        seek(OUT, 0, 2) or die "Can't seek  : $!";
        print OUT $logstr or die "Can't print : $!";
        close(OUT);
    } else {
        open(IN,"< $log_file") or die "Can't open ".$log_file." : $!";
        flock(IN, 1) or die "Can't flock  : $!";
        my @logs = <IN>;
        if (@logs > 1000) {
            shift @logs;
        }
        push @logs, $logstr;
        close(IN);
        open(OUT, "+< $log_file"); # 読み書きモードで開く
        flock(OUT, 2);             # ロック確認。ロック
        seek(OUT, 0, 0);           # ファイルポインタを先頭にセット
        for my $log (@logs) {
            print OUT $log;        # 書き込む
        }
        truncate(OUT, tell(OUT));  # ファイルサイズを書き込んだサイズにする
        close(OUT);                # closeすれば自動でロック解除        
    }
}

##################################################
# Sub GetLogHeader
##################################################
sub getlogheader {
    $ENV{'TZ'} = "JST-9";
    my ($sec, $min, $hour, $mday, $mon, $year) = localtime(time);
    $mon = ('01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12')[$mon];
    $year += 1900;
    if ($sec < 10) {$sec = "0$sec";}
    if ($min < 10) {$min = "0$min";}
    if ($hour < 10) {$hour = "0$hour";}
    if ($mday < 10) {$mday = "0$mday";}
    my $header_str = "[$year/$mon/$mday $hour:$min:$sec]";
    return $header_str;
}

1;
