#!/bin/bash
#This script generates the files required to build a custom pvpoke meta
#Refer to https://github.com/pvpoke/pvpoke/wiki/Creating-New-Cups-&-Rankings

webrt="/var/www/builder.devon.gg/public_html/pvpoke/src"
date=`date +"%Y%m%d-%H:%M:%S"`

#create gamemaster cup file
echo -n "Enter the name of the meta:"
read name
sleep 1s
echo -n "Enter the title of the meta:"
read title
sleep 1s
echo "I am now creating the Gamemaster Cup File $name.json for you ..."
sleep 2s
touch ${webrt}/data/gamemaster/cups/${name}.json
echo -n "Enter the json structure for the meta:"
read cup
cat <<< "$cup" >> ${webrt}/data/gamemaster/cups/${name}.json
rpl -w "custom" "$name" ${webrt}/data/gamemaster/cups/${name}.json
rpl -w "Custom" "$title" ${webrt}/data/gamemaster/cups/${name}.json

#backup all formats files before proceeding
echo "I am now backing up all format files before proceeding ..."
cp ${webrt}/data/gamemaster/formats.json ${webrt}/data/gamemaster/formats-bu/formats-${date}.json
cp ${webrt}/data/gamemaster/formats-all.json ${webrt}/data/gamemaster/formats-bu/formats-all-${date}.json
cp ${webrt}/data/gamemaster/formats-new.json ${webrt}/data/gamemaster/formats-bu/formats-new-${date}.json
sleep 2s

#create gamemaster format listing - make sure that formats-all.json and formats-new.json are in /usr/local/bin/files
echo "I am now editing the Gamemaster Format Listing to include your new meta ..."
sleep 2s

#backup formats-all.json before beginning
cp ${webrt}/data/gamemaster/formats-all.json ${webrt}/data/gamemaster/formats-bu/formats-all-${date}.json

#make a copy of all/new.json for the new meta leaving the originals untouched
cp ${webrt}/data/gamemaster/formats-new.json ${webrt}/data/gamemaster/formats-bu/formats-${name}-new.json
cp ${webrt}/data/gamemaster/formats-all.json ${webrt}/data/gamemaster/formats-bu/formats-${name}-all.json
echo "The necessary files are created, now editing the name and title ..."
sleep 2s

#edit the name and title to match that of what user entered - make sure rpl is installed or just use sed
rpl -w "custom" "$name" ${webrt}/data/gamemaster/formats-bu/formats-${name}-new.json
rpl -w "Custom" "$title" ${webrt}/data/gamemaster/formats-bu/formats-${name}-new.json
rpl -w "great" "$name" ${webrt}/data/gamemaster/formats-bu/formats-${name}-new.json
echo "Adding the new meta to formats.json in gamemaster, creating a backup of formats in case something goes wrong ..."
sleep 2s
cat ${webrt}/data/gamemaster/formats-bu/formats-${name}-new.json >> ${webrt}/data/gamemaster/formats-bu/formats-${name}-all.json
mv ${webrt}/data/gamemaster/formats.json ${webrt}/data/gamemaster/formats-bu/formats-${date}.json
cp -ar ${webrt}/data/gamemaster/formats-bu/formats-${name}-all.json ${webrt}/data/gamemaster/formats.json
echo "Removing temporary files I made and making sure you can add another meta when you are ready ..."
sleep 2s
head -n -1 ${webrt}/data/gamemaster/formats-bu/formats-${name}-all.json > ${webrt}/data/gamemaster/formats-bu/formats-temp1.json
head -n -1 ${webrt}/data/gamemaster/formats-bu/formats-temp1.json > ${webrt}/data/gamemaster/formats-bu/formats-temp2.json
echo "        }," >> ${webrt}/data/gamemaster/formats-bu/formats-temp2.json
mv ${webrt}/data/gamemaster/formats-bu/formats-temp2.json ${webrt}/data/gamemaster/formats-all.json
rm ${webrt}/data/gamemaster/formats-bu/formats-${name}-all.json
rm ${webrt}/data/gamemaster/formats-bu/formats-${name}-new.json
rm ${webrt}/data/gamemaster/formats-bu/formats-temp1.json
echo "Alright, formats.json is now complete - do not forget to compile and run the ranker/sandbox ..."
sleep 2s

#create Meta Group File
echo "I'll create an empty file for you in data/groups/$name.json that you can edit later for use with Multi Battle and Matrix battle ..."
sleep 2s
touch ${webrt}/data/groups/${name}.json
echo "[]" >> ${webrt}/data/groups/${name}.json
echo "Remember, to make the custom group json, enter your xml in Custom Rankings, Simulate, Import/Export, JSON Export  ..."
sleep 2s

#create Moveset Override File
echo -n "We need to create a file for potential moveset overrides - please enter the CP (500, 1500, 2500, or 10000) for this cup below:"
read cp
mkdir ${webrt}/data/overrides/${name}
touch ${webrt}/data/overrides/${name}/${cp}.json
echo "[]" >> ${webrt}/data/overrides/${name}/${cp}.json
echo "You will want to edit the $cp.json file according to your needs and run the ranker after each adjustment ..."

#create the Ranking Data Files
echo "Please standby as I create the ranking files/directories for running meta simulations ... "
sleep 2s
mkdir ${webrt}/data/rankings/${name}
mkdir ${webrt}/data/rankings/${name}/attackers
mkdir ${webrt}/data/rankings/${name}/chargers
mkdir ${webrt}/data/rankings/${name}/closers
mkdir ${webrt}/data/rankings/${name}/consistency
mkdir ${webrt}/data/rankings/${name}/leads
mkdir ${webrt}/data/rankings/${name}/overall
mkdir ${webrt}/data/rankings/${name}/switches
echo "[]" >> ${webrt}/data/rankings/${name}/attackers/rankings-${cp}.json
echo "[]" >> ${webrt}/data/rankings/${name}/chargers/rankings-${cp}.json
echo "[]" >> ${webrt}/data/rankings/${name}/closers/rankings-${cp}.json
echo "[]" >> ${webrt}/data/rankings/${name}/consistency/rankings-${cp}.json
echo "[]" >> ${webrt}/data/rankings/${name}/leads/rankings-${cp}.json
echo "[]" >> ${webrt}/data/rankings/${name}/overall/rankings-${cp}.json
echo "[]" >> ${webrt}/data/rankings/${name}/switches/rankings-${cp}.json
echo "Your files are now created - please compile, create a group of your choice, import movesets, & run ranker/sandbox and you should be good ..."

#set permissions
echo "Please standby as I set permissions ... "
chmod 777 -R /var/www/builder.devon.gg/public_html/pvpoke/
sleep 2s
