import re


def get_mail_attachments(mail):
    files = []
    for file_ref in re.finditer(r'\[.*]\(/.*\)', mail['content']):
        ref_span = file_ref.span()
        ref_string = mail['content'][ref_span[0]:ref_span[1]]

        fname, raw_furl = ref_string.split("](")
        fname = fname.split("[")[-1]
        raw_furl = raw_furl.split(")")[0]

        furl = f"https://dass.npst.no{raw_furl}" if raw_furl.startswith("/") else raw_furl

        files.append({"url": furl, "fname": fname, "raw": furl})
    return files


def render_mail(mail):
    message_content = f"~~{' ' * 200}~~\n"
    message_content += f"Sent: [{mail['sent']}]\n"
    message_content += f"From: [{mail['from']}]\n"
    message_content += f"To: [{', '.join([to.replace('{{display_name}}', 'YOU') for to in mail['to']])}]\n"
    message_content += f"Subject: {mail['subject']}\n"
    mail_content = mail['content']
    files = get_mail_attachments(mail)
    for file in files:
        if file['raw'] != file['url']:
            ref_string = f"[{file['fname']}]({file['raw']})"
            mail_content = mail_content.replace(ref_string, f"[{file['fname']}]({file['url']})")
    message_content += mail_content
    return message_content
