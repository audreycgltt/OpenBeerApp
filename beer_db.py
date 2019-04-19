#!/usr/bin/env python2
# -*- coding: utf-8 -*-
""" OpenBeer App methods in order to access and query the database. """

import sqlite3
import random
from datetime import datetime

class BeerDB(object):

    def __init__(self, database='database.db'):
        self.database = database

    def connect(self):
        """ Connection to the database. """
        con = sqlite3.connect(self.database)
        cur = con.cursor()

        return con, cur

    @staticmethod
    def disconnect_and_close(con):
        """ Disconnection from the database.
        :param con Database connector """

        con.commit()
        con.close()

    def search_description_by_name(self, beer_name):
        """ Search a beer in the beers table from a rough beer name.
        :param beer_name (String)
        :return (String) Response of Snips """

        con,cur = self.connect()

        alike_beer_name = "%" + beer_name + "%"
        cur.execute("""SELECT id, name, descript FROM beers WHERE name LIKE ?""", (alike_beer_name,))
        response = cur.fetchone()

        self.disconnect_and_close(con)

        beer_description = response[2]
        if not beer_description or beer_description == '':
            return u"Description unknown, sorry."
        else:
            return u'Description of the {0} : {1}'.format(response[1], response[2])

    def start_search_info(self, beer_name):
        """ Search every information about a specific beer in the databese.
        :param beer_name (String)
        :return session_state (Dict) Information about the beer
        :return (String) Response of Snips
        :return (Bool) Session continuation """

        con, cur = self.connect()

        alike_beer_name = "%" + beer_name + "%"
        response_formats = [u"So, the {0}, what do you want to know?",
                            "What would you like to know about the {0}?",
                            "What info do you want about the {0}?"]

        cur.execute("""SELECT id, name, cat_id, style_id, abv, ibu, srm, descript 
                       FROM beers 
                       WHERE name LIKE ?""", (alike_beer_name,))

        results = cur.fetchall()
        self.disconnect_and_close(con)

        if not results:
            return {}, "Problem finding the beer.", False
        else:
            states_names = ["beer_id", "beer_name", "cat_id", "style_id", "abv", "ibu", "srm", "descript"]
            session_state = dict(zip(states_names, results[0]))

            return session_state, random.choice(response_formats).format(session_state["beer_name"]), True

    def search_for_attribute(self, session_state, beer_attribute):
        """ Return the attribute asked by the user.
        :param session_state (Dict) Information acquired after the last interaction
        :param beer_attribute (String) Attribute asked by the user
        :return session_state (Dict)
        :return response (String) Response of Snips.
        :return bool_continue (Bool) Session continuation """

        question_formats = [u"Would you like something else ?",
                            u"What else ?",
                            u"Do you need something else ?"]
        question_choice = random.choice(question_formats)

        attribute_reshaped = {
            "beer_name": "name",
            "abv": "ABV",
            "ibu": "IBU",
            "srm": "SRM",
            "descript": "description"
        }

        if session_state is None:
            print "Error: session_state is None ==> intent triggered outside of dialog session"
            return session_state, "Session problem", False

        if beer_attribute is None:
            return session_state, "Beer attribute problem", False

        bool_continue = True

        if beer_attribute == "descript":
            beer_description = session_state[beer_attribute]
            if not beer_description or beer_description == '':
                response = "Description unknown."
            else:
                response = beer_description
            bool_continue = False

        elif beer_attribute == "style_name":
            con, cur = self.connect()

            cur.execute("""SELECT style_name
                           FROM styles
                           WHERE id=?""", (session_state["style_id"],))
            results = cur.fetchone()
            self.disconnect_and_close(con)

            style = results[0]
            style_article = select_which_article(style)
            response = u"It's {0} {1}.".format(style_article, style) + question_choice

        else:
            asked_attribute = session_state[beer_attribute]

            if asked_attribute is None:
                raise ValueError("There is some missing info about the question asked")

            response = u"The {0} is {1}".format(attribute_reshaped[beer_attribute], str(asked_attribute)) \
                       + question_choice

        return session_state, response, bool_continue

    def search_style_from_dish(self, dish_name):
        """ Search for the perfect beer style according to the type of the dish.
        :param dish_name (String) Name of a meal
        :return session_state (Dict) Session information
        :return response (String) Response of Snips"""

        con, cur = self.connect()

        styles_list = []
        styles_list_id = []

        response_formats = [u'With {0}, I suggest you to drink {1}. ',
                            u'With {0}, you could drink {1}. ',
                            u"I'm sure that {1} would be perfect. ",
                            u'Well, {1} could be great. ']

        question_formats = [u"Should I suggest you a beer ?",
                            u"Do you want the name of a beer ?",
                            u"Can I suggest you one ?"]
        question_asked = random.choice(question_formats)

        alike_dish_name = "%" + dish_name + "%"

        cur.execute("""SELECT DISTINCT styles.style_name, styles.id
                            FROM styles
                            INNER JOIN food_types ON food_types.style_id = styles.id
                            INNER JOIN dishes ON dishes.food_type_id = food_types.id
                            WHERE dishes.dish_name LIKE ?""", (alike_dish_name,))

        results = cur.fetchall()
        self.disconnect_and_close(con)

        if not results:
            response = u"I'm afraid I do not have this information right now. Sorry."
        else:
            for row in results:
                styles_list.append(select_which_article(row[0]) + " " + row[0])
                styles_list_id.append(row[1])

            if len(styles_list) > 1 :
                linked_styles = ", ".join(styles_list[:-1]) + " or " + styles_list[-1]
            else:
                linked_styles = ", ".join(styles_list)

            response = random.choice(response_formats).format(dish_name, linked_styles) + question_asked

        session_state = {
            "style_id": styles_list_id
        }

        return session_state, response

    def search_beer_from_style(self, session_state):
        """ Return a beer of a specific style from the user's favourites or just a random one.
        :param session_state (Dict) Session information
        :return (String) Snips response """

        if session_state is None:
            print "Error: session_state is None ==> intent triggered outside of dialog session"
            return session_state, u"Session problem"

        if not session_state["style_id"]:
            return u"Style not found"
        else:
            con, cur = self.connect()
            cur.execute('''CREATE TABLE IF NOT EXISTS favourites (beer_id INTEGER, added_date date)''')

            beer_list = []

            for id in session_state["style_id"]:

                cur.execute("""SELECT DISTINCT id, name
                               FROM beers
                               INNER JOIN favourites ON favourites.beer_id = beers.id
                               WHERE beers.style_id=? """, (id,))

                fav_results = cur.fetchall()

                if not fav_results:
                    cur.execute("""SELECT DISTINCT id, name
                                   FROM beers
                                   WHERE style_id=?""", (id,))
                    results = cur.fetchall()
                    for beer in results:
                        beer_list.append(beer[1])
                else:
                    for beer in fav_results:
                        beer_list.append(beer[1])

            try:
                beer_choice = random.choice(beer_list)
                return "I can suggest you a {0}.".format(beer_choice.encode('utf-8'))
            except IndexError:
                return "I'm afraid I have no beer of these types in the database, sorry."

    def search_dish_from_beer(self, beer_name):
        """ Return a food suggestion according to the name of a beer.
        :param beer_name (String)
        :return response (String) """
        con, cur = self.connect()

        food_type_id = []
        food_type_name = []
        dishes = []

        alike_beer_name = "%" + beer_name + "%"

        cur.execute("""SELECT DISTINCT food_types.id, food_types.type_name
                       FROM food_types
                       INNER JOIN beers ON beers.style_id = food_types.style_id
                       WHERE beers.name LIKE ?""", (alike_beer_name,))
        results = cur.fetchall()

        if not results:
            response = u"I am afraid I don't have anything to recommand."
        else:
            for row in results:
                food_type_id.append(row[0])
                food_type_name.append(row[1])
            for id in food_type_id:
                cur.execute("""SELECT DISTINCT dish_name
                               FROM dishes
                               WHERE food_type_id=?""", (id,))
                dish_results = cur.fetchall()
                for dish in dish_results:
                    dishes.append(dish[0])

            dishes_choices = random.sample(dishes, k=2)

            if len(food_type_name) == 1:
                response = u"I suggest you " + food_type_name[0] + u" such as " + u" or ".join(dishes_choices)
            else:
                response = u"I suggest you " + u", ".join(food_type_name[:-1]) + u" or " + food_type_name[-1] \
                       + u" such as " + u" or ".join(dishes_choices)

        return response

    def add_beer_to_fav(self, session_state):
        """ Add a beer in user's favourites.
        :param session_state (Dist) Session information
        :return session_state (Dict)
        :return (String) Snips response """

        if session_state is None:
            print "Error: session_state is None ==> intent triggered outside of dialog session"
            return session_state, "Session problem", False

        con, cur = self.connect()

        beer_id_to_add = session_state["beer_id"]

        cur.execute('''CREATE TABLE IF NOT EXISTS favourites (beer_id INTEGER, added_date date)''')

        current_date = datetime.now()
        cur.execute("""INSERT INTO favourites (beer_id, added_date) VALUES (?, ?)""", (beer_id_to_add, current_date))
        self.disconnect_and_close(con)

        return session_state, "Added to your favourites. Done."

    def list_all_fav_beers(self):
        """ Returns every beer that had been added to the user's favourites.
        :return (String) Snips response """

        con, cur = self.connect()

        cur.execute("""SELECT DISTINCT beers.name
                       FROM favourites
                       INNER JOIN beers ON beers.id = favourites.beer_id""")

        response_sql = cur.fetchall()
        self.disconnect_and_close(con)
        beer_list = []
        for beer in response_sql:
            beer_list.append(beer[0].encode('utf-8'))

        if len(beer_list) == 0:
            response = u"It's empty."
        elif len(beer_list) == 1:
            response = u"You got only one, the {0}.".format(beer_list[0])
        else:
            response = u"Here's the list: " + u", ".join(beer_list[:-1]) + u" and " + beer_list[-1] + u"."

        return response

    def remove_beer_from_fav(self, beer_name):
        """ Remove the selected beer from your favourites list if it's in it.
        :param beer_name (String)
        :return response (String) Snips response """

        response_done = [u'Okay, it has been removed! ',
                         u'Now it\'s done! ',
                         u"It is now removed. ",
                         u'Ok, done!']

        response_not_in_favs = [u'I\'m sorry, but it seems that beer isn\'t in your favourites.',
                         u'Well, I don\'t find that into your list.',
                         u"I\'m afraid that your already don\'t have it in your favourites.",
                         u'I can\'t find that beer in your favs.']

        con, cur = self.connect()

        alike_beer_name = "%" + beer_name + "%"

        cur.execute("""SELECT EXISTS (
                               SELECT 1 FROM favourites
                               INNER JOIN beers ON beers.id = favourites.beer_id
                               WHERE beers.name LIKE ?)""", (alike_beer_name,))

        presence_check = cur.fetchall()[0][0]

        if presence_check:
            cur.execute("""DELETE FROM favourites
                   WHERE beer_id IN (
                   SELECT beer_id FROM favourites
                   INNER JOIN beers ON beers.id = favourites.beer_id
                   WHERE beers.name LIKE ?)""", (alike_beer_name,))
            response = random.choice(response_done)
        else:
            response = random.choice(response_not_in_favs)

        self.disconnect_and_close(con)
        return response


def select_which_article(name):
    """ Select the correct article ('a' or 'an') according to the beginning of a beer style.
    :param name (String) name of a style
    :return (String) An article  """
    if name[0] in ['A','E','I','H'] :
        return 'an'
    else:
        return 'a'


def save_session_state(sessions_states, session_id, new_state):
    """ Save current states of the session.
    :param sessions_states (Dict)
    :param session_id (String)
    :param new_state """

    sessions_states[session_id] = _set_not_none_dict_value(sessions_states.get(session_id), new_state)


def remove_session_state(sessions_states, session_id):
    """ Remove session ID from the State before starting a new session.
    :param sessions_states (Dict) Current session states
    :param session_id (String) Current session ID """

    sessions_states[session_id] = None


def _set_not_none_dict_value(to_update, update):
    to_update = to_update or {}
    for key, value in update.iteritems():
        if value is not None:
            to_update[key] = value
    return to_update