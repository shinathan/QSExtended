import finnhub

finnhub_client = finnhub.Client(api_key="cilbg7hr01qk0p7aov30cilbg7hr01qk0p7aov3g")
symbols = finnhub_client.stock_symbols("US")
