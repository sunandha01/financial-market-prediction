// Static educational copy. No forecasts live here; live numbers come from the API.
// Results quoted below are from this project's own walk-forward evaluation (Phases 4-5).

export interface Topic {
  slug: string;
  title: string;
  summary: string;
  body: { heading?: string; text: string }[];
}

export const topics: Topic[] = [
  {
    slug: "return-vs-price",
    title: "Return vs price",
    summary: "Why the forecast is a percentage change, not a price.",
    body: [
      { text: "A price is a level: gold at 4,363, or one euro worth 1.1452 dollars. A return is the change between two prices, written as a percentage: +1% means the price rose by one hundredth of where it started." },
      { text: "Each forecast here is a return, defined as the closing price 7 trading days from now divided by today's closing price, minus 1. Returns put different markets on the same scale, so a 1% move in gold and a 1% move in EUR/USD can be compared directly." },
      { text: "The numbers are small on purpose. Over one week these markets usually move by a few percent at most, so a forecast like +0.126% is a very small nudge, not a big call." },
    ],
  },
  {
    slug: "seven-day-horizon",
    title: "The 7-day horizon",
    summary: "What “7 days ahead” means and why the last days have no answer yet.",
    body: [
      { text: "The horizon is 7 trading days, counted as rows in the price data. Weekends and market holidays are skipped, so 7 trading days is usually about a week and a half on the calendar." },
      { text: "Because the answer for a given day is only known once the price 7 trading days later exists, the most recent 7 sessions have no known outcome. Those days are left out of training and evaluation, but they are exactly the days a live forecast is made for." },
      { text: "We fixed one horizon for every market so results stay comparable. Nothing here says 7 days is the best horizon." },
    ],
  },
  {
    slug: "direction",
    title: "Direction and the naive baselines",
    summary: "Up or down, and the simple guesses a model has to beat.",
    body: [
      { text: "Direction is just the sign of the forecast: up if the predicted return is above zero, down if below, flat if exactly zero. Direction accuracy is the share of days where the predicted sign matched what actually happened. 50% is a coin flip." },
      { heading: "Naive baselines", text: "A forecast only means something if it beats simple guesses. We compare against two: always predict the average return seen in training, and always predict the direction that was most common in training. Gold and silver rose over 2019–2026, so “always up” scores well there without any modelling." },
      { heading: "What we found", text: "GBP/USD is the only market where a model beat both direction baselines, and the margin was small and measured on one period of history. No model in any market beat the average-return baseline on error size. Read every forecast with that in mind." },
    ],
  },
  {
    slug: "the-five-markets",
    title: "The five markets",
    summary: "FX pairs versus gold and silver futures.",
    body: [
      { heading: "Currency pairs", text: "USD/INR (INR=X, rupees per dollar), EUR/USD (EURUSD=X, dollars per euro) and GBP/USD (GBPUSD=X, dollars per pound) are foreign-exchange rates. Trading volume in FX data is indicative at best and often empty, so it is not used as a real measure of activity." },
      { heading: "Gold and silver are futures", text: "Gold (GC=F) and silver (SI=F) are COMEX futures contracts from Yahoo Finance, priced in US dollars per troy ounce. They are not MCX spot prices, so they will not match the rate at an Indian jeweller or on MCX. Futures series can also shift when the underlying contract rolls to the next month." },
      { text: "All prices come from Yahoo Finance daily data and may contain errors or delays." },
    ],
  },
  {
    slug: "indicators",
    title: "Indicators the models see",
    summary: "RSI, MACD, moving averages, Bollinger Bands and ATR in one paragraph each.",
    body: [
      { heading: "RSI (14)", text: "The Relative Strength Index compares recent gains with recent losses over 14 days and scales the result from 0 to 100. Readings above about 70 are often called overbought and below about 30 oversold. That is a description of recent momentum, not a promise that the price will reverse." },
      { heading: "MACD (12/26/9)", text: "MACD is the gap between a fast (12-day) and a slow (26-day) exponential moving average. A 9-day average of that gap is the signal line, and the difference between the two is the histogram. It shows whether momentum is strengthening or fading." },
      { heading: "Moving averages", text: "A simple moving average (5, 10, 20, 50 days) is the average of the last N closes; an exponential one (9, 21 days) gives recent days more weight. How far today's price sits above or below them is a rough description of the current trend." },
      { heading: "Bollinger Bands (20, 2)", text: "The bands sit two standard deviations above and below the 20-day average. Their width measures how volatile the market has been, and %B says where today's price sits inside them." },
      { heading: "ATR (14)", text: "Average True Range is the typical daily price movement over 14 days, including gaps between days. It is a volatility measure in price units." },
      { text: "These are inputs to the models, not signals to trade on. None of them predicts the future on its own." },
    ],
  },
  {
    slug: "walk-forward",
    title: "Walk-forward validation",
    summary: "Why the rows are never shuffled.",
    body: [
      { text: "If you shuffle days before splitting them into training and test sets, the model is trained on days that come after some of its test days. It has effectively seen the future, and the score looks better than it would ever be in real use." },
      { text: "Walk-forward validation avoids that. We split history into 5 folds in time order: train on an earlier stretch, test on the stretch right after it, then move forward and repeat. The test window is always later than the training window." },
      { text: "We also leave a 7-day gap between the two. A training day's answer looks 7 days ahead, so without the gap the last training answers would overlap with the start of the test period. Features for a given day use only data from that day or earlier." },
    ],
  },
  {
    slug: "mae-vs-direction",
    title: "MAE vs direction accuracy",
    summary: "Two different ways to score a forecast.",
    body: [
      { heading: "Error size", text: "MAE (mean absolute error) is the average size of the miss, in return terms: an MAE of 0.03 means the forecast was off by about 3 percentage points on average. RMSE is similar but punishes big misses more." },
      { heading: "Direction accuracy", text: "This ignores size and only asks whether the sign was right. A model can have a small average error yet be wrong about direction half the time, or get direction right while missing the size badly." },
      { heading: "Why baselines matter", text: "Seven-day returns are mostly noise, so simply predicting the average return is a hard error bar to clear. In this project none of the 25 model-and-market combinations beat that baseline on RMSE. Scores that look modest on their own can still be worse than doing nothing clever." },
    ],
  },
  {
    slug: "disclaimer",
    title: "Disclaimer",
    summary: "This is an experiment, not advice.",
    body: [
      { text: "This site is an experimental academic project. The forecasts are outputs of simple machine-learning models and are often wrong, sometimes by a lot." },
      { text: "Nothing here is investment, financial, tax or legal advice, and nothing is a recommendation to buy or sell anything. Do not make trading or money decisions based on these numbers. No profit or accuracy is promised or implied." },
      { text: "Data comes from Yahoo Finance and may be delayed or incorrect. Gold and silver are COMEX futures, not MCX spot prices. Past results, including any evaluation figures shown here, do not indicate future results." },
    ],
  },
];
