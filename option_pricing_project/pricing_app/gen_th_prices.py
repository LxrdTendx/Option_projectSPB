import numpy as np
import theoretical_prices as tp
import sys
import option_pricing as op
import yaml
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
# from scalene import scalene_profiler
# from numpy.polynomial import Polynomial as P
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


def get_out_strikes(oscfg, sample_strikes):
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
    plt.title("Premium samples vs polynomial function")
    ax.set_xlabel("strike")
    ax.set_ylabel("premium")
    ax.minorticks_on()
    ax.grid(which="major", linewidth=1)
    ax.grid(which="minor", linewidth=1, linestyle=":")
    # рисуем точками сэмплы
    ax.scatter(sample_strikes, bid, label="Bid", color="blue")
    ax.scatter(sample_strikes, ask, label="Ask", color="green")
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
    spot_price = config["spot_price"]
    #
    # блок работы калибровки - берем страйки и премии, выдаём риск-параметры
    #
    # получить страйки для аппроксимации
    (sample_strikes, spa) = get_sample_strikes(config["sample_strikes"])
    # получить премии для аппроксимации
    (prem_type, bid, ask) = get_sample_premium(
        config["sample_premium"], sample_strikes, spa, spot_price, opt_type
    )
    if prem_type == "bidask":
        sample_premium = (bid + ask) / 2
        # w = (1 / (ask - bid)) ** 2
        w = ((ask + bid) / (ask - bid)) ** 2
    else:
        sample_premium = bid
        w = None
    print(f"w {w}")
    # вычисляем центральный страйк аппроксимацией (всегда)
    # r_v1 = tp.CalcR_v1(opt_type, sample_strikes, sample_premium, spot_price)
    r_v2 = tp.CalcR_v2(opt_type, sample_strikes, sample_premium, spot_price)
    # заранее вычисляем страйки для применения параметров
    (out_strikes, ospa) = get_out_strikes(config["out_strikes"], sample_strikes)
    out_premium = get_out_premium(
        config["out_premium"], out_strikes, ospa, spot_price, opt_type
    )
    theors = []
    # вычисляем риск-параметры для всех методов аппроксимации и всех степеней
    for deg in degree:
        for appmode in approx_mode:
            # получаем метод
            approx_fn = tp.GetApproxMethod(appmode)
            # вычисляем полином теорцен по методу
            (_, _, poly, _) = approx_fn(opt_type, sample_strikes, sample_premium, spot_price, r_v2, deg, w)
            # получаем теорцены
            theor = tp.TheorPrice(opt_type, spot_price, out_strikes, r_v2, poly)
            theors.append({"name": f"Degree {deg} Approx {appmode}", "th": theor})
            print(f"Approx {appmode}, degree {deg}, R: {r_v2}, Coef: {poly.coef}, Poly: {poly}")
            # превращаем строки в столбцы и генерируем csv
            save_to_file(config["output"].format(appmode, str(deg)), out_strikes, theor, out_premium)

    draw_samples(
        sample_strikes, bid, ask, out_strikes, theors, out_premium, config["output_png"], config.get("show", False)
    )


if len(sys.argv) < 2:
    print(f"Usage: {sys.argv[0]} config.yaml")
    sys.exit(1)

# scalene_profiler.start()
calc_and_check(sys.argv[1])
# scalene_profiler.stop()
