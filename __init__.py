import DASSBetjent
import os

if __name__ == "__main__":
    bot = DASSBetjent.DassBetjent()
    bot.run(os.environ["DASSBETJENT_DISCORD_TOKEN"], os.environ["DASSBETJENT_NPST_TOKEN"])
