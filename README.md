# discord_anonymize_chat_data
 Python project to anonymize chat text data (CSV) from Discord using Faker and optionally discord.py to connect to a given channel to collect new data from the channel's history. Currently anomymizes AuthorID, Author, and mentions in Content for each row of messages. Exports to UTF-8 (unicode) encoded CSV (if importing into Excel, make sure you select UTF-8 encoding). **Note that only mentions in the name#discriminator format will be anonymized.**

 **In the latest version, the script supports input CSV files with any type of header if given a format for which fields to anonymize. See the new `-hf FIELDNAME=FIELDTYPE` option.** This parameter can be used to anonymize sources other than exported Discord chat data.
 
```
usage: discord_anonymize_chat_data.py [-h] [-i CSV] [-o CSV] [-c CHANNELID]
                                      [-t TOKEN] [-im]
                                      [-hf FIELDNAME=FIELDTYPE [FIELDNAME=FIELDTYPE ...]]

optional arguments:
  -h, --help            show this help message and exit
  -i CSV, --input CSV   anonymize existing CSV file
  -o CSV, --output CSV  ouput anonymized data to CSV file
  -c CHANNELID, --channelid CHANNELID
                        discord CHANNELID to export history from. Both CHANNELID and
                        TOKEN are required to export history from an online
                        channel
  -t TOKEN, --token TOKEN
                        TOKEN required for connecting to discord (bot token)
                        and exporting channel history. Both CHANNELID and TOKEN
                        are required to export history from an online channel
  -im, --ignorementions
                        Do not attempt to parse and replace mentions in the
                        Content field when given an input file
  -hf FIELDNAME=FIELDTYPE [FIELDNAME=FIELDTYPE ...], --headerformat FIELDNAME=FIELDTYPE [FIELDNAME=FIELDTYPE ...]
                        Anonymize given header field name and type (multiples
                        seperated by a space) instead of the default of
                        AuthorID and Author. Field names and types are case
                        insentitive. This parameter can be used to anonymize
                        sources other than exported Discord chat data, and
                        only affects a given CSV input file, also preserving
                        its original header in the resulting output. Currently
                        available types: Name,Number,Username. Example:
                        [UserID=Number DisplayName=Name] will anonymize the
                        UserID and DisplayName fields.
```

Requires the Faker and discord.py libraries: `pip install Faker discord.py`

To get your bot token, you'll need to setup a new app with your Discord account by going to https://discordapp.com/developers/applications. There are various tutorials out there for how to register a new bot on Discord.

To get your channel's ID, make sure Discord is in developer mode and *shift+left click* the **Copy ID** menu addition when right-clicking on a message. The first number before the dash is the channel ID, as explained in the KB linked [here](https://support.discordapp.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID-). Make sure the bot has been invited to the channel with the necessary permissions before trying to use it!
