;; Financial Knowledge Base in MeTTa
;; This file contains financial rules, facts, and relationships

;; Economic Effect Rules
;; Format: (<- (effect-of CAUSE) EFFECT)

;; Inflation Effects
(<- (effect-of inflation-increase) (high-interest-rates))
(<- (effect-of inflation-increase) (decreased-purchasing-power))
(<- (effect-of inflation-increase) (higher-commodity-prices))
(<- (effect-of inflation-decrease) (low-interest-rates))

;; Interest Rate Effects
(<- (effect-of high-interest-rates) (low-borrowing))
(<- (effect-of high-interest-rates) (high-savings-returns))
(<- (effect-of high-interest-rates) (stock-market-decline))
(<- (effect-of low-interest-rates) (high-borrowing))
(<- (effect-of low-interest-rates) (low-savings-returns))
(<- (effect-of low-interest-rates) (stock-market-growth))

;; Market Condition Effects
(<- (effect-of recession) (high-unemployment))
(<- (effect-of recession) (reduced-consumer-spending))
(<- (effect-of recession) (low-interest-rates))
(<- (effect-of economic-growth) (low-unemployment))
(<- (effect-of economic-growth) (increased-consumer-spending))
(<- (effect-of economic-growth) (gradually-rising-interest-rates))

;; Asset Relationships
(<- (asset-type stocks) (high-risk))
(<- (asset-type stocks) (high-potential-return))
(<- (asset-type stocks) (high-volatility))
(<- (asset-type bonds) (medium-risk))
(<- (asset-type bonds) (medium-potential-return))
(<- (asset-type bonds) (medium-volatility))
(<- (asset-type treasury-bills) (low-risk))
(<- (asset-type treasury-bills) (low-potential-return))
(<- (asset-type treasury-bills) (low-volatility))
(<- (asset-type real-estate) (medium-risk))
(<- (asset-type real-estate) (medium-potential-return))
(<- (asset-type real-estate) (low-volatility))
(<- (asset-type cryptocurrency) (very-high-risk))
(<- (asset-type cryptocurrency) (very-high-potential-return))
(<- (asset-type cryptocurrency) (extreme-volatility))

;; Investment Advice Rules
(<- (suitable-for conservative-investor) (low-risk))
(<- (suitable-for moderate-investor) (medium-risk))
(<- (suitable-for aggressive-investor) (high-risk))

;; Investment Timeframe Rules
(<- (suitable-for short-term) (low-volatility))
(<- (suitable-for medium-term) (medium-volatility))
(<- (suitable-for long-term) (high-volatility))

;; Financial Concept Definitions
(<- (definition assets) "Things of value that you own or control, which provide future economic benefits")
(<- (definition liabilities) "Financial obligations or debts that you owe to others")
(<- (definition equity) "The value of an asset minus any liabilities associated with it")
(<- (definition market-capitalization) "The total dollar value of a company's outstanding shares")
(<- (definition pe-ratio) "Price-to-earnings ratio; measures a company's current share price relative to its earnings per share")
(<- (definition inflation) "The rate at which the general level of prices for goods and services rises, eroding purchasing power")
(<- (definition interest-rate) "The amount a lender charges a borrower for the use of an asset, expressed as a percentage")
(<- (definition recession) "A significant decline in economic activity that lasts more than a few months")
(<- (definition diversification) "A risk management strategy that mixes a variety of investments within a portfolio")
(<- (definition compound-interest) "Interest calculated on the initial principal and accumulated interest over time")

;; Stock vs Crypto Relationships
(<- (property-of stocks) (regulated))
(<- (property-of stocks) (trading-hours-limited))
(<- (property-of stocks) (represents-company-ownership))
(<- (property-of stocks) (may-pay-dividends))
(<- (property-of stocks) (value-from-company-performance))
(<- (property-of crypto) (mostly-unregulated))
(<- (property-of crypto) (trading-24-7))
(<- (property-of crypto) (represents-digital-assets))
(<- (property-of crypto) (rarely-pays-dividends))
(<- (property-of crypto) (value-from-adoption-and-speculation))

;; Transitive Inference Rules
;; If A causes B and B causes C, then A causes C
(<- (causes ?X ?Z) (and (effect-of ?X ?Y) (effect-of ?Y ?Z)))

;; If an asset has property X and property X is suitable for investor Y, 
;; then the asset is suitable for investor Y
(<- (suitable-asset-for ?investor ?asset) 
    (and (asset-type ?asset ?property)
         (suitable-for ?investor ?property)))

;; Economic Scenario Rules
(<- (scenario recession-response)
    (and (effect-of recession low-interest-rates)
         (effect-of low-interest-rates high-borrowing)
         (effect-of high-borrowing increased-investment)))

;; Market Timing Rules
(<- (market-timing buy stocks) (and (market-condition bear) (investor-horizon long-term)))
(<- (market-timing sell stocks) (and (market-condition bubble) (investor-horizon short-term)))
(<- (market-timing buy bonds) (and (market-condition rising-interest-rates) (investor-horizon medium-term)))
(<- (market-timing sell bonds) (and (market-condition falling-interest-rates) (investor-horizon short-term))) 