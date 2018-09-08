import imaplib
import json
import re
from time import sleep

from django.conf import settings
from pytils import translit


def get_first_text_block(email_message_instance):
    maintype = email_message_instance.get_content_maintype()
    if maintype == 'multipart':
        for part in email_message_instance.get_payload():
            if part.get_content_maintype() == 'text':
                return part.get_payload()
    elif maintype == 'text':
        return email_message_instance.get_payload()


class Mailer:
    """
    Класс работы с почтовым ящиком
    """
    def __init__(self):
        self.mail = None
        self.NeedConnectionMessage = "Отсутствует подключение к серверу. Используйте connect"

    def connect(self, url, login, password):
        """
        Производит подключение к почтовому серверу
        :param url:
        :param login:
        :param password:
        :return: список папок на сервере
        """
        import socket
        settings.LOGGER.info("Logging in mail server. Login %s" % login)
        tmp = socket.getdefaulttimeout()
        socket.setdefaulttimeout(10)
        try:
            self.mail = imaplib.IMAP4_SSL(url, 993)
            settings.LOGGER.info("Successfully connected")
        except:
            settings.LOGGER.error("Can`t connect to mail server")
            self.mail = None
        socket.setdefaulttimeout(tmp)
        if self.mail is None:
            return []
        try:
            self.mail.login(login, password)
            settings.LOGGER.info("Successfully logged in.")
        except:
            settings.LOGGER.error("Auth error")
            return []
        folders = self.mail.list()
        return folders

    def select(self, folder):
        """
        Подключается к папке с письмами
        :param folder: имя папки с письмами
        :return: True В случае успешного подключения
        """
        if self.mail is None:
            raise Exception(self.NeedConnectionMessage)
        self.mail.select(folder)
        return True

    def get_links(self, pattern):
        """
        Возвращает tuple из ссылок для подтверждения и удаления объявлений.
        При успешном извлечении ссылок из письма удаляет его с сервера.
        :param pattern: текст объявления, ссылки для которого ищем
        :return:
        """
        self.select('INBOX')
        if self.mail is None:
            raise Exception(self.NeedConnectionMessage)
        tmp_result, data = self.mail.search(None, '(FROM "uhta24.ru")')
        ids = data[0]
        result = None
        settings.LOGGER.info("Got mail ids %s." % ids)
        id_list = ids.split()
        for uid in id_list:
            settings.LOGGER.info("Checking message %s" % uid)
            tmp_result, data = self.mail.fetch(uid, '(RFC822)')
            if data is None:
                return None
            if data[0] is None:
                continue
            raw_email = data[0][1]
            import email
            settings.LOGGER.info("Parsing message %s" % uid)
            email_message = email.message_from_bytes(raw_email)
            content = get_first_text_block(email_message)
            if content.find(pattern) != -1:
                settings.LOGGER.info("PATTERN %s FOUND" % translit.translify(pattern))
                result = re.findall(r'http.*\b', content)
                if len(result) != 2:
                    continue
                result = result[0], result[1]
                settings.LOGGER.info("Find links %s %s" % result)
                self.mail.store(uid, '+FLAGS', '\\Deleted')
                self.mail.expunge()
                settings.LOGGER.info("Deleting message %s" % uid)
                break
        return result

    def logout(self):
        settings.LOGGER.info("Logging out of mail server")
        try:
            self.mail.close()
            self.mail.logout()
            sleep(5)
            settings.LOGGER.info("Logged out")
        except:
            settings.LOGGER.error()


def get_links(server, login, password, pattern):
    try:
        m = Mailer()
        m.connect(server, login, password)
        result = m.get_links(pattern)
        m.logout()
        settings.LOGGER.info("get_links done")
        return result
    except:
        settings.LOGGER.exception("get links failed")
        return None
