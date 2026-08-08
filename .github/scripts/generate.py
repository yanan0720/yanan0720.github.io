#!/usr/bin/env python3
import requests, feedparser, json, os, random, time
from datetime import datetime, timedelta

API_KEY = os.environ.get('DEEPSEEK_API_KEY')
API_URL = "https://api.deepseek.com/v1/chat/completions"

# 按你的兴趣分类的 RSS 源（国内可访问）
RSS_SOURCES = {
    "历史": [
        "http://rss.sina.com.cn/news/history.xml",
        "https://plink.anyfeeder.com/weixin/lishi",
    ],
    "经济": [
        "https://plink.anyfeeder.com/eeo",
        "https://feedx.net/rss/caixin.xml",
    ],
    "文化": [
        "https://plink.anyfeeder.com/weixin/dandureading",
        "http://rss.sina.com.cn/book/all.xml",
    ],
    "女性主义": [
        "https://fnyjlc.wsic.ac.cn/CN/rss_lm_37.xml",
    ],
    "科技/社会": [
        "https://feeds.feedburner.com/TechCrunch/",
        "http://rss.sina.com.cn/tech/all.xml",
    ],
}

# 学习路线图（体系化，按顺序推送）
LEARNING_PATH = [
    # 第一周：女性主义入门
    ("女性主义", "什么是女性主义？三分钟搞懂核心概念"),
    ("女性主义", "父权制到底是什么？不是你想象的那样"),
    ("女性主义", "第一波浪潮：她们如何争取到投票权"),
    ("女性主义", "第二波浪潮：《女性的神话》改变了什么"),
    ("女性主义", "交叉性：为什么黑人女性被忽视"),
    # 第二周：中国历史脉络
    ("历史", "夏商周：中国从哪里开始"),
    ("历史", "春秋战国：百家争鸣的黄金时代"),
    ("历史", "秦始皇：千古一帝的统一密码"),
    ("历史", "唐朝：世界上最开放的国家"),
    ("历史", "宋朝：GDP占全球80%的富庶时代"),
    # 第三周：经济常识
    ("经济", "通货膨胀：钱为什么不值钱了"),
    ("经济", "供需关系：一只看不见的手"),
    ("经济", "GDP：一个国家的财富怎么算"),
    ("经济", "复利：巴菲特滚雪球的秘密"),
    ("经济", "贸易战：各国为什么互相加税"),
]

def fetch_rss_news():
    """抓取各 RSS 源的最新文章"""
    news_items = []
    for category, urls in RSS_SOURCES.items():
        for url in urls:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:3]:
                    news_items.append({
                        "title": entry.get("title", "")[:80],
                        "summary": entry.get("summary", "")[:200].replace("<p>","").replace("</p>",""),
                        "link": entry.get("link", ""),
                        "category": category,
                    })
            except: pass
            time.sleep(0.5)
    return news_items

def call_deepseek(prompt, system_msg="你是一个有趣的知识博主，擅长把复杂知识讲得生动易懂。"):
    """调用 DeepSeek API"""
    resp = requests.post(API_URL, headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }, json={
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.8,
        "max_tokens": 800
    }, timeout=30)
    return resp.json()["choices"][0]["message"]["content"]

def generate_from_news(news_items):
    """从新闻中挑选一条，生成知识点卡片"""
    if not news_items:
        return None
    item = random.choice(news_items[:15])
    prompt = f"""
基于以下新闻素材，写一篇**图文知识点卡片**（纯文字，适合手机阅读）：

标题：{item['title']}
摘要：{item['summary']}

要求：
1. 标题要有吸引力（10-20字，像小红书标题）
2. 正文分3-4段，每段不超过3行
3. 用**加粗**标重点，用通俗语言解释专业概念
4. 结尾加一句"💡 一句话记住：xxx"
5. 标注来源
6. 总字数控制在200-300字
"""
    content = call_deepseek(prompt)
    return {
        "title": item['title'],
        "content": content.replace('\n', '<br>'),
        "category": item['category'],
        "source": "RSS实时资讯",
    }

def generate_from_path():
    """从学习路线图中，按日期推进，生成体系化知识点"""
    path_idx = (datetime.now() - datetime(2026,1,1)).days % len(LEARNING_PATH)
    category, topic = LEARNING_PATH[path_idx]
    prompt = f"""
写一个关于「{topic}」的趣味知识卡片，分类为「{category}」。

要求：
1. 标题吸引人（10-20字，像小红书风格）
2. 正文200-300字，分3-4段
3. 用生动的比喻和例子，让小白也能秒懂
4. 关键概念用**加粗**
5. 结尾加"💡 一句话记住：xxx"
6. 语气轻松有趣，像朋友在跟你聊天

示例风格：
"你有没有想过，为什么古代女人不能上桌吃饭？这背后其实是一套叫'父权制'的系统在运作..."
"""
    content = call_deepseek(prompt)
    return {
        "title": topic,
        "content": content.replace('\n', '<br>'),
        "category": category,
        "source": "每日站·体系课",
    }

def main():
    today = datetime.now().strftime('%Y-%m-%d')
    
    articles = []
    
    # 1. 从学习路线图生成1篇体系化知识点
    try:
        path_article = generate_from_path()
        articles.append(path_article)
    except Exception as e:
        print(f"路径生成失败: {e}")
    
    # 2. 从 RSS 抓取实时新闻，生成1-2篇
    try:
        news = fetch_rss_news()
        for _ in range(2):
            news_article = generate_from_news(news)
            if news_article:
                articles.append(news_article)
    except Exception as e:
        print(f"新闻生成失败: {e}")
    
    # 3. 组装 data.json
    data = {
        "updated_at": datetime.now().strftime('%m月%d日 %H:%M'),
        "date": today,
        "articles": articles
    }
    
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 生成了 {len(articles)} 篇知识点")

if __name__ == "__main__":
    main()
