import DASSBetjent
import logging
import yaml
#  import os

if __name__ == "__main__":
    logging.basicConfig()
    logging.getLogger("DASSBetjent").setLevel(logging.DEBUG)

    with open("keys.yaml", "r") as fr:
        keys = yaml.load(fr, Loader=yaml.FullLoader)

    bot = DASSBetjent.DASSBetjent(prefix="+")
    bot.run(keys["npst"], keys["discord"])
