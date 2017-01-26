#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright Josh Rendek 2009 bluescripts.net
# No liability blah blah use at your own risk, etc

import lxml.html as html
import re, time, sys
import urllib2
import smtplib
from email.mime.text import MIMEText
from config import DEBUG, pap_url, seloger_url, paruvendu_url, emails

lastAnnonces = {}
try:
    with open("lastAnnonces.txt") as f:
        for url in f.readlines():
            lastAnnonces[url.strip('\n')] = 1
except:
    pass

def sendMail(site, title, annonce, url):
    title = title.replace("\n", " ")
    msg = MIMEText(annonce + "\n" + url)
    msg['Subject'] = '[%s] %s' % (site, title)
    if DEBUG:
        print >> sys.stderr, "SendMail", msg.as_string(), "\n----\n"
    else:
        s = smtplib.SMTP('localhost')
        s.sendmail('no-reply@rouxrc-pap.nul', emails, msg.as_string())
        s.quit()
        time.sleep(5)

re_clean_html = re.compile("[\n\s\r\t]+", re.M)
re_annonce = re.compile("^.*(\d\D+pièces.*€).*$")
re_tel = re.compile("((\d{2}\W*?){4}\d{2})")
re_metro = re.compile(ur"(?:m[eé]tro|m°)\s+(.*?)\s*(\.|,|et|dans|appart|$)", re.I)
re_clean_lnbrk = re.compile(r"[\n\r\s\t]+")
re_format_paruv = re.compile(r'^(.*) environ - (.*pièces) (.*)$')

# PAP.FR
#doc = html.parse(pap_url)
#doc = doc.getroot()
try:
    doc = html.fromstring(urllib2.urlopen(pap_url, timeout=60).read())
except (urllib2.URLError, ValueError):
    pass
else:
    annonces = doc.find_class("annonce")
    for annonce in annonces:
        url = annonce.xpath("div[@class='header-annonce']/a/@href")[0]
        url = "http://www.pap.fr" + url
        if url in lastAnnonces:
            continue
        if DEBUG:
            print >> sys.stderr, url
        else:
            lastAnnonces[url] = 1
        text = ""
        header = annonce.find_class("header-annonce")[0].text_content().encode("utf-8")
        header = re_clean_html.sub(" ", header)
        header = re_annonce.sub(r"\1", header)
        header = header.replace(".", "").replace("Paris ", "")
        text += header
        try:
            metro = annonce.find_class("metro")[0].text_content().encode("utf-8")
            text += "\nmétro " + re_clean_html.sub(" ", metro)
        except: pass
        try:
            description = annonce.find_class("description")[0].text_content().encode("utf-8")
            text += " " + re_tel.search(description.strip()).group(0)
        except: pass
        sendMail("PAP", text, text, url)

# SELOGER.COM
cururl = seloger_url
while cururl:
    doc = html.fromstring(urllib2.urlopen(cururl).read().decode("utf8"))
    nexturl = doc.find_class("pagination_next")
    if nexturl and nexturl[0].xpath("@href"):
        cururl = "http://www.seloger.com/"+nexturl[0].xpath("@href")[0]
    else:
        cururl = ""
    annonces = doc.find_class("listing")
    for annonce in annonces:
        url = annonce.xpath("div/div/div/a[@class='amount']/@href")[0]
        url = url[:url.find('?')]
        if url in lastAnnonces:
            continue
        if DEBUG:
            print >> sys.stderr, url
        else:
            lastAnnonces[url] = 1
        taille = annonce.xpath("div/div/ul[@class='property_list']/li")[-1].text_content().encode('utf8')
        tel = annonce.xpath("div/div/div[@data-phone]/@data-phone")[0]
        title = annonce.xpath("div/div/h2")[0].text_content().encode("utf-8").replace("Appartement ", "")
        prix = annonce.xpath("div/div/div/a[@class='amount']")[0].text_content()
        prix = prix.encode("utf-8").replace(' ', '').replace(' ', '')
        desc = annonce.xpath("div/div/p[@class='description']")[0].text_content().encode("utf-8").strip()
        title = title.replace("pièces", "pièces %s %s" % (taille, prix))
        text = "%s\n%s\n%s\n" % (title, desc, tel)
        metro = re_metro.findall(desc.decode("utf-8"))
        if "".join([a for a,_ in metro]).strip():
            title += " métro " + " / ".join([a.encode('utf-8') for a,_ in metro if a.strip()])
        sendMail("SeLoger", title, text, url)
    nexturl = doc.find_class("pagination_next")
    if nexturl and nexturl[0].xpath("@href"):
        cururl = nexturl[0].xpath("@href")[0].replace(" ", "%20")
        if not cururl.startswith("http://"):
            cururl = "http://www.seloger.com/"+cururl
    else:
        cururl = ""
    time.sleep(5)

# PARUVENDU.FR
try:
    doc = html.parse(paruvendu_url)
except IOError:
    pass
else:
    doc = doc.getroot()
    annonces = doc.find_class("annonce")
    for annonce in annonces:
        url = "http://www.paruvendu.fr" + annonce.xpath("a/@href")[0]
        if url in lastAnnonces:
            continue
        if DEBUG:
            print >> sys.stderr, url
        else:
            lastAnnonces[url] = 1
        prix = annonce.xpath("a/span[@class='price']")[0].text_content().strip().replace(" ", "")
        prix = prix[:prix.find('*')].encode("utf-8")
        title = annonce.xpath("a/span[@class='desc']/h3")[0].text_content().encode("utf-8")
        title = re_clean_lnbrk.sub(" ", title).replace("Location - ", "")
        title = title.replace("Appartement - ", "").replace("Maison - ", "")
        title = re_format_paruv.sub(r"\2 \1 %s, \3" % prix, title).strip()
        date = annonce.xpath("a/p[@class='date']")[0].text_content().encode("utf-8")
        desc = re_clean_lnbrk.sub(" ", annonce.xpath("a/span[@class='desc']")[0].text_content()).encode("utf-8").strip()
        details = re_clean_lnbrk.sub(" ", annonce.xpath("a/span[@class='price']")[0].text_content()).encode("utf-8").strip()
        desc = "%s\n%s\n%s\n" % (date, desc, details)
        if annonce.xpath("a/span[@class='price']/p/img/@src")[0] == "http://static.paruvendu.com/immobilier/img/pictos/pic_part.png":
            desc += "(particulier)\n"
        metro = re_metro.findall(desc.decode("utf-8"))
        if "".join([a for a,_ in metro]).strip():
            title += " métro " + " / ".join([a.encode('utf-8') for a,_ in metro if a.strip()])
        sendMail("ParuVendu", title, desc, url)


with open("lastAnnonces.txt", "w") as f:
    urls = lastAnnonces.keys()
    urls.sort()
    for url in urls:
        print >> f, url
