import json
import os
import tempfile
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
from telegram.ext import CallbackQueryHandler

def load_data():
    try:
        with open('data.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_data(data):
    with open('data.json', 'w') as file:
        json.dump(data, file, indent=4)

user_rooms = load_data()

ENTER_NUMBER, ENTER_ROOM_CHANGE, ENTER_ROOM_DELETE = range(3)

def push(update: Update, context: CallbackContext) -> None:
    global user_rooms
    json_file_content = json.dumps(user_rooms, indent=4)

    with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as temp_file:
        temp_file.write(json_file_content)

    with open(temp_file.name, 'rb') as file:
        context.bot.send_document(chat_id=update.message.chat_id, document=file)

    os.remove(temp_file.name)


def new(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Введите свой уникальный номер:')
    return ENTER_NUMBER

def enter_number(update: Update, context: CallbackContext) -> int:
    user_number = update.message.text
    if user_number in user_rooms:
        update.message.reply_text('Этот уникальный номер уже зарегистрирован. Введите другой уникальный номер.')
        return ENTER_NUMBER

    context.user_data['room_number'] = user_number

    update.message.reply_text('Введите номер комнаты:')
    return ENTER_ROOM_CHANGE

def enter_room_change(update: Update, context: CallbackContext) -> int:
    user_number = context.user_data['room_number']
    room_number = update.message.text
    user_rooms[user_number] = {"room": room_number}
    save_data(user_rooms)
    update.message.reply_text(f'Вы успешно зарегистрированы в комнате {room_number}.')
    return ConversationHandler.END

def inline_button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    if query.data == 'new':
        context.bot.send_message(chat_id=query.message.chat_id, text='/new - Зарегистрироваться')
    elif query.data == 'show':
        context.bot.send_message(chat_id=query.message.chat_id, text='/show - Показать список комнат')
    elif query.data == 'change':
        context.bot.send_message(chat_id=query.message.chat_id, text='/change - Изменить комнату')
    elif query.data == 'del':
        context.bot.send_message(chat_id=query.message.chat_id, text='/del - Удалить комнату')


def show(update: Update, context: CallbackContext) -> int:
    room_list = set(data["room"] for data in user_rooms.values() if data.get("room"))
    update.message.reply_text(f'Список комнат: {", ".join(room_list)}\nВведите номер комнаты, чтобы посмотреть учеников в ней:')
    return ENTER_ROOM_CHANGE

def show_students(update: Update, context: CallbackContext) -> None:
    room_number = update.message.text
    students_in_room = [uid for uid, data in user_rooms.items() if data.get("room") == room_number]
    update.message.reply_text(f'Ученики в комнате {room_number}: {", ".join(students_in_room)}')

def change(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Введите свой уникальный номер для смены комнаты:')
    return ENTER_NUMBER

def delete_room(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Введите номер комнаты, чтобы удалить её и всех учеников в ней:')
    return ENTER_ROOM_DELETE

def enter_room_delete(update: Update, context: CallbackContext, user_rooms) -> None:
    room_number = update.message.text
    if any(data.get("room") == room_number for data in user_rooms.values()):
        user_rooms = {user_number: data for user_number, data in user_rooms.items() if data.get("room") != room_number}
        save_data(user_rooms)
        update.message.reply_text(f'Комната {room_number} и все ученики в ней удалены.')
    else:
        update.message.reply_text(f'Комната {room_number} не найдена.')

def error(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(f'Произошла ошибка: {context.error}')

def main() -> None:
    updater = Updater("5947696330:AAGoMFod0WmW6RzRqThPnXEsHxj2SUKcQEo")  # Замените "YOUR_TOKEN" на токен вашего бота

    dp = updater.dispatcher

    dp.add_handler(CommandHandler('push', push))

    conv_handler_new = ConversationHandler(
        entry_points=[CommandHandler('new', new)],
        states={
            ENTER_NUMBER: [MessageHandler(Filters.text & ~Filters.command, enter_number)],
            ENTER_ROOM_CHANGE: [MessageHandler(Filters.text & ~Filters.command, enter_room_change)]
        },
        fallbacks=[]
    )

    show_handler = MessageHandler(Filters.text & ~Filters.command & Filters.regex(r'^\d+$'), show_students)
    dp.add_handler(conv_handler_new)
    dp.add_handler(CommandHandler('show', show))
    dp.add_handler(show_handler)
    dp.add_handler(CommandHandler('change', change))


    conv_handler_delete = ConversationHandler(
        entry_points=[CommandHandler('del', delete_room)],
        states={
            ENTER_ROOM_DELETE: [MessageHandler(Filters.text & ~Filters.command, enter_room_delete)]
        },
        fallbacks=[]
    )
    dp.add_handler(conv_handler_delete)

    dp.add_error_handler(error)


    updater.start_polling()

    dp.add_handler(CallbackQueryHandler(inline_button_handler))

    updater.idle()

    dp.add_handler(CommandHandler('push', push))

    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()

