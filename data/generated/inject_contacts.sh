#!/system/bin/sh
# Inject 500 contacts via content insert
# Run as: nohup sh /data/local/tmp/inject_contacts.sh > /data/local/tmp/inject_contacts.log 2>&1 &
LOG=/data/local/tmp/inject_contacts.log
echo "Starting contact injection at $(date)" > $LOG
COUNT=0

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Christian White" --bind data2:s:"Christian" --bind data3:s:"White" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13339158919" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"christian.white94@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Brandon Kim" --bind data2:s:"Brandon" --bind data3:s:"Kim" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19464074985" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Samantha Anderson" --bind data2:s:"Samantha" --bind data3:s:"Anderson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15946441408" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Vincent Baker" --bind data2:s:"Vincent" --bind data3:s:"Baker" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13458398593" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"vincent.baker58@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Margaret Howard" --bind data2:s:"Margaret" --bind data3:s:"Howard" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14404318726" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Louis Phillips" --bind data2:s:"Louis" --bind data3:s:"Phillips" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19479241069" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"louis.phillips48@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Joshua Carter" --bind data2:s:"Joshua" --bind data3:s:"Carter" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18925537858" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Elizabeth Reyes" --bind data2:s:"Elizabeth" --bind data3:s:"Reyes" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14493136871" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Gary Lopez" --bind data2:s:"Gary" --bind data3:s:"Lopez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19628639235" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Benjamin Rogers" --bind data2:s:"Benjamin" --bind data3:s:"Rogers" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16918202012" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"benjamin.rogers75@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Albert Phillips" --bind data2:s:"Albert" --bind data3:s:"Phillips" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12443338292" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"albert.phillips83@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Scott Lewis" --bind data2:s:"Scott" --bind data3:s:"Lewis" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17708478024" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"scott.lewis3@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Ashley Turner" --bind data2:s:"Ashley" --bind data3:s:"Turner" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14302478624" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Sandra Howard" --bind data2:s:"Sandra" --bind data3:s:"Howard" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18039298143" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"sandra.howard12@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Daniel Wilson" --bind data2:s:"Daniel" --bind data3:s:"Wilson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13564236544" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Eric Gonzalez" --bind data2:s:"Eric" --bind data3:s:"Gonzalez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15198295207" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Henry White" --bind data2:s:"Henry" --bind data3:s:"White" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14128074650" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Dennis Rivera" --bind data2:s:"Dennis" --bind data3:s:"Rivera" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13157537990" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Gabriel Roberts" --bind data2:s:"Gabriel" --bind data3:s:"Roberts" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13293765458" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Larry Kim" --bind data2:s:"Larry" --bind data3:s:"Kim" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18719582389" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Larry Evans" --bind data2:s:"Larry" --bind data3:s:"Evans" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17536283746" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Laura Thompson" --bind data2:s:"Laura" --bind data3:s:"Thompson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14626991725" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Benjamin Edwards" --bind data2:s:"Benjamin" --bind data3:s:"Edwards" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16713498616" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Patricia Morgan" --bind data2:s:"Patricia" --bind data3:s:"Morgan" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17358825849" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Karen Carter" --bind data2:s:"Karen" --bind data3:s:"Carter" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16962161011" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"karen.carter9@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Margaret Williams" --bind data2:s:"Margaret" --bind data3:s:"Williams" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12627431784" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Kyle Reed" --bind data2:s:"Kyle" --bind data3:s:"Reed" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16509562590" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Brian Hernandez" --bind data2:s:"Brian" --bind data3:s:"Hernandez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16539777118" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Carol Perez" --bind data2:s:"Carol" --bind data3:s:"Perez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16988093097" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Sean Lee" --bind data2:s:"Sean" --bind data3:s:"Lee" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19653942219" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Dennis Bailey" --bind data2:s:"Dennis" --bind data3:s:"Bailey" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12146965288" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"dennis.bailey13@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Vincent Cox" --bind data2:s:"Vincent" --bind data3:s:"Cox" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15216503647" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Gregory Williams" --bind data2:s:"Gregory" --bind data3:s:"Williams" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12928254922" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Douglas Mitchell" --bind data2:s:"Douglas" --bind data3:s:"Mitchell" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16142566851" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"douglas.mitchell27@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Gary Garcia" --bind data2:s:"Gary" --bind data3:s:"Garcia" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19768001656" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"gary.garcia79@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Thomas Thomas" --bind data2:s:"Thomas" --bind data3:s:"Thomas" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19273276795" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Andrew Morgan" --bind data2:s:"Andrew" --bind data3:s:"Morgan" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15786312976" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Eugene Harris" --bind data2:s:"Eugene" --bind data3:s:"Harris" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15219645228" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Dorothy Gutierrez" --bind data2:s:"Dorothy" --bind data3:s:"Gutierrez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18002239687" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"dorothy.gutierrez3@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Benjamin Turner" --bind data2:s:"Benjamin" --bind data3:s:"Turner" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13484468160" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Jacob Reyes" --bind data2:s:"Jacob" --bind data3:s:"Reyes" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16775699750" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Frank Brown" --bind data2:s:"Frank" --bind data3:s:"Brown" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14912312257" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Michelle Lopez" --bind data2:s:"Michelle" --bind data3:s:"Lopez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13474703546" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"michelle.lopez13@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Amy Hill" --bind data2:s:"Amy" --bind data3:s:"Hill" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15147271680" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Harold Edwards" --bind data2:s:"Harold" --bind data3:s:"Edwards" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18702778829" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Sarah Wilson" --bind data2:s:"Sarah" --bind data3:s:"Wilson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15167787928" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Amanda Hall" --bind data2:s:"Amanda" --bind data3:s:"Hall" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13424407983" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"amanda.hall68@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Susan Bailey" --bind data2:s:"Susan" --bind data3:s:"Bailey" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12367328724" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Rachel Roberts" --bind data2:s:"Rachel" --bind data3:s:"Roberts" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13147198356" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"rachel.roberts79@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Amanda Edwards" --bind data2:s:"Amanda" --bind data3:s:"Edwards" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12107514846" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Stephen Gutierrez" --bind data2:s:"Stephen" --bind data3:s:"Gutierrez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12293748445" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Bruce Kelly" --bind data2:s:"Bruce" --bind data3:s:"Kelly" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16467387409" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"bruce.kelly72@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Emily Parker" --bind data2:s:"Emily" --bind data3:s:"Parker" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13443979173" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Juan Flores" --bind data2:s:"Juan" --bind data3:s:"Flores" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14832476525" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Mary Kim" --bind data2:s:"Mary" --bind data3:s:"Kim" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18205846636" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Jerry Green" --bind data2:s:"Jerry" --bind data3:s:"Green" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12833331984" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"jerry.green45@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Edward Wilson" --bind data2:s:"Edward" --bind data3:s:"Wilson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13217708747" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Christian Lewis" --bind data2:s:"Christian" --bind data3:s:"Lewis" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15785697168" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"christian.lewis1@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Austin Collins" --bind data2:s:"Austin" --bind data3:s:"Collins" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12236516110" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Terry Martin" --bind data2:s:"Terry" --bind data3:s:"Martin" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13438795757" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Emma Perez" --bind data2:s:"Emma" --bind data3:s:"Perez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14323019188" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"emma.perez19@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Lawrence Kim" --bind data2:s:"Lawrence" --bind data3:s:"Kim" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19003706855" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"lawrence.kim76@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Kevin Richardson" --bind data2:s:"Kevin" --bind data3:s:"Richardson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18497469077" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Gary Gonzalez" --bind data2:s:"Gary" --bind data3:s:"Gonzalez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14639274531" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"gary.gonzalez77@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Mason Jones" --bind data2:s:"Mason" --bind data3:s:"Jones" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18499564767" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Ashley Anderson" --bind data2:s:"Ashley" --bind data3:s:"Anderson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17334538721" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Keith Parker" --bind data2:s:"Keith" --bind data3:s:"Parker" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14208087353" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Kimberly Walker" --bind data2:s:"Kimberly" --bind data3:s:"Walker" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15655961435" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Christian Walker" --bind data2:s:"Christian" --bind data3:s:"Walker" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18608638223" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Ralph Taylor" --bind data2:s:"Ralph" --bind data3:s:"Taylor" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18352487682" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Ronald Gonzalez" --bind data2:s:"Ronald" --bind data3:s:"Gonzalez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18362225320" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Roy Edwards" --bind data2:s:"Roy" --bind data3:s:"Edwards" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13459245208" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Peter Gutierrez" --bind data2:s:"Peter" --bind data3:s:"Gutierrez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19114793511" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Daniel Rivera" --bind data2:s:"Daniel" --bind data3:s:"Rivera" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17277027176" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"daniel.rivera40@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Margaret Sanchez" --bind data2:s:"Margaret" --bind data3:s:"Sanchez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17603182050" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Kathleen Moore" --bind data2:s:"Kathleen" --bind data3:s:"Moore" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14213951450" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Kyle Adams" --bind data2:s:"Kyle" --bind data3:s:"Adams" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17828242989" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"kyle.adams22@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Joshua Wilson" --bind data2:s:"Joshua" --bind data3:s:"Wilson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18307358520" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Jennifer Moore" --bind data2:s:"Jennifer" --bind data3:s:"Moore" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18206381745" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Kimberly Wright" --bind data2:s:"Kimberly" --bind data3:s:"Wright" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13382237864" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Nathan Reed" --bind data2:s:"Nathan" --bind data3:s:"Reed" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16672864280" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Sean Jackson" --bind data2:s:"Sean" --bind data3:s:"Jackson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13767502191" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"sean.jackson86@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Justin Young" --bind data2:s:"Justin" --bind data3:s:"Young" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16476371400" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Wayne Hall" --bind data2:s:"Wayne" --bind data3:s:"Hall" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12209565298" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"wayne.hall37@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Mason Cruz" --bind data2:s:"Mason" --bind data3:s:"Cruz" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17546566642" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Amy Gomez" --bind data2:s:"Amy" --bind data3:s:"Gomez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18458731417" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"amy.gomez35@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Sean Martinez" --bind data2:s:"Sean" --bind data3:s:"Martinez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18919951773" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"George Flores" --bind data2:s:"George" --bind data3:s:"Flores" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15082783667" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Nancy Reed" --bind data2:s:"Nancy" --bind data3:s:"Reed" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12353383605" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Willie Clark" --bind data2:s:"Willie" --bind data3:s:"Clark" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14536781836" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Matthew Taylor" --bind data2:s:"Matthew" --bind data3:s:"Taylor" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16267628937" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Willie Howard" --bind data2:s:"Willie" --bind data3:s:"Howard" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14792483797" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"James Rivera" --bind data2:s:"James" --bind data3:s:"Rivera" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18695934806" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Kenneth Cox" --bind data2:s:"Kenneth" --bind data3:s:"Cox" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13023197852" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"kenneth.cox58@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Catherine Morales" --bind data2:s:"Catherine" --bind data3:s:"Morales" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18778076805" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"catherine.morales97@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Linda Jackson" --bind data2:s:"Linda" --bind data3:s:"Jackson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17407213279" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"linda.jackson91@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Peter Nguyen" --bind data2:s:"Peter" --bind data3:s:"Nguyen" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12754732958" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"peter.nguyen84@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Benjamin Phillips" --bind data2:s:"Benjamin" --bind data3:s:"Phillips" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18257363857" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"benjamin.phillips80@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Arthur Davis" --bind data2:s:"Arthur" --bind data3:s:"Davis" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12927247765" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"arthur.davis93@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Christopher Evans" --bind data2:s:"Christopher" --bind data3:s:"Evans" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14845321183" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"christopher.evans82@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Justin Reed" --bind data2:s:"Justin" --bind data3:s:"Reed" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17349775523" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"justin.reed66@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Austin Wright" --bind data2:s:"Austin" --bind data3:s:"Wright" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18547782314" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Barbara Campbell" --bind data2:s:"Barbara" --bind data3:s:"Campbell" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16033713393" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"barbara.campbell1@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Sandra Ramos" --bind data2:s:"Sandra" --bind data3:s:"Ramos" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14466818870" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Carolyn Rodriguez" --bind data2:s:"Carolyn" --bind data3:s:"Rodriguez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17505123447" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Peter Peterson" --bind data2:s:"Peter" --bind data3:s:"Peterson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16295007818" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Terry Ortiz" --bind data2:s:"Terry" --bind data3:s:"Ortiz" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17274723664" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Christine Baker" --bind data2:s:"Christine" --bind data3:s:"Baker" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16769434536" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"christine.baker47@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Charles Rivera" --bind data2:s:"Charles" --bind data3:s:"Rivera" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15226466563" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"charles.rivera87@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Larry Turner" --bind data2:s:"Larry" --bind data3:s:"Turner" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16995243772" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"larry.turner65@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Roger Martin" --bind data2:s:"Roger" --bind data3:s:"Martin" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16675672038" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"roger.martin43@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Russell Hall" --bind data2:s:"Russell" --bind data3:s:"Hall" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13726457827" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Richard Scott" --bind data2:s:"Richard" --bind data3:s:"Scott" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19376817142" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Debra Walker" --bind data2:s:"Debra" --bind data3:s:"Walker" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15734834253" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Elijah Torres" --bind data2:s:"Elijah" --bind data3:s:"Torres" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15865348233" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"elijah.torres5@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Deborah Nguyen" --bind data2:s:"Deborah" --bind data3:s:"Nguyen" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16735603110" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"deborah.nguyen60@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Helen Moore" --bind data2:s:"Helen" --bind data3:s:"Moore" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15554528740" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"helen.moore76@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Timothy Jackson" --bind data2:s:"Timothy" --bind data3:s:"Jackson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18825986519" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Logan Rivera" --bind data2:s:"Logan" --bind data3:s:"Rivera" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14645881158" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"James Wilson" --bind data2:s:"James" --bind data3:s:"Wilson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18503906371" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"james.wilson10@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Roger Hernandez" --bind data2:s:"Roger" --bind data3:s:"Hernandez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16454397236" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Harold Ramos" --bind data2:s:"Harold" --bind data3:s:"Ramos" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14705358175" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"harold.ramos34@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Billy Robinson" --bind data2:s:"Billy" --bind data3:s:"Robinson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17016184258" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Gregory Martin" --bind data2:s:"Gregory" --bind data3:s:"Martin" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16503418839" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"gregory.martin33@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Angela Young" --bind data2:s:"Angela" --bind data3:s:"Young" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12636372570" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"angela.young90@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Alexander Baker" --bind data2:s:"Alexander" --bind data3:s:"Baker" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17172972787" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Adam Thompson" --bind data2:s:"Adam" --bind data3:s:"Thompson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16137113723" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Dennis Lee" --bind data2:s:"Dennis" --bind data3:s:"Lee" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12117617367" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Terry Diaz" --bind data2:s:"Terry" --bind data3:s:"Diaz" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16786686482" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Jeremy Bailey" --bind data2:s:"Jeremy" --bind data3:s:"Bailey" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19754915807" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Laura Flores" --bind data2:s:"Laura" --bind data3:s:"Flores" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12602121503" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Amy Kim" --bind data2:s:"Amy" --bind data3:s:"Kim" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16209664077" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Anthony Cooper" --bind data2:s:"Anthony" --bind data3:s:"Cooper" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15006649414" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Wayne Howard" --bind data2:s:"Wayne" --bind data3:s:"Howard" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12703964415" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Carolyn Allen" --bind data2:s:"Carolyn" --bind data3:s:"Allen" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12035186556" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Bobby Jones" --bind data2:s:"Bobby" --bind data3:s:"Jones" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19039574758" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"bobby.jones41@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Nicole Miller" --bind data2:s:"Nicole" --bind data3:s:"Miller" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18898657764" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"nicole.miller74@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Benjamin Hernandez" --bind data2:s:"Benjamin" --bind data3:s:"Hernandez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15135318528" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Bruce Gomez" --bind data2:s:"Bruce" --bind data3:s:"Gomez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18353963603" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"bruce.gomez94@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Brian Cook" --bind data2:s:"Brian" --bind data3:s:"Cook" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18292691806" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"brian.cook7@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Barbara Perez" --bind data2:s:"Barbara" --bind data3:s:"Perez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13643149872" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Jesse Lee" --bind data2:s:"Jesse" --bind data3:s:"Lee" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16049452397" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Amy Kelly" --bind data2:s:"Amy" --bind data3:s:"Kelly" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19638098079" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Dorothy Martinez" --bind data2:s:"Dorothy" --bind data3:s:"Martinez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17708156041" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Amy Morales" --bind data2:s:"Amy" --bind data3:s:"Morales" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18132049517" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Daniel Evans" --bind data2:s:"Daniel" --bind data3:s:"Evans" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13519679026" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"daniel.evans64@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Ashley Kim" --bind data2:s:"Ashley" --bind data3:s:"Kim" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13259387274" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"John Collins" --bind data2:s:"John" --bind data3:s:"Collins" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16649487017" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Lisa Carter" --bind data2:s:"Lisa" --bind data3:s:"Carter" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12745624421" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"lisa.carter65@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Harold Wright" --bind data2:s:"Harold" --bind data3:s:"Wright" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17896555628" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Lisa Scott" --bind data2:s:"Lisa" --bind data3:s:"Scott" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13652713888" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Richard Hill" --bind data2:s:"Richard" --bind data3:s:"Hill" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13523467542" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Jack Morris" --bind data2:s:"Jack" --bind data3:s:"Morris" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12378323298" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Amanda Anderson" --bind data2:s:"Amanda" --bind data3:s:"Anderson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16505677125" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"amanda.anderson23@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Emily Peterson" --bind data2:s:"Emily" --bind data3:s:"Peterson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14694243568" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"emily.peterson47@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Jeremy Jones" --bind data2:s:"Jeremy" --bind data3:s:"Jones" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15672667244" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"jeremy.jones32@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Linda Diaz" --bind data2:s:"Linda" --bind data3:s:"Diaz" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12065799791" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Brandon Lopez" --bind data2:s:"Brandon" --bind data3:s:"Lopez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15023307711" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Mason Johnson" --bind data2:s:"Mason" --bind data3:s:"Johnson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16287616852" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"mason.johnson88@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Sharon Ramirez" --bind data2:s:"Sharon" --bind data3:s:"Ramirez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12285911053" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"sharon.ramirez24@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Andrew Ward" --bind data2:s:"Andrew" --bind data3:s:"Ward" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14357024291" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"andrew.ward79@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Sandra Evans" --bind data2:s:"Sandra" --bind data3:s:"Evans" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19576888693" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Nathan Martinez" --bind data2:s:"Nathan" --bind data3:s:"Martinez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17265817104" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Matthew Nelson" --bind data2:s:"Matthew" --bind data3:s:"Nelson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17007146460" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"matthew.nelson21@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Angela Walker" --bind data2:s:"Angela" --bind data3:s:"Walker" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14934842384" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"angela.walker48@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Deborah Flores" --bind data2:s:"Deborah" --bind data3:s:"Flores" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18969646085" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"deborah.flores79@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"William King" --bind data2:s:"William" --bind data3:s:"King" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17882614881" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"william.king98@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"John Allen" --bind data2:s:"John" --bind data3:s:"Allen" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16519056641" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Bobby Williams" --bind data2:s:"Bobby" --bind data3:s:"Williams" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18537979584" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Roy Williams" --bind data2:s:"Roy" --bind data3:s:"Williams" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17508691642" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Eric Brown" --bind data2:s:"Eric" --bind data3:s:"Brown" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12637948657" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"eric.brown62@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Carol Jackson" --bind data2:s:"Carol" --bind data3:s:"Jackson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17002525724" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"carol.jackson51@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Brandon Scott" --bind data2:s:"Brandon" --bind data3:s:"Scott" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18614665625" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Joshua Morris" --bind data2:s:"Joshua" --bind data3:s:"Morris" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18048335702" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"joshua.morris13@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Keith Lee" --bind data2:s:"Keith" --bind data3:s:"Lee" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13468701363" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"keith.lee60@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Angela Rogers" --bind data2:s:"Angela" --bind data3:s:"Rogers" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17433179516" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Gerald Nguyen" --bind data2:s:"Gerald" --bind data3:s:"Nguyen" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18887868646" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Sandra Cruz" --bind data2:s:"Sandra" --bind data3:s:"Cruz" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13073995583" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Karen Flores" --bind data2:s:"Karen" --bind data3:s:"Flores" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14016937740" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Ronald Clark" --bind data2:s:"Ronald" --bind data3:s:"Clark" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13785927389" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Henry Walker" --bind data2:s:"Henry" --bind data3:s:"Walker" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12397735946" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Richard Evans" --bind data2:s:"Richard" --bind data3:s:"Evans" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13782642092" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Walter Morris" --bind data2:s:"Walter" --bind data3:s:"Morris" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14193812756" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"walter.morris55@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Christopher Hill" --bind data2:s:"Christopher" --bind data3:s:"Hill" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14977332449" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Richard Perez" --bind data2:s:"Richard" --bind data3:s:"Perez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17949534904" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"richard.perez95@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Eric Smith" --bind data2:s:"Eric" --bind data3:s:"Smith" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17215685780" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"eric.smith68@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Joshua Young" --bind data2:s:"Joshua" --bind data3:s:"Young" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13826104762" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Thomas Campbell" --bind data2:s:"Thomas" --bind data3:s:"Campbell" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16942508206" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"thomas.campbell3@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Jeremy Morales" --bind data2:s:"Jeremy" --bind data3:s:"Morales" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16284525068" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Joseph Collins" --bind data2:s:"Joseph" --bind data3:s:"Collins" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15046747240" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Russell Walker" --bind data2:s:"Russell" --bind data3:s:"Walker" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16587065166" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Joseph Howard" --bind data2:s:"Joseph" --bind data3:s:"Howard" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18768133633" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Nicholas Adams" --bind data2:s:"Nicholas" --bind data3:s:"Adams" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16387051329" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Billy Taylor" --bind data2:s:"Billy" --bind data3:s:"Taylor" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19252446900" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"billy.taylor76@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Elijah Walker" --bind data2:s:"Elijah" --bind data3:s:"Walker" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13912499901" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Joshua White" --bind data2:s:"Joshua" --bind data3:s:"White" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17528459146" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Logan Smith" --bind data2:s:"Logan" --bind data3:s:"Smith" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17103838777" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Nicole Robinson" --bind data2:s:"Nicole" --bind data3:s:"Robinson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16787579748" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"nicole.robinson49@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Emma Thomas" --bind data2:s:"Emma" --bind data3:s:"Thomas" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18807527051" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Aaron Nelson" --bind data2:s:"Aaron" --bind data3:s:"Nelson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18266978474" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"aaron.nelson17@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Keith Rivera" --bind data2:s:"Keith" --bind data3:s:"Rivera" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15369171000" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"keith.rivera69@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Jerry Kim" --bind data2:s:"Jerry" --bind data3:s:"Kim" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16393029133" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"jerry.kim51@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Rebecca Clark" --bind data2:s:"Rebecca" --bind data3:s:"Clark" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15659971096" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"rebecca.clark39@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Laura Adams" --bind data2:s:"Laura" --bind data3:s:"Adams" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13182085439" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Nicole Taylor" --bind data2:s:"Nicole" --bind data3:s:"Taylor" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18444653259" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Helen Morris" --bind data2:s:"Helen" --bind data3:s:"Morris" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17385397171" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"helen.morris15@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Edward Jackson" --bind data2:s:"Edward" --bind data3:s:"Jackson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13414324938" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Nicholas Ramos" --bind data2:s:"Nicholas" --bind data3:s:"Ramos" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13879542702" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"nicholas.ramos13@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Dylan Morales" --bind data2:s:"Dylan" --bind data3:s:"Morales" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14964671865" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"David Mitchell" --bind data2:s:"David" --bind data3:s:"Mitchell" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15707446932" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Nathan Ramirez" --bind data2:s:"Nathan" --bind data3:s:"Ramirez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13584445529" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Rachel Diaz" --bind data2:s:"Rachel" --bind data3:s:"Diaz" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16626074416" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"rachel.diaz41@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Kenneth Thomas" --bind data2:s:"Kenneth" --bind data3:s:"Thomas" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14838221563" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Arthur Gomez" --bind data2:s:"Arthur" --bind data3:s:"Gomez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19757259444" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Walter Flores" --bind data2:s:"Walter" --bind data3:s:"Flores" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16068867967" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Angela Ward" --bind data2:s:"Angela" --bind data3:s:"Ward" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18733266126" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Charles Stewart" --bind data2:s:"Charles" --bind data3:s:"Stewart" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15632862661" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Jeremy Ramirez" --bind data2:s:"Jeremy" --bind data3:s:"Ramirez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17366944378" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Frank Morris" --bind data2:s:"Frank" --bind data3:s:"Morris" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13547737463" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Randy Garcia" --bind data2:s:"Randy" --bind data3:s:"Garcia" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16447709428" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Alan Flores" --bind data2:s:"Alan" --bind data3:s:"Flores" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15128424977" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"alan.flores97@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Patricia Collins" --bind data2:s:"Patricia" --bind data3:s:"Collins" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19688064708" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Donald Young" --bind data2:s:"Donald" --bind data3:s:"Young" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16005333738" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"donald.young84@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Benjamin Torres" --bind data2:s:"Benjamin" --bind data3:s:"Torres" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16763998416" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Benjamin Ramos" --bind data2:s:"Benjamin" --bind data3:s:"Ramos" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18484251769" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Nathan Richardson" --bind data2:s:"Nathan" --bind data3:s:"Richardson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13779604214" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"nathan.richardson52@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Bruce Gutierrez" --bind data2:s:"Bruce" --bind data3:s:"Gutierrez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15224879614" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Austin Thompson" --bind data2:s:"Austin" --bind data3:s:"Thompson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13599146458" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"austin.thompson46@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Mason Richardson" --bind data2:s:"Mason" --bind data3:s:"Richardson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18529559019" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"William Torres" --bind data2:s:"William" --bind data3:s:"Torres" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12857083048" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Aaron Stewart" --bind data2:s:"Aaron" --bind data3:s:"Stewart" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12168377065" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"aaron.stewart31@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Samuel Sanchez" --bind data2:s:"Samuel" --bind data3:s:"Sanchez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18574292271" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"samuel.sanchez26@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Barbara Lewis" --bind data2:s:"Barbara" --bind data3:s:"Lewis" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12277534739" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Eugene King" --bind data2:s:"Eugene" --bind data3:s:"King" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19468945167" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"eugene.king81@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Kenneth Bailey" --bind data2:s:"Kenneth" --bind data3:s:"Bailey" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13605005813" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"kenneth.bailey83@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Kimberly Green" --bind data2:s:"Kimberly" --bind data3:s:"Green" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19732444630" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Mary Howard" --bind data2:s:"Mary" --bind data3:s:"Howard" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15412321859" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Vincent Richardson" --bind data2:s:"Vincent" --bind data3:s:"Richardson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19794708769" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"vincent.richardson42@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Betty Jackson" --bind data2:s:"Betty" --bind data3:s:"Jackson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19772192851" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"betty.jackson58@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Elizabeth Adams" --bind data2:s:"Elizabeth" --bind data3:s:"Adams" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18023991264" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"elizabeth.adams26@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Andrew Green" --bind data2:s:"Andrew" --bind data3:s:"Green" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13373191505" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"andrew.green52@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Kevin Adams" --bind data2:s:"Kevin" --bind data3:s:"Adams" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19347445120" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"kevin.adams36@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Terry Collins" --bind data2:s:"Terry" --bind data3:s:"Collins" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12053225712" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Timothy Torres" --bind data2:s:"Timothy" --bind data3:s:"Torres" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15702658635" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"timothy.torres56@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Jessica Scott" --bind data2:s:"Jessica" --bind data3:s:"Scott" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18854173598" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Nicholas Hernandez" --bind data2:s:"Nicholas" --bind data3:s:"Hernandez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19289496705" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Nancy Ward" --bind data2:s:"Nancy" --bind data3:s:"Ward" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19828731639" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Anthony Morales" --bind data2:s:"Anthony" --bind data3:s:"Morales" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14965065901" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Michelle Garcia" --bind data2:s:"Michelle" --bind data3:s:"Garcia" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12823815006" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Linda Ward" --bind data2:s:"Linda" --bind data3:s:"Ward" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19877625737" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Matthew Baker" --bind data2:s:"Matthew" --bind data3:s:"Baker" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18688303506" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"matthew.baker77@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Michael Torres" --bind data2:s:"Michael" --bind data3:s:"Torres" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15028215322" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"michael.torres99@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Mason Sanchez" --bind data2:s:"Mason" --bind data3:s:"Sanchez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14145689687" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Sharon Stewart" --bind data2:s:"Sharon" --bind data3:s:"Stewart" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16748517387" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"sharon.stewart45@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Karen Turner" --bind data2:s:"Karen" --bind data3:s:"Turner" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15124261264" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Elijah Phillips" --bind data2:s:"Elijah" --bind data3:s:"Phillips" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18873199218" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Cynthia Moore" --bind data2:s:"Cynthia" --bind data3:s:"Moore" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15648217182" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"cynthia.moore50@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Debra Parker" --bind data2:s:"Debra" --bind data3:s:"Parker" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14105437179" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"James Nguyen" --bind data2:s:"James" --bind data3:s:"Nguyen" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13564916621" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Zachary Clark" --bind data2:s:"Zachary" --bind data3:s:"Clark" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15927384360" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Daniel King" --bind data2:s:"Daniel" --bind data3:s:"King" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17822016692" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"daniel.king88@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Maria Flores" --bind data2:s:"Maria" --bind data3:s:"Flores" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18197567096" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Wayne Evans" --bind data2:s:"Wayne" --bind data3:s:"Evans" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12104505836" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Gabriel Harris" --bind data2:s:"Gabriel" --bind data3:s:"Harris" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13633883916" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"gabriel.harris30@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Rebecca Rogers" --bind data2:s:"Rebecca" --bind data3:s:"Rogers" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15733223920" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"rebecca.rogers80@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Sharon Rivera" --bind data2:s:"Sharon" --bind data3:s:"Rivera" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16423802762" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"sharon.rivera12@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Carol Allen" --bind data2:s:"Carol" --bind data3:s:"Allen" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14197195181" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Karen Edwards" --bind data2:s:"Karen" --bind data3:s:"Edwards" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12967252565" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"karen.edwards23@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Kevin King" --bind data2:s:"Kevin" --bind data3:s:"King" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19132084116" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Sharon Miller" --bind data2:s:"Sharon" --bind data3:s:"Miller" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12136466339" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Terry Bailey" --bind data2:s:"Terry" --bind data3:s:"Bailey" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16197841322" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"terry.bailey90@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Brian Carter" --bind data2:s:"Brian" --bind data3:s:"Carter" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13972661503" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Sandra Scott" --bind data2:s:"Sandra" --bind data3:s:"Scott" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17997291894" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Edward Gonzalez" --bind data2:s:"Edward" --bind data3:s:"Gonzalez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18843293046" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Jessica Cooper" --bind data2:s:"Jessica" --bind data3:s:"Cooper" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12647876915" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Ryan Lopez" --bind data2:s:"Ryan" --bind data3:s:"Lopez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15973619244" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Elizabeth Ward" --bind data2:s:"Elizabeth" --bind data3:s:"Ward" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18493736248" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Amy Phillips" --bind data2:s:"Amy" --bind data3:s:"Phillips" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17543299242" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"amy.phillips89@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Linda Anderson" --bind data2:s:"Linda" --bind data3:s:"Anderson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15487401933" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"linda.anderson60@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Joshua Davis" --bind data2:s:"Joshua" --bind data3:s:"Davis" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14815628930" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Kathleen Scott" --bind data2:s:"Kathleen" --bind data3:s:"Scott" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17506241324" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"kathleen.scott87@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Kathleen Cooper" --bind data2:s:"Kathleen" --bind data3:s:"Cooper" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14823203738" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"kathleen.cooper2@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Catherine Miller" --bind data2:s:"Catherine" --bind data3:s:"Miller" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19828223665" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Ryan Taylor" --bind data2:s:"Ryan" --bind data3:s:"Taylor" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12875371633" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"ryan.taylor39@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Nicole Harris" --bind data2:s:"Nicole" --bind data3:s:"Harris" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12519276119" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Gabriel Perez" --bind data2:s:"Gabriel" --bind data3:s:"Perez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16635231043" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Stephen Wright" --bind data2:s:"Stephen" --bind data3:s:"Wright" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17755662113" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Stephen Evans" --bind data2:s:"Stephen" --bind data3:s:"Evans" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15095957133" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Patrick Roberts" --bind data2:s:"Patrick" --bind data3:s:"Roberts" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13732602110" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Carolyn Peterson" --bind data2:s:"Carolyn" --bind data3:s:"Peterson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18663341110" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"carolyn.peterson98@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"William Carter" --bind data2:s:"William" --bind data3:s:"Carter" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15588099240" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Laura Rivera" --bind data2:s:"Laura" --bind data3:s:"Rivera" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13805406747" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Carolyn Rivera" --bind data2:s:"Carolyn" --bind data3:s:"Rivera" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14877206850" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Karen Collins" --bind data2:s:"Karen" --bind data3:s:"Collins" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17689811419" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Katherine Bailey" --bind data2:s:"Katherine" --bind data3:s:"Bailey" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14146657227" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Deborah Phillips" --bind data2:s:"Deborah" --bind data3:s:"Phillips" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16172253102" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"deborah.phillips96@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Edward Hall" --bind data2:s:"Edward" --bind data3:s:"Hall" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14202404295" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Alan Campbell" --bind data2:s:"Alan" --bind data3:s:"Campbell" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19293412418" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"alan.campbell18@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Susan Reyes" --bind data2:s:"Susan" --bind data3:s:"Reyes" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15138422761" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"susan.reyes55@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Edward Kelly" --bind data2:s:"Edward" --bind data3:s:"Kelly" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15585598109" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Steven Morales" --bind data2:s:"Steven" --bind data3:s:"Morales" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12573568115" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"steven.morales67@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"David Richardson" --bind data2:s:"David" --bind data3:s:"Richardson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19125613019" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Anthony Roberts" --bind data2:s:"Anthony" --bind data3:s:"Roberts" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16245689665" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Christian Parker" --bind data2:s:"Christian" --bind data3:s:"Parker" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12506776832" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Jennifer Diaz" --bind data2:s:"Jennifer" --bind data3:s:"Diaz" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18573216835" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Lawrence Martinez" --bind data2:s:"Lawrence" --bind data3:s:"Martinez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17753249455" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Donald Williams" --bind data2:s:"Donald" --bind data3:s:"Williams" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19386234478" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Roy Clark" --bind data2:s:"Roy" --bind data3:s:"Clark" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15489282137" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Gerald Thomas" --bind data2:s:"Gerald" --bind data3:s:"Thomas" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14457129640" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Jeffrey Nguyen" --bind data2:s:"Jeffrey" --bind data3:s:"Nguyen" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12585011539" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Brian Thompson" --bind data2:s:"Brian" --bind data3:s:"Thompson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16716715502" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Frank Jones" --bind data2:s:"Frank" --bind data3:s:"Jones" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16342871698" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Ralph Thomas" --bind data2:s:"Ralph" --bind data3:s:"Thomas" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17279627706" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Michael Taylor" --bind data2:s:"Michael" --bind data3:s:"Taylor" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14935982606" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Jonathan Martinez" --bind data2:s:"Jonathan" --bind data3:s:"Martinez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18883064440" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"jonathan.martinez21@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Timothy Cox" --bind data2:s:"Timothy" --bind data3:s:"Cox" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17202705445" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Jeffrey Wilson" --bind data2:s:"Jeffrey" --bind data3:s:"Wilson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18104957169" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Randy Sanchez" --bind data2:s:"Randy" --bind data3:s:"Sanchez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13757995245" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Samuel Stewart" --bind data2:s:"Samuel" --bind data3:s:"Stewart" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14628156982" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Mark Thompson" --bind data2:s:"Mark" --bind data3:s:"Thompson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13779246647" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"mark.thompson92@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Joseph Rivera" --bind data2:s:"Joseph" --bind data3:s:"Rivera" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15595916652" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Cynthia Reed" --bind data2:s:"Cynthia" --bind data3:s:"Reed" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16059119159" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Kimberly Lee" --bind data2:s:"Kimberly" --bind data3:s:"Lee" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16848471122" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Samantha Rivera" --bind data2:s:"Samantha" --bind data3:s:"Rivera" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16574842536" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"samantha.rivera67@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Barbara Gonzalez" --bind data2:s:"Barbara" --bind data3:s:"Gonzalez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19776177054" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Carol Thomas" --bind data2:s:"Carol" --bind data3:s:"Thomas" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15494909701" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Carolyn Harris" --bind data2:s:"Carolyn" --bind data3:s:"Harris" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18322367012" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Thomas Edwards" --bind data2:s:"Thomas" --bind data3:s:"Edwards" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17409464307" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"thomas.edwards87@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Sandra Diaz" --bind data2:s:"Sandra" --bind data3:s:"Diaz" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17348718537" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Stephen Kim" --bind data2:s:"Stephen" --bind data3:s:"Kim" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16412441005" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"stephen.kim10@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Walter Sanchez" --bind data2:s:"Walter" --bind data3:s:"Sanchez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17417235360" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Margaret Cook" --bind data2:s:"Margaret" --bind data3:s:"Cook" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12029905716" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Deborah Cook" --bind data2:s:"Deborah" --bind data3:s:"Cook" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14899176520" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Melissa Lopez" --bind data2:s:"Melissa" --bind data3:s:"Lopez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12566236107" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Peter Kelly" --bind data2:s:"Peter" --bind data3:s:"Kelly" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14573821516" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Frank Martin" --bind data2:s:"Frank" --bind data3:s:"Martin" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16204068249" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Anthony Cook" --bind data2:s:"Anthony" --bind data3:s:"Cook" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12466041300" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Bruce Torres" --bind data2:s:"Bruce" --bind data3:s:"Torres" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19188402424" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Bruce Cox" --bind data2:s:"Bruce" --bind data3:s:"Cox" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17703736788" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Russell Bailey" --bind data2:s:"Russell" --bind data3:s:"Bailey" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12896107214" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"russell.bailey5@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Sarah Moore" --bind data2:s:"Sarah" --bind data3:s:"Moore" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12355397580" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Terry Turner" --bind data2:s:"Terry" --bind data3:s:"Turner" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16467228447" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"terry.turner73@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Logan Martin" --bind data2:s:"Logan" --bind data3:s:"Martin" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14438085053" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Douglas Hill" --bind data2:s:"Douglas" --bind data3:s:"Hill" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18714926018" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Gerald Lee" --bind data2:s:"Gerald" --bind data3:s:"Lee" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14944028236" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Peter Cooper" --bind data2:s:"Peter" --bind data3:s:"Cooper" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17232635061" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"peter.cooper21@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Steven Clark" --bind data2:s:"Steven" --bind data3:s:"Clark" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15894026419" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Mary Jones" --bind data2:s:"Mary" --bind data3:s:"Jones" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18885644433" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"mary.jones86@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Ronald Wright" --bind data2:s:"Ronald" --bind data3:s:"Wright" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17915816067" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Kenneth Allen" --bind data2:s:"Kenneth" --bind data3:s:"Allen" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18283551912" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Andrew Howard" --bind data2:s:"Andrew" --bind data3:s:"Howard" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15752589517" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"andrew.howard32@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Peter Hernandez" --bind data2:s:"Peter" --bind data3:s:"Hernandez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16115386183" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Aaron Lopez" --bind data2:s:"Aaron" --bind data3:s:"Lopez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16224668007" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Mark Edwards" --bind data2:s:"Mark" --bind data3:s:"Edwards" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16664228123" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Billy King" --bind data2:s:"Billy" --bind data3:s:"King" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19954292602" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Dylan Smith" --bind data2:s:"Dylan" --bind data3:s:"Smith" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18543473726" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"dylan.smith66@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Jose Baker" --bind data2:s:"Jose" --bind data3:s:"Baker" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14032327525" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Amanda Gonzalez" --bind data2:s:"Amanda" --bind data3:s:"Gonzalez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16533964816" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"amanda.gonzalez99@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Keith Ramos" --bind data2:s:"Keith" --bind data3:s:"Ramos" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14943798867" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Mason Carter" --bind data2:s:"Mason" --bind data3:s:"Carter" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19826826653" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Gregory Parker" --bind data2:s:"Gregory" --bind data3:s:"Parker" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14617836716" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"gregory.parker1@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Aaron Ramirez" --bind data2:s:"Aaron" --bind data3:s:"Ramirez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19198766044" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Ralph Rogers" --bind data2:s:"Ralph" --bind data3:s:"Rogers" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16729142916" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Justin Kelly" --bind data2:s:"Justin" --bind data3:s:"Kelly" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18909726873" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Ronald Adams" --bind data2:s:"Ronald" --bind data3:s:"Adams" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17277757177" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Dennis Gonzalez" --bind data2:s:"Dennis" --bind data3:s:"Gonzalez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14869065668" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"dennis.gonzalez21@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Steven Stewart" --bind data2:s:"Steven" --bind data3:s:"Stewart" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19639498320" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Alexander Taylor" --bind data2:s:"Alexander" --bind data3:s:"Taylor" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13579758215" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Jonathan Stewart" --bind data2:s:"Jonathan" --bind data3:s:"Stewart" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16769335256" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"jonathan.stewart33@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Louis Rodriguez" --bind data2:s:"Louis" --bind data3:s:"Rodriguez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19896395089" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Roy Bailey" --bind data2:s:"Roy" --bind data3:s:"Bailey" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14302061536" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Austin Roberts" --bind data2:s:"Austin" --bind data3:s:"Roberts" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12044267196" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Willie Gomez" --bind data2:s:"Willie" --bind data3:s:"Gomez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19867639412" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"willie.gomez54@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Gary Martin" --bind data2:s:"Gary" --bind data3:s:"Martin" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19972218571" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"gary.martin64@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Margaret Lopez" --bind data2:s:"Margaret" --bind data3:s:"Lopez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14583431654" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Jerry Rogers" --bind data2:s:"Jerry" --bind data3:s:"Rogers" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16727779556" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Zachary Mitchell" --bind data2:s:"Zachary" --bind data3:s:"Mitchell" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14357857955" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Patricia Scott" --bind data2:s:"Patricia" --bind data3:s:"Scott" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18864924989" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Janet Anderson" --bind data2:s:"Janet" --bind data3:s:"Anderson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17629088188" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Bobby Lewis" --bind data2:s:"Bobby" --bind data3:s:"Lewis" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14407055749" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"bobby.lewis66@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Emily Stewart" --bind data2:s:"Emily" --bind data3:s:"Stewart" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19785034124" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Willie Perez" --bind data2:s:"Willie" --bind data3:s:"Perez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12683951535" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Lawrence Adams" --bind data2:s:"Lawrence" --bind data3:s:"Adams" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19948469642" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Steven Adams" --bind data2:s:"Steven" --bind data3:s:"Adams" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14374084157" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Patricia Cooper" --bind data2:s:"Patricia" --bind data3:s:"Cooper" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16626978756" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"patricia.cooper79@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Jerry Scott" --bind data2:s:"Jerry" --bind data3:s:"Scott" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12899967659" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Raymond Parker" --bind data2:s:"Raymond" --bind data3:s:"Parker" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18809838937" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Daniel Miller" --bind data2:s:"Daniel" --bind data3:s:"Miller" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15425257109" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Margaret Anderson" --bind data2:s:"Margaret" --bind data3:s:"Anderson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18693264084" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"margaret.anderson34@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Arthur Walker" --bind data2:s:"Arthur" --bind data3:s:"Walker" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13623389201" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Zachary Lopez" --bind data2:s:"Zachary" --bind data3:s:"Lopez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18879144772" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Randy Thompson" --bind data2:s:"Randy" --bind data3:s:"Thompson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19774504565" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Frank Gonzalez" --bind data2:s:"Frank" --bind data3:s:"Gonzalez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14739362554" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Samuel Morgan" --bind data2:s:"Samuel" --bind data3:s:"Morgan" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18015127183" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"samuel.morgan21@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Roger Adams" --bind data2:s:"Roger" --bind data3:s:"Adams" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15078497111" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"roger.adams69@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Rebecca Cooper" --bind data2:s:"Rebecca" --bind data3:s:"Cooper" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17207141503" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Rebecca Anderson" --bind data2:s:"Rebecca" --bind data3:s:"Anderson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14004139606" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Rachel Davis" --bind data2:s:"Rachel" --bind data3:s:"Davis" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15626077086" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Eric Murphy" --bind data2:s:"Eric" --bind data3:s:"Murphy" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17428154914" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Sarah Turner" --bind data2:s:"Sarah" --bind data3:s:"Turner" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18048916502" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Jack Taylor" --bind data2:s:"Jack" --bind data3:s:"Taylor" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14046655458" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"jack.taylor38@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Robert Davis" --bind data2:s:"Robert" --bind data3:s:"Davis" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14678144408" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"robert.davis21@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Nicholas Lopez" --bind data2:s:"Nicholas" --bind data3:s:"Lopez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14158173764" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Ronald Green" --bind data2:s:"Ronald" --bind data3:s:"Green" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14829481459" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"ronald.green11@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Willie Ramos" --bind data2:s:"Willie" --bind data3:s:"Ramos" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13486698063" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Justin Richardson" --bind data2:s:"Justin" --bind data3:s:"Richardson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19496883080" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Donna Lee" --bind data2:s:"Donna" --bind data3:s:"Lee" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17646089815" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Robert Cooper" --bind data2:s:"Robert" --bind data3:s:"Cooper" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14907584894" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Edward Ramos" --bind data2:s:"Edward" --bind data3:s:"Ramos" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19728983945" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Jennifer Edwards" --bind data2:s:"Jennifer" --bind data3:s:"Edwards" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19077259545" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Deborah Stewart" --bind data2:s:"Deborah" --bind data3:s:"Stewart" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12524934770" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"deborah.stewart93@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Carol Smith" --bind data2:s:"Carol" --bind data3:s:"Smith" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17692084056" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"David Davis" --bind data2:s:"David" --bind data3:s:"Davis" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15485306428" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Jack Cruz" --bind data2:s:"Jack" --bind data3:s:"Cruz" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19873825989" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Michelle Flores" --bind data2:s:"Michelle" --bind data3:s:"Flores" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19288533033" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"michelle.flores87@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Ronald Parker" --bind data2:s:"Ronald" --bind data3:s:"Parker" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15817049259" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Daniel Roberts" --bind data2:s:"Daniel" --bind data3:s:"Roberts" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12068746377" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"daniel.roberts32@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Logan Johnson" --bind data2:s:"Logan" --bind data3:s:"Johnson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14789064332" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Margaret Robinson" --bind data2:s:"Margaret" --bind data3:s:"Robinson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13909993993" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"margaret.robinson65@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Mason Brown" --bind data2:s:"Mason" --bind data3:s:"Brown" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18434878842" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Albert Taylor" --bind data2:s:"Albert" --bind data3:s:"Taylor" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19072152566" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Dennis Smith" --bind data2:s:"Dennis" --bind data3:s:"Smith" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12653836499" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Margaret Edwards" --bind data2:s:"Margaret" --bind data3:s:"Edwards" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15127755647" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"margaret.edwards59@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Deborah Edwards" --bind data2:s:"Deborah" --bind data3:s:"Edwards" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12934285598" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"deborah.edwards44@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Dennis Rodriguez" --bind data2:s:"Dennis" --bind data3:s:"Rodriguez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15415539166" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"dennis.rodriguez92@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Robert Carter" --bind data2:s:"Robert" --bind data3:s:"Carter" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17113976235" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"robert.carter50@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Roy Richardson" --bind data2:s:"Roy" --bind data3:s:"Richardson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15667395869" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Andrew Taylor" --bind data2:s:"Andrew" --bind data3:s:"Taylor" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18168878520" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"andrew.taylor59@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Vincent Gonzalez" --bind data2:s:"Vincent" --bind data3:s:"Gonzalez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13247542301" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"William Robinson" --bind data2:s:"William" --bind data3:s:"Robinson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14397806892" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Louis Anderson" --bind data2:s:"Louis" --bind data3:s:"Anderson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17413081173" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"louis.anderson33@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Mark Johnson" --bind data2:s:"Mark" --bind data3:s:"Johnson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18548113188" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Thomas Flores" --bind data2:s:"Thomas" --bind data3:s:"Flores" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18867717929" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Paul Rogers" --bind data2:s:"Paul" --bind data3:s:"Rogers" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19353575342" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Kathleen Green" --bind data2:s:"Kathleen" --bind data3:s:"Green" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14955334757" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Ronald Baker" --bind data2:s:"Ronald" --bind data3:s:"Baker" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12686231582" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Philip Richardson" --bind data2:s:"Philip" --bind data3:s:"Richardson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14104191279" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"philip.richardson33@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Sean Walker" --bind data2:s:"Sean" --bind data3:s:"Walker" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17145606194" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"sean.walker71@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Jack Baker" --bind data2:s:"Jack" --bind data3:s:"Baker" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14256238510" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"jack.baker87@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Elijah Kelly" --bind data2:s:"Elijah" --bind data3:s:"Kelly" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14514668127" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"elijah.kelly90@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Jacob Martin" --bind data2:s:"Jacob" --bind data3:s:"Martin" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16105735198" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Nancy Williams" --bind data2:s:"Nancy" --bind data3:s:"Williams" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17116009975" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Keith Ortiz" --bind data2:s:"Keith" --bind data3:s:"Ortiz" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16407106345" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Brian Gutierrez" --bind data2:s:"Brian" --bind data3:s:"Gutierrez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14529001167" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Ashley Smith" --bind data2:s:"Ashley" --bind data3:s:"Smith" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18308844657" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Christine Collins" --bind data2:s:"Christine" --bind data3:s:"Collins" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18049778980" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"christine.collins65@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Jeffrey Lopez" --bind data2:s:"Jeffrey" --bind data3:s:"Lopez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15379953430" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"jeffrey.lopez42@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Louis Moore" --bind data2:s:"Louis" --bind data3:s:"Moore" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13798854529" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"louis.moore11@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Patrick Cooper" --bind data2:s:"Patrick" --bind data3:s:"Cooper" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13486701185" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"patrick.cooper98@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Maria Gomez" --bind data2:s:"Maria" --bind data3:s:"Gomez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15056373228" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Nicole Thomas" --bind data2:s:"Nicole" --bind data3:s:"Thomas" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15572417629" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"James Perez" --bind data2:s:"James" --bind data3:s:"Perez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15984467915" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"james.perez28@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Timothy Adams" --bind data2:s:"Timothy" --bind data3:s:"Adams" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13898185697" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Elijah Sanchez" --bind data2:s:"Elijah" --bind data3:s:"Sanchez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15937139096" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Elizabeth Rogers" --bind data2:s:"Elizabeth" --bind data3:s:"Rogers" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12432485006" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Michelle Torres" --bind data2:s:"Michelle" --bind data3:s:"Torres" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16992873742" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Philip Perez" --bind data2:s:"Philip" --bind data3:s:"Perez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18405964045" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Zachary Hall" --bind data2:s:"Zachary" --bind data3:s:"Hall" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17865721615" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"zachary.hall64@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Joshua Anderson" --bind data2:s:"Joshua" --bind data3:s:"Anderson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13873525638" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"joshua.anderson1@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"David Gonzalez" --bind data2:s:"David" --bind data3:s:"Gonzalez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14288063900" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"david.gonzalez12@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Carolyn Cook" --bind data2:s:"Carolyn" --bind data3:s:"Cook" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12032853245" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"carolyn.cook41@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Nicole White" --bind data2:s:"Nicole" --bind data3:s:"White" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17189461132" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"nicole.white22@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Gabriel Turner" --bind data2:s:"Gabriel" --bind data3:s:"Turner" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12466962327" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"gabriel.turner52@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Rachel Cooper" --bind data2:s:"Rachel" --bind data3:s:"Cooper" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12119722601" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"rachel.cooper10@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Stephen Gonzalez" --bind data2:s:"Stephen" --bind data3:s:"Gonzalez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19002371773" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"stephen.gonzalez27@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Roy Taylor" --bind data2:s:"Roy" --bind data3:s:"Taylor" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13546977240" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Matthew Williams" --bind data2:s:"Matthew" --bind data3:s:"Williams" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19776568583" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Bobby Rogers" --bind data2:s:"Bobby" --bind data3:s:"Rogers" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14062175814" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Jesse Kim" --bind data2:s:"Jesse" --bind data3:s:"Kim" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+17553901092" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Harold Peterson" --bind data2:s:"Harold" --bind data3:s:"Peterson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15278476380" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Carl Morgan" --bind data2:s:"Carl" --bind data3:s:"Morgan" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14095433358" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"carl.morgan32@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Michelle Wilson" --bind data2:s:"Michelle" --bind data3:s:"Wilson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15435805004" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Roy Parker" --bind data2:s:"Roy" --bind data3:s:"Parker" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14563223903" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Debra Ward" --bind data2:s:"Debra" --bind data3:s:"Ward" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16584954522" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"debra.ward80@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Rachel Hill" --bind data2:s:"Rachel" --bind data3:s:"Hill" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13237463297" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Jerry Phillips" --bind data2:s:"Jerry" --bind data3:s:"Phillips" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15229871493" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Helen Jackson" --bind data2:s:"Helen" --bind data3:s:"Jackson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14003897966" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"helen.jackson35@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Walter Perez" --bind data2:s:"Walter" --bind data3:s:"Perez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12259729466" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"walter.perez90@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Karen White" --bind data2:s:"Karen" --bind data3:s:"White" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18215362693" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"karen.white5@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Emma Wright" --bind data2:s:"Emma" --bind data3:s:"Wright" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12267302256" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Emily Gonzalez" --bind data2:s:"Emily" --bind data3:s:"Gonzalez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13485987808" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Joshua Thomas" --bind data2:s:"Joshua" --bind data3:s:"Thomas" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+16204729316" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Brian Nelson" --bind data2:s:"Brian" --bind data3:s:"Nelson" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+19683164206" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Laura Ramirez" --bind data2:s:"Laura" --bind data3:s:"Ramirez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15622508055" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Paul Stewart" --bind data2:s:"Paul" --bind data3:s:"Stewart" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18595967888" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"paul.stewart52@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Catherine King" --bind data2:s:"Catherine" --bind data3:s:"King" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+14438932306" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Helen Gomez" --bind data2:s:"Helen" --bind data3:s:"Gomez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15987087839" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Ronald Phillips" --bind data2:s:"Ronald" --bind data3:s:"Phillips" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15618466806" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"ronald.phillips44@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Jerry Nguyen" --bind data2:s:"Jerry" --bind data3:s:"Nguyen" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13814755208" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Jose Ramos" --bind data2:s:"Jose" --bind data3:s:"Ramos" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15475865115" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Scott Ward" --bind data2:s:"Scott" --bind data3:s:"Ward" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12908706961" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Patricia Hill" --bind data2:s:"Patricia" --bind data3:s:"Hill" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12779186838" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Laura Gutierrez" --bind data2:s:"Laura" --bind data3:s:"Gutierrez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13426674016" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Gregory Ward" --bind data2:s:"Gregory" --bind data3:s:"Ward" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+12163036847" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Brian Miller" --bind data2:s:"Brian" --bind data3:s:"Miller" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13959644536" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"brian.miller47@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Gary Edwards" --bind data2:s:"Gary" --bind data3:s:"Edwards" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13183963872" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Alan White" --bind data2:s:"Alan" --bind data3:s:"White" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18668968230" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"alan.white71@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Brian Reyes" --bind data2:s:"Brian" --bind data3:s:"Reyes" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+13213293965" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"brian.reyes70@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Elijah Diaz" --bind data2:s:"Elijah" --bind data3:s:"Diaz" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+15658235008" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:"elijah.diaz48@gmail.com" --bind data2:i:1 2>/dev/null

content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:com.google --bind account_name:s:epolusamuel682@gmail.com 2>/dev/null
RID=$((COUNT + 1))
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:"Donna Hernandez" --bind data2:s:"Donna" --bind data3:s:"Hernandez" 2>/dev/null
content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$RID --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:"+18035945402" --bind data2:i:2 2>/dev/null
COUNT=$((COUNT + 1))

echo "Done: $COUNT contacts inserted at $(date)" >> $LOG
echo "CONTACTS_DONE_$COUNT"
