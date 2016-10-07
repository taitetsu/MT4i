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
package Config;

# 設定読み込み
sub Read {
    my ($cfg_file) = @_;
    
    # 設定ファイルオープン
    open(IN,"< $cfg_file") or return undef;

    # 設定格納用連想配列（ハッシュ）変数宣言
    my %cfg = ();
    
    # 読み込み
    while (<IN>){
        my $tmp = $_;
        
        # 改行コードの削除
        chomp($tmp);
        
        if ($tmp !~ /^#/) {
            my $key;
            my $val;
            ($key, $val) = split(/<>/,$tmp);
            if ($key && ($val || $val eq '0')) {
                $cfg{$key} = $val;
            }
        }
    }

    # 設定ファイルクローズ
    close(IN);
    
    return %cfg;
}

1;
