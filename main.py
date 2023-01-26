import yaml
import kv
import aiohttp
import json
from telethon import TelegramClient, events, sync, tl
from telethon.tl.custom.message import Message
from telethon.tl.types import DocumentAttributeSticker, DocumentAttributeImageSize
from typing import List, Dict

with open('config.yaml') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)
with open('save.json') as f:
    durable = json.load(f)

saved_message = durable["saved"]
session_name = config["session"]["name"]
api_id = config["client"]["api_id"]
api_hash = config["client"]["api_hash"]
reminder = config["reminder"]
all_listen_user = ['me']


async def bot_send(message):
    async with aiohttp.ClientSession() as session:
        await session.post(
            url=f"https://api.telegram.org/bot{reminder['bot']['token']}/sendMessage",
            data={
                "chat_id": reminder['bot']['chat_id'],
                "text": message
            })


def add_data(o_d, n_d):
    if isinstance(o_d, List):
        if isinstance(n_d, List):
            o_d.extend(n_d)
        elif isinstance(n_d, str):
            o_d.append(n_d)
    elif isinstance(o_d, str):
        if isinstance(n_d, List):
            o_d = [o_d, *n_d]
        elif isinstance(n_d, str):
            o_d = [o_d, n_d]
    return o_d


with TelegramClient(session_name, api_id, api_hash) as client:
    # client.send_message('me', 'Hello, myself!')
    # print(client.download_profile_photo('me'))

    @client.on(events.NewMessage(func=lambda e: e.is_private))
    async def listen_private(event: events.newmessage.NewMessage.Event):
        """
        监听所有发出的新信息
        :param event:
        :return:
        """
        message: Message = event.message

        if message.out:
            message_user = 'me'
        else:
            chat = await event.get_chat()
            if chat.username:
                message_user = f"@{chat.username}"
            else:
                message_user = f"{chat.lastname}{chat.firstname}"

        if message.from_id:
            message_from_id = message.from_id.user_id if message.from_id.user_id else message.from_id.channel_id
        else:
            message_from_id = None

        if message.message == '':
            try:
                message_content = message.media.document.attributes
                for msg in message_content:
                    if isinstance(msg, DocumentAttributeSticker):
                        message_content = message_content.alt
            except AttributeError:
                message_content = None
            if message.media.photo:
                await client.download_media(message)
        else:
            message_content = message.message
        saved_message.append(message.id)
        await kv.save_data(f"{session_name}_{message.id}", {
            "message": message_content,
            "message_user": message_user,
            "message_date": message.date.strftime('%Y-%m-%d %H:%M:%S'),
            "is_edited": False,
            "is_deleted": False,
            "message_id": message.id,
            "message_from_id": message_from_id,
            "user_id": message.peer_id.user_id,
            "reply_to": message.reply_to.reply_to_msg_id if message.reply_to else None,
            "fwd_form": {
                "fwd_id": message.fwd_from.from_id,
                "fwd_name": message.fwd_from.from_name,
            } if message.fwd_from else None,
        })


    @client.on(events.MessageDeleted)
    async def handler(event: events.messagedeleted.MessageDeleted.Event):
        """
        :param event:
        :return:
        """
        deleted_id = event.deleted_id
        deleted_ids = event.deleted_ids.append(deleted_id)
        if deleted_id:
            if deleted_ids:
                deleted_ids.append(deleted_id)
            else:
                deleted_ids = [deleted_id]
        for msg_id in deleted_ids:
            if msg_id not in saved_message:
                continue
            original_message = await kv.get_data(f"{session_name}_{msg_id}")
            if original_message:
                original_message["is_deleted"] = True
                await kv.save_data(f"{session_name}_{msg_id}", original_message)
                await bot_send(
                    f"{msg_id} in {original_message['message_user']} was deleted\n{original_message['message']}")


    @client.on(events.MessageEdited(func=lambda e: e.is_private))
    async def listen_private_msg_edited(event: events.messageedited.MessageEdited.Event):
        """
        监听所有私人频道中被编辑的信息
        :param event:
        :return:
        """
        message: Message = event.message
        original_message: Dict = await kv.get_data(f"{session_name}_{message.id}")
        print(original_message)
        original_message["is_edited"] = True
        original_message["message"] = add_data(original_message["message"], message.message)
        original_message["message_date"] = add_data(original_message["message_date"],
                                                    message.date.strftime('%Y-%m-%d %H:%M:%S'))
        print(original_message)
        await kv.save_data(f"{session_name}_{message.id}", original_message)


    client.run_until_disconnected()
