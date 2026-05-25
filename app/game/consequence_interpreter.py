def _intensity(delta: int) -> str:
    absolute = abs(delta)

    if absolute >= 4:
        return "резко"
    if absolute >= 2:
        return "заметно"
    return "слегка"


def interpret_effects(effects: dict[str, int]) -> list[str]:
    consequences: list[str] = []

    wealth = effects.get("wealth", 0)
    if wealth > 0:
        consequences.append(f"материальное положение {_intensity(wealth)} улучшилось")
    elif wealth < 0:
        consequences.append(f"материальное положение {_intensity(wealth)} ухудшилось")

    loyalty = effects.get("loyalty", 0)
    if loyalty > 0:
        consequences.append(f"власть стала {_intensity(loyalty)} больше доверять игроку")
    elif loyalty < 0:
        consequences.append(f"лояльность игрока стала {_intensity(loyalty)} сильнее вызывать сомнения")

    influence = effects.get("influence", 0)
    if influence > 0:
        consequences.append(f"личное влияние игрока {_intensity(influence)} выросло")
    elif influence < 0:
        consequences.append(f"личное влияние игрока {_intensity(influence)} ослабло")

    suspicion = effects.get("suspicion", 0)
    if suspicion > 0:
        consequences.append(f"подозрение к игроку {_intensity(suspicion)} усилилось")
    elif suspicion < 0:
        consequences.append(f"подозрение к игроку {_intensity(suspicion)} снизилось")

    survival = effects.get("survival", 0)
    if survival > 0:
        consequences.append(f"личная безопасность игрока {_intensity(survival)} укрепилась")
    elif survival < 0:
        consequences.append(f"личная безопасность игрока {_intensity(survival)} ухудшилась")

    people_support = effects.get("people_support", 0)
    if people_support > 0:
        consequences.append(f"отношение обычных людей к игроку {_intensity(people_support)} улучшилось")
    elif people_support < 0:
        consequences.append(f"отношение обычных людей к игроку {_intensity(people_support)} ухудшилось")

    if not consequences:
        consequences.append("выбор почти не изменил положение игрока, но оставил след в памяти окружающих")

    return consequences


def format_effect_meanings(effect_meanings: list[str]) -> str:
    return "\n".join(f"- {item}" for item in effect_meanings)
