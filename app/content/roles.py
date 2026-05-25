from app.domain.models import RoleDefinition


ROLES: dict[str, RoleDefinition] = {
    "communist": RoleDefinition(
        id="communist",
        name="☭ Идейный коммунист",
        description=(
            "Ты веришь в социалистический проект и готов жертвовать "
            "личной выгодой ради идеи, партии и будущего общества."
        ),
        initial_stats={
            "wealth": 1,
            "loyalty": 5,
            "influence": 2,
            "suspicion": 0,
            "survival": 5,
            "people_support": 2,
        },
    ),
    "opportunist": RoleDefinition(
        id="opportunist",
        name="💰 Прагматик",
        description=(
            "Ты хочешь выжить и разбогатеть, приспосабливаясь к обстоятельствам. "
            "Идеология для тебя вторична, главное — выгода и безопасность."
        ),
        initial_stats={
            "wealth": 4,
            "loyalty": 1,
            "influence": 1,
            "suspicion": 1,
            "survival": 4,
            "people_support": 1,
        },
    ),
    "traitor": RoleDefinition(
        id="traitor",
        name="🕵️ Скрытый противник советской власти",
        description=(
            "Ты хочешь ослабления советской власти, но вынужден скрывать "
            "свои намерения и действовать осторожно."
        ),
        initial_stats={
            "wealth": 2,
            "loyalty": -4,
            "influence": 1,
            "suspicion": 3,
            "survival": 3,
            "people_support": 0,
        },
    ),
}
