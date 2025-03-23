import okx.MarketData as MarketData
import argparse
import time
import logging
import os
import csv

# 设置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def save_to_csv(data, filename):
    """
    将数据保存到 CSV 文件，按时间升序排序
    """
    os.makedirs(os.path.dirname(filename), exist_ok=True)  # 确保目录存在

    # 按时间戳升序排序（假设时间戳在第一列）
    data.sort(key=lambda x: int(x[0]))  

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["timestamp", "open", "high", "low", "close", "vol", "volCcy", "volCcyQuote", "confirm"])  # 表头
        writer.writerows(data)

    logging.info(f"数据已按时间升序排序并保存到 {filename}")

def fetch_all_candlesticks(marketDataAPI, instId, total_limit, sleep_time=0.1, max_retries=3):
    """
    从 OKX API 获取历史 K 线数据，支持自动翻页。
    """
    all_data = []
    limit_per_request = 100  # 每次请求最多 100 条
    after = None  # 初始请求不指定 after
    request_count = 0
    
    while len(all_data) < total_limit:
        request_count += 1
        fetch_limit = min(limit_per_request, total_limit - len(all_data))
        logging.info(f"请求 {request_count}: {instId}, after={after}, limit={fetch_limit}")

        for retry in range(max_retries):
            try:
                params = {"instId": instId, "limit": str(fetch_limit), "bar": "5m"}
                if after:
                    params["after"] = after
                response = marketDataAPI.get_history_candlesticks(**params)
                if isinstance(response, dict) and "code" in response:
                    if response["code"] != "0":
                        logging.error(f"API 错误: {response.get('msg', '未知错误')}")
                        break
                
                data = response["data"]
                if isinstance(data, list) and len(data) > 0:
                    all_data.extend(data)
                    after = data[-1][0]  # 取最后一条数据的时间戳
                    logging.info(f"成功获取 {len(data)} 条数据，总计 {len(all_data)}/{total_limit}")
                else:
                    logging.warning("API 返回空数据，结束循环")
                    return all_data

                break  # 成功获取数据，跳出重试循环

            except Exception as e:
                logging.error(f"请求失败: {e}")
                if retry < max_retries - 1:
                    sleep_duration = sleep_time * (2 ** retry)
                    logging.warning(f"重试 {retry + 1}/{max_retries}，等待 {sleep_duration} 秒")
                    time.sleep(sleep_duration)
                else:
                    logging.error("重试次数耗尽，终止请求")
                    return all_data

        time.sleep(sleep_time)

    return all_data

def main():
    parser = argparse.ArgumentParser(description="获取 OKX 历史 K 线数据")
    parser.add_argument("instId", type=str, help="交易对，例如 BTC-USD")
    parser.add_argument("--flag", type=str, default="0", help="实盘:0 , 模拟盘：1")
    parser.add_argument("--limit", type=int, default=100000, help="返回数据条数")
    parser.add_argument("--sleep_time", type=float, default=0.1, help="API 请求间隔时间")
    
    args = parser.parse_args()
    
    marketDataAPI = MarketData.MarketAPI(flag=args.flag)
    result = fetch_all_candlesticks(marketDataAPI, args.instId, args.limit, sleep_time=args.sleep_time)
    
    logging.info(f"最终获取 {len(result)} 条数据")
    
    if result:
        output_filename = os.path.join("data", f"{args.instId}_candlesticks.csv")
        save_to_csv(result, output_filename)

if __name__ == "__main__":
    main()
