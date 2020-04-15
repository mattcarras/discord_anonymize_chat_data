"""
WIP to get and then anonymize a given Discord channel's chat history OR to read from a file of exisitng chat data
Makes sure all mentions are exported with discriminators for ease of parsing
Writes to exported_chat_data.csv in UTF-8 (unicode) format
NOTE: Mentions must be in the name#discriminator format to be anonymized
Last Updated: 4-15-20 by Matt Carras
"""

import re 
import io
from argparse import ArgumentParser
from backports import csv
from faker import Faker
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
        self.fakerNames = defaultdict(faker.name)
        self.fakerIds   = defaultdict(faker.random_number)
consts = Constants()

# Anonymize a row of data, search through content for mentions and anonymizing them as well. 
# Mentions must be in name#discriminator format.
# Currently anonymizes the Author and AuthorID field, as well as mentions in content.
def anonymize_row(row):
    row['AuthorID'] = consts.fakerIds[row['AuthorID']]
    row['Author'] = consts.fakerNames[row['Author']]
    
    # Search for mentions in Content row in format of name#discriminator
    mentions = re.findall('@([^#]+#[0-9]+)', row['Content'])
    for mention in mentions:
        row['Content'] = row['Content'].replace(mention, consts.fakerNames[mention])
    
# Anonymize all rows of a given CSV file to destination file
def anonymize_file(source,dest):
    print('Reading from [{0}] and writing anonymized data to [{1}]...'.format(source,dest))
    with io.open(source, 'r', encoding='utf8') as f:
    #with io.open(source, 'r') as f:
        with io.open(dest, 'w', encoding='utf8') as o:
            fieldnames = consts.defaultHeader
            reader = csv.DictReader(f)
            writer = csv.DictWriter(o,fieldnames)
            writer.writeheader()
            for row in reader:
                anonymize_row(row)
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
                    
                    anonymize_row(row)
                    
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
                    help="CHANNELID to export history from. Both CHANNELID and TOKEN are required to export history from an online channel", metavar="CHANNELID")
parser.add_argument("-t", "--token", dest="bottoken",
                    help="TOKEN required for connecting to discord (bot token) to export channel history. Both CHANNELID and TOKEN are required to export history from an online channel", metavar="TOKEN")                    
# parser.add_argument("-q", "--quiet",
                    # action="store_false", dest="verbose", default=True,
                    # help="don't print status messages to stdout")

args = parser.parse_args()

if args.csvinput:
    anonymize_file(args.csvinput,args.csvoutput)
elif args.channelid and args.bottoken:
    client = DiscordClient()
    client.prepare_get_channel_history(exportChannelID=args.channelid,exportCSV=args.csvoutput,exportChannelLimit=None,exportChannelAfter=None)
    client.run(args.bottoken)
elif args.channelid or args.bottoken:
    print('ERROR: Both TOKEN and CHANNELID are required to connect to discord')
else:
    # Empty / invalid arguments
    parser.print_help()
           

