#!/bin/sh -e

# This will force the download of the file, avoiding too permissive acces to
# system apps by firefox
cat >> /etc/firefox/pref/firefox.js <<EOF
lockPref("helpers.global_mailcap_file", '');
lockPref("helpers.private_mailcap_file", '');
lockPref("general.smoothScroll", false);
pref("browser.cache.disk.enable", false);
EOF

exit 0
