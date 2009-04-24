#!/bin/sh

mkdir -p /etc/vim
cat > /etc/vim/vimrc.local <<EOF
set nobackup
set nowritebackup
set noswapfile   
EOF

exit 0
