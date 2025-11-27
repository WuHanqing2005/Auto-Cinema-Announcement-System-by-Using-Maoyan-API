import json
import csv
import random
import requests
import os
from datetime import datetime

# ============================
# 1. 生成 10 个随机 UA (User Agents)
# 每次运行时生成新的 UA 列表，提高随机性
# ============================
def generate_user_agents():
    return [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.%d.0 Safari/537.36" % random.randint(1000, 5000),
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.%d Safari/605.1.15" % random.randint(1, 9),
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:%d.0) Gecko/20100101 Firefox/%d.0" % (random.randint(80, 123), random.randint(80, 123)),
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.%d.0 Safari/537.36" % random.randint(1000, 4000),
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.%d.0 Safari/537.36" % random.randint(1000, 4000),
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.%d Safari/605.1.15" % random.randint(1, 9),
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/119.0.%d.%d Safari/537.36" % (random.randint(0, 9999), random.randint(0, 999)),
        "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.%d Mobile Safari/537.36" % random.randint(2000, 6000),
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.%d" % random.randint(1, 9),
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/121.0.%d.%d Safari/537.36" % (random.randint(0, 9999), random.randint(0, 999))
    ]

USER_AGENTS = generate_user_agents()

# ============================
# 2. 读取 config.json (增强错误处理)
# ============================
def load_config():
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("错误：未找到 config.json 文件。请在程序目录下创建它，并设置 cinemaId。")
        raise
    except json.JSONDecodeError:
        print("错误：config.json 文件格式不正确。")
        raise
    except Exception as e:
        print(f"读取 config.json 时发生未知错误: {e}")
        raise

# ============================
# 3. 请求影院排期接口 (增强错误处理)
# ============================
def fetch_cinema_data(cinema_id):
    url = f"https://m.maoyan.com/ajax/cinemaDetail?cinemaId={cinema_id}"
    
    # 随机选择一个 User-Agent
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        # 参照来源，可以帮助通过某些反爬检查
        "Referer": f"https://m.maoyan.com/cinema/{cinema_id}" 
    }

    print("使用的 User-Agent：", headers["User-Agent"])

    try:
        resp = requests.get(url, headers=headers, timeout=10) # 增加超时设置
        resp.raise_for_status() # 检查 HTTP 状态码是否为 200
        data = resp.json()
        
        if "showData" not in data:
             print("警告：响应 JSON 中缺少 'showData' 字段，可能接口结构已变更。")
             return {}
             
        return data.get("showData", {})
        
    except requests.exceptions.RequestException as e:
        print(f"请求影院数据失败: {e}")
        return {}
    except json.JSONDecodeError:
        print("警告：响应内容不是有效的 JSON 格式。")
        return {}
    except Exception as e:
        print(f"请求过程中发生未知错误: {e}")
        return {}

# ============================
# 4. 将排期写入 filmdata.csv
# ============================
def save_to_csv(cinema_id, movies):
    filename = "filmdata.csv"
    
    # 优化判断是否写入表头
    write_header = not os.path.exists(filename) or os.path.getsize(filename) == 0

    with open(filename, "a", encoding="utf-8", newline="") as csvfile:
        writer = csv.writer(csvfile)

        if write_header:
            writer.writerow([
                "cinema_id", "movie_id", "movie_name",
                "date", "start_time", "hall", "language",
                "version", "price", "seq_no", "crawl_time"
            ])

        crawl_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        record_count = 0
        for movie in movies:
            movie_name = movie.get("nm", "N/A")
            movie_id = movie.get("id", "N/A")

            # 遍历日期分组 (day)
            for day in movie.get("shows", []):
                # !!! 注意: date字段并不在 day 对象中，而是在其子列表 plist 的每个元素中 !!!
                # day.get("dt") 是错误的，应该删除或保留为空。

                # 遍历具体场次 (p)
                for p in day.get("plist", []):
                    # ==== 【核心修改：从场次对象 p 中提取 'dt' 日期字段】 ====
                    date = p.get("dt", "N/A") # 从场次信息 p 中获取日期 'dt'
                    # =======================================================
                    
                    start_time = p.get("tm", "N/A")
                    hall = p.get("th", "N/A")
                    lang = p.get("lang", "N/A")
                    version = p.get("tp", "N/A")
                    price = p.get("discountSellPrice", "N/A")
                    seq_no = p.get("seqNo", "N/A")

                    writer.writerow([
                        cinema_id,
                        movie_id,
                        movie_name,
                        date,  # 现在 date 已经正确获取
                        start_time,
                        hall,
                        lang,
                        version,
                        price,
                        seq_no,
                        crawl_time
                    ])
                    record_count += 1

    print(f"排期写入 CSV 完成！共记录 {record_count} 条场次信息。")

# ============================
# 5. 主流程
# ============================
def main():
    try:
        config = load_config()
        cinema_id = config.get("cinemaId")
        
        if not cinema_id:
            print("错误：config.json 中缺少 'cinemaId' 字段。")
            return

        print(f"开始爬取影院 {cinema_id} 的排期信息...")

        data = fetch_cinema_data(cinema_id)
        movies = data.get("movies", [])
        
        if not movies:
            print("未能获取到任何电影排期信息，程序退出。")
            return

        print(f"共获取到 {len(movies)} 部电影的排期")

        # 传入从 API 响应中获取的 movies 列表进行写入
        save_to_csv(cinema_id, movies)

        print("任务完成！")

    except Exception as e:
        print(f"\n主程序执行失败: {e}")

if __name__ == "__main__":
    main()