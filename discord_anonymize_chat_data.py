"""
WIP to get and then anonymize a given Discord channel's chat history OR to read from a file of exisitng chat data
Makes sure all mentions are exported with discriminators for ease of parsing
Writes to exported_chat_data.csv in UTF-8 (unicode) format
Last Updated: 4-20-20 by Matt Carras
"""

import re 
import io
from argparse import ArgumentParser
from backports import csv
from faker import Faker
from faker.providers import internet
from collections import defaultdict
import discord

# Create an immutable class of constant values.
class Constants:
    defaultOutputFile = 'exported_anonymized_data.csv'
    
    # Default CSV header / fieldnames
    defaultHeader = ['AuthorID','Author','Date','Content','Attachments','Reactions']
    
    # Initialize Faker and create mappings
    def __init__(self):
        faker = Faker()
        faker.add_provider(internet)
        self.fakerNames     = defaultdict(faker.name)
        self.fakerNumbers   = defaultdict(faker.random_number)
        self.fakerUsernames = defaultdict(faker.user_name)
        self.anonymizationDicts = { 
            'name': self.fakerNames, 
            'number': self.fakerNumbers,
            'username': self.fakerUsernames
        }
consts = Constants()

# Abort script, displaying message and doing any required clean-up first.
def abort_script(msg):
    print('ERROR: {0}'.format(msg))
    quit()
    
# Anonymize a row of data, search through content for mentions and anonymizing them as well. 
# Mentions must be in name#discriminator format.
# Currently anonymizes the Author and AuthorID field, as well as mentions in content.
def anonymize_row(row,fieldnames,csvheaderformatdict=None,ignorementions=False):
    # See if we're given a custom CSV header format
    if not csvheaderformatdict:
        row['AuthorID'] = consts.fakerNumbers[row['AuthorID']]
        row['Author'] = consts.fakerUsernames[row['Author']]
    else:
        # FieldName: FieldType
        for fieldname in fieldnames:
            anondictname = csvheaderformatdict.get(fieldname.lower())
            if anondictname:
                row[fieldname] = consts.anonymizationDicts[anondictname][row[fieldname]]
                
    # Search for mentions in Content row in format of name#discriminator
    if not ignorementions:
        mentions = re.findall('@([^#]+#[0-9]+)', row['Content'])
        for mention in mentions:
            row['Content'] = row['Content'].replace(mention, consts.fakerUsernames[mention])
    
# Anonymize all rows of a given CSV file to destination file
def anonymize_file(source,dest,csvheaderformatdict=None,ignorementions=False):
    print('Reading from [{0}] and writing anonymized data to [{1}]...'.format(source,dest))
    with io.open(source, 'r', encoding='utf8') as f:
    #with io.open(source, 'r') as f:
        with io.open(dest, 'w', encoding='utf8') as o:
            reader = csv.DictReader(f)
            if not csvheaderformatdict:
                fieldnames = consts.defaultHeader
            else:
                fieldnames = reader.fieldnames
            writer = csv.DictWriter(o,fieldnames)
            writer.writeheader()
            for row in reader:
                anonymize_row(row,fieldnames,csvheaderformatdict,ignorementions)
                writer.writerow(row)

# Create class for interacting with discord.py and the export_anonymized_channel_history method             
class DiscordClient(discord.Client):
    # Prepare the class variables needed for the on_ready event. Make sure to run this method BEFORE client.run()!
    def prepare_get_channel_history(self,exportChannelID,exportCSV,exportChannelLimit=None,exportChannelAfter=None):
        self.exportChannelID=exportChannelID
        self.exportCSV=exportCSV
        self.exportChannelLimit=exportChannelLimit
        self.exportChannelAfter=exportChannelAfter
        
    async def on_ready(self):
        print('Logged on to discord as {0}!'.format(self.user))
        print('Attempting to query discord channel ID {0}...'.format(self.exportChannelID))
        channel = self.get_channel( int(self.exportChannelID) )
        if channel:
            with io.open(self.exportCSV, 'w', encoding='utf8') as o:
                print('Exporting anonymized data to [{0}]...'.format(self.exportCSV))
                fieldnames = consts.defaultHeader
                writer = csv.DictWriter(o,fieldnames)
                writer.writeheader()
                print('Parsing channel history...')
                async for message in channel.history(limit=self.exportChannelLimit,after=self.exportChannelAfter):
                    # TODO: Do something with attachments and reactions
                    row = {'AuthorID': message.author.id,'Author': format(message.author),'Date': message.created_at,'Content': message.content,'Attachments': len(message.attachments),'Reactions': len(message.reactions)}
                    
                    # Replace all mentions with name#discriminator format
                    # TODO: Optimize this iteration, also combining it with the anonymization (callback?)
                    for user in message.mentions:
                        row['Content'] = row['Content'].replace('<@!{0}>'.format(user.id),'@{0}#{1}'.format(user.name,user.discriminator))
                    
                    anonymize_row(row,fieldnames)
                    
                    writer.writerow(row)
        # Using await should wait until any previous async finishes
        print('Disconnecting from discord')
        await self.logout()
        
# Setup command-line argument parser and parse given arguments.
parser = ArgumentParser()

parser.add_argument("-i", "--input", dest="csvinput",
                    help="anonymize existing CSV file", metavar="CSV")
parser.add_argument("-o", "--output", dest="csvoutput",
                    help="ouput anonymized data to CSV file", metavar="CSV",
                    default=consts.defaultOutputFile)
parser.add_argument("-c", "--channelid", dest="channelid",
                    help="discord CHANNELID to export history from. Both CHANNELID and TOKEN are required to export history from an online channel", metavar="CHANNELID")
parser.add_argument("-t", "--token", dest="bottoken",
                    help="TOKEN required for connecting to discord (bot token) and exporting channel history. Both CHANNELID and TOKEN are required to export history from an online channel", metavar="TOKEN")
parser.add_argument("-im", "--ignorementions", dest="ignorementions",
                    help="do not attempt to parse and replace mentions in the Content field when given an input file",
                    action='store_true', default=False)
# Fancy format command below takes the keys from consts.anonymizationDicts.keys, capitlizes the first letter of each key, sorts them, and joins them to a single string, separated by commas
parser.add_argument("-hf", "--headerformat", dest="csvheaderformat",
                    nargs='+',
                    help='anonymize given header field name and type (multiples seperated by a space) instead of the default of AuthorID and Author. Field names and types are case insentitive. This parameter can be used to anonymize sources other than exported Discord chat data, and only affects a given CSV input file, also preserving its original header in the resulting output. Currently available types: {0}. Example: [UserID=Number DisplayName=Name] will anonymize the UserID and DisplayName fields.'.format(','.join(sorted([s.capitalize() for s in consts.anonymizationDicts.keys()]))), metavar='FIELDNAME=FIELDTYPE')
                    
# parser.add_argument("-q", "--quiet",
                    # action="store_false", dest="verbose", default=True,
                    # help="don't print status messages to stdout")

args = parser.parse_args()

# If --headerformat argument given, convert from list to hash table / dictionary
csvheaderformatdict = None
if args.csvheaderformat:
    print('Parsing given custom header format...')
    csvheaderformatdict = {}
    # Look for arguments in the given list in the format of FieldName=Type
    for hformatstr in args.csvheaderformat:
        splitstr = hformatstr.split('=', 1)
        if splitstr:
            fieldnamestr = splitstr[0].lower()
            typestr = splitstr[1].lower()
            # Double-check we have a valid type
            if not typestr in consts.anonymizationDicts.keys():
                abort_script('Invalid or unknown field type in [{0}]. Check -h for more information on valid field types.'.format(hformatstr))
            csvheaderformatdict[ fieldnamestr ] = typestr
    
if args.csvinput:
    anonymize_file(args.csvinput,args.csvoutput,csvheaderformatdict,args.ignorementions)
elif args.channelid and args.bottoken:
    client = DiscordClient()
    client.prepare_get_channel_history(exportChannelID=args.channelid,exportCSV=args.csvoutput,exportChannelLimit=None,exportChannelAfter=None)
    client.run(args.bottoken)
elif args.channelid or args.bottoken:
    print('ERROR: Both TOKEN and CHANNELID are required to connect to discord')
else:
    # Empty / invalid arguments
    print('ERROR: Input source required (CSV file or directly from Discord)')
    parser.print_help()

# DC.MC^2 Channel ID = 176329233319198720

