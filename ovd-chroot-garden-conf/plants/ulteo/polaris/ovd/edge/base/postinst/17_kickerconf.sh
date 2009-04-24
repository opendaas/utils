#!/bin/sh

exit 0

cat > /usr/share/ulteo-kde-default-settings/kde-profile/default/share/config/kickerrc << EOF
[Applet_2]
ConfigFile=taskbar_panelapplet_kwfyddh6a3jocxzwpdum_rc
DesktopFile=taskbarapplet.desktop
FreeSpace2=0.039823
WidthForHeightHint=10

[General]
UntrustedApplets=
UntrustedExtensions=
ShowLeftHideButton=false
ShowRightHideButton=false
Alignment=0
Applets2=ServiceButton_2,ServiceButton_1,Applet_2
AutoHideDelay=3
AutoHidePanel=false
AutoHideSwitch=false
BackgroundHide=false
BackgroundTheme=/usr/share/apps/kicker/wallpapers/default.png
CustomSize=56
ExpandSize=true
HideAnimation=true
HideAnimationSpeed=40
IExist=true
Position=3
Size=1
SizePercentage=100
TintColor=198,198,195
UnhideLocation=0
XineramaScreen=0
HideAppletHandles=true
UseBackgroundTheme=false

[ServiceButton_1]
DesktopFile=/usr/share/applications/ooo-writer.desktop
FreeSpace2=0
StorageId=ooo-writer.desktop

[ServiceButton_2]
DesktopFile=/usr/share/applications/firefox.desktop
FreeSpace2=0
StorageId=firefox.desktop

[menus]
Extensions=
MenuEntryFormat=NameAndDescription
MenuEntryHeight=22
NumVisibleEntries=3
RecentAppsStat=
UseBookmarks=false
UseBrowser=false

[button_tiles]
EnableBrowserTiles=false
EnableDesktopButtonTiles=false
EnableKMenuTiles=false
EnableURLTiles=false
EnableWindowListTiles=false

[buttons][\$i]
EnableTileBackground=false

[KMenu][\$i]
UseSidePixmap=false
EOF

exit 0
