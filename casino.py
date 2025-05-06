import random
import telebot
from telebot import types

# Конфигурация
TOKEN = '7891481051:AAHMiTc0AVlDK_1zXCENykyiR1eh0hTh89A'
ADMIN_USERNAME = "@work_with_mvd"  # Ваш юзернейм для пополнений
CHANNEL_ID = '@MMMillion_casino'  # Замените на username вашего канала
ADMIN_ID = 7400244823 # Замените на свой ID

bot = telebot.TeleBot(TOKEN)

# База данных пользователей
users = {}

# Стандартные ставки
BET_AMOUNTS = [50, 100, 200, 500, 1000, 5000, 10000]

# Команда старт
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if user_id not in users:
        users[user_id] = {
            'balance': 0,
            'username': message.from_user.username or str(user_id),
            'games_played': 0,
            'total_wins': 0
        }

    markup = main_menu_markup()
    bot.send_message(message.chat.id,
                    f"🎉 Добро пожаловать в виртуальное казино!\n"
                    f"💵 Ваш баланс: {users[user_id]['balance']}$\n"
                    f"📢 Результаты игр публикуются в канале: {CHANNEL_ID}",
                    reply_markup=markup)


# --- Главное меню с кнопкой пополнения ---
def main_menu_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton('🎰 Слоты')
    btn2 = types.KeyboardButton('🎯 Рулетка')
    btn3 = types.KeyboardButton('🎲 Кости')
    btn4 = types.KeyboardButton('💰 Баланс')
    btn5 = types.KeyboardButton('💳 Пополнить баланс')
    markup.add(btn1, btn2, btn3, btn4, btn5)
    return markup

# --- Обработка нехватки средств ---
def handle_low_balance(message, game_name, min_bet):
    user_id = message.from_user.id
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💌 Написать админу", url=f"https://t.me/{ADMIN_USERNAME[1:]}"))
    
    bot.send_message(
        message.chat.id,
        f"❌ Недостаточно средств!\n\n"
        f"Для игры в {game_name} нужно минимум {min_bet}$.\n"
        f"Ваш баланс: {users[user_id]['balance']}\n\n"
        f"📩 Для пополнения обратитесь к администратору ",
        reply_markup=markup
    )
    
    # Уведомление админу
    bot.send_message(
        CHANNEL_ID,
        f"⚠️ @{users[user_id]['username']} нуждается в пополнении!\n"
        f"Текущий баланс: {users[user_id]['balance']}\n"
        f"Требуется для {game_name}: {min_bet}"
    )

# --- Команда пополнения ---
@bot.message_handler(func=lambda msg: msg.text == '💳 Пополнить баланс')
def deposit_menu(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📩 Написать админу", url=f"https://t.me/{ADMIN_USERNAME[1:]}"))
    
    bot.send_message(
        message.chat.id,
        f"💳 Пополнение баланса\n\n"
        f"Для пополнения обратитесь к администратору \n"
        f"Укажите ваш ID: `{message.from_user.id}`",
        reply_markup=markup,
        parse_mode="Markdown"
    )

def bet_amounts_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    buttons = [types.KeyboardButton(str(amount)) for amount in BET_AMOUNTS]
    buttons.append(types.KeyboardButton('Отмена'))
    markup.add(*buttons)
    return markup

# Админ команда
@bot.message_handler(commands=['admin'], func=lambda message: message.from_user.id == ADMIN_ID)
def admin_panel(message):
    markup = types.InlineKeyboardMarkup()
    for user_id, user_data in users.items():
        markup.add(types.InlineKeyboardButton(user_data['username'], callback_data=f'add_credits_{user_id}'))
    markup.add(types.InlineKeyboardButton("Себе", callback_data=f'add_credits_{ADMIN_ID}'))
    bot.send_message(message.chat.id, "Выберите пользователя для зачисления $:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('add_credits_'))
def add_credits_callback(call):
    user_id = int(call.data.split('_')[2])
    bot.send_message(call.message.chat.id, f"Введите сумму для зачисления пользователю {users[user_id]['username']}:")
    bot.register_next_step_handler(call.message, process_credit_addition, user_id)

def process_credit_addition(message, user_id):
    try:
        amount = int(message.text)
        if amount <= 0:
            raise ValueError("Сумма должна быть положительной")

        users[user_id]['balance'] += amount
        bot.send_message(message.chat.id, f"Пользователю {users[user_id]['username']} зачислено {amount}$. Новый баланс: {users[user_id]['balance']}")
        bot.send_message(
            user_id,
            f"💰 Администратор пополнил ваш баланс на {amount}$!\n"
            f"Текущий баланс: {users[user_id]['balance']}"
        )

    except ValueError as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

# Обработка кнопок
@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.from_user.id
    if user_id not in users:
        users[user_id] = {
            'balance': 0,
            'username': message.from_user.username or str(user_id),
            'games_played': 0,
            'total_wins': 0
        }

    if message.text == '💰 Баланс':
        show_balance(message)
    elif message.text == '🎰 Слоты':
        ask_bet_amount(message, 'slots')
    elif message.text == '🎯 Рулетка':
        ask_bet_amount(message, 'roulette')
    elif message.text == '🎲 Кости':
        ask_bet_amount(message, 'dice')
    elif message.text == '🏆 Топ игроков':
        show_top_players(message)

def ask_bet_amount(message, game_type):
    user_id = message.from_user.id
    bot.send_message(message.chat.id,
                    f"💵 Ваш баланс: {users[user_id]['balance']}$\n"
                    f"Введите сумму ставки или выберите из предложенных:",
                    reply_markup=bet_amounts_markup())
    bot.register_next_step_handler(message, process_bet_amount, game_type)

def process_bet_amount(message, game_type):
    user_id = message.from_user.id

    if message.text == 'Отмена':
        bot.send_message(message.chat.id, "❌ Действие отменено", reply_markup=main_menu_markup())
        return

    try:
        bet = int(message.text)
        if bet <= 0:
            bot.send_message(message.chat.id, "❌ Ставка должна быть положительной!", reply_markup=main_menu_markup())
            return
        if bet > users[user_id]['balance']:
            bot.send_message(message.chat.id, "❌ Недостаточно средств на балансе!", reply_markup=main_menu_markup())
            return
    except ValueError:
        bot.send_message(message.chat.id, "❌ Пожалуйста, введите число!", reply_markup=main_menu_markup())
        return

    if game_type == 'slots':
        play_slots(message, bet)
    elif game_type == 'roulette':
        play_roulette(message, bet)
    elif game_type == 'dice':
        start_dice_game(message, bet)

def show_balance(message):
    user_id = message.from_user.id
    stats = (
        f"📊 Ваша статистика:\n"
        f"💰 Баланс: {users[user_id]['balance']}$\n"
        f"🎮 Сыграно игр: {users[user_id]['games_played']}\n"
        f"🏆 Побед: {users[user_id]['total_wins']}\n"
        f"📈 Процент побед: {users[user_id]['total_wins']/users[user_id]['games_played']*100 if users[user_id]['games_played'] > 0 else 0:.1f}%"
    )
    bot.send_message(message.chat.id, stats)

def show_top_players(message):
    sorted_users = sorted(users.items(), key=lambda x: x[1]['balance'], reverse=True)[:10]
    top_list = "🏆 ТОП-10 игроков по балансу:\n\n"
    for i, (user_id, data) in enumerate(sorted_users, 1):
        top_list += f"{i}. @{data['username']} - {data['balance']}$\n"
    bot.send_message(message.chat.id, top_list)

def post_to_channel(text):
    try:
        bot.send_message(CHANNEL_ID, text)
    except Exception as e:
        print(f"Ошибка при отправке в канал: {e}")

def update_stats(user_id, is_win):
    users[user_id]['games_played'] += 1
    if is_win:
        users[user_id]['total_wins'] += 1

# ===== ИГРА В СЛОТЫ =====
def play_slots(message, bet):
    user_id = message.from_user.id
    username = users[user_id]['username']

    users[user_id]['balance'] -= bet

    symbols = ['🍒', '🍋', '🍊', '🍇', '🔔', '7️⃣']
    result = [random.choice(symbols) for _ in range(3)]

    if result[0] == result[1] == result[2]:
        win = bet * 3  # Джекпот x10
    elif result[0] == result[1] or result[1] == result[2]:
        win = bet * 1.1  # x3 за 2 одинаковых
    else:
        win = 0

    users[user_id]['balance'] += win
    is_win = win > 0
    update_stats(user_id, is_win)

    # Сообщение пользователю
    user_message = (
        f"🎰 Результат: {' '.join(result)} 🎰\n"
        f"Ставка: {bet}$\n"
        f"Вы {'выиграли' if is_win else 'проиграли'} {win if is_win else bet}$!\n"
        f"💰 Новый баланс: {users[user_id]['balance']}"
    )
    bot.send_message(message.chat.id, user_message, reply_markup=main_menu_markup())

    # Сообщение в канал
    channel_message = (
        f"🎰 Игрок @{username} сыграл в слоты:\n"
        f"Ставка: {bet}$\n"
        f"Результат: {' '.join(result)}\n"
        f"Статус: {'🟢 ВЫИГРЫШ' if is_win else '🔴 ПРОИГРЫШ'}\n"
        f"Сумма: {'+' + str(win) if is_win else '-' + str(bet)}$\n"
        f"#слоты #казино"
    )
    post_to_channel(channel_message)

# ===== РУЛЕТКА =====
def play_roulette(message, bet):
    user_id = message.from_user.id
    username = users[user_id]['username']

    markup = types.InlineKeyboardMarkup(row_width=3)
    btn_red = types.InlineKeyboardButton('🔴 Красное (x2)', callback_data=f'roulette_red_{bet}')
    btn_black = types.InlineKeyboardButton('⚫ Чёрное (x2)', callback_data=f'roulette_black_{bet}')
    btn_green = types.InlineKeyboardButton('🟢 Зелёное (x14)', callback_data=f'roulette_green_{bet}')
    markup.add(btn_red, btn_black, btn_green)

    bot.send_message(message.chat.id, f"🎯 Ставка: {bet}$\nВыберите цвет:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('roulette_'))
def handle_roulette_bet(call):
    user_id = call.from_user.id
    username = users[user_id]['username']
    _, color, bet = call.data.split('_')
    bet = int(bet)

    users[user_id]['balance'] -= bet

    result = random.randint(0, 36)
    if result == 0:
        actual_color = 'green'
    elif 1 <= result <= 10 or 19 <= result <= 28:
        actual_color = 'red' if result % 2 == 1 else 'black'
    else:
        actual_color = 'black' if result % 2 == 1 else 'red'

    if color == actual_color:
        if color == 'green':
            win = bet * 5  # x14 за зелёное
        else:
            win = bet * 1.3   # x2 за красное/чёрное
    else:
        win = 0

    users[user_id]['balance'] += win
    is_win = win > 0
    update_stats(user_id, is_win)

    # Сообщение пользователю
    user_message = (
        f"🎯 Результат рулетки: {result} ({'🔴' if actual_color == 'red' else '⚫' if actual_color == 'black' else '🟢'})\n"
        f"Ставка: {bet}$ на {color}\n"
        f"Вы {'выиграли' if is_win else 'проиграли'} {win if is_win else bet}$!\n"
        f"💰 Новый баланс: {users[user_id]['balance']}"
    )
    bot.send_message(call.message.chat.id, user_message, reply_markup=main_menu_markup())

    # Сообщение в канал
    color_name = {'red': 'красное', 'black': 'чёрное', 'green': 'зелёное'}[color]
    channel_message = (
        f"🎯 Игрок @{username} сыграл в рулетку:\n"
        f"Ставка: {bet}$ на {color_name} ({'x14' if color == 'green' else 'x2'})\n"
        f"Выпало: {result} ({'🔴' if actual_color == 'red' else '⚫' if actual_color == 'black' else '🟢'})\n"
        f"Статус: {'🟢 ВЫИГРЫШ' if is_win else '🔴 ПРОИГРЫШ'}\n"
        f"Сумма: {'+' + str(win) if is_win else '-' + str(bet)}$\n"
        f"#рулетка #казино"
    )
    post_to_channel(channel_message)

    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

# ===== ИГРА В КОСТИ =====
def start_dice_game(message, bet):
    user_id = message.from_user.id
    username = users[user_id]['username']

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton('Больше')
    btn2 = types.KeyboardButton('Меньше')
    btn3 = types.KeyboardButton('Равно')
    btn4 = types.KeyboardButton('Отмена')
    markup.add(btn1, btn2, btn3, btn4)

    bot.send_message(message.chat.id,
                    f"🎲 Ваша ставка: {bet}$\n"
                    f"Выберите прогноз:\n"
                    f"• Больше - сумма костей >7 (x1.3)\n"
                    f"• Меньше - сумма костей <7 (x1.3)\n"
                    f"• Равно - сумма костей =7 (x2)",
                    reply_markup=markup)

    users[user_id]['current_bet'] = bet
    bot.register_next_step_handler(message, process_dice_choice)

def process_dice_choice(message):
    user_id = message.from_user.id
    username = users[user_id]['username']

    if message.text == 'Отмена':
        bot.send_message(message.chat.id, "❌ Игра отменена", reply_markup=main_menu_markup())
        return

    choice = message.text.lower()
    if choice not in ['больше', 'меньше', 'равно']:
        bot.send_message(message.chat.id, "❌ Пожалуйста, выберите один из вариантов!", reply_markup=main_menu_markup())
        return

    bet = users[user_id]['current_bet']
    users[user_id]['balance'] -= bet

    # Бросаем кости
    dice1 = random.randint(1, 6)
    dice2 = random.randint(1, 6)
    total = dice1 + dice2

    # Определяем результат
    if (choice == 'больше' and total > 7) or \
       (choice == 'меньше' and total < 7) or \
       (choice == 'равно' and total == 7):

        if choice == 'равно':
            multiplier = 2  # x5 за точное угадывание
        else:
            multiplier = 1.3  # x2 за больше/меньше

        win = bet * multiplier
        users[user_id]['balance'] += win
        result_text = f"🎲 Победа! +{win}$"
        is_win = True
    else:
        result_text = f"🎲 Проигрыш! -{bet}$"
        is_win = False

    update_stats(user_id, is_win)

    # Сообщение пользователю
    user_message = (
        f"🎲 Результат броска: {dice1} + {dice2} = {total}\n"
        f"Ваш прогноз: {choice.capitalize()}\n"
        f"Ставка: {bet}$\n"
        f"{result_text}\n"
        f"💰 Новый баланс: {users[user_id]['balance']}"
    )
    bot.send_message(message.chat.id, user_message, reply_markup=main_menu_markup())

# Сообщение в канал
    channel_message = (
        f"🎲 Игрок @{username} сыграл в кости:\n"
        f"Ставка: {bet}$\n"
        f"Прогноз: {choice.capitalize()} ({'x5' if choice == 'равно' else 'x2'})\n"
        f"Результат: {dice1} + {dice2} = {total}\n"
        f"Статус: {'🟢 ВЫИГРЫШ' if is_win else '🔴 ПРОИГРЫШ'}\n"
        f"Сумма: {'+' + str(win) if is_win else '-' + str(bet)}$\n"
        f"#кости #казино"
    )
    post_to_channel(channel_message)

# --- Команда для админа (ручное пополнение) ---
@bot.message_handler(commands=['add_balance'])
def admin_add_balance(message):
    if not message.from_user.username == ADMIN_USERNAME[1:]:  # Проверка админа
        return
    
    try:
        _, user_id, amount = message.text.split()
        amount = int(amount)
        
        if user_id not in users:
            bot.send_message(message.chat.id, "❌ Пользователь не найден!")
            return
            
        users[user_id]['balance'] += amount
        bot.send_message(
            message.chat.id,
            f"✅ Баланс пользователя {user_id} пополнен на {amount}$\n"
            f"Новый баланс: {users[user_id]['balance']}"
        )
        
        # Уведомление пользователю
        bot.send_message(
            user_id,
            f"💰 Администратор пополнил ваш баланс на {amount}$!\n"
            f"Текущий баланс: {users[user_id]['balance']}"
        )
    except:
        bot.send_message(message.chat.id, "❌ Формат: /add_balance user_id amount")

if __name__ == '__main__':
    print("Бот казино запущен...Misha poshel nahuy")
    bot.polling(none_stop=True)
    print("Misha poshel nahuy")