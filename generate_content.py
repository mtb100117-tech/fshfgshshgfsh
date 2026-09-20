#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор контента для приложения "Языки детям".

Порядок уроков:
  1. Алфавит (первый урок — с него начинается обучение)
  2. Диалоги (10 бытовых сцен)
  3. Тематические уроки-словари (15 тем)

Арабский текст — с полной огласовкой (tashkeel).
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


# ============================================================
# АЛФАВИТ
# ============================================================

ALPHABET = {
    "en": [
        ("A a", "эй"), ("B b", "би"), ("C c", "си"), ("D d", "ди"),
        ("E e", "и"),  ("F f", "эф"), ("G g", "джи"), ("H h", "эйч"),
        ("I i", "ай"), ("J j", "джей"), ("K k", "кей"), ("L l", "эл"),
        ("M m", "эм"), ("N n", "эн"), ("O o", "оу"), ("P p", "пи"),
        ("Q q", "кью"), ("R r", "ар"), ("S s", "эс"), ("T t", "ти"),
        ("U u", "ю"), ("V v", "ви"), ("W w", "дабл-ю"), ("X x", "экс"),
        ("Y y", "уай"), ("Z z", "зед"),
    ],
    "ar": [
        ("ا", "алиф"), ("ب", "ба"),  ("ت", "та"),   ("ث", "са"),
        ("ج", "джим"), ("ح", "ха"),  ("خ", "ха"),   ("د", "даль"),
        ("ذ", "заль"), ("ر", "ра"),  ("ز", "зай"),  ("س", "син"),
        ("ش", "шин"),  ("ص", "сад"), ("ض", "дад"),  ("ط", "та"),
        ("ظ", "за"),   ("ع", "айн"), ("غ", "гайн"), ("ف", "фа"),
        ("ق", "каф"),  ("ك", "кяф"), ("ل", "лям"),  ("م", "мим"),
        ("ن", "нун"),  ("ه", "ха"),  ("و", "вав"),  ("ي", "йа"),
    ],
    "zh": [
        ("一", "один",      "yī"),
        ("二", "два",       "èr"),
        ("三", "три",       "sān"),
        ("四", "четыре",    "sì"),
        ("五", "пять",      "wǔ"),
        ("六", "шесть",     "liù"),
        ("七", "семь",      "qī"),
        ("八", "восемь",    "bā"),
        ("九", "девять",    "jiǔ"),
        ("十", "десять",    "shí"),
        ("人", "человек",   "rén"),
        ("大", "большой",   "dà"),
        ("小", "маленький", "xiǎo"),
        ("上", "вверх",     "shàng"),
        ("下", "вниз",      "xià"),
    ],
}


# ============================================================
# ДИАЛОГИ
# ============================================================

DIALOGS = {
    "greeting": {
        "icon": "👋",
        "name": {"en": "Greeting", "ar": "التَّحِيَّة", "zh": "问候", "ru": "Приветствие"},
        "lines": [
            {"speaker": {"en": "Mom", "ar": "أُمِّي", "zh": "妈妈", "ru": "Мама"},
             "text": {"en": "Hello!", "ar": "!مَرْحَبًا", "zh": "你好！", "ru": "Привет!"},
             "zh_pinyin": "nǐ hǎo!"},
            {"speaker": {"en": "Child", "ar": "الطِّفْل", "zh": "宝宝", "ru": "Малыш"},
             "text": {"en": "Hi, Mom!", "ar": "!أَهْلًا يَا أُمِّي", "zh": "妈妈好！", "ru": "Привет, мама!"},
             "zh_pinyin": "māma hǎo!"},
            {"speaker": {"en": "Mom", "ar": "أُمِّي", "zh": "妈妈", "ru": "Мама"},
             "text": {"en": "How are you?", "ar": "كَيْفَ حَالُك؟", "zh": "你好吗？", "ru": "Как ты?"},
             "zh_pinyin": "nǐ hǎo ma?"},
            {"speaker": {"en": "Child", "ar": "الطِّفْل", "zh": "宝宝", "ru": "Малыш"},
             "text": {"en": "I am fine, thank you!", "ar": "!أَنَا بِخَيْر، شُكْرًا", "zh": "我很好，谢谢！", "ru": "Хорошо, спасибо!"},
             "zh_pinyin": "wǒ hěn hǎo, xièxie!"},
        ],
    },
    "family": {
        "icon": "👨‍👩‍👧",
        "name": {"en": "Family", "ar": "الْعَائِلَة", "zh": "家人", "ru": "Семья"},
        "lines": [
            {"speaker": {"en": "Child", "ar": "الطِّفْل", "zh": "宝宝", "ru": "Малыш"},
             "text": {"en": "Look! This is my family.", "ar": ".اُنْظُر! هَذِهِ عَائِلَتِي", "zh": "看！这是我的家人。", "ru": "Смотри! Это моя семья."},
             "zh_pinyin": "kàn! zhè shì wǒ de jiārén."},
            {"speaker": {"en": "Mom", "ar": "أُمِّي", "zh": "妈妈", "ru": "Мама"},
             "text": {"en": "Who is this?", "ar": "مَنْ هَذَا؟", "zh": "这是谁？", "ru": "Кто это?"},
             "zh_pinyin": "zhè shì shéi?"},
            {"speaker": {"en": "Child", "ar": "الطِّفْل", "zh": "宝宝", "ru": "Малыш"},
             "text": {"en": "This is my dad.", "ar": "هَذَا أَبِي", "zh": "这是我爸爸。", "ru": "Это мой папа."},
             "zh_pinyin": "zhè shì wǒ bàba."},
            {"speaker": {"en": "Child", "ar": "الطِّفْل", "zh": "宝宝", "ru": "Малыш"},
             "text": {"en": "And this is my sister.", "ar": "وَهَذِهِ أُخْتِي", "zh": "这是我姐姐。", "ru": "А это моя сестра."},
             "zh_pinyin": "zhè shì wǒ jiějie."},
        ],
    },
    "food": {
        "icon": "🍎",
        "name": {"en": "Food", "ar": "الطَّعَام", "zh": "吃饭", "ru": "Еда"},
        "lines": [
            {"speaker": {"en": "Child", "ar": "الطِّفْل", "zh": "宝宝", "ru": "Малыш"},
             "text": {"en": "I am hungry.", "ar": "أَنَا جَائِع", "zh": "我饿了。", "ru": "Я голоден."},
             "zh_pinyin": "wǒ è le."},
            {"speaker": {"en": "Mom", "ar": "أُمِّي", "zh": "妈妈", "ru": "Мама"},
             "text": {"en": "Do you want an apple?", "ar": "هَلْ تُرِيدُ تُفَّاحَة؟", "zh": "你想吃苹果吗？", "ru": "Хочешь яблоко?"},
             "zh_pinyin": "nǐ xiǎng chī píngguǒ ma?"},
            {"speaker": {"en": "Child", "ar": "الطِّفْل", "zh": "宝宝", "ru": "Малыш"},
             "text": {"en": "Yes, please!", "ar": "!نَعَمْ، مِنْ فَضْلِك", "zh": "好的，谢谢！", "ru": "Да, пожалуйста!"},
             "zh_pinyin": "hǎo de, xièxie!"},
            {"speaker": {"en": "Mom", "ar": "أُمِّي", "zh": "妈妈", "ru": "Мама"},
             "text": {"en": "Here you are.", "ar": "تَفَضَّل", "zh": "给你。", "ru": "Держи."},
             "zh_pinyin": "gěi nǐ."},
            {"speaker": {"en": "Child", "ar": "الطِّفْل", "zh": "宝宝", "ru": "Малыш"},
             "text": {"en": "Thank you!", "ar": "!شُكْرًا", "zh": "谢谢！", "ru": "Спасибо!"},
             "zh_pinyin": "xièxie!"},
        ],
    },
    "play": {
        "icon": "🎮",
        "name": {"en": "Play", "ar": "اللَّعِب", "zh": "玩耍", "ru": "Игра"},
        "lines": [
            {"speaker": {"en": "Child", "ar": "الطِّفْل", "zh": "宝宝", "ru": "Малыш"},
             "text": {"en": "Let's play!", "ar": "!هَيَّا نَلْعَب", "zh": "我们玩吧！", "ru": "Давай играть!"},
             "zh_pinyin": "wǒmen wán ba!"},
            {"speaker": {"en": "Friend", "ar": "الصَّدِيق", "zh": "朋友", "ru": "Друг"},
             "text": {"en": "OK! What is this?", "ar": "!حَسَنًا! مَا هَذَا؟", "zh": "好！这是什么？", "ru": "Хорошо! Что это?"},
             "zh_pinyin": "hǎo! zhè shì shénme?"},
            {"speaker": {"en": "Child", "ar": "الطِّفْل", "zh": "宝宝", "ru": "Малыш"},
             "text": {"en": "It is a ball.", "ar": "إِنَّهَا كُرَة", "zh": "这是球。", "ru": "Это мяч."},
             "zh_pinyin": "zhè shì qiú."},
            {"speaker": {"en": "Friend", "ar": "الصَّدِيق", "zh": "朋友", "ru": "Друг"},
             "text": {"en": "I like it!", "ar": "!أُحِبُّهَا", "zh": "我喜欢！", "ru": "Мне нравится!"},
             "zh_pinyin": "wǒ xǐhuan!"},
            {"speaker": {"en": "Child", "ar": "الطِّفْل", "zh": "宝宝", "ru": "Малыш"},
             "text": {"en": "Me too!", "ar": "!وَأَنَا أَيْضًا", "zh": "我也是！", "ru": "Мне тоже!"},
             "zh_pinyin": "wǒ yě shì!"},
        ],
    },
    "animal_sounds": {
        "icon": "🐾",
        "name": {"en": "Animal sounds", "ar": "أَصْوَات الْحَيَوَانَات", "zh": "动物叫声", "ru": "Голоса животных"},
        "lines": [
            {"speaker": {"en": "Child", "ar": "الطِّفْل", "zh": "宝宝", "ru": "Малыш"},
             "text": {"en": "What does the cat say?", "ar": "مَاذَا تَقُولُ الْقِطَّة؟", "zh": "猫怎么叫？", "ru": "Как говорит кошка?"},
             "zh_pinyin": "māo zěnme jiào?"},
            {"speaker": {"en": "Mom", "ar": "أُمِّي", "zh": "妈妈", "ru": "Мама"},
             "text": {"en": "The cat says meow!", "ar": "!الْقِطَّة تَقُول: مِيَاو", "zh": "猫喵喵叫！", "ru": "Кошка говорит: мяу!"},
             "zh_pinyin": "māo miāomiāo jiào!"},
            {"speaker": {"en": "Child", "ar": "الطِّفْل", "zh": "宝宝", "ru": "Малыш"},
             "text": {"en": "What does the dog say?", "ar": "مَاذَا يَقُولُ الْكَلْب؟", "zh": "狗怎么叫？", "ru": "Как говорит собака?"},
             "zh_pinyin": "gǒu zěnme jiào?"},
            {"speaker": {"en": "Mom", "ar": "أُمِّي", "zh": "妈妈", "ru": "Мама"},
             "text": {"en": "The dog says woof!", "ar": "!الْكَلْب يَقُول: هَاو هَاو", "zh": "狗汪汪叫！", "ru": "Собака говорит: гав!"},
             "zh_pinyin": "gǒu wāngwāng jiào!"},
            {"speaker": {"en": "Child", "ar": "الطِّفْل", "zh": "宝宝", "ru": "Малыш"},
             "text": {"en": "I like animals!", "ar": "!أُحِبُّ الْحَيَوَانَات", "zh": "我喜欢动物！", "ru": "Я люблю животных!"},
             "zh_pinyin": "wǒ xǐhuan dòngwù!"},
        ],
    },
    "bedtime": {
        "icon": "🌙",
        "name": {"en": "Bedtime", "ar": "وَقْت النَّوْم", "zh": "睡前", "ru": "Перед сном"},
        "lines": [
            {"speaker": {"en": "Mom", "ar": "أُمِّي", "zh": "妈妈", "ru": "Мама"},
             "text": {"en": "It is time to sleep.", "ar": "وَقْت النَّوْم", "zh": "该睡觉了。", "ru": "Пора спать."},
             "zh_pinyin": "gāi shuìjiào le."},
            {"speaker": {"en": "Child", "ar": "الطِّفْل", "zh": "宝宝", "ru": "Малыш"},
             "text": {"en": "Good night, Mom!", "ar": "!تُصْبِحِينَ عَلَى خَيْر يَا أُمِّي", "zh": "妈妈晚安！", "ru": "Спокойной ночи, мама!"},
             "zh_pinyin": "māma wǎn'ān!"},
            {"speaker": {"en": "Mom", "ar": "أُمِّي", "zh": "妈妈", "ru": "Мама"},
             "text": {"en": "Good night, sweetheart.", "ar": "تُصْبِحُ عَلَى خَيْر يَا حَبِيبِي", "zh": "宝贝晚安。", "ru": "Спокойной ночи, малыш."},
             "zh_pinyin": "bǎobèi wǎn'ān."},
            {"speaker": {"en": "Child", "ar": "الطِّفْل", "zh": "宝宝", "ru": "Малыш"},
             "text": {"en": "See you tomorrow!", "ar": "!أَرَاك غَدًا", "zh": "明天见！", "ru": "До завтра!"},
             "zh_pinyin": "míngtiān jiàn!"},
            {"speaker": {"en": "Mom", "ar": "أُمِّي", "zh": "妈妈", "ru": "Мама"},
             "text": {"en": "Sleep well!", "ar": "!نَمْ جَيِّدًا", "zh": "睡个好觉！", "ru": "Сладких снов!"},
             "zh_pinyin": "shuì ge hǎo jiào!"},
        ],
    },
    "counting": {
        "icon": "🔢",
        "name": {"en": "Counting", "ar": "الْعَدّ", "zh": "数数", "ru": "Счёт"},
        "lines": [
            {"speaker": {"en": "Child", "ar": "الطِّفْل", "zh": "宝宝", "ru": "Малыш"},
             "text": {"en": "How many apples?", "ar": "كَمْ تُفَّاحَة؟", "zh": "有几个苹果？", "ru": "Сколько яблок?"},
             "zh_pinyin": "yǒu jǐ gè píngguǒ?"},
            {"speaker": {"en": "Mom", "ar": "أُمِّي", "zh": "妈妈", "ru": "Мама"},
             "text": {"en": "One, two, three!", "ar": "!وَاحِد، اِثْنَان، ثَلَاثَة", "zh": "一、二、三！", "ru": "Один, два, три!"},
             "zh_pinyin": "yī, èr, sān!"},
            {"speaker": {"en": "Child", "ar": "الطِّفْل", "zh": "宝宝", "ru": "Малыш"},
             "text": {"en": "Three apples!", "ar": "!ثَلَاث تُفَّاحَات", "zh": "三个苹果！", "ru": "Три яблока!"},
             "zh_pinyin": "sān gè píngguǒ!"},
            {"speaker": {"en": "Mom", "ar": "أُمِّي", "zh": "妈妈", "ru": "Мама"},
             "text": {"en": "Yes, three apples.", "ar": ".نَعَمْ، ثَلَاث تُفَّاحَات", "zh": "对，三个苹果。", "ru": "Да, три яблока."},
             "zh_pinyin": "duì, sān gè píngguǒ."},
            {"speaker": {"en": "Child", "ar": "الطِّفْل", "zh": "宝宝", "ru": "Малыш"},
             "text": {"en": "One for you, two for me!", "ar": "!وَاحِدَة لَك، اِثْنَتَان لِي", "zh": "一个给你，两个给我！", "ru": "Одно тебе, два мне!"},
             "zh_pinyin": "yī gè gěi nǐ, liǎng gè gěi wǒ!"},
        ],
    },
    "shop": {
        "icon": "🛒",
        "name": {"en": "At the shop", "ar": "فِي الْمَتْجَر", "zh": "在商店", "ru": "В магазине"},
        "lines": [
            {"speaker": {"en": "Mom", "ar": "أُمِّي", "zh": "妈妈", "ru": "Мама"},
             "text": {"en": "Let's go to the shop.", "ar": ".هَيَّا نَذْهَب إِلَى الْمَتْجَر", "zh": "我们去商店吧。", "ru": "Пойдём в магазин."},
             "zh_pinyin": "wǒmen qù shāngdiàn ba."},
            {"speaker": {"en": "Child", "ar": "الطِّفْل", "zh": "宝宝", "ru": "Малыш"},
             "text": {"en": "I want a toy.", "ar": "أُرِيد لُعْبَة", "zh": "我要一个玩具。", "ru": "Я хочу игрушку."},
             "zh_pinyin": "wǒ yào yī gè wánjù."},
            {"speaker": {"en": "Seller", "ar": "الْبَائِع", "zh": "售货员", "ru": "Продавец"},
             "text": {"en": "Hello! What do you want?", "ar": "!مَرْحَبًا! مَاذَا تُرِيد", "zh": "你好！你想要什么？", "ru": "Здравствуйте! Что вы хотите?"},
             "zh_pinyin": "nǐ hǎo! nǐ yào shénme?"},
            {"speaker": {"en": "Child", "ar": "الطِّفْل", "zh": "宝宝", "ru": "Малыш"},
             "text": {"en": "A red ball, please.", "ar": ".كُرَة حَمْرَاء، مِنْ فَضْلِك", "zh": "一个红球，谢谢。", "ru": "Красный мяч, пожалуйста."},
             "zh_pinyin": "yī gè hóng qiú, xièxie."},
            {"speaker": {"en": "Seller", "ar": "الْبَائِع", "zh": "售货员", "ru": "Продавец"},
             "text": {"en": "Here you are.", "ar": "تَفَضَّل", "zh": "给你。", "ru": "Держите."},
             "zh_pinyin": "gěi nǐ."},
            {"speaker": {"en": "Child", "ar": "الطِّفْل", "zh": "宝宝", "ru": "Малыш"},
             "text": {"en": "Thank you!", "ar": "!شُكْرًا", "zh": "谢谢！", "ru": "Спасибо!"},
             "zh_pinyin": "xièxie!"},
        ],
    },
    "school": {
        "icon": "🏫",
        "name": {"en": "At school", "ar": "فِي الْمَدْرَسَة", "zh": "在学校", "ru": "В школе"},
        "lines": [
            {"speaker": {"en": "Teacher", "ar": "الْمُعَلِّم", "zh": "老师", "ru": "Учитель"},
             "text": {"en": "Good morning, children!", "ar": "!صَبَاح الْخَيْر يَا أَطْفَال", "zh": "孩子们，早上好！", "ru": "Доброе утро, дети!"},
             "zh_pinyin": "háizimen, zǎoshang hǎo!"},
            {"speaker": {"en": "Children", "ar": "الْأَطْفَال", "zh": "孩子们", "ru": "Дети"},
             "text": {"en": "Good morning!", "ar": "!صَبَاح الْخَيْر", "zh": "早上好！", "ru": "Доброе утро!"},
             "zh_pinyin": "zǎoshang hǎo!"},
            {"speaker": {"en": "Teacher", "ar": "الْمُعَلِّم", "zh": "老师", "ru": "Учитель"},
             "text": {"en": "Open your books, please.", "ar": ".اِفْتَحُوا كُتُبَكُم، مِنْ فَضْلِكُم", "zh": "请打开你们的书。", "ru": "Откройте книги, пожалуйста."},
             "zh_pinyin": "qǐng dǎkāi nǐmen de shū."},
            {"speaker": {"en": "Child", "ar": "الطِّفْل", "zh": "宝宝", "ru": "Малыш"},
             "text": {"en": "Where is my book?", "ar": "أَيْنَ كِتَابِي؟", "zh": "我的书在哪儿？", "ru": "Где моя книга?"},
             "zh_pinyin": "wǒ de shū zài nǎr?"},
            {"speaker": {"en": "Teacher", "ar": "الْمُعَلِّم", "zh": "老师", "ru": "Учитель"},
             "text": {"en": "It is on the desk.", "ar": ".إِنَّهُ عَلَى الْمَكْتَب", "zh": "在桌子上。", "ru": "На парте."},
             "zh_pinyin": "zài zhuōzi shàng."},
            {"speaker": {"en": "Child", "ar": "الطِّفْل", "zh": "宝宝", "ru": "Малыш"},
             "text": {"en": "Thank you!", "ar": "!شُكْرًا", "zh": "谢谢！", "ru": "Спасибо!"},
             "zh_pinyin": "xièxie!"},
        ],
    },
    "doctor": {
        "icon": "🩺",
        "name": {"en": "At the doctor", "ar": "عِنْد الطَّبِيب", "zh": "看医生", "ru": "У врача"},
        "lines": [
            {"speaker": {"en": "Mom", "ar": "أُمِّي", "zh": "妈妈", "ru": "Мама"},
             "text": {"en": "We are at the doctor.", "ar": ".نَحْنُ عِنْد الطَّبِيب", "zh": "我们到医生这里了。", "ru": "Мы у врача."},
             "zh_pinyin": "wǒmen dào yīshēng zhèlǐ le."},
            {"speaker": {"en": "Doctor", "ar": "الطَّبِيب", "zh": "医生", "ru": "Врач"},
             "text": {"en": "Hello! How are you?", "ar": "!مَرْحَبًا! كَيْفَ حَالُك", "zh": "你好！你怎么样？", "ru": "Здравствуй! Как ты?"},
             "zh_pinyin": "nǐ hǎo! nǐ zěnmeyàng?"},
            {"speaker": {"en": "Child", "ar": "الطِّفْل", "zh": "宝宝", "ru": "Малыш"},
             "text": {"en": "I have a headache.", "ar": ".لَدَيَّ صُدَاع", "zh": "我头疼。", "ru": "У меня болит голова."},
             "zh_pinyin": "wǒ tóu téng."},
            {"speaker": {"en": "Doctor", "ar": "الطَّبِيب", "zh": "医生", "ru": "Врач"},
             "text": {"en": "Open your mouth, please.", "ar": ".اِفْتَح فَمَك، مِنْ فَضْلِك", "zh": "请张开嘴。", "ru": "Открой рот, пожалуйста."},
             "zh_pinyin": "qǐng zhāngkāi zuǐ."},
            {"speaker": {"en": "Doctor", "ar": "الطَّبِيب", "zh": "医生", "ru": "Врач"},
             "text": {"en": "Drink water and rest.", "ar": ".اِشْرَب الْمَاء وَارْتَح", "zh": "多喝水，好好休息。", "ru": "Пей воду и отдыхай."},
             "zh_pinyin": "hē shuǐ, hǎohǎo xiūxi."},
            {"speaker": {"en": "Mom", "ar": "أُمِّي", "zh": "妈妈", "ru": "Мама"},
             "text": {"en": "Thank you, doctor!", "ar": "!شُكْرًا يَا دُكْتُور", "zh": "谢谢医生！", "ru": "Спасибо, доктор!"},
             "zh_pinyin": "xièxie yīshēng!"},
        ],
    },
}


# ============================================================
# ТЕМАТИЧЕСКИЕ УРОКИ-СЛОВАРИ
# ============================================================

TOPICS = {
    "animals": {
        "icon": "🐾",
        "name": {"en": "Animals", "ar": "حَيَوَانَات", "zh": "动物", "ru": "Животные"},
        "words": [
            {"id": "cat", "en": "Cat", "ar": "قِطَّة", "zh": "猫", "pinyin": "māo", "ru": "Кошка", "emoji": "🐱"},
            {"id": "dog", "en": "Dog", "ar": "كَلْب", "zh": "狗", "pinyin": "gǒu", "ru": "Собака", "emoji": "🐶"},
            {"id": "bird", "en": "Bird", "ar": "طَائِر", "zh": "鸟", "pinyin": "niǎo", "ru": "Птица", "emoji": "🐦"},
            {"id": "fish", "en": "Fish", "ar": "سَمَكَة", "zh": "鱼", "pinyin": "yú", "ru": "Рыба", "emoji": "🐟"},
            {"id": "horse", "en": "Horse", "ar": "حِصَان", "zh": "马", "pinyin": "mǎ", "ru": "Лошадь", "emoji": "🐴"},
            {"id": "cow", "en": "Cow", "ar": "بَقَرَة", "zh": "牛", "pinyin": "niú", "ru": "Корова", "emoji": "🐮"},
            {"id": "elephant", "en": "Elephant", "ar": "فِيل", "zh": "大象", "pinyin": "dàxiàng", "ru": "Слон", "emoji": "🐘"},
            {"id": "lion", "en": "Lion", "ar": "أَسَد", "zh": "狮子", "pinyin": "shīzi", "ru": "Лев", "emoji": "🦁"},
            {"id": "pig", "en": "Pig", "ar": "خِنْزِير", "zh": "猪", "pinyin": "zhū", "ru": "Свинья", "emoji": "🐷"},
            {"id": "rabbit", "en": "Rabbit", "ar": "أَرْنَب", "zh": "兔子", "pinyin": "tùzi", "ru": "Кролик", "emoji": "🐰"},
        ]
    },
    "food": {
        "icon": "🍎",
        "name": {"en": "Food", "ar": "طَعَام", "zh": "食物", "ru": "Еда"},
        "words": [
            {"id": "apple", "en": "Apple", "ar": "تُفَّاحَة", "zh": "苹果", "pinyin": "píngguǒ", "ru": "Яблоко", "emoji": "🍎"},
            {"id": "banana", "en": "Banana", "ar": "مَوْز", "zh": "香蕉", "pinyin": "xiāngjiāo", "ru": "Банан", "emoji": "🍌"},
            {"id": "bread", "en": "Bread", "ar": "خُبْز", "zh": "面包", "pinyin": "miànbāo", "ru": "Хлеб", "emoji": "🍞"},
            {"id": "milk", "en": "Milk", "ar": "حَلِيب", "zh": "牛奶", "pinyin": "niúnǎi", "ru": "Молоко", "emoji": "🥛"},
            {"id": "water", "en": "Water", "ar": "مَاء", "zh": "水", "pinyin": "shuǐ", "ru": "Вода", "emoji": "💧"},
            {"id": "cheese", "en": "Cheese", "ar": "جُبْن", "zh": "奶酪", "pinyin": "nǎilào", "ru": "Сыр", "emoji": "🧀"},
            {"id": "egg", "en": "Egg", "ar": "بَيْضَة", "zh": "鸡蛋", "pinyin": "jīdàn", "ru": "Яйцо", "emoji": "🥚"},
            {"id": "meat", "en": "Meat", "ar": "لَحْم", "zh": "肉", "pinyin": "ròu", "ru": "Мясо", "emoji": "🍖"},
            {"id": "orange", "en": "Orange", "ar": "بُرْتُقَال", "zh": "橙子", "pinyin": "chéngzi", "ru": "Апельсин", "emoji": "🍊"},
            {"id": "rice", "en": "Rice", "ar": "أَرُز", "zh": "米饭", "pinyin": "mǐfàn", "ru": "Рис", "emoji": "🍚"},
        ]
    },
    "family": {
        "icon": "👨‍👩‍👧",
        "name": {"en": "Family", "ar": "عَائِلَة", "zh": "家庭", "ru": "Семья"},
        "words": [
            {"id": "mom", "en": "Mom", "ar": "أُمّ", "zh": "妈妈", "pinyin": "māma", "ru": "Мама", "emoji": "👩"},
            {"id": "dad", "en": "Dad", "ar": "أَب", "zh": "爸爸", "pinyin": "bàba", "ru": "Папа", "emoji": "👨"},
            {"id": "sister", "en": "Sister", "ar": "أُخْت", "zh": "姐姐", "pinyin": "jiějie", "ru": "Сестра", "emoji": "👧"},
            {"id": "brother", "en": "Brother", "ar": "أَخ", "zh": "哥哥", "pinyin": "gēge", "ru": "Брат", "emoji": "👦"},
            {"id": "baby", "en": "Baby", "ar": "طِفْل", "zh": "宝宝", "pinyin": "bǎobao", "ru": "Малыш", "emoji": "👶"},
            {"id": "friend", "en": "Friend", "ar": "صَدِيق", "zh": "朋友", "pinyin": "péngyou", "ru": "Друг", "emoji": "🧑‍🤝‍🧑"},
            {"id": "grandma", "en": "Grandma", "ar": "جَدَّة", "zh": "奶奶", "pinyin": "nǎinai", "ru": "Бабушка", "emoji": "👵"},
            {"id": "grandpa", "en": "Grandpa", "ar": "جَدّ", "zh": "爷爷", "pinyin": "yéye", "ru": "Дедушка", "emoji": "👴"},
        ]
    },
    "colors": {
        "icon": "🎨",
        "name": {"en": "Colors", "ar": "أَلْوَان", "zh": "颜色", "ru": "Цвета"},
        "words": [
            {"id": "red", "en": "Red", "ar": "أَحْمَر", "zh": "红色", "pinyin": "hóngsè", "ru": "Красный", "emoji": "🔴"},
            {"id": "blue", "en": "Blue", "ar": "أَزْرَق", "zh": "蓝色", "pinyin": "lánsè", "ru": "Синий", "emoji": "🔵"},
            {"id": "green", "en": "Green", "ar": "أَخْضَر", "zh": "绿色", "pinyin": "lǜsè", "ru": "Зелёный", "emoji": "🟢"},
            {"id": "yellow", "en": "Yellow", "ar": "أَصْفَر", "zh": "黄色", "pinyin": "huángsè", "ru": "Жёлтый", "emoji": "🟡"},
            {"id": "black", "en": "Black", "ar": "أَسْوَد", "zh": "黑色", "pinyin": "hēisè", "ru": "Чёрный", "emoji": "⚫"},
            {"id": "white", "en": "White", "ar": "أَبْيَض", "zh": "白色", "pinyin": "báisè", "ru": "Белый", "emoji": "⚪"},
            {"id": "orange", "en": "Orange", "ar": "بُرْتُقَالِي", "zh": "橙色", "pinyin": "chéngsè", "ru": "Оранжевый", "emoji": "🟠"},
            {"id": "pink", "en": "Pink", "ar": "وَرْدِي", "zh": "粉色", "pinyin": "fěnsè", "ru": "Розовый", "emoji": "🩷"},
        ]
    },
    "weather": {
        "icon": "🌤️",
        "name": {"en": "Weather", "ar": "طَقْس", "zh": "天气", "ru": "Погода"},
        "words": [
            {"id": "sun", "en": "Sun", "ar": "شَمْس", "zh": "太阳", "pinyin": "tàiyáng", "ru": "Солнце", "emoji": "☀️"},
            {"id": "rain", "en": "Rain", "ar": "مَطَر", "zh": "雨", "pinyin": "yǔ", "ru": "Дождь", "emoji": "🌧️"},
            {"id": "snow", "en": "Snow", "ar": "ثَلْج", "zh": "雪", "pinyin": "xuě", "ru": "Снег", "emoji": "❄️"},
            {"id": "cloud", "en": "Cloud", "ar": "سَحَابَة", "zh": "云", "pinyin": "yún", "ru": "Облако", "emoji": "☁️"},
        ]
    },
    "clothes": {
        "icon": "👕",
        "name": {"en": "Clothes", "ar": "مَلَابِس", "zh": "衣服", "ru": "Одежда"},
        "words": [
            {"id": "shirt", "en": "Shirt", "ar": "قَمِيص", "zh": "衬衫", "pinyin": "chènshān", "ru": "Рубашка", "emoji": "👕"},
            {"id": "pants", "en": "Pants", "ar": "بَنْطَلُون", "zh": "裤子", "pinyin": "kùzi", "ru": "Штаны", "emoji": "👖"},
            {"id": "shoes", "en": "Shoes", "ar": "أَحْذِيَة", "zh": "鞋子", "pinyin": "xiézi", "ru": "Обувь", "emoji": "👟"},
            {"id": "hat", "en": "Hat", "ar": "قُبَّعَة", "zh": "帽子", "pinyin": "màozi", "ru": "Шапка", "emoji": "🧢"},
        ]
    },
    "emotions": {
        "icon": "😊",
        "name": {"en": "Emotions", "ar": "مَشَاعِر", "zh": "情绪", "ru": "Эмоции"},
        "words": [
            {"id": "happy", "en": "Happy", "ar": "سَعِيد", "zh": "高兴", "pinyin": "gāoxìng", "ru": "Счастливый", "emoji": "😊"},
            {"id": "sad", "en": "Sad", "ar": "حَزِين", "zh": "伤心", "pinyin": "shāngxīn", "ru": "Грустный", "emoji": "😢"},
            {"id": "angry", "en": "Angry", "ar": "غَاضِب", "zh": "生气", "pinyin": "shēngqì", "ru": "Злой", "emoji": "😠"},
            {"id": "tired", "en": "Tired", "ar": "مُتْعَب", "zh": "累", "pinyin": "lèi", "ru": "Усталый", "emoji": "😴"},
        ]
    },
    "numbers": {
        "icon": "🔢",
        "name": {"en": "Numbers", "ar": "أَرْقَام", "zh": "数字", "ru": "Числа"},
        "words": [
            {"id": "one", "en": "One", "ar": "وَاحِد", "zh": "一", "pinyin": "yī", "ru": "Один", "emoji": "1️⃣"},
            {"id": "two", "en": "Two", "ar": "اِثْنَان", "zh": "二", "pinyin": "èr", "ru": "Два", "emoji": "2️⃣"},
            {"id": "three", "en": "Three", "ar": "ثَلَاثَة", "zh": "三", "pinyin": "sān", "ru": "Три", "emoji": "3️⃣"},
            {"id": "four", "en": "Four", "ar": "أَرْبَعَة", "zh": "四", "pinyin": "sì", "ru": "Четыре", "emoji": "4️⃣"},
            {"id": "five", "en": "Five", "ar": "خَمْسَة", "zh": "五", "pinyin": "wǔ", "ru": "Пять", "emoji": "5️⃣"},
        ]
    },
    "body": {
        "icon": "🧑",
        "name": {"en": "Body", "ar": "جِسْم", "zh": "身体", "ru": "Тело"},
        "words": [
            {"id": "head", "en": "Head", "ar": "رَأْس", "zh": "头", "pinyin": "tóu", "ru": "Голова", "emoji": "👤"},
            {"id": "eye", "en": "Eye", "ar": "عَيْن", "zh": "眼睛", "pinyin": "yǎnjing", "ru": "Глаз", "emoji": "👁️"},
            {"id": "ear", "en": "Ear", "ar": "أُذُن", "zh": "耳朵", "pinyin": "ěrduo", "ru": "Ухо", "emoji": "👂"},
            {"id": "nose", "en": "Nose", "ar": "أَنْف", "zh": "鼻子", "pinyin": "bízi", "ru": "Нос", "emoji": "👃"},
            {"id": "mouth", "en": "Mouth", "ar": "فَم", "zh": "嘴", "pinyin": "zuǐ", "ru": "Рот", "emoji": "👄"},
            {"id": "hand", "en": "Hand", "ar": "يَد", "zh": "手", "pinyin": "shǒu", "ru": "Рука", "emoji": "✋"},
            {"id": "foot", "en": "Foot", "ar": "قَدَم", "zh": "脚", "pinyin": "jiǎo", "ru": "Нога", "emoji": "🦶"},
            {"id": "heart", "en": "Heart", "ar": "قَلْب", "zh": "心", "pinyin": "xīn", "ru": "Сердце", "emoji": "❤️"},
        ]
    },
    "house": {
        "icon": "🏠",
        "name": {"en": "House", "ar": "مَنْزِل", "zh": "房子", "ru": "Дом"},
        "words": [
            {"id": "door", "en": "Door", "ar": "بَاب", "zh": "门", "pinyin": "mén", "ru": "Дверь", "emoji": "🚪"},
            {"id": "window", "en": "Window", "ar": "نَافِذَة", "zh": "窗户", "pinyin": "chuānghu", "ru": "Окно", "emoji": "🪟"},
            {"id": "bed", "en": "Bed", "ar": "سَرِير", "zh": "床", "pinyin": "chuáng", "ru": "Кровать", "emoji": "🛏️"},
            {"id": "chair", "en": "Chair", "ar": "كُرْسِي", "zh": "椅子", "pinyin": "yǐzi", "ru": "Стул", "emoji": "🪑"},
            {"id": "table", "en": "Table", "ar": "طَاوِلَة", "zh": "桌子", "pinyin": "zhuōzi", "ru": "Стол", "emoji": "🍽️"},
            {"id": "lamp", "en": "Lamp", "ar": "مِصْبَاح", "zh": "灯", "pinyin": "dēng", "ru": "Лампа", "emoji": "💡"},
            {"id": "clock", "en": "Clock", "ar": "سَاعَة", "zh": "时钟", "pinyin": "shízhōng", "ru": "Часы", "emoji": "🕐"},
            {"id": "key", "en": "Key", "ar": "مِفْتَاح", "zh": "钥匙", "pinyin": "yàoshi", "ru": "Ключ", "emoji": "🔑"},
        ]
    },
    "school": {
        "icon": "🎒",
        "name": {"en": "School", "ar": "مَدْرَسَة", "zh": "学校", "ru": "Школа"},
        "words": [
            {"id": "book", "en": "Book", "ar": "كِتَاب", "zh": "书", "pinyin": "shū", "ru": "Книга", "emoji": "📚"},
            {"id": "pen", "en": "Pen", "ar": "قَلَم", "zh": "笔", "pinyin": "bǐ", "ru": "Ручка", "emoji": "🖊️"},
            {"id": "pencil", "en": "Pencil", "ar": "قَلَم رَصَاص", "zh": "铅笔", "pinyin": "qiānbǐ", "ru": "Карандаш", "emoji": "✏️"},
            {"id": "paper", "en": "Paper", "ar": "وَرَقَة", "zh": "纸", "pinyin": "zhǐ", "ru": "Бумага", "emoji": "📄"},
            {"id": "bag", "en": "Bag", "ar": "حَقِيبَة", "zh": "书包", "pinyin": "shūbāo", "ru": "Портфель", "emoji": "🎒"},
            {"id": "desk", "en": "Desk", "ar": "مَكْتَب", "zh": "课桌", "pinyin": "kèzhuō", "ru": "Парта", "emoji": "🪑"},
            {"id": "teacher", "en": "Teacher", "ar": "مُعَلِّم", "zh": "老师", "pinyin": "lǎoshī", "ru": "Учитель", "emoji": "🧑‍🏫"},
            {"id": "student", "en": "Student", "ar": "طَالِب", "zh": "学生", "pinyin": "xuésheng", "ru": "Ученик", "emoji": "🧑‍🎓"},
        ]
    },
    "transport": {
        "icon": "🚗",
        "name": {"en": "Transport", "ar": "مُوَاصَلَات", "zh": "交通工具", "ru": "Транспорт"},
        "words": [
            {"id": "car", "en": "Car", "ar": "سَيَّارَة", "zh": "汽车", "pinyin": "qìchē", "ru": "Машина", "emoji": "🚗"},
            {"id": "bus", "en": "Bus", "ar": "حَافِلَة", "zh": "公共汽车", "pinyin": "gōnggòng qìchē", "ru": "Автобус", "emoji": "🚌"},
            {"id": "truck", "en": "Truck", "ar": "شَاحِنَة", "zh": "卡车", "pinyin": "kǎchē", "ru": "Грузовик", "emoji": "🚚"},
            {"id": "train", "en": "Train", "ar": "قِطَار", "zh": "火车", "pinyin": "huǒchē", "ru": "Поезд", "emoji": "🚂"},
            {"id": "plane", "en": "Plane", "ar": "طَائِرَة", "zh": "飞机", "pinyin": "fēijī", "ru": "Самолёт", "emoji": "✈️"},
            {"id": "boat", "en": "Boat", "ar": "قَارِب", "zh": "船", "pinyin": "chuán", "ru": "Лодка", "emoji": "⛵"},
            {"id": "bike", "en": "Bike", "ar": "دَرَّاجَة", "zh": "自行车", "pinyin": "zìxíngchē", "ru": "Велосипед", "emoji": "🚲"},
        ]
    },
    "verbs": {
        "icon": "🏃",
        "name": {"en": "Verbs", "ar": "أَفْعَال", "zh": "动词", "ru": "Глаголы"},
        "words": [
            {"id": "eat", "en": "Eat", "ar": "يَأْكُل", "zh": "吃", "pinyin": "chī", "ru": "Есть", "emoji": "🍽️"},
            {"id": "drink", "en": "Drink", "ar": "يَشْرَب", "zh": "喝", "pinyin": "hē", "ru": "Пить", "emoji": "🥤"},
            {"id": "run", "en": "Run", "ar": "يَجْرِي", "zh": "跑", "pinyin": "pǎo", "ru": "Бегать", "emoji": "🏃"},
            {"id": "jump", "en": "Jump", "ar": "يَقْفِز", "zh": "跳", "pinyin": "tiào", "ru": "Прыгать", "emoji": "🤸"},
            {"id": "play", "en": "Play", "ar": "يَلْعَب", "zh": "玩", "pinyin": "wán", "ru": "Играть", "emoji": "🎮"},
            {"id": "read", "en": "Read", "ar": "يَقْرَأ", "zh": "读", "pinyin": "dú", "ru": "Читать", "emoji": "📖"},
            {"id": "write", "en": "Write", "ar": "يَكْتُب", "zh": "写", "pinyin": "xiě", "ru": "Писать", "emoji": "✍️"},
            {"id": "sing", "en": "Sing", "ar": "يُغَنِّي", "zh": "唱", "pinyin": "chàng", "ru": "Петь", "emoji": "🎤"},
            {"id": "sleep", "en": "Sleep", "ar": "يَنَام", "zh": "睡觉", "pinyin": "shuìjiào", "ru": "Спать", "emoji": "😴"},
        ]
    },
    "toys": {
        "icon": "🧸",
        "name": {"en": "Toys", "ar": "أَلْعَاب", "zh": "玩具", "ru": "Игрушки"},
        "words": [
            {"id": "ball", "en": "Ball", "ar": "كُرَة", "zh": "球", "pinyin": "qiú", "ru": "Мяч", "emoji": "⚽"},
            {"id": "doll", "en": "Doll", "ar": "دُمْيَة", "zh": "娃娃", "pinyin": "wáwa", "ru": "Кукла", "emoji": "🪆"},
            {"id": "teddy", "en": "Teddy bear", "ar": "دُبّ", "zh": "泰迪熊", "pinyin": "tàidíxióng", "ru": "Мишка", "emoji": "🧸"},
            {"id": "blocks", "en": "Blocks", "ar": "مُكَعَّبَات", "zh": "积木", "pinyin": "jīmù", "ru": "Кубики", "emoji": "🧱"},
            {"id": "kite", "en": "Kite", "ar": "طَائِرَة وَرَقِيَّة", "zh": "风筝", "pinyin": "fēngzheng", "ru": "Воздушный змей", "emoji": "🪁"},
            {"id": "puzzle", "en": "Puzzle", "ar": "أُحْجِيَّة", "zh": "拼图", "pinyin": "pīntú", "ru": "Пазл", "emoji": "🧩"},
            {"id": "train_toy", "en": "Toy train", "ar": "قِطَار لُعْبَة", "zh": "玩具火车", "pinyin": "wánjù huǒchē", "ru": "Игрушечный поезд", "emoji": "🚂"},
            {"id": "car_toy", "en": "Toy car", "ar": "سَيَّارَة لُعْبَة", "zh": "玩具车", "pinyin": "wánjù chē", "ru": "Машинка", "emoji": "🚗"},
        ]
    },
    "nature": {
        "icon": "🌳",
        "name": {"en": "Nature", "ar": "طَبِيعَة", "zh": "大自然", "ru": "Природа"},
        "words": [
            {"id": "tree", "en": "Tree", "ar": "شَجَرَة", "zh": "树", "pinyin": "shù", "ru": "Дерево", "emoji": "🌳"},
            {"id": "flower", "en": "Flower", "ar": "زَهْرَة", "zh": "花", "pinyin": "huā", "ru": "Цветок", "emoji": "🌸"},
            {"id": "grass", "en": "Grass", "ar": "عُشْب", "zh": "草", "pinyin": "cǎo", "ru": "Трава", "emoji": "🌱"},
            {"id": "leaf", "en": "Leaf", "ar": "وَرَقَة شَجَر", "zh": "叶子", "pinyin": "yèzi", "ru": "Лист", "emoji": "🍃"},
            {"id": "moon", "en": "Moon", "ar": "قَمَر", "zh": "月亮", "pinyin": "yuèliang", "ru": "Луна", "emoji": "🌙"},
            {"id": "star", "en": "Star", "ar": "نَجْمَة", "zh": "星星", "pinyin": "xīngxing", "ru": "Звезда", "emoji": "⭐"},
            {"id": "sky", "en": "Sky", "ar": "سَمَاء", "zh": "天空", "pinyin": "tiānkōng", "ru": "Небо", "emoji": "🌌"},
            {"id": "planet", "en": "Planet", "ar": "كَوْكَب", "zh": "星球", "pinyin": "xīngqiú", "ru": "Планета", "emoji": "🪐"},
            {"id": "river", "en": "River", "ar": "نَهْر", "zh": "河", "pinyin": "hé", "ru": "Река", "emoji": "🏞️"},
            {"id": "mountain", "en": "Mountain", "ar": "جَبَل", "zh": "山", "pinyin": "shān", "ru": "Гора", "emoji": "⛰️"},
        ]
    },
}


# ============================================================
# ПОИСК FFMPEG
# ============================================================

_STANDARD_WINDOWS_DIRS = [
    r"C:\ffmpeg", r"C:\ffmpeg\bin",
    r"C:\Program Files\ffmpeg", r"C:\Program Files\ffmpeg\bin",
    r"C:\Program Files (x86)\ffmpeg", r"C:\Program Files (x86)\ffmpeg\bin",
    r"C:\ProgramData\chocolatey\bin",
    r"C:\tools\ffmpeg\bin",
    r"C:\ProgramData\scoop\shims",
]


def find_ffmpeg():
    p = shutil.which('ffmpeg')
    if p:
        return p
    for base in _STANDARD_WINDOWS_DIRS:
        bp = Path(base)
        if not bp.exists():
            continue
        d = bp / 'ffmpeg.exe'
        if d.is_file():
            return str(d)
        b = bp / 'bin' / 'ffmpeg.exe'
        if b.is_file():
            return str(b)
        try:
            for sub in bp.iterdir():
                if not sub.is_dir():
                    continue
                sd = sub / 'ffmpeg.exe'
                if sd.is_file():
                    return str(sd)
                sb = sub / 'bin' / 'ffmpeg.exe'
                if sb.is_file():
                    return str(sb)
        except OSError:
            continue
    return None


def check_ffmpeg_verbose():
    p = find_ffmpeg()
    if p:
        try:
            subprocess.run([p, '-version'], check=True, capture_output=True, timeout=5)
            print(f"  ✓ ffmpeg найден: {p}")
            return p
        except Exception as e:
            print(f"  ⚠ ffmpeg найден ({p}), но не запускается: {e}")
            return None
    return None


# ============================================================
# СБОРКА lessons.json
# ============================================================

def _build_alphabet_lesson(lang: str) -> dict:
    entries = ALPHABET.get(lang, [])
    items = []
    for idx, entry in enumerate(entries, start=1):
        char = entry[0]
        name_ru = entry[1]
        item = {
            "id": f"{lang}_alpha_{idx:02d}",
            "text": char,
            "translation": name_ru,
            "audio": f"audio/{lang}/alphabet/{idx:02d}.wav",
        }
        if lang == "zh" and len(entry) >= 3:
            item["pinyin"] = entry[2]
        items.append(item)

    title_map = {
        "en": "🔤 Alphabet / Алфавит",
        "ar": "🔤 الْأَبْجَدِيَّة / Алфавит",
        "zh": "🔤 基础字 / Первые иероглифы",
    }

    return {
        "id": f"{lang}_alphabet",
        "title": title_map.get(lang, "Alphabet"),
        "language": lang,
        "level": 1,
        "is_dialog": False,
        "items": items,
    }


def _build_dialogue_lesson(dialog_id: str, dialog: dict, lang: str) -> dict:
    icon = dialog.get("icon", "💬")
    title = dialog["name"].get(lang, dialog["name"]["en"])
    lines = []
    for i, line in enumerate(dialog["lines"], start=1):
        entry = {
            "id": f"{lang}_dialog_{dialog_id}_line_{i}",
            "speaker": line["speaker"].get(lang, line["speaker"]["en"]),
            "text": line["text"].get(lang, line["text"]["en"]),
            "translation": line["text"]["ru"],
            "audio": f"audio/{lang}/dialog_{dialog_id}/line_{i}.wav",
        }
        if lang == "zh" and line.get("zh_pinyin"):
            entry["pinyin"] = line["zh_pinyin"]
        lines.append(entry)
    return {
        "id": f"{lang}_dialog_{dialog_id}",
        "title": f"{icon} {title}",
        "language": lang,
        "level": 1,
        "is_dialog": True,
        "items": [],
        "dialog": lines,
    }


def _build_topic_lesson(topic_id: str, topic: dict, lang: str) -> dict:
    items = []
    for word in topic["words"]:
        item = {
            "id": f"{lang}_{topic_id}_{word['id']}",
            "text": word[lang],
            "translation": word["ru"],
            "audio": f"audio/{lang}/{topic_id}/{word['id']}.wav",
        }
        if lang == "zh":
            item["pinyin"] = word["pinyin"]
        items.append(item)
    return {
        "id": f"{lang}_{topic_id}",
        "title": topic["name"].get(lang, topic["name"]["en"]),
        "language": lang,
        "level": 1,
        "is_dialog": False,
        "items": items,
    }


def generate_lessons_json(content_dir: Path) -> None:
    print("\n📚 Генерирую lessons.json...")
    for lang in ['en', 'ar', 'zh']:
        lessons = [_build_alphabet_lesson(lang)]
        for dialog_id, dialog in DIALOGS.items():
            lessons.append(_build_dialogue_lesson(dialog_id, dialog, lang))
        for topic_id, topic in TOPICS.items():
            lessons.append(_build_topic_lesson(topic_id, topic, lang))

        f = content_dir / lang / "lessons.json"
        f.parent.mkdir(parents=True, exist_ok=True)
        with open(f, "w", encoding="utf-8") as fp:
            json.dump(lessons, fp, ensure_ascii=False, indent=2)
        print(f"  ✓ {f} ({len(lessons)} уроков "
              f"[1 алфавит + {len(DIALOGS)} диалогов + {len(TOPICS)} тем])")


def generate_flashcards_json(content_dir: Path) -> None:
    print("\n🎴 Генерирую flashcards.json...")
    for lang in ['en', 'ar', 'zh']:
        flashcards = {"version": 1, "language": lang, "topics": []}
        for topic_id, topic in TOPICS.items():
            t = {
                "id": topic_id,
                "name": f"{topic['icon']} {topic['name'].get(lang, topic['name']['en'])} / {topic['name']['ru']}",
                "icon": topic["icon"],
                "cards": [],
            }
            for word in topic["words"]:
                c = {
                    "id": f"{lang}_{topic_id}_{word['id']}",
                    "word": word[lang],
                    "translation": word["ru"],
                    "image": f"images/{topic_id}/{word['id']}.png",
                    "audio": f"audio/{lang}/{topic_id}/{word['id']}.wav",
                }
                if lang == "zh":
                    c["pinyin"] = word["pinyin"]
                t["cards"].append(c)
            flashcards["topics"].append(t)
        f = content_dir / lang / "flashcards.json"
        f.parent.mkdir(parents=True, exist_ok=True)
        with open(f, "w", encoding="utf-8") as fp:
            json.dump(flashcards, fp, ensure_ascii=False, indent=2)
        print(f"  ✓ {f} ({len(flashcards['topics'])} тем)")


def generate_images(content_dir: Path) -> None:
    print("\n🖼️  Генерирую картинки...")
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("  ⚠ Pillow не установлен. Пропускаю.")
        return

    topic_colors = {
        "animals": "#FFE4B5", "food": "#FFDAB9", "family": "#FFB6C1",
        "colors": "#F0F8FF", "weather": "#E0FFFF", "clothes": "#FFF8DC",
        "emotions": "#FFE4E1", "numbers": "#E6E6FA", "body": "#FFEFD5",
        "house": "#F5F5DC", "school": "#E0EEE0", "transport": "#E6E6FA",
        "verbs": "#FFF0F5", "toys": "#FFFACD", "nature": "#E0F8E0",
    }

    font_paths = ["C:/Windows/Fonts/seguiemj.ttf",
                  "C:/Windows/Fonts/segoeui.ttf",
                  "C:/Windows/Fonts/arial.ttf"]
    emoji_font = text_font = big_text_font = None
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                if emoji_font is None and 'emoji' in fp.lower():
                    emoji_font = ImageFont.truetype(fp, 120)
                elif text_font is None:
                    text_font = ImageFont.truetype(fp, 32)
                    big_text_font = ImageFont.truetype(fp, 48)
            except Exception:
                continue
    if text_font is None:
        text_font = ImageFont.load_default()
        big_text_font = text_font

    total, skipped = 0, 0
    for topic_id, topic in TOPICS.items():
        bg = topic_colors.get(topic_id, "#FFFFFF")
        for word in topic["words"]:
            d = content_dir / "images" / topic_id
            d.mkdir(parents=True, exist_ok=True)
            p = d / f"{word['id']}.png"
            if p.exists():
                skipped += 1
                continue
            img = Image.new("RGB", (400, 400), bg)
            draw = ImageDraw.Draw(img)
            emoji = word.get("emoji", "")
            if emoji_font and emoji:
                try:
                    b = draw.textbbox((0, 0), emoji, font=emoji_font)
                    draw.text(((400 - (b[2] - b[0])) / 2, 40), emoji,
                              font=emoji_font, fill="#000000")
                except Exception:
                    pass
            for text_value, fnt, y in ((word["en"], big_text_font, 220),
                                       (word["ru"], text_font, 300)):
                if fnt:
                    b = draw.textbbox((0, 0), text_value, font=fnt)
                    draw.text(((400 - (b[2] - b[0])) / 2, y), text_value,
                              font=fnt, fill="#333333")
            img.save(p, "PNG")
            total += 1
    print(f"  ✓ Создано {total} картинок (пропущено: {skipped})")


def _tts_one_line(gTTS, ffmpeg_path, text: str, lang_code: str, audio_path: Path):
    tts = gTTS(text=text, lang=lang_code, slow=True)
    tmp = audio_path.with_suffix('.mp3')
    tts.save(str(tmp))
    if ffmpeg_path:
        subprocess.run([ffmpeg_path, '-y', '-i', str(tmp),
                        '-ar', '44100', '-ac', '1', str(audio_path)],
                       check=True, capture_output=True)
        tmp.unlink()
    else:
        tmp.replace(audio_path)


def generate_audio(content_dir: Path) -> None:
    print("\n🔊 Генерирую аудио через Google TTS...")
    try:
        from gtts import gTTS
    except ImportError:
        print("  ⚠ gTTS не установлен. Установите: pip install gTTS")
        return

    ffmpeg_path = check_ffmpeg_verbose()
    if not ffmpeg_path:
        print()
        print("  ⚠ ffmpeg не найден. MP3 сохранится под именем .wav.")
        print("    Для корректных WAV: https://ffmpeg.org/download.html")
        print()

    codes = {'en': 'en', 'ar': 'ar', 'zh': 'zh-CN'}
    total = skipped = failed = 0

    for lang in ['en', 'ar', 'zh']:
        print(f"\n  🌍 {lang.upper()}")

        # --- АЛФАВИТ ---
        # Для английского entry[0] содержит две буквы ("A a").
        # gTTS без правки читал бы обе: "эй эй". Берём только первый токен.
        # Файлы алфавита пересоздаются всегда — это позволяет
        # починить ранее сгенерированные с двойным произнесением.
        for idx, entry in enumerate(ALPHABET.get(lang, []), start=1):
            d = content_dir / "audio" / lang / "alphabet"
            d.mkdir(parents=True, exist_ok=True)
            p = d / f"{idx:02d}.wav"
            try:
                first_token = entry[0].split()[0] if entry[0].split() else entry[0]
                _tts_one_line(gTTS, ffmpeg_path, first_token, codes[lang], p)
                total += 1
            except Exception as e:
                failed += 1
                print(f"    ⚠ alpha {idx}: {e}")

        # --- СЛОВА ТЕМ ---
        for topic_id, topic in TOPICS.items():
            d = content_dir / "audio" / lang / topic_id
            d.mkdir(parents=True, exist_ok=True)
            for word in topic["words"]:
                p = d / f"{word['id']}.wav"
                if p.exists():
                    skipped += 1
                    continue
                try:
                    _tts_one_line(gTTS, ffmpeg_path, word[lang], codes[lang], p)
                    total += 1
                except Exception as e:
                    failed += 1
                    print(f"    ⚠ {topic_id}/{word['id']}: {e}")

        # --- РЕПЛИКИ ДИАЛОГОВ ---
        for dialog_id, dialog in DIALOGS.items():
            d = content_dir / "audio" / lang / f"dialog_{dialog_id}"
            d.mkdir(parents=True, exist_ok=True)
            for i, line in enumerate(dialog["lines"], start=1):
                p = d / f"line_{i}.wav"
                if p.exists():
                    skipped += 1
                    continue
                try:
                    txt = line["text"].get(lang, line["text"]["en"])
                    _tts_one_line(gTTS, ffmpeg_path, txt, codes[lang], p)
                    total += 1
                except Exception as e:
                    failed += 1
                    print(f"    ⚠ dialog_{dialog_id}/line_{i}: {e}")

    print(f"\n  ✓ Создано {total} аудиофайлов "
          f"(пропущено: {skipped}, ошибок: {failed})")


def main():
    print("=" * 70)
    print("🎨 ГЕНЕРАТОР КОНТЕНТА")
    print("=" * 70)

    base = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent
    content_dir = base / "content"
    content_dir.mkdir(exist_ok=True)

    topic_words = sum(len(t['words']) for t in TOPICS.values())
    dialog_lines = sum(len(d['lines']) for d in DIALOGS.values())
    alpha_total = sum(len(v) for v in ALPHABET.values())
    print(f"📊 План: 1 алфавит/язык ({alpha_total} элементов) + "
          f"{len(DIALOGS)} диалогов ({dialog_lines} реплик) + "
          f"{len(TOPICS)} тем ({topic_words} слов) × 3 языка")

    generate_lessons_json(content_dir)
    generate_flashcards_json(content_dir)
    generate_images(content_dir)
    generate_audio(content_dir)

    print("\n" + "=" * 70)
    print("✅ ГОТОВО!")
    print("=" * 70)


if __name__ == '__main__':
    main()