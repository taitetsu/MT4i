#!/usr/bin/perl
##################################################
#
# MT4i Manager - MT4i設定プログラム
my $version = "3.1";
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
#
##################################################

use strict;
use CGI;
use CGI::Carp qw(fatalsToBrowser);

# Config.pl、Func.plをrequire及び存在確認
eval {require 'lib/mt4i/Config.pl'; 1} || die &errorout('"./lib/mt4i/Config.pl"が見付かりません。');
eval {require 'lib/mt4i/Func.pl'; 1} || die &errorout('"./lib/mt4i/Func.pl"が見付かりません。');

# 変数定義
my %cfg;
my $mt4inm = 'mt4i.cgi';

####################
# 引数の取得
my $q = new CGI();
my $mode = $q->param("mode");                    # 処理モード
my $mgr_password = $q->param("mgr_password");    # 設定時パスワード
my $mgr_confirm = $q->param("mgr_confirm");      # 設定時確認用パスワード

####################
# 引数$modeの判断
if (!$mode)             { &default }
if ($mode eq 'passset') { &default }
if ($mode eq 'menu')    { &menu }
if ($mode eq 'edit')    { &edit }
if ($mode eq 'vup')     { &edit }
if ($mode eq 'save')    { &save }
if ($mode eq 'geturl')  { &geturl }
if ($mode eq 'dispurl') { &dispurl }

sub default {
    &header;

    if (!(%cfg = Config::Read("./mt4icfg.cgi")) || !$cfg{'Password'}) {
        if ($mode eq 'passset') {
            unless ($mgr_password) {
                print '<div class="alert">Error : パスワードを入力してください。</div>';
            } elsif ($mgr_password ne $mgr_confirm) {
                print '<div class="alert">Error : パスワードと確認用パスワードが異なります。</div>';
            } else {
                %cfg = Config::Read("./mt4icfg.cgi");
                $cfg{'Password'} = MT4i::Func::enc_crypt($mgr_password);
                &write_file(%cfg);
                print '<div class="description">MT4i Manager のパスワードを設定しました。</div>';
                &login;
            }
        }
        print "<form action=\"./mt4imgr.cgi\" method=\"post\">";
        print '<div class="description">';
        print 'まず最初に、MT4i Manager にログインする為のパスワードを設定してください。';
        print '<br />';
        print '誤入力防止の為、「確認用」にも同じパスワードを入力してください。';
        print '</div>';
        print '<div class="input">';
        print '<table><tr>';
        print '<td>パスワード：</td><td><input type="password" name="mgr_password" value="'.$mgr_password.'" /></td>';
        print '</tr><tr>';
        print '<td>確認用：</td><td><input type="password" name="mgr_confirm" value="'.$mgr_confirm.'" /></td>';
        print '</tr><tr>';
        print '<td colspan="2" ><input type="submit" name="submit" value="保存" /></td>';
        print '</tr></table>';
        print '</div>';
        print '<input type="hidden" name="mode" value="passset" />';
        print '</form>';
    } else {
        &login;
    }

    &hooter;
}

sub login {

    print "<form action=\"./mt4imgr.cgi\" method=\"post\">";
    print "<h3>ログイン</h3>";
    print '<div class="description">';
    print 'パスワード';
    print '</div>';
    print '<div class="input">';
    print '<input type="password" name="password" />';
    print '<input type="submit" name="submit" value="ログイン" />';
    print '</div>';
    print '<input type="hidden" name="mode" value="menu" />';
    print '</form>';

    &hooter;
    exit;
}

sub menu {
    %cfg = Config::Read("./mt4icfg.cgi");

    my $sendpass = $q->param("password");

    &header;

    if (!MT4i::Func::check_crypt($sendpass, $cfg{'Password'})) {
        print 'パスワードが違います。<br />';
        print '<form action="./mt4imgr.cgi" method="post">';
        print '<input type="hidden" name="password" value="'.$sendpass.'" />';
        print '<input type="submit" name="submit" value="戻る" />';
        print '</form>';
    
        &hooter;
    
        exit;
    }

    print "<form action=\"./mt4imgr.cgi\" method=\"post\">";
    print '<div class="description">';
    print 'メニュー';
    print '</div>';
    print '<div class="input">';
    print '<input type="radio" name="mode" id="edit" value="edit" style="vertical-align:middle" checked /><label for="edit" style="vertical-align:middle" >設定を編集する。</label>';
    if ($cfg{AdminPassword} && $cfg{AdminPassword} ne 'password') {
        print '<br />';
        print '<input type="radio" name="mode" id="geturl" value="geturl" style="vertical-align:middle" /><label for="geturl" style="vertical-align:middle" >管理者用のURLを取得する。</label>';
    }
    print '</div>';
    print '<div class="input">';
    print '<input type="submit" name="submit" value="ENTER" />';
    print '</div>';
    print '<input type="hidden" name="password" value="'.$sendpass.'" />';
    print '</form>';

    &hooter;
}

sub geturl {
    %cfg = Config::Read("./mt4icfg.cgi");

    my $sendpass = $q->param("password");

    &header;

    if (!MT4i::Func::check_crypt($sendpass, $cfg{'Password'})) {
        print 'パスワードが違います。<br />';
        print '<form action="./mt4imgr.cgi" method="post">';
        print '<input type="hidden" name="mode" value="menu" />';
        print '<input type="hidden" name="password" value="'.$sendpass.'" />';
        print '<input type="submit" name="submit" value="戻る" />';
        print '</form>';
    
        &hooter;
    
        exit;
    }

    print "<form action=\"./mt4imgr.cgi\" method=\"post\">";
    print '<div class="description">';
    print '管理者用URL取得パスワード';
    print '</div>';
    print '<div class="input">';
    print '<input type="password" name="adminpassword" />';
    print '<input type="submit" name="submit" value="ENTER" />';
    print '</div>';
    print '<input type="hidden" name="mode" value="dispurl" />';
    print '<input type="hidden" name="password" value="'.$sendpass.'" />';
    print '</form>';
    print '<form action="./mt4imgr.cgi" method="post">';
    print '<input type="hidden" name="mode" value="menu" />';
    print '<input type="hidden" name="password" value="'.$sendpass.'" />';
    print '<input type="submit" name="submit" value="メニューに戻る" />';
    print '</form>';
    
    &hooter;
}

sub dispurl {
    my $adminpass = $q->param("adminpassword");
    my $sendpass = $q->param("password");

    # 設定読み込み
    %cfg = Config::Read("./mt4icfg.cgi");

    &header;

    if ($adminpass ne $cfg{AdminPassword}) {
        print '管理者用URL取得パスワードが違います。<br />';
        print '<form action="./mt4imgr.cgi" method="post">';
        print '<input type="hidden" name="mode" value="geturl" />';
        print '<input type="hidden" name="password" value="'.$sendpass.'" />';
        print '<input type="submit" name="submit" value="戻る" />';
        print '</form>';
    
        &hooter;
    
        exit;
    } elsif (!MT4i::Func::check_crypt($sendpass, $cfg{'Password'})) {
        print 'パスワードが違います。<br />';
        print '<form action="./mt4imgr.cgi" method="post">';
        print '<input type="hidden" name="mode" value="geturl" />';
        print '<input type="hidden" name="password" value="'.$sendpass.'" />';
        print '<input type="submit" name="submit" value="戻る" />';
        print '</form>';
    
        &hooter;
    
        exit;
    }

    my $key = MT4i::Func::enc_crypt($cfg{AdminPassword}.$cfg{Blog_ID});

    print '<p>管理者用URLは';
    print "<a href=\"$cfg{MyName}?".$cfg{Blog_ID}."&key=".$key."\">こちら</a>";
    print 'です。</p>';
    print '<form action="./mt4imgr.cgi" method="post">';
    print '<input type="hidden" name="mode" value="menu" />';
    print '<input type="hidden" name="password" value="'.$sendpass.'" />';
    print '<input type="submit" name="submit" value="メニューに戻る" />';
    print '</form>';
    
    &hooter;
}

sub edit {
    %cfg = Config::Read("./mt4icfg.cgi");

    &header;

    # パスワード認証
    my $sendpass = $q->param("password");
    if (!MT4i::Func::check_crypt($sendpass, $cfg{'Password'})) {
        print 'パスワードが違います。<br />';
        print '<form action="./mt4imgr.cgi" method="post">';
        print '<input type="hidden" name="mode" value="menu" />';
        print '<input type="hidden" name="password" value="'.$sendpass.'" />';
        print '<input type="submit" name="submit" value="戻る" />';
        print '</form>';
    
        &hooter;
    
        exit;
    }

    if ($mode eq "vup") {
        if ($q->param("mt4inm")) {
            $mt4inm = $q->param("mt4inm");
        }
        if (!-e $mt4inm) {
            print "\"$mt4inm\"が見付かりません。<br />";
            print "MT4i本体のファイル名を入力してください。<br />";
            print "<form action=\"./mt4imgr.cgi\" method=\"post\">";
            print "<input type=\"text\" name=\"mt4inm\" style=\"width:200px\"><br />";
            print "<input type=\"submit\" name=\"submit\" value=\"送信\">";
            print "<input type=\"hidden\" name=\"mode\" value=\"vup\">";
            print "<input type=\"hidden\" name=\"password\" value=\"$cfg{'Password'}\">";
            print "</form>";
        
            &hooter;
        
            exit;
        }
        # mt4i.cgiオープン
        open(IN,"< $mt4inm") or die print "\"$mt4inm\"が見付かりません";
    
        my $rit_id_fl = 0;
        my $rat_id_fl = 0;
        while (<IN>){
            my $tmp = $_;
            chomp($tmp);
        
            # 注意：ここでは古いバージョンから値を読み込んでいるので、
            #       新規のパラメータをここに追加する必要はありません。
            if ($tmp =~ /^my/) {
                if ($tmp =~ /\(\$MT_DIR\)[^"']*["']([^"']*)["']/) {
                    $cfg{'MT_DIR'} = enc_tag($1);
                } elsif ($tmp =~ /\$blog_id[^"']*["']([^"']*)["']/) {
                    $cfg{'Blog_ID'} = enc_tag($1);
                } elsif ($tmp =~ /\$adm_nm[^"']*["']([^"']*)["']/) {
                    $cfg{'AdmNM'} = enc_tag($1);
                } elsif ($tmp =~ /\$adm_ml[^"']*["']([^"']*)["']/) {
                    $cfg{'AdmML'} = enc_tag($1);
                } elsif ($tmp =~ /\$logo_i[^"']*["']([^"']*)["']/) {
                    $cfg{'Logo_i'} = enc_tag($1);
                } elsif ($tmp =~ /\$logo_o[^"']*["']([^"']*)["']/) {
                    $cfg{'Logo_o'} = enc_tag($1);
                } elsif ($tmp =~ /\$disp_num[^"']*["']([^"']*)["']/) {
                    $cfg{'DispNum'} = enc_tag($1);
                } elsif ($tmp =~ /\$bg_color[^"']*["']([^"']*)["']/) {
                    $cfg{'BgColor'} = enc_tag($1);
                } elsif ($tmp =~ /\$txt_color[^"']*["']([^"']*)["']/) {
                    $cfg{'TxtColor'} = enc_tag($1);
                } elsif ($tmp =~ /\$lnk_color[^"']*["']([^"']*)["']/) {
                    $cfg{'LnkColor'} = enc_tag($1);
                } elsif ($tmp =~ /\$alnk_color[^"']*["']([^"']*)["']/) {
                    $cfg{'AlnkColor'} = enc_tag($1);
                } elsif ($tmp =~ /\$vlnk_color[^"']*["']([^"']*)["']/) {
                    $cfg{'VlnkColor'} = enc_tag($1);
                } elsif ($tmp =~ /\$z2h[^"']*["']([^"']*)["']/) {
                    $cfg{'Z2H'} = enc_tag($1);
                } elsif ($tmp =~ /\$bq2p[^"']*["']([^"']*)["']/) {
                    $cfg{'BQ2P'} = enc_tag($1);
                } elsif ($tmp =~ /\$bqcolor[^"']*["']([^"']*)["']/) {
                    $cfg{'BqColor'} = enc_tag($1);
                } elsif ($tmp =~ /\$sprtstr[^"']*["']([^"']*)["']/) {
                    $cfg{'SprtStr'} = enc_tag($1);
                } elsif ($tmp =~ /\$sprtlimit[^"']*["']([^"']*)["']/) {
                    $cfg{'SprtLimit'} = enc_tag($1);
                } elsif ($tmp =~ /\$myname[^"']*["']([^"']*)["']/) {
                    $cfg{'MyName'} = enc_tag($1);
                } elsif ($tmp =~ /\$accesskey[^"']*["']([^"']*)["']/) {
                    $cfg{'AccessKey'} = enc_tag($1);
                } elsif ($tmp =~ /\$image_autoreduce[^"']*["']([^"']*)["']/) {
                    $cfg{'ImageAutoReduce'} = enc_tag($1);
                } elsif ($tmp =~ /\$photo_width[^"']*["']([^"']*)["']/) {
                    $cfg{'PhotoWidth'} = enc_tag($1);
                } elsif ($tmp =~ /\$png_width[^"']*["']([^"']*)["']/) {
                    $cfg{'PngWidth'} = enc_tag($1);
                } elsif ($tmp =~ /\$cat_desc_replace[^"']*["']([^"']*)["']/) {
                    $cfg{'CatDescReplace'} = enc_tag($1);
                } elsif ($tmp =~ /\$cat_desc_sort[^"']*["']([^"']*)["']/) {
                    $cfg{'CatDescSort'} = enc_tag($1);
                } elsif ($tmp =~ /\$post_from_essential[^"']*["']([^"']*)["']/) {
                    $cfg{'PostFromEssential'} = enc_tag($1);
                } elsif ($tmp =~ /\$post_mail_essential[^"']*["']([^"']*)["']/) {
                    $cfg{'PostMailEssential'} = enc_tag($1);
                } elsif ($tmp =~ /\$post_text_essential[^"']*["']([^"']*)["']/) {
                    $cfg{'PostTextEssential'} = enc_tag($1);
                } elsif ($tmp =~ /\$recent_comment[^"']*["']([^"']*)["']/) {
                    $cfg{'RecentComment'} = enc_tag($1);
                } elsif ($tmp =~ /\$recent_trackback[^"']*["']([^"']*)["']/) {
                    $cfg{'RecentTB'} = enc_tag($1);
                } elsif ($tmp =~ /\$photo_host_original[^"']*["']([^"']*)["']/) {
                    $cfg{'Photo_Host_Original'} = enc_tag($1);
                } elsif ($tmp =~ /\$photo_host_replace[^"']*["']([^"']*)["']/) {
                    $cfg{'Photo_Host_Replace'} = enc_tag($1);
                } elsif ($tmp =~ /\$exitchtmltrans[^"']*["']([^"']*)["']/) {
                    $cfg{'ExitChtmlTrans'} = enc_tag($1);
                } elsif ($tmp =~ /\@rbld_indx_tmpl_id/) {
                    $rit_id_fl = 1;
                    $cfg{'RIT_ID'} = '';
                } elsif ($tmp =~ /\@rbld_arc_tmpl_id/) {
                    $rat_id_fl = 1;
                    $cfg{'RAT_ID'} = '';
                } elsif ($tmp =~ /\$approve_comment[^"']*["']([^"']*)["']/) {
                    $cfg{'ApproveComment'} = enc_tag($1);
                } elsif ($tmp =~ /\$admin_helper[^"']*["']([^"']*)["']/) {
                    my @arg = split(/,/, $1);
                    $cfg{'AdminHelper'} = 'yes';
                    $cfg{'AdminHelperID'} = $arg[0];
                    $cfg{'AdminHelperNM'} = $arg[1];
                    $cfg{'AdminHelperML'} = $arg[2];
                } elsif ($tmp =~ /\$author_name[^"']*["']([^"']*)["']/) {
                    $cfg{'AuthorName'} = enc_tag($1);
                } elsif ($tmp =~ /\$admin_password[^"']*["']([^"']*)["']/) {
                    $cfg{'AdminPassword'} = enc_tag($1);
                }
            } elsif ($rit_id_fl == 1) {
                if ($tmp !~ /\);/) {
                    $tmp =~ s/    //g;
                    $tmp =~ s/ //g;
                    $tmp =~ s/'//g;
                    $cfg{'RIT_ID'} = $cfg{'RIT_ID'} . $tmp;
                } else {
                    $rit_id_fl = 0;
                    $cfg{'RIT_ID'} =~ s/,$//g;
                }
            } elsif ($rat_id_fl == 1) {
                if ($tmp !~ /\);/) {
                    $tmp =~ s/    //g;
                    $tmp =~ s/ //g;
                    $tmp =~ s/'//g;
                    $cfg{'RAT_ID'} = $cfg{'RAT_ID'} . $tmp;
                } else {
                    $rat_id_fl = 0;
                    $cfg{'RAT_ID'} =~ s/,$//g;
                }
            }
            # 注意：ここでは古いバージョンから値を読み込んでいるので、
            #       新規のパラメータをここに追加する必要はありません。
        }
        print '<p>';
        if (!$cfg{'MT_DIR'}) {
            print '設定が存在しません。初期値を挿入します。<br />';
            print "→もしくは、<a href=\"./mt4imgr.cgi?mode=vup&amp;password=$sendpass\">v1.82β1以前の設定を読み込むにはこちら。</a>";
        } else {
            print '設定を読み込みました。<br />';
        }
        print '</p>';
    } elsif (!exists $cfg{'MT_DIR'}) {
        print '<p>';
        print '設定が存在しません。初期値を挿入します。<br />';
        print "→もしくは、<a href=\"./mt4imgr.cgi?mode=vup&amp;password=$sendpass\">v1.82β1以前の設定を読み込むにはこちら。</a>";
        print '</p>';
    }

    # デフォルト値設定
    if ( !exists $cfg{'MT_DIR'} ) { $cfg{'MT_DIR'} = './'; }
    if ( !exists $cfg{'Blog_ID'} ) { $cfg{'Blog_ID'} = ''; }
    if ( !exists $cfg{'AdmNM'} ) { $cfg{'AdmNM'} = ''; }
    if ( !exists $cfg{'AdmML'} ) { $cfg{'AdmML'} = ''; }
    if ( !exists $cfg{'Logo_i'} ) { $cfg{'Logo_i'} = ''; }
    if ( !exists $cfg{'Logo_o'} ) { $cfg{'Logo_o'} = ''; }
    if ( !exists $cfg{'DispNum'} ) { $cfg{'DispNum'} = 10; }
    if ( !exists $cfg{'DtLang'} ) { $cfg{'DtLang'} = 'ja'; }
    if ( !exists $cfg{'IndexDtFormat'} ) { $cfg{'IndexDtFormat'} = '%Y-%m-%d %H:%M:%S'; }
    if ( !exists $cfg{'IndividualDtFormat'} ) { $cfg{'IndividualDtFormat'} = '%Y-%m-%d %H:%M:%S'; }
    if ( !exists $cfg{'CommentDtFormat'} ) { $cfg{'CommentDtFormat'} = '%Y-%m-%d %H:%M:%S'; }
    if ( !exists $cfg{'TBPingDtFormat'} ) { $cfg{'TBPingDtFormat'} = '%Y-%m-%d %H:%M:%S'; }
    if ( !exists $cfg{'BgColor'} ) { $cfg{'BgColor'} = '#FFFFFF'; }
    if ( !exists $cfg{'TxtColor'} ) { $cfg{'TxtColor'} = '#000000'; }
    if ( !exists $cfg{'LnkColor'} ) { $cfg{'LnkColor'} = '#0000FF'; }
    if ( !exists $cfg{'AlnkColor'} ) { $cfg{'AlnkColor'} = '#FF0000'; }
    if ( !exists $cfg{'VlnkColor'} ) { $cfg{'VlnkColor'} = '#800080'; }
    if ( !exists $cfg{'Z2H'} ) { $cfg{'Z2H'} = 'yes'; }
    if ( !exists $cfg{'BQ2P'} ) { $cfg{'BQ2P'} = 'no'; }
    if ( !exists $cfg{'BqColor'} ) { $cfg{'BqColor'} = '#008000'; }
    if ( !exists $cfg{'SprtStr'} ) { $cfg{'SprtStr'} = '<br>,<br />,</p>'; }
    if ( !exists $cfg{'SprtLimit'} ) { $cfg{'SprtLimit'} = 4096; }
    if ( !exists $cfg{'MyName'} ) { $cfg{'MyName'} = 'mt4i.cgi'; }
    if ( !exists $cfg{'AccessKey'} ) { $cfg{'AccessKey'} = 'yes'; }
    if ( !exists $cfg{'ImageAutoReduce'} ) { $cfg{'ImageAutoReduce'} = 'imagemagick'; }
    if ( !exists $cfg{'PhotoWidth'} ) { $cfg{'PhotoWidth'} = 144; }
    if ( !exists $cfg{'PhotoWidthForce'} ) { $cfg{'PhotoWidthForce'} = 0; }
    if ( !exists $cfg{'PngWidth'} ) { $cfg{'PngWidth'} = 48; }
    if ( !exists $cfg{'CatDescReplace'} ) { $cfg{'CatDescReplace'} = 'no'; }
    if ( !exists $cfg{'CatDescSort'} ) { $cfg{'CatDescSort'} = 'none'; }
    if ( !exists $cfg{'PostFromEssential'} ) { $cfg{'PostFromEssential'} = 'yes'; }
    if ( !exists $cfg{'PostMailEssential'} ) { $cfg{'PostMailEssential'} = 'yes'; }
    if ( !exists $cfg{'PostTextEssential'} ) { $cfg{'PostTextEssential'} = 'yes'; }
    if ( !exists $cfg{'RecentComment'} ) { $cfg{'RecentComment'} = 15; }
    if ( !exists $cfg{'RecentTB'} ) { $cfg{'RecentTB'} = 10; }
    if ( !exists $cfg{'Photo_Host_Original'} ) { $cfg{'Photo_Host_Original'} = ''; }
    if ( !exists $cfg{'Photo_Host_Replace'} ) { $cfg{'Photo_Host_Replace'} = 'localhost'; }
    if ( !exists $cfg{'CommentNum'} ) { $cfg{'CommentNum'} = 5; }
    if ( !exists $cfg{'ChtmlTrans'} ) { $cfg{'ChtmlTrans'} = 1; }
    if ( !exists $cfg{'ExitChtmlTrans'} ) { $cfg{'ExitChtmlTrans'} = '携帯対応'; }
    if ( !exists $cfg{'MobileGW'} ) { $cfg{'MobileGW'} = '1'; }
    if ( !exists $cfg{'ECTrans_Str_i'} ) { $cfg{'ECTrans_Str_i'} = '<font color="#FFCC33">&#xE6D2;</font>'; }
    if ( !exists $cfg{'ECTrans_Str_j'} ) { $cfg{'ECTrans_Str_j'} = "\x1B\$Fu\x0F"; }
    if ( !exists $cfg{'ECTrans_Str_o'} ) { $cfg{'ECTrans_Str_o'} = '(携帯対応)'; }
    if ( !exists $cfg{'Ainori_Str_i'} ) { $cfg{'Ainori_Str_i'} = '<font color="#FFCC33">&#xE6D2;</font>'; }
    if ( !exists $cfg{'Ainori_Str_j'} ) { $cfg{'Ainori_Str_j'} = "\x1B\$Fu\x0F"; }
    if ( !exists $cfg{'Ainori_Str_o'} ) { $cfg{'Ainori_Str_o'} = '(MT4i)'; }
    if ( !exists $cfg{'RIT_ID'} ) { $cfg{'RIT_ID'} = 'ALL'; }
    if ( !exists $cfg{'RAT_ID'} ) { $cfg{'RAT_ID'} = 'ALL'; }
    if ( !exists $cfg{'ApproveComment'} ) { $cfg{'ApproveComment'} = 'yes'; }
    if ( !exists $cfg{'CommentFilterStr'} ) { $cfg{'CommentFilterStr'} = '<h1>,<a\s,^[\x00-\xff]+$'; }
    if ( !exists $cfg{'SerNo'} ) { $cfg{'SerNo'} = 0; }
    if ( !exists $cfg{'AdminHelper'} ) { $cfg{'AdminHelper'} = 'no'; }
    if ( !exists $cfg{'AdminHelperID'} ) { $cfg{'AdminHelperID'} = ''; }
    if ( !exists $cfg{'AdminHelperNM'} ) { $cfg{'AdminHelperNM'} = ''; }
    if ( !exists $cfg{'AdminHelperML'} ) { $cfg{'AdminHelperML'} = ''; }
    if ( !exists $cfg{'AuthorName'} ) { $cfg{'AuthorName'} = ''; }
    if ( !exists $cfg{'AdminPassword'} ) { $cfg{'AdminPassword'} = 'password'; }
    if ( !exists $cfg{'NonDispCat'} ) { $cfg{'NonDispCat'} = ''; }
    if ( !exists $cfg{'LenCutCat'} ) { $cfg{'LenCutCat'} = 0; }
    if ( !exists $cfg{'ArrowComments'} ) { $cfg{'ArrowComments'} = 1; }
    if ( !exists $cfg{'CacheTime'} ) { $cfg{'CacheTime'} = 0; }
    if ( !exists $cfg{'PurgeCacheLimit'} ) { $cfg{'PurgeCacheLimit'} = 24; }
    if ( !exists $cfg{'PurgeCacheMailFrom'} ) { $cfg{'PurgeCacheMailFrom'} = ''; }
    if ( !exists $cfg{'PurgeCacheMailTo'} ) { $cfg{'PurgeCacheMailTo'} = ''; }
    if ( !exists $cfg{'CachePageCountIndex'} ) { $cfg{'CachePageCountIndex'} = 0; }
    if ( !exists $cfg{'PathOfUseLib'} ) { $cfg{'PathOfUseLib'} = ''; }
    if ( !exists $cfg{'ContentType'} ) { $cfg{'ContentType'} = 'xhtml'; }
    if ( !exists $cfg{'UseThumbnail'} ) { $cfg{'UseThumbnail'} = 0; }
    if ( !exists $cfg{'ThumbWidth'} ) { $cfg{'ThumbWidth'} = 75; }
    if ( !exists $cfg{'EmojiConvResult'} ) { $cfg{'EmojiConvResult'} = 'image'; }

    #----------------------------------------------------------------------------------------------------
    print '<table><tr><td>';
    print '<ul>';
    print '    <li><span style="font-weight:bold;color:#FF0000;">必須設定項目</span>';
    print '    <ul>';
    print '        <li><a href="#MT_DIR"> MTホームディレクトリ</a></li>';
    print '        <li><a href="#Blog_ID">Movable Type 上で使用しているBlog固有のID</a></li>';
    print '    </ul>';
    print '    </li>';
    print '</ul>';
    print '<ul>';
    print '    <li>表示関連設定項目';
    print '    <ul>';
    print '        <li><a href="#AdmNML">管理者名の表示とメールアドレス</a></li>';
    print '        <li><a href="#Logo">タイトルロゴ画像を設定する</a></li>';
    print '        <li><a href="#DispNum">トップ（記事一覧）に表示させる記事数</a></li>';
    print '        <li><a href="#DT">投稿日時の表示形式</a></li>';
    print '        <li><a href="#Colors">色の設定</a></li>';
    print '    </ul>';
    print '    </li>';
    print '</ul>';
    print '<ul>';
    print '    <li>コメント関連設定項目';
    print '    <ul>';
    print '        <li><a href="#CommentNum">1ページに表示するコメント数</a></li>';
    print '        <li><a href="#PostEssential">コメント投稿時入力必須項目の指定</a></li>';
    print '        <li><a href="#RecentComment">最近のコメント一覧表示コメント数</a></li>';
    print '        <li><a href="#RIAT_ID">コメント投稿時のRebuild対象テンプレートを指定する</a></li>';
    print '        <li><a href="#ArrowComments">コメント投稿機能のON/OFF</a></li>';
    print '        <li><a href="#ApproveComment">コメント掲載の承諾（MT3.0以上で有効）</a></li>';
    print '        <li><a href="#CommentFilterStr">コメント SPAM 判定正規表現</a></li>';
    print '        <li><a href="#SerNo">コメント投稿時に固有識別情報を要求する</a></li>';
    print '    </ul>';
    print '    </li>';
    print '</ul>';
    print '<ul>';
    print '    <li>カテゴリ関連設定項目';
    print '    <ul>';
    print '        <li><a href="#CatDescReplace">カテゴリ名のDescription置換</a></li>';
    print '        <li><a href="#CatDescSort">カテゴリ名のソート</a></li>';
    print '        <li><a href="#NonDispCat">特定のカテゴリを非表示にする</a></li>';
    print '        <li><a href="#LenCutCat">カテゴリ名を指定文字数でカットする</a></li>';
    print '    </ul>';
    print '    </li>';
    print '</ul>';
    print '<ul>';
    print '    <li>Cache 関連設定項目';
    print '    <ul>';
    print '        <li><a href="#CacheTime">キャッシュの保持期間</a></li>';
    print '        <li><a href="#PurgeCacheScript">purge_old_cache.pl スクリプトに関する設定</a></li>';
    print '        <li><a href="#CachePageCountIndex">インデックスページをキャッシュするページ数</a></li>';
    print '    </ul>';
    print '    </li>';
    print '</ul>';
    print '</td><td>';
    print '<ul>';
    print '    <li>画像関連設定項目';
    print '    <ul>';
    print '        <li><a href="#ImageAutoReduce">画像の自動縮小</a></li>';
    print '        <li><a href="#PhotoWidth">デフォルト画像の横幅</a></li>';
    print '        <li><a href="#PngWidth">vodafoneの特定機種(6機種)のPNG画像の横幅</a></li>';
    print '        <li><a href="#PhotoWidthForce">画像を指定した幅に強制的に縮小する</a></li>';
    print '        <li><a href="#UseThumbnail">サムネイル画像のオンオフ</a></li>';
    print '        <li><a href="#ThumbWidth">サムネイル画像のサイズ</a></li>';
    print '    </ul>';
    print '    </li>';
    print '</ul>';
    print '<ul>';
    print '    <li>その他任意設定項目';
    print '    <ul>';
    print '        <li><a href="#Z2H">全角→半角変換</a></li>';
    print '        <li><a href="#BQ2P">&lt;blockquote&gt;→&lt;p&gt;変換</a></li>';
    print '        <li><a href="#SprtStr">記事分割時の区切り文字列</a></li>';
    print '        <li><a href="#SprtLimit">記事本文を分割をする制限バイト数</a></li>';
    print '        <li><a href="#MyName">MT4i本体のファイル名</a></li>';
    print '        <li><a href="#AccessKey">携帯電話の絵文字及びアクセスキー</a></li>';
    print '        <li><a href="#RecentTB">最近のトラックバック表示数</a></li>';
    print '        <li><a href="#Photo_Host">自宅サーバの外/内部ホスト名</a></li>';
    print '        <li><a href="#ChtmlTrans">モバイル変換ゲートウェイ周りの設定</a></li>';
    print '        <li><a href="#Ainori">あいのり機能（Mobile Link Discovery）</a></li>';
    print '        <li><a href="#ContentType">使用する Content-Type</a></li>';
    print '        <li><a href="#EmojiConvResult">絵文字の変換結果</a></li>';
    print '    </ul>';
    print '    </li>';
    print '</ul>';
    print '<ul>';
    print '    <li>管理者モード設定項目';
    print '    <ul>';
    print '        <li><a href="#AdminHelper">コメント投稿時の管理者情報入力補助</a></li>';
    print '        <li><a href="#AuthorName">Entry投稿者のログイン名</a></li>';
    print '        <li><a href="#AdminPassword">管理者URL取得パスワード</a></li>';
    print '    </ul>';
    print '    </li>';
    print '</ul>';
    print '<ul>';
    print '    <li>高度設定項目';
    print '    <ul>';
    print '        <li><a href="#PathOfUseLib">追加ライブラリのパス</a></li>';
    print '    </ul>';
    print '    </li>';
    print '</ul>';
    print '<ul>';
    print '    <li>MT4i Manager 設定項目';
    print '    <ul>';
    print '        <li><a href="#ManagementPass">MT4i Manager パスワードの変更</a></li>';
    print '    </ul>';
    print '    </li>';
    print '</ul>';
    print '</td></tr></table>';
    #----------------------------------------------------------------------------------------------------

    print '<form action="./mt4imgr.cgi" method="post">';
    print '<input type="hidden" name="mode" value="menu" />';
    print '<input type="hidden" name="password" value="'.$sendpass.'" />';
    print '<input type="submit" name="submit" value="メニューに戻る" />';
    print '</form>';
    print "<form action=\"./mt4imgr.cgi\" method=\"post\">";
    print '<input type="submit" name="submit" value="保存" /><br />';

    #----------------------------------------------------------------------------------------------------
    print '<h3>必須設定項目</h3>';
    print '<h4 id="MT_DIR">MT_DIR - MTホームディレクトリ</h4>';
    print '<div class="description">';
    print 'Movable Type をインストールしたディレクトリ（mt.cgiのある場所）を、絶対パスあるいは相対パスで指定。<br />「"http://〜" で始まるURLではない」ので注意。<br />最後には必ず"/"（スラッシュ）を付けてください。<br />　例：/home/user/www/mt/<br />またMT3.0以上では、MTホームディレクトリ以外のディレクトリにMT4iをインストールし、相対パスにてMTホームディレクトリを指定した場合、一部機能が正常に動作しないことを確認しています（Pluginにて追加したテキストフォーマットがドロップダウンリストに現われないなど）。<br />MT3.0以上を使用している場合は、絶対パスで指定してください。<br />';
    print '</div>';
    print '<div class="input">';
    print '<input type="text" name="MT_DIR" value="' . $cfg{MT_DIR} . '" /><br />';
    print '</div><div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    print '<h4 id="Blog_ID">Blog_ID - Movable Type 上で使用しているBlog固有のID</h4>';
    print '<div class="description">';
    print 'Movable Type 設置後、デフォルトで作成されるBlogのIDが "1"。<br />その後、Blogを追加する毎に連番で付与される。<br />ここで指定しなくても、アクセスする際のURLに "?id=" として渡してやっても良い。<br />MT4iへのURLが "http://your-domain/mt4i.cgi"、BlogのIDが "1" ならば、<br />"http://your-domain/mt4i.cgi?id=1" となる。<br />良く分からない場合はここで指定せずに設置、アクセスすると解説を表示するのでそちらを参照のこと。<br />';
    print '</div>';
    print '<div class="input">';
    print '<input type="text" name="Blog_ID" value="' . $cfg{Blog_ID} . '" /><br />';
    print '</div><div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    #----------------------------------------------------------------------------------------------------
    print '<h3>任意設定項目</h3>';
    print '<h4 id="AdmNML">管理者名の表示とメールアドレス</h4>';
    print '<div class="description">';
    print '各画面下に管理者名を表示する場合には管理者名を入力する。<br />';
    print '何も入力されていなければ非表示。';
    print '</div>';
    print '<div class="input">';
    print '管理者名： <input type="text" name="AdmNM" value="' . $cfg{AdmNM} . '" /><br />';
    print '</div>';
    print '<div class="description">';
    print '上記管理者名に、"mailto:〜" のハイパーリンクを貼る場合には管理者メールアドレスを入力する。<br />必然的に上記管理者名の設定が必須。<br />メールアドレスは表示時、"@" と "." のみ数値文字参照に変換（SPAMメール対策）。<br />';
    print '</div>';
    print '<div class="input">';
    print '管理者メールアドレス： <input type="text" name="AdmML" value="' . $cfg{AdmML} . '" style="width:200px;" /><br />';
    print '</div><div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    print '<h4 id="Logo">Logo - タイトルロゴ画像の指定</h4>';
    print '<div class="description">';
    print 'トップに表示するタイトルを画像表示したい場合、表示したい画像のURLを入力。相対パスでも可。未入力ならテキストで表示。i-mode用はGIF、i-mode以外用はPNG画像を指定すること。<br />';
    print '</div>';
    print '<div class="input">';
    print 'i-mode用： ';
    print '<input type="text" name="Logo_i" value="' . $cfg{Logo_i} . '" class="long" /><br />';
    print 'i-mode以外用： ';
    print '<input type="text" name="Logo_o" value="' . $cfg{Logo_o} . '" class="long" /><br />';
    print '</div><div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    print '<h4 id="DispNum">DispNum - トップ（記事一覧）に表示させる記事数</h4>';
    print '<div class="input">';
    print '<input type="text" name="DispNum" value="' . $cfg{DispNum} . '" /><br />';
    print '</div><div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    print '<h4 id="DT">投稿日時の表示形式</h4>';
    print '<div class="description">';
    print 'Movable Type のテンプレートタグで使う、日付に関するモディファイアにて形式が指定できます。<br />また、言語別の日付フォーマットを指定できます。<br /><a href="http://movabletype.jp/documentation/appendices/date-formats.html">日付に関するテンプレートタグのモディファイアリファレンス</a>';
    print '</div>';
    print '<div class="input">';
    print '<table border="0">';
    print '<tr><td>';
    print '言語別の日付フォーマット：';
    print '</td><td>';
    print '<input type="text" name="DtLang" value="' . $cfg{DtLang} . '" class="middle" /><br />';
    print '</td></tr>';
    print '<tr><td>';
    print 'トップ（記事タイトル一覧）ページ：';
    print '</td><td>';
    print '<input type="text" name="IndexDtFormat" value="' . $cfg{IndexDtFormat} . '" class="middle" /><br />';
    print '</td></tr>';
    print '<tr><td>';
    print '個別記事ページ：';
    print '</td><td>';
    print '<input type="text" name="IndividualDtFormat" value="' . $cfg{IndividualDtFormat} . '" class="middle" /><br />';
    print '</td></tr>';
    print '<tr><td>';
    print 'コメント一覧ページ：';
    print '</td><td>';
    print '<input type="text" name="CommentDtFormat" value="' . $cfg{CommentDtFormat} . '" class="middle" /><br />';
    print '</td></tr>';
    print '<tr><td>';
    print 'トラックバック一覧ページ：';
    print '</td><td>';
    print '<input type="text" name="TBPingDtFormat" value="' . $cfg{TBPingDtFormat} . '" class="middle" /><br />';
    print '</td></tr>';
    print '</table>';
    print '</div><div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    print '<h4 id="Colors">色の設定</h4>';
    print '<div class="input">';
    print '<table border="0">';
    print '<tr><td>';
    print '背景色(bgcolor)：';
    print '</td><td>';
    print '<input type="text" name="BgColor" value="' . $cfg{BgColor} . '" /><br />';
    print '</td></tr><tr><td>';
    print 'テキストの色(text)：';
    print '</td><td>';
    print '<input type="text" name="TxtColor" value="' . $cfg{TxtColor} . '" /><br />';
    print '</td></tr><tr><td>';
    print 'リンク色(link)：';
    print '</td><td>';
    print '<input type="text" name="LnkColor" value="' . $cfg{LnkColor} . '" /><br />';
    print '</td></tr><tr><td>';
    print 'アクティブなリンク色(alink)：';
    print '</td><td>';
    print '<input type="text" name="AlnkColor" value="' . $cfg{AlnkColor} . '" /><br />';
    print '</td></tr><tr><td>';
    print '既訪問のリンク色(vlink)：';
    print '</td><td>';
    print '<input type="text" name="VlnkColor" value="' . $cfg{VlnkColor} . '" /><br />';
    print '</td></tr><tr><td>';
    print 'Entry本文&lt;blockquote&gt;部の色： ';
    print '</td><td>';
    print '<input type="text" name="BqColor" value="' . $cfg{BqColor} . '" />';
    print ' Movable Type の設定で、convert_breaks が ON になっていることが前提。';
    print '</td></tr>';
    print '</table>';
    print '</div><div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    print '<h4 id="Z2H">Z2H - 全角→半角変換</h4>';
    print '<div class="input">';
    print '<select name="Z2H">';
    if ($cfg{Z2H} eq 'yes') {
        print '<option value="yes" selected>する</option>';
        print '<option value="no">しない</option>';
    } else {
        print '<option value="yes">する</option>';
        print '<option value="no" selected>しない</option>';
    }
    print '</select>';
    print '</div><div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    print '<h4 id="BQ2P">BQ2P - &lt;blockquote&gt;→&lt;p&gt;変換</h4>';
    print '<div class="description">';
    print 'Movable Type の設定で、convert_breaks が ON になっていることが前提。';
    print '</div>';
    print '<div class="input">';
    print '<select name="BQ2P">';
    if ($cfg{BQ2P} eq 'yes') {
        print '<option value="yes" selected>する</option>';
        print '<option value="no">しない</option>';
    } else {
        print '<option value="yes">する</option>';
        print '<option value="no" selected>しない</option>';
    }
    print '</select>';
    print '</div><div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    print '<h4 id="SprtStr">SprtStr - 記事分割時の区切り文字列</h4>';
    print '<div class="description">';
    print 'カンマで区切って複数パターン指定することができます。<br />';
    print '1番目に指定した文字列がマッチしなかったら2番目、と順番にマッチングします。<br />';
    print '例：&lt;br /&gt;,&lt;br&gt;,&lt;/p&gt;';
    print '</div>';
    print '<div class="input">';
    print '<input type="text" name="SprtStr" value="' . $cfg{SprtStr} . '" /><br />';
    print '</div><div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    print '<h4 id="SprtLimit">SprtLimit - 記事本文を分割をする制限バイト数（ヘッダやフッタを考慮すること）</h4>';
    print '<div class="input">';
    print '<input type="text" name="SprtLimit" value="' . $cfg{SprtLimit} . '" /><br />';
    print '</div><div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    print '<h4 id="MyName">MyName - MT4i本体のファイル名（index.cgiなどに変更したい人用）</h4>';
    print '<div class="input">';
    print '<input type="text" name="MyName" value="' . $cfg{MyName} . '" /><br />';
    print '</div><div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    print '<h4 id="AccessKey">AccessKey - 携帯電話の絵文字及びアクセスキー</h4>';
    print '<div class="description">';
    print 'これを有効にすると、携帯電話からアクセスされた際、自動的に記事一覧で表示される記事数が6件以下に調整されます。<br />';
    print '</div>';
    print '<div class="input">';
    print '<select name="AccessKey">';
    if ($cfg{AccessKey} eq 'yes') {
        print '<option value="yes" selected>有効</option>';
        print '<option value="no">無効</option>';
    } else {
        print '<option value="yes">有効</option>';
        print '<option value="no" selected>無効</option>';
    }
    print '</select>';
    print '</div><div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    print '<h4 id="ImageAutoReduce">ImageAutoReduce - 画像の自動縮小</h4>';
    print '<div class="input">';
    print '<select name="ImageAutoReduce">';
    if ($cfg{ImageAutoReduce} eq 'imagemagick') {
        print '<option value="imagemagick" selected>自前（Image::Magick）</option>';
        print '<option value="picto">外部サービス（Picto）</option>';
        print '<option value="no">しない</option>';
    } elsif ($cfg{ImageAutoReduce} eq 'picto') {
        print '<option value="imagemagick">自前（Image::Magick）</option>';
        print '<option value="picto" selected>外部サービス（Picto）</option>';
        print '<option value="no">しない</option>';
    } else {
        print '<option value="imagemagick">自前（Image::Magick）</option>';
        print '<option value="picto">外部サービス（Picto）</option>';
        print '<option value="no" selected>しない</option>';
    }
    print '</select>';
    print '</div><div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    print '<h4 id="PhotoWidth">デフォルト画像の横幅</h4>';
    print '<div class="input">';
    print '<input type="text" name="PhotoWidth" value="' . $cfg{PhotoWidth} . '" /><br />';
    print '</div><div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    print '<h4 id="PngWidth">vodafoneの特定機種(6機種)のPNG画像の横幅</h4>';
    print '<div class="input">';
    print '<input type="text" name="PngWidth" value="' . $cfg{PngWidth} . '" /><br />';
    print '</div><div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    print '<h4 id="PhotoWidthForce">画像を指定した幅に強制的に縮小する</h4>';
    print '<div class="description">';
    print '端末のキャッシュサイズに関係なく、画像の横幅を上記サイズへ強制的に縮小するかどうかを選択できます(縦の高さも横幅に比例して縮小されます）。<br />';
    print '「強制縮小しない」（デフォルト）を選択すると、端末のキャッシュサイズを検出し、表示できる最大サイズで表示します。<br />';
    print '</div>';
    print '<select name="PhotoWidthForce">';
    print '<option value="1"'.($cfg{PhotoWidthForce} == 1 ? ' selected' : '').'>強制縮小する</option>';
    print '<option value="0"'.($cfg{PhotoWidthForce} == 0 ? ' selected' : '').'>強制縮小しない</option>';
    print '</select>';
    print '</div><div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    print '<h4 id="CatDescReplace">CatDescReplace - カテゴリ名のDescription置換</h4>';
    print '<div class="description">';
    print 'カテゴリ名の日本語化をMTCategoryDescriptionで行っているか。';
    print '</div>';
    print '<div class="input">';
    print '<select name="CatDescReplace">';
    if ($cfg{CatDescReplace} eq 'yes') {
        print '<option value="yes" selected>行っている</option>';
        print '<option value="no">行っていない</option>';
    } else {
        print '<option value="yes">行っている</option>';
        print '<option value="no" selected>行っていない</option>';
    }
    print '</select>';
    print '</div><div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    print '<h4 id="CatDescSort">CatDescSort - カテゴリ名のソート</h4>';
    print '<div class="input">';
    print '<select name="CatDescSort">';
    if ($cfg{CatDescSort} eq 'none') {
        print '<option value="none" selected>しない</option>';
        print '<option value="asc">昇順</option>';
        print '<option value="desc">降順</option>';
    } elsif ($cfg{CatDescSort} eq 'asc') {
        print '<option value="none">しない</option>';
        print '<option value="asc" selected>昇順</option>';
        print '<option value="desc">降順</option>';
    } else {
        print '<option value="none">しない</option>';
        print '<option value="asc">昇順</option>';
        print '<option value="desc" selected>降順</option>';
    }
    print '</select>';
    print '</div><div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    print '<h4 id="PostEssential">コメント投稿時入力必須項目の指定</h4>';
    print '<div class="input">';
    print '<table border="0">';
    print '<tr><td>';
    print '投稿者名：';
    print '</td><td>';
    print '<select name="PostFromEssential">';
    if ($cfg{PostFromEssential} eq 'yes') {
        print '<option value="yes" selected>必須</option>';
        print '<option value="no">省略可</option>';
    } else {
        print '<option value="yes">必須</option>';
        print '<option value="no" selected>省略可</option>';
    }
    print '</select>';
    print '</td></tr><tr><td>';
    print 'メールアドレス：';
    print '</td><td>';
    print '<select name="PostMailEssential">';
    if ($cfg{PostMailEssential} eq 'yes') {
        print '<option value="yes" selected>必須</option>';
        print '<option value="no">省略可</option>';
    } else {
        print '<option value="yes">必須</option>';
        print '<option value="no" selected>省略可</option>';
    }
    print '</select>';
    print '</td></tr><tr><td>';
    print 'コメント本文：';
    print '</td><td>';
    print '<select name="PostTextEssential">';
    if ($cfg{PostTextEssential} eq 'yes') {
        print '<option value="yes" selected>必須</option>';
        print '<option value="no">省略可</option>';
    } else {
        print '<option value="yes">必須</option>';
        print '<option value="no" selected>省略可</option>';
    }
    print '</select>';
    print '</td></tr>';
    print '</table>';
    print '</div><div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    print '<h4 id="RecentComment">RecentComment - 最近のコメント一覧表示コメント数</h4>';
    print '<div class="input">';
    print '<input type="text" name="RecentComment" value="' . $cfg{RecentComment} . '" /><br />';
    print '</div><div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    print '<h4 id="RecentTB">RecentTB - 最近のトラックバック表示数</h4>';
    print '<div class="input">';
    print '<input type="text" name="RecentTB" value="' . $cfg{RecentTB} . '" /><br />';
    print '</div><div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    print '<h4 id="Photo_Host">Photo_Host_Original/Replace - 自宅サーバの外部／内部ホスト名</h4>';
    print '<div class="description">';
    print '自宅サーバ運用等で画像縮小が動かない場合、また、あいのり機能（Mobile Link Discovery）が動かない場合、\'外部ホスト名\'に外から見えるホスト名、\'内部ホスト名\'に内部的なホスト名を入力。<br />';
    print '(記述例)\'www.hazama.nu\'の場合、<br />';
    print '<ul><li>http://www.hazama.nu/archive/test.jpg</li></ul>が<ul><li>http://localhost/archive/test.jpg</li></ul>に置換されることで、自ホストの画像データを読み込めたりモバイル向けURLが取得できるようになる場合あり。<br />';
    print '\'Photo_Host_Original\'未入力で機能オフ。<br />';
    print '</div>';
    print '<div class="input">';
    print '外部ホスト名: ';
    print '<input type="text" name="Photo_Host_Original" value="' . $cfg{Photo_Host_Original} . '" /><br />';
    print '内部ホスト名: ';
    print '<input type="text" name="Photo_Host_Replace" value="' . $cfg{Photo_Host_Replace} . '" /><br />';
    print '</div><div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    print '<h4 id="CommentNum">1ページに表示するコメント数</h4>';
    print '<div class="description">';
    print 'コメントページにて、1ページに表示するコメント数を指定します。<br />';
    print 'ここで指定された数を超える投稿があった場合、改ページされます。<br />';
    print 'コメント数は1コメントの大きさなどを見つつ、適宜調整してください。<br />';
    print '</div>';
    print '<div class="input">';
    print '<input type="text" name="CommentNum" value="' . $cfg{CommentNum} . '" /><br />';
    print '</div><div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    print '<h4 id="ChtmlTrans">モバイル変換ゲートウェイ周りの設定</h4>';
    print '<div class="description">';
    print '記事本文に含まれるリンクを、携帯向けに表示を変換してくれるゲートウェイ（プロキシ）に関する設定。';
    print '</div>';
    print '<div class="description">';
    print 'モバイル変換ゲートウェイを使用するか否か。';
    print '</div>';
    print '<div class="input">';
    print '<select name="ChtmlTrans">';
    print '<option value="1"'.( $cfg{ChtmlTrans} ? ' selected' : '').'>する</option>';
    print '<option value="0"'.(!$cfg{ChtmlTrans} ? ' selected' : '').'>しない</option>';
    print '</select>';
    print '</div>';
    print '<div class="description">';
    print 'AタグのTITLE属性が、以下に指定した文字列を含む場合、モバイル変換ゲートウェイを経由しない。<br />';
    print '</div>';
    print '<div class="input">';
    print '<input type="text" name="ExitChtmlTrans" value="' . enc_amp_quot($cfg{ExitChtmlTrans}) . '" /><br />';
    print '</div>';
    print '<div class="description">';
    print '携帯対応リンク（モバイル変換ゲートウェイを経由しないリンク）の前に表示する文字(付けたくない場合は空文字列にする）';
    print '</div>';
    print '<div class="input">';
    print 'i-mode および EZWeb：<input type="text" name="ECTrans_Str_i" value="' . enc_amp_quot($cfg{ECTrans_Str_i}) . '" style="width:300px;" /><br />';
    print 'J-SKY：<input type="text" name="ECTrans_Str_j" value="' . enc_amp_quot($cfg{ECTrans_Str_j}) . '" style="width:300px;" /><br />';
    print 'その他：<input type="text" name="ECTrans_Str_o" value="' . enc_amp_quot($cfg{ECTrans_Str_o}) . '" style="width:300px;" /><br />';
    print '</div>';
    print '<div class="description">';
    print 'モバイル変換ゲートウェイ選択';
    print '</div>';
    print '<div class="input">';
    print '<select name="MobileGW">';
    if ($cfg{MobileGW} eq '1') {
        print '<option value="1" selected>通勤ブラウザ</option>';
        print '<option value="2">Google.co.jp</option>';
    } elsif ($cfg{MobileGW} eq '2') {
        print '<option value="1">通勤ブラウザ</option>';
        print '<option value="2" selected>Google.co.jp</option>';
    }
    print '</select>';
    print '</div><div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    print '<h4 id="Ainori">あいのり機能（Mobile Link Discovery）</h4>';
    print '<div class="description">';
    print 'あいのり機能でモバイル対応となったリンクの前に表示する文字(付けたくない場合は空文字列にする）';
    print '</div>';
    print '<div class="input">';
    print 'i-mode および EZWeb：<input type="text" name="Ainori_Str_i" value="' . enc_amp_quot($cfg{Ainori_Str_i}) . '" style="width:300px;" /><br />';
    print 'J-SKY：<input type="text" name="Ainori_Str_j" value="' . enc_amp_quot($cfg{Ainori_Str_j}) . '" style="width:300px;" /><br />';
    print 'その他：<input type="text" name="Ainori_Str_o" value="' . enc_amp_quot($cfg{Ainori_Str_o}) . '" style="width:300px;" /><br />';
    print '</div>';
    print '</div><div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    print '<h4 id="RIAT_ID">コメント投稿時のRebuild対象テンプレートを指定する</h4>';
    print '<div class="description">';
    print 'コメント投稿時にRebuildの対象とするIndexテンプレートのTemplete IDを指定する。<br />';
    print 'Indexテンプレートすべてを対象とするなら"ALL"と指定する。<br />';
    print '各IDはカンマ（,）で区切る（注：スペースは入れないこと）<br />';
    print '例：10,13,20<br />';
    print '</div>';
    print '<div class="input">';
    print 'Indexテンプレート：<input type="text" name="RIT_ID" value="' . $cfg{RIT_ID} . '" style="width:300px;" /><br />';
    print '</div>';
    print '<div class="description">';
    print 'コメント投稿時にRebuildの対象とするArchiveテンプレートを指定する。<br />';
    print 'Archiveテンプレートすべてを対象とするなら"ALL"と指定する。';
    print '各IDはカンマ（,）で区切る（注：スペースは入れないこと）<br />';
    print '例：Individual,Daily,Weekly,Monthly,Category<br />';
    print '</div>';
    print '<div class="input">';
    print 'Archiveテンプレート：<input type="text" name="RAT_ID" value="' . $cfg{RAT_ID} . '" style="width:300px;" /><br />';
    print '</div><div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    print '<h4 id="ApproveComment">ApproveComment - コメント掲載の承諾（MT3.0以上で有効）</h4>';
    print '<div class="input">';
    print '<select name="ApproveComment">';
    if ($cfg{ApproveComment} eq 'yes') {
        print '<option value="yes" selected>即承諾する</option>';
        print '<option value="no">一旦保留する</option>';
    } else {
        print '<option value="yes">即承諾する</option>';
        print '<option value="no" selected>一旦保留する</option>';
    }
    print '</select>';
    print '</div><div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    print '<h4 id="CommentFilterStr">CommentFilterStr - コメント SPAM 判定正規表現</h4>';
    print '<div class="description">';
    print 'コメント本文が指定した正規表現にマッチする場合、コメント SPAM として弾く。<br />';
    print '複数指定する場合は半角カンマで区切る。<br />';
    print '</div>';
    print '<div class="input">';
    print '<input type="text" name="CommentFilterStr" value="' . $cfg{CommentFilterStr} . '" style="width:300px;" /><br />';
    print '</div>';
    print '<div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    print '<h4 id="SerNo">コメント投稿時に固有識別情報を要求する</h4>';
    print '<div class="description">';
    print 'Docomo のみ。<br />';
    print 'コメント投稿の際に、固有識別情報の送信を要求する。<br />';
    print '送信拒否した場合には、コメントの投稿がされない。<br />';
    print '</div>';
    print '<div class="input">';
    print '<select name="SerNo">';
    if ($cfg{SerNo} == 1) {
        print '<option value="1" selected>要求する</option>';
        print '<option value="0">要求しない</option>';
    } else {
        print '<option value="1">要求する</option>';
        print '<option value="0" selected>要求しない</option>';
    }
    print '</select>';
    print '</div>';
    print '<div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    print '<h4 id="NonDispCat">NonDispCat - 特定のカテゴリを非表示にする</h4>';
    print '<div class="description">';
    print '非表示にするカテゴリのIDを指定する。<br />';
    print '未入力ですべてを表示。<br />';
    print 'カテゴリIDは、MT管理画面の「カテゴリー」にて、各カテゴリ名のリンクをポイントしてステータスバーに表示される「http://your-domain.com/mt/mt.cgi?__mode=view&_type=category&blog_id=x&id=xx」といったURLの最後の「id=xx」の「xx」の部分。<br />';
    print '各IDはカンマ（,）で区切る（注：スペースは入れないこと）<br />';
    print '例：10,13,20<br />';
    print '親カテゴリを非表示に設定すると、それに属する子カテゴリも表示されなくなるので注意すること。<br />';
    print '</div>';
    print '<div class="input">';
    print '<input type="text" name="NonDispCat" value="' . $cfg{NonDispCat} . '" style="width:300px;" /><br />';
    print '</div>';
    print '<div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    print '<h4 id="LenCutCat">LenCutCat - カテゴリ名を指定バイト数でカットする</h4>';
    print '<div class="description">';
    print 'カテゴリセレクタ内のカテゴリ名を、指定バイト数でカットする。<br />';
    print 'カテゴリ名が長過ぎて、携帯端末のバイト数制限などに引っ掛かる場合に使用。<br />';
    print '「0（ゼロ）」指定で無効（デフォルト）。<br />';
    print '</div>';
    print '<div class="input">';
    print '<input type="text" name="LenCutCat" value="' . $cfg{LenCutCat} . '" style="width:300px;" /><br />';
    print '</div>';
    print '<div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    print '<h4 id="ArrowComments">ArrowComments - コメント投稿機能のON/OFF</h4>';
    print '<div class="description">';
    print 'コメント投稿の可／不可は、デフォルトではMT（あるいは個々のエントリ）の設定に従うが、';
    print '強制的にOFFにしたい（MT4i上でのコメント投稿を禁止したい）場合に使用。';
    print '</div>';
    print '<div class="input">';
    print '<select name="ArrowComments">';
    if ($cfg{ArrowComments} eq '1') {
        print '<option value="1" selected>MTの設定に従う（デフォルト）</option>';
        print '<option value="0">強制的にOFFにする</option>';
    } else {
        print '<option value="1">MTの設定に従う（デフォルト）</option>';
        print '<option value="0" selected>強制的にOFFにする</option>';
    }
    print '</select>';
    print '</div>';
    print '<div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    print '<h4 id="CacheTime">CacheTime - キャッシュの保持期間</h4>';
    print '<div class="description">';
    print 'キャッシュを使用する場合、キャッシュを保持する期間を分単位で指定。<br />';
    print '「0（ゼロ）」指定で無効（デフォルト）。<br />';
    print '</div>';
    print '<div class="input">';
    print '<input type="text" name="CacheTime" value="' . $cfg{CacheTime} . '" /><br />';
    print '</div>';
    print '<div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    print '<h4 id="PurgeCacheScript">PurgeCacheScript - purge_old_cache.pl スクリプトに関する設定</h4>';
    print '<div class="description">';
    print 'スクリプト purge_old_cache.pl を使用してキャッシュを消し込む場合の、キャッシュを保持する期間を時単位で指定。<br />';
    print 'ファイルの更新時間がここで指定した時間より昔のファイルが unlink で削除されます。<br />';
    print 'また、スクリプト動作後に送信される通知メールの送信元、送信先のメールアドレスを入力してください。<br />';
    print '</div>';
    print '<div class="input">';
    print '<table><tr><th>';
    print '保持期間：';
    print '</th><td>';
    print '<input type="text" name="PurgeCacheLimit" value="' . $cfg{PurgeCacheLimit} . '" /><br />';
    print '</td></tr><tr><th>';
    print 'メール送信元：';
    print '</th><td>';
    print '<input type="text" name="PurgeCacheMailFrom" value="' . $cfg{PurgeCacheMailFrom} . '" style="width:200px;" /><br />';
    print '</td></tr><tr><th>';
    print 'メール送信先：';
    print '</th><td>';
    print '<input type="text" name="PurgeCacheMailTo" value="' . $cfg{PurgeCacheMailTo} . '" style="width:200px;" /><br />';
    print '</td></tr></table>';
    print '</div>';
    print '<div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    print '<h4 id="CachePageCountIndex">インデックスページをキャッシュするページ数</h4>';
    print '<div class="description">';
    print 'インデックス（記事一覧）ページのキャッシュはエントリー投稿/編集時に全件クリアする必要がある。<br />';
    print 'エントリーの投稿などに時間がかかる場合は、ここの値を調整する。<br />';
    print 'そのかわり、ページ数を制限するとボットのクロールが高負荷を生む可能性がある。<br />';
    print '何ページ目までをキャッシュするか、ページ数を入力。<br />';
    print '「0（ゼロ）」指定で全ページをキャッシュする（デフォルト）。<br />';
    print '</div>';
    print '<div class="input">';
    print '<input type="text" name="CachePageCountIndex" value="' . $cfg{CachePageCountIndex} . '" /><br />';
    print '</div>';
    print '<div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    print '<h4 id="ContentType">使用する Content-Type</h4>';
    print '<div class="description">';
    print 'テンプレートの言語に HTML を使用するか、XHTML を使用するか選択。<br />';
    print 'HTML を選択すると HTTP ヘッダに Content-Type として text/html を、<br />';
    print 'XHTML を選択すると application/xhtml+xml を出力します。';
    print '</div>';
    print '<div class="input">';
    print '<select name="ContentType">';
    print '<option value="html"'.(($cfg{ContentType} eq 'html') ? ' selected' : '').'>HTML</option>';
    print '<option value="xhtml"'.(($cfg{ContentType} eq 'xhtml') ? ' selected' : '').'>XHTML</option>';
    print '</select>';
    print '</div>';
    print '<div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    print '<h4 id="UseThumbnail">サムネイル画像のオンオフ</h4>';
    print '<div class="description">';
    print '記事本文中に埋め込まれた画像のサムネイルを表示するかどうか選択します。<br />';
    print 'サムネイルを表示しない場合、"&lt;画像：[alt タグの内容]&gt;"という代替テキストが表示されます。（デフォルト）';
    print '</div>';
    print '<div class="input">';
    print '<select name="UseThumbnail">';
    print '<option value="0"'.((!$cfg{UseThumbnail}) ? ' selected' : '').'>OFF</option>';
    print '<option value="1"'.(( $cfg{UseThumbnail}) ? ' selected' : '').'>ON</option>';
    print '</select>';
    print '</div>';
    print '<div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    print '<h4 id="ThumbWidth">サムネイル画像のサイズ</h4>';
    print '<div class="description">';
    print '本文中に表示されるサムネイル画像のサイズをピクセルにて指定します。<br />';
    print '縦横どちらか、長辺に対して適用されます。<br />';
    print 'デフォルトは 75 ピクセルです。';
    print '</div>';
    print '<div class="input">';
    print '<input type="text" name="ThumbWidth" value="' . $cfg{ThumbWidth} . '" /><br />';
    print '</div>';
    print '<div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    print '<h4 id="EmojiConvResult">絵文字の変換結果</h4>';
    print '<div class="description">';
    print '記事やコメント投稿時、入力された絵文字を何に変換するか設定します。<br />';
    print 'デフォルトは img タグです。TypeCast タグに変換することもできます。';
    print '</div>';
    print '<div class="input">';
    print '<select name="EmojiConvResult">';
    print '<option value="image"'.(($cfg{EmojiConvResult}) eq 'image' ? ' selected' : '').'>画像(imgタグ)</option>';
    print '<option value="tctag"'.(($cfg{EmojiConvResult}) eq 'tctag' ? ' selected' : '').'>TypeCastタグ</option>';
    print '</select>';
    print '</div>';
    print '<div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    #----------------------------------------------------------------------------------------------------
    print '<h3>管理者モード設定項目</h3>';
    print '<h4 id="AdminHelper">AdminHelper - コメント投稿時の管理者情報入力を手助け</h4>';
    print '<div class="description">';
    print '名前の代わりにIDを記入するだけで、名前、メールアドレスが自動的に記入される。<br />';
    print '管理者モードでのみ有効。<br />';
    print '</div>';
    print '<div class="input">';
    print '<table border="0">';
    print '<tr><td>';
    print 'AdminHelperを使用する';
    print '</td><td>';
    print '<select name="AdminHelper">';
    if ($cfg{AdminHelper} eq 'yes') {
        print '<option value="yes" selected>はい</option>';
        print '<option value="no">いいえ</option>';
    } else {
        print '<option value="yes">はい</option>';
        print '<option value="no" selected>いいえ</option>';
    }
    print '</select>';
    print '</td></tr><tr><td>';
    print 'ID：';
    print '</td><td>';
    print '<input type="text" name="AdminHelperID" value="' . $cfg{AdminHelperID} . '" /><br />';
    print '</td></tr><tr><td>';
    print '名前：';
    print '</td><td>';
    print '<input type="text" name="AdminHelperNM" value="' . $cfg{AdminHelperNM} . '" /><br />';
    print '</td></tr><tr><td>';
    print 'メールアドレス：';
    print '</td><td>';
    print '<input type="text" name="AdminHelperML" value="' . $cfg{AdminHelperML} . '" style="width:200px;" /><br />';
    print '</td></tr>';
    print '</table>';
    print '</div><div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    print '<h4 id="AuthorName">AuthorName - Entry投稿者のログイン名</h4>';
    print '<div class="description">';
    print 'MovableTypeに登録済みの、投稿者（ユーザ）のログイン名（ユーザ名）を指定する。<br />';
    print '3.0以降：メイン・メニュー &gt; システム・メニュー &gt; 投稿者 &gt; 投稿者名 &gt; ログイン名<br />';
    print '2.661以前：メインメニュー &gt; プロフィールを編集する &gt; ユーザ名<br />';
    print '</div>';
    print '<div class="input">';
    print '<input type="text" name="AuthorName" value="' . $cfg{AuthorName} . '" /><br />';
    print '</div><div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    print '<h4 id="AdminPassword">AdminPassword - 「管理者向けURL取得」の為のパスワード</h4>';
    print '<div class="description">';
    print '英数字。必ずデフォルトのパスワードから変更すること。<br />';
    print '</div>';
    print '<div class="input">';
    print '<input type="text" name="AdminPassword" value="' . $cfg{AdminPassword} . '" /><br />';
    print '</div><div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';
 
    #----------------------------------------------------------------------------------------------------
    print '<h3>高度設定項目</h3>';
    print '<h4 id="PathOfUseLib">追加ライブラリへのパス</h4>';
    print '<div class="description">';
    print '\'use lib\' して使用するライブラリパスを指定します。<br />';
    print '複数ある場合は半角カンマで区切ってください。';
    print '</div>';
    print '<div class="input">';
    print '<table border="0">';
    print '<tr><th>';
    print 'パス：';
    print '</th><td>';
    print '<input type="text" name="PathOfUseLib" value="'.$cfg{PathOfUseLib}.'" style="width:300px;" /><br />';
    print '</td></tr>';
    print '</table>';
    print '</div><div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    #----------------------------------------------------------------------------------------------------
    print '<h3>MT4i Manager の設定項目</h3>';
    print '<h4 id="ManagementPass">MT4i Manager パスワードの変更</h4>';
    print '<div class="description">';
    print 'このスクリプトにログインする為のパスワードを設定します。<br />';
    print '</div>';
    print '<div class="input">';
    print '<table border="0">';
    print '<tr><th>';
    print '現在のパスワード：';
    print '</th><td>';
    print '<input type="password" name="PresentPass" /><br />';
    print '</td></tr><tr><th>';
    print '新しいパスワード：';
    print '</th><td>';
    print '<input type="password" name="NewPass" /><br />';
    print '</td></tr><tr><th>';
    print '新しいパスワード確認：';
    print '</th><td>';
    print '<input type="password" name="ConfirmPass" /><br />';
    print '</td></tr>';
    print '</table>';
    print '</div><div class="backlink"><a href="#top">ページのTOPへ戻る</a></div>';

    #----------------------------------------------------------------------------------------------------
    print '<input type="submit" name="submit" value="保存">';
    print '<input type="hidden" name="mode" value="save">';
    print '<input type="hidden" name="password" value="'.$sendpass.'">';
    print '</form>';
    print '<form action="./mt4imgr.cgi" method="post">';
    print '<input type="hidden" name="mode" value="menu" />';
    print '<input type="hidden" name="password" value="'.$sendpass.'" />';
    print '<input type="submit" name="submit" value="メニューに戻る" />';
    print '</form>';

    &hooter;
}

sub save {
    %cfg = Config::Read("./mt4icfg.cgi");

    # パスワード認証
    my $sendpass = $q->param("password");
    if (!MT4i::Func::check_crypt($sendpass, $cfg{'Password'})) {
        &header;

        print 'パスワードが違います。<br />';
        print '<form action="./mt4imgr.cgi" method="post">';
        print '<input type="hidden" name="mode" value="edit" />';
        print '<input type="hidden" name="password" value="'.$sendpass.'" />';
        print '<input type="submit" name="submit" value="戻る" />';
        print '</form>';
    
        &hooter;
    
        exit;
    }

    # パスワード変更の確認
    my $presentpass = $q->param("PresentPass");
    my $newpass = $q->param("NewPass");
    my $confirmpass = $q->param("ConfirmPass");
    if ($presentpass) {
        if (!MT4i::Func::check_crypt($presentpass, $cfg{'Password'}) || $newpass ne $confirmpass) {
            &header;

            print '現在のパスワードか、確認用のパスワードが間違っています。<br />';
            print '<form action="./mt4imgr.cgi" method="post">';
            print '<input type="button" name="button" value="戻る" onclick=\'javascript:history.back()\'/>';
            print '</form>';
    
            &hooter;
    
            exit;
        } else {
            $cfg{'Password'} = MT4i::Func::enc_crypt($newpass);
            $sendpass = $newpass;
        }
    }
    
    ####################
    # 引数の取得
    my @names = get_setting_names();
    foreach my $name (@names) {
        $cfg{$name} = del_rn($q->param($name));
    }

    ####################
    # 書き込み
    &write_file(%cfg);

    # 出力
    &header;

    print '設定を保存しました。';
    print "<form action=\"./mt4imgr.cgi\" method=\"post\">";
    print '<input type="submit" name="submit" value="戻る" />';
    print '<input type="hidden" name="password" value="'.$sendpass.'" />';
    print '<input type="hidden" name="mode" value="edit" />';
    print '</form>';

    &hooter;
}

############################################################
# Write to file
############################################################
sub write_file {
    my (%new_cfg) = @_;
    my $cfg_file = "./mt4icfg.cgi";

    my %cfg = Config::Read($cfg_file);
    my @names = get_setting_names();
    foreach my $name (@names) {
        $cfg{$name} = $new_cfg{$name}
            if ($name ne 'Password' || ($name eq 'Password' && $new_cfg{$name}));
    }

    if (!-e $cfg_file) {
        open(OUT,"> $cfg_file") or die "Can't open  : $!";
    } else {
        open(OUT,"+< $cfg_file") or die "Can't open  : $!";
    }
    flock(OUT, 2) or die "Can't flock : $!";
    seek(OUT, 0, 0) or die "Can't seek  : $!";
    while ( my ( $key , $value ) = each %cfg ) {
        print OUT "$key<>$value\n" or die "Can't print : $!";
    }
    truncate(OUT, tell(OUT)) or die "Can't truncate : $!";
    close(OUT);
}

############################################################
# 改行を削除
############################################################
sub del_rn {
    my ($val) = @_;
    $val =~ s/\r//g;
    $val =~ s/\n//g;
    return $val;
}

############################################################
# '<'と'>'を実体参照に変換する
############################################################
sub enc_tag {
    my ($val) = @_;
    $val =~ s/</&lt;/g;
    $val =~ s/>/&gt;/g;
    return $val;
}

############################################################
# "&"及びダブルクォーテーションを実体参照に変換する
############################################################
sub enc_amp_quot {
    my ($val) = @_;
    $val =~ s/&/&amp;/g;
    $val =~ s/"/&quot;/g;
    return $val;
}

############################################################
# Errorの出力
############################################################
sub errorout {
    my ($val) = @_;
    print "Content-type: text/plain; charset=UTF-8\n\nError!\n$val";
}

############################################################
# ヘッダの出力
############################################################
sub header {
    print "Content-type: text/html; charset=UTF-8\n\n";
    print '<?xml version="1.0" encoding="UTF-8"?>';
    print '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">';
    print '<html xmlns="http://www.w3.org/1999/xhtml" lang="ja" xml:lang="ja">';
    print '<head>';
    print '<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />';
    print '<title>MT4i Manager</title>';
    print '<link rel="stylesheet" href="./css/mt4imanager.css" type="text/css" />';
    print '</head>';
    print '<body>';
    print '<h2 id="top">MT4i Manager</h2>';
}

############################################################
# フッタの出力
############################################################
sub hooter {
    print "<div class=\"version\">version $version</div>";
    print "</body>";
    print "</html>";
}

############################################################
# Get the list of a setting name.
############################################################
sub get_setting_names {
    return (
        'Password', 'MT_DIR', 'Blog_ID', 'AdmNM', 'AdmML',
        'Logo_i', 'Logo_o', 'DispNum', 'DtLang',
        'IndexDtFormat', 'IndividualDtFormat', 'CommentDtFormat', 'TBPingDtFormat',
        'BgColor', 'TxtColor', 'LnkColor', 'AlnkColor', 'VlnkColor',
        'Z2H', 'BQ2P', 'BqColor', 'SprtStr',
        'SprtLimit', 'MyName', 'AccessKey', 'ImageAutoReduce',
        'PhotoWidth', 'PhotoWidthForce', 'PngWidth',
        'CatDescReplace', 'CatDescSort', 'PostFromEssential', 'PostMailEssential',
        'PostTextEssential', 'RecentComment', 'RecentTB', 'Photo_Host_Original',
        'Photo_Host_Replace', 'CommentNum', 'CommentNum', 'ChtmlTrans',
        'ExitChtmlTrans', 'MobileGW', 'ECTrans_Str_i', 'ECTrans_Str_j',
        'ECTrans_Str_o', 'Ainori_Str_i', 'Ainori_Str_j', 'Ainori_Str_o',
        'RIT_ID', 'RAT_ID', 'ApproveComment', 'CommentFilterStr',
        'SerNo', 'AdminHelper', 'AdminHelperID', 'AdminHelperNM',
        'AdminHelperML', 'AuthorName', 'AdminPassword', 'NonDispCat',
        'LenCutCat', 'ArrowComments', 'CacheTime', 'PurgeCacheLimit',
        'PurgeCacheMailFrom', 'PurgeCacheMailTo', 'CachePageCountIndex', 'PathOfUseLib',
        'ContentType', 'UseThumbnail', 'ThumbWidth', 'EmojiConvResult',
    );
}
