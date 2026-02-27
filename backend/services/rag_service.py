"""RAG (retrieval-augmented generation) service for FinNexus.

This module provides a light-weight, well-formed ChromaDB integration used
by the application startup to initialize and seed the educational knowledge
collection. It exposes:

- `initialize_chromadb()` to initialize the client/collection (idempotent)
- `seed_initial_knowledge()` to seed curated lesson documents
- `_collection` global (used elsewhere for quick checks)

The implementation below is intentionally simple and robust for local
development: it uses a SentenceTransformer embedder wrapped for Chroma.
"""
import logging
from typing import List, Dict, Any

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer

from ..config import settings

logger = logging.getLogger(__name__)

# Module-level references required by other modules (main.py checks _collection)
_client = None
_collection = None
_embedder = None


def _get_embedder():
    global _embedder
    if _embedder is None:
        try:
            _embedder = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("SentenceTransformer embedder loaded")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    return _embedder


def initialize_chromadb() -> bool:
    """Initialize ChromaDB persistent client and the knowledge collection.

    Returns True on success. If the collection is empty it will be seeded.
    """
    global _client, _collection

    try:
        # Ensure embedder is ready (used to build embedding function wrapper)
        embedder = _get_embedder()

        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2",
            model=embedder
        )

        _client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False, allow_reset=False)
        )

        _collection = _client.get_or_create_collection(
            name="finlearn_knowledge",
            embedding_function=ef,
            metadata={"description": "FinNexus educational content"}
        )

        count = _collection.count()
        logger.info(f"ChromaDB initialized at {settings.chroma_persist_dir} with {count} documents")

        if count == 0:
            seed_initial_knowledge()

        return True

    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB: {e}")
        return False


def chunk_text(text: str, chunk_size: int = 200, overlap: int = 50) -> List[str]:
    if not text:
        return []
    words = text.split()
    chunks: List[str] = []
    i = 0
    n = len(words)
    while i < n:
        chunk = words[i:i + chunk_size]
        chunks.append(" ".join(chunk))
        i += chunk_size - overlap
    return chunks


def seed_initial_knowledge() -> bool:
    """Seed the collection with curated educational documents.

    This function is idempotent for common development use-cases.
    """
    global _collection
    if _collection is None:
        logger.error("Cannot seed knowledge: collection is not initialized")
        return False

    try:
        # Minimal curated set used for demos and tests
        docs = [
            {
                "id": "lesson_001",
                "title": "Introduction to Stock Markets",
                "content": (
                    "A stock represents ownership in a company. When you buy shares, you "
                    "become a partial owner. Stock markets are exchanges where buyers and "
                    "sellers trade shares. Key concepts: Bull market, Bear market, Dividends, "
                    "Capital gains. Market indices like the S&P 500 track performance."
                ),
                "topic": "Stocks",
                "level": "BEGINNER",
                "source": "seed"
            },
            {
                "id": "lesson_002",
                "title": "Technical Analysis Basics",
                "content": (
                    "Technical analysis studies price action and volume to forecast short-term "
                    "movements. Tools include moving averages, RSI, MACD, and candlestick patterns."
                ),
                "topic": "Technical Analysis",
                "level": "INTERMEDIATE",
                "source": "seed"
            },
            {
                "id": "lesson_003",
                "title": "Portfolio Diversification",
                "content": (
                    "Diversification reduces idiosyncratic risk by spreading exposure across "
                    "uncorrelated assets. Asset classes include stocks, bonds, commodities, "
                    "and cash. Rebalancing maintains target allocations over time."
                ),
                "topic": "Portfolio",
                "level": "BEGINNER",
                "source": "seed"
            }
        ]

        # Ingest documents as chunked entries so retrieval works via Chroma
        for doc in docs:
            doc_id = doc["id"]
            # Skip if already ingested (simple check by id existence)
            try:
                existing = _collection.get(ids=[f"{doc_id}_chunk_0"])
                if existing and len(existing.get("ids", [])) > 0:
                    logger.info(f"Document {doc_id} already present, skipping")
                    continue
            except Exception:
                # Collection.get may raise if id not present; ignore
                pass

            chunks = chunk_text(doc["content"], chunk_size=200, overlap=50)
            ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
            metadatas = [
                {
                    "doc_id": doc_id,
                    "title": doc["title"],
                    "topic": doc.get("topic", "general"),
                    "level": doc.get("level", "BEGINNER"),
                    "source": doc.get("source", "seed"),
                    "chunk_index": i
                }
                for i in range(len(chunks))
            ]

            _collection.add(ids=ids, documents=chunks, metadatas=metadatas)
            logger.info(f"Seeded document {doc_id} with {len(chunks)} chunks")

        logger.info("ChromaDB seeding complete")
        return True

    except Exception as e:
        logger.error(f"Failed to seed initial knowledge: {e}")
        return False


def retrieve_context(query: str, user_level: str = None, top_k: int = 3) -> List[Dict[str, Any]]:
    """Perform a semantic search and return top_k passages with metadata."""
    global _collection
    if _collection is None:
        logger.warning("retrieve_context called before collection initialization")
        return []

    try:
        where = None
        if user_level:
            where = {"level": user_level.upper()}

        results = _collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"]
        )

        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0]

        out = []
        for c, m, d in zip(docs, metas, dists):
            out.append({
                "content": c,
                "topic": m.get("topic"),
                "title": m.get("title"),
                "relevance_score": float(1 - d) if d is not None else 0.0
            })

        return out

    except Exception as e:
        logger.error(f"retrieve_context failed: {e}")
        return []

                    def seed_initial_knowledge(self) -> bool:
                        """Seed the collection with curated educational documents if collection has < 5 docs."""
                        try:
                            count = self._collection.count()
                            if count >= 5:
                                logger.info("Collection already seeded")
                                return True

                            docs = []

                            # BEGINNER (10)
                            beginner_topics = [
                                ("what_is_stock_market", "What is Stock Market",
                                 "The stock market is a public marketplace where shares of publicly held companies are issued and traded. Investors buy and sell shares to gain exposure to company performance, receive dividends, or speculate on price movements. Stocks represent ownership, and prices fluctuate based on supply and demand, earnings, macro factors, and investor sentiment. Exchanges like NYSE and NASDAQ provide venues, while indices like the S&P 500 track overall market performance." , "BEGINNER"),
                                ("what_is_investing", "What is Investing",
                                 "Investing is allocating capital to assets such as stocks, bonds, or real estate with the expectation of generating returns over time. It differs from trading by focusing on long-term growth, compounding, and risk management. Key principles include diversification, aligning investments with goals and time horizon, and understanding risk tolerance." , "BEGINNER"),
                                ("stocks_vs_bonds", "Stocks vs Bonds",
                                 "Stocks provide equity ownership and potential capital appreciation, typically with higher volatility. Bonds are debt instruments offering fixed or variable interest payments and are generally lower risk, providing income and capital preservation. Combining both helps balance return and risk through asset allocation." , "BEGINNER"),
                                ("what_is_crypto", "What is Cryptocurrency",
                                 "Cryptocurrency is a digital asset using cryptography and decentralized networks like blockchain to secure and record transactions. Bitcoin is the first and most recognized, serving as a store of value, while platforms like Ethereum support smart contracts and decentralized applications. Crypto markets are highly volatile and governed by supply-demand, network adoption, and regulatory developments." , "BEGINNER"),
                                ("what_is_gold", "What is Gold as Investment",
                                 "Gold has historically been a store of value and hedge against inflation and currency devaluation. Investors hold gold via physical bullion, ETFs, or mining stocks. Gold typically has low correlation to equities, making it a diversification tool during market stress." , "BEGINNER"),
                                ("bull_and_bear", "Bull and Bear Market",
                                 "Bull markets are periods of rising prices and optimistic investor sentiment. Bear markets are prolonged declines often caused by economic contraction or negative shocks. Recognizing phases helps investors adjust allocations and risk management strategies." , "BEGINNER"),
                                ("what_is_portfolio", "What is a Portfolio",
                                 "A portfolio is a collection of investments held by an individual or institution. Effective portfolios balance risk and return by diversifying across asset classes, sectors, and geographies. Rebalancing maintains target allocations over time." , "BEGINNER"),
                                ("risk_and_return", "Risk and Return Basics",
                                 "Higher potential returns generally come with higher risk. Investors use measures like volatility and drawdown to quantify risk, and tools such as diversification to manage it. The goal is to achieve risk-adjusted returns aligned with objectives." , "BEGINNER"),
                                ("what_is_inflation", "What is Inflation",
                                 "Inflation measures the rate at which general price levels rise, reducing purchasing power. Central banks monitor inflation to guide monetary policy; moderate inflation is normal, while high inflation erodes real returns on fixed-income investments." , "BEGINNER"),
                                ("what_is_interest_rate", "What is Interest Rate",
                                 "Interest rates are the cost of borrowing money. Central bank policy rates influence market interest rates, impacting consumer spending, corporate borrowing costs, and asset valuations. Rising rates can pressure equities but benefit savers and fixed-income yields." , "BEGINNER")
                            ]

                            # INTERMEDIATE (10)
                            intermediate_topics = [
                                ("pe_ratio", "P/E Ratio Explained",
                                 "Price-to-earnings (P/E) ratio compares a company\'s share price to its per-share earnings. It helps investors judge whether a stock is over- or undervalued relative to peers or historical norms. High P/E may indicate growth expectations; low P/E could signal value or depressed prospects." , "INTERMEDIATE"),
                                ("rsi_indicator", "RSI Indicator",
                                 "The Relative Strength Index (RSI) is a momentum oscillator measuring recent price changes to evaluate overbought or oversold conditions. Values above 70 often suggest overbought, below 30 oversold. Traders use RSI divergences and crossovers as signals." , "INTERMEDIATE"),
                                ("macd_indicator", "MACD Indicator",
                                 "MACD (Moving Average Convergence Divergence) captures momentum by subtracting two EMAs. A signal line helps identify crossovers; the histogram shows divergence. MACD is used to spot trend changes and momentum shifts." , "INTERMEDIATE"),
                                ("bollinger_bands", "Bollinger Bands",
                                 "Bollinger Bands plot standard deviation bands around a moving average to show volatility. Price touching the upper band may indicate short-term overbought conditions, while the lower band may signal oversold. Traders use band squeezes to anticipate breakouts." , "INTERMEDIATE"),
                                ("interest_rate_effects", "How Interest Rates Affect Markets",
                                 "Interest rates affect discount rates for future cash flows, influencing equity valuations. Higher rates raise borrowing costs and can dampen consumer spending and corporate investment; lower rates can stimulate growth and elevate asset prices." , "INTERMEDIATE"),
                                ("crypto_cycles", "Crypto Market Cycles",
                                 "Cryptocurrency markets exhibit distinct cycles influenced by adoption, halving events, regulatory news, and macro liquidity. Understanding on-chain metrics and macro drivers helps contextualize price phases." , "INTERMEDIATE"),
                                ("gold_safe_haven", "Gold as Safe Haven",
                                 "Gold often outperforms during market stress; investors use it to hedge geopolitical risk and inflation. Its role depends on liquidity needs and portfolio allocation goals." , "INTERMEDIATE"),
                                ("portfolio_diversification", "Portfolio Diversification",
                                 "Diversification reduces idiosyncratic risk by spreading exposure across uncorrelated assets. Modern portfolio theory formalizes optimal mixes given expected returns and covariances." , "INTERMEDIATE"),
                                ("tech_analysis_basics", "Technical Analysis Basics",
                                 "Technical analysis studies price action and volume to forecast short-term movements. Common tools include trendlines, moving averages, and momentum indicators." , "INTERMEDIATE"),
                                ("fundamental_analysis", "Fundamental Analysis Basics",
                                 "Fundamental analysis focuses on company financials, industry position, and macro trends to estimate intrinsic value and long-term prospects." , "INTERMEDIATE")
                            ]

                            # ADVANCED (10)
                            advanced_topics = [
                                ("sharpe_ratio", "Sharpe Ratio and Risk-Adjusted Returns",
                                 "Sharpe ratio measures excess return per unit of volatility. It helps compare strategies on a risk-adjusted basis; however, it assumes returns distribution symmetry and may be supplemented by Sortino ratio or drawdown-focused metrics." , "ADVANCED"),
                                ("options_derivatives", "Options and Derivatives Basics",
                                 "Options are contracts granting the right but not obligation to buy/sell an asset at a strike price before expiry. Greeks quantify sensitivity to price, volatility, and time decay, enabling hedging and strategic exposures." , "ADVANCED"),
                                ("quant_trading", "Quantitative Trading Strategies",
                                 "Quant strategies use systematic rules and statistical signals to exploit market inefficiencies, ranging from momentum to mean-reversion and factor models. Robust backtesting and risk controls are essential." , "ADVANCED"),
                                ("macro_indicators", "Macroeconomic Indicators Deep Dive",
                                 "Macroeconomic indicators like GDP, CPI, and employment data drive monetary policy and market cycles. Interpreting leading vs lagging indicators aids positioning decisions." , "ADVANCED"),
                                ("central_bank_policy", "Central Bank Policy and Market Impact",
                                 "Central banks use tools like policy rates and asset purchases to manage inflation and growth. Policy shifts affect yield curves, currency values, and risk asset valuations globally." , "ADVANCED"),
                                ("correlation_portfolio", "Correlation and Portfolio Theory",
                                 "Understanding asset correlations and covariance matrices enables construction of efficient portfolios and risk budgeting across factors and regimes." , "ADVANCED"),
                                ("volatility_vix", "Volatility and VIX",
                                 "Volatility is a key risk metric; the VIX reflects S&P 500 implied volatility. Volatility regimes influence option pricing and risk hedging strategies." , "ADVANCED"),
                                ("sector_rotation", "Sector Rotation Strategy",
                                 "Sector rotation allocates to sectors expected to outperform in different economic phases, informed by macro indicators and earnings cycles." , "ADVANCED"),
                                ("algo_trading", "Algorithmic Trading Overview",
                                 "Algorithmic trading automates execution and strategy deployment, integrating low-latency data, signal generation, and execution algorithms to manage market impact." , "ADVANCED"),
                                ("black_swan", "Black Swan Events and Tail Risk",
                                 "Tail risks are rare high-impact events; preparing involves stress testing, tail-hedging, and contingency planning to protect capital during extreme shocks." , "ADVANCED")
                            ]

                            all_docs = beginner_topics + intermediate_topics + advanced_topics

                            # Ingest all docs
                            for doc_id, title, content, level in all_docs:
                                self.ingest_document({
                                    "id": doc_id,
                                    "title": title,
                                    "content": content,
                                    "topic": title,
                                    "level": level,
                                    "source": "seed"
                                })

                            logger.info(f"ChromaDB seeded with {len(all_docs)} documents")
                            return True

                        except Exception as e:
                            logger.error(f"Failed to seed initial knowledge: {e}")
                            return False

                    def get_collection_stats(self) -> Dict[str, Any]:
                        try:
                            total = self._collection.count()
                            # gather topics and levels
                            metas = self._collection.get(include=["metadatas"]).get("metadatas", [])
                            topics = set()
                            levels = set()
                            if metas and isinstance(metas, list):
                                flat = metas[0] if isinstance(metas[0], list) else metas
                                for m in flat:
                                    topics.add(m.get("topic"))
                                    levels.add(m.get("level"))

                            return {
                                "total_documents": total,
                                "topics_covered": list(topics),
                                "levels_covered": list(levels)
                            }
                        except Exception as e:
                            logger.error(f"Failed to get collection stats: {e}")
                            return {"total_documents": 0, "topics_covered": [], "levels_covered": []}


                # Singleton instance for app usage
                _rag_service = None

                def get_rag_service() -> RAGService:
                    global _rag_service
                    if _rag_service is None:
                        _rag_service = RAGService(persist_dir=settings.chroma_persist_dir)
                    return _rag_service
