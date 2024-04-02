""" модуль работы с теорценами.
содержит три базовые функции: CalcR_v2 и семейство CalcTeorParams* для получения параметров из списка цен
и TheorPrice для вычисления теорцены по параметрам, страйку и цене БА

Риск-параметры состоят из числа R и полинома Poly.

Порядок работы:
    * Если получаем на входе bid/ask, то используем GetWeightByBidAsk для получения премий и весов. Мидпоинты нужны для вычисления R и полинома, а веса для полинома
    * Вызываем CalcR_v2 для вычисления R
    * Вызываем CalcTheorParams* для получения полинома
        * Актуальная функция CalcTheorParams3
        * Остальные функции оставлены для совместимости
    * Если нужен полином Эрмита, то можно получить с помощью Poly2Hermit из обычного полинома. Смысла еще раз вызывать МНК нет.
    * По полученным параметрам теорцена вычисляется с помощью TheorPrice

Функции TheorPrice можно передавать и один страйк и массив страйков
"""
import math
import numpy as np
from numpy.polynomial import Polynomial as P
# from numpy.polynomial import Hermite as H
import numpy.linalg as LA
import scipy
from . import option_pricing as op

DEFAULT_DEGREE = 5


def CalcR_v1(opt_type, strikes, premium, spot_price):
    """Deprecated. получить интерполяцией премию центрального страйка"""
    return math.sqrt(2 * math.pi) * np.interp(spot_price, strikes, premium)


def FindClosestStrikes(strikes, premium, spot_price):
    """Найти страйки, ближайшие к центральному в массиве страйков и вернуть 2D массив со страйками и премиями
    В массиве ноль, одна или две строки. В каждой строке страйк и премия
    Функция может вернуть одну или две строки:
    - Если есть страйк, соответствующий центральному, то возвращаем его
    - Если точного совпадения нет, то возвращаем по ближайшему снизу и сверху
    - Если центральныый страйк находится вне диапазона страйков, то возвращаем одну строку
    - Если список страйков пустой, то возвращаем ноль строк
    """
    prev_sp = None
    has_prev_val = False
    for sp in zip(strikes, premium):
        sp = np.array(sp)
        if sp[0] == spot_price:
            return np.array([sp])  # [ ... spot, ...]
        if sp[0] > spot_price:
            if has_prev_val:
                return np.array([prev_sp, sp])  # [ ...spot-x0, spot+x1, ...]
            return np.array([sp])  # [ spot+x1, ...]
        has_prev_val = True
        prev_sp = sp
    if has_prev_val:
        return np.array([prev_sp])  # [ ..., spot-x0]
    return np.array([])


def SolveRByPremium(opt_type, strike, premium, spot_price):
    ''' Подбор R методом Ньютона из strike/premium/spot_price'''
    # Подбираем R методом Ньютона так, чтобы из страйка вычислялась заданная теорцена
    # В качестве полинома используем константу 1
    # Чтобы не дублировать функции используем TheorPrice с соответствующим полиномом
    # В качестве начального значения R берем spot_price
    return scipy.optimize.newton(
        (lambda R: TheorPrice(opt_type, spot_price, strike, R, (lambda x: 1)) - premium), spot_price
    )


def CalcR_v2(opt_type, strikes, premium, spot_price):
    ''' Вычисляем R из массива страйков, массива премий и цены БА'''
    # во второй версии вместо интерполяции премии для ЦС вычисляем R для ближних страйков и интерполируем для ЦС
    # выбираем страйки и премии, ближайшие к центральному
    sps = FindClosestStrikes(strikes, premium, spot_price)
    # для всех (одного-двух) ближних страйков вычисляем R
    Rs = [SolveRByPremium(opt_type, s, p, spot_price) for (s, p) in sps]
    print("Rs:", Rs)

    # линейно интерполируем значение для центрального страйка из ближних
    return np.interp(spot_price, sps[:, 0], Rs)


def CalcTheorParams2(
    opt_type,
    strikes,
    premium,
    spot_price,
    r,
    degree=DEFAULT_DEGREE,
    w=None,
):
    """Получение полинома из отдельных массивов страйков и премий полиномом (b0, b1 ... bn)
       Базовая версия - вызывает fit и получает полином
    """

    xs = (strikes - spot_price) / r
    if opt_type == "c":
        z = 1 - op.N(xs)
    else:
        z = -op.N(xs)
    ys = (premium / r + xs * z) / op.n(xs)
    poly = P.fit(
        xs, ys, degree, w=w, domain=[]
    )  # не выкидывать domain, без него возникают масштабы
    return (xs, ys, poly, r)


def CalcTheorParams3(
    opt_type,
    strikes,
    premium,
    spot_price,
    r,
    degree=DEFAULT_DEGREE,
    w=None,
):
    """Получение полинома из отдельных массивов страйков и премий полиномом (b0, b1 ... bn)
       Актуальная версия: избегает деления на op.n()
    """
    # проверка по размерности. допустим, что страйки и премии - это массивы длины N
    xs = (strikes - spot_price) / r  # N
    z = -op.N(xs)  # N
    if opt_type == "c":
        z += 1  # N
    bs = premium / r + xs * z  # N
    aos = np.vander(xs, N=degree+1, increasing=True)  # N*M M=degree+1
    aos *= op.n(xs).reshape(len(xs), 1)  # aos N*M, правая часть N*1  reshape нужен для правильного broadcast: каждой строке свой nd(xs[i]), один на строку
    if w is not None:
        # https://stackoverflow.com/questions/27128688/how-to-use-least-squares-with-weight-matrix
        wm = np.sqrt(np.diag(w))  # N*N
        aos = np.dot(wm, aos)  # N*M
        bs = np.dot(bs, wm)  # N
    res = LA.lstsq(aos, bs, rcond=None)  # aos N*M, bs 1*N
    poly = P(res[0])
    return (aos, bs, poly, r)


def CalcTheorParams2Degree(
    opt_type,
    strikes,
    premium,
    spot_price,
    r,
    degree=DEFAULT_DEGREE,
    w=None,
):
    """Получение полинома из отдельных массивов страйков и премий полиномом (1, b1 ... bn)
       Эта версия принудительно cnfdbn b0 в единицу.
    """
    xs = (strikes - spot_price) / r
    if opt_type == "c":
        z = 1 - op.N(xs)
    else:
        z = -op.N(xs)
    ys = (premium / r + xs * z) / op.n(xs)
    # хак для того чтобы коэф poly.coef[0] был равен единице
    # + вычитаем единицу из ys
    # + указываем вектор степеней без нулевой
    # + после подбора прописываем в нулевой коэф единицу
    # + возвращаем оригинальный ys
    poly = P.fit(
        xs, ys - 1, list(range(1, degree + 1)), w=w, domain=[]
    )  # не выкидывать domain, без него возникают масштабы
    poly.coef[0] = 1
    return (xs, ys, poly, r)


def CalcTheorParams2DegreeH2(
    opt_type,
    strikes,
    premium,
    spot_price,
    r,
    degree=DEFAULT_DEGREE,
    w=None,
):
    """Deprecated. Получение полинома из отдельных массивов страйков и премий полиномом Эрмита (1, b1 ... bn)"""
    (xs, ys, poly, r) = CalcTheorParams2Degree(opt_type, strikes, premium, spot_price, r, degree, w)
    hpoly = poly.convert(kind=np.polynomial.hermite.Hermite)  # domain=[],
    return (xs, ys, hpoly, r)


def Poly2Hermit(poly):
    return poly.convert(kind=np.polynomial.hermite.Hermite)


def CalcTheorParams(
    opt_type, spa, spot_price, r, fun, degree=DEFAULT_DEGREE, w=None
):
    """получение полинома из массива N*2 (в каждой строке страйк и премия) методом fun"""
    return fun(
        opt_type, spa[:, 0], spa[:, 1], spot_price, r, degree, w
    )


def GetWeightByBidAsk(bid, ask):
    ''' возвращает вектора премий и весов (mid, w)'''
    mid = (bid + ask) / 2
    w = ((ask + bid) / (ask - bid)) ** 2
    return (mid, w)


def CalcTheorParamsBidAsk(
    opt_type, spa, spot_price, r, fun, degree=DEFAULT_DEGREE, w=None
):
    """получение полинома из массива N*3 (в каждой строке страйк, бид и аск премии)"""
    bid = spa[:, 1]
    ask = spa[:, 2]
    mid = (bid + ask) / 2
    if w is None:
        w = ((ask + bid) / (ask - bid)) ** 2
    return fun(
        opt_type, spa[:, 0], mid, spot_price, r, degree, w
    )


def TheorPrice(opt_type, spot_price, strike, r, poly):
    """вычисление теорцены из параметров
    в strike можно передавать и число и массив"""
    moneyless = strike - spot_price
    x = moneyless / r
    return r * op.n(x) * poly(x) + moneyless * (op.N(x) - (1 if opt_type == "c" else 0))


approx_dict = {'poly': CalcTheorParams2, 'poly1': CalcTheorParams2Degree, 'hermit': CalcTheorParams2DegreeH2, 'linal': CalcTheorParams3}


def GetApproxMethod(name):
    return approx_dict[name]
