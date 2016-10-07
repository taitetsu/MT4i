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
package MT4i::Func;

########################################
# Encryption and collation by crypt()
# referred : http://www.rfs.co.jp/sitebuilder/perl/05/01.html#crypt
########################################

# Function that receives character string ($val),
# and returns encrypted character string
sub enc_crypt {
    my ($val) = @_;

    my( $sec, $min, $hour, $day, $mon, $year, $weekday )
        = localtime( time );
    my( @token ) = ( '0'..'9', 'A'..'Z', 'a'..'z' );
    my $salt = $token[(time | $$) % scalar(@token)];
    $salt .= $token[($sec + $min*60 + $hour*60*60) % scalar(@token)];
    my $passwd2 =  crypt( $val, $salt );

    $passwd2 =~ s/\//\@2F/g;
    $passwd2 =~ s/\$/\@24/g;
    $passwd2 =~ s/\./\@2E/g;

    return $passwd2;
}

########################################
# パスワード($passwd1)と暗号化したパスワード($passwd2)を受け取り、
# 一致するかを判定する関数
########################################
sub check_crypt{
    my ($passwd1, $passwd2) = @_;

    # 空のパスワードは許さない
    return 0 if (!$passwd1 || !$passwd2);

    $passwd2 =~ s/\@2F/\//g;
    $passwd2 =~ s/\@24/\$/g;
    $passwd2 =~ s/\@2E/\./g;

    # 暗号のチェック
    return ( crypt($passwd1, $passwd2) eq $passwd2 ) ? 1 : 0 ;
}

############################################################
# calc_cache_size:携帯のキャッシュ(1画面に出力できる最大値)を求める
# 返値 携帯のキャッシュサイズ
# 参考：http://deneb.jp/Perl/mobile/
# Special Thanks：drry
############################################################
sub calc_cache_size {

     my ( $user_agent ) = @_;
     my $cache_size = 50*1024;
    if ( $user_agent =~ m|DoCoMo.*\W.*c(\d+).*(c\d+)?|i ) {
         $cache_size = $1*1024;
     } elsif ( $user_agent =~ m|DoCoMo|i ) {
         $cache_size = 5*1024;
    } elsif ( $user_agent =~ m!(?:SoftBank|Vodafone)/\d\.\d|MOT-\w980! ) {
         $cache_size = 300*1024;
    } elsif ( $user_agent =~ m!J-PHONE(?:/([45]\.\d))?! ) {
        $cache_size = ($1 ? ($1 >= 5.0 ? 200: ($1 >= 4.3 ? 30: 12)): 6)*1024;
     } elsif ( $ENV{HTTP_X_UP_DEVCAP_MAX_PDU} ) {
         $cache_size = $ENV{HTTP_X_UP_DEVCAP_MAX_PDU};
     } elsif ( $user_agent =~ m|KDDI\-| ) {
        $cache_size = 9*1024;
    } elsif ( $user_agent =~ m|UP\.Browser| ) {
        $cache_size = 7.5*1024;
    }
    return $cache_size;
}

#################################################################
# Sub Get_mt4ilink - MT4iへのリンクを取得
#
# リンク先のHTMLを取得してMT4iで閲覧するのに適したリンク先を
# 取得する。具体的には [rel|rev]="alternate" のlinkタグのうち、
# title="MT4i" あるいは media="handheld" の属性をもつタグで指
# 定されている href を返す。両方あった場合は title="MT4i" の方
# を優先する。見つからなければ空文字列を返す。
#
#################################################################
sub get_mt4ilink {
    my $url = $_[0];

    # ホスト名の置換
    $url =~ s/http:\/\///;
    my $host = substr($url, 0, index($url, "/"));
    my $path = substr($url, index($url, "/"));
    if ($host eq $cfg{Photo_Host_Original}){
        $host = $cfg{Photo_Host_Replace};
    }
    $url = 'http://'.$host.$path;

    require LWP::Simple;
    # リンク先コンテンツ取得
    my $content = LWP::Simple::get($url);
    if (!$content) {
        # 取得失敗
        return "";
    }

    # ヘッダーの取り出し
    my $pattern = "<[\s\t]*?head[\s\t]*?>(.*?)<[\s\t]*?/[\s\t]*?head[\s\t]*?>";
    my @head = ($content =~ m/$pattern/is);
    if (!$head[0]) {
        return "";
    }

    # linkタグの取り出し
    $pattern = "<[\s\t]*?link[\s\t]*?(.*?)[\s\t/]*?>";
    my @links = ($head[0] =~ m/$pattern/isg);

    my $mt4ilink = ""; # titile="MT4i"
    my $hhlink     = ""; # media="handheld"

    found : foreach my $link ( @links ) {
        my $title = "";
        my $rel = "";
        my $media = "";
        my $href = "";
        if ($link =~ /title[\s\t]*?=[\s\t]*?([^\s\t]*)/i) {
            $title = $1;
            $title =~ s/["']//g;
        }
        if ($link =~ /rel[\s\t]*?=[\s\t]*?([^\s\t]*)/i) {
            $rel = $1;
        } elsif ($link =~ /rev[\s\t]*?=[\s\t]*?([^\s\t]*)/i) {
            $rel = $1;
        }
        if ($rel) {
            $rel =~ s/["']//g;
        }
        if ($link =~ /media[\s\t]*?=[\s\t]*?([^\s\t]*)/i) {
            $media = $1;
            $media =~ s/["']//g;
        }
        if ($link =~ /href[\s\t]*?=[\s\t]*?([^\s\t]*)/i) {
            $href = $1;
            $href =~ s/["']//g;
        }
        if ((lc $rel) eq 'alternate') {
            if ((lc $title) eq 'mt4i') {
                $mt4ilink = $href;
                last found;
            } elsif ((lc $media) eq 'handheld') {
                if (!$hhlink) {
                    $hhlink = $href;
                }
            }
        }
    }

    if ($mt4ilink) {
        return $mt4ilink;
    }
    return $hhlink;
}

##################################################
# Sub Get_SubObjList - サブカテゴリオブジェクトリストの取得
##################################################
sub get_subcatobjlist {
    my $category = shift;
    
    #取得したカテゴリオブジェクトから子カテゴリを取得
    my @sub_categories = $category->children_categories;
    if (@sub_categories) {
        # サブカテゴリの取得
        foreach my $sub_category (@sub_categories) {
            my @ssub_categories = &get_subcatobjlist($sub_category);
            foreach my $ssub_category (@ssub_categories) {
                push @sub_categories, $ssub_category;
            }
        }
    }
    return @sub_categories;
}

####################
# Career distinction by User Agent
# 参考：http://specters.net/cgipon/labo/c_dist.html
####################
sub get_ua {
    my ($ejpemoji) = @_;
    my $ua;
    my @user_agent = split(/\//,$::ENV{'HTTP_USER_AGENT'});
    my $png_flag;
    if ($user_agent[0] eq 'ASTEL') {
        # dot i
        $ua = 'other';
    } elsif ($user_agent[0] eq 'UP.Browser') {
        # EZweb old model
        $ua = 'ezweb';
    } elsif ($user_agent[0] =~ /^KDDI/) {
        # EZweb WAP2.0
        $ua = 'ezweb';
    } elsif ($user_agent[0] eq 'PDXGW') {
        # H"
        $ua = 'other';
    } elsif ($user_agent[0] eq 'DoCoMo') {
        # i-mode
        $ua = 'i-mode';
    } elsif ($user_agent[0] eq 'Vodafone' ||
             $user_agent[0] eq 'SoftBank') {
        # Vodafone or SoftBank
        $ua = 'j-sky';
    } elsif ($user_agent[0] eq 'J-PHONE') {
        # J-PHONE
        $ua = 'j-sky';
    
        # The model that can display only PNG is checked beforehand.
        if (($user_agent[2] =~ /^J-DN02/) ||
            ($user_agent[2] =~ /^J-P02/) ||
            ($user_agent[2] =~ /^J-P03/) ||
            ($user_agent[2] =~ /^J-T04/) ||
            ($user_agent[2] =~ /^J-SA02/) ||
            ($user_agent[2] =~ /^J-SH02/) ||
            ($user_agent[2] =~ /^J-SH03/)){
                $png_flag = 1;
        }
    } elsif ($user_agent[1] =~ 'DDIPOCKET' ||
             $user_agent[1] =~ 'WILLCOM') {
        # AirH"PHONE、Willcom
        $ua = 'i-mode';
    } elsif ($user_agent[0] eq 'L-mode') {
        # L-mode
        $ua = 'other';
    } elsif ($user_agent[0] =~ 'emobile') {
        # emobile
        $ua = 'i-mode';
    } elsif ($user_agent[1] =~ /iPhone/ ||
             $user_agent[1] =~ /Android/ ) {
        # iPhone or Android
        $ua = 'smartphone';
    } else {
        # Other
        $ua = 'other';
    }

    my $enc_emoji_sjis;
    my $enc_e4u_sjis;
    my $enc_e4u_utf8;
    if ($ejpemoji) {
        my $cellular = ($ua eq 'i-mode' || $ua eq 'other') ? 'docomo'
                     : ($ua eq 'ezweb')                    ? 'kddiapp'
                     :                                       'softbank3g';
        $enc_emoji_sjis = 'x-sjis-emoji-'.$cellular;
        $enc_e4u_sjis   = 'x-sjis-e4u-'.$cellular;
        $enc_e4u_utf8   = 'x-utf8-e4u-'.$cellular;
    } else {
        $enc_emoji_sjis = 'shiftjis';
        $enc_e4u_sjis   = 'shiftjis';
        $enc_e4u_utf8   = 'utf8';
    }

    return ($ua, $png_flag, $enc_emoji_sjis, $enc_e4u_sjis, $enc_e4u_utf8);
}

##################################################
# Sub Get_NonDispCats - 非表示カテゴリリストの取得
##################################################
sub get_nondispcats {
    my @nondispcats = split(",", $::cfg{NonDispCat});
    my @nonsubdispcats;
    foreach my $nondispcatid (@nondispcats) {
        # IDからカテゴリオブジェクトを取得
        require MT::Category;
        my $category = MT::Category->load($nondispcatid);
        if (defined $category) {
            my @sub_categories = MT4i::Func::get_subcatobjlist($category);
            foreach my $sub_category (@sub_categories) {
                push @nonsubdispcats, $sub_category->id;
            }
        }
    }
    push @nondispcats, @nonsubdispcats;

    return @nondispcats;
}

##################################################
# Sub URL_Encode
# via http://sonic64.com/2003-08-31.html
##################################################
sub url_encode {
    my $url = shift;
    $url =~ s/([^\w ])/'%'.unpack('H2', $1)/eg;
    $url =~ tr/ /+/;
    return $url;
}

1;
