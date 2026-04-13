#!/system/bin/sh
# Inject 1500 call records via content insert
LOG=/data/local/tmp/inject_calls.log
echo "Starting call log injection at $(date)" > $LOG
COUNT=0
content insert --uri content://call_log/calls --bind number:s:+17755004237 --bind date:l:1766419781158 --bind duration:i:14 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18545902102 --bind date:l:1761385010767 --bind duration:i:73 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16174382028 --bind date:l:1760472419693 --bind duration:i:454 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15772632290 --bind date:l:1766138032942 --bind duration:i:1872 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18096706382 --bind date:l:1772238389480 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12119828059 --bind date:l:1745252465260 --bind duration:i:79 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16004085750 --bind date:l:1761010643265 --bind duration:i:313 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13249535716 --bind date:l:1754597988446 --bind duration:i:34 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13568963583 --bind date:l:1746370182558 --bind duration:i:68 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16907273364 --bind date:l:1764269194942 --bind duration:i:76 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19362382990 --bind date:l:1768521029220 --bind duration:i:37 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14675289028 --bind date:l:1754801976158 --bind duration:i:13 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13463409573 --bind date:l:1756189336470 --bind duration:i:2938 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14093003468 --bind date:l:1762588795262 --bind duration:i:441 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12259262762 --bind date:l:1762819441939 --bind duration:i:88 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19252159124 --bind date:l:1756511340486 --bind duration:i:406 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17002777027 --bind date:l:1751251393690 --bind duration:i:2751 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17155815546 --bind date:l:1756880356070 --bind duration:i:579 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17057283489 --bind date:l:1772120975297 --bind duration:i:2582 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17348186341 --bind date:l:1754583405642 --bind duration:i:353 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16835371111 --bind date:l:1758182680954 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19165604260 --bind date:l:1761842810527 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16419782407 --bind date:l:1756499087139 --bind duration:i:42 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15654748652 --bind date:l:1760704693927 --bind duration:i:47 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19782581231 --bind date:l:1756668582591 --bind duration:i:74 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15754687102 --bind date:l:1768410849658 --bind duration:i:2393 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16753519202 --bind date:l:1765160611283 --bind duration:i:828 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13276169370 --bind date:l:1763106271039 --bind duration:i:49 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17955108125 --bind date:l:1751443645599 --bind duration:i:570 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19779148747 --bind date:l:1756110934030 --bind duration:i:119 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15637045968 --bind date:l:1751603870634 --bind duration:i:316 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19195991647 --bind date:l:1773136433460 --bind duration:i:543 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16897407316 --bind date:l:1749459299203 --bind duration:i:89 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18655254700 --bind date:l:1765855794033 --bind duration:i:76 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19542047917 --bind date:l:1746239778025 --bind duration:i:858 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17033791889 --bind date:l:1772026632340 --bind duration:i:9 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14189684539 --bind date:l:1764463969195 --bind duration:i:394 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17486862774 --bind date:l:1774178922815 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13975551760 --bind date:l:1767352304452 --bind duration:i:72 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14436569334 --bind date:l:1755395496545 --bind duration:i:59 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15455316903 --bind date:l:1765323437943 --bind duration:i:10 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13363403449 --bind date:l:1753669733980 --bind duration:i:56 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15615211267 --bind date:l:1752202439178 --bind duration:i:13 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19958302328 --bind date:l:1774744321372 --bind duration:i:7 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17559288584 --bind date:l:1761526914274 --bind duration:i:78 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15663265258 --bind date:l:1765141443794 --bind duration:i:91 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13778101419 --bind date:l:1753712569587 --bind duration:i:95 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16967713387 --bind date:l:1769102632330 --bind duration:i:48 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19288693071 --bind date:l:1746356808247 --bind duration:i:231 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19147908512 --bind date:l:1766840956289 --bind duration:i:1001 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17323568120 --bind date:l:1774134551086 --bind duration:i:43 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17543247048 --bind date:l:1751607876979 --bind duration:i:249 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18423366497 --bind date:l:1770760309500 --bind duration:i:1687 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16088846420 --bind date:l:1747031608254 --bind duration:i:36 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14417593238 --bind date:l:1774252953726 --bind duration:i:18 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18339764179 --bind date:l:1748016957682 --bind duration:i:832 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16845021191 --bind date:l:1770498927196 --bind duration:i:91 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12092374037 --bind date:l:1763456579074 --bind duration:i:87 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19607399773 --bind date:l:1749752107172 --bind duration:i:398 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15148109259 --bind date:l:1771125846561 --bind duration:i:58 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15619833371 --bind date:l:1753877171971 --bind duration:i:396 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15033034958 --bind date:l:1772749360098 --bind duration:i:35 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12635595555 --bind date:l:1773823139393 --bind duration:i:663 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15736051055 --bind date:l:1761312671123 --bind duration:i:11 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16809191490 --bind date:l:1748194950661 --bind duration:i:100 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16133571408 --bind date:l:1754697774590 --bind duration:i:46 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15348013002 --bind date:l:1746541201990 --bind duration:i:109 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18445097493 --bind date:l:1772379008013 --bind duration:i:91 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17239409308 --bind date:l:1766730918660 --bind duration:i:33 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13685574239 --bind date:l:1765249840677 --bind duration:i:117 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17274256524 --bind date:l:1744914527257 --bind duration:i:94 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19368223556 --bind date:l:1770444603773 --bind duration:i:187 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18588877908 --bind date:l:1745706294279 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18386122436 --bind date:l:1749084348622 --bind duration:i:385 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13673844195 --bind date:l:1774619263669 --bind duration:i:284 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19988457821 --bind date:l:1765830552628 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16193606330 --bind date:l:1762938455083 --bind duration:i:819 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15818752470 --bind date:l:1766440299100 --bind duration:i:259 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14596795769 --bind date:l:1751043630436 --bind duration:i:83 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19612422443 --bind date:l:1745639340867 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15754626499 --bind date:l:1755839798304 --bind duration:i:28 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12448626827 --bind date:l:1769302450248 --bind duration:i:2816 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19487306661 --bind date:l:1768521241029 --bind duration:i:102 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17176766725 --bind date:l:1750261049043 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12848541977 --bind date:l:1745237309172 --bind duration:i:15 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15476902109 --bind date:l:1765647857994 --bind duration:i:60 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13034173013 --bind date:l:1746063914836 --bind duration:i:309 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16839985012 --bind date:l:1771414032201 --bind duration:i:88 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17524699136 --bind date:l:1766359260696 --bind duration:i:860 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17376038077 --bind date:l:1764711286016 --bind duration:i:120 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18488265177 --bind date:l:1747003947885 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18588945373 --bind date:l:1769949165173 --bind duration:i:28 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15022407764 --bind date:l:1774296025398 --bind duration:i:692 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17389124129 --bind date:l:1757997196800 --bind duration:i:67 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15634209534 --bind date:l:1747197222741 --bind duration:i:90 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14895299133 --bind date:l:1744944805718 --bind duration:i:170 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17154349779 --bind date:l:1752648681666 --bind duration:i:80 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12856374436 --bind date:l:1748547139612 --bind duration:i:61 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16685482029 --bind date:l:1774480974356 --bind duration:i:43 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17676852282 --bind date:l:1773837851107 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14177586167 --bind date:l:1769371022570 --bind duration:i:786 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12256097092 --bind date:l:1767506815996 --bind duration:i:42 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15282306818 --bind date:l:1746993399035 --bind duration:i:59 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18104986482 --bind date:l:1761847616023 --bind duration:i:18 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17944665182 --bind date:l:1773692175645 --bind duration:i:41 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18412322775 --bind date:l:1758523639348 --bind duration:i:2873 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16635392651 --bind date:l:1754033094757 --bind duration:i:626 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17937536179 --bind date:l:1751973327154 --bind duration:i:108 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18543917987 --bind date:l:1762096965821 --bind duration:i:635 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14154157058 --bind date:l:1747382748746 --bind duration:i:99 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16933999504 --bind date:l:1759968651512 --bind duration:i:170 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14047098764 --bind date:l:1747267394747 --bind duration:i:107 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14397627999 --bind date:l:1761350862697 --bind duration:i:45 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15058601286 --bind date:l:1759423475108 --bind duration:i:43 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17113943088 --bind date:l:1760561680409 --bind duration:i:56 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13197554346 --bind date:l:1753174828109 --bind duration:i:761 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19836654191 --bind date:l:1763273283022 --bind duration:i:19 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17785433395 --bind date:l:1765649868841 --bind duration:i:119 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12525579748 --bind date:l:1754192877254 --bind duration:i:120 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13735724209 --bind date:l:1768555037403 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17309794576 --bind date:l:1765449453524 --bind duration:i:46 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18397876285 --bind date:l:1751812033381 --bind duration:i:313 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17075409256 --bind date:l:1747232492351 --bind duration:i:33 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14267035390 --bind date:l:1751738396038 --bind duration:i:48 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15197894804 --bind date:l:1751715121076 --bind duration:i:19 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19852063983 --bind date:l:1772177928926 --bind duration:i:286 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15174751773 --bind date:l:1770506854013 --bind duration:i:19 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18907381489 --bind date:l:1747220147063 --bind duration:i:882 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13443254571 --bind date:l:1774197855351 --bind duration:i:65 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14224285266 --bind date:l:1768057303186 --bind duration:i:90 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18775974083 --bind date:l:1752977504397 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17269806679 --bind date:l:1746152846174 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16344039944 --bind date:l:1770701858743 --bind duration:i:2063 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13288626394 --bind date:l:1768203899357 --bind duration:i:211 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14694896540 --bind date:l:1752357768771 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16839185706 --bind date:l:1744935836512 --bind duration:i:872 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16476721414 --bind date:l:1749796823233 --bind duration:i:2723 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16345798444 --bind date:l:1763495432412 --bind duration:i:41 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12536662435 --bind date:l:1768526211954 --bind duration:i:3126 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19654644190 --bind date:l:1756289762241 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18654641202 --bind date:l:1772539761225 --bind duration:i:387 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17078334046 --bind date:l:1750098092837 --bind duration:i:865 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18844732078 --bind date:l:1757376926622 --bind duration:i:85 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15229454667 --bind date:l:1758427453682 --bind duration:i:1667 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17386112721 --bind date:l:1761873260236 --bind duration:i:79 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13215356713 --bind date:l:1758792442151 --bind duration:i:885 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18694962962 --bind date:l:1750635925031 --bind duration:i:170 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19084669028 --bind date:l:1771865074697 --bind duration:i:703 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13367091685 --bind date:l:1760725679151 --bind duration:i:65 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18074114950 --bind date:l:1773404318518 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16047291970 --bind date:l:1748123291824 --bind duration:i:546 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17513976537 --bind date:l:1749742746398 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15284189140 --bind date:l:1752284927780 --bind duration:i:114 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15818668697 --bind date:l:1752485364974 --bind duration:i:37 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15154068621 --bind date:l:1763262937818 --bind duration:i:106 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12922953902 --bind date:l:1761065641636 --bind duration:i:43 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17956813016 --bind date:l:1773761785847 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15454615642 --bind date:l:1773878858977 --bind duration:i:3487 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16317646432 --bind date:l:1754711275641 --bind duration:i:35 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18073435319 --bind date:l:1766805444733 --bind duration:i:68 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13367032259 --bind date:l:1744319983788 --bind duration:i:154 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18788429827 --bind date:l:1744960622539 --bind duration:i:106 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15268537948 --bind date:l:1769731068048 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13942842698 --bind date:l:1750708689463 --bind duration:i:45 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19218063770 --bind date:l:1757837051253 --bind duration:i:26 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16519703247 --bind date:l:1768372429451 --bind duration:i:382 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17847243960 --bind date:l:1756439884327 --bind duration:i:118 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14753671565 --bind date:l:1756289042947 --bind duration:i:90 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14879291864 --bind date:l:1748669599836 --bind duration:i:167 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16988024907 --bind date:l:1759441517204 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12964362509 --bind date:l:1771104325736 --bind duration:i:857 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18217218122 --bind date:l:1745305258875 --bind duration:i:14 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15564844516 --bind date:l:1760354846905 --bind duration:i:190 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19358608925 --bind date:l:1746233919693 --bind duration:i:12 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18852742090 --bind date:l:1764526964396 --bind duration:i:100 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16864131408 --bind date:l:1766699099939 --bind duration:i:116 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13858184630 --bind date:l:1767967393947 --bind duration:i:1204 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17713496800 --bind date:l:1772654879280 --bind duration:i:27 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15087383124 --bind date:l:1766544241877 --bind duration:i:45 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17684064448 --bind date:l:1768060214274 --bind duration:i:86 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19253721132 --bind date:l:1772657788653 --bind duration:i:37 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18434447111 --bind date:l:1770685057462 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19093269290 --bind date:l:1759373318833 --bind duration:i:2467 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13417956956 --bind date:l:1772770261027 --bind duration:i:118 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14489684406 --bind date:l:1755642102619 --bind duration:i:2380 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18609506453 --bind date:l:1744074810453 --bind duration:i:86 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16618559017 --bind date:l:1748286772946 --bind duration:i:632 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15356306255 --bind date:l:1765111951556 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17873708123 --bind date:l:1758446830668 --bind duration:i:69 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15037292254 --bind date:l:1750404763764 --bind duration:i:489 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15876662231 --bind date:l:1772293699502 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13677271434 --bind date:l:1767427661291 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19258529740 --bind date:l:1759359028307 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14748082568 --bind date:l:1766966641095 --bind duration:i:75 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13706557267 --bind date:l:1759336489263 --bind duration:i:120 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15906893620 --bind date:l:1768409863025 --bind duration:i:51 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19858245733 --bind date:l:1750315317561 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14278214656 --bind date:l:1745755525214 --bind duration:i:78 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15465751257 --bind date:l:1758902836263 --bind duration:i:87 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19049848871 --bind date:l:1753559484734 --bind duration:i:71 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18957592655 --bind date:l:1771368169519 --bind duration:i:42 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12848255515 --bind date:l:1768391241381 --bind duration:i:102 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15892699543 --bind date:l:1770592884221 --bind duration:i:53 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19635973198 --bind date:l:1748656647497 --bind duration:i:81 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15746998359 --bind date:l:1756664188674 --bind duration:i:117 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13783132661 --bind date:l:1756882881721 --bind duration:i:60 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14398818677 --bind date:l:1745296398841 --bind duration:i:37 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18637082688 --bind date:l:1764066727599 --bind duration:i:1102 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13166661086 --bind date:l:1759953870306 --bind duration:i:102 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17172023764 --bind date:l:1746920085996 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17159093160 --bind date:l:1745621996200 --bind duration:i:85 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14713508379 --bind date:l:1749459209730 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15376556334 --bind date:l:1755423628161 --bind duration:i:85 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18538134452 --bind date:l:1753883255222 --bind duration:i:96 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17995495911 --bind date:l:1745463918393 --bind duration:i:24 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17679549568 --bind date:l:1763559292664 --bind duration:i:817 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14618306699 --bind date:l:1747238897430 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16624784565 --bind date:l:1767349805012 --bind duration:i:110 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16805341800 --bind date:l:1769484992743 --bind duration:i:68 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17569717901 --bind date:l:1745240563238 --bind duration:i:79 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18724959811 --bind date:l:1769577231034 --bind duration:i:181 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18525301824 --bind date:l:1766537889727 --bind duration:i:2467 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15622983593 --bind date:l:1746163530862 --bind duration:i:134 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16858263805 --bind date:l:1747334360241 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15476821272 --bind date:l:1751091717247 --bind duration:i:35 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18263602949 --bind date:l:1747210941426 --bind duration:i:3469 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12347534302 --bind date:l:1747381166806 --bind duration:i:263 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12013862029 --bind date:l:1760310156988 --bind duration:i:1057 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16829546916 --bind date:l:1771981434642 --bind duration:i:432 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17989332737 --bind date:l:1768545962931 --bind duration:i:661 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15056476687 --bind date:l:1760147796189 --bind duration:i:3143 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16695227228 --bind date:l:1748077720010 --bind duration:i:102 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18967744028 --bind date:l:1744510260574 --bind duration:i:596 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14845349571 --bind date:l:1761631841488 --bind duration:i:55 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12293389147 --bind date:l:1758015596018 --bind duration:i:117 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16314722987 --bind date:l:1756284913485 --bind duration:i:67 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17785007965 --bind date:l:1769123412602 --bind duration:i:10 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18895144803 --bind date:l:1747153861918 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19426108432 --bind date:l:1751173234172 --bind duration:i:69 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17359462439 --bind date:l:1767371130575 --bind duration:i:118 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19849346490 --bind date:l:1768179155432 --bind duration:i:533 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15902441331 --bind date:l:1754601802487 --bind duration:i:102 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17457951702 --bind date:l:1772324569004 --bind duration:i:456 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12689619478 --bind date:l:1762831026266 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15249365620 --bind date:l:1770540382684 --bind duration:i:97 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18634281885 --bind date:l:1757085799315 --bind duration:i:266 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14485949074 --bind date:l:1770742063554 --bind duration:i:2179 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12269008223 --bind date:l:1767806981933 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12882528918 --bind date:l:1753729843471 --bind duration:i:16 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14355686105 --bind date:l:1762110440950 --bind duration:i:770 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18156117556 --bind date:l:1758119878614 --bind duration:i:100 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14809896525 --bind date:l:1756138425608 --bind duration:i:104 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14338842153 --bind date:l:1760728554611 --bind duration:i:328 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14645936590 --bind date:l:1752665957957 --bind duration:i:108 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15405031780 --bind date:l:1759224342435 --bind duration:i:82 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19283537601 --bind date:l:1763117561204 --bind duration:i:82 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17132271139 --bind date:l:1752117456910 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19122201459 --bind date:l:1758514444021 --bind duration:i:399 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19703144876 --bind date:l:1766276470268 --bind duration:i:62 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16099169462 --bind date:l:1750564148772 --bind duration:i:2691 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16737805221 --bind date:l:1770988534069 --bind duration:i:44 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14665492059 --bind date:l:1748519579129 --bind duration:i:9 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19435123019 --bind date:l:1749239812273 --bind duration:i:472 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14725878279 --bind date:l:1753229844373 --bind duration:i:79 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18284878854 --bind date:l:1764220167224 --bind duration:i:9 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18049715782 --bind date:l:1745211868604 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14997406348 --bind date:l:1757589217220 --bind duration:i:96 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18927699630 --bind date:l:1770603431050 --bind duration:i:260 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19554843805 --bind date:l:1774747004682 --bind duration:i:71 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17934205837 --bind date:l:1757267272426 --bind duration:i:815 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16735829122 --bind date:l:1773042730534 --bind duration:i:2212 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18979255506 --bind date:l:1759063144046 --bind duration:i:24 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18366655729 --bind date:l:1762680299456 --bind duration:i:13 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14202961981 --bind date:l:1755646830586 --bind duration:i:1269 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17649041596 --bind date:l:1769387676878 --bind duration:i:17 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15634666970 --bind date:l:1752520728114 --bind duration:i:363 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12057343067 --bind date:l:1746314184890 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12397663486 --bind date:l:1765589543222 --bind duration:i:195 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14459007098 --bind date:l:1759364366476 --bind duration:i:290 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18889107359 --bind date:l:1760268793765 --bind duration:i:54 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14365733708 --bind date:l:1766591418715 --bind duration:i:39 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19553264905 --bind date:l:1769176851356 --bind duration:i:103 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15483843319 --bind date:l:1760504081880 --bind duration:i:20 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13073652897 --bind date:l:1767746811099 --bind duration:i:30 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18142508186 --bind date:l:1770753828987 --bind duration:i:37 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14156986309 --bind date:l:1774479762138 --bind duration:i:64 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12058119052 --bind date:l:1755300207969 --bind duration:i:45 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19123463969 --bind date:l:1767020869402 --bind duration:i:21 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18269304599 --bind date:l:1759512419460 --bind duration:i:355 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19595152757 --bind date:l:1764807041896 --bind duration:i:784 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14369763028 --bind date:l:1756776244471 --bind duration:i:24 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18327672222 --bind date:l:1758749990077 --bind duration:i:522 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12396718089 --bind date:l:1750394250175 --bind duration:i:61 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16616815705 --bind date:l:1774033474783 --bind duration:i:212 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14902521924 --bind date:l:1770942622386 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18429517939 --bind date:l:1762866820619 --bind duration:i:27 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14886902815 --bind date:l:1757480681395 --bind duration:i:2525 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19804035971 --bind date:l:1761359272164 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16084897830 --bind date:l:1760912037945 --bind duration:i:95 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16454023601 --bind date:l:1765109531350 --bind duration:i:53 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18452127431 --bind date:l:1756728024621 --bind duration:i:6 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16977594236 --bind date:l:1760740870827 --bind duration:i:40 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14084315660 --bind date:l:1760070185760 --bind duration:i:67 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16636772638 --bind date:l:1763813806381 --bind duration:i:342 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13148157918 --bind date:l:1758615421003 --bind duration:i:408 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14856718139 --bind date:l:1764386289432 --bind duration:i:37 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17674193659 --bind date:l:1759862047220 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15067329369 --bind date:l:1749099510047 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13976121451 --bind date:l:1764806811469 --bind duration:i:97 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19015766051 --bind date:l:1751595080538 --bind duration:i:2413 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17855744362 --bind date:l:1764797690139 --bind duration:i:794 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17177289176 --bind date:l:1766710224812 --bind duration:i:708 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19874508413 --bind date:l:1752798611885 --bind duration:i:73 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16017888135 --bind date:l:1751573973233 --bind duration:i:72 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14524302616 --bind date:l:1756501522927 --bind duration:i:51 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16134322858 --bind date:l:1749449406921 --bind duration:i:526 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14577086649 --bind date:l:1749682354674 --bind duration:i:58 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12119971596 --bind date:l:1746724745536 --bind duration:i:23 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13282619110 --bind date:l:1754533749942 --bind duration:i:2004 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14795405843 --bind date:l:1753891196310 --bind duration:i:114 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15595497115 --bind date:l:1744194430046 --bind duration:i:1062 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16196605998 --bind date:l:1759827917925 --bind duration:i:9 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14834133325 --bind date:l:1755386623948 --bind duration:i:105 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14537043495 --bind date:l:1745551878483 --bind duration:i:581 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14608401771 --bind date:l:1752441395260 --bind duration:i:37 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17333983184 --bind date:l:1770287763172 --bind duration:i:95 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12562144254 --bind date:l:1755877281243 --bind duration:i:9 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13354566868 --bind date:l:1763789456795 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14675924133 --bind date:l:1756615986942 --bind duration:i:8 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12626044400 --bind date:l:1758294556992 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12968005808 --bind date:l:1766394783243 --bind duration:i:81 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17452017774 --bind date:l:1750177587599 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19068018077 --bind date:l:1749094052941 --bind duration:i:3414 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12388272163 --bind date:l:1756568628771 --bind duration:i:87 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17232757528 --bind date:l:1752572011048 --bind duration:i:87 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16745297006 --bind date:l:1751490558711 --bind duration:i:241 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19415065728 --bind date:l:1773509656160 --bind duration:i:5 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13898147783 --bind date:l:1762333269801 --bind duration:i:3140 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18654838431 --bind date:l:1755827801842 --bind duration:i:92 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16335568394 --bind date:l:1769441295985 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12412862268 --bind date:l:1753792513758 --bind duration:i:58 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12888419872 --bind date:l:1751612395638 --bind duration:i:84 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14313099062 --bind date:l:1774038176733 --bind duration:i:26 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16568386054 --bind date:l:1771198145741 --bind duration:i:2075 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13526728917 --bind date:l:1765189304526 --bind duration:i:498 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12156697054 --bind date:l:1768818232374 --bind duration:i:53 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14217932426 --bind date:l:1748579266780 --bind duration:i:9 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15132922030 --bind date:l:1748968256314 --bind duration:i:24 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17828347796 --bind date:l:1756066794706 --bind duration:i:643 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12312418990 --bind date:l:1755203155227 --bind duration:i:444 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15229668986 --bind date:l:1768348881426 --bind duration:i:18 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13354115577 --bind date:l:1745326882779 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16428872665 --bind date:l:1752748029748 --bind duration:i:7 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14304516278 --bind date:l:1755267358579 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16279289267 --bind date:l:1747680126993 --bind duration:i:23 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17979122150 --bind date:l:1774489802510 --bind duration:i:825 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17738323707 --bind date:l:1762208560105 --bind duration:i:12 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19127572059 --bind date:l:1768687014212 --bind duration:i:7 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14013358915 --bind date:l:1748291890990 --bind duration:i:46 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15514587667 --bind date:l:1763146375372 --bind duration:i:119 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16935862378 --bind date:l:1754458170012 --bind duration:i:858 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15389095510 --bind date:l:1757724878992 --bind duration:i:990 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17997171706 --bind date:l:1761978684791 --bind duration:i:103 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16254643657 --bind date:l:1766078174751 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17615429813 --bind date:l:1754848814320 --bind duration:i:87 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13535849685 --bind date:l:1762922291744 --bind duration:i:158 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12013033020 --bind date:l:1766922341405 --bind duration:i:834 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13482139442 --bind date:l:1751245080680 --bind duration:i:245 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18112768751 --bind date:l:1764285838616 --bind duration:i:1838 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15736792292 --bind date:l:1745976916293 --bind duration:i:83 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12365267738 --bind date:l:1759373296554 --bind duration:i:303 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12035578443 --bind date:l:1769340913097 --bind duration:i:57 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17839238435 --bind date:l:1760402385545 --bind duration:i:50 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16984508209 --bind date:l:1763328986634 --bind duration:i:84 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12808305545 --bind date:l:1749419142344 --bind duration:i:42 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18166614856 --bind date:l:1766615060652 --bind duration:i:115 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18526695481 --bind date:l:1750933203293 --bind duration:i:52 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14628875843 --bind date:l:1750734643282 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14613489602 --bind date:l:1758908485193 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17295812256 --bind date:l:1773691386759 --bind duration:i:3468 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13768344325 --bind date:l:1754643663172 --bind duration:i:72 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19076734075 --bind date:l:1748135400366 --bind duration:i:499 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16009862548 --bind date:l:1750559454465 --bind duration:i:19 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14853851306 --bind date:l:1749630797177 --bind duration:i:565 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13304374479 --bind date:l:1767184532562 --bind duration:i:236 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14524127994 --bind date:l:1745112354987 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16472179929 --bind date:l:1755677763486 --bind duration:i:67 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12676289048 --bind date:l:1751830391598 --bind duration:i:67 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19788991478 --bind date:l:1748646016112 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16336188017 --bind date:l:1760549122907 --bind duration:i:71 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13587889904 --bind date:l:1754239818965 --bind duration:i:95 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13265228136 --bind date:l:1763478465777 --bind duration:i:87 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12802191291 --bind date:l:1748545487347 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13597804089 --bind date:l:1745639963193 --bind duration:i:58 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15896819986 --bind date:l:1765867989877 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16965259570 --bind date:l:1755284728292 --bind duration:i:102 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19573956816 --bind date:l:1764864617056 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17677067285 --bind date:l:1756249905490 --bind duration:i:35 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13354306022 --bind date:l:1764552744116 --bind duration:i:574 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15638022455 --bind date:l:1765524852246 --bind duration:i:28 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14618679322 --bind date:l:1748092207563 --bind duration:i:29 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17236947701 --bind date:l:1760684115188 --bind duration:i:1355 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13133705512 --bind date:l:1772371246267 --bind duration:i:668 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18764711376 --bind date:l:1751207678983 --bind duration:i:389 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18213835189 --bind date:l:1745917679424 --bind duration:i:77 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13782032926 --bind date:l:1746422424156 --bind duration:i:1815 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19315816079 --bind date:l:1764066148612 --bind duration:i:2539 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18447501812 --bind date:l:1747492149236 --bind duration:i:25 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14527893740 --bind date:l:1760242678577 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19125311259 --bind date:l:1761819381360 --bind duration:i:729 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13084451111 --bind date:l:1751099669602 --bind duration:i:752 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13985773289 --bind date:l:1748918055372 --bind duration:i:570 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12294996585 --bind date:l:1765827636617 --bind duration:i:82 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17327454670 --bind date:l:1767886179049 --bind duration:i:820 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14827246624 --bind date:l:1753406873721 --bind duration:i:14 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12825708439 --bind date:l:1774484981255 --bind duration:i:26 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19129613733 --bind date:l:1765498469306 --bind duration:i:933 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12808661999 --bind date:l:1770663900084 --bind duration:i:304 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19882313889 --bind date:l:1761643570291 --bind duration:i:50 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16895557853 --bind date:l:1760224578632 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16047681768 --bind date:l:1759558960977 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17253885543 --bind date:l:1750836937019 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17706866520 --bind date:l:1770930995381 --bind duration:i:22 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15677355715 --bind date:l:1768615863980 --bind duration:i:29 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19762947970 --bind date:l:1769272890877 --bind duration:i:118 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18007855204 --bind date:l:1774208556586 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16436821199 --bind date:l:1766547626137 --bind duration:i:74 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19704101324 --bind date:l:1751274160544 --bind duration:i:74 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15822629459 --bind date:l:1759280855552 --bind duration:i:38 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14199275573 --bind date:l:1771409999226 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14092226578 --bind date:l:1770891675398 --bind duration:i:141 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12106552023 --bind date:l:1747837194908 --bind duration:i:13 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14719665374 --bind date:l:1766944508611 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16038946289 --bind date:l:1774211425705 --bind duration:i:78 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14563584177 --bind date:l:1744459563267 --bind duration:i:79 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18132112170 --bind date:l:1764614121192 --bind duration:i:2942 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14086462885 --bind date:l:1773283466354 --bind duration:i:100 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13675441954 --bind date:l:1774416139911 --bind duration:i:588 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19375985309 --bind date:l:1745740544654 --bind duration:i:56 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16013743759 --bind date:l:1771441855693 --bind duration:i:276 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19983718992 --bind date:l:1752465466924 --bind duration:i:56 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14173813551 --bind date:l:1754723942949 --bind duration:i:1912 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17544998270 --bind date:l:1760833761625 --bind duration:i:54 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16937569834 --bind date:l:1746685784733 --bind duration:i:677 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12984555172 --bind date:l:1753785657159 --bind duration:i:23 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18015223621 --bind date:l:1761817620429 --bind duration:i:49 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12043097602 --bind date:l:1760754872757 --bind duration:i:12 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18836325920 --bind date:l:1748716857240 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15116937467 --bind date:l:1751568443126 --bind duration:i:43 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17952464499 --bind date:l:1764870295057 --bind duration:i:267 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19203472219 --bind date:l:1752308003653 --bind duration:i:81 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18569394966 --bind date:l:1749250101923 --bind duration:i:47 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13857147488 --bind date:l:1745707199890 --bind duration:i:339 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15353826949 --bind date:l:1758418543442 --bind duration:i:94 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12535484561 --bind date:l:1762243435984 --bind duration:i:812 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12396022323 --bind date:l:1749388988041 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15078283882 --bind date:l:1754508641070 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14715334740 --bind date:l:1770565613727 --bind duration:i:1489 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15403445890 --bind date:l:1774640617502 --bind duration:i:85 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15512875513 --bind date:l:1768192814270 --bind duration:i:81 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12715366634 --bind date:l:1762995743806 --bind duration:i:50 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17083439515 --bind date:l:1766059147405 --bind duration:i:100 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14125739514 --bind date:l:1763253478047 --bind duration:i:2472 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12438838074 --bind date:l:1752241218823 --bind duration:i:54 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19453026085 --bind date:l:1765848542475 --bind duration:i:29 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12488548962 --bind date:l:1758701976152 --bind duration:i:53 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15813728347 --bind date:l:1758704841023 --bind duration:i:55 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12017554846 --bind date:l:1767317549639 --bind duration:i:117 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14323582093 --bind date:l:1745104902838 --bind duration:i:120 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16939908184 --bind date:l:1745510127096 --bind duration:i:9 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19673806457 --bind date:l:1744829778458 --bind duration:i:103 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12816768975 --bind date:l:1768030352226 --bind duration:i:163 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18482524739 --bind date:l:1751457937243 --bind duration:i:88 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19478262577 --bind date:l:1768091528818 --bind duration:i:98 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18389843586 --bind date:l:1769552106757 --bind duration:i:856 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12907927488 --bind date:l:1765629273462 --bind duration:i:832 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17303951493 --bind date:l:1769409852087 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19866252708 --bind date:l:1752360777195 --bind duration:i:39 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14085644311 --bind date:l:1762495854702 --bind duration:i:35 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18849763370 --bind date:l:1772499055884 --bind duration:i:105 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14119271694 --bind date:l:1757015183791 --bind duration:i:30 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17476762124 --bind date:l:1754080977144 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12078179454 --bind date:l:1758829910587 --bind duration:i:318 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17502004411 --bind date:l:1772128933873 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14557444536 --bind date:l:1753415234016 --bind duration:i:458 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15922874013 --bind date:l:1772239305197 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17703532742 --bind date:l:1774360165918 --bind duration:i:92 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17804837136 --bind date:l:1759012666430 --bind duration:i:658 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15863368188 --bind date:l:1761611338907 --bind duration:i:2448 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18035773446 --bind date:l:1770924424816 --bind duration:i:79 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15284641937 --bind date:l:1748012850695 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13898409332 --bind date:l:1760079291415 --bind duration:i:42 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18446705207 --bind date:l:1757680683820 --bind duration:i:42 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16304695636 --bind date:l:1749253553303 --bind duration:i:797 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18746729424 --bind date:l:1745342824261 --bind duration:i:79 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16955335455 --bind date:l:1774476469281 --bind duration:i:779 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18878986644 --bind date:l:1772349631932 --bind duration:i:736 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18795116942 --bind date:l:1760060850427 --bind duration:i:655 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16106321132 --bind date:l:1771691215419 --bind duration:i:382 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16323105653 --bind date:l:1749324564398 --bind duration:i:16 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12519256820 --bind date:l:1768251782638 --bind duration:i:680 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16657936984 --bind date:l:1771960979265 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18789912953 --bind date:l:1752491316972 --bind duration:i:142 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17489463439 --bind date:l:1768851465189 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13862571607 --bind date:l:1771865293059 --bind duration:i:62 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16409843439 --bind date:l:1770702038425 --bind duration:i:21 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16048079182 --bind date:l:1760337206303 --bind duration:i:830 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17917781473 --bind date:l:1749307085572 --bind duration:i:275 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12732821422 --bind date:l:1752514199906 --bind duration:i:13 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17495705361 --bind date:l:1747564193623 --bind duration:i:80 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12847983829 --bind date:l:1774419346575 --bind duration:i:119 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19947328504 --bind date:l:1769195416682 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19589145678 --bind date:l:1773808093393 --bind duration:i:99 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15605049401 --bind date:l:1758550621446 --bind duration:i:893 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15009848712 --bind date:l:1768211883190 --bind duration:i:56 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18372335008 --bind date:l:1744293572558 --bind duration:i:2041 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13128268261 --bind date:l:1747686888309 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15683904336 --bind date:l:1755583080138 --bind duration:i:79 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17448494990 --bind date:l:1767838374504 --bind duration:i:829 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16613881458 --bind date:l:1765555429308 --bind duration:i:95 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17748558482 --bind date:l:1770084900082 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14339855907 --bind date:l:1756719570117 --bind duration:i:79 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16186107403 --bind date:l:1770552241515 --bind duration:i:36 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19015357617 --bind date:l:1766093757150 --bind duration:i:5 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14047268882 --bind date:l:1756693177408 --bind duration:i:280 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14087854187 --bind date:l:1761977776597 --bind duration:i:610 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17413296506 --bind date:l:1767763430973 --bind duration:i:86 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15868017458 --bind date:l:1745762315355 --bind duration:i:28 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18657658064 --bind date:l:1746391856041 --bind duration:i:16 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19762777708 --bind date:l:1764277766892 --bind duration:i:99 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19073535205 --bind date:l:1753960509084 --bind duration:i:510 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13514181022 --bind date:l:1757051585199 --bind duration:i:3059 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19534764883 --bind date:l:1757297180552 --bind duration:i:76 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19508659750 --bind date:l:1749473393220 --bind duration:i:849 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17847025601 --bind date:l:1760514002919 --bind duration:i:32 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12912883953 --bind date:l:1762128134271 --bind duration:i:721 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14279516986 --bind date:l:1753445339533 --bind duration:i:237 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18277185271 --bind date:l:1774018225942 --bind duration:i:51 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16937831258 --bind date:l:1772398258645 --bind duration:i:43 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15363253763 --bind date:l:1770277837015 --bind duration:i:106 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16832649771 --bind date:l:1747366415708 --bind duration:i:45 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18944352800 --bind date:l:1768424256919 --bind duration:i:51 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13737334898 --bind date:l:1748446368395 --bind duration:i:63 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13044089780 --bind date:l:1760367304525 --bind duration:i:32 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12224138384 --bind date:l:1745743568023 --bind duration:i:83 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12236762178 --bind date:l:1751909297949 --bind duration:i:1793 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16372819254 --bind date:l:1766059982938 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16373086906 --bind date:l:1767291197823 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12084195347 --bind date:l:1754249995222 --bind duration:i:765 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19755333464 --bind date:l:1757454228121 --bind duration:i:865 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18429734772 --bind date:l:1744146472887 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17955215814 --bind date:l:1769792787427 --bind duration:i:175 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14243464099 --bind date:l:1762396748662 --bind duration:i:90 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13203597833 --bind date:l:1755581014169 --bind duration:i:47 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18427047246 --bind date:l:1747869298522 --bind duration:i:114 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17636864062 --bind date:l:1754521180445 --bind duration:i:780 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19286472933 --bind date:l:1750091085301 --bind duration:i:3106 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17139679531 --bind date:l:1772554938302 --bind duration:i:91 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13694488531 --bind date:l:1748836265066 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15327146684 --bind date:l:1754038757108 --bind duration:i:2049 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18943743216 --bind date:l:1759657860347 --bind duration:i:277 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17623265074 --bind date:l:1744046345737 --bind duration:i:874 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18423903705 --bind date:l:1756326831243 --bind duration:i:38 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14702597436 --bind date:l:1766986224100 --bind duration:i:85 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17098002894 --bind date:l:1763040716034 --bind duration:i:66 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15218044297 --bind date:l:1752026583898 --bind duration:i:185 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13533088597 --bind date:l:1764722658062 --bind duration:i:160 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19507567066 --bind date:l:1755081613987 --bind duration:i:96 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17953302873 --bind date:l:1748182041939 --bind duration:i:114 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12918309637 --bind date:l:1769327630453 --bind duration:i:78 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17854954750 --bind date:l:1762805139601 --bind duration:i:110 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16846672664 --bind date:l:1765623173283 --bind duration:i:102 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14609618968 --bind date:l:1769474957310 --bind duration:i:23 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16078439763 --bind date:l:1747054014780 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16343208431 --bind date:l:1748627975542 --bind duration:i:30 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15293861557 --bind date:l:1765837679859 --bind duration:i:75 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18674441240 --bind date:l:1765131149382 --bind duration:i:848 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15785425782 --bind date:l:1761924349249 --bind duration:i:695 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15988619613 --bind date:l:1748356619412 --bind duration:i:747 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13213022966 --bind date:l:1760854296937 --bind duration:i:114 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14522082137 --bind date:l:1753626394482 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12484666837 --bind date:l:1751997711753 --bind duration:i:427 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12287535656 --bind date:l:1754096636002 --bind duration:i:99 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17166996849 --bind date:l:1745179124077 --bind duration:i:80 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18836771027 --bind date:l:1765208599757 --bind duration:i:1962 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14363623590 --bind date:l:1770814228961 --bind duration:i:111 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12269838600 --bind date:l:1767034805909 --bind duration:i:216 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15557896017 --bind date:l:1754532308062 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15736237943 --bind date:l:1758303854289 --bind duration:i:62 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17093656997 --bind date:l:1748101754342 --bind duration:i:228 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16274915455 --bind date:l:1758161458988 --bind duration:i:42 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12734976034 --bind date:l:1770561856070 --bind duration:i:45 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17369759444 --bind date:l:1765718524373 --bind duration:i:96 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15052773293 --bind date:l:1770125910647 --bind duration:i:84 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19657202034 --bind date:l:1751692287087 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13337416637 --bind date:l:1771443330787 --bind duration:i:23 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15838468997 --bind date:l:1773192677683 --bind duration:i:283 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13062529986 --bind date:l:1753594377699 --bind duration:i:97 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18254101802 --bind date:l:1761094696790 --bind duration:i:58 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18304632176 --bind date:l:1744529344061 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12586275476 --bind date:l:1759249750750 --bind duration:i:97 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12076503983 --bind date:l:1762211905090 --bind duration:i:28 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15726486458 --bind date:l:1765900835341 --bind duration:i:42 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19209267582 --bind date:l:1746776725580 --bind duration:i:110 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16137889330 --bind date:l:1747356383638 --bind duration:i:852 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14636019141 --bind date:l:1770786538458 --bind duration:i:67 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13388763641 --bind date:l:1772877828854 --bind duration:i:1803 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12277927639 --bind date:l:1767017961616 --bind duration:i:2038 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15883412332 --bind date:l:1759009399119 --bind duration:i:260 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13314579406 --bind date:l:1754613835090 --bind duration:i:1008 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19147655873 --bind date:l:1757988523188 --bind duration:i:83 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17659244398 --bind date:l:1750681246435 --bind duration:i:16 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18844732008 --bind date:l:1768685328062 --bind duration:i:803 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19855225241 --bind date:l:1750166654371 --bind duration:i:181 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13652253983 --bind date:l:1767919837770 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13266119672 --bind date:l:1755024237338 --bind duration:i:97 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19935741233 --bind date:l:1757502187866 --bind duration:i:112 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18112595050 --bind date:l:1747982797866 --bind duration:i:276 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15175053348 --bind date:l:1763713102396 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15586164506 --bind date:l:1767659369269 --bind duration:i:98 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16906643259 --bind date:l:1762693278705 --bind duration:i:366 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13536655941 --bind date:l:1752417168529 --bind duration:i:1940 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13967798239 --bind date:l:1767316429805 --bind duration:i:91 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15123565366 --bind date:l:1757773281121 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17792906659 --bind date:l:1771249482070 --bind duration:i:384 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16505388979 --bind date:l:1753599170533 --bind duration:i:426 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12179461821 --bind date:l:1772892636957 --bind duration:i:76 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17594905598 --bind date:l:1764375203266 --bind duration:i:5 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17687762682 --bind date:l:1756211113734 --bind duration:i:300 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16833917551 --bind date:l:1745708246639 --bind duration:i:110 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15668713537 --bind date:l:1761232524706 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15323609689 --bind date:l:1770974520029 --bind duration:i:837 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13215739174 --bind date:l:1759104029384 --bind duration:i:23 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12979844064 --bind date:l:1754320922015 --bind duration:i:360 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14079136136 --bind date:l:1755253188897 --bind duration:i:377 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16528115044 --bind date:l:1750476193681 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17724509205 --bind date:l:1766120225790 --bind duration:i:112 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15022965172 --bind date:l:1749269739043 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17989377022 --bind date:l:1745889383687 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19043666043 --bind date:l:1763406078236 --bind duration:i:109 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12312716817 --bind date:l:1753763636604 --bind duration:i:3502 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16004269810 --bind date:l:1757409449076 --bind duration:i:45 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14519289934 --bind date:l:1757318898810 --bind duration:i:351 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12056167039 --bind date:l:1763758525460 --bind duration:i:105 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19932103651 --bind date:l:1762301264257 --bind duration:i:70 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17477889268 --bind date:l:1752159549745 --bind duration:i:2579 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12679465688 --bind date:l:1761119560783 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14163619838 --bind date:l:1756194740991 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15548708249 --bind date:l:1772886370111 --bind duration:i:99 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17026518177 --bind date:l:1765969964426 --bind duration:i:549 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13518966112 --bind date:l:1768500255673 --bind duration:i:2457 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12394917216 --bind date:l:1746805561597 --bind duration:i:614 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12423532902 --bind date:l:1745435450651 --bind duration:i:861 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18765384460 --bind date:l:1747923261600 --bind duration:i:609 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16179874798 --bind date:l:1767497650742 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15609638845 --bind date:l:1758603921716 --bind duration:i:104 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12847695662 --bind date:l:1761628385956 --bind duration:i:12 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18412064753 --bind date:l:1757086935181 --bind duration:i:2842 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15305587900 --bind date:l:1768473906769 --bind duration:i:297 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15967206625 --bind date:l:1751959870028 --bind duration:i:3467 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16903406430 --bind date:l:1745084037909 --bind duration:i:5 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15455431776 --bind date:l:1767685727665 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12858609686 --bind date:l:1773506043554 --bind duration:i:1739 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12767468008 --bind date:l:1768893871363 --bind duration:i:103 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18229912061 --bind date:l:1770657128305 --bind duration:i:2637 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16389675306 --bind date:l:1759613957345 --bind duration:i:359 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13097059677 --bind date:l:1760689758952 --bind duration:i:57 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15555402802 --bind date:l:1769471168866 --bind duration:i:49 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18787868637 --bind date:l:1761475937294 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19785201798 --bind date:l:1747204316809 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16802695106 --bind date:l:1763655266638 --bind duration:i:30 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17047334364 --bind date:l:1767401363142 --bind duration:i:60 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15635321627 --bind date:l:1753618231619 --bind duration:i:28 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15927305897 --bind date:l:1768056705268 --bind duration:i:103 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19909754289 --bind date:l:1756515422399 --bind duration:i:550 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17897483574 --bind date:l:1758087642103 --bind duration:i:86 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13518278447 --bind date:l:1753971986558 --bind duration:i:63 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12883665520 --bind date:l:1773313863163 --bind duration:i:48 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16882286197 --bind date:l:1756634770103 --bind duration:i:650 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12358622588 --bind date:l:1768219682993 --bind duration:i:81 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14395266930 --bind date:l:1757046644372 --bind duration:i:52 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16038008203 --bind date:l:1754833830502 --bind duration:i:134 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18832258553 --bind date:l:1748230459588 --bind duration:i:116 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15848779750 --bind date:l:1757949366774 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15929827812 --bind date:l:1761022103239 --bind duration:i:44 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12528675156 --bind date:l:1750304908327 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13035504076 --bind date:l:1773296848109 --bind duration:i:31 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13835991766 --bind date:l:1769987358418 --bind duration:i:29 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12825205353 --bind date:l:1756352767152 --bind duration:i:856 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13684334842 --bind date:l:1755439256043 --bind duration:i:2278 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14203175468 --bind date:l:1758337499694 --bind duration:i:111 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12148514798 --bind date:l:1755361333118 --bind duration:i:100 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17587219338 --bind date:l:1773713632750 --bind duration:i:133 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13347684788 --bind date:l:1760442666309 --bind duration:i:594 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18265669963 --bind date:l:1753366251648 --bind duration:i:110 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18209167164 --bind date:l:1751058228611 --bind duration:i:290 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15485419289 --bind date:l:1769951456333 --bind duration:i:52 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18376333292 --bind date:l:1757840031286 --bind duration:i:36 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17295066346 --bind date:l:1765476371041 --bind duration:i:111 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18893352912 --bind date:l:1774274086457 --bind duration:i:894 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19277201002 --bind date:l:1769230685205 --bind duration:i:78 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13015128950 --bind date:l:1745486573450 --bind duration:i:95 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18224569791 --bind date:l:1768588827709 --bind duration:i:5 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12133035919 --bind date:l:1761736617746 --bind duration:i:65 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15814693405 --bind date:l:1748475783789 --bind duration:i:87 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14644446441 --bind date:l:1771886040299 --bind duration:i:625 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16844752140 --bind date:l:1750718663596 --bind duration:i:322 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17296911400 --bind date:l:1761704702144 --bind duration:i:61 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14262858847 --bind date:l:1748040308538 --bind duration:i:723 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15313229796 --bind date:l:1767935676044 --bind duration:i:48 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15183805460 --bind date:l:1746574632631 --bind duration:i:50 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14197158829 --bind date:l:1768830804528 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15802555911 --bind date:l:1766981131209 --bind duration:i:39 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13574898854 --bind date:l:1766557922482 --bind duration:i:29 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14383359677 --bind date:l:1762506193165 --bind duration:i:18 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14409502950 --bind date:l:1744965053953 --bind duration:i:233 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12478108791 --bind date:l:1768347476422 --bind duration:i:37 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13096116950 --bind date:l:1765280816794 --bind duration:i:2604 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15064908544 --bind date:l:1753758697451 --bind duration:i:64 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17952686218 --bind date:l:1769510977234 --bind duration:i:85 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14732773610 --bind date:l:1773772534073 --bind duration:i:92 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16287979659 --bind date:l:1755289928782 --bind duration:i:1335 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13744548137 --bind date:l:1765775150657 --bind duration:i:20 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17402529974 --bind date:l:1757055561166 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19082137888 --bind date:l:1744216554884 --bind duration:i:14 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15539223616 --bind date:l:1773301602106 --bind duration:i:98 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16087508394 --bind date:l:1764547450725 --bind duration:i:70 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17327947040 --bind date:l:1748160617386 --bind duration:i:10 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13663795244 --bind date:l:1751848926081 --bind duration:i:49 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17474162906 --bind date:l:1752092864123 --bind duration:i:49 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17096747974 --bind date:l:1769233461016 --bind duration:i:65 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14297946161 --bind date:l:1764365464752 --bind duration:i:70 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18718342167 --bind date:l:1772079732356 --bind duration:i:322 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19579611825 --bind date:l:1771976232916 --bind duration:i:83 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13603788307 --bind date:l:1763092357599 --bind duration:i:169 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17902698467 --bind date:l:1750949791999 --bind duration:i:79 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19154155135 --bind date:l:1747754040350 --bind duration:i:3034 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19232138136 --bind date:l:1766401322815 --bind duration:i:69 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12983039329 --bind date:l:1749682731287 --bind duration:i:71 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15907993887 --bind date:l:1754434397754 --bind duration:i:824 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16716253124 --bind date:l:1765856495470 --bind duration:i:37 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13017852481 --bind date:l:1749140776046 --bind duration:i:3089 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19933102011 --bind date:l:1744525064283 --bind duration:i:111 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13994296721 --bind date:l:1750275964435 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14413076508 --bind date:l:1748237652253 --bind duration:i:3288 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12825409512 --bind date:l:1744572222904 --bind duration:i:79 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16079631032 --bind date:l:1762304335156 --bind duration:i:47 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12264518681 --bind date:l:1762102248358 --bind duration:i:148 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19928383947 --bind date:l:1746759071443 --bind duration:i:472 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12965258092 --bind date:l:1766045788491 --bind duration:i:27 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12106435620 --bind date:l:1770302140150 --bind duration:i:19 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18397047911 --bind date:l:1752311160093 --bind duration:i:868 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14997289824 --bind date:l:1753317856317 --bind duration:i:88 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15238193399 --bind date:l:1754005238932 --bind duration:i:33 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12493888551 --bind date:l:1771905209199 --bind duration:i:57 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14828627280 --bind date:l:1744568507773 --bind duration:i:45 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12806709736 --bind date:l:1745088106678 --bind duration:i:17 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18559557293 --bind date:l:1772785425377 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18719172676 --bind date:l:1774436536507 --bind duration:i:111 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17627866219 --bind date:l:1770323550408 --bind duration:i:16 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15062662674 --bind date:l:1754653184026 --bind duration:i:821 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17143398863 --bind date:l:1757794420564 --bind duration:i:68 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18479024453 --bind date:l:1754377432504 --bind duration:i:471 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15406273459 --bind date:l:1754145495327 --bind duration:i:363 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13937658885 --bind date:l:1749727833701 --bind duration:i:396 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15765818812 --bind date:l:1755311081513 --bind duration:i:44 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15078308820 --bind date:l:1764660017836 --bind duration:i:111 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18624846671 --bind date:l:1747159295295 --bind duration:i:78 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16858077516 --bind date:l:1756080770982 --bind duration:i:81 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17813575135 --bind date:l:1752012944380 --bind duration:i:58 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18518007385 --bind date:l:1771385216272 --bind duration:i:155 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14645395880 --bind date:l:1744529441018 --bind duration:i:106 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18705009056 --bind date:l:1773637892603 --bind duration:i:411 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14139419842 --bind date:l:1758165503526 --bind duration:i:65 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14516525789 --bind date:l:1773437209222 --bind duration:i:97 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17326153007 --bind date:l:1763817509816 --bind duration:i:42 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17908403909 --bind date:l:1771403340338 --bind duration:i:25 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15364168445 --bind date:l:1760974203064 --bind duration:i:3371 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16669487730 --bind date:l:1760960862776 --bind duration:i:30 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18568443792 --bind date:l:1770965409187 --bind duration:i:191 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12264851163 --bind date:l:1745663600252 --bind duration:i:112 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12338292891 --bind date:l:1752415648196 --bind duration:i:373 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12729738306 --bind date:l:1774753765675 --bind duration:i:11 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19629046737 --bind date:l:1747008599832 --bind duration:i:342 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14265049534 --bind date:l:1749671716021 --bind duration:i:43 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16779019005 --bind date:l:1773448161782 --bind duration:i:102 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16928345528 --bind date:l:1771706161728 --bind duration:i:475 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19838801653 --bind date:l:1755755677171 --bind duration:i:65 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13094349899 --bind date:l:1772894782835 --bind duration:i:886 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16424717764 --bind date:l:1764022144296 --bind duration:i:398 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19567636433 --bind date:l:1745054790246 --bind duration:i:6 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13005859357 --bind date:l:1751926512569 --bind duration:i:18 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15636787788 --bind date:l:1759427791536 --bind duration:i:38 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13979607425 --bind date:l:1750016214881 --bind duration:i:59 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18988949073 --bind date:l:1772789759963 --bind duration:i:108 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16005696554 --bind date:l:1760271535048 --bind duration:i:580 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13638758423 --bind date:l:1772467469445 --bind duration:i:69 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17836124476 --bind date:l:1768937228200 --bind duration:i:528 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16009806979 --bind date:l:1759029091906 --bind duration:i:691 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13024541224 --bind date:l:1762207693618 --bind duration:i:26 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15604328563 --bind date:l:1760394628113 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19049256816 --bind date:l:1767088161091 --bind duration:i:697 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12335733488 --bind date:l:1752706309221 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12508927599 --bind date:l:1755755590505 --bind duration:i:759 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17773185675 --bind date:l:1744854081309 --bind duration:i:257 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16156399095 --bind date:l:1768158161542 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18859275685 --bind date:l:1769162258489 --bind duration:i:116 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19933568524 --bind date:l:1765822436775 --bind duration:i:816 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14286118279 --bind date:l:1747890599284 --bind duration:i:417 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17576388330 --bind date:l:1747803243908 --bind duration:i:581 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19374547264 --bind date:l:1773375598505 --bind duration:i:456 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14768433513 --bind date:l:1770170386862 --bind duration:i:292 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17727299003 --bind date:l:1770014454609 --bind duration:i:31 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14384147787 --bind date:l:1764514965353 --bind duration:i:364 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14726083824 --bind date:l:1770521775542 --bind duration:i:116 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12935638017 --bind date:l:1751872946335 --bind duration:i:2442 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16323804896 --bind date:l:1771359751563 --bind duration:i:116 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17047527777 --bind date:l:1761315219245 --bind duration:i:32 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12703762038 --bind date:l:1749562321496 --bind duration:i:79 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14987879613 --bind date:l:1750636977742 --bind duration:i:1472 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15354811348 --bind date:l:1759044312288 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19299941582 --bind date:l:1772149733135 --bind duration:i:41 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18068073542 --bind date:l:1763384533011 --bind duration:i:352 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15654875871 --bind date:l:1757060654982 --bind duration:i:557 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17605615659 --bind date:l:1769759203907 --bind duration:i:80 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14754106018 --bind date:l:1771557098000 --bind duration:i:2680 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16898084693 --bind date:l:1752669669663 --bind duration:i:84 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17102815858 --bind date:l:1773608115254 --bind duration:i:854 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18247343161 --bind date:l:1757903043929 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12559409607 --bind date:l:1745721192033 --bind duration:i:20 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19422027933 --bind date:l:1746351758632 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15876644411 --bind date:l:1763537089835 --bind duration:i:115 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17233673944 --bind date:l:1751985275995 --bind duration:i:60 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16495282095 --bind date:l:1753834679638 --bind duration:i:622 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13352468993 --bind date:l:1748657877245 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15819634565 --bind date:l:1745247652316 --bind duration:i:3037 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17039281327 --bind date:l:1768718444304 --bind duration:i:87 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12732335520 --bind date:l:1771288701084 --bind duration:i:229 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16513655575 --bind date:l:1765765715640 --bind duration:i:1919 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17947085127 --bind date:l:1767200571232 --bind duration:i:52 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12527123124 --bind date:l:1756275119580 --bind duration:i:83 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18066659324 --bind date:l:1745779717407 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16779499667 --bind date:l:1773229348396 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15918483080 --bind date:l:1759308623108 --bind duration:i:827 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16145315895 --bind date:l:1772379645462 --bind duration:i:2603 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12783858627 --bind date:l:1757234037308 --bind duration:i:5 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16788232638 --bind date:l:1755135123553 --bind duration:i:26 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14529253792 --bind date:l:1756910643734 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19375797503 --bind date:l:1754666795563 --bind duration:i:44 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19189215498 --bind date:l:1767837897469 --bind duration:i:568 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16613343699 --bind date:l:1750856388248 --bind duration:i:102 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19507422406 --bind date:l:1774498306461 --bind duration:i:50 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14327516939 --bind date:l:1770961667664 --bind duration:i:39 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19857708143 --bind date:l:1772624530735 --bind duration:i:40 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19945074456 --bind date:l:1755073364251 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12206719195 --bind date:l:1761586821499 --bind duration:i:69 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18792435920 --bind date:l:1748960184199 --bind duration:i:37 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18697596585 --bind date:l:1746005148161 --bind duration:i:226 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12846065590 --bind date:l:1764340652781 --bind duration:i:107 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16352443805 --bind date:l:1756777338974 --bind duration:i:68 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19609363111 --bind date:l:1768259756213 --bind duration:i:36 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12064916058 --bind date:l:1747871156590 --bind duration:i:35 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14107947339 --bind date:l:1754864857937 --bind duration:i:66 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14772984181 --bind date:l:1758279166473 --bind duration:i:704 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16676064570 --bind date:l:1748474887427 --bind duration:i:59 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16534034199 --bind date:l:1760685874824 --bind duration:i:89 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12086631881 --bind date:l:1752697645924 --bind duration:i:927 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18544524181 --bind date:l:1753133906461 --bind duration:i:501 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15415385090 --bind date:l:1758327582259 --bind duration:i:1101 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14018799916 --bind date:l:1750728812119 --bind duration:i:86 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16663975849 --bind date:l:1744837779347 --bind duration:i:768 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12427509668 --bind date:l:1771499008419 --bind duration:i:96 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18895936131 --bind date:l:1768015690715 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18183173912 --bind date:l:1758149563044 --bind duration:i:87 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12329283585 --bind date:l:1744516093363 --bind duration:i:92 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12747574602 --bind date:l:1753776021305 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17019703743 --bind date:l:1764369393780 --bind duration:i:483 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17229481103 --bind date:l:1772435213964 --bind duration:i:70 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13656704118 --bind date:l:1765433662208 --bind duration:i:84 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12563132929 --bind date:l:1765015869807 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16567135413 --bind date:l:1752822675534 --bind duration:i:57 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19036065406 --bind date:l:1768018576588 --bind duration:i:115 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19545675302 --bind date:l:1745638108300 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15943711296 --bind date:l:1752686226774 --bind duration:i:2279 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17599082051 --bind date:l:1764303310084 --bind duration:i:7 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18089065400 --bind date:l:1765531884300 --bind duration:i:70 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14176605462 --bind date:l:1761564339407 --bind duration:i:621 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15773105326 --bind date:l:1758005415185 --bind duration:i:149 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16678331800 --bind date:l:1766693388803 --bind duration:i:11 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19062813971 --bind date:l:1772079826382 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19292592747 --bind date:l:1744349088593 --bind duration:i:89 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19755722941 --bind date:l:1765197092892 --bind duration:i:68 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17396043119 --bind date:l:1757613243321 --bind duration:i:161 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17207252154 --bind date:l:1748571757353 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16627809618 --bind date:l:1745155712581 --bind duration:i:53 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17029069239 --bind date:l:1763153562616 --bind duration:i:78 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17133768222 --bind date:l:1753697514352 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12345988753 --bind date:l:1747887443769 --bind duration:i:107 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16863586696 --bind date:l:1748084634373 --bind duration:i:1325 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14959971163 --bind date:l:1766914889315 --bind duration:i:288 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13632898811 --bind date:l:1758811519991 --bind duration:i:25 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18122983073 --bind date:l:1752443095731 --bind duration:i:514 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13315479446 --bind date:l:1763910958461 --bind duration:i:83 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19867608868 --bind date:l:1753565255090 --bind duration:i:660 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17454508743 --bind date:l:1747446271023 --bind duration:i:849 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17276412562 --bind date:l:1747747042705 --bind duration:i:48 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12457572846 --bind date:l:1746759885554 --bind duration:i:865 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12203721966 --bind date:l:1773793658632 --bind duration:i:759 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19148228993 --bind date:l:1758930282717 --bind duration:i:93 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19596972361 --bind date:l:1750375220566 --bind duration:i:55 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18607801442 --bind date:l:1761248867711 --bind duration:i:29 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14024885989 --bind date:l:1771036949756 --bind duration:i:85 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16477977960 --bind date:l:1757140579069 --bind duration:i:113 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14697075475 --bind date:l:1746699980060 --bind duration:i:865 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13019916848 --bind date:l:1746473285363 --bind duration:i:3224 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15773081819 --bind date:l:1761197653275 --bind duration:i:7 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19313924720 --bind date:l:1747774060859 --bind duration:i:88 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14134625407 --bind date:l:1746726634872 --bind duration:i:57 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18869402686 --bind date:l:1748517296865 --bind duration:i:1748 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16349024823 --bind date:l:1760255506519 --bind duration:i:70 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17146973725 --bind date:l:1764212985336 --bind duration:i:33 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13844557436 --bind date:l:1747744553836 --bind duration:i:738 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17442232616 --bind date:l:1749084086430 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15232508800 --bind date:l:1757449510453 --bind duration:i:85 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14468471208 --bind date:l:1746771180033 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17803466955 --bind date:l:1748856435300 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12206677290 --bind date:l:1744179009382 --bind duration:i:58 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14905811355 --bind date:l:1754762424811 --bind duration:i:827 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15378488773 --bind date:l:1754204032795 --bind duration:i:39 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13015491541 --bind date:l:1744684763764 --bind duration:i:553 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13774785776 --bind date:l:1774298320485 --bind duration:i:12 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14672375920 --bind date:l:1770139902239 --bind duration:i:773 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18178364357 --bind date:l:1745666728951 --bind duration:i:1849 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15793726492 --bind date:l:1768975223186 --bind duration:i:72 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18769182949 --bind date:l:1752528229667 --bind duration:i:142 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19459341995 --bind date:l:1759590888063 --bind duration:i:897 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13532221693 --bind date:l:1771499552207 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17594097857 --bind date:l:1749238881686 --bind duration:i:265 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14157284279 --bind date:l:1761024628700 --bind duration:i:45 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13173259022 --bind date:l:1745385155930 --bind duration:i:234 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15302446075 --bind date:l:1758977768188 --bind duration:i:265 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16577762207 --bind date:l:1745428518846 --bind duration:i:32 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16045545451 --bind date:l:1758309098641 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18376215450 --bind date:l:1762201184090 --bind duration:i:107 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14584408225 --bind date:l:1768739443877 --bind duration:i:100 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15296249896 --bind date:l:1768734264378 --bind duration:i:596 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18016101665 --bind date:l:1768602486027 --bind duration:i:779 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12779566975 --bind date:l:1749309805625 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18634764848 --bind date:l:1758956744887 --bind duration:i:22 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16308619146 --bind date:l:1772681160108 --bind duration:i:232 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13946233800 --bind date:l:1762702119139 --bind duration:i:1958 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16783207345 --bind date:l:1757137550041 --bind duration:i:42 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19907606845 --bind date:l:1758263961407 --bind duration:i:277 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13038418741 --bind date:l:1769932545236 --bind duration:i:24 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19313956025 --bind date:l:1763048811201 --bind duration:i:93 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16424568749 --bind date:l:1767206420395 --bind duration:i:263 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19963787793 --bind date:l:1756471084318 --bind duration:i:81 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19847912323 --bind date:l:1766919901232 --bind duration:i:15 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14398536593 --bind date:l:1764507187227 --bind duration:i:120 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19717215275 --bind date:l:1756011234521 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16382022297 --bind date:l:1759331036874 --bind duration:i:885 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16556357957 --bind date:l:1767060803925 --bind duration:i:115 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18863723562 --bind date:l:1765964287929 --bind duration:i:514 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19346566427 --bind date:l:1745901141822 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14545539822 --bind date:l:1756733825401 --bind duration:i:864 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15349997361 --bind date:l:1748184821899 --bind duration:i:3062 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14829049937 --bind date:l:1744584379801 --bind duration:i:752 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18936885553 --bind date:l:1754690956560 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12456725828 --bind date:l:1757815511055 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16447781877 --bind date:l:1749633611148 --bind duration:i:205 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14675102763 --bind date:l:1773624392611 --bind duration:i:90 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16435289109 --bind date:l:1757712787231 --bind duration:i:49 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19856186870 --bind date:l:1771693424015 --bind duration:i:87 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15019119009 --bind date:l:1749953304575 --bind duration:i:87 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19539118461 --bind date:l:1744955166492 --bind duration:i:51 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12934758111 --bind date:l:1759661752692 --bind duration:i:1639 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13678211427 --bind date:l:1752297418914 --bind duration:i:58 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13215742361 --bind date:l:1759327307211 --bind duration:i:622 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16726138689 --bind date:l:1755428965591 --bind duration:i:112 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15908815037 --bind date:l:1769770454646 --bind duration:i:63 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18866381669 --bind date:l:1772044808808 --bind duration:i:115 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16469615181 --bind date:l:1760802114270 --bind duration:i:113 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17795553725 --bind date:l:1759884645722 --bind duration:i:118 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12476691555 --bind date:l:1759878211982 --bind duration:i:640 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16954192821 --bind date:l:1771988547725 --bind duration:i:2380 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15805711935 --bind date:l:1753288317510 --bind duration:i:63 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12199592802 --bind date:l:1751721402343 --bind duration:i:2563 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17699131404 --bind date:l:1755021148244 --bind duration:i:494 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12057857556 --bind date:l:1754235071520 --bind duration:i:467 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18638702968 --bind date:l:1748731929620 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16562157739 --bind date:l:1765577218699 --bind duration:i:85 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12228394247 --bind date:l:1769821611453 --bind duration:i:32 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16892502960 --bind date:l:1751464184629 --bind duration:i:65 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13447057902 --bind date:l:1745913540310 --bind duration:i:180 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18019593888 --bind date:l:1756464231856 --bind duration:i:159 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15059318507 --bind date:l:1768112689240 --bind duration:i:110 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18697329137 --bind date:l:1750007099617 --bind duration:i:23 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13655591495 --bind date:l:1767525838117 --bind duration:i:115 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12064913714 --bind date:l:1749026545880 --bind duration:i:107 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17612021352 --bind date:l:1770450677599 --bind duration:i:63 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19186899113 --bind date:l:1770596827466 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18208481135 --bind date:l:1746027825252 --bind duration:i:785 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15775499656 --bind date:l:1764199593812 --bind duration:i:706 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17016615173 --bind date:l:1750087335365 --bind duration:i:49 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12448581950 --bind date:l:1746312352806 --bind duration:i:120 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14309032502 --bind date:l:1767270417779 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13889276263 --bind date:l:1771711903490 --bind duration:i:118 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14408863363 --bind date:l:1744143004146 --bind duration:i:3298 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17953615188 --bind date:l:1746380419306 --bind duration:i:535 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12658638950 --bind date:l:1768756060140 --bind duration:i:2100 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15522786788 --bind date:l:1751398640398 --bind duration:i:66 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12713729840 --bind date:l:1747789154891 --bind duration:i:103 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15225925181 --bind date:l:1756207137151 --bind duration:i:10 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15567947103 --bind date:l:1759020241436 --bind duration:i:83 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16046841948 --bind date:l:1758160159577 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15705945083 --bind date:l:1755783656765 --bind duration:i:60 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12146108849 --bind date:l:1745054435230 --bind duration:i:80 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16485224278 --bind date:l:1764552667618 --bind duration:i:1349 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12402334292 --bind date:l:1770121895816 --bind duration:i:53 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12665967112 --bind date:l:1767233395345 --bind duration:i:309 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18289838078 --bind date:l:1762887849148 --bind duration:i:14 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18335473814 --bind date:l:1770139141508 --bind duration:i:107 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16585949914 --bind date:l:1752996436977 --bind duration:i:119 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16226332397 --bind date:l:1761494356103 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19734991982 --bind date:l:1748173348793 --bind duration:i:112 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12613292527 --bind date:l:1758790684968 --bind duration:i:45 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13007693750 --bind date:l:1766500909311 --bind duration:i:361 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18468912056 --bind date:l:1757864124957 --bind duration:i:11 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18172816946 --bind date:l:1756828862153 --bind duration:i:2561 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16777779789 --bind date:l:1751096758273 --bind duration:i:45 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15462453611 --bind date:l:1750438448527 --bind duration:i:101 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14628083574 --bind date:l:1765533563809 --bind duration:i:54 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18146526320 --bind date:l:1759501722333 --bind duration:i:80 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18464806132 --bind date:l:1748361550748 --bind duration:i:119 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18392681493 --bind date:l:1770082472320 --bind duration:i:39 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16354522453 --bind date:l:1767662088510 --bind duration:i:120 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16409928965 --bind date:l:1764288373370 --bind duration:i:1857 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17982552030 --bind date:l:1748742359108 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19109507181 --bind date:l:1744277273726 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13916993321 --bind date:l:1750642068727 --bind duration:i:161 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13656348970 --bind date:l:1746788694457 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13549547616 --bind date:l:1749838608029 --bind duration:i:66 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12676067310 --bind date:l:1755735681435 --bind duration:i:56 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16805751568 --bind date:l:1757149345874 --bind duration:i:56 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19873539861 --bind date:l:1768300496414 --bind duration:i:115 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13896882862 --bind date:l:1753281049271 --bind duration:i:2705 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16745442086 --bind date:l:1745649568456 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18053745273 --bind date:l:1755706281468 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16447203756 --bind date:l:1745764245598 --bind duration:i:405 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12846175373 --bind date:l:1750554537185 --bind duration:i:17 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14033776170 --bind date:l:1763410467029 --bind duration:i:60 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12709728693 --bind date:l:1761879126337 --bind duration:i:102 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18597614262 --bind date:l:1772912023042 --bind duration:i:119 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18746379008 --bind date:l:1746352619015 --bind duration:i:622 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16029588948 --bind date:l:1768036134952 --bind duration:i:485 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14865307231 --bind date:l:1771295887129 --bind duration:i:786 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16678139921 --bind date:l:1759483902416 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16669119723 --bind date:l:1757656926811 --bind duration:i:755 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16185714177 --bind date:l:1761455230720 --bind duration:i:1848 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17719475221 --bind date:l:1764763574228 --bind duration:i:1339 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19648872877 --bind date:l:1763911553740 --bind duration:i:319 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16663763408 --bind date:l:1773282158372 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16388714459 --bind date:l:1771510718632 --bind duration:i:100 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17266361072 --bind date:l:1759136264652 --bind duration:i:225 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12498455722 --bind date:l:1770269945699 --bind duration:i:858 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15382062786 --bind date:l:1748816590898 --bind duration:i:68 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12456121127 --bind date:l:1759771096718 --bind duration:i:113 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17849197700 --bind date:l:1754671541727 --bind duration:i:2809 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18562274689 --bind date:l:1753158901953 --bind duration:i:89 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18359357389 --bind date:l:1768306500871 --bind duration:i:24 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15197172368 --bind date:l:1772801451530 --bind duration:i:37 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19265603511 --bind date:l:1758763404209 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18706509279 --bind date:l:1767380002891 --bind duration:i:681 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15073257582 --bind date:l:1745878274828 --bind duration:i:186 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17504778559 --bind date:l:1748013287943 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15974712028 --bind date:l:1750080370982 --bind duration:i:96 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17798682987 --bind date:l:1763042897780 --bind duration:i:102 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12812709131 --bind date:l:1770216854212 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17327433626 --bind date:l:1759241757625 --bind duration:i:837 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15155529162 --bind date:l:1771523017331 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13465331374 --bind date:l:1763901153088 --bind duration:i:29 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13099477421 --bind date:l:1758226875798 --bind duration:i:97 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19109146847 --bind date:l:1767320040782 --bind duration:i:140 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19425885109 --bind date:l:1773055048963 --bind duration:i:567 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19374605553 --bind date:l:1771270047840 --bind duration:i:18 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12866426843 --bind date:l:1774054444277 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16872506601 --bind date:l:1749797581975 --bind duration:i:93 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19233629022 --bind date:l:1759923643063 --bind duration:i:34 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13269094036 --bind date:l:1768011841731 --bind duration:i:13 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12133694411 --bind date:l:1750825962307 --bind duration:i:402 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19329503652 --bind date:l:1744517666687 --bind duration:i:97 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16604007720 --bind date:l:1751405505380 --bind duration:i:89 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13964804884 --bind date:l:1753179880211 --bind duration:i:44 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18123451230 --bind date:l:1765913753038 --bind duration:i:70 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12422026219 --bind date:l:1751647473394 --bind duration:i:2428 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17356404090 --bind date:l:1744164708207 --bind duration:i:37 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14692905395 --bind date:l:1765812439587 --bind duration:i:1794 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18603332054 --bind date:l:1769429721926 --bind duration:i:567 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13774643113 --bind date:l:1770231779598 --bind duration:i:77 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18329882311 --bind date:l:1760944082081 --bind duration:i:61 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12015283291 --bind date:l:1751602620350 --bind duration:i:64 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13062062733 --bind date:l:1767200218673 --bind duration:i:218 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17099223912 --bind date:l:1754373413940 --bind duration:i:30 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12267053464 --bind date:l:1769511757805 --bind duration:i:56 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14432797688 --bind date:l:1767116469588 --bind duration:i:33 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19589385168 --bind date:l:1766096524757 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14216544217 --bind date:l:1773969407872 --bind duration:i:211 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16349091250 --bind date:l:1758565420539 --bind duration:i:106 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17462348434 --bind date:l:1750106670101 --bind duration:i:90 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15666964208 --bind date:l:1757521579464 --bind duration:i:94 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15863637528 --bind date:l:1753406438447 --bind duration:i:6 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12183473749 --bind date:l:1758358318827 --bind duration:i:57 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19297203542 --bind date:l:1762740916839 --bind duration:i:384 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12813442235 --bind date:l:1757341085627 --bind duration:i:91 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12103942913 --bind date:l:1755110713029 --bind duration:i:123 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19022867864 --bind date:l:1766009251203 --bind duration:i:117 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16998437514 --bind date:l:1758077387953 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14655538908 --bind date:l:1747947052951 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16046101640 --bind date:l:1769468912776 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18952241946 --bind date:l:1745618532051 --bind duration:i:93 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14883359758 --bind date:l:1753170226253 --bind duration:i:47 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13724676292 --bind date:l:1765740142181 --bind duration:i:12 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12143625277 --bind date:l:1761151533812 --bind duration:i:25 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15005522642 --bind date:l:1763855903268 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16414433690 --bind date:l:1767184227591 --bind duration:i:398 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18384168621 --bind date:l:1758995313272 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18244333159 --bind date:l:1750915922360 --bind duration:i:76 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19205081767 --bind date:l:1771272318977 --bind duration:i:2635 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17748518441 --bind date:l:1745697351131 --bind duration:i:94 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14008923186 --bind date:l:1746555274892 --bind duration:i:105 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18732277672 --bind date:l:1744873294924 --bind duration:i:8 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19925231846 --bind date:l:1761966052218 --bind duration:i:118 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14217835213 --bind date:l:1747036794751 --bind duration:i:58 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15825823598 --bind date:l:1750905923976 --bind duration:i:7 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19497674760 --bind date:l:1749051694737 --bind duration:i:318 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17488705168 --bind date:l:1753085746954 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17409696465 --bind date:l:1746460115228 --bind duration:i:52 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16322597753 --bind date:l:1754602386240 --bind duration:i:79 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13137453239 --bind date:l:1773728015917 --bind duration:i:292 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12093035997 --bind date:l:1768643186336 --bind duration:i:1051 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17388677936 --bind date:l:1768737942602 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17529432409 --bind date:l:1745163458556 --bind duration:i:198 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13263999088 --bind date:l:1761434207954 --bind duration:i:35 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19773406962 --bind date:l:1769364801146 --bind duration:i:52 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13103822404 --bind date:l:1762979313983 --bind duration:i:109 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15345748542 --bind date:l:1763328655770 --bind duration:i:24 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19344659914 --bind date:l:1759416285451 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13184871939 --bind date:l:1759760352432 --bind duration:i:692 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19819457250 --bind date:l:1744636385344 --bind duration:i:117 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19377654438 --bind date:l:1765970123822 --bind duration:i:1771 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15987434676 --bind date:l:1768763503702 --bind duration:i:10 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16386668764 --bind date:l:1765676563745 --bind duration:i:96 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16832085613 --bind date:l:1770629797259 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13814625944 --bind date:l:1766832744976 --bind duration:i:101 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18765932597 --bind date:l:1744225374757 --bind duration:i:51 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16677593527 --bind date:l:1769209098254 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17877453981 --bind date:l:1758146708716 --bind duration:i:257 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16666318799 --bind date:l:1748945505765 --bind duration:i:43 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15543817769 --bind date:l:1761075918293 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14072774000 --bind date:l:1751466880879 --bind duration:i:20 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18567697843 --bind date:l:1760510634418 --bind duration:i:70 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16899778510 --bind date:l:1752346137641 --bind duration:i:486 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13489798743 --bind date:l:1751252319853 --bind duration:i:72 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12945431889 --bind date:l:1750556599488 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14456071798 --bind date:l:1760731054105 --bind duration:i:889 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16344534201 --bind date:l:1756860760580 --bind duration:i:32 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17684617752 --bind date:l:1755175329145 --bind duration:i:66 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19398261788 --bind date:l:1771681618902 --bind duration:i:101 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14086029633 --bind date:l:1751076851248 --bind duration:i:47 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12765014181 --bind date:l:1769048456188 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17283087050 --bind date:l:1752438876908 --bind duration:i:458 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18189837297 --bind date:l:1755482121875 --bind duration:i:66 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15074675287 --bind date:l:1762877806116 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15584565438 --bind date:l:1758375172239 --bind duration:i:77 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14145955243 --bind date:l:1764828245186 --bind duration:i:79 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18346252539 --bind date:l:1763853952769 --bind duration:i:35 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17439908049 --bind date:l:1747360109808 --bind duration:i:118 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13639248477 --bind date:l:1770605833877 --bind duration:i:120 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17598452132 --bind date:l:1753193590512 --bind duration:i:32 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19483547671 --bind date:l:1744169525136 --bind duration:i:19 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17135241366 --bind date:l:1749663537560 --bind duration:i:96 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17966199922 --bind date:l:1748259460743 --bind duration:i:900 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15144873474 --bind date:l:1768437123837 --bind duration:i:2341 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17924357465 --bind date:l:1745904848566 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18579075135 --bind date:l:1772775326566 --bind duration:i:782 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19029604057 --bind date:l:1759478055596 --bind duration:i:866 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15665999160 --bind date:l:1755977179132 --bind duration:i:871 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18426452749 --bind date:l:1744575860713 --bind duration:i:52 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15159234796 --bind date:l:1767606543860 --bind duration:i:495 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12686376973 --bind date:l:1762983073141 --bind duration:i:117 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19706523098 --bind date:l:1753266573241 --bind duration:i:756 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19844312480 --bind date:l:1750025656112 --bind duration:i:483 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16346696805 --bind date:l:1752926248124 --bind duration:i:608 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14939481023 --bind date:l:1756656706334 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16195862342 --bind date:l:1764684101469 --bind duration:i:97 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16474436240 --bind date:l:1758584680081 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14785895650 --bind date:l:1770065012928 --bind duration:i:120 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18402565202 --bind date:l:1747496324639 --bind duration:i:118 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12992986257 --bind date:l:1755047541469 --bind duration:i:22 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12474395714 --bind date:l:1769293717871 --bind duration:i:103 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14112964763 --bind date:l:1759690532110 --bind duration:i:93 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16552963760 --bind date:l:1774265505386 --bind duration:i:75 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16725853189 --bind date:l:1773091469178 --bind duration:i:38 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14486434277 --bind date:l:1770755618504 --bind duration:i:117 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12127641762 --bind date:l:1770890667849 --bind duration:i:10 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14067696226 --bind date:l:1765734008253 --bind duration:i:85 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15734696249 --bind date:l:1767757936752 --bind duration:i:1208 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16465976383 --bind date:l:1752448061393 --bind duration:i:38 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18935839431 --bind date:l:1774422666155 --bind duration:i:35 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14308206239 --bind date:l:1769605970851 --bind duration:i:14 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16237861248 --bind date:l:1757883570213 --bind duration:i:223 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16302955883 --bind date:l:1747831669090 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19233071918 --bind date:l:1762531010639 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16273661683 --bind date:l:1749520719304 --bind duration:i:1054 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14622128411 --bind date:l:1771544510391 --bind duration:i:12 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14454103652 --bind date:l:1766107812919 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17035817959 --bind date:l:1772999353210 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14755769189 --bind date:l:1744918226096 --bind duration:i:15 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12653902101 --bind date:l:1760350398936 --bind duration:i:45 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17505476733 --bind date:l:1764169820959 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13253322611 --bind date:l:1751539861827 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18308122418 --bind date:l:1767068124040 --bind duration:i:89 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12598004544 --bind date:l:1759388400364 --bind duration:i:14 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16113707634 --bind date:l:1767357058813 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17964119985 --bind date:l:1767103832754 --bind duration:i:58 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18713428949 --bind date:l:1760677172709 --bind duration:i:37 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17789013844 --bind date:l:1757419037489 --bind duration:i:113 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15817516784 --bind date:l:1767172578792 --bind duration:i:498 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15299746482 --bind date:l:1767147622743 --bind duration:i:1335 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13533153263 --bind date:l:1773677097266 --bind duration:i:79 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12233445925 --bind date:l:1751355612261 --bind duration:i:212 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14899767760 --bind date:l:1748810507982 --bind duration:i:573 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14854943216 --bind date:l:1748938915968 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15143554804 --bind date:l:1749406199121 --bind duration:i:37 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16679877856 --bind date:l:1756634309531 --bind duration:i:359 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17644402180 --bind date:l:1758463105481 --bind duration:i:87 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18314999610 --bind date:l:1774083181945 --bind duration:i:46 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13143955223 --bind date:l:1760452113409 --bind duration:i:62 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14902722079 --bind date:l:1770766687445 --bind duration:i:250 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17592766937 --bind date:l:1771708481491 --bind duration:i:43 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12476993980 --bind date:l:1770552084506 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13189979116 --bind date:l:1762036212923 --bind duration:i:2310 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17619114024 --bind date:l:1758721393165 --bind duration:i:29 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19839399180 --bind date:l:1749183791604 --bind duration:i:286 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19702082170 --bind date:l:1763018552087 --bind duration:i:212 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17933325571 --bind date:l:1771720277111 --bind duration:i:9 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13179114044 --bind date:l:1749329643020 --bind duration:i:244 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13347064761 --bind date:l:1745820616801 --bind duration:i:2087 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12749087008 --bind date:l:1760851263035 --bind duration:i:117 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18215845737 --bind date:l:1767528014292 --bind duration:i:117 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15396822371 --bind date:l:1754452203876 --bind duration:i:77 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19342191375 --bind date:l:1770342679072 --bind duration:i:50 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14127451324 --bind date:l:1749200696391 --bind duration:i:27 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18245853282 --bind date:l:1751763453689 --bind duration:i:2171 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13297973622 --bind date:l:1774211735015 --bind duration:i:508 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17007976235 --bind date:l:1755081816265 --bind duration:i:526 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14087686678 --bind date:l:1765841288334 --bind duration:i:27 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15053111863 --bind date:l:1772048704167 --bind duration:i:59 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18997482590 --bind date:l:1763160124234 --bind duration:i:48 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18796704741 --bind date:l:1764620419846 --bind duration:i:769 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12115021603 --bind date:l:1765165394127 --bind duration:i:91 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16995797688 --bind date:l:1763841003354 --bind duration:i:784 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17005698149 --bind date:l:1762329432743 --bind duration:i:30 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15552152336 --bind date:l:1766719217834 --bind duration:i:442 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19166004291 --bind date:l:1766072435508 --bind duration:i:78 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16663618552 --bind date:l:1749539055450 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13506253031 --bind date:l:1768243822089 --bind duration:i:497 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17474024968 --bind date:l:1774771428217 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14789778631 --bind date:l:1762267794145 --bind duration:i:752 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12363055595 --bind date:l:1759569242382 --bind duration:i:1447 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16082521762 --bind date:l:1772832946515 --bind duration:i:58 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12357671063 --bind date:l:1755746701736 --bind duration:i:111 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16058052922 --bind date:l:1772187250990 --bind duration:i:109 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17126092923 --bind date:l:1764390055724 --bind duration:i:26 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17493609198 --bind date:l:1750043771751 --bind duration:i:850 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16107685546 --bind date:l:1745926149340 --bind duration:i:89 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13454403580 --bind date:l:1761108423765 --bind duration:i:446 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13487401867 --bind date:l:1772178147557 --bind duration:i:877 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15286209852 --bind date:l:1759525142611 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14834398043 --bind date:l:1758303325341 --bind duration:i:43 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16206607632 --bind date:l:1756896334386 --bind duration:i:579 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12527564435 --bind date:l:1748066111212 --bind duration:i:66 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17648412771 --bind date:l:1746592968247 --bind duration:i:42 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14888226679 --bind date:l:1771602767881 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12519368773 --bind date:l:1773559892321 --bind duration:i:25 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14582526923 --bind date:l:1755634387327 --bind duration:i:95 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12099586189 --bind date:l:1767860664959 --bind duration:i:102 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17839709076 --bind date:l:1768375838872 --bind duration:i:31 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19785913486 --bind date:l:1751046863961 --bind duration:i:25 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15867163225 --bind date:l:1766536149359 --bind duration:i:576 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15579023097 --bind date:l:1766021831604 --bind duration:i:107 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14287628860 --bind date:l:1757769998944 --bind duration:i:58 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16245811667 --bind date:l:1756829266059 --bind duration:i:109 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19693202813 --bind date:l:1767910052205 --bind duration:i:875 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13653074461 --bind date:l:1755121451949 --bind duration:i:42 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19416246021 --bind date:l:1748764604936 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17924129008 --bind date:l:1752710512827 --bind duration:i:479 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16488697325 --bind date:l:1770070412538 --bind duration:i:93 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14546388901 --bind date:l:1768286242629 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14847105163 --bind date:l:1747118048403 --bind duration:i:45 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17357898373 --bind date:l:1745946287387 --bind duration:i:93 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19893628735 --bind date:l:1757062579203 --bind duration:i:664 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17187157130 --bind date:l:1772809266984 --bind duration:i:34 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15872082562 --bind date:l:1763145763928 --bind duration:i:101 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12224084618 --bind date:l:1759286959629 --bind duration:i:253 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17108131997 --bind date:l:1763849140095 --bind duration:i:13 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18635494601 --bind date:l:1755546333803 --bind duration:i:88 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15144414517 --bind date:l:1761277447419 --bind duration:i:441 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14272354144 --bind date:l:1774221325619 --bind duration:i:68 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14649681475 --bind date:l:1759092442491 --bind duration:i:26 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18796798644 --bind date:l:1770129970028 --bind duration:i:79 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17957895938 --bind date:l:1757129037340 --bind duration:i:65 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12527518790 --bind date:l:1759508114291 --bind duration:i:1836 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16606009508 --bind date:l:1754064705496 --bind duration:i:49 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13295135129 --bind date:l:1761123684797 --bind duration:i:373 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17934554480 --bind date:l:1746566271956 --bind duration:i:2266 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15844303089 --bind date:l:1767162073246 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18238935008 --bind date:l:1744285499247 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15728699826 --bind date:l:1767592770499 --bind duration:i:2497 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15399588515 --bind date:l:1753160318223 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12878636526 --bind date:l:1749470864629 --bind duration:i:42 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14456288097 --bind date:l:1770147724125 --bind duration:i:338 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18943717096 --bind date:l:1761787319983 --bind duration:i:69 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14313448838 --bind date:l:1745008791000 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13349142653 --bind date:l:1770786147435 --bind duration:i:82 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19659557568 --bind date:l:1749624781161 --bind duration:i:184 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19458812114 --bind date:l:1769751470672 --bind duration:i:71 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19132002740 --bind date:l:1773561784342 --bind duration:i:711 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18772251663 --bind date:l:1762592445510 --bind duration:i:87 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15017046364 --bind date:l:1773094054479 --bind duration:i:34 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15089838631 --bind date:l:1747232780595 --bind duration:i:24 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18372285914 --bind date:l:1772882760410 --bind duration:i:549 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14032301230 --bind date:l:1774087305630 --bind duration:i:188 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12558644622 --bind date:l:1771682682665 --bind duration:i:97 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17848812010 --bind date:l:1752569365938 --bind duration:i:45 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18288008394 --bind date:l:1765974066460 --bind duration:i:1944 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16087921577 --bind date:l:1772653217796 --bind duration:i:221 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17027218104 --bind date:l:1752772183701 --bind duration:i:3545 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19082724077 --bind date:l:1771887394968 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13042546911 --bind date:l:1752388185668 --bind duration:i:56 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13925079694 --bind date:l:1752637105447 --bind duration:i:108 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17869468007 --bind date:l:1752228963868 --bind duration:i:21 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14334284561 --bind date:l:1772412288908 --bind duration:i:112 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16993775365 --bind date:l:1759626445034 --bind duration:i:30 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16597058508 --bind date:l:1770710175809 --bind duration:i:17 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12299749123 --bind date:l:1747789258418 --bind duration:i:77 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12619473431 --bind date:l:1752541364954 --bind duration:i:1257 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18688847084 --bind date:l:1760137009869 --bind duration:i:95 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13514159158 --bind date:l:1746680440029 --bind duration:i:406 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15999064361 --bind date:l:1763051036721 --bind duration:i:10 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13975991899 --bind date:l:1756807360812 --bind duration:i:49 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16783969812 --bind date:l:1749825343659 --bind duration:i:34 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19234466877 --bind date:l:1745067860981 --bind duration:i:58 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13009061992 --bind date:l:1753683922065 --bind duration:i:35 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16525842951 --bind date:l:1755285638702 --bind duration:i:60 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12113615592 --bind date:l:1760663341812 --bind duration:i:886 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13472199183 --bind date:l:1753156131678 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18125544797 --bind date:l:1768448252228 --bind duration:i:278 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18138035348 --bind date:l:1766781146017 --bind duration:i:616 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13485634348 --bind date:l:1767436455893 --bind duration:i:823 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15577766489 --bind date:l:1774345351979 --bind duration:i:67 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18808869927 --bind date:l:1771612386512 --bind duration:i:85 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13475848322 --bind date:l:1751289564115 --bind duration:i:27 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13834328694 --bind date:l:1757924035682 --bind duration:i:60 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12963533328 --bind date:l:1769188119257 --bind duration:i:110 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16148747124 --bind date:l:1750864194193 --bind duration:i:71 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16518905931 --bind date:l:1746412172517 --bind duration:i:305 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16993035425 --bind date:l:1756035964523 --bind duration:i:66 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18559332885 --bind date:l:1762531317341 --bind duration:i:117 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18933745793 --bind date:l:1753886342436 --bind duration:i:27 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12084129953 --bind date:l:1767406600110 --bind duration:i:49 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12397685780 --bind date:l:1774302898874 --bind duration:i:1810 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16869419452 --bind date:l:1767470794272 --bind duration:i:57 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18462272149 --bind date:l:1744671559213 --bind duration:i:224 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12344364353 --bind date:l:1770201845165 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17708952673 --bind date:l:1763327820914 --bind duration:i:741 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13215674717 --bind date:l:1767118062602 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19432251767 --bind date:l:1757913569289 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17974575291 --bind date:l:1768964034650 --bind duration:i:66 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19973405017 --bind date:l:1765172452772 --bind duration:i:3115 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13678021874 --bind date:l:1767785088904 --bind duration:i:856 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12596785393 --bind date:l:1755677341538 --bind duration:i:116 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12357163963 --bind date:l:1755937456522 --bind duration:i:53 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14789887015 --bind date:l:1766136915884 --bind duration:i:103 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18479584338 --bind date:l:1757771820434 --bind duration:i:7 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18475534259 --bind date:l:1759943653401 --bind duration:i:512 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16102326597 --bind date:l:1755368677163 --bind duration:i:1870 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15807297149 --bind date:l:1764641904183 --bind duration:i:59 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15162518234 --bind date:l:1771572072965 --bind duration:i:71 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19724933075 --bind date:l:1754749459676 --bind duration:i:95 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17754445348 --bind date:l:1753784725570 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16175899644 --bind date:l:1768379833417 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15203672291 --bind date:l:1748034864582 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12313422371 --bind date:l:1771770109640 --bind duration:i:103 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12577561639 --bind date:l:1762457917405 --bind duration:i:89 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15986596862 --bind date:l:1758123695466 --bind duration:i:469 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19814938993 --bind date:l:1764840438422 --bind duration:i:74 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17333908819 --bind date:l:1767489172635 --bind duration:i:9 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17279336743 --bind date:l:1747689250564 --bind duration:i:772 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16897962461 --bind date:l:1756211080730 --bind duration:i:184 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17344526811 --bind date:l:1756934161212 --bind duration:i:728 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13933815074 --bind date:l:1772569263051 --bind duration:i:450 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13174922929 --bind date:l:1761169185730 --bind duration:i:152 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14138449133 --bind date:l:1763759148830 --bind duration:i:832 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16877412424 --bind date:l:1745752906902 --bind duration:i:3278 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14707722593 --bind date:l:1760823172104 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14676377225 --bind date:l:1769698333368 --bind duration:i:808 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15013603253 --bind date:l:1747141605461 --bind duration:i:455 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13234001815 --bind date:l:1749903933414 --bind duration:i:422 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14839411427 --bind date:l:1765482875895 --bind duration:i:1372 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12684975978 --bind date:l:1772304042711 --bind duration:i:38 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18117072012 --bind date:l:1754416717640 --bind duration:i:99 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13642607684 --bind date:l:1754554167319 --bind duration:i:81 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13964886993 --bind date:l:1770735074421 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14414275147 --bind date:l:1774175837131 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15006056767 --bind date:l:1770100216283 --bind duration:i:186 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17105252646 --bind date:l:1750102022701 --bind duration:i:368 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17575557899 --bind date:l:1757321998572 --bind duration:i:55 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15194098329 --bind date:l:1765191923957 --bind duration:i:81 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15362202908 --bind date:l:1772391249841 --bind duration:i:82 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16136248428 --bind date:l:1748263578874 --bind duration:i:80 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17469804501 --bind date:l:1755599143784 --bind duration:i:8 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17164551168 --bind date:l:1774415847033 --bind duration:i:853 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13793378939 --bind date:l:1751125037578 --bind duration:i:64 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16996611958 --bind date:l:1752791029035 --bind duration:i:83 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18193178044 --bind date:l:1750130837054 --bind duration:i:492 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19497944877 --bind date:l:1771626251897 --bind duration:i:56 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15015546642 --bind date:l:1747613395813 --bind duration:i:55 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14987008108 --bind date:l:1758332710779 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15478705574 --bind date:l:1748931040652 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14478328508 --bind date:l:1758072358793 --bind duration:i:73 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14046834871 --bind date:l:1769229023028 --bind duration:i:140 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15126888246 --bind date:l:1763644672629 --bind duration:i:3179 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16894241178 --bind date:l:1764814994745 --bind duration:i:749 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13132518496 --bind date:l:1766354601747 --bind duration:i:22 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13414196319 --bind date:l:1765265485563 --bind duration:i:1139 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15308945501 --bind date:l:1757156067573 --bind duration:i:272 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13503679019 --bind date:l:1767424261085 --bind duration:i:45 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15228588284 --bind date:l:1755921190806 --bind duration:i:831 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14969293554 --bind date:l:1752575340397 --bind duration:i:522 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12507616801 --bind date:l:1744624738899 --bind duration:i:2313 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15158769881 --bind date:l:1758667450894 --bind duration:i:11 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17368142119 --bind date:l:1761308389426 --bind duration:i:862 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13657834761 --bind date:l:1762772889753 --bind duration:i:25 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16529829720 --bind date:l:1759706495156 --bind duration:i:15 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12305248550 --bind date:l:1770700608546 --bind duration:i:207 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16264832362 --bind date:l:1773161443683 --bind duration:i:745 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15825427227 --bind date:l:1766374563107 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17967899602 --bind date:l:1770803672388 --bind duration:i:338 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19369673311 --bind date:l:1757039524287 --bind duration:i:111 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16004015970 --bind date:l:1748747993870 --bind duration:i:37 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19569321829 --bind date:l:1763831396488 --bind duration:i:232 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15035465362 --bind date:l:1751461016913 --bind duration:i:2641 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13428139085 --bind date:l:1751082222191 --bind duration:i:96 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15005205557 --bind date:l:1751286008406 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15674148270 --bind date:l:1754169659782 --bind duration:i:75 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15798509344 --bind date:l:1751162408667 --bind duration:i:701 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19134197408 --bind date:l:1747707549486 --bind duration:i:43 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18153566481 --bind date:l:1758377513134 --bind duration:i:182 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15346305562 --bind date:l:1773995917062 --bind duration:i:385 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13186026549 --bind date:l:1753183443621 --bind duration:i:313 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19856411128 --bind date:l:1758003548129 --bind duration:i:672 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16687208518 --bind date:l:1767882753282 --bind duration:i:474 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12125013391 --bind date:l:1764556319600 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17738349045 --bind date:l:1773129042309 --bind duration:i:90 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17277888394 --bind date:l:1770825045880 --bind duration:i:2319 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16918646903 --bind date:l:1749294724150 --bind duration:i:2566 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12637547197 --bind date:l:1748064755188 --bind duration:i:92 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17562852560 --bind date:l:1774294205196 --bind duration:i:106 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19352773582 --bind date:l:1744049143278 --bind duration:i:593 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14543147536 --bind date:l:1768574769360 --bind duration:i:37 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18683803656 --bind date:l:1763910507320 --bind duration:i:30 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14223745137 --bind date:l:1753660533702 --bind duration:i:17 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19027475342 --bind date:l:1754353795803 --bind duration:i:1980 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15349235693 --bind date:l:1759206478625 --bind duration:i:104 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15745036269 --bind date:l:1771816017130 --bind duration:i:750 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12872408961 --bind date:l:1774006891986 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14324081635 --bind date:l:1750798612394 --bind duration:i:488 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14938465436 --bind date:l:1774146069173 --bind duration:i:742 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12165327062 --bind date:l:1749307684360 --bind duration:i:23 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+18452409477 --bind date:l:1768378623232 --bind duration:i:31 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16168694916 --bind date:l:1748018120313 --bind duration:i:256 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15727296579 --bind date:l:1774025778062 --bind duration:i:6 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14352093870 --bind date:l:1756174488169 --bind duration:i:71 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15283077570 --bind date:l:1747895510429 --bind duration:i:51 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19983381671 --bind date:l:1769173244591 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17065994348 --bind date:l:1758547055153 --bind duration:i:547 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16636957226 --bind date:l:1749714895889 --bind duration:i:88 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19225098253 --bind date:l:1771009673138 --bind duration:i:0 --bind type:i:3 --bind new:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13017475245 --bind date:l:1755946062711 --bind duration:i:349 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+12237841038 --bind date:l:1771033503135 --bind duration:i:1914 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19273242663 --bind date:l:1773234811966 --bind duration:i:72 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17154441946 --bind date:l:1769421118504 --bind duration:i:730 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+19133638180 --bind date:l:1764446780128 --bind duration:i:79 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13634521720 --bind date:l:1753085186472 --bind duration:i:37 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+13039858466 --bind date:l:1767397589063 --bind duration:i:87 --bind type:i:1 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+17707778543 --bind date:l:1774144394564 --bind duration:i:0 --bind type:i:3 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+14845086948 --bind date:l:1747446935722 --bind duration:i:82 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+15598678560 --bind date:l:1760961378661 --bind duration:i:20 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://call_log/calls --bind number:s:+16246447100 --bind date:l:1763225589419 --bind duration:i:21 --bind type:i:2 --bind new:i:0 2>/dev/null
COUNT=$((COUNT + 1))

echo "Done: $COUNT call records at $(date)" >> $LOG
echo "CALLS_DONE_$COUNT"
