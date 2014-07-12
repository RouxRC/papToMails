#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright Josh Rendek 2009 bluescripts.net
# No liability blah blah use at your own risk, etc

import lxml.html as html
import re, time
import smtplib
from email.mime.text import MIMEText
from config import pap_url, emails

#xml parsed
doc = html.parse(pap_url)
doc = doc.getroot()
annonces = doc.find_class("annonce")

stringAnnonces = []

re_clean_html = re.compile("[\n\s\r\t]+", re.M)
re_clean_url = re.compile("\s+http.*$", re.M)
re_annonce = re.compile("^.*(\d\D+pièces.*€).*$")
re_tel = re.compile("((\d{2}\W*?){4}\d{2})")
for annonce in annonces:
    tweet = ""
    header = annonce.find_class("header-annonce")[0].text_content().encode("utf-8")
    header = re_clean_html.sub(" ", header)
    header = re_annonce.sub(r"\1", header)
    header = header.replace(".", "").replace("Paris ", "")
    tweet += header
    try:
        metro = annonce.find_class("metro")[0].text_content().encode("utf-8")
        tweet += "\nmetro" + re_clean_html.sub(" ", metro)
    except: pass
    try:
        description = annonce.find_class("description")[0].text_content().encode("utf-8")
        tweet += " " + re_tel.search(description.strip()).group(0)
    except: pass
    url = annonce.xpath("div[@class='header-annonce']/a/@href")[0]
    tweet += "\nhttp://www.pap.fr" + url
    stringAnnonces.append(tweet+"\n")

try:
    with open("lastAnnonces.txt") as f:
        for l in f.readlines():
            lastAnnonces.append(l.replace("\t", "\n"))
except:
    lastAnnonces = []

for annonce in stringAnnonces:
    if annonce in lastAnnonces:
        pass
    else:
        print annonce
        title = re_clean_url.sub('', annonce)
        msg = MIMEText(annonce)
        msg['Subject'] = '[PAP] %s' % title
        msg['From'] = 'no-reply@rouxrc-pap.nul'
        msg['To'] = ", ".join(emails)
        s = smtplib.SMTP('localhost')
        s.sendmail(msg['From'], emails, msg.as_string())
        s.quit()
        time.sleep(10)

with open("lastAnnonces.txt","w") as f:
    for string in stringAnnonces :
        f.write(string.replace("\n", "\t")+"\n")
