import discord
import re


def format_display_name(display_name: str, illegal_strings=('👉', '👑', ':crown:', ':point_right:')):
    formatted = display_name[:20]
    if len(display_name) > 20:
        formatted += '...'
    for illegal_string in illegal_strings:
        formatted = formatted.replace(illegal_string, '💩')
    return formatted


def get_score_user_info(user, score_pos: int):
    formatted_name = format_display_name(user["display_name"])
    points = int(user["challenges_solved"]) * 10
    ret_str = f'#{score_pos+1} {formatted_name} - {points} poeng'

    if user["eggs_solved"] == "0":
        ret_str += '\n'
    else:
        ret_str += f' og ⭐ x {user["eggs_solved"]}\n'
    
    return ret_str


def get_max_score_users(score):
    highest_score = [score[0]["challenges_solved"], score[0]["eggs_solved"]]

    for x, user in enumerate(score):
        user_score = [user["challenges_solved"], user["eggs_solved"]]
        if user_score != highest_score:
            return x


async def get_scoreboard_embed(scoreboard, input_users=()):
    if scoreboard is None:
        return discord.Embed(
            title="Poengoversikt",
            color=0xff0000,
            description="Det oppsto en feil!\nKlarte ikke å hente scoreboardet."
        )

    embed_description = ""
    embed_finished = False
    scoreboard_users = 0
    for x, user in enumerate(scoreboard):
        if len(input_users) > 0:
            for input_user in input_users:
                if input_user.lower() in user['display_name'].lower():
                    embed_description += get_score_user_info(user, x)
                    scoreboard_users += 1
                    if scoreboard_users >= 15:
                        embed_description += '...'
                        embed_finished = True
                        break
        else:
            scoreboard_users += 1
            embed_description += get_score_user_info(user, x)
            if scoreboard_users >= 15:
                max_score_users = get_max_score_users(scoreboard)
                embed_description += f'...\n\n{max_score_users} alvebetjenter har maks poeng'

                embed_finished = True

        if embed_finished:
            break
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
