#!/bin/sh

exit 0

mkdir -p /usr/share/ulteo-kde-default-settings/kde-profile/default/share/config/
cat > /usr/share/ulteo-kde-default-settings/kde-profile/default/share/config/kwinrulesrc.ulteo << EOF
[1]
description=Unnamed entry
fullscreen=true
fullscreenrule=2
types=257
wmclass=
wmclasscomplete=true
wmclassmatch=0

[DesktopIcons]
Animated[\$d]
Size[\$d]

[Directories]
userProfileMapFile[\$d]

[Directories-default]
prefixes[\$d]

[General]
BrowserApplication[\$d]
XftHintStyle[\$d]
XftSubPixel[\$d]
alternateBackground[\$d]
background[\$d]
buttonBackground[\$d]
buttonForeground[\$d]
count=1
fixed[\$d]
font[\$d]
foreground[\$d]
linkColor[\$d]
menuFont[\$d]
selectBackground[\$d]
selectForeground[\$d]
shadeSortColumn[\$d]
taskbarFont[\$d]
toolBarFont[\$d]
visitedLinkColor[\$d]
widgetStyle[\$d]
windowBackground[\$d]
windowForeground[\$d]

[Global Shortcuts]
Popup Launch Menu[\$d]

[Icons]
Theme[\$d]

[KDE]
ChangeCursor[\$d]
EffectAnimateCombo[\$d]
EffectAnimateMenu[\$d]
EffectAnimateTooltip[\$d]
EffectNoTooltip[\$d]
EffectsEnabled[\$d]
InsertTearOffHandle[\$d]
OpaqueResize[\$d]
ShowIconsOnPushButtons[\$d]
SingleClick[\$d]
colorScheme[\$d]
contrast[\$d]

[KSpell]
KSpell_Client[\$d]
KSpell_Encoding[\$d]

[Paths]
Trash[\$d]

[PreviewSettings]
BoostSize[\$d]
MaximumSize[\$d]

[Toolbar style]
Highlighting[\$d]
IconText[\$d]
TransparentMoving[\$d]

[WM]
activeBackground[\$d]
activeBlend[\$d]
activeFont[\$d]
activeForeground[\$d]
activeTitleBtnBg[\$d]
frame[\$d]
handle[\$d]
inactiveBackground[\$d]
inactiveBlend[\$d]
inactiveForeground[\$d]
inactiveFrame[\$d]
inactiveHandle[\$d]
inactiveTitleBtnBg[\$d]

EOF

exit 0
