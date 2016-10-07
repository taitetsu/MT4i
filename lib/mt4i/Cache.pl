# Copyright (C) ﾂﾀﾅｴ All rights reserved.
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
package MT4i::Cache;

##################################################
# Sub ReadCacheOut
##################################################
sub readcacheout {
    my ($key) = @_;

    return 0 if ($::cfg{CacheTime} < 1 || $::admin_mode eq 'yes');

    my $cache_file = $::cfg{MT_DIR}.'mt4i/cache/'.$key;

    # Returns, if the cache file exists or it is size 0.
    return 0 if (!-e $cache_file || -z $cache_file);

    my $mtime = (stat($cache_file))[9];
    my $ntime = time();

    return 0 if ($ntime - $mtime >= $::cfg{CacheTime}*60);

    my $cdata;
    eval { $cdata = lock_retrieve($cache_file); };
    &errout('retrieve cache failed: '.$@) if($@);

    print "Content-Type: text/html\n\n", $$cdata;

    exit;
}

##################################################
# Sub WriteCache
##################################################
sub writecache {
    my ($key, $cdata) = @_;

die "?";
    return 0 if ($::cfg{CacheTime} < 1 || $::admin_mode eq 'yes');

    # make directory
    my @directories = split('/', $key);
    my $dirstr = $::cfg{MT_DIR}.'mt4i/cache/';
    for (my $i = 0; $i < $#directories; $i++) {
        if (!(-d $dirstr.$directories[$i])) {
            mkdir($dirstr.$directories[$i]);
        }
        $dirstr .= $directories[$i].'/';
    }

    # write cache
    my $cache_file = $::cfg{MT_DIR}.'mt4i/cache/'.$key;

    eval { lock_store(\$cdata, $cache_file); };
    &errout('store cache failed: '.$@) if($@);
}

##################################################
# Sub PurgeCache
##################################################
sub purgecache {
    my ($key) = @_;
    my $cache_file = $::cfg{MT_DIR}.'mt4i/cache/'.$key;
    my @fnames = glob($cache_file);
    for my $fname (@fnames) {
        open(OUT,">> $fname") or die "Can't open $fname : $!";
        flock(OUT, 2) or die "Can't flock  : $!";
        truncate(OUT,0) or die "Can't truncate  : $!";
        close(OUT);

        my $log_pl = $Bin.'/lib/mt4i/Log.pl';
        eval {require $log_pl; 1} or &errout('File not found: '.$log_pl);
        MT4i::Log::writelog('truncate cache file: '.$fname);
    }
}

1;
