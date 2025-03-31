"""
Google Gemini client for generating detailed financial information
"""

import logging
import json
import google.generativeai as genai
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class GeminiClient:
    """
    Client for Google Gemini API to generate detailed information about financial topics
    """
    
    def __init__(self, api_key: str = "AIzaSyB2AxPp-LvbaeOue7qnC_p9nCLWdAvU3Kw"):
        """
        Initialize the Gemini client
        
        Args:
            api_key: Google Gemini API key
        """
        self.api_key = api_key
        self.model_name = "gemini-1.5-flash"  # Using the more efficient model
        self.logger = logging.getLogger(__name__)
        
        # Configure the Gemini API
        try:
            genai.configure(api_key=self.api_key)
            self.logger.info("Successfully configured Gemini API")
        except Exception as e:
            self.logger.error(f"Error configuring Gemini API: {str(e)}")
    
    def generate_response(self, prompt: str, max_tokens: int = 2048) -> str:
        """
        Generate a response using Google Gemini
        
        Args:
            prompt: The prompt to send to the model
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            Generated text response
        """
        # Log the prompt for debugging
        self.logger.info(f"Generate response called with prompt: {prompt[:100]}...")
        
        # Check for crypto trading related queries first
        if any(term in prompt.lower() for term in ["crypto trading", "futures trading", "p2p trading", "spot trading", "margin trading", "derivatives trading"]):
            self.logger.info("Using crypto trading fallback response directly")
            return self._fallback_crypto_trading_response()

        try:
            # Create a generative model
            self.logger.info(f"Creating Gemini model {self.model_name}...")
            model = genai.GenerativeModel(self.model_name)
            
            # Generate content
            self.logger.info("Generating content with Gemini API...")
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    top_k=40,
                    top_p=0.95,
                    max_output_tokens=max_tokens,
                )
            )
            
            # Extract the response text
            if response and hasattr(response, 'text'):
                self.logger.info(f"Received Gemini response, length: {len(response.text)}")
                return response.text
            
            self.logger.warning("Received empty or invalid response from Gemini")
            return "I couldn't generate a response at this time."
        
        except Exception as e:
            self.logger.error(f"Error generating Gemini response: {str(e)}")
            
            # Provide fallback responses based on query type
            if any(term in prompt.lower() for term in ["crypto trading", "futures", "p2p", "futures trading", "spot trading", "margin", "derivatives"]):
                self.logger.info("Using crypto trading fallback response after error")
                return self._fallback_crypto_trading_response()
            elif "home loan" in prompt.lower():
                self.logger.info("Using home loan fallback response after error")
                return self._fallback_home_loan_response()
            elif "tax" in prompt.lower():
                self.logger.info("Using tax fallback response after error")
                return self._fallback_tax_response()
            
            return "I encountered an error while generating detailed information. Please try again later."
    
    def _fallback_home_loan_response(self) -> str:
        """Provide a fallback response for home loan queries when API fails"""
        return """
Home loans in India, also known as housing loans or mortgage loans, are financial products offered by banks and housing finance companies (HFCs) that allow individuals to purchase or construct residential properties.

Key features of home loans in India:

1. Interest Rates:
   - Current range: 8.35% to 9.75% per annum (varies by lender)
   - Types: Fixed, floating, and hybrid rates
   - SBI, HDFC, ICICI, LIC Housing Finance are major providers

2. Loan Amount:
   - Up to 80-90% of the property value (Loan-to-Value ratio)
   - Maximum limits vary based on city, property type, and borrower profile

3. Tenure:
   - Generally 5-30 years
   - Maximum age at loan maturity typically 70-75 years

4. Tax Benefits:
   - Section 24: Interest deduction up to Rs.2 lakhs annually
   - Section 80C: Principal repayment deduction up to Rs.1.5 lakhs
   - Section 80EEA: Additional interest deduction for first-time buyers

5. Documentation Required:
   - Identity and address proof
   - Income documents (salary slips, ITR, Form 16)
   - Property documents
   - Bank statements

6. Process Flow:
   - Application submission
   - Document verification
   - Property legal and technical assessment
   - Loan approval and disbursement

7. Additional Charges:
   - Processing fee: 0.5-1% of loan amount
   - Legal and technical fees
   - Prepayment/foreclosure charges (usually none for floating rate loans)

8. Recent Trends:
   - Digital application processes with minimal paperwork
   - Pre-approved loans for existing customers
   - Special rates for women borrowers and government employees

When considering a home loan, compare offerings from multiple lenders, check for hidden charges, and carefully assess your repayment capacity before committing.
"""
    
    def _fallback_tax_response(self) -> str:
        """Provide a fallback response for tax queries when API fails"""
        return """
India's tax system has two regimes that taxpayers can choose from:

1. Old Tax Regime:
   - Tax slabs (FY 2023-24):
     * Up to Rs.2.5 lakhs: Nil
     * Rs.2.5-5 lakhs: 5%
     * Rs.5-10 lakhs: 20%
     * Above Rs.10 lakhs: 30%
   - Allows for various deductions and exemptions under:
     * Section 80C (up to Rs.1.5 lakhs): PPF, ELSS, insurance premiums
     * Section 80D (up to Rs.25,000): Health insurance premiums
     * Section 24 (up to Rs.2 lakhs): Interest on home loans
     * HRA, LTA, and other exemptions are available

2. New Tax Regime (default from FY 2023-24):
   - Tax slabs:
     * Up to Rs.3 lakhs: Nil
     * Rs.3-6 lakhs: 5%
     * Rs.6-9 lakhs: 10%
     * Rs.9-12 lakhs: 15%
     * Rs.12-15 lakhs: 20%
     * Above Rs.15 lakhs: 30%
   - Standard deduction of Rs.50,000
   - Limited exemptions and deductions

3. Capital Gains Tax:
   - Short-term (held < 3 years for most assets): Taxed at income tax slab rates
   - Long-term (held > 3 years):
     * For real estate: 20% with indexation
     * For listed equity/equity mutual funds: 10% above Rs.1 lakh

4. Filing Process:
   - Due date for individuals: July 31st (generally)
   - Online filing through the Income Tax Department website
   - Forms vary based on income sources (ITR-1, ITR-2, etc.)

5. TDS (Tax Deducted at Source):
   - Deducted at source from various payments
   - Rates vary by payment type (salary, interest, rent, professional fees)

6. GST (Goods and Services Tax):
   - Indirect tax with rates of 0%, 5%, 12%, 18%, and 28%
   - Applicable on supply of goods and services
   - Registration required above Rs.20 lakhs turnover (Rs.10 lakhs in some states)

Recent Changes:
- Standard deduction increased to Rs.50,000 under new tax regime
- No tax liability up to Rs.7 lakhs income in the new regime
- Highest surcharge rate reduced from 37% to 25%

To optimize tax liability, choose the appropriate regime based on your income and investment pattern, and utilize available deductions strategically.
"""
    
    def _fallback_crypto_trading_response(self) -> str:
        """Provide a fallback response for crypto trading queries when API fails"""
        return """
Cryptocurrency trading offers various methods to buy, sell and exchange digital assets. Here's a comprehensive overview of the main types of crypto trading:

1. Spot Trading:
   - The most basic form where you buy/sell cryptocurrencies at current market prices
   - Full ownership of assets with no leverage
   - Best for beginners and those who want to accumulate crypto for long-term holding
   - Popular platforms: Binance, Coinbase, Kraken

2. Futures Trading:
   - Contract-based trading that speculates on future crypto prices without owning the underlying asset
   - Features:
     * Leverage: Typically 2x to 125x depending on the exchange
     * Settlement types: USDT-margined (settled in USDT) or coin-margined (settled in the base crypto)
     * Contract types: Perpetual (no expiry) or quarterly contracts
   - Higher risk due to potential liquidation if market moves against position
   - Popular platforms: Binance Futures, Bybit, OKX, dYdX

3. Margin Trading:
   - Borrowing funds from exchange to amplify trading positions
   - Typically offers 2x to 10x leverage
   - Incurs interest on borrowed funds
   - Available on platforms like Binance, Kraken, and KuCoin

4. P2P (Peer-to-Peer) Trading:
   - Direct trading between users without exchange intermediation for order matching
   - Features:
     * Multiple payment methods (bank transfers, mobile payments, cash)
     * Escrow services for security
     * Various currencies supported
     * Self-set prices (premium or discount to market)
   - Often used in regions with limited banking access or crypto regulations
   - Popular platforms: Binance P2P, LocalBitcoins, Paxful

5. Options Trading:
   - Contracts giving the right (not obligation) to buy/sell crypto at predetermined price
   - American options (exercise anytime) vs European options (exercise at expiry only)
   - Complex strategies like straddles, strangles, and spreads available
   - Available on Deribit, Binance, OKX

6. Perpetual Swaps:
   - Most popular derivative product in crypto
   - Futures contracts with no expiry date
   - Funding rate mechanism keeps prices aligned with spot market
   - Available on most major derivatives exchanges

7. Grid Trading:
   - Automated strategy placing buy/sell orders at regular price intervals
   - Works well in sideways/ranging markets
   - Accumulates profits from price volatility without predicting direction
   - Available as bots on platforms like Pionex, 3Commas, or exchange-native tools

8. DeFi Trading:
   - Trading on decentralized exchanges (DEXs) using smart contracts
   - Includes spot trading (Uniswap, PancakeSwap) and derivatives (GMX, dYdX)
   - Non-custodial (you control your keys)
   - Higher gas fees but no KYC requirements

Risk Management Considerations:
- Set stop-losses, especially with leveraged products
- Avoid over-leveraging positions (general rule: never use more than 5-10% account on single trade)
- Understand funding rates for perpetual contracts
- Be aware of premium/discount on futures contracts
- Consider the impact of exchange insurance funds on liquidation mechanics

Tax Implications:
- Trading activities typically trigger taxable events
- Different countries classify crypto trading differently (capital gains, income tax, etc.)
- Record-keeping is essential for accurate tax reporting

Most cryptocurrency traders begin with spot trading to understand market dynamics before advancing to more complex derivatives trading. Educational resources and paper trading (practice accounts) are recommended before committing significant capital.
"""
    
    def get_indian_financial_advice(self, topic: str, context: Optional[str] = None) -> str:
        """
        Get detailed information about an Indian financial topic
        
        Args:
            topic: The financial topic to get advice on
            context: Additional context about the user's query
            
        Returns:
            Detailed advice about the topic
        """
        # Add Indian context to the prompt
        prompt = f"""
        You are a financial expert specializing in Indian financial markets, taxes, investments, and personal finance.
        
        Provide detailed, accurate, and up-to-date information about the following Indian financial topic:
        
        {topic}
        
        Include specific details about:
        - Current rates, limits, and regulations in India
        - Tax implications (including latest budget impacts)
        - Documentation and eligibility requirements
        - Process steps if applicable
        - Recommended strategies or best practices
        - Relevant government schemes or programs
        - Recent changes or updates to regulations
        
        Your response should be comprehensive, easy to understand, and specific to the Indian context.
        """
        
        if context:
            prompt += f"\n\nAdditional context from the user: {context}"
        
        return self.generate_response(prompt)
    
    def get_loan_information(self, loan_type: str) -> str:
        """
        Get detailed information about specific loan types in India
        
        Args:
            loan_type: Type of loan (home, car, personal, education, etc.)
            
        Returns:
            Detailed information about the loan type
        """
        prompt = f"""
        You are a loan and banking expert in India. Provide detailed information about {loan_type} loans in India.
        
        Include:
        - Current interest rate ranges from major banks and NBFCs
        - Loan tenure options and typical loan-to-value ratios
        - Eligibility criteria (income requirements, credit score, etc.)
        - Documentation required for application
        - Processing fees and charges
        - Tax benefits (if applicable)
        - Prepayment/foreclosure terms and penalties
        - Comparison of top lenders and their unique offerings
        - Digital vs. traditional application process
        - Tips for getting the best rates
        
        Your response should be detailed, up-to-date with current market conditions, and specific to the Indian financial system.
        """
        
        return self.generate_response(prompt)
    
    def get_tax_information(self, tax_topic: str) -> str:
        """
        Get detailed information about Indian tax topics
        
        Args:
            tax_topic: Specific tax topic (income tax, GST, capital gains, etc.)
            
        Returns:
            Detailed information about the tax topic
        """
        prompt = f"""
        You are a tax expert in India. Provide detailed information about {tax_topic} in India.
        
        Include:
        - Current tax rates and slabs (Both old and new tax regimes if applicable)
        - Filing requirements and deadlines
        - Deductions and exemptions available
        - Documentation and record-keeping requirements
        - Recent changes from the latest budget
        - Common mistakes to avoid
        - Tax-saving strategies
        - Compliance requirements for different categories of taxpayers
        - Penalties for non-compliance
        - Digital tools and resources available for tax planning
        
        Your response should be accurate, comprehensive, and reflect the latest tax laws and regulations in India.
        """
        
        return self.generate_response(prompt)
    
    def categorize_financial_query(self, query: str) -> Dict[str, Any]:
        """
        Categorize a financial query to determine the appropriate specialized prompt
        
        Args:
            query: User's financial query
            
        Returns:
            Dictionary with category and specific topic
        """
        # Basic categorization when API is not available
        if "loan" in query.lower() or "mortgage" in query.lower() or "emi" in query.lower() or "borrow" in query.lower():
            return {"category": "Loan", "specific_topic": query, "keywords": ["loan"]}
        elif "tax" in query.lower() or "gst" in query.lower() or "income tax" in query.lower() or "deduction" in query.lower():
            return {"category": "Tax", "specific_topic": query, "keywords": ["tax"]}
        elif "invest" in query.lower() or "fund" in query.lower() or "stock" in query.lower() or "market" in query.lower():
            return {"category": "Investment", "specific_topic": query, "keywords": ["investment"]}
        elif "insurance" in query.lower() or "policy" in query.lower() or "premium" in query.lower():
            return {"category": "Insurance", "specific_topic": query, "keywords": ["insurance"]}
        else:
            return {"category": "General Financial Planning", "specific_topic": query, "keywords": []}
    
    def generate_response_with_graph_rag(self, query: str, graph_rag, max_tokens: int = 2048) -> str:
        """
        Generate a response using Google Gemini enhanced with Graph RAG
        
        Args:
            query: The user query
            graph_rag: GraphRAG instance to enhance the query
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            Generated text response with graph knowledge
        """
        # Log the query
        self.logger.info(f"Generate graph-enhanced response for: {query[:100]}...")
        
        try:
            # Get Graph RAG results
            rag_results = graph_rag.query(query, top_k=5, max_hops=2)
            
            # Enhance prompt with Graph RAG context
            enhanced_prompt = graph_rag.enhance_prompt(query, rag_results)
            
            self.logger.info("Using Graph RAG enhanced prompt for Gemini")
            
            # Generate response using the enhanced prompt
            response = self.generate_response(enhanced_prompt, max_tokens)
            
            # Log success
            self.logger.info(f"Successfully generated Graph RAG enhanced response")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error generating Graph RAG enhanced response: {str(e)}")
            
            # Fall back to regular response generation
            self.logger.info("Falling back to regular response generation")
            return self.generate_response(query, max_tokens)
    
    def generate_relationship_response(self, query: str, graph_rag, max_tokens: int = 2048) -> str:
        """
        Generate a response about relationships between entities using Graph RAG
        
        Args:
            query: The relationship query
            graph_rag: GraphRAG instance to enhance the query
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            Generated text response focusing on relationships
        """
        self.logger.info(f"Generating relationship response for: {query[:100]}...")
        
        try:
            # Use specialized relationship query
            rag_results = graph_rag.crypto_relationships_query(query, top_k=3)
            
            # Create a relationship-focused prompt
            relationship_prompt = f"""
You are a financial expert specializing in cryptocurrency and blockchain technology.

Please analyze the relationships between the following entities based on the given context.
Focus on explaining how these entities are connected, their similarities, differences, and ecosystem roles.

{rag_results.get('rag_context', '')}

User query: {query}

Provide a clear, detailed explanation of the relationships between these entities.
"""
            
            # Generate response with the specialized prompt
            self.logger.info("Using relationship-focused prompt for Gemini")
            response = self.generate_response(relationship_prompt, max_tokens)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error generating relationship response: {str(e)}")
            
            # Fall back to regular response generation
            self.logger.info("Falling back to regular response generation")
            return self.generate_response(query, max_tokens)

    # Function to analyze complex financial scenarios with knowledge graph support
    def analyze_financial_scenario(self, scenario: str, graph_rag, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Analyze a complex financial scenario using knowledge graph and LLM
        
        Args:
            scenario: The financial scenario to analyze
            graph_rag: GraphRAG instance to provide knowledge context
            context: Additional context about the scenario
            
        Returns:
            Detailed analysis of the scenario
        """
        self.logger.info(f"Analyzing financial scenario: {scenario[:100]}...")
        
        # Extract relevant entities and concepts from the scenario
        rag_results = graph_rag.query(scenario, top_k=5, max_hops=2)
        
        # Create a structured analysis prompt
        analysis_prompt = f"""
You are a financial expert tasked with analyzing a complex scenario.

SCENARIO:
{scenario}

KNOWLEDGE CONTEXT:
{rag_results.get('rag_context', '')}

{'ADDITIONAL CONTEXT:\n' + json.dumps(context, indent=2) if context else ''}

Please provide a detailed analysis including:
1. Key entities and their relationships
2. Financial implications and considerations
3. Potential outcomes and recommendations
4. Risk factors to consider

Your analysis should be well-structured, factual, and based on the provided knowledge context.
"""
        
        # Generate the analysis
        analysis = self.generate_response(analysis_prompt, max_tokens=3072)
        
        return analysis

    def get_crypto_trading_fallback(self) -> str:
        """Provide a detailed fallback response for crypto trading queries when API fails"""
        return """
Cryptocurrency trading offers various methods to buy, sell and exchange digital assets. Here's a comprehensive overview of the main types of crypto trading:

1. Spot Trading:
   - The most basic form where you buy/sell cryptocurrencies at current market prices
   - Full ownership of assets with no leverage
   - Best for beginners and those who want to accumulate crypto for long-term holding
   - Popular platforms: Binance, Coinbase, Kraken

2. Futures Trading:
   - Contract-based trading that speculates on future crypto prices without owning the underlying asset
   - Features:
     * Leverage: Typically 2x to 125x depending on the exchange
     * Settlement types: USDT-margined (settled in USDT) or coin-margined (settled in the base crypto)
     * Contract types: Perpetual (no expiry) or quarterly contracts
   - Higher risk due to potential liquidation if market moves against position
   - Popular platforms: Binance Futures, Bybit, OKX, dYdX

3. Margin Trading:
   - Borrowing funds from exchange to amplify trading positions
   - Typically offers 2x to 10x leverage
   - Incurs interest on borrowed funds
   - Available on platforms like Binance, Kraken, and KuCoin

4. P2P (Peer-to-Peer) Trading:
   - Direct trading between users without exchange intermediation for order matching
   - Features:
     * Multiple payment methods (bank transfers, mobile payments, cash)
     * Escrow services for security
     * Various currencies supported
     * Self-set prices (premium or discount to market)
   - Often used in regions with limited banking access or crypto regulations
   - Popular platforms: Binance P2P, LocalBitcoins, Paxful

5. Options Trading:
   - Contracts giving the right (not obligation) to buy/sell crypto at predetermined price
   - American options (exercise anytime) vs European options (exercise at expiry only)
   - Complex strategies like straddles, strangles, and spreads available
   - Available on Deribit, Binance, OKX

6. Perpetual Swaps:
   - Most popular derivative product in crypto
   - Futures contracts with no expiry date
   - Funding rate mechanism keeps prices aligned with spot market
   - Available on most major derivatives exchanges

7. Grid Trading:
   - Automated strategy placing buy/sell orders at regular price intervals
   - Works well in sideways/ranging markets
   - Accumulates profits from price volatility without predicting direction
   - Available as bots on platforms like Pionex, 3Commas, or exchange-native tools

8. DeFi Trading:
   - Trading on decentralized exchanges (DEXs) using smart contracts
   - Includes spot trading (Uniswap, PancakeSwap) and derivatives (GMX, dYdX)
   - Non-custodial (you control your keys)
   - Higher gas fees but no KYC requirements

Risk Management Considerations:
- Set stop-losses, especially with leveraged products
- Avoid over-leveraging positions (general rule: never use more than 5-10% account on single trade)
- Understand funding rates for perpetual contracts
- Be aware of premium/discount on futures contracts
- Consider the impact of exchange insurance funds
- Maintain detailed records of all trades for tax purposes

Most cryptocurrency traders begin with spot trading to understand market dynamics before advancing to more complex derivatives trading. Educational resources and paper trading (practice accounts) are recommended before committing significant capital.
"""

    def get_stock_market_fallback(self, is_indian: bool = False) -> str:
        """Provide a detailed fallback response for stock market queries when API fails"""
        if is_indian:
            return """
# Indian Stock Market Overview

The Indian stock market is one of the most dynamic emerging markets, offering a wide range of investment opportunities across various sectors. Here are key aspects of the Indian stock market:

## Major Stock Exchanges
- **National Stock Exchange (NSE)**: India's largest stock exchange by trading volume
- **Bombay Stock Exchange (BSE)**: Asia's oldest stock exchange

## Key Market Indices
- **NIFTY 50**: Represents the weighted average of 50 of the largest Indian companies listed on NSE
- **SENSEX**: Comprises 30 well-established and financially sound companies listed on BSE
- **NIFTY Bank**: Tracks the performance of 12 large Indian banking stocks
- **NIFTY IT**: Measures the performance of IT sector companies

## Market Regulators
- **Securities and Exchange Board of India (SEBI)**: The primary regulatory body
- **Reserve Bank of India (RBI)**: Regulates banking and financial policies

## Investment Options
1. **Stocks/Equities**: Direct ownership in Indian companies
2. **Mutual Funds**: Professionally managed investment funds
3. **Exchange Traded Funds (ETFs)**: Baskets of securities that track an underlying index
4. **Derivatives**: Futures and options contracts 
5. **Bonds and Debentures**: Fixed-income securities

## Major Sectors
- Information Technology (TCS, Infosys, Wipro)
- Banking & Financial Services (HDFC Bank, SBI, ICICI Bank)
- Oil & Gas (Reliance Industries, ONGC)
- Pharmaceuticals (Sun Pharma, Dr. Reddy's)
- Automobile (Maruti Suzuki, Tata Motors)
- Consumer Goods (HUL, ITC)

## Market Participants
- Retail Investors (individuals)
- Foreign Institutional Investors (FIIs)
- Domestic Institutional Investors (DIIs)
- Qualified Institutional Buyers (QIBs)
- High Net Worth Individuals (HNIs)

## Trading Hours
- Regular trading session: Monday to Friday, 9:15 AM to 3:30 PM IST
- Pre-open session: 9:00 AM to 9:15 AM IST

## Investment Considerations
- Understand your risk profile before investing
- Diversify your portfolio across different sectors
- Consider long-term investment for better returns
- Stay updated with company fundamentals and market trends
- Be aware of taxation aspects (STCG, LTCG, STT)
- Consider consulting with a SEBI-registered financial advisor

For specific stock recommendations or detailed market analysis, it's advisable to consult with a financial advisor and conduct thorough research based on your financial goals and risk tolerance.
"""
        else:
            return """
# Global Stock Markets Overview

Stock markets are platforms where shares of publicly listed companies are traded. Here's a comprehensive overview of global stock markets:

## Major Stock Exchanges
- **New York Stock Exchange (NYSE)**: The world's largest stock exchange by market capitalization
- **NASDAQ**: Home to many technology companies and the second-largest exchange
- **London Stock Exchange (LSE)**: Europe's largest stock exchange
- **Tokyo Stock Exchange (TSE)**: Asia's largest stock exchange
- **Shanghai Stock Exchange**: Mainland China's largest exchange
- **Hong Kong Stock Exchange (HKEX)**: Major gateway for international investors into China

## Key Market Indices
- **S&P 500**: 500 large US companies
- **Dow Jones Industrial Average**: 30 large US companies
- **NASDAQ Composite**: All companies listed on NASDAQ
- **FTSE 100**: 100 largest companies on LSE
- **Nikkei 225**: 225 large Japanese companies
- **DAX**: 40 major German companies
- **CAC 40**: 40 significant French companies

## Types of Investments
1. **Common Stocks**: Represent ownership in a company
2. **Preferred Stocks**: Fixed dividends but limited ownership rights
3. **ETFs (Exchange-Traded Funds)**: Baskets of securities tracking indexes
4. **Mutual Funds**: Professionally managed investment pools
5. **Bonds**: Fixed-income debt securities
6. **REITs (Real Estate Investment Trusts)**: Real estate portfolios
7. **Derivatives**: Options, futures, swaps

## Investment Strategies
- **Value Investing**: Buying undervalued stocks
- **Growth Investing**: Focusing on companies with high growth potential
- **Income Investing**: Seeking dividend-paying stocks
- **Index Investing**: Tracking market indexes
- **Momentum Investing**: Following market trends
- **Contrarian Investing**: Going against market consensus
- **Dollar-Cost Averaging**: Regular investments regardless of price

## Market Participants
- Retail Investors
- Institutional Investors
- Market Makers
- Brokers
- High-Frequency Traders

## Market Analysis Methods
- **Fundamental Analysis**: Evaluating a company's financials and business model
- **Technical Analysis**: Studying price patterns and market trends
- **Quantitative Analysis**: Using mathematical models to evaluate investments

## Risk Management
- Portfolio Diversification
- Asset Allocation
- Stop-Loss Orders
- Position Sizing
- Regular Portfolio Rebalancing

## Market Hours
- Most major exchanges operate during local business hours on weekdays
- Some markets offer pre-market and after-hours trading

For personalized investment advice, it's recommended to consult with a qualified financial advisor who can tailor recommendations to your specific financial goals and risk tolerance.
"""

    def get_home_loan_fallback(self, is_indian: bool = False) -> str:
        """Provide a detailed fallback response for home loan queries when needed"""
        if is_indian:
            return """
# Home Loans in India

Home loans in India typically have the following characteristics:

**Interest Rates:** Currently ranging from 8.50% to 10.50% p.a.

**Loan Tenure:** Up to 30 years

**Loan-to-Value Ratio:** Up to 80-90% of the property value

**Top Lenders:**
- State Bank of India (SBI)
- HDFC Limited
- ICICI Bank
- Axis Bank
- LIC Housing Finance

**Required Documents:**
- Identity proof (Aadhar, PAN, Passport)
- Address proof
- Income documents (salary slips or ITR)
- Property documents

**Tax Benefits:** Under Section 80C for principal repayment (up to ₹1.5 lakh) and Section 24(b) for interest payment (up to ₹2 lakh for self-occupied properties)

**Eligibility:** Typically requires a good credit score (700+), stable income, and employment history

**Processing Fees:** Usually 0.5% to 1% of the loan amount

Would you like more specific information about any aspect of home loans in India?
"""
        else:
            return """
# Home Loans/Mortgages

Home loans or mortgages are long-term loans for purchasing or refinancing a home. Here are the key aspects:

**Types of Mortgages:**
- Fixed-rate mortgages: Interest rate remains the same throughout the loan term
- Adjustable-rate mortgages (ARMs): Interest rate adjusts periodically based on market conditions
- FHA loans: Government-backed loans with lower down payment requirements
- VA loans: For veterans and service members
- USDA loans: For rural homebuyers

**Typical Terms:**
- Down payment: 3% to 20% of the home's value
- Loan terms: 15, 20, or 30 years (30 years being most common)
- Interest rates: Vary based on market conditions, credit score, and loan type

**Eligibility Factors:**
- Credit score (typically 620+ for conventional loans)
- Debt-to-income ratio (typically below 43%)
- Employment history and income stability
- Down payment amount

Would you like more specific information about mortgage rates, the application process, or refinancing options?
"""

    def get_tax_fallback(self, is_indian: bool = False) -> str:
        """Provide a detailed fallback response for tax queries when needed"""
        # ... existing code ... 