#!/system/bin/sh
# Inject ~1700 SMS messages via content insert
LOG=/data/local/tmp/inject_sms.log
echo "Starting SMS injection at $(date)" > $LOG
COUNT=0
content insert --uri content://sms --bind address:s:+15675298503 --bind date:l:1752496554562 --bind date_sent:l:1752496554562 --bind type:i:2 --bind body:s:"Do not forget electric bill" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15675298503 --bind date:l:1761266264322 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15675298503 --bind date:l:1766059463110 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15675298503 --bind date:l:1763421790313 --bind date_sent:l:1763421790313 --bind type:i:2 --bind body:s:"Hey are you free tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15675298503 --bind date:l:1772555990375 --bind date_sent:l:1772555990375 --bind type:i:2 --bind body:s:"Movie starts at 7" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12468458925 --bind date:l:1762005231016 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Movie starts at 7" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12468458925 --bind date:l:1769384291445 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just landed will call soon" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12468458925 --bind date:l:1744124029041 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12468458925 --bind date:l:1765079571630 --bind date_sent:l:1765079571630 --bind type:i:2 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12468458925 --bind date:l:1756465496257 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"WiFi password sunshine2024" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16667816685 --bind date:l:1758888803172 --bind date_sent:l:1758888803172 --bind type:i:2 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16667816685 --bind date:l:1762799439372 --bind date_sent:l:1762799439372 --bind type:i:2 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16667816685 --bind date:l:1757716251250 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Let me know when you are ready" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14525172134 --bind date:l:1761458440366 --bind date_sent:l:1761458440366 --bind type:i:2 --bind body:s:"What time works for you" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14525172134 --bind date:l:1751777053329 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Great news got the job" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14525172134 --bind date:l:1746168740065 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you send me that address" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14525172134 --bind date:l:1772687044265 --bind date_sent:l:1772687044265 --bind type:i:2 --bind body:s:"Did you see the game" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14525172134 --bind date:l:1745811167480 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Sounds good see you then" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14413987665 --bind date:l:1743056438112 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Congrats on the promotion" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14413987665 --bind date:l:1747871094463 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Weather looks great this weekend" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14413987665 --bind date:l:1770086280636 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14413987665 --bind date:l:1749696079770 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15536194155 --bind date:l:1769584986670 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15536194155 --bind date:l:1758923239820 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"WiFi password sunshine2024" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15536194155 --bind date:l:1758127326277 --bind date_sent:l:1758127326277 --bind type:i:2 --bind body:s:"Running 10 mins late" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15536194155 --bind date:l:1749554500739 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just finished work heading home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17793746734 --bind date:l:1758011675733 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17793746734 --bind date:l:1759353758028 --bind date_sent:l:1759353758028 --bind type:i:2 --bind body:s:"Reminder dentist tomorrow 9am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17793746734 --bind date:l:1757442862671 --bind date_sent:l:1757442862671 --bind type:i:2 --bind body:s:"Sorry I missed your call" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17793746734 --bind date:l:1741515609633 --bind date_sent:l:1741515609633 --bind type:i:2 --bind body:s:"Do not forget electric bill" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12192262865 --bind date:l:1770654807167 --bind date_sent:l:1770654807167 --bind type:i:2 --bind body:s:"Sorry I missed your call" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12192262865 --bind date:l:1756054752569 --bind date_sent:l:1756054752569 --bind type:i:2 --bind body:s:"What time works for you" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12192262865 --bind date:l:1761548309472 --bind date_sent:l:1761548309472 --bind type:i:2 --bind body:s:"What time works for you" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12192262865 --bind date:l:1758992619525 --bind date_sent:l:1758992619525 --bind type:i:2 --bind body:s:"Let me know when you are ready" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12192262865 --bind date:l:1758686909038 --bind date_sent:l:1758686909038 --bind type:i:2 --bind body:s:"Can you send me that address" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13375189086 --bind date:l:1766840450677 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Reminder dentist tomorrow 9am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13375189086 --bind date:l:1753567472424 --bind date_sent:l:1753567472424 --bind type:i:2 --bind body:s:"Sounds good see you then" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13375189086 --bind date:l:1741573620657 --bind date_sent:l:1741573620657 --bind type:i:2 --bind body:s:"Movie starts at 7" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18627384547 --bind date:l:1771623744205 --bind date_sent:l:1771623744205 --bind type:i:2 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18627384547 --bind date:l:1765111571142 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18627384547 --bind date:l:1760976965433 --bind date_sent:l:1760976965433 --bind type:i:2 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19768314647 --bind date:l:1772758994698 --bind date_sent:l:1772758994698 --bind type:i:2 --bind body:s:"Let me know when you are ready" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19768314647 --bind date:l:1754648457698 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17376066533 --bind date:l:1762990246267 --bind date_sent:l:1762990246267 --bind type:i:2 --bind body:s:"Doctor appointment at 10am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17376066533 --bind date:l:1762203097812 --bind date_sent:l:1762203097812 --bind type:i:2 --bind body:s:"Great news got the job" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12706024645 --bind date:l:1767209582897 --bind date_sent:l:1767209582897 --bind type:i:2 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12706024645 --bind date:l:1744037772504 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you send me that address" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12706024645 --bind date:l:1773051469486 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Great news got the job" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19798884556 --bind date:l:1760972643612 --bind date_sent:l:1760972643612 --bind type:i:2 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19798884556 --bind date:l:1757138460373 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19798884556 --bind date:l:1763007173969 --bind date_sent:l:1763007173969 --bind type:i:2 --bind body:s:"Traffic is terrible" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19798884556 --bind date:l:1744915243409 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Sorry I missed your call" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12582769795 --bind date:l:1751620551926 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Traffic is terrible" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12582769795 --bind date:l:1753374455940 --bind date_sent:l:1753374455940 --bind type:i:2 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12582769795 --bind date:l:1757795603994 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12582769795 --bind date:l:1759942111795 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"The package arrived today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12515864153 --bind date:l:1747803932769 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12515864153 --bind date:l:1767649092738 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Do not forget electric bill" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12515864153 --bind date:l:1747259340551 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Sorry I missed your call" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12515864153 --bind date:l:1771588227789 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Weather looks great this weekend" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12515864153 --bind date:l:1749164476841 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Weather looks great this weekend" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12736216547 --bind date:l:1771019746597 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"I am at the store need anything" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12736216547 --bind date:l:1746230608264 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you send me that address" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15538142101 --bind date:l:1744087746522 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15538142101 --bind date:l:1756511424243 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16285411242 --bind date:l:1767192762422 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16285411242 --bind date:l:1747319065757 --bind date_sent:l:1747319065757 --bind type:i:2 --bind body:s:"Your mom called call her back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16285411242 --bind date:l:1754307160638 --bind date_sent:l:1754307160638 --bind type:i:2 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19912169014 --bind date:l:1749347165025 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19912169014 --bind date:l:1761682237796 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Running 10 mins late" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19912169014 --bind date:l:1745302011197 --bind date_sent:l:1745302011197 --bind type:i:2 --bind body:s:"What time works for you" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19912169014 --bind date:l:1763763854733 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18225369976 --bind date:l:1757063953812 --bind date_sent:l:1757063953812 --bind type:i:2 --bind body:s:"I am at the store need anything" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18225369976 --bind date:l:1753302687618 --bind date_sent:l:1753302687618 --bind type:i:2 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18225369976 --bind date:l:1766161497684 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13248491590 --bind date:l:1759804526500 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Congrats on the promotion" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13248491590 --bind date:l:1753773797332 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you send me that address" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13248491590 --bind date:l:1761327549604 --bind date_sent:l:1761327549604 --bind type:i:2 --bind body:s:"Let me know when you are ready" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13248491590 --bind date:l:1762269529884 --bind date_sent:l:1762269529884 --bind type:i:2 --bind body:s:"Got your message" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13248491590 --bind date:l:1772009388633 --bind date_sent:l:1772009388633 --bind type:i:2 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15836151121 --bind date:l:1767980230596 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Your mom called call her back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15836151121 --bind date:l:1771695476839 --bind date_sent:l:1771695476839 --bind type:i:2 --bind body:s:"Your mom called call her back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15836151121 --bind date:l:1748472341474 --bind date_sent:l:1748472341474 --bind type:i:2 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12306172651 --bind date:l:1762232805138 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12306172651 --bind date:l:1759059581387 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Traffic is terrible" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17457034720 --bind date:l:1755105125141 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Hey are you free tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17457034720 --bind date:l:1769539517660 --bind date_sent:l:1769539517660 --bind type:i:2 --bind body:s:"Traffic is terrible" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17457034720 --bind date:l:1768942020085 --bind date_sent:l:1768942020085 --bind type:i:2 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17457034720 --bind date:l:1744459479222 --bind date_sent:l:1744459479222 --bind type:i:2 --bind body:s:"I am at the store need anything" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12407445530 --bind date:l:1774154252654 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12407445530 --bind date:l:1746809113445 --bind date_sent:l:1746809113445 --bind type:i:2 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12934177534 --bind date:l:1761637514750 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12934177534 --bind date:l:1756609428594 --bind date_sent:l:1756609428594 --bind type:i:2 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17704081876 --bind date:l:1758611646075 --bind date_sent:l:1758611646075 --bind type:i:2 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17704081876 --bind date:l:1774614495437 --bind date_sent:l:1774614495437 --bind type:i:2 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17704081876 --bind date:l:1758662230121 --bind date_sent:l:1758662230121 --bind type:i:2 --bind body:s:"Sounds good see you then" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17414758251 --bind date:l:1741954895956 --bind date_sent:l:1741954895956 --bind type:i:2 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17414758251 --bind date:l:1751469076237 --bind date_sent:l:1751469076237 --bind type:i:2 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17414758251 --bind date:l:1770142039110 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"I am at the store need anything" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12417421441 --bind date:l:1765244707074 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12417421441 --bind date:l:1766055400994 --bind date_sent:l:1766055400994 --bind type:i:2 --bind body:s:"I am at the store need anything" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12417421441 --bind date:l:1748893663017 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Sorry I missed your call" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12417421441 --bind date:l:1755881856179 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Your mom called call her back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16846527974 --bind date:l:1759796470813 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Got your message" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16846527974 --bind date:l:1769411626479 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you watch the kids Saturday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16846527974 --bind date:l:1750478857040 --bind date_sent:l:1750478857040 --bind type:i:2 --bind body:s:"Let me know when you are ready" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16846527974 --bind date:l:1770632192616 --bind date_sent:l:1770632192616 --bind type:i:2 --bind body:s:"Sorry I missed your call" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12287922021 --bind date:l:1757130688173 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Running 10 mins late" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12287922021 --bind date:l:1747566162528 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Movie starts at 7" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12287922021 --bind date:l:1741370271078 --bind date_sent:l:1741370271078 --bind type:i:2 --bind body:s:"Sounds good see you then" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18557038047 --bind date:l:1767745717338 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Let me know when you are ready" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18557038047 --bind date:l:1755892747060 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Your mom called call her back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18557038047 --bind date:l:1768300177190 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Sounds good see you then" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13998737094 --bind date:l:1745651085173 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"The package arrived today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13998737094 --bind date:l:1753727290055 --bind date_sent:l:1753727290055 --bind type:i:2 --bind body:s:"Doctor appointment at 10am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13998737094 --bind date:l:1748261036189 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13998737094 --bind date:l:1763784656285 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you watch the kids Saturday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18623919874 --bind date:l:1766818903851 --bind date_sent:l:1766818903851 --bind type:i:2 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18623919874 --bind date:l:1754937862475 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Congrats on the promotion" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18623919874 --bind date:l:1751766443256 --bind date_sent:l:1751766443256 --bind type:i:2 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12569467557 --bind date:l:1749647490826 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Reminder dentist tomorrow 9am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12569467557 --bind date:l:1773417956713 --bind date_sent:l:1773417956713 --bind type:i:2 --bind body:s:"Do not forget electric bill" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12569467557 --bind date:l:1767704724422 --bind date_sent:l:1767704724422 --bind type:i:2 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17937962656 --bind date:l:1761084271343 --bind date_sent:l:1761084271343 --bind type:i:2 --bind body:s:"Weather looks great this weekend" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17937962656 --bind date:l:1743547971488 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19263274871 --bind date:l:1767001948984 --bind date_sent:l:1767001948984 --bind type:i:2 --bind body:s:"Let me know when you are ready" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19263274871 --bind date:l:1743847701240 --bind date_sent:l:1743847701240 --bind type:i:2 --bind body:s:"Got your message" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15089785519 --bind date:l:1762834954225 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Hey are you free tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15089785519 --bind date:l:1760379825221 --bind date_sent:l:1760379825221 --bind type:i:2 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15089785519 --bind date:l:1755866592413 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15089785519 --bind date:l:1752855933321 --bind date_sent:l:1752855933321 --bind type:i:2 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15089785519 --bind date:l:1750908755309 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How is your day going" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16206419947 --bind date:l:1754309324647 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Great news got the job" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16206419947 --bind date:l:1768307391803 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16206419947 --bind date:l:1746852862917 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just landed will call soon" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16206419947 --bind date:l:1742836407110 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18478863914 --bind date:l:1747115226041 --bind date_sent:l:1747115226041 --bind type:i:2 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18478863914 --bind date:l:1772123648333 --bind date_sent:l:1772123648333 --bind type:i:2 --bind body:s:"Your mom called call her back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16817755771 --bind date:l:1756217397292 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Sorry I missed your call" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16817755771 --bind date:l:1747836923116 --bind date_sent:l:1747836923116 --bind type:i:2 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16817755771 --bind date:l:1773889903809 --bind date_sent:l:1773889903809 --bind type:i:2 --bind body:s:"Can you send me that address" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16817755771 --bind date:l:1743070365442 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16817755771 --bind date:l:1765978516389 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17256702894 --bind date:l:1744190693659 --bind date_sent:l:1744190693659 --bind type:i:2 --bind body:s:"Can you send me that address" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17256702894 --bind date:l:1751279544994 --bind date_sent:l:1751279544994 --bind type:i:2 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17256702894 --bind date:l:1742597323454 --bind date_sent:l:1742597323454 --bind type:i:2 --bind body:s:"Your mom called call her back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17256702894 --bind date:l:1767212569396 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just finished work heading home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13987123735 --bind date:l:1741550702201 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13987123735 --bind date:l:1757284407949 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Great news got the job" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13987123735 --bind date:l:1744391934272 --bind date_sent:l:1744391934272 --bind type:i:2 --bind body:s:"Sorry I missed your call" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17819426834 --bind date:l:1770218670827 --bind date_sent:l:1770218670827 --bind type:i:2 --bind body:s:"Just finished work heading home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17819426834 --bind date:l:1754373095082 --bind date_sent:l:1754373095082 --bind type:i:2 --bind body:s:"Can you watch the kids Saturday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17819426834 --bind date:l:1752590176429 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How is your day going" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16518641561 --bind date:l:1755269383918 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16518641561 --bind date:l:1767506668567 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Great news got the job" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16518641561 --bind date:l:1742398682564 --bind date_sent:l:1742398682564 --bind type:i:2 --bind body:s:"Congrats on the promotion" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16518641561 --bind date:l:1773561571247 --bind date_sent:l:1773561571247 --bind type:i:2 --bind body:s:"The package arrived today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13895497537 --bind date:l:1752173145770 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13895497537 --bind date:l:1767148417365 --bind date_sent:l:1767148417365 --bind type:i:2 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15037327463 --bind date:l:1760741235250 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Let me know when you are ready" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15037327463 --bind date:l:1772899070453 --bind date_sent:l:1772899070453 --bind type:i:2 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15037327463 --bind date:l:1749444295160 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Congrats on the promotion" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13732584764 --bind date:l:1755866434303 --bind date_sent:l:1755866434303 --bind type:i:2 --bind body:s:"Traffic is terrible" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13732584764 --bind date:l:1771739192351 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Movie starts at 7" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13732584764 --bind date:l:1762937306345 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Sounds good see you then" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17427941830 --bind date:l:1756372341024 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17427941830 --bind date:l:1763787898830 --bind date_sent:l:1763787898830 --bind type:i:2 --bind body:s:"Just landed will call soon" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17427941830 --bind date:l:1751028369382 --bind date_sent:l:1751028369382 --bind type:i:2 --bind body:s:"Just finished work heading home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17427941830 --bind date:l:1756290882162 --bind date_sent:l:1756290882162 --bind type:i:2 --bind body:s:"Just finished work heading home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17427941830 --bind date:l:1746286327316 --bind date_sent:l:1746286327316 --bind type:i:2 --bind body:s:"Sounds good see you then" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16288599962 --bind date:l:1774205749332 --bind date_sent:l:1774205749332 --bind type:i:2 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16288599962 --bind date:l:1750034730783 --bind date_sent:l:1750034730783 --bind type:i:2 --bind body:s:"Running 10 mins late" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16288599962 --bind date:l:1748345380711 --bind date_sent:l:1748345380711 --bind type:i:2 --bind body:s:"Movie starts at 7" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16288599962 --bind date:l:1755304572231 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12638518229 --bind date:l:1749203221045 --bind date_sent:l:1749203221045 --bind type:i:2 --bind body:s:"Hey are you free tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12638518229 --bind date:l:1763730522914 --bind date_sent:l:1763730522914 --bind type:i:2 --bind body:s:"Did you see the game" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12638518229 --bind date:l:1751802715927 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Sounds good see you then" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12638518229 --bind date:l:1742357925093 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13035578042 --bind date:l:1744996005874 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13035578042 --bind date:l:1742360405490 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13035578042 --bind date:l:1769635210815 --bind date_sent:l:1769635210815 --bind type:i:2 --bind body:s:"Just landed will call soon" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13035578042 --bind date:l:1751909486969 --bind date_sent:l:1751909486969 --bind type:i:2 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13035578042 --bind date:l:1770307078910 --bind date_sent:l:1770307078910 --bind type:i:2 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15209788754 --bind date:l:1752601694072 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"I am at the store need anything" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15209788754 --bind date:l:1747480669331 --bind date_sent:l:1747480669331 --bind type:i:2 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15209788754 --bind date:l:1747907655108 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15544289296 --bind date:l:1759770061178 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15544289296 --bind date:l:1747084641117 --bind date_sent:l:1747084641117 --bind type:i:2 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16478496297 --bind date:l:1743209610005 --bind date_sent:l:1743209610005 --bind type:i:2 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16478496297 --bind date:l:1745378129480 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16478496297 --bind date:l:1764992386918 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16478496297 --bind date:l:1742001069469 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17617284066 --bind date:l:1758136915530 --bind date_sent:l:1758136915530 --bind type:i:2 --bind body:s:"Doctor appointment at 10am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17617284066 --bind date:l:1762080746262 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Doctor appointment at 10am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17617284066 --bind date:l:1763854515027 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Did you see the game" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17617284066 --bind date:l:1751367646792 --bind date_sent:l:1751367646792 --bind type:i:2 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17617284066 --bind date:l:1743268991950 --bind date_sent:l:1743268991950 --bind type:i:2 --bind body:s:"Do not forget electric bill" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12809882063 --bind date:l:1754871987741 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12809882063 --bind date:l:1772350454935 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12809882063 --bind date:l:1752394238706 --bind date_sent:l:1752394238706 --bind type:i:2 --bind body:s:"Just finished work heading home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12809882063 --bind date:l:1741977603593 --bind date_sent:l:1741977603593 --bind type:i:2 --bind body:s:"Sorry I missed your call" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14362966654 --bind date:l:1748117540169 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14362966654 --bind date:l:1755653553467 --bind date_sent:l:1755653553467 --bind type:i:2 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14362966654 --bind date:l:1762566400656 --bind date_sent:l:1762566400656 --bind type:i:2 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16874908715 --bind date:l:1743688569406 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16874908715 --bind date:l:1770612529291 --bind date_sent:l:1770612529291 --bind type:i:2 --bind body:s:"Can you watch the kids Saturday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16874908715 --bind date:l:1749078613678 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Did you see the game" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14384443329 --bind date:l:1761773454674 --bind date_sent:l:1761773454674 --bind type:i:2 --bind body:s:"Great news got the job" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14384443329 --bind date:l:1742753379692 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14384443329 --bind date:l:1773063099003 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12118101472 --bind date:l:1752780550280 --bind date_sent:l:1752780550280 --bind type:i:2 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12118101472 --bind date:l:1747105221339 --bind date_sent:l:1747105221339 --bind type:i:2 --bind body:s:"Just landed will call soon" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12118101472 --bind date:l:1753796123742 --bind date_sent:l:1753796123742 --bind type:i:2 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12118101472 --bind date:l:1763374253736 --bind date_sent:l:1763374253736 --bind type:i:2 --bind body:s:"Just finished work heading home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12393713908 --bind date:l:1752761987563 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Reminder dentist tomorrow 9am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12393713908 --bind date:l:1752279461408 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Congrats on the promotion" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12393713908 --bind date:l:1753863169196 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Did you see the game" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12393713908 --bind date:l:1762525279583 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14016443067 --bind date:l:1745825240863 --bind date_sent:l:1745825240863 --bind type:i:2 --bind body:s:"Do not forget electric bill" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14016443067 --bind date:l:1769251724276 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Reminder dentist tomorrow 9am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14016443067 --bind date:l:1770094745420 --bind date_sent:l:1770094745420 --bind type:i:2 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14016443067 --bind date:l:1767167201826 --bind date_sent:l:1767167201826 --bind type:i:2 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19902168984 --bind date:l:1747911588203 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Traffic is terrible" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19902168984 --bind date:l:1747285580037 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Hey are you free tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19902168984 --bind date:l:1754813774594 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19902168984 --bind date:l:1757698886667 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"WiFi password sunshine2024" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17044665679 --bind date:l:1754129286169 --bind date_sent:l:1754129286169 --bind type:i:2 --bind body:s:"WiFi password sunshine2024" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17044665679 --bind date:l:1773168237923 --bind date_sent:l:1773168237923 --bind type:i:2 --bind body:s:"Did you see the game" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17044665679 --bind date:l:1744472243551 --bind date_sent:l:1744472243551 --bind type:i:2 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17044665679 --bind date:l:1765885238236 --bind date_sent:l:1765885238236 --bind type:i:2 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15405725618 --bind date:l:1747850942868 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"WiFi password sunshine2024" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15405725618 --bind date:l:1760775368279 --bind date_sent:l:1760775368279 --bind type:i:2 --bind body:s:"Do not forget electric bill" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15405725618 --bind date:l:1748029334768 --bind date_sent:l:1748029334768 --bind type:i:2 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14282839576 --bind date:l:1748599511775 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14282839576 --bind date:l:1769791560814 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13227323559 --bind date:l:1758135885769 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13227323559 --bind date:l:1773975293587 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"I am at the store need anything" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13227323559 --bind date:l:1756969124330 --bind date_sent:l:1756969124330 --bind type:i:2 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13227323559 --bind date:l:1770933932119 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"The package arrived today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13227323559 --bind date:l:1742899460840 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Got your message" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19962196941 --bind date:l:1741966231780 --bind date_sent:l:1741966231780 --bind type:i:2 --bind body:s:"Can you watch the kids Saturday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19962196941 --bind date:l:1770263185719 --bind date_sent:l:1770263185719 --bind type:i:2 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19962196941 --bind date:l:1760482996841 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Your mom called call her back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12604955232 --bind date:l:1759679696257 --bind date_sent:l:1759679696257 --bind type:i:2 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12604955232 --bind date:l:1770249757030 --bind date_sent:l:1770249757030 --bind type:i:2 --bind body:s:"Traffic is terrible" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12604955232 --bind date:l:1762221477774 --bind date_sent:l:1762221477774 --bind type:i:2 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12604955232 --bind date:l:1765559050556 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Running 10 mins late" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12604955232 --bind date:l:1769417325285 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Movie starts at 7" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13533211086 --bind date:l:1741743356528 --bind date_sent:l:1741743356528 --bind type:i:2 --bind body:s:"Reminder dentist tomorrow 9am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13533211086 --bind date:l:1763690279052 --bind date_sent:l:1763690279052 --bind type:i:2 --bind body:s:"Just finished work heading home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13533211086 --bind date:l:1759311210190 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13533211086 --bind date:l:1751315323680 --bind date_sent:l:1751315323680 --bind type:i:2 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15912715066 --bind date:l:1767251055678 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15912715066 --bind date:l:1770895417816 --bind date_sent:l:1770895417816 --bind type:i:2 --bind body:s:"Can you send me that address" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15912715066 --bind date:l:1754583418625 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15912715066 --bind date:l:1745192689333 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"What time works for you" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17879921713 --bind date:l:1747094116690 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"WiFi password sunshine2024" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17879921713 --bind date:l:1765834408987 --bind date_sent:l:1765834408987 --bind type:i:2 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17879921713 --bind date:l:1755390703119 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Congrats on the promotion" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17879921713 --bind date:l:1761292176954 --bind date_sent:l:1761292176954 --bind type:i:2 --bind body:s:"Can you watch the kids Saturday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17879921713 --bind date:l:1770020358756 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Do not forget electric bill" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15227845593 --bind date:l:1753588199523 --bind date_sent:l:1753588199523 --bind type:i:2 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15227845593 --bind date:l:1766399721284 --bind date_sent:l:1766399721284 --bind type:i:2 --bind body:s:"Can you watch the kids Saturday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15227845593 --bind date:l:1772305604389 --bind date_sent:l:1772305604389 --bind type:i:2 --bind body:s:"Can you send me that address" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14868148604 --bind date:l:1754907254368 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14868148604 --bind date:l:1764257841787 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Weather looks great this weekend" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14868148604 --bind date:l:1751891011361 --bind date_sent:l:1751891011361 --bind type:i:2 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14868148604 --bind date:l:1742469033695 --bind date_sent:l:1742469033695 --bind type:i:2 --bind body:s:"Just finished work heading home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19719346572 --bind date:l:1746766482375 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19719346572 --bind date:l:1742476869467 --bind date_sent:l:1742476869467 --bind type:i:2 --bind body:s:"What time works for you" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14947286491 --bind date:l:1747218054057 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Weather looks great this weekend" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14947286491 --bind date:l:1763061212655 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Sounds good see you then" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14947286491 --bind date:l:1741727875532 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14947286491 --bind date:l:1754161726281 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Traffic is terrible" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14947286491 --bind date:l:1763295276885 --bind date_sent:l:1763295276885 --bind type:i:2 --bind body:s:"Did you see the game" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12797695078 --bind date:l:1749099987727 --bind date_sent:l:1749099987727 --bind type:i:2 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12797695078 --bind date:l:1766504477941 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12797695078 --bind date:l:1747802491474 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12797695078 --bind date:l:1752410383338 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Your mom called call her back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12797695078 --bind date:l:1773231486739 --bind date_sent:l:1773231486739 --bind type:i:2 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19466301946 --bind date:l:1753931960917 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19466301946 --bind date:l:1757818046362 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you send me that address" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19466301946 --bind date:l:1753228522044 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Got your message" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19466301946 --bind date:l:1754654052973 --bind date_sent:l:1754654052973 --bind type:i:2 --bind body:s:"Did you see the game" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17439636012 --bind date:l:1745886371749 --bind date_sent:l:1745886371749 --bind type:i:2 --bind body:s:"Sounds good see you then" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17439636012 --bind date:l:1769603893225 --bind date_sent:l:1769603893225 --bind type:i:2 --bind body:s:"Weather looks great this weekend" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17439636012 --bind date:l:1747866784822 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17439636012 --bind date:l:1747877357129 --bind date_sent:l:1747877357129 --bind type:i:2 --bind body:s:"Can you watch the kids Saturday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16683891267 --bind date:l:1758989448495 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Sorry I missed your call" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16683891267 --bind date:l:1747774953061 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Weather looks great this weekend" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16683891267 --bind date:l:1749178347022 --bind date_sent:l:1749178347022 --bind type:i:2 --bind body:s:"Traffic is terrible" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16683891267 --bind date:l:1749254477499 --bind date_sent:l:1749254477499 --bind type:i:2 --bind body:s:"Hey are you free tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16683891267 --bind date:l:1752432423849 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you send me that address" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14857423643 --bind date:l:1763158774925 --bind date_sent:l:1763158774925 --bind type:i:2 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14857423643 --bind date:l:1746242411425 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14857423643 --bind date:l:1754695505694 --bind date_sent:l:1754695505694 --bind type:i:2 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14857423643 --bind date:l:1750095585857 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14857423643 --bind date:l:1767983650954 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13772638850 --bind date:l:1761700917884 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13772638850 --bind date:l:1746713191829 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13772638850 --bind date:l:1747190531524 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Let me know when you are ready" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15986638924 --bind date:l:1774678847023 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Got your message" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15986638924 --bind date:l:1764780713915 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15986638924 --bind date:l:1741809740885 --bind date_sent:l:1741809740885 --bind type:i:2 --bind body:s:"Movie starts at 7" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15986638924 --bind date:l:1748578848900 --bind date_sent:l:1748578848900 --bind type:i:2 --bind body:s:"I am at the store need anything" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15986638924 --bind date:l:1762753855532 --bind date_sent:l:1762753855532 --bind type:i:2 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17824877860 --bind date:l:1763319178479 --bind date_sent:l:1763319178479 --bind type:i:2 --bind body:s:"What time works for you" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17824877860 --bind date:l:1754954010936 --bind date_sent:l:1754954010936 --bind type:i:2 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17824877860 --bind date:l:1765355257722 --bind date_sent:l:1765355257722 --bind type:i:2 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13282791312 --bind date:l:1742392998448 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13282791312 --bind date:l:1767258653909 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Sorry I missed your call" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13282791312 --bind date:l:1767726642103 --bind date_sent:l:1767726642103 --bind type:i:2 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18849665659 --bind date:l:1774229807607 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"What time works for you" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18849665659 --bind date:l:1763384585190 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18849665659 --bind date:l:1745096601916 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15395272148 --bind date:l:1772619746058 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15395272148 --bind date:l:1774271580755 --bind date_sent:l:1774271580755 --bind type:i:2 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15395272148 --bind date:l:1772743149790 --bind date_sent:l:1772743149790 --bind type:i:2 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12657683026 --bind date:l:1749926460139 --bind date_sent:l:1749926460139 --bind type:i:2 --bind body:s:"Do not forget electric bill" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12657683026 --bind date:l:1749930374799 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18795946008 --bind date:l:1750126370441 --bind date_sent:l:1750126370441 --bind type:i:2 --bind body:s:"Movie starts at 7" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18795946008 --bind date:l:1767092633249 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14516152344 --bind date:l:1763454254364 --bind date_sent:l:1763454254364 --bind type:i:2 --bind body:s:"Let me know when you are ready" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14516152344 --bind date:l:1750804520200 --bind date_sent:l:1750804520200 --bind type:i:2 --bind body:s:"Got your message" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14516152344 --bind date:l:1763476040143 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16659338602 --bind date:l:1754460480601 --bind date_sent:l:1754460480601 --bind type:i:2 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16659338602 --bind date:l:1769179597002 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16659338602 --bind date:l:1751845829389 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12946837370 --bind date:l:1768287507829 --bind date_sent:l:1768287507829 --bind type:i:2 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12946837370 --bind date:l:1774350870935 --bind date_sent:l:1774350870935 --bind type:i:2 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12946837370 --bind date:l:1763004777826 --bind date_sent:l:1763004777826 --bind type:i:2 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12946837370 --bind date:l:1752898605406 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How is your day going" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16565095675 --bind date:l:1770841705091 --bind date_sent:l:1770841705091 --bind type:i:2 --bind body:s:"WiFi password sunshine2024" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16565095675 --bind date:l:1747860919226 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16565095675 --bind date:l:1764831418429 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16565095675 --bind date:l:1772517007689 --bind date_sent:l:1772517007689 --bind type:i:2 --bind body:s:"How is your day going" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13463638800 --bind date:l:1766530408330 --bind date_sent:l:1766530408330 --bind type:i:2 --bind body:s:"Congrats on the promotion" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13463638800 --bind date:l:1769151872597 --bind date_sent:l:1769151872597 --bind type:i:2 --bind body:s:"Movie starts at 7" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13463638800 --bind date:l:1744666446458 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"WiFi password sunshine2024" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13463638800 --bind date:l:1773415852820 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13463638800 --bind date:l:1768521440624 --bind date_sent:l:1768521440624 --bind type:i:2 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19706326059 --bind date:l:1745866106372 --bind date_sent:l:1745866106372 --bind type:i:2 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19706326059 --bind date:l:1751351906009 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Running 10 mins late" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19706326059 --bind date:l:1763032495572 --bind date_sent:l:1763032495572 --bind type:i:2 --bind body:s:"Doctor appointment at 10am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19706326059 --bind date:l:1770571759388 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Your mom called call her back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19947677877 --bind date:l:1772299690714 --bind date_sent:l:1772299690714 --bind type:i:2 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19947677877 --bind date:l:1765135861674 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15583872514 --bind date:l:1756212903083 --bind date_sent:l:1756212903083 --bind type:i:2 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15583872514 --bind date:l:1767846059342 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19246567945 --bind date:l:1766863712457 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19246567945 --bind date:l:1753221781120 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14104658550 --bind date:l:1756509946280 --bind date_sent:l:1756509946280 --bind type:i:2 --bind body:s:"Reminder dentist tomorrow 9am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14104658550 --bind date:l:1749199066836 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14104658550 --bind date:l:1750693023255 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Great news got the job" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14104658550 --bind date:l:1745620839122 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Weather looks great this weekend" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14104658550 --bind date:l:1769999900291 --bind date_sent:l:1769999900291 --bind type:i:2 --bind body:s:"Sounds good see you then" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19307722940 --bind date:l:1766712288518 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19307722940 --bind date:l:1759983999326 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19307722940 --bind date:l:1772243826750 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just finished work heading home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19307722940 --bind date:l:1745614647066 --bind date_sent:l:1745614647066 --bind type:i:2 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19845314427 --bind date:l:1764872566882 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Weather looks great this weekend" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19845314427 --bind date:l:1744237898538 --bind date_sent:l:1744237898538 --bind type:i:2 --bind body:s:"The package arrived today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18899744690 --bind date:l:1763514416643 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18899744690 --bind date:l:1750395433284 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Hey are you free tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18899744690 --bind date:l:1745693902372 --bind date_sent:l:1745693902372 --bind type:i:2 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15119526104 --bind date:l:1759915339912 --bind date_sent:l:1759915339912 --bind type:i:2 --bind body:s:"Movie starts at 7" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15119526104 --bind date:l:1744721649507 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you send me that address" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15119526104 --bind date:l:1753751244294 --bind date_sent:l:1753751244294 --bind type:i:2 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15127264550 --bind date:l:1772936658083 --bind date_sent:l:1772936658083 --bind type:i:2 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15127264550 --bind date:l:1761949550575 --bind date_sent:l:1761949550575 --bind type:i:2 --bind body:s:"Got your message" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15307984476 --bind date:l:1757370328256 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Hey are you free tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15307984476 --bind date:l:1750469421444 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15307984476 --bind date:l:1750176544064 --bind date_sent:l:1750176544064 --bind type:i:2 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15307984476 --bind date:l:1746204172554 --bind date_sent:l:1746204172554 --bind type:i:2 --bind body:s:"Can you send me that address" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15307984476 --bind date:l:1772574900534 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Reminder dentist tomorrow 9am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13182248689 --bind date:l:1764566574211 --bind date_sent:l:1764566574211 --bind type:i:2 --bind body:s:"Just landed will call soon" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13182248689 --bind date:l:1744020841702 --bind date_sent:l:1744020841702 --bind type:i:2 --bind body:s:"Let me know when you are ready" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19307707600 --bind date:l:1743778219469 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19307707600 --bind date:l:1763304576961 --bind date_sent:l:1763304576961 --bind type:i:2 --bind body:s:"Running 10 mins late" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19307707600 --bind date:l:1774517677836 --bind date_sent:l:1774517677836 --bind type:i:2 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19307707600 --bind date:l:1759009606400 --bind date_sent:l:1759009606400 --bind type:i:2 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19307707600 --bind date:l:1760200763218 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you watch the kids Saturday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18708566760 --bind date:l:1754725563307 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"I am at the store need anything" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18708566760 --bind date:l:1759922817116 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just landed will call soon" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12766653341 --bind date:l:1769952376694 --bind date_sent:l:1769952376694 --bind type:i:2 --bind body:s:"WiFi password sunshine2024" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12766653341 --bind date:l:1762376182245 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15349143511 --bind date:l:1747501173038 --bind date_sent:l:1747501173038 --bind type:i:2 --bind body:s:"Can you send me that address" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15349143511 --bind date:l:1764964245194 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15349143511 --bind date:l:1760002632263 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15349143511 --bind date:l:1750299804188 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Weather looks great this weekend" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12376716100 --bind date:l:1748555708860 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you watch the kids Saturday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12376716100 --bind date:l:1772987887779 --bind date_sent:l:1772987887779 --bind type:i:2 --bind body:s:"Got your message" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12376716100 --bind date:l:1754481215258 --bind date_sent:l:1754481215258 --bind type:i:2 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12376716100 --bind date:l:1757964865699 --bind date_sent:l:1757964865699 --bind type:i:2 --bind body:s:"Reminder dentist tomorrow 9am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19285645934 --bind date:l:1752498896920 --bind date_sent:l:1752498896920 --bind type:i:2 --bind body:s:"How is your day going" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19285645934 --bind date:l:1759362976494 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"What time works for you" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19285645934 --bind date:l:1770666830517 --bind date_sent:l:1770666830517 --bind type:i:2 --bind body:s:"Can you watch the kids Saturday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19285645934 --bind date:l:1771481893033 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19285645934 --bind date:l:1765761098354 --bind date_sent:l:1765761098354 --bind type:i:2 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15024045529 --bind date:l:1769283669457 --bind date_sent:l:1769283669457 --bind type:i:2 --bind body:s:"Got your message" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15024045529 --bind date:l:1748515245761 --bind date_sent:l:1748515245761 --bind type:i:2 --bind body:s:"The package arrived today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19732215559 --bind date:l:1741397405551 --bind date_sent:l:1741397405551 --bind type:i:2 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19732215559 --bind date:l:1755835552871 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Weather looks great this weekend" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19732215559 --bind date:l:1774106591721 --bind date_sent:l:1774106591721 --bind type:i:2 --bind body:s:"Movie starts at 7" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18958651360 --bind date:l:1749732225480 --bind date_sent:l:1749732225480 --bind type:i:2 --bind body:s:"Running 10 mins late" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18958651360 --bind date:l:1755151098505 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you send me that address" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15124045186 --bind date:l:1756316513133 --bind date_sent:l:1756316513133 --bind type:i:2 --bind body:s:"Got your message" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15124045186 --bind date:l:1746611983016 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"The package arrived today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15124045186 --bind date:l:1756426693975 --bind date_sent:l:1756426693975 --bind type:i:2 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19148455483 --bind date:l:1767823756128 --bind date_sent:l:1767823756128 --bind type:i:2 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19148455483 --bind date:l:1754205901118 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19148455483 --bind date:l:1748277860217 --bind date_sent:l:1748277860217 --bind type:i:2 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19148455483 --bind date:l:1767543334502 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Traffic is terrible" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19259892990 --bind date:l:1754010149654 --bind date_sent:l:1754010149654 --bind type:i:2 --bind body:s:"Do not forget electric bill" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19259892990 --bind date:l:1774211069749 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19259892990 --bind date:l:1761335522180 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17084514157 --bind date:l:1759824655016 --bind date_sent:l:1759824655016 --bind type:i:2 --bind body:s:"What time works for you" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17084514157 --bind date:l:1772513043563 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"What time works for you" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17084514157 --bind date:l:1741412174147 --bind date_sent:l:1741412174147 --bind type:i:2 --bind body:s:"I am at the store need anything" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17084514157 --bind date:l:1759433339825 --bind date_sent:l:1759433339825 --bind type:i:2 --bind body:s:"Sounds good see you then" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18149999252 --bind date:l:1750525912338 --bind date_sent:l:1750525912338 --bind type:i:2 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18149999252 --bind date:l:1759815487745 --bind date_sent:l:1759815487745 --bind type:i:2 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18755477341 --bind date:l:1747453271848 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18755477341 --bind date:l:1754432682748 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Great news got the job" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18755477341 --bind date:l:1771170084182 --bind date_sent:l:1771170084182 --bind type:i:2 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18755477341 --bind date:l:1771974686784 --bind date_sent:l:1771974686784 --bind type:i:2 --bind body:s:"The package arrived today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18755477341 --bind date:l:1763614010088 --bind date_sent:l:1763614010088 --bind type:i:2 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17497745639 --bind date:l:1763231200646 --bind date_sent:l:1763231200646 --bind type:i:2 --bind body:s:"How is your day going" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17497745639 --bind date:l:1752677381171 --bind date_sent:l:1752677381171 --bind type:i:2 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17497745639 --bind date:l:1768369407082 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Running 10 mins late" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17497745639 --bind date:l:1767734029689 --bind date_sent:l:1767734029689 --bind type:i:2 --bind body:s:"Reminder dentist tomorrow 9am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17497745639 --bind date:l:1750762804119 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"The package arrived today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15012431538 --bind date:l:1749516280078 --bind date_sent:l:1749516280078 --bind type:i:2 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15012431538 --bind date:l:1766491509979 --bind date_sent:l:1766491509979 --bind type:i:2 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15012431538 --bind date:l:1742889147544 --bind date_sent:l:1742889147544 --bind type:i:2 --bind body:s:"Got your message" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15012431538 --bind date:l:1770784370320 --bind date_sent:l:1770784370320 --bind type:i:2 --bind body:s:"Got your message" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15012431538 --bind date:l:1746257961959 --bind date_sent:l:1746257961959 --bind type:i:2 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12714662133 --bind date:l:1768869541730 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Your mom called call her back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12714662133 --bind date:l:1768454682707 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12714662133 --bind date:l:1772246360426 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12714662133 --bind date:l:1750384147848 --bind date_sent:l:1750384147848 --bind type:i:2 --bind body:s:"What time works for you" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12072827175 --bind date:l:1759982267921 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Reminder dentist tomorrow 9am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12072827175 --bind date:l:1769586324237 --bind date_sent:l:1769586324237 --bind type:i:2 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12072827175 --bind date:l:1747148990712 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12072827175 --bind date:l:1765084942597 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Running 10 mins late" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12072827175 --bind date:l:1770759676081 --bind date_sent:l:1770759676081 --bind type:i:2 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19842633974 --bind date:l:1755872043990 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"What time works for you" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19842633974 --bind date:l:1767772945926 --bind date_sent:l:1767772945926 --bind type:i:2 --bind body:s:"Congrats on the promotion" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19842633974 --bind date:l:1748088399715 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Do not forget electric bill" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19842633974 --bind date:l:1769032882662 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17593421044 --bind date:l:1765508662265 --bind date_sent:l:1765508662265 --bind type:i:2 --bind body:s:"Do not forget electric bill" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17593421044 --bind date:l:1763069700637 --bind date_sent:l:1763069700637 --bind type:i:2 --bind body:s:"Do not forget electric bill" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14484208405 --bind date:l:1755740113347 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Did you see the game" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14484208405 --bind date:l:1741725207157 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14484208405 --bind date:l:1767328086116 --bind date_sent:l:1767328086116 --bind type:i:2 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14484208405 --bind date:l:1758050265966 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Doctor appointment at 10am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15096247528 --bind date:l:1754109588393 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15096247528 --bind date:l:1758077738963 --bind date_sent:l:1758077738963 --bind type:i:2 --bind body:s:"Your mom called call her back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16803022946 --bind date:l:1766913087041 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16803022946 --bind date:l:1757789226262 --bind date_sent:l:1757789226262 --bind type:i:2 --bind body:s:"WiFi password sunshine2024" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16803022946 --bind date:l:1765064034989 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15828107449 --bind date:l:1766735513781 --bind date_sent:l:1766735513781 --bind type:i:2 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15828107449 --bind date:l:1764218376132 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15828107449 --bind date:l:1773699604142 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16895096727 --bind date:l:1761037929777 --bind date_sent:l:1761037929777 --bind type:i:2 --bind body:s:"Congrats on the promotion" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16895096727 --bind date:l:1771471616360 --bind date_sent:l:1771471616360 --bind type:i:2 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12656945647 --bind date:l:1758052959030 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How is your day going" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12656945647 --bind date:l:1768883490846 --bind date_sent:l:1768883490846 --bind type:i:2 --bind body:s:"Movie starts at 7" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12656945647 --bind date:l:1748757830119 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Hey are you free tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15363613191 --bind date:l:1750455878648 --bind date_sent:l:1750455878648 --bind type:i:2 --bind body:s:"Can you send me that address" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15363613191 --bind date:l:1766997682757 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15363613191 --bind date:l:1774027046038 --bind date_sent:l:1774027046038 --bind type:i:2 --bind body:s:"WiFi password sunshine2024" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15363613191 --bind date:l:1744753939745 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Movie starts at 7" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14434344643 --bind date:l:1757291924863 --bind date_sent:l:1757291924863 --bind type:i:2 --bind body:s:"Got your message" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14434344643 --bind date:l:1770429248193 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"The package arrived today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19657112828 --bind date:l:1745488701442 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Weather looks great this weekend" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19657112828 --bind date:l:1749999088754 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19657112828 --bind date:l:1761039050756 --bind date_sent:l:1761039050756 --bind type:i:2 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19657112828 --bind date:l:1760467871389 --bind date_sent:l:1760467871389 --bind type:i:2 --bind body:s:"Running 10 mins late" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19657112828 --bind date:l:1754166235061 --bind date_sent:l:1754166235061 --bind type:i:2 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18035775722 --bind date:l:1759919263420 --bind date_sent:l:1759919263420 --bind type:i:2 --bind body:s:"Sounds good see you then" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18035775722 --bind date:l:1768449497191 --bind date_sent:l:1768449497191 --bind type:i:2 --bind body:s:"Weather looks great this weekend" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18035775722 --bind date:l:1765823709196 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18035775722 --bind date:l:1749684407299 --bind date_sent:l:1749684407299 --bind type:i:2 --bind body:s:"Running 10 mins late" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19369878862 --bind date:l:1770426244766 --bind date_sent:l:1770426244766 --bind type:i:2 --bind body:s:"Doctor appointment at 10am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19369878862 --bind date:l:1759397668903 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just finished work heading home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19369878862 --bind date:l:1757366573282 --bind date_sent:l:1757366573282 --bind type:i:2 --bind body:s:"Just finished work heading home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19062344638 --bind date:l:1766827304371 --bind date_sent:l:1766827304371 --bind type:i:2 --bind body:s:"Great news got the job" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19062344638 --bind date:l:1747004485908 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19062344638 --bind date:l:1754591501843 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"What time works for you" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19062344638 --bind date:l:1767600405574 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Your mom called call her back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15997476573 --bind date:l:1753405608144 --bind date_sent:l:1753405608144 --bind type:i:2 --bind body:s:"Doctor appointment at 10am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15997476573 --bind date:l:1759152198754 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18776616286 --bind date:l:1741882785554 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18776616286 --bind date:l:1761219557923 --bind date_sent:l:1761219557923 --bind type:i:2 --bind body:s:"Weather looks great this weekend" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14676608563 --bind date:l:1761045870600 --bind date_sent:l:1761045870600 --bind type:i:2 --bind body:s:"Traffic is terrible" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14676608563 --bind date:l:1743563264083 --bind date_sent:l:1743563264083 --bind type:i:2 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14676608563 --bind date:l:1759860057467 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How is your day going" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18065297254 --bind date:l:1745793233109 --bind date_sent:l:1745793233109 --bind type:i:2 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18065297254 --bind date:l:1767481004069 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18065297254 --bind date:l:1760632455964 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15456788218 --bind date:l:1756640266143 --bind date_sent:l:1756640266143 --bind type:i:2 --bind body:s:"Running 10 mins late" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15456788218 --bind date:l:1751350563994 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"The package arrived today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15456788218 --bind date:l:1749614922554 --bind date_sent:l:1749614922554 --bind type:i:2 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14853266525 --bind date:l:1751063028501 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Let me know when you are ready" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14853266525 --bind date:l:1763188593219 --bind date_sent:l:1763188593219 --bind type:i:2 --bind body:s:"Great news got the job" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14853266525 --bind date:l:1770328895642 --bind date_sent:l:1770328895642 --bind type:i:2 --bind body:s:"Weather looks great this weekend" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14853266525 --bind date:l:1755488475909 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Sounds good see you then" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14853266525 --bind date:l:1749248207955 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16597963019 --bind date:l:1765945024132 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16597963019 --bind date:l:1763348488626 --bind date_sent:l:1763348488626 --bind type:i:2 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16597963019 --bind date:l:1769702254475 --bind date_sent:l:1769702254475 --bind type:i:2 --bind body:s:"Do not forget electric bill" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16597963019 --bind date:l:1763561259478 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Did you see the game" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18979113148 --bind date:l:1741452545170 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"What time works for you" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18979113148 --bind date:l:1763898028463 --bind date_sent:l:1763898028463 --bind type:i:2 --bind body:s:"Sounds good see you then" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16277712329 --bind date:l:1762999664425 --bind date_sent:l:1762999664425 --bind type:i:2 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16277712329 --bind date:l:1759563639627 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Running 10 mins late" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16277712329 --bind date:l:1763446029853 --bind date_sent:l:1763446029853 --bind type:i:2 --bind body:s:"Running 10 mins late" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15985521824 --bind date:l:1766428466955 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15985521824 --bind date:l:1759660063650 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15985521824 --bind date:l:1745545743437 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15985521824 --bind date:l:1760433829645 --bind date_sent:l:1760433829645 --bind type:i:2 --bind body:s:"Can you send me that address" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19194558593 --bind date:l:1751422774315 --bind date_sent:l:1751422774315 --bind type:i:2 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19194558593 --bind date:l:1773410144531 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19194558593 --bind date:l:1760465236298 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How is your day going" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15933322973 --bind date:l:1746163267642 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Movie starts at 7" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15933322973 --bind date:l:1760864595334 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15933322973 --bind date:l:1762403201582 --bind date_sent:l:1762403201582 --bind type:i:2 --bind body:s:"Did you see the game" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15933322973 --bind date:l:1751531244523 --bind date_sent:l:1751531244523 --bind type:i:2 --bind body:s:"How is your day going" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15868263500 --bind date:l:1757552588401 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15868263500 --bind date:l:1762855018382 --bind date_sent:l:1762855018382 --bind type:i:2 --bind body:s:"Sounds good see you then" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18443491908 --bind date:l:1769245989160 --bind date_sent:l:1769245989160 --bind type:i:2 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18443491908 --bind date:l:1762834647975 --bind date_sent:l:1762834647975 --bind type:i:2 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13798604223 --bind date:l:1770430368853 --bind date_sent:l:1770430368853 --bind type:i:2 --bind body:s:"Traffic is terrible" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13798604223 --bind date:l:1752801588835 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16315786356 --bind date:l:1757774422758 --bind date_sent:l:1757774422758 --bind type:i:2 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16315786356 --bind date:l:1758801604350 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"WiFi password sunshine2024" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16315786356 --bind date:l:1768160343651 --bind date_sent:l:1768160343651 --bind type:i:2 --bind body:s:"Did you see the game" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15374463244 --bind date:l:1770267279670 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you send me that address" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15374463244 --bind date:l:1763108463976 --bind date_sent:l:1763108463976 --bind type:i:2 --bind body:s:"Did you see the game" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15374463244 --bind date:l:1747529297103 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Great news got the job" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15374463244 --bind date:l:1756473490430 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Movie starts at 7" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14764617455 --bind date:l:1774541755299 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Got your message" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14764617455 --bind date:l:1751274529947 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Sorry I missed your call" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14764617455 --bind date:l:1759886893650 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Hey are you free tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13367912094 --bind date:l:1768299881315 --bind date_sent:l:1768299881315 --bind type:i:2 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13367912094 --bind date:l:1757768800391 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13367912094 --bind date:l:1772094380983 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Reminder dentist tomorrow 9am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13367912094 --bind date:l:1771800081678 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13367912094 --bind date:l:1746100535375 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Great news got the job" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16455065111 --bind date:l:1742440848715 --bind date_sent:l:1742440848715 --bind type:i:2 --bind body:s:"Running 10 mins late" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16455065111 --bind date:l:1762583372213 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How is your day going" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18122771505 --bind date:l:1743856383522 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Traffic is terrible" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18122771505 --bind date:l:1752071163077 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Weather looks great this weekend" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17033546430 --bind date:l:1763044300406 --bind date_sent:l:1763044300406 --bind type:i:2 --bind body:s:"How is your day going" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17033546430 --bind date:l:1748398853603 --bind date_sent:l:1748398853603 --bind type:i:2 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17033546430 --bind date:l:1743235503803 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Weather looks great this weekend" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17033546430 --bind date:l:1773415813437 --bind date_sent:l:1773415813437 --bind type:i:2 --bind body:s:"Can you watch the kids Saturday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18416603756 --bind date:l:1745356768482 --bind date_sent:l:1745356768482 --bind type:i:2 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18416603756 --bind date:l:1768906771100 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18416603756 --bind date:l:1748490961245 --bind date_sent:l:1748490961245 --bind type:i:2 --bind body:s:"The package arrived today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18416603756 --bind date:l:1758076448935 --bind date_sent:l:1758076448935 --bind type:i:2 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12887148352 --bind date:l:1760374381910 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12887148352 --bind date:l:1767677167540 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12887148352 --bind date:l:1760954077198 --bind date_sent:l:1760954077198 --bind type:i:2 --bind body:s:"How is your day going" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12887148352 --bind date:l:1750949484656 --bind date_sent:l:1750949484656 --bind type:i:2 --bind body:s:"Sounds good see you then" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12887148352 --bind date:l:1757164676713 --bind date_sent:l:1757164676713 --bind type:i:2 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18638438311 --bind date:l:1754395344656 --bind date_sent:l:1754395344656 --bind type:i:2 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18638438311 --bind date:l:1762986889156 --bind date_sent:l:1762986889156 --bind type:i:2 --bind body:s:"Doctor appointment at 10am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18638438311 --bind date:l:1772208198210 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18638438311 --bind date:l:1755062405673 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Sorry I missed your call" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15034997221 --bind date:l:1752998751240 --bind date_sent:l:1752998751240 --bind type:i:2 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15034997221 --bind date:l:1741573586571 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Sounds good see you then" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15034997221 --bind date:l:1760977118843 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Hey are you free tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15034997221 --bind date:l:1760782125462 --bind date_sent:l:1760782125462 --bind type:i:2 --bind body:s:"What time works for you" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19417563034 --bind date:l:1765138930218 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19417563034 --bind date:l:1741283620692 --bind date_sent:l:1741283620692 --bind type:i:2 --bind body:s:"Just finished work heading home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19417563034 --bind date:l:1756906965427 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Hey are you free tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19417563034 --bind date:l:1769069588607 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Got your message" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19417563034 --bind date:l:1746324974564 --bind date_sent:l:1746324974564 --bind type:i:2 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13844715677 --bind date:l:1749604815304 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Congrats on the promotion" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13844715677 --bind date:l:1767366952981 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13844715677 --bind date:l:1754223166510 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13844715677 --bind date:l:1750135972587 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How is your day going" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13844715677 --bind date:l:1749437378715 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18916143226 --bind date:l:1755040690986 --bind date_sent:l:1755040690986 --bind type:i:2 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18916143226 --bind date:l:1755641944368 --bind date_sent:l:1755641944368 --bind type:i:2 --bind body:s:"I am at the store need anything" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17559758112 --bind date:l:1741828059927 --bind date_sent:l:1741828059927 --bind type:i:2 --bind body:s:"Great news got the job" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17559758112 --bind date:l:1767264587330 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Movie starts at 7" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17559758112 --bind date:l:1766660732815 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19057262462 --bind date:l:1743198675767 --bind date_sent:l:1743198675767 --bind type:i:2 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19057262462 --bind date:l:1771415631267 --bind date_sent:l:1771415631267 --bind type:i:2 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13415578175 --bind date:l:1768862853466 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Weather looks great this weekend" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13415578175 --bind date:l:1763295041880 --bind date_sent:l:1763295041880 --bind type:i:2 --bind body:s:"Did you see the game" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18867558509 --bind date:l:1748683108290 --bind date_sent:l:1748683108290 --bind type:i:2 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18867558509 --bind date:l:1769100810428 --bind date_sent:l:1769100810428 --bind type:i:2 --bind body:s:"Great news got the job" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18867558509 --bind date:l:1772002667955 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18272144597 --bind date:l:1750487302938 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18272144597 --bind date:l:1759768984524 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Great news got the job" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12396809804 --bind date:l:1761411367750 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12396809804 --bind date:l:1751075019488 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Sorry I missed your call" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17586975767 --bind date:l:1759663811349 --bind date_sent:l:1759663811349 --bind type:i:2 --bind body:s:"Your mom called call her back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17586975767 --bind date:l:1774719688698 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Doctor appointment at 10am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17586975767 --bind date:l:1741848396272 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"What time works for you" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17605654707 --bind date:l:1767021832124 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Do not forget electric bill" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17605654707 --bind date:l:1747293440938 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17605654707 --bind date:l:1741901058045 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"I am at the store need anything" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17605654707 --bind date:l:1755874511350 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12746415878 --bind date:l:1767876782866 --bind date_sent:l:1767876782866 --bind type:i:2 --bind body:s:"Weather looks great this weekend" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12746415878 --bind date:l:1749681598961 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How is your day going" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12746415878 --bind date:l:1748059289949 --bind date_sent:l:1748059289949 --bind type:i:2 --bind body:s:"Sounds good see you then" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19376307646 --bind date:l:1757588371601 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Sorry I missed your call" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19376307646 --bind date:l:1755864628806 --bind date_sent:l:1755864628806 --bind type:i:2 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19376307646 --bind date:l:1755388991738 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19376307646 --bind date:l:1745417486041 --bind date_sent:l:1745417486041 --bind type:i:2 --bind body:s:"The package arrived today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19376307646 --bind date:l:1753440412081 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18804999425 --bind date:l:1769374674168 --bind date_sent:l:1769374674168 --bind type:i:2 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18804999425 --bind date:l:1752236293218 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Sounds good see you then" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15924757935 --bind date:l:1767304682729 --bind date_sent:l:1767304682729 --bind type:i:2 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15924757935 --bind date:l:1752720938766 --bind date_sent:l:1752720938766 --bind type:i:2 --bind body:s:"Doctor appointment at 10am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15924757935 --bind date:l:1746550447580 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just landed will call soon" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15924757935 --bind date:l:1756660971658 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"What time works for you" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15924757935 --bind date:l:1763327876047 --bind date_sent:l:1763327876047 --bind type:i:2 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13355061865 --bind date:l:1755784345989 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13355061865 --bind date:l:1745226250745 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Hey are you free tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13355061865 --bind date:l:1773859050559 --bind date_sent:l:1773859050559 --bind type:i:2 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15509312722 --bind date:l:1771184509087 --bind date_sent:l:1771184509087 --bind type:i:2 --bind body:s:"Hey are you free tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15509312722 --bind date:l:1762815541883 --bind date_sent:l:1762815541883 --bind type:i:2 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15509312722 --bind date:l:1764953124869 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15509312722 --bind date:l:1743407919214 --bind date_sent:l:1743407919214 --bind type:i:2 --bind body:s:"How is your day going" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14016071190 --bind date:l:1750425625719 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14016071190 --bind date:l:1760127496612 --bind date_sent:l:1760127496612 --bind type:i:2 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14016071190 --bind date:l:1759554146900 --bind date_sent:l:1759554146900 --bind type:i:2 --bind body:s:"Did you see the game" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12109182801 --bind date:l:1749247071203 --bind date_sent:l:1749247071203 --bind type:i:2 --bind body:s:"The package arrived today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12109182801 --bind date:l:1743162394476 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15443243886 --bind date:l:1766765585180 --bind date_sent:l:1766765585180 --bind type:i:2 --bind body:s:"Do not forget electric bill" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15443243886 --bind date:l:1771170763216 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Running 10 mins late" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19735212219 --bind date:l:1746387451490 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19735212219 --bind date:l:1741509735997 --bind date_sent:l:1741509735997 --bind type:i:2 --bind body:s:"Just landed will call soon" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19735212219 --bind date:l:1749904118028 --bind date_sent:l:1749904118028 --bind type:i:2 --bind body:s:"Can you watch the kids Saturday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19735212219 --bind date:l:1761477635559 --bind date_sent:l:1761477635559 --bind type:i:2 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17233888231 --bind date:l:1741332229560 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17233888231 --bind date:l:1753622390876 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you watch the kids Saturday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17233888231 --bind date:l:1766483436677 --bind date_sent:l:1766483436677 --bind type:i:2 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13299828805 --bind date:l:1772294504716 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13299828805 --bind date:l:1752837559169 --bind date_sent:l:1752837559169 --bind type:i:2 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13299828805 --bind date:l:1756809714746 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Did you see the game" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13299828805 --bind date:l:1753463074324 --bind date_sent:l:1753463074324 --bind type:i:2 --bind body:s:"Doctor appointment at 10am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12034305760 --bind date:l:1745863811449 --bind date_sent:l:1745863811449 --bind type:i:2 --bind body:s:"Got your message" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12034305760 --bind date:l:1742460344229 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"The package arrived today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12034305760 --bind date:l:1760150332162 --bind date_sent:l:1760150332162 --bind type:i:2 --bind body:s:"Movie starts at 7" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12034305760 --bind date:l:1743780401930 --bind date_sent:l:1743780401930 --bind type:i:2 --bind body:s:"Just finished work heading home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12034305760 --bind date:l:1756537866989 --bind date_sent:l:1756537866989 --bind type:i:2 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12922387829 --bind date:l:1760859492943 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"WiFi password sunshine2024" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12922387829 --bind date:l:1766885501772 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12922387829 --bind date:l:1749265387240 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Weather looks great this weekend" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15783968188 --bind date:l:1774252096629 --bind date_sent:l:1774252096629 --bind type:i:2 --bind body:s:"Do not forget electric bill" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15783968188 --bind date:l:1762081923277 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15783968188 --bind date:l:1762154788457 --bind date_sent:l:1762154788457 --bind type:i:2 --bind body:s:"Sorry I missed your call" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19055826323 --bind date:l:1765193326739 --bind date_sent:l:1765193326739 --bind type:i:2 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19055826323 --bind date:l:1769338261509 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Do not forget electric bill" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14682359819 --bind date:l:1765320672587 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14682359819 --bind date:l:1749639318160 --bind date_sent:l:1749639318160 --bind type:i:2 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17498261004 --bind date:l:1765624510066 --bind date_sent:l:1765624510066 --bind type:i:2 --bind body:s:"Got your message" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17498261004 --bind date:l:1759571588184 --bind date_sent:l:1759571588184 --bind type:i:2 --bind body:s:"Weather looks great this weekend" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17498261004 --bind date:l:1756673648394 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Great news got the job" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17498261004 --bind date:l:1755977443855 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18702709842 --bind date:l:1743779594395 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Congrats on the promotion" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18702709842 --bind date:l:1747862740006 --bind date_sent:l:1747862740006 --bind type:i:2 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18702709842 --bind date:l:1754739779537 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Great news got the job" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18702709842 --bind date:l:1748801892758 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18393777931 --bind date:l:1764701933849 --bind date_sent:l:1764701933849 --bind type:i:2 --bind body:s:"Can you send me that address" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18393777931 --bind date:l:1744528249569 --bind date_sent:l:1744528249569 --bind type:i:2 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18393777931 --bind date:l:1746055483850 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you send me that address" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18393777931 --bind date:l:1743135798373 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Hey are you free tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18393777931 --bind date:l:1757056200992 --bind date_sent:l:1757056200992 --bind type:i:2 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14818924155 --bind date:l:1771282992618 --bind date_sent:l:1771282992618 --bind type:i:2 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14818924155 --bind date:l:1766217365795 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Traffic is terrible" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19493453502 --bind date:l:1768888945187 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19493453502 --bind date:l:1774778400414 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you send me that address" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19493453502 --bind date:l:1765188687565 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"The package arrived today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19493453502 --bind date:l:1758939367878 --bind date_sent:l:1758939367878 --bind type:i:2 --bind body:s:"Do not forget electric bill" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19493453502 --bind date:l:1756877325980 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18302127247 --bind date:l:1759460691980 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"The package arrived today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18302127247 --bind date:l:1774004170089 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18302127247 --bind date:l:1762913238372 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18302127247 --bind date:l:1744280247093 --bind date_sent:l:1744280247093 --bind type:i:2 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18302127247 --bind date:l:1742281913471 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Congrats on the promotion" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13615583901 --bind date:l:1753878747885 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Congrats on the promotion" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13615583901 --bind date:l:1760307518072 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you watch the kids Saturday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13615583901 --bind date:l:1769206796767 --bind date_sent:l:1769206796767 --bind type:i:2 --bind body:s:"Running 10 mins late" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13615583901 --bind date:l:1756674380510 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Running 10 mins late" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19068195938 --bind date:l:1742497110103 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Do not forget electric bill" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19068195938 --bind date:l:1749638646593 --bind date_sent:l:1749638646593 --bind type:i:2 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14778724230 --bind date:l:1753450997832 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Movie starts at 7" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14778724230 --bind date:l:1748467597141 --bind date_sent:l:1748467597141 --bind type:i:2 --bind body:s:"Hey are you free tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14778724230 --bind date:l:1762814220670 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Do not forget electric bill" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14778724230 --bind date:l:1755237549069 --bind date_sent:l:1755237549069 --bind type:i:2 --bind body:s:"What time works for you" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15959962951 --bind date:l:1765411400864 --bind date_sent:l:1765411400864 --bind type:i:2 --bind body:s:"Can you watch the kids Saturday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15959962951 --bind date:l:1773838674395 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How is your day going" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15959962951 --bind date:l:1753880894220 --bind date_sent:l:1753880894220 --bind type:i:2 --bind body:s:"Hey are you free tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15959962951 --bind date:l:1770086880888 --bind date_sent:l:1770086880888 --bind type:i:2 --bind body:s:"WiFi password sunshine2024" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15959962951 --bind date:l:1760731466908 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just finished work heading home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17387849711 --bind date:l:1753330507483 --bind date_sent:l:1753330507483 --bind type:i:2 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17387849711 --bind date:l:1767013175166 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17387849711 --bind date:l:1760284626970 --bind date_sent:l:1760284626970 --bind type:i:2 --bind body:s:"Let me know when you are ready" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17387849711 --bind date:l:1771220200645 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Your mom called call her back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17387849711 --bind date:l:1747113862128 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Reminder dentist tomorrow 9am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15354914831 --bind date:l:1766879258857 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15354914831 --bind date:l:1747187597896 --bind date_sent:l:1747187597896 --bind type:i:2 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15354914831 --bind date:l:1774612674195 --bind date_sent:l:1774612674195 --bind type:i:2 --bind body:s:"Hey are you free tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15354914831 --bind date:l:1761999814610 --bind date_sent:l:1761999814610 --bind type:i:2 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15354914831 --bind date:l:1750413553982 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"WiFi password sunshine2024" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12396212554 --bind date:l:1746443035240 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Got your message" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12396212554 --bind date:l:1773395891280 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12396212554 --bind date:l:1767653615252 --bind date_sent:l:1767653615252 --bind type:i:2 --bind body:s:"Doctor appointment at 10am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12396212554 --bind date:l:1755901223797 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"What time works for you" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15982971590 --bind date:l:1762962651532 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15982971590 --bind date:l:1744829827698 --bind date_sent:l:1744829827698 --bind type:i:2 --bind body:s:"Just landed will call soon" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15982971590 --bind date:l:1771865858408 --bind date_sent:l:1771865858408 --bind type:i:2 --bind body:s:"Reminder dentist tomorrow 9am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19698243070 --bind date:l:1765957338707 --bind date_sent:l:1765957338707 --bind type:i:2 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19698243070 --bind date:l:1769281878821 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"WiFi password sunshine2024" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15767821839 --bind date:l:1757818172439 --bind date_sent:l:1757818172439 --bind type:i:2 --bind body:s:"Just finished work heading home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15767821839 --bind date:l:1771346321385 --bind date_sent:l:1771346321385 --bind type:i:2 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15767821839 --bind date:l:1773174715800 --bind date_sent:l:1773174715800 --bind type:i:2 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13577056950 --bind date:l:1748216331847 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Great news got the job" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13577056950 --bind date:l:1758773984702 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13577056950 --bind date:l:1771967678202 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you send me that address" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13577056950 --bind date:l:1747380701639 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Did you see the game" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15876059777 --bind date:l:1753790366841 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Congrats on the promotion" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15876059777 --bind date:l:1766972025204 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Weather looks great this weekend" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14932093718 --bind date:l:1763246223164 --bind date_sent:l:1763246223164 --bind type:i:2 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14932093718 --bind date:l:1759938592713 --bind date_sent:l:1759938592713 --bind type:i:2 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14932093718 --bind date:l:1758677112251 --bind date_sent:l:1758677112251 --bind type:i:2 --bind body:s:"Can you watch the kids Saturday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14932093718 --bind date:l:1757971627905 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19773651633 --bind date:l:1769354872179 --bind date_sent:l:1769354872179 --bind type:i:2 --bind body:s:"Your mom called call her back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19773651633 --bind date:l:1770987817057 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Sorry I missed your call" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18147705861 --bind date:l:1773119576290 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18147705861 --bind date:l:1770765782857 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18147705861 --bind date:l:1769382353173 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just finished work heading home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18147705861 --bind date:l:1768123159764 --bind date_sent:l:1768123159764 --bind type:i:2 --bind body:s:"Just landed will call soon" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17185673946 --bind date:l:1772301205584 --bind date_sent:l:1772301205584 --bind type:i:2 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17185673946 --bind date:l:1774386232748 --bind date_sent:l:1774386232748 --bind type:i:2 --bind body:s:"Can you watch the kids Saturday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17185673946 --bind date:l:1769636805147 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"WiFi password sunshine2024" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17185673946 --bind date:l:1752863248110 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How is your day going" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14592336405 --bind date:l:1761198207083 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Your mom called call her back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14592336405 --bind date:l:1761805199679 --bind date_sent:l:1761805199679 --bind type:i:2 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14592336405 --bind date:l:1756021976794 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14592336405 --bind date:l:1766937518960 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19958559527 --bind date:l:1762220766641 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19958559527 --bind date:l:1749264409062 --bind date_sent:l:1749264409062 --bind type:i:2 --bind body:s:"Hey are you free tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19958559527 --bind date:l:1743406937909 --bind date_sent:l:1743406937909 --bind type:i:2 --bind body:s:"Great news got the job" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18559649087 --bind date:l:1745151355950 --bind date_sent:l:1745151355950 --bind type:i:2 --bind body:s:"Movie starts at 7" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18559649087 --bind date:l:1746415093109 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17153266095 --bind date:l:1744146953090 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just landed will call soon" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17153266095 --bind date:l:1743573197762 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17153266095 --bind date:l:1761130928312 --bind date_sent:l:1761130928312 --bind type:i:2 --bind body:s:"Did you see the game" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17153266095 --bind date:l:1773711651035 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17153266095 --bind date:l:1756554793217 --bind date_sent:l:1756554793217 --bind type:i:2 --bind body:s:"I am at the store need anything" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19056789730 --bind date:l:1751502432614 --bind date_sent:l:1751502432614 --bind type:i:2 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19056789730 --bind date:l:1774434270636 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19056789730 --bind date:l:1771394745695 --bind date_sent:l:1771394745695 --bind type:i:2 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17157861874 --bind date:l:1754817655158 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17157861874 --bind date:l:1744999246169 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Got your message" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17157861874 --bind date:l:1766172766376 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Did you see the game" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17459835105 --bind date:l:1742284804807 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Reminder dentist tomorrow 9am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17459835105 --bind date:l:1745919490896 --bind date_sent:l:1745919490896 --bind type:i:2 --bind body:s:"Do not forget electric bill" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16387926125 --bind date:l:1758093110006 --bind date_sent:l:1758093110006 --bind type:i:2 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16387926125 --bind date:l:1742285020080 --bind date_sent:l:1742285020080 --bind type:i:2 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16387926125 --bind date:l:1760801045820 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16387926125 --bind date:l:1762175883760 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12362968328 --bind date:l:1743604780727 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12362968328 --bind date:l:1764499928300 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just finished work heading home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12894831631 --bind date:l:1765700959501 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12894831631 --bind date:l:1761258872470 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12894831631 --bind date:l:1747998207964 --bind date_sent:l:1747998207964 --bind type:i:2 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12894831631 --bind date:l:1757160321350 --bind date_sent:l:1757160321350 --bind type:i:2 --bind body:s:"Sounds good see you then" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14379937186 --bind date:l:1760661185496 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14379937186 --bind date:l:1750434832434 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Weather looks great this weekend" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14379937186 --bind date:l:1772380133855 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14379937186 --bind date:l:1764545328063 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Doctor appointment at 10am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14625183395 --bind date:l:1744735271531 --bind date_sent:l:1744735271531 --bind type:i:2 --bind body:s:"Movie starts at 7" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14625183395 --bind date:l:1752184050298 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14625183395 --bind date:l:1760881145354 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14625183395 --bind date:l:1753865911209 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14625183395 --bind date:l:1772499758769 --bind date_sent:l:1772499758769 --bind type:i:2 --bind body:s:"Let me know when you are ready" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16153395583 --bind date:l:1765370970370 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16153395583 --bind date:l:1759117492671 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17629087895 --bind date:l:1774777763283 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How is your day going" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17629087895 --bind date:l:1761917410789 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"The package arrived today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17629087895 --bind date:l:1766901814474 --bind date_sent:l:1766901814474 --bind type:i:2 --bind body:s:"Great news got the job" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13135612362 --bind date:l:1753097817590 --bind date_sent:l:1753097817590 --bind type:i:2 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13135612362 --bind date:l:1765205486500 --bind date_sent:l:1765205486500 --bind type:i:2 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14622778658 --bind date:l:1769268197210 --bind date_sent:l:1769268197210 --bind type:i:2 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14622778658 --bind date:l:1771452197572 --bind date_sent:l:1771452197572 --bind type:i:2 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14622778658 --bind date:l:1747086578687 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just finished work heading home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14622778658 --bind date:l:1764945476264 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How is your day going" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12028309207 --bind date:l:1774156759920 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Weather looks great this weekend" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12028309207 --bind date:l:1744030778030 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12028309207 --bind date:l:1762770717867 --bind date_sent:l:1762770717867 --bind type:i:2 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18407363076 --bind date:l:1755130719579 --bind date_sent:l:1755130719579 --bind type:i:2 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18407363076 --bind date:l:1742879984600 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Sorry I missed your call" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18407363076 --bind date:l:1753696790772 --bind date_sent:l:1753696790772 --bind type:i:2 --bind body:s:"The package arrived today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18407363076 --bind date:l:1763929341399 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18407363076 --bind date:l:1768890178723 --bind date_sent:l:1768890178723 --bind type:i:2 --bind body:s:"The package arrived today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18172458698 --bind date:l:1760263488610 --bind date_sent:l:1760263488610 --bind type:i:2 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18172458698 --bind date:l:1749512768467 --bind date_sent:l:1749512768467 --bind type:i:2 --bind body:s:"Hey are you free tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18172458698 --bind date:l:1743400544353 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Did you see the game" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18172458698 --bind date:l:1766968753167 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18172458698 --bind date:l:1741653006249 --bind date_sent:l:1741653006249 --bind type:i:2 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13953272709 --bind date:l:1753059933764 --bind date_sent:l:1753059933764 --bind type:i:2 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13953272709 --bind date:l:1743281721039 --bind date_sent:l:1743281721039 --bind type:i:2 --bind body:s:"Congrats on the promotion" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13953272709 --bind date:l:1772713102640 --bind date_sent:l:1772713102640 --bind type:i:2 --bind body:s:"How is your day going" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18462468551 --bind date:l:1750993106332 --bind date_sent:l:1750993106332 --bind type:i:2 --bind body:s:"Sounds good see you then" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18462468551 --bind date:l:1761246661710 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18462468551 --bind date:l:1751424971390 --bind date_sent:l:1751424971390 --bind type:i:2 --bind body:s:"Reminder dentist tomorrow 9am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18462468551 --bind date:l:1770885674872 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18462468551 --bind date:l:1771594457342 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Doctor appointment at 10am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14716718151 --bind date:l:1771253184710 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Doctor appointment at 10am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14716718151 --bind date:l:1774357178326 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14716718151 --bind date:l:1767250691619 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14716718151 --bind date:l:1767650799905 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14716718151 --bind date:l:1766100420410 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14504951883 --bind date:l:1764908456911 --bind date_sent:l:1764908456911 --bind type:i:2 --bind body:s:"Can you watch the kids Saturday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14504951883 --bind date:l:1763825125666 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15949194286 --bind date:l:1748334300007 --bind date_sent:l:1748334300007 --bind type:i:2 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15949194286 --bind date:l:1750060166376 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just landed will call soon" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15949194286 --bind date:l:1770192255455 --bind date_sent:l:1770192255455 --bind type:i:2 --bind body:s:"I am at the store need anything" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15949194286 --bind date:l:1747942864661 --bind date_sent:l:1747942864661 --bind type:i:2 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15467332025 --bind date:l:1769023097090 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Sounds good see you then" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15467332025 --bind date:l:1769245502451 --bind date_sent:l:1769245502451 --bind type:i:2 --bind body:s:"Weather looks great this weekend" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15467332025 --bind date:l:1761893719293 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Sounds good see you then" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15467332025 --bind date:l:1772495067756 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Your mom called call her back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15467332025 --bind date:l:1772325748877 --bind date_sent:l:1772325748877 --bind type:i:2 --bind body:s:"Great news got the job" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13633552207 --bind date:l:1751564782278 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13633552207 --bind date:l:1754020886624 --bind date_sent:l:1754020886624 --bind type:i:2 --bind body:s:"Reminder dentist tomorrow 9am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13633552207 --bind date:l:1770837017707 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13633552207 --bind date:l:1746345817896 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Sorry I missed your call" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13633552207 --bind date:l:1742005863797 --bind date_sent:l:1742005863797 --bind type:i:2 --bind body:s:"Doctor appointment at 10am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17234863218 --bind date:l:1749364393686 --bind date_sent:l:1749364393686 --bind type:i:2 --bind body:s:"What time works for you" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17234863218 --bind date:l:1756218239087 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"What time works for you" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17234863218 --bind date:l:1772614235262 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Let me know when you are ready" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18124606766 --bind date:l:1758904199360 --bind date_sent:l:1758904199360 --bind type:i:2 --bind body:s:"The package arrived today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18124606766 --bind date:l:1771693059926 --bind date_sent:l:1771693059926 --bind type:i:2 --bind body:s:"Just landed will call soon" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17045002284 --bind date:l:1750153063417 --bind date_sent:l:1750153063417 --bind type:i:2 --bind body:s:"WiFi password sunshine2024" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17045002284 --bind date:l:1760650134152 --bind date_sent:l:1760650134152 --bind type:i:2 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16827587087 --bind date:l:1769999173244 --bind date_sent:l:1769999173244 --bind type:i:2 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16827587087 --bind date:l:1762385243642 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Traffic is terrible" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16827587087 --bind date:l:1751787397182 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Do not forget electric bill" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16827587087 --bind date:l:1753105718269 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Great news got the job" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16827587087 --bind date:l:1758249783116 --bind date_sent:l:1758249783116 --bind type:i:2 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17779653679 --bind date:l:1769625891984 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17779653679 --bind date:l:1763082500626 --bind date_sent:l:1763082500626 --bind type:i:2 --bind body:s:"Got your message" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18297761410 --bind date:l:1761549294502 --bind date_sent:l:1761549294502 --bind type:i:2 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18297761410 --bind date:l:1747697464895 --bind date_sent:l:1747697464895 --bind type:i:2 --bind body:s:"Hey are you free tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17316357395 --bind date:l:1742921816709 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17316357395 --bind date:l:1756333152571 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Movie starts at 7" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17316357395 --bind date:l:1760984968765 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Sorry I missed your call" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17316357395 --bind date:l:1761360584408 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just landed will call soon" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12036488832 --bind date:l:1742287819772 --bind date_sent:l:1742287819772 --bind type:i:2 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12036488832 --bind date:l:1769361044414 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Sorry I missed your call" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18517566383 --bind date:l:1765329965296 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Sorry I missed your call" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18517566383 --bind date:l:1743196819301 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18517566383 --bind date:l:1760235866824 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18517566383 --bind date:l:1761425372780 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18517566383 --bind date:l:1755579868225 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just finished work heading home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18109206061 --bind date:l:1751708091500 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18109206061 --bind date:l:1744181087153 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"WiFi password sunshine2024" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18109206061 --bind date:l:1758726334621 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Sorry I missed your call" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18109206061 --bind date:l:1761544541955 --bind date_sent:l:1761544541955 --bind type:i:2 --bind body:s:"Just landed will call soon" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18109206061 --bind date:l:1745608287229 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19787623144 --bind date:l:1772957148761 --bind date_sent:l:1772957148761 --bind type:i:2 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19787623144 --bind date:l:1766806381902 --bind date_sent:l:1766806381902 --bind type:i:2 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15207478957 --bind date:l:1761210408535 --bind date_sent:l:1761210408535 --bind type:i:2 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15207478957 --bind date:l:1764154959520 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15207478957 --bind date:l:1751670298856 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19328992426 --bind date:l:1752280825288 --bind date_sent:l:1752280825288 --bind type:i:2 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19328992426 --bind date:l:1748933558940 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"The package arrived today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19328992426 --bind date:l:1766561084078 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just landed will call soon" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19328992426 --bind date:l:1745057353131 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Got your message" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19328992426 --bind date:l:1774208725250 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Let me know when you are ready" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19004115874 --bind date:l:1749363516715 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Sounds good see you then" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19004115874 --bind date:l:1755945832999 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18437264549 --bind date:l:1744726820710 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Weather looks great this weekend" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18437264549 --bind date:l:1759672602961 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Your mom called call her back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13462758993 --bind date:l:1753781860617 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13462758993 --bind date:l:1771249752344 --bind date_sent:l:1771249752344 --bind type:i:2 --bind body:s:"Just finished work heading home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13462758993 --bind date:l:1772154920094 --bind date_sent:l:1772154920094 --bind type:i:2 --bind body:s:"Can you send me that address" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13462758993 --bind date:l:1774063592585 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Did you see the game" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13462758993 --bind date:l:1760671916402 --bind date_sent:l:1760671916402 --bind type:i:2 --bind body:s:"What time works for you" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15478299178 --bind date:l:1749524675034 --bind date_sent:l:1749524675034 --bind type:i:2 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15478299178 --bind date:l:1742291994409 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Traffic is terrible" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15478299178 --bind date:l:1745215431040 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Hey are you free tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15478299178 --bind date:l:1767564243040 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"The package arrived today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15478299178 --bind date:l:1761876766749 --bind date_sent:l:1761876766749 --bind type:i:2 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12367621828 --bind date:l:1745470448183 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12367621828 --bind date:l:1762640255782 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Did you see the game" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18433338842 --bind date:l:1743641484180 --bind date_sent:l:1743641484180 --bind type:i:2 --bind body:s:"I am at the store need anything" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18433338842 --bind date:l:1759569728381 --bind date_sent:l:1759569728381 --bind type:i:2 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18433338842 --bind date:l:1751032312360 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16185715141 --bind date:l:1745220493755 --bind date_sent:l:1745220493755 --bind type:i:2 --bind body:s:"Traffic is terrible" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16185715141 --bind date:l:1756753343401 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16185715141 --bind date:l:1757413458179 --bind date_sent:l:1757413458179 --bind type:i:2 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16185715141 --bind date:l:1742379381303 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Reminder dentist tomorrow 9am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13887183773 --bind date:l:1743815655859 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you watch the kids Saturday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13887183773 --bind date:l:1747059457469 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Running 10 mins late" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13887183773 --bind date:l:1750847497023 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Let me know when you are ready" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12276353849 --bind date:l:1755276923450 --bind date_sent:l:1755276923450 --bind type:i:2 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12276353849 --bind date:l:1754636205343 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12276353849 --bind date:l:1770671687889 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Traffic is terrible" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12276353849 --bind date:l:1758174731671 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13957274950 --bind date:l:1767729401716 --bind date_sent:l:1767729401716 --bind type:i:2 --bind body:s:"Reminder dentist tomorrow 9am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13957274950 --bind date:l:1747855332908 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Traffic is terrible" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13957274950 --bind date:l:1751338237132 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Let me know when you are ready" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13957274950 --bind date:l:1754150294241 --bind date_sent:l:1754150294241 --bind type:i:2 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13957274950 --bind date:l:1763208677866 --bind date_sent:l:1763208677866 --bind type:i:2 --bind body:s:"Great news got the job" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13559104505 --bind date:l:1746450334041 --bind date_sent:l:1746450334041 --bind type:i:2 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13559104505 --bind date:l:1761966452154 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12719253004 --bind date:l:1749757399592 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Movie starts at 7" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12719253004 --bind date:l:1760347526857 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Let me know when you are ready" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12719253004 --bind date:l:1772641761690 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12719253004 --bind date:l:1757693831816 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12719253004 --bind date:l:1771534595730 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13352424633 --bind date:l:1762763326096 --bind date_sent:l:1762763326096 --bind type:i:2 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13352424633 --bind date:l:1773144077791 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"What time works for you" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13352424633 --bind date:l:1758818867705 --bind date_sent:l:1758818867705 --bind type:i:2 --bind body:s:"Just landed will call soon" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13352424633 --bind date:l:1746626141098 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just landed will call soon" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13352424633 --bind date:l:1760942626221 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Reminder dentist tomorrow 9am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17392284656 --bind date:l:1764076570843 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17392284656 --bind date:l:1746932315803 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17392284656 --bind date:l:1766007896842 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Do not forget electric bill" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19027024236 --bind date:l:1741347261695 --bind date_sent:l:1741347261695 --bind type:i:2 --bind body:s:"Just landed will call soon" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19027024236 --bind date:l:1759001766778 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Running 10 mins late" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17998062571 --bind date:l:1771667052333 --bind date_sent:l:1771667052333 --bind type:i:2 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17998062571 --bind date:l:1741288408822 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Running 10 mins late" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17998062571 --bind date:l:1757875816820 --bind date_sent:l:1757875816820 --bind type:i:2 --bind body:s:"Do not forget electric bill" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17998062571 --bind date:l:1752886893240 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17998062571 --bind date:l:1761665710623 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Movie starts at 7" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18256626819 --bind date:l:1761166394437 --bind date_sent:l:1761166394437 --bind type:i:2 --bind body:s:"Got your message" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18256626819 --bind date:l:1751739780382 --bind date_sent:l:1751739780382 --bind type:i:2 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18256626819 --bind date:l:1769932702559 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Hey are you free tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18256626819 --bind date:l:1752821397767 --bind date_sent:l:1752821397767 --bind type:i:2 --bind body:s:"Can you watch the kids Saturday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12666876466 --bind date:l:1770488696808 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"What time works for you" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12666876466 --bind date:l:1741549932526 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12666876466 --bind date:l:1772578293093 --bind date_sent:l:1772578293093 --bind type:i:2 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12666876466 --bind date:l:1761907640077 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12666876466 --bind date:l:1764425618046 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just landed will call soon" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18962235446 --bind date:l:1768574519153 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18962235446 --bind date:l:1756885016772 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"WiFi password sunshine2024" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18962235446 --bind date:l:1765396571495 --bind date_sent:l:1765396571495 --bind type:i:2 --bind body:s:"Great news got the job" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19269722107 --bind date:l:1745651174883 --bind date_sent:l:1745651174883 --bind type:i:2 --bind body:s:"Running 10 mins late" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19269722107 --bind date:l:1761355653451 --bind date_sent:l:1761355653451 --bind type:i:2 --bind body:s:"Hey are you free tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19269722107 --bind date:l:1759959634544 --bind date_sent:l:1759959634544 --bind type:i:2 --bind body:s:"Running 10 mins late" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19269722107 --bind date:l:1747919479988 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13619057122 --bind date:l:1750220801083 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"WiFi password sunshine2024" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13619057122 --bind date:l:1772508332475 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13098045405 --bind date:l:1771259185428 --bind date_sent:l:1771259185428 --bind type:i:2 --bind body:s:"Great news got the job" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13098045405 --bind date:l:1755297189092 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Hey are you free tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12927043418 --bind date:l:1755481353881 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"The package arrived today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12927043418 --bind date:l:1744418637460 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"What time works for you" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12927043418 --bind date:l:1751307344863 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Movie starts at 7" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17452258978 --bind date:l:1766587197011 --bind date_sent:l:1766587197011 --bind type:i:2 --bind body:s:"Congrats on the promotion" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17452258978 --bind date:l:1771868660861 --bind date_sent:l:1771868660861 --bind type:i:2 --bind body:s:"Movie starts at 7" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17452258978 --bind date:l:1762468498655 --bind date_sent:l:1762468498655 --bind type:i:2 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17452258978 --bind date:l:1745392542226 --bind date_sent:l:1745392542226 --bind type:i:2 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17452258978 --bind date:l:1768284745617 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13553057056 --bind date:l:1772896305563 --bind date_sent:l:1772896305563 --bind type:i:2 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13553057056 --bind date:l:1773604477617 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13553057056 --bind date:l:1763762682750 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Your mom called call her back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13553057056 --bind date:l:1752422789585 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16392155044 --bind date:l:1748933853850 --bind date_sent:l:1748933853850 --bind type:i:2 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16392155044 --bind date:l:1755789931843 --bind date_sent:l:1755789931843 --bind type:i:2 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16392155044 --bind date:l:1755365098302 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Weather looks great this weekend" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13012036139 --bind date:l:1769775908794 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"What time works for you" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13012036139 --bind date:l:1748025272894 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13012036139 --bind date:l:1770438365125 --bind date_sent:l:1770438365125 --bind type:i:2 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12126101963 --bind date:l:1763833301148 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Weather looks great this weekend" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12126101963 --bind date:l:1751167247205 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12126101963 --bind date:l:1750718573667 --bind date_sent:l:1750718573667 --bind type:i:2 --bind body:s:"What time works for you" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19549851331 --bind date:l:1768544693370 --bind date_sent:l:1768544693370 --bind type:i:2 --bind body:s:"Do not forget electric bill" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19549851331 --bind date:l:1757460740644 --bind date_sent:l:1757460740644 --bind type:i:2 --bind body:s:"How is your day going" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19549851331 --bind date:l:1741747588915 --bind date_sent:l:1741747588915 --bind type:i:2 --bind body:s:"I am at the store need anything" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17947973625 --bind date:l:1756398571839 --bind date_sent:l:1756398571839 --bind type:i:2 --bind body:s:"WiFi password sunshine2024" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17947973625 --bind date:l:1768920467309 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17947973625 --bind date:l:1755077431947 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18102738342 --bind date:l:1745511106889 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Let me know when you are ready" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18102738342 --bind date:l:1741787918743 --bind date_sent:l:1741787918743 --bind type:i:2 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18102738342 --bind date:l:1764176189276 --bind date_sent:l:1764176189276 --bind type:i:2 --bind body:s:"Did you see the game" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18102738342 --bind date:l:1757181815715 --bind date_sent:l:1757181815715 --bind type:i:2 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18102738342 --bind date:l:1768988072089 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14749972373 --bind date:l:1745737483708 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Movie starts at 7" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14749972373 --bind date:l:1745311965355 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Doctor appointment at 10am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14749972373 --bind date:l:1742018391674 --bind date_sent:l:1742018391674 --bind type:i:2 --bind body:s:"Reminder dentist tomorrow 9am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19257693625 --bind date:l:1761990302993 --bind date_sent:l:1761990302993 --bind type:i:2 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19257693625 --bind date:l:1749242443745 --bind date_sent:l:1749242443745 --bind type:i:2 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19257693625 --bind date:l:1766791077076 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Running 10 mins late" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14436419987 --bind date:l:1763772474552 --bind date_sent:l:1763772474552 --bind type:i:2 --bind body:s:"Do not forget electric bill" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14436419987 --bind date:l:1772286670292 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Movie starts at 7" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14436419987 --bind date:l:1771395103955 --bind date_sent:l:1771395103955 --bind type:i:2 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13999836770 --bind date:l:1752844489496 --bind date_sent:l:1752844489496 --bind type:i:2 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13999836770 --bind date:l:1745396644417 --bind date_sent:l:1745396644417 --bind type:i:2 --bind body:s:"Can you send me that address" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13999836770 --bind date:l:1771587908374 --bind date_sent:l:1771587908374 --bind type:i:2 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13999836770 --bind date:l:1750249557581 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Great news got the job" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12922204243 --bind date:l:1750772029063 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just landed will call soon" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12922204243 --bind date:l:1774548427456 --bind date_sent:l:1774548427456 --bind type:i:2 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12922204243 --bind date:l:1769532825302 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12922204243 --bind date:l:1747467594237 --bind date_sent:l:1747467594237 --bind type:i:2 --bind body:s:"Just landed will call soon" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18576325472 --bind date:l:1761021415530 --bind date_sent:l:1761021415530 --bind type:i:2 --bind body:s:"Running 10 mins late" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18576325472 --bind date:l:1767131879447 --bind date_sent:l:1767131879447 --bind type:i:2 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18576325472 --bind date:l:1758881471824 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Congrats on the promotion" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18576325472 --bind date:l:1758277601634 --bind date_sent:l:1758277601634 --bind type:i:2 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16742555723 --bind date:l:1770281363324 --bind date_sent:l:1770281363324 --bind type:i:2 --bind body:s:"Just landed will call soon" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16742555723 --bind date:l:1750882829893 --bind date_sent:l:1750882829893 --bind type:i:2 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12447011973 --bind date:l:1772022532808 --bind date_sent:l:1772022532808 --bind type:i:2 --bind body:s:"Do not forget electric bill" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12447011973 --bind date:l:1762001228263 --bind date_sent:l:1762001228263 --bind type:i:2 --bind body:s:"Sorry I missed your call" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12447011973 --bind date:l:1761595159544 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12447011973 --bind date:l:1752106835495 --bind date_sent:l:1752106835495 --bind type:i:2 --bind body:s:"What time works for you" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18488326363 --bind date:l:1759169541158 --bind date_sent:l:1759169541158 --bind type:i:2 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18488326363 --bind date:l:1761618786520 --bind date_sent:l:1761618786520 --bind type:i:2 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18488326363 --bind date:l:1743342273936 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just finished work heading home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18488326363 --bind date:l:1753694794004 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Traffic is terrible" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15854325126 --bind date:l:1761197849578 --bind date_sent:l:1761197849578 --bind type:i:2 --bind body:s:"Sounds good see you then" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15854325126 --bind date:l:1772445328003 --bind date_sent:l:1772445328003 --bind type:i:2 --bind body:s:"Great news got the job" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15854325126 --bind date:l:1768390910934 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12388701517 --bind date:l:1754270425839 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How is your day going" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12388701517 --bind date:l:1762657718648 --bind date_sent:l:1762657718648 --bind type:i:2 --bind body:s:"Let me know when you are ready" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12115771212 --bind date:l:1756945153510 --bind date_sent:l:1756945153510 --bind type:i:2 --bind body:s:"Sorry I missed your call" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12115771212 --bind date:l:1749722712879 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12115771212 --bind date:l:1745814785952 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12115771212 --bind date:l:1752214429147 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"WiFi password sunshine2024" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12115771212 --bind date:l:1764951567072 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18509081999 --bind date:l:1761113315002 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18509081999 --bind date:l:1749326529287 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12807887260 --bind date:l:1767712425591 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12807887260 --bind date:l:1767560593798 --bind date_sent:l:1767560593798 --bind type:i:2 --bind body:s:"The package arrived today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12807887260 --bind date:l:1757800986550 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14018479487 --bind date:l:1767071372241 --bind date_sent:l:1767071372241 --bind type:i:2 --bind body:s:"Congrats on the promotion" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14018479487 --bind date:l:1769720951125 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14018479487 --bind date:l:1773173686455 --bind date_sent:l:1773173686455 --bind type:i:2 --bind body:s:"How is your day going" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14018479487 --bind date:l:1767877423676 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14018479487 --bind date:l:1769272257737 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12439683786 --bind date:l:1769077383885 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you watch the kids Saturday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12439683786 --bind date:l:1754233874293 --bind date_sent:l:1754233874293 --bind type:i:2 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14769437708 --bind date:l:1746232298467 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14769437708 --bind date:l:1763627894924 --bind date_sent:l:1763627894924 --bind type:i:2 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14769437708 --bind date:l:1772335780402 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just finished work heading home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13696461805 --bind date:l:1769425524024 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just finished work heading home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13696461805 --bind date:l:1768818513517 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Your mom called call her back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19543853504 --bind date:l:1757784792650 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Sorry I missed your call" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19543853504 --bind date:l:1769775279494 --bind date_sent:l:1769775279494 --bind type:i:2 --bind body:s:"Reminder dentist tomorrow 9am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19543853504 --bind date:l:1760568382698 --bind date_sent:l:1760568382698 --bind type:i:2 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19543853504 --bind date:l:1752493078223 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Let me know when you are ready" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19543853504 --bind date:l:1770716536468 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you send me that address" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19535883534 --bind date:l:1770318549680 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19535883534 --bind date:l:1743600095637 --bind date_sent:l:1743600095637 --bind type:i:2 --bind body:s:"Hey are you free tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19535883534 --bind date:l:1745671814860 --bind date_sent:l:1745671814860 --bind type:i:2 --bind body:s:"Reminder dentist tomorrow 9am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13962597801 --bind date:l:1758166502997 --bind date_sent:l:1758166502997 --bind type:i:2 --bind body:s:"Your mom called call her back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13962597801 --bind date:l:1759851827384 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13962597801 --bind date:l:1744308451124 --bind date_sent:l:1744308451124 --bind type:i:2 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13962597801 --bind date:l:1761087541997 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How is your day going" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15732048167 --bind date:l:1769162823928 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Running 10 mins late" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15732048167 --bind date:l:1745752466457 --bind date_sent:l:1745752466457 --bind type:i:2 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15732048167 --bind date:l:1757500137029 --bind date_sent:l:1757500137029 --bind type:i:2 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15732048167 --bind date:l:1764214835486 --bind date_sent:l:1764214835486 --bind type:i:2 --bind body:s:"What time works for you" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13919039701 --bind date:l:1763792056537 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13919039701 --bind date:l:1758000216700 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13919039701 --bind date:l:1768733338585 --bind date_sent:l:1768733338585 --bind type:i:2 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13919039701 --bind date:l:1769510193611 --bind date_sent:l:1769510193611 --bind type:i:2 --bind body:s:"Great news got the job" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13919039701 --bind date:l:1743650287832 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Do not forget electric bill" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19503406822 --bind date:l:1754804203219 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19503406822 --bind date:l:1774313073480 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Got your message" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19503406822 --bind date:l:1772742278348 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Reminder dentist tomorrow 9am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16736006073 --bind date:l:1759109654560 --bind date_sent:l:1759109654560 --bind type:i:2 --bind body:s:"I am at the store need anything" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16736006073 --bind date:l:1759174359150 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16736006073 --bind date:l:1772662614886 --bind date_sent:l:1772662614886 --bind type:i:2 --bind body:s:"Just finished work heading home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16736006073 --bind date:l:1774495810395 --bind date_sent:l:1774495810395 --bind type:i:2 --bind body:s:"Just landed will call soon" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19902451049 --bind date:l:1759367963848 --bind date_sent:l:1759367963848 --bind type:i:2 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19902451049 --bind date:l:1741770532321 --bind date_sent:l:1741770532321 --bind type:i:2 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19902451049 --bind date:l:1752090345911 --bind date_sent:l:1752090345911 --bind type:i:2 --bind body:s:"Just finished work heading home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15668879166 --bind date:l:1769866747391 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15668879166 --bind date:l:1771733330777 --bind date_sent:l:1771733330777 --bind type:i:2 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15668879166 --bind date:l:1759258187547 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Your mom called call her back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15668879166 --bind date:l:1741248955063 --bind date_sent:l:1741248955063 --bind type:i:2 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15858487220 --bind date:l:1748713360428 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15858487220 --bind date:l:1757902495040 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15858487220 --bind date:l:1755547853247 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15858487220 --bind date:l:1754120613209 --bind date_sent:l:1754120613209 --bind type:i:2 --bind body:s:"Congrats on the promotion" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15858487220 --bind date:l:1772183890079 --bind date_sent:l:1772183890079 --bind type:i:2 --bind body:s:"What time works for you" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15536413381 --bind date:l:1762177970400 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Traffic is terrible" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15536413381 --bind date:l:1768519441404 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15536413381 --bind date:l:1767665659049 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"I am at the store need anything" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19845443270 --bind date:l:1773048173043 --bind date_sent:l:1773048173043 --bind type:i:2 --bind body:s:"Just landed will call soon" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19845443270 --bind date:l:1742876911695 --bind date_sent:l:1742876911695 --bind type:i:2 --bind body:s:"Reminder dentist tomorrow 9am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13688868793 --bind date:l:1769942978208 --bind date_sent:l:1769942978208 --bind type:i:2 --bind body:s:"Doctor appointment at 10am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13688868793 --bind date:l:1759788259458 --bind date_sent:l:1759788259458 --bind type:i:2 --bind body:s:"WiFi password sunshine2024" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14086716212 --bind date:l:1774472282608 --bind date_sent:l:1774472282608 --bind type:i:2 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14086716212 --bind date:l:1752547294047 --bind date_sent:l:1752547294047 --bind type:i:2 --bind body:s:"Great news got the job" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17356732039 --bind date:l:1746623898555 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"What time works for you" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17356732039 --bind date:l:1762092429955 --bind date_sent:l:1762092429955 --bind type:i:2 --bind body:s:"Can you watch the kids Saturday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17356732039 --bind date:l:1741640876321 --bind date_sent:l:1741640876321 --bind type:i:2 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13882873748 --bind date:l:1750989405952 --bind date_sent:l:1750989405952 --bind type:i:2 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13882873748 --bind date:l:1771528098010 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13882873748 --bind date:l:1747819679067 --bind date_sent:l:1747819679067 --bind type:i:2 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13882873748 --bind date:l:1765325597673 --bind date_sent:l:1765325597673 --bind type:i:2 --bind body:s:"How is your day going" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19304664114 --bind date:l:1770590692537 --bind date_sent:l:1770590692537 --bind type:i:2 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19304664114 --bind date:l:1758246327495 --bind date_sent:l:1758246327495 --bind type:i:2 --bind body:s:"I am at the store need anything" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19304664114 --bind date:l:1760040088225 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you watch the kids Saturday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16185425363 --bind date:l:1770901080451 --bind date_sent:l:1770901080451 --bind type:i:2 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16185425363 --bind date:l:1758333284112 --bind date_sent:l:1758333284112 --bind type:i:2 --bind body:s:"Movie starts at 7" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16185425363 --bind date:l:1774445822288 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Reminder dentist tomorrow 9am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16185425363 --bind date:l:1756390313467 --bind date_sent:l:1756390313467 --bind type:i:2 --bind body:s:"Do not forget electric bill" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16185425363 --bind date:l:1769001987465 --bind date_sent:l:1769001987465 --bind type:i:2 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12594547848 --bind date:l:1754808633381 --bind date_sent:l:1754808633381 --bind type:i:2 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12594547848 --bind date:l:1751130871658 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just finished work heading home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12594547848 --bind date:l:1765425895695 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12594547848 --bind date:l:1741589919779 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Let me know when you are ready" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12594547848 --bind date:l:1772677835630 --bind date_sent:l:1772677835630 --bind type:i:2 --bind body:s:"Running 10 mins late" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19333978973 --bind date:l:1758737242975 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19333978973 --bind date:l:1753308423607 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Great news got the job" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19333978973 --bind date:l:1769361430759 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Congrats on the promotion" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19333978973 --bind date:l:1761194633707 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Got your message" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19333978973 --bind date:l:1770718712753 --bind date_sent:l:1770718712753 --bind type:i:2 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18956655043 --bind date:l:1742033462492 --bind date_sent:l:1742033462492 --bind type:i:2 --bind body:s:"Can you watch the kids Saturday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18956655043 --bind date:l:1766588652339 --bind date_sent:l:1766588652339 --bind type:i:2 --bind body:s:"Just finished work heading home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18956655043 --bind date:l:1773114975885 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Doctor appointment at 10am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13484138934 --bind date:l:1744901940761 --bind date_sent:l:1744901940761 --bind type:i:2 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13484138934 --bind date:l:1741958036934 --bind date_sent:l:1741958036934 --bind type:i:2 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13484138934 --bind date:l:1751727499643 --bind date_sent:l:1751727499643 --bind type:i:2 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13484138934 --bind date:l:1769547362189 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13347438052 --bind date:l:1774712691634 --bind date_sent:l:1774712691634 --bind type:i:2 --bind body:s:"Do not forget electric bill" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13347438052 --bind date:l:1769007159296 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Got your message" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19005557927 --bind date:l:1759570262312 --bind date_sent:l:1759570262312 --bind type:i:2 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19005557927 --bind date:l:1761999730268 --bind date_sent:l:1761999730268 --bind type:i:2 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19005557927 --bind date:l:1770608981448 --bind date_sent:l:1770608981448 --bind type:i:2 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19005557927 --bind date:l:1759133954328 --bind date_sent:l:1759133954328 --bind type:i:2 --bind body:s:"Movie starts at 7" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19005557927 --bind date:l:1768191616556 --bind date_sent:l:1768191616556 --bind type:i:2 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18438572919 --bind date:l:1760753487389 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"WiFi password sunshine2024" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18438572919 --bind date:l:1750212512349 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Traffic is terrible" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18438572919 --bind date:l:1763886083976 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18438572919 --bind date:l:1742504290571 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"The package arrived today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18438572919 --bind date:l:1771455277301 --bind date_sent:l:1771455277301 --bind type:i:2 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13688783633 --bind date:l:1760370117891 --bind date_sent:l:1760370117891 --bind type:i:2 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13688783633 --bind date:l:1758967866797 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Hey are you free tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13688783633 --bind date:l:1756257320383 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How is your day going" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13688783633 --bind date:l:1745875245449 --bind date_sent:l:1745875245449 --bind type:i:2 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13688783633 --bind date:l:1745416770823 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"I am at the store need anything" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16097351933 --bind date:l:1766430291006 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16097351933 --bind date:l:1763676829313 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Running 10 mins late" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16097351933 --bind date:l:1751228145679 --bind date_sent:l:1751228145679 --bind type:i:2 --bind body:s:"Just finished work heading home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19283854745 --bind date:l:1744933116352 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19283854745 --bind date:l:1748527969603 --bind date_sent:l:1748527969603 --bind type:i:2 --bind body:s:"Running 10 mins late" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19283854745 --bind date:l:1768497921359 --bind date_sent:l:1768497921359 --bind type:i:2 --bind body:s:"Sorry I missed your call" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19283854745 --bind date:l:1765104951134 --bind date_sent:l:1765104951134 --bind type:i:2 --bind body:s:"Weather looks great this weekend" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19283854745 --bind date:l:1749849179178 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Did you see the game" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12596297672 --bind date:l:1749170465225 --bind date_sent:l:1749170465225 --bind type:i:2 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12596297672 --bind date:l:1750380288600 --bind date_sent:l:1750380288600 --bind type:i:2 --bind body:s:"Sounds good see you then" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12596297672 --bind date:l:1749886009807 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Traffic is terrible" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14809137223 --bind date:l:1764713875082 --bind date_sent:l:1764713875082 --bind type:i:2 --bind body:s:"Movie starts at 7" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14809137223 --bind date:l:1744179043739 --bind date_sent:l:1744179043739 --bind type:i:2 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14327206566 --bind date:l:1753426567197 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you watch the kids Saturday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14327206566 --bind date:l:1765457603177 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15963753617 --bind date:l:1757186099314 --bind date_sent:l:1757186099314 --bind type:i:2 --bind body:s:"Hey are you free tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15963753617 --bind date:l:1750576390617 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Running 10 mins late" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15102989602 --bind date:l:1762274738536 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Congrats on the promotion" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15102989602 --bind date:l:1752050717972 --bind date_sent:l:1752050717972 --bind type:i:2 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15102989602 --bind date:l:1764580891771 --bind date_sent:l:1764580891771 --bind type:i:2 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15102989602 --bind date:l:1764156729759 --bind date_sent:l:1764156729759 --bind type:i:2 --bind body:s:"Running 10 mins late" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19778286144 --bind date:l:1751324287900 --bind date_sent:l:1751324287900 --bind type:i:2 --bind body:s:"Hey are you free tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19778286144 --bind date:l:1745350660404 --bind date_sent:l:1745350660404 --bind type:i:2 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16529188957 --bind date:l:1770802420441 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16529188957 --bind date:l:1753987928616 --bind date_sent:l:1753987928616 --bind type:i:2 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16529188957 --bind date:l:1745297292057 --bind date_sent:l:1745297292057 --bind type:i:2 --bind body:s:"What time works for you" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16529188957 --bind date:l:1746127267514 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Did you see the game" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16529188957 --bind date:l:1769138329677 --bind date_sent:l:1769138329677 --bind type:i:2 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18123873097 --bind date:l:1772619315702 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Great news got the job" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18123873097 --bind date:l:1750320268864 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Weather looks great this weekend" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18123873097 --bind date:l:1742258836474 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18123873097 --bind date:l:1763599427203 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"What time works for you" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18123873097 --bind date:l:1769885088379 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Your mom called call her back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14904081726 --bind date:l:1766763270146 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14904081726 --bind date:l:1744216164947 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13642713422 --bind date:l:1756192391500 --bind date_sent:l:1756192391500 --bind type:i:2 --bind body:s:"Traffic is terrible" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13642713422 --bind date:l:1755631409908 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13047703317 --bind date:l:1752858256005 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Reminder dentist tomorrow 9am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13047703317 --bind date:l:1744954658088 --bind date_sent:l:1744954658088 --bind type:i:2 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13047703317 --bind date:l:1770910046922 --bind date_sent:l:1770910046922 --bind type:i:2 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13047703317 --bind date:l:1745618421038 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14365189766 --bind date:l:1754496510770 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14365189766 --bind date:l:1748371320267 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14365189766 --bind date:l:1772360506587 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Hey are you free tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14904504319 --bind date:l:1760410348116 --bind date_sent:l:1760410348116 --bind type:i:2 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14904504319 --bind date:l:1770884331807 --bind date_sent:l:1770884331807 --bind type:i:2 --bind body:s:"Sounds good see you then" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14904504319 --bind date:l:1749240697840 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Reminder dentist tomorrow 9am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14904504319 --bind date:l:1759905672597 --bind date_sent:l:1759905672597 --bind type:i:2 --bind body:s:"Your mom called call her back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12283855886 --bind date:l:1745027276022 --bind date_sent:l:1745027276022 --bind type:i:2 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12283855886 --bind date:l:1773209379849 --bind date_sent:l:1773209379849 --bind type:i:2 --bind body:s:"Congrats on the promotion" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12283855886 --bind date:l:1758431907645 --bind date_sent:l:1758431907645 --bind type:i:2 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13328964624 --bind date:l:1768460045176 --bind date_sent:l:1768460045176 --bind type:i:2 --bind body:s:"Sorry I missed your call" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13328964624 --bind date:l:1741252981652 --bind date_sent:l:1741252981652 --bind type:i:2 --bind body:s:"How is your day going" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13328964624 --bind date:l:1762011881454 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"I am at the store need anything" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13328964624 --bind date:l:1760897709323 --bind date_sent:l:1760897709323 --bind type:i:2 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13328964624 --bind date:l:1760770894108 --bind date_sent:l:1760770894108 --bind type:i:2 --bind body:s:"Doctor appointment at 10am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15182188984 --bind date:l:1754477446337 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15182188984 --bind date:l:1741364840048 --bind date_sent:l:1741364840048 --bind type:i:2 --bind body:s:"WiFi password sunshine2024" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15182188984 --bind date:l:1755014360675 --bind date_sent:l:1755014360675 --bind type:i:2 --bind body:s:"Doctor appointment at 10am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15182188984 --bind date:l:1758289150551 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15182188984 --bind date:l:1755041798910 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Movie starts at 7" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12895057020 --bind date:l:1747261880618 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"What time works for you" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12895057020 --bind date:l:1744497065348 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Let me know when you are ready" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12895057020 --bind date:l:1763845666744 --bind date_sent:l:1763845666744 --bind type:i:2 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12895057020 --bind date:l:1760920484984 --bind date_sent:l:1760920484984 --bind type:i:2 --bind body:s:"Running 10 mins late" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18742483182 --bind date:l:1741719873429 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Hey are you free tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18742483182 --bind date:l:1742003765034 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18742483182 --bind date:l:1763000404542 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17558099779 --bind date:l:1747460000919 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17558099779 --bind date:l:1742638841974 --bind date_sent:l:1742638841974 --bind type:i:2 --bind body:s:"Can you watch the kids Saturday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19624313299 --bind date:l:1748569221638 --bind date_sent:l:1748569221638 --bind type:i:2 --bind body:s:"The package arrived today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19624313299 --bind date:l:1769577224881 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Your mom called call her back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19624313299 --bind date:l:1761039313532 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Your mom called call her back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19624313299 --bind date:l:1759813651434 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"The package arrived today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17637644623 --bind date:l:1770493604862 --bind date_sent:l:1770493604862 --bind type:i:2 --bind body:s:"Your mom called call her back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17637644623 --bind date:l:1755164547240 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"What time works for you" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14072089685 --bind date:l:1759091091859 --bind date_sent:l:1759091091859 --bind type:i:2 --bind body:s:"Did you see the game" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14072089685 --bind date:l:1745530780707 --bind date_sent:l:1745530780707 --bind type:i:2 --bind body:s:"Got your message" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14072089685 --bind date:l:1771720235167 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14072089685 --bind date:l:1757303609976 --bind date_sent:l:1757303609976 --bind type:i:2 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14072089685 --bind date:l:1742477920232 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"WiFi password sunshine2024" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13997255321 --bind date:l:1766235496697 --bind date_sent:l:1766235496697 --bind type:i:2 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13997255321 --bind date:l:1742670125341 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13997255321 --bind date:l:1748957306308 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13997255321 --bind date:l:1769239271799 --bind date_sent:l:1769239271799 --bind type:i:2 --bind body:s:"Weather looks great this weekend" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13997255321 --bind date:l:1758281907391 --bind date_sent:l:1758281907391 --bind type:i:2 --bind body:s:"Do not forget electric bill" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17686642433 --bind date:l:1766986657888 --bind date_sent:l:1766986657888 --bind type:i:2 --bind body:s:"Reminder dentist tomorrow 9am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17686642433 --bind date:l:1752966698779 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17686642433 --bind date:l:1755179376696 --bind date_sent:l:1755179376696 --bind type:i:2 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17686642433 --bind date:l:1753733382122 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Got your message" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17686642433 --bind date:l:1765957817129 --bind date_sent:l:1765957817129 --bind type:i:2 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13482128699 --bind date:l:1762654457999 --bind date_sent:l:1762654457999 --bind type:i:2 --bind body:s:"Congrats on the promotion" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13482128699 --bind date:l:1756275582924 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13482128699 --bind date:l:1772989141576 --bind date_sent:l:1772989141576 --bind type:i:2 --bind body:s:"Just landed will call soon" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13482128699 --bind date:l:1752622107390 --bind date_sent:l:1752622107390 --bind type:i:2 --bind body:s:"I am at the store need anything" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12817489569 --bind date:l:1765410016665 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12817489569 --bind date:l:1741955201099 --bind date_sent:l:1741955201099 --bind type:i:2 --bind body:s:"Sorry I missed your call" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12817489569 --bind date:l:1773589803230 --bind date_sent:l:1773589803230 --bind type:i:2 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12817489569 --bind date:l:1749475361379 --bind date_sent:l:1749475361379 --bind type:i:2 --bind body:s:"Reminder dentist tomorrow 9am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18653942799 --bind date:l:1752370074929 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Congrats on the promotion" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18653942799 --bind date:l:1758362128912 --bind date_sent:l:1758362128912 --bind type:i:2 --bind body:s:"How is your day going" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15738418185 --bind date:l:1764747199315 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Sounds good see you then" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15738418185 --bind date:l:1763073578881 --bind date_sent:l:1763073578881 --bind type:i:2 --bind body:s:"Sorry I missed your call" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18792201834 --bind date:l:1763433384558 --bind date_sent:l:1763433384558 --bind type:i:2 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18792201834 --bind date:l:1741851780145 --bind date_sent:l:1741851780145 --bind type:i:2 --bind body:s:"Movie starts at 7" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18792201834 --bind date:l:1770361819157 --bind date_sent:l:1770361819157 --bind type:i:2 --bind body:s:"How is your day going" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19383248271 --bind date:l:1743106040902 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Great news got the job" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19383248271 --bind date:l:1763123960342 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Traffic is terrible" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19383248271 --bind date:l:1753629313335 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Reminder dentist tomorrow 9am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19383248271 --bind date:l:1766977554041 --bind date_sent:l:1766977554041 --bind type:i:2 --bind body:s:"I am at the store need anything" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18543652182 --bind date:l:1754641718530 --bind date_sent:l:1754641718530 --bind type:i:2 --bind body:s:"I am at the store need anything" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18543652182 --bind date:l:1772397098763 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18543652182 --bind date:l:1745190342537 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"The package arrived today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12575292844 --bind date:l:1767331174806 --bind date_sent:l:1767331174806 --bind type:i:2 --bind body:s:"How is your day going" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12575292844 --bind date:l:1768022050650 --bind date_sent:l:1768022050650 --bind type:i:2 --bind body:s:"Your mom called call her back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19568922417 --bind date:l:1756200352211 --bind date_sent:l:1756200352211 --bind type:i:2 --bind body:s:"Traffic is terrible" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19568922417 --bind date:l:1749159522820 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Hey are you free tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19568922417 --bind date:l:1747142439313 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19568922417 --bind date:l:1757907906167 --bind date_sent:l:1757907906167 --bind type:i:2 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15723747630 --bind date:l:1769351870135 --bind date_sent:l:1769351870135 --bind type:i:2 --bind body:s:"Your mom called call her back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15723747630 --bind date:l:1769746039233 --bind date_sent:l:1769746039233 --bind type:i:2 --bind body:s:"Can you send me that address" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15723747630 --bind date:l:1749323292860 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15723747630 --bind date:l:1761223908251 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"WiFi password sunshine2024" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15723747630 --bind date:l:1745598903091 --bind date_sent:l:1745598903091 --bind type:i:2 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13806775961 --bind date:l:1742983198577 --bind date_sent:l:1742983198577 --bind type:i:2 --bind body:s:"Got your message" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13806775961 --bind date:l:1746073523502 --bind date_sent:l:1746073523502 --bind type:i:2 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13806775961 --bind date:l:1758601201006 --bind date_sent:l:1758601201006 --bind type:i:2 --bind body:s:"Traffic is terrible" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13806775961 --bind date:l:1760701642874 --bind date_sent:l:1760701642874 --bind type:i:2 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13806775961 --bind date:l:1764482044395 --bind date_sent:l:1764482044395 --bind type:i:2 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17292228098 --bind date:l:1758476670818 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17292228098 --bind date:l:1751636498452 --bind date_sent:l:1751636498452 --bind type:i:2 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19789418803 --bind date:l:1765950357731 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Reminder dentist tomorrow 9am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19789418803 --bind date:l:1764146984216 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"I am at the store need anything" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18718898478 --bind date:l:1762731931135 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Do not forget electric bill" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18718898478 --bind date:l:1756736422351 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Hey are you free tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15254451051 --bind date:l:1768506868547 --bind date_sent:l:1768506868547 --bind type:i:2 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15254451051 --bind date:l:1756856748426 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Weather looks great this weekend" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13194559176 --bind date:l:1748575478192 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Sorry I missed your call" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13194559176 --bind date:l:1769617193127 --bind date_sent:l:1769617193127 --bind type:i:2 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13194559176 --bind date:l:1773958797611 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13194559176 --bind date:l:1761027616571 --bind date_sent:l:1761027616571 --bind type:i:2 --bind body:s:"Did you see the game" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12398269574 --bind date:l:1769901776314 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Let me know when you are ready" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12398269574 --bind date:l:1767783377795 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Did you see the game" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12398269574 --bind date:l:1753969413323 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19328732452 --bind date:l:1766033182896 --bind date_sent:l:1766033182896 --bind type:i:2 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19328732452 --bind date:l:1761248259979 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Movie starts at 7" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14845464687 --bind date:l:1750592963981 --bind date_sent:l:1750592963981 --bind type:i:2 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14845464687 --bind date:l:1747306303033 --bind date_sent:l:1747306303033 --bind type:i:2 --bind body:s:"Can you send me that address" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14845464687 --bind date:l:1744159137135 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you send me that address" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14845464687 --bind date:l:1760384510143 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"WiFi password sunshine2024" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14845464687 --bind date:l:1766189671368 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13463681969 --bind date:l:1764472557745 --bind date_sent:l:1764472557745 --bind type:i:2 --bind body:s:"Running 10 mins late" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13463681969 --bind date:l:1773627292492 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17705451135 --bind date:l:1741464379590 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Your mom called call her back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17705451135 --bind date:l:1753396171277 --bind date_sent:l:1753396171277 --bind type:i:2 --bind body:s:"Got your message" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17705451135 --bind date:l:1763573158280 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Reminder dentist tomorrow 9am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17705451135 --bind date:l:1746337700669 --bind date_sent:l:1746337700669 --bind type:i:2 --bind body:s:"Weather looks great this weekend" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17705451135 --bind date:l:1748908742886 --bind date_sent:l:1748908742886 --bind type:i:2 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17302387207 --bind date:l:1741808697093 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Did you see the game" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17302387207 --bind date:l:1771599533746 --bind date_sent:l:1771599533746 --bind type:i:2 --bind body:s:"Just landed will call soon" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17302387207 --bind date:l:1747091325174 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just finished work heading home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13367715059 --bind date:l:1749106179132 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"WiFi password sunshine2024" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13367715059 --bind date:l:1755630322522 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13367715059 --bind date:l:1748225297605 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Weather looks great this weekend" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13367715059 --bind date:l:1745514457625 --bind date_sent:l:1745514457625 --bind type:i:2 --bind body:s:"Just landed will call soon" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13673882898 --bind date:l:1746519914916 --bind date_sent:l:1746519914916 --bind type:i:2 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13673882898 --bind date:l:1759815739376 --bind date_sent:l:1759815739376 --bind type:i:2 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12578872160 --bind date:l:1757479170830 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Sorry I missed your call" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12578872160 --bind date:l:1744502310246 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"WiFi password sunshine2024" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12578872160 --bind date:l:1755341151852 --bind date_sent:l:1755341151852 --bind type:i:2 --bind body:s:"I am at the store need anything" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12578872160 --bind date:l:1748497635455 --bind date_sent:l:1748497635455 --bind type:i:2 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12337615272 --bind date:l:1763730474022 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12337615272 --bind date:l:1771764381823 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12337615272 --bind date:l:1745216919969 --bind date_sent:l:1745216919969 --bind type:i:2 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12337615272 --bind date:l:1751454307228 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17309745264 --bind date:l:1761916270526 --bind date_sent:l:1761916270526 --bind type:i:2 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17309745264 --bind date:l:1751460693772 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18132345675 --bind date:l:1761098290423 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Congrats on the promotion" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18132345675 --bind date:l:1745502457517 --bind date_sent:l:1745502457517 --bind type:i:2 --bind body:s:"Just landed will call soon" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18132345675 --bind date:l:1754344675014 --bind date_sent:l:1754344675014 --bind type:i:2 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18132345675 --bind date:l:1761416698020 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"I am at the store need anything" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12943644445 --bind date:l:1755267778415 --bind date_sent:l:1755267778415 --bind type:i:2 --bind body:s:"Sounds good see you then" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12943644445 --bind date:l:1751993271480 --bind date_sent:l:1751993271480 --bind type:i:2 --bind body:s:"Your mom called call her back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16942332666 --bind date:l:1761498567473 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Hey are you free tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16942332666 --bind date:l:1750517803807 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15415388916 --bind date:l:1760193713086 --bind date_sent:l:1760193713086 --bind type:i:2 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15415388916 --bind date:l:1764939740331 --bind date_sent:l:1764939740331 --bind type:i:2 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14702518779 --bind date:l:1745736648278 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Running 10 mins late" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14702518779 --bind date:l:1764914409761 --bind date_sent:l:1764914409761 --bind type:i:2 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17689978673 --bind date:l:1762923590759 --bind date_sent:l:1762923590759 --bind type:i:2 --bind body:s:"Your mom called call her back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17689978673 --bind date:l:1761764317750 --bind date_sent:l:1761764317750 --bind type:i:2 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17689978673 --bind date:l:1746481301337 --bind date_sent:l:1746481301337 --bind type:i:2 --bind body:s:"I am at the store need anything" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18043931697 --bind date:l:1743845976809 --bind date_sent:l:1743845976809 --bind type:i:2 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18043931697 --bind date:l:1752977909512 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Weather looks great this weekend" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18043931697 --bind date:l:1757660943377 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Reminder dentist tomorrow 9am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18043931697 --bind date:l:1772412867534 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18043931697 --bind date:l:1750516526974 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19065668217 --bind date:l:1761730128885 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Sorry I missed your call" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19065668217 --bind date:l:1774230874211 --bind date_sent:l:1774230874211 --bind type:i:2 --bind body:s:"What time works for you" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19065668217 --bind date:l:1763431360512 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just finished work heading home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19065668217 --bind date:l:1763665748431 --bind date_sent:l:1763665748431 --bind type:i:2 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15654491434 --bind date:l:1772649823850 --bind date_sent:l:1772649823850 --bind type:i:2 --bind body:s:"Your mom called call her back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15654491434 --bind date:l:1769008209252 --bind date_sent:l:1769008209252 --bind type:i:2 --bind body:s:"Can you send me that address" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15654491434 --bind date:l:1757144860691 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Great news got the job" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17987469927 --bind date:l:1760260930454 --bind date_sent:l:1760260930454 --bind type:i:2 --bind body:s:"Can you send me that address" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17987469927 --bind date:l:1746052707477 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you send me that address" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17987469927 --bind date:l:1768399966098 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13502512594 --bind date:l:1742294119768 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13502512594 --bind date:l:1760337143234 --bind date_sent:l:1760337143234 --bind type:i:2 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13502512594 --bind date:l:1763151545207 --bind date_sent:l:1763151545207 --bind type:i:2 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19825164084 --bind date:l:1772034707009 --bind date_sent:l:1772034707009 --bind type:i:2 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19825164084 --bind date:l:1742267036602 --bind date_sent:l:1742267036602 --bind type:i:2 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19825164084 --bind date:l:1761494723344 --bind date_sent:l:1761494723344 --bind type:i:2 --bind body:s:"Got your message" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13092006439 --bind date:l:1769403796262 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Great news got the job" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13092006439 --bind date:l:1766471415275 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Movie starts at 7" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13092006439 --bind date:l:1765569719412 --bind date_sent:l:1765569719412 --bind type:i:2 --bind body:s:"How is your day going" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13092006439 --bind date:l:1760890684014 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"I am at the store need anything" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19355687582 --bind date:l:1767100488609 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19355687582 --bind date:l:1774737187294 --bind date_sent:l:1774737187294 --bind type:i:2 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19355687582 --bind date:l:1770019352158 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14045003345 --bind date:l:1752493111107 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14045003345 --bind date:l:1751866875437 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Hey are you free tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14045003345 --bind date:l:1766980833159 --bind date_sent:l:1766980833159 --bind type:i:2 --bind body:s:"Let me know when you are ready" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14045003345 --bind date:l:1749701629728 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Traffic is terrible" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14045003345 --bind date:l:1771101321583 --bind date_sent:l:1771101321583 --bind type:i:2 --bind body:s:"Great news got the job" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14016187295 --bind date:l:1768367191529 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"WiFi password sunshine2024" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14016187295 --bind date:l:1747154325615 --bind date_sent:l:1747154325615 --bind type:i:2 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14016187295 --bind date:l:1765911159312 --bind date_sent:l:1765911159312 --bind type:i:2 --bind body:s:"How is your day going" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14016187295 --bind date:l:1774257112804 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14133986301 --bind date:l:1752786948727 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just landed will call soon" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14133986301 --bind date:l:1749507448602 --bind date_sent:l:1749507448602 --bind type:i:2 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13543858871 --bind date:l:1762265679591 --bind date_sent:l:1762265679591 --bind type:i:2 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13543858871 --bind date:l:1757760562356 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Doctor appointment at 10am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13543858871 --bind date:l:1745846386204 --bind date_sent:l:1745846386204 --bind type:i:2 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13543858871 --bind date:l:1756055328112 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17587917141 --bind date:l:1763787339028 --bind date_sent:l:1763787339028 --bind type:i:2 --bind body:s:"Did you see the game" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17587917141 --bind date:l:1746910423934 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Your mom called call her back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14296611533 --bind date:l:1762052303079 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Hey are you free tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14296611533 --bind date:l:1762264778912 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Weather looks great this weekend" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14296611533 --bind date:l:1764616080498 --bind date_sent:l:1764616080498 --bind type:i:2 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14296611533 --bind date:l:1770100076347 --bind date_sent:l:1770100076347 --bind type:i:2 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12496746183 --bind date:l:1758831239882 --bind date_sent:l:1758831239882 --bind type:i:2 --bind body:s:"I am at the store need anything" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12496746183 --bind date:l:1749969771972 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you send me that address" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18783444038 --bind date:l:1745045791151 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Weather looks great this weekend" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18783444038 --bind date:l:1747298246017 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Did you see the game" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18783444038 --bind date:l:1762484167613 --bind date_sent:l:1762484167613 --bind type:i:2 --bind body:s:"I am at the store need anything" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14767179424 --bind date:l:1760272855664 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14767179424 --bind date:l:1773832697086 --bind date_sent:l:1773832697086 --bind type:i:2 --bind body:s:"I am at the store need anything" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14767179424 --bind date:l:1757423322324 --bind date_sent:l:1757423322324 --bind type:i:2 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14767179424 --bind date:l:1773220027711 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Sounds good see you then" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14767179424 --bind date:l:1766078792690 --bind date_sent:l:1766078792690 --bind type:i:2 --bind body:s:"Reminder dentist tomorrow 9am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19688759730 --bind date:l:1763989529057 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just landed will call soon" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19688759730 --bind date:l:1747443970362 --bind date_sent:l:1747443970362 --bind type:i:2 --bind body:s:"What time works for you" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19688759730 --bind date:l:1754680534422 --bind date_sent:l:1754680534422 --bind type:i:2 --bind body:s:"Can you send me that address" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19688759730 --bind date:l:1770402363348 --bind date_sent:l:1770402363348 --bind type:i:2 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17089446267 --bind date:l:1750614259359 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you send me that address" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17089446267 --bind date:l:1752348537212 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Great news got the job" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17089446267 --bind date:l:1757587766700 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17089446267 --bind date:l:1772269670527 --bind date_sent:l:1772269670527 --bind type:i:2 --bind body:s:"Can you watch the kids Saturday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17089446267 --bind date:l:1757251468875 --bind date_sent:l:1757251468875 --bind type:i:2 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18327979948 --bind date:l:1774760967436 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18327979948 --bind date:l:1757459357075 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12265896151 --bind date:l:1751469057974 --bind date_sent:l:1751469057974 --bind type:i:2 --bind body:s:"Got your message" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12265896151 --bind date:l:1769969568324 --bind date_sent:l:1769969568324 --bind type:i:2 --bind body:s:"Just landed will call soon" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16508187543 --bind date:l:1741962924080 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16508187543 --bind date:l:1746172960749 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you send me that address" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16508187543 --bind date:l:1766646481750 --bind date_sent:l:1766646481750 --bind type:i:2 --bind body:s:"Doctor appointment at 10am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16508187543 --bind date:l:1757793883483 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Doctor appointment at 10am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16508187543 --bind date:l:1753849891635 --bind date_sent:l:1753849891635 --bind type:i:2 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14228748790 --bind date:l:1763684718073 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"WiFi password sunshine2024" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14228748790 --bind date:l:1770733900149 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14228748790 --bind date:l:1764645629269 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13386237257 --bind date:l:1759778810038 --bind date_sent:l:1759778810038 --bind type:i:2 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13386237257 --bind date:l:1763804164005 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13386237257 --bind date:l:1762647657414 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13386237257 --bind date:l:1746751778716 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you watch the kids Saturday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13386237257 --bind date:l:1766185914620 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How is your day going" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15009166060 --bind date:l:1766009057854 --bind date_sent:l:1766009057854 --bind type:i:2 --bind body:s:"How is your day going" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15009166060 --bind date:l:1770465284607 --bind date_sent:l:1770465284607 --bind type:i:2 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18758669781 --bind date:l:1744144049286 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Doctor appointment at 10am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18758669781 --bind date:l:1758747335918 --bind date_sent:l:1758747335918 --bind type:i:2 --bind body:s:"Hey are you free tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18758669781 --bind date:l:1757665759041 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14234987361 --bind date:l:1753957849603 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you watch the kids Saturday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14234987361 --bind date:l:1748597457466 --bind date_sent:l:1748597457466 --bind type:i:2 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14234987361 --bind date:l:1769296910579 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18308646769 --bind date:l:1743820942935 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18308646769 --bind date:l:1761215392815 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just finished work heading home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17519997080 --bind date:l:1768609022467 --bind date_sent:l:1768609022467 --bind type:i:2 --bind body:s:"Sorry I missed your call" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17519997080 --bind date:l:1771176349490 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Did you see the game" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12216576378 --bind date:l:1747283934764 --bind date_sent:l:1747283934764 --bind type:i:2 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12216576378 --bind date:l:1763622920428 --bind date_sent:l:1763622920428 --bind type:i:2 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12216576378 --bind date:l:1759131027151 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12216576378 --bind date:l:1770776851994 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12216576378 --bind date:l:1772064933861 --bind date_sent:l:1772064933861 --bind type:i:2 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18465188801 --bind date:l:1767539099800 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Great news got the job" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18465188801 --bind date:l:1750383594435 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Reminder dentist tomorrow 9am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18465188801 --bind date:l:1755692796216 --bind date_sent:l:1755692796216 --bind type:i:2 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18465188801 --bind date:l:1769120138307 --bind date_sent:l:1769120138307 --bind type:i:2 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18465188801 --bind date:l:1767269528825 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"I am at the store need anything" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17159214186 --bind date:l:1751139072410 --bind date_sent:l:1751139072410 --bind type:i:2 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17159214186 --bind date:l:1742249180508 --bind date_sent:l:1742249180508 --bind type:i:2 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17159214186 --bind date:l:1763334812807 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17159214186 --bind date:l:1763669851159 --bind date_sent:l:1763669851159 --bind type:i:2 --bind body:s:"Did you see the game" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17159214186 --bind date:l:1758654603194 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Great news got the job" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13064981413 --bind date:l:1768171545440 --bind date_sent:l:1768171545440 --bind type:i:2 --bind body:s:"I am at the store need anything" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13064981413 --bind date:l:1744993595840 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13064981413 --bind date:l:1749758722374 --bind date_sent:l:1749758722374 --bind type:i:2 --bind body:s:"Sounds good see you then" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16668966103 --bind date:l:1762456428371 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16668966103 --bind date:l:1762192999439 --bind date_sent:l:1762192999439 --bind type:i:2 --bind body:s:"I am at the store need anything" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16668966103 --bind date:l:1766773669096 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16668966103 --bind date:l:1752487689853 --bind date_sent:l:1752487689853 --bind type:i:2 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17664897348 --bind date:l:1756395128681 --bind date_sent:l:1756395128681 --bind type:i:2 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17664897348 --bind date:l:1757059443196 --bind date_sent:l:1757059443196 --bind type:i:2 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17664897348 --bind date:l:1770106190449 --bind date_sent:l:1770106190449 --bind type:i:2 --bind body:s:"Movie starts at 7" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17664897348 --bind date:l:1746178209364 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17664897348 --bind date:l:1743313261997 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15075334904 --bind date:l:1746037274659 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15075334904 --bind date:l:1757289771904 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you watch the kids Saturday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15075334904 --bind date:l:1745323640725 --bind date_sent:l:1745323640725 --bind type:i:2 --bind body:s:"Sounds good see you then" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18548467981 --bind date:l:1759127416603 --bind date_sent:l:1759127416603 --bind type:i:2 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18548467981 --bind date:l:1744773841906 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"WiFi password sunshine2024" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18548467981 --bind date:l:1746695985461 --bind date_sent:l:1746695985461 --bind type:i:2 --bind body:s:"WiFi password sunshine2024" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18548467981 --bind date:l:1754279470641 --bind date_sent:l:1754279470641 --bind type:i:2 --bind body:s:"WiFi password sunshine2024" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17727374312 --bind date:l:1745608100270 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17727374312 --bind date:l:1764770187809 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Got your message" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17727374312 --bind date:l:1745027727980 --bind date_sent:l:1745027727980 --bind type:i:2 --bind body:s:"Movie starts at 7" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17727374312 --bind date:l:1745360041399 --bind date_sent:l:1745360041399 --bind type:i:2 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17727374312 --bind date:l:1743191348802 --bind date_sent:l:1743191348802 --bind type:i:2 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16156886329 --bind date:l:1759597883126 --bind date_sent:l:1759597883126 --bind type:i:2 --bind body:s:"Traffic is terrible" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16156886329 --bind date:l:1764889309051 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Sounds good see you then" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16156886329 --bind date:l:1765026549611 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just landed will call soon" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12446899355 --bind date:l:1754700703208 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12446899355 --bind date:l:1759539628663 --bind date_sent:l:1759539628663 --bind type:i:2 --bind body:s:"The package arrived today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12446899355 --bind date:l:1770243485841 --bind date_sent:l:1770243485841 --bind type:i:2 --bind body:s:"Weather looks great this weekend" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12446899355 --bind date:l:1743017982119 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12906541900 --bind date:l:1749652758867 --bind date_sent:l:1749652758867 --bind type:i:2 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12906541900 --bind date:l:1750179239821 --bind date_sent:l:1750179239821 --bind type:i:2 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15534713091 --bind date:l:1751926948000 --bind date_sent:l:1751926948000 --bind type:i:2 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15534713091 --bind date:l:1757204149462 --bind date_sent:l:1757204149462 --bind type:i:2 --bind body:s:"Traffic is terrible" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15534713091 --bind date:l:1760184750058 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15534713091 --bind date:l:1766186469879 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"The package arrived today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15534713091 --bind date:l:1762892496219 --bind date_sent:l:1762892496219 --bind type:i:2 --bind body:s:"Movie starts at 7" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13133425223 --bind date:l:1755444607773 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Reminder dentist tomorrow 9am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13133425223 --bind date:l:1744820461480 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"WiFi password sunshine2024" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13133425223 --bind date:l:1747826094893 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13133425223 --bind date:l:1757761005798 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13133425223 --bind date:l:1759059248873 --bind date_sent:l:1759059248873 --bind type:i:2 --bind body:s:"The package arrived today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13894785566 --bind date:l:1764092415603 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13894785566 --bind date:l:1741680636801 --bind date_sent:l:1741680636801 --bind type:i:2 --bind body:s:"Can you watch the kids Saturday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14236548779 --bind date:l:1765709751781 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14236548779 --bind date:l:1771297070773 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14236548779 --bind date:l:1760690307415 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Reminder dentist tomorrow 9am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14236548779 --bind date:l:1762626171232 --bind date_sent:l:1762626171232 --bind type:i:2 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14236548779 --bind date:l:1751827189108 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19945236369 --bind date:l:1760087057301 --bind date_sent:l:1760087057301 --bind type:i:2 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19945236369 --bind date:l:1752246422615 --bind date_sent:l:1752246422615 --bind type:i:2 --bind body:s:"Your mom called call her back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19945236369 --bind date:l:1752841899324 --bind date_sent:l:1752841899324 --bind type:i:2 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14945436342 --bind date:l:1764581635191 --bind date_sent:l:1764581635191 --bind type:i:2 --bind body:s:"Sorry I missed your call" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14945436342 --bind date:l:1764100751031 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14945436342 --bind date:l:1773909214097 --bind date_sent:l:1773909214097 --bind type:i:2 --bind body:s:"Running 10 mins late" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15066793961 --bind date:l:1763219888514 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"The package arrived today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15066793961 --bind date:l:1766187923648 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15066793961 --bind date:l:1767707938782 --bind date_sent:l:1767707938782 --bind type:i:2 --bind body:s:"Hey are you free tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15066793961 --bind date:l:1745717618088 --bind date_sent:l:1745717618088 --bind type:i:2 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17913152418 --bind date:l:1750775149127 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17913152418 --bind date:l:1746178764682 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16593116967 --bind date:l:1746212766920 --bind date_sent:l:1746212766920 --bind type:i:2 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16593116967 --bind date:l:1759976963654 --bind date_sent:l:1759976963654 --bind type:i:2 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16593116967 --bind date:l:1761131408852 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Great news got the job" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16593116967 --bind date:l:1751821826631 --bind date_sent:l:1751821826631 --bind type:i:2 --bind body:s:"Movie starts at 7" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13573268993 --bind date:l:1765246032691 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13573268993 --bind date:l:1745071216135 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13573268993 --bind date:l:1755293041705 --bind date_sent:l:1755293041705 --bind type:i:2 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15903678133 --bind date:l:1743273107948 --bind date_sent:l:1743273107948 --bind type:i:2 --bind body:s:"Doctor appointment at 10am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15903678133 --bind date:l:1750346623603 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Got your message" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15903678133 --bind date:l:1756038164916 --bind date_sent:l:1756038164916 --bind type:i:2 --bind body:s:"How is your day going" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13985686169 --bind date:l:1751546183155 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13985686169 --bind date:l:1741496051118 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13985686169 --bind date:l:1767915299812 --bind date_sent:l:1767915299812 --bind type:i:2 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17418495592 --bind date:l:1754880228385 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17418495592 --bind date:l:1754224379718 --bind date_sent:l:1754224379718 --bind type:i:2 --bind body:s:"Did you see the game" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17418495592 --bind date:l:1743416124055 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13482954307 --bind date:l:1749012895560 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13482954307 --bind date:l:1758770155257 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Your mom called call her back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13482954307 --bind date:l:1742422582026 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19503344514 --bind date:l:1744406150203 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How is your day going" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19503344514 --bind date:l:1768389186462 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16842233524 --bind date:l:1751223455780 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Movie starts at 7" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16842233524 --bind date:l:1749843474441 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you send me that address" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14046774753 --bind date:l:1754279989982 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"I am at the store need anything" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14046774753 --bind date:l:1761246186893 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How is your day going" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14046774753 --bind date:l:1759246655960 --bind date_sent:l:1759246655960 --bind type:i:2 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14046774753 --bind date:l:1762380453673 --bind date_sent:l:1762380453673 --bind type:i:2 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14046774753 --bind date:l:1774671123065 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"The package arrived today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19186258917 --bind date:l:1767987628415 --bind date_sent:l:1767987628415 --bind type:i:2 --bind body:s:"How is your day going" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19186258917 --bind date:l:1764577903954 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19186258917 --bind date:l:1741680360731 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19186258917 --bind date:l:1759027662153 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"The package arrived today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19186258917 --bind date:l:1754034574782 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17499367815 --bind date:l:1771144867759 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17499367815 --bind date:l:1762555821868 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"WiFi password sunshine2024" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15316201011 --bind date:l:1755600935591 --bind date_sent:l:1755600935591 --bind type:i:2 --bind body:s:"Did you see the game" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15316201011 --bind date:l:1757504877798 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Doctor appointment at 10am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15316201011 --bind date:l:1774704201134 --bind date_sent:l:1774704201134 --bind type:i:2 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15316201011 --bind date:l:1749047416180 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"What time works for you" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15316201011 --bind date:l:1749903976000 --bind date_sent:l:1749903976000 --bind type:i:2 --bind body:s:"Running 10 mins late" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16334058800 --bind date:l:1768117146011 --bind date_sent:l:1768117146011 --bind type:i:2 --bind body:s:"The package arrived today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16334058800 --bind date:l:1751769809952 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you watch the kids Saturday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15803022796 --bind date:l:1744533881323 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just landed will call soon" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15803022796 --bind date:l:1770349034474 --bind date_sent:l:1770349034474 --bind type:i:2 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15803022796 --bind date:l:1755949749937 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15803022796 --bind date:l:1765584592713 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15039662217 --bind date:l:1762303367170 --bind date_sent:l:1762303367170 --bind type:i:2 --bind body:s:"What time works for you" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15039662217 --bind date:l:1772168614232 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Reminder dentist tomorrow 9am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15039662217 --bind date:l:1773950603302 --bind date_sent:l:1773950603302 --bind type:i:2 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15039662217 --bind date:l:1752044552885 --bind date_sent:l:1752044552885 --bind type:i:2 --bind body:s:"Just finished work heading home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14116481003 --bind date:l:1768451568641 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14116481003 --bind date:l:1759751435483 --bind date_sent:l:1759751435483 --bind type:i:2 --bind body:s:"The package arrived today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14116481003 --bind date:l:1752647911807 --bind date_sent:l:1752647911807 --bind type:i:2 --bind body:s:"What time works for you" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12345048563 --bind date:l:1747570803430 --bind date_sent:l:1747570803430 --bind type:i:2 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12345048563 --bind date:l:1753639211382 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17598977675 --bind date:l:1750392801125 --bind date_sent:l:1750392801125 --bind type:i:2 --bind body:s:"Just finished work heading home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17598977675 --bind date:l:1765756209551 --bind date_sent:l:1765756209551 --bind type:i:2 --bind body:s:"Movie starts at 7" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17598977675 --bind date:l:1755967068624 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Sorry I missed your call" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17598977675 --bind date:l:1756084777871 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Do not forget electric bill" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15409182601 --bind date:l:1752823613335 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Do not forget electric bill" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15409182601 --bind date:l:1764321617400 --bind date_sent:l:1764321617400 --bind type:i:2 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15409182601 --bind date:l:1759177463027 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15409182601 --bind date:l:1765162830394 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Weather looks great this weekend" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13832936393 --bind date:l:1741509753952 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Your mom called call her back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13832936393 --bind date:l:1741374770216 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Traffic is terrible" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13832936393 --bind date:l:1750353909916 --bind date_sent:l:1750353909916 --bind type:i:2 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12015708879 --bind date:l:1742220587008 --bind date_sent:l:1742220587008 --bind type:i:2 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12015708879 --bind date:l:1769150678705 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12015708879 --bind date:l:1749817722777 --bind date_sent:l:1749817722777 --bind type:i:2 --bind body:s:"Just finished work heading home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12015708879 --bind date:l:1763526853826 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17956344620 --bind date:l:1753758717739 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Congrats on the promotion" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17956344620 --bind date:l:1761528213426 --bind date_sent:l:1761528213426 --bind type:i:2 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17956344620 --bind date:l:1742171862129 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you watch the kids Saturday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12086466324 --bind date:l:1771648369326 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12086466324 --bind date:l:1766894088081 --bind date_sent:l:1766894088081 --bind type:i:2 --bind body:s:"Congrats on the promotion" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12086466324 --bind date:l:1751856641351 --bind date_sent:l:1751856641351 --bind type:i:2 --bind body:s:"Just finished work heading home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12086466324 --bind date:l:1772751026901 --bind date_sent:l:1772751026901 --bind type:i:2 --bind body:s:"Reminder dentist tomorrow 9am" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19433992077 --bind date:l:1746881677705 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19433992077 --bind date:l:1767012133079 --bind date_sent:l:1767012133079 --bind type:i:2 --bind body:s:"Just landed will call soon" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19433992077 --bind date:l:1753946490925 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17795377466 --bind date:l:1753455891985 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17795377466 --bind date:l:1744316282336 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Thanks for your help today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17795377466 --bind date:l:1750492646417 --bind date_sent:l:1750492646417 --bind type:i:2 --bind body:s:"Running 10 mins late" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17795377466 --bind date:l:1760139894097 --bind date_sent:l:1760139894097 --bind type:i:2 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17795377466 --bind date:l:1772829300062 --bind date_sent:l:1772829300062 --bind type:i:2 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18109062783 --bind date:l:1750752517520 --bind date_sent:l:1750752517520 --bind type:i:2 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18109062783 --bind date:l:1774009615342 --bind date_sent:l:1774009615342 --bind type:i:2 --bind body:s:"Can you watch the kids Saturday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18109062783 --bind date:l:1773519317774 --bind date_sent:l:1773519317774 --bind type:i:2 --bind body:s:"Just landed will call soon" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18109062783 --bind date:l:1748698391813 --bind date_sent:l:1748698391813 --bind type:i:2 --bind body:s:"Got your message" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12607351411 --bind date:l:1754032862053 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12607351411 --bind date:l:1744962153131 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12607351411 --bind date:l:1773456732883 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12607351411 --bind date:l:1764901700697 --bind date_sent:l:1764901700697 --bind type:i:2 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19879622113 --bind date:l:1758537789898 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Got your message" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19879622113 --bind date:l:1745329094075 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Congrats on the promotion" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19879622113 --bind date:l:1759588592171 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19879622113 --bind date:l:1767691102497 --bind date_sent:l:1767691102497 --bind type:i:2 --bind body:s:"Sorry I missed your call" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17919938730 --bind date:l:1764480272363 --bind date_sent:l:1764480272363 --bind type:i:2 --bind body:s:"I am at the store need anything" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17919938730 --bind date:l:1759258768926 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17919938730 --bind date:l:1761814761288 --bind date_sent:l:1761814761288 --bind type:i:2 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18029952712 --bind date:l:1760362377347 --bind date_sent:l:1760362377347 --bind type:i:2 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18029952712 --bind date:l:1763973112426 --bind date_sent:l:1763973112426 --bind type:i:2 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18029952712 --bind date:l:1750053624836 --bind date_sent:l:1750053624836 --bind type:i:2 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18029952712 --bind date:l:1774365078280 --bind date_sent:l:1774365078280 --bind type:i:2 --bind body:s:"Sounds good see you then" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18029952712 --bind date:l:1762000444195 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15487584508 --bind date:l:1768749421994 --bind date_sent:l:1768749421994 --bind type:i:2 --bind body:s:"Can you watch the kids Saturday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15487584508 --bind date:l:1774224624109 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15487584508 --bind date:l:1763417203438 --bind date_sent:l:1763417203438 --bind type:i:2 --bind body:s:"Love you have a great day" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18579807748 --bind date:l:1744693585831 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Running 10 mins late" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18579807748 --bind date:l:1773569379917 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18579807748 --bind date:l:1771958109956 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18579807748 --bind date:l:1749998688085 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just landed will call soon" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19456361303 --bind date:l:1759640602600 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Do not forget electric bill" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19456361303 --bind date:l:1753596115298 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just finished work heading home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+19456361303 --bind date:l:1759790337866 --bind date_sent:l:1759790337866 --bind type:i:2 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17713621057 --bind date:l:1747806414091 --bind date_sent:l:1747806414091 --bind type:i:2 --bind body:s:"Did you see the game" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17713621057 --bind date:l:1768452874875 --bind date_sent:l:1768452874875 --bind type:i:2 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17713621057 --bind date:l:1763614408718 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Did you see the game" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17713621057 --bind date:l:1755924846891 --bind date_sent:l:1755924846891 --bind type:i:2 --bind body:s:"Your mom called call her back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17713621057 --bind date:l:1758494350977 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Do not forget electric bill" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18925178010 --bind date:l:1756092190991 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Running 10 mins late" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18925178010 --bind date:l:1758147413548 --bind date_sent:l:1758147413548 --bind type:i:2 --bind body:s:"Got your message" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18925178010 --bind date:l:1765178384765 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18925178010 --bind date:l:1762982355554 --bind date_sent:l:1762982355554 --bind type:i:2 --bind body:s:"Got your message" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14489242692 --bind date:l:1767493154107 --bind date_sent:l:1767493154107 --bind type:i:2 --bind body:s:"The package arrived today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14489242692 --bind date:l:1770139725408 --bind date_sent:l:1770139725408 --bind type:i:2 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14489242692 --bind date:l:1744314817939 --bind date_sent:l:1744314817939 --bind type:i:2 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14489242692 --bind date:l:1761661510743 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12615773764 --bind date:l:1766293399580 --bind date_sent:l:1766293399580 --bind type:i:2 --bind body:s:"Can you watch the kids Saturday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12615773764 --bind date:l:1744399560441 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just landed will call soon" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15673699923 --bind date:l:1757120259847 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How is your day going" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15673699923 --bind date:l:1773917304063 --bind date_sent:l:1773917304063 --bind type:i:2 --bind body:s:"Let me know when you are ready" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15673699923 --bind date:l:1746690420321 --bind date_sent:l:1746690420321 --bind type:i:2 --bind body:s:"Weather looks great this weekend" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15673699923 --bind date:l:1761426054764 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Great news got the job" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15673699923 --bind date:l:1763391723713 --bind date_sent:l:1763391723713 --bind type:i:2 --bind body:s:"Great news got the job" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16784168251 --bind date:l:1748387084458 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Did you see the game" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16784168251 --bind date:l:1762468566508 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Hey are you free tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16784168251 --bind date:l:1748428934258 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16784168251 --bind date:l:1767400627903 --bind date_sent:l:1767400627903 --bind type:i:2 --bind body:s:"Sorry I missed your call" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16784168251 --bind date:l:1741717063660 --bind date_sent:l:1741717063660 --bind type:i:2 --bind body:s:"I am at the store need anything" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15108621494 --bind date:l:1749309127746 --bind date_sent:l:1749309127746 --bind type:i:2 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15108621494 --bind date:l:1745363926794 --bind date_sent:l:1745363926794 --bind type:i:2 --bind body:s:"Did you see the game" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15108621494 --bind date:l:1756056105240 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Got your message" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15108621494 --bind date:l:1770503904509 --bind date_sent:l:1770503904509 --bind type:i:2 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17619541043 --bind date:l:1754594967207 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17619541043 --bind date:l:1756481941551 --bind date_sent:l:1756481941551 --bind type:i:2 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16538995307 --bind date:l:1764788758978 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16538995307 --bind date:l:1753818051612 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Congrats on the promotion" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16538995307 --bind date:l:1755440581814 --bind date_sent:l:1755440581814 --bind type:i:2 --bind body:s:"Congrats on the promotion" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16538995307 --bind date:l:1745498173340 --bind date_sent:l:1745498173340 --bind type:i:2 --bind body:s:"I will pick you up at 6" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17994322670 --bind date:l:1765129487396 --bind date_sent:l:1765129487396 --bind type:i:2 --bind body:s:"Got your message" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17994322670 --bind date:l:1746609959662 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15756433885 --bind date:l:1746440093991 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"I am at the store need anything" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15756433885 --bind date:l:1743016685516 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15756433885 --bind date:l:1764011604763 --bind date_sent:l:1764011604763 --bind type:i:2 --bind body:s:"How is your day going" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15756433885 --bind date:l:1764780024498 --bind date_sent:l:1764780024498 --bind type:i:2 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15756433885 --bind date:l:1746793363061 --bind date_sent:l:1746793363061 --bind type:i:2 --bind body:s:"Meeting at 3pm confirmed" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12756262378 --bind date:l:1746491559524 --bind date_sent:l:1746491559524 --bind type:i:2 --bind body:s:"Weather looks great this weekend" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12756262378 --bind date:l:1766470046921 --bind date_sent:l:1766470046921 --bind type:i:2 --bind body:s:"Congrats on the promotion" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12756262378 --bind date:l:1761832662519 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12756262378 --bind date:l:1745714329755 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just landed will call soon" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12756262378 --bind date:l:1774063815196 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13459755512 --bind date:l:1761667259358 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Flight delayed 2 hours" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13459755512 --bind date:l:1751395899330 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Sounds good see you then" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13459755512 --bind date:l:1741718733729 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18403646029 --bind date:l:1742893553665 --bind date_sent:l:1742893553665 --bind type:i:2 --bind body:s:"How was the interview" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18403646029 --bind date:l:1756364765062 --bind date_sent:l:1756364765062 --bind type:i:2 --bind body:s:"Thanks for dinner" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18403646029 --bind date:l:1762767079188 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12178399921 --bind date:l:1765241677322 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"WiFi password sunshine2024" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12178399921 --bind date:l:1743134683158 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+12178399921 --bind date:l:1750736726132 --bind date_sent:l:1750736726132 --bind type:i:2 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16056576317 --bind date:l:1767937820212 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Congrats on the promotion" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16056576317 --bind date:l:1752134278781 --bind date_sent:l:1752134278781 --bind type:i:2 --bind body:s:"Running 10 mins late" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17196881302 --bind date:l:1744499862901 --bind date_sent:l:1744499862901 --bind type:i:2 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17196881302 --bind date:l:1749544097651 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Congrats on the promotion" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15809595749 --bind date:l:1768613424382 --bind date_sent:l:1768613424382 --bind type:i:2 --bind body:s:"Be there in 20 minutes" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15809595749 --bind date:l:1750544302079 --bind date_sent:l:1750544302079 --bind type:i:2 --bind body:s:"Pizza or Chinese tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15809595749 --bind date:l:1752615662948 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Sounds good see you then" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18154684363 --bind date:l:1774562374470 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"How is your day going" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18154684363 --bind date:l:1752994896809 --bind date_sent:l:1752994896809 --bind type:i:2 --bind body:s:"I am at the store need anything" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18154684363 --bind date:l:1766463478841 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18154684363 --bind date:l:1761691426910 --bind date_sent:l:1761691426910 --bind type:i:2 --bind body:s:"Let me know when you are ready" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18154684363 --bind date:l:1772534265899 --bind date_sent:l:1772534265899 --bind type:i:2 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15442526520 --bind date:l:1742312346275 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Your mom called call her back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15442526520 --bind date:l:1763504088497 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just landed will call soon" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14958935588 --bind date:l:1761585597712 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just sent you the photos" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14958935588 --bind date:l:1758346967295 --bind date_sent:l:1758346967295 --bind type:i:2 --bind body:s:"Can you call me back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+14958935588 --bind date:l:1754366003000 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"The package arrived today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17733373669 --bind date:l:1741737072467 --bind date_sent:l:1741737072467 --bind type:i:2 --bind body:s:"Hey are you free tonight" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17733373669 --bind date:l:1772893839991 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Just finished work heading home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17733373669 --bind date:l:1771781280426 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Congrats on the promotion" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18194945180 --bind date:l:1748207652585 --bind date_sent:l:1748207652585 --bind type:i:2 --bind body:s:"WiFi password sunshine2024" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18194945180 --bind date:l:1773014929587 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18194945180 --bind date:l:1753005788132 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Your mom called call her back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+18194945180 --bind date:l:1773219007003 --bind date_sent:l:1773219007003 --bind type:i:2 --bind body:s:"Did you see the game" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13227654625 --bind date:l:1760777392745 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"The package arrived today" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+13227654625 --bind date:l:1755570403870 --bind date_sent:l:1755570403870 --bind type:i:2 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16919499916 --bind date:l:1767894673569 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Need to reschedule lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16919499916 --bind date:l:1753058617386 --bind date_sent:l:1753058617386 --bind type:i:2 --bind body:s:"Your mom called call her back" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+16919499916 --bind date:l:1772264353496 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Running 10 mins late" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15588894609 --bind date:l:1767414122100 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+15588894609 --bind date:l:1755243040359 --bind date_sent:l:1755243040359 --bind type:i:2 --bind body:s:"I am at the store need anything" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17508764349 --bind date:l:1759000655799 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Want to grab lunch" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17508764349 --bind date:l:1764041951936 --bind date_sent:l:1764041951936 --bind type:i:2 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17508764349 --bind date:l:1745271210716 --bind date_sent:l:1745271210716 --bind type:i:2 --bind body:s:"Pick up milk on the way home" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17462119749 --bind date:l:1765504247610 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Got your message" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17462119749 --bind date:l:1758475387212 --bind date_sent:l:1758475387212 --bind type:i:2 --bind body:s:"Still on for tomorrow" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17462119749 --bind date:l:1749301236596 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Happy birthday" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://sms --bind address:s:+17462119749 --bind date:l:1759538096583 --bind date_sent:l:0 --bind type:i:1 --bind body:s:"Congrats on the promotion" --bind read:i:1 --bind seen:i:1 2>/dev/null
COUNT=$((COUNT + 1))

echo "Done: $COUNT SMS messages at $(date)" >> $LOG
echo "SMS_DONE_$COUNT"
