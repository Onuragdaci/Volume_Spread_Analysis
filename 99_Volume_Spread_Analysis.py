import pandas as pd
import pandas_ta as ta
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
import mplcyberpunk
import mplfinance as mpf
from tvDatafeed import TvDatafeed, Interval
import ssl
from urllib import request
tv = TvDatafeed()

def Hisse_Temel_Veriler():
    url1="https://www.isyatirim.com.tr/tr-tr/analiz/hisse/Sayfalar/Temel-Degerler-Ve-Oranlar.aspx#page-1"
    context = ssl._create_unverified_context()
    response = request.urlopen(url1, context=context)
    url1 = response.read()
    df = pd.read_html(url1,decimal=',', thousands='.')                         #Tüm Hisselerin Tablolarını Aktar
    df=df[6]
    Hisseler=df['Kod'].values.tolist()
    return Hisseler


def vsa_indicator(data, length):
    df = data.copy()
    df['Atr'] = ta.atr(df['High'], df['Low'], df['Close'], length)
    df['Volume_Median'] = ta.median(df['Volume'],length)
    df['Normalized_Range'] = (df['High'] - df['Low']) / df['Atr']
    df['Range_Deviation'] = ((df['Close'] - df['Open'])/df['Close'])* 100
    df['Normalized_Volume'] = df['Volume'] / df['Volume_Median']
    df = df.reset_index()
    for i in range(length * 2, len(df)):
        window = df.iloc[i - length + 1: i + 1]
        slope, intercept, r_val, _, _ = stats.linregress(window['Normalized_Volume'], window['Normalized_Range'])

        if slope <= 0.0 or r_val < 0.2:
            df.loc[i, 'Deviation'] = 0.0
            continue

        pred_range = intercept + slope * df.loc[i, 'Normalized_Volume']
        df.loc[i, 'Deviation'] = df.loc[i, 'Normalized_Range'] - pred_range
    return df

def Plot_Candle(Hisse,data):
    plt.close()
    data.reset_index(drop=True, inplace=True)
    Extremes = data[data['Extremes']==1].index.tolist()
    data.set_index('datetime', inplace=True)
    with plt.style.context('cyberpunk'):
        fig, axs = plt.subplots(4, sharex=True, height_ratios=[6, 1, 1, 1])
        fig.suptitle(Hisse+' Hacim Yayılma Analizi',style='italic',fontsize=16,fontweight="bold")
        mco = [None] * len(data)
        add1 = mpf.make_addplot(data['Extremes'], ax=axs[2], title='Volume Spread')
        add2 = mpf.make_addplot(data['Range_Deviation'], ax=axs[3], title='Range Deviation')
        axs[1].set_title('Volume')
        if Extremes:
            for i in range(0,len(Extremes)):
                mco[Extremes[i]] = 'orange'

        mpf.plot(data, volume=axs[1], type='candle', style='charles', ax=axs[0], addplot=[add1,add2], marketcolor_overrides=mco, mco_faceonly=False)
    plt.gcf().set_size_inches(16, 9)  # Set the figure size
    plt.savefig(Hisse+' Hacim Yayılma Analizi.png', format='png', dpi=300)

Hisseler=Hisse_Temel_Veriler()

for j in range(0, len(Hisseler)):
    print(Hisseler[j])
    try:
        data = tv.get_hist(symbol=Hisseler[i],exchange='BIST',interval=Interval.in_1_hour,n_bars=1000)
        data.rename(columns = {'open':'Open', 'high':'High','low':'Low','close':'Close','volume':'Volume'}, inplace = True)
        data= vsa_indicator(data, 90)
        data['Extremes'] = np.where(
            ((data['Deviation'] < -0.90) | (data['Deviation'] > 0.90)) & 
            ((data['Range_Deviation'] >= -1.0) & (data['Range_Deviation'] <= 1.0)) &
            (data['Volume'].notna()),
            1,
            0
        )
        data = data.tail(45).copy()
        extreme_exists = (data['Extremes'] == 1).any()
        if extreme_exists==True:
            Plot_Candle(Hisseler[j],data)
    except:
        pass





