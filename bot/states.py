from aiogram.fsm.state import State, StatesGroup


class VoiceInput(StatesGroup):
    waiting_for_voice = State()


class ProgressInput(StatesGroup):
    waiting_for_episode = State()


class LinkInput(StatesGroup):
    waiting_for_link = State()


class TitleInput(StatesGroup):
    waiting_for_title = State()