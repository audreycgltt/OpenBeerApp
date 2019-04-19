#!/usr/bin/env python2
# -*- coding: utf-8 -*-
""" OpenBeer App Skill  for the Snips voice assistant. """

from hermes_python.hermes import Hermes
from hermes_python.ontology import *
import beer_db
import random

CONFIGURATION_ENCODING_FORMAT = "utf-8"

MQTT_IP_ADDR = "localhost"
MQTT_PORT = 1883
MQTT_ADDR = "{}:{}".format(MQTT_IP_ADDR, str(MQTT_PORT))

INTENT_ASK_DESCRIPTION = "redTitan:AskDescription"
INTENT_START_SEARCH_INFO = 'redTitan:StartSearchInfoBeerByName'
INTENT_SEARCH_FOR_DRINK = "redTitan:AskForWatToDrink"
INTENT_SEARCH_FOR_FOOD = "redTitan:AskForWatToEat"
INTENT_ASK_ATTRIBUTE = "redTitan:AskForAttribute"
INTENT_ADD_FAV = "redTitan:AddToFav"
INTENT_LIST_FAV = "redTitan:ListFavBeers"
INTENT_REMOVE_FAV = "redTitan:RemoveBeerFromFav"
INTENT_ABANDON_REQUEST = "redTitan:AbandonRequest"
INTENT_YES_APPROVAL = "redTitan:YesApprobation"
INTENT_NO_DISAPPROVAL = "redTitan:NoDisapproval"

INTENT_FILTER_GET_ANSWER_FROM_INFO = [
    INTENT_ASK_ATTRIBUTE,
    INTENT_ADD_FAV,
    INTENT_ABANDON_REQUEST
]

# If request isn't satisfied, Snips apologies.
APOLOGIES = [u"Didn't catch the name, sorry",
             u"I'm afraid I didn't understand the name.",
             u"Excuse me, I didn't catch the name.",
             u"Sorry, I didn't understand."]

# Snips conclusion after the interruption of an action.
INTERRUPT_SENT = [u"Okay, no problem",
                  u"Done",
                  u"Okay, see ya",
                  u"Okay",
                  u"No problem Honey.",
                  u"Okey-Dokey Artichoke"]


class OpenBeerApp(object):
    """OpenBeerApp class wrapper"""

    def __init__(self):

        self.db_access = beer_db.BeerDB("beers.db")
        self.sessionstate = {}
        self.start_blocking()

    def askdescription_callback(self, hermes, intent_message):
        """ Ask the description of a specific beer. One-turn action. """
        session_id = intent_message.session_id

        if intent_message.slots.beerName:
            detected_beer_name = intent_message.slots.beerName.first().value

            beer_description = self.db_access.search_description_by_name(detected_beer_name)

            hermes.publish_end_session(session_id, beer_description)
        else:
            hermes.publish_end_session(session_id, random.choice(APOLOGIES))

    def startinfosearch_callback(self, hermes, intent_message):
        """ Start asking information about a specific beer. """

        if intent_message.slots.beerName:
            detected_beer_name = intent_message.slots.beerName.first().value

            session_state, response, continues = self.db_access.start_search_info(detected_beer_name)

            if not continues:
                hermes.publish_end_session(intent_message.session_id, response)
                beer_db.remove_session_state(self.sessionstate, intent_message.session_id)
                return

            beer_db.save_session_state(self.sessionstate, intent_message.session_id, session_state)

            hermes.publish_continue_session(intent_message.session_id, response, INTENT_FILTER_GET_ANSWER_FROM_INFO)
        else:
            hermes.publish_end_session(intent_message.session_id, random.choice(APOLOGIES))

    def startsearchwattodrink_callback(self, hermes, intent_message):
        """ Start asking a beer suggestion according to food. """

        if intent_message.slots.dishes:
            detected_dish = intent_message.slots.dishes.first().value

            session_state, response = self.db_access.search_style_from_dish(detected_dish)
            beer_db.save_session_state(self.sessionstate, intent_message.session_id, session_state)

            hermes.publish_continue_session(intent_message.session_id, response, [INTENT_YES_APPROVAL, INTENT_NO_DISAPPROVAL, INTENT_ABANDON_REQUEST])
        else:
            session_state = {}
            response = "What are you planning to eat ?"
            beer_db.save_session_state(self.sessionstate, intent_message.session_id, session_state)
            hermes.publish_continue_session(intent_message.session_id, response, [INTENT_SEARCH_FOR_DRINK, INTENT_ABANDON_REQUEST])

    def startsearchwattoeat_callback(self, hermes, intent_message):
        """ Ask food suggestion according to the name of the understood beer name. One-turn action. """

        if intent_message.slots.beerName:
            detected_beer = intent_message.slots.beerName.first().value

            response = self.db_access.search_dish_from_beer(detected_beer)

            hermes.publish_end_session(intent_message.session_id, response)
        else:
            hermes.publish_end_session(intent_message.session_id, random.choice(APOLOGIES))

    def user_ask_for_attribute(self, hermes, intent_message):
        """ After asking for information, the user indicates which attribute does it want to know."""
        session_id = intent_message.session_id
        session_state = self.sessionstate.get(session_id)

        if intent_message.slots.beerattribute:
            detected_attribute = intent_message.slots.beerattribute.first().value

            session_state, response, continues = self.db_access.search_for_attribute(session_state, detected_attribute)

            if not continues:
                hermes.publish_end_session(session_id, response)
                beer_db.remove_session_state(self.sessionstate, session_id)
                return

            hermes.publish_continue_session(session_id, response, INTENT_FILTER_GET_ANSWER_FROM_INFO)

        else:
            hermes.publish_end_session(session_id, random.choice(APOLOGIES))
            beer_db.remove_session_state(self.sessionstate, session_id)
            return

    def add_beer_to_fav(self, hermes, intent_message):
        """ After asking for information, the user can decide to add a beer to its favourites. """

        session_id = intent_message.session_id
        session_state = self.sessionstate.get(session_id)

        session_state, response = self.db_access.add_beer_to_fav(session_state)

        hermes.publish_end_session(session_id, response)
        beer_db.remove_session_state(self.sessionstate, session_id)
        return

    def list_fav_beers(self, hermes, intent_message):
        """ After asking for information, the user can decide to add a beer to its favourites. """

        session_id = intent_message.session_id

        response = self.db_access.list_all_fav_beers()

        hermes.publish_end_session(session_id, response)

    def remove_fav_beer(self, hermes, intent_message):
        """ After asking for information, the user can decide to add a beer to its favourites. """

        session_id = intent_message.session_id

        if intent_message.slots.beerName:
            detected_beer_name = intent_message.slots.beerName.first().value

            response = self.db_access.remove_beer_from_fav(detected_beer_name)

            hermes.publish_end_session(session_id, response)
        else:
            hermes.publish_end_session(session_id, random.choice(APOLOGIES))

    def user_say_yes(self, hermes, intent_message):
        """ The user is answering 'Yes' to a query from the assistant. """

        session_id = intent_message.session_id
        session_state = self.sessionstate.get(session_id)

        response = self.db_access.search_beer_from_style(session_state)

        hermes.publish_end_session(session_id, response)
        beer_db.remove_session_state(self.sessionstate, session_id)

    # def user_say_no(self, hermes, intent_message):
    #
    #     session_id = intent_message.session_id
    #
    #     hermes.publish_end_session(session_id, random.choice(INTERRUPT_SENT))
    #     beer_db.remove_session_state(self.sessionstate, session_id)

    def user_interrupt(self, hermes, intent_message):
        """ The user is saying 'No' to a query or interrupt an action. """

        session_id = intent_message.session_id

        hermes.publish_end_session(session_id, random.choice(INTERRUPT_SENT))
        beer_db.remove_session_state(self.sessionstate, session_id)

    # --> Master callback function, triggered everytime an intent is recognized
    def master_intent_callback(self, hermes, intent_message):
        coming_intent = intent_message.intent.intent_name

        if coming_intent == INTENT_ASK_DESCRIPTION:
            self.askdescription_callback(hermes, intent_message)

        elif coming_intent == INTENT_START_SEARCH_INFO:
            self.startinfosearch_callback(hermes, intent_message)

        elif coming_intent == INTENT_ASK_ATTRIBUTE:
            self.user_ask_for_attribute(hermes, intent_message)

        elif coming_intent == INTENT_ABANDON_REQUEST:
            self.user_interrupt(hermes, intent_message)

        elif coming_intent == INTENT_ADD_FAV:
            self.add_beer_to_fav(hermes, intent_message)

        elif coming_intent == INTENT_LIST_FAV:
            self.list_fav_beers(hermes, intent_message)

        elif coming_intent == INTENT_REMOVE_FAV:
            self.remove_fav_beer(hermes, intent_message)

        elif coming_intent == INTENT_SEARCH_FOR_DRINK:
            self.startsearchwattodrink_callback(hermes, intent_message)

        elif coming_intent == INTENT_SEARCH_FOR_FOOD:
            self.startsearchwattoeat_callback(hermes, intent_message)

        elif coming_intent == INTENT_YES_APPROVAL:
            self.user_say_yes(hermes, intent_message)

        """
        elif coming_intent == INTENT_NO_DISAPPROVAL:
            self.user_interrupt(hermes, intent_message)"""

    def start_blocking(self):
        """ Subscribe to all intents.  """
        with Hermes(MQTT_ADDR, rust_logs_enabled=True) as h:
            h.subscribe_intents(self.master_intent_callback).start()


if __name__ == "__main__":
    OpenBeerApp()