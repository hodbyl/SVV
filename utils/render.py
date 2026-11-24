SEP = "-" * 90
MARK = "*C.B.A. Team* Не принадлежит распространению"


def window_a11():
    return (
        f"{SEP}\n"
        f"Добро пожаловать, оперативник [A.1.1]\n"
        f"Подтверждение личности\n"
        f"{SEP}\n{MARK}\n{SEP}\n"
        f"Введите код входа в аккаунт:\n"
        f"{SEP}\n{MARK}\n{SEP}"
    )


def window_x11():
    return (
        f"{SEP}\n"
        f"Добро пожаловать, оперативник [X.1.1]\n"
        f"Подтверждение личности\n"
        f"Вы были заблокированы системой\n"
        f"{SEP}\n{MARK}\n{SEP}\n"
        f"Введите код для разбана:\n"
        f"{SEP}\n{MARK}\n{SEP}"
    )


def window_a12(acc, staff_rank: int, protocol=None):
    lines = []
    if protocol:
        exp = protocol["expires_at"].strftime("%Y-%m-%d %H:%M UTC") if protocol["expires_at"] else "—"
        lines.append(f"!! ЭКСТРЕННЫЙ ПРОТОКОЛ: {protocol['level']} | Причина: {protocol['reason']} | До: {exp}")
        lines.append("")
    lines += [
        SEP,
        f"Добро пожаловать, {acc['callsign']} (Ранг {acc['rank']}) [A.1.2]",
        SEP, MARK, SEP,
        "Система C.B.A.",
        "1. Приказы",
        "2. Экстренный протокол",
        "3. Задачи",
        "4. Донесения",
        "5. Спецоперации",
        "6. Слежка",
        "7. Создание Досье",
        "8. Аналитика",
        "9. Прогнозы",
        "10. Проверка лояльности",
        "11. Ликвидация угроз",
        "12. Отчёты",
        "13. Архив",
        "14. Кодовые имена",
        "15. Шифры",
        "16. Протоколы",
        "17. База данных",
        "18. Связь с Отделами",
        "19. Рация",
        "20. Мессенджер",
        "21. Объявление",
        "22. Техподдержка",
        "23. Блокнот",
        "24. Выход",
    ]
    if staff_rank >= 6:
        lines.append("25. ADMIN MENU (6+ ранг)")
    lines.append("0. Выход")
    lines += [SEP, MARK, SEP]
    return "\n".join(lines)


def window_p1(staff_rank: int):
    return "\n".join([
        SEP,
        "ADMIN menu [P.1]",
        SEP, MARK, SEP,
        "Система C.B.A.",
        "1. Логирование (7+ ранг)",
        "2. Выдать наказание (6+ ранг)",
        "0. Выход",
        SEP, MARK, SEP,
    ])


def window_p11():
    return (
        f"{SEP}\nЛогирование [P.1.1]\n{SEP}\n{MARK}\n{SEP}\n"
        f"Система C.B.A.\n"
        f"1. Логирование Нарушений\n"
        f"2. Логирование Досье\n"
        f"3. Логирование Повышений\n"
        f"4. Логирование Понижений\n"
        f"5. Глобальное Логирование\n"
        f"0. Выход\n"
        f"{SEP}\n{MARK}\n{SEP}"
    )


def window_p12():
    return (
        f"{SEP}\nВыдать наказание [P.1.2]\n{SEP}\n{MARK}\n{SEP}\n"
        f"Система C.B.A.\n"
        f"1. Устное замечание\n"
        f"2. Предупреждение\n"
        f"3. Выговор\n"
        f"4. Штраф\n"
        f"5. Понижение в ранге\n"
        f"6. Перевод в другое подразделение\n"
        f"7. Исключение из отдела\n"
        f"8. Перманентный бан\n"
        f"0. Назад\n"
        f"{SEP}\n{MARK}\n{SEP}"
    )


def window_placeholder(title: str, window: str):
    return (
        f"{SEP}\n{title} {window}\n{SEP}\n{MARK}\n{SEP}\n"
        f"Раздел в разработке (Этап 3.2+).\n"
        f"0. Назад\n"
        f"{SEP}\n{MARK}\n{SEP}"
    )