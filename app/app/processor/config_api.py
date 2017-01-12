# coding: utf-8
from flask_restful import Resource, marshal, fields
from flask import current_app
from app.processor.models import ActionStatus, PersonType, ModelType
from app.processor.models import ModelStatus


defaults = {
    'ipp_latitude': 49.542683501849396,
    'ipp_longitude': 20.113735329584898,
    'rp_latitude': 49.542683501849396,
    'rp_longitude': 20.113735329584898,
    'map_latitude': 49.542683501849396,
    'map_longitude': 20.113735329584898,
    'map_zoom': 12,
    'map_base': 'topo'
}

labels = {
    "add_analysis": "Dodaj analizę",
    "edit_analysis": "Edytuj analizę",
    "action_removed": "Akcja została usunięta",
    "action_archived": "Akcja została zarchiwizowana",
    "action_unarchived": "Akcja została przywrócona",
    "action_created": "Akcja została utworzona",
    "analysis_removed": "Analiza została usunięta",
    "analysis_created": "Analiza została utworzona",
    "analysis_started": "Analiza zostanie rozpoczęta",
    "analysis_name": "Nazwa analizy",
    "action_name": "Nazwa akcji",
    "search": "Szukaj",
    "action_details": "Szczegóły",
    "save": "Zapisz",
    "ok": "OK",
    "create": "Utwórz",
    "remove": "Usuń",
    "remove_analysis": "Usuń analizę",
    "archive": "Archiwizuj",
    "cancel": "Anuluj",
    "new_action": "Nowa akcja",
    "edit_action": "Edytuj akcję",
    "new_analysis": "Nowa analiza",
    "confirm_required": "Wymagane potwierdzenie",
    "logout": "Wyloguj",
    "notifications": "Powiadomienia",
    "no_new_notifications": "brak nowych powiadomień",
    "actions_list": "Lista akcji",
    "analyses_list": "Lista analiz",
    "close": "Zamknij",
    "optional_description": "Opcjonalny opis",
    "description": "Opis",
    "lost_date": "Data zaginięcia",
    "hour": "Godzina",
    "name": "Nazwa",
    "display": "Wyświetl",
    "all_actions": "Wszystkie akcje",
    "hide_archived": "Ukryj zarchiwizowane",
    "archived_only": "Tylko zarchiwizowane",
    "action_status": "Status akcji",
    "from": "Od",
    "to": "Do",
    "created_date": "Data utworzenia",
    "action_type": "Rodzaj akcji",
    "select_window": "Wybierz okno",
    "window": "Okno",
    "used": "Używane",
    "open_new_window": "Otwórz nowe okno",
    "enable_popups": "Proszę odblokować wyskakujące okienka na stronie i spróbować ponownie.",
    "connected_action": "Powiązana akcja",
    "select_on_map": "Zaznacz na mapie",
    "location": "Położenie",
    "ipp_lat": "IPP (szerokość)",
    "ipp_lng": "IPP (długość)",
    "rp_lat": "RP (szerokość)",
    "rp_lng": "RP (długość)",
    "ipp_coordinates": "Współrzędne IPP",
    "rp_coordinates": "Współrzędne RP",
    "models": "Modele",
    "categories": "Kategorie",
    "select_action": "Wybierz akcję",
    "created": "Utworzono",
    "create_action": "Utwórz akcję",
    "no_results_for": "Brak wyników dla",
    "start_typing_for_suggestions": "Aby wyświetlić sugestie rozpocznij wpisywanie nazwy akcji.",
    "close_tab": "Zamknij zakładkę",
    "models_list": "Lista modeli",
    "open_map": "Otwórz mapę",
    "analysis_status": "Status analizy",
    "start": "Wykonaj",
    "copy": "Duplikuj",
    "unarchive": "Przywróć",
    "edit": "Edytuj",
    "information": "Informacja",
    "revert": "Cofnij",
    "changes_saved": "Zmiany zostały zapisane",
    "add_new": "Dodaj nową",
    "no_analyses": "Brak analiz",
    "no_actions": "Brak akcji",
    "or": "lub",
    "refresh": "Odśwież",
    "set": "Ustaw",
    "set_ipp": "Ustaw współrzędne IPP",
    "set_rp": "Ustaw współrzędne RP",
    "show_layer": "Pokaż warstwę",
    "visible": "widoczna",
    "hidden": "ukryta",
    "select_all": "Zaznacz wszystkie",
    "deselect_all": "Odznacz wszystkie",
    "retry": "Spróbuj ponownie",
    "no_opened_windows": "brak otwartych okien"
}

model_labels = {
    "IPP_RP": "IPP - RP",
    "HorDistIPP": "Odległość horyzontalna od IPP",
    "ElevChgIPP": "Zmiana wysokości względem IPP",
    "HorChgIPP": "Zmiana horyzontalna względem IPP",
    "DispAngle": "Rozproszenie kątowe",
    "TrackOffset": "Przesunięcie względem obiektów liniowych",
    "FindLocation": "Lokalizacja odniesienia",
    "Mobility": "Mobilność",
    "CombProb": "Suma prawdopodobieństw",
    "SearchSeg": "Wyznaczenie segmentów poszukiwawczych"
}

person_labels = {
    "tourist": "Turysta",
    "hunter": "Myśliwy",
    "fisherman": "Wędkarz",
    "atv": "ATV",
    "autistic": "Os. autystyczna",
    "child_1_3": "Dziecko 1-3",
    "child_4_6": "Dziecko 4-6",
    "child_7_9": "Dziecko 7-9",
    "child_10_12": "Dziecko 10-12",
    "child_13_15": "Dziecko 13-15",
    "climber": "Wspinacz",
    "dementia": "Demencja (Alzheimer)",
    "depressed": "Os. z depresją",
    "collector": "Zbieracz",
    "horseman": "Jeździec",
    "mentally_ill": "Os. chora psychicznie",
    "mentally_disabled": "Os. niepełnosprawna intelektualnie",
    "mountain_cyclist": "Kolarz górski",
    "extreme_sports": "Os. uprawiająca sporty ekstremalne",
    "motorcyclist": "Motocyklista",
    "runner": "Biegacz",
    "alpine_skier": "Narciarz alpejski",
    "classic_skier": "Narciarz klasyczny",
    "snowboarder": "Snowboardzista",
    "snowmobile": "Os. na skuterze śnieżnym",
    "psychoactive": "Os. pod wpływem subst. psychoakt.",
    "vehicle": "Os. z pojazdem",
    "manual_worker": "Robotnik"
}

status_labels = {
    "draft": "Wersja robocza",
    "processing": "Przetwarzanie",
    "finished": "Gotowa",
    "error": "Błąd",
    "converting": "Konwertowanie",
    "sent": "Wysłana",
    "resent": "Wysłana ponownie",
    "confirmed": "Potwierdzona",
    "queued": "W kolejce",
    "calculating": "Liczenie",
    "awaiting": "Oczekuje",
    "computing": "Przetwarzanie",
    "loading": "Wczytywanie",
    "waiting": "Oczekuje"
}

error_labels = {
    "error_title": "Ups!",
    "error_occured": "Podczas przetwarzania wystąpił nieznany błąd: ",
    "error_offline": "Wystąpił problem z połączeniem. \nMożliwa przyczyna to brak dostępu do internetu.",
    "error_does_not_exist": "Nie znaleziono akcji/analizy. \nPrawdopodobnie w międzyczasie została usunięta.",
    "error_validation_failed": "Wysłane dane są niepoprawne.",
    "error_server_not_available": "Nie udało się nawiązać połączenia z serwerem obliczeniowym.",
    "error_analysis_data_incomplete": "Analiza nie posiada wystarczającej ilości danych.",
    "error_request_resource_unavailable": "Nie można wykonać operacji."
}

config_fields = {
    "action_statuses": fields.List(fields.Nested({
        "id": fields.Integer,
        "name": fields.String,
    })),
    "model_statuses": fields.List(fields.Nested({
        "id": fields.Integer,
        "name": fields.String,
    })),
    "person_types": fields.List(fields.Nested({
        "id": fields.Integer,
        "name": fields.String,
    })),
    "model_types": fields.List(fields.Nested({
        "id": fields.Integer,
        "name": fields.String,
        "complex": fields.Boolean,
    })),
    "labels": fields.List(fields.Nested({
        "tag": fields.String,
        "label": fields.String,
    })),
    "endpoint": fields.String,
    "lang": fields.String,
    "notifications": fields.List(fields.String),
    "defaults": fields.Nested({key: fields.Raw for key in defaults}),
    "analysis_draft_id": fields.Integer,
    "analysis_ready_id": fields.Integer,
    "notifications_update_interval": fields.Integer,
    "results_per_page": fields.Integer
}


class TranslationLabel(object):
    def __init__(self, tag, label):
        self.tag = tag
        self.label = label


labels.update(model_labels)
labels.update(person_labels)
labels.update(status_labels)
labels.update(error_labels)
translation_labels = [TranslationLabel(tag=key, label=value) for key, value in labels.items()]


class ConfigApi(Resource):

    def get(self):
        possible_statuses = ['error', 'draft', 'processing', 'waiting', 'finished']
        model_statuses = ModelStatus.query.filter(ModelStatus.name.in_(possible_statuses))
        person_types = PersonType.query.filter(PersonType.active == True)

        possible_model_types = ['HorDistIPP', 'ElevChgIPP', 'HorChgIPP',
                                'DispAngle', 'TrackOffset', 'FindLocation',
                                'Mobility', 'CombProb', 'SearchSeg']
        model_types = ModelType.query.filter(ModelType.active == True,
                                             ModelType.name.in_(possible_model_types))

        endpoint_path = "http://{}:{}/app/api/v1".format(current_app.config['SERVER_ADDR'],
                                 current_app.config['SERVER_PORT'])

        analysis_draft_id = ModelStatus.query.filter(ModelStatus.name == 'draft').first().id
        analysis_ready_id = ModelStatus.query.filter(ModelStatus.name == 'finished').first().id

        config = {
            'endpoint': endpoint_path,
            'action_statuses': model_statuses,
            'model_statuses': model_statuses,
            'person_types': person_types,
            'model_types': model_types,
            'labels': translation_labels,
            'notifications': [],
            'defaults': defaults,
            'analysis_draft_id': analysis_draft_id,
            'analysis_ready_id': analysis_ready_id,
            'lang': 'pl',
            'notifications_update_interval': 60 * 1000,
            'results_per_page': 20
        }

        return marshal(config, config_fields)

