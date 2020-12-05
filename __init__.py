import DASSBetjent
import logging
import os

if __name__ == "__main__":
    logging.basicConfig()
    logging.getLogger("DASSBetjent").setLevel(logging.DEBUG)
    bot = DASSBetjent.DASSBetjent()
    bot.run(os.environ["DASSTEST_DISCORD_TOKEN"], os.environ["DASSBETJENT_NPST_TOKEN"])
