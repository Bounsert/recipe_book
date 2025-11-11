import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import json
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

# --- 1. Конфігурація ---
app = Flask(__name__)
app.secret_key = 'super-secret-key-change-this-to-something-random' 

basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'recipes.db')
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static/uploads')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'index' 
login_manager.login_message_category = 'info'

# --- 2. МОДЕЛІ БАЗИ ДАНИХ ---

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(60), nullable=False)
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    reviews = db.relationship('Review', backref='author', lazy=True)

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(100), nullable=False)
    base_portions = db.Column(db.Integer, nullable=False, default=4)
    category = db.Column(db.String(50), nullable=False, default='classic')
    title_uk = db.Column(db.String(100), nullable=False)
    description_uk = db.Column(db.Text, nullable=False)
    ingredients_uk = db.Column(db.JSON, nullable=False) 
    instructions_uk = db.Column(db.Text, nullable=False)
    title_en = db.Column(db.String(100), nullable=False)
    description_en = db.Column(db.Text, nullable=False)
    ingredients_en = db.Column(db.JSON, nullable=False) 
    instructions_en = db.Column(db.Text, nullable=False)
    reviews = db.relationship('Review', backref='recipe', lazy=True)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    photo = db.Column(db.String(100), nullable=True) 
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# --- 3. СЛОВНИКИ ПЕРЕКЛАДІВ (UI) ---

TRANSLATIONS_UK = {
    "app_title": "Книга рецептів",
    "nav_title": "Книга рецептів",
    "nav_home": "Головна",
    "nav_classic": "Класичні рецепти",
    "nav_world": "Картопля у світі",
    "nav_soups": "Супи",
    "nav_calculator": "Калькулятор",
    "nav_login": "Увійти",
    "nav_register": "Реєстрація",
    "nav_logout": "Вийти",
    "nav_profile": "Профіль",
    "welcome_title": "Ласкаво просимо до Книги Рецептів!",
    "welcome_text": "Будь ласка, оберіть рецепт з меню вище, щоб почати.",
    "login_title": "Вхід",
    "register_title": "Реєстрація",
    "email_label": "Email",
    "password_label": "Пароль",
    "confirm_password_label": "Підтвердіть пароль",
    "profile_title": "Редагувати профіль",
    "profile_first_name": "Ім'я:",
    "profile_last_name": "Прізвище:",
    "profile_button_save": "Зберегти зміни",
    "profile_overlay_title": "Ваш профіль",
    "profile_overlay_name": "Ім'я:",
    "profile_overlay_surname": "Прізвище:",
    "profile_overlay_not_set": "Не вказано",
    "profile_overlay_edit_btn": "Редагувати профіль",
    "reviews_login_prompt": "Ви повинні увійти в акаунт, щоб залишити відгук.",
    "calculator_title": "Калькулятор інгредієнтів",
    "calculator_select": "Оберіть рецепт:",
    "calculator_select_default": "-- Оберіть --",
    "calculator_base_text_1": "Рецепт розрахований на",
    "calculator_base_text_2": "порції.",
    "calculator_portions_label": "Скільки порцій вам потрібно?",
    "calculator_button": "Перерахувати",
    "calculator_results_title_1": "Інгредієнти на",
    "calculator_results_title_2": "порцій:",
    "calculator_nutrition_title": "Орієнтовне БЖУ",
    "nutrition_total": "Всього на",
    "nutrition_protein": "Білки",
    "nutrition_fats": "Жири",
    "nutrition_carbs": "Вуглеводи",
    "nutrition_unit": "г",
    "recipe_ingredients_title": "Інгредієнти",
    "recipe_portions": "порції",
    "recipe_instructions": "Інструкція",
    "reviews_title": "Залишити відгук",
    "reviews_label_text": "Ваш відгук:",
    "reviews_label_photo": "Прикріпити фото (необов'язково):",
    "reviews_button": "Надіслати відгук",
    "reviews_existing_title": "Відгуки",
    "reviews_none": "Відгуків поки що немає. Будьте першим!",
    "potato_greeting": "Привіт! Я твій Картопляний Друг. Оберіть рецепт!",
    "potato_switch_tab": "О, подивимось цей рецепт!",
    "potato_calc_many": "Ого, {portions} порцій! Це буде вечірка!",
    "potato_calc_few": "Хм, сьогодні готуємо небагато!",
    "potato_calc_butter": "Ого, це ДУЖЕ багато масла!",
    "fact_1": "Чи знали ви, що до Європи картоплю спочатку завезли як декоративну рослину?",
    "fact_2": "У Франції Антуан-Огюст Пармантьє влаштував 'рекламну кампанію', виставивши озброєну охорону біля картопляних полів.",
    "fact_3": "Картопля стала першою овочем, вирощеним у космосі на борту шатлу 'Колумбія' у 1995 році.",
    "ad_1": "Спробуйте рецепти з усього світу! Наприклад, Іспанську Тортилью.",
    "ad_2": "Потрібно більше порцій? Використовуйте наш калькулятор!",
    "flash_password_mismatch": "Паролі не співпадають!",
    "flash_email_exists": "Користувач з таким email вже існує.",
    "flash_login_fail": "Неправильний email або пароль."
}

TRANSLATIONS_EN = {
    "app_title": "Recipe Book",
    "nav_title": "Recipe Book",
    "nav_home": "Home",
    "nav_classic": "Classic Recipes",
    "nav_world": "Potatoes in the World",
    "nav_soups": "Soups",
    "nav_calculator": "Calculator",
    "nav_login": "Login",
    "nav_register": "Register",
    "nav_logout": "Logout",
    "nav_profile": "Profile",
    "welcome_title": "Welcome to the Recipe Book!",
    "welcome_text": "Please select a recipe from the menu above to get started.",
    "login_title": "Login",
    "register_title": "Register",
    "email_label": "Email",
    "password_label": "Password",
    "confirm_password_label": "Confirm Password",
    "profile_title": "Edit Profile",
    "profile_first_name": "First Name:",
    "profile_last_name": "Last Name:",
    "profile_button_save": "Save Changes",
    "profile_overlay_title": "Your Profile",
    "profile_overlay_name": "Name:",
    "profile_overlay_surname": "Surname:",
    "profile_overlay_not_set": "Not set",
    "profile_overlay_edit_btn": "Edit Profile",
    "reviews_login_prompt": "You must be logged in to leave a review.",
    "calculator_title": "Ingredient Calculator",
    "calculator_select": "Select a recipe:",
    "calculator_select_default": "-- Select --",
    "calculator_base_text_1": "Recipe based on",
    "calculator_base_text_2": "portions.",
    "calculator_portions_label": "How many portions do you need?",
    "calculator_button": "Recalculate",
    "calculator_results_title_1": "Ingredients for",
    "calculator_results_title_2": "portions:",
    "calculator_nutrition_title": "Estimated Macros",
    "nutrition_total": "Total for",
    "nutrition_protein": "Protein",
    "nutrition_fats": "Fats",
    "nutrition_carbs": "Carbs",
    "nutrition_unit": "g",
    "recipe_ingredients_title": "Ingredients",
    "recipe_portions": "portions",
    "recipe_instructions": "Instructions",
    "reviews_title": "Leave a review",
    "reviews_label_text": "Your review:",
    "reviews_label_photo": "Attach a photo (optional):",
    "reviews_button": "Submit Review",
    "reviews_existing_title": "Reviews",
    "reviews_none": "No reviews yet. Be the first!",
    "potato_greeting": "Hi! I'm your Potato Buddy. Pick a recipe!",
    "potato_switch_tab": "Oh, let's check out this recipe!",
    "potato_calc_many": "Wow, {portions} portions! That's a party!",
    "potato_calc_few": "Hm, cooking just a little today!",
    "potato_calc_butter": "Whoa, that's a LOT of butter!",
    "fact_1": "Did you know that potatoes were first brought to Europe as an ornamental plant?",
    "fact_2": "In France, Antoine-Augustin Parmentier ran a 'publicity campaign' by placing armed guards around potato fields.",
    "fact_3": "The potato was the first vegetable to be grown in space aboard the Space Shuttle Columbia in 1995.",
    "ad_1": """Try recipes from around the world!
For example, the Spanish Tortilla.""",
    "ad_2": "Need more portions? Use our calculator!",
    "flash_password_mismatch": "Passwords do not match!",
    "flash_email_exists": "A user with this email already exists.",
    "flash_login_fail": "Incorrect email or password."
}


# --- 4. Маршрути (Логіка) ---
@app.route('/')
def index():
    lang = session.get('lang', 'uk')
    translations = TRANSLATIONS_EN if lang == 'en' else TRANSLATIONS_UK

    # Отримуємо вкладку помилки з URL
    error_tab = request.args.get('error_tab')

    classic_recipes = Recipe.query.filter_by(category='classic').all()
    world_recipes = Recipe.query.filter_by(category='world').all()
    soup_recipes = Recipe.query.filter_by(category='soup').all() 
    
    all_recipes = classic_recipes + world_recipes + soup_recipes
    
    return render_template(
        'index.html', 
        classic_recipes=classic_recipes, 
        world_recipes=world_recipes,
        soup_recipes=soup_recipes, 
        all_recipes=all_recipes,
        t=translations,
        lang=lang,
        error_tab=error_tab  # Передаємо в шаблон
    )

@app.route('/set_lang/<lang_code>')
def set_lang(lang_code):
    if lang_code in ['uk', 'en']:
        session['lang'] = lang_code
    return redirect(url_for('index'))

@app.route('/register', methods=['POST'])
def register():
    lang = session.get('lang', 'uk')
    t = TRANSLATIONS_EN if lang == 'en' else TRANSLATIONS_UK

    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    
    if password != confirm_password:
        flash(t.get('flash_password_mismatch'), 'danger') 
        return redirect(url_for('index', error_tab='register')) # Перенаправляємо з параметром
    
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        flash(t.get('flash_email_exists'), 'danger')
        return redirect(url_for('index', error_tab='register')) # Перенаправляємо з параметром
        
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    user = User(email=email, password_hash=hashed_password)
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    lang = session.get('lang', 'uk')
    t = TRANSLATIONS_EN if lang == 'en' else TRANSLATIONS_UK

    email = request.form.get('email')
    password = request.form.get('password')
    user = User.query.filter_by(email=email).first()
    
    if user and bcrypt.check_password_hash(user.password_hash, password):
        login_user(user)
        return redirect(url_for('index'))
    else:
        flash(t.get('flash_login_fail'), 'danger')
        return redirect(url_for('index', error_tab='login')) # Перенаправляємо з параметром

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    current_user.first_name = request.form.get('first_name')
    current_user.last_name = request.form.get('last_name')
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/add_review/<int:recipe_id>', methods=['POST'])
@login_required 
def add_review(recipe_id):
    review_text = request.form['review_text']
    uploaded_photo_path = None
    if 'review_photo' in request.files:
        file = request.files['review_photo']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            uploaded_photo_path = f'uploads/{filename}'
    new_review = Review(
        text=review_text, 
        photo=uploaded_photo_path, 
        recipe_id=recipe_id,
        user_id=current_user.id 
    )
    db.session.add(new_review)
    db.session.commit()
    return redirect(url_for('index'))

# --- 5. ІНІЦІАЛІЗАЦІЯ БД (ПОВНІ РЕЦЕПТИ З БЖУ ТА ФОТО СУПІВ) ---
def populate_db_if_empty():
    with app.app_context():
        db.create_all()
        
        if Recipe.query.count() == 0:
            print("База даних пуста, заповнюємо рецептами...")
            
            initial_recipes = [
                # --- КАРТОПЛЯНІ РЕЦЕПТИ ---
                Recipe(
                    image="images/derevenski.jpg", base_portions=4, category='classic',
                    title_uk="Картопля по-селянськи",
                    description_uk="Ароматні запечені скибочки картоплі у спеціях.",
                    ingredients_uk=[
                        {"name": "Картопля", "amount": 1, "unit": "кг", "p": 20, "f": 1, "c": 170},
                        {"name": "Паприка", "amount": 1, "unit": "ст.л.", "p": 0.5, "f": 0.5, "c": 3},
                        {"name": "Часник", "amount": 3, "unit": "зуб.", "p": 1, "f": 0, "c": 5},
                        {"name": "Олія", "amount": 3, "unit": "ст.л.", "p": 0, "f": 45, "c": 0},
                        {"name": "Сіль, перець", "amount": 0, "unit": "за смаком", "p": 0, "f": 0, "c": 0}
                    ],
                    instructions_uk="1. Картоплю добре вимити (можна не чистити) і нарізати скибочками.\n2. У мисці змішати олію, вичавлений часник, паприку, сіль та перець.\n3. Додати картоплю до маринаду і добре перемішати, щоб кожна скибочка була покрита.\n4. Викласти картоплю в один шар на деко, застелене пергаментом.\n5. Запікати 30-40 хвилин при 200°C, перегорнувши один раз в середині приготування для рівномірної скоринки.",
                    
                    title_en="Country-Style Potatoes",
                    description_en="Aromatic baked potato wedges with spices.",
                    ingredients_en=[
                        {"name": "Potatoes", "amount": 1, "unit": "kg", "p": 20, "f": 1, "c": 170},
                        {"name": "Paprika", "amount": 1, "unit": "tbsp", "p": 0.5, "f": 0.5, "c": 3},
                        {"name": "Garlic", "amount": 3, "unit": "cloves", "p": 1, "f": 0, "c": 5},
                        {"name": "Vegetable Oil", "amount": 3, "unit": "tbsp", "p": 0, "f": 45, "c": 0},
                        {"name": "Salt, pepper", "amount": 0, "unit": "to taste", "p": 0, "f": 0, "c": 0}
                    ],
                    instructions_en="1. Wash the potatoes well (skin on is fine) and cut into wedges.\n2. In a bowl, mix oil, minced garlic, paprika, salt, and pepper.\n3. Add the potatoes to the marinade and toss well to coat each wedge.\n4. Spread the potatoes in a single layer on a baking sheet lined with parchment paper.\n5. Bake for 30-40 minutes at 200°C (400°F), flipping once halfway through for an even crust."
                ),
                Recipe(
                    image="images/draniki.jpg", base_portions=4, category='classic',
                    title_uk="Класичні деруни",
                    description_uk="Традиційні білоруські картопляні оладки.",
                    ingredients_uk=[
                        {"name": "Картопля (велика)", "amount": 6, "unit": "шт.", "p": 18, "f": 1, "c": 153},
                        {"name": "Цибуля", "amount": 1, "unit": "шт.", "p": 1, "f": 0, "c": 9},
                        {"name": "Яйце", "amount": 1, "unit": "шт.", "p": 6, "f": 5, "c": 0.5},
                        {"name": "Борошно", "amount": 2, "unit": "ст.л.", "p": 5, "f": 0.5, "c": 38},
                        {"name": "Олія (для смаження)", "amount": 5, "unit": "ст.л.", "p": 0, "f": 75, "c": 0},
                        {"name": "Сіль", "amount": 0, "unit": "за смаком", "p": 0, "f": 0, "c": 0}
                    ],
                    instructions_uk="1. Картоплю та цибулю почистити і натерти на дрібній тертці.\n2. Перекласти масу у дрібне сито або марлю і добре віджати зайву рідину.\n3. Перекласти суху масу в миску, додати яйце, борошно, сіль та перець. Добре перемішати.\n4. Розігріти сковороду з олією. Викладати масу столовою ложкою, формуючи оладки.\n5. Смажити на середньому вогні до золотистої скоринки з обох боків.",
                    
                    title_en="Classic Draniki (Potato Pancakes)",
                    description_en="Traditional Belarusian potato pancakes.",
                    ingredients_en=[
                        {"name": "Potatoes (large)", "amount": 6, "unit": "pcs", "p": 18, "f": 1, "c": 153},
                        {"name": "Onion", "amount": 1, "unit": "pc", "p": 1, "f": 0, "c": 9},
                        {"name": "Egg", "amount": 1, "unit": "pc", "p": 6, "f": 5, "c": 0.5},
                        {"name": "Flour", "amount": 2, "unit": "tbsp", "p": 5, "f": 0.5, "c": 38},
                        {"name": "Oil (for frying)", "amount": 5, "unit": "tbsp", "p": 0, "f": 75, "c": 0},
                        {"name": "Salt", "amount": 0, "unit": "to taste", "p": 0, "f": 0, "c": 0}
                    ],
                    instructions_en="1. Grate potatoes and onion on a fine grater.\n2. Squeeze out excess liquid.\n3. Add egg, flour, salt, and mix well.\n4. Fry on a hot pan with oil until golden brown on both sides."
                ),
                Recipe(
                    image="images/puree.jpg", base_portions=4, category='classic',
                    title_uk="Картопляне пюре",
                    description_uk="Ніжне та повітряне пюре з молоком та маслом.",
                    ingredients_uk=[
                        {"name": "Картопля", "amount": 1, "unit": "кг", "p": 20, "f": 1, "c": 170},
                        {"name": "Молоко", "amount": 200, "unit": "мл", "p": 6.6, "f": 7, "c": 10},
                        {"name": "Вершкове масло", "amount": 50, "unit": "г", "p": 0.4, "f": 41, "c": 0},
                        {"name": "Сіль", "amount": 0, "unit": "за смаком", "p": 0, "f": 0, "c": 0}
                    ],
                    instructions_uk="1. Картоплю почистити, нарізати великими шматками та відварити у підсоленій воді до готовності (близько 20 хвилин).\n2. Поки картопля вариться, підігріти молоко (не кип'ятити).\n3. Злити всю воду з картоплі.\n4. Додати вершкове масло і почати товкти.\n5. Поступово вливати тепле молоко, продовжуючи товкти до досягнення бажаної консистенції.\n6. Посолити за смаком і добре перемішати.",
                    
                    title_en="Mashed Potatoes",
                    description_en="Soft and fluffy mashed potatoes with milk and butter.",
                    ingredients_en=[
                        {"name": "Potatoes", "amount": 1, "unit": "kg", "p": 20, "f": 1, "c": 170},
                        {"name": "Milk", "amount": 200, "unit": "ml", "p": 6.6, "f": 7, "c": 10},
                        {"name": "Butter", "amount": 50, "unit": "g", "p": 0.4, "f": 41, "c": 0},
                        {"name": "Salt", "amount": 0, "unit": "to taste", "p": 0, "f": 0, "c": 0}
                    ],
                    instructions_en="1. Peel, chop, and boil potatoes in salted water until tender (about 20 minutes).\n2. While potatoes are boiling, heat the milk (do not boil).\n3. Drain all the water from the potatoes.\n4. Add the butter and begin to mash.\n5. Gradually pour in the warm milk, continuing to mash until you reach the desired consistency.\n6. Salt to taste and mix well."
                ),
                Recipe(
                    image="images/tortilla.jpg", base_portions=6, category='world',
                    title_uk="Іспанська Тортилья",
                    description_uk="Знаменитий іспанський омлет з картоплею та цибулею.",
                    ingredients_uk=[
                        {"name": "Картопля", "amount": 500, "unit": "г", "p": 10, "f": 0.5, "c": 85},
                        {"name": "Яйця", "amount": 6, "unit": "шт.", "p": 36, "f": 30, "c": 3},
                        {"name": "Цибуля", "amount": 1, "unit": "шт.", "p": 1, "f": 0, "c": 9},
                        {"name": "Оливкова олія", "amount": 150, "unit": "мл", "p": 0, "f": 150, "c": 0},
                        {"name": "Сіль", "amount": 0, "unit": "за смаком", "p": 0, "f": 0, "c": 0}
                    ],
                    instructions_uk="1. Картоплю та цибулю почистити і тонко нарізати (картоплю кружальцями, цибулю півкільцями).\n2. Нагріти оливкову олію у великій сковороді. Додати картоплю та цибулю.\n3. Готувати на повільному вогні, помішуючи, 20-25 хвилин, доки картопля не стане м'якою, але не коричневою.\n4. У великій мисці збити яйця з сіллю.\n5. Вийняти картоплю та цибулю з олії шумівкою і дати стекти зайвій олії. Додати до збитих яєць.\n6. Дати суміші постояти 10-15 хвилин.\n7. На чистій сковороді розігріти трохи олії. Вилити яєчну суміш.\n8. Готувати на середньо-повільному вогні, доки краї не схопляться (близько 5-7 хвилин).\n9. Накрити сковороду великою тарілкою і впевнено перевернути тортилью на тарілку. Потім зсунути її назад у сковороду іншим боком.\n10. Готувати ще 3-5 хвилин. Подавати теплою або кімнатної температури.",

                    title_en="Spanish Tortilla",
                    description_en="A famous Spanish omelette with potatoes and onion.",
                    ingredients_en=[
                        {"name": "Potatoes", "amount": 500, "unit": "g", "p": 10, "f": 0.5, "c": 85},
                        {"name": "Eggs", "amount": 6, "unit": "pcs", "p": 36, "f": 30, "c": 3},
                        {"name": "Onion", "amount": 1, "unit": "pc", "p": 1, "f": 0, "c": 9},
                        {"name": "Olive Oil", "amount": 150, "unit": "ml", "p": 0, "f": 150, "c": 0},
                        {"name": "Salt", "amount": 0, "unit": "to taste", "p": 0, "f": 0, "c": 0}
                    ],
                    instructions_en="1. Peel and thinly slice the potatoes and onion (potatoes in rounds, onion in half-moons).\n2. Heat olive oil in a large skillet. Add potatoes and onion.\n3. Cook over low heat, stirring occasionally, for 20-25 minutes until potatoes are tender but not browned.\n4. In a large bowl, beat the eggs with salt.\n5. Remove the potatoes and onion from the oil with a slotted spoon, draining excess oil. Add them to the beaten eggs.\n6. Let the mixture sit for 10-15 minutes.\n7. Heat a little oil in a clean skillet. Pour in the egg mixture.\n8. Cook on medium-low heat until the edges are set (about 5-7 minutes).\n9. Cover the skillet with a large plate and confidently flip the tortilla onto the plate. Then, slide it back into the skillet on the other side.\n10. Cook for another 3-5 minutes. Serve warm or at room temperature."
                ),
                
                # --- СУПИ ---
                Recipe(
                    image="images/borscht.jpg", base_portions=6, category='soup',
                    title_uk="Борщ (Україна)", description_uk="Традиційний український суп на основі буряка.",
                    ingredients_uk=[
                        {"name": "Яловичина", "amount": 500, "unit": "г", "p": 105, "f": 80, "c": 0},
                        {"name": "Буряк", "amount": 2, "unit": "шт.", "p": 3.2, "f": 0.2, "c": 20},
                        {"name": "Картопля", "amount": 4, "unit": "шт.", "p": 8, "f": 0.4, "c": 68},
                        {"name": "Капуста", "amount": 300, "unit": "г", "p": 3.9, "f": 0.3, "c": 17},
                        {"name": "Морква", "amount": 1, "unit": "шт.", "p": 0.9, "f": 0.1, "c": 7},
                        {"name": "Цибуля", "amount": 1, "unit": "шт.", "p": 1.1, "f": 0.1, "c": 9},
                        {"name": "Томатна паста", "amount": 2, "unit": "ст.л.", "p": 2.5, "f": 0.2, "c": 10}
                    ],
                    instructions_uk="1. Зварити бульйон з м'яса (близько 1.5-2 годин).\n2. Дістати м'ясо, нарізати. Бульйон процідити.\n3. Нарізати картоплю кубиками, кинути в бульйон.\n4. Нашаткувати капусту, додати через 10 хвилин після картоплі.\n5. Зробити засмажку: натерти моркву та буряк, нарізати цибулю. Смажити цибулю та моркву на олії, потім додати буряк. Скропити оцтом (щоб зберіг колір).\n6. Додати томатну пасту, трохи бульйону і тушкувати 10-15 хв.\n7. Додати засмажку в суп. Варити ще 5-7 хвилин.\n8. Додати нарізане м'ясо, подрібнений часник, сіль, перець, лавровий лист.\n9. Дати настоятися 20 хвилин. Подавати зі сметаною та зеленню.",
                    
                    title_en="Borscht (Ukraine)", description_en="Traditional Ukrainian soup based on beetroot.",
                    ingredients_en=[
                        {"name": "Beef", "amount": 500, "unit": "g", "p": 105, "f": 80, "c": 0},
                        {"name": "Beets", "amount": 2, "unit": "pcs", "p": 3.2, "f": 0.2, "c": 20},
                        {"name": "Potatoes", "amount": 4, "unit": "pcs", "p": 8, "f": 0.4, "c": 68},
                        {"name": "Cabbage", "amount": 300, "unit": "g", "p": 3.9, "f": 0.3, "c": 17},
                        {"name": "Carrot", "amount": 1, "unit": "pc", "p": 0.9, "f": 0.1, "c": 7},
                        {"name": "Onion", "amount": 1, "unit": "pc", "p": 1.1, "f": 0.1, "c": 9},
                        {"name": "Tomato Paste", "amount": 2, "unit": "tbsp", "p": 2.5, "f": 0.2, "c": 10}
                    ],
                    instructions_en="1. Boil broth from the meat (about 1.5-2 hours).\n2. Remove meat, chop. Strain the broth.\n3. Dice potatoes, add to broth.\n4. Shred cabbage, add 10 minutes after potatoes.\n5. Make the 'zasmazhka': grate carrot and beets, chop onion. Sauté onion and carrot in oil, then add beets. Sprinkle with vinegar (to retain color).\n6. Add tomato paste, a little broth, and simmer for 10-15 min.\n7. Add the 'zasmazhka' to the soup. Cook for another 5-7 minutes.\n8. Add chopped meat, minced garlic, salt, pepper, bay leaf.\n9. Let it rest for 20 minutes. Serve with sour cream and herbs."
                ),
                Recipe(
                    image="images/french_onion_soup.jpg", base_portions=4, category='soup',
                    title_uk="Французький цибулевий суп", description_uk="Класичний ситний суп.",
                    ingredients_uk=[
                        {"name": "Цибуля", "amount": 1, "unit": "кг", "p": 11, "f": 1, "c": 90},
                        {"name": "Вершкове масло", "amount": 50, "unit": "г", "p": 0.4, "f": 41, "c": 0},
                        {"name": "Яловичий бульйон", "amount": 1.5, "unit": "л", "p": 15, "f": 5, "c": 5},
                        {"name": "Сухе біле вино", "amount": 200, "unit": "мл", "p": 0.2, "f": 0, "c": 5.2},
                        {"name": "Борошно", "amount": 1, "unit": "ст.л.", "p": 2.5, "f": 0.2, "c": 19},
                        {"name": "Багет", "amount": 1, "unit": "шт.", "p": 27, "f": 9, "c": 150},
                        {"name": "Сир Грюєр", "amount": 150, "unit": "г", "p": 45, "f": 49.5, "c": 0.5}
                    ],
                    instructions_uk="1. Нарізати цибулю тонкими півкільцями.\n2. У глибокій каструлі розтопити вершкове масло. Додати цибулю.\n3. Карамелізувати цибулю на повільному вогні, помішуючи, 30-40 хвилин до темно-коричневого кольору.\n4. Додати борошно, перемішати і смажити 1 хвилину.\n5. Влити вино, дати йому випаруватися наполовину.\n6. Влити гарячий яловичий бульйон. Додати сіль, перець. Варити 20 хвилин.\n7. Підсушити скибочки багета в духовці.\n8. Розлити суп у жароміцні горщики. Зверху покласти грінку, посипати тертим сиром.\n9. Поставити в розігріту до 200°C духовку (або під гриль) на 5-10 хвилин, доки сир не розплавиться і не стане золотистим.",
                    
                    title_en="French Onion Soup", description_en="A classic hearty soup.",
                    ingredients_en=[
                        {"name": "Onions", "amount": 1, "unit": "kg", "p": 11, "f": 1, "c": 90},
                        {"name": "Butter", "amount": 50, "unit": "g", "p": 0.4, "f": 41, "c": 0},
                        {"name": "Beef Broth", "amount": 1.5, "unit": "L", "p": 15, "f": 5, "c": 5},
                        {"name": "Dry White Wine", "amount": 200, "unit": "ml", "p": 0.2, "f": 0, "c": 5.2},
                        {"name": "Flour", "amount": 1, "unit": "tbsp", "p": 2.5, "f": 0.2, "c": 19},
                        {"name": "Baguette", "amount": 1, "unit": "pc", "p": 27, "f": 9, "c": 150},
                        {"name": "Gruyère Cheese", "amount": 150, "unit": "g", "p": 45, "f": 49.5, "c": 0.5}
                    ],
                    instructions_en="1. Thinly slice the onions into half-moons.\n2. Melt the butter in a large pot. Add onions.\n3. Caramelize the onions on low heat, stirring, for 30-40 minutes until deep brown.\n4. Add flour, stir, and cook for 1 minute.\n5. Pour in the wine, let it reduce by half.\n6. Pour in the hot beef broth. Add salt, pepper. Simmer for 20 minutes.\n7. Toast baguette slices in the oven.\n8. Ladle soup into oven-safe bowls. Top with a crouton, sprinkle with grated cheese.\n9. Place in a preheated 200°C (400°F) oven (or under the broiler) for 5-10 minutes, until cheese is melted and golden."
                ),
                Recipe(
                    image="images/minestrone.jpg", base_portions=6, category='soup',
                    title_uk="Мінестроне (Італія)",
                    description_uk="Густий італійський овочевий суп.",
                    ingredients_uk=[
                        {"name": "Оливкова олія", "amount": 3, "unit": "ст.л.", "p": 0, "f": 45, "c": 0},
                        {"name": "Цибуля", "amount": 1, "unit": "шт.", "p": 1.1, "f": 0.1, "c": 9},
                        {"name": "Морква", "amount": 2, "unit": "шт.", "p": 1.8, "f": 0.2, "c": 14},
                        {"name": "Селера", "amount": 2, "unit": "стебла", "p": 0.7, "f": 0.1, "c": 3},
                        {"name": "Цукіні", "amount": 1, "unit": "шт.", "p": 2.4, "f": 0.6, "c": 6.2},
                        {"name": "Помідори (конс.)", "amount": 400, "unit": "г", "p": 3.6, "f": 0.8, "c": 15.6},
                        {"name": "Бульйон", "amount": 1.5, "unit": "л", "p": 1, "f": 1, "c": 1},
                        {"name": "Квасоля (конс.)", "amount": 400, "unit": "г", "p": 24, "f": 2, "c": 88},
                        {"name": "Паста", "amount": 100, "unit": "г", "p": 13, "f": 1.5, "c": 75}
                    ],
                    instructions_uk="1. Нарізати цибулю, моркву та селеру.\n2. У великій каструлі розігріти олію. Смажити овочі 10 хвилин.\n3. Додати часник, смажити 1 хв.\n4. Додати нарізаний цукіні, помідори та бульйон. Довести до кипіння.\n5. Зменшити вогонь, варити 15 хвилин.\n6. Додати квасолю та пасту.\n7. Варити ще 10-12 хвилин.\n8. Подавати з пармезаном.",
                    
                    title_en="Minestrone (Italy)",
                    description_en="A thick Italian vegetable soup.",
                    ingredients_en=[
                        {"name": "Olive Oil", "amount": 3, "unit": "tbsp", "p": 0, "f": 45, "c": 0},
                        {"name": "Onion", "amount": 1, "unit": "pc", "p": 1.1, "f": 0.1, "c": 9},
                        {"name": "Carrots", "amount": 2, "unit": "pcs", "p": 1.8, "f": 0.2, "c": 14},
                        {"name": "Celery", "amount": 2, "unit": "stalks", "p": 0.7, "f": 0.1, "c": 3},
                        {"name": "Zucchini", "amount": 1, "unit": "pc", "p": 2.4, "f": 0.6, "c": 6.2},
                        {"name": "Canned Tomatoes", "amount": 400, "unit": "g", "p": 3.6, "f": 0.8, "c": 15.6},
                        {"name": "Broth", "amount": 1.5, "unit": "L", "p": 1, "f": 1, "c": 1},
                        {"name": "Canned Beans", "amount": 400, "unit": "g", "p": 24, "f": 2, "c": 88},
                        {"name": "Small Pasta", "amount": 100, "unit": "g", "p": 13, "f": 1.5, "c": 75}
                    ],
                    instructions_en="1. Chop onion, carrots, and celery.\n2. Heat oil in a large pot. Sauté vegetables for 10 minutes.\n3. Add garlic, cook 1 min.\n4. Add chopped zucchini, tomatoes, and broth. Bring to a boil.\n5. Reduce heat, simmer 15 minutes.\n6. Add beans and pasta.\n7. Cook for 10-12 more minutes.\n8. Serve with Parmesan."
                ),
                Recipe(
                    image="images/ramen.jpg", base_portions=2, category='soup',
                    title_uk="Рамен (Японія)",
                    description_uk="Популярний японський суп з локшиною.",
                    ingredients_uk=[
                        {"name": "Курячий бульйон", "amount": 1, "unit": "л", "p": 10, "f": 5, "c": 5},
                        {"name": "Соєвий соус", "amount": 3, "unit": "ст.л.", "p": 5.4, "f": 0, "c": 4.8},
                        {"name": "Місо-паста", "amount": 1, "unit": "ст.л.", "p": 2, "f": 1, "c": 4.8},
                        {"name": "Локшина Рамен", "amount": 200, "unit": "г", "p": 26, "f": 3, "c": 150},
                        {"name": "Свинина (чашу)", "amount": 200, "unit": "г", "p": 54, "f": 28, "c": 0},
                        {"name": "Яйця (варені)", "amount": 2, "unit": "шт.", "p": 12, "f": 10, "c": 1}
                    ],
                    instructions_uk="1. У каструлі змішати бульйон, соєвий соус, місо-пасту. Довести до кипіння.\n2. Окремо відварити локшину.\n3. Яйця зварити (6-7 хвилин), почистити, розрізати.\n4. М'ясо нарізати.\n5. У миски викласти локшину.\n6. Залити гарячим бульйоном.\n7. Зверху викласти м'ясо, яйця, зелену цибулю.",
                    
                    title_en="Ramen (Japan)",
                    description_en="A popular Japanese noodle soup.",
                    ingredients_en=[
                        {"name": "Chicken Broth", "amount": 1, "unit": "L", "p": 10, "f": 5, "c": 5},
                        {"name": "Soy Sauce", "amount": 3, "unit": "tbsp", "p": 5.4, "f": 0, "c": 4.8},
                        {"name": "Miso Paste", "amount": 1, "unit": "tbsp", "p": 2, "f": 1, "c": 4.8},
                        {"name": "Ramen Noodles", "amount": 200, "unit": "g", "p": 26, "f": 3, "c": 150},
                        {"name": "Pork (Chashu)", "amount": 200, "unit": "g", "p": 54, "f": 28, "c": 0},
                        {"name": "Boiled Eggs", "amount": 2, "unit": "pcs", "p": 12, "f": 10, "c": 1}
                    ],
                    instructions_en="1. In a pot, combine broth, soy sauce, miso paste. Bring to a boil.\n2. Separately, cook noodles.\n3. Boil eggs (6-7 minutes), peel, and cut.\n4. Slice the meat.\n5. Divide noodles into bowls.\n6. Pour hot broth over.\n7. Top with meat, eggs, and green onions."
                ),
                Recipe(
                    image="images/pho_bo.jpg", base_portions=2, category='soup',
                    title_uk="Фо Бо (В'єтнам)",
                    description_uk="В'єтнамський яловичий суп з локшиною.",
                    ingredients_uk=[
                        {"name": "Яловичі кістки", "amount": 1, "unit": "кг", "p": 200, "f": 150, "c": 0},
                        {"name": "Яловича вирізка", "amount": 300, "unit": "г", "p": 63, "f": 48, "c": 0},
                        {"name": "Цибуля", "amount": 2, "unit": "шт.", "p": 2.2, "f": 0.2, "c": 18},
                        {"name": "Імбир (корінь)", "amount": 5, "unit": "см", "p": 0.5, "f": 0.2, "c": 4},
                        {"name": "Рисова локшина", "amount": 200, "unit": "г", "p": 14, "f": 1, "c": 84}
                    ],
                    instructions_uk="1. Обсмалити цибулю та імбир. Очистити.\n2. Кістки залити водою, довести до кипіння, злити. Промити.\n3. Залити кістки чистою водою (3-4 л), додати цибулю, імбир, спеції. Варити 3-6 годин.\n4. Процідити бульйон.\n5. Вирізку нарізати тонкими скибочками.\n6. Рисову локшину замочити.\n7. У миску викласти локшину, сиру яловичину.\n8. Залити киплячим бульйоном.\n9. Подавати з лаймом, м'ятою, кінзою.",
                    
                    title_en="Pho Bo (Vietnam)",
                    description_en="A Vietnamese beef noodle soup.",
                    ingredients_en=[
                        {"name": "Beef Bones", "amount": 1, "unit": "kg", "p": 200, "f": 150, "c": 0},
                        {"name": "Beef Sirloin", "amount": 300, "unit": "g", "p": 63, "f": 48, "c": 0},
                        {"name": "Onions", "amount": 2, "unit": "pcs", "p": 2.2, "f": 0.2, "c": 18},
                        {"name": "Ginger (root)", "amount": 5, "unit": "cm", "p": 0.5, "f": 0.2, "c": 4},
                        {"name": "Rice Noodles", "amount": 200, "unit": "g", "p": 14, "f": 1, "c": 84}
                    ],
                    instructions_en="1. Char onions and ginger. Peel.\n2. Cover bones with water, boil, discard water. Rinse.\n3. Cover bones with clean water (3-4 L), add onion, ginger, spices. Simmer 3-6 hours.\n4. Strain broth.\n5. Slice sirloin paper-thin.\n6. Soak rice noodles.\n7. Place noodles and raw beef in a bowl.\n8. Pour boiling hot broth over.\n9. Serve with lime, mint, cilantro."
                ),
                Recipe(
                    image="images/tom_yum.jpg", base_portions=4, category='soup',
                    title_uk="Том Ям (Таїланд)",
                    description_uk="Гострий і кислий тайський суп з креветками.",
                    ingredients_uk=[
                        {"name": "Креветки", "amount": 400, "unit": "г", "p": 96, "f": 4, "c": 0},
                        {"name": "Курячий бульйон", "amount": 1, "unit": "л", "p": 10, "f": 5, "c": 5},
                        {"name": "Паста Том Ям", "amount": 2, "unit": "ст.л.", "p": 2, "f": 10, "c": 10},
                        {"name": "Кокосове молоко", "amount": 200, "unit": "мл", "p": 4, "f": 40, "c": 6},
                        {"name": "Гриби", "amount": 200, "unit": "г", "p": 6, "f": 0.6, "c": 6.4}
                    ],
                    instructions_uk="1. У каструлі довести бульйон до кипіння.\n2. Додати пасту Том Ям.\n3. Додати нарізані гриби. Варити 5 хвилин.\n4. Додати очищені креветки. Варити 2-3 хвилини.\n5. Додати помідори чері.\n6. Влити кокосове молоко та рибний соус. Прогріти, не кип'ятити.\n7. Зняти з вогню, додати сік лайма.",
                    
                    title_en="Tom Yum (Thailand)",
                    description_en="A hot and sour Thai soup with shrimp.",
                    ingredients_en=[
                        {"name": "Shrimp", "amount": 400, "unit": "g", "p": 96, "f": 4, "c": 0},
                        {"name": "Chicken Broth", "amount": 1, "unit": "L", "p": 10, "f": 5, "c": 5},
                        {"name": "Tom Yum Paste", "amount": 2, "unit": "tbsp", "p": 2, "f": 10, "c": 10},
                        {"name": "Coconut Milk", "amount": 200, "unit": "ml", "p": 4, "f": 40, "c": 6},
                        {"name": "Mushrooms", "amount": 200, "unit": "g", "p": 6, "f": 0.6, "c": 6.4}
                    ],
                    instructions_en="1. In a pot, bring the broth to a boil.\n2. Add Tom Yum paste.\n3. Add sliced mushrooms. Cook 5 minutes.\n4. Add peeled shrimp. Cook 2-3 minutes.\n5. Add cherry tomatoes.\n6. Pour in coconut milk and fish sauce. Heat, do not boil.\n7. Remove from heat, add lime juice."
                ),
                Recipe(
                    image="images/gazpacho.jpg", base_portions=4, category='soup',
                    title_uk="Гаспачо (Іспанія)",
                    description_uk="Холодний іспанський овочевий суп.",
                    ingredients_uk=[
                        {"name": "Помідори", "amount": 1, "unit": "кг", "p": 9, "f": 2, "c": 39},
                        {"name": "Огірок", "amount": 1, "unit": "шт.", "p": 1, "f": 0.2, "c": 5.4},
                        {"name": "Болгарський перець", "amount": 1, "unit": "шт.", "p": 1.3, "f": 0.3, "c": 6},
                        {"name": "Оливкова олія", "amount": 100, "unit": "мл", "p": 0, "f": 100, "c": 0},
                        {"name": "Черствий хліб", "amount": 50, "unit": "г", "p": 4.5, "f": 1.5, "c": 25}
                    ],
                    instructions_uk="1. Овочі грубо нарізати.\n2. Хліб замочити у воді, віджати.\n3. Скласти овочі та хліб у блендер.\n4. Додати оливкову олію, оцет, сіль.\n5. Збити до однорідної маси.\n6. Охолодити в холодильнику щонайменше 2 години.",
                    
                    title_en="Gazpacho (Spain)",
                    description_en="A cold Spanish vegetable soup.",
                    ingredients_en=[
                        {"name": "Ripe Tomatoes", "amount": 1, "unit": "kg", "p": 9, "f": 2, "c": 39},
                        {"name": "Cucumber", "amount": 1, "unit": "pc", "p": 1, "f": 0.2, "c": 5.4},
                        {"name": "Bell Pepper", "amount": 1, "unit": "pc", "p": 1.3, "f": 0.3, "c": 6},
                        {"name": "Olive Oil", "amount": 100, "unit": "ml", "p": 0, "f": 100, "c": 0},
                        {"name": "Stale Bread", "amount": 50, "unit": "g", "p": 4.5, "f": 1.5, "c": 25}
                    ],
                    instructions_en="1. Roughly chop vegetables.\n2. Soak bread in water, squeeze.\n3. Place vegetables and bread in a blender.\n4. Add olive oil, vinegar, salt.\n5. Blend until smooth.\n6. Chill in the refrigerator for at least 2 hours."
                ),
                Recipe(
                    image="images/chicken_noodle_soup.jpg", base_portions=4, category='soup',
                    title_uk="Курячий суп з локшиною",
                    description_uk="Заспокійливий класичний суп.",
                    ingredients_uk=[
                        {"name": "Курка", "amount": 1, "unit": "кг", "p": 270, "f": 140, "c": 0},
                        {"name": "Морква", "amount": 2, "unit": "шт.", "p": 1.8, "f": 0.2, "c": 14},
                        {"name": "Селера", "amount": 2, "unit": "стебла", "p": 0.7, "f": 0.1, "c": 3},
                        {"name": "Цибуля", "amount": 1, "unit": "шт.", "p": 1.1, "f": 0.1, "c": 9},
                        {"name": "Яєчна локшина", "amount": 200, "unit": "г", "p": 28, "f": 4, "c": 140}
                    ],
                    instructions_uk="1. Покласти курку у каструлю, залити водою. Довести до кипіння, зняти піну.\n2. Додати цибулю, моркву, селеру. Варити 1.5 години.\n3. Вийняти курку та овочі. Бульйон процідити.\n4. Відокремити м'ясо курки від кісток, нарізати.\n5. Повернути бульйон на вогонь. Додати м'ясо.\n6. Всипати локшину і варити до готовності (5-7 хвилин).\n7. Додати сіль, перець, зелень.",
                    
                    title_en="Chicken Noodle Soup",
                    description_en="A comforting classic soup.",
                    ingredients_en=[
                        {"name": "Chicken", "amount": 1, "unit": "kg", "p": 270, "f": 140, "c": 0},
                        {"name": "Carrots", "amount": 2, "unit": "pcs", "p": 1.8, "f": 0.2, "c": 14},
                        {"name": "Celery", "amount": 2, "unit": "stalks", "p": 0.7, "f": 0.1, "c": 3},
                        {"name": "Onion", "amount": 1, "unit": "pc", "p": 1.1, "f": 0.1, "c": 9},
                        {"name": "Egg Noodles", "amount": 200, "unit": "g", "p": 28, "f": 4, "c": 140}
                    ],
                    instructions_en="1. Place chicken in a pot, cover with water. Bring to a boil, skim foam.\n2. Add onion, carrots, celery. Simmer 1.5 hours.\n3. Remove chicken and vegetables. Strain broth.\n4. Shred chicken meat.\n5. Return broth to pot. Add meat.\n6. Add noodles and cook until al dente (5-7 minutes).\n7. Add salt, pepper, and herbs."
                ),
                Recipe(
                    image="images/miso_soup.jpg", base_portions=4, category='soup',
                    title_uk="Місо-суп (Японія)",
                    description_uk="Традиційний японський суп.",
                    ingredients_uk=[
                        {"name": "Бульйон Дасі", "amount": 800, "unit": "мл", "p": 2, "f": 0.2, "c": 1},
                        {"name": "Місо-паста", "amount": 3, "unit": "ст.л.", "p": 6, "f": 3, "c": 14.4},
                        {"name": "Тофу (шовковий)", "amount": 150, "unit": "г", "p": 12, "f": 7.5, "c": 4.5},
                        {"name": "Водорості Вакаме (сухі)", "amount": 1, "unit": "ст.л.", "p": 0.5, "f": 0.1, "c": 2}
                    ],
                    instructions_uk="1. Замочити Вакаме у воді.\n2. Нарізати тофу кубиками.\n3. Нагріти Дасі (не кип'ятити).\n4. Розвести місо-пасту у невеликій кількості бульйону, влити у каструлю.\n5. Додати Вакаме та тофу. Прогріти 1-2 хвилини (не кип'ятити).\n6. Подавати, посипавши зеленою цибулею.",
                    
                    title_en="Miso Soup (Japan)",
                    description_en="A traditional Japanese soup.",
                    ingredients_en=[
                        {"name": "Dashi Stock", "amount": 800, "unit": "ml", "p": 2, "f": 0.2, "c": 1},
                        {"name": "Miso Paste", "amount": 3, "unit": "tbsp", "p": 6, "f": 3, "c": 14.4},
                        {"name": "Silken Tofu", "amount": 150, "unit": "g", "p": 12, "f": 7.5, "c": 4.5},
                        {"name": "Dried Wakame", "amount": 1, "unit": "tbsp", "p": 0.5, "f": 0.1, "c": 2}
                    ],
                    instructions_en="1. Soak Wakame in water.\n2. Cube the tofu.\n3. Heat Dashi (do not boil).\n4. Dissolve miso paste in a little broth, add to pot.\n5. Add Wakame and tofu. Heat for 1-2 minutes (do not boil).\n6. Serve, garnished with green onion."
                ),
                Recipe(
                    image="images/clam_chowder.jpg", base_portions=4, category='soup',
                    title_uk="Клем-чаудер (США)",
                    description_uk="Густий кремовий суп з молюсків.",
                    ingredients_uk=[
                        {"name": "Бекон", "amount": 100, "unit": "г", "p": 14, "f": 42, "c": 1.5},
                        {"name": "Цибуля", "amount": 1, "unit": "шт.", "p": 1.1, "f": 0.1, "c": 9},
                        {"name": "Картопля", "amount": 2, "unit": "шт.", "p": 4, "f": 0.2, "c": 34},
                        {"name": "Борошно", "amount": 2, "unit": "ст.л.", "p": 5, "f": 0.5, "c": 38},
                        {"name": "Молоко", "amount": 500, "unit": "мл", "p": 16.5, "f": 17.5, "c": 25},
                        {"name": "Вершки (20%)", "amount": 200, "unit": "мл", "p": 5, "f": 40, "c": 8},
                        {"name": "Молюски (конс.)", "amount": 200, "unit": "г", "p": 28, "f": 2, "c": 6}
                    ],
                    instructions_uk="1. Нарізати бекон і обсмажити. Вийняти.\n2. Нарізати цибулю. Смажити на жирі від бекону.\n3. Додати борошно, смажити 1 хвилину.\n4. Поступово влити молоко, помішуючи.\n5. Нарізати картоплю дрібними кубиками, додати в суп. Варити 15-20 хвилин.\n6. Додати вершки та молюски. Прогріти 5 хвилин.\n7. Додати сіль, перець та бекон.",
                    
                    title_en="Clam Chowder (USA)",
                    description_en="A thick, creamy soup made with clams.",
                    ingredients_en=[
                        {"name": "Bacon", "amount": 100, "unit": "g", "p": 14, "f": 42, "c": 1.5},
                        {"name": "Onion", "amount": 1, "unit": "pc", "p": 1.1, "f": 0.1, "c": 9},
                        {"name": "Potatoes", "amount": 2, "unit": "pcs", "p": 4, "f": 0.2, "c": 34},
                        {"name": "Flour", "amount": 2, "unit": "tbsp", "p": 5, "f": 0.5, "c": 38},
                        {"name": "Milk", "amount": 500, "unit": "ml", "p": 16.5, "f": 17.5, "c": 25},
                        {"name": "Heavy Cream (20%)", "amount": 200, "unit": "ml", "p": 5, "f": 40, "c": 8},
                        {"name": "Canned Clams", "amount": 200, "unit": "g", "p": 28, "f": 2, "c": 6}
                    ],
                    instructions_en="1. Dice bacon and fry. Remove.\n2. Chop onion. Sauté in bacon fat.\n3. Add flour, cook 1 minute.\n4. Gradually whisk in milk.\n5. Dice potatoes, add to soup. Cook 15-20 minutes.\n6. Add cream and clams. Heat 5 minutes.\n7. Add salt, pepper, and bacon."
                )
            ]
            
            db.session.bulk_save_objects(initial_recipes)
            db.session.commit()
            print(f"Рецепти (всього {len(initial_recipes)}) додано.")
        else:
            print("База даних вже заповнена.")

if __name__ == '__main__':
    populate_db_if_empty()
    app.run(debug=True)