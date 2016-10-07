package MT::Plugin::MT4iPurgeCache;
# mt4i-purge-cache.pl
# - When entry/comment is published or trackback is received, cache of MT4i is purged.
# Copyright (C) ÂÀÅ´ All rights reserved.
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
use strict;
use MT;
use MT::Plugin;
use MT::Blog;
use MT::TBPing;
use MT::Trackback;
our $VERSION = "0.3";

my $plugin = MT::Plugin->new({
    name => 'MT4i Purge Cache',
    version => $VERSION,
    description => "When publish/update entry/comment or received trackback, purge caches of MT4i.",
});

MT->add_plugin($plugin);
MT::Entry->add_callback('post_save', 10, $plugin, \&handler_entry_post_save);
MT::Entry->add_callback('pre_remove', 10, $plugin, \&handler_entry_pre_remove);
MT::Comment->add_callback('post_save', 10, $plugin, \&handler_comment_post_save);
MT::Comment->add_callback('pre_remove', 10, $plugin, \&handler_comment_pre_remove);
MT::TBPing->add_callback('post_save', 10, $plugin, \&handler_tbping_post_save);
MT::TBPing->add_callback('pre_remove', 10, $plugin, \&handler_tbping_pre_remove);

MT->add_callback('CMSPostSave.entry', 10, $plugin, \&handler_cms_post_save_entry);
MT->add_callback('CMSPostDelete.entry', 10, $plugin, \&handler_cms_post_delete_entry);

# ----- Entry ----- #
sub handler_entry_post_save {
    my ($eh, $entry, $org_entry) = @_;
    if ($entry->status == MT::Entry::RELEASE() && $entry->{column_values}{atom_id}) {
        writelog('['.getlocaltime().']entry_post_save:entry_id='.$entry->id);
        &_purge_cache_entry($entry);
    }
    1;
}

sub handler_entry_pre_remove {
    my ($eh, $entry) = @_;
    if ($entry->status == MT::Entry::RELEASE()) {
        writelog('['.getlocaltime().']entry_pre_remove:entry_id='.$entry->id);
        &_purge_cache_entry($entry);
    }
    1;
}

sub handler_cms_post_save_entry {
    my ($eh, $app, $entry, $org_entry) = @_;
    if ($entry->status == MT::Entry::HOLD() && $org_entry->status == MT::Entry::RELEASE()) {
        writelog('['.getlocaltime().']cms_post_save_entry:entry_id='.$entry->id);
        &_purge_cache_entry($entry);
    }
    1;
}

sub handler_cms_post_delete_entry {
    my ($eh, $app, $entry) = @_;
    if ($entry->status == MT::Entry::RELEASE()) {
        writelog('['.getlocaltime().']cms_post_delete_entry:entry_id='.$entry->id);
        &_purge_cache_entry($entry);
    }
    1;
}

sub _purge_cache_entry {
    my $entry = shift;

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
            my $key = 'b'.$entry->blog_id.'/e'.$next->id.'/c*/*';
            purgecache($key);
        }
        my $prev = _neighbor_entry($entry, $cid, 'next');
        if ($prev) {
            my $key = 'b'.$entry->blog_id.'/e'.$prev->id.'/c*/*';
            purgecache($key);
        }
    }
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
    $args{'sort'} = MT->version_number() >= 4.0 ? 'authored_on' : 'created_on';
    $args{'start_val'} = MT->version_number() >= 4.0 ? $entry->authored_on : $entry->created_on;

    return MT::Entry->load( \%terms, \%args );
}

# ----- Comment ----- #
sub handler_comment_post_save {
    my ($eh, $comment) = @_;
    if ($comment->visible) {
        writelog('['.getlocaltime().']comment_post_save:comment_id='.$comment->id);
        purgecache('b'.$comment->blog_id.'/idxc*/*');
        purgecache('b'.$comment->blog_id.'/e'.$comment->entry_id.'/c*/*');
        purgecache('b'.$comment->blog_id.'/e'.$comment->entry_id.'/ccp*');
        purgecache('b'.$comment->blog_id.'/rc_*');
    }
    1;
}

sub handler_comment_pre_remove {
    my ($eh, $comment) = @_;
    if ($comment->visible) {
        writelog('['.getlocaltime().']comment_pre_remove:comment_id='.$comment->id);
        purgecache('b'.$comment->blog_id.'/idxc*/*');
        purgecache('b'.$comment->blog_id.'/e'.$comment->entry_id.'/c*/*');
        purgecache('b'.$comment->blog_id.'/e'.$comment->entry_id.'/ccp*');
        purgecache('b'.$comment->blog_id.'/rc_*');
    }
    1;
}

# ----- TBPing ----- #
sub handler_tbping_post_save {
    my ($eh, $ping) = @_;
    if ($ping->visible) {
        my $tb = MT::Trackback->load({ id => $ping->tb_id });
        writelog('['.getlocaltime().']tbping_post_save:ping_id='.$ping->id);
        purgecache('b'.$ping->blog_id.'/idxc*/*');
        purgecache('b'.$ping->blog_id.'/e'.$tb->entry_id.'/c*/*');
        purgecache('b'.$ping->blog_id.'/e'.$tb->entry_id.'/tb*');
    }
    1;
}

sub handler_tbping_pre_remove {
    my ($eh, $ping) = @_;
    if ($ping->visible) {
        my $tb = MT::Trackback->load({ id => $ping->tb_id });
        writelog('['.getlocaltime().']tbping_pre_remove:ping_id='.$ping->id);
        purgecache('b'.$ping->blog_id.'/idxc*/*');
        purgecache('b'.$ping->blog_id.'/e'.$tb->entry_id.'/c*/*');
        purgecache('b'.$ping->blog_id.'/e'.$tb->entry_id.'/tb*');
    }
    1;
}

##################################################
# Sub PurgeCache
##################################################
sub purgecache {
    my ($key) = @_;
    my $cache_file = $ENV{MT_HOME}.'/mt4i/cache/page/'.$key;
    my @fnames = glob($cache_file);
    eval {
        for my $fname (@fnames) {
            next if (!-e $fname || -z $fname );

            open(OUT,">> $fname") or die "Can't open $fname : $!";
            flock(OUT, 2) or die "Can't flock  : $!";
            truncate(OUT,0) or die "Can't truncate  : $!";
            close(OUT);

            writelog('truncate cache file: '.$fname);
        }
    };
    if ($@) {
        writelog("Error: $@");

        my $log = MT::Log->new;
        $log->message("Error: $@");
        $log->save or die $log->errstr;

        die;
    }
}

##################################################
# Sub WriteLog
##################################################
sub writelog {
    my ($logstr) = @_;

    my $log_file = $ENV{MT_HOME}.'/mt4i/cache/purge.log';

    # open file
    if (!-e $log_file) {
        open(OUT,"> $log_file") or die "Can't open ".$log_file." : $!";
    } else {
        open(OUT,"+< $log_file") or die "Can't open ".$log_file." : $!";
    }
    # lock
    flock(OUT, 2) or die "Can't flock  : $!";

    # read
    my @temp;
    while (<OUT>) {
        push @temp, $_;
    }
    # push new string
    push @temp, $logstr."\n";

    # get row count
    my $cnt = $#temp;
    # get start row
    $cnt = ($cnt - 999 >= 0) ? $cnt - 999 : 0 ;
    # over write
    truncate(OUT, 0);
    seek(OUT, 0, 0) or die "Can't seek  : $!";
    for (my $i = $cnt; $i <= $#temp; $i++) {
        print OUT $temp[$i] or die "Can't print : $!";
    }

    # close file
    close(OUT);
}

##################################################
# Sub GetLocalTime
##################################################
sub getlocaltime {
    $ENV{'TZ'} = "JST-9";
    my ($sec, $min, $hour, $mday, $mon, $year) = localtime(time);
    $mon = ('01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12')[$mon];
    $year += 1900;
    if ($sec < 10) {$sec = "0$sec";}
    if ($min < 10) {$min = "0$min";}
    if ($hour < 10) {$hour = "0$hour";}
    if ($mday < 10) {$mday = "0$mday";}
    my $date = "$year/$mon/$mday $hour:$min:$sec";
    return $date;
}

1;
