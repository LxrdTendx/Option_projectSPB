import yaml
import csv
import math

STRIKE_RANGE_RATE = 0.8  # 0.2
OUT_RANGE_RATE = 0.4

# with open("feedos-op1.yml") as f:
with open("Coefs.yaml") as f:
    in_y = yaml.load(f, Loader=yaml.FullLoader)
# root = in_y[0]["fields"]
root = in_y["OptionSeriesPrices"]
spot_price = root["spot_price"]

cnt = 1
for pp in root["group"]:
    if pp["type"] == "Put":
        opt_type = 'p'
    else:
        opt_type = 'c'
    csvll = []
    for k in pp["price"]:
        strike = k["strike"]
        price = (k["buy"] + k["sell"])/2
        if math.fabs((strike - spot_price) / spot_price) < STRIKE_RANGE_RATE:
            # csvll.append([strike, k["buy"], k["sell"]])
            csvll.append([strike, price])

    csvll.sort()

    in_csv_fname = "feedos_" + str(cnt) + ".csv"
    out_csv_fname = "out/feedos_out_" + str(cnt) + "_{}_{}" + ".csv"

    dict_file = {'degree': 2, 'spot_price': spot_price, 'opt_type': opt_type, 'approx_mode': 'linal',
                 'sample_strikes': {'mode': 'file', 'file': in_csv_fname},
                 'sample_premium': {'model': 'strike_file'},
                 'out_strikes': {'mode': 'range_with_cnt', 'min': spot_price * (1 - OUT_RANGE_RATE), 'max': spot_price * (1 + OUT_RANGE_RATE), 'cnt': 20},
                 'out_premium': {'model': 'none'},
                 'output': out_csv_fname, 'output_png': 'out/theor.png', 'show': True}

    with open("config_feed_" + str(cnt) + ".yaml", 'w') as file:
        documents = yaml.dump(dict_file, file)

    with open(in_csv_fname, 'w') as file:
        writer = csv.writer(file)
        writer.writerows(csvll)

    cnt += 1
