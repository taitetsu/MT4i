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
package MT4i::Enc;

##################################################
# Sub Decode_Utf8
#  Firt is_utf8, then use decode_utf8
##################################################
sub decode_utf8 {
    my $str = shift;
    my $rtn = Encode::is_utf8($str)
              ? $str
              : Encode::decode_utf8($str);
    return $rtn;
}

##################################################
# Sub Replace_Garbled_Characters
##################################################
sub replace_garbled_characters {
    my ($s, $ejpemoji) = @_;

    unless ($ejpemoji) {
        # Replace 'FULLWIDTH TILDE' to 'WAVE DASH'
        $s =~ s/\x{ff5e}/\x{301c}/g;
        # Replace 'FULLWIDTH HYPHEN-MINUS' to 'MINUS SIGN'
        $s =~ s/\x{ff0d}/\x{2212}/g;
    } else {
        # Replace 'FULLWIDTH TILDE' to 'WAVE DASH'
        $s =~ s/\xEF\xBD\x9E/\xE3\x80\x9C/go;
        # Replace 'FULLWIDTH HYPHEN-MINUS' to 'MINUS SIGN'
        $s =~ s/\xEF\xBC\x8D/\xE2\x88\x92/go;
    }

    return $s;
}

##################################################
# Preparation for character-string handling
##################################################
use charnames ':full';

my ($hankaku, $zenkaku, $hankana, $zenkana);

for my $o (0xFF61 .. 0xFF9D){
    $hankaku .= chr $o;
    $hankana .= chr $o if ($o < 0xFF9E);
    my $n = charnames::viacode($o);
    $n =~ s/HALFWIDTH\s+//;
    $zenkaku .= chr charnames::vianame($n);                                 
    $zenkana .= chr charnames::vianame($n) if ($o < 0xFF9E);
}

my $hankakukana = $hankaku;

# Alphabet and sign
$hankaku .= "\x{0021}-\x{007D}";
$zenkaku .= "\x{FF01}-\x{FF5D}";

my @zendaku = (
"\x{30AC}", "\x{30AE}", "\x{30B0}", "\x{30B2}",
"\x{30B4}", "\x{30B6}", "\x{30B8}", "\x{30BA}",
"\x{30BC}", "\x{30BE}", "\x{30C0}", "\x{30C2}",
"\x{30C5}", "\x{30C7}", "\x{30C9}", "\x{30D0}",
"\x{30D1}", "\x{30D3}", "\x{30D4}", "\x{30D6}",
"\x{30D7}", "\x{30D9}", "\x{30DA}", "\x{30DC}",
"\x{30DD}");

my @handaku = (
"\x{FF76}\x{FF9E}", "\x{FF77}\x{FF9E}",
"\x{FF78}\x{FF9E}", "\x{FF79}\x{FF9E}",
"\x{FF7A}\x{FF9E}", "\x{FF7B}\x{FF9E}",
"\x{FF7C}\x{FF9E}", "\x{FF7D}\x{FF9E}",
"\x{FF7E}\x{FF9E}", "\x{FF7F}\x{FF9E}",
"\x{FF80}\x{FF9E}", "\x{FF81}\x{FF9E}",
"\x{FF82}\x{FF9E}", "\x{FF83}\x{FF9E}",
"\x{FF84}\x{FF9E}", "\x{FF8A}\x{FF9E}",
"\x{FF8A}\x{FF9F}", "\x{FF8B}\x{FF9E}",
"\x{FF8B}\x{FF9F}", "\x{FF8C}\x{FF9E}",
"\x{FF8C}\x{FF9F}", "\x{FF8D}\x{FF9E}",
"\x{FF8D}\x{FF9F}", "\x{FF8E}\x{FF9E}",
"\x{FF8E}\x{FF9F}");

*tr_h2z = eval "sub { local \$_ = shift; tr/$hankana/$zenkana/; \$_ }";
*tr_z2h = eval "sub { local \$_ = shift; tr/$zenkaku/$hankaku/; \$_ }";

# Zen Han Convert
sub han2zen { my$s=shift; for(my$i=0;$i<25;$i++){$s=~s/$handaku[$i]/$zendaku[$i]/g} $s=tr_h2z($s); $s }
sub zen2han { my$s=shift; $s=tr_z2h($s); for(my$i=0;$i<25;$i++){$s=~s/$zendaku[$i]/$handaku[$i]/g} $s }

##################################################
# Sub Substrb_sjis
#  Length for utf-8 as shift_jis
##################################################
sub lenb_sjis {
    my $str = shift;
    my $lenb_utf8  = length(Encode::encode_utf8($str));
       $lenb_utf8 -= $str =~ s/([\x{0800}-\x{FFFF}])/$1/g;
       $lenb_utf8 -= $str =~ s/([$hankakukana])/$1/g;
    return $lenb_utf8;
}

##################################################
# Sub Substrb_sjis
#  Substr for utf-8 as shift_jis
##################################################
sub substrb_sjis {
    my ($str, $start, $length) = @_;

    $start = 0 if $start <= 0;
    if ($start) {
        my $tmp_start = $start;
        my $tmp_str = substr($str, 0, $tmp_start);
        my $tmp_len = lenb_sjis($tmp_str);
        while ($tmp_len > $start) {
            $tmp_start--;
            $tmp_str = substr($str, 0, $tmp_start);
            $tmp_len = lenb_sjis($tmp_str);
        }
        $start = length($tmp_str);
    }

    my $tmp_length = $length;
    my $tmp_str = substr($str, $start, $tmp_length);
    my $tmp_len = lenb_sjis($tmp_str);
    while ($tmp_len > $length) {
        $tmp_length--;
        $tmp_str = substr($str, $start, $tmp_length);
        $tmp_len = lenb_sjis($tmp_str);
    }

    return $tmp_str;
}

##################################################
# Sub Encode_Emoji_Sjis
##################################################
sub encode_emoji_sjis {
    my ($ejp, $enc, $str) = @_;

    if ($ejp) {
        # Convert MINUS SIGN to HYPHEN-MINUS
        $str =~ s/\x{2212}/\x{002d}/g;
        # Replace 'WAVE DASH' to 'FULLWIDTH TILDE'
        $str =~ s/\x{301c}/\x{ff5e}/g;
    }

    eval { require Encode::JP::Emoji;
           require Encode::JP::Emoji::FB_EMOJI_TEXT; };

    $str = $ejp ? Encode::encode($enc, $str, Encode::JP::Emoji::FB_EMOJI_TEXT->FB_EMOJI_TEXT())
                : Encode::encode($enc, $str);
    $str = Encode::encode($enc,
        $::cfg{Z2H} eq 'yes' ? zen2han(Encode::decode($enc, $str))
                             : Encode::decode($enc, $str)
    );
    return $str;
}

