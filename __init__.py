import DASSBetjent
import logging
import yaml
import os

if __name__ == "__main__":
    logging.basicConfig()
    logging.getLogger("DASSBetjent").setLevel(logging.DEBUG)

    if os.path.exists("keys.yaml"):
        with open("keys.yaml", "r") as fr:
            keys = yaml.load(fr, Loader=yaml.FullLoader)

        bot = DASSBetjent.DASSBetjent(prefix="+")
        bot.run(keys["npst"], keys["discord"])
    else:
        with open("keys.yaml", "w") as fw:
            yaml.dump({"npst": "ENTER NPST TOKEN HERE", "discord": "ENTER DISCORD TOKEN HERE"}, fw)
        print(f"Please enter keys in keys.yaml")
