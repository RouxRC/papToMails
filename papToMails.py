#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright Josh Rendek 2009 bluescripts.net
# No liability blah blah use at your own risk, etc

import lxml.html as html
import re, time, sys
import smtplib
from email.mime.text import MIMEText
from config import DEBUG, pap_url, emails

newAnnonces = {}
lastAnnonces = {}
try:
     with open("lastAnnonces.txt") as f:
        for url in f.readlines():
             lastAnnonces[url.strip('\n')] = 1
except:
    pass

re_clean_html = re.compile("[\n\s\r\t]+", re.M)
re_annonce = re.compile("^.*(\d\D+pièces.*€).*$")
re_tel = re.compile("((\d{2}\W*?){4}\d{2})")

# PAP
doc = html.parse(pap_url)
doc = doc.getroot()
annonces = doc.find_class("annonce")
for annonce in annonces:
    url = annonce.xpath("div[@class='header-annonce']/a/@href")[0]
    url = "http://www.pap.fr" + url
    if url in lastAnnonces:
        continue
    lastAnnonces[url] = 1
    text = ""
    header = annonce.find_class("header-annonce")[0].text_content().encode("utf-8")
    header = re_clean_html.sub(" ", header)
    header = re_annonce.sub(r"\1", header)
    header = header.replace(".", "").replace("Paris ", "")
    text += header
    try:
        metro = annonce.find_class("metro")[0].text_content().encode("utf-8")
        text += "\nmetro" + re_clean_html.sub(" ", metro)
    except: pass
    try:
        description = annonce.find_class("description")[0].text_content().encode("utf-8")
        text += " " + re_tel.search(description.strip()).group(0)
    except: pass
    newAnnonces[url] = text

for url, annonce in newAnnonces.items():
    msg = MIMEText(annonce + "\n" + url)
    msg['Subject'] = '[PAP]' + annonce
    if DEBUG:
        print >> sys.stderr, "SendMail", msg.as_string(), "\n----\n"
    else:
        s = smtplib.SMTP('localhost')
        s.sendmail('no-reply@rouxrc-pap.nul', emails, msg.as_string())
        s.quit()
        time.sleep(5)

with open("lastAnnonces.txt", "w") as f:
    for url in lastAnnonces.keys():
        print >> f, url
