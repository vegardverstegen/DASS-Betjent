import discord
import re


def format_display_name(display_name: str, illegal_strings=('👉', '👑', ':crown:', ':point_right:')):
    formatted = display_name[:20]
    if len(display_name) > 20:
        formatted += '...'
    for illegal_string in illegal_strings:
        formatted = formatted.replace(illegal_string, '💩')
    return formatted


def get_score_user_info(user):
    formatted_name = format_display_name(user["name"])
    points = int(user["score"])
    score_pos = user["pos"]
    ret_str = f'#{score_pos+1} {formatted_name} - {points} poeng\n'

    return ret_str


def get_max_score_users(score):
    highest_score = [score[0]["score"]]

    for x, user in enumerate(score):
        user_score = [user["score"]]
        if user_score != highest_score:
            return x


async def get_scoreboard_embed(scoreboard, input_users=()):
    if scoreboard is None:
        return discord.Embed(
            title="FEIL",
            color=0xff0000,
            description="Det oppsto en feil!\nKlarte ikke å hente scoreboardet."
        )

    embed_description = ""
    embed_finished = False
    scoreboard_users = 0
    for user in scoreboard:
        if len(input_users) > 0:
            for input_user in input_users:
                if input_user.lower() in user['name'].lower():
                    embed_description += get_score_user_info(user)
                    scoreboard_users += 1
                    if scoreboard_users >= 15:
                        embed_description += '...'
                        embed_finished = True
                        break
        else:
            scoreboard_users += 1
            embed_description += get_score_user_info(user)
            if scoreboard_users >= 15:
                max_score_users = get_max_score_users(scoreboard)
                embed_description += f'...\n\n{max_score_users}/{len(scoreboard)} alvebetjenter har maks poeng'

                embed_finished = True

        if embed_finished:
            break

    if embed_description == '':
        return discord.Embed(title='FEIL', color=0x50bdfe, description='Brukeren ble ikke funnet!')

    return discord.Embed(title='Poengoversikt', color=0x50bdfe, description=embed_description)


def render_mail(mail):
    message_content = f"~~{' ' * 200}~~\n"
    message_content += f"Sent: [{mail['sent']}]\n"
    message_content += f"From: [{mail['from']}]\n"
    message_content += f"To: [{', '.join([to.replace('{{display_name}}', 'YOU') for to in mail['to']])}]\n"
    message_content += f"Subject: {mail['subject']}\n"
    mail_content = mail['content']
    for result in re.finditer(r'(\[.*\]\((.*)\))', mail_content):
        mail_content = mail_content.replace(result.groups(0)[0], f"https://dass.npst.no{result.groups(0)[1]}")
    message_content += mail_content
    return message_content