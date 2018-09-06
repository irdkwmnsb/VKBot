import vk

from VKPy import VKBot, Event

TOKEN = input("Enter a token: ")
GROUP_ID = int(input("Enter group id: "))
session = vk.Session(TOKEN)
api = vk.API(session, v='5.80')
bot = VKBot(api, GROUP_ID)


@bot.handle_message(func_text=lambda x: True)
def echo(event: Event):
    msg = event.object
    print("Echo for {0}".format(repr(msg)))
    api.messages.send(user_id=msg['from_id'], forward_messages=str(msg['id']), message=msg['text'])


bot.run(reload=True)
