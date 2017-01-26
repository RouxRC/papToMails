#!/usr/bin/env python
# -*- coding: utf-8 -*-

import lxml.html as html
from cStringIO import StringIO
from gzip import GzipFile
import re, time, sys
import urllib2
import smtplib
from email.mime.text import MIMEText
from config import DEBUG, pap_url, seloger_url, paruvendu_url, emails, admin_emails

lastAnnonces = {}
try:
    with open("lastAnnonces.txt") as f:
        for url in f.readlines():
            lastAnnonces[url.strip('\n')] = 1
except:
    pass

def sendMail(site, title, annonce, url, admin=False):
    title = title.replace("\n", " ")
    msg = MIMEText(annonce + "\n" + url)
    msg['Subject'] = '[%s] %s' % (site, title)
    if DEBUG:
        print >> sys.stderr, "SendMail", msg.as_string(), "\n----\n"
    else:
        s = smtplib.SMTP('localhost')
        s.sendmail('no-reply@rouxrc-pap.nul', admin_emails if admin else emails, msg.as_string())
        s.quit()
        time.sleep(5)

re_clean_html = re.compile("[\n\s\r\t]+", re.M)
re_annonce = re.compile("^.*(\d\D+pièces.*€).*$")
re_metro = re.compile(ur"(?:m[eé]tro|m°)\s+(.*?)\s*(\.|,|et|dans|appart|$)", re.I)
re_clean_lnbrk = re.compile(r"[\n\r\s\t]+")
re_format_paruv = re.compile(r'^(.*) environ - (.*pièces) (.*)$')

# PAP.FR
try:
    doc = html.fromstring(urllib2.urlopen(pap_url, timeout=60).read())
except (urllib2.URLError, ValueError):
    pass
else:
    annonces = doc.find_class("search-results-item")
    for annonce in annonces:
        url = annonce.xpath("div/a[@class='title-item']/@href")[0]
        if not url.startswith("http"):
            url = "http://www.pap.fr" + url
        if url in lastAnnonces:
            continue
        if DEBUG:
            print >> sys.stderr, url
        else:
            lastAnnonces[url] = 1
        text = ""
        header = annonce.find_class("title-item")[0].text_content().encode("utf-8")
        header = re_clean_html.sub(" ", header)
        header = re_annonce.sub(r"\1", header)
        header = header.replace(".", "").replace("Paris ", "")
        text += header
        try:
            metro = annonce.find_class("item-transports")[0].text_content().encode("utf-8")
            text += "\nmétro " + re_clean_html.sub(" ", metro)
        except: pass
        try:
            text += " " + annonce.find_class("item-description")[0].text_content().encode("utf-8").strip()
        except: pass
        sendMail("PAP", text, text, url)

def gunzip(s):
    return GzipFile('', 'r', 0, StringIO(s)).read()

# SELOGER.COM
cururl = seloger_url
opener = urllib2.build_opener()
opener.addheaders = [
    ('Pragma', 'no-cache'),
    ('DNT', '1'),
    ('Accept-Encoding', 'gzip, deflate, sdch'),
    ('Accept-Language', 'fr-FR,fr;q=0.8,en-US;q=0.6,en;q=0.4'),
    ('Upgrade-Insecure-Requests', '1'),
    ('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/53.0.2785.143 Chrome/53.0.2785.143 Safari/537.36'),
    ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'),
    ('Cache-Control', 'no-cache'),
    ('Cookie', 'mailD5=false; ASP.NET_SessionId=eb3ey2wgzcroacfntqwidv2x; __uzma=ma1d4c7379-bc06-46f3-a7de-a1f1ed92b5657477; __uzmb=1485449424; FirstVisitSeLoger=26/01/2017 16:50:24; HistoRecherches=GAEAAHicTcxBasMwEIXhq8ymykYl0thSSEDtFXqDINsTGIgVI8mFgOiheqocIyIi4MXwf28zunzzlLNDUXNfaGAKTsujGNkdjNJKy1ewpWvpW0yLFTmy48CZ/VUEn9f4/oMiDOeFaaTkOtlLA5ThAweR1njxI80cnFXll0KmBNPOL4uPmea6E9xWmAiut0s1dLIelPIFVsH8X7Cg3Su9R6UPoO3JqBP25cdHTqApSmjEx0xvdxv3G5uNbXX51H9PFhNXsg==; dtCookie=|U2VMb2dlcnww; vistId=bae02304-6c08-4225-bc59-01a04c829dbf; mailD5=false; __uzmc=921261961210; __uzmd=1485451735; SearchAnnDep=75; accept_cookies=true; __utma=208557584.2022651579.1485445891.1485445891.1485445891.1; __utmb=208557584.4.10.1485445891; __utmc=208557584; __utmz=208557584.1485445891.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)'),
    ('Connection', 'keep-alive')
]
while cururl:
    doc = html.fromstring(gunzip(opener.open(cururl).read()).decode("utf8"))
    annonces = doc.find_class("listing")
    if not annonces:
        print >> sys.stderr, "WARNING:", "no results found for", cururl, "\n----\n"
        sendMail("SeLoger", "NO RESULTS", "Warning, no results found for:", cururl, admin=True)
        break
    for annonce in annonces:
        url = annonce.xpath("div/div/div/a/@href")[0]
        url = url[:url.find('?')]
        if url in lastAnnonces:
            continue
        if DEBUG:
            print >> sys.stderr, url
        else:
            lastAnnonces[url] = 1
        try:
            taille = annonce.xpath("div/div/div/ul[@class='property_list']/li")[-1].text_content().encode('utf8')
        except:
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
        if not cururl.startswith("http"):
            cururl = "http://www.seloger.com/" + cururl
        time.sleep(5)
    else:
        cururl = ""

# PARUVENDU.FR
try:
    doc = html.parse(paruvendu_url)
except IOError:
    pass
else:
    doc = doc.getroot()
    annonces = doc.find_class("annonce")
    for annonce in annonces:
        url = annonce.xpath("a/@href")[0]
        if not url.startswith("http"):
            url = "http://www.paruvendu.fr" + url
        url = url[:url.find('#')]
        if url in lastAnnonces:
            continue
        if DEBUG:
            print >> sys.stderr, url
        else:
            lastAnnonces[url] = 1
        prix = annonce.xpath("a/span[@class='price2']")[0].text_content().strip().replace(" ", "")
        prix = prix[:prix.find('*')].encode("utf-8")
        title = annonce.xpath("a/span[@class='desc2']/h3")[0].text_content().encode("utf-8")
        title = re_clean_lnbrk.sub(" ", title).replace("Location - ", "")
        title = title.replace("Appartement - ", "").replace("Maison - ", "")
        title = re_format_paruv.sub(r"\2 \1 %s, \3" % prix, title).strip()
        dates = annonce.xpath("a/p")
        date = dates[0].text_content().encode("utf-8") if dates else ""
        desc = re_clean_lnbrk.sub(" ", annonce.xpath("a/span[@class='desc2']")[0].text_content()).encode("utf-8").strip()
        details = re_clean_lnbrk.sub(" ", annonce.xpath("a/span[@class='price2']")[0].text_content()).encode("utf-8").strip()
        desc = "%s\n%s\n%s\n" % (date, desc, details)
        if annonce.xpath("a/span[@class='price2']/p/img/@src")[0] == "http://static.paruvendu.com/immobilier/img/pictos/pic_part.png":
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
