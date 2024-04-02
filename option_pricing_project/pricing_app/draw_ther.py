import numpy as np
import theoretical_prices as tp
import sys
import option_pricing as op
import yaml
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
# from scalene import scalene_profiler
from numpy.polynomial import Polynomial as P
# from numpy.polynomial import Hermite as H


def get_sample_strikes(ssconfig):
    spa = None
    ss_mode = ssconfig["mode"]
    if ss_mode == "range_with_step":
        strikes = np.arange(ssconfig["min"], ssconfig["max"], ssconfig["step"])
    elif ss_mode == "range_with_cnt":
        strikes = np.linspace(ssconfig["min"], ssconfig["max"], ssconfig["cnt"])
    elif ss_mode == "file":
        spa = np.genfromtxt(ssconfig["file"], delimiter=",")
        # sort by strikes
        spa = spa[np.argsort(spa[:, 0])]
        strikes = spa[:, 0]
    else:
        print(f"Wrong strikes src {ss_mode}")
        sys.exit(1)
    return (strikes, spa)


def get_sample_premium(spconfig, strikes, spa, spot_price, opt_type):
    model = spconfig["model"]
    if model == "bs":
        print("Input model Black-Sholes")
        premium = op.BlackSholes(opt_type, spot_price, strikes, spconfig["time_in_days"] / 365.0, spconfig["riskless_rate"], spconfig["volat"])
        return ('premium', premium, premium)
    if model == "bach":
        print("Input model Bachelier")
        premium = op.Bachelier(opt_type, spot_price, strikes, spconfig["time_in_days"] / 365.0, spconfig["riskless_rate"], spconfig["volat"] * spot_price)
        return ('premium', premium, premium)
    if model == "strike_file":
        print("Own premium samples")
        if spa is None:
            print("Own model requires strike mode 'file'")
            sys.exit(1)
        (_, cols) = np.shape(spa)
        if cols == 2:
            premium = spa[:, 1]
            return ('premium', premium, premium)
        if cols == 3:
            bid = spa[:, 1]
            ask = spa[:, 2]
            return ('bidask', bid, ask)
    print(f"Wrong input mode {model}")
    sys.exit(1)


def get_spot_prices(oscfg, sample_strikes):
    ospa = None
    mode = oscfg["mode"]
    if mode == "range_with_step":
        strikes = np.arange(oscfg["min"], oscfg["max"], oscfg["step"])
    elif mode == "range_with_cnt":
        strikes = np.linspace(oscfg["min"], oscfg["max"], oscfg["cnt"])
    elif mode == "file":
        ospa = np.genfromtxt(oscfg["file"], delimiter=",")
        # sort by strikes
        ospa = ospa[np.argsort(ospa[:, 0])]
        strikes = ospa[:, 0]
    elif mode == "sample":
        strikes = sample_strikes
    else:
        print(f"Wrong out strikes mode: {mode}")
        sys.exit(1)
    return (strikes, ospa)


def get_out_premium(spconfig, strikes, ospa, spot_price, opt_type):
    model = spconfig["model"]
    if model == "bs":
        print("Output model Black-Sholes")
        premium = op.BlackSholes(opt_type, spot_price, strikes, spconfig["time_in_days"] / 365.0, spconfig["riskless_rate"], spconfig["volat"])
    elif model == "bach":
        print("Output model Bachelier")
        premium = op.Bachelier(opt_type, spot_price, strikes, spconfig["time_in_days"] / 365.0, spconfig["riskless_rate"], spconfig["volat"] * spot_price)
    elif model == "strike_file":
        print("Own premium test strikes")
        if ospa is None:
            print("Own model requires config entry sample_strikes/file ")
            sys.exit(1)
        premium = ospa[:, 1]
    elif model == "none":
        premium = None
    elif model == "as_input":
        print(f"Wrong input mode {model}")
        sys.exit(1)
    else:
        print(f"Wrong input mode {model}")
        sys.exit(1)
    return premium


def save_to_file(filename, strikes, theor, premium):
    if premium is None:
        header = "strikes,theor_price"
        li = (strikes, theor)
    else:
        header = "strikes,theor_price,premium,diff"
        li = (strikes, theor, premium, (theor - premium))
    x = np.transpose(np.array(li))
    np.savetxt(filename, x, fmt="%-5.5f", delimiter=",", header=header)


def draw_samples(
    sample_strikes, bid, ask, test_strikes, theors, test_premium, filename, show_me
):
    fig, ax = plt.subplots(1, 1, figsize=(9, 9))
    plt.title("Zero-strike polynome")
    ax.set_xlabel("strike")
    ax.set_ylabel("premium")
    ax.minorticks_on()
    ax.grid(which="major", linewidth=1)
    ax.grid(which="minor", linewidth=1, linestyle=":")
    # рисуем точками сэмплы
    # ax.scatter(sample_strikes, bid, label="Bid", color="blue")
    # ax.scatter(sample_strikes, ask, label="Ask", color="green")
    if test_premium is not None:
        ax.plot(test_strikes, test_premium, label="Test premium", color="red")
    for th in theors:
        ax.plot(test_strikes, th["th"], label=th["name"])
    ax.xaxis.set_minor_locator(AutoMinorLocator())
    ax.yaxis.set_minor_locator(AutoMinorLocator())
    ax.tick_params(which="major", length=10, width=2)
    ax.tick_params(which="minor", length=5, width=1)
    plt.legend()
    plt.savefig(filename)
    if show_me:
        plt.show()


def calc_and_check(configname):
    with open(configname) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    print(f"config {config}")
    opt_type = config["opt_type"]
    degree = config["degree"]
    if not isinstance(degree, list):
        degree = [degree]
    approx_mode = config['approx_mode']
    if not isinstance(approx_mode, list):
        approx_mode = [approx_mode]
    zero_strike = config["zero_strike"]
    #
    # блок работы калибровки - берем страйки и премии, выдаём риск-параметры
    #
    # получить страйки для аппроксимации
    (sample_strikes, spa) = get_sample_strikes(config["sample_strikes"])
    r_v2 = config["r"]
    # заранее вычисляем страйки для применения параметров
    (spot_prices, ospa) = get_spot_prices(config["spot_prices"], sample_strikes)
    out_premium = get_out_premium(
        config["out_premium"], spot_prices, ospa, zero_strike, opt_type
    )
    theors = []
    # вычисляем риск-параметры для всех методов аппроксимации и всех степеней
    # вычисляем полином теорцен по методу
    # получаем теорцены
    poly = P(config["coefs"])
    deg = poly.degree()
    # theor = tp.TheorPrice(opt_type, spot_price, out_strikes, r_v2, poly)
    theor = tp.TheorPrice(opt_type, spot_prices, zero_strike, r_v2, poly)
    theors.append({"name": f"Poly {poly}, R {r_v2}", "th": theor})
    print(f"degree {deg}, R: {r_v2}, Coef: {poly.coef}, Poly: {poly}")
    print(f"diff {theor - spot_prices}")
    # превращаем строки в столбцы и генерируем csv
    save_to_file(config["output"].format("", str(deg)), spot_prices, theor, out_premium)

    draw_samples(
        sample_strikes, [], [], spot_prices, theors, out_premium, config["output_png"], config.get("show", False)
    )


if len(sys.argv) < 2:
    print(f"Usage: {sys.argv[0]} config.yaml")
    sys.exit(1)

# scalene_profiler.start()
calc_and_check(sys.argv[1])
# scalene_profiler.stop()
