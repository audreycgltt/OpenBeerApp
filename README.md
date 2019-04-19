# OpenBeer App

OpenBeer App is a skill for the vocal assistant [Snips](https://snips.ai/) about zythology ("beer culture"). It is based on the old data of [OpenBeerDB](https://openbeerdb.com/). 

You can now ask to your favourite assistant some information about a specific beer (the style, its description, abv, ibu or srm) and then add it to your favourite !
More over, you can ask what type of food will be the best with a beer or, on the other side, ask which style of beer would be perfect with your tonight's meal. 
It will suggest you in priority the beers that you added into your favourites.

### How does this work ? 

All the information are provided by OpenBeerData. As the API is currently unavailable, it is based only on the old information (a lot of data are missing). 
The data are stored in `beers.db` which is handled with Sqlite. Data are divided in six different tables : 
* **beers** : id, brewery_id, name, cat_id, style_id, abv, ibu, srm, upc, filepath, descript, last_mod
* **categories** : id, cat_name, last_mod
* **styles** : id, cat_id, style_name, last_mod
* **food_types** : id, type_name, style_id
* **dishes** : id, dish_name, food_type_id
* **favourites** : beer_id, added_date

All the food suggestions are based on the [Beer & Food pairing guide](https://cdn.craftbeer.com/wp-content/uploads/beerandfood-1.pdf?fbclid=IwAR3a5CCRC0PjglRoVC1IYTl9JbGIDHqjO48TumMERILYf9MswIzC0gHJAjo) from [CraftBeer](https://www.craftbeer.com/) for now (all styles are not handled yet and there is just a small amount of food types).

### Installation

For now, this app isn't on the Snips App Store yet.

In order to be able to run it on your assistant, you have to install Sqlite on your device. 
(on a raspPi : `sudo apt-get install sqlite`)

Sqlite must have the right to write on `beers.db` and on the directory of the Snips skills (usually located in `/var/lib/snips/skills/OpenBeerApp` on the Pi).

For any troubles with installation or other platforms, please visit the official [Snips documentation](https://docs.snips.ai/).

### Usage

##### Ask for information about a specific beer: 
* _"I want information about the **Amber beer**."_
* _"I would like to know some information about the **Guinness.**"_
* _"I would like some info about the **Mad Bitch**, please."_
* _"Get info on the **Yakima Glory**."_

##### Ask your assistant to suggest you a beer: 
* _"What beer would be perfect with a **risotto**?"_
* _"I am eating **lentils** tonight, what do you suggest?"_
* _"Could you suggest me something with **Rice**?"_
* _"What can I drink with **Artichoke**?"_
* _"Could you suggest me something to drink with a **Raclette**?"_

##### Ask for food suggestion:
* _"What can I eat with a **Guinness**?"_
* _"What can I cook with a **Belgian Abbey**?"_
* _"Tell me what to eat with a **Boulevard Pale Ale**, please."_
* _"Knowing that I have a **Dulle Teve**, what should I eat?"_

##### Ask for the listing of your favourite beers:
* _"Which beers do I have into my favourites ?"_
* _"How much beers fo I have into my favourites"_
* _"Give me my favourites"_
* _"List all my favs"_

##### Remove a beer from your favourites:
* _"Remove the **Benchwarmer Porter** please"_
* _"Delete from my favorites the **Moosehead Lager**"_
* _"Remove the **Hocus Pocus** from my favourites"_
* _"Would you please delete the **Big Easy Beer**."_

### Limitations

This app is made for english-speaking assistants. Due to that, Snips is really bad for recognising beer names that are in french or belgian (I still didn't figured out how to ask for information about the Chouffe...).

Otherwise, the database contains other 5800 different beers, even if all of them have been added, a lot of famous ones are still missing. 
Some beers containing strange characters in their names or some with really similar names might not be understood correctly.

Also, there're just a sample of dishes, feel free to suggest any me that could be add !
  