# TOKEN = '6680689043:AAGCgNna-mNYkdsD_i7O4i6daZin5D-w0gs'

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext, Filters

from jira import JIRA

# Замените на свои данные
TOKEN = '6680689043:AAGCgNna-mNYkdsD_i7O4i6daZin5D-w0gs'
JIRA_SERVER = 'https://jira.goods.ru/'
JIRA_USER = 'egorov'
JIRA_PASSWORD = 'Goods_20188'

jira = JIRA(server=JIRA_SERVER, basic_auth=(JIRA_USER, JIRA_PASSWORD))

chat_state = {}
chat_logins = {}

def start(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    if chat_id not in chat_logins:
        chat_state[chat_id] = {"stage": "login"}
        update.message.reply_text('Введите свой логин в Jira:')
    else:
        update.message.reply_text('Привет! Для создания нового тикета Jira используйте команду /create_task')

def create_task(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    chat_state[chat_id] = {"stage": "choice"}
    reply_keyboard = ReplyKeyboardMarkup([[KeyboardButton('Создать новую инструкцию')], 
                                          [KeyboardButton('Обновить инструкцию')]], 
                                         one_time_keyboard=True)
    update.message.reply_text('Что вы хотите сделать?', reply_markup=reply_keyboard)

def process_message(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id

    if chat_id not in chat_state:
        return

    data = chat_state[chat_id]

    if data["stage"] == "login":
        chat_logins[chat_id] = update.message.text
        del data["stage"]
        update.message.reply_text('Логин сохранен. Теперь вы можете создать задачу с помощью команды /create_task')
    elif data["stage"] == "choice":
        data["choice"] = update.message.text
        data["stage"] = "title"
        update.message.reply_text('Введите тему:')
    elif data["stage"] == "title":
        data["title"] = update.message.text
        if data["choice"] == "Обновить инструкцию":
            data["stage"] = "link"
            update.message.reply_text('Введите ссылку на инструкцию:')
        else:
            data["stage"] = "description"
            update.message.reply_text('Что нужно сделать?')
    elif data["stage"] == "link":
        data["link"] = update.message.text
        data["stage"] = "description"
        update.message.reply_text('Что нужно сделать?')
    elif data["stage"] == "description":
        data["description"] = update.message.text
        del data["stage"]

        if data["choice"] == "Обновить инструкцию":
            description_text = f'*Ссылка:* {data["link"]}\n\n*Что нужно сделать:* {data["description"]}'
            labels_choice = ['Обновление_инструкции_запрос']
        else:
            description_text = f'*Что нужно сделать:* {data["description"]}'
            labels_choice = ['Новая_инструкция_запрос']

        issue_dict = {
            'project': {'key': 'ISD'},
            'summary': data["title"],
            'description': description_text,
            'issuetype': {'name': 'История'},
            'labels': labels_choice,
            'reporter': {'name': chat_logins[chat_id]},
        }

        new_issue = jira.create_issue(issue_dict)
        update.message.reply_text(f'Тикет Jira успешно создан: [{new_issue.key}]({JIRA_SERVER}browse/{new_issue.key})', parse_mode='Markdown')

        del chat_state[chat_id]

def main():
    updater = Updater(TOKEN, use_context=True)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("create_task", create_task))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, process_message))

    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()
