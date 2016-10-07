#!/usr/bin/perl
##################################################
#
# MovableType用 i-mode変換スクリプト
# 「MT4i」
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
# Special Thanks
#           ヴァリウム男爵 & Tonkey & drry
#
# MT4i - t2o2-Wiki
#  →http://hazama.nu/pukiwiki/?MT4i
# TonkeyさんのTonkey Magic
#  →http://tonkey.mails.ne.jp/
# ヴァリウム男爵の人生迷い箸
#  →http://mayoi.net/
# drryさんのdrry+@->Weblog
#  →http://blog.drry.jp/
#
# -- 言い訳ここから --
# ぶっちゃけ、行き当たりばったりの「動けばいいや」で
# コーディングしてますし、Perlに関しては素人同然なので、
# ソースが汚い＆技術的に未熟な点はご容赦ください。
# -- 言い訳ここまで --
#
##################################################

use strict;
use CGI;
use HTML::Template;
use Storable qw(lock_store lock_retrieve);
use FindBin qw($Bin);
use List::Util qw(first);
use HTTP::Date;
use CGI::Carp qw(fatalsToBrowser);
use Digest::MD5 qw(md5_hex);
use utf8;

my $bin;
my $log_pl;
our %cfg;

BEGIN {
    $bin = $Bin;
    
    # 外部ファイルの読み込み
    my $path = "$bin/lib/mt4i/";
    my $errstr = 'Content-type: text/plain; charset=UTF-8\n\nFile not found: '.$path;
    eval {require $path.'Config.pl'; 1};
    if ($@) { print $errstr.'Config.pl'; exit; }
    eval {require $path.'Func.pl'; 1};
    if ($@) { print $errstr.'Func.pl'; exit; }
    eval {require $path.'Enc.pl'; 1};
    if ($@) { print $errstr.'Enc.pl'; exit; }
    
    # Log library
    $log_pl = $bin.'/lib/mt4i/Log.pl';
    
    # 設定読み込み
    %cfg = Config::Read($bin.'/mt4icfg.cgi');
    if (!$cfg{MT_DIR}) {
        print "Content-type: text/plain; charset=UTF-8\n\nCan't read configuration.";
        exit;
    }
    
    # Set environment variable for the plug-in.
    $ENV{MT_HOME} = $cfg{MT_DIR};
    
    # Move to MT home directory
    chdir $cfg{MT_DIR};

    use lib $cfg{MT_DIR} . 'lib';
    use lib $cfg{MT_DIR} . 'extlib';
}

####################
# Jcode.pmの有無調査
eval 'use Jcode;';
if($@){
    print "Content-type: text/plain; charset=UTF-8\n\n\"Jcode.pm\"がインストールされていません。";
    exit;
}

use lib $bin.'/lib';
use lib split ',', $cfg{PathOfUseLib};
eval 'use Encode::JP::Emoji; use Encode::JP::Emoji::FB_EMOJI_TEXT;';
my $ejpemoji = ($@) ? 0 : 1 ;
            eval {require $log_pl; 1} or &errout('File not found: '.$log_pl);
            MT4i::Log::writelog('$ejpemoji = '.$ejpemoji);

# User Agent によるキャリア判別
my ($ua, $png_flag, $enc_emoji_sjis, $enc_e4u_sjis, $enc_e4u_utf8) = MT4i::Func::get_ua($ejpemoji);

####################
# AccessKey用文字列生成
my @nostr;
my @akstr;
for (my $i = 0; $i <= 9; $i++)  {
    $nostr[$i] = "";
    $akstr[$i] = "";
}
my $clock_icon;
my $mt4ilinkstr = $cfg{Ainori_Str_o};
my $ExitChtmlTransStr = MT4i::Enc::decode_utf8($cfg{ECTrans_Str_o});
if ($cfg{AccessKey} eq "yes") {
    for (my $i = 1; $i <= 10; $i++) {
        if ($i < 10) {
            $akstr[$i] = " accesskey=\"$i\"";
        } else {
            $akstr[0] = " accesskey=\"0\"";
        }
    }
    $akstr[10] = " accesskey=\"*\"";
    $akstr[11] = " accesskey=\"#\"";
    if ($ua eq "i-mode") {
        # docomo
        $mt4ilinkstr = $cfg{Ainori_Str_i};
        $ExitChtmlTransStr = MT4i::Enc::decode_utf8($cfg{ECTrans_Str_i});
        for (my $i = 1; $i <= 10; $i++) {
            my $code = sprintf("%04x", 0xE6E1 + $i);
            my $subscript = $i == 10 ? 0 : $i;
            $nostr[$subscript] = "&#x$code;";
        }
        $nostr[10] = "[*]";
        $nostr[11] = "&#xE6E0";
        # clock icon
        $clock_icon = "&#xE6BA;";
    } elsif ($ua eq "ezweb") {
        # EZweb
        $mt4ilinkstr = $cfg{Ainori_Str_i};
        $ExitChtmlTransStr = MT4i::Enc::decode_utf8($cfg{ECTrans_Str_i});
        $nostr[0] = "&#xE5AC";
        for (my $i = 1; $i <= 10; $i++) {
            if ($i < 10) {
                my $code = 63878 + $i;
                $nostr[$i] = "&#$code;";
            } else {
                $nostr[0] = "&#63888;";
            }
        }
        $nostr[10] = "[*]";
        $nostr[11] = "&#63877";
        # clock icon
        $clock_icon = "&#63838;";
    } elsif ($ua eq "j-sky") {
        # SoftBank
        $mt4ilinkstr = $cfg{Ainori_Str_j};
        $ExitChtmlTransStr = MT4i::Enc::decode_utf8($cfg{ECTrans_Str_j});
        $nostr[1] = "\x1B\$F<\x0F";
        $nostr[2] = "\x1B\$F=\x0F";
        $nostr[3] = "\x1B\$F>\x0F";
        $nostr[4] = "\x1B\$F?\x0F";
        $nostr[5] = "\x1B\$F@\x0F";
        $nostr[6] = "\x1B\$FA\x0F";
        $nostr[7] = "\x1B\$FB\x0F";
        $nostr[8] = "\x1B\$FC\x0F";
        $nostr[9] = "\x1B\$FD\x0F";
        $nostr[0] = "\x1B\$FE\x0F";
        $nostr[10] = "[*]";
        $nostr[11] = "\x1B\$F0\x0F";
        # clock icon
        $clock_icon = "\x1B\$GN\x0F";
    }
}

####################
# 引数の取得
my $q = new CGI();

my $blog_id = $q->param("id")
                    ? $q->param("id")
                    : $cfg{Blog_ID};      # blog ID
my $mode = $q->param("mode");             # 処理モード
my $no = $q->param("no");                 # エントリーNO
my $eid = $q->param("eid");               # エントリーID
&_check_is_number('Entry ID', $eid);

my $ref_eid = $q->param("ref_eid");       # 元記事のエントリーID
&_check_is_number('Entry ID', $ref_eid);

my $page = $q->param("page");             # ページNO
&_check_is_number('Page No', $page);

my $sprtpage = $q->param("sprtpage");     # 分割ページ数
my $sprtbyte = $q->param("sprtbyte");     # ページ分割byte数
my $redirect_url = $q->param("url");      # リダイレクト先のURL
# Validate URL
if ($redirect_url) {
    unless ($redirect_url =~ m/s?https?:\/\/[-_.!~*'()a-zA-Z0-9;\/?:\@&=+\$,%#]+/) {
        &errout('URL is illegal.');
    }
}
my $img = $q->param("img");               # 画像のURL
my $cat = $q->param("cat");               # カテゴリID
&_check_is_number('Category ID', $cat);

my $key = $q->param("key");                              # 暗号化キー
my $post_status = $q->param("post_status");              # エントリーのステータス
my $post_status_old = $q->param("post_status_old");      # エントリーの編集前のステータス
my $allow_comments = $q->param("allow_comments");        # エントリーのコメント許可チェック
my $allow_pings = $q->param("allow_pings");              # エントリーのping許可チェック
my $text_format = $q->param("convert_breaks");           # エントリーのテキストフォーマット
my %p;
foreach (qw/cat title text text_more excerpt keywords tags created_on authored_on/) {
    my $label = 'entry_'.$_;
    $p{$label} = $q->param($label) if $q->param($label);
}
$p{post_from} = $q->param("from");        # 投稿者
$p{post_mail} = $q->param("mail");        # メール
$p{post_text} = $q->param("text");        # コメント

# PerlMagick の有無調査
my $imk = 0;
if ($mode eq 'image' || $mode eq 'img_cut' || $mode eq 'thumbnail') {
    eval 'use Image::Magick;';

    if ($cfg{ImageAutoReduce} eq "imagemagick") {
        $imk = ($@) ? 0 : 1 ;
    } else {
        $imk = 0;
    }
} elsif ($cfg{ImageAutoReduce} eq "picto") {
    $imk = 2;
}

#管理者用暗号化キーをチェック
my $admin_mode;
if (($key ne "")&&(MT4i::Func::check_crypt($cfg{AdminPassword}.$blog_id,$key))){
    $admin_mode = 'yes';
}else{
    $admin_mode = 'no';
    $key = "";
}

### Global Variables ###
# mt object
my $mt;
# Encode.pm
my $ecd;
# PublishCharset
my $conv_in;
# blog object
my $blog;
# blog info
my $blog_name;
my $description;
my $sort_order_comments;
my $email_new_comments;
my $email_new_pings;
my $convert_paras;
my $convert_paras_comments;
# for Output
my $data;
# for Last_Modified header
my $cache_last_mod_gmt;

####################
# 引数$modeの判断
if (!$mode)                      { &main }
if ($mode eq 'individual')       { &individual }
if ($mode eq 'individual_rcm')   { &individual }
if ($mode eq 'individual_lnk')   { &individual }
if ($mode eq 'ainori')           { &individual }
if ($mode eq 'comment')          { &comment }
if ($mode eq 'comment_rcm')      { &comment }
if ($mode eq 'comment_lnk')      { &comment }
if ($mode eq 'image')            { &image }
if ($mode eq 'img_cut')          { &image_cut }
if ($mode eq 'thumbnail')        { &image_cut }
if ($mode eq 'comment_form')     { &comment_form }
if ($mode eq 'comment_form_rcm') { &comment_form }
if ($mode eq 'comment_form_lnk') { &comment_form }
if ($mode eq 'post_comment')     { &post_comment }
if ($mode eq 'post_comment_rcm') { &post_comment }
if ($mode eq 'post_comment_lnk') { &post_comment }
if ($mode eq 'recentcomment')    { &recent_comment }
if ($mode eq 'trackback')        { &trackback }
if ($mode eq 'redirect')         { &redirector }
if ($mode eq 'search_redirect')  { &search_redirector }
if ($mode eq 'search')           { &search }

#--- ここから先は管理モードでしか実行できない ---

    if ($admin_mode eq "yes") {
        if ($mode eq 'entryform')             { &entryform }
        if ($mode eq 'entry')                 { &entry }
        if ($mode eq 'comment_del')           { &comment_del }
        if ($mode eq 'entry_del')             { &entry_del }
        if ($mode eq 'trackback_del')         { &trackback_del }
        if ($mode eq 'trackback_ipban')       { &trackback_ipban }
        if ($mode eq 'comment_ipban')         { &comment_ipban }
        if ($mode eq 'email_comments')        { &email_comments }

        if ($mode eq 'confirm_comment_del')   { &confirm }
        if ($mode eq 'confirm_entry_del')     { &confirm }
        if ($mode eq 'confirm_trackback_del') { &confirm }
    }

########################################
# Sub Main - トップページの描画
########################################

sub main {

    if(!$mode && !$page) { $page = 0 }

    # キャッシュを読む
    if ((!$cfg{CachePageCountIndex} || $page < $cfg{CachePageCountIndex}) && $admin_mode eq 'no') {
        my $ccat = ($cat) ? 'c'.$cat : 'c0' ;
        my $template = _readcache('b'.$blog_id.'/idx'.$ccat.'/p'.$page.$ua, 1);
        &_cacheout($template) if $template;
    }

    # Get MT Object etc.
    &_get_mt_object();

    # HTMLテンプレートをオープン
    my $template = _tmpl_open('index.tmpl');

    if ($cfg{AccessKey} eq "yes" && ($ua eq "i-mode" || $ua eq "j-sky" || $ua eq "ezweb")) {
        # 携帯電話からのアクセスかつアクセスキー有効の場合は$cfg{DispNum}を6以下にする
        if ($cfg{DispNum} > 6) {
            $cfg{DispNum} = 6;
        }
    }
    my $rowid;
    if($page == 0) { $rowid = 0 } else { $rowid = $page * $cfg{DispNum} }

    ####################
    # 一覧の取得
    my @entries = &get_entries($rowid, $cfg{DispNum});

    # 一覧件数取得（$cfg{DispNum}より少ない可能性がある為）
    my $rowcnt = @entries + 1;

    ####################
    # 表示文字列生成

    ####################
    # 記事本文

    my @entry_index = ();
    my $entry_page;
    my $odd = 1;
    if (@entries > 0) {
        my $i = 0;
        for my $entry (@entries){ # 結果のフェッチと表示
            my $created_on = MT::Util::format_ts($cfg{IndexDtFormat},
                                                 $cfg{Version} >= 4.0 ? $entry->authored_on
                                                                              : $entry->created_on, undef, $cfg{DtLang});
            my $comment_cnt = $entry->comment_count;
            my $ping_cnt = $entry->ping_count;
            $rowid++;
            $i++;
            my $href = &make_href("individual", 0, 0, $entry->id, 0);
            my %row_data;  # 行データのための新しいハッシュを取得

            my @commons = _tmpl_loop_common($rowid, $i);
            $row_data{ENTRY_ROW_NO} = $commons[0];
            $row_data{ENTRY_ACCESS_KEY} = $commons[1];
            $row_data{ICON_CLOCK} = $commons[2];

            # Title
            my $title = _conv_utf8_z2h($entry->title);
            $title = "untitled" if($title eq '');
            # HOLD or FUTURE
            my $d_f = ($entry->status == 1) ? '(下書き)'
                    : ($entry->status == 3) ? '(指定日)' : '' ;
            $title = $d_f._conv_emoticon2tag($title);
            $title = MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, $title);
            $row_data{ENTRY_LINK_TITLE} = _conv_tag2binary($title);

            $row_data{ENTRY_LINK_URL} = $href;
            $row_data{ENTRY_CREATED_ON} = MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, MT4i::Enc::decode_utf8($created_on));
            if ($comment_cnt > 0) {
                $row_data{ENTRY_COMMENT_CNT} = "[$comment_cnt]";
            }
            if ($ping_cnt > 0) {
                $row_data{ENTRY_PING_CNT} = "[$ping_cnt]";
            }

            # Judge odd or even
            $row_data{ENTRY_ODD}  =  $odd;
            $row_data{ENTRY_EVEN} = !$odd;
            $odd                  = !$odd;

            # Customfields
            if ($cfg{Version} >= 4.1) {
                my $cfs = _get_customfields($entry);
                for my $cf (keys %$cfs) {
                    $row_data{"ENTRY_$cf"} = MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, MT4i::Enc::decode_utf8($cfs->{$cf}));
                }
            }

            # Keywords
            $row_data{ENTRY_KEYWORDS} = MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, MT4i::Enc::decode_utf8($entry->keywords));

            #Tags
            my @tag_hash;
            my @tags = $entry->tags;
            foreach my $tag (@tags) { # 結果のフェッチと表示
                my %tag_data;
                $tag_data{ENTRY_TAG} = MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, MT4i::Enc::decode_utf8($tag));
                push(@tag_hash, \%tag_data);
            }
            $row_data{ENTRY_TAGS} = \@tag_hash;

            # Indispensable step - Push the reference of this row to the array!
            push(@entry_index, \%row_data);
        }

        # エントリ総件数の取得
        my $ttlcnt = &get_ttlcnt;

        # 最終ページの算出
        if ($ttlcnt > $cfg{DispNum}) {
            my $lastpage;
            my $amari;
            $lastpage = int($ttlcnt / $cfg{DispNum});    # int()で小数点以下は切り捨て
            $amari = $ttlcnt % $cfg{DispNum};            # 余りの算出
            if ($amari > 0) { $lastpage++ }              # あまりがあったら+1
            my $ttl = $lastpage;                         # 下のページ数表示用に値取得
            $lastpage--;                                 # でもページは0から始まってるので-1（なんか間抜け）
            # ページ数表示
            my $here = $page + 1;
            $entry_page .= "$here/$ttl";

            # 引数用ページ数計算
            my $nextpage = $page + 1;
            my $prevpage = $page - 1;

            # 次、前、最初
            # 次
            if ($rowid < $ttlcnt) {
                $template->param(ENTRY_INDEX_NAVI_NEXT => 1);
                my $href = &make_href("", 0, $nextpage, 0, 0);
                $template->param(ENTRY_INDEX_NAVI_NEXT_URL => $href);
                $template->param(ENTRY_INDEX_NAVI_NEXT_COUNT => 
                    ($page == $lastpage - 1 && $amari > 0) ? $amari : $cfg{DispNum}
                );
            } else {
                $template->param(ENTRY_INDEX_NAVI_NEXT => 0);
            }
            # 前
            $rowid = $rowid - $rowcnt;
            if ($rowid > 0) {
                $template->param(ENTRY_INDEX_NAVI_PREV => 1);
                my $href = &make_href("", 0, $prevpage, 0, 0);
                $template->param(ENTRY_INDEX_NAVI_PREV_URL => $href);
                $template->param(ENTRY_INDEX_NAVI_PREV_COUNT => $cfg{DispNum});
            } else {
                $template->param(ENTRY_INDEX_NAVI_PREV => 0);
            }
            # 最初
            if ($page > 1) {
                $template->param(ENTRY_INDEX_NAVI_BEGIN => 1);
                my $href = &make_href("", 0, 0, 0, 0);
                $template->param(ENTRY_INDEX_NAVI_BEGIN_URL => $href);
                $template->param(ENTRY_INDEX_NAVI_BEGIN_COUNT => $cfg{DispNum});
            } else {
                $template->param(ENTRY_INDEX_NAVI_BEGIN => 0);
            }
            # 「最後」リンクの表示判定
            if ($page < $lastpage - 1) {
                $template->param(ENTRY_INDEX_NAVI_LAST => 1);
                my $href = &make_href("", 0, $lastpage, 0, 0);
                $template->param(ENTRY_INDEX_NAVI_LAST_URL => $href);
                $template->param(ENTRY_INDEX_NAVI_LAST_COUNT => ($amari > 0) ? $amari : $cfg{DispNum});
            } else {
                $template->param(ENTRY_INDEX_NAVI_LAST => 0);
            }
            if ($rowid < $ttlcnt ||
                $rowid > 0 ||
                $page > 1 ||
                $page < $lastpage - 1) {
                $template->param(ENTRY_INDEX_NAVI => 1);
            } else {
                $template->param(ENTRY_INDEX_NAVI => 0);
            }
        } else {
            $entry_page .= "1/1";
            $template->param(ENTRY_INDEX_NAVI => 0);
        }
    }

    # fill in some parameters
    $template->param(BLOG_LOGO => &index_title_logo);
    $template->param(BLOG_DESCRIPTION => &index_blog_description);
    $template->param(CATEGORY_SELECTOR => &index_category_selector);
    $template->param(ENTRIES => \@entry_index);
    $template->param(ENTRY_PAGE => MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, MT4i::Enc::decode_utf8($entry_page)));
    $template->param(LINK_RECENT_COMMENT => &index_link_recent_comment);
    $template->param(ADMIN_MENU => &index_admin_menu);
    $template->param(ADMIN_INFO => &index_admin_info);
    $template->param(TOP => $page == 0 ? 1 : 0 );
    $template->param(HOME => $page == 0 && !$cat ? 1 : 0 );
    $template->param(CELLPHONE => ($ua eq "i-mode" || $ua eq "ezweb" || $ua eq "j-sky") ? 1 : 0 );

    # Common
    $template = _tmpl_common($template);

    # キャッシュへ出力
    if ((!$cfg{CachePageCountIndex} || $page < $cfg{CachePageCountIndex}) && $admin_mode eq 'no') {
        my $ccat = ($cat) ? 'c'.$cat : 'c0' ;
        _writecache('b'.$blog_id.'/idx'.$ccat.'/p'.$page.$ua, $template);
    }

    # Output
    &_cacheout($template);
}

# ----- Top logo -----
sub index_title_logo {
    my $str;
    if (( $ua eq 'i-mode' && $cfg{Logo_i} ) || ( $ua ne 'i-mode' && $cfg{Logo_o} )) {
        $str = ($ua eq 'i-mode') ? "<img src=\"$cfg{Logo_i}\" alt=\"$blog_name\" />"
                                 : "<img src=\"$cfg{Logo_o}\" alt=\"$blog_name\" />" ;
    } else {
        $str = $blog_name;
    }
    return MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, _conv_utf8_z2h($str));
}

# ----- カテゴリセレクタ -----
sub index_category_selector {
    my $str;
    $str .= "<form action=\"$cfg{MyName}\">";
    if ($key){
        $str .= "<input type=hidden name=\"key\" value=\"$key\" />";
    }
    $str .= "<select name=\"cat\">";
    $str .= "<option value=\"0\">すべて</option>";

    if ($cfg{Version} >= 3.11) {
        my @catlist = &get_catlist;
        for my $cat (@catlist) {
            $str .= $cat;
        }
    } else {
        my @cat_datas = ();
        require MT::Category;
        my @categories = MT::Category->load({blog_id => $blog_id},
                                                {unique => 1});

        for my $category (@categories) {
            # 管理者モードでない場合には非表示カテゴリを処理する
            if ($admin_mode ne "yes"){
                my @nondispcats = MT4i::Func::get_nondispcats();
                next if (first { $category->id == $_ } @nondispcats);
            }

            my $label;

            # カテゴリ名の日本語化を$MTCategoryDescriptionで表示している場合に
            # カテゴリセレクタの内容を置換する
            $label = _conv_utf8_z2h( ($cfg{CatDescReplace} eq "yes") ? $category->description : $category->label );
            my $cat_id = $category->id;
            require MT::Entry;
            require MT::Placement;
            ####################
            # 属するエントリが1以上のカテゴリのみ列挙
            my %terms = (blog_id => $blog_id);
            # 管理者モードでなければステータスが'公開'のエントリのみカウント
            if ($admin_mode ne "yes"){
                $terms{'status'} = 2;
            }
            my $count = MT::Entry->count( \%terms,
                                        { join => [ 'MT::Placement', 'entry_id',
                                        { blog_id => $blog_id, category_id => $cat_id } ] });
            if ($count > 0) {
                if ($cat != 0 && $cat_id == $cat) {
                    @cat_datas = (@cat_datas,"$cat_id,$label,$count");
                } else {
                    @cat_datas = (@cat_datas,"$cat_id,$label,$count");
                }
            }
        }

        if ($cfg{CatDescSort} eq "asc"){
            @cat_datas = sort { (split(/\,/,$a))[1] cmp (split(/\,/,$b))[1] } @cat_datas;
        }elsif ($cfg{CatDescSort} eq "desc"){
            @cat_datas = reverse sort { (split(/\,/,$a))[1] cmp (split(/\,/,$b))[1] } @cat_datas;
        }

        for my $cat_data (@cat_datas) {
            my @cd_tmp = split(",", $cat_data);

            my $tmpdata = "$cd_tmp[1]($cd_tmp[2])";
            # 指定文字数でぶった切り
            if ($cfg{LenCutCat} > 0) {
                if (MT4i::Enc::lenb_sjis($tmpdata) > $cfg{LenCutCat}) {
                    $tmpdata = MT4i::Enc::substrb_sjis($cd_tmp[1], 0, $cfg{LenCutCat}-MT4i::Enc::lenb_sjis($cd_tmp[2])-2).'('.$cd_tmp[2].')';
                }
            }
            $str = ($cat == $cd_tmp[0])
                ? "<option value=$cd_tmp[0] selected>$tmpdata</option>"
                : "<option value=$cd_tmp[0]>$tmpdata</option>" ;
        }
    }
    $str .= "</select>";
    $str .= "<input type=\"hidden\" name=\"id\" value=\"$blog_id\" />";
    $str .= "<input type=\"submit\" value=\"選択\" /></form>";

    return MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, $str);
}

# ----- 概要 -----
sub index_blog_description {
    my $str;
    if ($description) {
        my $tmp_data .= "$description";
        #単なる改行を<br />タグに置換
        #(「ウェブログの説明」に改行が混ざるとauで表示されない不具合への対処)
        $tmp_data=~s/\r\n/<br \/>/g;
        $tmp_data=~s/\r/<br \/>/g;
        $tmp_data=~s/\n/<br \/>/g;
        $str .= $tmp_data;
    }
    return MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, _conv_utf8_z2h($str));
}

# ----- 最近のコメント一覧へのリンク -----
sub index_link_recent_comment {
    require MT::Comment;
    my $str;
    my $blog_comment_cnt = MT::Comment->count({ blog_id => $blog_id });
    if ($blog_comment_cnt) {
        my $href = &make_href("recentcomment", 0, 0, 0, 0);
        $str .= "<a href=\"$href\">最近のｺﾒﾝﾄ$cfg{RecentComment}件</a>";
    }
    return MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, $str);
}

# ----- 管理者用メニュー -----
sub index_admin_menu {
    my $str;
    $str .= "<form method=\"POST\" action=\"$cfg{MyName}\">";
    $str .= "<input type=\"submit\" value=\"[管]Entryの新規作成\" />";
    $str .= "<input type=\"hidden\" name=\"id\" value=\"$blog_id\" />";
    $str .= "<input type=\"hidden\" name=\"mode\" value=\"entryform\" />";
    $str .= "<input type=\"hidden\" name=\"key\" value=\"$key\" />";
    $str .= "</form>";

    $str .= "<form method=\"POST\" action=\"$cfg{MyName}\">";
    $str .=  ($email_new_comments)
        ? "<input type=\"submit\" value=\"[管]ｺﾒﾝﾄのﾒｰﾙ通知を停止する\" />"
        : "<input type=\"submit\" value=\"[管]ｺﾒﾝﾄのﾒｰﾙ通知を再開する\" />";
    $str .= "<input type=\"hidden\" name=\"id\" value=\"$blog_id\" />";
    $str .= "<input type=\"hidden\" name=\"mode\" value=\"email_comments\" />";
    $str .= "<input type=\"hidden\" name=\"key\" value=\"$key\" />";
    $str .= "</form>";
    return MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, $str);
}

sub index_admin_info {
    # 管理人情報
    my $str;
    if (exists $cfg{AdmNM}) {
        $str .= "管理人:";
        if (exists $cfg{AdmML}) {
            $cfg{AdmML} =~ s/\@/\&#64;/g;
            $cfg{AdmML} =~ s/\./\&#46;/g;
            $str .= "<a href=\"mailto:$cfg{AdmML}\">".MT4i::Enc::decode_utf8($cfg{AdmNM})."</a>";
        } else {
            $str .= MT4i::Enc::decode_utf8("$cfg{AdmNM}");
        }
    }
    return MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, $str);
}

#----------------------------------------------------------------------------------------------------

########################################
# Sub Individual - 単記事ページの描画
########################################

sub individual {
    # 携帯電話からのアクセスかつアクセスキー有効の場合は$cfg{DispNum}を6以下にする
    if ($cfg{AccessKey} eq "yes" && ($ua eq "i-mode" || $ua eq "j-sky" || $ua eq "ezweb")) {
        if ($cfg{DispNum} > 6) {
            $cfg{DispNum} = 6;
        }
    }

    # キャッシュを読む
    my $template;
    if ($admin_mode eq 'no') {
        my $ccat = ($cat) ? 'c'.$cat : 'c0' ;
        my $csprtpage = ($sprtpage) ? $sprtpage : '0' ;
        $template = _readcache('b'.$blog_id.'/e'.$eid.'/'.$ccat.'/p'.$csprtpage.$ua, 1);
    }

    my $ent_allow_comments;
    my $entry;
    my $rowid;

    unless ($template) {
        # Get MT Object etc.
        &_get_mt_object();

        ####################
        # 記事の取得
        $entry = _get_entry($eid);

        # 検索結果が0件の場合はメッセージ表示してSTOP（有り得ないけどな）
        if (!$entry) {
            my $cgi = new CGI;
            $cgi->charset('utf-8');
            &errout('Entry ID "'.$cgi->escapeHTML($eid).'" is wrong.');
        }

        # HTMLテンプレートをオープン
        $template = _tmpl_open('individual.tmpl');

        # URL argument "no" is abolished...
        if (($template->query(name => 'BACK_URL') eq 'VAR') ||
            ($template->query(name => 'ENTRY_NO') eq 'VAR') ||
            ($template->query(name => 'PAGE') eq 'VAR')) {
            if ($no) {
                $rowid = $no;
                $no--;
            } else {
                $no = 0;
                my $ttlcnt = &get_ttlcnt;
                FOUND: while ($ttlcnt > 0) {
                    my @entries = &get_entries($no, $cfg{DispNum});
                    if (@entries <= 0) {
                        last;
                    }
                    for my $entry (@entries) {
                        $no++;
                        if ($entry->id == $eid) {
                            last FOUND;
                        }
                    }
                    $ttlcnt -= $cfg{DispNum};
                }
                $rowid = $no;
                $no--;
            }
        }

        # 結果をテンプレートに埋め込む
        $template->param(ENTRY_ID => $entry->id);
        $template->param(ENTRY_CREATED_ON => MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, MT4i::Enc::decode_utf8(
                                             MT::Util::format_ts($cfg{IndividualDtFormat},
                                                 $cfg{Version} >= 4.0 ? $entry->authored_on
                                                                              : $entry->created_on, undef, $cfg{DtLang}))));

        # 結果を変数に格納
        my $text = _conv_utf8_z2h(MT->apply_text_filters($entry->text, $entry->text_filters));
        my $text_more = _conv_utf8_z2h(MT->apply_text_filters($entry->text_more, $entry->text_filters));

        # コメント投稿機能が強制OFFされている場合はallow_commentsをClosedに
        $ent_allow_comments = ($cfg{ArrowComments} == 1) ? $entry->allow_comments : 2 ;
        my $ent_status = $entry->status;

        # This entry is not displayed
        # if status is in draft and mode is admin mode.
        if ($ent_status == 1 && $admin_mode eq 'no') {
            &errout('Permission denied.');
        }

        # 本文と追記を一つにまとめる
        if($text_more){
            $text = "<p>$text</p><p>$text_more</p>";
        }

        ####################
        # リンクのURLをchtmltrans経由に変換
        $text = &conv_redirect($text, 0, $eid);

        ####################
        # 画像の除去（退避）

        my $href;

        # Convert emoticon img to tag
        $text = _conv_emoticon2tag($text);

        # convert img tag to link or other
        my $tmptext = $text;
        $text = '';
        while ($tmptext =~ /(<img [^>]*>)/i) {
            my $left   = $`;
            my $middle = $1;
            my $right  = $';

            # get attributes
            my $class = $1 if ($middle =~ /class=["']([^"'>]*)["']/);
            my $alt = $1 if ($middle =~ /alt=["']([^"'>]*)["']/);
            my $src = ($left  =~ /<a [^>]*href=["']([^"'>]*\.(?:jpg|jpeg|gif|png))["'][^>]*>\Z/)
                ? $1
                : ($middle =~ /src=["']([^"'>]*)["']/)
                    ? $1
                    : '' ;

            unless ($class =~ /emoticon .*/ || $alt =~ /icon:.*/) {
                # remove a tag
                $left  =~ s/<a [^>]*>\Z//;
                $right =~ s/\A<\/a>//;

                # create href string
                $href = _conv_url2resizer($src);

                # create caption string
                my $caption;
                if ($cfg{UseThumbnail}) {
                    $src = MT4i::Func::url_encode($src);
                    my $bid_str = ($blog_id != $cfg{Blog_ID}) ? "id=$blog_id&amp;" : '' ;
                    my $cgi = new CGI;
                    $cgi->charset('utf-8');
                    $caption = "<img src=\"./$cfg{MyName}?mode=thumbnail&amp;".$bid_str."img="
                                      .$cgi->escapeHTML($src)."\" alt=\"$alt\" />";
                } else {
                    my $gazou = '画像：';
                    $caption = $alt ? $gazou.$alt : $gazou ;
                }
                $middle = '<a href="'.$href.'">'.$caption.'</a>';
                $middle = '&lt;'.$middle.'&gt;' unless ($cfg{UseThumbnail});
            }
            $text .= $left . $middle;
            $tmptext = $right;
        }
        $text .= $tmptext;

        ####################
        # Convert tags etc.
        if($entry->convert_breaks eq '__default__' || ($entry->convert_breaks ne '__default__' && $entry->convert_breaks ne '0' && $convert_paras eq '__default__')) {
            # Change the color of bq tag
            if ($cfg{BqColor}) {
                if ($cfg{ContentType} eq 'xhtml') {
                    $text=~s/<blockquote>/<blockquote style="color: $cfg{BqColor}">/ig;
                } else {
                    $text=~s/<blockquote>/<blockquote><font color="$cfg{BqColor}">/ig;
                    $text=~s/<\/blockquote>/<\/font><\/blockquote>/ig;
                }
            }
            # Convert bq tag to p tag
            if ($cfg{BQ2P} eq "yes") {
                $text=~s/<blockquote>/<p>/ig;
                $text=~s/<\/blockquote>/<\/p>/ig;
            } else {
                # bqタグ周りの余計なbrタグ除去
                $text=~s/<br \/><br \/><blockquote>/<blockquote>/ig;
                $text=~s/<br \/><blockquote>/<blockquote>/ig;
                $text=~s/<\/blockquote><br \/><br \/>/<\/blockquote>/ig;
                $text=~s/<p><blockquote>/<blockquote>/ig;
                $text=~s/<\/blockquote><\/p>/<\/blockquote>/ig;
            }
            # pタグ周りの余計なbrタグ除去
            $text=~s/<br \/><br \/><p>/<p>/ig;
            $text=~s/<br \/><p>/<p>/ig;
            $text=~s/<\/p><br \/><br \/>/<\/p>/ig;
            $text=~s/<br \/><\/p>/<\/p>/ig;
            # ulタグ周りの余計なbrタグ除去
            $text=~s/<br \/><br \/><ul>/<ul>/ig;
            $text=~s/<br \/><ul>/<ul>/ig;
            $text=~s/<ul><br \/>/<ul>/ig;
            $text=~s/<\/ul><br \/><br \/>/<\/ul>/ig;
            # olタグ周りの余計なbrタグ除去
            $text=~s/<br \/><br \/><ol>/<ol>/ig;
            $text=~s/<br \/><ol>/<ol>/ig;
            $text=~s/<ol><br \/>/<ol>/ig;
            $text=~s/<\/ol><br \/><br \/>/<\/ol>/ig;
            # li閉じタグ除去
            $text=~s/<\/li>//ig;
        }

        ####################
        # 本文分割処理
        if (MT4i::Enc::lenb_sjis($text) > $cfg{SprtLimit}) {
            $text = &separate($text, 0);

            # ページリンク
            my $href = &make_href($mode, 0, 0, $eid, 0);
            my @argsprtbyte = split(/,/, $sprtbyte);
            my @page_navi = ();
            for (my $i = 1; $i <= $#argsprtbyte + 1; $i++)  {
                my %row_data;

                $row_data{PAGE_NAVI_NO} = $i;
                $row_data{PAGE_NAVI_URL} = ($i == $sprtpage)
                    ? '' : "$href&amp;sprtpage=$i&amp;sprtbyte=$sprtbyte";

                push @page_navi, \%row_data;
            }
            $template->param(PAGE_NAVI => \@page_navi);
        }

        # text
        $text = MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, $text);

        # Convert emoticon tag to binary
        $text = _conv_tag2binary($text);
        $template->param(ENTRY_TEXT => $text);

        # 記事一覧からの閲覧なら記事番号を振る
        if ($mode eq 'individual') {
            $template->param(ENTRY_NO => "$rowid.");
        }

        # 下書き／指定日かどうかを調べる
        my $d_f;
        if ($ent_status == 1) {
            $d_f = '(下書き)';
        } elsif ($ent_status == 3) {
            $d_f = '(指定日)';
        }
        # Convert emoticon to binary in entry_title
        my $title = MT4i::Enc::decode_utf8($d_f)._conv_emoticon2tag(_conv_utf8_z2h($entry->title));
        $title = MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, $title);
        $title = _conv_tag2binary($title);
        $template->param(ENTRY_TITLE => $title);
        $template->param(ENTRY_URL_ENCODE_TITLE => MT4i::Func::url_encode($title));

        # カテゴリ名の表示
        my $cat_label = &check_category($entry);
        if ($cat_label) {
            $template->param(CATEGORY => 1);
            $template->param(CATEGORY_LABEL => MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, $cat_label));
        }

        # Authorのnicknameがあれば、それを表示。無ければnameを表示する
        require MT::Author;
        my $author = MT::Author->load({ id => $entry->author_id });
        my $author_name;

        if ($author){
            $author_name = ($author->nickname)
                ? _conv_utf8_z2h($author->nickname) : $author->name;
            $template->param(ENTRY_AUTHOR_NAME => MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, $author_name));
        }

        # Original URL
        my $entry_original_url = $entry->archive_url("Individual");
        $template->param(ENTRY_ORIGINAL_URL => $entry_original_url);
        $template->param(ENTRY_URL_ENCODE_ORIGINAL_URL => MT4i::Func::url_encode($entry_original_url));

        # Trackback
        if ($entry->ping_count > 0) {
                $template->param(TRACKBACK => 1);
                my $href = &make_href("trackback", 0, 0, $eid);
                $template->param(TBPING_URL => $href);
                $template->param(TBPING_COUNT => $entry->ping_count);
        }
    
        # 管理者のみ「Entry編集・消去」が可能
        if ($admin_mode eq "yes"){
            my $admin_menu;
            $admin_menu .= "<form method=\"POST\" action=\"$cfg{MyName}\">";
            $admin_menu .= "<input type=\"submit\" value=\"[管]このEntryを編集\" />";
            $admin_menu .= "<input type=\"hidden\" name=\"id\" value=\"$blog_id\" />";
            $admin_menu .= "<input type=\"hidden\" name=\"mode\" value=\"entryform\" />";
            $admin_menu .= "<input type=\"hidden\" name=\"eid\" value=\"$eid\" />";
            $admin_menu .= "<input type=\"hidden\" name=\"key\" value=\"$key\" />";
            $admin_menu .= "</form>";
            $admin_menu .= "<form method=\"POST\" action=\"$cfg{MyName}\">";
            $admin_menu .= "<input type=\"submit\" value=\"[管]このEntryを削除\" />";
            $admin_menu .= "<input type=\"hidden\" name=\"id\" value=\"$blog_id\" />";
            $admin_menu .= "<input type=\"hidden\" name=\"mode\" value=\"confirm_entry_del\" />";
            $admin_menu .= "<input type=\"hidden\" name=\"eid\" value=\"$eid\" />";
            $admin_menu .= "<input type=\"hidden\" name=\"key\" value=\"$key\" />";
            $admin_menu .= "</form>";
            $template->param(ADMIN_MENU => MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, MT4i::Enc::decode_utf8($admin_menu)));
        }

        #####################
        # Noneでは投稿も表示も無し、Openなら両方OK、Closedは表示のみ
        # $ent_allow_comments, None = 0, Open = 1, Closed = 2 ('Closed' is only in less than v3.2)
        # MT3.2以降では Closed=2 が廃止された模様なので対応 2006/06/21
        if ( ($ent_allow_comments > 0
                || ($ent_allow_comments == 0 && $cfg{Version} >= 3.2) )
                        && $mode ne 'ainori' && $mode ne 'comment_lnk') {
            $template->param(ALLOW_COMMENT => 1);
            my $link_header;
            if ($entry->comment_count > 0) {
                $link_header = 'comment';
            } elsif ($ent_allow_comments == 1) {
                $link_header = 'comment_form';
            }
            my $href;
            if ($mode eq 'individual') {
                $href = &make_href($link_header, 0, 0, $eid, 0);
            } elsif ($mode eq 'individual_rcm') {
                $href = &make_href($link_header.'_rcm', 0, 0, $eid, 0);
            } elsif ($mode eq 'individual_lnk') {
                $href = &make_href($link_header.'_lnk', 0, 0, $eid, $ref_eid);
            }
            $template->param(COMMENT_URL => $href);
            $template->param(COMMENT_COUNT => $entry->comment_count);
        }
        if ($ent_allow_comments == 0 && $cfg{Version} < 3.2) {
            $template->param(DISP_COMMENT => 0);
            $template->param(POST_COMMENT => 0);
        } elsif ($ent_allow_comments == 1) {
            $template->param(DISP_COMMENT => 1);
            $template->param(POST_COMMENT => 1);
        } elsif ($ent_allow_comments == 2 || ($ent_allow_comments == 0 && $cfg{Version} >= 3.2)) {
            $template->param(DISP_COMMENT => 1);
            $template->param(POST_COMMENT => 0);
        }

        if ($mode eq 'individual') {
            # 総件数取得
            my $ttlcnt = &get_ttlcnt;

            # エントリー数表示
            $template->param(PAGE => "$rowid/$ttlcnt");

            # 引数用エントリーID算出（prevとnextが引っ繰り返っているので注意）
            my $nextid;
            my $previd;
            my $next;
            my $prev;
            unless ($cat) {
                $next = $entry->previous(1);
                $prev = $entry->next(1);
            } else {
                $next = _neighbor_entry($entry, $cat, 'prev');
                $prev = _neighbor_entry($entry, $cat, 'next');
            }
            if ($cfg{NonDispCat}) {
                # 非表示カテゴリが指定されている場合
                # 非表示カテゴリのリストをサブカテゴリも含めて取得する
                my @nondispcats = MT4i::Func::get_nondispcats();

                # ぐるぐる回して非表示カテゴリと突合せ
                while ($next) {
                    # エントリのカテゴリ取得
                    my @places = MT::Placement->load({ entry_id => $next->id });
                    if (@places) {
                        my $match = 0;
                        foreach my $place (@places) {
                            $match++
                                if (first { $place->category_id == $_ } @nondispcats);
                        }
                        if ($match < @places) {
                            last;
                        } else {
                            unless ($cat) {
                                $next = $next->previous(1);
                            } else {
                                $next = _neighbor_entry($entry, $cat, 'prev');
                            }
                        }
                    } else {
                        last;
                    }
                }
                while ($prev) {
                    # エントリのカテゴリ取得
                    my @places = MT::Placement->load({ entry_id => $prev->id });
                    if (@places) {
                        my $match = 0;
                        foreach my $place (@places) {
                            $match++
                                if (first { $place->category_id == $_ } @nondispcats);
                        }
                        if ($match < @places) {
                            last;
                        } else {
                            unless ($cat) {
                                $prev = $prev->next(1);
                            } else {
                                $prev = _neighbor_entry($entry, $cat, 'next');
                            }
                        }
                    } else {
                        last;
                    }
                }
            }
            if($next) {
                $nextid = $next->id;
                $template->param(NEXT => 1);
                my $href = &make_href("individual", 0, 0, $nextid, 0);
                $template->param(NEXT_URL => $href);
            }
            if($prev) {
                $previd = $prev->id;
                $template->param(PREV => 1);
                my $href = &make_href("individual", 0, 0, $previd, 0);
                $template->param(PREV_URL => $href);
            }
        }

        # TrackbackURL
        require MT::Template::Context;
        my $ctx = MT::Template::Context->new;
        if ($cfg{Version} >= 5.0) {
            if (my $tb = $entry->trackback) {
                my $cfg = $ctx->{config};
                $template->param(TRACKBACK_URL => _get_cgipath() . $cfg->TrackbackScript . '/' . $tb->id);
            }
        } else {
            $ctx->stash( 'blog', $blog);
            $ctx->stash( 'entry', $entry );
            $template->param(TRACKBACK_URL => $ctx->_hdlr_entry_tb_link);
        }

        # Customfields
        if ($cfg{Version} >= 4.1) {
            my $cfs = _get_customfields($entry);
            for my $cf (keys %$cfs) {
                $template->param('ENTRY_'.$cf => MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, MT4i::Enc::decode_utf8($cfs->{$cf})));
            }
        }

        # Keywords
        my $keywords = _conv_emoticon2tag(_conv_utf8_z2h($entry->keywords));
        $keywords = MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, $keywords);
        $keywords = _conv_tag2binary($keywords);
        $template->param('ENTRY_KEYWORDS' => $keywords);

        #Tags
        my @tag_hash;
        my @tags = $entry->tags;
        foreach my $tag (@tags) { # 結果のフェッチと表示
            my %tag_data;
            $tag = _conv_emoticon2tag(_conv_utf8_z2h($tag));
            $tag = MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, $tag);
            $tag_data{ENTRY_TAG} = _conv_tag2binary($tag);
            push(@tag_hash, \%tag_data);
        }
        $template->param('ENTRY_TAGS' => \@tag_hash);

        # Common
        $template = _tmpl_common($template);

        # キャッシュ
        if ($admin_mode eq 'no') {
            my $ccat = ($cat) ? 'c'.$cat : 'c0' ;
            my $csprtpage = ($sprtpage) ? $sprtpage : '0' ;
            _writecache('b'.$blog_id.'/e'.$eid.'/'.$ccat.'/p'.$csprtpage.$ua, $template);
        }
    } else {
        require Encode;
    }

    ####################
    # mode に絡む処理

    # コメント投稿＆表示制御
    if ($mode eq 'ainori' || $mode eq 'comment_lnk') {
        $template->param(DISP_COMMENT => 0);
        $template->param(POST_COMMENT => 0);
    }

    # URL argument "no" is abolished...
    if ($template->query(name => 'BACK_URL') eq 'VAR') {
        if ($mode eq 'individual') {
                # ページ数算出
                $page = int($no / $cfg{DispNum});    # int()で小数点以下は切り捨て

                my $href = &make_href("", 0, $page, 0, 0);
                $template->param(BACK_URL => $href);
                $template->param(BACK_STRING => MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, '一覧へ戻る'));
        } elsif ($mode eq 'individual_rcm') {
            # 最近コメント一覧からの閲覧
            my $href = &make_href("recentcomment", 0, 0, 0, 0);
            $template->param(BACK_URL => $href);
            $template->param(BACK_STRING => MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, '最近ｺﾒﾝﾄ一覧へ戻る'));
        } elsif ($mode eq 'individual_lnk') {
            # 記事中リンクからの閲覧
            my $href = &make_href("individual", 0, 0, $ref_eid, 0);
            $template->param(BACK_URL => $href);
            $template->param(BACK_STRING => MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, 'ﾘﾝｸ元の記事へ戻る'));
        } elsif ($mode eq 'ainori') {
            # あいのり時はリファラへ戻る
            if ($q->param("search")) {
                my $keyword = $q->param("search_keyword");
                my $offset = $q->param("offset") || 0;
                my $limit = $q->param("limit") || 5;

                my $url = &make_href("", 0, $page, 0, 0);
                my $encode_keywords_shiftjis
                    .= MT4i::Func::url_encode(MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, MT4i::Enc::decode_utf8($keyword)));
                $url .= '&id='.$blog_id if $blog_id;
                $url .= '&search_keyword='.$encode_keywords_shiftjis;
                $url .= '&offset='.$offset if $offset;
                $url .= '&limit='.$limit if $limit;
                $url .= '&mode=search';
                $template->param(BACK_URL => $url);
            } else {
                my $href = $ENV{'HTTP_REFERER'};
                $template->param(BACK_URL => $href);
            }
            $template->param(BACK_STRING => MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, 'ﾘﾝｸ元へ戻る'));
        }
    } else {
        my $href = &make_href("", 0, 0, 0, 0);
        $template->param(TOP_URL => $href);
    }

    # Output
    &_cacheout($template);
}

########################################
# Sub Comment - コメント描画
########################################

sub comment {
    my $rowid = $no;

    # キャッシュを読む
    if ($admin_mode eq 'no') {
        my $cpage = $page ? $page : '0' ;
        my $template = _readcache('b'.$blog_id.'/e'.$eid.'/ccp'.$cpage.$ua, 1);
        &_cacheout($template) if $template;
    }

    # Get MT Object etc.
    &_get_mt_object();

    # HTMLテンプレートをオープン
    my $template = _tmpl_open('comment.tmpl');

    ####################
    # Entry の取得
    my $entry = _get_entry($eid);

    # 検索結果が0件の場合はメッセージ表示してSTOP（有り得ないけどな）
    if ($entry <= 0) {
        my $cgi = new CGI;
        $cgi->charset('utf-8');
        &errout('Entry ID "'.$cgi->escapeHTML($eid).'" is wrong.');
    }

    # 結果を変数に格納
    $template->param(ENTRY_TITLE => _conv_emoticon2binary($entry->title));
    $template->param(ENTRY_CREATED_ON =>
        MT4i::Enc::encode_emoji_sjis(
            $ejpemoji, $enc_emoji_sjis, MT4i::Enc::decode_utf8( 
                                         MT::Util::format_ts($cfg{IndividualDtFormat},
                                             $cfg{Version} >= 4.0 ? $entry->authored_on
                                                                  : $entry->created_on, undef, $cfg{DtLang}))));
    my $ent_id = $entry->id;
    my $ent_status = $entry->status;

    ####################
    # コメントの取得
    my @coms;
    # 管理者モードではコメントを逆順表示する
    my $offset = $page ? $page * $cfg{'CommentNum'} : 0 ;
    if ($admin_mode eq "yes"){
        @coms = get_comments($ent_id, $cfg{'CommentNum'}, $offset, 'descend', 1);
    }else{
        @coms = get_comments($ent_id, $cfg{'CommentNum'}, $offset, $sort_order_comments, 1);
    }

    # Set comments params
    my @comments = ();
    my $odd = 1;
    for my $comment (@coms) {
        my %row_data;

        $row_data{COMMENT_AUTHOR} = _conv_emoticon2binary($comment->author);
        $row_data{COMMENT_EMAIL} = $comment->email;
        $row_data{COMMENT_URL} = $comment->url;

        my $comment_text = _conv_emoticon2tag($comment->text); # Convert emoticon img to tag
        $comment_text = $convert_paras_comments ?
            MT->apply_text_filters($comment_text, $blog->comment_text_filters) :
            $comment_text;
        $comment_text = _conv_utf8_z2h($comment_text);
        $comment_text = &conv_redirect($comment_text, $rowid, $eid);
        $comment_text =~ s/_ahref/a href/g;
        $comment_text = MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, $comment_text);
        $comment_text = _conv_tag2binary($comment_text); # Convert emoticon tag to binary
        $row_data{COMMENT_TEXT} = $comment_text;

        $row_data{COMMENT_CREATED_ON} =
            MT::Util::format_ts($cfg{CommentDtFormat}, $comment->created_on, undef, $cfg{DtLang});

        # Judge odd or even
        $row_data{COMMENT_ODD}  =  $odd;
        $row_data{COMMENT_EVEN} = !$odd;
        $odd                    = !$odd;

        # Admin
        if ($admin_mode eq "yes"){
            my $str;
            $str .= "<form method=\"POST\" action=\"$cfg{MyName}\">";
            $str .= "<input type=\"submit\" value=\"[管]このｺﾒﾝﾄを削除\" />";
            $str .= "<input type=\"hidden\" name=\"id\" value=\"$blog_id\" />";
            $str .= "<input type=\"hidden\" name=\"mode\" value=\"confirm_comment_del\" />";
            $str .= "<input type=\"hidden\" name=\"no\" value=\"$rowid\" />";
            $str .= "<input type=\"hidden\" name=\"page\" value=\"".$comment->id."\" />";
            $str .= "<input type=\"hidden\" name=\"eid\" value=\"$eid\" />";
            $str .= "<input type=\"hidden\" name=\"key\" value=\"$key\" />";
            $str .= "</form>";
            $row_data{COMMENT_DEL_BTN} = MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, $str);
        }

        push(@comments, \%row_data);
    }
    $template->param(COMMENTS => \@comments);

    # Comment page navi
    my $comment_cnt = MT::Comment->count({ entry_id => $ent_id });
    if ($comment_cnt > $cfg{'CommentNum'}) {
        my $page_num = ($comment_cnt / $cfg{'CommentNum'});
        $page_num += 1 if ($comment_cnt % $cfg{'CommentNum'});
        my $cpage = $page ? $page + 1 : '1' ;

        my @page_navi = ();
        for (my $i = 1; $i <= $page_num; $i++)  {
            my %row_data;

            $row_data{PAGE_NAVI_NO} = $i;
            if ($i != $cpage) {
                my $href = make_href($mode, $no, $i - 1, $ent_id, $ref_eid);
                $row_data{PAGE_NAVI_URL} = $href;
            }

            push(@page_navi, \%row_data);
        }
        $template->param(PAGE_NAVI => \@page_navi);
    }

    ####################
    # 表示文字列生成
    if ($rowid) {
        $template->param(ENTRY_ROW_NO => "$rowid.");
    }
    
    # コメント投稿機能が強制OFFされている場合はallow_commentsをClosedに
    my $ent_allow_comments;
    $ent_allow_comments = ($cfg{ArrowComments} == 1) ? $entry->allow_comments : 2 ;
    if ($ent_allow_comments == 1){
        if ($mode eq 'comment') {
            $template->param(ALLOW_COMMENT => 1);
            my $href = &make_href("comment_form", $rowid, 0, $eid, 0);
            $template->param(COMMENT_ENTRY_URL => $href);
        } elsif ($mode eq 'comment_rcm') {
            $template->param(ALLOW_COMMENT => 1);
            my $href = &make_href("comment_form_rcm", $rowid, 0, $eid, 0);
            $template->param(COMMENT_ENTRY_URL => $href);
        }
        # ※モード「comment_lnk」の時はコメント投稿できない。
        # ※参照目的なんだからコメント書くこと無いでしょ、たぶん。
    }
    my $href = &make_href("individual", $rowid, 0, $eid, 0);
    if ($mode eq 'comment') {
        $template->param(BACK_URL => $href);
        $template->param(BACK_TEXT => MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, '記事へ戻る'));
    } else {
        $template->param(REFERER => 1);
        if ($mode eq 'comment_rcm') {
            $href =~ s/individual/individual_rcm/ig;
        } elsif ($mode eq 'comment_lnk') {
            $href = &make_href("individual_lnk", $rowid, 0, $eid, $ref_eid);
        }
        $template->param(REFERER_URL => $href);
        if ($mode eq 'comment_rcm') {
            my $href = &make_href("recentcomment", 0, 0, 0, 0);
            $template->param(BACK_URL => $href);
            $template->param(BACK_TEXT => MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, '最近ｺﾒﾝﾄ一覧へ戻る'));
        } elsif ($mode eq 'comment_lnk') {
            my $href = &make_href("individual", $rowid, 0, $ref_eid, 0);
            $template->param(BACK_URL => $href);
            $template->param(BACK_TEXT => MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, 'ﾘﾝｸ元の記事へ戻る'));
        }
    }

    # Common
    $template = _tmpl_common($template);

    # キャッシュ＆画面出力
    if ($admin_mode eq 'no') {
        my $cpage = $page ? $page : '0' ;
        _writecache('b'.$blog_id.'/e'.$eid.'/ccp'.$cpage.$ua, $template);
    }

    # Output
    &_cacheout($template);
}

########################################
# Sub Recent_Comment - コメントまとめ読み
########################################

sub recent_comment {

    # キャッシュを読む
    if ($admin_mode eq 'no') {
        my $template = _readcache('b'.$blog_id.'/rc_'.$ua, 1);
        &_cacheout($template) if $template;
    }

    # Get MT Object etc.
    &_get_mt_object();

    ####################
    # コメントの取得
    my @comments = get_comments('', $cfg{RecentComment}, '', 'descend', 1);

    # HTMLテンプレートをオープン
    my $template = _tmpl_open('recent_comments.tmpl');

    my @recent_comments = ();
    for my $comment (@comments) {
        my %row_data;

        my $author = _conv_utf8_z2h($comment->author);
        $row_data{RECENT_COMMENT_AUTHOR} = MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, _conv_utf8_z2h($author));
        $row_data{RECENT_COMMENT_CREATED_ON} =
            MT::Util::format_ts($cfg{CommentDtFormat}, $comment->created_on, undef, $cfg{DtLang});

        my $eid = $comment->entry_id;
        my $entry = _get_entry($eid);
        my $title = _conv_utf8_z2h($entry->title);
        $row_data{RECENT_COMMENT_TITLE} = MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, _conv_utf8_z2h($title));
        $row_data{RECENT_COMMENT_URL} = &make_href("comment_rcm", 0, 0, $eid, 0);

        push(@recent_comments, \%row_data);
    }
    $template->param(RECENT_COMMENTS => \@recent_comments);
    $template->param(RECENT_COMMENTS_COUNT => $cfg{RecentComment});
    $template->param(BACK_URL => &make_href("", 0, 0, 0, 0));

    # Common
    $template = _tmpl_common($template);

    # キャッシュ＆画面出力
    if ($admin_mode eq 'no') {
        _writecache('b'.$blog_id.'/rc_'.$ua, $template);
    }

    # Output
    &_cacheout($template);
}

########################################
# Sub Trackback - トラックバック表示
########################################

sub trackback {

    my $rowid = $no;

    # キャッシュを読む
    if ($admin_mode eq 'no') {
        my $csprtpage = ($sprtpage) ? $sprtpage : '0' ;
        my $template = _readcache('b'.$blog_id.'/e'.$eid.'/tb'.$ua, 1);
        &_cacheout($template) if $template;
    }

    # Get MT Object etc.
    &_get_mt_object();

    # HTMLテンプレートをオープン
    my $template = _tmpl_open('trackback.tmpl');

    ####################
    # トラックバックの取得
    require MT::Trackback;
    my $tb = MT::Trackback->load(
            { blog_id => $blog_id , entry_id => $eid},
            { 'sort' => 'created_on',
              direction => 'descend',
              unique => 1,

              limit => 1 });

    my @tmp_tbpings;
    require MT::TBPing;
    if ($cfg{Version} >= 3.2) {
        @tmp_tbpings = MT::TBPing->load(
                { blog_id => $blog_id,
                  tb_id => $tb->id,
                  visible => 1,
                  junk_status => [ 0, 1 ] },
                { 'sort' => 'created_on',
                  direction => 'descend',
                  unique => 1,
                  limit => $cfg{RecentTB},
                  'range_incl' => { 'junk_status' => 1 } });
    } else {
        @tmp_tbpings = MT::TBPing->load(
                { blog_id => $blog_id,
                  tb_id => $tb->id },
                { 'sort' => 'created_on',
                  direction => 'descend',
                  unique => 1,
                  limit => $cfg{RecentTB} });
    }

    my $text;
    my @tbpings = ();
    for my $tbping (@tmp_tbpings) {
        my %row_data;  # 行データのための新しいハッシュを取得
        $row_data{TBPING_TITLE} = MT4i::Enc::encode_emoji_sjis(
            $ejpemoji, $enc_emoji_sjis, _conv_utf8_z2h($tbping->title));
        $row_data{TBPING_EXCERPT} = MT4i::Enc::encode_emoji_sjis(
            $ejpemoji, $enc_emoji_sjis, _conv_utf8_z2h($tbping->excerpt));
        $row_data{TBPING_BLOG_NAME} = MT4i::Enc::encode_emoji_sjis(
            $ejpemoji, $enc_emoji_sjis, _conv_utf8_z2h($tbping->blog_name));
        $row_data{TBPING_CREATED_ON} = MT4i::Enc::encode_emoji_sjis(
            $ejpemoji, $enc_emoji_sjis, MT4i::Enc::decode_utf8( 
                MT::Util::format_ts($cfg{TBPingDtFormat}, $tbping->created_on, undef, $cfg{DtLang})));
        $row_data{TBPING_SOURCEURL} = _conv_url_to_redirector($tbping->source_url, $rowid, $eid);
        $row_data{TBPING_ID} = $tbping->id;

        # 管理者のみ「トラックバック削除」等が可能
        if ($admin_mode eq "yes"){
            my $text;
            $text .= "<form method=\"POST\" action=\"$cfg{MyName}\">";
            $text .= "<input type=\"submit\" value=\"[管]このTBを削除\" />";
            $text .= "<input type=\"hidden\" name=\"id\" value=\"$blog_id\" />";
            $text .= "<input type=\"hidden\" name=\"mode\" value=\"confirm_trackback_del\" />";
            $text .= "<input type=\"hidden\" name=\"no\" value=\"$rowid\" />";
            $text .= "<input type=\"hidden\" name=\"page\" value=\"$row_data{TBPING_ID}\" />";
            $text .= "<input type=\"hidden\" name=\"eid\" value=\"$eid\" />";
            $text .= "<input type=\"hidden\" name=\"key\" value=\"$key\" />";
            $text .= "</form>";
            $row_data{TBPING_ADMIN_BUTTONS} = MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, MT4i::Enc::decode_utf8($text));
        }

        $row_data{TBPING_ICON_CLOCK} =
            ($cfg{AccessKey} eq "no"
                || ($cfg{AccessKey} eq "yes" && $ua ne "i-mode" && $ua ne "ezweb" && $ua ne "j-sky"))
                    ? '' : "$clock_icon" ;

        push(@tbpings, \%row_data);
    }

    $template->param(TBPINGS => \@tbpings);

    ####################
    # 表示文字列生成
    if (@tbpings < $cfg{RecentTB}){
        my $tb_count = @tbpings;
        $template->param(RECENT_TB_COUNT => $tb_count);
    }

    my $href = &make_href("individual", $rowid, 0, $eid);
    $template->param(BACK_URL => $href);
    if ($cfg{AccessKey} eq "no" || ($cfg{AccessKey} eq "yes" && $ua ne "i-mode" && $ua ne "ezweb" && $ua ne "j-sky")) {
        $template->param(ACCESS_KEY => '');
    } else {
        $template->param(ROW_NO => $nostr[0]);
        $template->param(ACCESS_KEY => $akstr[0]);
    }

    # Common
    $template = _tmpl_common($template);

    # キャッシュ＆画面出力
    if ($admin_mode eq 'no') {
        my $csprtpage = ($sprtpage) ? $sprtpage : '0' ;
        _writecache('b'.$blog_id.'/e'.$eid.'/tb'.$ua, $template);
    }

    # Output
    &_cacheout($template);
}

#############################################
# Sub Get_Entries - エントリの取得
# 第一引数 : オフセット
# 第二引数 : 取得個数
# 管理者の場合には、statusの限定解除
#############################################
sub get_entries {
    my @ent;
    require MT::Entry;

    my %terms = (blog_id => $blog_id);
    my %arg = (
            direction => 'descend',
            limit => $_[1],
            offset => $_[0],
    );
    $arg{'sort'} = $cfg{Version} >= 4.0 ? 'authored_on' : 'created_on';

    if ($cat != 0) {
        # カテゴリ指定あり
        $arg{'join'} = [ 'MT::Placement', 'entry_id',
                 { blog_id => $blog_id, category_id => $cat }, { unique => 1 } ];
    }

    if ($admin_mode eq "yes"){
        @ent = MT::Entry->load(\%terms, \%arg);
    } else {
        $terms{'status'} = 2;
        if ($cat == 0) {
            # カテゴリ指定なし
            if ($cfg{NonDispCat}) {
                # 非表示カテゴリ指定あり
                my %arg = (
                    direction => 'descend',
                );
                $arg{'sort'} = $cfg{Version} >= 4.0 ? 'authored_on' : 'created_on';
                my @entries = MT::Entry->load(\%terms, \%arg);

                # 非表示カテゴリのリストをサブカテゴリも含めて取得する
                my @nondispcats = MT4i::Func::get_nondispcats();

                my $count = 1;
                foreach my $entry (@entries) {
                    # エントリのカテゴリ取得
                    my @places = MT::Placement->load({ entry_id => $entry->id });
                    if (@places) {
                        my $match_cat = 0;
                        foreach my $place (@places) {
                            $match_cat++
                                if (first { $place->category_id == $_ } @nondispcats);
                        }
                        if ($match_cat < @places) {
                            if ($count > $_[0]) {
                                push @ent, $entry;
                            }
                            $count++;
                        }
                    } else {
                        # Non-Categoryは表示
                        if ($count > $_[0]) {
                            push @ent, $entry;
                        }
                        $count++;
                    }
                    if ($count == $_[1] + $_[0] + 1) {
                        last;
                    }
                }
            } else {
                # 非表示カテゴリ指定なし
                @ent = MT::Entry->load(\%terms, \%arg);
            }
        } else {
            # カテゴリ指定あり
            @ent = MT::Entry->load(\%terms, \%arg);
        }
    }

    return @ent;
}

#############################################
# Sub Get_Comments - コメントの取得
# arg1: entry ID
# arg2: limit
# arg3: offset
# arg4: sort ascend/descend
# arg5: check visible status 1:on or 0:off
#############################################
sub get_comments {
    my %terms;
    my %args;

    $terms{'blog_id'} = $blog_id;
    if ($_[0]) {
        $terms{'entry_id'} = $_[0];
    }
    if ($cfg{Version} >= 3.0 && $_[4] == 1) {
        $terms{'visible'} = 1;
    }

    $args{'sort'} = 'created_on';
    $args{'direction'} = $_[3];
    $args{'unique'} = 1;
    $args{'limit'} = ((!$_[0] || $cfg{NonDispCat}) && $_[1])
                         ? $_[1] * 10 # Limit for recent comment and non-display category specified.
                         : ($_[1] && !$cfg{NonDispCat}) ? $_[1] : '';
    $args{'offset'} = $_[2] if $_[2];
    my @comments;

    require MT::Comment;

    # Recent Comments or non-display category specified?
    if ($_[0] && !$cfg{NonDispCat}) {
        @comments = MT::Comment->load(\%terms, \%args);
    } else {
        # The status of Entry is confirmed at a recent comment.
        my $iter = MT::Comment->load_iter(\%terms, \%args);
        my %entries;
        my @nondispcats = MT4i::Func::get_nondispcats() if ($cfg{NonDispCat} || $admin_mode eq 'no');
        while (my $c = $iter->()) {
            my $e = $entries{$c->entry_id} ||= $c->entry;
            next unless $e;
            next if $e->status != MT::Entry::RELEASE();
            next unless ( ref $e eq 'MT::Entry' ); # comments to pages is excluded.

            # Is non-display category specified?
            if (!$cfg{NonDispCat} || $admin_mode eq 'yes') {
                push @comments, $c;
            } else {
                my @places = MT::Placement->load({ entry_id => $c->entry_id });
                if (@places) {
                    my $match_cat = 0;
                    foreach my $place (@places) {
                        $match_cat++
                            if (first { $place->category_id == $_ } @nondispcats);
                    }
                    if (@places > $match_cat) {
                        push @comments, $c;
                    }
                } else {
                    # Non-Category is displayed.
                    push @comments, $c;
                }
            }

            if ($_[1] && (scalar @comments == $_[1])) {
                $iter->('finish');
                last;
            }
        }
    }

    return @comments;
}

##############################################
# Sub Get_Ttlcnt - 記事総数の取得
##############################################
sub get_ttlcnt {
    require MT::Entry;
    require MT::Placement;
    my %terms;
    $terms{blog_id} = $blog_id;
    if ($admin_mode eq 'no') {
        $terms{status} = 2;
    }
    my %arg = (
            direction => 'descend',
            unique => 1,
    );
    $arg{'sort'} = $mt->version_number >= 4.0 ? 'authored_on' : 'created_on';
    if ($cat == 0) {
        #カテゴリなし
        if ($cfg{NonDispCat}) {
            # 非表示カテゴリ指定あり
            my @entries = MT::Entry->load(\%terms, \%arg);

            # 非表示カテゴリのリストをサブカテゴリも含めて取得する
            my @nondispcats = MT4i::Func::get_nondispcats();

            my @ent;
            foreach my $entry (@entries) {
                # エントリのカテゴリ取得
                my @places = MT::Placement->load({ entry_id => $entry->id });
                if (@places) {
                    my $match_cat = 0;
                    foreach my $place (@places) {
                        $match_cat++
                            if (first { $place->category_id == $_ } @nondispcats);
                    }
                    if ($match_cat < @places) {
                        push @ent, $entry;
                    }
                } else {
                    # Non-Categoryは表示
                    push @ent, $entry;
                }
            }
            return @ent;
        } else {
            # 非表示カテゴリの指定なし
            return MT::Entry->count(\%terms, \%arg);
        }
    } else {
        #カテゴリあり
        $arg{'join'} = [ 'MT::Placement', 'entry_id',
                 { blog_id => $blog_id, category_id => $cat }, { unique => 1 } ];
        return MT::Entry->count(\%terms, \%arg);
    }
}

##############################################
# Sub Make_Href - HREF文字列の作成
# 第一引数 : mode
# 第二引数 : no
# 第三引数 : page
# 第四引数 : eid
# 第五引数 : ref_eid
#
# 例外として、$modeが"post_comment"の場合には
# idを出力しません
##############################################
sub make_href
{
    my $h;
    if ($_[0] ne "post_comment" && $_[0] ne "post_comment_rcm" && $_[0] ne "post_comment_lnk"){
        if ($blog_id != $cfg{Blog_ID})      { $h .= "id=$blog_id" }

        if ($cat != 0)                      { $h .= $h ? '&amp;' : ''; $h .= "cat=$cat"; }
        if ($_[0] ne "" && $_[0] ne "main") { $h .= $h ? '&amp;' : ''; $h .= "mode=$_[0]"; }
        if ($_[1] != 0)                     { $h .= $h ? '&amp;' : ''; $h .= "no=$_[1]"; }
        if ($_[2] != 0)                     { $h .= $h ? '&amp;' : ''; $h .= "page=$_[2]"; }
        if ($_[3] != 0)                     { $h .= $h ? '&amp;' : ''; $h .= "eid=$_[3]"; }
        if ($_[4] != 0)                     { $h .= $h ? '&amp;' : ''; $h .= "ref_eid=$_[4]"; }
        if ($key)                           { $h .= $h ? '&amp;' : ''; $h .= "key=$key"; }
        if ($ua eq 'i-mode')                { $h .= $h ? '&amp;' : ''; $h .= "guid=ON"; }

        $h = $h ? $cfg{MyName}.'?'.$h : $cfg{MyName} ;
    }
    return $h;
}

########################################
# Sub Image - 画像表示
########################################

sub image {
    # Open template
    my $template = _tmpl_open('image.tmpl');

    my $cgi = new CGI;
    $cgi->charset('utf-8');

    # PerlMagick が無ければ画像縮小表示処理はしない
    if ($imk == 0){
        $img =~ s/\%2F/\//ig;
        $img =~ s/\%2B/\+/ig;
        $template->param(IMG_SRC => $cgi->escapeHTML($img));
    }else{
        # encode image url
        $img = MT4i::Func::url_encode($img);
        my $bid_str = ($blog_id != $cfg{Blog_ID}) ? "id=$blog_id&amp;" : '' ;
        $template->param(IMG_SRC =>
            "./$cfg{MyName}?mode=img_cut&amp;".$bid_str."img=".$cgi->escapeHTML($img)
        );
    }
    my $href = &make_href("individual", $no, 0, $eid, 0);
    $template->param(BACK_URL => $href);

    # Common
    $template = _tmpl_common($template);

    # Output
    &_cacheout($template);
}

########################################
# Sub Image_Cut - 画像縮小表示
########################################

sub image_cut {
    $img =~ s/\%2F/\//ig;
    $img =~ s/\%2B/\+/ig;
    my $url = $img;
    $url =~ s/http:\/\///;
    my $host = substr($url, 0, index($url, "/"));
    my $path = substr($url, index($url, "/"));
    $data = "";

    ####################
    # ホスト名置換
    if ($host eq $cfg{Photo_Host_Original}){
        $host = $cfg{Photo_Host_Replace};
    }

    ####################
    # 画像読み込みをLWPモジュール使用に変更
    require HTTP::Request;
    require LWP::UserAgent;
    my $ua = LWP::UserAgent->new;
    $url = 'http://'.$host.$path;
    my $request = HTTP::Request->new(GET => $url);
    my $response = $ua->request($request);

    if ($response->is_success) {
        $data = $response->as_string;
        $data =~ /(.*?\r?\n)\r?\n(.*)/s;
        $data = $2;
    } else {
        print "Content-type: text/html;\n\nHTTP Error:LWP";
        return;
    }

    my @blob = $data;

    ####################
    # vodafoneの特定機種に限りpng、それ以外はjpgに変換
    # サイズに関わらず、pngもしくはjpgに変換するように変更
    my $image = Image::Magick->new;
    $image->BlobToImage(@blob);

    # デジカメなどのアプリケーション情報の削除
    if (Image::Magick->VERSION >= 6.0) {
        $image->Strip();
    } else {
        $image->Profile( name=>'*' );
        $image->Comment('');
    }

    my $format;

    if ($png_flag){
        $image->Set(magick=>'png');
        $format = 'png';
        $cfg{PhotoWidth} = $cfg{PngWidth};
    }else{
        $image->Set(magick=>'jpg');
        $format = 'jpeg';
    }

    # Reference: http://deneb.jp/Perl/mobile/
    my $start_pos = 0;
    my $user_agent = $ENV{'HTTP_USER_AGENT'};
    my $cache_limit = -1024 + MT4i::Func::calc_cache_size( $user_agent );
    # If the image size is cache size or less, doesn't process it. 
    # However, if "PhotoWidthForce" is turning on, processes it.
    if ($mode eq 'thumbnail') {
        my $key = md5_hex($q->param("img"));
        my $tmp_blob;
        if ($admin_mode eq 'no') {
            $tmp_blob = _readcache('b'.$blog_id.'/img/'.$key, 1);
            @blob = $tmp_blob if $tmp_blob;
        }
        unless ($tmp_blob) {
            my ($w, $h) = $image->Get("width", "height");
            my $width = $cfg{ThumbWidth} || 75;
            $width = $w < $h ? $width."x" : "x".$width;
            my $clone = $image->Clone();
            $clone->Scale(geometry => "$width");
            @blob = $clone->ImageToBlob();
            _writecache('b'.$blog_id.'/img/'.$key, @blob);
        }
    } else {
        @blob = $image->ImageToBlob();
        if ( $cache_limit <  length($blob[0]) || $cfg{PhotoWidthForce} ) {
            foreach my $i ( $start_pos ..19 ) {
                my $img2 = $image->Clone();
                my $ratio = 1-$i*0.05;
                my $x = $cfg{PhotoWidth} * $ratio;
                $img2->Scale($x);
                @blob = $img2->ImageToBlob();
                if ( $cache_limit >=  length($blob[0]) ) {
                    last;
                }
            }
        }
    }

    print "Content-type: image/$format\n";
    print "Content-length: ",length($blob[0]),"\n\n";
    binmode STDOUT;
    print STDOUT $blob[0];
}

########################################
# Sub CommentForm - コメント投稿フォーム
########################################

sub comment_form {
    my $rowid = $no;

    # Get MT Object etc.
    &_get_mt_object();

    # Entry検索
    my $entry = _get_entry($eid);

    # 検索結果が0件の場合はメッセージ表示してSTOP（有り得ないけどな）
    if ($entry <= 0) {
        my $cgi = new CGI;
        $cgi->charset('utf-8');
        &errout('Entry ID "'.$cgi->escapeHTML($eid).'" is wrong.');
    }

    # HTMLテンプレートをオープン
    my $template = _tmpl_open('comment_form.tmpl');

    # 結果を変数に格納
    $template->param(ENTRY_TITLE => _conv_emoticon2binary($entry->title));
    $template->param(ENTRY_CREATED_ON => MT4i::Enc::encode_emoji_sjis(
        $ejpemoji, $enc_emoji_sjis, MT4i::Enc::decode_utf8( 
            MT::Util::format_ts($cfg{IndividualDtFormat},
                $mt->version_number >= 4.0 ? $entry->authored_on
                    : $entry->created_on, undef, $cfg{DtLang}))));

    ####################
    # 表示文字列生成
    if ($rowid) {
        $template->param(ENTRY_ROW_NO => "$rowid.");
    }
    
    if ($cfg{Version} >= 3.0 && $cfg{ApproveComment} eq 'no') {
        $template->param(NOTE => 
            MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, 
                "<p>ｺﾒﾝﾄは投稿後、掲載を保留されます。<br />管理人による承諾後、掲載されます。</p>"));
    }
    my $href;
    if ($mode eq 'comment_form') {
        $href = &make_href("post_comment", 0, 0, $eid, 0);
    } elsif ($mode eq 'comment_form_rcm') {
        $href = &make_href("post_comment_rcm", 0, 0, $eid, 0);
    } elsif ($mode eq 'comment_form_lnk') {
        $href = &make_href("post_comment_lnk", 0, 0, $eid, 0);
    }
    $template->param(POST_URL => $href);
    if ($cfg{PostFromEssential} eq "yes"){
        $template->param(REQUIRE_NAME => 1);
    }
    if ($cfg{PostMailEssential} eq "yes"){
        $template->param(REQUIRE_EMAIL => 1);
    }
    if ($cfg{PostTextEssential} eq "yes"){
        $template->param(REQUIRE_TEXT => 1);
    }
    $template->param(ID => $blog_id);
    if ($mode eq 'comment_form') {
        $template->param(POST_MODE => 'post_comment');
    } elsif ($mode eq 'comment_form_rcm') {
        $template->param(POST_MODE => 'post_comment_rcm');
    } elsif ($mode eq 'comment_form_lnk') {
        $template->param(POST_MODE => 'post_comment_lnk');
    }
    $template->param(NO => $rowid);
    $template->param(ENTRY_ID => $eid);
    if ($key){
        $template->param(KEY => $key);
    }
    if ($mode eq 'comment_form') {
        $href = &make_href("individual", $rowid, 0, $eid, 0);
    } elsif ($mode eq 'comment_form_rcm') {
        $href = &make_href("individual_rcm", $rowid, 0, $eid, 0);
    } elsif ($mode eq 'comment_form_lnk') {
        $href = &make_href("individual_lnk", $rowid, 0, $eid, 0);
    }
    $template->param(BACK_URL => $href);

    # Common
    $template = _tmpl_common($template);

    # Output
    &_cacheout($template);
}

########################################
# Sub Post_Comment - コメント投稿->表示処理
########################################
sub post_comment {
    require MT::Comment;
    require MT::App;

    # Get MT Object etc.
    &_get_mt_object();

    # SPAM対策
    # 本文が指定したパターンに適合したコメントを弾く
    my @comment_filter_strs = split(",", $cfg{CommentFilterStr});
    my $temp_post_text;
    $temp_post_text = ($ecd == 1)
        ? Encode::decode('shiftjis', $p{post_text})
        : Jcode->new($p{post_text},'sjis');
    foreach my $comment_filter_str (@comment_filter_strs) {
        if ($temp_post_text =~ /$comment_filter_str/i) {
            print "Content-type: text/plain;\n\n";
            print "Block!";

            eval {require $log_pl; 1} or &errout('File not found: '.$log_pl);
            MT4i::Log::writelog('blocked comment from '.$ENV{'REMOTE_ADDR'});

            exit;
        }
    }

    my $rowid = $no;
    $no--;

    my @p_labels = qw/post_from post_text/;
    _pre_post(@p_labels);

    ####################
    # admin_helperをチェック(管理者モード時のみ)
    my $post_from_org = $p{post_from};
    if (($cfg{AdminHelper} eq 'yes') && ($admin_mode eq 'yes')){
        if ($post_from_org eq $cfg{AdminHelperID}){
            $p{post_from} = $cfg{AdminHelperNM};
            $p{post_mail} = $cfg{AdminHelperML};
        }
    }

    ####################
    # 必須入力項目をチェック
    # 名前,mail,textのどれも入力が無ければエラー
    if(((!$p{post_from})&&(!$p{post_text})&&(!$p{post_mail}))||
       ((!$p{post_from})&&($cfg{PostFromEssential} eq "yes"))||
       ((!$p{post_mail})&&($cfg{PostMailEssential} eq "yes"))||
       ((!$p{post_text})&&($cfg{PostTextEssential} eq "yes")))
    {
        $data .="Error!<br />未入力項目があります.<br />";
        my $href = &make_href("comment_form", $rowid, 0, $eid, 0);
        $data .="$nostr[0]<a href='$href'$akstr[0]>戻る</a>";
        &htmlout;
        exit;
    }

    ####################
    # 携帯端末識別番号取得
    if ($cfg{SerNo} && $ua eq 'i-mode') {
        my $tmp_ua = $ENV{'HTTP_USER_AGENT'};
        unless ($tmp_ua =~ m/.*ser.*/i && $ENV{'HTTP_X_DCMGUID'}) {
            $data .= "Error!<br />携帯電話情報を送信してください.<br />";
            my $href = &make_href("comment_form", $rowid, 0, $eid, 0);
            $data .= "$nostr[0]<a href='$href'$akstr[0]>戻る</a>";
            &htmlout;
            exit;
        }
    }

    ####################
    # メールアドレスチェック
    if ($p{post_mail}){
        unless($p{post_mail}=~/^[\w\-+\.]+\@[\w\-+\.]+$/i){
            $data .="Error!<br />ﾒｰﾙｱﾄﾞﾚｽが不正です.<br />";
            my $href = &make_href("comment_form", $rowid, 0, $eid, 0);
            $data .="$nostr[0]<a href='$href'$akstr[0]>戻る</a>";
            &htmlout;
            return;
        }
    }

    _after_post(@p_labels);

    # 連続投稿防止
    # （直前のコメントと比較して同内容であれば
    #   連続投稿とみなしエラーとする。
    #   悪意ある連続投稿防止というよりは、
    #   タイムアウト後などの不作為の過失防止。）
    my @comments = get_comments($eid, 1, '', 'descend', 0);

    for my $tmp (@comments) {
        if ($p{post_from} eq $tmp->author &&
            $p{post_mail} eq $tmp->email &&
            $p{post_text} eq $tmp->text) {
            $data .="Error!<br />同内容のｺﾒﾝﾄが既に投稿されています<hr>";
            my $href = &make_href("comment", $rowid, 0, $eid, 0);
            $data .="$nostr[0]<a href='$href'$akstr[0]>投稿されたｺﾒﾝﾄを確認する</a>";
            &htmlout;
            return;
        }
    }

    # Entry ID、Entry Titleの取得
    my $entry = _get_entry($eid);

    # 検索結果が0件の場合はメッセージ表示してSTOP（有り得ないけどな）
    if ($entry <= 0) {
        my $cgi = new CGI;
        $cgi->charset('utf-8');
        &errout('Entry ID "'.$cgi->escapeHTML($eid).'" is wrong.');
    }

    # DB更新
    my $comment = MT::Comment->new;
    my $rm_ip = $ENV{'REMOTE_ADDR'};
    my $serno = $ENV{'HTTP_X_UP_SUBNO'} ? '('.$ENV{'HTTP_X_UP_SUBNO'}.')'
                                        : $ENV{'HTTP_X_DCMGUID'}
                                            ? '('.$ENV{'HTTP_X_DCMGUID'}.')'
                                            : '('.$ENV{'HTTP_USER_AGENT'}.')';
    $comment->ip($rm_ip);
    $comment->blog_id($blog_id);
    $comment->entry_id($entry->id);
    $comment->author($p{post_from});
    $comment->email($p{post_mail});
    $comment->text($p{post_text});
    #if ($admin_data[3]){
    #    $comment->url($admin_data[3]);
    #}

    # MT3.0以上ならvisible値設定
    if ($cfg{Version} >= 3.0) {
        # $cfg{ApproveComment}='yes'の場合には、書き込みと同時に掲載を承諾する
        $comment->visible( ($cfg{ApproveComment} eq 'yes') ? 1 : 0 );
    }

    $comment->save
        or &errout($comment->errstr);

    ####################
    # Mail & Rebuild
    my $notify_and_rebuild = sub {
        my ($entry, $comment, $serno) = @_;

        # Mail
        if ($blog->email_new_comments) {
            require MT::Mail;
            my $author = $entry->author;
            my $entry_title = MT4i::Enc::decode_utf8($entry->title);
            my $blog_name = MT4i::Enc::decode_utf8($blog->name);
            $mt->set_language($author->preferred_language)
                if $author && $author->preferred_language;
            if ($author && $author->email) {
                my %head = (    To => $author->email,
                                From => $comment->email || $author->email,
                                Subject =>
                                    '[' . $blog_name . '] ' .
                                    $entry_title . ' への新しいコメント from MT4i'
                            );
                my $charset;
                # MT3.3 higher?
                $charset = ($cfg{Version} >= 3.3)
                    ? $mt->{cfg}->MailEncoding || $mt->{cfg}->PublishCharset
                    : $mt->{cfg}->PublishCharset || 'iso-8859-1';
                $head{'Content-Type'} = qq(text/plain; charset="$charset");
                my $body = '新しいコメントがウェブログ ' .
                            $blog_name . ' ' .
                            'のエントリー #' . $entry->id . " (" .
                            $entry_title .
                            ') にありました';

                # Create link to entry
                my $link_url = MT4i::Enc::decode_utf8($entry->permalink);

                # For the mail garble
                my $comment_author = MT4i::Enc::decode_utf8($comment->author);
                my $comment_text = MT4i::Enc::decode_utf8($comment->text);

                use Text::Wrap;
                $Text::Wrap::cols = 72;
                $body = Text::Wrap::wrap('', '', $body) . "\n$link_url\n\n" .
                $body = $body        . "\n$link_url\n\n" .
                  'IPアドレス: '     . $comment->ip . "\n" .
                  '識別情報: '       . $serno . "\n" .
                  '名前: '           . $comment_author . "\n" .
                  'メールアドレス: ' . $comment->email . "\n" .
                  'URL: '            . $comment->url . "\n\n" .
                  'コメント:'        . "\n\n" . $comment_text . "\n\n" .
                  "-- \nfrom MT4i v${version}\n";
                $head{Subject} = encode($conv_in, $head{Subject});
                $body = encode($conv_in, $body);
                MT::Mail->send(\%head, $body);
            }
        }

        ####################
        # Rebuild

        # Index template
        if ($cfg{RIT_ID} eq 'ALL') {
            $mt->rebuild_indexes( BlogID => $blog_id )
                or &errout($mt->errstr);
        } else {
            my @tmp_RIT_ID = split(",", $cfg{RIT_ID});
            foreach my $indx_tmpl_id (@tmp_RIT_ID) {
                require MT::Template;
                my $tmpl_saved = MT::Template->load($indx_tmpl_id);
                $mt->rebuild_indexes( BlogID => $blog_id, Template => $tmpl_saved, Force => 1 )
                    or &errout($mt->errstr);
            }
        }

        # Archive template
        if ($cfg{RAT_ID} eq 'ALL') {
            $mt->rebuild_entry( Entry => $entry )
                or &errout($mt->errstr);
        } else {
            my @tmp_RAT_ID = split(",", $cfg{RAT_ID});
            foreach my $arc_tmpl_id (@tmp_RAT_ID) {
                $mt->publisher->_rebuild_entry_archive_type(
                    Entry => $entry,
                    Blog => $blog,
                    ArchiveType => $arc_tmpl_id
                    )
                    or &errout($mt->errstr);
            }
        }
    };

    # Run background task?
    if ($cfg{Version} >= 3.0) {
        require MT::Util;
        MT::Util::start_background_task(sub {
            $notify_and_rebuild->($entry, $comment, $serno)
        });
    } else {
        $notify_and_rebuild->($entry, $comment, $serno);
    }

    # purge cache
    eval {require $log_pl; 1} or &errout('File not found: '.$log_pl);
    MT4i::Log::writelog('post comment.');
    purgecache('b'.$comment->blog_id.'/idxc*/*');
    purgecache('b'.$comment->blog_id.'/e'.$comment->entry_id.'/c*/*');
    purgecache('b'.$comment->blog_id.'/e'.$comment->entry_id.'/ccp*');
    purgecache('b'.$comment->blog_id.'/rc_*');

    # Open template file.
    my $template = _tmpl_open('post_comment.tmpl');

    # Set params.
    $template->param(COMMENT_HIDDEN => 1)
        if ($cfg{Version} >= 3.0 && $cfg{ApproveComment} eq 'no');
    my $href;
    if ($mode eq 'post_comment') {
        $href = &make_href("comment", $rowid, 0, $eid, 0);
    } elsif ($mode eq 'post_comment_rcm') {
        $href = &make_href("comment_rcm", $rowid, 0, $eid, 0);
    } elsif ($mode eq 'post_comment_lnk') {
        $href = &make_href("comment_lnk", $rowid, 0, $eid, 0);
    }
    $template->param(BACK_URL => $href);

    # Common
    $template = _tmpl_common($template);

    # Output
    &_cacheout($template);
}

########################################
# Sub entryform - 新規Entry/Entry編集 フォーム
########################################
sub entryform {

    # Get MT Object etc.
    &_get_mt_object();

    my ($org_convert_breaks,
        $org_created_on,
        $org_authored_on,
        $org_comment_cnt,
        $org_ent_status,
        $org_ent_allow_comments,
        $org_ent_allow_pings
    );
    my %p;
    my $rowid = $no;

    if ($eid == 0){
        $data = "<h4>新規Entryの作成</h4><hr>";

        # 現在日時の取得
        $ENV{TZ} = 'JST-9';
        my $time = time;
        my ($sec,$min,$hour,$mday,$mon,$year,$wday) = localtime($time);
        $mon++;
        $year = 1900+$year;
        $mon = sprintf("%.2d",$mon);
        $mday = sprintf("%.2d",$mday);
        $hour = sprintf("%.2d",$hour);
        $sec = sprintf("%.2d",$sec);
        $min = sprintf("%.2d",$min);
        if ($mt->version_number >= 4.0) {
            $org_authored_on = "$year-$mon-$mday $hour:$min:$sec";
        } else {
            $org_created_on = "$year-$mon-$mday $hour:$min:$sec";
        }
    }else{

        $data = "<h4>Entryの編集</h4><hr>";

        # Entry検索
        my $entry = _get_entry($eid);

        # 検索結果が0件の場合はメッセージ表示してSTOP（有り得ないけどな）
        if (!$entry) {
            my $cgi = new CGI;
            $cgi->charset('utf-8');
            &errout('Entry ID "'.$cgi->escapeHTML($eid).'" is wrong.');
        }

        # Get original entry data
        foreach (qw/title text text_more excerpt keywords/) {
            my $label = 'org_'.$_;
            $p{$label} = _conv_emoticon2tag(_conv_utf8_z2h($entry->$_));
        }
        if ($cfg{Version} >= 3.3) {
            require MT::Author;
            # AuthorNameをPublishCharsetに変換
            if ($conv_in ne 'utf8') {
                $cfg{AuthorName} = encode($conv_in, MT4i::Enc::decode_utf8($cfg{AuthorName}));
            }
            my $author = MT::Author->load({ name => $cfg{AuthorName} });
            if (!$author) {
                &errout("AuthorName'$cfg{AuthorName}' is wrong.");
                exit;      # exitする
            }
            my $tag_delim = chr($author->entry_prefs->{tag_delim});
            require MT::Tag;
            my $tags = MT::Tag->join($tag_delim, $entry->tags);
            $p{org_tags} = _conv_emoticon2tag(_conv_utf8_z2h($tags));
        }
        $org_convert_breaks = $entry->convert_breaks;
        if ($mt->version_number >= 4.0) {
            $org_authored_on = $entry->authored_on;
            $org_authored_on =~ s/(\d\d\d\d)(\d\d)(\d\d)(\d\d)(\d\d)(\d\d)/$1-$2-$3 $4:$5:$6/;
        } else {
            $org_created_on = $entry->created_on;
            $org_created_on =~ s/(\d\d\d\d)(\d\d)(\d\d)(\d\d)(\d\d)(\d\d)/$1-$2-$3 $4:$5:$6/;
        }
        $org_comment_cnt = $entry->comment_count;
        $org_ent_status = $entry->status;
        $org_ent_allow_comments = $entry->allow_comments;
        $org_ent_allow_pings = $entry->allow_pings;

        # Encode
        foreach (qw/title text text_more excerpt keywords tags/) {
            $p{'org_'.$_} =~ s/&/&amp;/g;
            $p{'org_'.$_} =~ s/\</&lt;/g;
            $p{'org_'.$_} =~ s/\>/&gt;/g;
            $p{'org_'.$_} =~ s/ /&nbsp;/g
                if ($_ eq 'title' || $_ eq 'tags');
        }
    }

    ####################
    # 表示文字列生成
    my $href = &make_href("post_comment", 0, 0, $eid, 0);
    $data .= "<form method=\"post\" action=\"$href\">";

    # カテゴリセレクタ
    my $cat_label;
    if ($eid){
        $cat_label = &check_category(_get_entry($eid));
    }
    $data .= "ｶﾃｺﾞﾘ<br />";
    $data .= "<select name=\"entry_cat\">";
    $data .= "<option value=0>";
    require MT::Category;
    my @categories = MT::Category->load({blog_id => $blog_id},
                                            {unique => 1});
    for my $category (@categories) {
        my $label;
        $label =  ($cfg{CatDescReplace} eq "yes")
            ? _conv_utf8_z2h($category->description)
            : _conv_utf8_z2h($category->label);
        my $cat_id = $category->id;

        $data .=  ($cat_label eq $label)
            ? "<option value=$cat_id selected>$label<br />"
            :"<option value=$cat_id>$label<br />";
    }
    $data .= "</select><br />";

    $data .= 'ﾀｲﾄﾙ';
    $data .= '<br /><input type="text" name="entry_title" value=\''.$p{org_title}.'\' /><br />';
    $data .= 'Entryの内容';
    $data .= '<br /><textarea rows="4" name="entry_text">'.$p{org_text}.'</textarea><br />';
    $data .= 'Extended(追記)';
    $data .= '<br /><textarea rows="4" name="entry_text_more">'.$p{org_text_more}.'</textarea><br />';
    $data .= 'Excerpt(概要)';
    $data .= '<br /><textarea rows="4" name="entry_excerpt">'.$p{org_excerpt}.'</textarea><br />';
    $data .= 'ｷｰﾜｰﾄﾞ';
    $data .= '<br /><textarea rows="4" name="entry_keywords">'.$p{org_keywords}.'</textarea><br />';
    if ($cfg{Version} >= 3.3) {
        $data .= 'ﾀｸﾞ(ｶﾝﾏで区切る)';
        $data .= '<br /><input type="text" name="entry_tags" value=\''.$p{org_tags}.'\' /><br />';
    }

    $data .= '投稿の状態<br />';
    $data .= '<select name="post_status">';
    my @selected;
    if ($eid && $org_ent_status) {
        $selected[$org_ent_status] = " selected";
    } elsif (!$eid && $blog->status_default) {
        $selected[$blog->status_default] = " selected";
    } else {
        $selected[2] = " selected";
    }
    $data .= "<option value=1".$selected[1].">下書き<br />";
    $data .= "<option value=2".$selected[2].">公開<br />";
    if ($cfg{Version} >= 3.1) {
        $data .= "<option value=3".$selected[3].">指定日<br />";
    }
    $data .= "</select><br />";
    $data .= "<input type=\"hidden\" name=\"post_status_old\" value=\"".$org_ent_status."\" />";

    $data .= "ｺﾒﾝﾄ<br />";
    $data .= "<select name=\"allow_comments\">";
    @selected = ('', '', '');
    if ($eid && $org_ent_allow_comments >= 0) {
        $selected[$org_ent_allow_comments] = " selected";
    } elsif (!$eid && $blog->allow_comments_default >= 0) {
        $selected[$blog->allow_comments_default] = " selected";
    } else {
        $selected[2] = " selected";
    }
    $data .= "<option value=0".$selected[0].">なし<br />";
    $data .= "<option value=1".$selected[1].">ｵｰﾌﾟﾝ<br />";
    $data .= "<option value=2".$selected[2].">ｸﾛｰｽﾞ<br />";
    $data .= "</select><br />";

    $data .= "ﾄﾗｯｸﾊﾞｯｸを受けつける<br />";
    $data .=  (($eid && $org_ent_allow_pings) || (!$eid && $blog->allow_pings_default == 1))
        ? "<INPUT TYPE=checkbox name=\"allow_pings\" value=\"1\" CHECKED><br />"
        : "<INPUT TYPE=checkbox name=\"allow_pings\" value=\"1\"><br />";

    ## テキストフォーマットのロード
    my $filters = $mt->all_text_filters;
    my $text_filters = [];
    for my $filter (keys %$filters) {
        my $label = $filters->{$filter}{label};
        if ($cfg{Version} >= 4.0) {
            $label = $label->() if ref($label) eq 'CODE';
        }
        push @{ $text_filters }, {
            filter_key => $filter,
            filter_label => _conv_utf8_z2h($label),
        };
    }
    # ソート
    $text_filters = [ sort { $a->{filter_key} cmp $b->{filter_key} } @{ $text_filters } ];
    # 「なし」を追加
    unshift @{ $text_filters }, {
        filter_key => '0',
        filter_label => 'なし',
    };
    # 描画
    $data .= "ﾃｷｽﾄﾌｫｰﾏｯﾄ<br />";
    $data .= '<select name="convert_breaks">';
    foreach my $filter ( @{ $text_filters } ) {
        my $selected;
        if (($org_convert_breaks eq $filter->{filter_key}) || (!$org_convert_breaks && $convert_paras eq $filter->{filter_key})) {
            $selected = ' selected';
        }
        $data .= "<option value=\"$filter->{filter_key}\"$selected>$filter->{filter_label}";
    }
    $data .= '</select><br />';

    if ($cfg{Version} >= 4.0) {
        $data .= "公開日時<br />";
        $data .= "<input type=\"text\" name=\"entry_authored_on\" value=\"$org_authored_on\" /><br />";
    } else {
        $data .= "作成日時<br />";
        $data .= "<input type=\"text\" name=\"entry_created_on\" value=\"$org_created_on\" /><br />";
    }

    $data .= "<input type=\"hidden\" name=\"id\" value=\"$blog_id\" />";
    $data .= "<input type=\"hidden\" name=\"mode\" value=\"entry\" />";
    $data .= "<input type=\"hidden\" name=\"no\" value=\"$rowid\" />";
    $data .= "<input type=\"hidden\" name=\"eid\" value=\"$eid\" />";
    if ($key){
        $data .= "<input type=\"hidden\" name=\"key\" value=\"$key\" />";
    }
    $data .= "<input type=\"submit\" value=\"送信\" />";
    $data .= "</form>";
    $data .= "<hr>";
    $href = &make_href("", 0, 0, 0, 0);
    $data .= "$nostr[0]<a href='$href'$akstr[0]>一覧へ戻る</a>";

    &htmlout;
}

########################################
# Sub Entry - 新規Entry投稿->表示処理
########################################
sub entry {

    # Get MT Object etc.
    &_get_mt_object();

    my $rowid = $no;
    $no--;

    my @p_labels = qw/entry_title entry_text entry_text_more entry_excerpt entry_keywords entry_tags/;
    _pre_post(@p_labels);

    # 半角スペース'&nbsp;'をデコード
    $p{entry_title} =~ s/&nbsp;/ /g;
    $p{entry_tags} =~ s/&nbsp;/ /g;

    ####################
    # Check required parameters.
    my $error_column =
        ( !$p{entry_title} || !$p{entry_text} )
            ? '「ﾀｲﾄﾙ」と「Entryの内容」'
            : ( $cfg{Version} >= 4.0 )
                ? (!$p{entry_authored_on})
                    ? '「公開日時」'
                    : ''
                : (!$p{entry_created_on})
                    ? '「作成日時」'
                    : '' ;
    if ($error_column) {
        $data .="Error!<br />未入力項目があります。".$error_column."は必須です。<br />";
        my $href = &make_href("entryform", 0, 0, $eid, 0);
        $data .="$nostr[0]<a href=\"$href\"$akstr[0]>戻る</a>";
        &htmlout;
        return;
    }

    require MT::Author;
    # AuthorNameをPublishCharsetに変換
    if ($conv_in ne 'utf8') {
        $cfg{AuthorName} = encode($conv_in, MT4i::Enc::decode_utf8($cfg{AuthorName}));
    }
    if (!$cfg{AuthorName}) {
        &errout('AuthorName is not input in MT4i Manager.');
    }
    my $author = MT::Author->load({ name => $cfg{AuthorName} });
    if (!$author) {
        &errout('"'.$cfg{AuthorName}.'" is not registered as a author.');
    }

    _after_post(@p_labels);

    require MT::Entry;
    my $entry;
    $entry = ($eid) ? _get_entry($eid) : MT::Entry->new;
    $entry->blog_id($blog->id);
    $entry->status($post_status);
    $entry->author_id($author->id);
    $entry->title($p{entry_title});
    $entry->text($p{entry_text});
    $entry->text_more($p{entry_text_more});
    $entry->excerpt($p{entry_excerpt});
    $entry->keywords($p{entry_keywords});
    if ($cfg{Version} >= 3.3) {
        my $tag_delim = chr($author->entry_prefs->{tag_delim});
        require MT::Tag;
        my @tags = MT::Tag->split($tag_delim, $p{entry_tags});
        $entry->set_tags(@tags);
    }
    $entry->allow_pings( ($allow_pings == 1) ? 1 : 0 );
    $entry->allow_comments($allow_comments);
    $entry->convert_breaks($text_format);
    if ($cfg{Version} >= 4.0) {
        $p{entry_authored_on} =~ s/(\d\d\d\d)-(\d\d)-(\d\d) (\d\d):(\d\d):(\d\d)/$1$2$3$4$5$6/;
        $entry->authored_on($p{entry_authored_on});
    } else {
        $p{entry_created_on} =~ s/(\d\d\d\d)-(\d\d)-(\d\d) (\d\d):(\d\d):(\d\d)/$1$2$3$4$5$6/;
        $entry->created_on($p{entry_created_on});
    }
    $entry->save
        or &errout($entry->errstr);

    if ($p{entry_cat}) {
        require MT::Placement;
        my $place = MT::Placement->load({ blog_id => $blog_id , entry_id => $entry->id });

        if (!$place){
            $place = MT::Placement->new;
        }
        $place->entry_id($entry->id);
        $place->blog_id($blog_id);
        $place->category_id($p{entry_cat});
        $place->is_primary(1);
        $place->save
            or &errout($place->errstr);
    }
    $data = $eid ? "Entryは修正されました<hr>" : "新規Entryが作成されました<hr>";

    ####################
    # 保存のステータスがリリースか、あるいは編集前のステータスがリリースの場合のみ
    # エントリー及びインデックスのリビルドを行い、ピングを送信する。
    if ($post_status == MT::Entry::RELEASE() || $post_status_old eq MT::Entry::RELEASE()) {
        # MT3.0以上では、リビルド及び更新ping送信をバックグラウンドで行う
        if ($cfg{Version} >= 3.0) {
            require MT::Util;
            MT::Util::start_background_task(sub {
                # リビルド
                $mt->rebuild_entry( Entry => $entry, BuildDependencies => 1 )
                    or &errout($mt->errstr);

                ####################
                # 更新ping送信
                # 保存のステータスがリリースの場合のみping送信
                if ($post_status == MT::Entry::RELEASE() || $post_status_old eq MT::Entry::RELEASE()) {
                    require MT::XMLRPC;
                    if ($blog->ping_others){
                        my (@updateping_urls) = split(/\n/,$blog->ping_others);
                        for my $url (@updateping_urls) {
                            MT::XMLRPC->ping_update('weblogUpdates.ping', $blog, $url)
                                or &errout(MT::XMLRPC->errstr);
                        }
                    }
                }
            });
        } else {
            # リビルド
            $mt->rebuild_entry( Entry => $entry, BuildDependencies => 1 )
                or &errout($mt->errstr);

            ####################
            # 更新ping送信
            # 保存のステータスがリリースの場合のみping送信
            if ($post_status == MT::Entry::RELEASE()){
                require MT::XMLRPC;
                if ($blog->ping_others){
                    my (@updateping_urls) = split(/\n/,$blog->ping_others);
                    for my $url (@updateping_urls) {
                        MT::XMLRPC->ping_update('weblogUpdates.ping', $blog, $url)
                            or &errout(MT::XMLRPC->errstr);
                    }
                }
            }
        }
    }
    my $href = &make_href("", 0, 0, 0, 0);
    $data .= "$nostr[0]<a href=\"$href\"$akstr[0]>一覧へ戻る</a>";

    ## purge cache ##
    eval {require $log_pl; 1} or &errout('File not found: '.$log_pl);
    MT4i::Log::writelog('post entry.');
    purgecache('b'.$entry->blog_id.'/idxc*/*');
    purgecache('b'.$entry->blog_id.'/e'.$entry->id.'/c*/*');
    purgecache('b'.$entry->blog_id.'/e'.$entry->id.'/obj');
    # next and prev
    my $next = $entry->previous(1);
    purgecache('b'.$entry->blog_id.'/e'.$next->id.'/c*/*') if $next;
    purgecache('b'.$entry->blog_id.'/e'.$next->id.'/obj') if $next;
    my $prev = $entry->next(1);
    purgecache('b'.$entry->blog_id.'/e'.$prev->id.'/c*/*') if $prev;
    purgecache('b'.$entry->blog_id.'/e'.$prev->id.'/obj') if $prev;
    # categories
    my $cats = $entry->categories;
    for my $cat (@$cats) {
        my $cid = $cat->id;
        my $next = _neighbor_entry($entry, $cid, 'prev');
        if ($next) {
            my $key = 'b'.$entry->blog_id.'/e'.$next->id.'/c';
            $key .= $cfg{NonDispCat} ? '*' : $cid ;
            $key .= '/*';
            purgecache($key);
        }
        my $prev = _neighbor_entry($entry, $cid, 'next');
        if ($prev) {
            my $key = 'b'.$entry->blog_id.'/e'.$prev->id.'/c';
            $key .= $cfg{NonDispCat} ? '*' : $cid ;
            $key .= '/*';
            purgecache($key);
        }
    }

    &htmlout;
}

########################################
# Sub Entry_del - Entry削除
########################################
sub entry_del {

    # Get MT Object etc.
    &_get_mt_object();

    my $rowid = $no;
    $no--;

    my $entry = _get_entry($eid);
    if (!$entry) {
        my $cgi = new CGI;
        $cgi->charset('utf-8');
        &errout('Entry ID "'.$cgi->escapeHTML($eid).'" is wrong.');
    }

    # get categories
    my $cats = $entry->categories;

    $entry->remove;

    ####################
    # If MT is 3.0 or higher, rebuilds by the background.
    if ($cfg{Version} >= 3.0) {
        require MT::Util;
        MT::Util::start_background_task(sub {
            # rebuild
            $mt->rebuild_entry( Entry => $entry, BuildDependencies => 1 )
                or &errout($mt->errstr);
            # remove file info
            my %terms;
            $terms{blog_id}     = $entry->blog_id;
            $terms{entry_id}    = $entry->id;
            my @finfos = MT::FileInfo->load( \%terms );
            foreach (@finfos) { $_->remove(); }
            # remove file
            if ( $mt->config('DeleteFilesAtRebuild') ) {
                require MT::WeblogPublisher;
                my $pub = MT::WeblogPublisher->new;
                $pub->remove_entry_archive_file(
                    Entry       => $entry,
                    ArchiveType => 'Individual'
                );
            }
        });
    } else {
        # rebuild
        $mt->rebuild_entry( Entry => $entry, BuildDependencies => 1 )
            or &errout($mt->errstr);
        # remove file info
        my %terms;
        $terms{blog_id}     = $entry->blog_id;
        $terms{entry_id}    = $entry->id;
        my @finfos = MT::FileInfo->load( \%terms );
        foreach (@finfos) { $_->remove(); }
        # remove file
        if ( $mt->config('DeleteFilesAtRebuild') ) {
            require MT::WeblogPublisher;
            my $pub = MT::WeblogPublisher->new;
            $pub->remove_entry_archive_file(
                Entry       => $entry,
                ArchiveType => 'Individual'
            );
        }
    }

    $data = "Entryが削除されました<hr>";
    my $href = &make_href("", 0, 0, 0, 0);
    $data .= "$nostr[0]<a href='$href'$akstr[0]>一覧へ戻る</a>";

    # purge cache
    # next and prev
    my $next = $entry->previous(1);
    purgecache('b'.$entry->blog_id.'/e'.$next->id.'/c*/*') if $next;
    purgecache('b'.$entry->blog_id.'/e'.$next->id.'/obj') if $next;
    my $prev = $entry->next(1);
    purgecache('b'.$entry->blog_id.'/e'.$prev->id.'/c*/*') if $prev;
    purgecache('b'.$entry->blog_id.'/e'.$prev->id.'/obj') if $prev;
    # categories
    for my $cat (@$cats) {
        my $cid = $cat->id;
        my $next = _neighbor_entry($entry, $cid, 'prev');
        if ($next) {
            my $key = 'b'.$entry->blog_id.'/e'.$next->id.'/c';
            $key .= $cfg{NonDispCat} ? '*' : $cid ;
            $key .= '/*';
            purgecache($key);
        }
        my $prev = _neighbor_entry($entry, $cid, 'next');
        if ($prev) {
            my $key = 'b'.$entry->blog_id.'/e'.$prev->id.'/c';
            $key .= $cfg{NonDispCat} ? '*' : $cid ;
            $key .= '/*';
            purgecache($key);
        }
    }

    &htmlout;
}

########################################
# Sub Comment_del - コメント削除
########################################
sub comment_del {

    # Get MT Object etc.
    &_get_mt_object();

    my $rowid = $no;
    $no--;

    ####################
    # commentを探す
    require MT::Comment;
    my $comment = MT::Comment->load($page);    # コメント番号は$pageで渡す
    if (!$comment) {
        my $cgi = new CGI;
        $cgi->charset('utf-8');
        &errout('comment_del::Comment ID "'.$cgi->escapeHTML($page).'" is wrong.');
    }
    $comment->remove()
        or &errout($comment->errstr);

    #このcommentが属するEntryを探す
    my $entry = _get_entry($comment->entry_id);
    if (!$entry) {
        &errout("comment_del::Entry ID '".$comment->entry_id."' is wrong.");
    }

    ####################
    # MT3.0以上では、リビルドをバックグラウンドで行う
    if ($cfg{Version} >= 3.0) {
        require MT::Util;
        MT::Util::start_background_task(sub {
            # リビルド
            $mt->rebuild_entry( Entry => $entry, BuildDependencies => 1 )
                or &errout($mt->errstr);
        });
    } else {
        # リビルド
        $mt->rebuild_entry( Entry => $entry, BuildDependencies => 1 )
            or &errout($mt->errstr);
    }

    $data = "ｺﾒﾝﾄが削除されました<hr>";
    my $href = &make_href("comment", $rowid, 0, $eid, 0);
    $data .= "$nostr[0]<a href=\'$href\'$akstr[0]>ｺﾒﾝﾄ一覧へ戻る</a>";
    &htmlout;
}

########################################
# Sub Trackback_del - トラックバック削除
########################################
sub trackback_del {

    # Get MT Object etc.
    &_get_mt_object();

    my $rowid = $no;
    $no--;

    ####################
    # pingを探す
    require MT::TBPing;
    my $tbping = MT::TBPing->load($page);    # トラックバック番号は$pageで渡す
    if (!$tbping) {
        my $cgi = new CGI;
        $cgi->charset('utf-8');
        &errout('trackback_del::MTPing ID "'.$cgi->escapeHTML($page).'" is wrong.');
    }
    $tbping->remove()
        or &errout($tbping->errstr);

    #このtbpingが属するTrackbackを探す
    require MT::Trackback;
    my $trackback = MT::Trackback->load($tbping->tb_id);
    if (!$trackback) {
        &errout("trackback_del::Trackback ID '".$tbping->tb_id."' is wrong.");
    }

    #このTrackbackが属するEntryを探す
    my $entry = _get_entry($trackback->entry_id);
    if (!$entry) {
        &errout("trackback_del::Entry ID '".$trackback->entry_id."' is wrong.");
    }

    ####################
    # MT3.0以上では、リビルドをバックグラウンドで行う
    if ($cfg{Version} >= 3.0) {
        require MT::Util;
        MT::Util::start_background_task(sub {
            # リビルド
            $mt->rebuild_entry( Entry => $entry, BuildDependencies => 1 )
                or &errout($mt->errstr);
        });
    } else {
        # リビルド
        $mt->rebuild_entry( Entry => $entry, BuildDependencies => 1 )
            or &errout($mt->errstr);
    }

    $data = "ﾄﾗｯｸﾊﾞｯｸが削除されました<hr>";
    my $href = &make_href("trackback", $rowid, 0, $eid, 0);
    $data .= "$nostr[0]<a href=\'$href\'$akstr[0]>ﾄﾗｯｸﾊﾞｯｸ一覧へ戻る</a>";
    &htmlout;
}

########################################
# Sub Trackback_ipban - このIPからのトラックバックを禁止＆全削除
########################################
sub trackback_ipban {

    # Get MT Object etc.
    &_get_mt_object();

    my $rowid = $no;
    $no--;

    ####################
    # pingを探す
    require MT::TBPing;
    my $tbping = MT::TBPing->load($page);    # トラックバック番号は$pageで渡す
    if (!$tbping) {
        my $cgi = new CGI;
        $cgi->charset('utf-8');
        &errout('trackback_ipban::MTPing ID "'.$cgi->escapeHTML($page).'" is wrong.');
    }

    require MT::IPBanList;
    my $ban = MT::IPBanList->new;
    $ban->blog_id($blog->id);
    $ban->ip($tbping->ip);
    $ban->save
        or &errout($ban->errstr);

    ####################
    # そのIPから送信されたトラックバックを全て探す
    my @tbpings = MT::TBPing->load(
            { blog_id => $blog_id, ip => $tbping->ip});

    for my $tbping (@tbpings) {

        #このtbpingが属するTrackbackを探す
        require MT::Trackback;
        my $trackback = MT::Trackback->load($tbping->tb_id);
        if (!$trackback) {
            &errout("trackback_ipban::Trackback ID '".$tbping->tb_id."' is wrong.");
        }

        #このTrackbackが属するEntryを探す
        my $entry = _get_entry($trackback->entry_id);
        if (!$entry) {
            &errout("trackback_ipban::Entry ID '".$trackback->entry_id."' is wrong.");
        }

        $data .= _conv_utf8_z2h($tbping->excerpt)."<hr>";

        # トラックバックping削除
        $tbping->remove()
            or &errout($tbping->errstr);

        ####################
        # MT3.0以上では、リビルドをバックグラウンドで行う
        if ($cfg{Version} >= 3.0) {
            require MT::Util;
            MT::Util::start_background_task(sub {
                # entryのリビルド
                $mt->rebuild_entry( Entry => $entry, BuildDependencies => 1 )
                    or &errout($mt->errstr);
            });
        } else {
            # entryのリビルド
            $mt->rebuild_entry( Entry => $entry, BuildDependencies => 1 )
                or &errout($mt->errstr);
        }
    }

    $data = "IPを禁止ﾘｽﾄに追加し、".@tbpings."件のﾄﾗｯｸﾊﾞｯｸを削除しました。<hr>";
    my $href = &make_href("trackback", $rowid, 0, $eid ,0);
    $data .= "$nostr[0]<a href=\'$href\'$akstr[0]>ﾄﾗｯｸﾊﾞｯｸ一覧へ戻る</a>";
    &htmlout;

    ####################
    # MT3.0以上では、リビルドをバックグラウンドで行う
    if ($cfg{Version} >= 3.0) {
        require MT::Util;
        MT::Util::start_background_task(sub {
            # indexのリビルド
            $mt->rebuild_indexes( Blog => $blog )
                or &errout($mt->errstr);
        });
    } else {
        # indexのリビルド
        $mt->rebuild_indexes( Blog => $blog )
            or &errout($mt->errstr);
    }
}

########################################
# Sub Comment_ipban - このIPからのコメントを禁止＆全削除
########################################
sub comment_ipban {

    # Get MT Object etc.
    &_get_mt_object();

    my $rowid = $no;
    $no--;

    ####################
    # commentを探す
    require MT::Comment;
    my $comment = MT::Comment->load($page);    # コメント番号は$pageで渡す
    if (!$comment) {
        my $cgi = new CGI;
        $cgi->charset('utf-8');
        &errout('comment_ipban::Comment ID "'.$cgi->escapeHTML($page).'" is wrong.');
    }

    require MT::IPBanList;
    my $ban = MT::IPBanList->new;
    $ban->blog_id($blog->id);
    $ban->ip($comment->ip);
    $ban->save
        or &errout($ban->errstr);

    ####################
    # そのIPから送信されたコメントを全て探す
    my @comments = MT::Comment->load(
            { blog_id => $blog_id, ip => $comment->ip});

    for my $comment (@comments) {

        my $entry = _get_entry($comment->entry_id);
        if (!$entry) {
            &errout("comment_ipban::Entry ID '".$comment->entry_id."' is wrong.");
        }

        # コメント削除
        $comment->remove()
            or &errout($comment->errstr);

        ####################
        # MT3.0以上では、リビルドをバックグラウンドで行う
        if ($cfg{Version} >= 3.0) {
            require MT::Util;
            MT::Util::start_background_task(sub {
                # entryのリビルド
                $mt->rebuild_entry( Entry => $entry,, BuildDependencies => 1 )
                    or &errout($mt->errstr);
            });
        } else {
            # entryのリビルド
            $mt->rebuild_entry( Entry => $entry, BuildDependencies => 1 )
                or &errout($mt->errstr);
        }
    }

    $data = "IPを禁止ﾘｽﾄに追加し、".@comments."件のｺﾒﾝﾄを削除しました。<hr>";
    my $href = &make_href("comment", $rowid, 0, $eid, 0);
    $data .= "$nostr[0]<a href=\'$href\'$akstr[0]>ｺﾒﾝﾄ一覧へ戻る</a>";
    &htmlout;

    ####################
    # MT3.0以上では、リビルドをバックグラウンドで行う
    if ($cfg{Version} >= 3.0) {
        require MT::Util;
        MT::Util::start_background_task(sub {
            # indexのリビルド
            $mt->rebuild_indexes( Blog => $blog )
                or &errout($mt->errstr);
        });
    } else {
        # indexのリビルド
        $mt->rebuild_indexes( Blog => $blog )
            or &errout($mt->errstr);
    }
}

########################################
# Sub Email_comments - コメントのメール通知制御
########################################
sub email_comments {

    # Get MT Object etc.
    &_get_mt_object();

    $blog->email_new_comments( ($email_new_comments) ? 0 : 1 );

    $blog->save
        or &errout($blog->errstr);

    $data = ($email_new_comments) ? "ｺﾒﾝﾄのﾒｰﾙ通知を停止しました。<hr>" : "ｺﾒﾝﾄのﾒｰﾙ通知を再開しました。<hr>";

    my $href = &make_href("", 0, $page, 0, 0);
    $data .= "$nostr[0]<a href=\"$href\"$akstr[0]>一覧へ戻る</a>";
    &htmlout;

}

########################################
# Sub Confirm - 各種確認
########################################
sub confirm {

    # Get MT Object etc.
    &_get_mt_object();

    my $rowid = $no;

    # コメントIDは$pageで受け渡し
    if ($mode eq "confirm_comment_del"){

        require MT::Comment;
        my $comment = MT::Comment->load($page);    # コメント番号は$pageで渡す
        if (!$comment) {
            my $cgi = new CGI;
            $cgi->charset('utf-8');
            &errout('confirm_comment_del::Comment ID "'.$cgi->escapeHTML($page).'" is wrong.');
        }
        $data .= "本当に以下のコメントを削除してよろしいですか？<br />";

        $data .= "<form method=\"POST\" action=\"$cfg{MyName}\">";
        $data .= "<input type=\"submit\" value=\"キャンセルする\" />";
        $data .= "<input type=\"hidden\" name=\"id\" value=\"$blog_id\" />";
        $data .= "<input type=\"hidden\" name=\"mode\" value=\"comment\" />";
        $data .= "<input type=\"hidden\" name=\"no\" value=\"$rowid\" />";
        $data .= "<input type=\"hidden\" name=\"page\" value=\"$page\" />";
        $data .= "<input type=\"hidden\" name=\"eid\" value=\"$eid\" />";
        $data .= "<input type=\"hidden\" name=\"key\" value=\"$key\" />";
        $data .= "</form>";
        $data .= "<form method=\"POST\" action=\"$cfg{MyName}\">";
        $data .= "<input type=\"submit\" value=\"削除する\" />";
        $data .= "<input type=\"hidden\" name=\"id\" value=\"$blog_id\" />";
        $data .= "<input type=\"hidden\" name=\"mode\" value=\"comment_del\" />";
        $data .= "<input type=\"hidden\" name=\"no\" value=\"$rowid\" />";
        $data .= "<input type=\"hidden\" name=\"page\" value=\"$page\" />";
        $data .= "<input type=\"hidden\" name=\"eid\" value=\"$eid\" />";
        $data .= "<input type=\"hidden\" name=\"key\" value=\"$key\" />";
        $data .= "</form>";
        $data .= "<hr>";

        $data .= "Author:"._conv_utf8_z2h($comment->author)."<br />";
        $data .= "Text:"._conv_utf8_z2h($comment->text)."<br />";

    } elsif ($mode eq "confirm_entry_del"){

        my $entry = _get_entry($eid);
        if (!$entry) {
            my $cgi = new CGI;
            $cgi->charset('utf-8');
            &errout('confirm_entry_del::Entry ID "'.$cgi->escapeHTML($eid).'" is wrong.');
        }

        require MT::Author;
        my $author = MT::Author->load({ id => $entry->author_id });
        my $author_name = "";
        if ($author) {
            $author_name = _conv_utf8_z2h($author->name);
        }

        $data .= "本当に以下のEntryを削除してよろしいですか？<br />";

        $data .= "<form method=\"POST\" action=\"$cfg{MyName}\">";
        $data .= "<input type=\"submit\" value=\"キャンセルする\" />";
        $data .= "<input type=\"hidden\" name=\"id\" value=\"$blog_id\" />";
        $data .= "<input type=\"hidden\" name=\"mode\" value=\"individual\" />";
        $data .= "<input type=\"hidden\" name=\"no\" value=\"$rowid\" />";
        $data .= "<input type=\"hidden\" name=\"eid\" value=\"$eid\" />";
        $data .= "<input type=\"hidden\" name=\"key\" value=\"$key\" />";
        $data .= "</form>";
        $data .= "<form method=\"POST\" action=\"$cfg{MyName}\" />";
        $data .= "<input type=\"submit\" value=\"削除する\" />";
        $data .= "<input type=\"hidden\" name=\"id\" value=\"$blog_id\" />";
        $data .= "<input type=\"hidden\" name=\"mode\" value=\"entry_del\" />";
        $data .= "<input type=\"hidden\" name=\"no\" value=\"$rowid\" />";
        $data .= "<input type=\"hidden\" name=\"eid\" value=\"$eid\" />";
        $data .= "<input type=\"hidden\" name=\"key\" value=\"$key\" />";
        $data .= "</form>";
        $data .= "<hr>";

        if ($author_name){
            $data .= "Author:".$author_name."<br />";
        }
        $data .= "Text:"._conv_utf8_z2h($entry->text)."<br />";

    } elsif ($mode eq "confirm_trackback_del"){

        require MT::TBPing;
        my $tbping = MT::TBPing->load($page);    # トラックバック番号は$pageで渡す
        if (!$tbping) {
            my $cgi = new CGI;
            $cgi->charset('utf-8');
            &errout('confirm_trackback_del::MTPing ID "'.$cgi->escapeHTML($page).'" is wrong.');
        }

        $data .= "本当に以下のTBを削除してよろしいですか？<br />";

        $data .= "<form method=\"POST\" action=\"$cfg{MyName}\">";
        $data .= "<input type=\"submit\" value=\"キャンセルする\" />";
        $data .= "<input type=\"hidden\" name=\"id\" value=\"$blog_id\" />";
        $data .= "<input type=\"hidden\" name=\"mode\" value=\"trackback\" />";
        $data .= "<input type=\"hidden\" name=\"no\" value=\"$rowid\" />";
        $data .= "<input type=\"hidden\" name=\"page\" value=\"$page\" />";
        $data .= "<input type=\"hidden\" name=\"eid\" value=\"$eid\" />";
        $data .= "<input type=\"hidden\" name=\"key\" value=\"$key\" />";
        $data .= "</form>";
        $data .= "<form method=\"POST\" action=\"$cfg{MyName}\">";
        $data .= "<input type=\"submit\" value=\"削除する\" />";
        $data .= "<input type=\"hidden\" name=\"id\" value=\"$blog_id\" />";
        $data .= "<input type=\"hidden\" name=\"mode\" value=\"trackback_del\" />";
        $data .= "<input type=\"hidden\" name=\"no\" value=\"$rowid\" />";
        $data .= "<input type=\"hidden\" name=\"page\" value=\"$page\" />";
        $data .= "<input type=\"hidden\" name=\"eid\" value=\"$eid\" />";
        $data .= "<input type=\"hidden\" name=\"key\" value=\"$key\" />";
        $data .= "</form>";
        $data .= "<hr>";

        $data .= "BlogName:"._conv_utf8_z2h($tbping->blog_name)."<br />";
        $data .= "Title:"._conv_utf8_z2h($tbping->title)."<br />";
        $data .= "Excerpt:"._conv_utf8_z2h($tbping->excerpt)."<br />";

    } else {
        $data .="confirm::mode '".$mode."' は不正です。<br />";
    }

    &htmlout;
}

########################################
# Sub Separate - 単記事・コメント本文の分割
########################################

sub separate {
    my $text = $_[0];
    my $rowid = $_[1];

    # 区切り文字列を配列に格納しておく
    my @sprtstrlist = split(",",$cfg{SprtStr});

    # 本文のバイト数を求めておく
    my $maxlen = MT4i::Enc::lenb_sjis($text);

    # 初回に分割位置を決め、$sprtbyteへ格納
    if (!$sprtbyte) {
        $sprtpage = 1;
        my $i = 0;
        $sprtbyte = "0";
        while ($i < $maxlen - $cfg{SprtLimit}) {
            my $tmpstart = $i;
            my $tmpend;

            $tmpend = ($tmpstart + $cfg{SprtLimit} > $maxlen) ? $maxlen - $tmpstart : $cfg{SprtLimit};

            # 区切り文字列の検出
            my $sprtstart;
            my $tmptext = MT4i::Enc::substrb_sjis($text, $tmpstart, $tmpend);
            foreach my $tmpsprtstr (@sprtstrlist) {
                if ($tmptext =~ /(.*)$tmpsprtstr/s) {
                    $tmptext = $1;
                    $sprtstart = MT4i::Enc::lenb_sjis($tmptext) + MT4i::Enc::lenb_sjis($tmpsprtstr);
                    last;
                }
            }
            if (!$sprtstart) {
                $sprtstart = $maxlen;
            }

            $sprtstart = $sprtstart + $tmpstart;

            # 分割位置を$sprtbyteに格納
            if ($sprtstart < $maxlen) {
                $sprtbyte .= ",$sprtstart";
            }
            $i = $sprtstart + 1;
        }
    }

    # $sprtbyteを読み取る
    my @argsprtbyte = split(/,/, $sprtbyte);
    my $sprtstart = $argsprtbyte[$sprtpage - 1];
    my $sprtend;
    $sprtend = ($sprtpage - 1 < $#argsprtbyte) ? $argsprtbyte[$sprtpage] - $sprtstart : $maxlen - $sprtstart;

    ####################
    # 本文文字列生成

    # まずは記事本文切抜き
    my $text = MT4i::Enc::substrb_sjis($text, $sprtstart, $sprtend);

    ##### 足りないタグを補ってみる #####
    my $cnt_tag_o;
    my $cnt_tag_c;
    # ULタグ
    $cnt_tag_o = ($text =~ s!<ul!<ul!ig);
    $cnt_tag_c = ($text =~ s!</ul!</ul!ig);
    if ($cnt_tag_o < $cnt_tag_c) {
        for (my $i = 0; $i < $cnt_tag_c - $cnt_tag_o; $i++) {
            $text = '<ul>' . $text;
        }
    } elsif ($cnt_tag_o > $cnt_tag_c) {
        for (my $i = 0; $i < $cnt_tag_o - $cnt_tag_c; $i++) {
            $text .= '</ul>';
        }
    }
    # OLタグ
    $cnt_tag_o = ($text =~ s!<ol!<ol!ig);
    $cnt_tag_c = ($text =~ s!</ol!</ol!ig);
    if ($cnt_tag_o < $cnt_tag_c) {
        for (my $i = 0; $i < $cnt_tag_c - $cnt_tag_o; $i++) {
            $text = '<ol>' . $text;
        }
    } elsif ($cnt_tag_o > $cnt_tag_c) {
        for (my $i = 0; $i < $cnt_tag_o - $cnt_tag_c; $i++) {
            $text .= '</ol>';
        }
    }
    # BLOCKQUOTEタグ
    $cnt_tag_o = ($text =~ s!<blockquote!<blockquote!ig);
    $cnt_tag_c = ($text =~ s!</blockquote!</blockquote!ig);
    if ($cnt_tag_o < $cnt_tag_c) {
        for (my $i = 0; $i < $cnt_tag_c - $cnt_tag_o; $i++) {
            $text = '<blockquote>' . $text;
        }
    } elsif ($cnt_tag_o > $cnt_tag_c) {
        for (my $i = 0; $i < $cnt_tag_o - $cnt_tag_c; $i++) {
            $text .= '</blockquote>';
        }
    }
    # FONTタグ
    $cnt_tag_o = ($text =~ s!<font!<font!ig);
    $cnt_tag_c = ($text =~ s!</font!</font!ig);
    if ($cnt_tag_o < $cnt_tag_c) {
        for (my $i = 0; $i < $cnt_tag_c - $cnt_tag_o; $i++) {
            $text = '<font>' . $text;
        }
    } elsif ($cnt_tag_o > $cnt_tag_c) {
        for (my $i = 0; $i < $cnt_tag_o - $cnt_tag_c; $i++) {
            $text .= '</font>';
        }
    }

    return $text;
}

########################################
# Sub Conv_utf8_z2h - to UTF-8 and Zen to Han
########################################

sub _conv_utf8_z2h {
    my $tmpstr = shift;

    return $tmpstr unless $tmpstr;

    # convert to utf8
    if ($conv_in ne "utf8") {
        $tmpstr = Encode::decode($conv_in, $tmpstr);
    } else {
        $tmpstr = MT4i::Enc::decode_utf8($tmpstr);
    }
    $tmpstr = MT4i::Enc::replace_garbled_characters($tmpstr, $ejpemoji);
 
    # The em-size character is converted into the one-byte character.
    if ($cfg{Z2H} eq "yes") {
        $tmpstr = MT4i::Enc::zen2han($tmpstr);
    }
    return $tmpstr;
}

########################################
# Sub Conv_Redirect - リンクのURLをリダイレクタ経由に変換
########################################

sub conv_redirect {
    my $tmpstr = $_[0];
    my $ref_rowid = $_[1];
    my $ref_eid = $_[2];
    my $str = "";

    # ループしながらURLの置換
    while ($tmpstr =~ /(<a [^>]*>)/i) {
        my $left   = $`;
        my $middle = $1;
        my $right  = $';
        my $lnkstr = "";

        my $title = $1 if ($middle =~ /title=["']([^"'>]*)["']/);
        my $href = $1 if ($middle =~ /href=["']([^"'>]*)["']/);

        # convert flickr page link to direct image
        if ($href =~ /http:\/\/www.flickr.com\/photos\/.+\/(\w+)\//) {
            require LWP::Simple;
            my $url = 'http://www.flickr.com/services/rest/?api_key=b77db76d68a48ee10a584dde92c46ffd&method=flickr.photos.getSizes&photo_id='.$1;
            my $content = LWP::Simple::get($url);
            errout('') unless $content;

            require XML::Simple;
            my $parser = new XML::Simple();
            $data = $parser->XMLin($content);
            $href = $data->{sizes}{size}[3]{source};
        }

        # return or convert url to resizer if image link.
        if ($href =~ /(?:\.jpg|\.jpeg|\.gif|\.png)/) {
            unless ($right =~ /^<img/) {
                # create href string
                $href = _conv_url2resizer($href);
            }
            $str .= $left . '<a href="' . $href . '">';
            $tmpstr = $right;
            next;
        }

        if ($cfg{ChtmlTrans} && $href !~ /^#/ && $href !~ /^mailto:/) {
            my $ExitChtmlTrans = MT4i::Enc::decode_utf8($cfg{ExitChtmlTrans});
            if ($title !~ /$ExitChtmlTrans/) {
                $href = _conv_url_to_redirector($href, $ref_rowid, $ref_eid);
            } else {
                # Icon for cellular phone
                $lnkstr = $ExitChtmlTransStr;
            }
        }
        # Unites supplementing a double quotation.
        $str .= $left . '<a href="' . $href . '">' . $lnkstr;
        $tmpstr = $right;

    }
    $str .= $tmpstr;

    return $str;
}

########################################
# Sub _Conv_URL_To_Redirector 
########################################

sub _conv_url_to_redirector {
    my ($url, $rowid, $eid) = @_;

    return $url if ($url =~ /http:\/\/hb.afl.rakuten.co.jp\/hgc\//);

    # Convert sorce URL to redirector
    my $tmpurl = &make_href("redirect", $rowid, 0, 0, $eid);

    # URL encode
    $url = MT4i::Func::url_encode($url);

    $url = $tmpurl . '&amp;url=' . $url;

    return $url;
}

########################################
# Sub Redirector - リダイレクタ
########################################

sub redirector {
    # HTMLテンプレートをオープン
    my $template = _tmpl_open('redirector.tmpl');

    # URLを変換
    my ($lnkstr,$lnkurl) = &chtmltrans($redirect_url);

    $template->param(MLD_STR => $lnkstr) if $lnkstr;
    $template->param(SOURCE_URL => $redirect_url);
    $template->param(MOBILE_URL => $lnkurl);

    my $href = &make_href("individual", $no, 0, $ref_eid, 0);
    $template->param(BACK_URL => $href);

    # Common
    $template = _tmpl_common($template);

    # Output
    &_cacheout($template);
}

########################################
# Sub Chtmltrans - リンクのURLをchtmltrans経由その他に変換
# 参考：Perlメモ→http://www.din.or.jp/~ohzaki/perl.htm#HTML_Tag
########################################

sub chtmltrans {
    my $url = $_[0];
    my $lnkstr = "";

    if ($url =~ m/.*http:\/\/www.amazon.co.jp\/exec\/obidos\/ASIN\/.*/g) {
        # Amazon個別商品リンクならi-mode対応へ変換
        $url =~ s!exec/obidos/ASIN/!gp/aw/rd.html\?a=!g;
        $url =~ s!ref=nosim/!!g;
        $url =~ s!ref=nosim!!g;
        $url =~ s!/$!!g;
        $url =~ s!/([^/]*-22)!&amp;uid=NULLGWDOCOMO&amp;url=/gp/aw/d.html&amp;lc=msn&amp;at=$1!;
        $url .= '&amp;dl=1';
        $lnkstr = $mt4ilinkstr;
    } elsif ($url =~ m!.*http://www.amazon.co.jp/gp/product/.*!g) {
        # 新 Amazon リンクなら携帯対応 URL へ変換
        # 個別商品リンクのテキストのみ
        $url =~ s!(http://www.amazon.co.jp/gp/)product/(.*)\?ie=(.*)&tag=(.*)&linkCode.*!$1aw/rd.html?ie=$3&dl=1&uid=NULLGWDOCOMO&a=$2&at=$4&url=%2Fgp%2Faw%2Fd\.html!g;
    } elsif ($url =~ m/.*http:\/\/www.amazon.co.jp\/gp\/redirect.html.*/g) {
        # 新 Amazon リンクなら携帯対応 URL へ変換
        # テキストリンク | 特定のページ
        $url =~ s!(http://www.amazon.co.jp/gp/).*product/(.*)\?ie=(.*)&tag=(.*)&linkCode.*!$1aw/rd.html?ie=$3&dl=1&uid=NULLGWDOCOMO&a=$2&at=$4&url=%2Fgp%2Faw%2Fd\.html!g;
    } elsif ($url =~ m/.*http:\/\/www.amazlet.com\/browse\/ASIN\/.*/g) {
        # Amazletへのリンクなら、Amazonのi-mode対応へ変換
        $url =~ s!www.amazlet.com/browse/ASIN/!www.amazon.co.jp/gp/aw/rd.html?a=!g;
        $url =~ s!/ref=nosim/!!g;
        $url =~ s!/$!!g;
        $url =~ s!/([^/]*-22)!&amp;uid=NULLGWDOCOMO&amp;url=/gp/aw/d.html&amp;lc=msn&amp;at=$1!;
        $url .= '&amp;dl=1';
        $lnkstr = $mt4ilinkstr;
    } elsif ($url =~ m!.*http://www.nicovideo.jp/.*!g) {
        # NicoNicoDouga
        $url =~ s/www.nicovideo.jp/m.nicovideo.jp/g;
    } else {
        # リンク先を取得
        my $mt4ilink = MT4i::Func::get_mt4ilink($url);

        if ($mt4ilink) {
            $url = $mt4ilink;
            $lnkstr = $mt4ilinkstr;
        } else {
            if ($cfg{MobileGW} eq '1') {              # 通勤ブラウザ
                # 'http://'を削除
                $url =~ s!http://!!g;
                # URLを生成
                my $chtmltransurl = 'http://www.sjk.co.jp/c/w.exe?y=';
                $url = $chtmltransurl . $url;
            } elsif ($cfg{MobileGW} eq '2') {           # Google mobile Gateway
                # "/"→"%2F"、"?"→"%3F"、"+"→"%2B"
                $url =~ s/\//\%2F/g;
                $url =~ s/\?/\%3F/g;
                $url =~ s/\+/\%2B/g;
                # URLを生成
                my $chtmltransurl = 'http://www.google.co.jp/gwt/n?u=';
                $url = $chtmltransurl . $url;
            }
        }
    }
    return ($lnkstr,$url);
}

########################################
# Sub Htmlout - HTMLの出力
########################################

sub htmlout {
    # blog_nameから改行を削除
    my $hd_blog_name = MT4i::Enc::decode_utf8($blog_name);
    $hd_blog_name =~ s!<br />!!ig; 
    $hd_blog_name =~ s!<br />!!ig; 

    # HTMLヘッダ/フッタ定義
    $data = <<HEADER;
<?xml version="1.0" encoding="Shift_JIS"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="ja" xml:lang="ja">
<head>
    <meta http-equiv="Content-Type" content="application/xhtml+xml; charset=Shift_JIS" />
    <meta name="description" content="(ページ説明)" />
    <meta http-equiv="cache-control" content="no-cache" />
    <meta http-equiv="Pragma" content="no-cache" />
    <meta name="robots" content="index,follow" />
    <title>$hd_blog_name mobile ver.</title>
</head>
<body bgcolor="$cfg{BgColor}" text="$cfg{TxtColor}" link="$cfg{LnkColor}" alink="$cfg{AlnkColor}" vlink="$cfg{VlnkColor}">
$data
HEADER
    if (exists $cfg{AdmNM}) {
        $data .= '<p style="text-align:center">管理人:';
        if (exists $cfg{AdmML}) {
            $cfg{AdmML} =~ s/\@/\&#64;/g;
            $cfg{AdmML} =~ s/\./\&#46;/g;
            $data .= '<a href="mailto:'.MT4i::Enc::decode_utf8($cfg{AdmML}).'">'.MT4i::Enc::decode_utf8($cfg{AdmNM}).'</a>';
        } else {
            $data .= MT4i::Enc::decode_utf8($cfg{AdmNM});
        }
        $data .= "</p>";
    }
    $data .= '<p style="text-align:center">Powered by<br />';
    # 管理者モードではMT4i公式ページへのアンカーを表示しない
    $data .=  ($admin_mode eq 'yes')
        ? "MT4i v$version"
        : "<a href=\"http://hazama.nu/pukiwiki/?MT4i\">MT4i v$version</a>";
    $data .= "</p></body></html>";

    # 表示文字列をShift_JISに変換
    $data = MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, MT4i::Enc::decode_utf8($data));

    # Convert emoticon tags to binaries
    $data = _conv_tag2binary($data);

    # 表示
    binmode(STDOUT);
    print "Content-type: text/html; charset=Shift_JIS\n";
    print "Content-Length: ",length($data),"\n\n";
    print $data;
}

########################################
# Sub Errout - エラーの出力
########################################

sub errout {
    my $str = shift;

    # Open template file and set parameter
    my $template = _tmpl_open('error.tmpl');
    $template->param(ERROR_MESSAGE => $str);

    # Write log
    eval {require $log_pl; 1};
    if ($@) {
        print "Content-type: text/plain; charset=UTF-8\n\nFile not found: $log_pl";
        exit;
    }
    MT4i::Log::writelog($str);

    # Common
    $template = _tmpl_common($template);

    # Output
    &_cacheout($template);
}

##############################################################
# Sub conv_datetime - YYYYMMDDhhmmssを MM/DD hh:mm に変換
##############################################################

sub conv_datetime {
    $_[0] =~ s/\d\d\d\d(\d\d)(\d\d)(\d\d)(\d\d)\d\d/($1\/$2 $3:$4)/;
    return $_[0];
}

############################################################
# Sub Check_Category - エントリのプライマリカテゴリラベルを取得
#  プライマリカテゴリが非表示設定されている場合は最初に出てきた
#  サブカテゴリのラベルを取得
############################################################
sub check_category{
    my ($entry) = @_;
    my $cat_label;
    require MT::Category;
    require MT::Placement;
    my @categories = MT::Category->load({ blog_id => $blog_id }, { unique => 1 });
    if (@categories) {
        my $place = MT::Placement->load({ entry_id => $entry->id, is_primary => 1 });
        if ($place) {
            my $match_cat = 0;
            if ($mode ne 'entryform' || $admin_mode eq 'no') {
                my @nondispcats = MT4i::Func::get_nondispcats();
                $match_cat = 1
                    if (first { $place->category_id == $_ } @nondispcats);
            }
            if ($match_cat == 0) {
                my $category = first { $_->id == $place->category_id } @categories;
                $cat_label = _conv_utf8_z2h( ($category && $cfg{CatDescReplace} eq "yes")
                    ? $category->description
                    : $category->label
                );
            } else {
                my @places = MT::Placement->load({ entry_id => $entry->id });
                my @nondispcats = MT4i::Func::get_nondispcats();
                for my $category (@categories) {
                    if (!(first { $category->id == $_ } @nondispcats)
                            && first { $category->id == $_->category_id } @places) {
                        $cat_label = _conv_utf8_z2h( ($cfg{CatDescReplace} eq "yes")
                            ? $category->description
                            : $category->label
                        );
                        last;
                    }
                }
            }
        }
    }
    return $cat_label;
}

##################################################
# Sub Get_CatList - セレクタ用カテゴリリストの取得
##################################################
sub get_catlist {
    my @categories;

    require MT::Category;
    my @cats = MT::Category->top_level_categories($blog_id);

    # ソート
    my @s_cats = &sort_cat(@cats);

    # サブカテゴリの取得
    foreach my $category (@s_cats) {
        my @c_cats = &get_subcatlist($category, 0);
        foreach my $c_category (@c_cats) {
            push @categories, $c_category;
        }
    }
    return @categories;
}

##################################################
# Sub Get_SubCatList - セレクタ用サブカテゴリリストの取得
##################################################
sub get_subcatlist {
    my $category = shift;
    my $hierarchy = shift;

    # 管理者モードでない場合には非表示カテゴリを処理する
    # 親カテゴリが非表示なら子カテゴリも表示しない
    if ($admin_mode ne "yes"){
        my @nondispcats = MT4i::Func::get_nondispcats();
        return
            if (first { $category->id == $_ } @nondispcats);
    }

    ####################
    # カテゴリの列挙
    my %terms = (blog_id => $blog_id);
    # 管理者モードでなければステータスが'公開'のエントリのみカウント
    if ($admin_mode ne "yes"){
        $terms{'status'} = 2;
    }
    require MT::Entry;
    require MT::Placement;
    my $count = MT::Entry->count( \%terms,
                                { join => [ 'MT::Placement', 'entry_id',
                                { blog_id => $blog_id, category_id => $category->id } ] });
    #if ($count == 0) {
    #    return;
    #}

    my @categories;

    my $blank;
    foreach (my $i = 0; $i < $hierarchy; $i++) {
        $blank .= "-";
    }

    my $id = $category->{column_values}->{id};
    my $label;
    if ($cfg{CatDescReplace} eq "yes"){
        $label = _conv_utf8_z2h($category->{column_values}->{description});
        # カテゴリ名ぶった切り
        if ($cfg{LenCutCat} > 0) {
            if (MT4i::Enc::lenb_sjis($label) > $cfg{LenCutCat}) {
                $label = MT4i::Enc::substrb_sjis($label, 0, $cfg{LenCutCat});
            }
        }
        $label = $blank . $label;
    } else {
        $label = _conv_utf8_z2h($category->{column_values}->{label});
        # カテゴリ名ぶった切り
        if ($cfg{LenCutCat} > 0) {
            if (MT4i::Enc::lenb_sjis($label) > $cfg{LenCutCat}) {
                $label = MT4i::Enc::substrb_sjis($label, 0, $cfg{LenCutCat});
            }
        }
        $label = $blank . $label;
    }

    my $selected = ($cat == $id) ? ' selected' : '' ;
    push @categories, "<option value=\"$id\"$selected>$label($count)</option>";

    require MT::Category;
    my @cats = $category->children_categories;
    if (@cats) {
        # ソート
        my @s_cats = &sort_cat(@cats);

        # サブカテゴリの取得
        foreach my $s_cat (@s_cats) {
            my @c_cats = &get_subcatlist($s_cat, $hierarchy + 1);
            foreach my $c_cat (@c_cats) {
                push @categories, $c_cat;
            }
        }
    }
    return @categories;
}

##################################################
# Sub Sort_Cat - セレクタ用カテゴリリストのソート
##################################################
sub sort_cat {
    my @cats = @_;

    if ($cfg{CatDescSort} eq "asc"){
        @cats = sort { $a->{column_values}->{label} cmp $b->{column_values}->{label} } @cats;
    }elsif ($cfg{CatDescSort} eq "desc"){
        @cats = reverse sort { $a->{column_values}->{label} cmp $b->{column_values}->{label} } @cats;
    }
    return @cats;
}

##################################################
# Sub _Tmpl_Common - Fill the common parameter.
##################################################
sub _tmpl_common {
    my $tmpl = shift;

    # Blog ID
    $tmpl->param(BLOG_ID => $blog_id) if $blog_id;

    # Blog Title
    if ($tmpl->query(name => 'BLOG_TITLE') eq 'VAR' && $blog_name) {
        # blog_nameから改行を削除
        my $hd_blog_name = $blog_name;
        $hd_blog_name =~ s!<br />!!ig;
        $hd_blog_name =~ s!<br />!!ig;
        $tmpl->param(BLOG_TITLE => MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, _conv_utf8_z2h($hd_blog_name)));
    }

    # Blog Description
    $tmpl->param(BLOG_DESCRIPTION => MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, _conv_utf8_z2h($description)))
        if $description;

    # My(Script)Name
    $tmpl->param(SCRIPT_NAME => $cfg{MyName});

    # Color
    $tmpl->param(BODY_BG_COLOR    => $cfg{BgColor});
    $tmpl->param(BODY_TEXT_COLOR  => $cfg{TxtColor});
    $tmpl->param(BODY_LINK_COLOR  => $cfg{LnkColor});
    $tmpl->param(BODY_ALINK_COLOR => $cfg{AlnkColor});
    $tmpl->param(BODY_VLINK_COLOR => $cfg{VlnkColor});
    $tmpl->param(BODY_BQ_COLOR    => $cfg{BqColor});

    # Agent
    $tmpl->param(AGENT_DOCOMO     => 1) if $ua eq 'i-mode';
    $tmpl->param(AGENT_AU         => 1) if $ua eq 'ezweb';
    $tmpl->param(AGENT_SOFTBANK   => 1) if $ua eq 'j-sky';
    $tmpl->param(AGENT_OTHER      => 1) if $ua eq 'other';
    $tmpl->param(AGENT_SMARTPHONE => 1) if $ua eq 'smartphone';

    # Get serial No.
    $tmpl->param(SERNO => 1) if $cfg{SerNo};

    # Version No.
    if ($tmpl->query(name => 'VERSION') eq 'VAR' && $version) {
        require Encode;
        $tmpl->param(VERSION => MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, MT4i::Enc::decode_utf8($version)));
    }

    # Emoticon
    $tmpl = __emoticon($tmpl);

    # Admin mode
    $tmpl->param(ADMIN_MODE => $admin_mode eq "yes" ? 1 : 0 );

    return $tmpl;
}

##################################################
# Sub __Emoticon - Fill the emoticon to HTML Template
##################################################
sub __emoticon {
    my $tmpl = shift;
    if ($cfg{AccessKey} eq "no" || ($cfg{AccessKey} eq "yes" && $ua ne "i-mode" && $ua ne "ezweb" && $ua ne "j-sky")) {
        for (my $i = 0; $i < 10; $i++) {
            $tmpl->param("ICON_NO_$i" => '');
        }
        for (my $i = 0; $i < 10; $i++) {
            $tmpl->param("ACCESS_KEY_$i" => '');
        }
        $tmpl->param("ICON_NO_ASTERISK" => '');
        $tmpl->param("ICON_NO_SHARP" => '');
        $tmpl->param("ACCESS_KEY_ASTERISK" => '');
        $tmpl->param("ACCESS_KEY_SHARP" => '');
        $tmpl->param('ICON_CLOCK' => '');
    } else {
        for (my $i = 0; $i < 10; $i++) {
            $tmpl->param("ICON_NO_$i" => $nostr[$i]);
        }
        for (my $i = 0; $i < 10; $i++) {
            $tmpl->param("ACCESS_KEY_$i" => $akstr[$i]);
        }
        $tmpl->param("ICON_NO_ASTERISK" => $nostr[10]);
        $tmpl->param("ICON_NO_SHARP" => $nostr[11]);
        $tmpl->param("ACCESS_KEY_ASTERISK" => $akstr[10]);
        $tmpl->param("ACCESS_KEY_SHARP" => $akstr[11]);
        $tmpl->param('ICON_CLOCK' => $clock_icon);
    }
    return $tmpl;
}

##################################################
# Sub _Set_Mode_To_Tmpl - Set mode string to template
##################################################
sub _set_mode_to_tmpl {
    my $tmpl = shift;

    my $modestr = $mode ? $mode : 'index';
    $tmpl->param("MODE_$modestr" => 1);

    return $tmpl;
}

##################################################
# Sub _ReadCache
##################################################
sub _readcache {
    my ($key, $return_not_mod) = @_;

    return 0 if ($cfg{CacheTime} < 1 || $admin_mode eq 'yes');

    my $cache_file = $cfg{MT_DIR}.'mt4i/cache/page/'.$key;

    # Returns, if the cache file exists or it is size 0.
    return 0 if (!-e $cache_file || -z $cache_file);

    # Return 304 if the cache file doesn't modified.
    if ($return_not_mod) {
        my $if_mod_since_gmt = $ENV{'HTTP_IF_MODIFIED_SINCE'};
        my $cache_last_mod = (stat $cache_file)[9];
        if ($if_mod_since_gmt && $cache_last_mod) {
            my $if_mod_since = str2time($if_mod_since_gmt);
            $cache_last_mod_gmt = time2str($cache_last_mod);
            my $user_agent = $ENV{'HTTP_USER_AGENT'};
            my $logstr = $user_agent.', '.$if_mod_since_gmt.', '.$cache_last_mod_gmt;
            eval {require $log_pl; 1} or &errout('File not found: '.$log_pl);
            if ($if_mod_since >= $cache_last_mod) {
                print "Status: 304 Not Modified\n";
                print "Last-Modified: $cache_last_mod_gmt\n\n";
                $logstr .= ', 304 Not Modified';
                MT4i::Log::writelog($logstr);
                exit;
            }
            MT4i::Log::writelog($logstr);
        }
    }

    my $mtime = (stat($cache_file))[9];
    my $ntime = time();

    return 0 if ($ntime - $mtime >= $cfg{CacheTime}*60);

    my $tmpl_ref;
    eval { $tmpl_ref = lock_retrieve($cache_file); };
    &errout('retrieve cache failed: '.$@) if($@);

    return $$tmpl_ref;
}

##################################################
# Sub _CacheOut
##################################################
sub _cacheout {
    my ($tmpl) = @_;

    # Mode
    &_set_mode_to_tmpl($tmpl);

    # Adsense
    my $adsense_pl = $bin.'/lib/mt4i/Adsense.pl';
    if ($tmpl->query(name => 'ADSENSE') eq 'VAR') {
        my $adsense = (-e $adsense_pl)
                      ? `perl $adsense_pl`
                      : MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, 'Error: Adsense.pl が見付かりません。');
        $tmpl->param(ADSENSE => $adsense);
    }

    # Google Analytics
    if ($tmpl->query(name => 'GOOGLE_ANALYTICS') eq 'VAR') {
        my $g_analytics_pl = $bin.'/lib/mt4i/GoogleAnalytics.pl';
        if (-e $g_analytics_pl) {
            eval{require $g_analytics_pl; 1};
            my $anastr = '<img src="'.google_analytics_get_image_url().'" />';
            $tmpl->param(GOOGLE_ANALYTICS => $anastr);
        } else {
            &errout('File not found: '.$g_analytics_pl);
        }
    }

    # Advertisement Exchange
    if ($tmpl->query(name => 'AD_EXCHANGE') eq 'VAR') {
        my $ad_pl = $bin.'/lib/mt4i/Ad.pl';
        eval {require $ad_pl; 1} or &errout('File not found: '.$ad_pl);
        my $adstr = MT4i::Ad::ad_exchange($ua);
        $tmpl->param(AD_EXCHANGE => $adstr);
    }

    my $cdata = $tmpl->output;

    my $content_type = $ua ne 'other' && $cfg{ContentType} eq 'xhtml' 
                     ? "application/xhtml+xml"
                     : "text/html";

    eval {
        binmode(STDOUT);
        print "Content-Type: $content_type;charset=Shift_JIS\n";
        print "Last-Modified: $cache_last_mod_gmt\n" if $cache_last_mod_gmt;
        print "Content-Length: ".length($cdata)."\n";
        print "\n";
        print $cdata;
    };
    &errout('output failed: '.$@) if($@);

    exit;
}

##################################################
# Sub _WriteCache
##################################################
sub _writecache {
    my ($key, $template) = @_;

    return 0 if ($cfg{CacheTime} < 1 || $admin_mode eq 'yes');

    # make directory
    my @directories = split('/', $key);
    my $dirstr = $cfg{MT_DIR}.'mt4i/cache/page/';
    for (my $i = 0; $i < $#directories; $i++) {
        if (!(-d $dirstr.$directories[$i])) {
            mkdir($dirstr.$directories[$i]);
        }
        $dirstr .= $directories[$i].'/';
    }

    # write cache
    my $cache_file = $cfg{MT_DIR}.'mt4i/cache/page/'.$key;

    eval { lock_store(\$template, $cache_file); };
    &errout('store cache failed: '.$@) if($@);
}

##################################################
# Sub PurgeCache
##################################################
sub purgecache {
    my ($key) = @_;
    my $cache_file = $cfg{MT_DIR}.'mt4i/cache/page/'.$key;
    my @fnames = glob($cache_file);
    for my $fname (@fnames) {
        next if (!-e $fname || -z $fname );

        open(OUT,">> $fname") or &errout("Can't open $fname : $!");
        flock(OUT, 2) or &errout("Can't flock  : $!");
        truncate(OUT,0) or &errout("Can't truncate  : $!");
        close(OUT);

        eval {require $log_pl; 1} or &errout('File not found: '.$log_pl);
        MT4i::Log::writelog('truncate cache file: '.$fname);
    }
}

##################################################
# Sub _Tmpl_Open
##################################################
sub _tmpl_open {
    my $file = shift;
    my $filepath = (-e "$bin/tmpl/mt4i/$blog_id/$file")
                        ? "$bin/tmpl/mt4i/$blog_id/$file" : "$bin/tmpl/mt4i/$file";
    my $tmpl;
    eval {
        $tmpl = HTML::Template->new(filename => $filepath,
                                    die_on_bad_params => 0,
                                    loop_context_vars  => 1,
                                    file_cache => 1,
                                    file_cache_dir => $cfg{MT_DIR}.'mt4i/cache/tmpl',
                                    );
    };
    if ($@) {
        # To prevent an infinite loop, another error processing is done.
        print "Content-type: text/plain; charset=UTF-8\n\nLoading template '$filepath' failed: $@";
        exit;
    }
    return $tmpl;
}

##################################################
# Sub _get_mt_object
##################################################
sub _get_mt_object {
    # create MT object
    eval { use MT; };
    &errout($@) if ($@);
    $mt = MT->new;

    # set mt version
    $cfg{Version} = $mt->version_number();;

    # added path of packs to @INC
    if ($cfg{Version} >= 4.1) {
        my $packs = $mt->find_addons('pack');
        for my $pack (@{$packs}){
            push @INC, $pack->{path};
        }
    }

    # The presence of Encode.pm is confirmed.
    eval 'use Encode;';
    if($@){
        $ecd = 0;
    }else{
        eval 'use Encode::JP::H2Z;';
        $ecd = 1;
    }

    # Get PublishCharset
    $conv_in = lc $mt->{cfg}->PublishCharset eq lc "Shift_JIS"   ? "sjis"
             : lc $mt->{cfg}->PublishCharset eq lc "ISO-2022-JP" ? "jis"
             : lc $mt->{cfg}->PublishCharset eq lc "UTF-8"       ? "utf8"
             : lc $mt->{cfg}->PublishCharset eq lc "EUC-JP"      ? "euc"
             : "utf8";

    # if blog ID is not set, display error message.
    if (!$blog_id) {
        # Open template file
        my $template = _tmpl_open('blog_list.tmpl');

        # Get blog list.
        require MT::Blog;
        my @blogs = MT::Blog->load(undef, {unique => 1});

        # Sort
        @blogs = sort {$a->id <=> $b->id} @blogs;

        # Get new array
        my @blog_list = ();

        # Set values.
        for my $blog (@blogs) {
            # Get new hash for row data.
            my %row_data;

            $row_data{BLOG_ID} = $blog->id;
            $row_data{BLOG_NAME} = MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, _conv_utf8_z2h($blog->name));
            $row_data{BLOG_URL} = './'.$cfg{MyName}.'?id=' . $blog->id . ($admin_mode eq "yes" ? '&key='.$key : '');
            $row_data{BLOG_DESCRIPTION} = MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, _conv_utf8_z2h($blog->description));

            push(@blog_list, \%row_data);
        }

        $template->param(BLOGS => \@blog_list);

        # Common
        $template = _tmpl_common($template);

        # Output
        &_cacheout($template);
    }

    # Get blog name and blog description
    require MT::Blog;
    $blog = MT::Blog->load($blog_id,
                          {unique => 1});

    # wrong blog ID
    if (!$blog) {
        my $cgi = new CGI;
        $cgi->charset('utf-8');
        &errout('Blog ID "'.$cgi->escapeHTML($blog_id).'" is wrong.');
    }

    # The setting that relates to the blog name, the outline,
    # and the comment is stored in the variable.
    #$blog_name = _conv_utf8_z2h($blog->name);
    #$description = _conv_utf8_z2h($blog->description);
    $blog_name = $blog->name;
    $description = $blog->description;
    $sort_order_comments = $blog->sort_order_comments;
    $email_new_comments = $blog->email_new_comments;
    $email_new_pings = $blog->email_new_pings;
    $convert_paras = $blog->convert_paras;
    $convert_paras_comments = $blog->convert_paras_comments;
}

sub _neighbor_entry {
    my ($entry, $category_id, $prev_or_next) = @_;
    my $direction = ($prev_or_next eq 'next') ? 'ascend' : 'descend';
    my %terms = (
        blog_id => $entry->blog_id,
        status => 2
    );
    my %args = (
        direction => $direction,
       limit => 1,
       'join' => [ 'MT::Placement', 'entry_id',
                 { blog_id => $entry->blog_id, category_id => $category_id },
                 { unique => 1 } ],
    );
    $args{'sort'} = $cfg{Version} >= 4.0 ? 'authored_on' : 'created_on';
    $args{'start_val'} = $cfg{Version} >= 4.0 ? $entry->authored_on : $entry->created_on;

    return MT::Entry->load( \%terms, \%args );
}

sub _get_entry {
    my $eid = shift;
    my $entry;

    # Read cache
    $entry = _readcache('b'.$blog_id.'/e'.$eid.'/obj', 0);
    return $entry if $entry;

    # Load entry
    require MT::Entry;
    my $entry = MT::Entry->load($eid);

    # Write cache
    _writecache('b'.$blog_id.'/e'.$eid.'/obj', $entry);
    return $entry;
}

sub _get_customfields {
    my $obj = shift;

    eval { require CustomFields::Util; };

    return if ($@);

    my $meta = CustomFields::Util::get_meta($obj);

    return $meta;
}

##################################################
# Search - Search blog
##################################################
sub search {
    my $str = $q->param("search_keyword");
    my $offset = $q->param("offset") || 0;
    my $limit = $q->param("limit") || 5;

    my @keywords = split ' ', $str;

    my $encode_keywords;
    my $encode_keywords_shiftjis;
    for my $keyword (@keywords) {
        $encode_keywords .= '+' if $encode_keywords;
        $encode_keywords_shiftjis .= '+' if $encode_keywords;

        require Encode;
        $encode_keywords .= MT4i::Func::url_encode(Encode::encode($enc_e4u_utf8, Encode::decode($enc_e4u_sjis, $keyword)));
        $encode_keywords_shiftjis .= MT4i::Func::url_encode($keyword);
    }

    my $data;
    my $cache_key = 'b'.$blog_id.'/search/'.$encode_keywords.'-offset-'.$offset.'-limit-'.$limit.'-ua-'.$ua;

    # read cache
    if ($admin_mode eq 'no') {
        $data = _readcache($cache_key);
    }

    unless ($data) {
        # Get MT Object etc.
        &_get_mt_object();

        errout(MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, '検索機能は MT 4.15 以降でのみ使用可能です。'))
            if ($cfg{Version} < 4.15);

        my $url = _get_cgipath();
        $url .= $mt->config('SearchScript').'?search='.$encode_keywords.'&Template=feed';
        $url .= '&IncludeBlogs='.$blog_id if $blog_id;
        $url .= '&offset='.$offset if $offset;
        $url .= '&limit='.$limit if $limit;
        require LWP::Simple;
        my $content = LWP::Simple::get($url);
        errout('') unless $content;

        require XML::Simple;
        $XML::Simple::PREFERRED_PARSER = 'XML::Parser';
        my $parser = new XML::Simple(ForceArray => 'entry');
        $data = $parser->XMLin($content);

        _writecache($cache_key, $data);
    }
 
    my $total_results = $data->{'opensearch:totalResults'}[0];
    my @result_entries = @{$data->{'entry'}} if $total_results;
    
    # Open template file
    my $template = _tmpl_open('search_results.tmpl');

    my @search_results = ();
    my $count = 1;
    foreach my $result_entry (@result_entries) {
        my $search_results_title = $result_entry->{title}[0];
        my $search_results_content = $result_entry->{content}->{content};
        require MT::DateTime;
        my $search_results_published = _w3cdtf2ymdhms($result_entry->{published}[0]);
        my $search_results_updated = _w3cdtf2ymdhms($result_entry->{updated}[0]);
        my $search_results_author_name = $result_entry->{author}[0]->{name}[0];
        my $search_results_author_uri = $result_entry->{author}[0]->{uri}[0];

        my %row_data;

        $row_data{SEARCH_RESULTS_URL}
            =  _conv_url_to_search_redirector($result_entry->{link}[0]->{href}, $encode_keywords, $limit, $offset);
        $row_data{SEARCH_RESULTS_TITLE}
            = MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, $search_results_title);
        $row_data{SEARCH_RESULTS_CONTENT}
            = MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, $search_results_content);
        $row_data{SEARCH_RESULTS_PUBLISHED} = $search_results_published;
        $row_data{SEARCH_RESULTS_UPDATED} = $search_results_updated;
        $row_data{SEARCH_RESULTS_AUTHOR_NAME}
            = MT4i::Enc::encode_emoji_sjis($ejpemoji, $enc_emoji_sjis, $search_results_author_name);
        $row_data{SEARCH_RESULTS_AUTHOR_URI} = $search_results_author_uri;

        my @commons = _tmpl_loop_common($offset + $count, $count);
        $row_data{ROW_NO} = $commons[0];
        $row_data{ACCESS_KEY} = $commons[1];
        $row_data{ICON_CLOCK} = $commons[2];

        push(@search_results, \%row_data);

        $count++;
    }
    $template->param(search_results => \@search_results);
    $template->param(search_keywords => $str);

    my $href = &make_href("", 0, $page, 0, 0);

    # navigation link
    if ($offset + $limit < $total_results) {
        my $url = $href;
        $url .= $url =~ /\?/ ? '&' : '?';
        $url .= 'search_keyword='.$encode_keywords_shiftjis;
        $url .= '&mode=search';
        $url .= '&offset='.($offset + $limit);
        $url .= '&limit='.$limit if $limit;
        $template->param(NEXT_URL => $url);
    }
    if ($offset > 0) {
        my $url = $href;
        $url .= $url =~ /\?/ ? '&' : '?';
        $url .= 'search_keyword='.$encode_keywords_shiftjis;
        $url .= '&mode=search';
        my $prev_offset = $offset - $limit ? $offset - $limit : 0;
        $url .= '&offset='.$prev_offset;
        $url .= '&limit='.$limit if $limit;
        $template->param(PREV_URL => $url);
    }

    $template->param(BACK_URL => $href);

    # Common
    $template = _tmpl_common($template);

    # Output
    &_cacheout($template);
}

# _w3cdtf2ymdhms - Convert W3CDTF to "yyyy/mm/dd hh:mi:ss"
sub _w3cdtf2ymdhms {
    my $str = shift;

    $str =~ m{
        ^(\d{4})(?:
        -(\d\d)(?:
        -(\d\d)(?:
        T(\d\d)
        :(\d\d)(?:
        :(\d\d)(?:
        \.(\d+) )?)?
        ( Z|([+-])(\d\d):(\d\d) )?
        )?)?)?
    }x or return;

    return "$1/$2/$3 $4:$5:$6";
}

# _tmpl_loop_common - Common item for loop
sub _tmpl_loop_common {
    my ($rowid, $num) = @_;

    if ($cfg{AccessKey} eq "no"
        || ($cfg{AccessKey} eq "yes" && $ua ne "i-mode" && $ua ne "ezweb" && $ua ne "j-sky")) {
        return ("$rowid.", '', '');
    } else {
        return ($nostr[$num], $akstr[$num], "$clock_icon");
    }
}

# _conv_url_to_search_redirector - Convert URL to Search redirector
sub _conv_url_to_search_redirector {
    my ($url, $encode_keywords, $limit, $offset) = @_;

    my $tmpurl = &make_href("search_redirect", 0, 0, 0, 0);

    # URL encode
    $url = MT4i::Func::url_encode($url);

    $url = $tmpurl . '&amp;url=' . $url;
    $url .= '&id='.$blog_id if $blog_id;
    $url .= '&search_keyword='.$encode_keywords;
    $url .= '&offset='.$offset if $offset;
    $url .= '&limit='.$limit if $limit;

    return $url;
}

# search_redirector - redirector for search
sub search_redirector {
    my $keyword = $q->param("search_keyword");
    my $offset = $q->param("offset") || 0;
    my $limit = $q->param("limit") || 5;

    my $encode_keywords .= MT4i::Func::url_encode($keyword);
    my $url = MT4i::Func::get_mt4ilink($redirect_url);
    if ($url) {
        $url .= '&id='.$blog_id if $blog_id;
        $url .= '&search_keyword='.$encode_keywords;
        $url .= '&offset='.$offset if $offset;
        $url .= '&limit='.$limit if $limit;
        $url .= '&search=1';

        print "Location: $url\n\n";
    } else {
        print "Location: $redirect_url\n\n";
    }
}

# _get_cgipath - return Movable Type Config 'CGIPath'
sub _get_cgipath {
    my $url = $mt->config('CGIPath');
    if ($url =~ m!^/!) {
        # relative path, prepend blog domain
        my ($blog_domain) = $blog->archive_url =~ m|(.+://[^/]+)|;
        $url = $blog_domain . $url;
    }
    $url .= '/' unless $url =~ m/\/$/;
    return $url;
}

# _pre_post - prepare post entry or post comment
sub _pre_post {
    my @p_labels = @_;

    # Convert UTF-8
    foreach (@p_labels) {
        $p{$_} = encode($enc_e4u_utf8, decode($enc_e4u_sjis, $p{$_}));
    }

    # Convert emoticon binary to TC-tag
    unless ($ua eq 'other' || $ua eq 'smartphone') {
        eval { require $bin.'/lib/mt4i/Emoticon.pl'; 1 };
        if ($@) { errout($@); }
 
        my $range = MT4i::Emoticon::range($ua);

        foreach (@p_labels) {
            Encode::_utf8_on($p{$_});
            my @emoticons = $p{$_} =~ /[$range]/g;
            foreach my $emoticon (@emoticons) {
                my $name = MT4i::Emoticon::get_name($emoticon, $ua);
                $p{$_} =~ s/$emoticon/[E:$name]/ if $name;
            }
            Encode::_utf8_off($p{$_});
        }
    }
}

# _after_post - after post entry or post comment
sub _after_post {
    my @p_labels = @_;

    # The normal-width katakana of the posted character string
    # is converted into the em-size katakana.
    foreach (@p_labels) {
        $p{$_} = MT4i::Enc::han2zen(MT4i::Enc::decode_utf8($p{$_}));
    }

    # Convert emoticon img to tag
    if ($cfg{EmojiConvResult} eq 'image') {
        my $reg = q{(\[E:([^\]]*)\])};
        my $cgipath = _get_cgipath();
        Encode::_utf8_off($cgipath) if Encode::is_utf8($cgipath);
        foreach (@p_labels) {
            while ($p{$_} =~ $reg) {
                my $tag = '<img class="emoticon '.$2.'" src="'.$cgipath.'mt-static/plugins/EmoticonButton/images/emoticons/'.$2.'.gif" alt="'.$2.'" style="border: 0pt none ;" />';
                $p{$_} =~ s!$reg!$tag!;
            }
        }
    }

    # Convert to PublishCharset
    if ($conv_in ne 'utf8') {
        foreach (@p_labels) {
            $p{$_} = encode($conv_in, MT4i::Enc::decode_utf8($p{$_}));
        }
    }
}

# _conv_emoticon2tag - Convert emoticon img to tag
sub _conv_emoticon2tag {
    my $str = shift;
    unless ($ua eq 'other' || $ua eq 'smartphone') {
        my $reg =
            q{<img class="emoticon ([^"'>]*)" src="[^"'>]*" alt="[^"'>]*" style="[^"'>]*" />};
        while ($str =~ $reg) {
            $str =~ s/$reg/[E:$1]/;
        }
    }
    return $str;
}

# _conv_tag2binary - Convert emoticon tag to binary
sub _conv_tag2binary {
    my $str = shift;
    unless ($ua eq 'other' || $ua eq 'smartphone') {
        eval { require $bin.'/lib/mt4i/Emoticon.pl'; 1 };
        if ($@) { errout($@); }

        my $reg = q{\[E\:([^\]]*)]};
        while ($str =~ $reg) {
            my $code = MT4i::Emoticon::get_code($1, $ua, $enc_emoji_sjis, $enc_e4u_sjis, $ejpemoji);
            $str =~ s/$reg/$code/;
        }
    }
    return $str;
}

# _conv_emoticon2binary - Short Cut!
sub _conv_emoticon2binary {
    return _conv_tag2binary(MT4i::Enc::encode_emoji_sjis(
                $ejpemoji, $enc_emoji_sjis, _conv_utf8_z2h(_conv_emoticon2tag(shift))));
}

sub _conv_url2resizer {
    my $src = shift;
    my $href;

    if ($imk == 2) {
        $src =~ s!http://!!;
        $href = 'http://pic.to/'.$src;
    } else {
        $href = make_href("image", 0, 0, $eid, 0).'&amp;img='.MT4i::Func::url_encode($src);
    }

    return $href;
}

sub _check_is_number {
    my ($name, $value) = @_;
    if ($value && $value !~ /^[0-9]{1,}$/) {
        my $cgi = new CGI;
        $cgi->charset('utf-8');
        &errout($name.' "'.$cgi->escapeHTML($value).'" is wrong.');
        exit;
    }
}
