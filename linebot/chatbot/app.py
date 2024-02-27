from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

import MeCab
import requests
from bs4 import BeautifulSoup


import sqlite3
from contextlib import closing
import collections
from janome.tokenizer import Tokenizer


app = Flask(__name__)

line_bot_api = LineBotApi('xy0BDXaR4wFmR4rPXxV0K5yN76LPfCzvN3BQkCWZVW75EPaLQmEk1sqR18YEeFQoqCKV9zkMcnoua6ayYXAjbB+HGDwd3uudKBopTtuz0e1WWMNhEGPWSxzOPcE/Nnc/TS/+/du3S3vM0HFZovby1gdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('f3bdd970aa8e970bdbe8ac25a1fe6789')

@app.route("/")
def test():
    return "OK"

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    m = MeCab.Tagger()
    given_text=event.message.text
    node = m.parseToNode(given_text)
    while node:
        f = node.feature
        p = f.split(",")[0]
        q = f.split(",")[5]
        konomi = f.split(",")[8]
        
        if p == '感動詞':
            line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=node.surface))
        
        elif p == '動詞':
            if q == '命令形':
                line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='何様だお前'))
            elif q == '連用形-促音便':
                line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='いやだ'))
            elif q == '意志推量形':
                line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='うーん、、、やだ！！'))


        elif konomi == '教え':
            #Historyファイルの保存場所を指定
            history = '/Users/tokai/History'

            with closing(sqlite3.connect(history)) as conn:
                c = conn.cursor()
                sql_statements = "select title LONGVARCHAR from 'urls'"
                all_text = ''
                for row in c.execute(sql_statements):
                      all_text += row[0]
                #print(all_text)


            def common_words(text: str):
                t = Tokenizer()

                # 指定した名詞,固有名詞のみの頻出単語
                c = collections.Counter(token.base_form for token in t.tokenize(text)
                                        if token.part_of_speech.startswith('名詞,固有名詞'))

                search_word = c.most_common()[0]
                return search_word



            search_word = common_words(all_text)[0]
            pages_num = 1 + 1
            print(search_word)

            print(f'【検索ワード】{search_word}')

            # Googleから検索結果ページを取得する
            url = f'https://www.google.co.jp/search?hl=ja&num={pages_num}&q={search_word}'
            request = requests.get(url)

            # Googleのページ解析を行う
            soup = BeautifulSoup(request.text, "html.parser")
            search_site_list = soup.select('div.kCrYT > a')

            # ページ解析と結果の出力
            for rank, site in zip(range(1, pages_num), search_site_list):
                try:
                    site_title = site.select('h3.zBAuLc')[0].text
                except IndexError:
                    site_title = site.select('img')[0]['alt']
                site_url = site['href'].replace('/url?q=', '')

            line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=search_word + "::::" + url))
        
        
        elif p == '名詞':
            search_word = event.message.text
            pages_num = 1 + 1
            print(f'【検索ワード】{search_word}')

            url = f'https://www.google.co.jp/search?hl=ja&num={pages_num}&q={search_word}'
            request = requests.get(url)

            # Googleのページ解析を行う
            soup = BeautifulSoup(request.text, "html.parser")
            search_site_list = soup.select('div.kCrYT > a')

            # ページ解析と結果の出力
            for rank, site in zip(range(1, pages_num), search_site_list):
                try:
                    site_title = site.select('h3.zBAuLc')[0].text
                except IndexError:
                    site_title = site.select('img')[0]['alt']
            site_url = site['href'].replace('/url?q=', '')

            line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=site_title + "::::" + site_url))

        node = node.next
        

if __name__ == "__main__":
    app.run()
