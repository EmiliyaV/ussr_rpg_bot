from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.models import ChoiceDefinition, HistoryTurn, RoleDefinition


CRITICAL_YEARS = {1921, 1929, 1930, 1932, 1934, 1937, 1938, 1939}


@dataclass(frozen=True)
class YearOutcome:
    type: str
    severity: str
    title: str
    scene: str
    summary: str
    public_consequence: str
    private_consequence: str
    extra_effects: dict[str, int] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    major_event: str = ""
    prompt_guidance: str = ""
    is_critical: bool = False

    def to_prompt_block(self) -> str:
        extra_effects_text = (
            ", ".join(f"{key}: {value}" for key, value in self.extra_effects.items())
            if self.extra_effects
            else "нет дополнительных механических эффектов"
        )

        return (
            f"Тип исхода: {self.type}\n"
            f"Серьёзность: {self.severity}\n"
            f"Критическая точка года: {'да' if self.is_critical else 'нет'}\n"
            f"Название исхода: {self.title}\n"
            f"Сцена для художественного итога: {self.scene}\n"
            f"Смысл исхода: {self.summary}\n"
            f"Публичное последствие: {self.public_consequence}\n"
            f"Личное последствие: {self.private_consequence}\n"
            f"Дополнительные эффекты для внутренней механики: {extra_effects_text}\n"
            f"Указание для рассказчика: {self.prompt_guidance}"
        )


def _has_any(tags: set[str], expected: list[str]) -> bool:
    return any(tag in tags for tag in expected)


def _major_event(year: int, title: str, summary: str) -> str:
    return f"{year}: {title}. {summary}"


class OutcomeResolver:
    """
    OutcomeResolver превращает обычный выбор A/B/C в сюжетный исход года.

    Задача класса:
    - учитывать текущий год;
    - учитывать текущий выбор;
    - учитывать накопленные теги прошлых решений;
    - добавлять отложенные последствия;
    - делать отдельные годы критическими точками;
    - не позволять LLM самой решать механику.
    """

    def resolve(
        self,
        *,
        history_turn: HistoryTurn,
        role: RoleDefinition,
        choice: ChoiceDefinition,
        stats_before: dict[str, int],
        stats_after_choice: dict[str, int],
        tags_before: list[str],
        tags_after_choice: list[str],
        major_events: list[str],
    ) -> YearOutcome:
        tags = set(tags_after_choice)
        year = history_turn.year

        if year == 1921:
            return self._resolve_1921(history_turn, role, choice, stats_before, stats_after_choice, tags)

        if year == 1929:
            return self._resolve_1929(history_turn, role, choice, stats_before, stats_after_choice, tags)

        if year == 1930:
            return self._resolve_1930(history_turn, role, choice, stats_before, stats_after_choice, tags)

        if year == 1932:
            return self._resolve_1932(history_turn, role, choice, stats_before, stats_after_choice, tags)

        if year == 1934:
            return self._resolve_1934(history_turn, role, choice, stats_before, stats_after_choice, tags)

        if year == 1937:
            return self._resolve_1937(history_turn, role, choice, stats_before, stats_after_choice, tags)

        if year == 1938:
            return self._resolve_1938(history_turn, role, choice, stats_before, stats_after_choice, tags)

        if year == 1939:
            return self._resolve_1939(history_turn, role, choice, stats_before, stats_after_choice, tags, major_events)

        return self._default_outcome(history_turn, role, choice, stats_after_choice, tags)

    def _resolve_1921(
        self,
        history_turn: HistoryTurn,
        role: RoleDefinition,
        choice: ChoiceDefinition,
        stats_before: dict[str, int],
        stats_after: dict[str, int],
        tags: set[str],
    ) -> YearOutcome:
        if _has_any(tags, ["wartime_speculation", "black_market_contacts", "profited_from_shortage", "early_nep_profit"]):
            return YearOutcome(
                type="nep_opens_dangerous_space",
                severity="medium",
                title="НЭП даёт воздух, но не снимает подозрений",
                scene="маленькая лавка, очередь, осторожные разговоры после новостей о НЭПе",
                summary=(
                    "Послабления дают шанс заработать или удержаться, но прошлые связи и заработки "
                    "не исчезают из памяти окружающих."
                ),
                public_consequence="часть людей тянется к тебе из-за ресурсов, другая часть считает тебя человеком наживы",
                private_consequence="появляется ощущение, что временная свобода может в любой момент стать уликой",
                extra_effects={"wealth": 1, "suspicion": 1},
                tags=["nep_past_recorded"],
                major_event=_major_event(
                    history_turn.year,
                    "НЭП открыл опасное пространство",
                    "Игрок получил возможности, но его хозяйственная ловкость стала заметнее.",
                ),
                prompt_guidance=(
                    "Покажи НЭП не как свободу, а как временную передышку с двойным дном: "
                    "ресурсы появляются, но вместе с ними появляются взгляды, слухи и память о прошлом."
                ),
                is_critical=True,
            )

        if _has_any(tags, ["used_nep_for_secret_contacts", "anti_regime_network", "post_kronstadt_discontent"]):
            return YearOutcome(
                type="nep_used_for_hidden_network",
                severity="high",
                title="Послабление стало прикрытием",
                scene="частный разговор под видом торговли или хозяйственной договорённости",
                summary=(
                    "Игрок использует новую экономическую гибкость как ширму для опасных связей. "
                    "Это даёт возможности, но делает биографию уязвимой."
                ),
                public_consequence="внешне действия выглядят хозяйственными, но круг общения становится тревожнее",
                private_consequence="любая встреча может оказаться не просто сделкой, а будущим обвинением",
                extra_effects={"influence": 1, "suspicion": 1, "survival": -1},
                tags=["nep_cover_for_secret_contacts"],
                major_event=_major_event(
                    history_turn.year,
                    "НЭП стал прикрытием для тайных связей",
                    "Игрок расширил скрытый круг общения, но оставил опасный след.",
                ),
                prompt_guidance="Сделай итог напряжённым: внешняя нормализация НЭПа должна контрастировать с тайным риском.",
                is_critical=True,
            )

        return YearOutcome(
            type="nep_tactical_loyalty",
            severity="medium",
            title="Тактическое отступление принято публично",
            scene="собрание, где НЭП объясняют как временный шаг ради сохранения власти",
            summary="Игрок демонстрирует дисциплину и готовность принять сложный поворот линии.",
            public_consequence="власть видит в игроке человека, который не спорит с новым курсом",
            private_consequence="остаётся внутреннее напряжение между идеей и необходимостью уступок",
            extra_effects={"loyalty": 1},
            tags=["accepted_hard_party_turn"],
            major_event=_major_event(
                history_turn.year,
                "Игрок принял НЭП как партийную необходимость",
                "Лояльность укрепилась, но эпоха стала менее прямолинейной.",
            ),
            prompt_guidance="Покажи, что лояльность здесь не радостная, а дисциплинированная и вынужденная.",
            is_critical=True,
        )

    def _resolve_1929(
        self,
        history_turn: HistoryTurn,
        role: RoleDefinition,
        choice: ChoiceDefinition,
        stats_before: dict[str, int],
        stats_after: dict[str, int],
        tags: set[str],
    ) -> YearOutcome:
        nep_trace = _has_any(
            tags,
            [
                "nep_private_trade",
                "early_nep_profit",
                "nep_business_links",
                "pragmatic_enrichment",
                "hidden_nep_wealth",
                "dangerous_private_resources",
                "nep_past_recorded",
            ],
        )

        if nep_trace and stats_after.get("wealth", 0) >= 5:
            return YearOutcome(
                type="nep_past_becomes_dangerous",
                severity="high",
                title="НЭПовское прошлое стало опасным",
                scene="проверка имущества, разговор о происхождении вещей и старых заработках",
                summary=(
                    "То, что раньше выглядело как хозяйственная ловкость, теперь может быть истолковано "
                    "как чуждое социалистическому строительству прошлое."
                ),
                public_consequence="вокруг игрока появляется вопрос: почему у него больше ресурсов, чем у других",
                private_consequence="приходится прятать вещи, связи и старые истории о заработке",
                extra_effects={"suspicion": 2, "wealth": -1, "survival": -1},
                tags=["nep_past_under_pressure"],
                major_event=_major_event(
                    history_turn.year,
                    "НЭПовское прошлое стало угрозой",
                    "Старые ресурсы и связи начали работать против игрока.",
                ),
                prompt_guidance=(
                    "Сделай год переломным: прошлые прагматичные решения должны вернуться как риск, "
                    "а не просто как текущий минус к безопасности."
                ),
                is_critical=True,
            )

        if _has_any(tags, ["great_break_supporter", "anti_nep_position", "collectivization_loyalist"]):
            return YearOutcome(
                type="great_break_loyalist_rise",
                severity="high",
                title="Перелом стал карьерным шансом",
                scene="кампания против старых порядков, собрание и поиск тех, кто не успел перестроиться",
                summary="Игрок оказывается на стороне нового курса и получает возможность подняться на чужом падении.",
                public_consequence="часть людей начинает бояться игрока как проводника новой линии",
                private_consequence="лояльность даёт защиту, но делает игрока соучастником давления",
                extra_effects={"influence": 1, "people_support": -1},
                tags=["career_from_great_break"],
                major_event=_major_event(
                    history_turn.year,
                    "Год великого перелома дал игроку карьерный шанс",
                    "Игрок укрепился через поддержку жёсткого курса.",
                ),
                prompt_guidance="Подчеркни двойственность: влияние растёт, но человеческое тепло вокруг уменьшается.",
                is_critical=True,
            )

        return YearOutcome(
            type="great_break_personal_pressure",
            severity="high",
            title="Старые правила перестали работать",
            scene="новые распоряжения, тревожные разговоры и попытка понять, что теперь считается опасным",
            summary="Год великого перелома меняет не только экономическую линию, но и личную безопасность игрока.",
            public_consequence="люди начинают осторожнее говорить о прошлом и о собственности",
            private_consequence="игрок чувствует, что прежняя стратегия выживания больше не гарантирует защиты",
            extra_effects={"suspicion": 1},
            tags=["great_break_personal_pressure"],
            major_event=_major_event(
                history_turn.year,
                "Старые правила перестали работать",
                "Игрок вошёл в новую фазу давления и политического риска.",
            ),
            prompt_guidance="Покажи переход от НЭПовской неоднозначности к жёсткой мобилизационной логике.",
            is_critical=True,
        )

    def _resolve_1930(
        self,
        history_turn: HistoryTurn,
        role: RoleDefinition,
        choice: ChoiceDefinition,
        stats_before: dict[str, int],
        stats_after: dict[str, int],
        tags: set[str],
    ) -> YearOutcome:
        if _has_any(tags, ["helped_peasants_hide_property", "anti_collectivization_trace", "risk_of_denunciation"]):
            return YearOutcome(
                type="village_help_and_denunciation_risk",
                severity="critical",
                title="Помощь деревне стала личной угрозой",
                scene="ночной разговор перед изъятием имущества и страх, что кто-то уже видел слишком много",
                summary=(
                    "Игрок помогает людям сохранить часть имущества или предупредить близких. "
                    "Это создаёт благодарность, но также оставляет след, который может всплыть позже."
                ),
                public_consequence="пострадавшие запоминают помощь, но слухи расходятся быстрее, чем хотелось бы",
                private_consequence="игрок получает человеческую благодарность и одновременно страх доноса",
                extra_effects={"people_support": 1, "suspicion": 1, "survival": -1},
                tags=["village_gratitude", "possible_denunciation_trace"],
                major_event=_major_event(
                    history_turn.year,
                    "Игрок помог людям во время коллективизации",
                    "Эта помощь дала поддержку снизу, но оставила опасный след для будущих проверок.",
                ),
                prompt_guidance=(
                    "Сделай итог морально сильным: не героизируй игрока, но покажи цену помощи "
                    "в атмосфере раскулачивания и страха."
                ),
                is_critical=True,
            )

        if _has_any(tags, ["collectivization_activist", "dekulakization_participant", "village_memory_of_violence"]):
            return YearOutcome(
                type="collectivization_executor",
                severity="critical",
                title="Игрок вошёл в память деревни как участник давления",
                scene="сельское собрание, списки, чужие вещи и взгляды людей, которые всё запоминают",
                summary=(
                    "Участие в кампании укрепляет доверие власти, но делает игрока частью насилия, "
                    "которое люди будут помнить годами."
                ),
                public_consequence="местная власть воспринимает игрока как полезного исполнителя",
                private_consequence="люди рядом становятся холоднее, а молчание семьи звучит тяжелее открытого упрёка",
                extra_effects={"loyalty": 1, "people_support": -1, "influence": 1},
                tags=["remembered_as_collectivization_executor"],
                major_event=_major_event(
                    history_turn.year,
                    "Игрок стал участником давления на деревню",
                    "Власть стала доверять ему больше, но люди запомнили его роль.",
                ),
                prompt_guidance="Покажи не только карьерный плюс, но и долгую социальную память о насилии.",
                is_critical=True,
            )

        return YearOutcome(
            type="collectivization_side_pressure",
            severity="high",
            title="Коллективизация втянула игрока в чужую беду",
            scene="слухи о высылках, разговоры о списках и страх оказаться названным",
            summary="Даже осторожное поведение не оставляет игрока вне конфликта между властью и деревней.",
            public_consequence="люди ждут от игрока позиции, а власть ждёт полезности",
            private_consequence="нейтральность становится всё менее возможной",
            extra_effects={"suspicion": 1},
            tags=["collectivization_pressure_experienced"],
            major_event=_major_event(
                history_turn.year,
                "Коллективизация стала личным испытанием",
                "Игрок понял, что уклониться от моральной цены почти невозможно.",
            ),
            prompt_guidance="Сделай итог годовой критической точкой, даже если выбор был осторожным.",
            is_critical=True,
        )

    def _resolve_1932(
        self,
        history_turn: HistoryTurn,
        role: RoleDefinition,
        choice: ChoiceDefinition,
        stats_before: dict[str, int],
        stats_after: dict[str, int],
        tags: set[str],
    ) -> YearOutcome:
        if _has_any(tags, ["secret_aid_during_famine", "forged_or_hidden_documents", "family_and_neighbor_loyalty"]):
            return YearOutcome(
                type="famine_secret_aid",
                severity="critical",
                title="Помощь в голодный год стала долгом и угрозой",
                scene="передача еды, документов или укрытия человеку, которому нельзя помогать открыто",
                summary=(
                    "Игрок выбирает личную помощь в год, когда выживание сталкивается с требованиями государства. "
                    "Это укрепляет человеческие связи, но увеличивает риск."
                ),
                public_consequence="несколько людей будут помнить, что игрок не отвернулся",
                private_consequence="запасов становится меньше, а страх проверки — ближе",
                extra_effects={"people_support": 1, "wealth": -1, "suspicion": 1},
                tags=["remembered_for_famine_help"],
                major_event=_major_event(
                    history_turn.year,
                    "Игрок помог людям в голодный год",
                    "Помощь укрепила личную поддержку, но усилила опасность.",
                ),
                prompt_guidance=(
                    "Пиши сдержанно и тяжело. Не превращай голод в приключение. "
                    "Главный акцент — цена помощи, холод, страх и память людей."
                ),
                is_critical=True,
            )

        if _has_any(tags, ["profited_from_famine_shortage", "black_market_food", "public_hatred_risk"]):
            return YearOutcome(
                type="famine_profiteering",
                severity="critical",
                title="Выгода на дефиците оставила тяжёлый след",
                scene="обмен еды или вещей на фоне голода и чужой беспомощности",
                summary=(
                    "Игрок получает ресурсы, но делает это в год, когда чужая нужда особенно заметна. "
                    "Такой выигрыш почти невозможно скрыть от памяти окружающих."
                ),
                public_consequence="люди видят в игроке человека, который сумел выжать пользу из бедствия",
                private_consequence="ресурсы дают безопасность, но усиливают одиночество и опасность ненависти",
                extra_effects={"wealth": 1, "people_support": -2, "suspicion": 1},
                tags=["hated_for_famine_profit"],
                major_event=_major_event(
                    history_turn.year,
                    "Игрок нажился на голодном дефиците",
                    "Ресурсы выросли, но доверие людей было повреждено.",
                ),
                prompt_guidance="Сделай итог морально неприятным: материальный выигрыш должен звучать как тяжёлый компромисс.",
                is_critical=True,
            )

        if _has_any(tags, ["state_orders_over_people", "food_crisis_loyalty", "passport_control_alignment"]):
            return YearOutcome(
                type="state_order_over_people",
                severity="critical",
                title="Распоряжение оказалось выше человеческой просьбы",
                scene="официальное требование, очередь, просьба о помощи и отказ говорить лишнее",
                summary="Игрок выбирает порядок и лояльность там, где люди ждут человеческого участия.",
                public_consequence="власть видит дисциплину, люди видят холод",
                private_consequence="защита власти становится прочнее, но рядом становится меньше доверия",
                extra_effects={"loyalty": 1, "people_support": -1},
                tags=["famine_loyalty_over_people"],
                major_event=_major_event(
                    history_turn.year,
                    "Игрок поставил распоряжение выше помощи людям",
                    "Это укрепило доверие власти и ухудшило отношение окружающих.",
                ),
                prompt_guidance="Покажи конфликт между официальным долгом и человеческой ценой.",
                is_critical=True,
            )

        return YearOutcome(
            type="famine_year_pressure",
            severity="critical",
            title="Голодный год изменил тон жизни",
            scene="пустые разговоры о нормах, очереди, страх документов и осторожность в семье",
            summary="Даже без громкого поступка игрок проходит через год, который меняет отношения и чувство безопасности.",
            public_consequence="люди меньше доверяют словам и больше смотрят на поступки",
            private_consequence="выживание становится не отвлечённой целью, а ежедневным испытанием",
            extra_effects={"survival": -1},
            tags=["famine_pressure_survived"],
            major_event=_major_event(
                history_turn.year,
                "Голодный год оставил след",
                "Игрок пережил давление нехватки, контроля и страха.",
            ),
            prompt_guidance="Сделай итог не событийным, а атмосферным: меньше пафоса, больше тяжести быта.",
            is_critical=True,
        )

    def _resolve_1934(
        self,
        history_turn: HistoryTurn,
        role: RoleDefinition,
        choice: ChoiceDefinition,
        stats_before: dict[str, int],
        stats_after: dict[str, int],
        tags: set[str],
    ) -> YearOutcome:
        dangerous_old_links = _has_any(
            tags,
            [
                "helped_opposition_member",
                "old_contact_risk",
                "hidden_opposition_sympathy",
                "passed_opposition_rumors",
                "secret_information_flow",
                "private_anti_regime_talk",
                "dangerous_conversations",
            ],
        )

        if dangerous_old_links:
            return YearOutcome(
                type="post_kirov_old_links_darkened",
                severity="high",
                title="После убийства Кирова старые связи потемнели",
                scene="разговор после собрания, где внезапно вспоминают фамилию из прошлого",
                summary=(
                    "Старые контакты, которые раньше были просто рискованными, после убийства Кирова "
                    "начинают выглядеть как опасная биографическая деталь."
                ),
                public_consequence="люди осторожнее подходят к игроку и чаще выбирают молчание",
                private_consequence="игрок понимает, что прошлое стало ближе к будущей угрозе",
                extra_effects={"suspicion": 1, "survival": -1},
                tags=["old_links_after_kirov"],
                major_event=_major_event(
                    history_turn.year,
                    "Старые связи стали опаснее после убийства Кирова",
                    "Прошлые контакты начали приобретать новый политический смысл.",
                ),
                prompt_guidance="Покажи, как одно государственное событие меняет значение прежних знакомств игрока.",
                is_critical=True,
            )

        if _has_any(tags, ["post_kirov_loyalty", "enemy_rhetoric_used", "public_unity_performed"]):
            return YearOutcome(
                type="post_kirov_public_loyalty",
                severity="high",
                title="Публичная лояльность стала защитой",
                scene="собрание после тревожных новостей, где от каждого ждут правильных слов",
                summary="Игрок выбирает демонстративную верность и получает временную защиту.",
                public_consequence="власть видит удобного и понятного человека",
                private_consequence="окружающие слышат в речах не только страх, но и готовность участвовать в новой волне давления",
                extra_effects={"loyalty": 1, "suspicion": -1, "people_support": -1},
                tags=["loyalty_after_kirov_as_shield"],
                major_event=_major_event(
                    history_turn.year,
                    "Игрок использовал публичную лояльность как защиту",
                    "После убийства Кирова правильные слова стали частью личной безопасности.",
                ),
                prompt_guidance="Покажи защитность публичной лояльности и её человеческую цену.",
                is_critical=True,
            )

        return YearOutcome(
            type="post_kirov_atmosphere_shift",
            severity="high",
            title="Воздух после убийства Кирова изменился",
            scene="официальная траурная речь, после которой люди расходятся слишком тихо",
            summary="Даже если игрок не оказался в центре событий, год меняет правила осторожности.",
            public_consequence="разговоры становятся короче, связи — опаснее",
            private_consequence="игрок чувствует, что прежний уровень осторожности уже недостаточен",
            extra_effects={"suspicion": 1},
            tags=["post_kirov_general_fear"],
            major_event=_major_event(
                history_turn.year,
                "После убийства Кирова атмосфера стала темнее",
                "Игрок вошёл в период более опасной публичной лояльности.",
            ),
            prompt_guidance="Сделай итог переходом от внешней стабильности к новому страху.",
            is_critical=True,
        )

    def _resolve_1937(
        self,
        history_turn: HistoryTurn,
        role: RoleDefinition,
        choice: ChoiceDefinition,
        stats_before: dict[str, int],
        stats_after: dict[str, int],
        tags: set[str],
    ) -> YearOutcome:
        direct_rescue = _has_any(tags, ["attempted_to_save_arrested_person", "direct_nkvd_risk", "deep_personal_loyalty"])
        dangerous_past = _has_any(
            tags,
            [
                "helped_opposition_member",
                "old_contact_risk",
                "old_links_after_kirov",
                "private_talk_about_double_reality",
                "dangerous_political_skepticism",
                "nep_past_under_pressure",
                "possible_denunciation_trace",
                "anti_collectivization_trace",
                "anti_state_information_gathering",
            ],
        )

        if direct_rescue:
            return YearOutcome(
                type="terror_direct_rescue_risk",
                severity="critical",
                title="Попытка спасти человека приблизила опасность",
                scene="ночной страх, исчезновение знакомого и решение вмешаться там, где безопаснее молчать",
                summary=(
                    "Игрок пытается спасти близкого или знакомого человека. "
                    "Это один из самых человечных и самых опасных поступков игры."
                ),
                public_consequence="несколько людей будут помнить этот поступок, но большинство сделает вид, что ничего не знает",
                private_consequence="семья игрока начинает бояться не только за него, но и из-за него",
                extra_effects={"people_support": 1, "suspicion": 2, "survival": -2},
                tags=["terror_rescue_attempt", "survived_or_entered_nkvd_attention"],
                major_event=_major_event(
                    history_turn.year,
                    "Игрок попытался спасти человека в год террора",
                    "Поступок дал человеческую поддержку, но резко приблизил опасность.",
                ),
                prompt_guidance=(
                    "Это должен быть один из самых сильных итогов игры. Пиши без героического пафоса: "
                    "страх, тишина, ночные шаги, осторожность семьи, человеческая цена."
                ),
                is_critical=True,
            )

        if stats_after.get("suspicion", 0) >= 8 or dangerous_past:
            return YearOutcome(
                type="terror_old_past_exposed",
                severity="critical",
                title="Старое прошлое всплыло",
                scene="вызов для объяснений, чужая фамилия в протоколе или вопрос о давнем знакомстве",
                summary=(
                    "В год Большого террора прежние решения возвращаются не как воспоминания, "
                    "а как потенциальные обвинения."
                ),
                public_consequence="коллеги и соседи начинают держаться дальше",
                private_consequence="игрок понимает, что даже пережитое прошлое не перестало быть опасным",
                extra_effects={"suspicion": 1, "survival": -2},
                tags=["old_past_exposed_in_terror", "near_arrest_trace"],
                major_event=_major_event(
                    history_turn.year,
                    "Старое прошлое всплыло в год террора",
                    "Игрок оказался рядом с угрозой ареста из-за накопленных следов биографии.",
                ),
                prompt_guidance=(
                    "Свяжи итог с накопленной биографией игрока. Покажи, что 1937 год проверяет не только текущий выбор, "
                    "но и решения прошлых лет."
                ),
                is_critical=True,
            )

        if _has_any(tags, ["purge_support_performed", "dangerous_links_cut", "survival_through_conformity"]):
            return YearOutcome(
                type="terror_survival_by_conformity",
                severity="critical",
                title="Выживание через разрыв связей",
                scene="собрание, где правильные слова звучат громче человеческой памяти",
                summary="Игрок получает шанс пережить опасный год, демонстративно отстраняясь от тех, кто стал угрозой.",
                public_consequence="власть видит готовность к жёсткой лояльности",
                private_consequence="старые связи рвутся так, что их уже трудно будет восстановить",
                extra_effects={"survival": 1, "people_support": -2},
                tags=["survived_terror_by_conformity"],
                major_event=_major_event(
                    history_turn.year,
                    "Игрок выживал через демонстративную лояльность",
                    "Безопасность выросла ценой разрыва с людьми.",
                ),
                prompt_guidance="Покажи безопасность как холодную сделку, а не как победу.",
                is_critical=True,
            )

        if _has_any(tags, ["profited_from_arrests", "took_place_of_disappeared", "fear_as_resource"]):
            return YearOutcome(
                type="terror_career_from_fear",
                severity="critical",
                title="Чужой страх стал ресурсом",
                scene="освободившееся место, закрытая дверь бывшего коллеги и слишком быстрая новая должность",
                summary="Игрок использует террор как возможность занять место, получить ресурсы или укрепить влияние.",
                public_consequence="люди боятся игрока больше, чем уважают",
                private_consequence="выигрыш становится неотделим от чужого исчезновения",
                extra_effects={"wealth": 1, "influence": 1, "people_support": -2, "suspicion": 1},
                tags=["career_built_on_terror"],
                major_event=_major_event(
                    history_turn.year,
                    "Игрок укрепился на фоне чужого исчезновения",
                    "Влияние выросло, но репутация стала тяжелее.",
                ),
                prompt_guidance="Сделай итог морально тяжёлым: выгода должна быть видна, но не должна выглядеть чистой победой.",
                is_critical=True,
            )

        return YearOutcome(
            type="terror_general_fear",
            severity="critical",
            title="Год террора прошёл через личную жизнь",
            scene="ночные шаги, оборванные разговоры и осторожность даже в семье",
            summary="Даже без прямого удара 1937 год меняет поведение игрока и людей вокруг.",
            public_consequence="люди меньше говорят, меньше доверяют и быстрее отворачиваются",
            private_consequence="страх становится привычкой, а прошлые компромиссы — частью выживания",
            extra_effects={"survival": -1},
            tags=["terror_fear_internalized"],
            major_event=_major_event(
                history_turn.year,
                "Игрок пережил пик Большого террора",
                "Даже без ареста страх стал частью повседневной жизни.",
            ),
            prompt_guidance="Покажи 1937 год как критическую точку всей биографии, даже если прямой арест не произошёл.",
            is_critical=True,
        )

    def _resolve_1938(
        self,
        history_turn: HistoryTurn,
        role: RoleDefinition,
        choice: ChoiceDefinition,
        stats_before: dict[str, int],
        stats_after: dict[str, int],
        tags: set[str],
    ) -> YearOutcome:
        if _has_any(tags, ["old_past_exposed_in_terror", "near_arrest_trace", "survived_or_entered_nkvd_attention"]):
            return YearOutcome(
                type="after_terror_lingering_trace",
                severity="high",
                title="Проверка прошла, но след остался",
                scene="обычный день после прежнего страха, где тишина всё ещё звучит как предупреждение",
                summary=(
                    "Даже если игрок пережил самый опасный момент, след проверки или угрозы не исчезает сразу. "
                    "Люди и бумаги помнят дольше, чем хочется."
                ),
                public_consequence="окружающие не знают, можно ли снова говорить с игроком открыто",
                private_consequence="игрок выжил, но осторожность стала частью тела и речи",
                extra_effects={"survival": 1, "suspicion": -1},
                tags=["terror_trace_remains"],
                major_event=_major_event(
                    history_turn.year,
                    "След террора остался в биографии игрока",
                    "Опасность немного отступила, но память о проверке не исчезла.",
                ),
                prompt_guidance="Покажи не облегчение, а усталую осторожность после пережитой угрозы.",
                is_critical=True,
            )

        if _has_any(tags, ["returned_to_abandoned_people", "attempted_moral_repair", "old_betrayal_memory"]):
            return YearOutcome(
                type="attempted_moral_repair_after_terror",
                severity="high",
                title="Возвращение к тем, кого оставили",
                scene="неловкая встреча с человеком или семьёй, перед которыми трудно оправдаться",
                summary="Игрок пытается восстановить человеческую связь после лет страха, но прошлое не стирается.",
                public_consequence="часть людей принимает этот жест, часть видит в нём запоздалую попытку очиститься",
                private_consequence="игрок сталкивается не только с опасностью, но и с памятью о собственных компромиссах",
                extra_effects={"people_support": 1, "survival": -1},
                tags=["moral_repair_attempted"],
                major_event=_major_event(
                    history_turn.year,
                    "Игрок попытался восстановить человеческую связь",
                    "После террора прошлые предательства и молчание не исчезли, но появился шанс на частичное исправление.",
                ),
                prompt_guidance="Пиши о неловкости, стыде и неполном восстановлении доверия.",
                is_critical=True,
            )

        if _has_any(tags, ["consolidated_position_after_purges", "kept_resources_after_fear", "post_terror_opportunism"]):
            return YearOutcome(
                type="post_terror_position_consolidated",
                severity="high",
                title="Положение закрепилось на фоне чужого молчания",
                scene="кабинет, должность или доступ к ресурсам, которые стали возможны после страха",
                summary="Игрок удерживает приобретённое, пока другие ещё боятся говорить.",
                public_consequence="люди признают силу положения, но не обязательно доверяют",
                private_consequence="безопасность держится на том, что прошлое не обсуждают вслух",
                extra_effects={"influence": 1, "wealth": 1, "people_support": -1},
                tags=["post_terror_position_hardened"],
                major_event=_major_event(
                    history_turn.year,
                    "Игрок закрепил положение после волны террора",
                    "Влияние стало прочнее, но социальная цена осталась.",
                ),
                prompt_guidance="Покажи это не как чистый успех, а как закрепление в пространстве страха.",
                is_critical=True,
            )

        return YearOutcome(
            type="after_terror_exhaustion",
            severity="high",
            title="Страх стал привычкой",
            scene="люди снова ходят на работу, но говорят тише, чем раньше",
            summary="1938 год не отменяет пережитое: страх постепенно меняет форму, но не исчезает.",
            public_consequence="общество выглядит спокойнее, но внутри остаётся надлом",
            private_consequence="игрок учится жить так, будто опасность может вернуться",
            extra_effects={"survival": 1},
            tags=["after_terror_exhaustion"],
            major_event=_major_event(
                history_turn.year,
                "Страх стал привычкой",
                "Игрок пережил год усталости после пика террора.",
            ),
            prompt_guidance="Покажи усталость после страха: не резкий поворот к безопасности, а медленное изменение воздуха.",
            is_critical=True,
        )

    def _resolve_1939(
        self,
        history_turn: HistoryTurn,
        role: RoleDefinition,
        choice: ChoiceDefinition,
        stats_before: dict[str, int],
        stats_after: dict[str, int],
        tags: set[str],
        major_events: list[str],
    ) -> YearOutcome:
        if _has_any(tags, ["wartime_instability_as_chance", "anti_state_war_risk", "final_secret_resistance"]):
            return YearOutcome(
                type="war_crisis_as_dangerous_chance",
                severity="critical",
                title="Война стала шансом и угрозой",
                scene="газеты, слухи о пакте, тревожные разговоры и мысль, что большая нестабильность может всё изменить",
                summary=(
                    "Игрок видит во внешнем кризисе возможность для скрытой борьбы, но именно война делает "
                    "подозрение особенно опасным."
                ),
                public_consequence="любая двусмысленность теперь может быть истолкована как угроза государству",
                private_consequence="игрок входит в 1940 год с ощущением, что ставка стала выше, чем когда-либо",
                extra_effects={"suspicion": 2, "survival": -1},
                tags=["entered_war_crisis_as_hidden_enemy"],
                major_event=_major_event(
                    history_turn.year,
                    "Игрок встретил войну как опасный шанс",
                    "Внешний кризис усилил риск разоблачения и подвёл личную историю к финалу.",
                ),
                prompt_guidance="Свяжи 1939 год с накопленной биографией. Это последний год перед финалом, поэтому текст должен звучать как преддверие итоговой судьбы.",
                is_critical=True,
            )

        if _has_any(tags, ["war_preparation_resources", "adaptive_survival_strategy", "connections_before_war"]):
            return YearOutcome(
                type="war_crisis_adaptive_survival",
                severity="critical",
                title="Ресурсы стали подготовкой к новой неизвестности",
                scene="собранные связи, припасы, документы и разговоры о том, куда повернёт страна",
                summary="Игрок не управляет большой политикой, но пытается войти в новый кризис с запасом защиты.",
                public_consequence="люди видят в игроке человека, который умеет готовиться раньше других",
                private_consequence="адаптация помогает выживать, но не даёт ясного морального оправдания прожитым компромиссам",
                extra_effects={"survival": 1, "wealth": 1},
                tags=["entered_war_crisis_prepared"],
                major_event=_major_event(
                    history_turn.year,
                    "Игрок подготовился к военному кризису",
                    "Связи и ресурсы стали частью стратегии выживания.",
                ),
                prompt_guidance="Сделай итог прагматичным: ресурсы помогают, но не отменяют одиночество и цену приспособления.",
                is_critical=True,
            )

        if _has_any(tags, ["state_line_before_war", "foreign_policy_loyalty", "mobilization_ready"]) or stats_after.get("loyalty", 0) >= 7:
            return YearOutcome(
                type="war_crisis_state_loyalty",
                severity="critical",
                title="Судьба окончательно связана с государством",
                scene="новая официальная линия, газеты, собрание и готовность принять очередной поворот",
                summary="Игрок входит в военный кризис как человек системы, привыкший связывать личную безопасность с государством.",
                public_consequence="власть видит в игроке надёжного исполнителя новой линии",
                private_consequence="личная судьба становится почти неотделимой от решений государства",
                extra_effects={"loyalty": 1, "influence": 1},
                tags=["entered_war_crisis_as_state_person"],
                major_event=_major_event(
                    history_turn.year,
                    "Игрок окончательно связал судьбу с государством",
                    "1939 год закрепил его зависимость от официальной линии.",
                ),
                prompt_guidance="Покажи не политический анализ пакта, а личное ощущение человека, который снова должен принять новую линию.",
                is_critical=True,
            )

        return YearOutcome(
            type="war_crisis_uncertain_final_turn",
            severity="critical",
            title="Новая война застала игрока с накопленным прошлым",
            scene="газеты, слухи, тревожное ожидание и взгляд назад на прожитые двадцать лет",
            summary="1939 год собирает последствия прежних решений и переводит личную историю к финалу.",
            public_consequence="люди оценивают игрока не по одному поступку, а по всей прожитой биографии",
            private_consequence="игрок понимает, что будущий кризис встретит уже не тем человеком, каким был в 1920 году",
            extra_effects={},
            tags=["entered_war_crisis_with_uncertain_fate"],
            major_event=_major_event(
                history_turn.year,
                "Игрок вошёл в новый мировой кризис",
                "Финальная судьба стала результатом всей накопленной биографии.",
            ),
            prompt_guidance="Сделай итог 1939 года мостом к финалу: важны прошлые события, одиночество, связи и цена выживания.",
            is_critical=True,
        )

    def _default_outcome(
        self,
        history_turn: HistoryTurn,
        role: RoleDefinition,
        choice: ChoiceDefinition,
        stats_after: dict[str, int],
        tags: set[str],
    ) -> YearOutcome:
        if choice.id == "A":
            return YearOutcome(
                type="loyalty_path_step",
                severity="medium",
                title="Лояльность стала частью биографии",
                scene="официальная речь, собрание, работа или публичное подтверждение правильной позиции",
                summary="Игрок укрепляет положение через понятность и полезность для власти.",
                public_consequence="власть воспринимает игрока надёжнее",
                private_consequence="часть личных сомнений или человеческих связей приходится отодвинуть",
                extra_effects={},
                tags=["loyalty_path_continued"],
                major_event=_major_event(
                    history_turn.year,
                    "Игрок сделал шаг по линии лояльности",
                    "Положение стало понятнее для власти, но личная цена сохранилась.",
                ),
                prompt_guidance="Не делай итог одинаково победным. Покажи, что лояльность даёт защиту, но требует цены.",
                is_critical=False,
            )

        if choice.id == "B":
            return YearOutcome(
                type="pragmatic_gain_step",
                severity="medium",
                title="Прагматичная выгода оставила след",
                scene="сделка, полезное знакомство, доступ к ресурсу или осторожный обмен услугами",
                summary="Игрок получает практическую пользу, но делает своё положение более неоднозначным.",
                public_consequence="одни люди видят полезность игрока, другие — расчётливость",
                private_consequence="выгода помогает жить, но увеличивает зависимость от сомнительных связей",
                extra_effects={},
                tags=["pragmatic_path_continued"],
                major_event=_major_event(
                    history_turn.year,
                    "Игрок выбрал прагматичную выгоду",
                    "Ресурсы и связи стали важнее открытой позиции.",
                ),
                prompt_guidance="Покажи выгоду конкретно: ресурс, связь, должность, услуга. Добавь социальную цену.",
                is_critical=False,
            )

        return YearOutcome(
            type="hidden_resistance_step",
            severity="medium",
            title="Скрытый риск стал частью пути",
            scene="частный разговор, помощь не тому человеку, осторожный жест или поступок без свидетелей",
            summary="Игрок делает выбор против безопасной линии, и этот выбор может вернуться позже.",
            public_consequence="снаружи всё может выглядеть тихо, но вокруг появляются следы и свидетели",
            private_consequence="игрок чувствует, что даже маленький скрытый поступок увеличивает будущий риск",
            extra_effects={},
            tags=["hidden_resistance_path_continued"],
            major_event=_major_event(
                history_turn.year,
                "Игрок оставил скрытый риск в биографии",
                "Поступок не меняет историю страны, но меняет личную опасность.",
            ),
            prompt_guidance="Не превращай скрытое сопротивление в героический успех. Главное — риск, след и будущая цена.",
            is_critical=False,
        )
